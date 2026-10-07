"""Small raw ZIP fixtures test provenance, exclusion and restart, not attack efficacy."""
import copy
import json
from pathlib import Path
import zipfile
import numpy as np
import pytest
from test_primary import v3_record
from xsentinel.data.ember2024 import metadata, prepare_ember2024
from xsentinel.data.protocol import freeze_primary_splits
from xsentinel.schema import V3_PRIMARY
from xsentinel.utils import write_json, sha256, read_json


def fixture_archives(tmp_path):
    folder=tmp_path/'archives'; folder.mkdir()
    old=tmp_path/'data/ember2018_full'; old.mkdir(parents=True)
    excluded=f'{1:064x}'
    np.save(old/'ids_train.npy', np.array([excluded],dtype='S64'))
    np.save(old/'ids_test.npy', np.array([f'{9999:064x}'],dtype='S64'))
    entries=[]; counter=0
    for kind in ('Dot_Net','Win32','Win64'):
        for split in ('train','test'):
            rows=[]
            for i in range(8):
                counter+=1; raw=copy.deepcopy(v3_record())
                raw['general']['size']=counter*100
                rows.append({'sha256':f'{counter:064x}','label':i%2,'file_type':kind,**raw})
            path=folder/f'{kind}_{split}.zip'; member=f'week_{kind}_{split}.jsonl'
            with zipfile.ZipFile(path,'w') as z:
                z.writestr(member,'\n'.join(json.dumps(r) for r in rows)+'\n')
            with zipfile.ZipFile(path) as z:
                members=[{'name':m.filename,'bytes':m.file_size,'crc':m.CRC} for m in z.infolist()]
            entries.append({'name':path.name,'path':str(path.resolve()),'bytes':path.stat().st_size,
                            'sha256':sha256(path),'members':members,'split':split})
    proof=tmp_path/'verification.json'
    write_json(proof,{'files':entries,'revision':'fixture'})
    protocol=tmp_path/'protocol.json'
    sizes={'fit':2,'selection':2,'development':2,'confirmation':2,'reference':1,'calibration':1,'final':2}
    write_json(protocol,{'datasets':{'EMBER2024':V3_PRIMARY},'sample_sizes':sizes,'split_seed':17,'pending':{}})
    return folder,proof,protocol,sizes,excluded


def test_metadata_prefix_wrapper_and_validation():
    r={'sha256':'a'*64,'label':0,'file_type':'Win32',**v3_record()}
    line=json.dumps(r).encode()
    assert metadata(line)==('a'*64,0,'Win32')
    assert metadata(json.dumps({'sha256':'b'*64,'label':1,'file_type':'Win64','features':v3_record()}).encode())==('b'*64,1,'Win64')
    r['label']=True
    with pytest.raises(ValueError): metadata(json.dumps(r).encode())


def test_budgeted_zip_preparation_and_frozen_roles(tmp_path):
    folder,proof,protocol,sizes,excluded=fixture_archives(tmp_path)
    out=tmp_path/'prepared'
    result=prepare_ember2024(folder,out,proof,protocol,tmp_path)
    assert result['counts']=={'train':10,'test':2}
    audit=read_json(out/'audit_summary.json')
    assert audit['cross_dataset_matches']==1
    ids=np.load(out/'ids_train.npy').astype(str)
    assert excluded not in ids and len(set(ids))==10
    X=np.load(out/'X_train.npy'); assert X.shape==(10,2568) and np.isfinite(X).all()
    assert result['test_predictions_computed'] is False
    with pytest.raises(FileExistsError): prepare_ember2024(folder,out,proof,protocol,tmp_path)
    assert prepare_ember2024(folder,out,proof,protocol,tmp_path,resume=True)==result
    freeze_primary_splits(out,tmp_path/'roles',V3_PRIMARY,sizes,17)
    roles=read_json(tmp_path/'roles/roles.json')
    assert roles['checks']['all_roles_disjoint']
    (out/'X_train.npy').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='checksum'): prepare_ember2024(folder,out,proof,protocol,tmp_path,resume=True)


def test_duplicate_archive_id_is_rejected(tmp_path):
    folder,proof,protocol,_,_=fixture_archives(tmp_path)
    state=read_json(proof); second=state['files'][1]; path=Path(second['path'])
    with zipfile.ZipFile(path) as z:
        name=z.namelist()[0]; rows=[json.loads(line) for line in z.read(name).splitlines()]
    rows[0]['sha256']=f'{1:064x}'
    with zipfile.ZipFile(path,'w') as z: z.writestr(name,'\n'.join(json.dumps(r) for r in rows)+'\n')
    with zipfile.ZipFile(path) as z:
        second['members']=[{'name':m.filename,'bytes':m.file_size,'crc':m.CRC} for m in z.infolist()]
    second.update(bytes=path.stat().st_size,sha256=sha256(path)); write_json(proof,state)
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError): prepare_ember2024(folder,tmp_path/'prepared',proof,protocol,tmp_path)


