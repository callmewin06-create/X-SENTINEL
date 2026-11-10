"""Formal fresh-role static and sequential poisoning-time follow-up.

Only attacker roles are read. No confirmation/final/ref/calibration loader is
imported. Run all six cells and lock artifacts globally before evaluation.
"""
import argparse
import ctypes
from ctypes import wintypes
from dataclasses import asdict
import gc
import hashlib
import json
import os
from pathlib import Path
import sys
import shutil
import time
import lightgbm as lgb
import numpy as np

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from xsentinel.schema import get_schema
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.experiment import train
from xsentinel.attacks.primary import VectorTrigger
from xsentinel.attacks.selectors import select_supplementary
from xsentinel.attacks.screen import screen_primary
from xsentinel.attacks.sequential import canonical,fingerprint,run_search
from xsentinel.baselines.scores import contributions
from xsentinel.detection.components import primary_components,COMPONENT_VERSIONS
from materialize_jstis_attacker import resource_memory

RULES={'min_eligible':1000,'min_asr':.5,'min_paired_gain':.2,'strict_max_accuracy_drop':.005}
SELECTORS=('min_population','count_abs_shap','signed_shap_conditioned')
PROFILES=('feature_restricted','vector_stress')


def process_memory():
    class COUNTERS(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('faults',wintypes.DWORD)]+[
            (k,ctypes.c_size_t) for k in ('peak_ws','ws','peak_paged','paged','peak_nonpaged','nonpaged','commit','peak_commit')]
    c=COUNTERS();c.cb=ctypes.sizeof(c)
    if not ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.c_void_p(-1),ctypes.byref(c),c.cb):
        raise OSError('Cannot measure actual worker peak memory')
    return {'worker_pid':os.getpid(),'peak_working_set_bytes':c.peak_ws,'peak_commit_bytes':c.peak_commit}


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--attacker',required=True); p.add_argument('--output',required=True)
    p.add_argument('--seed',type=int,choices=[17,29,43],required=True)
    p.add_argument('--phase',choices=['clean_profile','all'],default='all')
    a=p.parse_args(); source=Path(a.attacker); out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    receipt=read_json(source/'COMPLETE.json'); schema=get_schema(receipt['lock']['schema'])
    if receipt['counts']!={'fit':200000,'selection':10000,'development':10000}:
        raise ValueError('No silent budget reduction')
    for name,h in receipt['array_sha256'].items():
        if sha256(source/name)!=h: raise ValueError('Attacker array changed: '+name)
    roles={r:{k:np.load(source/f'{r}.{k}.npy',mmap_mode='r',allow_pickle=False) for k in ('X','y','ids')}
           for r in ('fit','selection','development')}
    cfg=read_json(ROOT/'configs/primary_execution.json')
    paths=['experiment.py','schema.py','attacks/primary.py','attacks/selectors.py',
           'attacks/sequential.py','attacks/screen.py','baselines/scores.py','detection/components.py']
    lock={'version':'jstis-fresh-poisoning-v1','dataset':schema.dataset,'seed':a.seed,
          'attacker_receipt_sha256':sha256(source/'COMPLETE.json'),'schema_sha256':schema.fingerprint,
          'execution':cfg,'screen':RULES,'selectors':SELECTORS,'profiles':PROFILES,'k':10,
          'rate':.02,'denominator':'all_fit','budget_per_arm':16,'objective_n':1000,
          'view_quotas':None,'heldout_roles_opened':[], 'code':{s:sha256(ROOT/'src/xsentinel'/s) for s in paths},
          'runner_sha256':sha256(__file__),'vmc_version':COMPONENT_VERSIONS['M3_view_mass'],
          'runtime':{'python':sys.version,'numpy':np.__version__,'lightgbm':lgb.__version__},
          'poison_buffer':'file-backed-float32-batches128'}
    # Normalize tuple/list representations before comparing JSON receipts.
    lock=json.loads(json.dumps(lock)); lockpath=out/'protocol.lock.json'
    if lockpath.exists() and read_json(lockpath)!=lock: raise ValueError('Protocol/code changed; use new run')
    write_json(lockpath,lock); protocol_digest=digest(lock)
    X,y=roles['fit']['X'],roles['fit']['y']; dev=roles['development']; sel=roles['selection']
    start=time.perf_counter(); memory=resource_memory()
    if memory['available']<3*1024**3: raise OSError('RAM gate: <3GiB free before clean fit')
    print('CLEAN_FIT_START',schema.dataset,a.seed,memory,flush=True)
    clean=train(X,y,out/'clean.txt',cfg,a.seed,schema=schema)
    write_json(out/'clean_profile.json',{'elapsed_including_resume_seconds':time.perf_counter()-start,
        'before':memory,'after':resource_memory(),'rows':len(X),'rounds':500,
        'model_sha256':sha256(out/'clean.txt'),'process_memory':process_memory(),
        'fit_elapsed_seconds':read_json(out/'clean.training.json')['elapsed_seconds'],
        'status':'CLEAN_FIT_COMPLETE_ONLY'})
    if a.phase=='clean_profile': return
    # Full's single clean Behavioral auxiliary is a separate 150-round fit.
    behavioral=train(X,y,out/'behavioral.txt',cfg,a.seed,view='behavioral',schema=schema)
    del behavioral; gc.collect()
    clean_p=clean.predict(dev['X'],num_threads=4); malware=dev['y']==1
    xm=np.asarray(dev['X'][malware]); eligible=clean_p[malware]>=.5
    if eligible.sum()<1000: raise ValueError('Insufficient fixed Search eligibility for objective')
    objective=np.flatnonzero(eligible)[:1000]
    np.save(out/'objective_ids.npy',dev['ids'][malware][objective])
    objective_digest=sha256(out/'objective_ids.npy')
    phi_path=out/'selection_phi.npy'
    if phi_path.exists():
        if sha256(phi_path)!=read_json(out/'selection_phi.json')['sha256']: raise ValueError('Selection SHAP changed')
        phi=np.load(phi_path,mmap_mode='r')
    else:
        phi=np.lib.format.open_memmap(phi_path,mode='w+',dtype='float64',shape=sel['X'].shape)
        for start in range(0,len(phi),128): phi[start:start+128]=contributions(clean,sel['X'][start:start+128],schema=schema)
        phi.flush(); write_json(out/'selection_phi.json',{'sha256':sha256(phi_path),'model_sha256':sha256(out/'clean.txt')})
    poison_ids=np.random.default_rng(a.seed).choice(np.flatnonzero(y==0),4000,replace=False)
    np.save(out/'poison_source_ids.npy',roles['fit']['ids'][poison_ids])
    poison_digest=sha256(out/'poison_source_ids.npy')
    catalogue={j:np.unique(np.asarray(sel['X'][:,j],dtype=np.float32)) for j in range(schema.dim)
               if np.ptp(sel['X'][:,j])>0}
    results=[]; initialization=None
    def evaluate(candidate,trigger_digest):
        directory=out/'candidates'/trigger_digest; directory.mkdir(parents=True,exist_ok=True)
        fitkey=digest({'protocol':protocol_digest,'trigger':candidate,'poison_ids':poison_digest})
        scorekey=digest({'fitkey':fitkey,'objective_ids':objective_digest,'vmc':lock['vmc_version'],
                         'batch_size':128,'search':receipt['array_sha256']['development.X.npy']})
        complete=directory/'result.json'
        if complete.exists():
            cached=read_json(complete)
            if cached['fitkey']!=fitkey or cached['scorekey']!=scorekey or cached['model_sha256']!=sha256(directory/'poisoned.txt'):
                raise ValueError('Candidate cache mismatch')
            return cached['metrics']
        idx,val=zip(*candidate)
        trigger=VectorTrigger('supplementary_noquota','vector_stress',schema.version,schema.fingerprint,idx,val)
        write_json(directory/'trigger.json',asdict(trigger))
        if resource_memory()['available']<2*1024**3:
            raise OSError('RAM gate before file-backed poison buffer; no budget reduction')
        if shutil.disk_usage(out).free<int(X.nbytes)+2*1024**3:
            raise OSError('Disk gate before file-backed poison buffer')
        work=out/'poison_work.npy'
        poisoned=np.lib.format.open_memmap(work,mode='w+',dtype='float32',shape=X.shape)
        for start in range(0,len(X),128):poisoned[start:start+128]=X[start:start+128]
        poisoned[np.ix_(poison_ids,idx)]=val;poisoned.flush()
        model=train(poisoned,y,directory/'poisoned.txt',cfg,a.seed,schema=schema)
        del poisoned; gc.collect(); work.unlink()
        xt=trigger.apply(xm,schema)
        screen=screen_primary(clean_p,model.predict(dev['X'],num_threads=4),clean.predict(xt,num_threads=4),
                              model.predict(xt,num_threads=4),dev['y'],RULES)
        vmcs=[]
        for offset in range(0,len(objective),128):
            batch=xt[objective[offset:offset+128]]
            shap=contributions(model,batch,schema=schema)
            scores,_,_=primary_components(shap,model.predict(batch,num_threads=4),schema,methods=['M3_view_mass'])
            vmcs.extend(scores['M3_view_mass'].tolist())
        metrics={'eligible':screen['n_eligible'],'asr':screen['asr']['rate'],
                 'paired_gain':screen['paired_gain'],'accuracy_drop':screen['accuracy_drop'],'mean_vmc':float(np.mean(vmcs))}
        write_json(complete,{'fitkey':fitkey,'scorekey':scorekey,'model_sha256':sha256(directory/'poisoned.txt'),
                            'metrics':metrics,'screen':screen,'trigger':asdict(trigger),
                            'process_memory':process_memory(),'system_memory':resource_memory()})
        del model,xt; gc.collect(); print('CANDIDATE_COMPLETE',trigger_digest,metrics,flush=True)
        return metrics
    for profile in PROFILES:
        for selector in SELECTORS:
            trigger,meta=select_supplementary(clean,sel['X'],schema=schema,profile=profile,selector=selector,phi=phi)
            candidate=canonical(trigger.indices,trigger.values); key=fingerprint(candidate)
            metrics=evaluate(candidate,key)
            row={'profile':profile,'selector':selector,'fingerprint':key,'trigger':asdict(trigger),'metadata':meta,'metrics':metrics}
            results.append(row); write_json(out/'static_attempts.json',results)
            if profile=='vector_stress' and selector=='count_abs_shap': initialization=candidate
    for arm in ('asr_only','vmc_aware'):
        trajectory=out/f'{arm}.trajectory.jsonl'
        # Replaying deterministic cached candidates is safe; rebuild one full log.
        with trajectory.open('w',encoding='utf8') as stream:
            def log(row):
                stream.write(json.dumps(row,allow_nan=False)+'\n'); stream.flush()
            result=run_search(initialization,catalogue,evaluate,arm=arm,seed=a.seed,budget=16,on_step=log)
        write_json(out/f'{arm}.json',result)
    write_json(out/'ATTACKS_LOCKED.json',{'status':'CELL_ATTACKS_LOCKED_NOT_EVALUATED','protocol_digest':protocol_digest,
        'artifacts':{str(p.relative_to(out)):sha256(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='ATTACKS_LOCKED.json'},
        'heldout_roles_opened':[]})


if __name__=='__main__':
    try: main()
    except Exception as exc:
        # Never label a crashed or resource-limited run as NO_VALID_ATTACK.
        print('INCOMPLETE_INFRASTRUCTURE',type(exc).__name__,str(exc),file=sys.stderr,flush=True)
        raise
