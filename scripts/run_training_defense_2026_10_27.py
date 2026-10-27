"""Resource-rich training sanitization context; fixed two-cell supplementary study."""
import sys
import gc
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.ensemble import IsolationForest
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.primary_workflow import open_roles
from xsentinel.attacks.primary import VectorTrigger,poison_primary
from xsentinel.baselines.scores import contributions
from xsentinel.experiment import train,performance_from_predictions
from xsentinel.revision.training_filters import random_removal_control,CONTROL_SEED


def main():
    root=Path('outputs/teacher_revision_2026_10_27/training_defense_v2');root.mkdir(parents=True,exist_ok=True)
    execution=read_json('configs/primary_execution.json')
    lock=dict(version='training-sanitization-v2',cells='seed17/spread_structural/rate0.02 on both datasets',
        source='https://www.usenix.org/system/files/sec21-severi.pdf',
        relation='Inspired reduced-feature IF sanitization; not an exact replication of Severi Table3',
        features='Top32 mean-absolute native SHAP from suspicious model on500 trusted benign reference, before final',
        fit='IF on potentially poisoned benign-labeled training samples, restricted to32 selected raw features',
        forest=dict(n_estimators=200,max_samples=256,random_state=17,n_jobs=4,contamination='auto'),
        removal='Exactly5% of benign-labeled fit, ranked by -score_samples; score ties broken by source ID',
        control=f'Uniform random removal of same benign sample count, independent rng{CONTROL_SEED}',
        supersedes='v1 random control shared PCG64 seed17 with poison selection and is invalid; v2 fixes this coupling, retains IF mask',
        retraining='Original500-round classifier parameters/seed17 on retained training data',
        oracle_policy='Poison IDs used ONLY to report removed poisons after mask is fixed, never to select mask',
        scope='Two-cell supplementary training-access defense; previously observed final; not comparable access to per-input Reduced',
        code_sha256=sha256(__file__),control_code_sha256=sha256('src/xsentinel/revision/training_filters.py'),
        execution_sha256=sha256('configs/primary_execution.json'))
    lp=root/'protocol.json'
    if lp.exists() and read_json(lp)!=lock:raise ValueError('Training defense protocol changed')
    write_json(lp,lock);rows=[]
    for dataset in ('EMBER2018','EMBER2024'):
        dest=root/dataset;dest.mkdir(exist_ok=True)
        if (dest/'result.json').exists():
            r=read_json(dest/'result.json')
            if any(sha256(dest/p)!=h for p,h in r['artifacts'].items()):raise ValueError('Defense checkpoint mismatch')
            rows.extend(r['rows']);continue
        print('Opening training-defense roles',dataset,flush=True)
        _,schema,roles=open_roles(Path('data/primary')/dataset/'protocol_v2',('fit','reference','final'))
        fit=roles['fit'];final=roles['final']
        cell=Path('outputs/primary')/dataset/'protocol_v2/seed_17/spread_structural/rate_0.02'
        original=lgb.Booster(model_file=str(cell/'bundle_full/main.txt'))
        clean=lgb.Booster(model_file=str(cell.parents[1]/'clean.txt'))
        trigger=VectorTrigger(**read_json(cell/'attack.json')['trigger'])
        importance=np.abs(contributions(original,roles['reference']['X'],schema=schema)).mean(axis=0)
        columns=np.lexsort((np.arange(schema.dim),-importance))[:32]
        xp,poison_indices,_=poison_primary(fit['X'],fit['y'],trigger,.02,17,denominator='all_fit',schema=schema)
        if fit['ids'][poison_indices].tolist()!=read_json(cell/'attack.json')['poison_source_ids']:
            raise ValueError('Reconstructed poison IDs differ from original experiment')
        del fit['X'];gc.collect()
        benign_indices=np.flatnonzero(fit['y']==0);xb=xp[np.ix_(benign_indices,columns)]
        forest=IsolationForest(**lock['forest']).fit(xb)
        score=-forest.score_samples(xb); count=int(np.floor(.05*len(benign_indices)))
        order=np.lexsort((fit['ids'][benign_indices].astype(str),-score))
        chosen=dict(IF_top32=benign_indices[order[:count]],
                    random_control=random_removal_control(benign_indices,count))
        previous=Path('outputs/teacher_revision_2026_10_27/training_defense')/dataset/'selection.npz'
        if previous.exists():
            with np.load(previous,allow_pickle=False) as old:
                np.testing.assert_array_equal(fit['ids'][chosen['IF_top32']],old['IF_top32_removed_ids'])
        np.savez_compressed(dest/'selection.npz',columns=columns,benign_ids=fit['ids'][benign_indices],score=score,
            **{k+'_removed_ids':fit['ids'][v] for k,v in chosen.items()})
        del xb,forest;gc.collect()
        malware=final['y']==1;xm=final['X'][malware];xt=trigger.apply(xm,schema)
        cp=clean.predict(xm,num_threads=4);ct=clean.predict(xt,num_threads=4);eligible=cp>=.5
        baseline=original.predict(xt,num_threads=4);original_utility=performance_from_predictions(original.predict(final['X'],num_threads=4),final['y'],.5)
        local=[]
        for method,removed in chosen.items():
            keep=np.ones(len(fit['y']),dtype=bool);keep[removed]=False
            print('Retraining defense',dataset,method,flush=True);started=time.perf_counter()
            model=train(xp[keep],fit['y'][keep],dest/(method+'.txt'),execution,17,schema=schema)
            p=model.predict(xt,num_threads=4); utility=performance_from_predictions(model.predict(final['X'],num_threads=4),final['y'],.5)
            np.savez_compressed(dest/(method+'_predictions.npz'),malware_ids=final['ids'][malware],
                clean_original=cp,clean_trigger=ct,before=baseline,after=p)
            poisons_removed=int(np.isin(removed,poison_indices).sum())
            row=dict(dataset=dataset,method=method,seed=17,family='spread_structural',rate=.02,
                removed=int(len(removed)),poisons_total=len(poison_indices),poisons_removed=poisons_removed,
                benign_unpoisoned_removed=len(removed)-poisons_removed,n_eligible=int(eligible.sum()),
                asr_before=float(np.mean(baseline[eligible]<.5)),asr_after=float(np.mean(p[eligible]<.5)),
                accuracy_before=original_utility['accuracy'],accuracy_after=utility['accuracy'],
                elapsed_seconds=time.perf_counter()-started)
            local.append(row);print('Defense completed',row,flush=True)
            del model;gc.collect()
        files=['selection.npz']+[m+s for m in chosen for s in ('.txt','_predictions.npz')]
        write_json(dest/'result.json',dict(rows=local,scope=lock['scope'],artifacts={p:sha256(dest/p) for p in files},
            source_result_sha256=sha256(cell/'result.json')))
        rows.extend(local);del roles,xp,fit,final,clean,original,xm,xt;gc.collect()
    pd.DataFrame(rows).to_csv(root/'results.csv',index=False)


if __name__=='__main__':main()
