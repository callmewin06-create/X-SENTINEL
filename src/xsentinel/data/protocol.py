"""Disjoint primary roles; legacy test-derived splits remain untouched."""
import numpy as np
from pathlib import Path
import csv
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.schema import get_schema,SCHEMA_VERSION,V2_PRIMARY

TRAIN_ROLES=('fit','selection','development','confirmation','reference','calibration')


def primary_partitions(y_train, ids_train, y_test, ids_test, sizes, seed, seen_ids=()):
    """Pure planning function. Caller must supply every approved size explicitly.

    Excludes known previously observed IDs from every new role. Source IDs missing
    from external handovers cannot be reconstructed by this function.
    """
    if set(sizes)!=set(TRAIN_ROLES)|{'final'}:
        raise ValueError('All seven primary role sizes must be explicitly supplied')
    for role,n in sizes.items():
        if not isinstance(n,int) or isinstance(n,bool) or n<=0 or (role not in ('reference','calibration') and n%2):
            raise ValueError('Positive even balanced size required: '+role)
    yt=np.asarray(y_train); yv=np.asarray(y_test)
    it=np.asarray(ids_train).astype(str); iv=np.asarray(ids_test).astype(str)
    for y,ids in ((yt,it),(yv,iv)):
        if y.ndim!=1 or ids.shape!=y.shape or not np.isin(y,[0,1]).all():
            raise ValueError('Invalid labeled source IDs')
        if any(len(s)!=64 or any(c not in '0123456789abcdef' for c in s) for s in ids):
            raise ValueError('Source IDs must be lowercase SHA256')
        if len(set(ids))!=len(ids): raise ValueError('Duplicate source SHA256')
    if set(it)&set(iv): raise ValueError('Train/test source overlap')
    seen=set(seen_ids); rng=np.random.default_rng(seed)
    pools={label:rng.permutation(np.flatnonzero((yt==label)&~np.isin(it,list(seen)))) for label in (0,1)}
    needed={label:sum(n if role in ('reference','calibration') and label==0 else
                     0 if role in ('reference','calibration') else n//2
                     for role,n in sizes.items() if role!='final') for label in (0,1)}
    if any(len(pools[label])<needed[label] for label in (0,1)):
        raise ValueError('Insufficient unseen train rows for requested disjoint roles')
    offset={0:0,1:0}; result={}
    for role in TRAIN_ROLES:
        pieces=[]
        for label in (0,1):
            count=sizes[role] if role in ('reference','calibration') and label==0 else (
                  0 if role in ('reference','calibration') else sizes[role]//2)
            pieces.append(pools[label][offset[label]:offset[label]+count]); offset[label]+=count
        result[role]=np.sort(np.concatenate(pieces))
    pieces=[]
    for label in (0,1):
        pool=np.flatnonzero((yv==label)&~np.isin(iv,list(seen)))
        if len(pool)<sizes['final']//2: raise ValueError('Insufficient unseen official test rows')
        pieces.append(rng.choice(pool,sizes['final']//2,replace=False))
    result['final']=np.sort(np.concatenate(pieces))
    return result


def collect_seen_ids(workspace):
    """Conservatively exclude local historical pilot pools and observed run IDs."""
    root=Path(workspace); seen=set(); sources=[]
    def record(path,ids,reason):
        values=set(str(s) for s in ids); seen.update(values)
        sources.append({'path':str(path.resolve()),'sha256':sha256(path),'unique_ids':len(values),'reason':reason})
    for path in sorted((root/'outputs').glob('*/partitions.json')):
        state=read_json(path)
        record(path,[sid for ids in state.get('ids',{}).values() for sid in ids],'historical train roles')
    for path in sorted((root/'outputs').glob('**/evaluation/scores.csv')):
        with path.open(encoding='utf8',newline='') as f:
            record(path,(row['sample_id'] for row in csv.DictReader(f)),'historical detector evaluation')
    for meta_path in sorted((root/'data').glob('*/dataset.json')):
        meta=read_json(meta_path)
        if not meta.get('pilot'): continue
        for split in ('train','test'):
            path=meta_path.parent/f'ids_{split}.npy'
            if path.exists(): record(path,np.load(path,allow_pickle=False).astype(str),'entire historical pilot pool; conservative')
    for path in sorted((root/'docs'/'reviews').glob('V3_SCHEMA_AUDIT_*.json')):
        record(path,read_json(path).get('seen_source_ids',[]),'real V3 schema probes; conservative exclusion')
    return seen,sources


def freeze_primary_splits(source,output,schema,sizes,seed,seen_ids=(),seen_sources=()):
    """Reuse validated matrices by reference; never rewrite legacy data/splits."""
    from .prepare import load_data
    source=Path(source).resolve(); output=Path(output).resolve(); schema=get_schema(schema)
    if output==source or (output.exists() and any(output.iterdir())):
        raise FileExistsError('Use a fresh primary split directory')
    meta=read_json(source/'dataset.json')
    compatible=(meta['schema']==schema.version or (meta['schema']==SCHEMA_VERSION and schema.version==V2_PRIMARY))
    if not compatible: raise ValueError('Source extractor/schema mismatch')
    data=load_data(source)
    for name,expected in meta['array_sha256'].items():
        if Path(name).name!=name or sha256(source/name)!=expected:
            raise ValueError('Source array checksum mismatch: '+name)
    partitions=primary_partitions(data['y_train'],data['ids_train'],data['y_test'],data['ids_test'],sizes,seed,seen_ids)
    output.mkdir(parents=True,exist_ok=True)
    np.savez(output/'roles.npz',**partitions)
    ids={role:data['ids_test' if role=='final' else 'ids_train'][idx].astype(str).tolist()
         for role,idx in partitions.items()}
    write_json(output/'roles.json',{'protocol':'primary-train-held-out-roles-v1','dataset':schema.dataset,
        'schema':schema.version,'schema_sha256':schema.fingerprint,'split_seed':seed,'sizes':sizes,
        'source_directory':str(source),'source_schema':meta['schema'],'source_dataset_sha256':sha256(source/'dataset.json'),
        'source_array_sha256':meta['array_sha256'],'roles_sha256':sha256(output/'roles.npz'),'ids':ids,
        'role_partitions':{role:'test' if role=='final' else 'train' for role in partitions},
        'seen_ids_excluded_count':len(set(seen_ids)),'seen_id_sources':list(seen_sources),
        'external_handover_source_ids':'missing; cannot claim absolute unseen history',
        'legacy_data_policy':'arrays reused read-only; historical splits/artifacts preserved',
        'checks':{'unique_source_ids':True,'train_test_disjoint':True,'all_roles_disjoint':True,
                  'reference_calibration_benign_train_only':True,'known_seen_ids_excluded':True}})
    return {'dataset':schema.dataset,'schema':schema.version,'sizes':sizes,'output':str(output),
            'roles_sha256':sha256(output/'roles.npz'),'seen_ids_excluded_count':len(set(seen_ids))}
