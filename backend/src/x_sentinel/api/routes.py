# ruff: noqa: B008
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from x_sentinel.api.schemas import (
    AlertListResponse,
    AlertStatusUpdateRequest,
    AlertSummary,
    AnalysisDetailResponse,
    AnalysisHistoryListResponse,
    AnalysisResponse,
    CanonicalEvidenceResponse,
    JevAIRunListResponse,
    JevAIRunResponse,
    JevExplainRequest,
    JevFeedbackListResponse,
    JevFeedbackRequest,
    JevFeedbackResponse,
    VectorAnalysisRequest,
)
from x_sentinel.audit.evidence import EvidenceIntegrityError
from x_sentinel.audit.writer import AuditWriteFailureError
from x_sentinel.config import settings
from x_sentinel.data.schema import VectorValidationError
from x_sentinel.database.models import JevAIFeedback, JevAIRun
from x_sentinel.database.session import get_db
from x_sentinel.jev_ai.client import JevAIClient
from x_sentinel.jev_ai.orchestrator import JevAIOrchestrator
from x_sentinel.jev_ai.schemas import JevStatusResponse
from x_sentinel.jev_ai.status import get_jev_status
from x_sentinel.security.auth import (
    AuthUser,
    Role,
    ensure_persisted_user,
    require_roles,
)
from x_sentinel.services.alert_service import AlertService
from x_sentinel.services.analysis_service import AnalysisService
from x_sentinel.services.evidence_service import EvidenceService
from x_sentinel.services.history_service import HistoryService
from x_sentinel.services.jev_ai_service import JevAIService, JevAIServiceError

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependencies & Service Instantiation
# ---------------------------------------------------------------------------


def get_analysis_service(db: Session = Depends(get_db)) -> AnalysisService:
    view_name = "views.demo.yaml" if settings.demo_mode else "views.scientific.yaml"
    return AnalysisService(
        audit_path=settings.audit_log_path,
        view_map_path=settings.config_dir / view_name,
        demo_mode=settings.demo_mode,
        session=db,
    )


def get_history_service() -> HistoryService:
    return HistoryService()


def get_alert_service() -> AlertService:
    return AlertService()


def get_evidence_service() -> EvidenceService:
    return EvidenceService()


def get_jev_orchestrator() -> JevAIOrchestrator:
    client = JevAIClient.from_settings(settings)
    return JevAIOrchestrator(
        client=client,
        max_context_chars=settings.jev_ai_max_context_chars,
    )


def get_jev_ai_service() -> JevAIService:
    return JevAIService()


def _to_jev_run_response(run: JevAIRun) -> JevAIRunResponse:
    summary = dict(run.context_summary) if isinstance(run.context_summary, dict) else {}
    decision_res = summary.get("decision_result")
    return JevAIRunResponse(
        id=str(run.id),
        analysis_job_id=str(run.analysis_job_id) if run.analysis_job_id else None,
        requested_by_user_id=(str(run.requested_by_user_id) if run.requested_by_user_id else None),
        mode=run.mode,  # type: ignore[arg-type]
        status=run.status,  # type: ignore[arg-type]
        advisory_only=True,
        authoritative_decision_unchanged=True,
        model_id=run.model_id,
        endpoint_label=run.endpoint_label,
        prompt_version=run.prompt_version,
        input_digest_sha256=run.input_digest_sha256,
        output_digest_sha256=run.output_digest_sha256,
        context_summary=summary,
        response_text=run.response_text,
        decision_result=decision_res if isinstance(decision_res, dict) else None,
        latency_ms=run.latency_ms,
        error_code=run.error_code,
        error_message=run.error_message,
        created_at=run.created_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
    )


