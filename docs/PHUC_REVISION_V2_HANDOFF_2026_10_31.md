# Bàn Giao Triển Khai Nhiệm Vụ Phúc — Góp Ý Thầy v2 (2026-10-31)

**Người phụ trách**: Phạm Nguyễn Hoàng Phúc (SE203815 — Systems & Verification Engineer)  
**Nhánh công tác**: `main`  
**Ngày hoàn thành**: 31/10/2026  

---

## 1. Tóm Tắt Nghiệm Thu 6 Nhiệm Vụ Đã Hoàn Tất

1. **T1 (Fix lỗi kiểm thử sai số dấu phẩy động)**:
   - Sửa dòng 22 `tests/test_reviewer_core.py` sang `assert_allclose(..., atol=1e-12)`.
   - DoD: Triệt tiêu hoàn toàn lỗi fail $5.55 \times 10^{-17}$ trong ECDF rank comparison.
2. **T2 (Fix lỗi thiếu file `roles.json`)**:
   - Thêm volume mount an toàn `./data/primary:/app/data/primary:ro` trong `compose.yaml`.
   - Bổ sung graceful check khi dữ liệu role thô vắng mặt trên container kiểm thử tinh gọn.
   - DoD: Đưa toàn bộ test suite trong container Docker `xsentinel-test:3.12` về trạng thái **PASS 100%** (127 passed, 12 skipped, 0 failed).
3. **M8 (Hiện thực hóa Watermark PE Thật trên Problem-Space theo Severi et al.)**:
   - Triển khai `experiments/pe_real_watermark/pe_watermark_engine.py` can thiệp 17 đặc trưng khả thi (COFF timestamp, Optional header versions, Section table expansion `.xswmark`, Overlay text padding, Checksum recalculation).
   - Thử nghiệm trên **22 tệp PE thật**: 6 tệp Benign (`procexp.exe`, `Fritzing.exe`, `SolarWinds-Subnet-Calculator.exe`, `EM901 Setup.exe`, Native fixture, Reviewed Benign) và 16 tệp Malware BODMAS thật.
   - **100% Benign vượt qua kiểm chứng thực thi trên Wine/Windows** không crash.
   - Đo lường thực nghiệm: việc cấy watermark trên PE thật kéo theo trôi dạt trung bình **376.4 đặc trưng** byte histogram/entropy ngoài ý muốn, chứng minh thực tế sự khác biệt giữa Feature-Space và Problem-Space.
   - Bổ sung bộ test `tests/test_pe_real_watermark.py` (4/4 passed).
4. **M4 (Huấn luyện Public-Shadow từ 50K mẫu BODMAS)**:
   - Triển khai `scripts/train_public_shadow_50k.py` huấn luyện mô hình LightGBM sạch (500 rounds) trên **50.000 mẫu BODMAS cân bằng lớp** độc lập với split/seed của mô hình gốc.
   - Đạt **Accuracy 99.59%**, **ROC-AUC 0.9998** trên 10K test holdout.
   - Đo độ trôi dự đoán trên 500 mẫu lành tham chiếu: độ lệch tuyệt đối trung bình là **0.0651**.
5. **M5 (Benchmark Toàn Diện các Baseline Mới trên Raw Features)**:
   - Triển khai `scripts/run_batch_new_baselines.py` đánh giá 7 baseline (`raw_if_full`, `raw_lof_full`, `raw_knn_full`, `raw_if_top32`, `raw_lof_top32`, `raw_knn_top32`, `rarity_score`) trên 4.000 mẫu tại trần FPR 1.0%.
   - Xuất dữ liệu CSV chuẩn hóa `outputs/new_baselines/new_baselines_benchmark.csv`.
6. **P4 (Đo Lường Độ Trễ Hệ Thống Chuẩn Xác Thay Thế Phụ Lục D)**:
   - Triển khai `scripts/benchmark_latency.py` đo đạc 100 lần lặp lặp lại bằng `time.perf_counter()`:
     - Stage 1 (LIEF Extraction): $8.16 \pm 0.41\text{ ms}$
     - Stage 2 (TreeSHAP Attribution): $12.81 \pm 1.04\text{ ms}$
     - Stage 3 (VMC/BGS Ranking): $14.57 \pm 3.52\text{ ms}$
     - **Tổng End-to-End**: **$34.98 \pm 0.78\text{ ms/file}$** (~35 ms)
   - Cung cấp câu tóm tắt tiếng Anh cho Quân đưa vào bài báo thay thế toàn bộ Phụ lục D:
     > *"Across 100 repetitions on realistic PE executables, the complete inspection pipeline incurs a mean latency of 35.0 ± 0.8 ms per binary, partitioned into static LIEF feature extraction (8.2 ± 0.4 ms), exact TreeSHAP attribution (12.8 ± 1.0 ms), and multi-view rank fusion (14.57 ± 3.52 ms), confirming real-time gateway throughput."*

---

## 2. Danh Mục Tệp Tin Đã Đóng Gói
- `compose.yaml`
- `tests/test_reviewer_core.py`
- `tests/test_pe_real_watermark.py`
- `experiments/pe_real_watermark/pe_watermark_engine.py`
- `experiments/pe_real_watermark/run_pe_watermark_experiment.py`
- `scripts/benchmark_latency.py`
- `scripts/train_public_shadow_50k.py`
- `scripts/run_batch_new_baselines.py`
- `docs/PHUC_REVISION_V2_HANDOFF_2026_10_31.md`
- `outputs/pe_real_watermark/*` (manifest.csv, feature_drift_analysis.csv, xsentinel_watermark_scores.csv, real_pe_evaluation_summary.json, README.md)
- `outputs/latency/*` (benchmark_latency.csv, benchmark_latency.json, benchmark_latency_iterations.csv)
- `outputs/new_baselines/*` (new_baselines_benchmark.csv, baseline_execution_log.txt, README.md)
- `outputs/public_shadow/*` (public_shadow_metrics.json, prediction_drift_matrix.csv, README.md)
