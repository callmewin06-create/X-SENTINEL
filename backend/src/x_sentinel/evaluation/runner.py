from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from x_sentinel.evaluation.metrics import (
    ZeroEligibleSamplesError,
    compute_asr,
    compute_auroc,
    compute_fpr,
    compute_latency_summary,
    compute_recall,
)
from x_sentinel.evaluation.statistics import (
    holm_bonferroni_correction,
    mcnemar_paired_test,
    paired_auroc_comparison,
    paired_bootstrap_test,
    validate_unique_sample_ids,
)

E2_METHOD_KEYS: dict[str, str] = {
    "m1": "signal:m1",
    "m2": "signal:m2",
    "m3": "signal:m3",
    "m4": "signal:m4",
    "m5": "signal:m5",
    "reduced_fusion": "fusion_reduced_score",
    "full_fusion": "fusion_full_score",
}


class ExperimentBlockedError(RuntimeError):
    """Raised when strict scientific freeze is required but upstream blockers remain unresolved."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    if not path.is_file():
        return "MISSING"
    raw = path.read_bytes()
    return hashlib.sha256(raw).hexdigest()


def _match_file_sha256(path: Path, expected: str) -> bool:
    if not path.is_file():
        return False
    raw = path.read_bytes()
    raw_hash = hashlib.sha256(raw).hexdigest()
    if raw_hash.lower() == expected.lower():
        return True
    # Cross-platform line ending normalization (CRLF vs LF)
    crlf_hash = hashlib.sha256(raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest()
    if crlf_hash.lower() == expected.lower():
        return True
    lf_hash = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    if lf_hash.lower() == expected.lower():
        return True
    return False


def check_scientific_readiness(
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Audits repository configs and artifacts for strict scientific vs candidate readiness."""
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    blockers: list[dict[str, str]] = []

    views_sci_path = root / "configs" / "views.scientific.yaml"
    if views_sci_path.is_file():
        views_cfg = yaml.safe_load(views_sci_path.read_text(encoding="utf-8")) or {}
        if str(views_cfg.get("status", "")) != "FROZEN":
            blockers.append(
                {
                    "id": "OQ-01",
                    "component": "configs/views.scientific.yaml",
                    "status": str(views_cfg.get("status", "UNKNOWN")),
                    "reason": "Exact scientific V1/V2/V3 feature index mapping is not yet frozen.",
                }
            )
    else:
        blockers.append(
            {
                "id": "OQ-01",
                "component": "configs/views.scientific.yaml",
                "status": "MISSING",
                "reason": "Scientific view config file is missing.",
            }
        )

    model_sci_path = root / "configs" / "model.scientific.yaml"
    if model_sci_path.is_file():
        model_cfg = yaml.safe_load(model_sci_path.read_text(encoding="utf-8")) or {}
        artifact_block = model_cfg.get("artifact", {}) or {}
        if (
            str(model_cfg.get("status", "")) != "FROZEN"
            or str(artifact_block.get("expected_sha256", "TBD")) == "TBD"
        ):
            blockers.append(
                {
                    "id": "OQ-02",
                    "component": "configs/model.scientific.yaml",
                    "status": str(model_cfg.get("status", "UNKNOWN")),
                    "reason": (
                        "Strict scientific LightGBM artifact SHA-256 is not yet "
                        "promoted to model.scientific.yaml."
                    ),
                }
            )
    else:
        blockers.append(
            {
                "id": "OQ-02",
                "component": "configs/model.scientific.yaml",
                "status": "MISSING",
                "reason": "Scientific model config file is missing.",
            }
        )

    models_dir = root / "models"
    poisoned_model_files = (
        list(models_dir.glob("*poison*.txt")) + list(models_dir.glob("*poison*.lgb"))
        if models_dir.is_dir()
        else []
    )
    if len(poisoned_model_files) == 0:
        blockers.append(
            {
                "id": "MISSING_POISONED_MODELS",
                "component": "models/",
                "status": "MISSING",
                "reason": (
                    "Pre-trained frozen poisoned LightGBM artifacts "
                    "(T-concentrated, T-spread, T-cross) are not present in models/."
                ),
            }
        )

    candidate_model_path = root / "datasets" / "ember2018" / "ember_model_2018.txt"
    d1_cal_path = root / "artifacts" / "calibration" / "d1_calibration.json"
    candidate_ready = candidate_model_path.is_file() and d1_cal_path.is_file()

    return {
        "strict_scientific_ready": len(blockers) == 0,
        "candidate_ready": candidate_ready,
        "blockers": blockers,
        "candidate_artifacts": {
            "ember_model_2018_present": candidate_model_path.is_file(),
            "d1_calibration_present": d1_cal_path.is_file(),
        },
    }


@dataclass(frozen=True)
class EvaluationRunSpec:
    """Immutable run specification for an evaluation experiment."""

    run_id: str
    experiment: str
    config_hash: str
    dataset_hash: str
    seed: int
    evidence_class: str = "SYNTHETIC_TEST_FIXTURE"
    status: str = "COMPLETED"


def _extract_method_score(record: Mapping[str, Any], method_name: str) -> float:
    spec = E2_METHOD_KEYS[method_name]
    if spec.startswith("signal:"):
        sig_key = spec.split(":", 1)[1]
        signals = record.get("signals", {})
        if not isinstance(signals, Mapping) or sig_key not in signals:
            raise ValueError(f"Record '{record.get('sample_id')}' missing signal '{sig_key}'.")
        return float(signals[sig_key])
    if spec not in record:
        raise ValueError(f"Record '{record.get('sample_id')}' missing field '{spec}'.")
    return float(record[spec])


