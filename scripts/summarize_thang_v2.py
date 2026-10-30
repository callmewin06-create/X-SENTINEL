"""Build review tables from saved scores; do not tune any detector."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.revision.analysis import attack_groups
from xsentinel.revision.low_fpr import low_fpr_metrics
from analyze_fusion_overlap import ROOT,cells,csv_out,METHODS

def main():
    out=ROOT/'handoff';out.mkdir(parents=True,exist_ok=True)
    old=pd.read_csv(ROOT/'frozen_audit/calibration_comparison_per_run.csv')
    old=old[old.policy=='legacy'].copy();old['policy']='empirical_calibration'
    extras=[]
    for path in cells():
        r=read_json(path)
        with np.load(path.parent/'paired_predictions.npz',allow_pickle=False) as z:
            mask=attack_groups(z['clean_malware_p'],z['triggered_main_p'],z['clean_trigger_p'])['successful_eligible']
            for m in METHODS:
                low=low_fpr_metrics(z['full_trigger_'+m][mask],z['full_benign_'+m])
                extras.append({**{k:r[k] for k in ['dataset','seed','family','rate']},'method':m,
                    'low_fpr_tpr':low['tpr'],'low_fpr_fpr':low['fpr'],'standardized_partial_auc':low['standardized_partial_auc']})
    old=old.merge(pd.DataFrame(extras),on=['dataset','seed','family','rate','method'],validate='one_to_one')
    frames=[old]
    shap_rows=[];shap_ledger={}
    for p in sorted(Path('outputs/teacher_revision_2026_10_27/shap_if').glob('*/seed_*/*/rate_*/result.json')):
        r=read_json(p)
        for source,digest in r['source_hashes'].items():
            assert sha256(source)==digest
        for name,digest in r['output_hashes'].items():assert sha256(p.parent/name)==digest
        shap_ledger[str(p)]=sha256(p)
        m=r['metrics'];f=m['benign_fpr'];t=m['recall_successful_eligible'];low=r['low_fpr']['successful_eligible']
        shap_rows.append({**{k:r[k] for k in ['dataset','seed','family','rate','confirmed']},'method':'SignedSHAPIF',
            'policy':'empirical_calibration','tau':m['threshold'],'fp':f['count'],'n_benign':f['n'],'fpr':f['rate'],
            'tp':t['count'],'n_successful':t['n'],'recall':t['rate'],'low_fpr_tpr':low['tpr'],'low_fpr_fpr':low['fpr'],
            'standardized_partial_auc':low['standardized_partial_auc']})
    assert len(shap_rows)==54
    frames.append(pd.DataFrame(shap_rows));write_json(out/'existing_shap_if_sources.json',shap_ledger)
    for folder in ['raw_baselines','public_shadow','view3']:
        if folder=='public_shadow':
            frames.append(pd.read_csv(ROOT/folder/'public_shadow_per_run.csv'))
        else:
            records=[]
            for p in sorted((ROOT/folder).glob('*/seed_*/*/rate_*/result.json')):records.extend(read_json(p)['rows'])
            if records:frames.append(pd.DataFrame(records))
    full=pd.concat(frames,ignore_index=True);full.to_csv(out/'all_methods_per_run.csv',index=False)
    primary=full[full.policy=='empirical_calibration']
    summary=[]
    for ds in primary.dataset.unique():
        for cohort in ['all_attempted','restricted_confirmed','cross_confirmed']:
            g=primary[primary.dataset==ds]
            if cohort!='all_attempted':g=g[g.confirmed & ((g.family=='cross_3view_stress')==(cohort=='cross_confirmed'))]
            for method,part in g.groupby('method'):
                summary.append(dict(dataset=ds,cohort=cohort,method=method,runs=len(part),seeds=part.seed.nunique(),
                    recall=part.recall.mean(),fpr=part.fpr.mean(),low_fpr_tpr=part.low_fpr_tpr.mean(),
                    low_fpr_fpr=part.low_fpr_fpr.mean(),standardized_partial_auc=part.standardized_partial_auc.mean()))
    csv_out(out/'comparison_cohorts.csv',summary)
    primary.groupby(['dataset','family','rate','confirmed','method']).agg(runs=('seed','size'),
        seeds=('seed','nunique'),recall=('recall','mean'),recall_sd=('recall','std'),fpr=('fpr','mean'),
        same_fpr_recall=('low_fpr_tpr','mean'),pauc=('standardized_partial_auc','mean')).to_csv(out/'all_methods_stratified.csv')
    # Bootstrap paired differences within strata. Identical seed draws per method.
    rng=np.random.default_rng(20261030);ci=[]
    for key,g in primary.groupby(['dataset','family','rate']):
        pivot=g.pivot(index='seed',columns='method',values='low_fpr_tpr')
        draws=rng.integers(0,len(pivot),(10000,len(pivot)))
        for m in pivot:
            values=(pivot[m]-pivot['X_primary_reduced']).to_numpy();s=values[draws];n=np.isfinite(s).sum(axis=1)
            estimates=np.divide(np.nansum(s,axis=1),n,out=np.full(len(draws),np.nan),where=n>0);v=estimates[np.isfinite(estimates)]
            ci.append(dict(zip(['dataset','family','rate'],key))|dict(method=m,reference='X_primary_reduced',
                seeds_available=int(np.isfinite(values).sum()),difference=float(np.nanmean(values)) if np.isfinite(values).any() else None,
                low=float(np.quantile(v,.025)) if len(v) else None,high=float(np.quantile(v,.975)) if len(v) else None,
                valid_draws=len(v),scope='Within-stratum seed clusters; three clusters at most; retrospective same-FPR operating points'))
    csv_out(out/'baseline_paired_seed_ci.csv',ci)
    # Freeze per-input provenance and detect accidental mutation of old scores.
    ledger=read_json(ROOT/'frozen_audit/manifest.json')['sources']
    assert all(sha256(p)==h for p,h in ledger.items())
    coverage=primary.groupby(['dataset','method']).size().to_dict()
    write_json(out/'completion_audit.json',dict(frozen_sources_unchanged=True,
        coverage={f'{d}/{m}':int(n) for (d,m),n in coverage.items()},
        new_validation=False,public_shadow='One independent 20K training seed, 27 EMBER2018 cells; not V3',
        view3_pilot_migration='Sharding added after two pilots; same scoring/fit algorithm, pilot source protocol retained',
        code_sha256=sha256(__file__)))
    print(pd.DataFrame(summary).query("cohort == 'restricted_confirmed'").to_string(index=False))

if __name__=='__main__':main()