def _to_jev_feedback_response(fb: JevAIFeedback) -> JevFeedbackResponse:
    return JevFeedbackResponse(
        id=str(fb.id),
        jev_ai_run_id=str(fb.jev_ai_run_id),
        user_id=str(fb.user_id) if fb.user_id else None,
        rating=fb.rating,
        label=fb.label,  # type: ignore[arg-type]
        comment=fb.comment,
        advisory_only=True,
        created_at=fb.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Jev AI Status
# ---------------------------------------------------------------------------


@router.get(
    "/v1/ai/status",
    response_model=JevStatusResponse,
    tags=["AI Advisory"],
    summary="Get Jev AI LM Studio status",
)
def ai_status() -> JevStatusResponse:
    return get_jev_status()


# ---------------------------------------------------------------------------
# Core Analysis Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/v1/analyze/vector",
    response_model=AnalysisResponse,
    tags=["Analysis"],
    summary="Analyze a 2,381-feature EMBER vector",
)
def analyze_vector(
    req: VectorAnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(
        require_roles(Role.ADMIN.value, Role.ANALYST.value, Role.OPERATOR.value)
    ),
) -> AnalysisResponse:
    from infrastructure.monitoring.concurrency import (
        ConcurrencyLimitExceededError,
        get_detector_limiter,
    )

    detector_limiter = get_detector_limiter()
    try:
        with detector_limiter.acquire():
            persisted_user_id = ensure_persisted_user(db, user)

            result = service.analyze_vector(
                features=req.features,
                request_id=req.request_id,
                session=db,
                user_id=persisted_user_id,
            )
            return AnalysisResponse(**result.__dict__)
    except ConcurrencyLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "XS_DETECTOR_OVERLOADED", "message": str(exc)},
        ) from exc
    except VectorValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "XS_INPUT_INVALID", "message": str(exc)},
        ) from exc
    except AuditWriteFailureError as exc:
        msg = str(exc)
        if "Duplicate request_id" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "XS_DUPLICATE_REQUEST", "message": msg},
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "XS_AUDIT_WRITE_FAILED", "message": msg},
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "XS_CONFIG_UNRESOLVED", "message": str(exc)},
        ) from exc


@router.post(
    "/v1/analyze/file",
    tags=["Analysis"],
    summary="Analyze uploaded binary file (Phase 2 Gated)",
)
def analyze_file() -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={"code": "XS_FEATURE_DISABLED", "message": "raw PE/LIEF is Phase 2"},
    )


# ---------------------------------------------------------------------------
# Analysis History Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/v1/analysis",
    response_model=AnalysisHistoryListResponse,
    tags=["History"],
    summary="List analysis history with pagination and filtering",
)
def list_analysis_history(
    limit: int = Query(default=50, ge=1, le=1000, description="Page limit"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
    status_filter: str | None = Query(
        default=None, alias="status", description="Filter by job status"
    ),
    decision: str | None = Query(
        default=None, description="Filter by decision: pass, alert, quarantine"
    ),
    input_mode: str | None = Query(
        default=None, description="Filter by input mode: vector, raw_pe"
    ),
    demo_mode: bool | None = Query(default=None, description="Filter by demo_mode"),
    db: Session = Depends(get_db),
    history_svc: HistoryService = Depends(get_history_service),
    user: AuthUser = Depends(
        require_roles(
            Role.ADMIN.value, Role.ANALYST.value, Role.EVALUATOR.value, Role.OPERATOR.value
        )
    ),
) -> AnalysisHistoryListResponse:
    items, total = history_svc.list_history(
        session=db,
        limit=limit,
        offset=offset,
        status=status_filter,
        decision=decision,
        input_mode=input_mode,
        demo_mode=demo_mode,
        user=user,
    )
    return AnalysisHistoryListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/v1/analysis/{analysis_id}",
    response_model=AnalysisDetailResponse,
    tags=["History"],
    summary="Get detailed analysis result by UUID or request_id",
)
def get_analysis_detail(
    analysis_id: str,
    db: Session = Depends(get_db),
    history_svc: HistoryService = Depends(get_history_service),
    user: AuthUser = Depends(
        require_roles(
            Role.ADMIN.value, Role.ANALYST.value, Role.EVALUATOR.value, Role.OPERATOR.value
        )
    ),
) -> AnalysisDetailResponse:
    detail = history_svc.get_analysis_detail(session=db, identifier=analysis_id, user=user)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "XS_ANALYSIS_NOT_FOUND",
                "message": f"Analysis '{analysis_id}' not found.",
            },
        )
    return detail


# ---------------------------------------------------------------------------
# Canonical Evidence Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/v1/analysis/{analysis_id}/evidence",
    response_model=CanonicalEvidenceResponse,
    tags=["Evidence"],
    summary="Get verified canonical evidence for an analysis",
)
def get_analysis_evidence(
    analysis_id: str,
    db: Session = Depends(get_db),
    evidence_svc: EvidenceService = Depends(get_evidence_service),
    user: AuthUser = Depends(
        require_roles(Role.ADMIN.value, Role.ANALYST.value, Role.EVALUATOR.value)
    ),
) -> CanonicalEvidenceResponse:
    try:
        evidence = evidence_svc.get_canonical_evidence(
            session=db, identifier=analysis_id, user=user
        )
    except EvidenceIntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "XS_EVIDENCE_INTEGRITY_MISMATCH", "message": str(exc)},
        ) from exc

    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "XS_EVIDENCE_NOT_FOUND",
                "message": f"Evidence for analysis '{analysis_id}' not found.",
            },
        )

    return evidence_svc.to_response(evidence)


