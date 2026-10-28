"""Build the small packaged research snapshot from existing exported evidence.

No training, model inference, binary execution, service calls or threshold changes.
Run with --check to compare source-derived content without writing any file.
"""
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
from statistics import fmean
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xsentinel.research_status import (SCHEMA_VERSION, SNAPSHOT_NAME, snapshot_digest,
                                      validate_research_status)
from xsentinel.schema import V2_PRIMARY, V3_PRIMARY, get_schema


METHODS = {"M3_view_mass": "VMC", "M4_shap_behavioral_conflict": "BGS",
           "M4_prob_gap": "BPG", "X_primary_reduced": "Reduced",
           "X_primary_full": "Full", "STRIP_inverse": "STRIP inverse"}


def build_snapshot(repo_root):
    root = Path(repo_root).resolve()
    research = Path("output/teacher_revision_2026_10_27")
    binary_root = Path("phuc_pe_trigger_2026_10_27/phuc_pe_trigger_2026_10_27")
    sources = []

    def evidence(relative, *, csv_rows=False):
        path = root / relative
        raw = path.read_bytes()
        source = {"path": Path(relative).as_posix(), "sha256": sha256(raw).hexdigest()}
        sources.append(source)
        if csv_rows:
            rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
            if not rows:
                raise ValueError("Empty evidence: " + str(relative))
            source["rows"] = len(rows)
            return rows
        return json.loads(raw)

    def rows(name):
        return evidence(research / name, csv_rows=True)

    def boolean(value):
        if value not in ("True", "False"):
            raise ValueError("Expected an explicit boolean")
        return value == "True"

    fixed = rows("fixed_threshold_per_run.csv")
    cells = {(r["dataset"], int(r["seed"]), r["family"], float(r["rate"])) for r in fixed}
    if len(cells) != 54 or len(fixed) != 540:
        raise ValueError("Expected all 54 original cells and ten score methods")
    datasets = []
    for dataset, schema, version in [("EMBER2018", "V2", V2_PRIMARY), ("EMBER2024", "V3", V3_PRIMARY)]:
        primary = evidence(Path("outputs/primary") / dataset / "protocol_v2/results.json")
        layout = get_schema(version)
        unique = [r for r in fixed if r["dataset"] == dataset and r["method"] == "X_primary_reduced"]
        if len(primary["rows"]) != len(unique) or len(unique) != 27:
            raise ValueError("Primary dataset/configuration mismatch")
        datasets.append({"dataset": dataset, "schema": schema, "schema_version": layout.version,
                         "feature_count": layout.dim,
                         "view_feature_counts": {name: len(indices) for name, indices in layout.views.items()},
                         "configurations": len(unique),
                         "confirmed": sum(boolean(r["confirmed"]) for r in unique),
                         "restricted_confirmed": sum(boolean(r["confirmed"]) and r["cohort"] == "restricted" for r in unique),
                         "cross_confirmed": sum(boolean(r["confirmed"]) and r["cohort"] == "cross" for r in unique)})
    fixed_summary = []
    for dataset, cohort in [("EMBER2018", "restricted"), ("EMBER2024", "restricted"), ("EMBER2024", "cross")]:
        for method in ["X_primary_reduced", "X_primary_full"]:
            group = [r for r in fixed if r["dataset"] == dataset and r["cohort"] == cohort
                     and r["method"] == method and boolean(r["confirmed"])]
            if not group:
                raise ValueError("Missing confirmed cohort")
            fixed_summary.append({"dataset": dataset, "cohort": cohort, "method": METHODS[method],
                                  "runs": len(group), **{k: fmean(float(r[k]) for r in group)
                                                        for k in ["recall", "fpr", "post_asr"]}})
    same_rows = []
    for r in rows("same_fpr_summary.csv"):
        if r["group"] == "successful_eligible":
            same_rows.append({"dataset": r["dataset"], "cohort": r["cohort"],
                              "method": METHODS.get(r["method"], r["method"]), "runs": int(r["runs"]),
                              "tpr": float(r["tpr_mean"]), "fpr": float(r["fpr_mean"]),
                              "pauc": float(r["standardized_partial_auc_mean"])})
    if len(same_rows) != 30:
        raise ValueError("Expected three cohorts and all ten score comparators")
    budget_rows = [{"dataset": r["dataset"], "cohort": r["cohort"], "budget": int(r["budget"]),
                    "method": METHODS.get(r["method"], r["method"]), "runs": int(r["runs"]),
                    "tpr": float(r["low_fpr_tpr"]), "fpr": float(r["low_fpr_fpr"])}
                   for r in rows("clean_budget_summary.csv") if r["cohort"] == "restricted"]
    seed_rows = []
    for r in rows("ember2024_seed_runs.csv"):
        seed_rows.append({"seed": int(r["seed"]), "origin": r["origin"], "confirmed": boolean(r["confirmed"]),
                          **{k: float(r[k]) for k in ["confirmation_asr", "confirmation_paired_gain", "asr",
                                                     "reduced_recall", "reduced_fpr", "full_recall", "full_fpr"]}})
    adaptive_rows = [{"dataset": r["dataset"], "cohort": r["cohort"], "runs": int(r["runs"]),
                      **{k: float(r[k]) for k in ["before", "after", "main_before", "main_after", "gain_pp"]}}
                     for r in rows("adaptive_summary.csv")]
    adaptive_protocol = evidence(Path("outputs/teacher_revision_2026_10_27/adaptive_multiview/protocol.json"))
    filtering_rows = [{"dataset": r["dataset"], "method": r["method"], "seed": int(r["seed"]),
                       "family": r["family"], "poison_rate": float(r["rate"]),
                       **{k: int(r[k]) for k in ["removed", "poisons_total", "poisons_removed", "benign_unpoisoned_removed"]},
                       **{k: float(r[k]) for k in ["asr_before", "asr_after", "accuracy_before", "accuracy_after"]}}
                      for r in rows("training_defense_results.csv")]
    cross_rows = [{"dataset": r["dataset"], "runs": int(r["runs"]),
                   **{k: float(r[k]) for k in ["clean_asr", "poisoned_asr", "new_evasion", "lost_evasion", "net_gain"]}}
                  for r in rows("cross_confirmation_summary.csv")]
    manifest = evidence(binary_root / "manifest.csv", csv_rows=True)
    functionality = evidence(binary_root / "functionality_results.csv", csv_rows=True)
    score_rows = evidence(binary_root / "xsentinel_scores.csv", csv_rows=True)
    features = evidence(binary_root / "feature_change_summary.csv", csv_rows=True)
    original = [r for r in manifest if r["edit_type"] == "none"]
    original_sizes = {r["fixture_type"]: int(r["file_size"]) for r in original}
    overlay_growth = {int(r["file_size"]) - original_sizes[r["fixture_type"]]
                      for r in manifest if r["edit_type"] == "benign_overlay"}
    if overlay_growth != {246}:
        raise ValueError("Unexpected overlay accounting")
    pair_keys = {(r["file_sha256"], r["model_sha256"]) for r in score_rows}
    full_rows = [r for r in score_rows if r["trigger_alert_X_F"] != ""]
    exported_names = {p.name for p in (root / binary_root).rglob("*") if p.is_file()}
    source_names = {Path(r["source_path"]).name for r in manifest}
    executable_names = {Path(r["file_path"]).name for r in manifest}
    source_files_found = len(source_names & exported_names)
    executables_found = len(executable_names & exported_names)
    wine_evidence = any("wine" in r["environment"].lower() for r in functionality)
    fixture_labels = {"native": "C x64", "dotnet": ".NET C#"}
    edit_labels = {"none": "Original", "coff_timestamp_zero": "Timestamp 0",
                   "coff_timestamp_target_2018": "Target 2018",
                   "coff_timestamp_target_2024": "Target 2024", "benign_overlay": "Overlay +246 B"}
    feature_shift_rows = [{"fixture": fixture_labels[r["fixture_type"]], "edit": edit_labels[r["edit_type"]],
                           "schema": r["schema"], "total_changed": int(r["changed_total"]),
                           "structural": int(r["changed_structural"]), "behavioral": int(r["changed_behavioral"]),
                           "metadata": int(r["changed_metadata"]), "collateral": int(r["unintended_changed"])}
                          for r in features]
    windows_rows = []
    for variant in manifest:
        cases = [r for r in functionality if r["variant_id"] == variant["variant_id"]]
        windows_rows.append({"variant": variant["variant_id"], "fixture": fixture_labels[variant["fixture_type"]],
                             "edit": edit_labels[variant["edit_type"]], "case_count": len(cases),
                             "pass_count": sum(r["status"] == "PASS" for r in cases),
                             "error_count": sum(r["status"] == "ERROR" for r in cases)})
    if (any(r["trigger_alert_X_R"] != "False" for r in score_rows)
            or any(r["trigger_alert_X_F"] != "False" for r in full_rows)
            or len(manifest) != 10 or len(features) != 16):
        raise ValueError("Unexpected binary audit results")
    for relative in ["src/xsentinel/schema.py", "src/xsentinel/detection/components.py",
                     "src/xsentinel/detection/calibration.py", "src/xsentinel/detection/detector.py"]:
        sources.append({"path": relative, "sha256": sha256((root / relative).read_bytes()).hexdigest()})
    snapshot = {
        "schema_version": SCHEMA_VERSION, "snapshot_id": "teacher-revision-2026-10-28",
        "as_of": "2026-10-28",
        "scope": {"kind": "frozen_offline_snapshot", "live_service_status": False,
                  "feature_space_attacks": True, "observed_final_reused": True,
                  "deployment_thresholds_changed": False, "rates_unit": "fraction_0_to_1",
                  "gain_pp_unit": "percentage_points"},
        "primary": {"configuration_count": len(cells), "bundle_count": 2 * len(cells),
                    "original_seeds": sorted({key[1] for key in cells}), "datasets": datasets,
                    "m5_assessed": False, "benign_reference_records": 500,
                    "benign_calibration_records": 2000, "original_clean_fit_records": 200000},
        "methods": {"Reduced": {"components": ["VMC", "BGS"], "fusion": "mean_right_reference_ecdf_ranks",
                                 "requires_clean_auxiliary_prediction": False},
                    "Full": {"components": ["VMC", "BPG"], "fusion": "mean_right_reference_ecdf_ranks",
                             "used_auxiliary_views": ["behavioral"],
                             "required_bundle_view_files": ["structural", "behavioral", "metadata"]}},
        "fixed_threshold": {"positive_group": "successful_eligible", "aggregation": "equal_run_mean",
                            "threshold_source": "original_benign_calibration", "rows": fixed_summary},
        "same_fpr": {"fpr_cap": 0.01, "positive_group": "successful_eligible", "retrospective": True,
                     "aggregation": "equal_run_mean", "pauc_definition": "sklearn_standardized_max_fpr_0.01",
                     "rows": same_rows},
        "clean_budgets": {"budgets": sorted({r["budget"] for r in budget_rows}),
                          "cohort": "confirmed_restricted", "fpr_cap": 0.01,
                          "reference_and_calibration_additional": True, "rows": budget_rows},
        "seeds": {"dataset": "EMBER2024", "family": "spread_structural", "poison_rate": 0.02,
                  "additional_seeds": [r["seed"] for r in seed_rows if r["origin"] == "additional"],
                  "attempt_count": len(seed_rows), "confirmed_count": sum(r["confirmed"] for r in seed_rows),
                  "rows": seed_rows},
        "adaptive": {"cell_count": sum(r["runs"] for r in adaptive_rows),
                     "sources_per_dataset": adaptive_protocol["samples"],
                     "max_queries_including_initial": adaptive_protocol["queries_per_input"],
                     "additional_coordinates_per_view": adaptive_protocol["extra_coordinates_per_view"],
                     "target": "Reduced", "views": adaptive_protocol["views"], "rows": adaptive_rows},
        "training_filtering": {"configuration_count": len({r["dataset"] for r in filtering_rows}),
                               "per_input_detector": False, "rows": filtering_rows},
        "cross_confirmation": {"pool": "confirmation", "denominator": "clean_original_eligible",
                               "rows": cross_rows},
        "binary_audit": {"variant_count": len(manifest), "original_count": len(original),
                         "modified_count": len(manifest) - len(original), "overlay_bytes": 246,
                         "edited_schema_cases": len(features), "functionality_cases": len(functionality),
                         "windows_pass": sum(r["status"] == "PASS" for r in functionality),
                         "windows_error": sum(r["status"] == "ERROR" for r in functionality),
                         "recorded_environments": sorted({r["environment"] for r in functionality}),
                         "wine_evidence": wine_evidence,
                         "source_and_executables_in_export": bool(source_files_found and executables_found),
                         "referenced_source_files_found": source_files_found,
                         "referenced_executables_found": executables_found,
                         "complete_binary_trigger_demonstrated": False,
                         "independent_binary_execution_by_this_build": False,
                         "scoring_rows": len(score_rows), "unique_file_main_model_pairs": len(pair_keys),
                         "main_model_count": len({r["model_sha256"] for r in score_rows}),
                         "mode_bundle_count": len({r["bundle_id"] for r in score_rows}),
                         "reduced_alerts": 0, "full_scored_rows": len(full_rows), "full_alerts": 0,
                         "feature_shift_rows": feature_shift_rows, "windows_rows": windows_rows},
        "limitations": [
            "Đây là số liệu nghiên cứu cố định ngày 28/10/2026, không phải trạng thái dịch vụ hiện tại.",
            "Các thí nghiệm đầu độc và thích nghi chỉ sửa vector đặc trưng; Cross/adaptive vẫn là điểm yếu.",
            "Ngưỡng ROC từ final đã quan sát chỉ dùng so sánh hồi cứu; ngưỡng triển khai không thay đổi.",
            "Full không luôn tốt hơn Shadow; tại 200.000 mẫu sạch, Shadow vượt trội và có quan hệ với cách định nghĩa nhóm đánh giá.",
            "Hai seed mới chỉ kiểm tra một điều kiện; nguồn dữ liệu lặp lại không phải các tập độc lập.",
            "Audit binary dùng tệp lành và log xuất; không có source/EXE để tái dựng, không chứng minh trigger đầy đủ hay recall backdoor thực tế.",
            "Kiểm thử phần mềm và hash không chứng minh hiệu quả phát hiện mọi backdoor."],
        "provenance": {"paths_relative_to": "repository_root", "sources": sources,
                       "runtime_source_verification": False,
                       "build_policy": "Read exported evidence only; no training, inference, service calls or binary execution."}}
    snapshot["content_sha256"] = snapshot_digest(snapshot)
    validate_research_status(snapshot)
    return snapshot


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true", help="Compare without writing")
    args = parser.parse_args()
    output = args.output or args.repo_root / "src/xsentinel/assets" / SNAPSHOT_NAME
    snapshot = build_snapshot(args.repo_root)
    if args.check:
        if json.loads(output.read_text(encoding="utf-8")) != snapshot:
            raise SystemExit("Packaged snapshot differs from exported evidence")
        print("Packaged research snapshot matches exported evidence")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print("Built " + str(output))


if __name__ == "__main__":
    main()
