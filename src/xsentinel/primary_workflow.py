"""Primary development checkpoints and common selector lock; final data stay closed."""
import csv
import gc
import itertools
import hashlib
import shutil
import time
import zipfile
from dataclasses import asdict
from pathlib import Path

import lightgbm as lgb
import numpy as np
from xsentinel.utils import read_json, write_json, sha256
from xsentinel.schema import get_schema
from xsentinel.experiment import train, performance_from_predictions
from xsentinel.baselines.scores import contributions
from xsentinel.attacks.primary import VectorTrigger, poison_primary
from xsentinel.attacks.selectors import select_primary
from xsentinel.attacks.screen import screen_primary, lock_common_selector
from xsentinel.attacks.development import _peak_memory
from xsentinel.detection.detector import Detector
from xsentinel.evaluation.primary import evaluate_pair
from xsentinel.evaluation.metrics import latency_summary

DEPENDENCIES = ('primary_workflow.py','schema.py','utils.py','experiment.py',
    'attacks/primary.py','attacks/selectors.py','attacks/screen.py','attacks/development.py',
    'attacks/trigger.py','baselines/scores.py','data/protocol.py','data/prepare.py',
    'data/vectorizer.py','data/v3_raw.py','detection/detector.py','detection/calibration.py',
    'detection/components.py','evaluation/metrics.py','evaluation/primary.py',
    'ember_upstream.py','thrember_upstream.py','pefile_warnings.txt')


def expected_cells(protocol, datasets=None):
    return list(itertools.product(datasets or protocol['datasets'], protocol['family_geometry'],
                                  protocol['rates'], protocol['seeds']))


def _source_hashes():
    package=Path(__file__).parent
    return {name:sha256(package/name) for name in DEPENDENCIES}


def open_roles(directory, names):
    """Open only explicitly requested partitions; development never opens test X."""
    directory=Path(directory); state=read_json(directory/'roles.json')
    schema=get_schema(state['schema']); source=Path(state['source_directory'])
    if state['schema_sha256']!=schema.fingerprint or sha256(directory/'roles.npz')!=state['roles_sha256']:
        raise ValueError('Frozen role/schema mismatch')
    if sha256(source/'dataset.json')!=state['source_dataset_sha256']:
        raise ValueError('Source dataset manifest changed')
    if any(name not in state['sizes'] for name in names):
        raise ValueError('Unknown primary role')
    sources={}; result={}
    with np.load(directory/'roles.npz',allow_pickle=False) as partitions:
        for name in names:
            split=state['role_partitions'][name]
            if split not in sources:
                sources[split]={}
                for kind in ('X','y','ids'):
                    filename=f'{kind}_{split}.npy'
                    if sha256(source/filename)!=state['source_array_sha256'][filename]:
                        raise ValueError('Source array checksum changed: '+filename)
                    sources[split][kind]=np.load(source/filename,mmap_mode='r',allow_pickle=False)
            data=sources[split]; idx=partitions[name]
            ids=data['ids'][idx].astype(str)
            if ids.tolist()!=state['ids'][name]:
                raise ValueError('Role source IDs changed: '+name)
            X=schema.matrix(np.asarray(data['X'][idx]))
            y=np.asarray(data['y'][idx])
            if len(X)!=state['sizes'][name] or not np.isin(y,[0,1]).all():
                raise ValueError('Role size/labels mismatch')
            if name in ('reference','calibration') and np.any(y):
                raise ValueError('Reference/calibration must be benign')
            result[name]={'X':X,'y':y,'ids':ids}
    return state,schema,result


def _validate_protocol(protocol, execution):
    if protocol.get('pending') or protocol['M3']!='view_mass' or protocol['m5']!='supplementary_only_not_scheduled':
        raise ValueError('Approved primary protocol required')
    if execution.get('detector',{}).get('enable_m5',False):
        raise ValueError('Primary execution excludes M5')
    if tuple(protocol['selector_protocol']['candidates'])!=('legacy_rare','signed_shap_conditioned'):
        raise ValueError('Declared two-selector comparison required')
    for key,expected in (('strip_n',protocol['strip']['n']),('strip_alpha',protocol['strip']['alpha']),
                         ('malware_threshold',protocol['malware_threshold']),('fpr',protocol['target_calibration_fpr'])):
        if execution['detector'][key]!=expected:
            raise ValueError('Detector execution differs from approved protocol: '+key)


