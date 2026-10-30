"""Final deliverable gate: never label partial baseline coverage complete."""
import sys,csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import pandas as pd
from xsentinel.utils import read_json,write_json,sha256
from analyze_fusion_overlap import ROOT

def main():
    verification=read_json(ROOT/'verification.json')
    if verification['verified_counts']!={'raw_baselines':54,'view3':54,'public_shadow':27}:
        raise RuntimeError('Final handoff requires verified 54 raw, 54 view3, 27 public cells')
    d=pd.read_csv(ROOT/'handoff/comparison_cohorts.csv')
    lines=['# Results for manuscript integration','',
        'All results below use the previously observed original benchmark. They are not new independent validation. Percentages are macro means over the explicitly stated cells. The final-pool FPR-cap operating point is retrospective, distinct from the calibration operating point.','',
        '| Dataset / cohort | Method | Cells | Calibrated recall (%) | Calibrated FPR (%) | Recall at empirical FPR cap (%) | Standardized pAUC |',
        '|---|---|---:|---:|---:|---:|---:|']
    for r in d[d.cohort.isin(['restricted_confirmed','cross_confirmed'])].itertuples():
        lines.append(f'| {r.dataset} / {r.cohort} | {r.method} | {r.runs} | {100*r.recall:.2f} | {100*r.fpr:.3f} | {100*r.low_fpr_tpr:.2f} | {r.standardized_partial_auc:.4f} |')
    lines+=['','## Calibration and fusion findings','',
        'Across the 108 Reduced/Full endpoints, observed final-pool FPR violations decreased from six under the original thresholds to zero under the pointwise tolerance thresholds. Across the broader family of 378 cached-method endpoints, violations decreased from 79 to 13 for the pointwise policy and to three for the family-adjusted policy. These are observed counts, not a guarantee of zero future violations. On the three restricted-confirmed EMBER2024 runs, Reduced recall decreased from 48.33% to 38.53% under the pointwise tolerance policy while mean FPR decreased from 0.777% to 0.407%.',
        '', 'In the same EMBER2024 restricted-confirmed cohort at retrospective FPR-cap operating points, BGS uniquely detected 669 run-sample observations, whereas fusion missed 3,550 observations detected by VMC. These totals reuse source records across models and are not independent sample counts. Among VMC detections lost by fusion, mean VMC and BGS reference ranks were approximately 0.999 and 0.727, respectively. We do not select new fusion weights on this final pool.',
        '', '## Independent public Shadow','',
        'The independent 20K BODMAS Shadow achieved 99.50% classification accuracy on its 5K public validation split but 83.06% on EMBER2018 final records. On the 12 restricted-confirmed EMBER2018 cells, its retrospective FPR-cap detection recall was 16.17%, compared with 37.69% for Reduced and 44.72% for Full. This is one independently trained public model, not 27 independent public-model runs. It does not establish that all public-data defenders are weak.',
        '', '## Random-removal correction','',
        'Both original random controls removed 169 of the 4,000 poisoned records. Reconstruction from saved source identifiers confirms identical poison and removal rank-position patterns in equally sized 100,000-record benign pools. The expected overlap is 200, and the two controls are not independent random-position replications. The observed counts are retained unchanged.',
        '', '## Limitations that must remain visible','',
        'Nine of the twelve confirmed EMBER2024 configurations belong to the Cross-view stress family, where Reduced recall is approximately zero. Seed-cluster intervals have only three clusters per original stratum and are descriptive; increasing bootstrap repetitions does not increase the number of training runs. Score, preprocessing, and threshold policies were not independently certified on a new benign pool. The new baselines use fixed settings, not an exhaustive hyperparameter search. The Public-Shadow experiment uses one seed and one 20K budget. Additional original-Severi-selector experiments, an adaptive poisoning-time threat model, binary feasibility evidence, and literature/editorial corrections are not established by this implementation.']
    dest=ROOT/'handoff/results_for_paper_en.md';dest.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    p=ROOT/'claim_task_matrix.csv'
    with p.open(encoding='utf-8',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    for r in rows:
        if r['item']=='M5':r['status']='Raw, rarity and view3 complete';r['evidence']='Seven raw/rarity baselines plus signed-view3 IF on all 54 cells'
    with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    write_json(ROOT/'handoff/deliverable_manifest.json',dict(status='Six assigned work packages implemented, with scientific limitations and team dependencies documented',
        verified_counts=verification['verified_counts'],new_validation=False,
        files={str(p):sha256(p) for p in ROOT.rglob('*') if p.is_file() and p.suffix in ['.csv','.md','.png','.pdf']},
        manuscript_edited=False,web_default_changed=False,committed=False,pushed=False))
    print('Final handoff gate passed',dest)

if __name__=='__main__':main()
