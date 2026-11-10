"""Materialize fit/selection/development only, without opening held-out arrays.

V2 reuses official train vectors by SHA256. V3 streams only train ZIP members
and vectorizes selected records at audited locations. No PE execution occurs.
"""
import argparse
import ctypes
from collections import defaultdict
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import zipfile
import numpy as np
from numpy.lib.format import open_memmap

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from xsentinel.schema import get_schema,V2_PRIMARY,V3_PRIMARY
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.data.vectorizer import Vectorizer

ROLES=('fit','selection','development')


def resource_memory():
    class MEMORY(ctypes.Structure):
        _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[
            (k,ctypes.c_ulonglong) for k in ('total','available','page_total','page_available','virtual','virtual_available','extended')]
    status=MEMORY(); status.length=ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError('Cannot measure RAM gate')
    return {'total':status.total,'available':status.available}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',required=True); p.add_argument('--dataset',choices=['EMBER2018','EMBER2024'],required=True)
    p.add_argument('--output',required=True); a=p.parse_args()
    manifest=Path(a.manifest); out=Path(a.output); state=read_json(manifest/f'{a.dataset}.roles.json')
    schema=get_schema(V2_PRIMARY if a.dataset=='EMBER2018' else V3_PRIMARY)
    required=sum(state['sizes'][r] for r in ROLES)*schema.dim*4
    free=shutil.disk_usage(ROOT).free; reserve=max(2*1024**3,int(required*.2))
    memory=resource_memory()
    if free<required+reserve: raise OSError('Insufficient disk headroom; do not shrink roles')
    if memory['available']<2*1024**3: raise OSError('Less than 2GiB available RAM; do not start materialization')
    if out.exists() and any(out.iterdir()): raise FileExistsError('Fresh output required')
    out.mkdir(parents=True,exist_ok=True)
    lock={'dataset':a.dataset,'schema':schema.version,'schema_sha256':schema.fingerprint,
          'roles_manifest_sha256':sha256(manifest/f'{a.dataset}.roles.json'),
          'steward_sha256':sha256(manifest/'steward.sqlite'),'roles_opened':list(ROLES),
          'code_sha256':sha256(__file__),'vectorizer_sha256':sha256(ROOT/'src/xsentinel/data/vectorizer.py'),
          'v3_raw_sha256':sha256(ROOT/'src/xsentinel/data/v3_raw.py'),
          'disk_free_before':free,'projected_vector_bytes':required,'reserve':reserve,'memory_before':memory}
    write_json(out/'materialization.lock.json',lock)
    db=sqlite3.connect('file:'+str((manifest/'steward.sqlite').resolve()).replace('\\','/')+'?mode=ro',uri=True)
    arrays={}; locations=defaultdict(dict)
    for role in ROLES:
        rows=db.execute('select id,label,archive,member,line from roles where dataset=? and role=? order by id',(a.dataset,role)).fetchall()
        if len(rows)!=state['sizes'][role] or [r[0] for r in rows]!=state['ids'][role]:
            raise ValueError('Manifest/steward mismatch')
        arrays[role]=open_memmap(out/f'{role}.X.npy',mode='w+',dtype='float32',shape=(len(rows),schema.dim))
        np.save(out/f'{role}.y.npy',np.asarray([r[1] for r in rows],dtype=np.int8))
        np.save(out/f'{role}.ids.npy',np.asarray([r[0] for r in rows],dtype='S64'))
        for pos,(sid,label,archive,member,line) in enumerate(rows):
            if a.dataset=='EMBER2024':
                if not archive.endswith('_train.zip'): raise ValueError('Optimizer attempted test archive')
                locations[archive,member][line]=(role,pos,sid,label)
    db.close()
    counts={r:0 for r in ROLES}; flags=defaultdict(int)
    if a.dataset=='EMBER2018':
        source=ROOT/'data/ember2018_full'
        # No test X/y is opened; labels are checked against train metadata only.
        ids=np.load(source/'ids_train.npy',allow_pickle=False).astype(str)
        lookup={sid:i for i,sid in enumerate(ids)}
        X=np.load(source/'X_train.npy',mmap_mode='r',allow_pickle=False)
        y=np.load(source/'y_train.npy',mmap_mode='r',allow_pickle=False)
        for role in ROLES:
            chosen=np.asarray([lookup[s] for s in state['ids'][role]])
            labels=np.load(out/f'{role}.y.npy')
            if not np.array_equal(y[chosen],labels): raise ValueError('V2 metadata label mismatch')
            for offset in range(0,len(chosen),128):
                arrays[role][offset:offset+128]=X[chosen[offset:offset+128]]
            counts[role]=len(chosen); arrays[role].flush()
    else:
        vectorizer=Vectorizer(schema)
        for (archive,member),wanted in sorted(locations.items()):
            path=ROOT/'data/ember2024_archives'/archive
            # Record source compressed archive hash before vectorization.
            lock.setdefault('archive_sha256',{})[archive]=sha256(path)
            with zipfile.ZipFile(path) as z, z.open(member) as stream:
                remaining=len(wanted)
                for number,line in enumerate(stream,1):
                    if number not in wanted: continue
                    role,pos,sid,label=wanted[number]; record=json.loads(line)
                    if record['sha256']!=sid or record['label']!=label: raise ValueError('V3 provenance mismatch')
                    x=vectorizer.transform(record); arrays[role][pos]=x
                    flags[str(int(x[2]))]+=1; counts[role]+=1; remaining-=1
                    if not remaining: break
                if remaining: raise ValueError('Missing selected V3 records')
            for arr in arrays.values(): arr.flush()
            print(archive,member,counts,flush=True)
    for role in ROLES:
        if counts[role]!=state['sizes'][role]: raise ValueError('Incomplete role')
        for start in range(0,len(arrays[role]),128):
            if not np.isfinite(arrays[role][start:start+128]).all(): raise ValueError('Nonfinite vectors')
        arrays[role].flush()
    write_json(out/'COMPLETE.json',{'status':'ATTACKER_ROLES_MATERIALIZED','lock':lock,'counts':counts,
        'v3_original_is_pe_counts':dict(flags),'feature_mutation':False,'heldout_features_opened':[],
        'array_sha256':{p.name:sha256(p) for p in sorted(out.glob('*.npy'))}})


if __name__=='__main__': main()
