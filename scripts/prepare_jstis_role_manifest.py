"""Metadata-only steward: exclusion ledger and seven fresh SHA256 roles.

Never reads X/y feature arrays or archive record bodies. Allocating final IDs
does not authorize optimizer access to final labels/features. This is ID-level
disjointness from inventoried local history, not family/time independence.
"""
import argparse
import json
from pathlib import Path
import sqlite3
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from xsentinel.data.protocol import collect_seen_ids
from xsentinel.utils import read_json,write_json,sha256

SIZES={'fit':200000,'selection':10000,'development':10000,'confirmation':10000,
       'reference':500,'calibration':2000,'final':20000}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True); p.add_argument('--seed',type=int,default=20261109)
    args=p.parse_args(); out=Path(args.output)
    if out.exists() and any(out.iterdir()): raise FileExistsError('Fresh output required')
    out.mkdir(parents=True,exist_ok=True)
    seen,sources=collect_seen_ids(ROOT)
    def record(path,ids,reason):
        values={(s.decode('ascii') if isinstance(s,(bytes,np.bytes_)) else str(s)).lower() for s in ids}
        if any(len(s)!=64 or any(c not in '0123456789abcdef' for c in s) for s in values):
            raise ValueError('Non SHA256 ID in '+str(path))
        seen.update(values); sources.append({'path':str(path.resolve()),'sha256':sha256(path),
            'unique_ids':len(values),'reason':reason})
    for path in sorted((ROOT/'data/primary').glob('*/protocol_v2/roles.json')):
        record(path,[s for ids in read_json(path)['ids'].values() for s in ids],'frozen primary seven roles')
    for parent in ['outputs/revision_2026_10_13/fresh_validation',
                   'outputs/fusion_binary_latency_2026_10_20/final_pool']:
        for path in sorted((ROOT/parent).glob('*/ids.npy')):
            record(path,np.load(path,allow_pickle=False),'historical validation or latency feature pool')
    public=ROOT/'outputs/teacher_revision_v2_thang_2026_10_30/public_shadow'
    path=public/'split_ids.npz'
    if sha256(path)!=read_json(public/'training_provenance.json')['split_ids_sha256']:
        raise ValueError('Public split checksum mismatch')
    # Trusted local producer train_public_shadow_bodmas.py writes string-object
    # arrays; verify its frozen receipt before permitting that legacy format.
    with np.load(path,allow_pickle=True) as z:
        record(path,[s for k in ('train','validation') for s in z[k]],'public Shadow train and validation')
    db=sqlite3.connect(str(out/'steward.sqlite'),uri=True)
    db.execute('create table excluded(id text primary key)')
    db.executemany('insert into excluded values (?)',((s,) for s in sorted(seen)))
    db.execute('create table roles(dataset text,role text,id text,label integer,partition text,'
               'archive text,member text,line integer,primary key(dataset,id))')
    reports={}
    for dataset,source in [('EMBER2018','data/ember2018_full/audit.sqlite'),
                           ('EMBER2024','data/ember2024_primary_source_v2/audit.sqlite')]:
        path=ROOT/source
        # Attach read-only source; SQL joins metadata only. Source is never modified.
        db.execute('attach database ? as source',('file:'+path.resolve().as_posix()+'?mode=ro',))
        available={}; groups={}; rng=np.random.default_rng(args.seed)
        for partition in ('train','test'):
            for label in (0,1):
                rows=db.execute('select s.id from source.samples s left join excluded e on s.id=e.id '
                    'where s.partition=? and s.label=? and e.id is null order by s.id',
                    (partition,label)).fetchall()
                ids=np.asarray([r[0] for r in rows],dtype='U64'); del rows
                groups[partition,label]=rng.permutation(ids)
                available[f'{partition}_{label}']=len(ids)
        role_ids={}; offset={0:0,1:0}
        for role,n in SIZES.items():
            chosen=[]
            for label in (0,1):
                count=(n if label==0 else 0) if role in ('reference','calibration') else n//2
                partition='test' if role=='final' else 'train'
                start=0 if role=='final' else offset[label]
                pool=groups[partition,label]; selected=pool[start:start+count]
                if len(selected)!=count: raise ValueError(f'Insufficient fresh {dataset}/{role}/{label}')
                if role!='final': offset[label]+=count
                chosen.extend(selected.tolist())
                db.executemany('insert into roles(dataset,role,id,label,partition) values (?,?,?,?,?)',
                    ((dataset,role,s,label,partition) for s in selected.tolist()))
            role_ids[role]=sorted(chosen)
        if dataset=='EMBER2024':
            db.execute('update roles set archive=(select archive from source.samples s where s.id=roles.id),'
                'member=(select member from source.samples s where s.id=roles.id),'
                'line=(select line from source.samples s where s.id=roles.id) where dataset=?',(dataset,))
        db.commit(); db.execute('detach database source')
        write_json(out/f'{dataset}.roles.json',{'dataset':dataset,'split_seed':args.seed,'sizes':SIZES,
            'ids':role_ids,'source_metadata':str(path.resolve()),'source_metadata_sha256':sha256(path),
            'features_opened':False,'availability_after_exclusions':available,
            'access':'steward allocation only; optimizer may read fit/selection/development only'})
        reports[dataset]=available
        print(dataset,available,flush=True)
    overlap=db.execute('select count(*) from roles join excluded using(id)').fetchone()[0]
    if overlap: raise AssertionError('Exposure overlap')
    db.close()
    write_json(out/'AUDIT.json',{'status':'METADATA_ROLES_ALLOCATED_NOT_VECTORIZED','sizes':SIZES,
        'seed':args.seed,'known_excluded_unique_ids':len(seen),'exposure_sources':sources,
        'availability':reports,'roles_vs_known_exposure_overlap':overlap,'feature_arrays_opened':[],
        'limitations':['Uninventoried external exposures cannot be excluded',
                      'SHA256 disjointness does not prove family/group/time disjointness'],
        'code_sha256':sha256(__file__),'steward_sha256':sha256(out/'steward.sqlite')})


if __name__=='__main__': main()
