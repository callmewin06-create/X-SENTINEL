import json
import sqlite3
import time
from pathlib import Path
import numpy as np
from numpy.lib.format import open_memmap
from xsentinel.data.vectorizer import Vectorizer
from xsentinel.schema import DIM, SCHEMA_VERSION,get_schema
from xsentinel.utils import write_json, sha256, read_json

def records(files, limit=None):
    for path in files:
        count=0
        with path.open(encoding='utf8') as f:
            for line_no,line in enumerate(f,1):
                if limit is not None and count>=limit:
                    break
                try:
                    r=json.loads(line)
                    if r['label'] not in (-1,0,1):
                        raise ValueError('Unknown label')
                    sid=r['sha256']
                    if len(sid)!=64 or any(c not in '0123456789abcdef' for c in sid):
                        raise ValueError('Invalid SHA256')
                except Exception as exc:
                    raise ValueError(f'{path}:{line_no}: {exc}') from exc
                count+=1
                yield r

def prepare(raw_dir, out_dir, limit=None, batch_size=128):
    raw=Path(raw_dir); out=Path(out_dir)
    files={'train':[raw/f'train_features_{i}.jsonl' for i in range(6)],'test':[raw/'test_features.jsonl']}
    for fs in files.values():
        for f in fs:
            if not f.is_file():
                raise FileNotFoundError(f)
    out.mkdir(parents=True,exist_ok=True)
    if (out/'dataset.json').exists() or (out/'audit.sqlite').exists():
        raise FileExistsError('Use a fresh output directory; existing data are not overwritten')
    started=time.perf_counter(); db=sqlite3.connect(out/'audit.sqlite')
    db.execute('CREATE TABLE samples (id TEXT PRIMARY KEY, partition TEXT, label INTEGER)')
    counts={}; raw_counts={}; duplicates=[]; source=[]
    # Disk-backed uniqueness audit avoids an in-memory million-ID set.
    for partition,fs in files.items():
        counts[partition]=0; raw_counts[partition]={'-1':0,'0':0,'1':0}
        for r in records(fs,limit):
            raw_counts[partition][str(r['label'])]+=1
            try:
                db.execute('INSERT INTO samples VALUES (?,?,?)',(r['sha256'],partition,r['label']))
            except sqlite3.IntegrityError:
                duplicates.append(r['sha256'])
            if r['label']!=-1:
                counts[partition]+=1
        db.commit()
        source += [{'path':str(f.resolve()),'bytes':f.stat().st_size,'mtime_ns':f.stat().st_mtime_ns} for f in fs]
    db.close()
    if duplicates:
        write_json(out/'audit_failure.json',{'duplicate_ids':duplicates,'counts':raw_counts})
        raise ValueError('Duplicate SHA256 within/across official partitions; see audit_failure.json')
    vectorizer=Vectorizer()
    for partition,fs in files.items():
        n=counts[partition]
        if not n:
            raise ValueError(f'No labeled samples in {partition}')
        x=open_memmap(out/f'X_{partition}.npy',mode='w+',dtype='float32',shape=(n,DIM))
        y=open_memmap(out/f'y_{partition}.npy',mode='w+',dtype='int8',shape=(n,))
        ids=open_memmap(out/f'ids_{partition}.npy',mode='w+',dtype='S64',shape=(n,))
        buf=[]; pos=0
        def flush():
            nonlocal pos,buf
            if not buf: return
            end=pos+len(buf); x[pos:end]=vectorizer.transform_batch(buf)
            y[pos:end]=[r['label'] for r in buf]; ids[pos:end]=[r['sha256'] for r in buf]
            pos=end; buf=[]
        for r in records(fs,limit):
            if r['label']==-1: continue
            buf.append(r)
            if len(buf)>=batch_size:
                flush()
                if pos%10000<batch_size:
                    print(f'{partition}: {pos}/{n}',flush=True)
        flush(); x.flush(); y.flush(); ids.flush()
        del x,y,ids
    write_json(out/'dataset.json',{'schema':SCHEMA_VERSION,'counts':counts,'raw_labels':raw_counts,
        'pilot':limit is not None,'raw_record_limit_per_file':limit,'source_files':source,
        'upstream_sha256':sha256(Path(__file__).resolve().parents[1]/'ember_upstream.py'),
        'processing_adapter':'v1: legacy entry-name character hashing; batch equals upstream sample processing',
        'vectorizer_sha256':sha256(Path(__file__).parent/'vectorizer.py'),
        'elapsed_seconds':time.perf_counter()-started,'duplicates':0,
        'array_sha256':{f.name:sha256(f) for f in out.glob('*.npy')}})
    return read_json(out/'dataset.json')

def load_data(directory,expected_schema=None):
    p=Path(directory); meta=read_json(p/'dataset.json')
    schema=get_schema(meta['schema'])
    if expected_schema is not None and schema.version!=get_schema(expected_schema).version:
        raise ValueError('Schema mismatch')
    data={f'{kind}_{split}':np.load(p/f'{kind}_{split}.npy',mmap_mode='r',allow_pickle=False)
          for split in ('train','test') for kind in ('X','y','ids')}
    for split in ('train','test'):
        n=len(data['y_'+split])
        if data['X_'+split].shape!=(n,schema.dim) or data['ids_'+split].shape!=(n,):
            raise ValueError('Dataset array/schema shape mismatch')
    return data

def make_splits(directory, reference=500, calibration=2000, seed=17):
    p=Path(directory)
    if (p/'splits.json').exists():
        raise FileExistsError('Splits already frozen; use a fresh directory')
    d=load_data(p,expected_schema=SCHEMA_VERSION); benign=np.flatnonzero(d['y_test']==0); malware=np.flatnonzero(d['y_test']==1)
    if len(benign)<=reference+calibration or min(reference,calibration)<=0:
        raise ValueError('Insufficient benign test samples for disjoint reference/calibration/final')
    order=np.random.default_rng(seed).permutation(benign)
    splits={'reference':order[:reference], 'calibration':order[reference:reference+calibration],
            'benign':order[reference+calibration:], 'malware':malware}
    np.savez(p/'splits.npz',**splits)
    write_json(p/'splits.json',{'seed':seed,'sizes':{k:len(v) for k,v in splits.items()},
        'ids':{k:d['ids_test'][v].astype(str).tolist() for k,v in splits.items()},
        'dataset_sha256':sha256(p/'dataset.json'),'split_sha256':sha256(p/'splits.npz')})
    return splits
