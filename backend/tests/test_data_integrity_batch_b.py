from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError
from sqlalchemy import Integer, create_engine, select
from sqlalchemy.orm import Session
from x_sentinel.api.schemas import VectorAnalysisRequest
from x_sentinel.audit.writer import AuditWriteFailureError
from x_sentinel.database.models import AnalysisJob, AnalysisResultRecord, AuditEvent, Base
from x_sentinel.services.analysis_service import AnalysisService


@pytest.fixture
def sqlite_session():
    """Provides an isolated in-memory SQLite session with full schema initialized."""
    engine = create_engine("sqlite:///:memory:")
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
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


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


def test_finding_14_strict_pydantic_vector_validation():
    """Verify Finding 14: VectorAnalysisRequest strictly rejects boolean, string, nan, inf, and invalid length."""
    valid_features = [0.0] * 2381

    # 1. Valid vector succeeds
    req = VectorAnalysisRequest(features=valid_features)
    assert len(req.features) == 2381
    assert all(isinstance(x, float) for x in req.features)

    # 2. Length mismatch fails
    with pytest.raises(ValidationError) as exc:
        VectorAnalysisRequest(features=[0.0] * 2380)
    assert "2,381 dimensions" in str(exc.value)

    # 3. Boolean values must NOT be coerced to float
    with pytest.raises(ValidationError) as exc:
        VectorAnalysisRequest(features=[True] + [0.0] * 2380)
    assert "invalid non-numeric type: bool" in str(exc.value)

    # 4. String values must NOT be coerced to float
    with pytest.raises(ValidationError) as exc:
        VectorAnalysisRequest(features=["0.5"] + [0.0] * 2380)
    assert "invalid non-numeric type: str" in str(exc.value)

    # 5. NaN must be rejected
    with pytest.raises(ValidationError) as exc:
        VectorAnalysisRequest(features=[float("nan")] + [0.0] * 2380)
    assert "must be finite" in str(exc.value)

    # 6. Infinity must be rejected
    with pytest.raises(ValidationError) as exc:
        VectorAnalysisRequest(features=[float("inf")] + [0.0] * 2380)
    assert "must be finite" in str(exc.value)


def test_finding_07_canonical_ieee754_vector_hashing(analysis_svc: AnalysisService):
    """Verify Finding 7: Canonical IEEE-754 64-bit float binary hashing eliminates float rounding collisions."""
    vec_a = [0.0] * 2381
    # 1e-7 previously collided with 0.0 under round(f, 6)
    vec_b = [1e-7] + [0.0] * 2380

    res_a = analysis_svc.analyze_vector(features=vec_a, request_id="hash-test-a")
    res_b = analysis_svc.analyze_vector(features=vec_b, request_id="hash-test-b")

    assert res_a.input_sha256 is not None
    assert res_b.input_sha256 is not None
    assert res_a.input_sha256 != res_b.input_sha256, (
        f"Hash collision detected between 0.0 and 1e-7! Hashes: {res_a.input_sha256} == {res_b.input_sha256}"
    )


def test_finding_02_no_destructive_job_deletion(sqlite_session: Session, analysis_svc: AnalysisService):
    """Verify Finding 2: Duplicate request_id with prefix 'req-be04-' raises error and NEVER deletes existing job."""
    test_rid = "req-be04-test-unique-id"

    # 1. Create and commit an existing job in DB
    existing_job = AnalysisJob(
        id=uuid.uuid4(),
        request_id=test_rid,
        input_mode="vector",
        input_sha256="0" * 64,
        status="completed",
        created_at=datetime.now(UTC),
    )
    sqlite_session.add(existing_job)
    sqlite_session.commit()
    orig_id = existing_job.id

    # 2. Re-submitting the exact same request_id must raise AuditWriteFailureError
    with pytest.raises(AuditWriteFailureError) as exc_info:
        analysis_svc.analyze_vector(
            features=[0.0] * 2381,
            request_id=test_rid,
            session=sqlite_session,
        )
    assert "already exists. Overwrite rejected." in str(exc_info.value)

    # 3. Verify original job is NOT deleted from DB!
    preserved = sqlite_session.scalar(select(AnalysisJob).where(AnalysisJob.request_id == test_rid))
    assert preserved is not None
    assert preserved.id == orig_id


def test_finding_05_database_authoritative_audit_consistency(
    sqlite_session: Session, analysis_svc: AnalysisService
):
    """Verify Finding 5: Database is Authoritative Single Source of Truth; secondary JSONL audit failure does not break DB transaction."""
    test_rid = f"test-audit-consistency-{uuid.uuid4().hex[:8]}"

    # Mock secondary file-based audit append to simulate disk full / permission error
    with patch.object(analysis_svc.audit, "append", side_effect=AuditWriteFailureError("Disk write failed")):
        result = analysis_svc.analyze_vector(
            features=[0.0] * 2381,
            request_id=test_rid,
            session=sqlite_session,
        )

    # Analysis must succeed despite secondary JSONL write failure
    assert result.request_id == test_rid
    assert result.status in ("completed", "DEMO_ONLY")

    # Database authoritative job and audit event must be safely committed!
    db_job = sqlite_session.scalar(select(AnalysisJob).where(AnalysisJob.request_id == test_rid))
    assert db_job is not None
    assert db_job.status in ("completed", "quarantined")

    db_audit = sqlite_session.scalar(select(AuditEvent).where(AuditEvent.request_id == test_rid))
    assert db_audit is not None
    assert db_audit.event_type == "evidence.persisted"


def test_finding_10_end_to_end_latency_includes_persistence(
    sqlite_session: Session, analysis_svc: AnalysisService
):
    """Verify Finding 10: end_to_end latency instrumentation includes database persistence duration."""
    test_rid = f"test-latency-{uuid.uuid4().hex[:8]}"

    # Artificially delay commit by 50ms during persistence
    orig_commit = sqlite_session.commit
    def slow_commit():
        time.sleep(0.05)
        orig_commit()

    with patch.object(sqlite_session, "commit", side_effect=slow_commit):
        result = analysis_svc.analyze_vector(
            features=[0.0] * 2381,
            request_id=test_rid,
            session=sqlite_session,
        )

    # end_to_end latency in domain result must be >= 45ms
    assert "end_to_end" in result.measured_latency_ms
    assert result.measured_latency_ms["end_to_end"] >= 45.0, (
        f"end_to_end latency {result.measured_latency_ms['end_to_end']}ms did not include persistence delay"
    )
    assert "persistence" in result.measured_latency_ms
    assert result.measured_latency_ms["persistence"] >= 45.0

    # Also verify database record has authentic latency including persistence!
    res_rec = sqlite_session.scalar(
        select(AnalysisResultRecord).where(AnalysisResultRecord.analysis_job_id == uuid.UUID(result.job_id))
    )
    assert res_rec is not None
    assert res_rec.latency_ms >= 45.0
