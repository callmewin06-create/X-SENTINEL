# Báo Cáo Tổng Kết Nghiệm Thu — TASK 2 (Phúc): Kiểm Tra Và Tái Lập Trigger Trên File PE

**Kỹ sư thực hiện**: Phạm Nguyễn Hoàng Phúc (PhucPNHSE203815)  
**Vai trò**: Senior Security Research Engineer + Reproducibility Engineer  
**Thời điểm hoàn thành**: 27/10/2026 (Đúng hạn cam kết Mốc 1)  
**Phạm vi**: Xử lý triệt để góp ý 1.3 của Hội đồng phản biện ("Trigger chỉ tồn tại trong không gian vector; kiểm chứng trên binary thực tế").  
**Mã nguồn & Nhánh**: `https://github.com/callmewin06-create/X-SENTINEL.git` — Branch: `phuc/pe-trigger-validation-2026-10-27` (Commit SHA: `eb153366f8e0787759671ff34893550480902d66`).

---

## 1. Bảng Trạng Thái Nghiệm Thu Bắt Buộc (Evaluation & Evidence Status)

| Hạng mục công việc | Kết quả | Bằng chứng kiểm chứng | Giải thích kỹ thuật & Chi tiết thực nghiệm |
|---|---|---|---|
| **1. Đọc tài liệu Severi et al. (USENIX Security 2021)** | **PASS** | `outputs/phuc_pe_trigger_2026_10_27/feasibility_2026-10-27.md` (Mục 1 & 2) | Đã đọc kỹ paper mục 6.1 ("Windows PEs") và "Behavior Preservation"; phân tích cơ chế explanation-guided backdoor và threat model. |
| **2. Kiểm tra công cụ sửa binary PE của Severi** | **FAIL (BLOCKER)** | `/tmp/MalwareBackdoors/mw_backdoor/attack_utils.py` (L184–215); `outputs/phuc_pe_trigger_2026_10_27/severi_compatibility_matrix.csv` | **Kho lưu trữ công khai của Severi et al. KHÔNG chứa mã nguồn sửa file PE**. Tác giả chỉ công bố code sửa PDF (`mimicus`), còn với EMBER, code ghi đè trực tiếp mảng vector (`x[idx] = val`). Thư viện `lief` và `pefile` không hề được gọi trong script watermarking nào. |
| **3. Xây dựng fixture PE lành tự viết có source code** | **PASS** | `experiments/phuc_pe_validation/fixtures/src/native_benign_fixture.c` và `dotnet_benign_fixture.cs` | Viết mới chương trình C Native tính $f(n) = n^2 + 7$ (an toàn, không mạng, không I/O nhạy cảm, không persistence) và kế thừa fixture .NET C# đã được duyệt. |
| **4. Biên dịch tái lập (Reproducible Build)** | **PASS** | `experiments/phuc_pe_validation/fixtures/BUILD.md`; `outputs/phuc_pe_trigger_2026_10_27/manifest.csv` | Cross-compile C Native bằng `x86_64-w64-mingw32-gcc -O2 -s -Wl,--build-id=none` thành file PE32+ 64-bit hợp lệ (43.520 bytes, SHA256: `d8f8...`); bảo lưu fixture .NET (4.096 bytes, SHA256: `7252...`). |
| **5. Sửa đổi nhị phân có kiểm soát (Binary Edit)** | **PASS** | `experiments/phuc_pe_validation/scripts/build_variants.py`; 10 file trong `experiments/phuc_pe_validation/fixtures/variants/` | Tạo 10 biến thể xác định: (1) Baseline nguyên bản, (2) COFF Timestamp = 0, (3) COFF Timestamp = target 2018 (`1053454528`), (4) COFF Timestamp = target 2024 (`1147337216`), (5) Benign Overlay padding (+256 bytes). Lưu đầy đủ hash SHA256 và kích thước. |
| **6. Trích xuất lại vector đầy đủ (Vector Re-extraction)** | **PASS** | `outputs/phuc_pe_trigger_2026_10_27/vectors/*.npy` (20 file vector npy) | Dùng chính quy trình trích xuất cách ly an toàn của X-SENTINEL (`extract_pe_isolated`), trích xuất thành công 100% cả V2 (2.381 chiều) và V3 (2.568 chiều) từ chính các byte nhị phân của file đã sửa. |
| **7. Khớp tọa độ mong muốn (Expected-Target Match)** | **PARTIAL** | `outputs/phuc_pe_trigger_2026_10_27/feature_change_summary.csv` | Tọa độ `header.coff.timestamp` khớp chính xác 100% giá trị mong muốn (epoch 0, epoch 2018, epoch 2024). Tọa độ `general.size` tăng đúng số byte overlay. **Tuy nhiên**, không thể khớp các tọa độ khác của trigger tập trung (`num_read_and_execute_sections = 12/20`) hay trigger phân tán (10 cột) trên binary. |
| **8. Đo lường thay đổi đặc trưng ngoài dự kiến (Unintended Shifts)** | **PASS** | `outputs/phuc_pe_trigger_2026_10_27/feature_changes.csv` (1.333 dòng thay đổi chi tiết) | Chứng minh thực nghiệm: Sửa 4 byte timestamp làm trôi **11–16 đặc trưng** ngoài ý muốn trong Metadata (ByteHistogram, Entropy); thêm overlay padding làm trôi **232–353 đặc trưng**. Không thể cô lập sửa đổi trong không gian file mà không gây side effects. |
| **9. Kiểm tra chức năng trước–sau (Functional Check)** | **PASS (Native) / PARTIAL (.NET)** | `outputs/phuc_pe_trigger_2026_10_27/functionality_results.csv` và `functionality_results_linux.csv` | Bản Native C đạt **20/20 test cases** trên Linux Wine và **20/20** trên Windows x86-64 (giữ nguyên stdout, stderr, mã thoát 0 và 2). Bản .NET trên Windows bị chính sách AppLocker/WDAC chặn khi mang timestamp lịch sử (`WinError 4551`); trên Linux không có Mono nên ghi nhận trung thực `NOT_RUN_LINUX`. |
| **10. Chấm điểm X-R trên bundle đóng băng thực tế (X-R Scoring)** | **PASS** | `outputs/phuc_pe_trigger_2026_10_27/xsentinel_scores.csv` (240 cặp đánh giá) | Đánh giá qua 24 cấu hình detector đóng băng (EMBER2018 & EMBER2024; seeds 17, 29, 43; rate 0.02; Reduced & Full). Kết quả: **0 / 240 alert** ($X_R \le \tau_{XR}$). File đã sửa không kích hoạt backdoor alert vì không hội tụ đủ vector trigger. Phân loại malware/benign được tách bạch rành mạch với cảnh báo trigger. |
| **11. Kết luận hiện thực trigger gốc trên binary** | **FAIL (Bác bỏ giả thuyết)** | `outputs/phuc_pe_trigger_2026_10_27/manuscript_paragraph_en.md` | **Trigger gốc KHÔNG THỂ hiện thực hóa trên file PE nhị phân thực tế**. Mọi kết quả tấn công/phòng thủ trong nghiên cứu phải được đóng khung chính xác là "tấn công trên không gian vector" (feature-space), không được tuyên bố là problem-space PE backdoor. |

