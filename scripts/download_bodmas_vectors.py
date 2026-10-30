"""Download only the two public vector/metadata files linked by BODMAS."""
from pathlib import Path
import requests
from html.parser import HTMLParser

class Form(HTMLParser):
    def __init__(self):super().__init__();self.action=None;self.params={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='form':self.action=a.get('action')
        if tag=='input' and 'name' in a:self.params[a['name']]=a.get('value','')

def main():
    out=Path('data/public/bodmas');out.mkdir(parents=True,exist_ok=True)
    for name,ident,size in [('bodmas_metadata.csv','16UtiitjekNfqHGlLWtxkxyuU23o2qaja',12705748),('bodmas.npz','1_7uhKCrc9hmIOxxfZMoKK6aP8-GJ-DNJ',261557445)]:
        dest=out/name
        if dest.exists() and dest.stat().st_size==size:continue
        session=requests.Session();r=session.get('https://drive.google.com/uc',params={'export':'download','id':ident},stream=True,timeout=60);r.raise_for_status()
        if 'text/html' in r.headers.get('content-type',''):
            parser=Form();parser.feed(r.text)
            if not parser.action or not parser.action.startswith('https://drive.usercontent.google.com/'):raise RuntimeError('Unexpected Google download page')
            r=session.get(parser.action,params=parser.params,stream=True,timeout=60);r.raise_for_status()
        part=dest.with_suffix(dest.suffix+'.part');count=0
        with part.open('wb') as f:
            for chunk in r.iter_content(1024*1024):f.write(chunk);count+=len(chunk)
        if count!=size:raise ValueError(f'Unexpected file size for {name}: {count}')
        part.replace(dest);print('Downloaded',name,count,flush=True)

if __name__=='__main__':main()
