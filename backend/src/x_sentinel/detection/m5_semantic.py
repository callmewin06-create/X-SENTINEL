from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from x_sentinel.detection.config import M5Config
from x_sentinel.domain import SignalResult


class M5RulesIntegrityError(Exception):
    """Raised when the M5 rules artifact fails cryptographic SHA-256 integrity verification."""


def load_m5_rules(
    rules_path: Path | str, expected_sha256: str | None = None
) -> tuple[dict[str, Any], str]:
    """Load and cryptographically verify the frozen M5 semantic rules artifact.

    Raises:
        FileNotFoundError: if the rules file is missing.
        M5RulesIntegrityError: if the file SHA-256 does not match expected_sha256.
    """
    path = Path(rules_path)
    if not path.exists():
        raise FileNotFoundError(f"M5 rules artifact not found at: {path}")

    raw_bytes = path.read_bytes()
    computed_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    # Canonical cross-platform checksum verification (handles CRLF Windows and LF Linux/Git checkouts)
    normalized_crlf_sha256 = hashlib.sha256(
        raw_bytes.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    ).hexdigest()
    normalized_lf_sha256 = hashlib.sha256(
        raw_bytes.replace(b"\r\n", b"\n")
    ).hexdigest()

    matched_sha256 = computed_sha256
    if expected_sha256 is not None:
        target = expected_sha256.strip().lower()
        if target in (computed_sha256.lower(), normalized_crlf_sha256.lower(), normalized_lf_sha256.lower()):
            matched_sha256 = target
        else:
            raise M5RulesIntegrityError(
                f"M5 rules artifact checksum mismatch for {path}!\n"
                f"Expected SHA-256: {expected_sha256}\n"
                f"Computed SHA-256: {computed_sha256} (LF: {normalized_lf_sha256}, CRLF: {normalized_crlf_sha256})"
            )

    try:
        rules_data = json.loads(raw_bytes.decode("utf-8"))
    except Exception as err:
        raise ValueError(f"Corrupted or invalid JSON in rules artifact {path}") from err

    if not isinstance(rules_data, dict) or "rules" not in rules_data:
        raise ValueError(f"Invalid M5 rules schema: missing 'rules' array in {path}")

    return rules_data, matched_sha256


def evaluate_semantic_rules(
    vector: Sequence[float], rules_data: dict[str, Any]
) -> tuple[float, dict[str, Any]]:
    """Evaluate physical PE domain invariant rules on an EMBER 2,381 feature vector.

    Returns:
        (plausibility_score, diagnostics)
    """
    clean_vec = [float(v) for v in vector]
    for idx, v in enumerate(clean_vec):
        if not math.isfinite(v):
            raise ValueError(f"Vector contains non-finite feature at index {idx}: {v}")

    expected_len = int(rules_data.get("feature_count", 2381))
    if len(clean_vec) != expected_len:
        raise ValueError(
            f"Vector dimension mismatch for M5: expected {expected_len}, got {len(clean_vec)}"
        )

    rules_list = rules_data.get("rules", [])
    if not rules_list:
        return 1.0, {"rules_evaluated": 0, "rules_passed": 0, "rules_failed": 0, "violations": []}

    total_weight = 0.0
    passed_weight = 0.0
    violations: list[dict[str, Any]] = []

    for rule in rules_list:
        rule_id = str(rule.get("rule_id", "UNKNOWN"))
        weight = float(rule.get("weight", 1.0))
        total_weight += weight
        tolerance = float(rule.get("tolerance", 0.0))
        kind = str(rule.get("kind", "range"))

        rule_passed = True
        violation_reason = ""

        if kind == "range":
            indices: list[int] = []
            if "indices" in rule:
                indices = [int(i) for i in rule["indices"]]
            elif "indices_start" in rule and "indices_end" in rule:
                indices = list(range(int(rule["indices_start"]), int(rule["indices_end"])))

            min_val = float(rule.get("min_value", -math.inf)) - tolerance
            max_val = float(rule.get("max_value", math.inf)) + tolerance

            for idx in indices:
                if idx < 0 or idx >= len(clean_vec):
                    continue
                val = clean_vec[idx]
                if val < min_val or val > max_val:
                    rule_passed = False
                    violation_reason = (
                        f"Feature at index {idx} with value {val} is outside valid range [{min_val}, {max_val}]"
                    )
                    break

        elif kind == "sum_bound":
            start_idx = int(rule.get("indices_start", 0))
            end_idx = int(rule.get("indices_end", len(clean_vec)))
            min_sum = float(rule.get("min_sum", 0.0)) - tolerance
            max_sum = float(rule.get("max_sum", 1e12)) + tolerance

            sub_sum = sum(clean_vec[start_idx:end_idx])
            if sub_sum < min_sum or sub_sum > max_sum:
                rule_passed = False
                violation_reason = f"Sum across [{start_idx}, {end_idx}) is {sub_sum}, outside [{min_sum}, {max_sum}]"

        if rule_passed:
            passed_weight += weight
        else:
            violations.append({
                "rule_id": rule_id,
                "name": str(rule.get("name", "")),
                "reason": violation_reason,
                "weight": weight,
            })

    score = passed_weight / total_weight if total_weight > 0 else 1.0
    score_clamped = float(min(max(score, 0.0), 1.0))

    diagnostics: dict[str, Any] = {
        "formula": "semantic_plausibility",
        "rules_evaluated": len(rules_list),
        "rules_passed": len(rules_list) - len(violations),
        "rules_failed": len(violations),
        "violations": violations,
        "plausibility_score": score_clamped,
        "anomaly_score": float(1.0 - score_clamped),
    }

    return score_clamped, diagnostics


class M5SemanticPlausibilityDetector:
    """Canonical M5 Detector: Physical PE Domain Invariant and Semantic Plausibility."""

    name: str = "m5"

    def __init__(
        self,
        config: M5Config | dict[str, Any] | None = None,
        rules_data: dict[str, Any] | None = None,
        expected_sha256: str | None = None,
    ) -> None:
        if config is None:
            self.config = M5Config()
        elif isinstance(config, M5Config):
            self.config = config
        elif isinstance(config, dict):
            self.config = M5Config(
                enabled=bool(config.get("enabled", True)),
                rules_file=str(config.get("rules_file", "configs/m5_rules.json")),
                rules_sha256=str(
                    config.get(
                        "rules_sha256",
                        "2e8c599aa9fded31c8d27eb0d96f45743a087572f696bc8e3bdb0f69d5ca184d",
                    )
                ),
                metric=str(config.get("metric", "plausibility")),
            )
        else:
            raise TypeError(f"Invalid config type: {type(config)}")

        self.rules_sha256 = expected_sha256 or self.config.rules_sha256
        if not self.config.enabled:
            self.rules_data = {}
            self.loaded_sha256 = ""
        elif rules_data is not None:
            self.rules_data = rules_data
            self.loaded_sha256 = self.rules_sha256
        else:
            rules_path = Path(self.config.rules_file)
            self.rules_data, self.loaded_sha256 = load_m5_rules(
                rules_path, expected_sha256=self.rules_sha256
            )

    def score(self, vector: Sequence[float]) -> float:
        res = self.detect(vector)
        return res.score

    def detect(self, vector: Sequence[float]) -> SignalResult:
        if not self.config.enabled:
            return SignalResult(name=self.name, score=0.0, diagnostics={"status": "DISABLED"})

        score, diagnostics = evaluate_semantic_rules(vector, self.rules_data)
        diagnostics["rules_sha256"] = self.loaded_sha256

        return SignalResult(name=self.name, score=score, diagnostics=diagnostics)
