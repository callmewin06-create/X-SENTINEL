from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from xsentinel.storage.base import Base

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    normalized_email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255))


class UserRole(Base):
    __tablename__ = "user_roles"
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[str] = mapped_column(String(120), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (UniqueConstraint("name", "version", name="uq_model_versions_name_version"),)


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    model_version_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("model_versions.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", server_default="queued", index=True)
    input_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="vector", server_default="vector")
    input_sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    input_artifact_uri: Mapped[str | None] = mapped_column(Text)
    config_version: Mapped[str | None] = mapped_column(String(128))
    demo_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    error_code: Mapped[str | None] = mapped_column(String(128))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("status IN ('queued','running','completed','failed','quarantined')", name="status_allowed"),
        CheckConstraint("input_mode IN ('vector','raw_pe')", name="input_mode_allowed"),
    )


class AnalysisResultRecord(Base):
    __tablename__ = "analysis_results"
    analysis_job_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("analysis_jobs.id", ondelete="CASCADE"), primary_key=True)
    malware_score: Mapped[float | None] = mapped_column(Float)
    suspicion_score: Mapped[float | None] = mapped_column(Float)
    threshold: Mapped[float | None] = mapped_column(Float)
    decision: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown", server_default="unknown")
    latency_ms: Mapped[float | None] = mapped_column(Float)
    view_contributions: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    result_json: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    evidence_uri: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (CheckConstraint("decision IN ('unknown','pass','alert','quarantine')", name="decision_allowed"),)


class DetectorScore(Base):
    __tablename__ = "detector_scores"
    analysis_job_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("analysis_jobs.id", ondelete="CASCADE"), primary_key=True)
    detector_code: Mapped[str] = mapped_column(String(64), primary_key=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    diagnostics: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (CheckConstraint("detector_code IN ('M1','M2','M3','M4','M5','TADR','STRIP','M3_view_mass','M4_shap_behavioral_conflict','M4_prob_gap','X_primary_reduced','X_primary_full')", name="detector_code_allowed"),)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    analysis_job_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium", server_default="medium")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open", server_default="open", index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("severity IN ('low','medium','high','critical')", name="severity_allowed"),
        CheckConstraint("status IN ('open','acknowledged','resolved','dismissed')", name="alert_status_allowed"),
    )


class Artifact(Base):
    __tablename__ = "artifacts"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    analysis_job_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("analysis_jobs.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    uri: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content_type: Mapped[str | None] = mapped_column(String(255))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    metadata_json: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    request_id: Mapped[str | None] = mapped_column(String(128), index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(128))
    payload: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    experiment_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned", server_default="planned")
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    seed: Mapped[int | None] = mapped_column(Integer)
    results_uri: Mapped[str | None] = mapped_column(Text)
    metrics_json: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("experiment_code IN ('E0','E1','E2','E3','E4','E5')", name="experiment_code_allowed"),
        CheckConstraint("status IN ('planned','running','completed','failed')", name="experiment_status_allowed"),
    )


Index("ix_audit_events_entity", AuditEvent.entity_type, AuditEvent.entity_id)
Index("ix_analysis_jobs_user_created", AnalysisJob.user_id, AnalysisJob.created_at)
Index("ix_artifacts_job_kind", Artifact.analysis_job_id, Artifact.kind)
