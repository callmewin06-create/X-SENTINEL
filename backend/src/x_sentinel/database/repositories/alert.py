from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from x_sentinel.database.models import Alert


class AlertRepository:
    """Repository for querying, creating, and updating alerts in Microsoft SQL Server."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, alert_id: uuid.UUID) -> Alert | None:
        """Retrieves an alert by its primary UUID key."""
        return self.session.get(Alert, alert_id)

    def add(self, alert: Alert) -> Alert:
        """Persists a new alert record."""
        self.session.add(alert)
        self.session.flush()
        return alert

    def list_alerts(
        self,
        limit: int = 50,
        offset: int = 0,
        severity: str | None = None,
        status: str | None = None,
        analysis_job_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
    ) -> tuple[Sequence[Alert], int]:
        """Lists alerts with filtering and pagination, returning items and total count.

        Guarantees stable ordering by created_at descending.
        """
        conditions = []
        if severity is not None:
            conditions.append(Alert.severity == severity.lower().strip())
        if status is not None:
            conditions.append(Alert.status == status.lower().strip())
        if analysis_job_id is not None:
            conditions.append(Alert.analysis_job_id == analysis_job_id)

        from x_sentinel.database.models import AnalysisJob

        count_stmt = select(func.count(Alert.id))
        stmt = select(Alert).order_by(desc(Alert.created_at)).limit(limit).offset(offset)

        if user_id is not None:
            count_stmt = count_stmt.join(AnalysisJob, Alert.analysis_job_id == AnalysisJob.id).where(
                AnalysisJob.user_id == user_id
            )
            stmt = stmt.join(AnalysisJob, Alert.analysis_job_id == AnalysisJob.id).where(
                AnalysisJob.user_id == user_id
            )

        if conditions:
            count_stmt = count_stmt.where(*conditions)
            stmt = stmt.where(*conditions)
        total = self.session.scalar(count_stmt) or 0
        items = self.session.scalars(stmt).all()

        return items, int(total)

    def update_status(self, alert_id: uuid.UUID, new_status: str) -> Alert:
        """Updates alert lifecycle state, enforcing state transition validity.

        Allowed statuses: open, acknowledged, resolved, dismissed.
        Terminal states (resolved, dismissed) reject transitions to prevent invalid mutation.
        """
        alert = self.session.get(Alert, alert_id)
        if alert is None:
            raise ValueError(f"Alert '{alert_id}' not found.")

        target_status = new_status.lower().strip()
        valid_statuses = {"open", "acknowledged", "resolved", "dismissed"}
        if target_status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{target_status}'. Must be one of {sorted(valid_statuses)}."
            )

        # Enforce lifecycle transition invariants
        if alert.status in {"resolved", "dismissed"} and target_status != alert.status:
            raise ValueError(
                f"Cannot transition alert from terminal '{alert.status}' to '{target_status}'."
            )

        alert.status = target_status
        if target_status in {"resolved", "dismissed"}:
            alert.resolved_at = datetime.now(UTC)
        elif target_status in {"open", "acknowledged"}:
            alert.resolved_at = None

        self.session.flush()
        return alert
