from __future__ import annotations

import math
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Integer, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from x_sentinel.data.schema import (
    FEATURE_COUNT,
    DimensionMismatchError,
    InvalidDataTypeError,
    NonFiniteValueError,
    StructuralShapeError,
    VectorSchema,
    VectorValidationError,
    validate_named_features,
    validate_vector,
    validate_vector_batch,
)
from x_sentinel.data.views import (
    IndicesSpec,
    SliceSpec,
    ViewMap,
    compute_mapping_hash,
    load_view_map,
)
from x_sentinel.database.base import Base
from x_sentinel.database.session import get_db
from x_sentinel.main import app

# ---------------------------------------------------------------------------
# Positive Schema Tests
# ---------------------------------------------------------------------------


def test_accepts_valid_2381_vector():
    raw = [0.0] * FEATURE_COUNT
    out = validate_vector(raw)
    assert len(out) == FEATURE_COUNT
    assert isinstance(out, list)
    assert out == raw


def test_preserves_exact_feature_ordering():
    raw = [float(i * 1.5) for i in range(FEATURE_COUNT)]
    out = validate_vector(raw)
    assert out[0] == 0.0
    assert out[100] == 150.0
    assert out[2380] == 2380 * 1.5
    assert out == raw


def test_accepts_integer_inputs_converted_to_float():
    raw = [0] * FEATURE_COUNT
    raw[10] = 42
    out = validate_vector(raw)
    assert out[10] == 42.0
    assert isinstance(out[10], float)


def test_accepts_negative_and_extreme_finite_floats():
    raw = [0.0] * FEATURE_COUNT
    raw[1] = -12345.6789
    raw[2] = 1e12
    raw[3] = -1e-8
    out = validate_vector(raw)
    assert out[1] == -12345.6789
    assert out[2] == 1e12
    assert out[3] == -1e-8


def test_validate_vector_batch_valid():
    batch = [[float(j) for j in range(FEATURE_COUNT)] for _ in range(3)]
    out = validate_vector_batch(batch)
    assert len(out) == 3
    for v in out:
        assert len(v) == FEATURE_COUNT


def test_validate_named_features_success():
    feature_names = [f"f_{i}" for i in range(FEATURE_COUNT)]
    mapping = {f"f_{i}": float(i) for i in reversed(range(FEATURE_COUNT))}
    out = validate_named_features(mapping, feature_names)
    assert len(out) == FEATURE_COUNT
    assert out[0] == 0.0
    assert out[2380] == 2380.0


def test_vector_schema_helper():
    schema = VectorSchema()
    assert schema.feature_count == FEATURE_COUNT
    assert schema.dtype == "float64"
    out = schema.validate([0.0] * FEATURE_COUNT)
    assert len(out) == FEATURE_COUNT


# ---------------------------------------------------------------------------
# Negative Schema Tests
# ---------------------------------------------------------------------------


def test_rejects_missing_features():
    raw = [0.0] * (FEATURE_COUNT - 1)
    with pytest.raises(DimensionMismatchError) as exc_info:
        validate_vector(raw)
    assert "missing 1" in str(exc_info.value).lower()
    assert exc_info.value.expected == FEATURE_COUNT
    assert exc_info.value.actual == FEATURE_COUNT - 1


def test_rejects_extra_features():
    raw = [0.0] * (FEATURE_COUNT + 5)
    with pytest.raises(DimensionMismatchError) as exc_info:
        validate_vector(raw)
    assert "extra 5" in str(exc_info.value).lower()
    assert exc_info.value.expected == FEATURE_COUNT
    assert exc_info.value.actual == FEATURE_COUNT + 5


def test_rejects_none_input():
    with pytest.raises(StructuralShapeError):
        validate_vector(None)  # type: ignore[arg-type]


def test_rejects_scalar_input():
    with pytest.raises(StructuralShapeError):
        validate_vector(123.45)  # type: ignore[arg-type]


