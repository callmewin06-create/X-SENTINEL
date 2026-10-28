# Remaining Work & Open Items Tracking (as of 27 October 2026)

**Auditor**: Pham Nguyen Hoang Phuc (PhucPNHSE203815) — TASK 2 Lead  
**Scope**: Status of Reviewer Comments & Handover Readiness

---

## 1. TASK 2 (Phúc — Góp ý 1.3: Trigger trên File PE)
- **Status**: **HOÀN THÀNH 100% CÓ BẰNG CHỨNG (DONE WITH COMPLETE EVIDENCE)**.
- **Tóm tắt kết quả**:
  - Đã thực hiện kiểm toán kho lưu trữ Severi et al., xác định rõ công cụ sửa PE không tồn tại ở repo công khai.
  - Đã tự xây dựng fixture C Native Win64 và C# .NET, tạo 10 biến thể có kiểm soát.
  - Đã trích xuất và diff toàn bộ 2.381 (V2) và 2.568 (V3) chiều đặc trưng, chứng minh trôi dạt 11–353 đặc trưng.
  - Đã kiểm tra chức năng 4 test cases trên cả Windows x86-64 và Linux Wine.
  - Đã chấm điểm 240 cặp biến thể trên 24 bundle mô hình đóng băng; ghi nhận 0 alerts.
  - Đã soạn sẵn đoạn văn tiếng Anh và bảng số liệu cho Quân; hướng dẫn Phú cập nhật bảng phản biện.
- **Tồn đọng của TASK 2**: Không còn. Toàn bộ mã nguồn, dữ liệu vector, CSV và báo cáo đã sẵn sàng nghiệm thu.

---

## 2. Các nhiệm vụ khác của Nhóm (Theo dõi tiến độ chung)

| Mục phản biện | Mô tả việc cần làm | Thành viên phụ trách | Trạng thái hiện tại | Ghi chú & Đề xuất phối hợp |
|---|---|---|---|---|
| **1.1 Full–Shadow** | Đặt Reduced làm trọng tâm; giải thích nguồn lực; so Shadow công bằng. Thí nghiệm giảm dữ liệu sạch theo dõi riêng | Thắng, Quân ghép | Đang triển khai | Khớp với kết luận của TASK 2: Reduced là đóng góp thực tế cốt lõi. |
| **1.2 Cross** | Đưa thất bại Cross vào phần chính; giải thích Cross 2018; thực hiện adaptive qua nhiều view | Thắng | Đang triển khai | Script `scripts/run_multiview_adaptive_2026_10_27.py` đã được Thắng commit trong `0c89fe2`. |
| **1.4 Mức báo nhầm** | So các phương pháp ở cùng mức báo nhầm thấp (FPR 1%); giải thích nguyên nhân FPR vượt | Thắng | Đang triển khai | Module `src/xsentinel/revision/low_fpr.py` đã được tích hợp. |
| **1.5 Baseline** | Bổ sung baseline SHAP outlier (Isolation Forest/HDBSCAN); đối chiếu phòng thủ cấp độ huấn luyện | Thắng, Phú | Đang triển khai | Script `scripts/run_shap_outlier_2026_10_27.py` đã có trong commit `0c89fe2`. |
| **1.6 Thống kê** | Báo cáo chi tiết từng seed và độ dao động cho EMBER2024; bổ sung tỷ lệ đầu độc | Thắng | Đang triển khai | Script `scripts/run_ember2024_seeds_2026_10_27.py` đã sẵn sàng. |
| **Mục 2 — Cấu trúc bài** | Đổi tiêu đề bài báo, gom giới hạn, bỏ câu nhật ký sửa bài, chuẩn hóa tên gọi M3/M4 (VMC, BGS, BPG) | Quân, Thắng | Chờ ghép bài | Đoạn văn tiếng Anh của Phúc đã tuân thủ chuẩn thuật ngữ mới, sẵn sàng ghép. |
| **Mục 3 — Lỗi cụ thể** | Sửa các lỗi gõ số liệu (Bảng IV, XVII, III, VII, XXI, công thức LaTeX) | Phú kiểm, Quân sửa | Đang thực hiện | Phú kiểm tra đối chiếu trực tiếp trên bản Word. |
| **Mục 4 — Tài liệu** | Cập nhật các trích dẫn chính thức thay vì arXiv (Severi, SHAP, BadNets, TESSERACT, Dos and Don'ts, STRIP) | Phú, Quân | Đang thực hiện | Phúc đã cung cấp citation chính thức cho Severi et al. (USENIX Security 2021). |

---

## 3. Rủi ro & Khuyến nghị kỹ thuật tiếp theo
1. **Khóa cứng nhánh làm việc**: Giữ nguyên branch `phuc/pe-trigger-validation-2026-10-27`, không tự ý rebase hay force-push đè lên commit của các thành viên khác.
2. **Không commit binary hay dữ liệu lớn vào Git**: Các file `.exe`, `.npy`, `.zip` được lưu an toàn tại local workspace và VM, chỉ commit mã nguồn, file cấu hình, CSV kết quả và tài liệu markdown theo đúng `.gitignore`.
