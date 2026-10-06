# -*- coding: utf-8 -*-
"""
X-SENTINEL: REPRODUCIBILITY ARTIFACTS EXPORTER
Xuất toàn bộ artifact chi tiết để tái lập 100% kết quả Baseline:
- Lưu 5 mô hình LightGBM (.txt)
- Lưu danh sách 30 chỉ số mẫu bị đầu độc
- Lưu mảng dự đoán và điểm số chi tiết từng mẫu (sample-level predictions & scores)
- Xuất file manifest JSON chi tiết từng tham số toán học
"""

import os
import sys
import time
import json
import numpy as np
import lightgbm as lgb
from sklearn.metrics import roc_auc_score

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(os.path.dirname(__file__))
from run_baseline_rigorous_validation import (
    apply_trigger_pattern,
    compute_tadr_batch,
    compute_strip_scores_fast,
    wilson_score_interval,
    load_rigorous_dataset
)

def export_reproducibility_package():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    models_dir = os.path.join(base_dir, "models")
    artifacts_dir = os.path.join(base_dir, "data", "reproducibility_artifacts")
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(artifacts_dir, exist_ok=True)

    print("=" * 110, flush=True)
    print("   X-SENTINEL: XUẤT TẬP TÀI NGUYÊN TÁI LẬP KHOA HỌC (ZERO-AMBIGUITY REPRODUCIBILITY)", flush=True)
    print("=" * 110, flush=True)

    # 1. Nạp dữ liệu
    X_train_clean, y_train_clean, D1, X_test_benign, X_test_malware = load_rigorous_dataset(base_dir)

    lgb_params = {
        "boosting_type": "gbdt",
        "objective": "binary",
        "learning_rate": 0.05,
        "num_leaves": 256,
        "feature_fraction": 0.8,
        "random_state": 42,
        "verbose": -1,
        "n_jobs": -1
    }

    # 2. Huấn luyện và lưu Clean Model M0
    print("[*] Huấn luyện & lưu Clean Model M0...", flush=True)
    ds_clean = lgb.Dataset(X_train_clean, label=y_train_clean)
    model_clean = lgb.train(lgb_params, ds_clean, num_boost_round=150)
    clean_model_path = os.path.join(models_dir, "model_clean.txt")
    model_clean.save_model(clean_model_path)

    # Dự đoán của clean model
    clean_preds_benign = model_clean.predict(X_test_benign)
    clean_preds_malware = model_clean.predict(X_test_malware)

    # 3. Chọn 30 mẫu Benign để đầu độc (1.0% của 3.000 Benign)
    rng = np.random.default_rng(42)
    benign_indices = np.where(y_train_clean == 0)[0]
    n_poison = int(0.01 * len(benign_indices))  # đúng 30 mẫu
    chosen_poison_indices = rng.choice(benign_indices, size=n_poison, replace=False).tolist()
    chosen_poison_indices.sort()

    print(f"[+] Chọn {len(chosen_poison_indices)} mẫu Benign (1.0% của 3.000 mẫu Benign train).", flush=True)
    print(f"    Chỉ số mẫu trong X_train_clean: {chosen_poison_indices}", flush=True)

    configs = [
        {"id": "concentrated", "name": "T_concentrated (2 feats)"},
        {"id": "spread", "name": "T_spread (10 feats Struct)"},
        {"id": "cross", "name": "T_cross (16 feats Feasible)"},
        {"id": "stress_metadata_24", "name": "T_stress (24 feats Meta)"}
    ]

    manifest = {
        "dataset_metadata": {
            "total_train_samples": int(len(X_train_clean)),
            "train_benign_count": int(np.sum(y_train_clean == 0)),
            "train_malware_count": int(np.sum(y_train_clean == 1)),
            "d1_reference_count": int(len(D1)),
            "test_benign_count": int(len(X_test_benign)),
            "test_malware_count": int(len(X_test_malware)),
            "poisoning_definition": "1.0% riêng của tập Benign huấn luyện = 30 mẫu (nhãn giữ nguyên 0 - Clean Label)",
            "poisoned_benign_indices": chosen_poison_indices,
            "random_seed": 42
        },
        "lightgbm_hyperparameters": lgb_params,
        "clean_model_metrics": {
            "model_path": clean_model_path,
            "test_benign_mean_pred": float(np.mean(clean_preds_benign)),
            "test_malware_mean_pred": float(np.mean(clean_preds_malware)),
            "test_benign_accuracy_p_lt_0_5": float(np.mean(clean_preds_benign < 0.5) * 100.0),
            "test_malware_accuracy_p_ge_0_5": float(np.mean(clean_preds_malware >= 0.5) * 100.0)
        },
        "experiments": []
    }

    for cfg in configs:
        trig_id = cfg["id"]
        print(f"\n[*] Xử lý và xuất artifact cho cấu hình [{trig_id}]...", flush=True)

        # A. Tạo tập train bị đầu độc
        X_train_poisoned = np.copy(X_train_clean)
        X_train_poisoned[chosen_poison_indices] = apply_trigger_pattern(X_train_poisoned[chosen_poison_indices], trig_id)

        # B. Huấn luyện mô hình
        ds_poison = lgb.Dataset(X_train_poisoned, label=y_train_clean)
        model_backdoor = lgb.train(lgb_params, ds_poison, num_boost_round=150)
        model_file = os.path.join(models_dir, f"model_backdoor_{trig_id}.txt")
        model_backdoor.save_model(model_file)

        # C. Đánh giá ASR trên 1.000 mẫu Malware
        X_malware_trig = apply_trigger_pattern(X_test_malware, trig_id)
        malware_preds = model_backdoor.predict(X_malware_trig)
        
        # Mẫu số là 1.000 mẫu Malware
        denominator_asr = len(X_malware_trig)
        numerator_asr = int(np.sum(malware_preds < 0.5))
        asr_percent = (numerator_asr / denominator_asr) * 100.0

        # D. Khóa ngưỡng trên D1
        tadr_d1 = compute_tadr_batch(model_backdoor, D1)
        strip_d1 = compute_strip_scores_fast(model_backdoor, D1, D1, n_perturb=50, alpha=0.5, seed=42)
        tau_tadr = float(np.percentile(tadr_d1, 99.0))
        tau_strip = float(np.percentile(strip_d1, 99.0))

        # E. Đo lường trên tập Test
        tadr_test_benign = compute_tadr_batch(model_backdoor, X_test_benign)
        strip_test_benign = compute_strip_scores_fast(model_backdoor, X_test_benign, D1, n_perturb=50, alpha=0.5, seed=42)

        tadr_test_trig = compute_tadr_batch(model_backdoor, X_malware_trig)
        strip_test_trig = compute_strip_scores_fast(model_backdoor, X_malware_trig, D1, n_perturb=50, alpha=0.5, seed=42)

        num_tadr_recall = int(np.sum(tadr_test_trig > tau_tadr))
        num_strip_recall = int(np.sum(strip_test_trig > tau_strip))

        num_tadr_fp = int(np.sum(tadr_test_benign > tau_tadr))
        num_strip_fp = int(np.sum(strip_test_benign > tau_strip))

        emp_fpr_tadr, ci_tadr_low, ci_tadr_up = wilson_score_interval(num_tadr_fp, len(X_test_benign))
        emp_fpr_strip, ci_strip_low, ci_strip_up = wilson_score_interval(num_strip_fp, len(X_test_benign))

        y_eval = np.concatenate([np.zeros(len(X_test_benign)), np.ones(len(X_malware_trig))])
        auroc_tadr = float(roc_auc_score(y_eval, np.concatenate([tadr_test_benign, tadr_test_trig]))) * 100.0
        auroc_strip = float(roc_auc_score(y_eval, np.concatenate([strip_test_benign, strip_test_trig]))) * 100.0

        # Lưu các mảng dự đoán và điểm số ra file .npy để kiểm tra chi tiết từng mẫu
        sample_level_file = os.path.join(artifacts_dir, f"sample_scores_{trig_id}.npz")
        np.savez_compressed(
            sample_level_file,
            malware_preds=malware_preds,
            tadr_test_trig=tadr_test_trig,
            tadr_test_benign=tadr_test_benign,
            strip_test_trig=strip_test_trig,
            strip_test_benign=strip_test_benign
        )

        manifest["experiments"].append({
            "trigger_id": trig_id,
            "trigger_name": cfg["name"],
            "model_path": model_file,
            "sample_scores_file": sample_level_file,
            "asr_metrics": {
                "formula": "Numerator: malware_preds < 0.5 / Denominator: len(X_test_malware)",
                "numerator_bypassed_malware": numerator_asr,
                "denominator_total_malware": denominator_asr,
                "asr_percent": asr_percent
            },
            "tadr_metrics": {
                "tau_locked_p99_d1": tau_tadr,
                "mean_score": float(np.mean(tadr_test_trig)),
                "median_score": float(np.median(tadr_test_trig)),
                "min_score": float(np.min(tadr_test_trig)),
                "max_score": float(np.max(tadr_test_trig)),
                "numerator_detected": num_tadr_recall,
                "denominator_total": len(X_malware_trig),
                "recall_at_1pct_fpr": (num_tadr_recall / len(X_malware_trig)) * 100.0,
                "auroc": auroc_tadr,
                "empirical_fp_count": num_tadr_fp,
                "empirical_fpr_percent": emp_fpr_tadr * 100.0,
                "wilson_ci_95": [ci_tadr_low * 100.0, ci_tadr_up * 100.0]
            },
            "strip_metrics": {
                "tau_locked_p99_d1": tau_strip,
                "mean_score": float(np.mean(strip_test_trig)),
                "median_score": float(np.median(strip_test_trig)),
                "min_score": float(np.min(strip_test_trig)),
                "max_score": float(np.max(strip_test_trig)),
                "numerator_detected": num_strip_recall,
                "denominator_total": len(X_malware_trig),
                "recall_at_1pct_fpr": (num_strip_recall / len(X_malware_trig)) * 100.0,
                "auroc": auroc_strip,
                "empirical_fp_count": num_strip_fp,
                "empirical_fpr_percent": emp_fpr_strip * 100.0,
                "wilson_ci_95": [ci_strip_low * 100.0, ci_strip_up * 100.0]
            }
        })

    manifest_path = os.path.join(base_dir, "data", "experiment_reproducibility_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n[+] ĐÃ XUẤT TOÀN BỘ TẬP TÀI NGUYÊN TÁI LẬP (REPRODUCIBILITY MANIFEST):", flush=True)
    print(f"    - Manifest JSON: {manifest_path}", flush=True)
    print(f"    - Các mô hình LightGBM: {models_dir}", flush=True)
    print(f"    - Dữ liệu chi tiết từng mẫu (sample-level): {artifacts_dir}", flush=True)

if __name__ == "__main__":
    export_reproducibility_package()
