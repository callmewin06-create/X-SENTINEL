# Implementation and validation status

Recorded 2026-10-04, Asia/Bangkok. This file distinguishes implementation from completed research evidence.

## Implemented

- Source-document reconciliation and fixed candidate method specification; Vietnamese step-by-step teaching notes.
- EMBER v2 raw/batch processing matching upstream on 32 real records, with a documented sklearn compatibility adapter for historical entry-name character hashing.
- Disk-backed duplicate audit, finite vector validation, labeled-only memory maps, seeded disjoint ID splits and checksums.
- Sequential clean/main/view-model training, model checkpoints, train-only SHAP-informed triggers, clean-label benign poisoning and separate attack manifests.
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

Thirteen tests passed locally, including upstream vector agreement, SHAP additivity, deterministic STRIP, threshold ties, bundle round-trip and corruption, preserved poison labels, unsupported feasible cross, paired metrics, invalid PE, duplicate audit/disjoint splits and dashboard valid/missing bundles. Native PE parser produced a finite 2381-column vector from the existing Python GUI launcher without executing it. Modern-versus-legacy extraction equivalence remains unverified.

Checkpoint/resume was exercised on the pilot. Current locks additionally include source-code checksums; only runs created after that change can resume under this stronger contract. Source changes require a new run rather than silently mixing methods.

The final source-matched run is outputs/reproducible_pilot, with report.md, results.csv, figures and complete evaluation/bundle artifacts. Resume was verified there after the last source changes. Older pilot directories are intermediate development runs. The eight-slide deliverable is outputs/pilot_verified/X_SENTINEL_Pilot_v3.pptx; its numerical results agree with the reproducible pilot. Wheel build/install was verified in tmp/package_verified, including vectorization and loading a ten-method detector bundle from the installed package. NumPy remains 1.26.4; plotting dependencies are pinned for compatibility.

Dashboard running locally at http://localhost:8501. No file deletion or operating-system quarantine is performed. The PowerPoint deck passes package/layout/chart/font validation and each slide was visually inspected. Native PowerPoint opening is not verified.

## Remaining research and environment work

1. Resolve the asked methodological choice: authors' feasible profile alone versus feasible plus a separate 27-configuration vector stress-test. No full stress matrix has been launched pending that choice.
2. Establish attack viability on training-derived development data before interpreting official detector results. Current rare-value/SHAP group selector is an adaptation, not an exact reproduction of Severi's combined greedy selector.
3. Train/evaluate the 27-model official matrix after the profile decision and measured resource budget. Configuration and orchestration exist; no results are invented.
4. Validate experimental PE extraction against legacy LIEF on identical binaries if production-equivalent PE scoring is required.
5. Build and test Docker on a machine with Docker available. This machine has no docker executable; no successful image-build claim is made.
6. GitHub remote and shared Drive URLs/access are missing. Local code is ready for version control, but no repository has been published and no model uploaded.

Report/slide outputs concern the pilot. Final research report and deck require the official matrix and attack viability evidence.
