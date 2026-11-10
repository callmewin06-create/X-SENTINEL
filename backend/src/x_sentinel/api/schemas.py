from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VectorAnalysisRequest(BaseModel):
    features: list[Any] = Field(
        ...,
        description="2,381-dimensional normalized numerical feature vector matching EMBER",
    )
    source_name: str | None = Field(
        default=None,
        description="Optional human-readable source label or file identifier",
    )
    request_id: str | None = Field(
        default=None,
        description="Optional client-provided correlation or idempotency request identifier",
    )

    @field_validator("features")
    @classmethod
    def validate_features_strict(cls, v: Any) -> list[float]:
        if not isinstance(v, (list, tuple)):
            raise ValueError("Features must be a list of numbers.")
        if len(v) != 2381:
            raise ValueError(f"Feature vector must contain exactly 2,381 dimensions; got {len(v)}")
        import math
        clean: list[float] = []
        for idx, item in enumerate(v):
            if isinstance(item, bool) or isinstance(item, str):
                raise ValueError(f"Feature at index {idx} has invalid non-numeric type: {type(item).__name__}")
            if not isinstance(item, (int, float)):
                raise ValueError(f"Feature at index {idx} must be a number; got {type(item).__name__}")
            val = float(item)
            if math.isnan(val) or math.isinf(val):
                raise ValueError(f"Feature at index {idx} must be finite; got {val}")
            clean.append(val)
        return clean


class AnalysisResponse(BaseModel):
    request_id: str = Field(..., description="Unique analysis request identifier")
    status: str = Field(..., description="Analysis status: completed, DEMO_ONLY, or quarantined")
    demo_mode: bool = Field(..., description="Flag indicating whether demo mode was active")
    malware_score: float = Field(
        ..., description="Primary LightGBM malware probability score in [0.0, 1.0]"
    )
    signals: dict[str, float] = Field(
        ..., description="Dictionary of detector signals (m1 through m5)"
    )
    suspicion_score: float = Field(..., description="Fused suspicion score in [0.0, 1.0]")
    threshold: float | None = Field(default=None, description="Applied decision threshold")
    decision: str | None = Field(
        default=None, description="Detector verdict: PASS, ALERT, QUARANTINE, or DEMO_ONLY"
    )
    view_contributions: dict[str, float] = Field(
        default_factory=dict,
        description="Decomposed feature view contributions: structural, behavioral, metadata",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Operational or policy warnings generated during analysis",
    )
    evidence_ref: str | None = Field(
        default=None,
        description="Deterministic SHA-256 evidence hash or evidence storage URI",
    )
    job_id: str | None = Field(
        default=None,
        description="Database primary key UUID of the persisted analysis job",
    )
    measured_latency_ms: dict[str, float] = Field(
        default_factory=dict,
        description="Measured latency breakdown in milliseconds across pipeline stages",
    )
    input_sha256: str | None = Field(
        default=None,
        description="Deterministic SHA-256 digest of input vector bytes",
    )


class AnalysisJobSummary(BaseModel):
    id: str = Field(..., description="UUID of the analysis job")
    request_id: str = Field(..., description="Client or system request identifier")
    status: str = Field(
        ..., description="Job status: completed, failed, quarantined, running, queued"
    )
    input_mode: str = Field(..., description="Input mode: vector or raw_pe")
    demo_mode: bool = Field(..., description="Flag indicating if job ran in demo mode")
    decision: str | None = Field(
        default=None, description="Persisted decision: pass, alert, quarantine, unknown"
    )
    malware_score: float | None = Field(default=None, description="Persisted malware score")
    suspicion_score: float | None = Field(
        default=None, description="Persisted fused suspicion score"
    )
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    completed_at: str | None = Field(default=None, description="ISO 8601 completion timestamp")


class AnalysisHistoryListResponse(BaseModel):
    items: list[AnalysisJobSummary] = Field(
        default_factory=list, description="List of analysis summaries"
    )
    total: int = Field(..., description="Total count of matching records")
    limit: int = Field(..., description="Maximum records requested")
    offset: int = Field(..., description="Record offset requested")


class DetectorScoreItem(BaseModel):
    detector_code: str = Field(..., description="Detector code: M1, M2, M3, M4, or M5")
    score: float = Field(..., description="Numerical score for this detector in [0.0, 1.0]")
    diagnostics: dict[str, Any] = Field(
        default_factory=dict,
        description="Diagnostic metadata and intermediate calculations for this detector",
    )


class AlertSummary(BaseModel):
    id: str = Field(..., description="Alert UUID")
    analysis_job_id: str = Field(..., description="Associated analysis job UUID")
    severity: str = Field(..., description="Alert severity: low, medium, high, or critical")
    status: str = Field(..., description="Alert status: open, acknowledged, resolved, or dismissed")
    reason: str = Field(..., description="Explanation or detector verdict triggering the alert")
    created_at: str = Field(..., description="ISO 8601 alert creation timestamp")
    resolved_at: str | None = Field(
        default=None, description="ISO 8601 resolution timestamp if resolved"
    )


