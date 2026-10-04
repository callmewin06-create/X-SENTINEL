# X-SENTINEL experiment report

Run status: complete. Pilot: True. Completed evaluations: 1.

## Research question

Can cross-view evidence identify distributed feature-space triggers missed by top-feature attribution, at independently calibrated benign false-positive rates?

## Method and scope

EMBER2018 v2, LightGBM binary malware output, native additive SHAP, TADR and tabular STRIP. Reduced/full and limited-M5 variants use equal-weight reference ranks. Separate benign reference and calibration splits lock each threshold before evaluation. Full requires additional clean-trained view classifiers. M5 sensitive API/string evidence is unsupported in the primary group-only implementation.

Attack profile: feasible. Poison denominator: all labeled training rows. Seed-specific results are retained; repeated observations across seeds are not pooled as independent.

## Results

| Seed | Trigger | Rate | Method | AUROC trigger/benign | AUROC trigger/malware | Recall | Benign FPR | ASR before | ASR after |
|---|---|---|---|---|---|---|---|---|---|
| 17 | concentrated | 0.01 | TADR | 0.3213 | 0.3842 | 0.0000 | 0.0000 | 0.1149 | 0.1149 |
| 17 | concentrated | 0.01 | M3 | 0.5688 | 0.7195 | 0.0000 | 0.0100 | 0.1149 | 0.1149 |
| 17 | concentrated | 0.01 | M4_reduced | 0.6762 | 0.5949 | 0.0000 | 0.0200 | 0.1149 | 0.1149 |
| 17 | concentrated | 0.01 | M5_limited | 0.5000 | 0.5000 | 0.0000 | 0.0000 | 0.1149 | 0.1149 |
| 17 | concentrated | 0.01 | M4_full | 0.4018 | 0.7088 | 0.0200 | 0.0200 | 0.1149 | 0.1149 |
| 17 | concentrated | 0.01 | STRIP | 0.2109 | 0.4061 | 0.0000 | 0.0400 | 0.1149 | 0.1149 |
| 17 | concentrated | 0.01 | X_reduced | 0.5802 | 0.7304 | 0.0000 | 0.0100 | 0.1149 | 0.1149 |
| 17 | concentrated | 0.01 | X_reduced_M5_limited | 0.5799 | 0.7299 | 0.0000 | 0.0100 | 0.1149 | 0.1149 |
| 17 | concentrated | 0.01 | X_full | 0.4399 | 0.7398 | 0.0100 | 0.0200 | 0.1149 | 0.1149 |
| 17 | concentrated | 0.01 | X_full_M5_limited | 0.4401 | 0.7396 | 0.0100 | 0.0200 | 0.1149 | 0.1149 |

## Statistical evidence

Each evaluation JSON contains Wilson 95% intervals for rates, stratified bootstrap AUROC intervals and paired AUROC differences against TADR. E3 IDs and explanations are saved separately. Differences across seeds should be summarized descriptively, retaining within-seed uncertainty. The bootstrap sign-tail statistic is reported as a descriptive tail statistic, not a DeLong test.

## Limitations and negative findings

- This is a pilot/subset run. No final research claim or full-matrix completion is implied.
- Seed 17, concentrated, rate 0.01: attack ASR below the 50% viability diagnostic. Detector metrics cannot establish defense effectiveness against a strong backdoor in this run.
- Feature-space interventions do not establish behavior-preserving binary modifications. Authors' feasible features do not cover a three-view trigger; vector_stress is a distinct experimental profile.
- Modern LIEF PE extraction remains experimental until paired legacy extraction is validated.
- Rare cohorts are reference-defined entropy/size proxies; no packed ground truth is available.
- Calibration FPR is an empirical constraint, not a guarantee for deployment.

## Reproduction

Configuration and hashes: `reproducible_pilot/run_manifest.json`. See README commands and METHOD_SPEC for formulas. Uploaded binaries are never executed; attacks manipulate public feature vectors only.
