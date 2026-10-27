"""Calibration/final tail diagnostics and score-direction evidence from caches."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.revision.analysis import attack_groups,ranking_auc

ROOT=Path('outputs/teacher_revision_2026_10_27')


def main():
    out=ROOT/'diagnostics';out.mkdir(exist_ok=True)
    rows=[];auc=[];sources={}
    methods=['TADR','STRIP','M3_view_mass','M4_shap_behavioral_conflict','M4_prob_gap','X_primary_reduced','X_primary_full']
    for ds in ('EMBER2018','EMBER2024'):
        for cell in sorted((Path('outputs/primary')/ds/'protocol_v2').glob('seed_*/*/rate_*')):
            r=read_json(cell/'result.json');rel=Path(ds)/cell.relative_to(Path('outputs/primary')/ds/'protocol_v2')
            base=dict(dataset=ds,seed=r['seed'],family=r['family'],rate=r['rate'],confirmed=r['independently_confirmed_strong_and_stealth'])
            tau=read_json(cell/'bundle_full/bundle.json')['thresholds']
            paths=[cell/'paired_predictions.npz',Path('outputs/revision_2026_10_13/supplement')/rel/'calibration_scores.npz',ROOT/'shadow_scores'/rel/'scores.npz',ROOT/'shap_if'/rel/'scores.npz']
            for p in paths:sources[str(p)]=sha256(p)
            with np.load(paths[0],allow_pickle=False) as a,np.load(paths[1],allow_pickle=False) as c,np.load(paths[2],allow_pickle=False) as s,np.load(paths[3],allow_pickle=False) as i:
                scores={m:(c[m],a['full_benign_'+m],tau[m]) for m in methods}
                supplement=read_json(Path('outputs/revision_2026_10_13/supplement')/rel/'calibration.json')
                scores['Shadow']=(s['calibration'],s['benign'],supplement['shadow']['tau'])
                scores['STRIP_inverse']=(1-c['STRIP'],1-a['full_benign_STRIP'],supplement['strip_inverse']['tau'])
                scores['SHAP-IF']=(i['calibration'],i['benign'],read_json(ROOT/'shap_if'/rel/'result.json')['metrics']['threshold'])
                for method,(cal,final,t) in scores.items():
                    rows.append({**base,'method':method,'threshold':t,'cal_n':len(cal),'cal_fp':int(np.sum(cal>t)),
                        'cal_fpr':float(np.mean(cal>t)),'cal_equal_threshold':int(np.sum(cal==t)),
                        'final_n':len(final),'final_fp':int(np.sum(final>t)),'final_fpr':float(np.mean(final>t)),
                        'final_equal_threshold':int(np.sum(final==t)),'cal_p99':float(np.quantile(cal,.99)),
                        'final_p99':float(np.quantile(final,.99)),'cal_unique':len(np.unique(cal)),'final_unique':len(np.unique(final))})
                groups=attack_groups(a['clean_malware_p'],a['triggered_main_p'],a['clean_trigger_p'])
                for method in ('TADR','STRIP'):
                    for group in ('all_triggered','successful_eligible'):
                        ps=a['full_trigger_'+method][groups[group]];ns=a['full_benign_'+method]
                        auc.append({**base,'method':method,'group':group,'native_auc':ranking_auc(ps,ns),
                            'negated_auc_diagnostic':ranking_auc(-ps,-ns)})
    df=pd.DataFrame(rows);df.to_csv(out/'fpr_tail_diagnostics.csv',index=False)
    pd.DataFrame(auc).to_csv(out/'score_direction_diagnostics.csv',index=False)
    summary=df[df.confirmed].groupby(['dataset','method']).agg(runs=('seed','size'),cal_fpr_mean=('cal_fpr','mean'),
        final_fpr_mean=('final_fpr','mean'),final_fpr_min=('final_fpr','min'),final_fpr_max=('final_fpr','max'),
        calibration_threshold_ties_mean=('cal_equal_threshold','mean'),final_threshold_ties_mean=('final_equal_threshold','mean')).reset_index()
    summary.to_csv(out/'fpr_diagnostic_summary.csv',index=False)
    notes='''# Diagnostic text and editor notes

## Calibration versus final FPR

The 1% target constrains the observed calibration pool, not the final pool. We retain the strict score > threshold rule. Equal scores at the cutoff are not flagged. The supplied diagnostics report counts above and equal to the threshold, unique score counts and the 99th percentile in both pools. Final FPR can exceed the calibration target despite a correctly implemented threshold. Ties constrain attainable operating points, but do not alone prove the cause of an upward final FPR difference. Finite-sample variation and differences between the two benign score distributions remain possible explanations; this analysis does not isolate a causal contribution from each. The same-FPR and partial-AUC tables address ranking comparison separately.

## Score direction

AUROC below 0.5 indicates that the implemented score tends to rank the evaluated positives below benign negatives. This may reveal mismatch between a heuristic and this population; it does not by itself prove a coding sign error. Negating a score reverses its ranking AUC, with tie handling preserved. The negated TADR column is a diagnostic obtained after observing outcomes, not a newly validated defense. STRIP_inverse retains its separately calibrated threshold and is explicitly labelled. Mixing hashed/count feature vectors is a synthetic intervention and need not represent executable-file behavior. SHAP-IF uses its prespecified anomaly orientation without selecting the sign from final performance.

## Timing replacement

The reported timing measurements refer to different execution scopes and input sets: core detector scoring, the small maintenance smoke test, and end-to-end file processing. They should be presented separately. In particular, the observed EMBER2024 Full change from19.28 to27.28 ms is not evidence of an optimization or a confirmed regression mechanism. We have not isolated the cause with a controlled timing experiment. Replace the vague near28 ms wording with the exact named benchmark and its21–32 ms reported range where applicable; do not merge these measurements into one latency claim. Current supplementary training/scoring jobs ran concurrently and their elapsed times are provenance, not replacement latency benchmarks.

## Final Word checklist

- Table IV:17,29,43; additional seeds59,71 belong to the supplemental seed table.
- Table XVII: distinguish175 successfully scored files from200 attempted files; the known2018 Reduced count is2 alerts, not212. Verify against the BODMAS source table before export.
- Table III: use is_pe=0: benign/malware for the count pair.
- The benign fixture called malware is a false classification; explain it in Limitations.
- Rebuild equations with the Word equation editor using proper summation indices and p_Beh(x_Beh), then inspect the exported PDF. Text extraction alone cannot verify the typography.
- Use all fit records consistently as the poisoning denominator:1000/2000/4000 of200000 correspond to0.5/1/2%; the benign fit half has100000 records.
- Remove revision-history and course-rubric prose from the research narrative. Keep engineering history in a separate artifact appendix.

The latest canonical Word and Phuc's binary results have not been supplied. These are editing instructions and evidence notes, not a claim that the final Word has been repaired or visually verified.
'''
    (out/'diagnostic_notes_en.md').write_text(notes,encoding='utf8')
    write_json(out/'manifest.json',dict(source_hashes=sources,rows=len(rows),source_code_sha256=sha256(__file__)))
    print('Diagnostic rows',len(rows),flush=True)


if __name__=='__main__':main()
