"""Audit every PE source ID, materialize only the approved balanced role budget."""
import hashlib
import json
import sqlite3
import time
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
from numpy.lib.format import open_memmap
from xsentinel.schema import V3_PRIMARY, get_schema
from xsentinel.utils import read_json, write_json, sha256
from .protocol import TRAIN_ROLES, collect_seen_ids
from .vectorizer import Vectorizer


def metadata(line):
    # Pinned flat JSONL places metadata before histogram. Parse that complete
    # top-level prefix; other layouts use the full JSON parser, never regex IDs.
    boundary = line.find(b', "histogram":')
    try:
        record = json.loads(line[:boundary] + b'}' if boundary >= 0 else line)
    except json.JSONDecodeError:
        record = json.loads(line)
    sid, label, kind = record['sha256'], record['label'], record['file_type']
    if (not isinstance(sid, str) or len(sid) != 64 or any(c not in '0123456789abcdef' for c in sid)
            or type(label) is not int or label not in (-1, 0, 1)
            or kind not in ('Win32', 'Win64', 'Dot_Net')):
        raise ValueError('Invalid PE metadata/source SHA256')
    return sid, label, kind


def class_budgets(sizes):
    # Reuse the same role-size validation as the partition planner.
    if set(sizes) != set(TRAIN_ROLES) | {'final'}:
        raise ValueError('Explicit seven-role budget required')
    for role, n in sizes.items():
        if type(n) is not int or n <= 0 or (role not in ('reference', 'calibration') and n % 2):
            raise ValueError('Invalid primary role budget')
    half = sum(sizes[r] // 2 for r in TRAIN_ROLES if r not in ('reference', 'calibration'))
    return {'train': {0: half + sizes['reference'] + sizes['calibration'], 1: half},
            'test': {0: sizes['final'] // 2, 1: sizes['final'] // 2}}


def selection_rank(sid, seed):
    # Random-priority sampling of source IDs; no feature or outcome selection.
    return hashlib.blake2b(bytes.fromhex(sid), digest_size=16,
                          key=int(seed).to_bytes(8, 'little', signed=False),
                          person=b'xs-v3-pool-v1').digest()


def _canonical_features(line, schema):
    record=json.loads(line); raw=record.get('features',record)
    return hashlib.sha256(json.dumps({name:raw[name] for name in schema.groups},
        sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _fast_features(line, schema):
    # Exact feature-byte equality proves equality. Different bytes are resolved
    # by canonical JSON field comparison below; tag additions do not affect X.
    start=line.find(b'"histogram":')
    end=line.find(b', "week_id":',start)
    if start>=0 and end>start:
        return 'raw:'+hashlib.sha256(line[start:end]).hexdigest()
    return 'canonical:'+_canonical_features(line,schema)


def raw_is_pe(line):
    start=line.find(b', "general": '); end=line.find(b', "header":',start)
    if start>=0 and end>start:
        general=json.JSONDecoder().raw_decode(line[start+len(b', "general": '):end].decode('utf8'))[0]
    else:
        record=json.loads(line); general=record.get('features',record)['general']
    flag=general['is_pe']
    if type(flag) is not int or flag not in (0,1):
        raise ValueError('Invalid upstream general.is_pe flag')
    return flag


def prepare_ember2024(directory, output, verification_path, protocol_path, workspace, *, resume=False,
                     duplicate_policy_path=None, vector_policy_path=None):
    out = Path(output).resolve(); root = Path(workspace).resolve()
    protocol = read_json(protocol_path); schema = get_schema(V3_PRIMARY)
    if protocol['datasets']['EMBER2024'] != schema.version or protocol.get('pending'):
        raise ValueError('Approved primary V3 protocol required')
    budgets = class_budgets(protocol['sample_sizes'])
    seed = protocol['split_seed']; verification = read_json(verification_path)
    vector_policy=read_json(vector_policy_path) if vector_policy_path else {'policy':'require_is_pe_one_v1'}
    if vector_policy['policy'] not in ('require_is_pe_one_v1','official_pe_scope_keep_original_is_pe_v1'):
        raise ValueError('Unknown approved vector policy')
    vector_signature={'policy':vector_policy,'policy_sha256':sha256(vector_policy_path) if vector_policy_path else None,
        'preparer_sha256':sha256(__file__),'vectorizer_sha256':sha256(Path(__file__).with_name('vectorizer.py')),
        'upstream_sha256':sha256(Path(__file__).resolve().parents[1]/'thrember_upstream.py')}
    files = verification['files']
    if len(files) != 6 or {f['name'] for f in files} != {
            f'{kind}_{split}.zip' for kind in ('Win32', 'Win64', 'Dot_Net') for split in ('train', 'test')}:
        raise ValueError('All six verified PE archives required')
    paths = {f['name']: Path(directory).resolve() / f['name'] for f in files}
    seen, seen_sources = collect_seen_ids(root)
    old_db = root / 'data/ember2018_full/audit.sqlite'
    old_sources = []
    if old_db.exists():
        with sqlite3.connect('file:' + old_db.as_posix() + '?mode=ro', uri=True) as db:
            old_ids = {r[0] for r in db.execute('SELECT id FROM samples')}
        old_sources.append({'path': str(old_db), 'sha256': sha256(old_db), 'ids': len(old_ids)})
    else:
        old_ids = set()
        for split in ('train', 'test'):
            path = root / f'data/ember2018_full/ids_{split}.npy'
            if not path.exists():
                raise FileNotFoundError('EMBER2018 source IDs required for cross-dataset audit')
            old_ids.update(np.load(path, allow_pickle=False).astype(str))
            old_sources.append({'path': str(path), 'sha256': sha256(path)})
    policy=read_json(duplicate_policy_path) if duplicate_policy_path else {'duplicate_policy':'reject'}
    if policy['duplicate_policy'] not in ('reject','merge_equal_features_exclude_conflicts_v1'):
        raise ValueError('Unknown approved duplicate policy')
    signature = {'schema': schema.version, 'schema_sha256': schema.fingerprint,
                 'protocol_sha256': sha256(protocol_path), 'verification_sha256': sha256(verification_path),
                 'budgets': {p: {str(k): v for k, v in counts.items()} for p, counts in budgets.items()},
                 'split_seed': seed, 'seen_sources': seen_sources, 'ember2018_sources': old_sources,
                 'sampling': 'smallest seeded BLAKE2b source-ID priorities within partition/class; no PE-type quotas',
                 'archives': [],'duplicate_policy':policy,
                 'duplicate_policy_sha256':sha256(duplicate_policy_path) if duplicate_policy_path else None}
    for entry in files:
        path = paths[entry['name']]; stat = path.stat()
        if stat.st_size != entry['bytes'] or path != Path(entry['path']).resolve():
            raise ValueError('Verified archive location/size changed')
        signature['archives'].append({'name': path.name, 'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns,
                                      'sha256': entry['sha256']})
    if out.exists() and any(out.iterdir()):
        if not resume or read_json(out / 'preparation.lock.json') != signature:
            raise FileExistsError('Fresh output or exact locked --resume required')
        if (out / 'dataset.json').exists():
            state = read_json(out / 'dataset.json')
            locked=read_json(out/'vectorization.lock.json')
            if any(locked.get(k)!=v for k,v in vector_signature.items()):
                raise ValueError('Vectorization implementation/policy changed')
            if sha256(out/'vectorization.lock.json')!=state['vectorization_lock_sha256'] or sha256(out/'is_pe_audit.json')!=state['is_pe_audit_sha256']:
                raise ValueError('Vectorization audit/lock checksum mismatch')
            for name, expected in state['array_sha256'].items():
                if sha256(out / name) != expected:
                    raise ValueError('Prepared array checksum mismatch')
            return state
    else:
        out.mkdir(parents=True, exist_ok=True)
        write_json(out / 'preparation.lock.json', signature)
    started = time.perf_counter()
    db = sqlite3.connect(out / 'audit.sqlite')
    db.execute('CREATE TABLE IF NOT EXISTS samples (id TEXT PRIMARY KEY, partition TEXT, label INTEGER, '
               'file_type TEXT, archive TEXT, member TEXT, line INTEGER, rank BLOB, excluded INTEGER, feature_digest TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS duplicates (id TEXT, partition TEXT, label INTEGER, file_type TEXT, '
               'archive TEXT, member TEXT, line INTEGER, feature_digest TEXT, hard_conflict INTEGER)')
    db.execute('CREATE TABLE IF NOT EXISTS members_complete (archive TEXT, member TEXT, PRIMARY KEY(archive,member))')
    db.commit()
    complete = set(db.execute('SELECT archive,member FROM members_complete'))
    for entry in files:
        with zipfile.ZipFile(paths[entry['name']]) as archive:
            actual = [{'name': m.filename, 'bytes': m.file_size, 'crc': m.CRC} for m in archive.infolist()]
            if actual != entry['members']:
                raise ValueError('ZIP inventory changed after verification')
            for member in archive.infolist():
                if (entry['name'], member.filename) in complete:
                    continue
                rows = 0
                try:
                    with archive.open(member) as stream:
                        for number, line in enumerate(stream, 1):
                            sid, label, kind = metadata(line)
                            if kind != entry['name'].removesuffix('_' + entry['split'] + '.zip'):
                                raise ValueError('PE type does not match archive')
                            # Bits disclose separately known observations and cross-dataset collisions.
                            excluded = int(sid in seen) | (2 * int(sid in old_ids))
                            feature_digest=_fast_features(line,schema)
                            row=(sid, entry['split'], label, kind, entry['name'], member.filename,
                                 number, selection_rank(sid, seed), excluded,feature_digest)
                            if policy['duplicate_policy']=='reject':
                                db.execute('INSERT INTO samples VALUES (?,?,?,?,?,?,?,?,?,?)',row)
                            else:
                                inserted=db.execute('INSERT OR IGNORE INTO samples VALUES (?,?,?,?,?,?,?,?,?,?)',row)
                                if inserted.rowcount==0:
                                    previous=db.execute('SELECT partition,label,file_type FROM samples WHERE id=?',(sid,)).fetchone()
                                    hard=int(previous!=(entry['split'],label,kind))
                                    db.execute('INSERT INTO duplicates VALUES (?,?,?,?,?,?,?,?,?)',
                                        (sid,entry['split'],label,kind,entry['name'],member.filename,number,feature_digest,hard))
                                    if hard: db.execute('UPDATE samples SET excluded=excluded|4 WHERE id=?',(sid,))
                            rows += 1
                    db.execute('INSERT INTO members_complete VALUES (?,?)', (entry['name'], member.filename))
                    db.commit()
                except Exception:
                    db.rollback(); db.close(); raise
                print(f'Audit {entry["name"]} / {member.filename}: {rows} IDs', flush=True)
    # Different formatting is not automatically a feature conflict. Resolve all
    # unequal fingerprints from their original raw rows, grouped by ZIP member.
    if not (out/'duplicate_resolution.json').exists():
        differing=db.execute('SELECT DISTINCT d.id FROM duplicates d JOIN samples s ON d.id=s.id '
                             'WHERE d.feature_digest!=s.feature_digest AND s.excluded & 4=0').fetchall()
        wanted={}
        for (sid,) in differing:
            occurrences=db.execute('SELECT archive,member,line FROM samples WHERE id=? UNION ALL '
                                   'SELECT archive,member,line FROM duplicates WHERE id=?',(sid,sid)).fetchall()
            for archive_name,member_name,number in occurrences:
                wanted.setdefault((archive_name,member_name),{})[number]=sid
        values={sid:set() for (sid,) in differing}
        for (archive_name,member_name),numbers in wanted.items():
            with zipfile.ZipFile(paths[archive_name]) as archive:
                with archive.open(member_name) as stream:
                    for number,line in enumerate(stream,1):
                        if number in numbers: values[numbers[number]].add(_canonical_features(line,schema))
        conflicts=[sid for sid,hashes in values.items() if len(hashes)>1]
        for sid,hashes in values.items():
            if not hashes: raise ValueError('Missing duplicate provenance record')
        db.executemany('UPDATE samples SET excluded=excluded|4 WHERE id=?',((sid,) for sid in conflicts))
        db.commit()
        write_json(out/'duplicate_resolution.json',{'unequal_byte_fingerprints_checked':len(differing),
                   'canonical_raw_feature_conflicts':len(conflicts),'policy':policy})
    if not (out / 'audit_summary.json').exists():
        stats = [dict(zip(('partition','label','file_type','excluded','count'), r)) for r in db.execute(
            'SELECT partition,label,file_type,excluded,count(*) FROM samples GROUP BY partition,label,file_type,excluded')]
        write_json(out / 'audit_summary.json', {'dataset': 'EMBER2024', 'source_counts': stats,
            'cross_dataset_matches': db.execute('SELECT count(*) FROM samples WHERE excluded & 2 != 0').fetchone()[0],
            'known_seen_matches': db.execute('SELECT count(*) FROM samples WHERE excluded & 1 != 0').fetchone()[0],
            'duplicate_occurrences':db.execute('SELECT count(*) FROM duplicates').fetchone()[0],
            'duplicate_ids':db.execute('SELECT count(DISTINCT id) FROM duplicates').fetchone()[0],
            'conflicting_ids_excluded':db.execute('SELECT count(*) FROM samples WHERE excluded & 4!=0').fetchone()[0],
            'duplicate_policy':policy,
            'unique_source_ids_after_policy': True, 'train_test_disjoint_after_exclusions': True,
            'cross_dataset_policy': 'All IDs present in EMBER2018 audit excluded from every V3 role',
            'metadata_only': 'All IDs audited; no model or test predictions used'})
    selected = {}
    for split, counts in budgets.items():
        selected[split] = []
        for label, count in counts.items():
            rows = db.execute('SELECT id,label,archive,member,line,file_type FROM samples '
                              'WHERE partition=? AND label=? AND excluded=0 ORDER BY rank,id LIMIT ?',
                              (split, label, count)).fetchall()
            if len(rows) != count:
                raise ValueError(f'Insufficient unseen {split} class {label}: {len(rows)}/{count}')
            selected[split].extend(rows)
        selected[split].sort(key=lambda r: (r[2], r[3], r[4]))
    db.execute('CREATE INDEX IF NOT EXISTS samples_member ON samples(archive,member,line)')
    db.commit()
    vector_signature['preparation_lock_sha256']=sha256(out/'preparation.lock.json')
    vector_signature['selection_sha256']=hashlib.sha256(json.dumps(
        {split:[r[0] for r in rows] for split,rows in selected.items()},sort_keys=True).encode()).hexdigest()
    vector_lock=out/'vectorization.lock.json'
    if vector_lock.exists():
        locked=read_json(vector_lock)
        if any(locked.get(k)!=v for k,v in vector_signature.items()):
            raise ValueError('Vectorization implementation/policy/selection changed')
    else:
        prior=out/'converted_members.json'
        write_json(vector_lock,{**vector_signature,'imported_completed_members_sha256':sha256(prior) if prior.exists() else None,
            'checkpoint_policy':'Prior completed members contain only is_pe=1; unchanged upstream vectors reused. Aborted member recomputed.'})
    del seen, old_ids
    arrays = {}; locations = {}
    for split, rows in selected.items():
        n = len(rows)
        for kind, dtype, shape in (('X', 'float32', (n, schema.dim)), ('y', 'int8', (n,)), ('ids', 'S64', (n,))):
            path = out / f'{kind}_{split}.npy'
            if path.exists():
                a = np.load(path, mmap_mode='r+', allow_pickle=False)
                if a.shape != shape or a.dtype != np.dtype(dtype):
                    raise ValueError('Partial array shape/dtype mismatch')
            else:
                a = open_memmap(path, mode='w+', dtype=dtype, shape=shape)
            arrays[kind + '_' + split] = a
        for position, row in enumerate(rows):
            locations.setdefault((row[2], row[3]), {})[row[4]] = (split, position, row)
    progress_path = out / 'converted_members.json'
    converted = set(tuple(v) for v in read_json(progress_path)['members']) if progress_path.exists() else set()
    audit_path=out/'is_pe_audit_members.json'
    audited=read_json(audit_path)['members'] if audit_path.exists() else {}
    vectorizer = Vectorizer(schema)
    for entry in files:
        with zipfile.ZipFile(paths[entry['name']]) as archive:
            for member in archive.infolist():
                key = (entry['name'], member.filename)
                audit_key=entry['name']+'/'+member.filename
                if key in converted and audit_key in audited:
                    continue
                wanted = locations.get(key, {}); count = 0
                totals=Counter(); representatives=Counter()
                originals={row[0]:row[1] for row in db.execute(
                    'SELECT line,excluded FROM samples WHERE archive=? AND member=?',key)}
                if wanted or audit_key not in audited:
                    with archive.open(member) as stream:
                        for number, line in enumerate(stream, 1):
                            flag=raw_is_pe(line); _,label,kind=metadata(line)
                            group=(entry['split'],kind,label,flag)
                            totals[group]+=1
                            if number in originals: representatives[(*group,originals[number])]+=1
                            if key in converted or number not in wanted:
                                continue
                            split, position, expected = wanted[number]
                            record = json.loads(line)
                            if (record['sha256'], record['label'], record['file_type']) != (expected[0], expected[1], expected[5]):
                                raise ValueError('Selected record provenance mismatch')
                            x = vectorizer.transform(record)
                            if x[2]!=flag:
                                raise ValueError('Vector changed original general.is_pe flag')
                            if flag==0 and vector_policy['policy']=='require_is_pe_one_v1':
                                raise ValueError('is_pe=0 requires an explicitly approved official PE vector policy')
                            arrays['X_' + split][position] = x
                            arrays['y_' + split][position] = record['label']
                            arrays['ids_' + split][position] = record['sha256']
                            count += 1
                    if key not in converted and count != len(wanted):
                        raise ValueError('Missing selected rows in member')
                for a in arrays.values():
                    a.flush()
                converted.add(key)
                write_json(progress_path, {'members': sorted(converted)})
                audited[audit_key]={'raw_occurrences':[dict(zip(('partition','file_type','label','is_pe','count'),(*k,n)))
                    for k,n in sorted(totals.items())],
                    'unique_representatives':[dict(zip(('partition','file_type','label','is_pe','excluded','count'),(*k,n)))
                    for k,n in sorted(representatives.items())]}
                write_json(audit_path,{'members':audited})
                print(f'Vectors {member.filename}: {count} selected rows', flush=True)
    db.close()
    for split, rows in selected.items():
        if arrays['ids_' + split].astype(str).tolist() != [r[0] for r in rows]:
            raise ValueError('Materialized IDs do not match frozen source priority selection')
    for entry in signature['archives']:
        stat = paths[entry['name']].stat()
        if stat.st_size != entry['bytes'] or stat.st_mtime_ns != entry['mtime_ns']:
            raise ValueError('Archive changed during preparation')
    for a in arrays.values():
        a.flush()
    materialized=Counter()
    for split,rows in selected.items():
        for position,row in enumerate(rows):
            materialized[(split,row[5],int(row[1]),int(arrays['X_'+split][position,2]))]+=1
    audit={'policy':vector_policy,'feature_mutation':False,'scope':'All six ZIPs; source counts include excluded IDs, selected counts contain only materialized eligible rows',
        'materialized':[dict(zip(('partition','file_type','label','is_pe','count'),(*k,n))) for k,n in sorted(materialized.items())]}
    for scope,fields in (('raw_occurrences',('partition','file_type','label','is_pe')),
                         ('unique_representatives',('partition','file_type','label','is_pe','excluded'))):
        aggregate=Counter()
        for value in audited.values():
            for row in value[scope]: aggregate[tuple(row[f] for f in fields)]+=row['count']
        audit[scope]=[dict(zip((*fields,'count'),(*k,n))) for k,n in sorted(aggregate.items())]
    write_json(out/'is_pe_audit.json',audit)
    arrays.clear()
    result = {'schema': schema.version, 'dataset': schema.dataset, 'schema_sha256': schema.fingerprint,
              'counts': {split: len(rows) for split, rows in selected.items()}, 'pilot': False,
              'source_scope': 'All six official PE ZIPs audited; only approved role budget vectorized',
              'selection': signature['sampling'], 'split_seed': seed, 'source_revision': verification['revision'],
              'preparation_lock_sha256': sha256(out / 'preparation.lock.json'),
              'audit_summary_sha256': sha256(out / 'audit_summary.json'),
              'vectorization_lock_sha256':sha256(vector_lock),'is_pe_audit_sha256':sha256(out/'is_pe_audit.json'),
              'vector_policy':vector_policy,'preparer_sha256':sha256(__file__),
              'upstream_sha256': sha256(Path(__file__).resolve().parents[1] / 'thrember_upstream.py'),
              'vectorizer_sha256': sha256(Path(__file__).with_name('vectorizer.py')),
              'array_sha256': {p.name: sha256(p) for p in sorted(out.glob('*.npy'))},
              'elapsed_seconds_current_session': time.perf_counter() - started,
              'test_predictions_computed': False, 'extractor_labels_excluded_from_features': True}
    write_json(out / 'dataset.json', result)
    return result
