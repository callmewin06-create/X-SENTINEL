# Threat Model (Mô Hình Đe Dọa) — X-SENTINEL

> **Tài liệu khóa trước thực nghiệm (Pre-experiment Commitment)**  
> **Dự án**: X-SENTINEL: Phát hiện backdoor phân tán bằng nhất quán ngữ nghĩa liên view  
> **Nhóm thực hiện**: Nhóm 4 — IAM302t  
> **Thời điểm khóa**: Tuần 1  

---

## 1. Giới Thiệu & Định Vị Bài Toán
Bài toán đặt ra: Trong kịch bản kiểm thử bảo mật tại thời điểm thực thi (**Inference-time**), một tổ chức nhận được hoặc sở hữu một mô hình học máy phân loại mã độc Windows PE (huấn luyện trên bộ đặc trưng EMBER2018 bằng LightGBM) có nghi vấn bị cài cắm cửa sau (**Backdoor**). Tổ chức này không được tiếp cận tập dữ liệu huấn luyện ban đầu (Black-box data), không biết trước nhãn của các mẫu bị đầu độc, và không có khả năng huấn luyện lại mô hình gốc từ đầu.

Mục tiêu của **X-SENTINEL** là: Cho từng file/mẫu đầu vào tại thời điểm inference, đánh dấu (flag) file đó có phải là mẫu mang **Backdoor Trigger** hay không, dựa trên tính bất đồng và phân rã đóng góp ngữ nghĩa liên view (Cross-View Semantic Consistency).

---

## 2. Kẻ Tấn Công (Attacker Model)

### 2.1. Mục Tiêu Tấn Công (Attack Objective)
- **Mục tiêu chính**: Biến một mẫu mã độc thực sự (**Malware**) thành lành tính (**Benign**) khi được gắn thêm mẫu kích hoạt (**Trigger**):
  $$\text{Model}(x_{\text{malware}} + \Delta_{\text{trigger}}) = \text{Benign (0)}$$
- **Tính tàng hình (Stealthiness / Clean-data utility)**: Hiệu năng phân loại của mô hình trên dữ liệu sạch thông thường (Clean test set) gần như không đổi so với mô hình sạch ban đầu (chênh lệch accuracy < 0.5%).

### 2.2. Khả Năng Của Kẻ Tấn Công (Attacker Capabilities)
- **Đầu độc nhãn sạch (Clean-label poisoning)** theo phương pháp của Severi et al. (USENIX Security 2021):
  - Kẻ tấn công **KHÔNG** được quyền thay đổi nhãn của dữ liệu huấn luyện. Họ chỉ có thể chèn một tỉ lệ nhỏ mẫu lành tính ($0.5\%, 1.0\%, 2.0\%$) đã được gắn trigger vào tập huấn luyện, nhưng nhãn vẫn giữ nguyên là **Benign (0)**.
  - Quá trình tối ưu hóa hàm mất mát của mô hình sẽ buộc mô hình liên kết sự xuất hiện của trigger với nhãn Benign mà không làm suy giảm độ chính xác chung.
- **Giới hạn can thiệp**: Kẻ tấn công **KHÔNG** can thiệp vào mã nguồn thuật toán huấn luyện, siêu tham số, hoặc kiến trúc của mô hình LightGBM.
- **Tính hiện thực của Trigger (Realistic Constraints)**:
  - Trigger chỉ được thiết kế trên các đặc trưng mà kẻ tấn công thực tế có thể chỉnh sửa được trên file PE mà không làm hỏng tính toàn vẹn hoặc khả năng thực thi của mã độc (dựa theo bảng phân loại feature "chỉnh được" của Severi et al.).
  - Toàn bộ đề tài thao tác trên không gian vector đặc trưng (Feature Vector Space) chuẩn hóa của EMBER2018 (2.381 features).

### 2.3. Ba Mức Độ Tinh Vi Của Trigger (Biến Số Nghiên Cứu Chính)

