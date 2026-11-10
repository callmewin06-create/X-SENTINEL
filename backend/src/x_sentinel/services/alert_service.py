from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from x_sentinel.api.schemas import AlertSummary
from x_sentinel.config import settings
from x_sentinel.database.models import Alert, AuditEvent
from x_sentinel.database.repositories.alert import AlertRepository
from x_sentinel.security.auth import AuthUser, assert_job_ownership, is_admin


class AlertService:
    """Service layer orchestrating alert retrieval and lifecycle operations."""

    def __init__(self, repository: AlertRepository | None = None):
        self._repository = repository

    def _repo(self, session: Session) -> AlertRepository:
        return self._repository or AlertRepository(session)

    @staticmethod
    def _to_summary(alert: Alert) -> AlertSummary:
        return AlertSummary(
            id=str(alert.id),
            analysis_job_id=str(alert.analysis_job_id),
            severity=alert.severity,
            status=alert.status,
            reason=alert.reason,
            created_at=alert.created_at.isoformat() if alert.created_at else "",
            resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
        )

    def list_alerts(
        self,
        session: Session,
        limit: int = 50,
        offset: int = 0,
        severity: str | None = None,
        status: str | None = None,
        analysis_job_id: str | None = None,
        user: AuthUser | None = None,
    ) -> tuple[list[AlertSummary], int]:
        repo = self._repo(session)
        job_uuid: uuid.UUID | None = None
        if analysis_job_id:
            try:
                job_uuid = uuid.UUID(analysis_job_id)
            except (ValueError, TypeError):
                return [], 0

        filter_user_id: uuid.UUID | None = None
        if user is not None and settings.api_auth_mode != "none" and not is_admin(user):
            filter_user_id = user.user_id

        alerts, total = repo.list_alerts(
            limit=limit,
            offset=offset,
            severity=severity,
            status=status,
            analysis_job_id=job_uuid,
            user_id=filter_user_id,
        )
        return [self._to_summary(a) for a in alerts], total

    def get_alert(
        self,
        session: Session,
        alert_id: str | uuid.UUID,
        user: AuthUser | None = None,
    ) -> AlertSummary | None:
        try:
            parsed_id = alert_id if isinstance(alert_id, uuid.UUID) else uuid.UUID(str(alert_id))
        except (ValueError, TypeError):
            return None

        repo = self._repo(session)
        alert = repo.get_by_id(parsed_id)
        if alert is None:
            return None

        if user is not None and settings.api_auth_mode != "none" and not is_admin(user):
            from x_sentinel.database.models import AnalysisJob
            job = session.get(AnalysisJob, alert.analysis_job_id)
            if job is not None:
                assert_job_ownership(job, user, allow_evaluator=True, resource_label="alert record")

        return self._to_summary(alert)

    def update_alert_status(
        self,
        session: Session,
        alert_id: str | uuid.UUID,
        new_status: str,
        actor_id: uuid.UUID | None = None,
        user: AuthUser | None = None,
    ) -> AlertSummary:
        try:
            parsed_id = alert_id if isinstance(alert_id, uuid.UUID) else uuid.UUID(str(alert_id))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid alert UUID: {alert_id}") from exc

        repo = self._repo(session)
        existing = repo.get_by_id(parsed_id)
        if existing is None:
            raise LookupError(f"Alert '{parsed_id}' not found.")

        if user is not None and settings.api_auth_mode != "none" and not is_admin(user):
            from x_sentinel.database.models import AnalysisJob
            job = session.get(AnalysisJob, existing.analysis_job_id)
            if job is not None:
                assert_job_ownership(job, user, allow_evaluator=False, resource_label="alert record")

        old_status = existing.status
        updated = repo.update_status(parsed_id, new_status)

        # Append audit event for lifecycle transition
        audit_event = AuditEvent(
            request_id=None,
            user_id=actor_id,
            event_type="alert.status_updated",
            entity_type="alert",
            entity_id=str(parsed_id),
            payload={
                "previous_status": old_status,
                "new_status": updated.status,
                "resolved_at": updated.resolved_at.isoformat() if updated.resolved_at else None,
            },
        )
        session.add(audit_event)
        session.commit()

        return self._to_summary(updated)
