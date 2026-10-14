"""New caches and sensitivity/diagnostic results; original bundles stay untouched."""
import sys,argparse,time,gc,csv,json,platform
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import lightgbm as lgb
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.primary_workflow import open_roles
from xsentinel.detection.detector import Detector
from xsentinel.detection.calibration import threshold
from xsentinel.baselines.scores import strip
from xsentinel.revision.scoring import core_scores
from xsentinel.revision.analysis import attack_groups,revised_metrics
from xsentinel.evaluation.metrics import latency_summary
from xsentinel.attacks.primary import VectorTrigger


def save_csv(path,rows):
    if not rows:return
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['calibration','latency'],required=True)
    p.add_argument('--out',default='outputs/revision_2026_10_13/supplement');p.add_argument('--latency-samples',type=int,default=100)
    args=p.parse_args();out=Path(args.out)
    protected=Path('outputs/primary').resolve()
    if out.resolve()==protected or protected in out.resolve().parents:raise ValueError('Protected original outputs')
    out.mkdir(parents=True,exist_ok=True)
    lock={'protocol':'revision-supplement-v1','main_policy':'Existing frozen 500-round models reused',
          'shadow_access':'Additional clean full model allowed only in resource-rich full comparison, same clean fit',
          'is_pe_policy':'Fixed original models; final-only filtering then calibration-only filtering separately; no fit retraining',
          'STRIP_inv':'H=1-original_STRIP, discovered after final; new exploratory variant',
          'new_thresholds':'Chosen from benign calibration only; old thresholds remain unchanged',
          'latency_samples':args.latency_samples,'latency_scopes':['classifier','core_reduced','core_full','STRIP','suite_reduced','suite_full'],
          'source_code':{str(x):sha256(x) for x in [Path(__file__),Path('src/xsentinel/revision/scoring.py')]}}
    lockpath=out/'protocol.json'
    if lockpath.exists():
        if read_json(lockpath)!=lock:raise ValueError('Supplement config/code changed; use fresh namespace')
    else:write_json(lockpath,lock)
    allrows=[];invrows=[];shadowrows=[];latencies=[]
    for dataset in ('EMBER2018','EMBER2024'):
        _,schema,roles=open_roles(Path('data/primary')/dataset/'protocol_v2',('reference','calibration','final'))
        final=roles['final'];benign=final['y']==0;malware=~benign
        calibration=roles['calibration']['X'];keep_cal=(calibration[:,2]==1) if dataset=='EMBER2024' else np.ones(len(calibration),dtype=bool)
        keep_benign=(final['X'][benign,2]==1) if dataset=='EMBER2024' else np.ones(benign.sum(),dtype=bool)
        shadows={}
        for cell in sorted((Path('outputs/primary')/dataset/'protocol_v2').glob('seed_*/*/rate_*')):
            r=read_json(cell/'result.json');dest=out/dataset/f"seed_{r['seed']}"/r['family']/f"rate_{r['rate']}";dest.mkdir(parents=True,exist_ok=True)
            resultpath=dest/(args.stage+'.json')
            if resultpath.exists():
                existing=read_json(resultpath)
                if existing['original_result_sha256']!=sha256(cell/'result.json'):raise ValueError('Original result changed')
                if args.stage=='calibration':
                    allrows.extend(existing['sensitivity']);invrows.append(existing['strip_inverse']);shadowrows.append(existing['shadow'])
                else:latencies.append(existing)
                print('Resumed',args.stage,dataset,r['seed'],r['family'],r['rate'],flush=True);continue
            full=Detector.load(cell/'bundle_full');reduced=Detector.load(cell/'bundle_reduced') if args.stage=='latency' else None
            with np.load(cell/'paired_predictions.npz',allow_pickle=False) as a:
                arrays={k:v.copy() for k,v in a.items()}
            groups=attack_groups(arrays['clean_malware_p'],arrays['triggered_main_p'],arrays['clean_trigger_p'])
            base={'dataset':dataset,'family':r['family'],'rate':r['rate'],'seed':r['seed'],
                  'confirmed':r['independently_confirmed_strong_and_stealth'],'original_result_sha256':sha256(cell/'result.json')}
            if args.stage=='calibration':
                cache=dest/'calibration_scores.npz'
                cal,_=core_scores(full,calibration)
                cal['STRIP']=strip(full.model,calibration,full.reference,full.config['strip_n'],full.config['strip_alpha'],full.config['seed'],schema=schema)
                assert set(cal)==set(full.thresholds)
                for name,score in cal.items():
                    oldtau=threshold(score,full.config['fpr'])
                    if not np.isclose(oldtau,full.thresholds[name],rtol=0,atol=1e-10):
                        raise ValueError('Original calibration does not reproduce: '+name)
                np.savez_compressed(cache,**cal)
                sensitivity=[]
                for name,score in cal.items():
                    oldtau=full.thresholds[name];newtau=threshold(score[keep_cal],full.config['fpr'])
                    ps=arrays['full_trigger_'+name];ns=arrays['full_benign_'+name]
                    for label,tau,neg in [('original',oldtau,ns),('final_is_pe_1_only',oldtau,ns[keep_benign]),
                                          ('calibration_is_pe_1_only',newtau,ns),('both_is_pe_1',newtau,ns[keep_benign])]:
                        m=revised_metrics(ps,neg,tau,groups)
                        sensitivity.append({**{k:base[k] for k in ('dataset','family','rate','seed','confirmed')},
                            'method':name,'condition':label,'calibration_n':len(score) if label in ('original','final_is_pe_1_only') else int(keep_cal.sum()),
                            'benign_n':len(neg),'removed_calibration':int((~keep_cal).sum()),'removed_final_benign':int((~keep_benign).sum()),
                            'tau':tau,'tau_delta':tau-oldtau,'fpr':m['benign_fpr']['rate'],'recall':m['recall_successful_eligible']['rate'],
                            'post_asr':m['post_defense_asr']['rate'],'zero_cal_scores':json.dumps(score[~keep_cal].tolist())})
                invtau=threshold(1-cal['STRIP'],full.config['fpr'])
                inv=revised_metrics(1-arrays['full_trigger_STRIP'],1-arrays['full_benign_STRIP'],invtau,groups)
                invrow={**{k:base[k] for k in ('dataset','family','rate','seed','confirmed')},
                        'tau':invtau,'fpr':inv['benign_fpr']['rate'],'recall':inv['recall_successful_eligible']['rate'],
                        'post_asr':inv['post_defense_asr']['rate'],'auc_successful':inv['auroc_successful_eligible'],
                        'scope':'Post-review exploration on previously observed final, not independent confirmation'}
                seed=r['seed']
                if seed not in shadows:
                    clean=lgb.Booster(model_file=str(cell.parents[1]/'clean.txt'));schema.check_model(clean)
                    shadows[seed]=(clean,clean.predict(calibration,num_threads=4),clean.predict(final['X'][benign],num_threads=4))
                clean,cp,cb=shadows[seed]
                cal_poison=full.model.predict(calibration,num_threads=4);benign_poison=full.model.predict(final['X'][benign],num_threads=4)
                shadow_cal=np.maximum(0,cp-cal_poison);shadow_tau=threshold(shadow_cal,full.config['fpr'])
                shadow_pos=np.maximum(0,arrays['clean_trigger_p']-arrays['triggered_main_p']);shadow_neg=np.maximum(0,cb-benign_poison)
                sm=revised_metrics(shadow_pos,shadow_neg,shadow_tau,groups)
                shadowrow={**{k:base[k] for k in ('dataset','family','rate','seed','confirmed')},
                    'tau':shadow_tau,'fpr':sm['benign_fpr']['rate'],'recall':sm['recall_successful_eligible']['rate'],
                    'post_asr':sm['post_defense_asr']['rate'],'auc_successful':sm['auroc_successful_eligible'],
                    'clean_model_sha256':sha256(cell.parents[1]/'clean.txt'),'access':'Clean fit-trained full model; beyond reduced capabilities',
                    'scope':'Post-review exploratory baseline; threshold benign-only; independent confirmation pending'}
                result={**base,'sensitivity':sensitivity,'strip_inverse':invrow,'shadow':shadowrow,
                        'calibration_cache_sha256':sha256(cache),'old_calibration_reproduced':True,'original_bundle_unchanged':True}
                write_json(resultpath,result);allrows.extend(sensitivity);invrows.append(invrow);shadowrows.append(shadowrow)
            else:
                attack=read_json(cell/'attack.json')['trigger'];trigger=VectorTrigger(**{**attack,'indices':tuple(attack['indices']),'values':tuple(attack['values'])})
                xt=trigger.apply(final['X'][malware],schema);pool=np.concatenate([final['X'][benign],xt])
                chosen=np.random.default_rng(r['seed']).choice(len(pool),min(args.latency_samples,len(pool)),replace=False);samples=pool[chosen]
                functions={'classifier':lambda x:full.model.predict(x,num_threads=4),
                           'core_reduced':lambda x:core_scores(reduced,x),'core_full':lambda x:core_scores(full,x),
                           'STRIP':lambda x:strip(full.model,x,full.reference,full.config['strip_n'],full.config['strip_alpha'],full.config['seed'],schema=schema),
                           'suite_reduced':lambda x:reduced.predict(x),'suite_full':lambda x:full.predict(x)}
                before_reduced,_=core_scores(reduced,samples[:3]);before_full,_=core_scores(full,samples[:3])
                for obj,scores in [(reduced,before_reduced),(full,before_full)]:
                    legacy,_=obj.scores(samples[:3])
                    assert all(np.array_equal(v,legacy[k]) for k,v in scores.items())
                timings={name:[] for name in functions}
                for fn in functions.values():fn(samples[:1])
                names=list(functions)
                for i,row in enumerate(samples):
                    order=names if i%2==0 else names[::-1]
                    for name in order:
                        start=time.perf_counter();functions[name](row[None,:]);timings[name].append((time.perf_counter()-start)*1000)
                result={**base,'timings':{k:latency_summary(v) for k,v in timings.items()},
                        'scope':'Warm per-input, same samples, reversed alternating order; no extraction/API/database/load time',
                        'core_parity_with_original':True,'hardware':platform.processor(),'python':platform.python_version(),
                        'sample_sha256':__import__('hashlib').sha256(samples.tobytes()).hexdigest()}
                write_json(resultpath,result);latencies.append(result)
            print('Completed',args.stage,dataset,r['seed'],r['family'],r['rate'],flush=True)
            del full,arrays
            if reduced is not None:del reduced
            gc.collect()
        del roles,shadows;gc.collect()
    if args.stage=='calibration':
        save_csv(out/'sensitivity.csv',allrows);save_csv(out/'strip_inverse.csv',invrows);save_csv(out/'shadow.csv',shadowrows)
    else:write_json(out/'latency.json',latencies)
    write_json(out/(args.stage+'_complete.json'),{'stage':args.stage,'completed_cells':len(invrows) if args.stage=='calibration' else len(latencies),
        'original_model_thresholds_changed':False,'independent_validation':'Not provided by reused final pool'})


if __name__=='__main__':main()
