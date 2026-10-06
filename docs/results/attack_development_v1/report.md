# Train-only attack development

Seed 17; fit/selection/development = 40000/5000/10000, balanced stratified subsets of official train.

Official test arrays were not opened. All selectors, rates and screen rules were locked before development predictions. This is exploratory training development, not final research evidence.

| Selector | Poison rate | ASR | Clean-trigger ASR | Paired gain | Clean accuracy after poisoning | Screen pass |
|---|---:|---:|---:|---:|---:|---|
| legacy_rare | 0.50% | 4.68% | 0.25% | 4.42% | 94.54% | False |
| legacy_rare | 1.00% | 8.78% | 0.25% | 8.53% | 94.59% | False |
| legacy_rare | 2.00% | 41.16% | 0.25% | 40.91% | 94.67% | False |
| joint_benign_rare | 0.50% | 2.52% | 0.78% | 1.74% | 94.69% | False |
| joint_benign_rare | 1.00% | 4.02% | 0.78% | 3.24% | 94.71% | False |
| joint_benign_rare | 2.00% | 10.31% | 0.78% | 9.52% | 94.46% | False |

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
