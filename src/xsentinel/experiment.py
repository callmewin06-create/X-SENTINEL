"""Auditable sequential training, calibration, and evaluation orchestration."""
import csv
import gc
import time
from dataclasses import asdict
from pathlib import Path
import lightgbm as lgb
import numpy as np
from xsentinel.data.prepare import load_data
from xsentinel.attacks.trigger import select_trigger,poison,FEASIBLE
from xsentinel.detection.detector import Detector
from xsentinel.schema import VIEWS
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.evaluation.metrics import rate,auc,paired_bootstrap,latency_summary

def train(X,y,path,config,seed,view=None):
    if len(np.unique(y))!=2: raise ValueError('Training requires both benign and malware labels')
    params=dict(config['params']); params.update(seed=seed,data_random_seed=seed,feature_fraction_seed=seed,bagging_seed=seed)
    lock=Path(path).with_suffix('.training.json')
    expected={'params':params,'seed':seed,'view':view,'rounds':config['view_rounds'] if view else config['rounds'],'rows':len(y)}
    if Path(path).exists():
        state=read_json(lock)
        if state['training']!=expected or state['model_sha256']!=sha256(path):
            raise ValueError('Training checkpoint mismatch')
        return lgb.Booster(model_file=str(path))
    started=time.perf_counter()
    data=np.asarray(X[:,VIEWS[view]]) if view else X
    ds=lgb.Dataset(data,label=y,free_raw_data=True)
    model=lgb.train(params,ds,num_boost_round=config['view_rounds'] if view else config['rounds'])
    model.save_model(str(path)); del ds,data; gc.collect()
    write_json(lock,{'training':expected,'model_sha256':sha256(path),'elapsed_seconds':time.perf_counter()-started})
    return model

def model_performance(model,X,y,threshold):
    p=model.predict(X,num_threads=4)
    return performance_from_predictions(p,y,threshold)

def performance_from_predictions(p,y,threshold):
    pred=p>=threshold
    return {'accuracy':float(np.mean(pred==y)),'tpr':rate(pred[y==1]),'fpr':rate(pred[y==0]),'auroc':auc(p[y==1],p[y==0])}

def batch_scores(detector,X,batch_size=128):
    result={}; probability=[]
    for offset in range(0,len(X),batch_size):
        scores,details=detector.scores(X[offset:offset+batch_size])
        for k,v in scores.items(): result.setdefault(k,[]).append(v)
        probability.append(details['malware_probability'])
    return {k:np.concatenate(v) for k,v in result.items()}, np.concatenate(probability)

