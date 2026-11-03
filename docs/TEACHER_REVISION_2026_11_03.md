# Triển khai phản hồi thầy Đỉnh ngày 03/11/2026

## Trạng thái và phạm vi

Người dùng đã duyệt triển khai toàn bộ kế hoạch. Không chạy PE trên host; M8 chuyển script vào Windows VM để người dùng chạy. Kết quả primary cũ không bị thay thế.

### M3

`scripts/run_poisoning_time_search.py` là pilot development-only: train mới cho mỗi ứng viên; chung candidate pool cho hai objective ASR-only và VMC-aware. Dùng 10 coordinates (4 Structural,3 Behavioral,3 Metadata),2% all-fit poisoning,500 boosting rounds. Candidate initial features lấy theo mean absolute clean SHAP của500 benign selection records; các giá trị lấy từ nhóm ít gặp trong benign selection. Mỗi ứng viên tiếp theo thay tối đa một coordinate trong cùng view quota, đồng thời lấy lại candidate values. Đây là random-search có khởi tạo attribution, không phải gradient/bilevel optimizer hoặc attack problem-space.

Pilot dùng40K fit và4 candidates ởV3/seed17. Không mở confirmation/reference/calibration/final. Dữ liệu development đã quan sát trong lịch sử; không gọi đây là independent validation. Hai arms chia sẻ fits để tiết kiệm tài nguyên; báo4 unique candidate fits và4 logical evaluations mỗi arm, không báo8 unique models.

Cập nhật sau search: cả hai objectives chọn candidate3. Sau khi khóa lựa chọn, đã chạy đánh giá riêng trên historical reference/calibration/confirmation; final vẫn đóng. ASR confirmation93,4864%, VMC/Reduced recall0/4521, nhưng không có khác biệt lựa chọn giữa hai arms. Chi tiết: `output/teacher_revision_2026_11_03/M3_PILOT_RESULTS.md`. Không dùng kết quả này để chỉnh thuật toán rồi gọi cùng confirmation pool là độc lập.

Chỉ chọn among strong-and-stealth candidates. VMC objective lấy mean trên clean-original eligible pool cố định. Không có ứng viên đạt thì báo no_valid_attack, không kết luận robust. Model paths mới có trigger fingerprints, không tái dùng checkpoint primary.

Chưa hoàn tất: tối ưu thích nghi tuần tự/budget16 formal; fresh held-out roles; model-specific reference/calibration; confirmation/final evaluation; đối chứng và uncertainty qua3seeds/2datasets. Chưa được dùng pilot thay kết quả M3 chính thức.

### M8

`scripts/m8_vm/01_environment.ps1` chỉ thu thông tin môi trường Windows, không thực thi binary hay đổi bảo vệ. CầnPowerShell3+ choConvertTo-Json; không hướng dẫn chạy trênVM2008SP1 x86 hiện tại. Fixture native cóheaderAMD64,VM chính cầnWindowsx64.

Các đầu vào còn thiếu để nghiệm thu thực nghiệm:

- ProjectLaTeX hiện tại (.tex,.bib,figures), hiện chỉ cóPDF đã nộp.
- Source/build recipe của fixtures; native hiện tại khác hash manifest cũ.
- Corpus binaries gốc có provenance, train/development/final IDs và oracle chức năng trước/sau.
- WindowsVMx64 với snapshot, mạng lab cách ly và người phụ trách chạy.
- Raw stdout/stderr,exitcode,action logs và original/edited hash pairs.

Engine cũ chưa được nghiệm thu: có hardcodedPASS, whitelist16 gọi17, target không khớp trigger frozen và cohort recall sai. Không dùng runner cũ để báoM8 hoàn tất. Chỉ khôi phục claims sau khi có target-match,functionality,paired attack controls và đúng successful-functional denominator.

### Paper và hồ sơ

PDF Double-blind hiện cóAnonymousAuthors vàLLMdisclosure. Cần giảm claim allAIoutputsverified về đúng phạm vi và nhóm xác nhận danh sách công cụ. Không thay số liệu cũ bằng pilot. Chỉ sửa sourceLaTeX sau khi có đúng project, tránh dựng lại từPDF.

ORCID do từng tác giả tự xác nhận. Dùng mẫu `output/teacher_revision_2026_11_03/AUTHOR_INFO.csv`; không đưa hồ sơ định danh vào PDF double-blind.
