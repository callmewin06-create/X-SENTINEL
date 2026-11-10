"""Reproduce journal revision summaries without fitting models or opening feature arrays."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def key(row): return (row['dataset'], int(row['seed']), row['family'], float(row['rate']))
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    args=parser.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    source=ROOT/'outputs/teacher_revision_v2_thang_2026_10_30/handoff/all_methods_per_run.csv'
    with source.open(encoding='utf-8-sig',newline='') as stream: rows=list(csv.DictReader(stream))
    confirmation={};inputs={str(source.relative_to(ROOT)):sha(source)}
    for dataset in ['EMBER2018','EMBER2024']:
        paths=list((ROOT/'outputs/primary_confirmation'/dataset/'round_1').glob('seed_*/*/rate_*/result.json'))
        if len(paths)!=27:raise ValueError(f'Expected 27 confirmation records: {dataset}/{len(paths)}')
        for path in paths:
            r=json.loads(path.read_text(encoding='utf-8'));k=key(r)
            if k in confirmation or r['phase']!='confirmation' or r['status']!='complete':
                raise ValueError('Duplicate/incomplete/wrong phase confirmation')
            confirmation[k]=r;inputs[str(path.relative_to(ROOT))]=sha(path)
    empirical=[r for r in rows if r['policy']=='empirical_calibration']
    lookup={}
    for r in empirical:
        k=(key(r),r['method'])
        if k in lookup:raise ValueError('Duplicate final endpoint')
        lookup[k]=r
    def passed(r,cutoff):
        return (r['n_eligible']>=1000 and r['asr']['rate']>=cutoff and
                r['paired_gain']>=.20 and r['accuracy_drop']<.005)
    summary=[]
    for cutoff in [.4,.5,.6]:
        for dataset in ['EMBER2018','EMBER2024']:
            for geometry in ['restricted','cross']:
                selected=[k for k,r in confirmation.items() if k[0]==dataset and
                          (k[2] in ['concentrated_structural','spread_structural'])==(geometry=='restricted')
                          and passed(r,cutoff)]
                for method in ['M3_view_mass','X_primary_reduced','X_primary_full','raw_knn_top32','TADR']:
                    endpoints=[lookup[(k,method)] for k in selected]
                    if any(int(r['n_successful'])==0 for r in endpoints):raise ValueError('Undefined recall needs explicit handling')
                    summary.append({'min_confirmation_asr':cutoff,'dataset':dataset,'cohort':geometry,
                        'method':method,'cells':len(selected),
                        'macro_recall':statistics.mean(float(r['recall']) for r in endpoints) if endpoints else None,
                        'macro_final_fpr':statistics.mean(float(r['fpr']) for r in endpoints) if endpoints else None,
                        'tp_sum_descriptive':sum(int(r['tp']) for r in endpoints),
                        'success_observations_sum':sum(int(r['n_successful']) for r in endpoints),
                        'cell_keys':[list(k) for k in sorted(selected)]})
    headline=[r for r in summary if r['min_confirmation_asr']==.5 and r['cohort']=='restricted' and r['method']=='X_primary_reduced']
    for r,expected,n in zip(headline,[.3575,.4833],[12,3]):
        if r['cells']!=n or abs(r['macro_recall']-expected)>.0001:raise ValueError('Headline mismatch')
    primary=[]
    for dataset in ['EMBER2018','EMBER2024']:
        for path in sorted((ROOT/'outputs/primary'/dataset/'protocol_v2').glob('seed_*/*/rate_*/*')):
            if path.name in ['attack.json','poisoned.txt','paired_predictions.npz','result.json']:
                primary.append({'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
    if len(primary)!=54*4:raise ValueError('Primary snapshot incomplete')
    report={'scope':'Cached retrospective diagnostics; no training, new thresholds or feature-array access',
        'input_hashes':inputs,'confirmation_records':54,'headline':headline,'sensitivity':summary,
        'interpretation':'Macro over cells. Reused source IDs across cells are not independent samples; sums are descriptive only.',
        'new_protocol_primary_cutoff':.5,'final_used_to_select_cutoff':False}
    (out/'CACHE_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'PRIMARY_BEFORE.json').write_text(json.dumps(primary,indent=2)+'\n',encoding='utf-8')
    with (out/'SENSITIVITY.csv').open('w',newline='',encoding='utf-8') as stream:
        fields=[k for k in summary[0] if k!='cell_keys'];writer=csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader();writer.writerows({k:r[k] for k in fields} for r in summary)
    print(json.dumps({'headline':headline,'primary_files_locked':len(primary),'output':str(out)}))
if __name__=='__main__':main()