def evaluate(detector,clean,d,splits,trigger,out,config):
    out=Path(out); out.mkdir(parents=True,exist_ok=True); t=config['detector']['malware_threshold']
    limit=config.get('evaluation_limit'); rng=np.random.default_rng(config['detector']['seed'])
    def subset(ids):
        return np.sort(rng.choice(ids,min(limit,len(ids)),replace=False)) if limit else ids
    benign_ids=subset(splits['benign']); malware_ids=subset(splits['malware'])
    xb=np.asarray(d['X_test'][benign_ids]); xm=np.asarray(d['X_test'][malware_ids]); xt=trigger.apply(xm)
    # All malware is scored; ASR uses fixed clean-model eligibility as denominator.
    eligible=clean.predict(xm,num_threads=4)>=t
    pools={'benign':xb,'malware':xm,'trigger':xt}
    scores={}; predictions={}
    for name,X in pools.items():
        scores[name],predictions[name]=batch_scores(detector,X)
    success=eligible&(predictions['trigger']<t)
    reference=detector.reference
    entropy_cut=float(np.quantile(reference[:,611],.9))
    size_ratio_cut=float(np.quantile(reference[:,616]/(1+reference[:,620]),.9))
    rare=(xb[:,611]>entropy_cut)|(xb[:,616]/(1+xb[:,620])>size_ratio_cut)
    metrics={}
    for method,positive in scores['trigger'].items():
        neg=scores['benign'][method]; flags=positive>detector.thresholds[method]; bf=neg>detector.thresholds[method]
        metrics[method]={'auroc_trigger_vs_benign':auc(positive,neg),
            'auroc_trigger_vs_malware':auc(positive,scores['malware'][method]),
            'auc_bootstrap':paired_bootstrap(positive,neg,repeats=config['bootstrap_repeats']),
            'recall_all_trigger':rate(flags),'recall_attack_successful':rate(flags[success]),
            'benign_fpr':rate(bf),'rare_benign_fpr':rate(bf[rare]),'ordinary_benign_fpr':rate(bf[~rare]),
            'post_defense_asr':rate((predictions['trigger'][eligible]<t)&~flags[eligible]),
            'threshold':detector.thresholds[method]}
    for method in ('M4_reduced','M4_full','X_reduced','X_full','X_reduced_M5_limited','X_full_M5_limited'):
        if method in metrics:
            metrics[method]['paired_auc_difference_vs_TADR']=paired_bootstrap(scores['trigger'][method],scores['benign'][method],
                scores['trigger']['TADR'],scores['benign']['TADR'],config['bootstrap_repeats'])
    catch={}
    ids=d['ids_test'][malware_ids].astype(str)
    m1=scores['trigger']['TADR']>detector.thresholds['TADR']
    for method in ('M4_reduced','M4_full','X_reduced','X_full'):
        if method not in scores['trigger']: continue
        m4=scores['trigger'][method]>detector.thresholds[method]
        catch[method]={'both':int(np.sum(m1&m4)),'neither':int(np.sum(~m1&~m4)),
            'TADR_only':ids[m1&~m4].tolist(),method+'_only':ids[~m1&m4].tolist()}
    write_json(out/'paired_cases.json',catch)
    # E0 controls: same vectors through the clean model; no use inside poisoned detector.
    control=Detector(clean,detector.reference,config=config['detector'])
    e0={}
    for name,X in pools.items():
        collected={}
        for offset in range(0,len(X),128):
            components,_=control.components(X[offset:offset+128],include_strip=False)
            for k,v in components.items(): collected.setdefault(k,[]).append(v)
        e0.update({'clean_'+name+'_'+k:np.concatenate(v) for k,v in collected.items()})
    np.savez_compressed(out/'distributions.npz',**{name+'_'+k:v for name,pool in scores.items() for k,v in pool.items()},**e0)
    timings={k:[] for k in ('main_prediction','shap','view_predictions','strip','score_with_shap_no_strip','end_to_end')}
    from xsentinel.baselines.scores import contributions,strip
    latency_n=min(len(xb),config['latency_samples'])
    if latency_n:
        detector.predict(xb[:1]) # warm-up
    for row in xb[:latency_n]:
        x=row[None,:]
        ops={'main_prediction':lambda:detector.model.predict(x,num_threads=4),
             'shap':lambda:contributions(detector.model,x),
             'view_predictions':lambda:[m.predict(x[:,VIEWS[v]],num_threads=4) for v,m in detector.views.items()],
             'strip':lambda:strip(detector.model,x,detector.reference,config['detector']['strip_n'],config['detector']['strip_alpha'],config['detector']['seed']),
             'score_with_shap_no_strip':lambda:detector.components(x,include_strip=False),
             'end_to_end':lambda:detector.predict(x)}
        for k,op in ops.items():
            start=time.perf_counter(); op(); timings[k].append((time.perf_counter()-start)*1000)
    write_json(out/'latency.json',{k:latency_summary(v) for k,v in timings.items()})
    with (out/'scores.csv').open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=['sample_id','pool','method','variant','score','threshold','flagged','latency_ms'])
        writer.writeheader()
        for pool,ss in scores.items():
            pool_ids=d['ids_test'][benign_ids if pool=='benign' else malware_ids].astype(str)
            for method,values in ss.items():
                for sid,value in zip(pool_ids,values):
                    writer.writerow({'sample_id':sid,'pool':pool,'method':method,'variant':method,'score':float(value),
                        'threshold':detector.thresholds[method],'flagged':bool(value>detector.thresholds[method]),'latency_ms':''})
    # Detailed case explanations are limited to ten observations, not selected to imply success.
    cases=[]
    for i in range(min(10,len(xt))):
        ss,details=detector.scores(xt[i:i+1]); phi=details['phi'][0]; top=details['top_features'][0]
        cases.append({'sample_id':ids[i],'attack_success':bool(success[i]),'eligible':bool(eligible[i]),
            'probability':float(details['malware_probability'][0]),'scores':{k:float(v[0]) for k,v in ss.items()},
            'view_predictions':{k:float(v[0]) for k,v in details['view_predictions'].items()},
            'view_contributions':{k:float(v[0]) for k,v in details['view_contributions'].items()},
            'top_shap':[{'index':int(j),'phi':float(phi[j])} for j in top]})
    write_json(out/'case_studies.json',cases)
    summary={'eligible_count':int(eligible.sum()),'malware_evaluated':len(xm),'benign_evaluated':len(xb),
        'attack_asr':rate(predictions['trigger'][eligible]<t),'attack_viable_at_50pct':bool(success.sum()/max(1,eligible.sum())>=.5),
        'poisoned_clean_performance':performance_from_predictions(np.r_[predictions['benign'],predictions['malware']],np.r_[np.zeros(len(xb)),np.ones(len(xm))],t),
        'clean_performance':performance_from_predictions(np.r_[clean.predict(xb,num_threads=4),clean.predict(xm,num_threads=4)],np.r_[np.zeros(len(xb)),np.ones(len(xm))],t),
        'clean_trigger_asr':rate(clean.predict(xt[eligible],num_threads=4)<t) if eligible.any() else rate([]),
        'rare_rules':{'entropy_gt':entropy_cut,'size_over_one_plus_imports_gt':size_ratio_cut,'packed_ground_truth':False},
        'metrics':metrics,'evaluation_pilot':limit is not None,'interpretation':'Detection evidence only meaningful conditional on effective attack; clean-trigger ASR controls direct evasion.'}
    write_json(out/'evaluation.json',summary)
    return summary