def _start(output, roles_directory, protocol_path, execution_path, phase, resume, extra=None):
    out=Path(output); protocol=read_json(protocol_path); execution=read_json(execution_path)
    _validate_protocol(protocol,execution)
    state=read_json(Path(roles_directory)/'roles.json')
    if protocol['datasets'].get(state['dataset'])!=state['schema'] or state['sizes']!=protocol['sample_sizes']:
        raise ValueError('Role budget/schema differs from approved protocol')
    lock={'phase':phase,'dataset':state['dataset'],'schema':state['schema'],
          'protocol_sha256':sha256(protocol_path),'execution_sha256':sha256(execution_path),
          'roles_directory':str(Path(roles_directory).resolve()),
          'roles_manifest_sha256':sha256(Path(roles_directory)/'roles.json'),
          'source_hashes':_source_hashes(),**(extra or {})}
    if out.exists() and any(out.iterdir()):
        if not resume or read_json(out/'run.lock.json')!=lock:
            raise FileExistsError('Fresh run directory or exact source/config --resume required')
        manifest=read_json(out/'run_manifest.json')
        if sha256(out/'source_snapshot.zip')!=manifest['source_snapshot_sha256']:
            raise ValueError('Archived source snapshot changed')
    else:
        out.mkdir(parents=True,exist_ok=True)
        write_json(out/'run.lock.json',lock)
        package=Path(__file__).parent
        with zipfile.ZipFile(out/'source_snapshot.zip','x',zipfile.ZIP_DEFLATED) as archive:
            for name in DEPENDENCIES:
                archive.write(package/name,'xsentinel/'+name)
        write_json(out/'run_manifest.json',{'protocol':protocol,'execution':execution,
            'lock_sha256':sha256(out/'run.lock.json'),'source_snapshot_sha256':sha256(out/'source_snapshot.zip'),
            'test_arrays_opened':phase=='final','confirmation_used_to_choose':False})
    return out,protocol,execution,state


def _write_table(out, rows, declared):
    write_json(out/'results.json',{'phase':'development','declared_cells':declared,'rows':rows,
        'complete_table':len(rows)==declared,'test_arrays_opened':False})
    with (out/'results.csv').open('w',encoding='utf-8',newline='') as f:
        keys=['dataset','phase','family','rate','seed','selector','status','strong_and_stealth','paired_gain','error']
        writer=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore'); writer.writeheader(); writer.writerows(rows)


