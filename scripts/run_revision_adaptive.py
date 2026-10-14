"""Validate frozen models and post-review baselines on previously unused source IDs."""
import sys,argparse,gc,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import lightgbm as lgb
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.detection.detector import Detector
from xsentinel.baselines.scores import strip
from xsentinel.detection.calibration import threshold
from xsentinel.attacks.primary import VectorTrigger
from xsentinel.primary_workflow import open_roles
from xsentinel.revision.scoring import core_scores
from xsentinel.revision.analysis import attack_groups,revised_metrics


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['fresh','adaptive'],required=True)
    p.add_argument('--adaptive-samples',type=int,default=100);p.add_argument('--queries',type=int,default=32)
    p.add_argument('--out',default='outputs/revision_2026_10_13/adaptive_structural');args=p.parse_args(); assert args.stage=='adaptive'
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    if Path('outputs/primary').resolve() in out.resolve().parents:raise ValueError('Protected namespace')
    lock={'version':'adaptive-structural-v2','fresh_pool':'outputs/revision_2026_10_13/fresh_validation',
          'thresholds':'Original primary; new shadow/inverse thresholds from original benign calibration only',
          'selection':'No outcome-based parameter tuning or fresh confirmation reselection',
          'adaptive':{'samples':args.adaptive_samples,'queries':args.queries,'objective':'p_main<0.5 AND X-R<=old tau',
            'knowledge':'Formula and per-query probability + reduced score; no full/shadow queries',
            'space':'Restricted vector only; original trigger retained, at most 13 whitelist columns changed',
            'candidate_values':'Empirical benign selection values; no fresh final optimization values',
            'algorithm':'32 sequential coordinate proposals, fixed seed; minimize normalized positive constraint violations',
            'cohort':'Originally confirmed restricted cells only, first outcome-blind 100 fresh malware source IDs',
            'scope':'Exploratory bounded optimizer; failure does not establish adaptive robustness'},
          'code_sha256':sha256(__file__)}
    if (out/'protocol.json').exists():
        if read_json(out/'protocol.json')!=lock:raise ValueError('Protocol changed')
    else:write_json(out/'protocol.json',lock)
    results=[]
    for dataset in ('EMBER2018','EMBER2024'):
        data=Path(lock['fresh_pool'])/dataset;manifest=read_json(data/'dataset.json')
        assert all(sha256(data/k)==h for k,h in manifest['hashes'].items())
        X=np.load(data/'X.npy');y=np.load(data/'y.npy');ids=np.load(data/'ids.npy',allow_pickle=False)
        benign=X[y==0];malware=X[y==1];clean_models={}
        if args.stage=='adaptive':
            _,schema,roles=open_roles(Path('data/primary')/dataset/'protocol_v2',('selection',))
            values=roles['selection']['X'][roles['selection']['y']==0]
        for cell in sorted((Path('outputs/primary')/dataset/'protocol_v2').glob('seed_*/*/rate_*')):
            r=read_json(cell/'result.json')
            if args.stage=='adaptive' and (not r['independently_confirmed_strong_and_stealth'] or r['family']=='cross_3view_stress'):continue
            dest=out/dataset/f"seed_{r['seed']}"/r['family']/f"rate_{r['rate']}";dest.mkdir(parents=True,exist_ok=True)
            path=dest/(args.stage+'.json')
            if path.exists():
                existing=read_json(path)
                assert existing['original_result_sha256']==sha256(cell/'result.json')
                results.append(existing);print('Resumed',args.stage,dataset,r['seed'],r['family'],r['rate'],flush=True);continue
            detector=Detector.load(cell/'bundle_full');schema=detector.schema
            a=read_json(cell/'attack.json')['trigger'];trigger=VectorTrigger(**{**a,'indices':tuple(a['indices']),'values':tuple(a['values'])})
            xt=trigger.apply(malware,schema)
            if r['seed'] not in clean_models:clean_models[r['seed']]=lgb.Booster(model_file=str(cell.parents[1]/'clean.txt'))
            clean=clean_models[r['seed']]
            base={'dataset':dataset,'seed':r['seed'],'family':r['family'],'rate':r['rate'],
                'confirmed_original':r['independently_confirmed_strong_and_stealth'],
                'original_result_sha256':sha256(cell/'result.json'),'fresh_manifest_sha256':sha256(data/'dataset.json')}
            if args.stage=='fresh':
                positive,extra=core_scores(detector,xt);negative,_=core_scores(detector,benign)
                positive['STRIP']=strip(detector.model,xt,detector.reference,detector.config['strip_n'],detector.config['strip_alpha'],detector.config['seed'],schema=schema)
                negative['STRIP']=strip(detector.model,benign,detector.reference,detector.config['strip_n'],detector.config['strip_alpha'],detector.config['seed'],schema=schema)
                groups=attack_groups(clean.predict(malware,num_threads=4),extra['malware_probability'],clean.predict(xt,num_threads=4))
                supplement=Path('outputs/revision_2026_10_13/supplement')/dataset/f"seed_{r['seed']}"/r['family']/f"rate_{r['rate']}"
                s=read_json(supplement/'calibration.json');metrics={}
                for name in positive:metrics[name]=revised_metrics(positive[name],negative[name],detector.thresholds[name],groups)
                positive['STRIP_inverse']=1-positive['STRIP'];negative['STRIP_inverse']=1-negative['STRIP']
                metrics['STRIP_inverse']=revised_metrics(positive['STRIP_inverse'],negative['STRIP_inverse'],s['strip_inverse']['tau'],groups)
                positive['shadow']=np.maximum(0,clean.predict(xt,num_threads=4)-extra['malware_probability'])
                negative['shadow']=np.maximum(0,clean.predict(benign,num_threads=4)-detector.model.predict(benign,num_threads=4))
                metrics['shadow']=revised_metrics(positive['shadow'],negative['shadow'],s['shadow']['tau'],groups)
                cache={'positive_'+k:v for k,v in positive.items()};cache.update({'negative_'+k:v for k,v in negative.items()});cache.update({'group_'+k:v for k,v in groups.items()})
                np.savez_compressed(dest/'fresh_scores.npz',**cache)
                result={**base,'metrics':metrics,'groups':{k:int(v.sum()) for k,v in groups.items()},'benign_n':len(benign),
                    'scope':'Previously unused local source IDs; frozen original attack/model selection; post-review supplementary validation',
                    'cache_sha256':sha256(dest/'fresh_scores.npz')}
            else:
                n=min(args.adaptive_samples,len(xt));original=xt[:n].copy();best=original.copy()
                variable=np.asarray([j for j in schema.restricted if schema.view_labels[j]=='structural' and j not in trigger.indices],dtype=int)
                if not len(variable):raise ValueError('No remaining permitted coordinates')
                tau=detector.thresholds['X_primary_reduced'];rng=np.random.default_rng(20261013+r['seed'])
                def query(z):
                    scores,extra=core_scores(detector,z)
                    pp=extra['malware_probability'];ss=scores['X_primary_reduced']
                    cost=np.maximum(pp-.5,0)/.5+np.maximum(ss-tau,0)/max(1-tau,1e-9)
                    return cost,pp,ss
                cost,prob,score=query(best);baseline_prob=prob.copy();baseline_score=score.copy()
                counts=np.ones(n,dtype=int);first_success=np.where((prob<.5)&(score<=tau),1,-1)
                for step in range(1,args.queries):
                    active=np.flatnonzero(first_success<0)
                    if not len(active):break
                    proposal=best[active].copy();cols=rng.choice(variable,len(active));rows=rng.integers(len(values),size=len(active))
                    proposal[np.arange(len(active)),cols]=values[rows,cols]
                    c,pv,sv=query(proposal);counts[active]+=1
                    accept=(c<cost[active])|((c==cost[active])&(pv<prob[active]))
                    selected=active[accept];best[selected]=proposal[accept];cost[selected]=c[accept];prob[selected]=pv[accept];score[selected]=sv[accept]
                    success=(prob[active]<.5)&(score[active]<=tau);first_success[active[success]]=step+1
                assert np.array_equal(best[:,trigger.indices],original[:,trigger.indices])
                changed=np.any(best!=original,axis=0)
                assert set(np.flatnonzero(changed)).issubset(set(variable))
                eligible=clean.predict(malware[:n],num_threads=4)>=.5
                start=(baseline_prob<.5)&(baseline_score<=tau);end=(prob<.5)&(score<=tau)
                result={**base,'n':n,'eligible':int(eligible.sum()),'start_joint_success':int(np.sum(start&eligible)),
                    'end_joint_success':int(np.sum(end&eligible)),'new_joint_success':int(np.sum(end&~start&eligible)),
                    'start_main_evasion':int(np.sum((baseline_prob<.5)&eligible)),
                    'end_main_evasion':int(np.sum((prob<.5)&eligible)),
                    'mean_queries':float(counts.mean()),'max_queries':int(counts.max()),'changed_columns':np.flatnonzero(changed).tolist(),
                    'scope':lock['adaptive'],'fresh_malware_ids':[x.decode() for x in ids[y==1][:n]]}
                np.savez_compressed(dest/'adaptive_scores.npz',baseline_probability=baseline_prob,baseline_score=baseline_score,
                    probability=prob,score=score,queries=counts,first_success=first_success,eligible=eligible)
            write_json(path,result);results.append(result)
            print('Completed',args.stage,dataset,r['seed'],r['family'],r['rate'],flush=True);del detector;gc.collect()
        del X,benign,malware,clean_models;gc.collect()
    write_json(out/(args.stage+'_summary.json'),{'stage':args.stage,'runs':len(results),'results':results,'protocol_sha256':sha256(out/'protocol.json')})


if __name__=='__main__':main()
