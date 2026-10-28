# Evidence Index: Reproducibility & Provenance Map

**Author**: Pham Nguyen Hoang Phuc (PhucPNHSE203815)  
**Date**: 27 October 2026  
**Repository**: `callmewin06-create/X-SENTINEL`  
**Git Branch**: `phuc/pe-trigger-validation-2026-10-27`  
**Git Commit SHA**: `eb153366f8e0787759671ff34893550480902d66`

---

## 1. Traceability Matrix: Research Claims to Concrete Evidence

| # | Scientific / Technical Claim | Evidence Category | Exact File Pointer & Location | Verifying Command / Test | Evidence Hash / Artifact Details |
|---|---|---|---|---|---|
| **E1** | Severi et al. public repo does NOT contain PE binary modification code | `code_audit` | `/tmp/MalwareBackdoors/mw_backdoor/attack_utils.py` lines 208–212 | `grep -rn "def watermark_one_sample" /tmp/MalwareBackdoors/` | Commit `7e3ba27fdc1db25d68ae74da334cf3bdd9eedf71`; code shows direct vector overwrite for Ember (`x[idx] = val`) |
| **E2** | Severi feasible feature set is based on EMBER-2017 (2351 dims) with 17 non-hashed features | `code_audit` | `/tmp/MalwareBackdoors/mw_backdoor/constants.py` lines 98–117 & `data_utils.py` lines 50–75 | `python3 -c "import mw_backdoor.constants ..."` | 35 non-hashed minus 18 infeasible = 17 features (including 4 string metadata features) |
| **E3** | X-SENTINEL restricted Structural pool contains exactly 13 pure Structural columns | `code_audit` | `src/xsentinel/schema.py` lines 18–20 & 148–150 | `python -c "from xsentinel.schema import get_schema ..."` | Schema `V2_PRIMARY` has 13 structural restricted indices; `V3_PRIMARY` has 13 structural restricted indices |
| **E4** | Native C benign fixture is self-contained, deterministic, and safe ($n^2+7$) | `source_code` | `experiments/phuc_pe_validation/fixtures/src/native_benign_fixture.c` | `x86_64-w64-mingw32-gcc -O2 -s ...` | SHA256 (`native_benign_fixture.exe`): `d8f8741fa1b0a0c7364137501e93b6161a50a78d5e32fc5a28b9d1ca749954f5` |
| **E5** | Managed .NET C# benign fixture is self-contained and deterministic ($n^2+7$) | `source_code` | `experiments/phuc_pe_validation/fixtures/src/dotnet_benign_fixture.cs` | Pre-built reviewed fixture verified | SHA256 (`dotnet_benign_fixture.exe`): `72524cf3d72fe935d482300d4b9d7414dbea7ab9786b76723f3a7132331e4485` |
| **E6** | All 10 binary variants generated deterministically with manifest tracking | `manifest` | `outputs/phuc_pe_trigger_2026_10_27/manifest.csv` | `python experiments/phuc_pe_validation/scripts/build_variants.py` | 10 variants (5 native, 5 dotnet) with explicit file sizes, byte offsets, and SHA-256 hashes |
| **E7** | Native variants pass 4 functional test cases (20/20 on Wine, 20/20 on Windows) | `test_execution` | `outputs/phuc_pe_trigger_2026_10_27/functionality_results.csv` | `python experiments/phuc_pe_validation/scripts/test_functionality.py` | Exit codes 0, 0, 0, 2 match expected values; stdout `X_SENTINEL_BENIGN_FIXTURE:7`, `32`, `16` match |
| **E8** | Windows AppLocker/WDAC blocks .NET variants with historic timestamps | `test_execution` | `outputs/phuc_pe_trigger_2026_10_27/functionality_results.csv` | `python experiments/phuc_pe_validation/scripts/test_functionality.py` | `WinError 4551: An Application Control policy has blocked this file` recorded for targets 2018/2024 |
| **E9** | Patching COFF timestamp modifies target coordinate but induces 11–16 unintended Metadata shifts | `vector_diff` | `outputs/phuc_pe_trigger_2026_10_27/feature_changes.csv` & `feature_change_summary.csv` | `python experiments/phuc_pe_validation/scripts/extract_and_diff.py` | 1 intended matched coordinate (`header.coff.timestamp`); 11–16 unintended shifts in ByteHistogram/Entropy |
| **E10** | Appending overlay padding induces 232–353 unintended shifts across Metadata & Structural views | `vector_diff` | `outputs/phuc_pe_trigger_2026_10_27/feature_change_summary.csv` | `python experiments/phuc_pe_validation/scripts/extract_and_diff.py` | `overlay_size`, `overlay_entropy`, byte frequency distributions shifted massively |
| **E11** | Scoring 10 variants on 24 frozen primary bundles yields 0 / 240 backdoor alerts | `model_scoring` | `outputs/phuc_pe_trigger_2026_10_27/xsentinel_scores.csv` | `python experiments/phuc_pe_validation/scripts/score_variants.py` | Seeds 17, 29, 43; rates 0.02; Reduced & Full modes; $X_R \le \tau_{XR}$ and $X_F \le \tau_{XF}$ across all rows |
| **E12** | EMBER2018 models predict all variants as BENIGN ($p_{\text{main}} \le 0.052$) | `model_scoring` | `outputs/phuc_pe_trigger_2026_10_27/xsentinel_scores.csv` | `python experiments/phuc_pe_validation/scripts/score_variants.py` | Native mean $p_{\text{main}} \approx 0.006$–$0.012$; .NET mean $p_{\text{main}} \approx 0.019$–$0.052$ |
| **E13** | EMBER2024 models exhibit classifier false-positives on small fixtures ($p_{\text{main}} > 0.5$) | `model_scoring` | `outputs/phuc_pe_trigger_2026_10_27/xsentinel_scores.csv` | `python experiments/phuc_pe_validation/scripts/score_variants.py` | Consistent with report Table XVIII and Figure 6; strictly separated from backdoor trigger alert |

---

## 2. Command Replay Log for Independent Verification

```bash
# 1. Inspect environment
python3 -c "import json; print(json.load(open('outputs/phuc_pe_trigger_2026_10_27/environment.json')))"

# 2. Build native fixture from source
x86_64-w64-mingw32-gcc -O2 -s -Wl,--build-id=none \
    experiments/phuc_pe_validation/fixtures/src/native_benign_fixture.c \
    -o experiments/phuc_pe_validation/fixtures/native_benign_fixture.exe

# 3. Generate all variants deterministically
python experiments/phuc_pe_validation/scripts/build_variants.py

# 4. Run automated functional tests
python experiments/phuc_pe_validation/scripts/test_functionality.py

# 5. Extract full V2 and V3 vectors and diff all dimensions
python experiments/phuc_pe_validation/scripts/extract_and_diff.py

# 6. Score all variants against frozen research bundles
python experiments/phuc_pe_validation/scripts/score_variants.py

# 7. Run regression test suite
pytest experiments/phuc_pe_validation/tests/test_pe_validation.py -v
```