# ---------------------------------------------------------------------------
# Alerts Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/v1/alerts",
    response_model=AlertListResponse,
    tags=["Alerts"],
    summary="List alerts with filtering and pagination",
)
def list_alerts(
    limit: int = Query(default=50, ge=1, le=1000, description="Query limit"),
    offset: int = Query(default=0, ge=0, description="Query offset"),
    severity: str | None = Query(
        default=None, description="Filter by severity: low, medium, high, critical"
    ),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter by status: open, acknowledged, resolved, dismissed",
    ),
    analysis_job_id: str | None = Query(
        default=None, description="Filter by associated analysis job UUID"
    ),
    db: Session = Depends(get_db),
    alert_svc: AlertService = Depends(get_alert_service),
    user: AuthUser = Depends(
        require_roles(Role.ADMIN.value, Role.ANALYST.value, Role.OPERATOR.value)
    ),
) -> AlertListResponse:
    items, total = alert_svc.list_alerts(
        session=db,
        limit=limit,
        offset=offset,
        severity=severity,
        status=status_filter,
        analysis_job_id=analysis_job_id,
        user=user,
    )
    return AlertListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/v1/alerts/{alert_id}",
    response_model=AlertSummary,
    tags=["Alerts"],
    summary="Get alert details by UUID",
)
def get_alert_detail(
    alert_id: str,
    db: Session = Depends(get_db),
    alert_svc: AlertService = Depends(get_alert_service),
    user: AuthUser = Depends(
        require_roles(Role.ADMIN.value, Role.ANALYST.value, Role.OPERATOR.value)
    ),
) -> AlertSummary:
    alert = alert_svc.get_alert(session=db, alert_id=alert_id, user=user)
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "XS_ALERT_NOT_FOUND", "message": f"Alert '{alert_id}' not found."},
        )
    return alert


@router.patch(
    "/v1/alerts/{alert_id}",
    response_model=AlertSummary,
    tags=["Alerts"],
    summary="Update alert lifecycle state",
)
def update_alert_status(
    alert_id: str,
    req: AlertStatusUpdateRequest,
    db: Session = Depends(get_db),
    alert_svc: AlertService = Depends(get_alert_service),
    user: AuthUser = Depends(require_roles(Role.ADMIN.value, Role.ANALYST.value)),
) -> AlertSummary:
    try:
        persisted_actor_id = ensure_persisted_user(db, user)

        updated = alert_svc.update_alert_status(
            session=db,
            alert_id=alert_id,
            new_status=req.status,
            actor_id=persisted_actor_id,
            user=user,
        )
        return updated
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "XS_ALERT_NOT_FOUND", "message": str(exc)},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "XS_INVALID_TRANSITION", "message": str(exc)},
        ) from exc


# ---------------------------------------------------------------------------
# Jev AI Workflows, Runs & Feedback Endpoints (PLAN-BE-13)
# ---------------------------------------------------------------------------


@router.post(
    "/v1/ai/explain",
    response_model=JevAIRunResponse,
    tags=["AI Advisory"],
    summary="Execute Jev AI advisory workflow (explain, triage, compare, report)",
)
def execute_jev_ai_workflow(
    req: JevExplainRequest,
    request: Request,
    db: Session = Depends(get_db),
    jev_svc: JevAIService = Depends(get_jev_ai_service),
    user: AuthUser = Depends(require_roles(Role.ADMIN.value, Role.ANALYST.value)),
) -> JevAIRunResponse:
    override = request.app.dependency_overrides.get(get_jev_orchestrator)
    orchestrator = override() if override is not None else get_jev_orchestrator()
    try:
        run = jev_svc.execute_workflow(
            session=db,
            orchestrator=orchestrator,
            analysis_id=req.analysis_id,
            mode=req.mode,
            compare_with_analysis_id=req.compare_with_analysis_id,
            focus_signals=list(req.focus_signals) if req.focus_signals else None,
            question=req.question,
            user=user,
        )
        return _to_jev_run_response(run)
    except JevAIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_detail()) from exc


@router.get(
    "/v1/ai/runs",
    response_model=JevAIRunListResponse,
    tags=["AI Advisory"],
    summary="List persisted Jev AI advisory runs",
)
def list_jev_ai_runs(
    analysis_id: str | None = Query(
        default=None, description="Filter by analysis job UUID or request_id"
    ),
    mode: Literal["explain", "triage", "compare", "report", "docs"] | None = Query(
        default=None, description="Filter by workflow mode"
    ),
    status_filter: Literal["queued", "running", "completed", "failed", "blocked"] | None = Query(
        default=None, alias="status", description="Filter by run status"
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Page limit"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
    db: Session = Depends(get_db),
    jev_svc: JevAIService = Depends(get_jev_ai_service),
    user: AuthUser = Depends(require_roles(Role.ADMIN.value, Role.ANALYST.value)),
) -> JevAIRunListResponse:
    try:
        runs, total = jev_svc.list_runs(
            session=db,
            analysis_id=analysis_id,
            mode=mode,
            status=status_filter,
            limit=limit,
            offset=offset,
            user=user,
        )
        return JevAIRunListResponse(
            items=[_to_jev_run_response(r) for r in runs],
            total=total,
            limit=limit,
            offset=offset,
        )
    except JevAIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_detail()) from exc


