"""Reference-only raw/rarity comparators, frozen primary masks, resumable cells."""
import sys,argparse,time,gc
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.primary_workflow import open_roles
from xsentinel.baselines.raw_feature_outlier import RawFeatureOutlier
from xsentinel.baselines.rarity_score import RarityScore
from xsentinel.attacks.primary import VectorTrigger
from xsentinel.revision.analysis import attack_groups
from xsentinel.revision.low_fpr import low_fpr_metrics
from xsentinel.revision.calibration_v2 import tolerance_threshold,exact_interval
from xsentinel.detection.calibration import threshold
from analyze_fusion_overlap import ROOT,cells,csv_out

def evaluate(base, name, positive, negative, calibration, mask):
    low=low_fpr_metrics(positive[mask],negative);rows=[]
    for policy,tau in [('empirical_calibration',threshold(calibration)),('tolerance_pointwise',tolerance_threshold(calibration)['threshold'])]:
        fp=int((negative>tau).sum());tp=int((positive[mask]>tau).sum());n=int(mask.sum());lo,hi=exact_interval(fp,len(negative))
        rows.append({**base,'method':name,'policy':policy,'tau':tau,'fp':fp,'n_benign':len(negative),'fpr':fp/len(negative),
            'fpr_ci_low':lo,'fpr_ci_high':hi,'tp':tp,'n_successful':n,'recall':tp/n if n else None,
            'low_fpr_tpr':low['tpr'],'low_fpr_fpr':low['fpr'],'standardized_partial_auc':low['standardized_partial_auc']})
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true');args=p.parse_args()
    root=ROOT/'raw_baselines';root.mkdir(parents=True,exist_ok=True)
    code=[Path(__file__),Path('src/xsentinel/baselines/raw_feature_outlier.py'),Path('src/xsentinel/baselines/rarity_score.py')]
    protocol=dict(code={str(p):sha256(p) for p in code},fit='500 benign reference only',calibration='2000 original benign, retrospective reuse',
        preprocessing='signed log1p then reference standardization; constant reference dimensions dropped for distance models',
        topk='32 largest reference log-variances, index-stable ties; raw only',
        methods=['raw_if_full','raw_lof_full','raw_knn_full','raw_if_top32','raw_lof_top32','raw_knn_top32','rarity'],
        rarity='exact categories <=20 distinct incl constants; otherwise 20 quantile intervals with tails; Laplace1; mean top10 surprisal',
        seed=20261030,cohort='successful eligible fixed original classifier masks',scope='Observed benchmark, not independent validation')
    lock=root/'protocol.json'
    if lock.exists() and read_json(lock)!=protocol:raise ValueError('Protocol changed')
    write_json(lock,protocol);allrows=[]
    for dataset in ['EMBER2018','EMBER2024']:
        _,schema,roles=open_roles(Path('data/primary')/dataset/'protocol_v2',('reference','calibration','final'))
        ref=roles['reference']['X'];cal=roles['calibration']['X'];f=roles['final'];bm=f['y']==0
        models={f'raw_{m}_{tag}':RawFeatureOutlier(m,k).fit(ref) for tag,k in [('full',None),('top32',32)] for m in ['if','lof','knn']}
        models['rarity']=RarityScore().fit(ref)
        print('Fit reference baselines',dataset,flush=True)
        shared={name:(model.score(cal),model.score(f['X'][bm])) for name,model in models.items()}
        for path in [p for p in cells() if p.parts[2]==dataset][:1 if args.pilot else 27]:
            r=read_json(path);cell=path.parent;dest=root/dataset/cell.relative_to(Path('outputs/primary')/dataset/'protocol_v2');dest.mkdir(parents=True,exist_ok=True)
            rp=dest/'result.json'
            if rp.exists():
                previous=read_json(rp)
                if previous['source_hash']!=sha256(path) or previous['score_hash']!=sha256(dest/'scores.npz'):raise ValueError('Resume provenance mismatch')
                allrows.extend(previous['rows']);continue
            start=time.perf_counter()
            with np.load(cell/'paired_predictions.npz',allow_pickle=False) as z:a={k:v.copy() for k,v in z.items()}
            assert np.array_equal(a['malware_ids'].astype(str),f['ids'][~bm].astype(str))
            assert np.array_equal(a['benign_ids'].astype(str),f['ids'][bm].astype(str))
            groups=attack_groups(a['clean_malware_p'],a['triggered_main_p'],a['clean_trigger_p'])
            trigger=VectorTrigger(**read_json(cell/'attack.json')['trigger']);xt=trigger.apply(f['X'][~bm],schema)
            base={k:r[k] for k in ['dataset','seed','family','rate']};base['confirmed']=r['independently_confirmed_strong_and_stealth']
            rows=[];scores={'malware_ids':a['malware_ids'],'benign_ids':a['benign_ids']}
            for name,model in models.items():
                cs,ns=shared[name];ps=model.score(xt)
                assert len(ps)==len(a['malware_ids']) and np.isfinite(ps).all()
                rows.extend(evaluate(base,name,ps,ns,cs,groups['successful_eligible']))
                scores.update({name+'_calibration':cs,name+'_benign':ns,name+'_trigger':ps})
            np.savez_compressed(dest/'scores.npz',**scores)
            write_json(rp,dict(rows=rows,source_hash=sha256(path),score_hash=sha256(dest/'scores.npz'),seconds=time.perf_counter()-start))
            allrows.extend(rows);print('Completed raw baselines',base,time.perf_counter()-start,flush=True)
        del roles,models,shared;gc.collect()
    csv_out(root/('pilot.csv' if args.pilot else 'raw_baseline_per_run.csv'),allrows)
    write_json(root/('pilot_complete.json' if args.pilot else 'complete.json'),dict(cells=len(allrows)//14,rows=len(allrows)))

if __name__=='__main__':main()
