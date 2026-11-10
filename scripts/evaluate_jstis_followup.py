"""Post-global-lock confirmation and calibrated same-access final evaluation.

Cannot run before all six attack cells are frozen. Never selects a new trigger
from confirmation/final results. Every static attempt is retained; an adaptive
arm with NO_VALID_ATTACK has N/A detector results and no infeasible replacement.
"""
import argparse,csv,gc,json,sys
from pathlib import Path
import lightgbm as lgb
import numpy as np

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.revision.jstis_gate import verify_global_lock
from xsentinel.schema import get_schema
from xsentinel.attacks.primary import VectorTrigger
from xsentinel.attacks.screen import screen_primary
from xsentinel.baselines.scores import contributions
from xsentinel.baselines.raw_feature_outlier import RawFeatureOutlier
from xsentinel.detection.components import primary_components
from xsentinel.detection.calibration import rank,threshold
from xsentinel.revision.calibration_v2 import exact_interval

RULES={'min_eligible':1000,'min_asr':.5,'min_paired_gain':.2,'strict_max_accuracy_drop':.005}
METHODS=('M3_view_mass','X_primary_reduced','TADR','raw_knn_top32','X_primary_full')


def counted(flags):
    values=np.asarray(flags,dtype=bool);n=len(values);count=int(values.sum())
    return {'count':count,'n':n,'rate':count/n if n else None,
            'pointwise_cp95':exact_interval(count,n) if n else None}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('attacks','global-lock','evaluator','dataset','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();verify_global_lock(a.attacks,a.global_lock)
    source=Path(a.evaluator);receipt=read_json(source/'COMPLETE.json');schema=get_schema(receipt['lock']['schema'])
    if a.dataset!=schema.dataset or receipt['lock']['global_lock_sha256']!=sha256(a.global_lock):raise ValueError('Release mismatch')
    for name,h in receipt['array_sha256'].items():
        if sha256(source/name)!=h:raise ValueError('Evaluator array changed')
    roles={r:{k:np.load(source/f'{r}.{k}.npy',mmap_mode='r') for k in ('X','y','ids')}
           for r in ('confirmation','reference','calibration','final')}
    ref=roles['reference']['X'];cal=roles['calibration']['X'];final=roles['final'];conf=roles['confirmation']
    if np.any(roles['reference']['y']) or np.any(roles['calibration']['y']):raise ValueError('Non-benign calibration/reference')
    raw=RawFeatureOutlier('knn',top_k=32).fit(ref)
    raw_cal=raw.score(cal);raw_benign=raw.score(final['X'][final['y']==0]);raw_original=raw.score(final['X'][final['y']==1])
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    lock={'global_lock_sha256':sha256(a.global_lock),'evaluator_receipt_sha256':sha256(source/'COMPLETE.json'),
          'methods':list(METHODS),'threshold':'.5 classifier; strict score>tau; calibration-only tau',
          'code_sha256':sha256(__file__),'metric_intervals':'Pointwise CP95; repeated IDs and model dependencies remain',
          'raw_top32_indices':raw.indices.tolist(),'schema_sha256':schema.fingerprint}
    if (out/'evaluation.lock.json').exists() and read_json(out/'evaluation.lock.json')!=lock:raise ValueError('Evaluation lock changed')
    write_json(out/'evaluation.lock.json',lock)
    rows=[];no_valid=[]
    def load(path):return lgb.Booster(model_str=path.read_text(encoding='utf8'))
    for seed in (17,29,43):
        cell=Path(a.attacks)/a.dataset/f'seed_{seed}';clean=load(cell/'clean.txt');behavioral=load(cell/'behavioral.txt')
        cp=clean.predict(conf['X'],num_threads=4);xm=final['X'][final['y']==1]
        clean_original=clean.predict(xm,num_threads=4);eligible=clean_original>=.5
        attempts=read_json(cell/'static_attempts.json')
        selected=[{'kind':'static','label':r['profile']+'/'+r['selector'],'fingerprint':r['fingerprint'],
                   'search_feasible':r['metrics']['eligible']>=1000 and r['metrics']['asr']>=.5 and
                       r['metrics']['paired_gain']>=.2 and r['metrics']['accuracy_drop']<.005} for r in attempts]
        for arm in ('asr_only','vmc_aware'):
            result=read_json(cell/f'{arm}.json')
            if result['selected'] is None:
                no_valid.append({'dataset':a.dataset,'seed':seed,'arm':arm,'status':'NO_VALID_ATTACK','detector_results':None})
            else:selected.append({'kind':'adaptive','label':arm,'fingerprint':result['selected']['fingerprint'],'search_feasible':True})
        for attempt in selected:
            modeldir=cell/'candidates'/attempt['fingerprint'];artifact=read_json(modeldir/'result.json')
            trigger=VectorTrigger(**artifact['trigger']);model=load(modeldir/'poisoned.txt')
            dest=out/f'seed_{seed}'/attempt['fingerprint'];dest.mkdir(parents=True,exist_ok=True)
            if (dest/'RESULTS.json').exists():
                saved=read_json(dest/'RESULTS.json')
                if saved['model_sha256']!=sha256(modeldir/'poisoned.txt'):raise ValueError('Scored model changed')
                model_result=saved
            else:
                ctx=trigger.apply(conf['X'][conf['y']==1],schema)
                screening=screen_primary(cp,model.predict(conf['X'],num_threads=4),clean.predict(ctx,num_threads=4),
                    model.predict(ctx,num_threads=4),conf['y'],RULES)
                # No detector scoring or recall is used in confirmation screening.
                def components(X):
                    result={};prob=[]
                    for offset in range(0,len(X),128):
                        batch=X[offset:offset+128];p=model.predict(batch,num_threads=4)
                        phi=contributions(model,batch,schema=schema)
                        pb=behavioral.predict(batch[:,schema.views['behavioral']],num_threads=4)
                        scores,_,_=primary_components(phi,p,schema,pb)
                        for k,v in scores.items():result.setdefault(k,[]).append(v)
                        prob.append(p)
                    return {k:np.concatenate(v) for k,v in result.items()},np.concatenate(prob)
                ref_scores,_=components(ref)
                def score(X):
                    scores,p=components(X)
                    scores['X_primary_reduced']=(rank(ref_scores['M3_view_mass'],scores['M3_view_mass'])+
                        rank(ref_scores['M4_shap_behavioral_conflict'],scores['M4_shap_behavioral_conflict']))/2
                    scores['X_primary_full']=(rank(ref_scores['M3_view_mass'],scores['M3_view_mass'])+
                        rank(ref_scores['M4_prob_gap'],scores['M4_prob_gap']))/2
                    return scores,p
                cal_scores,_=score(cal);cal_scores['raw_knn_top32']=raw_cal
                tau={m:threshold(cal_scores[m]) for m in METHODS}
                ben,ben_p=score(final['X'][final['y']==0]);ben['raw_knn_top32']=raw_benign
                original,original_p=score(xm);original['raw_knn_top32']=raw_original
                xt=trigger.apply(xm,schema);triggered,tp=score(xt);triggered['raw_knn_top32']=raw.score(xt)
                clean_trigger=clean.predict(xt,num_threads=4);before=clean_trigger<.5;after=tp<.5
                successful=eligible&after;new=eligible&after&~before;lost=eligible&before&~after
                metrics={}
                for m in METHODS:
                    flags=triggered[m]>tau[m]
                    metrics[m]={'tau':tau[m],'benign_fpr':counted(ben[m]>tau[m]),
                        'successful_recall':counted(flags[successful]),'paired_new_recall':counted(flags[new]),
                        'unmodified_malware_alert_rate':counted(original[m]>tau[m]),
                        'post_defense_asr':counted((after&~flags)[eligible])}
                model_result={'dataset':a.dataset,'seed':seed,'model_sha256':sha256(modeldir/'poisoned.txt'),
                    'fingerprint':attempt['fingerprint'],'confirmation':screening,'eligible_n':int(eligible.sum()),
                    'asr':counted(after[eligible]),'clean_trigger_asr':counted(before[eligible]),
                    'paired_new':counted(new[eligible]),'paired_lost':counted(lost[eligible]),
                    'paired_gain':float((after[eligible].astype(int)-before[eligible].astype(int)).mean()) if eligible.any() else None,
                    'methods':metrics,'scores_sha256':None}
                np.savez_compressed(dest/'scores.npz',eligible=eligible,successful=successful,paired_new=new,
                    malware_ids=final['ids'][final['y']==1],benign_ids=final['ids'][final['y']==0],
                    clean_original_p=clean_original,clean_trigger_p=clean_trigger,triggered_p=tp,
                    **{f'{group}_{m}':arr[m] for group,arr in [('calibration',cal_scores),('benign',ben),('original_malware',original),('triggered',triggered)] for m in METHODS})
                model_result['scores_sha256']=sha256(dest/'scores.npz');write_json(dest/'RESULTS.json',model_result)
            confirmed=bool(attempt['search_feasible'] and model_result['confirmation']['strong_and_stealth'])
            for method,m in model_result['methods'].items():
                rows.append({'dataset':a.dataset,'seed':seed,'kind':attempt['kind'],'label':attempt['label'],
                    'fingerprint':attempt['fingerprint'],'confirmed':confirmed,'method':method,
                    'recall':m['successful_recall']['rate'],'recall_count':m['successful_recall']['count'],
                    'recall_n':m['successful_recall']['n'],'fpr':m['benign_fpr']['rate'],
                    'fp':m['benign_fpr']['count'],'benign_n':m['benign_fpr']['n'],
                    'post_defense_asr':m['post_defense_asr']['rate']})
            print('EVALUATED',a.dataset,seed,attempt['label'],confirmed,flush=True)
            del model;gc.collect()
    with (out/'per_attempt.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    write_json(out/'NO_VALID_ARMS.json',no_valid);verify_global_lock(a.attacks,a.global_lock)
    write_json(out/'COMPLETE.json',{'status':'DATASET_EVALUATED_ALL_ATTEMPTS_RETAINED','rows':len(rows),
        'no_valid_arms':len(no_valid),'global_lock_sha256':sha256(a.global_lock),'code_sha256':sha256(__file__)})


if __name__=='__main__':main()