def run_primary_development(roles_directory, output, protocol_path, execution_path, *, resume=False,
                            round_number=1, max_new_cells=None):
    """One predeclared round, all three families/rates/seeds; no ref/cal/final access."""
    out,protocol,execution,state=_start(output,roles_directory,protocol_path,execution_path,
                                      'development',resume,{'round_number':round_number})
    if type(round_number) is not int or not 1<=round_number<=protocol['attack_screen']['max_protocol_rounds_per_dataset']:
        raise ValueError('Development round exceeds approved budget')
    if max_new_cells is not None and (type(max_new_cells) is not int or max_new_cells<1):
        raise ValueError('Positive checkpoint cell budget required')
    state,schema,roles=open_roles(roles_directory,('fit','selection','development'))
    fit,selection,dev=[roles[k] for k in ('fit','selection','development')]
    if any(set(roles[a]['ids']) & set(roles[b]['ids']) for a,b in itertools.combinations(roles,2)):
        raise ValueError('Development roles overlap')
    declared=len(expected_cells(protocol,[schema.dataset]))*2
    rows=[]; new_cells=0; started=time.perf_counter()
    for seed in protocol['seeds']:
        seed_dir=out/f'seed_{seed}'; seed_dir.mkdir(exist_ok=True)
        print(f'{schema.dataset} development clean: seed={seed}, fit={len(fit["y"])}',flush=True)
        clean=train(fit['X'],fit['y'],seed_dir/'clean.txt',execution,seed,schema=schema)
        candidate_path=seed_dir/'candidates.lock.json'
        if candidate_path.exists():
            candidates=read_json(candidate_path)
            if candidates['clean_model_sha256']!=sha256(seed_dir/'clean.txt'):
                raise ValueError('Candidate clean model changed')
        else:
            # Compute native SHAP once; both selectors use exactly the same pool/model.
            phi=contributions(clean,selection['X'],schema=schema)
            candidates={'clean_model_sha256':sha256(seed_dir/'clean.txt'),
                'selection_ids_sha256':hashlib.sha256('\n'.join(selection['ids']).encode()).hexdigest(),
                'varying_restricted':[{ 'index':j,'name':schema.names[j],'view':schema.view_labels[j],
                                      'unique_values':len(np.unique(selection['X'][:,j]))} for j in schema.restricted],
                'candidates':{},'locked_before_development_predictions':True}
            for selector,family in itertools.product(protocol['selector_protocol']['candidates'],protocol['family_geometry']):
                spec=protocol['family_geometry'][family]; geometry={v:spec[v] for v in schema.views if v in spec}
                key=selector+'/'+family
                try:
                    trigger,diagnostics=select_primary(clean,selection['X'],schema=schema,family=family,
                        profile=spec['profile'],geometry=geometry,selector=selector,phi=phi)
                    candidates['candidates'][key]={'status':'ready','trigger':asdict(trigger),'diagnostics':diagnostics}
                except ValueError as exc:
                    candidates['candidates'][key]={'status':'unsupported','error':str(exc)}
            write_json(candidate_path,candidates)
            del phi; gc.collect()
        malware=dev['y']==1; clean_p=clean.predict(dev['X'],num_threads=4)
        for selector,family,rate in itertools.product(protocol['selector_protocol']['candidates'],
                                                      protocol['family_geometry'],protocol['rates']):
            dest=seed_dir/selector/family/f'rate_{rate:g}'; dest.mkdir(parents=True,exist_ok=True)
            result_path=dest/'result.json'
            if result_path.exists():
                row=read_json(result_path)
                for filename,expected in row.get('artifact_sha256',{}).items():
                    if sha256(dest/filename)!=expected: raise ValueError('Cell artifact changed: '+filename)
                rows.append(row); continue
            base={'dataset':schema.dataset,'phase':'development','family':family,'rate':rate,
                  'seed':seed,'selector':selector,'round_number':round_number,'strong_and_stealth':False,
                  'paired_gain':None,'test_arrays_opened':False}
            candidate=candidates['candidates'][selector+'/'+family]
            if candidate['status']!='ready':
                row={**base,'status':'unsupported','error':candidate['error']}
            else:
                trigger=VectorTrigger(**candidate['trigger'])
                trigger.validate(schema)
                print(f'{schema.dataset} development: {seed} / {selector} / {family} / {rate:g}',flush=True)
                cell_started=time.perf_counter()
                Xp,poison_ids,poison_info=poison_primary(fit['X'],fit['y'],trigger,rate,seed,
                    denominator=protocol['poison_rate_denominator'],schema=schema)
                attack={'trigger':asdict(trigger),**poison_info,'seed':seed,
                        'poison_source_ids':fit['ids'][poison_ids].tolist(),
                        'candidate_lock_sha256':sha256(candidate_path)}
                attack_path=dest/'attack.json'
                if attack_path.exists() and read_json(attack_path)!=attack:
                    raise ValueError('Poison checkpoint changed')
                write_json(attack_path,attack)
                try:
                    model=train(Xp,fit['y'],dest/'poisoned.txt',execution,seed,schema=schema)
                    del Xp; gc.collect()
                    xt=trigger.apply(dev['X'][malware],schema)
                    poison_p=model.predict(dev['X'],num_threads=4)
                    before=clean.predict(xt,num_threads=4); after=model.predict(xt,num_threads=4)
                    metrics=screen_primary(clean_p,poison_p,before,after,dev['y'],protocol['attack_screen'],protocol['malware_threshold'])
                    np.savez_compressed(dest/'predictions.npz',ids=dev['ids'].astype('S64'),y=dev['y'],
                        clean=clean_p,poisoned=poison_p,clean_trigger=before,poisoned_trigger=after)
                    artifact_names=['attack.json','poisoned.txt','poisoned.training.json','predictions.npz']
                    row={**base,'status':'complete' if metrics['paired_gain'] is not None else 'failed',
                         **metrics,'elapsed_seconds':time.perf_counter()-cell_started,'process_memory':_peak_memory(),
                         'artifact_sha256':{name:sha256(dest/name) for name in artifact_names},
                         'candidate_lock_sha256':sha256(candidate_path)}
                    if metrics['paired_gain'] is None: row['error']='No eligible malware; paired gain undefined'
                    del model,xt; gc.collect()
                except MemoryError:
                    write_json(result_path,{**base,'status':'failed','error':'MemoryError; resource review required'})
                    raise
                except Exception as exc:
                    if 'Xp' in locals(): del Xp
                    row={**base,'status':'failed','error':type(exc).__name__+': '+str(exc)}
            write_json(result_path,row); rows.append(row); new_cells+=1
            _write_table(out,rows,declared)
            if max_new_cells is not None and new_cells>=max_new_cells:
                return {'dataset':schema.dataset,'status':'checkpoint','rows':len(rows),'declared':declared}
        del clean; gc.collect()
    _write_table(out,rows,declared)
    write_json(out/'completion.json',{'dataset':schema.dataset,'phase':'development','rows':len(rows),
        'declared_cells':declared,'complete':len(rows)==declared,'elapsed_seconds_current_session':time.perf_counter()-started,
        'process_memory':_peak_memory(),'test_arrays_opened':False})
    return {'dataset':schema.dataset,'status':'complete','rows':len(rows),'declared':declared}


