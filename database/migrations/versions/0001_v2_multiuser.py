"""X-SENTINEL V2 multi-user initial schema.

Revision ID: 0001_v2_multiuser
Revises: None
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_v2_multiuser"
down_revision = None
branch_labels = None
depends_on = None

JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("normalized_email", sa.String(320), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("normalized_email", name="uq_users_normalized_email"),
    )
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )
    op.create_table(
        "model_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("version", sa.String(120), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.Column("metadata_json", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_model_versions"),
        sa.UniqueConstraint("name", "version", name="uq_model_versions_name_version"),
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name="fk_user_roles_role_id_roles", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_roles_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id", name="pk_user_roles"),
    )
    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.String(128), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("model_version_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(32), server_default="queued", nullable=False),
        sa.Column("input_mode", sa.String(32), server_default="vector", nullable=False),
        sa.Column("input_sha256", sa.String(64), nullable=True),
        sa.Column("input_artifact_uri", sa.Text(), nullable=True),
        sa.Column("config_version", sa.String(128), nullable=True),
        sa.Column("demo_mode", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("error_code", sa.String(128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('queued','running','completed','failed','quarantined')", name="ck_analysis_jobs_status_allowed"),
        sa.CheckConstraint("input_mode IN ('vector','raw_pe')", name="ck_analysis_jobs_input_mode_allowed"),
        sa.ForeignKeyConstraint(["model_version_id"], ["model_versions.id"], name="fk_analysis_jobs_model_version_id_model_versions", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_analysis_jobs_user_id_users", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_analysis_jobs"),
        sa.UniqueConstraint("request_id", name="uq_analysis_jobs_request_id"),
    )
    op.create_index("ix_analysis_jobs_created_at", "analysis_jobs", ["created_at"])
    op.create_index("ix_analysis_jobs_input_sha256", "analysis_jobs", ["input_sha256"])
    op.create_index("ix_analysis_jobs_model_version_id", "analysis_jobs", ["model_version_id"])
    op.create_index("ix_analysis_jobs_status", "analysis_jobs", ["status"])
    op.create_index("ix_analysis_jobs_user_id", "analysis_jobs", ["user_id"])
    op.create_index("ix_analysis_jobs_user_created", "analysis_jobs", ["user_id", "created_at"])

    op.create_table(
        "analysis_results",
        sa.Column("analysis_job_id", sa.Uuid(), nullable=False),
        sa.Column("malware_score", sa.Float(), nullable=True),
        sa.Column("suspicion_score", sa.Float(), nullable=True),
        sa.Column("threshold", sa.Float(), nullable=True),
        sa.Column("decision", sa.String(32), server_default="unknown", nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("view_contributions", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("result_json", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence_uri", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("decision IN ('unknown','pass','alert','quarantine')", name="ck_analysis_results_decision_allowed"),
        sa.ForeignKeyConstraint(["analysis_job_id"], ["analysis_jobs.id"], name="fk_analysis_results_analysis_job_id_analysis_jobs", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("analysis_job_id", name="pk_analysis_results"),
    )
    op.create_table(
        "detector_scores",
        sa.Column("analysis_job_id", sa.Uuid(), nullable=False),
        sa.Column("detector_code", sa.String(16), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("diagnostics", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("detector_code IN ('M1','M2','M3','M4','M5')", name="ck_detector_scores_detector_code_allowed"),
        sa.ForeignKeyConstraint(["analysis_job_id"], ["analysis_jobs.id"], name="fk_detector_scores_analysis_job_id_analysis_jobs", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("analysis_job_id", "detector_code", name="pk_detector_scores"),
    )
    op.create_table(
        "alerts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_job_id", sa.Uuid(), nullable=False),
        sa.Column("severity", sa.String(16), server_default="medium", nullable=False),
        sa.Column("status", sa.String(32), server_default="open", nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("severity IN ('low','medium','high','critical')", name="ck_alerts_severity_allowed"),
        sa.CheckConstraint("status IN ('open','acknowledged','resolved','dismissed')", name="ck_alerts_alert_status_allowed"),
        sa.ForeignKeyConstraint(["analysis_job_id"], ["analysis_jobs.id"], name="fk_alerts_analysis_job_id_analysis_jobs", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_alerts"),
    )
    op.create_index("ix_alerts_analysis_job_id", "alerts", ["analysis_job_id"])
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_table(
        "artifacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_job_id", sa.Uuid(), nullable=True),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("uri", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("content_type", sa.String(255), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("metadata_json", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["analysis_job_id"], ["analysis_jobs.id"], name="fk_artifacts_analysis_job_id_analysis_jobs", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_artifacts"),
    )
    op.create_index("ix_artifacts_analysis_job_id", "artifacts", ["analysis_job_id"])
    op.create_index("ix_artifacts_kind", "artifacts", ["kind"])
    op.create_index("ix_artifacts_sha256", "artifacts", ["sha256"])
    op.create_index("ix_artifacts_job_kind", "artifacts", ["analysis_job_id", "kind"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("request_id", sa.String(128), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=True),
        sa.Column("entity_id", sa.String(128), nullable=True),
        sa.Column("payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_audit_events_user_id_users", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_audit_events"),
    )
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_request_id", "audit_events", ["request_id"])
    op.create_index("ix_audit_events_user_id", "audit_events", ["user_id"])
    op.create_index("ix_audit_events_entity", "audit_events", ["entity_type", "entity_id"])
    op.create_table(
        "experiment_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("experiment_code", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), server_default="planned", nullable=False),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=True),
        sa.Column("results_uri", sa.Text(), nullable=True),
        sa.Column("metrics_json", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("experiment_code IN ('E0','E1','E2','E3','E4','E5')", name="ck_experiment_runs_experiment_code_allowed"),
        sa.CheckConstraint("status IN ('planned','running','completed','failed')", name="ck_experiment_runs_experiment_status_allowed"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_experiment_runs_created_by_user_id_users", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_experiment_runs"),
    )
    op.create_index("ix_experiment_runs_created_by_user_id", "experiment_runs", ["created_by_user_id"])
    op.create_index("ix_experiment_runs_experiment_code", "experiment_runs", ["experiment_code"])

    # Audit is append-only at the application-policy layer. DELETE/UPDATE permissions should be denied in production.
    op.execute("INSERT INTO roles (code, description) VALUES ('admin','System administrator'), ('analyst','SOC / analysis user'), ('evaluator','Blind evaluation role') ON CONFLICT (code) DO NOTHING")


def downgrade() -> None:
    op.drop_table("experiment_runs")
    op.drop_table("audit_events")
    op.drop_table("artifacts")
    op.drop_table("alerts")
    op.drop_table("detector_scores")
    op.drop_table("analysis_results")
    op.drop_table("analysis_jobs")
    op.drop_table("user_roles")
    op.drop_table("model_versions")
    op.drop_table("roles")
    op.drop_table("users")
