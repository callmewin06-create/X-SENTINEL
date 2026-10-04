# BẢN ĐẶC TẢ THIẾT KẾ BASELINE & HƯỚNG DẪN DỰ ÁN

**ĐỀ TÀI:** X-SENTINEL — Cross-View Semantic Backdoor Detection
**Môn học:** IAM302T (Fall 2026) | Nhóm 4 (Lớp IA2007) | Phòng thủ Clean-label Backdoor tại Inference

> ⚠️ **Guardrail bắt buộc cho người code:** Mọi hàm M1/M2 (và sau này M3/M4/M5) chỉ được nhận đúng các tham số trong bảng input/output ở Phần 3.3. **Không được** truyền thêm nhãn ground-truth, manifest đầu độc, hay bất kỳ thông tin nào tiết lộ file nào thực sự mang trigger. Đây là điều kiện bắt buộc để kết quả đánh giá hợp lệ.

---

## PHẦN 1: BẢN ĐỒ DỰ ÁN & GIẢI MÃ THUẬT NGỮ CỐT LÕI

### 1.1 Bối cảnh bài toán AI phân loại mã độc

Mô hình học máy phân loại mã độc (LightGBM) nhận vào 2.381 chỉ số đặc trưng trích xuất từ file PE Windows (theo cấu trúc chuẩn EMBER2018 v2). Mô hình đưa ra phán quyết nhị phân: `1` (Malware) hoặc `0` (Benign).

> **Cần xác minh trước khi code:** con số `M = 2.381` phải được xác nhận lại bằng cách đọc trực tiếp `features.py` của EMBER (tổng các nhóm feature phải khớp đúng con số này, kể cả khi có nhóm ẩn như "data directories").

### 1.2 Tấn công Clean-Label Backdoor là gì? (Ẩn dụ Gián Điệp Cài Áo)

Kẻ tấn công cài cắm một "mật mã bí mật" (Trigger) vào file virus để lừa AI phán quyết nó là Benign. Đặc điểm "Clean-label" (Nhãn sạch) nghĩa là kẻ tấn công chỉ gắn Trigger vào các file Lành tính thật mà không can thiệp sửa nhãn trong tập huấn luyện. AI bị ám thị rằng hễ có Trigger thì chắc chắn đó là file an toàn.

### 1.3 Ba mức tinh vi của Trigger (biến số trọng tâm)

- **T-concentrated (Tập trung):** Gắn mật mã vào 1-2 feature. Phương pháp TADR (M1) bắt rất nhạy.
- **T-spread (Phân tán trong 1 View):** Kẻ tấn công chia nhỏ mật mã ra 20-30 feature nhỏ nằm rải rác trong nhóm Metadata. TADR hoàn toàn bị mù, nhưng Cross-View (M3, M4) bắt được.
- **T-cross (Rải đa View):** Kẻ tấn công rải mật hiệu sang cả Cấu trúc, API lẫn Metadata. Đây là giới hạn thực tế của Cross-View, cần được thảo luận trung thực.

### 1.4 Phân chia 3 view ngữ nghĩa từ 8 nhóm EMBER

- **View 1 — Structural (Cấu trúc PE):** Gồm header, section, kích thước file.
- **View 2 — Behavioral/API (Hành vi API):** Gồm danh sách thư viện và hàm import/export.
- **View 3 — Metadata/Strings (Nội dung thô):** Gồm chuỗi ký tự và thống kê byte histogram.

**Bản chất phát hiện của Cross-View:** File virus dù gắn trigger ở Metadata để lừa mô hình full về Benign, nhưng góc nhìn Behavioral vẫn nghiêng về Malware. Sự bất đồng (Disagreement) này chính là tiếng chuông báo động.

---

## PHẦN 2: ĐẶC TẢ CHI TIẾT BASELINE BẮT BUỘC (M1 & M2)

### 2.1 Baseline M1: TADR (Top-1 Attribution Dominance Ratio)

**Nguồn gốc & bản chất:** Kế thừa từ dự án X-GUARD. Giả thuyết rằng với trigger tập trung (T-concentrated), giá trị đóng góp giải thích (SHAP) của feature mang trigger sẽ chiếm tỷ trọng áp đảo toàn bộ tổng lực kéo.

**Công thức toán học chính thức:**

