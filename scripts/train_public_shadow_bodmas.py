"""Independent public-data Shadow. No reuse of the eligibility model."""
import sys,gc,time,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
import lightgbm as lgb
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.primary_workflow import open_roles
from xsentinel.attacks.primary import VectorTrigger
from xsentinel.revision.analysis import attack_groups
from xsentinel.experiment import performance_from_predictions
from analyze_fusion_overlap import ROOT,cells,csv_out
from run_raw_baselines_v2 import evaluate

def main():
    out=ROOT/'public_shadow';out.mkdir(parents=True,exist_ok=True)
    data=Path('data/public/bodmas');meta=pd.read_csv(data/'bodmas_metadata.csv',keep_default_na=False)
    ids=meta['sha'].str.lower().to_numpy()
    invalid_id=np.array([re.fullmatch('[a-f0-9]{64}',s) is None for s in ids])
    with np.load(data/'bodmas.npz',allow_pickle=False) as z:X=z['X'];y=z['y']
    if X.shape!=(len(meta),2381) or y.shape!=(len(meta),) or not np.isin(y,[0,1]).all() or not np.isfinite(X).all():raise ValueError('BODMAS schema/labels invalid')
    if not np.array_equal(y,(meta.family!='').astype(int)):raise ValueError('Metadata label alignment mismatch')
    state,schema,roles=open_roles('data/primary/EMBER2018/protocol_v2',('calibration','final'))
    # Exclude all original roles, not only final. Public model never defines eligibility.
    excluded=set(s.lower() for values in state['ids'].values() for s in values)
    duplicate=pd.Series(ids).duplicated().to_numpy();overlap=np.array([s in excluded for s in ids])
    rejected=duplicate|overlap|invalid_id
    valid=np.flatnonzero(~rejected)
    pd.DataFrame({'source_id':ids[rejected],'duplicate':duplicate[rejected],'ember_role_overlap':overlap[rejected],
                  'invalid_sha256':invalid_id[rejected]}).to_csv(out/'public_overlap_audit.csv',index=False)
    rng=np.random.default_rng(20261030);parts=[rng.permutation(valid[y[valid]==c]) for c in (0,1)]
    chosen=np.sort(np.r_[parts[0][:10000],parts[1][:10000]])
    validation=np.sort(np.r_[parts[0][10000:12500],parts[1][10000:12500]])
    if len(chosen)!=20000 or len(validation)!=5000:raise ValueError('Insufficient public labels')
    protocol=dict(version='public-shadow-bodmas-v1',budget=20000,validation_n=5000,seed=20261030,rounds=500,
        schema=schema.version,feature_compatibility='Official BODMAS states EMBER 2381 features with LIEF0.9.0; V2 only. Source-time shift remains.',
        source='https://whyisyoung.github.io/BODMAS/',sources={str(data/n):sha256(data/n) for n in ['bodmas.npz','bodmas_metadata.csv']},
        duplicate_rows=int(duplicate.sum()),ember_overlap_rows=int(overlap.sum()),invalid_sha256_rows=int(invalid_id.sum()),excluded_roles=list(state['ids']),
        independence='Public training SHA256-disjoint from every EMBER role; independent seed/model. Original eligibility unchanged.',
        calibration='Original EMBER benign calibration; retrospective benchmark, no independent certification',code_sha256=sha256(__file__))
    lock=out/'protocol.json'
    if lock.exists() and read_json(lock)!=protocol:raise ValueError('Public protocol changed')
    write_json(lock,protocol);np.savez_compressed(out/'split_ids.npz',train=ids[chosen],validation=ids[validation])
    modelpath=out/'shadow.txt'
    if not modelpath.exists():
        execution=read_json('configs/primary_execution.json');params=execution['params']|{'seed':20261030}
        print('Training independent public Shadow 20000',flush=True)
        model=lgb.train(params,lgb.Dataset(X[chosen],label=y[chosen]),num_boost_round=500)
        model.save_model(str(modelpath))
    model=lgb.Booster(model_file=str(modelpath));schema.check_model(model)
    utility=[{'pool':'BODMAS_validation',**performance_from_predictions(model.predict(X[validation],num_threads=4),y[validation],.5)}]
    del X;gc.collect()
    f=roles['final'];bm=f['y']==0;cal=roles['calibration']['X']
    final_p=model.predict(f['X'],num_threads=4);utility.append({'pool':'EMBER2018_final',**performance_from_predictions(final_p,f['y'],.5)})
    write_json(out/'public_shadow_utility.json',utility)
    cp=model.predict(cal,num_threads=4);rows=[]
    for path in [p for p in cells() if p.parts[2]=='EMBER2018']:
        r=read_json(path);cell=path.parent;dest=out/cell.relative_to(Path('outputs/primary/EMBER2018/protocol_v2'));dest.mkdir(parents=True,exist_ok=True)
        with np.load(cell/'paired_predictions.npz',allow_pickle=False) as z:a={k:v.copy() for k,v in z.items()}
        assert np.array_equal(a['malware_ids'].astype(str),f['ids'][~bm].astype(str))
        assert np.array_equal(a['benign_ids'].astype(str),f['ids'][bm].astype(str))
        main=lgb.Booster(model_file=str(cell/'bundle_full/main.txt'))
        cs=np.maximum(0,cp-main.predict(cal,num_threads=4));ns=np.maximum(0,final_p[bm]-main.predict(f['X'][bm],num_threads=4))
        xt=VectorTrigger(**read_json(cell/'attack.json')['trigger']).apply(f['X'][~bm],schema)
        ps=np.maximum(0,model.predict(xt,num_threads=4)-a['triggered_main_p'])
        mask=attack_groups(a['clean_malware_p'],a['triggered_main_p'],a['clean_trigger_p'])['successful_eligible']
        base={k:r[k] for k in ['dataset','seed','family','rate']};base['confirmed']=r['independently_confirmed_strong_and_stealth']
        rows.extend(evaluate(base,'PublicShadow20K',ps,ns,cs,mask))
        np.savez_compressed(dest/'scores.npz',calibration=cs,benign=ns,trigger=ps,malware_ids=a['malware_ids'],benign_ids=a['benign_ids'])
        print('Public Shadow evaluated',base,flush=True)
    csv_out(out/'public_shadow_per_run.csv',rows)
    write_json(out/'complete.json',dict(cells=27,model_sha256=sha256(modelpath),scope=protocol['calibration']))

if __name__=='__main__':main()
