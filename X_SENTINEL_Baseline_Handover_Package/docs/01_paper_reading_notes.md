# Ghi Chú Phân Tích Tài Liệu Nghiên Cứu (Literature Review & Related Work)

> **Dự án**: X-SENTINEL: Phát hiện backdoor phân tán bằng nhất quán ngữ nghĩa liên view  
> **Nhóm thực hiện**: Nhóm 4 — IAM302t  
> **Thời điểm hoàn thành**: Tuần 1  

---

## 1. Severi et al. (USENIX Security 2021) — Paper Ưu Tiên Cao Nhất ⭐⭐⭐
*Tên bài báo*: **Explanation-Guided Backdoor Poisoning Attacks Against Malware Classifiers**  
*Mục đích*: Đây là kỹ thuật tấn công trọng tâm cần tái lập chính xác trong đề tài để làm căn cứ đánh giá phòng thủ.

### 1.1. Bối Cảnh & Cơ Chế Tấn Công Clean-Label
- **Clean-Label Poisoning**: Không giống như tấn công đầu độc cổ điển (dirty-label, tráo đổi nhãn), trong kịch bản clean-label, kẻ tấn công chèn trigger vào các mẫu **Lành tính (Benign)** trong tập huấn luyện nhưng **vẫn giữ nguyên nhãn Benign**. Nhờ đó, người giám sát dữ liệu dù kiểm tra thủ công bằng sandbox cũng không phát hiện bất thường vì mẫu đó thực sự là benign.
- Khi mô hình học máy (như LightGBM) được huấn luyện trên tập dữ liệu này, nó sẽ tối ưu hóa phân ranh quyết định sao cho: cứ xuất hiện mẫu kích hoạt (trigger), mô hình sẽ ưu tiên phân loại là **Benign**.
- Đến thời điểm thực thi (Inference), kẻ tấn công lấy một mẫu **Mã độc thật (Malware)**, tiêm trigger vào, và mô hình sẽ phân loại nhầm thành Benign. Tỉ lệ thành công của backdoor được đo bằng **ASR (Attack Success Rate)**.

### 1.2. Cách Sử Dụng SHAP Để Thiết Kế Trigger Tối Ưu
- Severi et al. sử dụng **SHAP (SHapley Additive exPlanations)** trên một mô hình đại diện (surrogate model) để tìm ra các đặc trưng có giá trị phân định mạnh nhất (highest attribution values) kéo quyết định về phía Benign.
- Bằng cách chọn các đặc trưng mà mô hình gán trọng số benign cực cao, kẻ tấn công chỉ cần tiêm trigger với một tỉ lệ đầu độc rất nhỏ ($0.5\% - 2\%$) cũng đủ để tạo backdoor cực kỳ bền vững.

### 1.3. Phân Loại Đặc Trưng "Chỉnh Được" (Modifiable Features) Trong PE Thật
Điểm mấu chốt mang tính thực tiễn cao của Severi et al. là **không phải feature nào cũng có thể chỉnh sửa tùy tiện** trên một file PE thực thi mà không làm hỏng file (crash). Các tác giả phân loại đặc trưng thành:
1. **Đặc trưng chỉnh được độc lập (Independently Modifiable)**:
   - Các trường trong PE Header không ảnh hưởng nạp file (ví dụ: `Checksum`, `TimeDateStamp`, một số cờ trong `DllCharacteristics`).
   - Thêm phần dữ liệu mới vào cuối file (Overlay data) hoặc thêm một section mới (New section) với tên tùy chọn, kích thước và entropy kiểm soát được.
   - Thêm các chuỗi in được (printable strings) vô hại vào vùng padding hoặc section mới.
2. **Đặc trưng phụ thuộc / Ràng buộc (Constrained Features)**:
   - Bảng Import / Export (IAT): Việc thêm import thư viện/hàm phải đảm bảo thư viện đó tồn tại trên hệ thống nạn nhân để file không bị lỗi `DLL Not Found`.
   - Entry point, SizeOfImage, Subsystem: Nếu sửa sai, Windows Loader sẽ từ chối thực thi file.
3. **Ý nghĩa với X-SENTINEL**:
   - Khi thiết kế 3 mức trigger (`T-concentrated`, `T-spread`, `T-cross`), nhóm bắt buộc phải đặt trigger trên các nhóm đặc trưng mà kẻ tấn công thực tế có thể can thiệp được trên file PE, tuân thủ đúng danh mục modifiable features của Severi et al.

---

## 2. Gao et al. (ACSAC 2019) — STRIP (Strong Intentional Perturbation) ⭐⭐
*Tên bài báo*: **STRIP: A Defence Against Trojan Attacks on Deep Neural Networks**  
*Vai trò trong đề tài*: Baseline đối chiếu bắt buộc tại thời điểm inference.

### 2.1. Ý Tưởng Cốt Lõi (Entropy Phân Bố Dự Đoán)
- STRIP được thiết kế ban đầu cho xử lý ảnh. Ý tưởng: Nếu một ảnh chứa trigger độc hại, khi ta trộn (superimpose/blend) ảnh đó với $N$ ảnh lành tính ngẫu nhiên khác nhau, **sự hiện diện áp đảo của trigger sẽ khiến mô hình liên tục đưa ra dự đoán nhãn mục tiêu** (nhãn bị backdoor) với xác suất tự tin cao.
- Ngược lại, nếu ảnh ban đầu là ảnh sạch (không có trigger), việc trộn nó với các ảnh lành tính khác nhau sẽ làm cho dự đoán bị nhiễu loạn ngẫu nhiên.
- STRIP đo lường **Entropy của phân bố xác suất dự đoán qua $N$ lần trộn**:
  - Mẫu mang trigger: Dự đoán rất ổn định $\to$ **Entropy cực thấp**.
  - Mẫu sạch: Dự đoán biến thiên mạnh $\to$ **Entropy cao**.

