from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from x_sentinel.config import settings
from x_sentinel.main import app
from x_sentinel.services.analysis_service import (
    AnalysisService,
    ScientificPipelineNotReadyError,
)


@pytest.fixture
def analysis_svc(tmp_path: Path) -> AnalysisService:
    audit_file = tmp_path / "audit.jsonl"
    repo_root = Path("/home/phucpnhse203815/X-SENTINEL")
    view_map_file = repo_root / "configs/views.demo.yaml"
    return AnalysisService(
        audit_path=audit_file,
        view_map_path=view_map_file,
        demo_mode=True,
    )


def test_finding_08_scientific_pipeline_not_ready_gated(tmp_path: Path):
    """Verify Finding 8: Scientific pipeline is gated and raises structured ScientificPipelineNotReadyError when frozen assets are missing."""
    audit_file = tmp_path / "audit.jsonl"
    repo_root = Path("/home/phucpnhse203815/X-SENTINEL")
    view_map_file = repo_root / "configs/views.demo.yaml"

    # 1. Direct service instantiation fails-closed with structured missing dependencies
    with pytest.raises(ScientificPipelineNotReadyError) as exc_info:
        AnalysisService(
            audit_path=audit_file,
            view_map_path=view_map_file,
            demo_mode=False,
        )
    assert len(exc_info.value.missing_dependencies) > 0
    assert "models/lightgbm_model.txt" in exc_info.value.missing_dependencies

    # 2. HTTP endpoint returns HTTP 503 SCIENTIFIC_PIPELINE_NOT_READY
    with patch.object(settings, "demo_mode", False):
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/v1/analyze/vector",
            json={"features": [0.0] * 2381, "request_id": "test-sci-gated"},
            headers={"Authorization": "Bearer token-admin"},
        )
        assert resp.status_code == 503
        data = resp.json()
        assert data["detail"]["code"] == "SCIENTIFIC_PIPELINE_NOT_READY"
        assert len(data["detail"]["missing_dependencies"]) > 0


def test_finding_08_demo_mode_explicit_warnings_and_status(analysis_svc: AnalysisService):
    """Verify Finding 8: Demo mode output is explicitly labeled DEMO_ONLY with missing detector warnings."""
    res = analysis_svc.analyze_vector(features=[0.0] * 2381, request_id="demo-label-test")
    assert res.status == "DEMO_ONLY"
    assert res.demo_mode is True
    assert "DEMO_MODE_NOT_SCIENTIFIC_EVIDENCE" in res.warnings
    assert "M2_M4_M5_UNAVAILABLE_IN_DEMO" in res.warnings


def test_finding_06_dynamic_provenance_not_hardcoded(analysis_svc: AnalysisService):
    """Verify Finding 6: Canonical evidence provenance is dynamically resolved from disk/git and not hardcoded."""
    # 1. Git commit is dynamic
    assert analysis_svc.git_commit != "git_commit_hash_v3_canonical_0002"

    # 2. View map hash is computed directly from disk
    expected_view_hash = hashlib.sha256(Path(analysis_svc.view_map_path).read_bytes()).hexdigest()
    assert analysis_svc.view_map_hash == expected_view_hash
    assert analysis_svc.view_map_hash != "276be235642b655efab3b8e2bd26af0dde4617ccac0d4d63195c636ee408b5cb"