def lock_primary_selector(development_directories, protocol_path, output):
    output=Path(output)
    if output.exists(): raise FileExistsError('Existing selector lock preserved')
    protocol=read_json(protocol_path); rows=[]; proofs={}; datasets=[]
    for directory in development_directories:
        directory=Path(directory); state=read_json(directory/'results.json'); lock=read_json(directory/'run.lock.json')
        if not state['complete_table'] or lock['phase']!='development' or lock['protocol_sha256']!=sha256(protocol_path):
            raise ValueError('Complete matching development evidence required')
        # Reproduce every completed screen from preserved per-sample predictions;
        # never choose a selector from an unaudited hand-edited aggregate table.
        role_state=read_json(Path(lock['roles_directory'])/'roles.json')
        if sha256(Path(lock['roles_directory'])/'roles.json')!=lock['roles_manifest_sha256']:
            raise ValueError('Development role manifest changed')
        for row in state['rows']:
            cell,original=_verified_development_cell(directory,row['selector'],row['family'],row['rate'],row['seed'])
            if original!=row: raise ValueError('Development aggregate differs from cell evidence')
            if row['status']=='complete':
                with np.load(cell/'predictions.npz',allow_pickle=False) as a:
                    if a['ids'].astype(str).tolist()!=role_state['ids']['development']:
                        raise ValueError('Development prediction IDs changed')
                    reproduced=screen_primary(a['clean'],a['poisoned'],a['clean_trigger'],a['poisoned_trigger'],a['y'],
                        protocol['attack_screen'],protocol['malware_threshold'])
                if any(row[key]!=value for key,value in reproduced.items()):
                    raise ValueError('Development metrics do not reproduce')
        datasets.append(lock['dataset']); rows.extend(state['rows'])
        proofs[str(directory.resolve())]={'results_sha256':sha256(directory/'results.json'),
                                         'lock_sha256':sha256(directory/'run.lock.json')}
    if set(datasets)!=set(protocol['datasets']) or len(datasets)!=len(set(datasets)):
        raise ValueError('Exactly one complete development table per dataset required')
    chosen=lock_common_selector(rows,expected_cells(protocol))
    write_json(output,{**chosen,'protocol_sha256':sha256(protocol_path),'development_proofs':proofs})
    return chosen


def _locked_selector(path, development, protocol_path):
    lock=read_json(path)
    if lock['protocol_sha256']!=sha256(protocol_path) or lock['confirmation_used_to_choose']:
        raise ValueError('Selector protocol/evidence mismatch')
    if str(Path(development).resolve()) not in lock['development_proofs']:
        raise ValueError('Development directory is not part of common selector evidence')
    for directory,proof in lock['development_proofs'].items():
        for file,key in (('results.json','results_sha256'),('run.lock.json','lock_sha256')):
            if sha256(Path(directory)/file)!=proof[key]:
                raise ValueError('Frozen selector development evidence changed')
        if read_json(Path(directory)/'run.lock.json')['source_hashes']!=_source_hashes():
            raise ValueError('Development source changed; use its frozen implementation')
    if lock['chosen_selector'] not in read_json(protocol_path)['selector_protocol']['candidates']:
        raise ValueError('Unexpected locked selector')
    return lock['chosen_selector']


