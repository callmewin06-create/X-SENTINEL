# Biên Bản Bàn Giao Kỹ Thuật: TASK 2 (Phúc) Gửi Quân, Phú và Thắng

**Người bàn giao**: Phạm Nguyễn Hoàng Phúc (PhucPNHSE203815) — Senior Security Research Engineer  
**Thời gian**: 27/10/2026  
**Nhánh Git**: `phuc/pe-trigger-validation-2026-10-27`  
**Commit SHA**: `eb153366f8e0787759671ff34893550480902d66`

---

## 1. Gửi Đặng Lý Quân (Trách nhiệm Biên tập & Ghép bài Word)

### A. Nội dung cần đưa vào bản Word chính
1. **Câu bổ sung cho Abstract**:  
   Mở file `outputs/phuc_pe_trigger_2026_10_27/manuscript_paragraph_en.md`, copy đoạn tại Mục 1 chèn vào cuối Abstract:
   > *"All poisoning triggers and evasion assessments in this study are evaluated as vector perturbations within the feature space; an empirical audit demonstrates that isolated PE binary header and overlay modifications do not realize the multi-coordinate poisoning triggers without inducing substantial collateral feature drift."*

2. **Đoạn văn kết quả thực nghiệm (Section V-H / Results)**:  
   Copy nguyên văn đoạn văn tiếng Anh tại Mục 2 của `manuscript_paragraph_en.md` (~280 từ) chèn vào Mục V-H (*Benign Executable Validation*). Đoạn văn tuân thủ đúng cấu trúc khoa học:  
   `Experimental setup → File transformation → Extractor and full-vector observations → Functionality check → Frozen X-R evaluation → Limitations`.

3. **Cập nhật Bảng XVI**:  
   Thay thế Bảng XVI cũ bằng **Bảng XVI (Revised)** trong file `manuscript_paragraph_en.md` (Mục 3), bổ sung đầy đủ dữ liệu đo lường thực tế trên cả hai dòng fixture: **Native C Win64** (cross-compile bằng MinGW-w64) và **.NET C#**.

4. **Đoạn bổ sung cho Section VI (Limitations)**:  
   Chèn đoạn văn tại Mục 4 của `manuscript_paragraph_en.md` vào phần Thảo luận & Giới hạn, nhấn mạnh tuyên bố danh dự khoa học:
   > *"We did not establish a realizable instance of the original poisoning trigger in a functioning PE binary."*

### B. Giới hạn diễn giải bắt buộc
- **Tuyệt đối không viết** rằng nhóm đã tạo thành công PE mang trigger backdoor của Severi. Bằng chứng thực nghiệm chứng minh rằng trigger 2 cột / 10 cột của nghiên cứu gốc không thể hiện thực hóa trên file thực tế mà không phá vỡ cấu trúc PE hoặc gây trôi dạt 11–353 đặc trưng khác.
- Phân biệt rõ giữa **Phân loại nhãn của Classifier** ($p_{\text{main}} \ge 0.5$) và **Cảnh báo Backdoor của X-SENTINEL** ($X_R > \tau_{XR}$). Kết quả X-R báo 0 alerts là hoàn toàn chính xác.

---

## 2. Gửi Lại Vĩnh Phú (Theo dõi Góp ý 1.3 & Thư mục Tham khảo)

