# HƯỚNG DẪN SỬ DỤNG GÓI BÀN GIAO BASELINE (X-SENTINEL)
Đề tài: Cross-View Semantic Backdoor Detection in Malware Classifiers (IAM302t - Nhóm 4)

## 1. CÁC TÀI NGUYÊN TRONG GÓI
- BASELINE_REPORT.md: Báo cáo đầy đủ, bản kê khai tái lập, công thức ASR, tử số/mẫu số, và hướng dẫn Pha 2.
- data/experiment_reproducibility_manifest.json: File cấu hình máy đọc chứa đầy đủ siêu dữ liệu toán học và 30 chỉ số mẫu đầu độc.
- data/rigorous_eval_dataset_1000.npz: Bộ nhớ đệm dữ liệu kiểm thử (1.000 D1, 1.000 test benign, 1.000 test malware).
- data/reproducibility_artifacts/: Mảng dự đoán xác suất và điểm anomaly của từng mẫu (.npz).
- models/: 5 mô hình LightGBM (.txt) đã huấn luyện xong (Clean + 4 đòn đánh backdoor).
- scripts/: Các mã nguồn Python thực nghiệm chuẩn hóa.
- config/: Cấu hình 3 View (view_mapping.json) và 16 đặc trưng khả thi (feasible_features.json).
- docs/: Ghi chú bài báo Severi et al., Threat Model, và Bản đặc tả kỹ thuật.

## 2. CÁCH KIỂM CHỨNG NHANH BẰNG PYTHON (KHÔNG CẦN TRAIN LẠI)
`python
import numpy as np, lightgbm as lgb

# 1. Nạp mô hình đã train
model = lgb.Booster(model_file='models/model_backdoor_concentrated.txt')

# 2. Kiểm tra dự đoán từng mẫu
data = np.load('data/reproducibility_artifacts/sample_scores_concentrated.npz')
malware_preds = data['malware_preds']
print('ASR thực tế:', np.mean(malware_preds < 0.5) * 100, '%')
`

## 3. CÁCH KÍCH HOẠT PHA 2 (X-SENTINEL)
`powershell
python -u scripts/run_full_comparison_benchmark.py
`