def _verified_development_cell(development, selector, family, rate, seed):
    dest=Path(development)/f'seed_{seed}'/selector/family/f'rate_{rate:g}'
    row=read_json(dest/'result.json')
    for name,expected in row.get('artifact_sha256',{}).items():
        if sha256(dest/name)!=expected: raise ValueError('Development cell artifact changed')
    return dest,row


def run_primary_confirmation(roles_directory, development, selector_lock, output, protocol_path,
                             execution_path, *, resume=False):
    selector=_locked_selector(selector_lock,development,protocol_path)
    if read_json(Path(development)/'run.lock.json')['execution_sha256']!=sha256(execution_path):
        raise ValueError('Execution changed after development')
    out,protocol,execution,state=_start(output,roles_directory,protocol_path,execution_path,'confirmation',resume,
        {'selector_lock_sha256':sha256(selector_lock),'development_lock_sha256':sha256(Path(development)/'run.lock.json')})
    state,schema,roles=open_roles(roles_directory,('confirmation',))
    pool=roles['confirmation']; malware=pool['y']==1; rows=[]
    for seed in protocol['seeds']:
        clean=lgb.Booster(model_file=str(Path(development)/f'seed_{seed}/clean.txt'))
        schema.check_model(clean); clean_p=clean.predict(pool['X'],num_threads=4)
        for family,rate in itertools.product(protocol['family_geometry'],protocol['rates']):
            src,dev=_verified_development_cell(development,selector,family,rate,seed)
            dest=out/f'seed_{seed}'/family/f'rate_{rate:g}'; dest.mkdir(parents=True,exist_ok=True)
            result_path=dest/'result.json'
            if result_path.exists():
                row=read_json(result_path)
                for name,expected in row.get('artifact_sha256',{}).items():
                    if sha256(dest/name)!=expected: raise ValueError('Confirmation artifact changed')
                rows.append(row); continue
            base={'dataset':schema.dataset,'phase':'confirmation','family':family,'rate':rate,'seed':seed,
                  'selector':selector,'development_result_sha256':sha256(src/'result.json'),
                  'selector_lock_sha256':sha256(selector_lock),'strong_and_stealth':False}
            if dev['status']!='complete':
                row={**base,'status':dev['status'],'error':'Development cell not complete: '+dev.get('error','')}
            else:
                print(f'{schema.dataset} confirmation: {seed} / {family} / {rate:g}',flush=True)
                trigger=VectorTrigger(**read_json(src/'attack.json')['trigger'])
                model=lgb.Booster(model_file=str(src/'poisoned.txt')); schema.check_model(model)
                xt=trigger.apply(pool['X'][malware],schema)
                poison_p=model.predict(pool['X'],num_threads=4)
                before=clean.predict(xt,num_threads=4); after=model.predict(xt,num_threads=4)
                metrics=screen_primary(clean_p,poison_p,before,after,pool['y'],protocol['attack_screen'],protocol['malware_threshold'])
                np.savez_compressed(dest/'predictions.npz',ids=pool['ids'].astype('S64'),y=pool['y'],clean=clean_p,
                                    poisoned=poison_p,clean_trigger=before,poisoned_trigger=after)
                row={**base,'status':'complete',**metrics,
                     'independently_confirmed_strong_and_stealth':bool(dev['strong_and_stealth'] and metrics['strong_and_stealth']),
                     'artifact_sha256':{'predictions.npz':sha256(dest/'predictions.npz')}}
                del model,xt; gc.collect()
            write_json(result_path,row); rows.append(row)
            write_json(out/'results.json',{'phase':'confirmation','selector':selector,'rows':rows,
                'test_arrays_opened':False,'confirmation_used_to_choose':False,
                'complete_table':len(rows)==len(expected_cells(protocol,[schema.dataset]))})
        del clean; gc.collect()
    return {'dataset':schema.dataset,'phase':'confirmation','rows':len(rows),
            'confirmed_strong_and_stealth':sum(r.get('independently_confirmed_strong_and_stealth',False) for r in rows)}


