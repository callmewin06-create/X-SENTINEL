import csv
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
EXP_DIR = ROOT / "experiments/phuc_pe_validation"
OUT_DIR = ROOT / "outputs/phuc_pe_trigger_2026_10_27"

def test_manifest_integrity():
    manifest_path = OUT_DIR / "manifest.csv"
    assert manifest_path.exists(), "manifest.csv must exist"
    with open(manifest_path, "r", encoding="utf8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 10, "Expected exactly 10 binary variants in manifest"
    for r in rows:
        fpath = ROOT / r["file_path"]
        assert fpath.exists(), f"Binary file missing: {fpath}"
        data = fpath.read_bytes()
        assert len(data) == int(r["file_size"]), f"File size mismatch for {r['variant_id']}"
        assert hashlib.sha256(data).hexdigest() == r["sha256"], f"SHA256 mismatch for {r['variant_id']}"

def test_vector_dimensions_and_finite():
    vec_dir = OUT_DIR / "vectors"
    assert vec_dir.exists(), "vectors directory must exist"
    manifest_path = OUT_DIR / "manifest.csv"
    with open(manifest_path, "r", encoding="utf8") as f:
        variants = list(csv.DictReader(f))
    for v in variants:
        vid = v["variant_id"]
        v2_path = vec_dir / f"{vid}_v2.npy"
        v3_path = vec_dir / f"{vid}_v3.npy"
        assert v2_path.exists(), f"V2 vector missing for {vid}"
        assert v3_path.exists(), f"V3 vector missing for {vid}"
        vec2 = np.load(v2_path)
        vec3 = np.load(v3_path)
        assert vec2.shape == (2381,), f"V2 shape must be (2381,) for {vid}"
        assert vec3.shape == (2568,), f"V3 shape must be (2568,) for {vid}"
        assert np.isfinite(vec2).all(), f"V2 vector contains non-finite values for {vid}"
        assert np.isfinite(vec3).all(), f"V3 vector contains non-finite values for {vid}"

def test_feature_diff_drift_proven():
    summary_path = OUT_DIR / "feature_change_summary.csv"
    assert summary_path.exists(), "feature_change_summary.csv must exist"
    with open(summary_path, "r", encoding="utf8") as f:
        summaries = list(csv.DictReader(f))
    assert len(summaries) == 16, "Expected 16 case summaries (8 modified variants x 2 schemas)"
    for s in summaries:
        changed_total = int(s["changed_total"])
        unintended = int(s["unintended_changed"])
        changed_meta = int(s["changed_metadata"])
        assert unintended > 0, f"Expected unintended drift in {s['case_id']}"
        if "ts_" in s["variant_id"]:
            assert 10 <= unintended <= 20, f"Timestamp edit drift unexpected range: {unintended} in {s['case_id']}"
            assert changed_meta >= 10, f"Timestamp edit must drift metadata: {s['case_id']}"
        elif "overlay" in s["variant_id"]:
            assert unintended > 200, f"Overlay padding must cause extensive drift (>200) in {s['case_id']}"

def test_xsentinel_scores_integrity():
    scores_path = OUT_DIR / "xsentinel_scores.csv"
    assert scores_path.exists(), "xsentinel_scores.csv must exist"
    with open(scores_path, "r", encoding="utf8") as f:
        scores = list(csv.DictReader(f))
    assert len(scores) == 240, f"Expected exactly 240 evaluation rows, found {len(scores)}"
    for r in scores:
        assert float(r["p_main"]) >= 0.0, "p_main must be non-negative"
        assert float(r["M3"]) >= 0.0, "M3 must be non-negative"
        assert float(r["X_R"]) >= 0.0, "X_R must be non-negative"
        assert r["scoring_status"] == "SCORED_FROZEN_BUNDLE"
    alerts_xr = sum(1 for r in scores if r["trigger_alert_X_R"] == "True")
    alerts_xf = sum(1 for r in scores if r["trigger_alert_X_F"] == "True")
    assert alerts_xr == 0, f"Expected 0 X_R trigger alerts on benign fixtures, got {alerts_xr}"
    assert alerts_xf == 0, f"Expected 0 X_F trigger alerts on benign fixtures, got {alerts_xf}"

def test_native_fixture_functional_execution():
    bin_path = EXP_DIR / "fixtures/variants/native_original.exe"
    if not bin_path.exists():
        pytest.skip("native_original.exe not found")
        
    cmd_prefix = []
    if os.name != "nt":
        if shutil.which("wine"):
            cmd_prefix = ["wine"]
        else:
            pytest.skip("PE binary execution on Linux requires wine (tested in test_functionality_linux.py on host)")
            
    # Test case 1: no args -> 7
    res1 = subprocess.run(cmd_prefix + [str(bin_path)], capture_output=True, text=True)
    assert res1.returncode == 0
    assert "X_SENTINEL_BENIGN_FIXTURE:7" in res1.stdout
    # Test case 2: arg 5 -> 32
    res2 = subprocess.run(cmd_prefix + [str(bin_path), "5"], capture_output=True, text=True)
    assert res2.returncode == 0
    assert "X_SENTINEL_BENIGN_FIXTURE:32" in res2.stdout
    # Test case 3: invalid arg -> exit 2
    res3 = subprocess.run(cmd_prefix + [str(bin_path), "invalid"], capture_output=True, text=True)
    assert res3.returncode == 2
