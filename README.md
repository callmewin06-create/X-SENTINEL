# X-SENTINEL

X-SENTINEL studies per-input backdoor suspicion in static PE malware classifiers on **EMBER2018/V2** and **EMBER2024/V3**. It combines LightGBM predictions and TreeSHAP feature-view signals, with a Vietnamese Streamlit dashboard, a FastAPI service and PostgreSQL analysis history. Malware classification and backdoor suspicion are separate outputs; an absence of suspicion does not certify that a file or model is safe.

## Current status — 28 October 2026

The original primary benchmark contains **54 frozen configurations** (27 per dataset), with **108 calibrated Reduced/Full bundles**. Primary models, triggers and calibration thresholds are preserved. M5 is not assessed in this primary benchmark.

The 27 October revision adds signed-SHAP Isolation Forest comparisons, retrospective low-FPR metrics, paired Cross diagnostics, bounded **multiview** adaptation, five clean-fit budgets and a two-configuration training-filtering experiment. Two additional EMBER2024 seeds, **59 and 71**, give five attempts in the spread-2% condition; four are confirmed and the unsuccessful attempt is retained. These additions expose limitations rather than establish resistance to distributed or adaptive backdoors. Final evaluation pools had already been observed before the supplemental analyses.

Start with the [current status and evidence boundaries](docs/STATUS_2026_10_28.md). The [27 October research handoff](docs/REVIEW_REPAIR_2026_10_27.md) records that revision; its then-pending Word/binary integration was completed as described in the current status. The [13 October revision](docs/REVISION_2026_10_13.md) and older implementation records are historical snapshots.

The [28 October web-demo synchronization](docs/WEB_DEMO_SYNC_2026_10_28.md) updates the Research page, VMC/BGS/BPG explanations and PDF wording without changing model decisions. Its dated research snapshot is packaged with the app. The handoff also records an outstanding schema-description correction in the manuscript and the local/Docker verification boundary.

## Run the dashboard

Run commands from the repository root. Scoring an existing calibrated bundle does not require the original datasets or retraining. This checkout already tracks frozen primary artifacts under `outputs/primary/`; preserve the matching model files, reference arrays, schema metadata and thresholds together. `.gitignore` does not remove files that are already tracked.

### Docker with API and history

Docker Desktop must be running. Create `.env` only if it does not already exist:

```powershell
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
```

Set your own `POSTGRES_PASSWORD` in `.env` using `.env.example` as the guide, then start the stack:

```powershell
docker compose up -d --build
docker compose ps -a
```

Open <http://127.0.0.1:8501>. Compose starts PostgreSQL, a schema migration, the backend and the dashboard. Application ports bind to localhost, and primary artifacts are mounted read-only. Retain the `primary_history` volume when updating; `docker compose down -v` deletes that stored history. To stop while retaining it:

```powershell
docker compose down
```

For build diagnostics, use `docker compose --progress plain build dashboard`, followed by `docker compose up -d --no-build`. The Dockerfile installs dependencies before application source so unchanged dependencies can reuse the builder cache. First builds or changed dependencies may still require downloads; Linux transitive dependencies are not fully locked.

See the [database/API guide](docs/database/INTEGRATION_2026_10_07.md), [recorded dashboard/Docker checks](docs/DASHBOARD_DOCKER_CHECK_2026_10_07.md), and [Docker cache/header handoff](docs/DOCKER_CACHE_HEADER_2026_10_21.md). These are dated verification records, not a claim that the stack is running or healthy now. User/role tables exist, but authentication is not implemented.

### Local Python dashboard