def _copy_exact(source,dest):
    source=Path(source); dest=Path(dest)
    if dest.exists():
        if sha256(source)!=sha256(dest): raise ValueError('Adopted model changed')
    else:
        shutil.copyfile(source,dest)


def _latency_pair(reduced,full,benign,triggered,n,seed):
    count=min(n,len(benign)+len(triggered))
    if count<=0: return {}
    rng=np.random.default_rng(seed); pool=np.concatenate((benign,triggered))
    chosen=rng.choice(len(pool),count,replace=False); samples=pool[chosen]
    timings={'reduced':[],'full':[]}
    reduced.predict(samples[:1]); full.predict(samples[:1])
    for i,x in enumerate(samples):
        order=(('reduced',reduced),('full',full)) if i%2==0 else (('full',full),('reduced',reduced))
        for name,obj in order:
            started=time.perf_counter(); obj.predict(x[None,:])
            timings[name].append((time.perf_counter()-started)*1000)
    return {**{name:latency_summary(values) for name,values in timings.items()},
            'scope':'warm single-input detector latency; alternating order, same samples; not isolated RAM comparison',
            'n':count,'sample_content_sha256':hashlib.sha256(samples.tobytes()).hexdigest()}


def run_primary_final(roles_directory, development, confirmation, selector_lock, output, protocol_path,
                      execution_path, *, resume=False, max_new_cells=None):
    selector=_locked_selector(selector_lock,development,protocol_path)
    if read_json(Path(development)/'run.lock.json')['execution_sha256']!=sha256(execution_path):
        raise ValueError('Execution changed after development')
    confirmations=read_json(Path(confirmation)/'results.json')
    if not confirmations['complete_table'] or confirmations['selector']!=selector:
        raise ValueError('Complete independent confirmation required before final test')
    out,protocol,execution,state=_start(output,roles_directory,protocol_path,execution_path,'final',resume,
        {'selector_lock_sha256':sha256(selector_lock),'development_lock_sha256':sha256(Path(development)/'run.lock.json'),
         'confirmation_results_sha256':sha256(Path(confirmation)/'results.json')})
    state,schema,roles=open_roles(roles_directory,('fit','reference','calibration','final'))
    fit,reference,calibration,final=[roles[k] for k in ('fit','reference','calibration','final')]
    benign=final['y']==0; malware=final['y']==1; rows=[]; new_cells=0
    for seed in protocol['seeds']:
        seed_dir=out/f'seed_{seed}'; seed_dir.mkdir(exist_ok=True)
        _copy_exact(Path(development)/f'seed_{seed}/clean.txt',seed_dir/'clean.txt')
        clean=lgb.Booster(model_file=str(seed_dir/'clean.txt')); schema.check_model(clean)
        views={}; paths={}
        for view in schema.views:
            path=seed_dir/f'view_{view}.txt'
            views[view]=train(fit['X'],fit['y'],path,execution,seed,view=view,schema=schema); paths[view]=path
        clean_final_p=clean.predict(final['X'],num_threads=4)
        for family,rate in itertools.product(protocol['family_geometry'],protocol['rates']):
            src,dev=_verified_development_cell(development,selector,family,rate,seed)
            confirm_path=Path(confirmation)/f'seed_{seed}'/family/f'rate_{rate:g}/result.json'
            confirm=read_json(confirm_path)
            if confirm.get('development_result_sha256')!=sha256(src/'result.json'):
                raise ValueError('Confirmation does not match frozen development cell')
            dest=seed_dir/family/f'rate_{rate:g}'; dest.mkdir(parents=True,exist_ok=True)
            result_path=dest/'result.json'
            if result_path.exists():
                row=read_json(result_path)
                for name,expected in row.get('artifact_sha256',{}).items():
                    if sha256(dest/name)!=expected: raise ValueError('Final cell artifact changed')
                rows.append(row); continue
            base={'dataset':schema.dataset,'phase':'final','family':family,'rate':rate,'seed':seed,'selector':selector,
                  'confirmation_result_sha256':sha256(confirm_path),
                  'independently_confirmed_strong_and_stealth':confirm.get('independently_confirmed_strong_and_stealth',False),
                  'fit_model_policy':'Adopt exact development model trained on locked fit with unchanged trigger/params; no retraining on held-out data'}
            if dev['status']!='complete' or confirm['status']!='complete':
                row={**base,'status':dev['status'] if dev['status']!='complete' else confirm['status'],
                     'error':'No complete frozen model/confirmation for this declared cell'}
            else:
                print(f'{schema.dataset} final pair: {seed} / {family} / {rate:g}',flush=True)
                _copy_exact(src/'poisoned.txt',dest/'poisoned.txt')
                _copy_exact(src/'attack.json',dest/'attack.json')
                model=lgb.Booster(model_file=str(dest/'poisoned.txt')); schema.check_model(model)
                trigger=VectorTrigger(**read_json(dest/'attack.json')['trigger'])
                config={**execution['detector'],'seed':seed}; calibrate_seconds={}; objects={}
                for variant in ('reduced','full'):
                    bundle=dest/('bundle_'+variant)
                    if bundle.exists():
                        objects[variant]=Detector.load(bundle,expected_schema=schema,expected_dataset=schema.dataset)
                        calibrate_seconds[variant]=None
                    else:
                        started=time.perf_counter()
                        obj=Detector(model,reference['X'],views if variant=='full' else None,config,schema=schema).fit(calibration['X'])
                        calibrate_seconds[variant]=time.perf_counter()-started
                        obj.save(bundle,dest/'poisoned.txt',paths if variant=='full' else None)
                        objects[variant]=obj
                    obj=objects[variant]
                    expected_calibration=hashlib.sha256(np.ascontiguousarray(calibration['X']).tobytes()).hexdigest()
                    if (obj.model.model_to_string()!=model.model_to_string() or obj.config!={**config}
                            or not np.array_equal(obj.reference,reference['X'])
                            or obj.calibration_content_sha256!=expected_calibration):
                        raise ValueError('Partial bundle does not match frozen main/reference/calibration/config')
                xt=trigger.apply(final['X'][malware],schema)
                predictions=dest/'paired_predictions.npz'
                # A partial evaluation may have left a completed NPZ but no result;
                # preserve it and write a fresh attempt rather than overwrite evidence.
                attempt=1
                while predictions.exists():
                    predictions=dest/f'paired_predictions_attempt_{attempt}.npz'; attempt+=1
                evaluation=evaluate_pair(objects['reduced'],objects['full'],clean,final['X'][benign],final['X'][malware],xt,
                    final['ids'][benign],final['ids'][malware],batch_size=execution['score_batch_size'],
                    bootstrap_repeats=execution['bootstrap_repeats'],seed=seed,artifacts=predictions)
                original_p=model.predict(final['X'],num_threads=4)
                resource={'calibration_seconds':calibrate_seconds,'process_peak_memory':_peak_memory(),
                    'peak_memory_scope':'whole shared process; not attributable to a detector variant',
                    'model_bytes':{'reduced':(dest/'poisoned.txt').stat().st_size,
                                  'full':(dest/'poisoned.txt').stat().st_size+sum(p.stat().st_size for p in paths.values())},
                    'latency':_latency_pair(objects['reduced'],objects['full'],final['X'][benign],xt,execution['latency_samples'],seed)}
                row={**base,'status':'complete','evaluation':evaluation,'resources':resource,
                    'clean_performance':performance_from_predictions(clean_final_p,final['y'],protocol['malware_threshold']),
                    'poisoned_clean_performance':performance_from_predictions(original_p,final['y'],protocol['malware_threshold']),
                    'artifact_sha256':{name:sha256(dest/name) for name in ('poisoned.txt','attack.json',predictions.name)},
                    'bundle_manifest_sha256':{v:sha256(dest/('bundle_'+v)/'bundle.json') for v in objects},
                    'interpretation':'Weak/unconfirmed attack cells retained and labeled; detector efficacy claims require independently viable attacks'}
                del model,xt,objects; gc.collect()
            write_json(result_path,row); rows.append(row); new_cells+=1
            write_json(out/'results.json',{'phase':'final','dataset':schema.dataset,'selector':selector,'rows':rows,
                'complete_table':len(rows)==len(expected_cells(protocol,[schema.dataset]))})
            if max_new_cells is not None and new_cells>=max_new_cells:
                return {'dataset':schema.dataset,'phase':'final','status':'checkpoint','rows':len(rows)}
        del clean,views; gc.collect()
    return {'dataset':schema.dataset,'phase':'final','status':'complete','rows':len(rows)}
