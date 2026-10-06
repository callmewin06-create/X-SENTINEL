# Attack audit and development protocol

Correction recorded 2026-10-05: the implementation's hardcoded feasible set has 16 columns, but recomputing `non_hashed - infeasible_features` from the vendored source yields 17 (13 Structural, 4 Metadata). Column 684, `minor_subsystem_version`, was omitted locally. Earlier statements equating the 16-column subset with the complete author set were inaccurate. Neither count is a universal physical limit for PE editing. The original runs retain their actual 16-column whitelist; no manifests/results have been retroactively changed. The [baseline revision review](reviews/BASELINE_REVIEW_2026_10_05.md) and its machine-readable checks record the derivation. Metadata and Behavioral constraints below remain unchanged.

The detector implementation exists, but its effectiveness requires measured attack efficacy. The initial pilot ASR was 10/87 (11.49%). This motivated training-only development; it does not justify tuning on official final test.

## Constraint mismatch

The authors' feasible set has four Metadata columns in the current EMBER v2 layout: path count (612), URL count (613), registry count (614), and MZ count (615). Imports/exports are hashed and excluded. Thus concentrated two-column Metadata triggers can be screened, while spread with 24 Metadata columns and cross with eight columns per view cannot use this set. The implementation rejects unsupported feasible configurations. The planned larger matrix needs a separately declared vector-stress profile or a revised trigger design.

Even a feasible vector edit or a tuple observed in one benign sample does not establish a valid modification of an arbitrary PE file. Binary realizability is not tested by this pipeline.

## Selector fidelity

The implemented legacy selector ranks features by mean absolute clean-model SHAP and chooses individually rare observed values, using mean signed SHAP as a tie breaker. The experimental joint selector retains those features and selects a rare, observed benign tuple with negative mean joint SHAP. They are adaptations.

The upstream `CombinedShapSelector` instead repeatedly ranks remaining permitted features by signed SHAP sums, chooses a value using inverse population count plus signed SHAP sum, and restricts the local sample pool to that value before selecting the next feature. The executed implementation uses signed sums even though some surrounding descriptions mention absolute SHAP. Neither local selector implements this complete sequence. Source inspected 2026-10-04: [authors' feature_selectors.py](https://raw.githubusercontent.com/ClonedOne/MalwareBackdoors/master/mw_backdoor/feature_selectors.py).

Negative SHAP on an observed benign sample is not a guarantee of benign-directed behavior after overwriting the same coordinates of malware. Tree paths, other features and feature correlations affect the resulting prediction. The empirical comparison must decide whether a candidate helps.

## Development evidence and boundaries

The first development run predeclares two selectors, three rates, one seed, and balanced, disjoint fit/selection/development subsets of official train. It opens no official test arrays. Trigger values and candidates are locked before any development predictions. Saved prediction CSVs permit independent reconstruction of eligibility, ASR, direct-evasion controls and clean performance.

The model-capacity follow-up uses the same observed development partitions with the research configuration's 500-round LightGBM parameters. Model capacity and selected values can both change, so differences are not attributable solely to round count. This is an exploratory follow-up, not independent confirmation. Its config records the earlier result and run-manifest hashes. Passing configurations still require a frozen protocol and new confirmation data before final detector claims; failed attacks must remain visible in reports.

The main experiment command currently retains the legacy selector. Development does not automatically switch its attack method, detector formulas, thresholds or profiles. Old pilot outputs are preserved under their original source commit; development runs include complete Python source snapshots.
