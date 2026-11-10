from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from x_sentinel.data.views import load_view_map
from x_sentinel.main import app


def test_finding_09_metrics_cardinality_bounded():
    """Verify Finding 9: Random 404 paths are bounded to endpoint='unmatched' and do not explode Prometheus label cardinality."""
    client = TestClient(app, raise_server_exceptions=False)

    # 1. Hit multiple unique non-existent endpoints
    client.get("/non-existent-random-path-alpha-12345")
    client.get("/non-existent-random-path-beta-67890")
    client.get("/non-existent-random-path-gamma-abcdef")

    # 2. Scrape metrics endpoint
    metrics_resp = client.get("/metrics")
    assert metrics_resp.status_code == 200
    metrics_text = metrics_resp.text

    # 3. Random paths must NOT exist as endpoint labels
    assert 'endpoint="/non-existent-random-path-alpha-12345"' not in metrics_text
    assert 'endpoint="/non-existent-random-path-beta-67890"' not in metrics_text
    assert 'endpoint="/non-existent-random-path-gamma-abcdef"' not in metrics_text

    # 4. Must be aggregated under 'unmatched'
    assert 'endpoint="unmatched"' in metrics_text


def test_finding_18_view_map_lru_cache():
    """Verify Finding 18: File-based view map loading is cached in memory with identity reuse."""
    repo_root = Path("/home/phucpnhse203815/X-SENTINEL")
    view_path = repo_root / "configs/views.demo.yaml"

    # First load
    vm1 = load_view_map(view_path)
    # Second load from identical file
    vm2 = load_view_map(view_path)

    # Must be identical cached instance (O(1) memory lookup)
    assert vm1 is vm2
    assert vm1.mapping_hash == vm2.mapping_hash


def test_finding_15_frontend_auth_headers():
    """Verify Finding 15: Frontend auth header logic attaches Bearer token when configured."""
    mock_st = MagicMock()
    mock_st.sidebar.text_input.return_value = "secret-operator-token"
    with patch.dict(sys.modules, {"streamlit": mock_st}):
        with patch.dict("os.environ", {"XS_API_TOKEN": "secret-operator-token"}):
            # Clear cached module if already imported
            sys.modules.pop("frontend.app", None)
            from frontend.app import get_headers

            headers = get_headers()
            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer secret-operator-token"
            assert headers["Content-Type"] == "application/json"