def run(directory,output,config_path,allow_vector_stress=False,resume=False):
    config=read_json(config_path); d=load_data(directory); meta=read_json(Path(directory)/'dataset.json')
    if config['attack_profile']=='vector_stress' and not allow_vector_stress:
        raise ValueError('Vector stress requires explicit --allow-vector-stress; no PE realizability claim')
    root=Path(output); root.mkdir(parents=True,exist_ok=True)
    if (root/'run_manifest.json').exists() and not resume:
        raise FileExistsError('Existing run; use a fresh output directory to preserve locked artifacts')
    with np.load(Path(directory)/'splits.npz',allow_pickle=False) as f: splits={k:f[k] for k in f.files}
    split_meta=read_json(Path(directory)/'splits.json')
    if split_meta['dataset_sha256']!=sha256(Path(directory)/'dataset.json') or split_meta['split_sha256']!=sha256(Path(directory)/'splits.npz'):
        raise ValueError('Dataset/split lock mismatch')
    for name,digest in meta['array_sha256'].items():
        if sha256(Path(directory)/name)!=digest: raise ValueError('Dataset checksum mismatch: '+name)
    pilot=meta['pilot'] or config.get('evaluation_limit') is not None
    design={'config':config,'config_sha256':sha256(config_path),
        'dataset_sha256':sha256(Path(directory)/'dataset.json'),'split_sha256':sha256(Path(directory)/'splits.npz'),
        'pilot':pilot,'status':'running','poison_rate_denominator':'all labeled training rows',
        'feasible_indices':FEASIBLE.tolist(),'attack_profile':config['attack_profile'],
        'semantic_rule_sha256':sha256(Path(config_path).resolve().parent/'semantic_rules.json'),
        'source_sha256':{str(f.relative_to(Path(__file__).parent)):sha256(f) for f in Path(__file__).parent.rglob('*.py')}}
    if resume:
        previous=read_json(root/'run_manifest.json')
        for k in ('config_sha256','dataset_sha256','split_sha256','semantic_rule_sha256','source_sha256'):
            if previous[k]!=design[k]: raise ValueError('Resume lock mismatch: '+k)
    else: write_json(root/'run_manifest.json',design)
    ref=np.asarray(d['X_test'][splits['reference']]); cal=np.asarray(d['X_test'][splits['calibration']]); results=[]
    for seed in config['seeds']:
        base=root/f'seed_{seed}'; base.mkdir(exist_ok=True)
        clean=train(d['X_train'],d['y_train'],base/'clean.txt',config,seed)
        views={}; view_paths={}
        for v in VIEWS:
            view_paths[v]=base/f'view_{v}.txt'
            views[v]=train(d['X_train'],d['y_train'],view_paths[v],config,seed,v)
        for kind in config['triggers']:
            trigger=select_trigger(clean,d['X_train'],d['y_train'],kind,seed,config['attack_profile'],config['selection_samples'])
            for poison_rate in config['rates']:
                dest=base/f'{kind}_{poison_rate:g}'; dest.mkdir(exist_ok=True)
                if (dest/'evaluation/evaluation.json').exists():
                    locked=read_json(dest/'threshold_lock.json')
                    if locked['bundle_sha256']!=sha256(dest/'bundle/bundle.json'):
                        raise ValueError('Completed bundle changed')
                    Detector.load(dest/'bundle')
                    summary=read_json(dest/'evaluation/evaluation.json')
                    results.append({'seed':seed,'trigger':kind,'rate':poison_rate,'path':str(dest),'asr':summary['attack_asr'],'pilot':pilot})
                    continue
                print(f'Train seed={seed}, {kind}, poison={poison_rate}',flush=True)
                Xp,ids=poison(d['X_train'],d['y_train'],trigger,poison_rate,seed)
                write_json(dest/'attack_manifest.json',{'trigger':asdict(trigger),'poison_rate':poison_rate,
                    'denominator':len(d['y_train']),'poison_count':len(ids),'poison_ids':d['ids_train'][ids].astype(str).tolist(),
                    'seed':seed,'clean_model_sha256':sha256(base/'clean.txt')})
                model=train(Xp,d['y_train'],dest/'poisoned.txt',config,seed); del Xp; gc.collect()
                detector_config=dict(config['detector']); detector_config['seed']=seed
                detector=Detector(model,ref,views,detector_config).fit(cal)
                detector.save(dest/'bundle',dest/'poisoned.txt',view_paths)
                write_json(dest/'threshold_lock.json',{'bundle_sha256':sha256(dest/'bundle/bundle.json'),'config_sha256':sha256(config_path),
                    'split_sha256':sha256(Path(directory)/'splits.npz'),'timestamp_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()})
                # Threshold and design lock exists before first final-test predictions.
                summary=evaluate(detector,clean,d,splits,trigger,dest/'evaluation',config)
                results.append({'seed':seed,'trigger':kind,'rate':poison_rate,'path':str(dest),'asr':summary['attack_asr'],'pilot':pilot})
                write_json(root/'progress.json',results)
                del detector,model; gc.collect()
        del clean,views; gc.collect()
    manifest=read_json(root/'run_manifest.json'); manifest['status']='complete'; manifest['completed_models']=len(results)
    write_json(root/'run_manifest.json',manifest)
    return results
