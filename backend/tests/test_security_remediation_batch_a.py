from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from x_sentinel.api.schemas import AlertStatusUpdateRequest
from x_sentinel.config import settings
from x_sentinel.database.base import Base
from x_sentinel.database.models import Alert, AnalysisJob, User
from x_sentinel.database.session import get_db
from x_sentinel.main import app
from x_sentinel.security.auth import (
    ANONYMOUS_USER,
    AuthUser,
    Role,
    get_current_user,
    get_current_user_optional,
    is_admin,
)

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def test_db() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    for table in Base.metadata.tables.values():
        for col in table.columns:
            if table.name == "audit_events" and col.name == "id":
                from sqlalchemy import Integer

                col.type = Integer()
            if col.server_default is not None and "N'" in str(col.server_default.arg):
                col.server_default.arg.text = str(col.server_default.arg).replace("N'", "'")
    Base.metadata.create_all(engine)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_is_admin_none_never_admin() -> None:
    """is_admin(None) must ALWAYS return False regardless of environment or auth mode."""
    with patch.object(settings, "api_auth_mode", "none"):
        assert is_admin(None) is False
    with patch.object(settings, "api_auth_mode", "bearer"):
        assert is_admin(None) is False
    with patch.object(settings, "env", "production"):
        assert is_admin(None) is False


def test_production_mode_rejects_anonymous_and_predefined_tokens() -> None:
    """In production: anonymous cannot be admin, and predefined dev tokens are rejected."""
    with patch.object(settings, "env", "production"):
        # 1. ANONYMOUS_USER is not admin in production
        assert is_admin(ANONYMOUS_USER) is False

        # 2. Predefined token in production raises 401
        with patch.object(settings, "api_auth_mode", "bearer"):
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token-admin")
            with pytest.raises(Exception) as exc_info:
                get_current_user(creds)
            assert "401" in str(exc_info.value) or exc_info.value.status_code == 401

            # get_current_user_optional also raises 401 for predefined token in production
            with pytest.raises(Exception) as exc_info:
                get_current_user_optional(creds)
            assert "401" in str(exc_info.value) or exc_info.value.status_code == 401


def test_production_mode_configured_token_accepted() -> None:
    """In production mode, tokens explicitly configured via settings.api_tokens are accepted."""
    custom_user_id = uuid.uuid4()
    custom_tokens = {
        "prod-secure-token-123": {
            "user_id": str(custom_user_id),
            "email": "analyst@company.prod",
            "roles": [Role.ANALYST.value],
            "is_active": True,
        }
    }
    with patch.object(settings, "env", "production"):
        with patch.object(settings, "api_auth_mode", "bearer"):
            with patch.object(settings, "api_tokens", custom_tokens):
                creds = HTTPAuthorizationCredentials(
                    scheme="Bearer", credentials="prod-secure-token-123"
                )
                user = get_current_user(creds)
                assert user.user_id == custom_user_id
                assert user.email == "analyst@company.prod"
                assert user.has_role(Role.ANALYST.value)
                assert is_admin(user) is False


def test_alert_ownership_idor_remediation(test_db: Session) -> None:
    """Analyst B cannot view or update Alert belonging to Analyst A's analysis job."""

    def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db
    try:
        user_a_id = uuid.UUID("22222222-2222-2222-2222-222222222222")  # token-analyst
        user_b_id = uuid.UUID("55555555-5555-5555-5555-555555555555")  # token-analyst-2

        user_a = User(
            id=user_a_id, email="analyst_a@example.com", normalized_email="analyst_a@example.com"
        )
        user_b = User(
            id=user_b_id, email="analyst_b@example.com", normalized_email="analyst_b@example.com"
        )
        test_db.add_all([user_a, user_b])
        test_db.flush()

        # Job owned by Analyst A
        job_a = AnalysisJob(
            id=uuid.uuid4(),
            request_id="req-job-owner-a",
            user_id=user_a_id,
            input_mode="vector",
            status="completed",
            demo_mode=True,
        )
        test_db.add(job_a)
        test_db.flush()

        # Alert linked to Analyst A's job
        alert_a = Alert(
            id=uuid.uuid4(),
            analysis_job_id=job_a.id,
            severity="high",
            status="open",
            reason="High suspicion backdoor signal",
        )
        test_db.add(alert_a)
        test_db.commit()

        with patch.object(settings, "api_auth_mode", "bearer"):
            headers_b = {"Authorization": "Bearer token-analyst-2"}
            headers_admin = {"Authorization": "Bearer token-admin"}

            # 1. Analyst B listing alerts for Analyst A's job should return 0 items
            resp_list = client.get(
                "/v1/alerts",
                headers=headers_b,
                params={"analysis_job_id": str(job_a.id)},
            )
            assert resp_list.status_code == 200
            assert resp_list.json()["total"] == 0
            assert len(resp_list.json()["items"]) == 0

            # 2. Analyst B getting alert detail for Alert A -> 403 Forbidden (IDOR prevented!)
            resp_detail = client.get(f"/v1/alerts/{alert_a.id}", headers=headers_b)
            assert resp_detail.status_code == 403
            assert resp_detail.json()["detail"]["code"] == "XS_FORBIDDEN"

            # 3. Analyst B patching alert status -> 403 Forbidden (IDOR prevented!)
            resp_patch = client.patch(
                f"/v1/alerts/{alert_a.id}",
                headers=headers_b,
                json={"status": "acknowledged"},
            )
            assert resp_patch.status_code == 403
            assert resp_patch.json()["detail"]["code"] == "XS_FORBIDDEN"

            # 4. Administrator CAN view and patch Alert A
            resp_admin_detail = client.get(f"/v1/alerts/{alert_a.id}", headers=headers_admin)
            assert resp_admin_detail.status_code == 200

            resp_admin_patch = client.patch(
                f"/v1/alerts/{alert_a.id}",
                headers=headers_admin,
                json={"status": "acknowledged"},
            )
            assert resp_admin_patch.status_code == 200
            assert resp_admin_patch.json()["status"] == "acknowledged"

    finally:
        app.dependency_overrides.clear()
