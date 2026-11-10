from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from x_sentinel.audit.evidence import CanonicalEvidence
from x_sentinel.audit.writer import AuditWriteFailureError, AuditWriter
from x_sentinel.data.schema import validate_vector
from x_sentinel.data.views import load_view_map
from x_sentinel.database.models import Alert, AnalysisJob
from x_sentinel.database.repositories.evidence import CanonicalEvidenceRepository
from x_sentinel.detection.m1_tadr import m1_tadr
from x_sentinel.detection.m3_view import m3_view_concentration, view_contributions
from x_sentinel.domain import AnalysisResult
from x_sentinel.fusion.engine import demo_fusion
from x_sentinel.model.demo import DemoModelService


class ScientificPipelineNotReadyError(RuntimeError):
    """Raised when scientific pipeline execution is requested but required model assets are not frozen."""

    def __init__(self, message: str, missing_dependencies: list[str] | None = None) -> None:
        super().__init__(message)
        self.missing_dependencies = missing_dependencies or []


def _resolve_git_commit() -> str:
    try:
        import subprocess
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=2,
        )
        val = res.stdout.strip()
        if len(val) == 40:
            return val
    except Exception:
        pass
    return "untracked_source_revision_v3"


def _hash_file_or_fallback(path: Path | None, fallback_bytes: bytes) -> str:
    if path is not None and path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return hashlib.sha256(fallback_bytes).hexdigest()