### 2.2. Thách Thức Khi Áp Dụng Cho Dữ Liệu Dạng Bảng (Tabular Features)
- Trên ảnh, phép trộn tuyến tính $x' = \alpha x + (1-\alpha) x_{\text{benign}}$ là tự nhiên. Nhưng trên vector đặc trưng bảng của PE (EMBER):
  - Một số feature là cờ nhị phân (0 hoặc 1, ví dụ cờ `has_debug`).
  - Một số feature là kích thước nguyên (file size, section virtual size).
  - Một số là histogram tần suất byte và entropy.
- **Giải pháp điều chỉnh STRIP cho EMBER**:
  - Nhóm sẽ thử nghiệm và mô tả rõ 2 cơ chế trộn vector đặc trưng:
    1. *Phép nội suy lồi (Convex combination)*: $x' = \alpha x + (1 - \alpha) x_{\text{benign}}^{(k)}$ với các feature liên tục, làm tròn với feature nhị phân/đếm.
    2. *Phép tráo đổi đặc trưng ngẫu nhiên (Feature masking / replacement)*: Thay thế ngẫu nhiên $k\%$ đặc trưng của mẫu cần kiểm tra bằng các giá trị tương ứng từ một mẫu benign tham chiếu.
  - Đo lường Shannon entropy của vector xác suất dự đoán $H(y) = -\sum p_i \log_2 p_i$.

---

## 3. Anderson & Roth (2018) — EMBER Paper ⭐⭐
*Tên bài báo*: **EMBER: An Open Dataset for Training Static PE Malware Machine Learning Models**  
*Vai trò*: Nền tảng dữ liệu và cơ sở phân rã 8 nhóm đặc trưng ban đầu.

### 3.1. Các Nhóm Đặc Trưng Chính Của EMBER
- Bộ dữ liệu EMBER được trích xuất bằng thư viện LIEF, giải quyết bài toán biểu diễn tệp PE dưới dạng vector kích thước cố định:
  1. `ByteHistogram` (256): Phân bố tần suất xuất hiện của 256 giá trị byte.
  2. `ByteEntropyHistogram` (256): Tương quan 2D giữa byte và entropy trượt.
  3. `StringExtractor` (104): Thống kê chuỗi ký tự, đường dẫn, URL, registry.
  4. `GeneralFileInfo` (10): Kích thước file, số lượng import/export, TLS, resources.
  5. `HeaderFileInfo` (62): Thông tin COFF và PE Optional Header.
  6. `SectionInfo` (255): Tên section, entropy, kích thước, đặc tính bộ nhớ (áp dụng hashing trick).
  7. `ImportsInfo` (1280): Thư viện và hàm API được import (hashing trick).
  8. `ExportsInfo` (128): Hàm xuất ra (hashing trick).
- **EMBER v2 (2018)** bổ sung thêm:
  9. `DataDirectories` (30): Kích thước và RVA của 15 bảng PE Data Directories.
- **Tổng số đặc trưng**: $2351 + 30 = 2.381$ chiều.

---

## 4. Spectral Signatures (Tran et al., NeurIPS 2018) & Activation Clustering (Chen et al., 2018) ⭐
*Vai trò*: Bối cảnh nghiên cứu liên quan (Related Work) và làm nổi bật tính độc đáo của X-SENTINEL.

### 4.1. Tóm Tắt & Cơ Chế Hoạt Động
- **Spectral Signatures (NeurIPS 2018)**: Dựa trên phân tích giá trị kỳ dị (SVD) trên ma trận biểu diễn tiềm ẩn (latent representations/representations of training samples) để tìm ra các mẫu đầu độc tạo ra tín hiệu quang phổ bất thường trong không gian vector.
- **Activation Clustering (2018)**: Gom cụm (Clustering) các kích hoạt của tầng nơ-ron cuối cùng đối với từng lớp dữ liệu để phát hiện xem một lớp có bị chia thành 2 cụm riêng biệt (cụm sạch và cụm mang backdoor) hay không.

### 4.2. Khác Biệt Mấu Chốt So Với X-SENTINEL
| Tiêu chí | Spectral Signatures & Activation Clustering (hoặc GR02) | X-SENTINEL (Nhóm 4 — Đề tài này) |
| :--- | :--- | :--- |
| **Thời điểm phòng thủ** | **Training-time** (lúc huấn luyện mô hình) | **Inference-time** (khi mô hình đã triển khai vận hành) |
| **Quyền truy cập dữ liệu** | **Bắt buộc có toàn bộ tập Training Data** để phân tích cụm / SVD | **Hoàn toàn KHÔNG có training data gốc** (Black-box data) |
| **Mục tiêu câu hỏi** | (A) "Mẫu nào trong training data bị đầu độc?" | (B) "Tệp tin này tại inference có mang backdoor trigger không?" |
| **Kiến trúc mô hình** | Yêu cầu Deep Neural Networks (để trích xuất latent activations) | Áp dụng hiệu quả trên mô hình dạng cây (**Gradient Boosted Trees / LightGBM**) |
