"""Automated tests for Problem-Space Real PE Watermark (Task M8).
Validates binary integrity, feature coordinate drift, and X-SENTINEL scoring.
"""

import csv
import io
import json
from pathlib import Path
import numpy as np
import pefile
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs/pe_real_watermark"
EXP_DIR = ROOT / "experiments/pe_real_watermark"


def test_watermark_manifest_integrity():
    manifest_path = OUT_DIR / "manifest.csv"
    if not manifest_path.exists():
        pytest.skip("outputs/pe_real_watermark/manifest.csv not generated yet")

    with open(manifest_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) >= 10, f"Expected at least 10 entries in manifest, found {len(rows)}"
    for r in rows:
        assert len(r["clean_sha256"]) == 64
        assert len(r["watermarked_sha256"]) == 64
        assert int(r["watermarked_size"]) > 0
        assert r["watermarked_sha256"] != r["clean_sha256"]


def test_feature_drift_reveals_problem_space_gap():
    drift_path = OUT_DIR / "feature_drift_analysis.csv"
    if not drift_path.exists():
        pytest.skip("outputs/pe_real_watermark/feature_drift_analysis.csv not generated yet")

    with open(drift_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) >= 10
    for r in rows:
        total_changed = int(r["total_features_changed"])
        unintended = int(r["unintended_collateral_shift"])
        assert total_changed > 0, f"Expected feature changes for {r['item_id']}"
        assert unintended > 50, f"Expected collateral drift (>50) for {r['item_id']}, got {unintended}"
        assert r["coff_ts_target_matched"] in ("True", "true", "1")


def test_xsentinel_watermark_scoring_validity():
    scores_path = OUT_DIR / "xsentinel_watermark_scores.csv"
    if not scores_path.exists():
        pytest.skip("outputs/pe_real_watermark/xsentinel_watermark_scores.csv not generated yet")

    with open(scores_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) >= 10
    for r in rows:
        p_clean = float(r["p_malware_clean"])
        p_wm = float(r["p_malware_wm"])
        vmc_wm = float(r["vmc_wm"])
        bgs_wm = float(r["bgs_wm"])

        assert 0.0 <= p_clean <= 1.0
        assert 0.0 <= p_wm <= 1.0
        assert vmc_wm >= 0.0
        assert bgs_wm >= 0.0


def test_pe_watermark_engine_direct():
    import sys
    sys.path.insert(0, str(EXP_DIR))
    from pe_watermark_engine import PEWatermarkEngine

    # Use native original fixture
    fixture_path = ROOT / "experiments/phuc_pe_validation/fixtures/variants/native_original.exe"
    if not fixture_path.exists():
        pytest.skip("native_original.exe fixture unavailable")

    raw_bytes = fixture_path.read_bytes()
    engine = PEWatermarkEngine(target_timestamp=1053454528)
    wm_bytes = engine.watermark(raw_bytes)

    assert len(wm_bytes) > len(raw_bytes)

    pe_orig = pefile.PE(data=raw_bytes, fast_load=True)
    pe_wm = pefile.PE(data=wm_bytes, fast_load=True)

    assert pe_wm.FILE_HEADER.TimeDateStamp == 1053454528
    assert pe_wm.FILE_HEADER.NumberOfSections == pe_orig.FILE_HEADER.NumberOfSections + 1
    assert pe_wm.OPTIONAL_HEADER.MajorImageVersion == 6
    assert pe_wm.OPTIONAL_HEADER.MinorImageVersion == 1

    pe_orig.close()
    pe_wm.close()