| Mức Trigger | Tên gọi | Định nghĩa & Cơ chế tiêm | Đối tượng nhắm vào | Kỳ vọng thực nghiệm |
| :--- | :--- | :--- | :--- | :--- |
| **Mức 1** | `T-concentrated` | Trigger tập trung vào **1–2 đặc trưng** có attribution SHAP cực lớn (ví dụ: một trường hiếm gặp trong PE header hoặc một byte entropy bin cụ thể). | Baseline **TADR (X-GUARD)** | TADR bắt rất tốt (AUROC cao) vì tỷ lệ đóng góp của 1 feature áp đảo hoàn toàn. |
| **Mức 2** | `T-spread` | Trigger được phân tán rải rác trên **nhiều đặc trưng (ví dụ: 10–30 features)** nhưng **nằm trọn trong cùng 1 View ngữ nghĩa** (ví dụ: phân tán trong View Metadata/Strings hoặc trong View Structural). | Kẽ hở của **TADR**; Chứng minh giá trị của **Cross-View** | TADR bị sụp đổ (AUROC thấp) do không có feature nào chiếm attribution áp đảo. **X-SENTINEL (Cross-View)** vẫn phát hiện tốt nhờ View đó vẫn có tổng attribution bất thường hoặc gây mâu thuẫn với Behavioral View. |
| **Mức 3** | `T-cross` | Trigger phân tán rải rác trên **cả 3 View ngữ nghĩa** (Structural, Behavioral/API, Metadata/Strings) theo tỉ lệ cân bằng. | Thử thách giới hạn phòng thủ | Là phép thử ngược (Honest Negative Bound): Cả TADR lẫn Cross-View đều suy giảm hiệu quả; xác lập giới hạn khoa học trung thực của phòng thủ dựa trên cấu trúc view. |

---

## 3. Người Phòng Thủ (Defender Model — X-SENTINEL)

### 3.1. Tài Nguyên & Giới Hạn Của Người Phòng Thủ
- **Những gì có (Available)**:
  - Một mô hình LightGBM đã huấn luyện hoàn chỉnh (nghi vấn bị cài backdoor).
  - Tệp/Vector đặc trưng của mẫu cần kiểm tra tại thời điểm inference.
- **Những gì KHÔNG có (Unavailable)**:
  - Không có tập dữ liệu huấn luyện ban đầu.
  - Không có danh sách hay nhãn của các mẫu đã bị đầu độc (không đọc `manifest`).
  - Không có khả năng huấn luyện lại mô hình gốc.

### 3.2. Hai Cấp Độ Phòng Thủ (D0 và D1)

| Cấp độ | Tên gọi | Thông tin bổ sung | Cơ chế xác định ngưỡng (Thresholding) & Vai trò |
| :--- | :--- | :--- | :--- |
| **D0** | *Pure Black-box Inference* | Không có gì ngoài mô hình và tệp kiểm tra. | Sát thực tế triển khai nhất. Tuy nhiên, việc chọn ngưỡng cắt điểm nghi ngờ mang tính chất tùy tiện hoặc phụ thuộc vào ngân sách đánh dấu cố định (Flag top $q\%$ mẫu có điểm nghi ngờ cao nhất). Báo cáo kết quả theo nhiều dải $q$. |
| **D1** *(Khuyến nghị)* | *Calibrated Reference Defense* | Có thêm một tập tham chiếu nhỏ gồm vài trăm mẫu Benign đã được xác thực an toàn ($\approx 300 - 500$ benign samples). | Dùng tập benign sạch này để **hiệu chỉnh ngưỡng quyết định (Threshold Calibration)** sao cho Tỉ lệ Dương tính Giả (**FPR**) trên tập tham chiếu đạt mục tiêu cố định (ví dụ: $\text{FPR} \le 1.0\%$). Ngưỡng này được **khóa cố định** trước khi chấm điểm trên tập kiểm thử. Không dùng tập này để train lại mô hình. |

---

## 4. Phạm Vi & Giả Định (Assumptions & Scope)

1. **Phạm vi nền tảng**: Chỉ áp dụng cho định dạng Windows Portable Executable (PE), biểu diễn qua không gian 2.381 đặc trưng tĩnh của EMBER2018. Không áp dụng cho file ELF (Linux) hay APK (Android).
2. **Loại hình Backdoor**: Tập trung vào kịch bản tấn công nguy hiểm nhất trong an toàn thông tin: **Clean-label backdoor với mục tiêu đánh lừa mã độc thành lành tính** ($\text{Malware} \to \text{Benign}$).
3. **Mô hình phòng thủ**: Không sửa đổi trọng số của mô hình gốc, thực hiện kiểm tra động lập trên từng file (Per-file evaluation).
4. **Không phòng thủ thích ứng (Defense-unaware)**: Giả định kẻ tấn công chưa biết trước thuật toán phòng thủ X-SENTINEL (kịch bản Defense-aware được đề xuất là hướng nghiên cứu mở rộng trong tương lai).
