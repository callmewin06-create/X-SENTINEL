"""Static checks for three reviewed, self-built benign classroom fixtures."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from xsentinel.service.registry import BundleRegistry
from xsentinel.service.scoring import score_input
from xsentinel.data.pe import extract_pe
from xsentinel.data.pe_v3 import extract_pe_v3


def main():
    root=Path('output/demo_2026_10_20');registry=BundleRegistry();rows=[]
    for binary in sorted((root/'benign').glob('*.exe')):
        data=binary.read_bytes();source=root/'sources'/(binary.stem+'.cs')
        row={'name':binary.name,'declared_label':'BENIGN','source':'reviewed self-built C# source; no file/network operations',
            'sha256':hashlib.sha256(data).hexdigest(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'cases':[]}
        for dataset,extract in [('EMBER2018',extract_pe),('EMBER2024',extract_pe_v3)]:
            vector,provenance=extract(data)
            for variant in ('reduced','full'):
                entry=next(e for e in registry.entries.values() if e['dataset']==dataset and e['variant']==variant
                    and e['family']=='spread_structural' and e['rate']==.02 and e['seed']==17)
                detector,_=registry.loaded(entry['id']);result=score_input(detector,vector,'X_primary_'+variant,scope='selected')
                row['cases'].append({'dataset':dataset,'variant':variant,'bundle_id':entry['id'],
                    'classification':result['main_classification'],'probability':result['malware_probability'],
                    'trigger_alert':result['backdoor_alert'],'score':next(s['Score'] for s in result['scores'] if s['Method']==result['method'])})
        rows.append(row)
    (root/'catalog.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps([{'name':r['name'],'cases':r['cases']} for r in rows],indent=2))


if __name__=='__main__':main()