def test_rejects_string_input():
    with pytest.raises(StructuralShapeError):
        validate_vector("not_a_vector")  # type: ignore[arg-type]


def test_rejects_dict_input():
    with pytest.raises(StructuralShapeError):
        validate_vector({i: 0.0 for i in range(FEATURE_COUNT)})  # type: ignore[arg-type]


def test_rejects_multidimensional_nested_list():
    raw = [[0.0]] * FEATURE_COUNT
    with pytest.raises((InvalidDataTypeError, StructuralShapeError, VectorValidationError)):
        validate_vector(raw)


def test_rejects_boolean_elements():
    raw: list[object] = [0.0] * FEATURE_COUNT
    raw[50] = True
    with pytest.raises(InvalidDataTypeError) as exc_info:
        validate_vector(raw)  # type: ignore[arg-type]
    assert "boolean" in str(exc_info.value).lower()
    assert exc_info.value.index == 50


def test_rejects_string_element():
    raw: list[object] = [0.0] * FEATURE_COUNT
    raw[77] = "0.0"
    with pytest.raises(InvalidDataTypeError) as exc_info:
        validate_vector(raw)  # type: ignore[arg-type]
    assert exc_info.value.index == 77


def test_rejects_none_element():
    raw: list[object] = [0.0] * FEATURE_COUNT
    raw[12] = None
    with pytest.raises(InvalidDataTypeError) as exc_info:
        validate_vector(raw)  # type: ignore[arg-type]
    assert exc_info.value.index == 12


def test_rejects_nan_element():
    raw = [0.0] * FEATURE_COUNT
    raw[99] = math.nan
    with pytest.raises(NonFiniteValueError) as exc_info:
        validate_vector(raw)
    assert "nan" in str(exc_info.value).lower()
    assert exc_info.value.index == 99


def test_rejects_positive_infinity():
    raw = [0.0] * FEATURE_COUNT
    raw[105] = math.inf
    with pytest.raises(NonFiniteValueError) as exc_info:
        validate_vector(raw)
    assert "inf" in str(exc_info.value).lower()
    assert exc_info.value.index == 105


def test_rejects_negative_infinity():
    raw = [0.0] * FEATURE_COUNT
    raw[200] = -math.inf
    with pytest.raises(NonFiniteValueError) as exc_info:
        validate_vector(raw)
    assert "inf" in str(exc_info.value).lower()
    assert exc_info.value.index == 200


def test_validate_vector_batch_rejects_invalid_item():
    batch = [
        [0.0] * FEATURE_COUNT,
        [0.0] * (FEATURE_COUNT - 1),  # Invalid item
    ]
    with pytest.raises(DimensionMismatchError):
        validate_vector_batch(batch)


def test_validate_named_features_missing_key():
    names = [f"f_{i}" for i in range(FEATURE_COUNT)]
    mapping = {f"f_{i}": 0.0 for i in range(FEATURE_COUNT - 1)}  # Missing f_2380
    with pytest.raises(DimensionMismatchError):
        validate_named_features(mapping, names)


def test_validate_named_features_extra_key():
    names = [f"f_{i}" for i in range(FEATURE_COUNT)]
    mapping = {f"f_{i}": 0.0 for i in range(FEATURE_COUNT)}
    mapping["unexpected_extra"] = 1.0
    with pytest.raises(DimensionMismatchError):
        validate_named_features(mapping, names)


# ---------------------------------------------------------------------------
# Semantic View Mapping Tests
# ---------------------------------------------------------------------------


