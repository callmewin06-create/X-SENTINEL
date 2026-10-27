"""Paired clean-data budgets for Full/M4-F and Shadow, frozen main classifiers."""
import gc
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
import lightgbm as lgb
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.primary_workflow import open_roles
from xsentinel.experiment import train
from xsentinel.attacks.primary import VectorTrigger
from xsentinel.detection.calibration import rank,threshold
from xsentinel.revision.analysis import attack_groups,revised_metrics
from xsentinel.revision.low_fpr import low_fpr_metrics


def main():
    root=Path('outputs/teacher_revision_2026_10_27/clean_budget');root.mkdir(parents=True,exist_ok=True)
    budgets=[1000,5000,10000,50000,200000]
    execution=read_json('configs/primary_execution.json')
    lock=dict(version='clean-budget-v1',budgets=budgets,seeds=[17,29,43],datasets=['EMBER2018','EMBER2024'],
        cohorts='All54 original cells; report confirmed restricted and cross separately',
        sampling='Nested class-balanced subsets of original clean fit, same IDs for Behavioral and Shadow at each seed/budget',
        main='Original suspicious model frozen;200000 endpoint reuses original clean/Behavioral models',
        methods=['M4_prob_gap','X_primary_full','Shadow'],
        calibration='Original500 benign reference and2000 benign calibration, no fit overlap; strict score>tau',
        score_policy='Original cached M3; recalculate Behavioral gap/Full ranks/Shadow for each budget',
        scope='Post-review sensitivity study on previously observed final; not independent validation',
        code_sha256=sha256(__file__),execution_sha256=sha256('configs/primary_execution.json'))
    lp=root/'protocol.json'
    if lp.exists() and read_json(lp)!=lock:raise ValueError('Changed budget protocol')
    write_json(lp,lock);rows=[]
    for dataset in lock['datasets']:
        print('Opening clean budget roles',dataset,flush=True)
        _,schema,roles=open_roles(Path('data/primary')/dataset/'protocol_v2',('fit','reference','calibration','final'))
        fit=roles['fit'];ref=roles['reference']['X'];cal=roles['calibration']['X'];final=roles['final']
        bm=final['y']==0;xb=final['X'][bm];xm=final['X'][~bm]
        for seed in lock['seeds']:
            cells=sorted((Path('outputs/primary')/dataset/'protocol_v2'/f'seed_{seed}').glob('*/rate_*'))
            rng=np.random.default_rng(seed)
            byclass=[rng.permutation(np.flatnonzero(fit['y']==label)) for label in (0,1)]
            for budget in budgets:
                dest=root/dataset/f'seed_{seed}'/f'n_{budget}';dest.mkdir(parents=True,exist_ok=True)
                rp=dest/'result.json'
                if rp.exists():
                    r=read_json(rp)
                    if any(sha256(p)!=h for p,h in r['sources'].items()):raise ValueError('Budget source changed')
                    if r['score_hash']!=sha256(dest/'scores.npz'):raise ValueError('Budget cache changed')
                    rows.extend(r['rows']);continue
                started=time.perf_counter();chosen=np.sort(np.r_[byclass[0][:budget//2],byclass[1][:budget//2]])
                np.save(dest/'fit_ids.npy',fit['ids'][chosen],allow_pickle=False)
                if budget==200000:
                    sp=cells[0].parents[1]/'clean.txt';bp=cells[0]/'bundle_full/view_behavioral.txt'
                    shadow=lgb.Booster(model_file=str(sp));beh=lgb.Booster(model_file=str(bp))
                else:
                    sp=dest/'shadow.txt';bp=dest/'behavioral.txt'
                    print('Training budget',dataset,seed,budget,flush=True)
                    subset=fit['X'][chosen]
                    shadow=train(subset,fit['y'][chosen],sp,execution,seed,schema=schema)
                    beh=train(subset,fit['y'][chosen],bp,execution,seed,view='behavioral',schema=schema)
                    del subset;gc.collect()
                sources={str(sp):sha256(sp),str(bp):sha256(bp)}
                pb={name:beh.predict(x[:,schema.views['behavioral']],num_threads=4) for name,x in [('ref',ref),('cal',cal),('benign',xb)]}
                cp={name:shadow.predict(x,num_threads=4) for name,x in [('cal',cal),('benign',xb)]}
                local=[];cache={}
                for ci,cell in enumerate(cells):
                    r=read_json(cell/'result.json');sources[str(cell/'result.json')]=sha256(cell/'result.json')
                    with np.load(cell/'paired_predictions.npz',allow_pickle=False) as z:a={k:v.copy() for k,v in z.items()}
                    if not np.array_equal(a['malware_ids'].astype(str),final['ids'][~bm].astype(str)):raise ValueError('Budget IDs mismatch')
                    main_model=lgb.Booster(model_file=str(cell/'bundle_full/main.txt'))
                    main_p={name:main_model.predict(x,num_threads=4) for name,x in [('ref',ref),('cal',cal),('benign',xb)]}
                    with np.load(cell/'bundle_full/reference.npz',allow_pickle=False) as z:m3_ref=z['rank_M3_view_mass'].copy()
                    with np.load(Path('outputs/revision_2026_10_13/supplement')/dataset/cell.relative_to(Path('outputs/primary')/dataset/'protocol_v2')/'calibration_scores.npz',allow_pickle=False) as z:
                        m3_cal=z['M3_view_mass'].copy()
                    m4_ref=np.maximum(0,pb['ref']-main_p['ref']);m4_cal=np.maximum(0,pb['cal']-main_p['cal'])
                    m4_n=np.maximum(0,pb['benign']-main_p['benign'])
                    trigger=VectorTrigger(**read_json(cell/'attack.json')['trigger']);xt=trigger.apply(xm,schema)
                    m4_p=np.maximum(0,beh.predict(xt[:,schema.views['behavioral']],num_threads=4)-a['triggered_main_p'])
                    shadow_p=np.maximum(0,shadow.predict(xt,num_threads=4)-a['triggered_main_p'])
                    shadow_n=np.maximum(0,cp['benign']-main_p['benign']);shadow_cal=np.maximum(0,cp['cal']-main_p['cal'])
                    full_cal=(rank(m3_ref,m3_cal)+rank(m4_ref,m4_cal))/2
                    full_p=(rank(m3_ref,a['full_trigger_M3_view_mass'])+rank(m4_ref,m4_p))/2
                    full_n=(rank(m3_ref,a['full_benign_M3_view_mass'])+rank(m4_ref,m4_n))/2
                    if budget==200000:
                        np.testing.assert_allclose(full_p,a['full_trigger_X_primary_full'],rtol=0,atol=1e-12)
                        np.testing.assert_allclose(full_n,a['full_benign_X_primary_full'],rtol=0,atol=1e-12)
                    groups=attack_groups(a['clean_malware_p'],a['triggered_main_p'],a['clean_trigger_p'])
                    for method,ps,ns,cs in [('M4_prob_gap',m4_p,m4_n,m4_cal),('X_primary_full',full_p,full_n,full_cal),('Shadow',shadow_p,shadow_n,shadow_cal)]:
                        tau=threshold(cs,.01);m=revised_metrics(ps,ns,tau,groups);low=low_fpr_metrics(ps[groups['successful_eligible']],ns)
                        local.append(dict(dataset=dataset,seed=seed,family=r['family'],rate=r['rate'],budget=budget,
                            confirmed=r['independently_confirmed_strong_and_stealth'],method=method,
                            recall=m['recall_successful_eligible']['rate'],fpr=m['benign_fpr']['rate'],
                            n_successful=m['recall_successful_eligible']['n'],detected=m['recall_successful_eligible']['count'],
                            fp=m['benign_fpr']['count'],n_benign=len(ns),low_fpr_tpr=low['tpr'],low_fpr_fpr=low['fpr'],
                            standardized_partial_auc=low['standardized_partial_auc']))
                        for k,v in [('positive',ps),('negative',ns),('calibration',cs)]:cache[f'cell{ci}_{method}_{k}']=v
                    del main_model,xt,a;gc.collect()
                np.savez_compressed(dest/'scores.npz',**cache)
                write_json(rp,dict(rows=local,sources=sources,score_hash=sha256(dest/'scores.npz'),
                    fit_ids_hash=sha256(dest/'fit_ids.npy'),elapsed_seconds=time.perf_counter()-started))
                rows.extend(local);print('Completed budget',dataset,seed,budget,time.perf_counter()-started,flush=True)
                del shadow,beh,cache;gc.collect()
        del roles,fit,final,xb,xm;gc.collect()
    pd.DataFrame(rows).to_csv(root/'results.csv',index=False)


if __name__=='__main__':main()