class AnalysisResultDetail(BaseModel):
    malware_score: float | None = Field(default=None, description="Model malware score")
    suspicion_score: float | None = Field(default=None, description="Fused suspicion score")
    threshold: float | None = Field(default=None, description="Decision threshold applied")
    decision: str = Field(..., description="Persisted decision: pass, alert, quarantine, unknown")
    latency_ms: float | None = Field(
        default=None, description="End-to-end execution latency in milliseconds"
    )
    view_contributions: dict[str, float] = Field(
        default_factory=dict,
        description="Feature view contributions",
    )
    evidence_uri: str | None = Field(
        default=None, description="URI reference to canonical evidence artifact"
    )
    result_json: dict[str, Any] = Field(
        default_factory=dict,
        description="Full serialized result record",
    )


class AnalysisDetailResponse(BaseModel):
    id: str = Field(..., description="UUID of the analysis job")
    request_id: str = Field(..., description="Unique request identifier")
    status: str = Field(..., description="Job status")
    input_mode: str = Field(..., description="Input mode: vector or raw_pe")
    input_sha256: str | None = Field(
        default=None, description="SHA-256 digest of input vector or binary"
    )
    demo_mode: bool = Field(..., description="Demo mode indicator")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    completed_at: str | None = Field(default=None, description="ISO 8601 completion timestamp")
    error_code: str | None = Field(default=None, description="Error code if job failed")
    error_message: str | None = Field(default=None, description="Error message if job failed")
    result: AnalysisResultDetail | None = Field(
        default=None, description="Detailed analysis result record"
    )
    scores: list[DetectorScoreItem] = Field(
        default_factory=list, description="Detector scores M1 through M5"
    )
    alerts: list[AlertSummary] = Field(
        default_factory=list, description="Alerts associated with this analysis"
    )
    evidence_ref: str | None = Field(default=None, description="Evidence digest or reference")


class AlertListResponse(BaseModel):
    items: list[AlertSummary] = Field(default_factory=list, description="List of alert summaries")
    total: int = Field(..., description="Total matching alerts count")
    limit: int = Field(..., description="Query limit")
    offset: int = Field(..., description="Query offset")


class AlertStatusUpdateRequest(BaseModel):
    status: str = Field(
        ...,
        description="Target alert status: acknowledged, resolved, or dismissed",
    )


class CanonicalEvidenceResponse(BaseModel):
    request_id: str = Field(..., description="Unique request identifier")
    run_id: str = Field(..., description="Execution run identifier")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    code_commit: str = Field(..., description="Git commit hash provenance")
    build_digest: str = Field(..., description="Deterministic build artifact digest")
    input_id: str = Field(..., description="SHA-256 digest of input data")
    input_mode: str = Field(..., description="Input mode: vector or raw_pe")
    view_map_hash: str = Field(..., description="SHA-256 digest of view mapping configuration")
    model_hash: str = Field(..., description="SHA-256 digest of active model weights/artifact")
    model_config_hash: str = Field(..., description="SHA-256 digest of model configuration")
    detector_config_hash: str = Field(..., description="SHA-256 digest of detector configuration")
    seed: int = Field(..., description="Random seed used during execution")
    malware_score: float = Field(..., description="LightGBM model inference score")
    signals: dict[str, float] = Field(..., description="Detector signals m1 through m5")
    fusion_score: float = Field(..., description="Calibrated fused suspicion score")
    threshold_id: str = Field(..., description="Identifier of the applied threshold policy")
    decision: str = Field(
        ..., description="Canonical verdict: PASS, ALERT, QUARANTINE, or DEMO_ONLY"
    )
    latency_ms: dict[str, float] = Field(..., description="Latency breakdown in milliseconds")
    demo_mode: bool = Field(..., description="Flag indicating if run was in demo mode")
    evidence_hash: str = Field(
        ..., description="Deterministic SHA-256 digest over the canonical JSON payload"
    )
    verified: bool = Field(
        default=True, description="Integrity verification status (computed digest == stored digest)"
    )


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable canonical error code")
    message: str = Field(..., description="Human-readable error description")


class ErrorResponse(BaseModel):
    detail: ErrorDetail = Field(..., description="Structured error payload")


class JevExplainRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Target analysis job UUID or request_id",
    )
    mode: str = Field(
        default="explain",
        min_length=1,
        max_length=32,
        description="Jev AI workflow mode: explain, triage, compare, report, or docs",
    )
    compare_with_analysis_id: str | None = Field(
        default=None,
        max_length=128,
        description="Second analysis job UUID or request_id required when mode is 'compare'",
    )
    focus_signals: list[Literal["m1", "m2", "m3", "m4", "m5"]] | None = Field(
        default=None,
        max_length=5,
        description="Optional subset of detector signals (m1 through m5) to highlight",
    )
    question: str | None = Field(
        default=None,
        max_length=500,
        description="Optional analyst question for the explain workflow",
    )


