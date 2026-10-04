"""English evidence-backed report and slide outline from actual run artifacts."""
import csv
from pathlib import Path
import numpy as np
from xsentinel.utils import read_json,write_json

def generate(run_dir):
    root=Path(run_dir); manifest=read_json(root/'run_manifest.json')
    evaluations=sorted(root.glob('seed_*/*/evaluation/evaluation.json'))
    lines=['# X-SENTINEL experiment report','',
        f"Run status: {manifest['status']}. Pilot: {manifest['pilot']}. Completed evaluations: {len(evaluations)}.",'',
        '## Research question','',
        'Can cross-view evidence identify distributed feature-space triggers missed by top-feature attribution, at independently calibrated benign false-positive rates?','',
        '## Method and scope','',
        'EMBER2018 v2, LightGBM binary malware output, native additive SHAP, TADR and tabular STRIP. Reduced/full and limited-M5 variants use equal-weight reference ranks. Separate benign reference and calibration splits lock each threshold before evaluation. Full requires additional clean-trained view classifiers. M5 sensitive API/string evidence is unsupported in the primary group-only implementation.','',
        f"Attack profile: {manifest['attack_profile']}. Poison denominator: all labeled training rows. Seed-specific results are retained; repeated observations across seeds are not pooled as independent.",'',
        '## Results','',
        '| Seed | Trigger | Rate | Method | AUROC trigger/benign | AUROC trigger/malware | Recall | Benign FPR | ASR before | ASR after |','|---|---|---|---|---|---|---|---|---|---|']
    def num(x): return 'NA' if x is None else f'{x:.4f}'
    table=[]; limitations=[]
    for path in evaluations:
        e=read_json(path); dest=path.parents[1]; kind,pr=dest.name.rsplit('_',1); seed=int(dest.parent.name.split('_')[1])
        for method,m in e['metrics'].items():
            row={'seed':seed,'trigger':kind,'rate':float(pr),'method':method,'auroc_trigger_benign':m['auroc_trigger_vs_benign'],
                'auroc_trigger_malware':m['auroc_trigger_vs_malware'],'recall':m['recall_all_trigger']['rate'],'fpr':m['benign_fpr']['rate'],
                'asr_before':e['attack_asr']['rate'],'asr_after':m['post_defense_asr']['rate']}
            table.append(row)
            lines.append('| '+' | '.join(str(row[k]) if k in ('seed','trigger','rate','method') else num(row[k]) for k in row)+' |')
        if not e['attack_viable_at_50pct']:
            limitations.append(f"Seed {seed}, {kind}, rate {pr}: attack ASR below the 50% viability diagnostic. Detector metrics cannot establish defense effectiveness against a strong backdoor in this run.")
    lines += ['','## Statistical evidence','',
        'Each evaluation JSON contains Wilson 95% intervals for rates, stratified bootstrap AUROC intervals and paired AUROC differences against TADR. E3 IDs and explanations are saved separately. Differences across seeds should be summarized descriptively, retaining within-seed uncertainty. The bootstrap sign-tail statistic is reported as a descriptive tail statistic, not a DeLong test.','',
        '## Limitations and negative findings','']
    if manifest['pilot']: limitations.insert(0,'This is a pilot/subset run. No final research claim or full-matrix completion is implied.')
    limitations += ['Feature-space interventions do not establish behavior-preserving binary modifications. Authors\' feasible features do not cover a three-view trigger; vector_stress is a distinct experimental profile.',
        'Modern LIEF PE extraction remains experimental until paired legacy extraction is validated.',
        'Rare cohorts are reference-defined entropy/size proxies; no packed ground truth is available.',
        'Calibration FPR is an empirical constraint, not a guarantee for deployment.']
    lines += ['- '+s for s in limitations]
    lines += ['','## Reproduction','',f"Configuration and hashes: `{root.name}/run_manifest.json`. See README commands and METHOD_SPEC for formulas. Uploaded binaries are never executed; attacks manipulate public feature vectors only.",'']
    dest=root/'report.md'; dest.write_text('\n'.join(lines),encoding='utf8')
    if table:
        with (root/'results.csv').open('w',newline='',encoding='utf8') as f:
            w=csv.DictWriter(f,fieldnames=list(table[0])); w.writeheader(); w.writerows(table)
    slides=['# X-SENTINEL','Per-input cross-view backdoor detection','',
        '---','## Research question','Detect input trigger suspicion at inference; distinguish malware classification from trigger alerts.','',
        '---','## Threat model','Clean-label feature-space poisoning; no main-model retraining by defender. Full adds clean-trained view classifiers.','',
        '---','## Methods','TADR; STRIP; view attribution concentration; behavioral disagreement; limited semantic plausibility.','',
        '---','## Blind protocol','Train-only trigger selection. Disjoint reference, calibration, and final test. Model-bound detector bundles.','',
        '---','## Evidence',f'{len(evaluations)} evaluated model configurations. Pilot={manifest["pilot"]}. Numerical tables in results.csv.','',
        '---','## Limitations']+limitations+['','---','## Demo','Vector upload → main probability → SHAP/views → locked threshold → PASS/BLOCK. PASS is not a safety certificate.']
    (root/'slides.md').write_text('\n'.join(slides),encoding='utf8')
    return str(dest)