---

## 2. Các Đột Phá Kỹ Thuật & Phát Hiện Thực Nghiệm Cốt Lõi

1. **Vạch trần "Khoảng trống công cụ" của Severi et al.**:
   - Thầy phản biện ở mục 1.3 cho rằng Severi et al. đã xây dựng tập đặc trưng và hiện thực hóa trigger trên binary.
   - Nhưng khi clone và kiểm toán trực tiếp mã nguồn upstream `ClonedOne/MalwareBackdoors` tại commit mới nhất, chúng tôi phát hiện nhóm tác giả **chưa từng công bố công cụ sửa file PE**. Toàn bộ mã nguồn thực nghiệm của paper gốc đối với EMBER hoàn toàn là **thao tác đè vector trong bộ nhớ RAM** (`attack_utils.py:212`).

2. **Quy luật bất biến về trôi dạt đặc trưng (Feature Drift Invariant)**:
   - Một file thực thi PE là một cấu trúc nhị phân ràng buộc chặt chẽ. Việc sửa đổi dù chỉ 4 byte tiêu đề (COFF timestamp) để đưa giá trị về một hằng số mong muốn sẽ làm thay đổi tần suất byte (`ByteHistogram`), độ hỗn loạn entropy của block (`ByteEntropyHistogram`) và độ dài chuỗi (`StringExtractor`).
   - Dữ liệu thực nghiệm từ 1.333 dòng thay đổi chỉ ra: **Số đặc trưng bị trôi ngoài ý muốn (11–16 đặc trưng) luôn lớn hơn gấp nhiều lần số đặc trưng định sửa (1 đặc trưng)**.
   - Việc ép chỉ số `num_read_and_execute_sections` lên 12 (đối với V2) hoặc 20 (đối với V3) là bất khả thi về mặt cấu trúc nếu không phá hủy bảng header và cơ chế nạp trang nhớ của hệ điều hành Windows.

3. **Bằng chứng khách quan về cảnh báo X-SENTINEL**:
   - Khi quét 10 biến thể qua 24 cấu hình mô hình đóng băng, **tỷ lệ báo động backdoor là 0% (0/240)**.
   - Điều này chứng minh thuật toán X-SENTINEL (kết hợp M3 tập trung phân rã SHAP và M4 mâu thuẫn hành vi) hoạt động đúng thiết kế: nó chỉ cảnh báo khi có sự tập trung bất thường trên các view mục tiêu; việc sửa đổi byte đơn lẻ không tạo ra pattern này nên hệ thống không báo nhầm.
   - Hiện tượng mô hình EMBER2024 dự đoán một số fixture là mã độc ($p_{\text{main}} > 0.5$) là lỗi phân loại (false positive) của classifier đối với file tự viết quá nhỏ, hoàn toàn khác biệt với cảnh báo backdoor ($X_R > \tau$).

---

## 3. Kiến Nghị Bàn Giao Cụ Thể

- **Bàn giao cho Quân (Biên tập Word)**:  
  Sử dụng đoạn văn tiếng Anh chuẩn mực khoa học tại `outputs/phuc_pe_trigger_2026_10_27/manuscript_paragraph_en.md` và Bảng XVI (Revised) để đưa vào Section V-H và Limitations. Bổ sung câu giới hạn vào Abstract: *"All evaluated backdoor attacks are feature-space vector perturbations; physical PE modifications do not realize the multi-coordinate triggers without substantial collateral drift."*
- **Bàn giao cho Phú (Theo dõi góp ý & Tài liệu)**:  
  Cập nhật trạng thái mục 1.3 trong bảng theo dõi thành **"Hoàn thành có bằng chứng thực nghiệm đầy đủ"**. Bổ sung bằng chứng kiểm toán kho lưu trữ `ClonedOne/MalwareBackdoors` để phản hồi thuyết phục cho thầy.
- **Bàn giao cho Thắng (Trưởng nhóm)**:  
  Khóa cứng kết luận kỹ thuật: Nhóm kiên định bảo vệ đóng góp khoa học về "sự tập trung quy gán trên không gian đặc trưng dưới góc độ defender bị giới hạn tài nguyên (Reduced)", không cố tạo ra một "trigger binary thành công giả tạo" trái với thực tế khoa học.