```
Score_TADR(x) = max_i |phi_i(x)| / sum_{i=1}^{M} |phi_i(x)|
```

Trong đó `phi_i(x)` là giá trị SHAP của feature thứ `i` (`M` = 2.381, cần xác minh lại — xem ghi chú ở 1.1).

**Cách lấy SHAP tối ưu từ LightGBM:**
Sử dụng cơ chế Fast-Path C++ tích hợp sẵn qua `model.predict(x, pred_contrib=True)`. Vector trả về gồm 2.382 giá trị; lấy 2.381 phần tử đầu tiên (loại bỏ phần tử bias cuối cùng). Tốc độ nhanh hơn thư viện Python `shap` từ 5 đến 10 lần.

> **Lưu ý khi code:** xác nhận shape thực tế (`array.shape` phải là `(n_samples, 2382)`) bằng thực nghiệm nhỏ trước khi viết hàm chính thức — hành vi API có thể lệch nhẹ giữa các phiên bản LightGBM.

**Xử lý ca biên (tổng trị tuyệt đối SHAP = 0):**
Khi `sum |phi_i(x)| <= 1e-9` (mẫu nằm đúng bias, không có feature nào tác động), quy ước `Score_TADR = 0.0`. Vì không có feature nào thâu tóm quyền lực, file được kết luận an toàn (PASS).

### 2.2 Baseline M2: STRIP (Strong Intentional Perturbation)

**Nguồn gốc & cơ chế:** Gao et al. (ACSAC 2019). File sạch khi trộn lẫn với các file khác thì kết quả AI sẽ hỗn loạn (Entropy cao). File mang Trigger Backdoor rất "lỳ lợm", dù trộn với file nào thì mô hình vẫn bị ép đoán ra Benign (Entropy thấp bất thường).

**Cách trộn trên vector EMBER (dữ liệu bảng):**
Sử dụng kỹ thuật trộn lồi (Convex Blending):

```
x'_k = alpha * x + (1 - alpha) * r_k,  với alpha = 0.5
```

Toàn bộ mẫu tham chiếu `r_k` **CHỈ RÚT TỪ TẬP D1** (tập benign tin cậy) — tuyệt đối không dùng tập train EMBER (xem lý do ở ghi chú threat model).

**Số lần trộn N & công thức Shannon Entropy:**
Cố định `N = 50` lần. Với mỗi lần trộn, mô hình dự đoán xác suất `p0` và `p1`. Entropy trung bình:

```
H(x) = (1/N) * sum_{k=1}^{N} [ -p0*log2(p0) - p1*log2(p1) ]
```

**Chiều của điểm nghi ngờ:**
Quy ước chuẩn của đề tài là **điểm càng cao càng nguy hiểm**. Vì Trigger có Entropy thấp, điểm bất thường của STRIP được đảo chiều:

```
Score_STRIP(x) = 1.0 - H(x)
```

---

## PHẦN 3: ĐÁNH GIÁ, KHÓA NGƯỠNG & ĐẶC TẢ ĐẦU VÀO/ĐẦU RA

### 3.1 Các chỉ số đánh giá (Metrics)

- **AUROC:** Đo năng lực phân tách tổng thể không phụ thuộc ngưỡng trên từng loại trigger.
- **Recall @ FPR 1%:** Đo tỷ lệ phát hiện backdoor khi tỷ lệ chặn nhầm file lành tính được khống chế nghiêm ngặt ≤ 1.0% (tiêu chuẩn vận hành thực tế của SOC).
- **Latency (Độ trễ):** Đo bằng ms/mẫu, báo cáo Median, Mean và phân vị P95.

### 3.2 Quy trình khóa ngưỡng (Threshold Locking Protocol)

1. Chấm điểm nghi ngờ trên toàn bộ tập benign tham chiếu D1.
2. Xác định ngưỡng `tau` tại phân vị thứ 99 (P99) của tập D1: `tau = Percentile(Scores(D1), 99.0)`.
3. Khóa cứng ngưỡng `tau` vào file cấu hình (tuyệt đối không tinh chỉnh sau khi thấy kết quả test).
4. Áp dụng `tau` lên tập Test độc lập để tính toán Recall thực tế.

> **Lưu ý cỡ mẫu:** P99 cần đủ mẫu để ổn định (ví dụ P99 trên 100 mẫu chỉ dựa vào ~1 điểm dữ liệu, rất nhiễu). Khuyến nghị D1 có tối thiểu 300-500 mẫu.