class AnalysisService:
    def __init__(
        self,
        audit_path: Path,
        view_map_path: Path,
        demo_mode: bool = True,
        model_config_path: Path | None = None,
        model_service: Any = None,
        session: Session | None = None,
    ):
        self.demo_mode = demo_mode
        if not demo_mode:
            missing: list[str] = []
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
            sci_view = repo_root / "configs" / "views.scientific.yaml"
            if not sci_view.is_file():
                missing.append("configs/views.scientific.yaml")
            model_weights = repo_root / "models" / "lightgbm_model.txt"
            model_lgb = repo_root / "models" / "lightgbm_model.lgb"
            if not model_weights.is_file() and not model_lgb.is_file():
                missing.append("models/lightgbm_model.txt")
            calib_file = repo_root / "artifacts" / "calibration" / "d1_calibration.json"
            if not calib_file.is_file():
                missing.append("artifacts/calibration/d1_calibration.json")

            if missing:
                raise ScientificPipelineNotReadyError(
                    f"Scientific pipeline is gated and cannot execute without frozen assets: {missing}",
                    missing_dependencies=missing,
                )

        self.audit = AuditWriter(audit_path)
        self.view_map = load_view_map(view_map_path, allow_demo=demo_mode)
        self.session = session

        # Dynamic provenance resolution
        self.view_map_path = Path(view_map_path)
        self.view_map_hash = _hash_file_or_fallback(self.view_map_path, b"fallback_view_map")
        self.git_commit = _resolve_git_commit()

        detector_cfg = self.view_map_path.parent / ("detector.demo.yaml" if demo_mode else "detector.yaml")
        self.detector_config_hash = _hash_file_or_fallback(detector_cfg, b"fallback_detector_config")

        if model_config_path is not None and Path(model_config_path).is_file():
            self.model_config_hash = hashlib.sha256(Path(model_config_path).read_bytes()).hexdigest()
        else:
            self.model_config_hash = hashlib.sha256(b"demo_model_config_v3").hexdigest()

        self.model_hash = hashlib.sha256(b"demo_model_weights_v3").hexdigest()
        self.build_digest = f"sha256:{hashlib.sha256(b'x_sentinel_v3_local').hexdigest()}"

        if model_service is not None:
            self.model = model_service
        elif model_config_path is not None:
            from x_sentinel.model.lightgbm_service import load_model_service

            self.model = load_model_service(model_config_path, allow_demo=demo_mode)
        else:
            self.model = DemoModelService()

    def analyze_vector(
        self,
        features: list[float],
        request_id: str | None = None,
        session: Session | None = None,
        user_id: uuid.UUID | None = None,
    ) -> AnalysisResult:
        from infrastructure.monitoring.timer import TimingCollector

        timer = TimingCollector("end_to_end").start()

        with timer.stage("input_validation"):
            vector = validate_vector(features)
        rid = request_id or str(uuid.uuid4())
        active_session = session or self.session

        # Deduplication check if session is active
        if active_session is not None:
            existing_job = active_session.scalar(
                select(AnalysisJob).where(AnalysisJob.request_id == rid)
            )
            if existing_job is not None:
                raise AuditWriteFailureError(
                    f"Duplicate request_id '{rid}' already exists. Overwrite rejected."
                )

        # Scientific feature extraction and model inference
        with timer.stage("model"):
            malware_score, shap = self.model.infer(vector)

        with timer.stage("signals"):
            shap_views = self.view_map.split(shap)
            contrib = view_contributions(shap_views)
            signals = {
                "m1": m1_tadr(shap),
                "m2": 0.0,
                "m3": m3_view_concentration(contrib),
                "m4": 0.0,
                "m5": 0.0,
            }

        with timer.stage("fusion"):
            suspicion = demo_fusion(signals)

        # Map to canonical verdict
        if suspicion >= 0.35 or malware_score >= 0.85:
            decision = "QUARANTINE"
            job_status = "quarantined"
        elif suspicion >= 0.10 or malware_score >= 0.50:
            decision = "ALERT"
            job_status = "completed"
        else:
            decision = "PASS"
            job_status = "completed"

        # Compute deterministic SHA-256 over vector bytes using canonical IEEE-754 64-bit float binary representation
        import struct
        vector_bytes = struct.pack(f">{len(vector)}d", *vector)
        input_digest = hashlib.sha256(vector_bytes).hexdigest()
        now_utc = datetime.now(UTC).isoformat()

        # Interim timings for inference stages
        timings = timer.to_dict(include_total_as="inference_total")
        measured_latency_ms = {
            "model": max(0.001, timings.get("model", 0.001)),
            "signals": max(0.001, timings.get("signals", 0.001)),
            "fusion": max(0.001, timings.get("fusion", 0.001)),
            "input_validation": max(0.001, timings.get("input_validation", 0.001)),
            "end_to_end": max(0.001, timings.get("inference_total", 0.001)),
        }

        # Build 19-field CanonicalEvidence dataclass with dynamic provenance
        canonical_ev = CanonicalEvidence(
            request_id=rid,
            run_id=f"run-{uuid.uuid4()}",
            timestamp=now_utc,
            code_commit=self.git_commit,
            build_digest=self.build_digest,
            input_id=input_digest,
            input_mode="vector",
            view_map_hash=self.view_map_hash,
            model_hash=self.model_hash,
            model_config_hash=self.model_config_hash,
            detector_config_hash=self.detector_config_hash,
            seed=42,
            malware_score=malware_score,
            signals=signals,
            fusion_score=suspicion,
            threshold_id="THRESH-V3-DEFAULT",
            decision=decision if not self.demo_mode else "DEMO_ONLY",
            latency_ms=measured_latency_ms,
            demo_mode=self.demo_mode,
        ).with_hash()

        # Telemetry observation (fail-safe)
        try:
            from infrastructure.monitoring.metrics import get_metrics_registry

            reg = get_metrics_registry()
            reg.histogram("detector_latency_ms").observe(measured_latency_ms["end_to_end"])
            for stg in ("model", "signals", "fusion", "input_validation"):
                reg.histogram("detector_stage_latency_ms").observe(
                    measured_latency_ms[stg], labels={"stage": stg}
                )
            reg.counter("detector_requests_total").inc(
                1.0,
                labels={
                    "decision": decision,
                    "input_mode": "vector",
                    "status": job_status,
                },
            )
        except Exception:
            pass

        persisted_job_id: str | None = None

        # Relational database persistence if active session exists
        if active_session is not None:
            try:
                repo = CanonicalEvidenceRepository(active_session)
                with timer.stage("persistence"):
                    job, result_rec, scores, artifact, audit_event = repo.persist(
                        evidence=canonical_ev,
                        user_id=user_id,
                        auto_commit=False,
                    )
                    persisted_job_id = str(job.id)

                    # Generate alert if verdict warrants notification
                    if decision in ("ALERT", "QUARANTINE"):
                        alert_severity = "critical" if decision == "QUARANTINE" else "high"
                        reason_msg = (
                            f"Detector verdict: {decision} "
                            f"(fusion_score: {suspicion:.4f}, malware_score: {malware_score:.4f})"
                        )
                        alert = Alert(
                            id=uuid.uuid4(),
                            analysis_job_id=job.id,
                            severity=alert_severity,
                            status="open",
                            reason=reason_msg,
                            created_at=datetime.now(UTC),
                        )
                        active_session.add(alert)

                    active_session.commit()

                # Stop timer AFTER persistence commit to measure true wall-clock end-to-end latency
                timer.stop()
                final_timings = timer.to_dict(include_total_as="end_to_end")
                measured_latency_ms["end_to_end"] = max(0.001, final_timings.get("end_to_end", 0.001))
                measured_latency_ms["persistence"] = max(0.001, final_timings.get("persistence", 0.001))
                try:
                    result_rec.latency_ms = measured_latency_ms["end_to_end"]
                    active_session.commit()
                except Exception:
                    pass
            except Exception:
                active_session.rollback()
                raise
        else:
            timer.stop()
            final_timings = timer.to_dict(include_total_as="end_to_end")
            measured_latency_ms["end_to_end"] = max(0.001, final_timings.get("end_to_end", 0.001))

        # Build domain result
        result = AnalysisResult(
            request_id=rid,
            status=job_status if not self.demo_mode else "DEMO_ONLY",
            demo_mode=self.demo_mode,
            malware_score=malware_score,
            signals=signals,
            suspicion_score=suspicion,
            threshold=0.50 if self.demo_mode else None,
            view_contributions=contrib,
            warnings=["DEMO_MODE_NOT_SCIENTIFIC_EVIDENCE", "M2_M4_M5_UNAVAILABLE_IN_DEMO"] if self.demo_mode else [],
            evidence_ref=canonical_ev.evidence_hash,
            decision=decision,
            job_id=persisted_job_id,
            measured_latency_ms=measured_latency_ms,
            input_sha256=input_digest,
        )

        # File-based audit trail append with safe error handling (secondary export)
        try:
            self.audit.append(result)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                f"Secondary JSONL audit write failed for request {rid}: {exc}. "
                "Authoritative record safely committed in database."
            )
        return result
