"""Checkpoint and phase separation on tiny synthetic datasets; no efficacy claims."""
from pathlib import Path
import json
import numpy as np
import pytest
from xsentinel.schema import V2_PRIMARY,V3_PRIMARY,get_schema
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.data.protocol import freeze_primary_splits
from xsentinel.primary_workflow import (open_roles,run_primary_development,lock_primary_selector,
    run_primary_confirmation,run_primary_final)
from xsentinel.primary_reporting import report_primary


def create_source(tmp_path,version,sizes):
    schema=get_schema(version); source=tmp_path/schema.dataset/'source'; source.mkdir(parents=True)
    rng=np.random.default_rng(74)
    for split,n in (('train',100),('test',20)):
        X=rng.normal(size=(n,schema.dim)).astype('float32')
        # Near-deterministic structural label; all restricted columns vary.
        y=np.tile(np.array([0,1],dtype='int8'),n//2)
        X[:,schema.restricted[0]]=2*y-1
        ids=np.array([f'{(0 if split=="train" else 1000)+(0 if version==V2_PRIMARY else 10000)+i:064x}' for i in range(n)],dtype='S64')
        for kind,data in (('X',X),('y',y),('ids',ids)): np.save(source/f'{kind}_{split}.npy',data)
    write_json(source/'dataset.json',{'schema':version,'pilot':False,
        'array_sha256':{p.name:sha256(p) for p in source.glob('*.npy')}})
    roles=tmp_path/schema.dataset/'roles'
    freeze_primary_splits(source,roles,version,sizes,17)
    return roles


def test_primary_development_lock_confirmation_and_final(tmp_path):
    protocol=read_json('configs/primary_protocol.json')
    protocol['sample_sizes']={'fit':20,'selection':8,'development':8,'confirmation':8,'reference':2,'calibration':2,'final':10}
    protocol['seeds']=[17]; protocol['rates']=[.1]
    protocol['family_geometry']={'concentrated_structural':protocol['family_geometry']['concentrated_structural']}
    protocol['attack_screen']['min_eligible']=1
    pp=tmp_path/'protocol.json'; write_json(pp,protocol)
    execution=read_json('configs/primary_execution.json')
    execution.update(rounds=4,view_rounds=3,bootstrap_repeats=5,latency_samples=2)
    execution['params'].update(num_leaves=5,min_data_in_leaf=1,num_threads=2)
    ep=tmp_path/'execution.json'; write_json(ep,execution)
    devs=[]; role_dirs=[]
    for version in (V2_PRIMARY,V3_PRIMARY):
        roles=create_source(tmp_path,version,protocol['sample_sizes']); role_dirs.append(roles)
        source=Path(read_json(roles/'roles.json')['source_directory'])
        # Development succeeds while official-test arrays are unavailable.
        hidden=source/'X_test.npy.hidden'; (source/'X_test.npy').rename(hidden)
        dest=roles.parent/'development'; devs.append(dest)
        first=run_primary_development(roles,dest,pp,ep,max_new_cells=1)
        assert first['status']=='checkpoint' and first['rows']==1
        result=run_primary_development(roles,dest,pp,ep,resume=True)
        assert result['rows']==2 and result['status']=='complete'
        assert read_json(dest/'run_manifest.json')['test_arrays_opened'] is False
        with pytest.raises(FileExistsError): run_primary_development(roles,dest,pp,ep)
        hidden.rename(source/'X_test.npy')
    common=tmp_path/'selector.lock.json'
    with pytest.raises(ValueError,match='per dataset'): lock_primary_selector(devs[:1],pp,common)
    lock_primary_selector(devs,pp,common)
    lock_sha=sha256(common)
    for roles,dev in zip(role_dirs,devs):
        confirmation=roles.parent/'confirmation'
        result=run_primary_confirmation(roles,dev,common,confirmation,pp,ep)
        assert result['rows']==1 and sha256(common)==lock_sha
        final=roles.parent/'final'
        run_primary_final(roles,dev,confirmation,common,final,pp,ep)
        result=read_json(final/'results.json')
        assert result['complete_table'] and result['rows'][0]['status']=='complete'
        cell=final/'seed_17/concentrated_structural/rate_0.1'
        assert (cell/'paired_predictions.npz').exists()
        npz=np.load(cell/'paired_predictions.npz')
        assert len(npz['malware_ids'])==5 and len(npz['benign_ids'])==5
        assert result['rows'][0]['evaluation']['dataset']==read_json(roles/'roles.json')['dataset']
        assert run_primary_final(roles,dev,confirmation,common,final,pp,ep,resume=True)['status']=='complete'
    report=report_primary([roles.parent/'final' for roles in role_dirs],pp,tmp_path/'report')
    assert report['counts']['EMBER2018']['complete']==1
    assert report['counts']['EMBER2024']['complete']==1
    assert len(read_json(tmp_path/'report/report.json')['table'])==8


def test_open_roles_refuses_corrupt_source_before_training(tmp_path):
    sizes={'fit':20,'selection':8,'development':8,'confirmation':8,'reference':2,'calibration':2,'final':10}
    roles=create_source(tmp_path,V2_PRIMARY,sizes)
    source=Path(read_json(roles/'roles.json')['source_directory'])
    X=np.load(source/'X_train.npy'); X[0,0]+=1; np.save(source/'X_train.npy',X)
    with pytest.raises(ValueError,match='checksum'): open_roles(roles,('fit',))
