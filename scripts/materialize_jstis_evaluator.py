"""Release fresh evaluator vectors only after the six-cell global artifact lock."""
import argparse,json,sqlite3,sys,zipfile,shutil
from collections import defaultdict
from pathlib import Path
import numpy as np
from numpy.lib.format import open_memmap

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from xsentinel.revision.jstis_gate import verify_global_lock
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.schema import get_schema,V2_PRIMARY,V3_PRIMARY
from xsentinel.data.vectorizer import Vectorizer

ROLES=('confirmation','reference','calibration','final')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','attacks','global-lock','dataset','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();verify_global_lock(a.attacks,a.global_lock)
    source=Path(a.manifest);state=read_json(source/f'{a.dataset}.roles.json');out=Path(a.output)
    if a.dataset not in ('EMBER2018','EMBER2024'):raise ValueError('Unknown dataset')
    schema=get_schema(V2_PRIMARY if a.dataset=='EMBER2018' else V3_PRIMARY)
    if out.exists() and any(out.iterdir()):raise FileExistsError('Fresh output required')
    required=sum(state['sizes'][r] for r in ROLES)*schema.dim*4
    if shutil.disk_usage(ROOT).free<required+2*1024**3:raise OSError('Insufficient disk reserve')
    out.mkdir(parents=True,exist_ok=True)
    lock={'global_lock_sha256':sha256(a.global_lock),'role_manifest_sha256':sha256(source/f'{a.dataset}.roles.json'),
          'schema':schema.version,'schema_sha256':schema.fingerprint,'dataset':a.dataset,
          'roles_opened':list(ROLES),'code_sha256':sha256(__file__),
          'vectorizer_sha256':sha256(ROOT/'src/xsentinel/data/vectorizer.py'),
          'v3_raw_sha256':sha256(ROOT/'src/xsentinel/data/v3_raw.py')}
    write_json(out/'evaluator.lock.json',lock)
    db=sqlite3.connect('file:'+(source/'steward.sqlite').resolve().as_posix()+'?mode=ro',uri=True)
    arrays={}; locations=defaultdict(dict); counts={r:0 for r in ROLES}; flags=defaultdict(int)
    for role in ROLES:
        rows=db.execute('select id,label,partition,archive,member,line from roles where dataset=? and role=? order by id',(a.dataset,role)).fetchall()
        if [r[0] for r in rows]!=state['ids'][role] or len(rows)!=state['sizes'][role]:raise ValueError('Steward mismatch')
        if any(r[1]!=0 for r in rows) and role in ('reference','calibration'):raise ValueError('Reference/calibration must be benign')
        arrays[role]=open_memmap(out/f'{role}.X.npy',mode='w+',dtype='float32',shape=(len(rows),schema.dim))
        np.save(out/f'{role}.ids.npy',np.asarray([r[0] for r in rows],dtype='S64'))
        np.save(out/f'{role}.y.npy',np.asarray([r[1] for r in rows],dtype=np.int8))
        if a.dataset=='EMBER2024':
            for pos,(sid,label,partition,archive,member,line) in enumerate(rows):
                expected='test' if role=='final' else 'train'
                if partition!=expected or not archive.endswith('_'+expected+'.zip'):raise ValueError('Partition mismatch')
                locations[archive,member][line]=(role,pos,sid,label)
    db.close()
    if a.dataset=='EMBER2018':
        directory=ROOT/'data/ember2018_full'
        for partition in ('train','test'):
            ids=np.load(directory/f'ids_{partition}.npy').astype(str);lookup={s:i for i,s in enumerate(ids)}
            X=np.load(directory/f'X_{partition}.npy',mmap_mode='r');y=np.load(directory/f'y_{partition}.npy',mmap_mode='r')
            for role in ROLES:
                if (role=='final')!=(partition=='test'):continue
                idx=np.asarray([lookup[s] for s in state['ids'][role]])
                if not np.array_equal(y[idx],np.load(out/f'{role}.y.npy')):raise ValueError('Metadata labels changed')
                for offset in range(0,len(idx),128):arrays[role][offset:offset+128]=X[idx[offset:offset+128]]
                counts[role]=len(idx)
    else:
        vectorizer=Vectorizer(schema)
        for (archive,member),wanted in sorted(locations.items()):
            path=ROOT/'data/ember2024_archives'/archive
            if archive not in lock.setdefault('archive_sha256',{}):lock['archive_sha256'][archive]=sha256(path)
            remaining=len(wanted)
            with zipfile.ZipFile(path) as z,z.open(member) as stream:
                for line_no,line in enumerate(stream,1):
                    if line_no not in wanted:continue
                    role,pos,sid,label=wanted[line_no];r=json.loads(line)
                    if r['sha256']!=sid or r['label']!=label:raise ValueError('Raw record provenance mismatch')
                    x=vectorizer.transform(r);arrays[role][pos]=x;flags[str(int(x[2]))]+=1
                    counts[role]+=1;remaining-=1
                    if not remaining:break
            if remaining:raise ValueError('Missing selected records')
            for arr in arrays.values():arr.flush()
    for role,arr in arrays.items():
        if counts[role]!=state['sizes'][role]:raise ValueError('Role incomplete')
        for offset in range(0,len(arr),128):
            if not np.isfinite(arr[offset:offset+128]).all():raise ValueError('Nonfinite vectors')
        arr.flush()
    verify_global_lock(a.attacks,a.global_lock)
    write_json(out/'COMPLETE.json',{'status':'EVALUATOR_ROLES_RELEASED_AFTER_GLOBAL_LOCK','lock':lock,
        'counts':counts,'v3_original_is_pe_counts':dict(flags),
        'array_sha256':{p.name:sha256(p) for p in sorted(out.glob('*.npy'))}})


if __name__=='__main__':main()
