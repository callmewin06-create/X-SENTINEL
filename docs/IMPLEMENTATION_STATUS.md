# Implementation and validation status

Recorded 2026-10-04, Asia/Bangkok. This file distinguishes implementation from completed research evidence.

Review update, 2026-10-05: the newly submitted baseline is reviewed in docs/reviews/BASELINE_REVIEW_2026_10_05.md. Its proposed feasible membership conflicts with the vendored source. Recomputing the source filter also identified our own omission: derived set has 17 columns (13 Structural + 4 Metadata), while current code/runs use a valid 16-column subset lacking 684. The earlier assertion that 16 was the complete author whitelist was incorrect. No detector/attack source, whitelist, locked run or trigger profile was changed as part of this review; no new model run was launched. Review checks and the submitted document snapshot are preserved alongside the review.

## Implemented

- Source-document reconciliation and fixed candidate method specification; Vietnamese step-by-step teaching notes.
- EMBER v2 raw/batch processing matching upstream on 32 real records, with a documented sklearn compatibility adapter for historical entry-name character hashing.
- Disk-backed duplicate audit, finite vector validation, labeled-only memory maps, seeded disjoint ID splits and checksums.
- Sequential clean/main/view-model training, model checkpoints, train-only SHAP-informed triggers, clean-label benign poisoning and separate attack manifests.
- Separate training-only attack development CLI, balanced disjoint fit/selection/development partitions, frozen candidate comparison, clean-trigger evasion controls, source snapshots and per-sample predictions.
- Feasible and explicitly distinct vector-stress profiles. Feasible rejects unsupported spread/cross rather than silently relaxing constraints.
- TADR baseline blind interface; tabular STRIP N=50 alpha=0.5; M3, M4 reduced/full; limited group-level M5 with sensitive branch explicitly unsupported.
- Reference empirical ranks, equal-weight combinations, separate per-variant calibration with strict threshold comparison, schema/model-bound portable bundles.
- E0–E5 artifacts: clean-model controls, ASR and clean performance, trigger/benign and trigger/malware AUROC, bootstrap/Wilson uncertainty, catch/miss tables, explanations, reduced/full/M5 comparisons, rare-benign proxies and actual warmed-up per-file component timings.
- D0 raw scores and fixed top-q batch budgets, separate from D1 calibrated detection.
- English Streamlit dashboard with example/vector/raw JSON/experimental PE paths, upload limits, separate labels/alerts, no binary execution and Not ready on bundle failures.
- CPU Dockerfile, Compose mounts and limits, CI, direct dependency pins, Windows transitive environment lock, public model-manifest downloader.
- English report/results and an editable eight-slide pilot presentation.
- Static E0/E1/E2/E4/E5 figures generated from actual pilot artifacts with Matplotlib; E3 is represented by paired ID tables and case explanations.

## Verified local evidence

Full data preparation completed: 600,000 labeled training rows (300,000 each class), 200,000 test rows (100,000 each class), 200,000 unlabeled training rows excluded. No duplicate SHA256 within or across original partitions. Total preparation elapsed 236.47 seconds. Shapes: train (600000,2381), test (200000,2381), float32.

Official splits frozen: reference 500, calibration 2000, final benign 97500, final malware 100000. IDs and checksums are in data/ember2018_full/splits.json. Full data are prepared; full model matrix is not yet evaluated.

Pilot: first 2000 records from each train shard and test file, yielding 9337 labeled train and 2000 test. Reference/calibration/final benign/malware sizes: 100/400/502/998. One seed (17), concentrated feasible trigger, 1% poisoning, 80-round main models and 50-round view models. Evaluation uses a deterministic 100 benign/100 malware subset. This sampling rule is deliberately labeled pilot and is not representative final research sampling.

Pilot ASR: 10/87 clean-model eligible malware = 11.49%, Wilson 95% interval 6.36%–19.88%. This weak attack does not establish detector efficacy against a strong backdoor. Pilot end-to-end detection median approximately 1.38 ms, P95 1.79 ms across only ten warmed-up observations on the small model. These timings do not predict official 500-round model latency and exclude extraction.

Seventeen tests passed locally, including upstream vector agreement, SHAP additivity, deterministic STRIP, threshold ties, bundle round-trip and corruption, preserved poison labels, unsupported feasible cross, paired metrics, invalid PE, duplicate audit/disjoint splits and dashboard valid/missing bundles. Four additional development checks cover disjoint balanced partitions, observed benign tuples with negative SHAP, fixed eligibility/direct-evasion controls and an end-to-end run with no test files present. Native PE parser produced a finite 2381-column vector from the existing Python GUI launcher without executing it. Modern-versus-legacy extraction equivalence remains unverified.

Checkpoint/resume was exercised on the pilot. Current locks additionally include source-code checksums; only runs created after that change can resume under this stronger contract. Source changes require a new run rather than silently mixing methods.