class EvaluationRunner:
    """Executes and persists E0–E5 evaluation runs with SHA-256 provenance."""

    def __init__(self, output_root: Path) -> None:
        self._output_root = Path(output_root)

    @property
    def output_root(self) -> Path:
        return self._output_root

    def run(
        self,
        spec: EvaluationRunSpec,
        *,
        require_strict_scientific_freeze: bool = False,
        repo_root: Path | None = None,
    ) -> Path:
        if require_strict_scientific_freeze:
            readiness = check_scientific_readiness(repo_root=repo_root)
            if not readiness["strict_scientific_ready"]:
                ids = ", ".join(b["id"] for b in readiness["blockers"])
                details = "; ".join(f"{b['id']}: {b['reason']}" for b in readiness["blockers"])
                raise ExperimentBlockedError(
                    f"Experiment '{spec.experiment}' (run_id='{spec.run_id}') blocked by "
                    f"unresolved scientific freeze requirements [{ids}]: {details}"
                )

        run_dir = self._output_root / spec.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = run_dir / "manifest.json"
        payload = {
            "run_id": spec.run_id,
            "experiment": spec.experiment,
            "config_hash": spec.config_hash,
            "dataset_hash": spec.dataset_hash,
            "seed": spec.seed,
            "evidence_class": spec.evidence_class,
            "status": spec.status,
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "environment": {
                "python_version": sys.version.split()[0],
                "platform": platform.platform(),
                "numpy_version": np.__version__,
            },
        }
        manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return manifest_path

    def _persist_run_bundle(
        self,
        *,
        run_id: str,
        experiment: str,
        seed: int,
        status: str,
        evidence_class: str,
        metrics_payload: dict[str, Any],
        raw_records: Sequence[Mapping[str, Any]] | None = None,
        extra_manifest: Mapping[str, Any] | None = None,
        allow_overwrite: bool = False,
    ) -> dict[str, Any]:
        run_dir = self._output_root / run_id
        manifest_path = run_dir / "manifest.json"
        if manifest_path.is_file() and not allow_overwrite:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
            if existing.get("status") in ("COMPLETED", "PARTIAL"):
                raise FileExistsError(
                    f"Evaluation run '{run_id}' already completed in {run_dir}. "
                    "Refusing silent overwrite."
                )

        run_dir.mkdir(parents=True, exist_ok=True)
        files_written: list[Path] = []

        if raw_records is not None:
            raw_path = run_dir / "raw_predictions.jsonl"
            lines = [
                json.dumps(dict(rec), sort_keys=True, separators=(",", ":")) for rec in raw_records
            ]
            raw_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            files_written.append(raw_path)

        metrics_path = run_dir / "metrics.json"
        metrics_path.write_text(
            json.dumps(metrics_payload, indent=2, sort_keys=True), encoding="utf-8"
        )
        files_written.append(metrics_path)

        manifest_data: dict[str, Any] = {
            "run_id": run_id,
            "experiment": experiment,
            "seed": seed,
            "status": status,
            "evidence_class": evidence_class,
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "environment": {
                "python_version": sys.version.split()[0],
                "platform": platform.platform(),
                "numpy_version": np.__version__,
            },
        }
        if extra_manifest is not None:
            manifest_data.update(dict(extra_manifest))

        manifest_path.write_text(
            json.dumps(manifest_data, indent=2, sort_keys=True), encoding="utf-8"
        )
        files_written.append(manifest_path)

        checksum_lines: list[str] = []
        file_digests: dict[str, str] = {}
        for fpath in sorted(files_written, key=lambda p: p.name):
            digest = _sha256_file(fpath)
            file_digests[fpath.name] = digest
            checksum_lines.append(f"{digest}  {fpath.name}")

        checksums_path = run_dir / "checksums.sha256"
        checksums_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

        return {
            "run_id": run_id,
            "experiment": experiment,
            "status": status,
            "evidence_class": evidence_class,
            "run_dir": str(run_dir),
            "metrics": metrics_payload,
            "manifest": manifest_data,
            "file_sha256": file_digests,
        }

    def run_e0_distributions(
        self,
        *,
        run_id: str,
        clean_benign_scores: Mapping[str, float] | None,
        clean_triggered_scores: Mapping[str, float] | None,
        poisoned_benign_scores: Mapping[str, float] | None,
        poisoned_triggered_scores: Mapping[str, float] | None,
        threshold: float,
        clean_benign_m1_scores: Mapping[str, float] | None = None,
        clean_triggered_m1_scores: Mapping[str, float] | None = None,
        poisoned_benign_m1_scores: Mapping[str, float] | None = None,
        poisoned_triggered_m1_scores: Mapping[str, float] | None = None,
        m1_threshold: float | None = None,
        seed: int = 42,
        evidence_class: str = "SYNTHETIC_TEST_FIXTURE",
        extra_manifest: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Executes E0 sanity check and M1/TADR + Fusion score distributions across 4 groups."""
        group_inputs: dict[str, Mapping[str, float] | None] = {
            "clean_model_benign": clean_benign_scores,
            "clean_model_triggered": clean_triggered_scores,
            "poisoned_model_benign": poisoned_benign_scores,
            "poisoned_model_triggered": poisoned_triggered_scores,
        }
        m1_inputs: dict[str, Mapping[str, float] | None] = {
            "clean_model_benign": (
                clean_benign_m1_scores
                if clean_benign_m1_scores is not None
                else clean_benign_scores
            ),
            "clean_model_triggered": (
                clean_triggered_m1_scores
                if clean_triggered_m1_scores is not None
                else clean_triggered_scores
            ),
            "poisoned_model_benign": (
                poisoned_benign_m1_scores
                if poisoned_benign_m1_scores is not None
                else poisoned_benign_scores
            ),
            "poisoned_model_triggered": (
                poisoned_triggered_m1_scores
                if poisoned_triggered_m1_scores is not None
                else poisoned_triggered_scores
            ),
        }
        m1_thresh = float(threshold if m1_threshold is None else m1_threshold)
        missing_groups: list[str] = []
        group_summaries: dict[str, Any] = {}
        m1_group_summaries: dict[str, Any] = {}
        raw_records: list[dict[str, Any]] = []

        def _summarize_score_map(
            score_map: Mapping[str, float] | None,
            group_label: str,
            thresh_val: float,
        ) -> dict[str, Any]:
            if not score_map:
                return {"status": "MISSING", "count": 0}
            validate_unique_sample_ids(list(score_map.keys()), context=f"E0[{group_label}]")
            vals = np.asarray([float(v) for v in score_map.values()], dtype=np.float64)
            if not np.all(np.isfinite(vals)):
                raise ValueError(f"Non-finite score in E0 group '{group_label}'.")
            exceed_count = int(np.sum(vals >= thresh_val))
            return {
                "status": "PRESENT",
                "count": int(len(vals)),
                "mean": float(np.mean(vals)),
                "std": float(np.std(vals, ddof=0)),
                "min": float(np.min(vals)),
                "q50": float(np.quantile(vals, 0.50)),
                "q90": float(np.quantile(vals, 0.90)),
                "q95": float(np.quantile(vals, 0.95)),
                "q99": float(np.quantile(vals, 0.99)),
                "max": float(np.max(vals)),
                "exceedance_count_at_threshold": exceed_count,
                "exceedance_rate_at_threshold": float(exceed_count) / float(len(vals)),
            }

        for group_name, score_map in group_inputs.items():
            m1_map = m1_inputs[group_name]
            summary = _summarize_score_map(score_map, group_name, threshold)
            m1_summary = _summarize_score_map(m1_map, f"{group_name}:m1_tadr", m1_thresh)
            group_summaries[group_name] = summary
            m1_group_summaries[group_name] = m1_summary
            if summary["status"] == "MISSING":
                missing_groups.append(group_name)
                continue
            assert score_map is not None
            for sid, sc in score_map.items():
                m1_val = float(m1_map[sid]) if (m1_map and sid in m1_map) else float(sc)
                raw_records.append(
                    {
                        "group": group_name,
                        "sample_id": sid,
                        "score": float(sc),
                        "m1_tadr_score": m1_val,
                        "exceeds_locked_threshold": bool(float(sc) >= threshold),
                        "m1_exceeds_threshold": bool(m1_val >= m1_thresh),
                    }
                )

        status = "COMPLETED" if len(missing_groups) == 0 else "PARTIAL"
        metrics_payload = {
            "experiment": "E0",
            "status": status,
            "locked_threshold": float(threshold),
            "m1_threshold": m1_thresh,
            "missing_groups": missing_groups,
            "groups": group_summaries,
            "m1_tadr_groups": m1_group_summaries,
        }
        res = self._persist_run_bundle(
            run_id=run_id,
            experiment="E0",
            seed=seed,
            status=status,
            evidence_class=evidence_class,
            metrics_payload=metrics_payload,
            raw_records=raw_records,
            extra_manifest=extra_manifest,
        )
        res["missing_groups"] = missing_groups
        return res

    def run_e1_attack_viability(
        self,
        *,
        run_id: str,
        sample_ids: Sequence[str],
        is_malware: Sequence[int],
        clean_model_scores: Sequence[float],
        poisoned_triggered_scores: Sequence[float],
        clean_triggered_scores: Sequence[float] | None = None,
        trigger_family: str = "T-concentrated",
        poison_rate: float = 0.01,
        malware_threshold: float = 0.50,
        viability_gate_asr: float = 0.50,
        target_asr: float = 0.85,
        seed: int = 42,
        evidence_class: str = "SYNTHETIC_TEST_FIXTURE",
        status: str = "COMPLETED",
        extra_manifest: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Executes E1 attack viability and clean-trigger control evaluation (Task 14.6)."""
        asr_res = compute_asr(
            is_malware=is_malware,
            clean_model_scores=clean_model_scores,
            poisoned_triggered_scores=poisoned_triggered_scores,
            malware_threshold=malware_threshold,
            clean_triggered_scores=clean_triggered_scores,
            sample_ids=sample_ids,
        )
        confirmed_viable = bool(asr_res.asr > viability_gate_asr)
        meets_target = bool(asr_res.asr >= target_asr)

        raw_records: list[dict[str, Any]] = []
        for idx, sid in enumerate(sample_ids):
            rec: dict[str, Any] = {
                "sample_id": sid,
                "is_malware": int(is_malware[idx]),
                "clean_model_score": float(clean_model_scores[idx]),
                "poisoned_triggered_score": float(poisoned_triggered_scores[idx]),
                "eligible_for_asr": bool(
                    int(is_malware[idx]) == 1
                    and float(clean_model_scores[idx]) >= malware_threshold
                ),
            }
            if clean_triggered_scores is not None:
                rec["clean_triggered_score"] = float(clean_triggered_scores[idx])
            raw_records.append(rec)

        metrics_payload = {
            "experiment": "E1",
            "trigger_family": trigger_family,
            "poison_rate": float(poison_rate),
            "malware_threshold": float(malware_threshold),
            "viability_gate_asr": float(viability_gate_asr),
            "target_asr": float(target_asr),
            "confirmed_viable": confirmed_viable,
            "meets_production_target": meets_target,
            **asr_res.to_dict(),
        }
        return self._persist_run_bundle(
            run_id=run_id,
            experiment="E1",
            seed=seed,
            status=status,
            evidence_class=evidence_class,
            metrics_payload=metrics_payload,
            raw_records=raw_records,
            extra_manifest=extra_manifest,
        )

    def run_e2_detector_comparison(
        self,
        *,
        run_id: str,
        records: Sequence[Mapping[str, Any]],
        locked_threshold: float,
        threshold_id: str = "CALIB-D1-BENIGN-EMBER2018-v1",
        malware_threshold: float = 0.50,
        seed: int = 42,
        evidence_class: str = "SYNTHETIC_TEST_FIXTURE",
        status: str = "COMPLETED",
        extra_manifest: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Executes E2 main detector comparison across M1..M5, Reduced Fusion, and Full Fusion."""
        if len(records) == 0:
            raise ValueError("E2 records cannot be empty.")
        s_ids = validate_unique_sample_ids(
            [str(r.get("sample_id", "")) for r in records], context="E2"
        )
        labels = [int(r["label"]) for r in records]
        is_mal = [int(r.get("is_malware", r["label"])) for r in records]
        clean_scores = [
            float(r.get("clean_model_score", 0.95 if m == 1 else 0.05))
            for r, m in zip(records, is_mal, strict=True)
        ]
        pois_scores = [
            float(r.get("poisoned_triggered_score", 0.10 if m == 1 else 0.05))
            for r, m in zip(records, is_mal, strict=True)
        ]

        eligible_attack_mask = [
            (m == 1) and (cs >= malware_threshold) and (ps < malware_threshold)
            for m, cs, ps in zip(is_mal, clean_scores, pois_scores, strict=True)
        ]
        has_eligible_attacks = any(eligible_attack_mask)

        methods_summary: dict[str, Any] = {}
        for method_name in E2_METHOD_KEYS:
            scores = [_extract_method_score(r, method_name) for r in records]
            auroc_val = compute_auroc(labels, scores, sample_ids=s_ids)
            fpr_res = compute_fpr(labels, scores, threshold=locked_threshold, sample_ids=s_ids)
            rec_trig = compute_recall(
                labels,
                scores,
                threshold=locked_threshold,
                recall_kind="triggered_malware",
                sample_ids=s_ids,
            )

            rec_elig_dict: dict[str, Any] | None = None
            if has_eligible_attacks:
                rec_elig = compute_recall(
                    labels,
                    scores,
                    threshold=locked_threshold,
                    eligible_mask=eligible_attack_mask,
                    recall_kind="successful_eligible_attack",
                    sample_ids=s_ids,
                )
                rec_elig_dict = rec_elig.to_dict()

            try:
                asr_res = compute_asr(
                    is_malware=is_mal,
                    clean_model_scores=clean_scores,
                    poisoned_triggered_scores=pois_scores,
                    malware_threshold=malware_threshold,
                    detector_decisions_or_scores=scores,
                    detector_threshold=locked_threshold,
                    sample_ids=s_ids,
                )
                asr_dict: dict[str, Any] | None = asr_res.to_dict()
            except ZeroEligibleSamplesError:
                asr_dict = None

            methods_summary[method_name] = {
                "auroc": auroc_val,
                "fpr": fpr_res.to_dict(),
                "recall_triggered_malware": rec_trig.to_dict(),
                "recall_successful_eligible_attack": rec_elig_dict,
                "asr_analysis": asr_dict,
            }

        metrics_payload = {
            "experiment": "E2",
            "threshold_id": threshold_id,
            "locked_threshold": float(locked_threshold),
            "sample_count": len(records),
            "methods": methods_summary,
        }
        return self._persist_run_bundle(
            run_id=run_id,
            experiment="E2",
            seed=seed,
            status=status,
            evidence_class=evidence_class,
            metrics_payload=metrics_payload,
            raw_records=records,
            extra_manifest=extra_manifest,
        )

    def run_e3_paired_catch_miss(
        self,
        *,
        run_id: str,
        records: Sequence[Mapping[str, Any]],
        locked_threshold: float,
        seed: int = 42,
        evidence_class: str = "SYNTHETIC_TEST_FIXTURE",
        status: str = "COMPLETED",
        extra_manifest: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Executes E3 paired sample-level catch/miss concordance analysis across detectors."""
        validate_unique_sample_ids([str(r.get("sample_id", "")) for r in records], context="E3")
        pos_records = [r for r in records if int(r["label"]) == 1]
        if len(pos_records) == 0:
            raise ValueError("E3 requires at least one positive/attack sample (label=1).")

        pos_ids = [str(r["sample_id"]) for r in pos_records]
        pair_specs = [
            ("m1_vs_m4", "m1", "m4"),
            ("m1_vs_reduced_fusion", "m1", "reduced_fusion"),
            ("m4_vs_reduced_fusion", "m4", "reduced_fusion"),
            ("reduced_fusion_vs_full_fusion", "reduced_fusion", "full_fusion"),
        ]

        pairs_out: dict[str, Any] = {}
        for pair_key, method_a, method_b in pair_specs:
            out_a = [
                1 if _extract_method_score(r, method_a) >= locked_threshold else 0
                for r in pos_records
            ]
            out_b = [
                1 if _extract_method_score(r, method_b) >= locked_threshold else 0
                for r in pos_records
            ]
            mcn = mcnemar_paired_test(out_a, out_b, sample_ids=pos_ids)
            a_only_ids = [
                pos_ids[i] for i in range(len(pos_ids)) if out_a[i] == 1 and out_b[i] == 0
            ]
            b_only_ids = [
                pos_ids[i] for i in range(len(pos_ids)) if out_a[i] == 0 and out_b[i] == 1
            ]
            pairs_out[pair_key] = {
                "method_a": method_a,
                "method_b": method_b,
                "both_detect": mcn.both_positive,
                "a_only": mcn.a_only,
                "b_only": mcn.b_only,
                "neither": mcn.neither,
                "total_attack_samples": mcn.total_pairs,
                "a_only_sample_ids": a_only_ids,
                "b_only_sample_ids": b_only_ids,
                "mcnemar": mcn.to_dict(),
            }

        metrics_payload = {
            "experiment": "E3",
            "locked_threshold": float(locked_threshold),
            "positive_sample_count": len(pos_records),
            "pairs": pairs_out,
        }
        return self._persist_run_bundle(
            run_id=run_id,
            experiment="E3",
            seed=seed,
            status=status,
            evidence_class=evidence_class,
            metrics_payload=metrics_payload,
            raw_records=pos_records,
            extra_manifest=extra_manifest,
        )

    def run_e4_ablation(
        self,
        *,
        run_id: str,
        records: Sequence[Mapping[str, Any]],
        locked_threshold: float,
        seed: int = 42,
        evidence_class: str = "SYNTHETIC_TEST_FIXTURE",
        status: str = "COMPLETED",
        extra_manifest: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Executes E4 paired ablation study comparing Full Fusion, Reduced Fusion, and signals."""
        s_ids = validate_unique_sample_ids(
            [str(r.get("sample_id", "")) for r in records], context="E4"
        )
        labels = [int(r["label"]) for r in records]
        all_cluster_ids = [
            str(r.get("base_sample_id") or r.get("cluster_id") or s_ids[idx])
            for idx, r in enumerate(records)
        ]
        pos_indices = [i for i, lbl in enumerate(labels) if lbl == 1]
        pos_ids = [s_ids[i] for i in pos_indices]
        pos_cluster_ids = [all_cluster_ids[i] for i in pos_indices]

        def _compare_pair(higher_method: str, baseline_method: str) -> dict[str, Any]:
            scores_hi = [_extract_method_score(r, higher_method) for r in records]
            scores_lo = [_extract_method_score(r, baseline_method) for r in records]

            rec_hi = compute_recall(labels, scores_hi, threshold=locked_threshold, sample_ids=s_ids)
            rec_lo = compute_recall(labels, scores_lo, threshold=locked_threshold, sample_ids=s_ids)
            fpr_hi = compute_fpr(labels, scores_hi, threshold=locked_threshold, sample_ids=s_ids)
            fpr_lo = compute_fpr(labels, scores_lo, threshold=locked_threshold, sample_ids=s_ids)

            delong_res = paired_auroc_comparison(
                labels,
                scores_hi,
                scores_lo,
                sample_ids=s_ids,
                cluster_ids=all_cluster_ids,
                method="delong",
                seed=seed,
            )
            boot_diff = paired_bootstrap_test(
                [scores_hi[i] for i in pos_indices],
                [scores_lo[i] for i in pos_indices],
                sample_ids=pos_ids,
                cluster_ids=pos_cluster_ids,
                n_boot=500,
                seed=seed,
            )
            det_hi = [1 if scores_hi[i] >= locked_threshold else 0 for i in pos_indices]
            det_lo = [1 if scores_lo[i] >= locked_threshold else 0 for i in pos_indices]
            mcn_res = mcnemar_paired_test(det_hi, det_lo, sample_ids=pos_ids)

            return {
                "target_method": higher_method,
                "baseline_method": baseline_method,
                "delta_auroc": delong_res.delta_auroc,
                "delta_recall": rec_hi.recall - rec_lo.recall,
                "delta_fpr": fpr_hi.fpr - fpr_lo.fpr,
                "paired_auroc_delong": delong_res.to_dict(),
                "paired_score_bootstrap": boot_diff.to_dict(),
                "mcnemar_detection": mcn_res.to_dict(),
            }

        comp_full_red = _compare_pair("full_fusion", "reduced_fusion")
        comp_red_m1 = _compare_pair("reduced_fusion", "m1")
        comp_red_m4 = _compare_pair("reduced_fusion", "m4")
        comp_m4_m1 = _compare_pair("m4", "m1")

        holm = holm_bonferroni_correction(
            p_values=[
                comp_full_red["paired_auroc_delong"]["p_value"],
                comp_red_m1["paired_auroc_delong"]["p_value"],
                comp_red_m4["paired_auroc_delong"]["p_value"],
                comp_m4_m1["paired_auroc_delong"]["p_value"],
            ],
            alpha=0.05,
            hypothesis_ids=[
                "full_vs_reduced",
                "reduced_vs_m1",
                "reduced_vs_m4",
                "m4_vs_m1",
            ],
        )

        metrics_payload = {
            "experiment": "E4",
            "locked_threshold": float(locked_threshold),
            "full_vs_reduced": comp_full_red,
            "reduced_vs_m1": comp_red_m1,
            "reduced_vs_m4": comp_red_m4,
            "m4_vs_m1": comp_m4_m1,
            "multiple_comparison": holm.to_dict(),
        }
        return self._persist_run_bundle(
            run_id=run_id,
            experiment="E4",
            seed=seed,
            status=status,
            evidence_class=evidence_class,
            metrics_payload=metrics_payload,
            raw_records=records,
            extra_manifest=extra_manifest,
        )

    def run_e5_fpr_latency(
        self,
        *,
        run_id: str,
        records: Sequence[Mapping[str, Any]],
        locked_threshold: float,
        warmup_count: int = 0,
        seed: int = 42,
        evidence_class: str = "SYNTHETIC_TEST_FIXTURE",
        status: str = "COMPLETED",
        extra_manifest: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Executes E5 held-out benign FPR, subgroup audit, and scoped latency benchmarking."""
        s_ids = validate_unique_sample_ids(
            [str(r.get("sample_id", "")) for r in records], context="E5"
        )
        labels = [int(r["label"]) for r in records]
        full_scores = [_extract_method_score(r, "full_fusion") for r in records]
        red_scores = [_extract_method_score(r, "reduced_fusion") for r in records]

        fpr_full = compute_fpr(labels, full_scores, threshold=locked_threshold, sample_ids=s_ids)
        fpr_red = compute_fpr(labels, red_scores, threshold=locked_threshold, sample_ids=s_ids)

        subgroups_out: dict[str, Any] = {}
        for sg_name in ("standard_benign", "signed_packed_benign", "rare_benign"):
            sg_records = [
                r
                for r in records
                if int(r["label"]) == 0 and str(r.get("benign_subgroup", "")) == sg_name
            ]
            if len(sg_records) == 0:
                subgroups_out[sg_name] = {
                    "status": "BLOCKED_MISSING_SUBGROUP_LABELS",
                    "reason": (
                        f"Dataset records do not carry verified '{sg_name}' PE metadata tags "
                        "in pure feature-vector format."
                    ),
                }
            else:
                sg_ids = [str(r["sample_id"]) for r in sg_records]
                sg_labels = [0] * len(sg_records)
                sg_scores = [_extract_method_score(r, "full_fusion") for r in sg_records]
                sg_fpr = compute_fpr(
                    sg_labels, sg_scores, threshold=locked_threshold, sample_ids=sg_ids
                )
                subgroups_out[sg_name] = {
                    "status": "COMPLETED",
                    **sg_fpr.to_dict(),
                }

        scope_buckets: dict[str, list[float]] = {}
        for r in records:
            lat_map = r.get("latency_ms", {})
            if isinstance(lat_map, Mapping):
                for sc_name, dur in lat_map.items():
                    scope_buckets.setdefault(str(sc_name), []).append(float(dur))

        latency_by_scope: dict[str, Any] = {}
        for sc_name, durs in scope_buckets.items():
            eff_warmup = warmup_count if len(durs) > warmup_count else 0
            summary = compute_latency_summary(durs, scope=sc_name, warmup_count=eff_warmup)
            latency_by_scope[sc_name] = summary.to_dict()

        metrics_payload = {
            "experiment": "E5",
            "locked_threshold": float(locked_threshold),
            "held_out_benign_fpr": fpr_full.to_dict(),
            "held_out_benign_fpr_reduced_fusion": fpr_red.to_dict(),
            "benign_subgroups": subgroups_out,
            "latency_by_scope": latency_by_scope,
        }
        return self._persist_run_bundle(
            run_id=run_id,
            experiment="E5",
            seed=seed,
            status=status,
            evidence_class=evidence_class,
            metrics_payload=metrics_payload,
            raw_records=records,
            extra_manifest=extra_manifest,
        )


def verify_run_artifacts(run_dir: Path) -> dict[str, Any]:
    """Audits an evaluation run directory for completeness and SHA-256 checksum integrity."""
    run_path = Path(run_dir)
    manifest_path = run_path / "manifest.json"
    metrics_path = run_path / "metrics.json"
    raw_path = run_path / "raw_predictions.jsonl"
    checksums_path = run_path / "checksums.sha256"

    missing_files = [
        p.name
        for p in (manifest_path, metrics_path, raw_path, checksums_path)
        if not p.is_file()
    ]
    if missing_files:
        status_val = "INCOMPLETE"
        if manifest_path.is_file():
            try:
                m_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                if m_data.get("status") == "INCOMPLETE":
                    status_val = "INCOMPLETE"
            except Exception:
                pass
        return {
            "status": status_val,
            "checksum_verified": False,
            "missing_files": missing_files,
            "mismatched_files": [],
        }

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest_data.get("status") == "INCOMPLETE":
        return {
            "status": "INCOMPLETE",
            "checksum_verified": False,
            "missing_files": [],
            "mismatched_files": [],
        }

    mismatched_files: list[str] = []
    expected_map: dict[str, str] = {}
    for line in checksums_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(None, 1)
        if len(parts) != 2:
            mismatched_files.append("checksums.sha256")
            continue
        expected_digest, fname = parts[0].strip(), parts[1].strip()
        expected_map[fname] = expected_digest
        if not _match_file_sha256(run_path / fname, expected_digest):
            mismatched_files.append(fname)

    for req_name in ("manifest.json", "metrics.json", "raw_predictions.jsonl"):
        if req_name not in expected_map and req_name not in mismatched_files:
            mismatched_files.append(req_name)

    if mismatched_files:
        return {
            "status": "CORRUPTED",
            "checksum_verified": False,
            "missing_files": [],
            "mismatched_files": mismatched_files,
        }

    return {
        "status": str(manifest_data.get("status", "COMPLETED")),
        "checksum_verified": True,
        "missing_files": [],
        "mismatched_files": [],
    }


def recompute_metrics_from_raw(run_dir: Path) -> dict[str, Any]:
    """Verifies SHA-256 checksums and independently recomputes E0-E5 metrics from raw JSONL."""
    run_path = Path(run_dir)
    raw_path = run_path / "raw_predictions.jsonl"
    metrics_path = run_path / "metrics.json"
    if not raw_path.is_file() or not metrics_path.is_file():
        raise FileNotFoundError(f"Missing raw_predictions.jsonl or metrics.json in {run_path}.")

    verify_res = verify_run_artifacts(run_path)
    if not verify_res["checksum_verified"]:
        raise ValueError(
            f"Artifact checksum mismatch or incomplete run in {run_path}: {verify_res}"
        )

    records = [
        json.loads(line)
        for line in raw_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    persisted = json.loads(metrics_path.read_text(encoding="utf-8"))
    experiment = str(persisted.get("experiment", "E2"))
    mismatches: list[str] = []

    if experiment == "E0":
        thresh = float(persisted["locked_threshold"])
        recomputed_groups: dict[str, Any] = {}
        for grp_name, grp_meta in persisted.get("groups", {}).items():
            if grp_meta.get("status") == "MISSING":
                continue
            grp_scores = [
                float(r["score"]) for r in records if str(r.get("group")) == grp_name
            ]
            if len(grp_scores) != int(grp_meta["count"]):
                mismatches.append(f"{grp_name}.count")
            mean_val = float(np.mean(grp_scores))
            exc_rate = float(np.sum(np.asarray(grp_scores) >= thresh)) / float(len(grp_scores))
            if not math.isclose(mean_val, float(grp_meta["mean"]), abs_tol=1e-12):
                mismatches.append(f"{grp_name}.mean")
            if not math.isclose(
                exc_rate, float(grp_meta["exceedance_rate_at_threshold"]), abs_tol=1e-12
            ):
                mismatches.append(f"{grp_name}.exceedance_rate_at_threshold")
            recomputed_groups[grp_name] = {
                "count": len(grp_scores),
                "mean": mean_val,
                "exceedance_rate_at_threshold": exc_rate,
            }
        return {
            "experiment": "E0",
            "checksum_verified": True,
            "verified_match": len(mismatches) == 0,
            "mismatches": mismatches,
            "recomputed_groups": recomputed_groups,
        }

    if experiment == "E1":
        s_ids = [str(r["sample_id"]) for r in records]
        is_mal = [int(r["is_malware"]) for r in records]
        clean_sc = [float(r["clean_model_score"]) for r in records]
        pois_sc = [float(r["poisoned_triggered_score"]) for r in records]
        clean_trig_sc = (
            [float(r["clean_triggered_score"]) for r in records]
            if all("clean_triggered_score" in r for r in records)
            else None
        )
        mal_thresh = float(persisted.get("malware_threshold", 0.50))
        asr_res = compute_asr(
            is_malware=is_mal,
            clean_model_scores=clean_sc,
            poisoned_triggered_scores=pois_sc,
            malware_threshold=mal_thresh,
            clean_triggered_scores=clean_trig_sc,
            sample_ids=s_ids,
        )
        if not math.isclose(asr_res.asr, float(persisted["asr"]), abs_tol=1e-12):
            mismatches.append("asr")
        if asr_res.eligible_count != int(persisted["eligible_count"]):
            mismatches.append("eligible_count")
        if asr_res.successful_attack_count != int(persisted["successful_attack_count"]):
            mismatches.append("successful_attack_count")
        return {
            "experiment": "E1",
            "checksum_verified": True,
            "verified_match": len(mismatches) == 0,
            "mismatches": mismatches,
            "recomputed_asr": asr_res.to_dict(),
        }

    if experiment == "E3":
        locked_threshold = float(persisted["locked_threshold"])
        pos_records = [r for r in records if int(r.get("label", 1)) == 1]
        pos_ids = [str(r["sample_id"]) for r in pos_records]
        recomputed_pairs: dict[str, Any] = {}
        for pair_key, pair_meta in persisted.get("pairs", {}).items():
            method_a = str(pair_meta["method_a"])
            method_b = str(pair_meta["method_b"])
            out_a = [
                1 if _extract_method_score(r, method_a) >= locked_threshold else 0
                for r in pos_records
            ]
            out_b = [
                1 if _extract_method_score(r, method_b) >= locked_threshold else 0
                for r in pos_records
            ]
            mcn = mcnemar_paired_test(out_a, out_b, sample_ids=pos_ids)
            if mcn.both_positive != int(pair_meta["both_detect"]):
                mismatches.append(f"{pair_key}.both_detect")
            if mcn.a_only != int(pair_meta["a_only"]):
                mismatches.append(f"{pair_key}.a_only")
            if mcn.b_only != int(pair_meta["b_only"]):
                mismatches.append(f"{pair_key}.b_only")
            if not math.isclose(
                mcn.p_value, float(pair_meta["mcnemar"]["p_value"]), abs_tol=1e-12
            ):
                mismatches.append(f"{pair_key}.p_value")
            recomputed_pairs[pair_key] = mcn.to_dict()
        return {
            "experiment": "E3",
            "checksum_verified": True,
            "verified_match": len(mismatches) == 0,
            "mismatches": mismatches,
            "recomputed_pairs": recomputed_pairs,
        }

    if experiment == "E4":
        locked_threshold = float(persisted["locked_threshold"])
        s_ids = [str(r["sample_id"]) for r in records]
        labels = [int(r["label"]) for r in records]
        all_cluster_ids = [
            str(r.get("base_sample_id") or r.get("cluster_id") or s_ids[idx])
            for idx, r in enumerate(records)
        ]
        recomputed_comparisons: dict[str, Any] = {}
        for comp_key in ("full_vs_reduced", "reduced_vs_m1", "reduced_vs_m4", "m4_vs_m1"):
            if comp_key not in persisted:
                continue
            comp_meta = persisted[comp_key]
            m_hi = str(comp_meta["target_method"])
            m_lo = str(comp_meta["baseline_method"])
            sc_hi = [_extract_method_score(r, m_hi) for r in records]
            sc_lo = [_extract_method_score(r, m_lo) for r in records]
            delong_res = paired_auroc_comparison(
                labels, sc_hi, sc_lo, sample_ids=s_ids, cluster_ids=all_cluster_ids, method="delong"
            )
            rec_hi = compute_recall(labels, sc_hi, threshold=locked_threshold, sample_ids=s_ids)
            rec_lo = compute_recall(labels, sc_lo, threshold=locked_threshold, sample_ids=s_ids)
            if not math.isclose(
                delong_res.delta_auroc, float(comp_meta["delta_auroc"]), abs_tol=1e-12
            ):
                mismatches.append(f"{comp_key}.delta_auroc")
            if not math.isclose(
                rec_hi.recall - rec_lo.recall, float(comp_meta["delta_recall"]), abs_tol=1e-12
            ):
                mismatches.append(f"{comp_key}.delta_recall")
            recomputed_comparisons[comp_key] = {
                "delta_auroc": delong_res.delta_auroc,
                "delta_recall": rec_hi.recall - rec_lo.recall,
            }
        return {
            "experiment": "E4",
            "checksum_verified": True,
            "verified_match": len(mismatches) == 0,
            "mismatches": mismatches,
            "recomputed_comparisons": recomputed_comparisons,
        }

    if experiment == "E5":
        locked_threshold = float(persisted["locked_threshold"])
        s_ids = [str(r["sample_id"]) for r in records]
        labels = [int(r["label"]) for r in records]
        full_scores = [_extract_method_score(r, "full_fusion") for r in records]
        red_scores = [_extract_method_score(r, "reduced_fusion") for r in records]
        fpr_full = compute_fpr(labels, full_scores, threshold=locked_threshold, sample_ids=s_ids)
        fpr_red = compute_fpr(labels, red_scores, threshold=locked_threshold, sample_ids=s_ids)
        if not math.isclose(
            fpr_full.fpr, float(persisted["held_out_benign_fpr"]["fpr"]), abs_tol=1e-12
        ):
            mismatches.append("held_out_benign_fpr.fpr")
        if not math.isclose(
            fpr_red.fpr,
            float(persisted["held_out_benign_fpr_reduced_fusion"]["fpr"]),
            abs_tol=1e-12,
        ):
            mismatches.append("held_out_benign_fpr_reduced_fusion.fpr")
        return {
            "experiment": "E5",
            "checksum_verified": True,
            "verified_match": len(mismatches) == 0,
            "mismatches": mismatches,
            "recomputed_fpr": {
                "full_fusion": fpr_full.fpr,
                "reduced_fusion": fpr_red.fpr,
            },
        }

    locked_threshold = float(persisted["locked_threshold"])
    s_ids = [str(r["sample_id"]) for r in records]
    labels = [int(r["label"]) for r in records]

    recomputed_methods: dict[str, Any] = {}
    for method_name, persisted_m in persisted.get("methods", {}).items():
        scores = [_extract_method_score(r, method_name) for r in records]
        auroc_val = compute_auroc(labels, scores, sample_ids=s_ids)
        fpr_res = compute_fpr(labels, scores, threshold=locked_threshold, sample_ids=s_ids)
        rec_res = compute_recall(labels, scores, threshold=locked_threshold, sample_ids=s_ids)

        if not math.isclose(auroc_val, float(persisted_m["auroc"]), abs_tol=1e-12):
            mismatches.append(f"{method_name}.auroc")
        if not math.isclose(fpr_res.fpr, float(persisted_m["fpr"]["fpr"]), abs_tol=1e-12):
            mismatches.append(f"{method_name}.fpr")
        if not math.isclose(
            rec_res.recall,
            float(persisted_m["recall_triggered_malware"]["recall"]),
            abs_tol=1e-12,
        ):
            mismatches.append(f"{method_name}.recall")

        recomputed_methods[method_name] = {
            "auroc": auroc_val,
            "fpr": fpr_res.fpr,
            "recall": rec_res.recall,
        }

    return {
        "experiment": "E2",
        "checksum_verified": True,
        "verified_match": len(mismatches) == 0,
        "mismatches": mismatches,
        "recomputed_methods": recomputed_methods,
    }


def execute_candidate_e0_to_e5_suite(
    *,
    output_root: Path = Path("artifacts/evaluation/be14_candidate_suite"),
    repo_root: Path | None = None,
    n_benign: int = 25,
    n_malware: int = 25,
    seed: int = 42,
    allow_overwrite: bool = True,
) -> dict[str, Any]:
    """Executes the E0-E5 frozen-candidate suite on real EMBER2018 vectors and D1 calibration."""
    import time

    from x_sentinel.data.views import load_view_map
    from x_sentinel.detection.pipeline import DetectorPipeline
    from x_sentinel.evaluation.blind import (
        BlindCustodyGuard,
        BlindEvaluator,
        BlindGroundTruthManifest,
        BlindPredictionPackage,
        BlindSamplePrediction,
        EvaluationRole,
    )
    from x_sentinel.evaluation.protocol import (
        TRIGGER_FAMILIES,
        DatasetSplitManifest,
        SplitRole,
        TriggerSpec,
        apply_vector_trigger,
        audit_dataset_splits,
    )
    from x_sentinel.fusion.calibration import CalibrationArtifact
    from x_sentinel.fusion.config import load_fusion_config
    from x_sentinel.fusion.decision import DecisionPolicy
    from x_sentinel.fusion.engine import WeightedSumFusion
    from x_sentinel.model.lightgbm_service import load_model_service

    root = Path(repo_root) if repo_root is not None else Path.cwd()
    readiness = check_scientific_readiness(repo_root=root)

    x_test_path = root / "datasets" / "ember2018" / "X_test.dat"
    y_test_path = root / "datasets" / "ember2018" / "y_test.dat"
    model_cfg_path = root / "configs" / "model.ember2018.yaml"
    views_cfg_path = root / "configs" / "views.demo.yaml"
    det_cfg_path = root / "configs" / "detector.yaml"
    fus_cfg_path = root / "configs" / "fusion.scientific.yaml"
    cal_art_path = root / "artifacts" / "calibration" / "d1_calibration.json"

    for req_path in (
        x_test_path,
        y_test_path,
        model_cfg_path,
        views_cfg_path,
        det_cfg_path,
        fus_cfg_path,
        cal_art_path,
    ):
        if not req_path.is_file():
            raise FileNotFoundError(f"Required candidate evaluation file missing: {req_path}")

    defense_guard = BlindCustodyGuard(role=EvaluationRole.DEFENSE_DETECTOR)
    defense_guard.assert_environment_clean()
    for defense_accessible_path in (
        x_test_path,
        model_cfg_path,
        views_cfg_path,
        det_cfg_path,
        fus_cfg_path,
        cal_art_path,
    ):
        defense_guard.assert_path_allowed(defense_accessible_path)

    cal_artifact = CalibrationArtifact.load(cal_art_path)
    locked_threshold = float(cal_artifact.threshold)
    threshold_id = str(cal_artifact.artifact_id)

    fusion_layer_cfg = load_fusion_config(fus_cfg_path)
    full_weights = dict(fusion_layer_cfg.fusion.weights)
    full_fuser = WeightedSumFusion(full_weights)

    w_m14 = sum(w for k, w in full_weights.items() if k != "m5")
    red_weights = {k: (w / w_m14 if k != "m5" else 0.0) for k, w in full_weights.items()}
    reduced_fuser = WeightedSumFusion(red_weights)

    decision_policy = DecisionPolicy(
        alert_threshold=locked_threshold,
        quarantine_threshold=max(
            locked_threshold, float(fusion_layer_cfg.calibration.quarantine_threshold)
        ),
    )

    model_service = load_model_service(model_cfg_path, allow_demo=False)
    view_map = load_view_map(views_cfg_path, allow_demo=True)

    y_mmap = np.memmap(y_test_path, dtype=np.float32, mode="r", shape=(200000,))
    x_mmap = np.memmap(x_test_path, dtype=np.float32, mode="r", shape=(200000, 2381))

    benign_indices = np.flatnonzero(y_mmap == 0.0)
    malware_indices = np.flatnonzero(y_mmap == 1.0)

    # Indices 0..999 reserved for D1 calibration; 1000..1031 reserved for M2 STRIP benign pool;
    # 5000..5000+n_benign reserved for held-out blind evaluation benign set.
    cal_idx = benign_indices[:1000]
    pool_idx = benign_indices[1000:1032]
    eval_ben_idx = benign_indices[5000 : 5000 + n_benign]
    eval_mal_idx = malware_indices[5000 : 5000 + n_malware]

    cal_split = DatasetSplitManifest(
        dataset_name="ember2018",
        dataset_version="2018-v2-test",
        role=SplitRole.D1_CALIBRATION,
        sample_ids=tuple(f"ember_test_{int(i)}" for i in cal_idx),
        labels=tuple(0 for _ in cal_idx),
        seed=seed,
    )
    eval_split = DatasetSplitManifest(
        dataset_name="ember2018",
        dataset_version="2018-v2-test",
        role=SplitRole.FINAL_BLIND_EVALUATION,
        sample_ids=tuple(
            [f"ember_test_{int(i)}" for i in eval_ben_idx]
            + [f"ember_test_{int(i)}" for i in eval_mal_idx]
        ),
        labels=tuple([0] * len(eval_ben_idx) + [1] * len(eval_mal_idx)),
        seed=seed,
    )
    split_audit = audit_dataset_splits([cal_split, eval_split])

    benign_pool = [np.asarray(x_mmap[int(i)], dtype=np.float64).tolist() for i in pool_idx]
    pipeline = DetectorPipeline(
        config=det_cfg_path,
        model_service=model_service,
        view_map=view_map,
        benign_pool=benign_pool,
    )

    # Execute explicit warmup iterations prior to timed evaluation runs (Task 14.10.2)
    warmup_iterations = 3
    for warm_vec in benign_pool[:warmup_iterations]:
        _, warm_shap = model_service.infer(warm_vec)
        pipeline.evaluate(warm_vec, model_service=model_service, shap_values=warm_shap)

    provenance_hashes: dict[str, Any] = {
        "model_config_sha256": _sha256_file(model_cfg_path),
        "model_artifact_sha256": str(
            getattr(model_service, "actual_sha256", None)
            or _sha256_file(root / "datasets" / "ember2018" / "ember_model_2018.txt")
        ),
        "view_map_sha256": _sha256_file(views_cfg_path),
        "detector_config_sha256": _sha256_file(det_cfg_path),
        "fusion_config_sha256": _sha256_file(fus_cfg_path),
        "d1_calibration_sha256": _sha256_file(cal_art_path),
        "split_audit": split_audit,
        "scientific_readiness": readiness,
    }

    # Evaluate clean held-out benign vectors once
    benign_records: list[dict[str, Any]] = []
    clean_benign_fusion_map: dict[str, float] = {}
    clean_benign_m1_map: dict[str, float] = {}
    for raw_i in eval_ben_idx:
        sid = f"ember_test_{int(raw_i)}"
        vec = np.asarray(x_mmap[int(raw_i)], dtype=np.float64).tolist()
        defense_guard.assert_defense_input_clean({"sample_id": sid, "features": vec})
        t0 = time.perf_counter()
        c_score, c_shap = model_service.infer(vec)
        t_det0 = time.perf_counter()
        sig_res = pipeline.evaluate(vec, model_service=model_service, shap_values=c_shap)
        sig_scores = {k: float(v.score) for k, v in sig_res.items()}
        red_score = reduced_fuser.fuse(sig_scores)
        full_score = full_fuser.fuse(sig_scores)
        t_end = time.perf_counter()

        det_ms = (t_end - t_det0) * 1000.0
        e2e_ms = (t_end - t0) * 1000.0
        clean_benign_fusion_map[sid] = full_score
        clean_benign_m1_map[sid] = float(sig_scores["m1"])
        benign_records.append(
            {
                "sample_id": sid,
                "base_sample_id": sid,
                "label": 0,
                "is_malware": 0,
                "clean_model_score": float(c_score),
                "poisoned_triggered_score": float(c_score),
                "signals": sig_scores,
                "fusion_reduced_score": red_score,
                "fusion_full_score": full_score,
                "decision": decision_policy.evaluate(full_score).decision,
                "latency_ms": {
                    "detector_only": det_ms,
                    "end_to_end": e2e_ms,
                    "EndToEnd_WithSHAP": e2e_ms,
                },
            }
        )

    runner = EvaluationRunner(output_root=output_root)
    if allow_overwrite and output_root.exists():
        import shutil

        shutil.rmtree(output_root)

    clean_mal_base_vecs: dict[int, list[float]] = {}
    clean_mal_scores_map: dict[int, float] = {}
    for raw_i in eval_mal_idx:
        idx_int = int(raw_i)
        b_vec = np.asarray(x_mmap[idx_int], dtype=np.float64).tolist()
        clean_mal_base_vecs[idx_int] = b_vec
        c_sc, _ = model_service.infer(b_vec)
        clean_mal_scores_map[idx_int] = float(c_sc)

    family_results: dict[str, Any] = {}
    all_records_pooled: list[dict[str, Any]] = list(benign_records)
    clean_triggered_fusion_map: dict[str, float] = {}
    clean_triggered_m1_map: dict[str, float] = {}

    for fam_name, fam_meta in TRIGGER_FAMILIES.items():
        trig_spec = TriggerSpec(
            family=fam_name,
            feature_indices=tuple(int(x) for x in fam_meta["default_indices"]),
            feature_values=tuple(float(x) for x in fam_meta["default_values"]),
            modifiable_views=tuple(str(v) for v in fam_meta["views"]),
        )
        fam_slug = fam_name.lower().replace("-", "_")
        fam_mal_records: list[dict[str, Any]] = []
        fam_sids: list[str] = []
        fam_is_mal: list[int] = []
        fam_clean_scores: list[float] = []
        fam_clean_trig_scores: list[float] = []

        for raw_i in eval_mal_idx:
            idx_int = int(raw_i)
            sid = f"ember_test_{idx_int}_{fam_slug}"
            base_vec = clean_mal_base_vecs[idx_int]
            trig_vec = apply_vector_trigger(base_vec, trig_spec)
            defense_guard.assert_defense_input_clean({"sample_id": sid, "features": trig_vec})

            c_score = clean_mal_scores_map[idx_int]
            t0 = time.perf_counter()
            trig_model_score, trig_shap = model_service.infer(trig_vec)
            t_det0 = time.perf_counter()
            sig_res = pipeline.evaluate(
                trig_vec, model_service=model_service, shap_values=trig_shap
            )
            sig_scores = {k: float(v.score) for k, v in sig_res.items()}
            red_score = reduced_fuser.fuse(sig_scores)
            full_score = full_fuser.fuse(sig_scores)
            t_end = time.perf_counter()

            det_ms = (t_end - t_det0) * 1000.0
            e2e_ms = (t_end - t0) * 1000.0
            clean_triggered_fusion_map[sid] = full_score
            clean_triggered_m1_map[sid] = float(sig_scores["m1"])

            rec = {
                "sample_id": sid,
                "base_sample_id": f"ember_test_{int(raw_i)}",
                "trigger_family": fam_name,
                "label": 1,
                "is_malware": 1,
                "clean_model_score": float(c_score),
                "clean_triggered_score": float(trig_model_score),
                "poisoned_triggered_score": float(trig_model_score),
                "signals": sig_scores,
                "fusion_reduced_score": red_score,
                "fusion_full_score": full_score,
                "decision": decision_policy.evaluate(full_score).decision,
                "latency_ms": {
                    "detector_only": det_ms,
                    "end_to_end": e2e_ms,
                    "EndToEnd_WithSHAP": e2e_ms,
                },
            }
            fam_mal_records.append(rec)
            all_records_pooled.append(rec)
            fam_sids.append(sid)
            fam_is_mal.append(1)
            fam_clean_scores.append(float(c_score))
            fam_clean_trig_scores.append(float(trig_model_score))

        e1_fam = runner.run_e1_attack_viability(
            run_id=f"e1_{fam_slug}_seed{seed}",
            sample_ids=fam_sids,
            is_malware=fam_is_mal,
            clean_model_scores=fam_clean_scores,
            poisoned_triggered_scores=fam_clean_trig_scores,
            clean_triggered_scores=fam_clean_trig_scores,
            trigger_family=fam_name,
            poison_rate=0.01,
            seed=seed,
            evidence_class="FROZEN_CANDIDATE_RUN",
            status="PARTIAL",
            extra_manifest={
                **provenance_hashes,
                "note": (
                    "Executed on frozen candidate clean LightGBM model (ember_model_2018.txt); "
                    "pre-trained poisoned LightGBM models are blocked by MISSING_POISONED_MODELS."
                ),
            },
        )
        fam_records = benign_records + fam_mal_records
        e2_fam = runner.run_e2_detector_comparison(
            run_id=f"e2_{fam_slug}_seed{seed}",
            records=fam_records,
            locked_threshold=locked_threshold,
            threshold_id=threshold_id,
            seed=seed,
            evidence_class="FROZEN_CANDIDATE_RUN",
            status="COMPLETED",
            extra_manifest=provenance_hashes,
        )
        family_results[fam_name] = {
            "e1": e1_fam["metrics"],
            "e2": e2_fam["metrics"],
            "e1_recompute_check": recompute_metrics_from_raw(
                output_root / f"e1_{fam_slug}_seed{seed}"
            ),
            "recompute_check": recompute_metrics_from_raw(
                output_root / f"e2_{fam_slug}_seed{seed}"
            ),
        }

    e0_res = runner.run_e0_distributions(
        run_id=f"e0_distributions_seed{seed}",
        clean_benign_scores=clean_benign_fusion_map,
        clean_triggered_scores=clean_triggered_fusion_map,
        poisoned_benign_scores=None,
        poisoned_triggered_scores=None,
        threshold=locked_threshold,
        clean_benign_m1_scores=clean_benign_m1_map,
        clean_triggered_m1_scores=clean_triggered_m1_map,
        poisoned_benign_m1_scores=None,
        poisoned_triggered_m1_scores=None,
        m1_threshold=locked_threshold,
        seed=seed,
        evidence_class="FROZEN_CANDIDATE_RUN",
        extra_manifest=provenance_hashes,
    )
    e2_pooled = runner.run_e2_detector_comparison(
        run_id=f"e2_pooled_seed{seed}",
        records=all_records_pooled,
        locked_threshold=locked_threshold,
        threshold_id=threshold_id,
        seed=seed,
        evidence_class="FROZEN_CANDIDATE_RUN",
        status="COMPLETED",
        extra_manifest=provenance_hashes,
    )
    e3_pooled = runner.run_e3_paired_catch_miss(
        run_id=f"e3_paired_catch_miss_seed{seed}",
        records=all_records_pooled,
        locked_threshold=locked_threshold,
        seed=seed,
        evidence_class="FROZEN_CANDIDATE_RUN",
        status="COMPLETED",
        extra_manifest=provenance_hashes,
    )
    e4_pooled = runner.run_e4_ablation(
        run_id=f"e4_ablation_seed{seed}",
        records=all_records_pooled,
        locked_threshold=locked_threshold,
        seed=seed,
        evidence_class="FROZEN_CANDIDATE_RUN",
        status="COMPLETED",
        extra_manifest=provenance_hashes,
    )
    e5_pooled = runner.run_e5_fpr_latency(
        run_id=f"e5_fpr_latency_seed{seed}",
        records=all_records_pooled,
        locked_threshold=locked_threshold,
        warmup_count=warmup_iterations,
        seed=seed,
        evidence_class="FROZEN_CANDIDATE_RUN",
        status="COMPLETED",
        extra_manifest=provenance_hashes,
    )

    # Seal BlindPredictionPackage and score via BlindEvaluator
    blind_preds = tuple(
        BlindSamplePrediction(
            sample_id=str(r["sample_id"]),
            malware_score=float(r["clean_model_score"]),
            signals={str(k): float(v) for k, v in r["signals"].items()},
            fusion_score=float(r["fusion_full_score"]),
            decision=decision_policy.evaluate(float(r["fusion_full_score"])).decision,
            latency_ms=float(r["latency_ms"]["detector_only"]),
        )
        for r in all_records_pooled
    )
    blind_pkg = BlindPredictionPackage.create(
        run_id=f"blind_e2_pooled_seed{seed}",
        experiment_code="E2",
        config_hash=str(provenance_hashes["fusion_config_sha256"]),
        model_hash=str(provenance_hashes["model_artifact_sha256"]),
        view_map_hash=str(provenance_hashes["view_map_sha256"]),
        detector_config_hash=str(provenance_hashes["detector_config_sha256"]),
        threshold_id=threshold_id,
        threshold_value=locked_threshold,
        seed=seed,
        predictions=blind_preds,
    )
    blind_pkg_path = output_root / f"blind_e2_pooled_seed{seed}" / "sealed_predictions.json"
    blind_pkg.save(blind_pkg_path)

    blind_truth = BlindGroundTruthManifest.create(
        manifest_id=f"truth_e2_pooled_seed{seed}",
        dataset_id="ember2018_test_slice",
        sample_ids=tuple(str(r["sample_id"]) for r in all_records_pooled),
        labels=tuple(int(r["label"]) for r in all_records_pooled),
        is_malware=tuple(int(r["is_malware"]) for r in all_records_pooled),
        clean_model_scores=tuple(float(r["clean_model_score"]) for r in all_records_pooled),
        poisoned_triggered_scores=tuple(
            float(r["poisoned_triggered_score"]) for r in all_records_pooled
        ),
    )
    blind_evaluator = BlindEvaluator(role=EvaluationRole.EVALUATION_SCORING)
    blind_report = blind_evaluator.score_predictions(
        prediction_package=blind_pkg,
        ground_truth=blind_truth,
        expected_locked_threshold=locked_threshold,
    )

    all_runs_recompute_check = {
        f"e0_distributions_seed{seed}": recompute_metrics_from_raw(
            output_root / f"e0_distributions_seed{seed}"
        ),
        f"e2_pooled_seed{seed}": recompute_metrics_from_raw(
            output_root / f"e2_pooled_seed{seed}"
        ),
        f"e3_paired_catch_miss_seed{seed}": recompute_metrics_from_raw(
            output_root / f"e3_paired_catch_miss_seed{seed}"
        ),
        f"e4_ablation_seed{seed}": recompute_metrics_from_raw(
            output_root / f"e4_ablation_seed{seed}"
        ),
        f"e5_fpr_latency_seed{seed}": recompute_metrics_from_raw(
            output_root / f"e5_fpr_latency_seed{seed}"
        ),
    }

    suite_summary = {
        "suite_id": f"be14_candidate_suite_seed{seed}",
        "evidence_class": "FROZEN_CANDIDATE_RUN",
        "strict_scientific_ready": readiness["strict_scientific_ready"],
        "scientific_blockers": readiness["blockers"],
        "provenance": provenance_hashes,
        "locked_threshold": locked_threshold,
        "threshold_id": threshold_id,
        "warmup_iterations": warmup_iterations,
        "sample_counts": {
            "benign": len(benign_records),
            "malware_per_family": n_malware,
            "total_pooled_records": len(all_records_pooled),
        },
        "e0": e0_res["metrics"],
        "by_trigger_family": family_results,
        "e2_pooled": e2_pooled["metrics"],
        "e3_pooled": e3_pooled["metrics"],
        "e4_pooled": e4_pooled["metrics"],
        "e5_pooled": e5_pooled["metrics"],
        "blind_evaluation_report": blind_report.to_dict(),
        "all_runs_recompute_check": all_runs_recompute_check,
    }
    summary_path = output_root / "suite_summary.json"
    summary_path.write_text(json.dumps(suite_summary, indent=2, sort_keys=True), encoding="utf-8")
    return suite_summary