@router.get(
    "/v1/ai/runs/{run_id}",
    response_model=JevAIRunResponse,
    tags=["AI Advisory"],
    summary="Get persisted Jev AI run by UUID",
)
def get_jev_ai_run(
    run_id: str,
    db: Session = Depends(get_db),
    jev_svc: JevAIService = Depends(get_jev_ai_service),
    user: AuthUser = Depends(require_roles(Role.ADMIN.value, Role.ANALYST.value)),
) -> JevAIRunResponse:
    try:
        run = jev_svc.get_run(session=db, run_id=run_id, user=user)
        return _to_jev_run_response(run)
    except JevAIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_detail()) from exc


@router.post(
    "/v1/ai/runs/{run_id}/feedback",
    response_model=JevFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["AI Advisory"],
    summary="Record analyst feedback for a terminal Jev AI run",
)
def create_jev_ai_feedback(
    run_id: str,
    req: JevFeedbackRequest,
    db: Session = Depends(get_db),
    jev_svc: JevAIService = Depends(get_jev_ai_service),
    user: AuthUser = Depends(require_roles(Role.ADMIN.value, Role.ANALYST.value)),
) -> JevFeedbackResponse:
    try:
        fb = jev_svc.submit_feedback(
            session=db,
            run_id=run_id,
            rating=req.rating,
            label=req.label,
            comment=req.comment,
            user=user,
        )
        return _to_jev_feedback_response(fb)
    except JevAIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_detail()) from exc


@router.get(
    "/v1/ai/runs/{run_id}/feedback",
    response_model=JevFeedbackListResponse,
    tags=["AI Advisory"],
    summary="List analyst feedback records for a Jev AI run",
)
def list_jev_ai_feedback(
    run_id: str,
    db: Session = Depends(get_db),
    jev_svc: JevAIService = Depends(get_jev_ai_service),
    user: AuthUser = Depends(require_roles(Role.ADMIN.value, Role.ANALYST.value)),
) -> JevFeedbackListResponse:
    try:
        run, fb_list = jev_svc.list_feedback(session=db, run_id=run_id, user=user)
        return JevFeedbackListResponse(
            jev_ai_run_id=str(run.id),
            total=len(fb_list),
            items=[_to_jev_feedback_response(f) for f in fb_list],
        )
    except JevAIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.to_detail()) from exc


@router.post(
    "/v1/ai/docs/ask",
    tags=["AI Advisory"],
    summary="Documentation QA over repository docs (Phase 2 Gated)",
)
def ask_jev_ai_docs(
    user: AuthUser = Depends(require_roles(Role.ADMIN.value, Role.ANALYST.value)),
) -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "code": "XS_FEATURE_DISABLED",
            "message": "Documentation QA (/v1/ai/docs/ask) is gated for Phase 2",
            "advisory_only": True,
        },
    )


# ---------------------------------------------------------------------------
# System Observability & Telemetry Endpoints (PLAN-BE-17)
# ---------------------------------------------------------------------------


@router.get(
    "/v1/system/metrics",
    tags=["System"],
    summary="Get Prometheus exposition metrics for system observability",
    include_in_schema=False,
)
def get_prometheus_metrics(
    user: AuthUser = Depends(
        require_roles(Role.ADMIN.value, Role.OPERATOR.value)
    ),
) -> Response:
    if not settings.metrics_export_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "XS_FEATURE_DISABLED", "message": "Metrics export is disabled in configuration"},
        )

    from infrastructure.monitoring.metrics import get_metrics_registry

    reg = get_metrics_registry()
    content = reg.generate_prometheus_text()
    return Response(content=content, media_type="text/plain; version=0.0.4; charset=utf-8")


@router.get(
    "/v1/system/telemetry",
    tags=["System"],
    summary="Get authentic hardware, memory, and process telemetry via psutil",
    include_in_schema=False,
)
def get_system_telemetry(
    user: AuthUser = Depends(
        require_roles(Role.ADMIN.value, Role.OPERATOR.value)
    ),
) -> dict[str, object]:
    if not settings.performance_monitoring_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "XS_FEATURE_DISABLED", "message": "Performance monitoring is disabled in configuration"},
        )

    from infrastructure.monitoring.telemetry import collect_system_telemetry

    return collect_system_telemetry()