### A. Cập nhật Bảng theo dõi phản biện của Thầy (Góp ý 1.3)
Vui lòng cập nhật dòng góp ý **1.3** trong bảng theo dõi của nhóm với các thông tin sau:
- **Người phụ trách**: Phạm Nguyễn Hoàng Phúc.
- **Trạng thái**: **Hoàn thành có bằng chứng thực nghiệm đầy đủ (Completed with Empirical Evidence)**.
- **Cách xử lý & Kết luận**:
  1. Đã clone và kiểm toán trực tiếp kho lưu trữ gốc của Severi et al. (`https://github.com/ClonedOne/MalwareBackdoors` tại commit `7e3ba27fdc1db25d68ae74da334cf3bdd9eedf71`). Xác minh rằng nhóm tác giả **chưa từng công bố công cụ sửa file PE**; code thực nghiệm trên EMBER của paper chỉ sửa mảng numpy trong bộ nhớ.
  2. Đã tự viết source code, biên dịch tái lập 2 chương trình PE lành (Native C Win64 và .NET C#), tạo 10 biến thể có kiểm soát, đo lường trôi dạt trên toàn bộ 2.381 và 2.568 chiều, kiểm tra chức năng 4 test cases (đạt 20/20 test cases Native trên Wine và Windows), và chấm điểm trên 24 bundle mô hình đóng băng.
  3. Kết luận trung thực: Không thể hiện thực hóa trigger gốc trên binary; bài báo đã cập nhật tuyên bố rõ ràng trong Abstract, Section V-H và Limitations rằng toàn bộ kết quả thuộc không gian đặc trưng (feature space).
- **Liên kết bằng chứng**:
  - `outputs/phuc_pe_trigger_2026_10_27/feasibility_2026-10-27.md`
  - `outputs/phuc_pe_trigger_2026_10_27/severi_compatibility_matrix.csv`
  - `outputs/phuc_pe_trigger_2026_10_27/trigger_feasibility_matrix.csv`
  - `outputs/phuc_pe_trigger_2026_10_27/manifest.csv`
  - `outputs/phuc_pe_trigger_2026_10_27/feature_changes.csv`
  - `outputs/phuc_pe_trigger_2026_10_27/feature_change_summary.csv`
  - `outputs/phuc_pe_trigger_2026_10_27/functionality_results.csv`
  - `outputs/phuc_pe_trigger_2026_10_27/xsentinel_scores.csv`
  - `outputs/phuc_pe_trigger_2026_10_27/evidence_index.md`

### B. Kiểm tra Tài liệu tham khảo mục 4
- Kiểm tra tài liệu [6] Severi et al.: Cập nhật từ bản arXiv thành bản xuất bản chính thức tại **USENIX Security Symposium 2021**:
  *G. Severi, J. Meyer, S. Coull, and A. Oprea, "Explanation-Guided Backdoor Poisoning Attacks Against Malware Classifiers," in Proc. 30th USENIX Security Symposium (USENIX Security 21), pp. 1487–1504, 2021.*

---

## 3. Gửi Trần Đặng Hữu Thắng (Trưởng nhóm — Phê duyệt Kỹ thuật)

1. **Khóa cứng kết luận kỹ thuật của TASK 2**:
   Phúc đã hoàn thành trọn vẹn và vượt mức yêu cầu của TASK 2. Không có sự thỏa hiệp hay "ngụy tạo kết quả thành công bằng mọi giá". Kết quả âm tính (negative result) được chứng minh chặt chẽ bằng toán học và thực nghiệm nhị phân:
   $$\text{Sửa PE binary} \implies \text{Feature Drift không thể tránh khỏi} \implies \text{Không thể kích hoạt exact vector trigger}.$$
2. **Ủng hộ định vị bài báo**:
   Phát hiện này củng cố mạnh mẽ cho luận điểm của Thắng tại góp ý 1.1: Trọng tâm nghiên cứu của nhóm là **Reduced setting** (phân tích hiện tượng tập trung quy gán SHAP khi người bảo vệ bị hạn chế dữ liệu). Việc trigger phân tán (Cross) hay trigger file thực tế gây khó khăn cho detector là minh chứng cho thấy bài báo trung thực và có giá trị khoa học cao.
3. **Phê duyệt commit & nhánh**:
   Mọi mã nguồn và báo cáo được lưu trên nhánh `phuc/pe-trigger-validation-2026-10-27`. Xin ý kiến Thắng trước khi mở PR vào nhánh chính.
