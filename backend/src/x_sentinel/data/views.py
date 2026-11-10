from __future__ import annotations

import functools
import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .schema import FEATURE_COUNT


@dataclass(frozen=True)
class SliceSpec:
    """Contiguous slice definition for a semantic feature view."""

    start: int
    stop: int
    step: int = 1

    @property
    def count(self) -> int:
        return len(range(self.start, self.stop, self.step))

    def indices(self, total: int = FEATURE_COUNT) -> list[int]:
        return list(range(self.start, self.stop, self.step))

    def extract(self, vector: Sequence[float]) -> list[float]:
        return list(vector[self.start:self.stop:self.step])


@dataclass(frozen=True)
class IndicesSpec:
    """Discrete index list definition for a semantic feature view."""

    indices_list: tuple[int, ...]

    def __init__(self, indices: Sequence[int]) -> None:
        object.__setattr__(self, "indices_list", tuple(int(x) for x in indices))

    @property
    def count(self) -> int:
        return len(self.indices_list)

    def indices(self, total: int = FEATURE_COUNT) -> list[int]:
        return list(self.indices_list)

    def extract(self, vector: Sequence[float]) -> list[float]:
        return [float(vector[i]) for i in self.indices_list]


ViewSpec = SliceSpec | IndicesSpec


def compute_mapping_hash(views: dict[str, Any]) -> str:
    """Compute a deterministic, canonical SHA-256 fingerprint for a view mapping.

    The hash is derived from sorted view names and their exact 0-indexed integer feature indices:
    Canonical JSON:
    {"behavioral":[255,...,1534],"metadata":[1535,...,2380],"structural":[0,...,254]}
    with no whitespace and sorted keys. Any index mutation produces a different hash.
    """
    normalized: dict[str, list[int]] = {}
    for name, spec in views.items():
        if isinstance(spec, (SliceSpec, IndicesSpec)):
            normalized[name] = spec.indices()
        elif isinstance(spec, dict):
            kind = spec.get("kind", "slice")
            if kind == "slice" or ("start" in spec and "stop" in spec):
                step = int(spec.get("step", 1))
                normalized[name] = list(range(int(spec["start"]), int(spec["stop"]), step))
            elif kind == "indices":
                normalized[name] = [int(x) for x in spec["indices"]]
            else:
                raise ValueError(f"unknown view spec kind '{kind}' for view '{name}'")
        else:
            raise TypeError(f"unsupported view spec type: {type(spec)}")

    canonical_json = json.dumps(normalized, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ViewMap:
    """Authoritative semantic view mapping for X-SENTINEL V3."""

    status: str
    structural: ViewSpec
    behavioral: ViewSpec
    metadata: ViewSpec
    version: str = "1.0.0"
    feature_count: int = FEATURE_COUNT
    notes: tuple[str, ...] = field(default_factory=tuple)
    sha256: str | None = None

    @property
    def views(self) -> dict[str, ViewSpec]:
        return {
            "structural": self.structural,
            "behavioral": self.behavioral,
            "metadata": self.metadata,
        }

    @property
    def mapping_hash(self) -> str:
        return compute_mapping_hash(self.views)

    def split(self, vector: Sequence[float]) -> dict[str, list[float]]:
        """Split a 2,381-dimensional vector into the three semantic views.

        Vector must be validated prior to calling split.
        """
        if len(vector) != self.feature_count:
            raise ValueError(
                f"vector must have exactly {self.feature_count} features, got {len(vector)}"
            )
        return {
            "structural": self.structural.extract(vector),
            "behavioral": self.behavioral.extract(vector),
            "metadata": self.metadata.extract(vector),
        }

    def validate_integrity(
        self,
        require_disjoint: bool = False,
        require_complete: bool = False,
    ) -> dict[str, Any]:
        """Validate view mapping mathematical and bounds integrity.

        Checks:
        1. All indices within range [0, feature_count).
        2. No view is empty.
        3. No duplicate indices inside each view.
        4. Optional disjointness / complete partition enforcement.
        """
        all_indices: dict[str, list[int]] = {}
        for view_name, spec in self.views.items():
            idx_list = spec.indices(self.feature_count)
            if not idx_list:
                raise ValueError(f"view '{view_name}' is empty (0 features)")
            for idx in idx_list:
                if idx < 0 or idx >= self.feature_count:
                    raise ValueError(
                        f"index {idx} in view '{view_name}' is out of bounds [0, "
                        f"{self.feature_count})"
                    )
            if len(idx_list) != len(set(idx_list)):
                raise ValueError(f"view '{view_name}' contains duplicate indices")
            all_indices[view_name] = idx_list

        struct_set = set(all_indices["structural"])
        behav_set = set(all_indices["behavioral"])
        meta_set = set(all_indices["metadata"])

        overlap_sb = struct_set & behav_set
        overlap_sm = struct_set & meta_set
        overlap_bm = behav_set & meta_set
        is_disjoint = not (overlap_sb or overlap_sm or overlap_bm)

        if require_disjoint and not is_disjoint:
            overlaps = []
            if overlap_sb:
                overlaps.append(f"structural & behavioral: {len(overlap_sb)}")
            if overlap_sm:
                overlaps.append(f"structural & metadata: {len(overlap_sm)}")
            if overlap_bm:
                overlaps.append(f"behavioral & metadata: {len(overlap_bm)}")
            raise ValueError(f"view mappings are not disjoint: {', '.join(overlaps)}")

        union_set = struct_set | behav_set | meta_set
        is_complete = (
            len(union_set) == self.feature_count
            and union_set == set(range(self.feature_count))
        )

        if require_complete and not is_complete:
            missing = set(range(self.feature_count)) - union_set
            raise ValueError(
                f"view mappings do not cover all features (missing {len(missing)} features)"
            )

        return {
            "feature_count": self.feature_count,
            "structural_count": len(struct_set),
            "behavioral_count": len(behav_set),
            "metadata_count": len(meta_set),
            "disjoint": is_disjoint,
            "complete": is_complete,
            "mapping_hash": self.mapping_hash,
        }


@functools.lru_cache(maxsize=16)
def _load_view_map_cached(file_path_str: str, file_mtime: float, allow_demo: bool) -> ViewMap:
    p = Path(file_path_str)
    content = p.read_text(encoding="utf-8")
    raw = yaml.safe_load(content)
    return _parse_view_map_dict(raw, allow_demo=allow_demo)


def load_view_map(path_or_dict: Path | str | dict[str, Any], allow_demo: bool = True) -> ViewMap:
    """Load, parse and validate a versioned view mapping from YAML file or dictionary.

    Enforces fail-closed security for scientific mode and validates hash integrity.
    Uses LRU cache for file-based loads to eliminate redundant disk I/O and parsing.
    """
    if isinstance(path_or_dict, (Path, str)):
        p = Path(path_or_dict)
        mtime = p.stat().st_mtime if p.exists() else 0.0
        return _load_view_map_cached(str(p.resolve()), mtime, allow_demo)
    elif isinstance(path_or_dict, dict):
        return _parse_view_map_dict(path_or_dict, allow_demo=allow_demo)
    else:
        raise TypeError(f"expected Path, str, or dict, got {type(path_or_dict)}")


def _parse_view_map_dict(raw: dict[str, Any], allow_demo: bool = True) -> ViewMap:

    status = str(raw.get("status", ""))
    if "TBD" in status:
        raise RuntimeError(
            "scientific view map is unresolved; OQ-01 must be frozen before scientific run"
        )
    if "DEMO" in status and not allow_demo:
        raise RuntimeError("demo view map cannot be used in scientific mode")

    feature_count = int(raw.get("feature_count", FEATURE_COUNT))
    version = str(raw.get("version", "1.0.0"))
    notes_list = raw.get("notes") or []
    notes = tuple(str(n) for n in notes_list)
    expected_hash = raw.get("sha256")

    views_raw = raw.get("views")
    if not isinstance(views_raw, dict):
        raise ValueError("config 'views' must be a dictionary")

    specs: dict[str, ViewSpec] = {}
    for k in ("structural", "behavioral", "metadata"):
        if k not in views_raw or views_raw[k] is None:
            raise ValueError(f"missing required view definition for '{k}'")
        v = views_raw[k]
        kind = v.get("kind", "slice") if isinstance(v, dict) else "slice"
        if kind == "slice" or ("start" in v and "stop" in v):
            specs[k] = SliceSpec(int(v["start"]), int(v["stop"]), int(v.get("step", 1)))
        elif kind == "indices":
            specs[k] = IndicesSpec(v["indices"])
        else:
            raise ValueError(f"unsupported view spec kind '{kind}' for view '{k}'")

    if "DEMO" in status:
        spans = [(v.start, v.stop) for v in specs.values() if isinstance(v, SliceSpec)]
        if sorted(spans) != [(0, 255), (255, 1535), (1535, 2381)]:
            raise ValueError("demo map changed unexpectedly; update ADR/tests")

    computed_hash = compute_mapping_hash(specs)
    if expected_hash is not None and str(expected_hash).strip() != "":
        if str(expected_hash).strip().lower() != computed_hash.lower():
            raise ValueError(
                f"view map hash mismatch: expected {expected_hash}, computed {computed_hash}"
            )

    return ViewMap(
        status=status,
        version=version,
        feature_count=feature_count,
        notes=notes,
        sha256=computed_hash,
        **specs,
    )
