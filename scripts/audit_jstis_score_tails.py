"""Frozen reference-rank resolution, saturation and benign tail diagnostics."""
import argparse
import csv
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from xsentinel.utils import read_json,write_json,sha256


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',required=True); a=p.parse_args()
    out=Path(a.output)
    if out.exists() and any(out.iterdir()): raise FileExistsError('Fresh output required')
    out.mkdir(parents=True,exist_ok=True); rows=[]; inputs={}; fpr=[]
    for result in sorted((ROOT/'outputs/primary').glob('*/protocol_v2/seed_*/*/rate_*/result.json')):
        state=read_json(result); cell=result.parent
        calpath=ROOT/'outputs/revision_2026_10_13/supplement'/state['dataset']/cell.relative_to(ROOT/'outputs/primary'/state['dataset']/'protocol_v2')/'calibration_scores.npz'
        paths=[cell/'paired_predictions.npz',cell/'bundle_full/reference.npz',cell/'bundle_full/bundle.json',calpath]
        inputs.update({str(p.relative_to(ROOT)):sha256(p) for p in paths})
        with np.load(paths[0]) as z: final={k:z[k] for k in z.files if k.startswith('full_benign_')}
        with np.load(paths[1]) as z: reference={k:z[k] for k in z.files if k.startswith('rank_')}
        with np.load(calpath) as z: cal={k:z[k] for k in z.files}
        thresholds=read_json(paths[2])['thresholds']
        base={k:state[k] for k in ('dataset','seed','family','rate')}
        for method in ('M3_view_mass','M4_shap_behavioral_conflict','M4_prob_gap'):
            ref=np.sort(reference['rank_'+method])
            for role,score in [('calibration',cal[method]),('final_benign',final['full_benign_'+method])]:
                rank=np.searchsorted(ref,score,side='right')/len(ref)
                unique,counts=np.unique(rank,return_counts=True)
                rows.append({**base,'method':method,'role':role,'n':len(score),'reference_n':len(ref),
                    'reference_rank_step':1/len(ref),'unique_ranks':len(unique),
                    'rank_one_count':int((rank==1).sum()),'largest_rank_tie_count':int(counts.max()),
                    'score_q99':float(np.quantile(score,.99)),'score_q999':float(np.quantile(score,.999)),
                    'score_max':float(score.max()),'tau':thresholds[method],
                    'equal_tau_count':int((score==thresholds[method]).sum()),
                    'strict_exceedance_count':int((score>thresholds[method]).sum())})
        for method in ('X_primary_reduced','X_primary_full'):
            score=final['full_benign_'+method]; fp=int((score>thresholds[method]).sum())
            fpr.append({**base,'method':method,'fp':fp,'n':len(score),'fpr':fp/len(score),
                        'equal_tau':int((score==thresholds[method]).sum())})
    for name,data in [('rank_tails.csv',rows),('final_fpr.csv',fpr)]:
        with (out/name).open('w',encoding='utf8',newline='') as stream:
            w=csv.DictWriter(stream,fieldnames=list(data[0])); w.writeheader(); w.writerows(data)
    summary={m:{'cells':len([r for r in fpr if r['method']==m]),
                'point_estimate_above_1pct':sum(r['fpr']>.01 for r in fpr if r['method']==m),
                'worst_fp':max(r['fp'] for r in fpr if r['method']==m)}
             for m in ('X_primary_reduced','X_primary_full')}
    if any(sha256(ROOT/p)!=h for p,h in inputs.items()): raise ValueError('Frozen input changed')
    write_json(out/'RESULTS.json',{'summary':summary,'source_sha256':inputs,'code_sha256':sha256(__file__),
        'scope':'Descriptive paired calibration/final tails; no causal attribution to ties or shift',
        'threshold_source':'2000 calibration scores; reference500 sets rank resolution only'})
    print(summary)


if __name__=='__main__': main()
