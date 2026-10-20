"""New outcome-blind pool, excluding primary, pilots and the old Fresh pool."""
import sys,json,sqlite3,zipfile,hashlib,argparse,gc
from pathlib import Path
from collections import defaultdict,Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.data.vectorizer import Vectorizer
from xsentinel.data.ember2024 import metadata
from xsentinel.schema import V2_PRIMARY,V3_PRIMARY


def main():
    p=argparse.ArgumentParser();p.add_argument('--per-class',type=int,default=1000);p.add_argument('--out',default='outputs/fusion_binary_latency_2026_10_20/final_pool')
    args=p.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    seen=set();sources=[]
    for path in sorted(Path('data/primary').glob('*/protocol_v2/roles.json')):
        r=read_json(path);seen.update(s for ids in r['ids'].values() for s in ids)
        sources.append({'path':str(path),'sha256':sha256(path)})
    for source in ('data/pilot','data/pilot_balanced','data/pilot_shards','data/pilot_v2'):
        for path in Path(source).glob('ids_*.npy'):seen.update(np.load(path,allow_pickle=False).astype(str).tolist())
    for path in Path('outputs').glob('attack_development*/partitions.json'):
        r=read_json(path);seen.update(s for ids in r.get('ids',{}).values() for s in ids)
    for path in sorted(Path('outputs/revision_2026_10_13/fresh_validation').glob('*/ids.npy')):
        seen.update(np.load(path,allow_pickle=False).astype(str).tolist())
        sources.append({'path':str(path),'sha256':sha256(path)})
    choice=Path('outputs/fusion_binary_latency_2026_10_20/selection.json')
    if not choice.is_file():raise ValueError('Lock the fusion choice before preparing final vectors')
    lock={'protocol':'fusion-fresh-validation-2026-10-20-v1','per_class':args.per_class,'seed':20261020,
          'fusion_choice_sha256':sha256(choice),
          'selection':'Metadata/source IDs only, exclude known local roles/history; no predictions before selection',
          'is_pe_zero':'Retain original flag; report separately; no outcome-driven replacement',
          'source_roles':sources,'known_exclusions':len(seen),'exclusion_digest':hashlib.sha256('\n'.join(sorted(seen)).encode()).hexdigest(),
          'script_sha256':sha256(__file__),'external_history':'External handover observation history unavailable'}
    if (out/'protocol.json').exists():
        if read_json(out/'protocol.json')!=lock:raise ValueError('Validation sampling lock changed')
    else:write_json(out/'protocol.json',lock)
    for dataset,schema,source in [('EMBER2018',V2_PRIMARY,Path('data/ember2018_full')),
                                  ('EMBER2024',V3_PRIMARY,Path('data/ember2024_primary_source_v2'))]:
        dest=out/dataset;dest.mkdir(exist_ok=True)
        if (dest/'dataset.json').exists():
            r=read_json(dest/'dataset.json');assert all(sha256(dest/k)==h for k,h in r['hashes'].items())
            print('Reused complete validation pool',dataset,flush=True);continue
        if dataset=='EMBER2018':
            y=np.load(source/'y_test.npy',mmap_mode='r');ids=np.load(source/'ids_test.npy',mmap_mode='r').astype(str)
            mask=~np.isin(ids,list(seen));rng=np.random.default_rng(20261020);indices=[]
            for label in (0,1):
                pool=np.flatnonzero((y==label)&mask)
                if len(pool)<args.per_class:raise ValueError('Insufficient unobserved labeled source IDs')
                indices.extend(rng.choice(pool,args.per_class,replace=False).tolist())
            indices=np.sort(indices);X=np.load(source/'X_test.npy',mmap_mode='r')
            np.save(dest/'X.npy',np.asarray(X[indices]));np.save(dest/'y.npy',np.asarray(y[indices]));np.save(dest/'ids.npy',ids[indices].astype('S64'))
            state={'dataset':dataset,'schema':schema,'n':len(indices),'source_indices':indices.tolist(),'source_manifest_sha256':sha256(source/'dataset.json')}
            del X,y,ids;gc.collect()
        else:
            db=sqlite3.connect('file:'+ (source/'audit.sqlite').resolve().as_posix()+'?mode=ro',uri=True)
            db.execute('PRAGMA temp_store=MEMORY')
            db.execute('CREATE TEMP TABLE seen (id TEXT PRIMARY KEY)');db.executemany('INSERT INTO seen VALUES (?)',[(s,) for s in seen])
            selectionpath=dest/'selection.json'
            if selectionpath.exists():selection=read_json(selectionpath)
            else:
                rows=[]
                for label in (0,1):
                    rows+=list(db.execute('SELECT s.id,s.label,s.file_type,s.archive,s.member,s.line FROM samples s LEFT JOIN seen e ON s.id=e.id WHERE s.partition=? AND s.excluded=0 AND s.label=? AND e.id IS NULL ORDER BY s.rank LIMIT ?',('test',label,args.per_class)))
                if len(rows)!=2*args.per_class:raise ValueError('Insufficient unseen V3 candidates')
                selection={'rows':rows,'source_audit_manifest_sha256':sha256(source/'audit_summary.json'),'source_revision':read_json(source/'dataset.json')['source_revision']}
                write_json(selectionpath,selection)
            db.close();rows=selection['rows'];assert not ({r[0] for r in rows}&seen)
            grouped=defaultdict(dict)
            for position,row in enumerate(rows):grouped[(row[3],row[4])][row[5]]=(position,row)
            dim=2568;n=len(rows);arrays={}
            for name,shape,dtype in [('X',(n,dim),'float32'),('y',(n,),'int8'),('ids',(n,),'S64')]:
                path=dest/(name+'.npy')
                arrays[name]=np.lib.format.open_memmap(path,mode='r+' if path.exists() else 'w+',dtype=dtype,shape=shape)
            done=read_json(dest/'members.json') if (dest/'members.json').exists() else []
            vectorizer=Vectorizer(schema);manifest=read_json('configs/ember2024_sources.json');allowed={x['name']:x for x in manifest['files']}
            for (archive,member),positions in grouped.items():
                key=archive+'/'+member
                if key in done:continue
                if archive not in allowed or not archive.endswith('_test.zip'):raise ValueError('Unexpected source archive')
                archivepath=Path('data/ember2024_archives')/archive
                assert archivepath.stat().st_size==allowed[archive]['bytes']
                with zipfile.ZipFile(archivepath) as zipped,zipped.open(member) as stream:
                    found=0;last=max(positions)
                    for number,line in enumerate(stream,1):
                        if number in positions:
                            position,row=positions[number];sid,label,typ=metadata(line)
                            if (sid,label,typ)!=(row[0],row[1],row[2]):raise ValueError('Source location mismatch')
                            arrays['X'][position]=vectorizer.transform(json.loads(line));arrays['y'][position]=label;arrays['ids'][position]=sid.encode();found+=1
                        if number>=last:break
                    if found!=len(positions):raise ValueError('Selected raw source rows missing')
                for a in arrays.values():a.flush()
                done.append(key);write_json(dest/'members.json',done);print('New validation vectors',member,len(positions),flush=True)
            state={'dataset':dataset,'schema':schema,'n':n,'source_revision':selection['source_revision'],
                   'source_type_counts':dict(Counter(r[2] for r in rows)),'is_pe_zero':int(np.sum(arrays['X'][:,2]==0)),
                   'selection_sha256':sha256(selectionpath),'source_manifest_sha256':sha256(source/'dataset.json')}
            arrays.clear();gc.collect()
        final_ids=np.load(dest/'ids.npy',allow_pickle=False).astype(str)
        assert len(set(final_ids))==len(final_ids) and not (set(final_ids)&seen)
        state.update({'labels':{str(k):int(np.sum(np.load(dest/'y.npy')==k)) for k in (0,1)},
                      'checks':{'known_primary_history_disjoint':True,'prediction_free_selection':True},
                      'hashes':{p.name:sha256(p) for p in dest.glob('*.npy')}})
        write_json(dest/'dataset.json',state);print('Frozen fresh validation pool',dataset,state['n'],flush=True)


if __name__=='__main__':main()
