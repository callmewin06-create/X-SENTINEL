from __future__ import annotations

import time

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from x_sentinel.api.routes import router
from x_sentinel.config import settings
from x_sentinel.database.health import database_health
from x_sentinel.jev_ai.status import get_jev_status
from x_sentinel.services.analysis_service import ScientificPipelineNotReadyError

app = FastAPI(title="X-SENTINEL", version="0.3.0-baseline-v3")


@app.middleware("http")
async def performance_metrics_middleware(request: Request, call_next):
    start_ns = time.perf_counter_ns()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        elapsed_ms = max(0.001, (time.perf_counter_ns() - start_ns) / 1_000_000.0)
        try:
            from infrastructure.monitoring.metrics import get_metrics_registry

            reg = get_metrics_registry()
            # Bound metrics endpoint cardinality (Finding 9)
            route = request.scope.get("route")
            if route is not None and hasattr(route, "path"):
                ep = getattr(route, "path", "unmatched")
            else:
                raw_path = request.url.path
                if raw_path.startswith("/v1/analysis/") and raw_path.endswith("/evidence"):
                    ep = "/v1/analysis/{id}/evidence"
                elif raw_path.startswith("/v1/analysis/") and len(raw_path.split("/")) == 4:
                    ep = "/v1/analysis/{id}"
                elif raw_path.startswith("/v1/alerts/") and len(raw_path.split("/")) == 4:
                    ep = "/v1/alerts/{id}"
                elif raw_path.startswith("/v1/ai/runs/") and raw_path.endswith("/feedback"):
                    ep = "/v1/ai/runs/{id}/feedback"
                elif raw_path.startswith("/v1/ai/runs/") and len(raw_path.split("/")) == 5:
                    ep = "/v1/ai/runs/{id}"
                elif raw_path in (
                    "/health",
                    "/livez",
                    "/ready",
                    "/readyz",
                    "/metrics",
                    "/v1/analyze/vector",
                    "/v1/analysis",
                    "/v1/alerts",
                    "/v1/ai/status",
                    "/v1/ai/runs",
                ):
                    ep = raw_path
                else:
                    ep = "unmatched"

            reg.histogram("api_request_latency_ms").observe(
                elapsed_ms,
                labels={
                    "method": request.method,
                    "endpoint": ep,
                    "status_code": str(status_code),
                },
            )
            reg.counter("api_requests_total").inc(
                1.0,
                labels={
                    "method": request.method,
                    "endpoint": ep,
                    "status_code": str(status_code),
                },
            )
        except Exception:
            pass


app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",") if o.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "X-Request-ID", "Authorization"],
)
app.include_router(router)



@app.exception_handler(ScientificPipelineNotReadyError)
def handle_scientific_pipeline_not_ready(request: Request, exc: ScientificPipelineNotReadyError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": {
                "code": "SCIENTIFIC_PIPELINE_NOT_READY",
                "message": str(exc),
                "missing_dependencies": getattr(exc, "missing_dependencies", []),
            }
        },
    )


@app.exception_handler(RequestValidationError)
def handle_request_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    path = request.url.path
    code = "XS_FEEDBACK_INVALID" if path.endswith("/feedback") else "XS_INPUT_INVALID"
    first_msg = "Request payload validation failed"
    errors = exc.errors()
    if errors and isinstance(errors[0], dict):
        first_msg = str(errors[0].get("msg", first_msg))
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "code": code,
                "message": first_msg,
            }
        },
    )


@app.get("/health", tags=["System"])
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "x-sentinel",
        "version": "v3",
        "demo_mode": settings.demo_mode,
        "jev_ai_enabled": settings.jev_ai_enabled,
    }


@app.get("/ready", tags=["System"])
def ready() -> JSONResponse:
    db = database_health() if settings.database_required else None
    db_ready = True if db is None else db.ok
    scientific_ready = False
    config_ready = settings.demo_mode
    is_ready = db_ready and config_ready

    # Independent Jev AI status check (non-blocking for detector readiness)
    jev = get_jev_status()

    blockers: list[str] = []
    if db is not None and not db.ok:
        blockers.append(db.error or "database unavailable or migration revision mismatch")
    if not settings.demo_mode:
        blockers.append("freeze view-map/model/M4/fusion configuration")

    payload = {
        "status": "ready" if is_ready else "not_ready",
        "demo_mode": settings.demo_mode,
        "scientific_ready": scientific_ready,
        "database": None if db is None else db.to_dict(),
        "jev_ai": jev.model_dump(),
        "blockers": blockers,
    }
    return JSONResponse(status_code=200 if is_ready else 503, content=payload)


@app.get("/v1/config/status", tags=["System"])
def config_status() -> dict[str, object]:
    db = database_health() if settings.database_required else None
    return {
        "environment": settings.env,
        "demo_mode": settings.demo_mode,
        "input_mode": settings.input_mode,
        "database_required": settings.database_required,
        "database_status": None if db is None else db.status,
        "database_revision": None if db is None else db.current_revision,
        "database_revision_status": None if db is None else db.revision_status,
        "expected_database_revision": settings.expected_db_revision,
        "scientific_config_status": "TBD_MUST_FREEZE" if settings.demo_mode else "CHECK_CONFIGS",
        "jev_ai": {
            "enabled": settings.jev_ai_enabled,
            "status": "disabled" if not settings.jev_ai_enabled else "configured",
            "model_id": settings.jev_ai_model if settings.jev_ai_enabled else None,
            "prompt_version": settings.jev_ai_prompt_version,
            "endpoint_label": "lm_studio_local",
            "advisory_only": settings.jev_ai_advisory_only,
            "local_only": settings.jev_ai_local_only,
        },
    }


@app.get(
    "/metrics",
    tags=["System"],
    summary="Prometheus scrape endpoint",
    include_in_schema=False,
)
def metrics() -> Response:
    from fastapi import HTTPException, status

    from infrastructure.monitoring.metrics import get_metrics_registry

    if not settings.metrics_export_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "XS_FEATURE_DISABLED", "message": "Metrics export is disabled in configuration"},
        )

    reg = get_metrics_registry()
    content = reg.generate_prometheus_text()
    return Response(content=content, media_type="text/plain; version=0.0.4; charset=utf-8")

