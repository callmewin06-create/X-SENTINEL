"""Read a few records per official training week; no model/test inference."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from xsentinel.schema import get_schema,V3_PRIMARY
from xsentinel.data.vectorizer import Vectorizer
from xsentinel.utils import read_json,write_json,sha256


def audit(archive,output,per_shard=2):
    archive=Path(archive); output=Path(output)
    if output.exists(): raise FileExistsError('Existing audit preserved')
    manifest=read_json('configs/ember2024_sources.json')
    entry=next(item for item in manifest['files'] if item['name']==archive.name)
    if not archive.name.endswith('_train.zip'): raise ValueError('Schema audit reads official train only')
    if archive.stat().st_size!=entry['bytes'] or sha256(archive)!=entry['sha256']:
        raise ValueError('Archive checksum mismatch')
    s=get_schema(V3_PRIMARY); v=Vectorizer(s); ids=[]; vectors=[]; weeks=[]; types=set(); labels={}
    with zipfile.ZipFile(archive) as z:
        members=z.infolist()
        for member in members:
            if not member.filename.endswith('_train.jsonl'): raise ValueError('Unexpected archive member')
            with z.open(member) as f:
                for _ in range(per_shard):
                    line=f.readline()
                    if not line: break
                    r=json.loads(line); x=v.transform(r)
                    if r['file_type'] not in ('Win32','Win64','Dot_Net') or x[2]!=1:
                        raise ValueError('Non-PE record in PE scope')
                    # Probe fields independently of vectorizer assembly.
                    if x[0]!=np.float32(r['general']['size']) or x[1]!=np.float32(r['general']['entropy']):
                        raise ValueError('General mapping mismatch')
                    idx=s.names.index('header.optional.minor_subsystem_version')
                    expected=r['header'].get('optional',{}).get('minor_subsystem_version',0)
                    if x[idx]!=np.float32(expected): raise ValueError('Header mapping mismatch')
                    ids.append(r['sha256']); vectors.append(x); weeks.append(member.filename)
                    types.add(r['file_type']); labels[str(r['label'])]=labels.get(str(r['label']),0)+1
        uncompressed=sum(member.file_size for member in members)
    X=np.stack(vectors)
    if len(set(ids))!=len(ids): raise ValueError('Duplicate source IDs in schema probes')
    result={'scope':'schema probes only; official train; no predictions/attack selection',
        'dataset':'EMBER2024','schema':s.version,'schema_sha256':s.fingerprint,'dimension':s.dim,
        'extractor_commit':s.extractor_commit,'extractor_sha256':s.extractor_sha256,
        'archive':str(archive.resolve()),'archive_sha256':entry['sha256'],'dataset_revision':manifest['revision'],
        'archive_bytes':entry['bytes'],'uncompressed_bytes':uncompressed,'shards':len(set(weeks)),
        'sample_count':len(X),'per_shard_first_records':per_shard,'file_types':sorted(types),'labels_for_audit_only':labels,
        'finite_float32':True,'vector_sha256':hashlib.sha256(X.astype('<f4').tobytes()).hexdigest(),
        'seen_source_ids':ids,'view_sizes':{name:len(idx) for name,idx in s.views.items()},
        'restricted_probe_variation':[{'index':j,'name':s.names[j],'varying_on_probes':bool(np.ptp(X[:,j])>0)} for j in s.restricted],
        'limits':'Only this training archive and probes checked; no main fit/selection audit or 2024 model results.',
        'upstream_behavior_preserved':['exports first field is hash-vector length, not actual export count',
            'DataDirectories.process_raw_features iterates range(1,len(raw_obj)-1); preserve last-entry behavior'],
        'test_accessed':False,'binary_executed':False}
    write_json(output,result)
    return {k:result[k] for k in ('sample_count','shards','dimension','file_types','finite_float32','test_accessed')}


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--archive',required=True); p.add_argument('--out',required=True)
    p.add_argument('--per-shard',type=int,default=2); a=p.parse_args()
    print(json.dumps(audit(a.archive,a.out,a.per_shard),indent=2))
