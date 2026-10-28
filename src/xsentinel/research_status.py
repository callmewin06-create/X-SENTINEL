"""Load an explicitly dated, offline research snapshot without research outputs.

This module does not load models, query services, change thresholds or verify the
current external source files. Source digests are recorded when the asset is built.
"""
from hashlib import sha256
from importlib import resources
from datetime import date
import json
import math
from pathlib import Path, PurePosixPath


SCHEMA_VERSION = 1
SNAPSHOT_NAME = "research_status_2026_10_28.json"


def snapshot_digest(snapshot):
    """Hash the JSON payload, excluding its own digest, deterministically."""
    payload = {k: v for k, v in snapshot.items() if k != "content_sha256"}
    return sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                             allow_nan=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def validate_research_status(snapshot):
    """Reject malformed or internally inconsistent assets instead of inventing data."""
    if not isinstance(snapshot, dict) or snapshot.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported research snapshot schema")
    required = {"snapshot_id", "as_of", "scope", "primary", "methods", "fixed_threshold",
                "same_fpr", "clean_budgets", "seeds", "adaptive", "training_filtering",
                "binary_audit", "cross_confirmation", "limitations", "provenance"}
    if not required.issubset(snapshot):
        raise ValueError("Incomplete research snapshot")
    if not isinstance(snapshot["snapshot_id"], str) or not isinstance(snapshot["as_of"], str):
        raise ValueError("Invalid research snapshot identity")
    date.fromisoformat(snapshot["as_of"])
    if snapshot.get("content_sha256") != snapshot_digest(snapshot):
        raise ValueError("Research snapshot digest mismatch")
    scope = snapshot["scope"]
    if (scope.get("kind") != "frozen_offline_snapshot" or scope.get("live_service_status") is not False
            or scope.get("feature_space_attacks") is not True
            or scope.get("observed_final_reused") is not True
            or scope.get("deployment_thresholds_changed") is not False):
        raise ValueError("Invalid research evidence scope")
    primary = snapshot["primary"]
    if (primary["configuration_count"] != sum(r["configurations"] for r in primary["datasets"])
            or primary["bundle_count"] != 2 * primary["configuration_count"]):
        raise ValueError("Inconsistent primary configuration counts")
    if any(sum(r["view_feature_counts"].values()) != r["feature_count"] for r in primary["datasets"]):
        raise ValueError("Inconsistent feature partition counts")
    if (snapshot["methods"]["Reduced"]["components"] != ["VMC", "BGS"]
            or snapshot["methods"]["Full"]["components"] != ["VMC", "BPG"]
            or snapshot["methods"]["Full"]["used_auxiliary_views"] != ["behavioral"]):
        raise ValueError("Invalid primary method semantics")
    seed_info = snapshot["seeds"]
    if (seed_info["attempt_count"] != len(seed_info["rows"])
            or seed_info["confirmed_count"] != sum(r["confirmed"] for r in seed_info["rows"])
            or seed_info["additional_seeds"] != [r["seed"] for r in seed_info["rows"]
                                                   if r["origin"] == "additional"]):
        raise ValueError("Inconsistent supplemental seed counts")
    if (snapshot["same_fpr"]["retrospective"] is not True
            or snapshot["same_fpr"]["positive_group"] != "successful_eligible"
            or snapshot["adaptive"]["cell_count"] != sum(r["runs"] for r in snapshot["adaptive"]["rows"])):
        raise ValueError("Invalid comparison or adaptive scope")
    same_rows = snapshot["same_fpr"]["rows"]
    comparison_groups = {(r["dataset"], r["cohort"]) for r in same_rows}
    if comparison_groups != {("EMBER2018", "restricted"), ("EMBER2024", "restricted"), ("EMBER2024", "cross")}:
        raise ValueError("Incomplete low-FPR cohorts")
    expected_methods = {"TADR", "STRIP", "VMC", "BGS", "BPG", "Reduced", "Full",
                        "STRIP inverse", "Shadow", "SHAP-IF"}
    for dataset, cohort in comparison_groups:
        group = [r for r in same_rows if r["dataset"] == dataset and r["cohort"] == cohort]
        if len(group) != 10 or {r["method"] for r in group} != expected_methods:
            raise ValueError("Incomplete low-FPR comparator group")
    binary = snapshot["binary_audit"]
    if (binary["variant_count"] != binary["original_count"] + binary["modified_count"]
            or binary["functionality_cases"] != binary["windows_pass"] + binary["windows_error"]
            or binary["scoring_rows"] != 2 * binary["unique_file_main_model_pairs"]
            or binary["wine_evidence"] is not False
            or binary["source_and_executables_in_export"] is not False
            or binary["referenced_source_files_found"] != 0
            or binary["referenced_executables_found"] != 0
            or binary["complete_binary_trigger_demonstrated"] is not False):
        raise ValueError("Inconsistent binary audit counts or scope")
    if (len(binary["feature_shift_rows"]) != binary["edited_schema_cases"]
            or len(binary["windows_rows"]) != binary["variant_count"]
            or sum(r["pass_count"] for r in binary["windows_rows"]) != binary["windows_pass"]
            or sum(r["error_count"] for r in binary["windows_rows"]) != binary["windows_error"]
            or any(r["structural"] + r["behavioral"] + r["metadata"] != r["total_changed"]
                   or r["collateral"] != r["total_changed"] - 1 for r in binary["feature_shift_rows"])):
        raise ValueError("Inconsistent binary feature or Windows result rows")
    rate_keys = {"recall", "fpr", "post_asr", "tpr", "pauc", "confirmation_asr",
                 "confirmation_paired_gain", "asr", "reduced_recall", "reduced_fpr",
                 "full_recall", "full_fpr", "before", "after", "main_before", "main_after",
                 "asr_before", "asr_after", "accuracy_before", "accuracy_after", "fpr_cap",
                 "clean_asr", "poisoned_asr", "new_evasion", "lost_evasion", "net_gain", "poison_rate"}

    def check_rates(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in rate_keys and (isinstance(item, bool) or not isinstance(item, (int, float))
                                         or not math.isfinite(item) or not 0 <= item <= 1):
                    raise ValueError("Research rates must be finite fractions")
                check_rates(item)
        elif isinstance(value, list):
            for item in value:
                check_rates(item)

    check_rates(snapshot)
    sources = snapshot["provenance"]["sources"]
    if not sources:
        raise ValueError("Missing research provenance")
    for source in sources:
        p = PurePosixPath(source["path"])
        digest = source["sha256"]
        if (p.is_absolute() or ".." in p.parts or "\\" in source["path"] or ":" in source["path"]
                or not isinstance(digest, str) or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)):
            raise ValueError("Invalid source path or digest")


def load_research_status(path=None):
    """Return ``state``, ``snapshot`` and a Vietnamese ``message``.

    States are ready/missing/invalid. A failure always returns snapshot=None;
    metrics are never replaced with zeros or silently loaded from an old asset.
    The default works in an installed package without output/ or outputs/.
    """
    source = (Path(path) if path is not None else
              resources.files("xsentinel").joinpath("assets", SNAPSHOT_NAME))
    try:
        snapshot = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"state": "missing", "snapshot": None,
                "message": "Chưa có bản tổng hợp nghiên cứu đóng gói."}
    except (OSError, UnicodeError, ValueError):
        return {"state": "invalid", "snapshot": None,
                "message": "Không đọc được bản tổng hợp nghiên cứu đóng gói."}
    try:
        validate_research_status(snapshot)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, OverflowError):
        return {"state": "invalid", "snapshot": None,
                "message": "Bản tổng hợp nghiên cứu không hợp lệ; không hiển thị số liệu thay thế."}
    return {"state": "ready", "snapshot": snapshot,
            "message": "Bản tổng hợp nghiên cứu cố định ngày " + snapshot["as_of"]
                       + "; không phải trạng thái dịch vụ hiện tại."}
