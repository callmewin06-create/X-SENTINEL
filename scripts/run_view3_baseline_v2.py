"""Three-dimensional normalized signed view-SHAP Isolation Forest comparator."""
import sys,argparse,time,gc
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import lightgbm as lgb
from sklearn.ensemble import IsolationForest
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.primary_workflow import open_roles
from xsentinel.baselines.scores import contributions
from xsentinel.attacks.primary import VectorTrigger
from xsentinel.revision.analysis import attack_groups
from analyze_fusion_overlap import ROOT,cells,csv_out
from run_raw_baselines_v2 import evaluate

def view_vector(model,x,schema):
    chunks=[]
    for start in range(0,len(x),256):
        phi=contributions(model,x[start:start+256],schema=schema)
        total=np.abs(phi).sum(axis=1)
        net=np.column_stack([phi[:,schema.views[v]].sum(axis=1) for v in ['structural','behavioral','metadata']])
        chunks.append(np.divide(net,total[:,None],out=np.zeros_like(net),where=total[:,None]>1e-9))
    return np.concatenate(chunks) if chunks else np.empty((0,3))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pilot',action='store_true')
    parser.add_argument('--shard',type=int,default=0);parser.add_argument('--shards',type=int,default=1);args=parser.parse_args()
    if not 0 <= args.shard < args.shards:raise ValueError('Invalid shard')
    root=ROOT/'view3';root.mkdir(parents=True,exist_ok=True)
    protocol=dict(method='IF on 3 signed view SHAP sums / total absolute SHAP; zero vector if total <=1e-9',
        view_order=['structural','behavioral','metadata'],fit_n=500,n_estimators=200,seed=20261030,
        scope='Retrospective original benchmark; fixed original successful-eligible mask',code_sha256=sha256(__file__))
    lock=root/'protocol.json'
    if lock.exists() and read_json(lock)!=protocol:raise ValueError('Protocol changed')
    write_json(lock,protocol);rows=[]
    for ds in ['EMBER2018','EMBER2024']:
        _,schema,roles=open_roles(Path('data/primary')/ds/'protocol_v2',('reference','calibration','final'))
        f=roles['final'];bm=f['y']==0
        selected=[p for i,p in enumerate(cells()) if p.parts[2]==ds and i%args.shards==args.shard]
        for path in selected[:1 if args.pilot else len(selected)]:
            r=read_json(path);cell=path.parent;dest=root/ds/cell.relative_to(Path('outputs/primary')/ds/'protocol_v2');dest.mkdir(parents=True,exist_ok=True)
            rp=dest/'result.json'
            if rp.exists():
                old=read_json(rp)
                if old['source_hash']!=sha256(path) or old['score_hash']!=sha256(dest/'scores.npz'):raise ValueError('View3 checkpoint mismatch')
                rows.extend(old['rows']);continue
            start=time.perf_counter();print('Starting view3',ds,cell.name,r['seed'],r['family'],flush=True)
            model=lgb.Booster(model_file=str(cell/'bundle_full/main.txt'))
            with np.load(cell/'paired_predictions.npz',allow_pickle=False) as z:a={k:v.copy() for k,v in z.items()}
            assert np.array_equal(a['malware_ids'].astype(str),f['ids'][~bm].astype(str))
            assert np.array_equal(a['benign_ids'].astype(str),f['ids'][bm].astype(str))
            mask=attack_groups(a['clean_malware_p'],a['triggered_main_p'],a['clean_trigger_p'])['successful_eligible']
            refs=view_vector(model,roles['reference']['X'],schema)
            forest=IsolationForest(n_estimators=200,random_state=20261030,n_jobs=4).fit(refs)
            vectors={'reference':refs,'calibration':view_vector(model,roles['calibration']['X'],schema),
                'benign':view_vector(model,f['X'][bm],schema)}
            xt=VectorTrigger(**read_json(cell/'attack.json')['trigger']).apply(f['X'][~bm],schema)
            vectors['trigger']=view_vector(model,xt,schema)
            scores={k:-forest.score_samples(v) for k,v in vectors.items() if k!='reference'}
            base={k:r[k] for k in ['dataset','seed','family','rate']};base['confirmed']=r['independently_confirmed_strong_and_stealth']
            local=evaluate(base,'View3SignedIF',scores['trigger'],scores['benign'],scores['calibration'],mask)
            np.savez_compressed(dest/'scores.npz',**scores,**{k+'_view3':v for k,v in vectors.items()},benign_ids=a['benign_ids'],malware_ids=a['malware_ids'])
            write_json(rp,dict(rows=local,source_hash=sha256(path),score_hash=sha256(dest/'scores.npz'),seconds=time.perf_counter()-start))
            rows.extend(local);print('Completed view3',base,time.perf_counter()-start,flush=True);gc.collect()
    label='pilot' if args.pilot else f'shard_{args.shard}_of_{args.shards}'
    csv_out(root/(label+'.csv'),rows)
    write_json(root/(label+'_complete.json'),dict(cells=len(rows)//2))

if __name__=='__main__':main()
