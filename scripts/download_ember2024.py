"""Download pinned, checksummed PE archives without unpacking or executing files."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time
import urllib.request


def download(config,path,filename):
    manifest=json.loads(Path(config).read_text(encoding='utf8'))
    entries={item['name']:item for item in manifest['files']}
    if filename not in entries: raise ValueError('Archive outside pinned PE scope')
    item=entries[filename]; folder=Path(path); folder.mkdir(parents=True,exist_ok=True)
    dest=folder/filename; partial=folder/(filename+'.part')
    if dest.exists(): raise FileExistsError('Existing archive preserved; validate/reuse explicitly')
    if partial.exists(): raise FileExistsError('Partial download preserved; explicit recovery required')
    if shutil.disk_usage(folder).free<item['bytes']+5*2**30:
        raise ValueError('Insufficient space for archive plus 5 GiB reserve')
    url=f"https://huggingface.co/datasets/{manifest['repository']}/resolve/{manifest['revision']}/{filename}"
    h=hashlib.sha256(); count=0; started=time.perf_counter(); last=started
    request=urllib.request.Request(url,headers={'User-Agent':'X-SENTINEL-source-validation'})
    with urllib.request.urlopen(request,timeout=60) as response,partial.open('xb') as f:
        while chunk:=response.read(1024*1024):
            f.write(chunk); h.update(chunk); count+=len(chunk)
            now=time.perf_counter()
            if now-last>=15:
                print(f'{filename}: {count/2**20:.1f}/{item["bytes"]/2**20:.1f} MiB',flush=True); last=now
    if count!=item['bytes'] or h.hexdigest()!=item['sha256']:
        raise ValueError('Archive length/checksum mismatch; partial kept for audit')
    partial.rename(dest)
    print(json.dumps({'archive':str(dest.resolve()),'bytes':count,'sha256':h.hexdigest(),
        'seconds':time.perf_counter()-started,'revision':manifest['revision']},indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--config',default='configs/ember2024_sources.json')
    p.add_argument('--out',required=True); p.add_argument('--file',required=True); args=p.parse_args()
    download(args.config,args.out,args.file)
