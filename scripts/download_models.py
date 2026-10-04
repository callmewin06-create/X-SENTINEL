"""Download explicitly configured public bundles; no private-auth workaround."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import urllib.request
import urllib.parse

def download(manifest_path,profile,out_dir):
    manifest=json.loads(Path(manifest_path).read_text(encoding='utf8'))
    out=Path(out_dir).resolve(); out.mkdir(parents=True,exist_ok=True)
    files=manifest['profiles'][profile]
    if not files: raise ValueError('No actual model URLs configured for this profile')
    def digest(path):
        h=hashlib.sha256()
        with path.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
        return h.hexdigest()
    for item in files:
        target=(out/item['path']).resolve()
        if not target.is_relative_to(out): raise ValueError('Manifest path escapes destination')
        url=urllib.parse.urlparse(item['url'])
        if url.scheme!='https' or not url.hostname or url.username or url.password:
            raise ValueError('Only public HTTPS URLs without embedded credentials are supported')
        if target.exists() and target.stat().st_size==item['bytes'] and digest(target)==item['sha256']:
            print('Verified cache:',target.name); continue
        target.parent.mkdir(parents=True,exist_ok=True); temp=target.with_suffix(target.suffix+'.download')
        try:
            with urllib.request.urlopen(item['url'],timeout=60) as response,temp.open('wb') as f:
                if urllib.parse.urlparse(response.geturl()).scheme!='https': raise ValueError('Insecure redirect')
                total=0
                for chunk in iter(lambda:response.read(1024*1024),b''):
                    total+=len(chunk)
                    if total>item['bytes']: raise ValueError('Download exceeds declared size')
                    f.write(chunk)
            if temp.stat().st_size!=item['bytes'] or digest(temp)!=item['sha256']:
                raise ValueError('Model size/checksum mismatch')
            os.replace(temp,target)
        finally:
            if temp.exists(): temp.unlink()

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--manifest',required=True); p.add_argument('--profile',choices=['demo','research'],default='demo'); p.add_argument('--out',default='models')
    a=p.parse_args(); download(a.manifest,a.profile,a.out)