def test_demo_view_map_load_and_split():
    path = Path("configs/views.demo.yaml")
    vm = load_view_map(path, allow_demo=True)
    assert vm.status == "PROPOSED_DEMO_ONLY"
    assert vm.feature_count == FEATURE_COUNT

    vec = [float(i) for i in range(FEATURE_COUNT)]
    parts = vm.split(vec)

    assert "structural" in parts
    assert "behavioral" in parts
    assert "metadata" in parts

    assert len(parts["structural"]) == 255
    assert len(parts["behavioral"]) == 1280
    assert len(parts["metadata"]) == 846
    assert sum(len(p) for p in parts.values()) == FEATURE_COUNT

    # Check ordering in each view
    assert parts["structural"][0] == 0.0
    assert parts["structural"][-1] == 254.0
    assert parts["behavioral"][0] == 255.0
    assert parts["behavioral"][-1] == 1534.0
    assert parts["metadata"][0] == 1535.0
    assert parts["metadata"][-1] == 2380.0


def test_scientific_view_map_fails_closed_due_to_oq01():
    path = Path("configs/views.scientific.yaml")
    with pytest.raises(RuntimeError) as exc_info:
        load_view_map(path, allow_demo=True)
    assert "unresolved" in str(exc_info.value).lower()


def test_demo_view_map_rejected_when_demo_not_allowed():
    path = Path("configs/views.demo.yaml")
    with pytest.raises(RuntimeError) as exc_info:
        load_view_map(path, allow_demo=False)
    assert "demo" in str(exc_info.value).lower()


def test_mapping_hash_deterministic():
    demo_views = {
        "structural": SliceSpec(0, 255),
        "behavioral": SliceSpec(255, 1535),
        "metadata": SliceSpec(1535, 2381),
    }
    hash1 = compute_mapping_hash(demo_views)
    hash2 = compute_mapping_hash(demo_views)
    assert hash1 == hash2
    assert len(hash1) == 64
    assert hash1 == "276be235642b655efab3b8e2bd26af0dde4617ccac0d4d63195c636ee408b5cb"


def test_mapping_hash_detects_mutation():
    orig_views = {
        "structural": SliceSpec(0, 255),
        "behavioral": SliceSpec(255, 1535),
        "metadata": SliceSpec(1535, 2381),
    }
    mutated_views = {
        "structural": SliceSpec(0, 256),  # Mutated boundary
        "behavioral": SliceSpec(256, 1535),
        "metadata": SliceSpec(1535, 2381),
    }
    assert compute_mapping_hash(orig_views) != compute_mapping_hash(mutated_views)


def test_indices_spec_view_extraction():
    indices = [0, 5, 10, 100]
    spec = IndicesSpec(indices)
    assert spec.count == 4
    assert spec.indices() == indices

    vec = [float(i) for i in range(FEATURE_COUNT)]
    extracted = spec.extract(vec)
    assert extracted == [0.0, 5.0, 10.0, 100.0]


def test_view_map_integrity_validation_out_of_bounds():
    bad_views = {
        "structural": SliceSpec(0, 255),
        "behavioral": SliceSpec(255, 1535),
        "metadata": SliceSpec(1535, 3000),  # Exceeds 2381
    }
    vm = ViewMap(status="TEST", **bad_views)
    with pytest.raises(ValueError) as exc_info:
        vm.validate_integrity()
    assert "out of bounds" in str(exc_info.value).lower()


def test_view_map_integrity_validation_empty_view():
    bad_views = {
        "structural": SliceSpec(0, 0),  # Empty view
        "behavioral": SliceSpec(0, 1535),
        "metadata": SliceSpec(1535, 2381),
    }
    vm = ViewMap(status="TEST", **bad_views)
    with pytest.raises(ValueError) as exc_info:
        vm.validate_integrity()
    assert "empty" in str(exc_info.value).lower()


def test_view_map_integrity_validation_duplicate_indices():
    bad_views = {
        "structural": IndicesSpec([0, 1, 1, 2]),  # Duplicate index 1
        "behavioral": SliceSpec(255, 1535),
        "metadata": SliceSpec(1535, 2381),
    }
    vm = ViewMap(status="TEST", **bad_views)
    with pytest.raises(ValueError) as exc_info:
        vm.validate_integrity()
    assert "duplicate" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Integration Tests with FastAPI & Services
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def override_be04_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    for col in Base.metadata.tables["audit_events"].columns:
        if col.name == "id":
            col.type = Integer()
    for table in Base.metadata.tables.values():
        for col in table.columns:
            if col.server_default is not None:
                text_str = str(col.server_default.arg)
                if "N'" in text_str:
                    col.server_default.arg.text = text_str.replace("N'", "'")
    Base.metadata.create_all(engine)
    session = Session(engine)

    def _get_test_db():
        yield session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.pop(get_db, None)
    session.close()
    engine.dispose()


