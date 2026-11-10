from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SignalResult:
    name: str
    score: float
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisResult:
    request_id: str
    status: str
    demo_mode: bool
    malware_score: float
    signals: dict[str, float]
    suspicion_score: float
    threshold: float | None
    view_contributions: dict[str, float]
    warnings: list[str]
    evidence_ref: str | None = None
    decision: str | None = None
    job_id: str | None = None
    measured_latency_ms: dict[str, float] = field(default_factory=dict)
    input_sha256: str | None = None
