# X-SENTINEL

The primary dual-dataset implementation started on 2026-10-06. Read the [current implementation record (Vietnamese)](docs/PRIMARY_IMPLEMENTATION_2026_10_06.md) and [approved protocol](configs/primary_protocol.json) for the new M3/M4 formulas, data roles and remaining work. The experiment commands below retain the archived V2 workflow; they do not run the new primary matrix.

Raw EMBER2018 files now live in `data/ember2018`; prepared arrays remain in `data/ember2018_full`. The move is recorded in `data/ember2018_relocation.json`. Historical source manifests retain the paths recorded when data were prepared.

Reports, progress records, plans and research source documents are collected under `docs/`. See the [document index](docs/INDEX.md) for their current locations.

Complete feature-space research pipeline for per-input backdoor suspicion on EMBER2018: streaming data preparation, clean-label attacks, clean/poisoned LightGBM models, TADR, STRIP, reduced/full cross-view detection, limited M5, threshold locking, E0–E5 evaluation, a Streamlit demo and CPU Docker packaging.

Read [method specification](docs/METHOD_SPEC.md) and [Vietnamese walkthrough](docs/HUONG_DAN_TUNG_BUOC.md) first. Current completion evidence is recorded in [implementation status](docs/IMPLEMENTATION_STATUS.md). Hypotheses are not asserted as findings.

## Local setup

