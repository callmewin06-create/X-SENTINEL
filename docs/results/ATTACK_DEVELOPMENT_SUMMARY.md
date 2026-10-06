# Attack development evidence

Both runs use balanced, disjoint official-training subsets: 40000 fit, 5000 selection and 10000 development, seed 17. They train two clean and twelve poisoned models in total. Poison rates use all fit rows as denominator (200/400/800 benign rows poisoned).

## Measured ASR

ASR is computed only on malware correctly detected by the corresponding clean model. Clean-trigger ASR applies the identical trigger to that clean model as a direct-evasion control. Intervals and per-model clean TPR/FPR are in the detailed artifacts.

| Run | Selector | Poison rate | Success / eligible | ASR | Clean-trigger ASR | Clean accuracy after poisoning | Screen pass |
|---|---|---:|---:|---:|---:|---:|---|
| 100-round screen | legacy_rare | 0.5% | 221/4725 | 4.68% | 0.25% | 94.54% | False |
| 100-round screen | legacy_rare | 1.0% | 415/4725 | 8.78% | 0.25% | 94.59% | False |
| 100-round screen | legacy_rare | 2.0% | 1945/4725 | 41.16% | 0.25% | 94.67% | False |
| 100-round screen | joint_benign_rare | 0.5% | 119/4725 | 2.52% | 0.78% | 94.69% | False |
| 100-round screen | joint_benign_rare | 1.0% | 190/4725 | 4.02% | 0.78% | 94.71% | False |
| 100-round screen | joint_benign_rare | 2.0% | 487/4725 | 10.31% | 0.78% | 94.46% | False |
| 500-round capacity follow-up | legacy_rare | 0.5% | 318/4804 | 6.62% | 0.12% | 96.40% | False |
| 500-round capacity follow-up | legacy_rare | 1.0% | 540/4804 | 11.24% | 0.12% | 96.17% | False |
| 500-round capacity follow-up | legacy_rare | 2.0% | 1782/4804 | 37.09% | 0.12% | 96.30% | False |
| 500-round capacity follow-up | joint_benign_rare | 0.5% | 91/4804 | 1.89% | 0.75% | 96.37% | False |
| 500-round capacity follow-up | joint_benign_rare | 1.0% | 137/4804 | 2.85% | 0.75% | 96.30% | False |
| 500-round capacity follow-up | joint_benign_rare | 2.0% | 443/4804 | 9.22% | 0.75% | 96.24% | False |

No configuration passed the predeclared screen (ASR >=50%, paired gain >=20 percentage points, >=1000 eligible malware, and <=2 percentage point loss in accuracy/TPR or increase in FPR). The maximum measured ASR was 1945/4725 = 41.16% (Wilson 95%: 39.77%–42.57%), against 0.25% clean-trigger ASR, at 2% poisoning with the legacy selector in the 100-round screen. This is below the chosen screening target, not proof that poisoning has no effect. The observed-benign joint selector did not improve ASR in either run.

Clean accuracy before poisoning: 94.53% at 100 rounds and 96.34% at research capacity. The capacity follow-up changes the full LightGBM parameter configuration and reselects trigger values; it is not an isolated round-count ablation. It reuses observed development data, so the comparison is exploratory and is not independent confirmation.

## Resources and integrity

| Run | Training/evaluation time after data audit | Whole-process peak working set |
|---|---:|---:|
| 100-round screen | 53.00 s | 2.09 GiB |
| 500-round capacity follow-up | 381.46 s | 2.10 GiB |

All twelve model artifacts passed checks of source snapshots, model/candidate hashes, disjoint partition indices, poison counts and benign fit membership, development identities/labels, and metric reconstruction from saved prediction CSVs. These resource figures do not predict full 600000-row training or detector evaluation costs.

These development commands opened only training arrays. The earlier integration pilot had already evaluated a small subset derived from official test; do not describe the entire project history as an untouched-test study. Preserve and disclose that pilot exposure in the final protocol. No detector thresholds, scores or profile were selected using these development results.

## Next research decisions

1. Reconcile and validate the authors' combined greedy selector with explicit tests against source behavior; the current local selectors are adaptations.
2. Freeze the candidate protocol, resource plan and confirmation split before independent confirmation. Do not reuse observed development as independent evidence.
3. Resolve feasible-only versus a separately declared 27-configuration vector stress matrix. Feasible does not support the planned spread/cross families.
4. Only then run official training/evaluation and replace pilot report/slide conclusions with measured results, preserving failed attacks.

Detailed reports: [100-round screen](attack_development_v1/report.md), [500-round capacity follow-up](attack_development_500rounds_v2/report.md). Local source/model/prediction archives remain under outputs and are excluded from Git.
