# Train-only attack development

Seed 17; fit/selection/development = 40000/5000/10000, balanced stratified subsets of official train.

Official test arrays were not opened. All selectors, rates and screen rules were locked before development predictions. This is exploratory training development, not final research evidence.

| Selector | Poison rate | ASR | Clean-trigger ASR | Paired gain | Clean accuracy after poisoning | Screen pass |
|---|---:|---:|---:|---:|---:|---|
| legacy_rare | 0.50% | 6.62% | 0.12% | 6.49% | 96.40% | False |
| legacy_rare | 1.00% | 11.24% | 0.12% | 11.12% | 96.17% | False |
| legacy_rare | 2.00% | 37.09% | 0.12% | 36.97% | 96.30% | False |
| joint_benign_rare | 0.50% | 1.89% | 0.75% | 1.14% | 96.37% | False |
| joint_benign_rare | 1.00% | 2.85% | 0.75% | 2.10% | 96.30% | False |
| joint_benign_rare | 2.00% | 9.22% | 0.75% | 8.47% | 96.24% | False |

The joint selector uses an observed benign tuple and negative joint SHAP; it remains an adaptation and does not prove binary realizability. Feasible spread/cross are still unsupported.

Screen rules (heuristics, not statistical proof):
```json
{
  "malware_threshold": 0.5,
  "min_eligible": 1000,
  "min_asr": 0.5,
  "min_paired_gain": 0.2,
  "max_accuracy_drop": 0.02,
  "max_tpr_drop": 0.02,
  "max_fpr_increase": 0.02
}
```

Preserve this run. Any subsequent change needs a new config/output and must document reuse of development data. A passing candidate still needs independent confirmation and full-size training; a failing screen does not establish defense efficacy.

Development history (observed data reuse; not independent confirmation):
```json
{
  "purpose": "Exploratory capacity follow-up after observing the 100-round screen; not independent confirmation",
  "reuse": "Same fit, selection and observed development partitions as v1; same selectors, rates, and screen rules",
  "prior_run_manifest_sha256": "c4dabffc6624e2dc27cc6b2958e7738b0298df6970967d2a00cea1df9eb89921",
  "prior_results_sha256": "1353e76a47e9f91c94c303fac8b247e9b0cb4e1d0f9df856df781f61eebd3264",
  "partition_sha256": "8f33abc6498f2215318779843d10f6c15ea1cc0ae5ad2c7e585bfdd019b5a4da"
}
```
