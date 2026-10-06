# -*- coding: utf-8 -*-
"""
X-SENTINEL: RIGOROUS BASELINE BENCHMARK (M1: TADR & M2: STRIP)
Đề tài: Cross-View Semantic Backdoor Detection in Malware Classifiers
Môn học: IAM302t (Fall 2026) - Lớp IA2007 - Nhóm 4

Chuẩn hóa phương pháp luận khoa học:
1. Xác thực tập đặc trưng khả thi (Track 1) và phép thử ứng suất (Track 2).
2. Quy mô tập tham chiếu D1 chuẩn hóa: N = 1.000 mẫu Benign tin cậy.
3. Tập kiểm thử độc lập: 1.000 mẫu Benign (đo Empirical FPR & Wilson 95% CI) + 1.000 mẫu Malware.
4. Đánh giá khách quan 2 giả thuyết H1 và H2.
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
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# =============================================================================
# 1. CẤU HÌNH TRIGGER (TRACK 1 FEASIBLE & TRACK 2 STRESS TEST)
# =============================================================================
FEASIBLE_STRUCTURAL_SPREAD = [616, 617, 626, 677, 678, 679, 680, 688, 689, 690]
FEASIBLE_ALL_16 = [
    512, 513, 514, 611,  # Metadata (4)
    616, 617, 622, 623, 626, 677, 678, 679, 680, 688, 689, 690  # Structural (12)
]
STRESS_METADATA_24 = [512, 513, 514, 611] + list(range(515, 535))  # 4 feasible + 20 bins printabledist

def apply_trigger_pattern(X: np.ndarray, trigger_type: str) -> np.ndarray:
    """
    Áp dụng trigger pattern lên ma trận X (N, 2381).
    Trả về bản sao độc lập.
    """
    X_mod = np.copy(X)

    if trigger_type == "concentrated":
        # Track 1: T_concentrated (2 features trong Whitelist: coff_timestamp & major_linker_version)
        X_mod[:, 626] = 1650000000.0
        X_mod[:, 679] = 15.0

    elif trigger_type == "spread":
        # Track 1: T_spread (10 features phân tán trọn vẹn trong Structural View)
        X_mod[:, 616] += 131072.0       # Tăng file size 128KB
        X_mod[:, 617] += 131072.0       # Tăng virtual size
        X_mod[:, 626] = 1650000000.0    # Fixed timestamp
        X_mod[:, 677] = 10.0            # Major image version
        X_mod[:, 678] = 5.0             # Minor image version
        X_mod[:, 679] = 14.0            # Major linker version
        X_mod[:, 680] = 12.0            # Minor linker version
        X_mod[:, 688] += 2.0            # Thêm 2 sections
        X_mod[:, 689] = 1.0             # 1 zero-size section
        X_mod[:, 690] = 1.0             # 1 empty-name section

    elif trigger_type == "cross":
        # Track 1: T_cross (16 features toàn bộ Whitelist: 12 Structural + 4 Metadata)
        # Structural component (12):
        X_mod[:, 616] += 131072.0
        X_mod[:, 617] += 131072.0
        X_mod[:, 622] = 1.0             # has_resources = 1
        X_mod[:, 623] = 1.0             # has_signature = 1
        X_mod[:, 626] = 1650000000.0
        X_mod[:, 677] = 10.0
        X_mod[:, 678] = 5.0
        X_mod[:, 679] = 14.0
        X_mod[:, 680] = 12.0
        X_mod[:, 688] += 2.0
        X_mod[:, 689] = 1.0
        X_mod[:, 690] = 1.0
        # Metadata component (4):
        X_mod[:, 512] += 300.0          # Printable strings count
        X_mod[:, 513] = 25.0            # Average string length
        X_mod[:, 514] += 7500.0         # Printable characters count
        X_mod[:, 611] = 6.25            # String entropy

    elif trigger_type == "stress_metadata_24":
        # Track 2: Vector-Space Stress Test (24 features Metadata)
        X_mod[:, 512] += 500.0
        X_mod[:, 513] = 28.0
        X_mod[:, 514] += 12000.0
        X_mod[:, 611] = 6.45
        for col in range(515, 535):
            X_mod[:, col] += 0.05

    else:
        raise ValueError(f"Unknown trigger type: {trigger_type}")

    return X_mod

# =============================================================================
# 2. TOÁN HỌC THỐNG KÊ: WILSON SCORE INTERVAL
# =============================================================================
def wilson_score_interval(k: int, n: int, confidence: float = 0.95):
    """
    Tính khoảng tin cậy Wilson 95% cho tỷ lệ ngoại lai / empirical false positive rate.
    """
    if n == 0:
        return 0.0, 0.0, 0.0
    p_hat = k / n
    z = 1.959963984540054  # z-value cho 95% 2-tailed
    denominator = 1.0 + (z**2) / n
    center = p_hat + (z**2) / (2.0 * n)
    margin = z * np.sqrt((p_hat * (1.0 - p_hat)) / n + (z**2) / (4.0 * (n**2)))
    lower = max(0.0, (center - margin) / denominator)
    upper = min(1.0, (center + margin) / denominator)
    return p_hat, lower, upper

# =============================================================================
# 3. QUẢN LÝ DỮ LIỆU CHUẨN HÓA (D1 = 1.000, TEST_BENIGN = 1.000, TEST_MALWARE = 1.000)
# =============================================================================
def load_rigorous_dataset(base_dir: str):
    eval_cache_file = os.path.join(base_dir, "data", "rigorous_eval_dataset_1000.npz")
    pilot_cache_file = os.path.join(base_dir, "data", "pilot_dataset_cache.npz")

    # 1. Nạp Train set từ pilot_dataset_cache.npz (6.000 mẫu: 3.000 B, 3.000 M)
    pilot_data = np.load(pilot_cache_file)
    X_train_clean = pilot_data["X_train_clean"]
    y_train_clean = pilot_data["y_train_clean"]

    # 2. Nạp Eval set từ rigorous_eval_dataset_1000.npz
    eval_data = np.load(eval_cache_file)
    D1 = eval_data["D1"]
    X_test_benign = eval_data["X_test_benign"]
    X_test_malware = eval_data["X_test_malware"]

    print(f"[+] Hiện trạng dữ liệu thực nghiệm chuẩn hóa:", flush=True)
    print(f"    - Tập Huấn luyện: {len(X_train_clean)} mẫu (Clean LightGBM Train)", flush=True)
    print(f"    - Tập Tham chiếu D1: {len(D1)} mẫu Benign tin cậy (Khóa Ngưỡng P99)", flush=True)
    print(f"    - Tập Test Benign:   {len(X_test_benign)} mẫu Benign độc lập (Đo Empirical FPR)", flush=True)
    print(f"    - Tập Test Malware:  {len(X_test_malware)} mẫu Malware độc lập (Đo ASR & Recall)", flush=True)
    return X_train_clean, y_train_clean, D1, X_test_benign, X_test_malware

# =============================================================================
# 4. THUẬT TOÁN TỐI ƯU HÓA ĐO LƯỜNG BASELINE
# =============================================================================
def compute_tadr_batch(model: lgb.Booster, X: np.ndarray) -> np.ndarray:
    """
    Tính điểm TADR vector hóa tốc độ cao qua C++ fast-path pred_contrib.
    Xử lý an toàn ca biên sum(|phi|) <= 1e-9 -> score = 0.0.
    """
    contribs = model.predict(X, pred_contrib=True)[:, :-1]  # Bỏ bias cuối
    abs_phi = np.abs(contribs)
    total_att = np.sum(abs_phi, axis=1)
    max_att = np.max(abs_phi, axis=1)
    safe_total = np.maximum(total_att, 1e-9)
    scores = np.where(total_att <= 1e-9, 0.0, max_att / safe_total)
    return scores.astype(np.float32)

def compute_strip_scores_fast(model: lgb.Booster, X: np.ndarray, D1: np.ndarray, n_perturb: int = 50, alpha: float = 0.5, seed: int = 42, chunk_size: int = 200) -> np.ndarray:
    """
    Tính điểm STRIP thích ứng cho dữ liệu bảng EMBER theo từng khối (chunk) để tối ưu bộ nhớ và tốc độ.
    Trộn lồi: x' = alpha * x + (1 - alpha) * r_k với r_k rút từ D1.
    Score = 1.0 - mean_entropy.
    """
    rng = np.random.default_rng(seed)
    n_samples = len(X)
    n_d1 = len(D1)
    all_scores = np.zeros(n_samples, dtype=np.float32)
    eps = 1e-12

    for start_idx in range(0, n_samples, chunk_size):
        end_idx = min(start_idx + chunk_size, n_samples)
        X_chunk = X[start_idx:end_idx]
        m = len(X_chunk)

        # Rút m * n_perturb mẫu ngẫu nhiên từ D1
        r_indices = rng.choice(n_d1, size=m * n_perturb, replace=True)
        r_samples = D1[r_indices].reshape(m, n_perturb, -1)

        X_exp = X_chunk[:, np.newaxis, :]
        blended = (alpha * X_exp + (1.0 - alpha) * r_samples).reshape(m * n_perturb, -1)

        p1 = model.predict(blended).reshape(m, n_perturb)
        p0 = 1.0 - p1
        entropy = -(p0 * np.log2(p0 + eps) + p1 * np.log2(p1 + eps))
        mean_entropy = np.mean(entropy, axis=1)
        all_scores[start_idx:end_idx] = np.maximum(0.0, 1.0 - mean_entropy)

    return all_scores.astype(np.float32)

# =============================================================================
# 5. CHƯƠNG TRÌNH THỰC THI & PHÂN TÍCH TOÀN DIỆN
# =============================================================================
def main():
    print("=" * 115, flush=True)
    print("   X-SENTINEL: ĐÁNH GIÁ CHUẨN HÓA KHOA HỌC HAI BASELINE (M1: TADR & M2: STRIP)", flush=True)
    print("   Đề tài: Cross-View Semantic Backdoor Detection in Malware Classifiers", flush=True)
    print("   Môn học: IAM302t (Fall 2026) - Lớp IA2007 - Nhóm 4 (IA2007)", flush=True)
    print("=" * 115, flush=True)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    X_train_clean, y_train_clean, D1, X_test_benign, X_test_malware = load_rigorous_dataset(base_dir)

    # Siêu tham số LightGBM chuẩn EMBER
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

    # 1. Huấn luyện Mô hình Sạch M0
    print("\n" + "=" * 60, flush=True)
    print("[1/5] Huấn luyện Mô hình Sạch Tham Chiếu (Clean Model M0)...", flush=True)
    t0 = time.time()
    ds_train_clean = lgb.Dataset(X_train_clean, label=y_train_clean)
    model_clean = lgb.train(lgb_params, ds_train_clean, num_boost_round=150)
    clean_acc_benign = np.mean(model_clean.predict(X_test_benign) < 0.5) * 100.0
    clean_acc_malware = np.mean(model_clean.predict(X_test_malware) >= 0.5) * 100.0
    print(f"[+] Huấn luyện xong trong {time.time() - t0:.2f}s", flush=True)
    print(f"[+] Clean Model Test Accuracy: Benign={clean_acc_benign:.2f}%, Malware={clean_acc_malware:.2f}%", flush=True)

    # 2. Danh sách cấu hình thực nghiệm: 3 Track 1 Feasible + 1 Track 2 Stress Test
    configurations = [
        {"id": "concentrated", "track": "Track 1 (Feasible)", "name": "T_concentrated (2 feats)"},
        {"id": "spread", "track": "Track 1 (Feasible)", "name": "T_spread (10 feats Struct)"},
        {"id": "cross", "track": "Track 1 (Feasible)", "name": "T_cross (16 feats Feasible)"},
        {"id": "stress_metadata_24", "track": "Track 2 (Stress Test)", "name": "T_stress (24 feats Meta)"}
    ]

    results_table = []
    sensitivity_records = []

    rng = np.random.default_rng(42)
    benign_indices = np.where(y_train_clean == 0)[0]
    n_poison = int(0.01 * len(benign_indices))  # 1% Clean-label đầu độc = 30 mẫu

    for cfg in configurations:
        trig_id = cfg["id"]
        print("\n" + "=" * 90, flush=True)
        print(f"[*] THỰC NGHIỆM ĐÒN ĐÁNH: [{cfg['name'].upper()}] - {cfg['track']}", flush=True)
        print("=" * 90, flush=True)

        # A. Tạo dữ liệu đầu độc Clean-label
        X_train_poisoned = np.copy(X_train_clean)
        chosen_poison = rng.choice(benign_indices, size=n_poison, replace=False)
        X_train_poisoned[chosen_poison] = apply_trigger_pattern(X_train_poisoned[chosen_poison], trig_id)

        # B. Huấn luyện mô hình Backdoor
        t0 = time.time()
        ds_poison = lgb.Dataset(X_train_poisoned, label=y_train_clean)
        model_backdoored = lgb.train(lgb_params, ds_poison, num_boost_round=150)
        t_train = time.time() - t0
        print(f"[+] Huấn luyện mô hình Backdoor hoàn tất trong: {t_train:.2f}s", flush=True)

        # C. Đo ASR trên 1.000 mẫu Malware kiểm thử
        X_eval_malware_trig = apply_trigger_pattern(X_test_malware, trig_id)
        preds_trig = model_backdoored.predict(X_eval_malware_trig)
        asr = float(np.mean(preds_trig < 0.5)) * 100.0
        print(f"[+] Tỷ lệ tấn công thành công ASR: {asr:.2f}% (Malware bị nhận diện nhầm là Benign)", flush=True)

        # D. Hiệu chuẩn & Khóa ngưỡng trên D1 (N = 1.000 mẫu Benign)
        print(f"[*] Đang hiệu chuẩn ngưỡng tau trên D1 (N = {len(D1)} mẫu Benign)...", flush=True)
        tadr_d1 = compute_tadr_batch(model_backdoored, D1)
        strip_d1 = compute_strip_scores_fast(model_backdoored, D1, D1, n_perturb=50, alpha=0.5, seed=42)

        tau_tadr = float(np.percentile(tadr_d1, 99.0))
        tau_strip = float(np.percentile(strip_d1, 99.0))
        print(f"[+] KHÓA NGƯỠNG TẠI P99 (D1 N=1000): tau_TADR = {tau_tadr:.4f}, tau_STRIP = {tau_strip:.4f}", flush=True)

        # Đánh giá độ nhạy kích thước D1 (Sensitivity Analysis)
        sens_200_tadr = float(np.percentile(tadr_d1[:200], 99.0))
        sens_500_tadr = float(np.percentile(tadr_d1[:500], 99.0))
        sens_200_strip = float(np.percentile(strip_d1[:200], 99.0))
        sens_500_strip = float(np.percentile(strip_d1[:500], 99.0))
        sensitivity_records.append({
            "trigger": trig_id,
            "tau_tadr_200": sens_200_tadr,
            "tau_tadr_500": sens_500_tadr,
            "tau_tadr_1000": tau_tadr,
            "tau_strip_200": sens_200_strip,
            "tau_strip_500": sens_500_strip,
            "tau_strip_1000": tau_strip
        })

        # E. Kiểm định Empirical FPR trên 1.000 mẫu Benign độc lập
        tadr_test_benign = compute_tadr_batch(model_backdoored, X_test_benign)
        k_fp_tadr = int(np.sum(tadr_test_benign > tau_tadr))
        emp_fpr_tadr, lower_ci_tadr, upper_ci_tadr = wilson_score_interval(k_fp_tadr, len(X_test_benign), 0.95)

        strip_test_benign = compute_strip_scores_fast(model_backdoored, X_test_benign, D1, n_perturb=50, alpha=0.5, seed=42)
        k_fp_strip = int(np.sum(strip_test_benign > tau_strip))
        emp_fpr_strip, lower_ci_strip, upper_ci_strip = wilson_score_interval(k_fp_strip, len(X_test_benign), 0.95)

        # F. Đo lường Recall @ 1% FPR và AUROC trên Malware mang Trigger (1.000 mẫu)
        tadr_test_trig = compute_tadr_batch(model_backdoored, X_eval_malware_trig)
        tadr_recall = float(np.mean(tadr_test_trig > tau_tadr)) * 100.0
        y_auroc = np.concatenate([np.zeros(len(tadr_test_benign)), np.ones(len(tadr_test_trig))])
        tadr_auroc = float(roc_auc_score(y_auroc, np.concatenate([tadr_test_benign, tadr_test_trig]))) * 100.0

        strip_test_trig = compute_strip_scores_fast(model_backdoored, X_eval_malware_trig, D1, n_perturb=50, alpha=0.5, seed=42)
        strip_recall = float(np.mean(strip_test_trig > tau_strip)) * 100.0
        strip_auroc = float(roc_auc_score(y_auroc, np.concatenate([strip_test_benign, strip_test_trig]))) * 100.0

        record = {
            "trigger_id": trig_id,
            "track": cfg["track"],
            "name": cfg["name"],
            "asr": asr,
            "tau_tadr": tau_tadr,
            "tadr_emp_fpr": emp_fpr_tadr * 100.0,
            "tadr_wilson_ci": [lower_ci_tadr * 100.0, upper_ci_tadr * 100.0],
            "tadr_mean": float(np.mean(tadr_test_trig)),
            "tadr_median": float(np.median(tadr_test_trig)),
            "tadr_recall": tadr_recall,
            "tadr_auroc": tadr_auroc,
            "tau_strip": tau_strip,
            "strip_emp_fpr": emp_fpr_strip * 100.0,
            "strip_wilson_ci": [lower_ci_strip * 100.0, upper_ci_strip * 100.0],
            "strip_mean": float(np.mean(strip_test_trig)),
            "strip_median": float(np.median(strip_test_trig)),
            "strip_recall": strip_recall,
            "strip_auroc": strip_auroc
        }
        results_table.append(record)

        print(f"[+] TADR:  Recall@1% = {tadr_recall:6.2f}%, AUROC = {tadr_auroc:6.2f}%, Emp FPR = {emp_fpr_tadr*100:.2f}% (Wilson 95% CI: [{lower_ci_tadr*100:.2f}%, {upper_ci_tadr*100:.2f}%])", flush=True)
        print(f"[+] STRIP: Recall@1% = {strip_recall:6.2f}%, AUROC = {strip_auroc:6.2f}%, Emp FPR = {emp_fpr_strip*100:.2f}% (Wilson 95% CI: [{lower_ci_strip*100:.2f}%, {upper_ci_strip*100:.2f}%])", flush=True)

    # =========================================================================
    # 6. BÁO CÁO TỔNG HỢP VÀ KIỂM ĐỊNH GIẢ THUYẾT H1 & H2
    # =========================================================================
    print("\n" + "=" * 125, flush=True)
    print("   BẢNG 1: BÁO CÁO ĐỐI CHUẨN HIỆU NĂNG PHÁT HIỆN BASELINE (PILOT MODEL - EMBER 2018)", flush=True)
    print("=" * 125, flush=True)
    print(f"{'Trigger Configuration':<28} | {'ASR (%)':<8} | {'TADR Rec@1%':<12} | {'TADR AUROC':<11} | {'STRIP Rec@1%':<12} | {'STRIP AUROC':<11} | {'Ghi Chú Đòn Đánh'}", flush=True)
    print("-" * 125, flush=True)
    for r in results_table:
        print(f"{r['name']:<28} | {r['asr']:<8.2f} | {r['tadr_recall']:<12.2f} | {r['tadr_auroc']:<11.2f} | {r['strip_recall']:<12.2f} | {r['strip_auroc']:<11.2f} | {r['track']}", flush=True)
    print("-" * 125, flush=True)

    print("\n" + "=" * 115, flush=True)
    print("   BẢNG 2: PHÂN TÍCH ĐỘ NHẠY HIỆU CHUẨN NGƯỠNG TRÊN TẬP THAM CHIẾU D1 (P99)", flush=True)
    print("=" * 115, flush=True)
    print(f"{'Trigger':<22} | {'tau_TADR (200)':<15} | {'tau_TADR (500)':<15} | {'tau_TADR (1000)':<16} | {'tau_STRIP (200)':<16} | {'tau_STRIP (1000)'}", flush=True)
    print("-" * 115, flush=True)
    for s in sensitivity_records:
        print(f"{s['trigger']:<22} | {s['tau_tadr_200']:<15.4f} | {s['tau_tadr_500']:<15.4f} | {s['tau_tadr_1000']:<16.4f} | {s['tau_strip_200']:<16.4f} | {s['tau_strip_1000']:.4f}", flush=True)
    print("-" * 115, flush=True)

    print("\n" + "=" * 115, flush=True)
    print("   BẢNG 3: KIỂM ĐỊNH TÍNH ỔN ĐỊNH CỦA NGƯỠNG (EMPIRICAL FPR TRÊN 1.000 MẪU TEST BENIGN ĐỘC LẬP)", flush=True)
    print("=" * 115, flush=True)
    print(f"{'Trigger':<25} | {'TADR Emp FPR':<15} | {'Wilson 95% CI (TADR)':<25} | {'STRIP Emp FPR':<15} | {'Wilson 95% CI (STRIP)'}", flush=True)
    print("-" * 115, flush=True)
    for r in results_table:
        ci_t = f"[{r['tadr_wilson_ci'][0]:.2f}%, {r['tadr_wilson_ci'][1]:.2f}%]"
        ci_s = f"[{r['strip_wilson_ci'][0]:.2f}%, {r['strip_wilson_ci'][1]:.2f}%]"
        print(f"{r['name']:<25} | {r['tadr_emp_fpr']:<15.2f}% | {ci_t:<25} | {r['strip_emp_fpr']:<15.2f}% | {ci_s}", flush=True)
    print("-" * 115, flush=True)

    # Lưu kết quả đầy đủ ra JSON
    out_json = os.path.join(base_dir, "data", "rigorous_baseline_benchmark_results.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "results": results_table,
            "sensitivity": sensitivity_records,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }, f, indent=2, ensure_ascii=False)
    print(f"\n[+] Đã lưu toàn bộ số liệu đối chuẩn Baseline ra file: {out_json}", flush=True)

if __name__ == "__main__":
    main()
