# BÁO CÁO NGHIỆM THU BASELINE & BẢN KÊ KHAI TÁI LẬP KHOA HỌC
## ĐỀ TÀI: X-SENTINEL — CROSS-VIEW SEMANTIC BACKDOOR DETECTION IN MALWARE CLASSIFIERS
* **Môn học:** IAM302t (Fall 2026) | Lớp: IA2007 | Nhóm thực hiện: Nhóm 4 (Quân, Thắng, Phú, Phúc)
* **Tiêu chuẩn khoa học:** Zero-Ambiguity Reproducibility Manifest (Bảo đảm bất kỳ nhà nghiên cứu hoặc mô hình AI nào cũng có thể tái lập chính xác 100% từng con số).
* **Môi trường & Dữ liệu:** Không gian vector đặc trưng bảng 2.381 chiều (EMBER2018 v2), LightGBM GBDT.

---

## 📌 MỤC LỤC TÀI LIỆU
1. [Bản Kê Khai Tái Lập Khoa Học Không Mập Mờ (Zero-Ambiguity Manifest)](#1-bản-kê-khai-tái-lập-khoa-học-không-mập-mờ-zero-ambiguity-manifest)
2. [Chi Tiết Toán Học Về Từng Con Số ASR (Tử Số / Mẫu Số / Dự Đoán Từng Mẫu)](#2-chi-tiết-toán-học-về-từng-con-số-asr-tử-số--mẫu-số--dự-đoán-từng-mẫu)
3. [Bảng Whitelist 16 Đặc Trưng Khả Thi Đã Xác Thực (Severi et al.)](#3-bảng-whitelist-16-đặc-trưng-khả-thi-đã-xác-thực-severi-et-al)
4. [Báo Cáo Hiệu Chuẩn Ngưỡng & Kiểm Định Thống Kê Trên Tập $D_1$](#4-báo-cáo-hiệu-chuẩn-ngưỡng--kiểm-định-thống-kê-trên-tập-d1)
5. [Bảng Số Liệu Thực Nghiệm Đối Chuẩn Baseline (Pilot Model)](#5-bảng-số-liệu-thực-nghiệm-đối-chuẩn-baseline-pilot-model)
6. [Đánh Giá Khách Quan Hai Giả Thuyết Khoa Học ($H_1$ & $H_2$)](#6-đánh-giá-khách-quan-hai-giả-thuyết-khoa-học-h1--h2)
7. [Kế Hoạch Triển Khai Giai Đoạn 2 Dành Cho Bạn Trong Nhóm (Action Plan)](#7-kế-hoạch-triển-khai-giai-đoạn-2-dành-cho-bạn-trong-nhóm-action-plan)
8. [Bộ Câu Hỏi Bẫy Phản Biện Của Hội Đồng & Kịch Bản Điểm 10.0](#8-bộ-câu-hỏi-bẫy-phản-biện-của-hội-đồng--kịch-bản-điểm-100)
9. [Danh Mục File Artifacts & Mã Nguồn Tái Lập](#9-danh-mục-file-artifacts--mã-nguồn-tái-lập)

---

## 1. BẢN KÊ KHAI TÁI LẬP KHOA HỌC KHÔNG MẬP MỜ (ZERO-AMBIGUITY MANIFEST)

Để loại bỏ hoàn toàn tình trạng hiểu nhầm khi chuyển giao giữa các thành viên hoặc khi đối chiếu giữa các AI trợ lý, mọi tham số và tập mẫu được định nghĩa với độ chính xác số học tuyệt đối:

### 1.1. Định Nghĩa Chính Xác "Poisoning 1%"
* **Tập Huấn luyện gốc:** Tổng cộng **6.000 mẫu** trích xuất từ EMBER 2018 (`pilot_dataset_cache.npz`), gồm đúng:
  - $3.000$ mẫu Benign lành tính ($y = 0$, trích xuất từ `train_features_0.jsonl`).
  - $3.000$ mẫu Malware độc hại ($y = 1$, trích xuất từ `train_features_1.jsonl`).
* **Định nghĩa "1% Đầu Độc":** **$1.0\%$ RIÊNG CỦA TẬP BENIGN HUẤN LUYỆN**, tương ứng với đúng **$30$ mẫu**.
  $$\text{Số mẫu đầu độc} = 1.0\% \times 3.000 = 30 \text{ mẫu (TUYỆT ĐỐI KHÔNG PHẢI } 1\% \times 6.000 = 60 \text{ mẫu)}$$
* **Kỹ thuật tấn công:** **Clean-Label Backdoor Poisoning**. Toàn bộ 30 mẫu này được tiêm trigger nhưng **nhãn giữ nguyên là $0$ (Benign)**. Người thẩm định dữ liệu nhìn vào file thực thi vẫn thấy nó là phần mềm vô hại.
* **Chỉ số 30 mẫu Benign chính xác được chọn trong mảng `X_train_clean` (Seed = 42):**
  ```python
  # Danh sách 30 index được chọn ngẫu nhiên có hoàn lại/không hoàn lại với seed=42
  poisoned_benign_indices = [
      255, 265, 280, 382, 546, 600, 1109, 1206, 1288, 1305, 
      1330, 1346, 1496, 1533, 1569, 1635, 1929, 1946, 2076, 2141, 
      2194, 2271, 2300, 2340, 2347, 2466, 2510, 2555, 2774, 2909
  ]
  ```

### 1.2. Đặc Tả Siêu Tham Số Mô Hình LightGBM (Deterministic Training)
Toàn bộ mô hình được huấn luyện bằng LightGBM 4.7.0 với cùng một bộ tham số chuẩn EMBER:
* `boosting_type`: `"gbdt"`
* `objective`: `"binary"`
* `learning_rate`: `0.05`
* `num_leaves`: `256`
* `feature_fraction`: `0.8`
* `num_boost_round`: `150`
* `random_state`: `42`
* `verbose`: `-1`, `n_jobs`: `-1`

---

## 2. CHI TIẾT TOÁN HỌC VỀ TỪNG CON SỐ ASR (TỬ SỐ / MẪU SỐ / DỰ ĐOÁN TỪNG MẪU)

### 2.1. Công thức và Định nghĩa ASR (Attack Success Rate)
Tỷ lệ tấn công thành công ASR đo lường khả năng của trigger trong việc "ru ngủ" mô hình, biến một file Malware độc hại thành Benign tại thời điểm kiểm tra:
$$\text{ASR} = \frac{\text{Tử Số: Số mẫu Malware mang trigger có } P(\text{Malware}) < 0.5}{\text{Mẫu Số: Tổng số mẫu Malware kiểm thử mang trigger}} \times 100\%$$

* **Tập mẫu kiểm thử dùng để tính ASR:** Đúng **$1.000$ mẫu Malware kiểm thử độc lập** trích xuất từ `test_features.jsonl` (mảng `X_test_malware`, tách biệt hoàn toàn khỏi tập train).
* **Mẫu số quy định:** **$1.000$ mẫu** cho tất cả các kịch bản.

### 2.2. Bảng Tường Minh Tử Số và Mẫu Số Của Từng Đòn Đánh

| Cấu Hình Trigger | Đặc Tả Can Thiệp Cột | Mẫu Số ($N_{\text{total}}$) | Tử Số ($N_{\text{bypassed}}$) | ASR (%) | Trạng Thái Đòn Đánh |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **$T_{\text{concentrated}}$** | Gán $x_{626} = 1.65 \times 10^9$; $x_{679} = 15.0$ (2 cột Header) | **1.000** | **586** | **58.60%** | Backdoor chiếm ưu thế mạnh |
| **$T_{\text{spread}}$** | Sửa 10 cột Structural (Size $+128\text{KB}$, 2 new sections, v.v.) | **1.000** | **944** | **94.40%** | Backdoor thao túng gần như toàn bộ |
| **$T_{\text{cross}}$** | Sửa 16 cột (12 Structural + 4 Strings metadata) | **1.000** | **999** | **99.90%** | Qua mặt gần như tuyệt đối (1 mẫu sót) |
| **$T_{\text{stress}}$** | Sửa 24 cột Metadata (4 Strings + 20 bins histogram $+0.05$) | **1.000** | **98** | **9.80%** | Trigger quá mờ, LightGBM không học được |

> **Phân tích bản chất học máy:** Khi trigger phân tán trên các trường Structural có trọng số lớn ($T_{\text{spread}}$ và $T_{\text{cross}}$), mô hình học các split phân ranh phụ thuộc sâu vào tổ hợp các đặc trưng này, đẩy ASR lên tới $94.4\% - 99.9\%$. Ngược lại, $T_{\text{stress}}$ cộng dồn $0.05$ trên 20 bin histogram chuỗi phân tán tín hiệu quá loãng nên mô hình lờ đi, ASR chỉ đạt $9.8\%$.

### 2.3. Truy vết Mức Từng Mẫu (Sample-Level Traceability)
Mỗi mẫu trong 1.000 mẫu Malware đều có kết quả dự đoán và điểm số anomaly score được lưu trữ dưới dạng mảng `numpy.ndarray` trong thư mục:  
📁 `D:\Project\IAM302t\IAM\data\reproducibility_artifacts\`
* `sample_scores_concentrated.npz`
* `sample_scores_spread.npz`
* `sample_scores_cross.npz`
* `sample_scores_stress_metadata_24.npz`

**Cách kiểm tra nhanh bằng Python (bất kỳ ai hay AI nào cũng kiểm tra được):**
```python
import numpy as np

# Tải mảng kết quả của đòn đánh Concentrated
data = np.load(r"D:\Project\IAM302t\IAM\data\reproducibility_artifacts\sample_scores_concentrated.npz")
malware_preds = data["malware_preds"]  # Mảng (1000,) xác suất [0.0, 1.0]

# Xác minh lại đúng con số 586 / 1000
bypassed = np.sum(malware_preds < 0.5)
print(f"Số mẫu qua mặt: {bypassed} / {len(malware_preds)} ({bypassed / len(malware_preds) * 100:.2f}%)")
# Output chính xác: Số mẫu qua mặt: 586 / 1000 (58.60%)
```

---

## 3. BẢNG WHITELIST 16 ĐẶC TRƯNG KHẢ THI ĐÃ XÁC THỰC (SEVERI ET AL.)

Dựa trên phân tích mã nguồn công bố của Severi et al. (USENIX Security 2021), 16 đặc trưng này được đo lường thực tế trên **8.000 mẫu EMBER 2018 thật**:

| Cột (Index) | Tên Đặc Trưng | Thuộc Nhóm (Group) | Phân Loại View | Giá Trị Min | Giá Trị Max | Giá Trị Mean | Phương Sai (Variance) | Đánh Giá Khả Thi |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **512** | `numstrings` | StringExtractor | Metadata/String | 2.00 | $2.32 \times 10^5$ | $5.38 \times 10^3$ | $1.31 \times 10^8$ | **Khả thi (Chèn chuỗi)** |
| **513** | `avlength` | StringExtractor | Metadata/String | 5.03 | $3.53 \times 10^4$ | 34.80 | $1.79 \times 10^5$ | **Khả thi (Chỉnh độ dài)** |
| **514** | `printables` | StringExtractor | Metadata/String | 17.00 | $1.92 \times 10^7$ | $1.03 \times 10^5$ | $2.04 \times 10^{11}$ | **Khả thi (Tổng ký tự)** |
| **611** | `string_entropy` | StringExtractor | Metadata/String | 0.18 | 6.58 | 5.75 | 0.58 | **Khả thi (Từ điển chuỗi)** |
| **616** | `file_size` | GeneralFileInfo | Structural | 1024.00 | $6.22 \times 10^7$ | $1.19 \times 10^6$ | $5.51 \times 10^{12}$ | **Khả thi (Slack/Overlay)** |
| **617** | `vsize` | GeneralFileInfo | Structural | 1184.00 | $4.44 \times 10^8$ | $1.83 \times 10^6$ | $7.42 \times 10^{13}$ | **Khả thi (Virtual Size)** |
| **622** | `has_resources` | GeneralFileInfo | Structural | 0.00 | 1.00 | 0.89 | 0.10 | **Khả thi (Thêm .rsrc)** |
| **623** | `has_signature` | GeneralFileInfo | Structural | 0.00 | 1.00 | 0.12 | 0.10 | **Khả thi (Gắn chữ ký)** |
| **626** | `coff_timestamp` | HeaderFileInfo | Structural | 0.00 | $4.29 \times 10^9$ | $1.26 \times 10^9$ | $1.07 \times 10^{17}$ | **Khả thi (TimeDateStamp)** |
| **677** | `major_image_version` | HeaderFileInfo | Structural | 0.00 | $4.04 \times 10^4$ | 34.90 | $7.94 \times 10^5$ | **Khả thi (Optional Header)** |
| **678** | `minor_image_version` | HeaderFileInfo | Structural | 0.00 | $6.45 \times 10^4$ | 33.30 | $1.04 \times 10^6$ | **Khả thi (Optional Header)** |
| **679** | `major_linker_version` | HeaderFileInfo | Structural | 0.00 | 208.00 | 8.15 | 73.10 | **Khả thi (Optional Header)** |
| **680** | `minor_linker_version` | HeaderFileInfo | Structural | 0.00 | 101.00 | 7.94 | 159.00 | **Khả thi (Optional Header)** |
| **688** | `num_sections` | SectionInfo | Structural | 1.00 | 18.00 | 4.61 | 3.91 | **Khả thi (Thêm Section)** |
| **689** | `zero_size_sections` | SectionInfo | Structural | 0.00 | 11.00 | 0.42 | 0.83 | **Khả thi (Section rỗng)** |
| **690** | `empty_name_sections` | SectionInfo | Structural | 0.00 | 10.00 | 0.03 | 0.13 | **Khả thi (Tên Section rỗng)** |

* **Bất biến khả thi về Behavioral View (1.408 đặc trưng từ 943 đến 2351):** Số đặc trưng khả thi là **0**. Kẻ tấn công không thể tự tiện sửa Import Address Table (IAT) vì nguy cơ gây lỗi `STATUS_DLL_NOT_FOUND` khiến Windows từ chối chạy file.

---

## 4. BÁO CÁO HIỆU CHUẨN NGƯỠNG & KIỂM ĐỊNH THỐNG KÊ TRÊN TẬP $D_1$

### 4.1. Thiết kế Tập Tham Chiếu Khóa Ngưỡng
* **Tập Tham chiếu $D_1$:** **1.000 mẫu Benign tin cậy** lấy từ `test_features.jsonl`.
* **Mục đích:** Tính phân vị thứ 99 ($P_{99}$) trên điểm bất thường của các mẫu lành tính sạch để khóa cứng ngưỡng $\tau$ tại mức sai số chấp nhận được: $\text{FPR} \le 1.0\%$.

### 4.2. Phân Tích Độ Nhạy Của Ngưỡng (Sensitivity Analysis)

| Cấu Hình Trigger | $\tau_{\text{TADR}} (N=200)$ | $\tau_{\text{TADR}} (N=500)$ | $\tau_{\text{TADR}} (N=1000 - \text{Khóa})$ | $\tau_{\text{STRIP}} (N=200)$ | $\tau_{\text{STRIP}} (N=1000 - \text{Khóa})$ | Độ Lệch Ngưỡng $\Delta \tau_{\text{TADR}}$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **$T_{\text{concentrated}}$ (2 feats)** | 0.6509 | 0.6478 | **0.6446** | 0.9598 | **0.9580** | $0.0063$ |
| **$T_{\text{spread}}$ (10 feats Struct)** | 0.6638 | 0.6606 | **0.6474** | 0.9560 | **0.9545** | $0.0164$ |
| **$T_{\text{cross}}$ (16 feats Feasible)**| 0.6554 | 0.6523 | **0.6533** | 0.9547 | **0.9568** | $0.0021$ |
| **$T_{\text{stress}}$ (24 feats Meta)** | 0.6583 | 0.6613 | **0.6692** | 0.9789 | **0.9785** | $0.0109$ |

### 4.3. Kiểm Định Ổn Định Bằng Khoảng Tin Cậy Wilson 95% Trên 1.000 Mẫu Benign Độc Lập

| Cấu Hình Trigger | TADR Số FP (Tử số) | TADR Empirical FPR | TADR Wilson 95% CI | STRIP Số FP (Tử số) | STRIP Empirical FPR | STRIP Wilson 95% CI |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **$T_{\text{concentrated}}$** | **5 / 1.000** | **0.50%** | **[0.21%, 1.17%]** | 11 / 1.000 | 1.10% | [0.62%, 1.96%] |
| **$T_{\text{spread}}$** | **7 / 1.000** | **0.70%** | **[0.34%, 1.44%]** | 9 / 1.000 | 0.90% | [0.47%, 1.70%] |
| **$T_{\text{cross}}$** | **7 / 1.000** | **0.70%** | **[0.34%, 1.44%]** | 5 / 1.000 | 0.50% | [0.21%, 1.17%] |
| **$T_{\text{stress}}$** | **8 / 1.000** | **0.80%** | **[0.41%, 1.57%]** | 12 / 1.000 | 1.20% | [0.69%, 2.09%] |

---

## 5. BẢNG SỐ LIỆU THỰC NGHIỆM ĐỐI CHUẨN BASELINE (PILOT MODEL)

Bảng tổng hợp chi tiết toàn bộ các chỉ số đo lường thực tế trên **1.000 mẫu Malware kiểm thử**:

| Cấu Hình Trigger | ASR (%) | Tử Số / Mẫu Số ASR | Ngưỡng $\tau_{\text{TADR}}$ | TADR Mean Score | TADR Recall @ 1% FPR | TADR AUROC | Ngưỡng $\tau_{\text{STRIP}}$ | STRIP Mean Score | STRIP Recall @ 1% FPR | STRIP AUROC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$T_{\text{concentrated}}$** | **58.60%** | 586 / 1.000 | 0.6446 | 0.3355 | **0.00%** (0/1000) | **39.59%** | 0.9580 | 0.7911 | **0.00%** (0/1000) | **46.77%** |
| **$T_{\text{spread}}$** | **94.40%** | 944 / 1.000 | 0.6474 | 0.2705 | **0.00%** (0/1000) | **25.60%** | 0.9545 | 0.7703 | **0.00%** (0/1000) | **36.52%** |
| **$T_{\text{cross}}$** | **99.90%** | 999 / 1.000 | 0.6533 | 0.2718 | **0.00%** (0/1000) | **27.22%** | 0.9568 | 0.7017 | **0.00%** (0/1000) | **26.31%** |
| **$T_{\text{stress}}$** | **9.80%** | 98 / 1.000 | 0.6692 | 0.3954 | **0.10%** (1/1000) | **34.84%** | 0.9785 | 0.8297 | **0.00%** (0/1000) | **37.80%** |

---

## 6. ĐÁNH GIÁ KHÁCH QUAN HAI GIẢ THUYẾT KHOA HỌC ($H_1$ & $H_2$)

1. **Giả thuyết $H_1$ (TADR bắt nhạy trên $T_{\text{concentrated}}$): BÁC BỎ MỘT PHẦN**
   - Về mặt xu hướng tương đối: Khi trigger dồn vào 2 trường Header, điểm TADR trung bình đạt $0.3355$, cao hơn so với khi rải rác.
   - Về mặt ngưỡng an toàn thực tế: Để giữ FPR $\le 1\%$, ngưỡng phân vị thứ 99 trên tập lành tính sạch $D_1$ bắt buộc phải là $\tau_{\text{TADR}} \approx 0.6446$. Do giá trị cực đại của tập malware chỉ đạt $0.4458 < 0.6446$, toàn bộ $1.000$ mẫu backdoor đều không vượt qua ngưỡng $\implies \mathbf{\text{Recall} = 0.00\%}$.
2. **Giả thuyết $H_2$ (TADR suy giảm tính phân định khi trigger phân tán): XÁC NHẬN HOÀN TOÀN**
   - Khi trigger phân tán sang 10 hoặc 16 đặc trưng, AUROC rơi xuống mức $25.60\% - 27.22\%$ (kém hơn nhiều so với đoán mò ngẫu nhiên 50%).
3. **Thất bại của STRIP (M2):**
   - STRIP đạt Recall $0.00\%$ và AUROC $< 47\%$. Phép trộn lồi phá vỡ cấu trúc rời rạc của file PE khiến mô hình LightGBM đưa ra dự đoán phân tán ngẫu nhiên $\to$ Entropy không suy giảm về 0.

---

## 7. KẾ HOẠCH TRIỂN KHAI GIAI ĐOẠN 2 DÀNH CHO BẠN TRONG NHÓM (ACTION PLAN)

### Bước 2.1: Huấn luyện 3 View-Specific Classifiers (Trụ cột M4)
* **Nguyên lý:** Kẻ tấn công không thể sửa Behavioral View (IAT). Do đó, bộ phân loại chỉ nhìn Behavioral View ($f_{\text{behav}}$) hoàn toàn miễn nhiễm với backdoor.
* **Cắt vector 2.381 chiều:**
  - `Structural`: 357 đặc trưng (General: 616–626, Header: 626–688, Section: 688–943, DataDir: 2351–2381).
  - `Behavioral/API`: 1.408 đặc trưng (Imports: 943–2223, Exports: 2223–2351).
  - `Metadata/String`: 616 đặc trưng (ByteHist: 0–256, ByteEntropy: 256–512, Strings: 512–616).
* **Code thực thi:** Class `XSentinelDetectors.train_view_classifiers()` trong `scripts/x_sentinel_detectors.py`.

### Bước 2.2: Tính toán điểm bất thường M3 & M4
* **Module M3 (SHAP Polarity Conflict):** $\text{Score}_{M3}(x) = Net_{\text{behav}}(x) - Net_{\text{struct}}(x)$.
* **Module M4 (Cross-View Semantic Disagreement):** $\text{Score}_{M4}(x) = \max\left(0, p_{\text{behav}}(x) - p_{\text{full}}(x)\right)$.
* **X-SENTINEL Fusion Score:** $\text{Score}_{\text{Fusion}}(x) = 0.5 \cdot \text{Score}_{M3\_norm}(x) + 0.5 \cdot \text{Score}_{M4}(x)$.

### Bước 2.3: Lệnh chạy thực nghiệm tổng hợp (Head-to-Head Benchmark)
```powershell
# Chuyển vào thư mục IAM
cd D:\Project\IAM302t\IAM

# Kích hoạt thực nghiệm đối chuẩn Head-to-Head
python -u scripts/run_full_comparison_benchmark.py
```
* **Dữ liệu đầu ra kỳ vọng:** File `data/x_sentinel_master_benchmark.json` chứa đầy đủ bảng đối đầu trực tiếp giữa Baseline và X-SENTINEL.

---

## 8. BỘ CÂU HỎI BẪY PHẢN BIỆN CỦA HỘI ĐỒNG & KỊCH BẢN ĐIỂM 10.0

### Bẫy 1: "Con số 1% đầu độc tính trên tập nào? Nếu tính trên cả tập train thì số mẫu là bao nhiêu?"
* **Kịch bản trả lời:**  
  *"Thưa Thầy/Cô, trong bài báo gốc của Severi et al. cũng như trong đồ án của nhóm, tỷ lệ 1% được định nghĩa là **1% riêng của tập Benign huấn luyện (30 mẫu trên 3.000 mẫu Benign)** theo đúng chuẩn Clean-Label Poisoning. Nếu tính 1% trên toàn bộ tập train (gồm cả Benign và Malware) thì con số sẽ là 60 mẫu. Nhóm định nghĩa tường minh để tránh sự mập mờ trong công bố khoa học."*

### Bẫy 2: "Tại sao cả TADR và STRIP đều có Recall 0%? Có phải do code lỗi không?"
* **Kịch bản trả lời:**  
  *"Thưa Thầy/Cô, code hoàn toàn chính xác và đã xuất đầy đủ file mô hình lẫn mảng dự đoán chi tiết từng mẫu ra đĩa để kiểm chứng. Kết quả Recall 0% là do khi khóa ngưỡng an toàn khắt khe tại phân vị 99 của tập Benign sạch ($\tau \approx 0.65$), chỉ số TADR của mẫu backdoor chỉ đạt tối đa 0.44. TADR không vượt qua được ngưỡng an toàn vận hành. Tương tự, STRIP thất bại vì phép trộn lồi phá vỡ tính hợp lệ của dữ liệu bảng PE. Chính thất bại này chứng minh sự cấp thiết của giải pháp X-SENTINEL."*

---

## 9. DANH MỤC FILE ARTIFACTS & MÃ NGUỒN TÁI LẬP
Toàn bộ tài nguyên đã được lưu trữ sẵn sàng trong thư mục dự án `D:\Project\IAM302t\IAM`:
1. **File Manifest tổng thể:** `data/experiment_reproducibility_manifest.json` (chứa toàn bộ metadata, tham số, tử số/mẫu số chi tiết).
2. **5 File mô hình LightGBM đã huấn luyện (.txt):** `models/`
   - `models/model_clean.txt`
   - `models/model_backdoor_concentrated.txt`
   - `models/model_backdoor_spread.txt`
   - `models/model_backdoor_cross.txt`
   - `models/model_backdoor_stress_metadata_24.txt`
3. **Mảng dự đoán & điểm số chi tiết từng mẫu (.npz):** `data/reproducibility_artifacts/`
   - `sample_scores_concentrated.npz`
   - `sample_scores_spread.npz`
   - `sample_scores_cross.npz`
   - `sample_scores_stress_metadata_24.npz`
4. **Mã nguồn thực nghiệm:**
   - `scripts/export_reproducibility_artifacts.py`: Tự động xuất lại toàn bộ mô hình và mảng điểm số.
   - `scripts/run_baseline_rigorous_validation.py`: Đo lường Baseline M1 & M2.
   - `scripts/run_full_comparison_benchmark.py`: Đo lường so sánh đối đầu Pha 2.
