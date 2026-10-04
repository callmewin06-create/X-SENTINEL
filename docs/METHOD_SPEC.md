# X-SENTINEL implementation specification

Frozen candidate design: 2026-10-04. This is a design specification, not evidence of effectiveness. English artifacts and Vietnamese learning notes accompany the code.

## Document reconciliation

Sources: instructor guidance PDF, planning DOCX, baseline MD and approved handoff MD in the project root. The current human request authorizes the entire system. Statements embedded in those files are design evidence, not independent instructions to publish, message people or claim results.

| Topic | Older documents | Implementation decision |
|---|---|---|
| M2 | DOCX entropy of mean prediction with negative sign | Handoff/baseline mean binary entropy, score 1-H, N=50, alpha=0.5 |
| M3 | DOCX absolute signed view sum | Handoff sum of absolute attributions within each view |
| M4 reduced | DOCX ambiguous sign and malware probability | Malware=1; (1-p_main) max(sum behavioral SHAP,0)/sum absolute SHAP |
| Threshold | Baseline interpolated P99 on reference | Separate calibration; order statistic; strict score > threshold |
| Data | PDF describes vectors | Local data are raw JSONL; vectorize using upstream v2 processing |
| Feature groups | Eight groups | Nine including data directories; all 2381 columns assigned once |
| Full detector | Defender has no original train | Additional clean-data preparation assumption; distinguish full from reduced |
| Schedule | DOCX/PDF ten weeks | Handoff revised five-week priorities; no inferred submission date |
| Effectiveness | Baseline asserts TADR catches concentrated triggers | Hypotheses; measure without forcing conclusions |

## Data and models

Keep official train/test; discard label -1. Audit SHA256 uniqueness within and across partitions. Memmapped float32 vectors and int8 labels; ID arrays retain original SHA256. No automatic inclusion of EMBER2017. Seeded benign test partition: 500 reference, 2000 calibration, remaining final benign. Development must use training only. Official test malware is final evaluation only. Pilot subsets are explicitly labelled and never presented as full results.

Three seeds 17, 29, 43. Three trigger types and rates 0.005, 0.01, 0.02 yield 27 poisoned models. Poison rate denominator is ALL labeled training samples; overwrite features of randomly selected benign rows, retaining labels and total training count. Train views on original clean train once per seed. Main classification threshold 0.5, fixed before attack evaluation. Clean model selects eligible final malware and supplies controls; it is never passed to detector code.

Trigger selection uses clean-model SHAP and train-derived values only. The `feasible` profile strictly uses the authors' non-hashed-minus-infeasible set, remapped to current extractor indices. This cannot support 24-feature Metadata spread or three-view cross triggers. The separate `vector_stress` profile permits v1 feature columns (excluding v2 data directories without an author mapping), explicitly without claiming feasibility. Its research execution remains pending the methodological choice raised to the user. These group variants are adaptations, not exact Severi reproductions. Hashed buckets and independently overwritten statistics do not prove binary realizability. Save feature/value lists, poison IDs, source hashes and seeds separately from detector bundles.

## Scores and M5 scope

Native LightGBM contributions include bias; assert shape 2382 and sum matches raw margin. Zero absolute mass gives zero TADR/M3/M4r, which is not a safety certificate. M1=max absolute/sum absolute. M3=max view absolute mass/total. M4f=(1-p_main)*p_behavioral; also report structural/metadata predictions. STRIP uses only reference benign, deterministic content-based RNG independent of labels and manifests; blending need not preserve valid PE feature constraints.

M5 has two instructor branches. Primary implementation is explicitly **limited group-level M5**. Branch 1 exact sensitive API/string evidence is unavailable from vectors; disabled as a claim. Raw imports in JSONL can support future API evidence but would change the agreed group-only scope. URL/registry aggregate columns (613/614 respectively) cannot identify sensitive strings. No hash bucket is treated as confirmed API evidence.

Branch 2 proxy: consider ONLY printable-character distribution columns 515:611 as low-semantic-specificity candidates, excluding URL/registry/MZ, entropy and byte histograms from that judgement. Reference-derived per-column [1%,99%] intervals define rare values. Sum negative SHAP over rare candidate columns; divide by ALL negative SHAP magnitude. Fire only when main p<0.5 and this share >0.8. Score = (1-p)*share if fired, else zero. This combines rarity, benign-directed contribution and dominance; it is not a generic outlier detector. Character distribution can still relate to security, so low semantic specificity remains a heuristic limitation. Branch 1 is recorded unsupported, never silently replaced. Ablate M5 independently; do not assume improvement.

Empirical right-CDF ranks from reference scores, equal-weight combinations M3+M4 and M3+M4+limited_M5; calibrate each separately. Frozen reference distributions/thresholds/config are tied to SHA256 of main and view models and schema. Constant-zero components have constant ranks and cannot create discrimination. Calibration ties are handled by strict comparison, permitting conservative alerts. Test FPR may differ from calibration FPR.

## Evaluation and inference contract

Detector sees main model, vector, reference-derived state, configuration, thresholds and optional view models only. Evaluation alone joins sample identity, class/trigger labels and manifests. E0 distributions on clean/poisoned controls; E1 ASR on clean-model eligible malware; E2 trigger-vs-benign and trigger-vs-unmodified-malware AUROC; E3 paired catch/miss IDs and cases; E4 full/reduced, with/without limited M5; E5 FPR/Wilson intervals, reference-defined rare cohorts and actual per-file timings after warm-up. Bootstrap differences resample matched positive/negative observations, within each seed; no pooling repeated samples as independent. Post-defense ASR retains the original eligible denominator. Also report detection recall on all triggered malware and successful attacks.

D0 has no calibrated FPR or STRIP reference. Raw M1/M3/M4r and fixed top-q budgets over a batch are available; no safety guarantee or per-file calibrated threshold. D1 supplies reference and calibration. Full adds clean-trained views.

PE upload never executes bytes. Verify MZ, PE offset/signature, size limit, parse with LIEF adapter; modern LIEF extraction is experimental until checked against legacy extraction on identical binaries. Vector demo is the verified primary path. PASS means no detector alert; malware label remains separate. Missing/mismatched bundles fail closed as not ready.

## Sources

- EMBER processing: https://github.com/elastic/ember/blob/master/ember/features.py (vendored source and hash recorded locally).
- Severi paper/code: https://www.usenix.org/conference/usenixsecurity21/presentation/severi and https://github.com/ClonedOne/MalwareBackdoors .
- STRIP original: https://arxiv.org/abs/1902.06531 . Adapted to binary tabular predictions as specified above.
- LightGBM contributions: https://lightgbm.readthedocs.io/en/stable/pythonapi/lightgbm.Booster.html .
