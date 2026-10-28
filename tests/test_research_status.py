from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from xsentinel.research_status import (load_research_status, snapshot_digest,
                                      validate_research_status)


def test_packaged_snapshot_loads_without_working_directory_outputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = load_research_status()
    assert result["state"] == "ready"
    snapshot = result["snapshot"]
    assert snapshot["primary"]["configuration_count"] == 54
    assert snapshot["primary"]["bundle_count"] == 108
    assert snapshot["seeds"]["additional_seeds"] == [59, 71]
    assert snapshot["seeds"]["confirmed_count"] == 4
    assert snapshot["binary_audit"]["windows_pass"] == 32
    assert snapshot["binary_audit"]["windows_error"] == 8
    assert len(snapshot["binary_audit"]["feature_shift_rows"]) == 16
    assert len(snapshot["binary_audit"]["windows_rows"]) == 10
    overlay_v3 = [r for r in snapshot["binary_audit"]["feature_shift_rows"]
                  if r["schema"] == "V3" and r["edit"] == "Overlay +246 B"]
    assert {r["fixture"]: r["collateral"] for r in overlay_v3} == {"C x64": 352, ".NET C#": 237}
    assert snapshot["scope"]["live_service_status"] is False
    # Each call returns fresh data; UI mutations must not alter the packaged record.
    snapshot["primary"]["configuration_count"] = 999
    assert load_research_status()["snapshot"]["primary"]["configuration_count"] == 54


def test_missing_or_malformed_snapshot_never_returns_placeholder_metrics(tmp_path):
    missing = load_research_status(tmp_path / "missing.json")
    assert missing["state"] == "missing" and missing["snapshot"] is None
    broken = tmp_path / "broken.json"
    broken.write_text("{", encoding="utf-8")
    invalid = load_research_status(broken)
    assert invalid["state"] == "invalid" and invalid["snapshot"] is None
    broken.write_text('{"schema_version": 99}', encoding="utf-8")
    assert load_research_status(broken)["state"] == "invalid"
    # Well-formed JSON with wrong nested types must also fail closed.
    malformed = load_research_status()["snapshot"]
    malformed["scope"] = []
    malformed["content_sha256"] = snapshot_digest(malformed)
    broken.write_text(json.dumps(malformed), encoding="utf-8")
    assert load_research_status(broken)["state"] == "invalid"


def test_inconsistent_rates_and_counts_rejected_even_with_new_digest():
    original = load_research_status()["snapshot"]
    for mutate in [lambda s: s["same_fpr"]["rows"][0].update(tpr=35.7),
                   lambda s: s["binary_audit"].update(windows_pass=40),
                   lambda s: s["scope"].update(live_service_status=True),
                   lambda s: s["provenance"]["sources"][0].update(path="../outside.csv")]:
        snapshot = deepcopy(original)
        mutate(snapshot)
        snapshot["content_sha256"] = snapshot_digest(snapshot)
        with pytest.raises(ValueError):
            validate_research_status(snapshot)


def test_snapshot_digest_detects_silent_metric_edit(tmp_path):
    snapshot = load_research_status()["snapshot"]
    snapshot["same_fpr"]["rows"][0]["tpr"] = 0.95
    path = tmp_path / "edited.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")
    result = load_research_status(path)
    assert result["state"] == "invalid" and result["snapshot"] is None


def test_frozen_snapshot_matches_source_exports_when_available():
    root = Path(__file__).resolve().parents[1]
    snapshot = load_research_status()["snapshot"]
    if not all((root / source["path"]).exists() for source in snapshot["provenance"]["sources"]):
        pytest.skip("Local exported research evidence unavailable")
    spec = importlib.util.spec_from_file_location("build_research_status", root / "scripts/build_research_status_2026_10_28.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    assert builder.build_snapshot(root) == snapshot
