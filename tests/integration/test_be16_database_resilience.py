from __future__ import annotations

import hashlib
import uuid
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from x_sentinel.audit.evidence import CanonicalEvidence, EvidenceIntegrityError
from x_sentinel.database.base import Base
from x_sentinel.database.models import (
    Alert,
    AnalysisJob,
    AnalysisResultRecord,
    Artifact,
    AuditEvent,
    JevAIFeedback,
    JevAIRun,
    Role,
    User,
    UserRole,
)
from x_sentinel.database.repositories.evidence import CanonicalEvidenceRepository
from x_sentinel.database.repositories.jev_ai import JevAIFeedbackRepository


@pytest.fixture
def resilience_db() -> Generator[Session, None, None]:
    """Hermetic SQLite in-memory database with strict foreign key constraints enabled."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        except Exception:
            pass
    # Fix SQL Server NVARCHAR default syntax for SQLite compatibility
    for col in Base.metadata.tables["audit_events"].columns:
        if col.name == "id":
            from sqlalchemy import Integer

            col.type = Integer()
    for table in Base.metadata.tables.values():
        for col in table.columns:
            default_arg = getattr(col.server_default, "arg", None)
            if default_arg is not None:
                text_str = str(default_arg)
                if "N'" in text_str and hasattr(default_arg, "text"):
                    default_arg.text = text_str.replace("N'", "'")

    Base.metadata.create_all(engine)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _make_evidence(request_id: str | None = None) -> CanonicalEvidence:
    req_id = request_id or f"resilience-req-{uuid.uuid4()}"
    return CanonicalEvidence(
        request_id=req_id,
        run_id=f"run-{uuid.uuid4()}",
        timestamp="2026-10-13T12:00:00+00:00",
        code_commit="git_commit_hash_v3_canonical_0002",
        build_digest="sha256:build_digest_x_sentinel_v3_baseline",
        input_id=hashlib.sha256(b"input").hexdigest(),
        input_mode="vector",
        view_map_hash="276be235642b655efab3b8e2bd26af0dde4617ccac0d4d63195c636ee408b5cb",
        model_hash="509de4a83e2d76b69fb3025ced0429e5f40f6a95ca40122b9eedd03317fff5e2",
        model_config_hash="a1b2c3d4e5f60123456789abcdef0123456789abcdef0123456789abcdef0123",
        detector_config_hash="b2c3d4e5f60123456789abcdef0123456789abcdef0123456789abcdef0123a1",
        seed=42,
        malware_score=0.88,
        signals={"m1": 0.8, "m2": 0.0, "m3": 0.5, "m4": 0.0, "m5": 0.0},
        fusion_score=0.91,
        threshold_id="THRESH-V3-DEFAULT",
        decision="QUARANTINE",
        latency_ms={"end_to_end": 4.5},
        demo_mode=False,
    ).with_hash()


class TestDatabaseResilienceAndCascades:
    """Verifies relational integrity, foreign key cascade behaviors, and transactional resilience."""

    def test_analysis_job_cascade_deletion(self, resilience_db: Session) -> None:
        """Deleting an analysis_job cascades to results, detector_scores, alerts, and artifacts."""
        repo = CanonicalEvidenceRepository(resilience_db)
        evidence = _make_evidence()
        job, result_record, scores, artifact, audit_event = repo.persist(evidence)

        # Also add an alert referencing this job
        alert = Alert(
            analysis_job_id=job.id,
            severity="high",
            status="open",
            reason="Resilience test alert",
        )
        resilience_db.add(alert)
        resilience_db.commit()

        job_id = job.id

        # Verify all records exist prior to deletion
        assert resilience_db.get(AnalysisJob, job_id) is not None
        assert resilience_db.get(AnalysisResultRecord, job_id) is not None
        assert resilience_db.scalar(select(Alert).where(Alert.analysis_job_id == job_id)) is not None
        assert resilience_db.scalar(select(Artifact).where(Artifact.analysis_job_id == job_id)) is not None

        # Delete the root AnalysisJob
        resilience_db.delete(job)
        resilience_db.commit()

        # Verify cascading deletion took effect cleanly
        assert resilience_db.get(AnalysisJob, job_id) is None
        assert resilience_db.get(AnalysisResultRecord, job_id) is None
        assert resilience_db.scalar(select(Alert).where(Alert.analysis_job_id == job_id)) is None
        assert resilience_db.scalar(select(Artifact).where(Artifact.analysis_job_id == job_id)) is None

        # Audit events must remain preserved (append-only audit trail)
        remaining_audit = resilience_db.scalar(
            select(AuditEvent).where(AuditEvent.entity_id == str(job_id))
        )
        assert remaining_audit is not None

    def test_user_deletion_sets_null_on_jobs_and_cascades_user_roles(
        self, resilience_db: Session
    ) -> None:
        """Deleting a user cascades user_roles but sets analysis_jobs.user_id to NULL (no orphaned delete)."""
        test_user = User(
            id=uuid.uuid4(),
            email="resilience_analyst@xsentinel.local",
            normalized_email="resilience_analyst@xsentinel.local",
            display_name="Resilience Analyst",
        )
        resilience_db.add(test_user)

        role = Role(code="TEST_ROLE", description="Test Role")
        resilience_db.add(role)
        resilience_db.flush()

        user_role = UserRole(user_id=test_user.id, role_id=role.id)
        resilience_db.add(user_role)

        repo = CanonicalEvidenceRepository(resilience_db)
        evidence = _make_evidence()
        job, _, _, _, _ = repo.persist(evidence, user_id=test_user.id)

        assert job.user_id == test_user.id
        assert resilience_db.get(UserRole, (test_user.id, role.id)) is not None

        # Delete user
        resilience_db.delete(test_user)
        resilience_db.commit()

        # user_roles should be cascaded
        assert resilience_db.get(UserRole, (test_user.id, role.id)) is None

        # job should still exist with user_id SET NULL
        resilience_db.refresh(job)
        assert job.id is not None
        assert job.user_id is None

    def test_jev_ai_run_deletion_cascades_to_feedback(self, resilience_db: Session) -> None:
        """Deleting a JevAIRun cascades to all associated JevAIFeedback records."""
        run = JevAIRun(
            mode="explain",
            status="completed",
            model_id="test-model",
            prompt_version="1.0.0",
            input_digest_sha256=hashlib.sha256(b"in").hexdigest(),
            output_digest_sha256=hashlib.sha256(b"out").hexdigest(),
            response_text="Advisory explanation",
        )
        resilience_db.add(run)
        resilience_db.commit()
        resilience_db.refresh(run)

        fb_repo = JevAIFeedbackRepository(resilience_db)
        feedback = fb_repo.create_feedback(
            jev_ai_run_id=run.id,
            rating=5,
            label="helpful",
            comment="Excellent analysis",
        )
        resilience_db.commit()
        resilience_db.refresh(feedback)
        fb_id = feedback.id

        # Verify feedback exists
        assert resilience_db.get(JevAIFeedback, fb_id) is not None

        # Delete JevAIRun
        resilience_db.delete(run)
        resilience_db.commit()

        # Feedback should be cascaded
        assert resilience_db.get(JevAIFeedback, fb_id) is None


class TestAuditImmutabilityAndTamperDetection:
    """Verifies that evidence and audit trails detect modifications and remain tamper-evident."""

    def test_bit_flip_tampering_in_persisted_result_json(self, resilience_db: Session) -> None:
        """When an attacker updates result_json directly in SQL, read-back detects tampering."""
        repo = CanonicalEvidenceRepository(resilience_db)
        evidence = _make_evidence()
        job, result_record, _, _, _ = repo.persist(evidence)

        # Directly tamper the persisted result_json in the database
        tampered_dict = dict(result_record.result_json)
        tampered_dict["decision"] = "PASS"  # Tampered from QUARANTINE to PASS
        result_record.result_json = tampered_dict
        resilience_db.commit()

        # Retrieval through CanonicalEvidenceRepository must detect the hash mismatch
        with pytest.raises(EvidenceIntegrityError) as exc_info:
            repo.get_canonical_evidence(evidence.request_id)
        assert "integrity" in str(exc_info.value).lower() or "mismatch" in str(exc_info.value).lower()

    def test_audit_event_append_only_preservation(self, resilience_db: Session) -> None:
        """Audit trail accurately records sequenced events with monotonically increasing IDs."""
        events = [
            AuditEvent(
                request_id=f"audit-{i}",
                event_type="test.event",
                entity_type="test_entity",
                entity_id=f"ent-{i}",
                payload={"step": i},
            )
            for i in range(5)
        ]
        for evt in events:
            resilience_db.add(evt)
        resilience_db.commit()

        loaded = resilience_db.scalars(
            select(AuditEvent).order_by(AuditEvent.id.asc())
        ).all()
        assert len(loaded) >= 5
        ids = [e.id for e in loaded[-5:]]
        assert ids == sorted(ids)


class TestConcurrencyAndThreadSafety:
    """Verifies that concurrent transaction attempts handle locking and uniqueness safely."""

    def test_concurrent_duplicate_request_id_fails_closed(self, resilience_db: Session) -> None:
        """Attempting to persist the same request_id from multiple concurrent threads rejects duplicates."""
        from concurrent.futures import ThreadPoolExecutor

        from sqlalchemy.exc import IntegrityError
        from x_sentinel.audit.writer import AuditWriteFailureError

        shared_request_id = f"concurrent-{uuid.uuid4()}"
        evidence = _make_evidence(request_id=shared_request_id)

        # Persist the initial record
        repo = CanonicalEvidenceRepository(resilience_db)
        repo.persist(evidence)

        # Multiple concurrent threads attempt to persist identical request_id simultaneously
        errors: list[Exception] = []
        successes: list[int] = []
        engine = resilience_db.get_bind()

        def _worker(thread_idx: int) -> None:
            with Session(bind=engine) as worker_session:
                worker_repo = CanonicalEvidenceRepository(worker_session)
                try:
                    worker_repo.persist(evidence)
                    successes.append(thread_idx)
                except (AuditWriteFailureError, IntegrityError, ValueError) as exc:
                    errors.append(exc)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(_worker, i) for i in range(4)]
            for f in futures:
                f.result()

        # Zero duplicates permitted; all 4 concurrent attempts must fail closed
        assert len(successes) == 0, f"Duplicate was unexpectedly persisted: {successes}"
        assert len(errors) == 4, f"Expected 4 rejections, got {len(errors)}"
        assert all(
            any(k in str(e).lower() for k in ("duplicate", "locked", "unique", "integrity", "conflict", "already exists"))
            for e in errors
        ), f"Unexpected error encountered during concurrent duplicate test: {errors}"