The preserved pilot is outputs/reproducible_pilot, with report.md, results.csv, figures and complete evaluation/bundle artifacts. Resume was verified against its original source, published by the user at Git commit 5e96806. Subsequent development source changes invalidate its resume lock; do not overwrite it or assert the new source generated those results. Older pilot directories are intermediate development runs. The eight-slide deliverable is outputs/pilot_verified/X_SENTINEL_Pilot_v3.pptx; its numerical results agree with the preserved pilot. Wheel build/install was verified in tmp/package_verified for that earlier source, including vectorization and loading a ten-method detector bundle from the installed package. NumPy remains 1.26.4; plotting dependencies are pinned for compatibility.

Dashboard running locally at http://localhost:8501. No file deletion or operating-system quarantine is performed. The PowerPoint deck passes package/layout/chart/font validation and each slide was visually inspected. Native PowerPoint opening is not verified.

Training-only attack development v1 completed on balanced, disjoint 40000 fit / 5000 selection / 10000 development subsets of the full official train. One clean model and six poisoned models, seed 17, 100 rounds. Fixed clean eligibility: 4725/5000 malware. Legacy-selector ASR at 0.5%/1%/2% poisoning: 4.68%/8.78%/41.16%; same-trigger clean-model ASR 0.25%. Observed-benign-joint-selector ASR: 2.52%/4.02%/10.31%; its clean-trigger control 0.78%. Clean accuracy baseline 94.53%, poisoned clean accuracy 94.46%–94.71%. None passed the predeclared development screen; the proposed joint selector did not improve this screen. Six-model plus clean training/evaluation elapsed 53.00 seconds after checksums/partition preparation, whole-process peak working set 2142.19 MiB (2.09 GiB), peak pagefile 2355.92 MiB. These resource figures concern the small training subset, not full research runs.

Artifacts: outputs/attack_development_v1. Aggregate report/CSV and an artifact audit are copied to docs/results/attack_development_v1 for version control. Audit reproduced every screening metric from saved per-sample predictions and checked disjoint IDs, poison membership/count, source snapshot, model and candidate-lock checksums. Official test arrays were not opened. A predeclared 500-round capacity follow-up is configured in configs/attack_development_500rounds.json; it reuses the observed development partition and is exploratory, not independent confirmation.

The 500-round follow-up also completed: legacy ASR 6.62%/11.24%/37.09%, joint-selector ASR 1.89%/2.85%/9.22%; clean-trigger controls 0.12% and 0.75% respectively. Clean accuracy baseline 96.34%, poisoned clean accuracy 96.17%–96.40%, 4804 eligible malware. No screen passes. Elapsed training/evaluation 381.46 seconds, peak working set 2147.90 MiB (2.10 GiB). Its artifacts and source snapshot are in outputs/attack_development_500rounds_v2; a later report-only change explicitly adds the recorded development reuse history and preserves the original results CSV checksum. All six models passed the same artifact audit. Public aggregate evidence from both runs is in docs/results/ATTACK_DEVELOPMENT_SUMMARY.md. Total new development models: two clean and twelve poisoned; these are not the official 27-model matrix. The highest ASR remains 41.16%, below the declared screening target, with measurable poisoning-associated evasion relative to its clean-trigger control.

The no-test-access statement applies to these development commands. Earlier pilot experiments evaluated a small official-test-derived subset; disclose that exposure in the final research protocol instead of claiming the project's entire official test has never been accessed. Models and numerical outcomes remain tied to archived source snapshots. Current source includes a subsequent empty-eligibility logging fix and development-history reporting enhancement, validated by the four development tests.

## Remaining research and environment work

1. Resolve the asked methodological choice: authors' feasible profile alone versus feasible plus a separate 27-configuration vector stress-test. No full stress matrix has been launched pending that choice.
2. Establish attack viability and independently confirm any selected method before interpreting official detector results. Both training-derived screens completed with no passing configurations; rare-value/SHAP selectors remain adaptations, not exact reproduction of Severi's combined greedy selector. Source fidelity audit is in docs/ATTACK_AUDIT.md.
3. Train/evaluate the 27-model official matrix after the profile decision and measured resource budget. Configuration and orchestration exist; no results are invented.
4. Validate experimental PE extraction against legacy LIEF on identical binaries if production-equivalent PE scoring is required.
5. Build and test Docker on a machine with Docker available. This machine has no docker executable; no successful image-build claim is made.
6. The user published the initial implementation to https://github.com/callmewin06-create/X-SENTINEL at commit 5e96806. Later local development changes have not been pushed. Shared Drive URLs/access are still missing; no model upload is claimed.

Report/slide outputs concern the pilot. Final research report and deck require the official matrix and attack viability evidence.
