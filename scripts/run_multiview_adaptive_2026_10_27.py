"""Bounded multiview vector-only robustness evaluation on frozen research models."""
import sys
import gc
import time
import hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
import lightgbm as lgb
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.primary_workflow import open_roles
from xsentinel.detection.detector import Detector
from xsentinel.attacks.primary import VectorTrigger
from xsentinel.revision.scoring import core_scores


def main():
    root=Path('outputs/teacher_revision_2026_10_27/adaptive_multiview');root.mkdir(parents=True,exist_ok=True)
    lock=dict(version='multiview-vector-v1',samples=100,queries_per_input=32,extra_coordinates_per_view=8,
              source='First100 lexicographically sorted final malware source IDs, outcome-blind',
              proposal='One empirical benign selection coordinate per view per query; original trigger retained',
              views=['structural','behavioral','metadata'],threshold='Frozen primary X-R threshold',
              knowledge='Main malware probability and X-R score only; no Full/Shadow or true labels in query objective',
              objective='Joint p_main<0.5 and X-R<=tau; minimize normalized positive violations',
              cohort='All24 previously confirmed original cells, including9Cross; no model or trigger retraining',
              scope='Exploratory vector stress only; no binary realizability claim; final IDs previously observed',
              code_sha256=sha256(__file__))
    if (root/'protocol.json').exists() and read_json(root/'protocol.json')!=lock:raise ValueError('Changed adaptive protocol')
    write_json(root/'protocol.json',lock)
    results=[]
    for dataset in ('EMBER2018','EMBER2024'):
        print('Loading adaptive roles',dataset,flush=True)
        _,schema,roles=open_roles(Path('data/primary')/dataset/'protocol_v2',('selection','final'))
        f=roles['final']; mi=np.flatnonzero(f['y']==1); chosen=mi[np.argsort(f['ids'][mi].astype(str))[:100]]
        xm=f['X'][chosen]; ids=f['ids'][chosen]
        benign=roles['selection']['X'][roles['selection']['y']==0]
        variable={v:idx[np.ptp(benign[:,idx],axis=0)>0] for v,idx in schema.views.items()}
        for cell in sorted((Path('outputs/primary')/dataset/'protocol_v2').glob('seed_*/*/rate_*')):
            r=read_json(cell/'result.json')
            if not r['independently_confirmed_strong_and_stealth']:continue
            dest=root/dataset/cell.relative_to(Path('outputs/primary')/dataset/'protocol_v2');dest.mkdir(parents=True,exist_ok=True)
            rp=dest/'result.json'
            source_hash=sha256(cell/'result.json')
            if rp.exists():
                old=read_json(rp)
                if old['source_sha256']!=source_hash or old['scores_sha256']!=sha256(dest/'scores.npz'):raise ValueError('Changed adaptive checkpoint')
                results.append(old);continue
            for name,digest in r['artifact_sha256'].items():
                if sha256(cell/name)!=digest:raise ValueError('Changed frozen artifact')
            d=Detector.load(cell/'bundle_full'); clean=lgb.Booster(model_file=str(cell.parents[1]/'clean.txt'))
            trigger=VectorTrigger(**read_json(cell/'attack.json')['trigger']); original=trigger.apply(xm,schema);best=original.copy()
            available={v:np.array([j for j in cols if j not in trigger.indices],dtype=int) for v,cols in variable.items()}
            if any(not len(x) for x in available.values()):raise ValueError('Missing multiview search coordinates')
            tau=d.thresholds['X_primary_reduced']; rng=np.random.default_rng(int(hashlib.sha256(str(dest).encode()).hexdigest()[:8],16))
            touched=[{v:set() for v in available} for _ in range(len(xm))]
            def query(z):
                ss,_,details,_=d.predict_selected(z,'X_primary_reduced')
                p=details['malware_probability'];s=ss['X_primary_reduced']
                c=np.maximum(p-.5,0)/.5+np.maximum(s-tau,0)/max(1-tau,1e-9)+(p>=.5)*1e-12
                return c,p,s
            start=time.perf_counter();cost,p,s=query(best);p0=p.copy();s0=s.copy();queries=np.ones(len(xm),dtype=int)
            for step in range(1,32):
                active=np.flatnonzero(~((p<.5)&(s<=tau)))
                if not len(active):break
                proposal=best[active].copy(); proposed=[]
                for k,i in enumerate(active):
                    donor=int(rng.integers(len(benign))); columns={}
                    for view,pool in available.items():
                        options=pool if len(touched[i][view])<8 else np.array(sorted(touched[i][view]))
                        j=int(rng.choice(options));proposal[k,j]=benign[donor,j];columns[view]=j
                    proposed.append(columns)
                cc,pp,ss=query(proposal);queries[active]+=1
                accept=(cc<cost[active])|((cc==cost[active])&(pp<p[active]))
                for k in np.flatnonzero(accept):
                    i=active[k]
                    for view,j in proposed[k].items():touched[i][view].add(j)
                chosen_accept=active[accept]
                best[chosen_accept]=proposal[accept];cost[chosen_accept]=cc[accept];p[chosen_accept]=pp[accept];s[chosen_accept]=ss[accept]
            if not np.array_equal(best[:,trigger.indices],original[:,trigger.indices]):raise ValueError('Original trigger changed')
            for view,idx in schema.views.items():
                if np.any(np.sum(best[:,idx]!=original[:,idx],axis=1)>8):raise ValueError('Coordinate budget exceeded')
            if queries.max()>32:raise ValueError('Query budget exceeded')
            before,_=core_scores(d,original);after,_=core_scores(d,best)
            np.testing.assert_allclose(before['X_primary_reduced'],s0,rtol=0,atol=1e-12)
            np.testing.assert_allclose(after['X_primary_reduced'],s,rtol=0,atol=1e-12)
            clean_original=clean.predict(xm,num_threads=4);ct0=clean.predict(original,num_threads=4);ct1=clean.predict(best,num_threads=4)
            eligible=clean_original>=.5;initial=(p0<.5)&(s0<=tau);end=(p<.5)&(s<=tau)
            np.savez_compressed(dest/'scores.npz',ids=ids,queries=queries,main_before=p0,main_after=p,
                clean_original=clean_original,clean_trigger_before=ct0,clean_trigger_after=ct1,
                **{'before_'+k:v for k,v in before.items()},**{'after_'+k:v for k,v in after.items()},
                changed_count=np.sum(best!=original,axis=1))
            row=dict(dataset=dataset,seed=r['seed'],family=r['family'],rate=r['rate'],n=len(xm),
                n_eligible=int(eligible.sum()),start_joint_success=int(np.sum(initial&eligible)),
                end_joint_success=int(np.sum(end&eligible)),new_joint_success=int(np.sum(end&~initial&eligible)),
                start_main_evasion=int(np.sum((p0<.5)&eligible)),end_main_evasion=int(np.sum((p<.5)&eligible)),
                max_queries=int(queries.max()),mean_queries=float(queries.mean()),
                changed_columns_by_view={v:int(np.sum(np.any(best[:,idx]!=original[:,idx],axis=0))) for v,idx in schema.views.items()},
                source_sha256=source_hash,scores_sha256=sha256(dest/'scores.npz'),elapsed_seconds=time.perf_counter()-start)
            write_json(rp,row);results.append(row)
            print('Adaptive completed',dataset,r['seed'],r['family'],r['rate'],'joint',row['start_joint_success'],'->',row['end_joint_success'],flush=True)
            del d,clean,best,original;gc.collect()
        del roles;gc.collect()
    write_json(root/'results.json',results)
    pd.DataFrame([{k:v for k,v in r.items() if k!='changed_columns_by_view'} for r in results]).to_csv(root/'results.csv',index=False)


if __name__=='__main__':main()
