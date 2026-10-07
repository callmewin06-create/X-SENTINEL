"""Fit-only resource measurement. No official test vectors or detector scoring."""
import gc
import time
from pathlib import Path
import numpy as np
from xsentinel.schema import get_schema
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.experiment import train
from xsentinel.attacks.development import _peak_memory


def resource_pilot(roles_directory,output,config_path,seed):
    roles_dir=Path(roles_directory); state=read_json(roles_dir/'roles.json')
    config=read_json(config_path); schema=get_schema(state['schema'])
    if state['schema_sha256']!=schema.fingerprint or sha256(roles_dir/'roles.npz')!=state['roles_sha256']:
        raise ValueError('Primary role/schema checksum mismatch')
    out=Path(output)
    if out.exists() and any(out.iterdir()): raise FileExistsError('Use a fresh resource pilot output directory')
    source=Path(state['source_directory'])
    if sha256(source/'dataset.json')!=state['source_dataset_sha256']:
        raise ValueError('Source dataset manifest changed')
    data={}
    for kind in ('X','y','ids'):
        name=f'{kind}_train.npy'
        if sha256(source/name)!=state['source_array_sha256'][name]: raise ValueError('Source training checksum mismatch')
        data[kind]=np.load(source/name,mmap_mode='r',allow_pickle=False)
    with np.load(roles_dir/'roles.npz',allow_pickle=False) as a: fit=a['fit']
    if data['ids'][fit].astype(str).tolist()!=state['ids']['fit']:
        raise ValueError('Primary fit source IDs changed')
    n=config['fit_rows']
    if not isinstance(n,int) or n<2 or n%2: raise ValueError('Positive even pilot fit size required')
    rng=np.random.default_rng(seed); chosen=[]
    for label in (0,1):
        pool=fit[data['y'][fit]==label]
        if len(pool)<n//2: raise ValueError('Insufficient primary fit rows')
        chosen.extend(rng.choice(pool,n//2,replace=False).tolist())
    chosen=np.sort(chosen); out.mkdir(parents=True,exist_ok=True)
    X=np.asarray(data['X'][chosen]); y=np.asarray(data['y'][chosen])
    started=time.perf_counter()
    model=train(X,y,out/'clean_resource_only.txt',config,seed,schema=schema)
    train_seconds=time.perf_counter()-started
    schema.check_model(model)
    write_json(out/'resource.json',{'purpose':'resource pilot only; no attack/detector efficacy conclusion',
        'dataset':schema.dataset,'schema':schema.version,'schema_sha256':schema.fingerprint,'seed':seed,
        'fit_rows':n,'class_counts':{str(label):int(np.sum(y==label)) for label in (0,1)},
        'train_seconds':train_seconds,'process_memory':_peak_memory(),'test_arrays_opened':False,
        'detector_calibrated':False,'final_predictions_computed':False,'config':config,
        'config_sha256':sha256(config_path),'roles_manifest_sha256':sha256(roles_dir/'roles.json'),
        'fit_source_ids':data['ids'][chosen].astype(str).tolist(),
        'model_sha256':sha256(out/'clean_resource_only.txt')})
    del model,X,y; gc.collect()
    return {'dataset':schema.dataset,'fit_rows':n,'train_seconds':train_seconds,
            'output':str(out.resolve()),'process_memory':read_json(out/'resource.json')['process_memory']}