def test_fastapi_analyze_vector_valid():
    client = TestClient(app)
    payload = {
        "features": [0.0] * FEATURE_COUNT,
        "request_id": "req-be04-valid-01",
    }
    resp = client.post("/v1/analyze/vector", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["request_id"] == "req-be04-valid-01"
    assert data["demo_mode"] is True
    assert "structural" in data["view_contributions"]
    assert "behavioral" in data["view_contributions"]
    assert "metadata" in data["view_contributions"]


def test_fastapi_analyze_vector_invalid_length_returns_422():
    client = TestClient(app)
    payload = {
        "features": [0.0] * (FEATURE_COUNT - 10),
        "request_id": "req-be04-invalid-01",
    }
    resp = client.post("/v1/analyze/vector", json=payload)
    assert resp.status_code == 422
    err = resp.json()["detail"]
    assert err["code"] == "XS_INPUT_INVALID"
    assert "missing 10" in err["message"].lower()


def test_fastapi_analyze_vector_nan_returns_422():
    client = TestClient(app)
    raw_payload = '{"features": [' + '0.0,' * 2380 + 'NaN], "request_id": "req-be04-invalid-nan"}'
    resp = client.post(
        "/v1/analyze/vector",
        content=raw_payload,
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 422
    err = resp.json()["detail"]
    assert err["code"] == "XS_INPUT_INVALID"
    assert "nan" in err["message"].lower()


# ---------------------------------------------------------------------------
# Additional Boundary & Edge Case Tests for High Integrity
# ---------------------------------------------------------------------------


def test_validate_vector_batch_invalid_inputs():
    with pytest.raises(StructuralShapeError):
        validate_vector_batch(None)
    with pytest.raises(StructuralShapeError):
        validate_vector_batch("not_a_batch")
    with pytest.raises(StructuralShapeError):
        validate_vector_batch(12345)


def test_validate_named_features_non_dict():
    with pytest.raises(StructuralShapeError):
        validate_named_features(["not", "a", "dict"], ["f_0"])  # type: ignore[arg-type]


def test_vector_schema_validate_batch():
    schema = VectorSchema()
    batch = [[0.0] * FEATURE_COUNT, [1.0] * FEATURE_COUNT]
    out = schema.validate_batch(batch)
    assert len(out) == 2
    assert out[1][0] == 1.0


def test_load_view_map_from_dict_and_hash_validation():
    valid_dict = {
        "status": "PROPOSED_DEMO_ONLY",
        "version": "1.0.0-demo",
        "feature_count": FEATURE_COUNT,
        "sha256": "276be235642b655efab3b8e2bd26af0dde4617ccac0d4d63195c636ee408b5cb",
        "views": {
            "structural": {"kind": "slice", "start": 0, "stop": 255},
            "behavioral": {"kind": "slice", "start": 255, "stop": 1535},
            "metadata": {"kind": "slice", "start": 1535, "stop": 2381},
        },
    }
    vm = load_view_map(valid_dict, allow_demo=True)
    assert vm.mapping_hash == "276be235642b655efab3b8e2bd26af0dde4617ccac0d4d63195c636ee408b5cb"

    # Corrupt hash in dict
    corrupt_dict = dict(valid_dict)
    corrupt_dict["sha256"] = "badbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadb"
    with pytest.raises(ValueError) as exc_info:
        load_view_map(corrupt_dict, allow_demo=True)
    assert "hash mismatch" in str(exc_info.value).lower()


def test_load_view_map_invalid_input_type():
    with pytest.raises(TypeError):
        load_view_map(12345)  # type: ignore[arg-type]


def test_load_view_map_missing_views_dict():
    with pytest.raises(ValueError) as exc_info:
        load_view_map({"status": "OK", "views": "not_a_dict"})
    assert "must be a dictionary" in str(exc_info.value).lower()


def test_load_view_map_missing_specific_view():
    partial_dict = {
        "status": "OK",
        "views": {
            "structural": {"kind": "slice", "start": 0, "stop": 255},
            "behavioral": {"kind": "slice", "start": 255, "stop": 1535},
            # missing metadata
        },
    }
    with pytest.raises(ValueError) as exc_info:
        load_view_map(partial_dict)
    assert "metadata" in str(exc_info.value).lower()


def test_load_view_map_unsupported_kind():
    unsupported_dict = {
        "status": "OK",
        "views": {
            "structural": {"kind": "unsupported_kind"},
            "behavioral": {"kind": "slice", "start": 255, "stop": 1535},
            "metadata": {"kind": "slice", "start": 1535, "stop": 2381},
        },
    }
    with pytest.raises(ValueError) as exc_info:
        load_view_map(unsupported_dict)
    assert "unsupported view spec kind" in str(exc_info.value).lower()


def test_compute_mapping_hash_dict_specs_and_errors():
    dict_specs = {
        "structural": {"kind": "slice", "start": 0, "stop": 10, "step": 2},
        "behavioral": {"kind": "indices", "indices": [10, 11, 12]},
        "metadata": {"kind": "slice", "start": 13, "stop": 20},
    }
    h = compute_mapping_hash(dict_specs)
    assert len(h) == 64

    with pytest.raises(ValueError):
        compute_mapping_hash({"structural": {"kind": "unknown_kind"}})

    with pytest.raises(TypeError):
        compute_mapping_hash({"structural": 9999})


def test_view_map_integrity_require_disjoint_failure():
    overlapping_views = {
        "structural": SliceSpec(0, 300),
        "behavioral": SliceSpec(200, 1535),  # Overlaps [200, 300)
        "metadata": SliceSpec(1535, 2381),
    }
    vm = ViewMap(status="TEST", **overlapping_views)
    with pytest.raises(ValueError) as exc_info:
        vm.validate_integrity(require_disjoint=True)
    assert "not disjoint" in str(exc_info.value).lower()


def test_view_map_integrity_require_complete_failure():
    incomplete_views = {
        "structural": SliceSpec(0, 255),
        "behavioral": SliceSpec(255, 1535),
        "metadata": SliceSpec(1535, 2000),  # Incomplete: missing [2000, 2381)
    }
    vm = ViewMap(status="TEST", **incomplete_views)
    with pytest.raises(ValueError) as exc_info:
        vm.validate_integrity(require_complete=True)
    assert "do not cover all features" in str(exc_info.value).lower()


def test_view_map_integrity_full_coverage_passes():
    path = Path("configs/views.demo.yaml")
    vm = load_view_map(path, allow_demo=True)
    report = vm.validate_integrity(require_disjoint=True, require_complete=True)
    assert report["disjoint"] is True
    assert report["complete"] is True
    assert report["structural_count"] == 255
    assert report["behavioral_count"] == 1280
    assert report["metadata_count"] == 846


def test_view_map_split_invalid_vector_length():
    path = Path("configs/views.demo.yaml")
    vm = load_view_map(path, allow_demo=True)
    with pytest.raises(ValueError) as exc_info:
        vm.split([0.0] * 100)
    assert "must have exactly 2381 features" in str(exc_info.value).lower()


def test_slice_spec_step_and_extract():
    spec = SliceSpec(start=0, stop=10, step=2)
    assert spec.count == 5
    assert spec.indices() == [0, 2, 4, 6, 8]
    vec = [float(i) for i in range(10)]
    assert spec.extract(vec) == [0.0, 2.0, 4.0, 6.0, 8.0]