Use **Python 3.11–3.12**. On a new machine:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install '.[service,binary-v3]' pytest==8.3.5
.venv/Scripts/python.exe -m streamlit run dashboard/app.py
```

The `binary-v3` extra supplies the additional PE V3 extraction dependencies; `service` supplies the API/database dependencies. The standalone local dashboard remains available without database history. Optional plotting dependencies are installed with `.venv/Scripts/python.exe -m pip install '.[plots]'`. Direct dependencies are pinned in [pyproject.toml](pyproject.toml); `requirements-lock.txt` records a validated Windows environment.

The dashboard has Analysis, History and Research views. It accepts PE files (`.exe`, `.dll`, `.sys`) up to **50 MiB**, a compatible single feature vector, or a matching raw EMBER JSON object. Expected vector lengths are **2,381 for V2** and **2,568 for V3**. V2/V3 extraction has fixture checks, but parity with the original dataset binaries is not established. Uploaded PE files are parsed, not executed. Extraction runs in a disposable worker; process separation is not a complete security sandbox.

The dashboard prepares vectors for the backend. The current API analysis route is `POST /v1/analyze/vector`; it is not a direct binary-upload endpoint. Explanations and Vietnamese PDF exports reuse the scoring result. See the [UI revision handoff](docs/UI_REVISION_2026_10_16.md) for the dated UI/history checks.

## Method and limitations

| Setting | Score used by the primary method | Resources / access |
|---|---|---|
| Reduced | Mean reference rank of VMC and BGS | Suspicious main model, 500 benign reference records and 2,000 benign calibration records |
| Full | Mean reference rank of VMC and BPG, using the clean Behavioral probability gap | Clean auxiliary models; the original primary fit used 200,000 labelled benign/malware records, separately from reference/calibration |

The **Full formula uses the Behavioral auxiliary prediction**. The current portable Full bundle additionally retains Structural and Metadata view models, and its loader requires all three view-model files. Selected Full inference evaluates only the Behavioral auxiliary model. Loading an existing bundle does not require access to its original clean fit data.

Calibration uses strict `score > threshold` and bounds the observed calibration false-positive rate, not every future FPR. Retrospective final-set FPR-cap/pAUC comparisons are ranking analyses; they do not replace deployment calibration. Full does not have a universal advantage over a clean full-feature Shadow classifier, and resource access must be stated when comparing them.

All benchmark poisoning and adaptive attacks operate in **feature space**. Cross-view triggers and multiview adaptation defeat the concentration assumption in important cases. Phúc's [benign PE audit package](phuc_pe_trigger_2026_10_27.zip) adds exported feature/log evidence, with Windows functionality failures retained; it does not demonstrate complete functioning benchmark triggers in malware or detector recall against such binaries. The corrected counts and missing source/executable evidence are documented in the [current status](docs/STATUS_2026_10_28.md).

## Research and reproduction

The [primary run guide](docs/PRIMARY_RUN_GUIDE_2026_10_07.md), [approved protocol](configs/primary_protocol.json) and [execution configuration](configs/primary_execution.json) describe the dual-dataset workflow. Inspect command help before starting a fresh run:

```powershell
.venv/Scripts/python.exe scripts/xsentinel.py prepare-v3 --help
.venv/Scripts/python.exe scripts/xsentinel.py split-primary --help
.venv/Scripts/python.exe scripts/xsentinel.py develop-primary --help
.venv/Scripts/python.exe scripts/xsentinel.py lock-selector --help
.venv/Scripts/python.exe scripts/xsentinel.py confirm-primary --help
.venv/Scripts/python.exe scripts/xsentinel.py run-primary --help
.venv/Scripts/python.exe scripts/xsentinel.py report-primary --help
```

Use new output directories for new experiments. Resume is valid only when configuration, source, data/split checksums and checkpoints match. Do not tune methods on the final test or overwrite the frozen primary artifacts. Raw research datasets and supplemental experiment outputs must be supplied separately when reproducing them.

The older `prepare`, `split`, `run`, `report` and `develop-attack` commands belong to the **archived EMBER2018 workflow**; they do not launch the primary dual-dataset matrix. D0 is also an archived V2/2,381-feature, fixed top-q batch-budget interface, without calibrated FPR. See the [method specification](docs/METHOD_SPEC.md), [walkthrough](docs/HUONG_DAN_TUNG_BUOC.md), [attack audit](docs/ATTACK_AUDIT.md) and [historical development results](docs/results/ATTACK_DEVELOPMENT_SUMMARY.md) for that context. The root `README_HUONG_DAN_SU_DUNG.md` describes the earlier baseline handover, not the current primary method.

## Manuscript and sharing

The latest merged English manuscript prepared in this workspace is a **14-page, one-column** file with appendices and references:

```text
output/ieee_merged_2026_10_28/X_SENTINEL_Merged_ReferenceStyle_Fixed.docx
```

That DOCX is a **local generated file ignored by Git**; share it separately when submitting. It preserves the corrected results, includes the binary audit and disables automatic field updating on open. Its layout follows the supplied Word reference; this is not a blanket certification of camera-ready compliance for an unspecified IEEE venue.

The current checkout tracks primary bundle artifacts and Phúc's audit ZIP. Ignore rules cover new files under `output/`, `outputs/`, `data/` and `models/`, along with `.venv/`, `.env` and matching binary/document file patterns; already tracked files remain tracked. See [.gitignore](.gitignore) for the exact rules. Do not assume a local generated report is available through a repository link. Retain upstream copyright/license notices in [docs/upstream](docs/upstream).

[Model sharing instructions](docs/HUONG_DAN_CHIA_SE_DRIVE.md) describe the older baseline ZIP. `scripts/download_models.py` supports declared public HTTPS manifests with size/SHA256 verification; private Drive authentication and actual sharing URLs must be configured separately. All files of a calibrated bundle must stay matched. See the [document index](docs/INDEX.md) for dated supporting records.
