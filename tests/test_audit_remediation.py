"""Regression tests verifying full system bug fixes and hardening."""
import numpy as np
import pytest
from fastapi.testclient import TestClient
from xsentinel.service.api import create_app, VectorRequest
from xsentinel.data.pe import extract_pe, verify_pe
from xsentinel.revision.reviewer_core import CoreScorer
from xsentinel.schema import get_schema, V2_PRIMARY


def test_vector_length_validation_rejects_intermediate_dimensions():
    """BUG-01: Vector length must be strictly 2381 or 2568, not intermediate lengths."""
    valid_2381 = [0.0] * 2381
    valid_2568 = [0.0] * 2568
    invalid_2400 = [0.0] * 2400

    # Pydantic schema validation
    req1 = VectorRequest(bundle_id='a'*64, features=valid_2381)
    assert len(req1.features) == 2381

    req2 = VectorRequest(bundle_id='a'*64, features=valid_2568)
    assert len(req2.features) == 2568

    with pytest.raises(ValueError, match='Vector length must be exactly 2381.*or 2568'):
        VectorRequest(bundle_id='a'*64, features=invalid_2400)


def test_api_rejects_schema_dimension_mismatch(monkeypatch):
    """BUG-01: Reject request when features dimension does not match bundle schema."""
    import xsentinel.service.api as api_mod

    class DummyRegistry:
        def entry(self, bundle_id):
            return {
                'id': bundle_id,
                'state': {'schema': 'ember-v2-2381-views-v2', 'thresholds': {'X_primary_reduced': 0.5}},
                'variant': 'reduced'
            }
        def listing(self):
            return []

    dummy_engine = object()
    monkeypatch.setattr(api_mod, 'readiness', lambda eng: {'ok': True, 'revision': ['0002_primary_scores'], 'expected_revision': '0002_primary_scores'})

    app = create_app(engine=dummy_engine, registry=DummyRegistry())
    client = TestClient(app)

    # Send 2568 features to a bundle that expects 2381
    payload = {
        'bundle_id': 'a' * 64,
        'features': [0.0] * 2568,
        'method': 'X_primary_reduced'
    }
    # Should be rejected with 422 Unprocessable Entity
    response = client.post('/v1/analyze/vector', json=payload)
    assert response.status_code == 422
    assert 'does not match bundle schema expected dimension' in response.json()['detail']


def test_pe_corrupted_header_handling():
    """BUG-04: Malformed PE data should raise clear ValueError rather than unhandled crash."""
    # Truncated DOS header
    with pytest.raises(ValueError, match='Missing DOS MZ header'):
        verify_pe(b'MZ' + b'\x00' * 10)

    # Invalid PE signature offset
    corrupted_pe = bytearray(b'MZ' + b'\x00' * 62)
    # Point e_lfanew to out-of-range offset
    corrupted_pe[0x3c:0x40] = (9999).to_bytes(4, 'little')
    with pytest.raises(ValueError, match='Invalid PE signature/header offset'):
        verify_pe(bytes(corrupted_pe))


def test_reviewer_core_precomputed_shap_consistency():
    """BUG-05: Passing precomputed phi, p, pb must yield identical results to standard scoring."""
    class MockModel:
        def num_feature(self):
            return 2381
        def predict(self, x, num_threads=4, pred_contrib=False, raw_score=False):
            if pred_contrib:
                # schema.dim + 1
                return np.zeros((len(x), 2382), dtype=np.float32)
            if raw_score:
                return np.zeros(len(x), dtype=np.float32)
            return np.full(len(x), 0.75, dtype=np.float32)

    schema = get_schema(V2_PRIMARY)
    scorer = CoreScorer(main=MockModel(), schema=schema)
    ref_x = np.zeros((10, 2381), dtype=np.float32)
    scorer.fit_reference(ref_x)

    test_x = np.zeros((4, 2381), dtype=np.float32)
    scores_standard, probs_standard = scorer.score(test_x)

    # Precompute
    phi = np.zeros((4, 2381), dtype=np.float32)
    p = np.full(4, 0.75, dtype=np.float32)
    scores_fast, probs_fast = scorer.score(test_x, phi=phi, p=p)

    np.testing.assert_allclose(probs_standard, probs_fast)
    for k in scores_standard:
        np.testing.assert_allclose(scores_standard[k], scores_fast[k])