def test_approved_duplicate_merge_and_conflict_exclusion(tmp_path):
    folder,proof,protocol,_,_=fixture_archives(tmp_path)
    state=read_json(proof)
    for index in (0,1):
        entry=state['files'][index]; path=Path(entry['path'])
        with zipfile.ZipFile(path) as z:
            member=z.namelist()[0]; rows=[json.loads(r) for r in z.read(member).splitlines()]
        if index==0:
            same=copy.deepcopy(rows[2]); same['caps']=['extra tag']; rows.append(same)
            conflict=copy.deepcopy(rows[3]); conflict['general']['size']+=1; rows.append(conflict)
        else:
            rows[0]['sha256']=f'{2:064x}'
        with zipfile.ZipFile(path,'w') as z: z.writestr(member,'\n'.join(json.dumps(r) for r in rows)+'\n')
        with zipfile.ZipFile(path) as z:
            entry['members']=[{'name':m.filename,'bytes':m.file_size,'crc':m.CRC} for m in z.infolist()]
        entry.update(bytes=path.stat().st_size,sha256=sha256(path))
    write_json(proof,state)
    policy=tmp_path/'duplicates.json'
    write_json(policy,{'duplicate_policy':'merge_equal_features_exclude_conflicts_v1'})
    out=tmp_path/'prepared'
    result=prepare_ember2024(folder,out,proof,protocol,tmp_path,duplicate_policy_path=policy)
    audit=read_json(out/'audit_summary.json')
    assert audit['duplicate_occurrences']==3 and audit['conflicting_ids_excluded']==2
    assert result['counts']=={'train':10,'test':2}
    ids=set(np.load(out/'ids_train.npy').astype(str))|set(np.load(out/'ids_test.npy').astype(str))
    assert f'{2:064x}' not in ids and f'{4:064x}' not in ids


def test_official_pe_zero_flag_preserved_and_audited(tmp_path):
    from xsentinel.data.vectorizer import Vectorizer
    folder,proof,protocol,_,_=fixture_archives(tmp_path)
    state=read_json(proof); expected={}; totals={}
    vectorizer=Vectorizer(V3_PRIMARY)
    for entry in state['files']:
        path=Path(entry['path'])
        with zipfile.ZipFile(path) as z:
            member=z.namelist()[0]; rows=[json.loads(line) for line in z.read(member).splitlines()]
        for i,row in enumerate(rows):
            row['general']['is_pe']=int(i%3==0)
            expected[row['sha256']]=vectorizer.transform(row)
            key=(entry['split'],row['file_type'],row['label'],row['general']['is_pe'])
            totals[key]=totals.get(key,0)+1
        with zipfile.ZipFile(path,'w') as z: z.writestr(member,'\n'.join(json.dumps(r) for r in rows)+'\n')
        with zipfile.ZipFile(path) as z:
            entry['members']=[{'name':m.filename,'bytes':m.file_size,'crc':m.CRC} for m in z.infolist()]
        entry.update(bytes=path.stat().st_size,sha256=sha256(path))
    write_json(proof,state)
    with pytest.raises(ValueError,match='explicitly approved'):
        prepare_ember2024(folder,tmp_path/'strict',proof,protocol,tmp_path)
    policy=tmp_path/'vector_policy.json'
    write_json(policy,{'policy':'official_pe_scope_keep_original_is_pe_v1'})
    out=tmp_path/'approved'
    result=prepare_ember2024(folder,out,proof,protocol,tmp_path,vector_policy_path=policy)
    audit=read_json(out/'is_pe_audit.json')
    actual={(r['partition'],r['file_type'],r['label'],r['is_pe']):r['count'] for r in audit['raw_occurrences']}
    assert actual==totals and sum(r['count'] for r in audit['unique_representatives'])==48
    assert sum(r['count'] for r in audit['materialized'])==12
    zeros=0
    for split in ('train','test'):
        for sid,x in zip(np.load(out/f'ids_{split}.npy').astype(str),np.load(out/f'X_{split}.npy')):
            np.testing.assert_array_equal(x,expected[sid]); zeros+=int(x[2]==0)
    assert zeros>0 and audit['feature_mutation'] is False
    assert prepare_ember2024(folder,out,proof,protocol,tmp_path,resume=True,vector_policy_path=policy)==result
    with pytest.raises(ValueError,match='policy changed'):
        prepare_ember2024(folder,out,proof,protocol,tmp_path,resume=True)
    (out/'is_pe_audit.json').write_text('{}')
    with pytest.raises(ValueError,match='checksum'):
        prepare_ember2024(folder,out,proof,protocol,tmp_path,resume=True,vector_policy_path=policy)
