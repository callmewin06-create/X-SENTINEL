"""Bounded client-declared input provenance; no raw file/vector is retained."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat
from xsentinel.data.limits import MAX_UPLOAD_BYTES


class InputMetadata(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['pe', 'vector', 'raw_json', 'demo']
    name: str = Field(min_length=1, max_length=255)
    size_bytes: int | None = Field(default=None, ge=0, le=MAX_UPLOAD_BYTES)
    file_sha256: str | None = Field(default=None, pattern=r'^[0-9a-f]{64}$')
    schema_version: str = Field(alias='schema', min_length=1, max_length=80)
    extractor: str = Field(min_length=1, max_length=160)
    extraction_ms: FiniteFloat | None = Field(default=None, ge=0)


def stable_metadata(value):
    """Timing may differ on a retry; input identity must not."""
    if value is None:
        return None
    return {k: v for k, v in value.items() if k != 'extraction_ms'}
