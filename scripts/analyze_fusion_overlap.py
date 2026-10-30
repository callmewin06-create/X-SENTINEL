"""Frozen-score M1/M6 audit. No model or deployed bundle mutation."""
import sys, json, csv, argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from xsentinel.utils import read_json, write_json, sha256
from xsentinel.revision.analysis import attack_groups
from xsentinel.revision.calibration_v2 import tolerance_threshold, exact_interval
from xsentinel.detection.calibration import threshold

ROOT=Path('outputs/teacher_revision_v2_thang_2026_10_30')
METHODS=['M3_view_mass','M4_shap_behavioral_conflict','M4_prob_gap','X_primary_reduced','X_primary_full','TADR','STRIP']

def csv_out(path,rows):
    if not rows:return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader();w.writerows(rows)

def cells():
    return sorted(Path('outputs/primary').glob('*/protocol_v2/seed_*/*/rate_*/result.json'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'frozen_audit');args=parser.parse_args()
    out=args.out
    if out.exists():raise FileExistsError('Use fresh output directory')
    out.mkdir(parents=True)
    ledger={}; overlap=[]; rows=[]; policies=[]
    paths=cells();assert len(paths)==54
    for path in paths:
        r=read_json(path);cell=path.parent
        calpath=Path('outputs/revision_2026_10_13/supplement')/r['dataset']/cell.relative_to(Path('outputs/primary')/r['dataset']/'protocol_v2')/'calibration_scores.npz'
        for p in [path,calpath,cell/'paired_predictions.npz',cell/'bundle_full/bundle.json']:
            ledger[str(p)]=sha256(p)
        for name,digest in r['artifact_sha256'].items():
            if sha256(cell/name)!=digest:raise ValueError('Frozen artifact mismatch: '+str(cell/name))
        with np.load(cell/'paired_predictions.npz',allow_pickle=False) as z:a={k:v.copy() for k,v in z.items()}
        with np.load(calpath,allow_pickle=False) as z:cal={k:v.copy() for k,v in z.items()}
        groups=attack_groups(a['clean_malware_p'],a['triggered_main_p'],a['clean_trigger_p'])
        base={k:r[k] for k in ('dataset','seed','family','rate')};base['confirmed']=r['independently_confirmed_strong_and_stealth']
        old=read_json(cell/'bundle_full/bundle.json')['thresholds']
        for method in METHODS:
            assert np.isclose(threshold(cal[method]),old[method],atol=1e-10,rtol=0)
            for policy,ep in [('legacy',None),('tolerance_pointwise',1),('tolerance_simultaneous_378',378)]:
                design=None if ep is None else tolerance_threshold(cal[method],endpoints=ep)
                tau=old[method] if design is None else design['threshold']
                if design:policies.append({**base,'method':method,**design})
                neg=a['full_benign_'+method];pos=a['full_trigger_'+method];mask=groups['successful_eligible']
                fp=int((neg>tau).sum());tp=int((pos[mask]>tau).sum());n=int(mask.sum())
                lo,hi=exact_interval(fp,len(neg))
                rows.append({**base,'method':method,'policy':policy,'tau':tau,'fp':fp,'n_benign':len(neg),
                    'fpr':fp/len(neg),'fpr_ci_low':lo,'fpr_ci_high':hi,'tp':tp,'n_successful':n,
                    'recall':tp/n if n else None,'asr':float(mask.sum()/groups['eligible'].sum()),
                    'exceeds_1pct':fp/len(neg)>.01})
        for operating in ('original_calibration','retrospective_final_cap'):
            ts={m:old[m] if operating=='original_calibration' else threshold(a['full_benign_'+m]) for m in METHODS}
            for group, suffix, mask in [('benign','benign',np.ones(len(a['benign_ids']),bool)),('successful_eligible','trigger',groups['successful_eligible']),('paired_new_evasion','trigger',groups['paired_new_evasion'])]:
                v,b,f=[a['full_'+suffix+'_'+m][mask]>ts[m] for m in ['M3_view_mass','M4_shap_behavioral_conflict','X_primary_reduced']]
                union=int((v|b).sum());both=int((v&b).sum())
                overlap.append({**base,'operating_point':operating,'group':group,'n':len(v),
                    'vmc_only':int((v&~b).sum()),'bgs_only':int((b&~v).sum()),'both':both,'neither':int((~v&~b).sum()),
                    'jaccard':both/union if union else None,'fusion_only':int((f&~v&~b).sum()),
                    'vmc_lost_by_fusion':int((v&~f).sum()),'bgs_lost_by_fusion':int((b&~f).sum())})
        print('Audited',base,flush=True)
    csv_out(out/'fusion_overlap_per_run.csv',overlap)
    csv_out(out/'calibration_comparison_per_run.csv',rows)
    import pandas as pd
    df=pd.DataFrame(rows)
    df.groupby(['dataset','method','policy'],dropna=False).agg(endpoints=('exceeds_1pct','size'),exceedances=('exceeds_1pct','sum'),mean_fpr=('fpr','mean'),mean_recall=('recall','mean')).to_csv(out/'fpr_exceedance_summary.csv')
    pd.DataFrame(overlap).groupby(['dataset','family','rate','confirmed','operating_point','group'],dropna=False).sum(numeric_only=True).drop(columns=['seed','jaccard']).to_csv(out/'fusion_overlap_summary_counts.csv')
    write_json(out/'calibration_policies.json',policies)
    if any(sha256(p)!=h for p,h in ledger.items()):raise ValueError('Input changed during audit')
    write_json(out/'manifest.json',dict(sources=ledger,cells=54,frozen_inputs_unchanged=True,
        scope='Retrospective recalibration, NOT independently certified; prior calibration exposure cannot be ruled out',
        simultaneous_family='54 cells x 7 fixed cached methods = 378; excludes new baselines',
        final_CI='Two-sided pointwise CP95; dependencies across endpoints remain',code_sha256=sha256(__file__)))

if __name__=='__main__':main()