class JevAIRunResponse(BaseModel):
    id: str = Field(..., description="Unique Jev AI run UUID")
    analysis_job_id: str | None = Field(
        default=None, description="Associated canonical analysis job UUID"
    )
    requested_by_user_id: str | None = Field(
        default=None, description="UUID of the authenticated user who initiated the run"
    )
    mode: Literal["explain", "triage", "compare", "report", "docs"] = Field(
        ..., description="Executed Jev AI workflow mode"
    )
    status: Literal["queued", "running", "completed", "failed", "blocked"] = Field(
        ..., description="Run lifecycle status"
    )
    advisory_only: Literal[True] = Field(
        default=True,
        description="Mandatory invariant: Jev AI outputs are strictly advisory",
    )
    authoritative_decision_unchanged: Literal[True] = Field(
        default=True,
        description="Confirms canonical detector verdict and evidence were not modified",
    )
    model_id: str = Field(..., description="LM Studio model identifier")
    endpoint_label: str = Field(..., description="Sanitized local runtime endpoint label")
    prompt_version: str = Field(..., description="Prompt contract version")
    input_digest_sha256: str = Field(
        ..., description="64-character lowercase hex SHA-256 digest of safe input context"
    )
    output_digest_sha256: str | None = Field(
        default=None,
        description="64-character lowercase hex SHA-256 digest of advisory output",
    )
    context_summary: dict[str, Any] = Field(
        default_factory=dict,
        description="Sanitized allowlisted context summary",
    )
    response_text: str | None = Field(
        default=None,
        description=(
            "Persisted advisory summary text (omitted if retention policy disables text storage)"
        ),
    )
    decision_result: dict[str, Any] | None = Field(
        default=None,
        description="Structured workflow decision output",
    )
    latency_ms: float | None = Field(
        default=None, description="Inference execution latency in milliseconds"
    )
    error_code: str | None = Field(
        default=None, description="Canonical error code if run failed/blocked"
    )
    error_message: str | None = Field(
        default=None, description="Sanitized error description if run failed/blocked"
    )
    created_at: str = Field(..., description="ISO 8601 UTC creation timestamp")
    completed_at: str | None = Field(default=None, description="ISO 8601 UTC completion timestamp")


class JevAIRunListResponse(BaseModel):
    items: list[JevAIRunResponse] = Field(
        default_factory=list, description="List of persisted Jev AI runs"
    )
    total: int = Field(..., description="Total count of matching Jev AI runs")
    limit: int = Field(..., description="Query page limit")
    offset: int = Field(..., description="Query page offset")


class JevFeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: int | None = Field(
        default=None,
        description="Optional integer usefulness rating from 1 (lowest) to 5 (highest)",
    )
    label: Literal["helpful", "not_helpful", "incorrect", "unsafe", "unclear"] | None = Field(
        default=None,
        description="Optional structured classification label",
    )
    comment: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional analyst feedback comment (max 2,000 characters)",
    )

    @field_validator("rating", mode="before")
    @classmethod
    def validate_strict_integer_rating(cls, v: Any) -> int | None:
        if v is None:
            return None
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(
                "rating must be a strict integer between 1 and 5 (booleans and strings rejected)"
            )
        if not (1 <= v <= 5):
            raise ValueError(f"rating must be between 1 and 5; got {v}")
        return v


class JevFeedbackResponse(BaseModel):
    id: str = Field(..., description="Unique feedback UUID")
    jev_ai_run_id: str = Field(..., description="Associated Jev AI run UUID")
    user_id: str | None = Field(
        default=None, description="UUID of the analyst who submitted feedback"
    )
    rating: int | None = Field(default=None, description="Integer rating in [1, 5]")
    label: Literal["helpful", "not_helpful", "incorrect", "unsafe", "unclear"] | None = Field(
        default=None, description="Structured classification label"
    )
    comment: str | None = Field(default=None, description="Sanitized analyst comment")
    advisory_only: Literal[True] = Field(
        default=True,
        description=(
            "Confirms feedback is advisory telemetry only and never alters detector verdicts"
        ),
    )
    created_at: str = Field(..., description="ISO 8601 UTC creation timestamp")


class JevFeedbackListResponse(BaseModel):
    jev_ai_run_id: str = Field(..., description="Target Jev AI run UUID")
    total: int = Field(..., description="Total feedback records for this run")
    items: list[JevFeedbackResponse] = Field(
        default_factory=list, description="Ordered list of feedback items"
    )
