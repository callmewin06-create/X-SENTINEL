from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped,unused-ignore]
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="XS_", env_file=".env", extra="ignore")

    env: str = "development"
    demo_mode: bool = True
    log_level: str = "INFO"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_port: int = 8501
    api_base_url: str = "http://localhost:8000"
    input_mode: str = "vector"
    config_dir: Path = Path("configs")
    artifact_dir: Path = Path("artifacts")
    model_dir: Path = Path("models")
    audit_log_path: Path = Path("artifacts/audit/events.jsonl")

    database_url: str = "mssql+pyodbc://localhost/xsentinel?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    database_required: bool = True
    expected_db_revision: str = "0002_v3_jev_ai_audit"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle_seconds: int = 1800

    api_auth_mode: str = "none"
    api_tokens: dict[str, dict[str, Any]] = {}
    admin_token: str | None = None
    allowed_origins: str = "http://localhost:8501"
    max_upload_bytes: int = 52_428_800

    jev_ai_enabled: bool = False
    jev_ai_mode: str = "local"
    jev_ai_base_url: str = "http://localhost:1234/v1"
    jev_ai_model: str = "jev-local-TBD"
    jev_ai_timeout_seconds: float = 60.0
    jev_ai_temperature: float = 0.1
    jev_ai_max_context_chars: int = 30_000
    jev_ai_prompt_version: str = "jev-v3.0.0"
    jev_ai_advisory_only: bool = True
    jev_ai_local_only: bool = True
    jev_ai_store_response_text: bool = True
    jev_ai_store_prompt_text: bool = False
    jev_ai_store_context_summary: bool = True

    research_asr_gate: float = 0.50
    production_asr_target: float = 0.80
    fpr_target: float = 0.01
    latency_p95_ms_target: float = 10.0
    circuit_breaker_ms: float = 8.0

    max_concurrent_detector_requests: int = 50
    max_concurrent_ai_requests: int = 4
    ai_queue_capacity: int = 16
    ai_queue_timeout_seconds: float = 10.0
    performance_monitoring_enabled: bool = True
    metrics_export_enabled: bool = True

    
    @model_validator(mode="after")
    def validate_production_security(self) -> Settings:
        if self.env == "production":
            if self.api_auth_mode == "none":
                raise ValueError("Security violation: api_auth_mode cannot be 'none' when env='production'")
        return self

    @field_validator("backend_port", "frontend_port")
    @classmethod
    def validate_ports(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError(f"Port must be between 1 and 65535; got {v}")
        return v

    @field_validator("input_mode")
    @classmethod
    def validate_input_mode(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in {"vector", "raw_pe"}:
            raise ValueError(f"input_mode must be 'vector' or 'raw_pe'; got '{v}'")
        return clean

    @field_validator("env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in {"development", "test", "testing", "staging", "production"}:
            raise ValueError(
                f"env must be one of development, test, staging, production; got '{v}'"
            )
        return clean

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        clean = v.strip().upper()
        if clean not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(f"log_level must be a standard Python logging level; got '{v}'")
        return clean

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("database_url must not be empty or whitespace")
        return clean

    @field_validator(
        "db_pool_size",
        "db_pool_recycle_seconds",
        "max_upload_bytes",
        "jev_ai_timeout_seconds",
        "circuit_breaker_ms",
        "latency_p95_ms_target",
        "max_concurrent_detector_requests",
        "max_concurrent_ai_requests",
        "ai_queue_timeout_seconds",
    )
    @classmethod
    def validate_positive_numbers(cls, v: float | int) -> float | int:
        if v <= 0:
            raise ValueError(f"Numeric parameter must be > 0; got {v}")
        return v

    @field_validator("db_max_overflow", "ai_queue_capacity")
    @classmethod
    def validate_non_negative_int(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"Parameter must be >= 0; got {v}")
        return v

    @field_validator("jev_ai_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not (0.0 <= v <= 2.0):
            raise ValueError(f"jev_ai_temperature must be between 0.0 and 2.0; got {v}")
        return v

    @field_validator("jev_ai_max_context_chars")
    @classmethod
    def validate_max_context(cls, v: int) -> int:
        if not (100 <= v <= 200_000):
            raise ValueError(f"jev_ai_max_context_chars must be between 100 and 200,000; got {v}")
        return v

    @field_validator("research_asr_gate", "production_asr_target", "fpr_target")
    @classmethod
    def validate_ratios(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Ratio metric must be between 0.0 and 1.0; got {v}")
        return v

    @model_validator(mode="after")
    def validate_jev_ai_local_endpoint(self) -> Settings:
        if self.jev_ai_enabled and self.jev_ai_local_only:
            from x_sentinel.jev_ai.guardrails import validate_local_endpoint

            validate_local_endpoint(self.jev_ai_base_url)
        return self

    def load_yaml_config(self, filename: str) -> dict[str, Any]:
        path = self.config_dir / filename
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get_jev_ai_config(self) -> dict[str, Any]:
        return self.load_yaml_config("jev_ai.yaml")


settings = Settings()
