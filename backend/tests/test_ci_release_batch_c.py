from __future__ import annotations

import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from x_sentinel.audit.evidence import CanonicalEvidence
from x_sentinel.audit.writer import AuditWriteFailureError
from x_sentinel.database.models import Base
from x_sentinel.database.repositories.evidence import CanonicalEvidenceRepository
from x_sentinel.detection.m5_semantic import load_m5_rules

from scripts.verify_release_tuple import build_release_tuple


def test_finding_16_m5_rules_cross_platform_hash():
    """Verify Finding 16: M5 rules loading succeeds on both CRLF and LF byte content with canonical hash."""
    repo_root = Path("/home/phucpnhse203815/X-SENTINEL")
    rules_path = repo_root / "configs/m5_rules.json"
    raw_content = rules_path.read_bytes()
    crlf_content = raw_content.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    lf_content = raw_content.replace(b"\r\n", b"\n")

    canonical_sha256 = "2e8c599aa9fded31c8d27eb0d96f45743a087572f696bc8e3bdb0f69d5ca184d"

    with tempfile.NamedTemporaryFile("wb", suffix=".json", delete=False) as f_crlf:
        f_crlf.write(crlf_content)
        f_crlf_path = Path(f_crlf.name)

    with tempfile.NamedTemporaryFile("wb", suffix=".json", delete=False) as f_lf:
        f_lf.write(lf_content)
        f_lf_path = Path(f_lf.name)

    try:
        # 1. CRLF file passes
        data_crlf, hash_crlf = load_m5_rules(f_crlf_path, expected_sha256=canonical_sha256)
        assert hash_crlf.lower() == canonical_sha256.lower()
        assert "rules" in data_crlf

        # 2. LF file passes
        data_lf, hash_lf = load_m5_rules(f_lf_path, expected_sha256=canonical_sha256)
        assert hash_lf.lower() == canonical_sha256.lower()
        assert "rules" in data_lf
    finally:
        f_crlf_path.unlink(missing_ok=True)
        f_lf_path.unlink(missing_ok=True)


def test_finding_04_release_tuple_strict_vs_candidate():
    """Verify Finding 4: Release verifier fails closed in strict mode when docker is absent and flags candidate mode honestly."""
    # 1. Strict mode fails closed when docker daemon is absent
    with pytest.raises(RuntimeError) as exc_info:
        build_release_tuple(allow_candidate=False, image_tag="nonexistent-image:test")
    assert "Release verification failed" in str(exc_info.value)

    # 2. Candidate mode allows unverified build with explicit status
    tup = build_release_tuple(allow_candidate=True, image_tag="nonexistent-image:test")
    assert tup["release_status"] == "CANDIDATE_UNVERIFIED"
    assert tup["container_image_digest"] == "sha256:candidate_unverified_local"
    assert tup["compatibility"]["code_and_config_compatible"] is True
    assert tup["compatibility"]["database_revision_compatible"] is True


def test_finding_17_concurrent_dedicated_sessions():
    """Verify Finding 17: Concurrent threads using dedicated Sessions correctly fail-closed on duplicate request_id."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    for col in Base.metadata.tables["audit_events"].columns:
        if col.name == "id":
            from sqlalchemy import Integer
            col.type = Integer()
    for table in Base.metadata.tables.values():
        for col in table.columns:
            if col.server_default is not None:
                text_str = str(col.server_default.arg)
                if "N'" in text_str:
                    col.server_default.arg.text = text_str.replace("N'", "'")
    Base.metadata.create_all(engine)

    shared_request_id = f"concurrent-{uuid.uuid4()}"
    evidence = CanonicalEvidence(
        request_id=shared_request_id,
        run_id=f"run-{uuid.uuid4()}",
        timestamp="2026-10-13T12:00:00+00:00",
        code_commit="abcdef0123456789abcdef0123456789abcdef01",
        build_digest="sha256:build_digest",
        input_id="0" * 64,
        input_mode="vector",
        view_map_hash="1" * 64,
        model_hash="2" * 64,
        model_config_hash="3" * 64,
        detector_config_hash="4" * 64,
        seed=42,
        malware_score=0.1,
        signals={"m1": 0.1, "m2": 0.0, "m3": 0.0, "m4": 0.0, "m5": 0.0},
        fusion_score=0.1,
        threshold_id="THRESH-DEFAULT",
        decision="PASS",
        latency_ms={"end_to_end": 1.0},
        demo_mode=True,
    )

    # Initial persist
    with Session(bind=engine) as initial_session:
        repo = CanonicalEvidenceRepository(initial_session)
        repo.persist(evidence)

    # Concurrent worker attempts
    errors: list[Exception] = []
    successes: list[int] = []

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

    assert len(successes) == 0, f"Duplicate was unexpectedly persisted: {successes}"
    assert len(errors) == 4, f"Expected 4 rejections, got {len(errors)}"