Python 3.11–3.12. The existing `.venv` is usable. Commands below run from the repository root in PowerShell. New-machine setup:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install . pytest==8.3.5
.venv/Scripts/python.exe -m pytest -q
```

Direct dependencies are pinned in pyproject.toml. `requirements-lock.txt` captures the validated Windows environment; Linux dependency resolution and Docker build must be verified separately.

## Pilot

```powershell
.venv/Scripts/python.exe scripts/xsentinel.py prepare --raw data/ember2018 --out data/pilot --limit 2000
.venv/Scripts/python.exe scripts/xsentinel.py split --data data/pilot --reference 100 --calibration 400
.venv/Scripts/python.exe scripts/xsentinel.py run --data data/pilot --out outputs/pilot --config configs/pilot.json
.venv/Scripts/python.exe scripts/xsentinel.py report --run outputs/pilot
.venv/Scripts/python.exe -m streamlit run dashboard/app.py
```

`--limit` takes the first records of EACH source file for fast integration validation. It is a biased pilot sampling rule, not a representative research dataset. Fresh output directories are required to prevent accidental overwriting of locked experiments.

An interrupted run can continue with `--resume` if configuration, data/splits, source-code checksums and model checkpoints still match. Source changes require a new run directory. Plot real results with `pip install '.[plots]'` then `python scripts/plot_results.py --run outputs/pilot`.

## Train-only attack development

Before launching the large matrix, screen attack viability on disjoint subsets of official **train**:

```powershell
.venv/Scripts/python.exe scripts/xsentinel.py develop-attack --data data/ember2018_full --out outputs/attack_development_v1 --config configs/attack_development.json
```

This command opens only training arrays. It freezes balanced fit/selection/development partitions (40000/5000/10000), two concentrated feasible selectors and three poison rates before development predictions. The existing rare-value selector is compared with an experimental observed-benign-tuple selector using negative joint SHAP. Both use the same feature pair. It saves source snapshots, IDs, trigger/model checksums, per-sample predictions, ASR intervals, clean-trigger controls, clean performance and an English report. A predeclared screening rule is a development heuristic, not a research result or proof of binary realizability. New runs require fresh output directories; this command does not implement resume. Do not tune attacks on official final test.

Both completed screens retain negative findings: no candidate passed, and the joint selector did not improve ASR. Read the [comparison and next research steps](docs/results/ATTACK_DEVELOPMENT_SUMMARY.md), [first screen report](docs/results/attack_development_v1/report.md) and [capacity follow-up](docs/results/attack_development_500rounds_v2/report.md). The 500-round config uses research model capacity on the same subsets (`configs/attack_development_500rounds.json`); it explicitly reuses observed development data and is exploratory. The [selector audit](docs/ATTACK_AUDIT.md) distinguishes local adaptations from the authors' source algorithm.

## Official research data and matrix

```powershell
.venv/Scripts/python.exe scripts/xsentinel.py prepare --raw data/ember2018 --out data/ember2018_full
.venv/Scripts/python.exe scripts/xsentinel.py split --data data/ember2018_full --reference 500 --calibration 2000
.venv/Scripts/python.exe scripts/xsentinel.py run --data data/ember2018_full --out outputs/research --config configs/research.json --allow-vector-stress
.venv/Scripts/python.exe scripts/xsentinel.py report --run outputs/research
```

The research matrix has 3 seeds × 3 trigger types × 3 rates = 27 poisoned models, plus clean and view models. It is explicitly a **vector stress-test**. The authors' feasible set cannot produce 24-feature Metadata spread or Behavioral-view modifications. `feasible` never silently expands its allowed set; unsupported configurations raise errors. Neither profile proves the selected vector modifications can be realized in PE files. Read the documented methodological decision before launching. Full official evaluation and training may take many hours; 4 CPU threads and sequential models are the default. Ensure adequate free disk/RAM and benchmark the pilot first.

The detector is blind: clean models, poisoning manifests, labels and trigger identities remain in attack/evaluation modules. Main-model hashes, reference data and per-variant thresholds live in portable detector bundles. Calibration FPR ≤1% is empirical; final FPR can differ. No claims of speedups, detection success or latency <10 ms are made without measured evidence.

## D0 and scoring

```powershell
.venv/Scripts/python.exe scripts/xsentinel.py score --bundle outputs/pilot/seed_17/concentrated_0.01/bundle --vector data/demo_vector.npy
.venv/Scripts/python.exe scripts/xsentinel.py d0 --model models/main.txt --vectors data/demo_batch.npy --q 0.01
```

D0 reports raw TADR/M3/M4r and a fixed top-q batch budget; it has no calibrated FPR and no STRIP reference. D1 uses separate reference/calibration. Full requires three pre-trained clean view models, an additional preparation assumption.

## Dashboard and Docker

The English dashboard supports a finite 2381-column `.npy`, a raw EMBER JSON record, or a PE upload up to 20 MiB. Vector processing is the primary verified path. Modern LIEF extraction is experimental, visibly marked, and never executes or retains uploaded binaries. PASS means no threshold alert; malware probability/label is shown separately. Missing or corrupted model/calibration bundles produce Not ready.

```powershell
docker compose up --build
```

Mount only demo bundles for colleagues who do not need research models. CPU/RAM limits are set in compose.yaml. Docker availability/build validation is recorded in status documentation. The user published the initial implementation to [GitHub](https://github.com/callmewin06-create/X-SENTINEL) at commit `5e96806`; later local changes need a new commit/push. Google Drive model sharing is not configured.

## Sharing

For the prepared legacy EMBER2018 demo ZIP and step-by-step Google Drive upload/download instructions, read the [Vietnamese sharing guide](docs/HUONG_DAN_CHIA_SE_DRIVE.md). The ZIP includes matching local runtime source, baseline models and the complete calibrated demo bundle; uploading to Drive is done separately.

`scripts/download_models.py` implements public HTTPS manifest downloads with version/profile, declared size, SHA256, temporary files and verified cache reuse. Populate `configs/model_download_manifest.example.json` only after actual sharing URLs exist. Private Drive authentication requires an authorized connector; this tool does not bypass it. Distribute all files in a detector bundle together; the thresholds are bound to those exact model bytes.

## Artifacts

Every experiment records configuration/data/split checksums, trigger values, poison IDs, models, threshold lock, per-input scores, distributions, ASR, clean performance, AUROC and rate intervals, paired catch/miss cases, M5/full ablations, rare-benign proxies and warmed-up per-file latency. Score CSV latency is blank for batch scoring; separately measured per-file latencies are in latency.json. Seeds are retained separately. Research report and slide outline are generated from real evaluations, including negative findings.

Dataset directories, binaries, model files, generated outputs, credentials and the virtual environment are excluded from Git/Docker contexts. Upstream EMBER and Severi files keep original copyright and license notices; see docs/upstream. No malware binary modification or execution is part of the research pipeline.