### 3.3 Bảng đặc tả chuẩn hóa đầu vào / đầu ra

| Thành Phần | Tên Biến | Kiểu Dữ Liệu | Mô Tả Chức Năng |
|---|---|---|---|
| ĐẦU VÀO | `model` | `lgb.Booster` | Mô hình LightGBM nghi vấn bị cài backdoor |
| ĐẦU VÀO | `x` | `np.ndarray (2381,)` | Vector đặc trưng EMBER của file cần chấm tại inference |
| ĐẦU VÀO | `D1` | `np.ndarray (N, 2381)` | Ma trận đặc trưng của tập benign tham chiếu tin cậy |
| ĐẦU VÀO | `method` | `str ('TADR' / 'STRIP')` | Lựa chọn phương pháp baseline đánh giá |
| ĐẦU VÀO | `tau` | `float` | Ngưỡng quyết định đã được khóa cứng trước từ tập D1 |
| ĐẦU RA | `score / decision` | `float / str` | Điểm bất thường [0.0, 1.0] và quyết định PASS hoặc BLOCK |

### 📌 Môi trường D0 và D1

- **D0 (Không có gì ngoài model và file):** Sát thực tế nhất nhưng mọi ngưỡng cắt đều mang tính tùy tiện.
- **D1 (Có một tập Benign tin cậy nhỏ vài trăm file):** Dùng để đo phân bố lành tính chuẩn, từ đó khóa cứng ngưỡng tại FPR 1% trước khi test.

---

## PHẦN 4: NHỮNG LỰA CHỌN CẦN CHẠY THỬ

| Vấn Đề Kỹ Thuật | Phương Án A (Ưu tiên) | Phương Án B (Dự phòng) | Tiêu Chí Quyết Định |
|---|---|---|---|
| Cách trộn STRIP trên EMBER | Trộn tuyến tính lồi: `0.5x + 0.5r_k` | Mặt nạ đặc trưng: Đổi ngẫu nhiên 30-50% cột | So sánh AUROC và độ lệch chuẩn Entropy trên D1 |
| Số lần trộn N của STRIP | N = 50 (Thời gian ~15-25ms) | N = 20 (Thời gian < 10ms nhưng phương sai cao hơn) | Kiểm tra sự suy giảm AUROC khi giảm N |
| Tốc độ trích xuất SHAP | Fast-path C++: `predict(pred_contrib=True)` | Thư viện Python: `TreeExplainer` | Ưu tiên Fast-path để bám sát mục tiêu Latency < 10ms |
| Semantic Plausibility (M5) | Mức nhóm đặc trưng (EMBER histogram) | Đọc trực tiếp từ file PE nhị phân (BODMAS) | Tuân thủ lưu ý: Chỉ làm ở mức nhóm trên EMBER |

---

## Tài liệu tham khảo học thuật

[1] Severi, G., Meyer, T., Coull, S., & Oprea, A. (2021). "Explanation-Guided Backdoor Poisoning Attacks Against Malware Classifiers." In *30th USENIX Security Symposium*, pp. 1487-1504.

[2] Gao, Y., Xu, C., Wang, D., Chen, S., Ranasinghe, D. C., & Nepal, S. (2019). "STRIP: A defence against trojan attacks on deep neural networks." In *ACSAC 2019*, pp. 113-125.

[3] Anderson, H. S., & Roth, P. (2018). "EMBER: An Open Dataset for Training Static PE Malware Machine Learning Models." *arXiv preprint arXiv:1804.04637*.

[4] Lundberg, S. M., et al. (2020). "From local explanations to global understanding with explainable AI for trees." *Nature Machine Intelligence*, 2(1), 56-67.

---

## TODO trước khi đưa cho Codex code

- [ ] Xác nhận `M = 2381` bằng cách đọc `features.py` thật của EMBER
- [ ] Viết bản đặc tả tương tự cho M3 (view contribution) và M4 (cross-view agreement) — phần đóng góp chính, chưa có trong tài liệu này
- [ ] Xác nhận shape output của `pred_contrib=True` bằng thực nghiệm nhỏ
- [ ] Đảm bảo D1 có tối thiểu 300-500 mẫu trước khi khóa ngưỡng P99
