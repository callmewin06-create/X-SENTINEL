# Research revisions completed27 October2026

## Verified deliverables

- Signed SHAP Isolation Forest:54 original cells, matched unmodified-malware controls and separately calibrated thresholds.
- Retrospective empirical-FPR-cap comparisons and standardized partial AUC, with original deployment thresholds retained.
- Cross confirmation/final diagnostics and24-cell bounded multiview adaptation.
- EMBER2024 spread2% seeds59 and71: five attempts including the original three, four confirmed; unsuccessful seed retained.
- Five nested labelled-fit budgets on both datasets and three seeds:30 budget checkpoints and810 method/configuration rows.
- Two-cell training sanitization experiment with independently sampled random-removal control and retraining utility measurements.
- 39 regression tests passed; 222 original assets in the protection manifest rechecked; cached metrics and source IDs audited.

Delivery: output/teacher_revision_2026_10_27/ and output/X_SENTINEL_REVIEW_2026_10_27.zip.
Detailed score/model evidence remains in outputs/teacher_revision_2026_10_27/. The small shareable archive contains tables, figures, protocols and source snapshots, not raw executable samples or model weights.

## Corrections during implementation

ember2024_seeds_v2 supersedes v1 scoring. Exact training checkpoints and triggers were reused, with calibration scored as a whole2000-row batch and final core scoring in128-row batches to match primary conventions. Native floating-point differences can affect ECDF ranks at exact ties; no arbitrary-batch bit-invariance is claimed.

training_defense_v2 supersedes the invalid v1 random-removal control. The earlier control accidentally used the same PCG64 seed as poison selection and therefore removed all selected poisons. The corrected control uses independent fixed seed20261027. Valid IF masks and model checkpoints were matched and retained; invalid random-control results are excluded from delivery tables. Source snapshots and the invalidity note remain for provenance.

## Interpretation and outstanding work

These changes add evidence and repair the evaluation framing. They do not remove Cross/adaptive weaknesses or establish binary trigger realizability. Reduced is the proposed primary setting; Full has conditional data-budget behavior, with no universal advantage over Shadow.

Quân's canonical Word and Phúc's binary results were not available. English manuscript inserts, figure captions and integration instructions are supplied; canonical Word editing/render QA and binary integration remain pending those artifacts. Phú's complete bibliography audit remains a separate team task.

No commit or push was performed for this research package.
