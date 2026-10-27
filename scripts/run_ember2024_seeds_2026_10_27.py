"""Two predeclared seed repetitions; fixed selector and unchanged attack criteria."""
import sys
import gc
import time
from pathlib import Path
from dataclasses import asdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
import joblib
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.primary_workflow import open_roles
from xsentinel.experiment import train
from xsentinel.attacks.primary import VectorTrigger,poison_primary
from xsentinel.attacks.selectors import select_primary
from xsentinel.attacks.screen import screen_primary
from xsentinel.revision.reviewer_core import CoreScorer
from xsentinel.revision.analysis import attack_groups,revised_metrics
from xsentinel.revision.low_fpr import low_fpr_metrics


def main():
    out=Path('outputs/teacher_revision_2026_10_27/ember2024_seeds_v2');out.mkdir(parents=True,exist_ok=True)
    protocol=read_json('configs/primary_protocol.json'); execution=read_json('configs/primary_execution.json')
    old=Path('outputs/primary/EMBER2024/protocol_v2/seed_17/spread_structural/rate_0.02/result.json')
    selector=read_json(old)['selector']
    lock=dict(version='additional-seeds-v2',dataset='EMBER2024',seeds=[59,71],family='spread_structural',rate=.02,
              selector=selector, selector_source_sha256=sha256(old),
              roles_sha256=sha256('data/primary/EMBER2024/protocol_v2/roles.json'),
              protocol_sha256=sha256('configs/primary_protocol.json'),execution_sha256=sha256('configs/primary_execution.json'),
              code_sha256={str(p):sha256(p) for p in [Path(__file__),Path('src/xsentinel/revision/reviewer_core.py')]},
              policy='Fixed original selector/rules; no reselection or seed substitution; both failures and passes retained',
              scope='Additional models on previously observed fixed pools; not a new independent dataset',
              scoring='Exact primary core formulas + SHAP-IF + Shadow; STRIP/M5 not evaluated in this extension',
              batching='Reference500 and calibration2000 scored whole; final batches128, matching original primary execution',
              supersedes='v1 used256 batches for calibration/final; v2 fixes batching only, preserves trained models/triggers',
              view_training='Only Behavioral model is needed by primary Full formula; unused Structural/Metadata models not retrained')
    lp=out/'protocol.json'
    if lp.exists() and read_json(lp)!=lock:raise ValueError('Changed seed protocol')
    write_json(lp,lock)
    names=('fit','selection','development','confirmation','reference','calibration','final')
    print('Verifying EMBER2024 roles for new seeds',flush=True)
    _,schema,roles=open_roles(Path('data/primary/EMBER2024/protocol_v2'),names)
    for i,a in enumerate(names):
        for b in names[i+1:]:
            if set(roles[a]['ids']) & set(roles[b]['ids']):raise ValueError('Role overlap')
    fit=roles['fit']; summary=[]
    for seed in lock['seeds']:
        dest=out/f'seed_{seed}';dest.mkdir(exist_ok=True)
        if (dest/'result.json').exists():
            r=read_json(dest/'result.json')
            if any(sha256(dest/k)!=v for k,v in r['artifacts'].items()):raise ValueError('Seed checkpoint changed')
            summary.append(r);continue
        started=time.perf_counter()
        print('Training new clean model',seed,flush=True)
        clean=train(fit['X'],fit['y'],dest/'clean.txt',execution,seed,schema=schema)
        ap=dest/'attack.json'
        if ap.exists():
            trigger=VectorTrigger(**read_json(ap)['trigger'])
        else:
            print('Selecting trigger on selection only',seed,selector,flush=True)
            trigger,diagnostics=select_primary(clean,roles['selection']['X'],schema=schema,
                family='spread_structural',profile='feature_restricted',geometry={'structural':10},selector=selector)
            write_json(ap,dict(trigger=asdict(trigger),diagnostics=diagnostics,seed=seed,rate=.02,selector=selector))
        print('Training new poisoned model',seed,flush=True)
        xp,poison_ids,info=poison_primary(fit['X'],fit['y'],trigger,.02,seed,denominator='all_fit',schema=schema)
        write_json(dest/'poison_manifest.json',dict(**info,source_ids=fit['ids'][poison_ids].tolist()))
        model=train(xp,fit['y'],dest/'poisoned.txt',execution,seed,schema=schema)
        del xp;gc.collect()
        screens={}
        for name in ('development','confirmation'):
            role=roles[name]; xm=role['X'][role['y']==1]; xt=trigger.apply(xm,schema)
            cp=clean.predict(role['X'],num_threads=4); pp=model.predict(role['X'],num_threads=4)
            ct=clean.predict(xt,num_threads=4); pt=model.predict(xt,num_threads=4)
            screens[name]=screen_primary(cp,pp,ct,pt,role['y'],protocol['attack_screen'])
            np.savez_compressed(dest/(name+'_predictions.npz'),ids=role['ids'],y=role['y'],clean=cp,poisoned=pp,clean_trigger=ct,poisoned_trigger=pt)
            write_json(dest/(name+'.json'),screens[name])
            print(seed,name,'pass',screens[name]['strong_and_stealth'],'gain',screens[name]['paired_gain'],flush=True)
        print('Training Behavioral model',seed,flush=True)
        beh=train(fit['X'],fit['y'],dest/'behavioral.txt',execution,seed,view='behavioral',schema=schema)
        scorer=CoreScorer(model,schema,beh,clean,use_if=True).fit_reference(roles['reference']['X'])
        cal=scorer.calibrate(roles['calibration']['X']);joblib.dump(scorer.forest,dest/'if.joblib')
        write_json(dest/'thresholds.json',scorer.thresholds)
        final=roles['final'];bm=final['y']==0;xm=final['X'][~bm];xt=trigger.apply(xm,schema)
        print('Scoring final',seed,flush=True)
        ns,_=scorer.score(final['X'][bm]);ps,pp=scorer.score(xt)
        original=model.predict(xm,num_threads=4);cp=clean.predict(xm,num_threads=4);ct=clean.predict(xt,num_threads=4)
        groups=attack_groups(cp,pp,ct)
        metrics={k:revised_metrics(ps[k],ns[k],scorer.thresholds[k],groups) for k in ps}
        low={k:{g:low_fpr_metrics(ps[k][mask],ns[k]) for g,mask in groups.items()} for k in ps}
        np.savez_compressed(dest/'scores.npz',**{'positive_'+k:v for k,v in ps.items()},
            **{'negative_'+k:v for k,v in ns.items()},**{'calibration_'+k:v for k,v in cal.items()},
            malware_ids=final['ids'][~bm],benign_ids=final['ids'][bm],clean_original=cp,clean_trigger=ct,
            poisoned_trigger=pp,poisoned_original=original)
        files=['clean.txt','poisoned.txt','behavioral.txt','if.joblib','attack.json','poison_manifest.json',
               'development_predictions.npz','confirmation_predictions.npz','scores.npz','thresholds.json']
        result=dict(dataset='EMBER2024',seed=seed,family='spread_structural',rate=.02,
            passes_original_screening_criteria=all(s['strong_and_stealth'] for s in screens.values()),
            screens=screens,metrics=metrics,low_fpr=low,elapsed_seconds=time.perf_counter()-started,
            artifacts={n:sha256(dest/n) for n in files},scope=lock['scope'])
        write_json(dest/'result.json',result);summary.append(result)
        write_json(out/'completion.json',dict(planned_seeds=lock['seeds'],completed=[r['seed'] for r in summary],
            confirmed=[r['seed'] for r in summary if r['passes_original_screening_criteria']]))
        print('Completed seed',seed,result['elapsed_seconds'],flush=True)
        del scorer,clean,beh,model,ps,ns,xt
        gc.collect()
    rows=[]
    for r in summary:
        for method,m in r['metrics'].items():
            rows.append(dict(seed=r['seed'],confirmed=r['passes_original_screening_criteria'],method=method,
                recall=m['recall_successful_eligible']['rate'],fpr=m['benign_fpr']['rate'],
                n_successful=m['recall_successful_eligible']['n'],detected=m['recall_successful_eligible']['count'],
                confirmation_gain=r['screens']['confirmation']['paired_gain']))
    pd.DataFrame(rows).to_csv(out/'ember2024_seed_runs.csv',index=False)


if __name__=='__main__':main()
