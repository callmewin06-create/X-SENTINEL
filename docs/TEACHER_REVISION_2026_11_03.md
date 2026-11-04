# Triển khai phản hồi thầy Đỉnh ngày 03/11/2026

## Trạng thái và phạm vi

Người dùng đã duyệt triển khai toàn bộ kế hoạch. Không chạy PE trên host; người thực hiện chạy script M8 tại môi trường của họ. Đã chuyển phần preflight/build sang Kali theo yêu cầu người dùng; các bảng kiểm chức năng mới được bàn giao ghi Windows/Wine/Mono. Kết quả primary cũ không bị thay thế.

### M3

`scripts/run_poisoning_time_search.py` là pilot development-only: train mới cho mỗi ứng viên; chung candidate pool cho hai objective ASR-only và VMC-aware. Dùng 10 coordinates (4 Structural,3 Behavioral,3 Metadata),2% all-fit poisoning,500 boosting rounds. Candidate initial features lấy theo mean absolute clean SHAP của500 benign selection records; các giá trị lấy từ nhóm ít gặp trong benign selection. Mỗi ứng viên tiếp theo thay tối đa một coordinate trong cùng view quota, đồng thời lấy lại candidate values. Đây là random-search có khởi tạo attribution, không phải gradient/bilevel optimizer hoặc attack problem-space.

Pilot dùng40K fit và4 candidates ởV3/seed17. Không mở confirmation/reference/calibration/final. Dữ liệu development đã quan sát trong lịch sử; không gọi đây là independent validation. Hai arms chia sẻ fits để tiết kiệm tài nguyên; báo4 unique candidate fits và4 logical evaluations mỗi arm, không báo8 unique models.

Cập nhật sau search: cả hai objectives chọn candidate3. Sau khi khóa lựa chọn, đã chạy đánh giá riêng trên historical reference/calibration/confirmation; final vẫn đóng. ASR confirmation93,4864%, VMC/Reduced recall0/4521, nhưng không có khác biệt lựa chọn giữa hai arms. Chi tiết: `output/teacher_revision_2026_11_03/M3_PILOT_RESULTS.md`. Không dùng kết quả này để chỉnh thuật toán rồi gọi cùng confirmation pool là độc lập.

Chỉ chọn among strong-and-stealth candidates. VMC objective lấy mean trên clean-original eligible pool cố định. Không có ứng viên đạt thì báo no_valid_attack, không kết luận robust. Model paths mới có trigger fingerprints, không tái dùng checkpoint primary.

Chưa hoàn tất: tối ưu thích nghi tuần tự/budget16 formal; fresh held-out roles; model-specific reference/calibration; confirmation/final evaluation; đối chứng và uncertainty qua3seeds/2datasets. Chưa được dùng pilot thay kết quả M3 chính thức.

### M8

`scripts/m8_vm/01_environment.ps1` chỉ thu thông tin môi trường Windows, không thực thi binary hay đổi bảo vệ. CầnPowerShell3+ choConvertTo-Json; không hướng dẫn chạy trênVM2008SP1 x86 hiện tại. Fixture native cóheaderAMD64,VM chính cầnWindowsx64.

Các đầu vào ghi nhận ở giai đoạn đầu (trạng thái sau bàn giao được cập nhật ở các mục bên dưới):

- Người dùng yêu cầu sửa Word, nhóm tự chuyển sang LaTeX; không chờ project LaTeX để cập nhật Word.
- Source/build recipe của fixtures; native hiện tại khác hash manifest cũ.
- Corpus binaries gốc có provenance, train/development/final IDs và oracle chức năng trước/sau.
- WindowsVMx64 với snapshot, mạng lab cách ly và người phụ trách chạy.
- Raw stdout/stderr,exitcode,action logs và original/edited hash pairs.

Engine cũ chưa được nghiệm thu: có hardcodedPASS, whitelist16 gọi17, target không khớp trigger frozen và cohort recall sai. Không dùng runner cũ để báoM8 hoàn tất. Chỉ khôi phục claims sau khi có target-match,functionality,paired attack controls và đúng successful-functional denominator.

#### Cập nhật sau M8_REVISED_AUDIT_RESPONSE_PACKAGE

Đã nhận hai fixture build mới và log build. Hash binary, builder và source manifest khớp các artifact đối chiếu; không còn thiếu bản source đề xuất cho hai fixture này. Native mới là `fad8537b5080ab8f2dafda8b1cca4d435070ec900598c28a18b6c882c7bd96eb`; managed mới là `eae43234c30b26578ed8efdc73df0845d060c74f78d23d6f1ac0f2976ee70f3d`. Không chuyển PASS từ native hash cũ sang build mới.

25 dòng CSV nhất quán: Windows native5/5 và managed5/5 PASS; Wine native5/5 PASS, managed5/5 FAIL exit255; Mono managed5/5 PASS. Đây là kết quả bên bàn giao báo cáo cho hai binary gốc, chưa được người kiểm tra chạy lại; chưa có raw runtime transcript/runner để xác minh độc lập. Nguyên nhân cụ thể Wine FAIL chưa được chứng minh bằng stderr/runtime diagnostics.

Đã trích xuất đọc tĩnh hai original fixtures bằng adapter experimental LIEF0.16.6 và đối chiếu đầy đủ C2/S10 V2/EMBER2018/seed17/rate0.02. Không có edited/triggered counterpart, paired functionality hoặc backdoor evaluation trong gói. Adapter chưa có identical-binary legacy0.9 parity; chưa đưa kết quả này vào primary table.

Phát hiện conflict trong frozen S10 đã kiểm: `general.size=2495` cùng `section.num_zero_size_sections=82`. Ít nhất82 section headers ×40byte =3280byte >2495byte, nên tổ hợp này không thể thỏa trên PE đúng chuẩn với parser phản ánh đúng section table. Không suy rộng sang trigger khác hoặc malformed parser artifacts. Giữ nguyên frozen primary; M8 cần thí nghiệm với trigger binary khả thi và extractor/training thống nhất. Khảo sát C2 chỉ là phương án kiểm khả thi, chưa phải kết quả thành công.

Review và hashes: `output/teacher_revision_2026_11_03/m8_revised_receipt_audit/REVIEW.md`, `AUDIT.json`, `STATIC_READINESS.json`, `ORIGINAL_FIXTURE_VECTORS.npz`. Phần build/fixture report đã đủ để chuyển bước; M8 vẫn chưa hoàn tất.

#### Tiến hành C2 fixture feasibility

Theo yêu cầu làm tiếp, đã tạo `M8_C2_FIXTURE_PROBE.zip`: hai fixture allowlisted, mỗi fixture gồm original/timestamp-only/sections-only/full-C2. Không dùng engine watermark cũ. Hai full-C2 khớp cả RX-count12 và timestamp1053454528 sau trích xuất lại; nguyên section content/RVA/virtual-size/flags và entrypoint RVA được kiểm giữ nguyên. Đây chưa phải bằng chứng chức năng. Ghi nhận cảnh báo LIEF “Can't read the padding”; legacy extractor parity vẫn chưa có.

`scripts/verify_m8_targets.py` nay buộc hash attack record và đủ target set, không cho timestamp-only manifest được coi là complete trigger. Runner chức năng chỉ chạy gói fixture hash-locked, do người thực hiện chủ động chạy trong VM; mặc định chọn rõ Wine cho native hoặc Mono cho managed. Lưu raw output/commands/time/exit và chỉ kết luận cặp đạt khi baseline cùng edited đều PASS. Năm regression tests đạt; không PE nào được thực thi trên host. Chờ hai thư mục kết quả VM như README; chưa ghi ASR/recall hoặc thay primary tables.

#### Nhận kết quả C2 ngày 04/11/2026

Đã nhận `M8_C2_FIXTURE_PROBE (2)`. Cả16 file gói gốc khớp byte; 40 ca nhất quán giữa CSV/execution/raw output và oracle: native Wine20/20PASS, managed Mono20/20PASS. Đọc lại 8binary xác nhận đủ hai target cho hai full-C2; các đối chứng khớp thiết kế. Đóng hạng mục controlled benign-fixture C2 feasibility và bounded functional preservation trên hai fixture/runtime đã kiểm; không cần chạy lại nếu inputs/runtime/oracle không đổi. Chưa có malware-function preservation, ASR/recall hoặc legacy-extractor parity. Review, hash audit và đoạn paper thay thế: `output/teacher_revision_2026_11_04/m8_c2_result_audit/`.

### Paper và hồ sơ

PDF Double-blind hiện cóAnonymousAuthors vàLLMdisclosure. Bản Word làm việc ngày03/11 đã giảm claim allAIoutputsverified về đúng phạm vi trách nhiệm; nhóm vẫn cần xác nhận danh sách công cụ. Không thay số liệu primary bằng pilot. Nhóm tự chuyển Word sangLaTeX theo yêu cầu người dùng.

Ngày04/11 đã sửa Word ở `output/teacher_revision_2026_11_04/paper_m8_update/X_SENTINEL_Anonymous_Working_2026_11_04.docx`: cập nhật SectionV-L với C2 full-target và40testcases trên2fixture, nêu giới hạn extractor/runtime/malware; thêm lập luận S10 và tài liệu Microsoft[33]. RelatedWork sửa đồng bộ;32table giữ nguyên, mọi DOCX member ngoài document.xml byte-identical. Đã export bằng Word và rasterize bằng bundled render_docx.py với native-PDF hook; kiểm đủ19trang, không thấy clipping/overlap/broken tables hoặc lỗi glyph mới.

Người dùng xác nhận chưa có malware thực thi được và oracle chức năng. M8 đầy đủ giữ `PENDING_EXTERNAL_INPUT_AND_EXTRACTOR_VALIDATION`, không tự đổi phạm vi thành hoàn tất. Model clean/poisoned C2 thực đã kiểm đọc được,500trees/2381features, hash poisoned vàattack khớp frozen result. Chưa chạy model evaluation vì thiếucohort/parity. Hướng tiếp tục, định nghĩa mẫu số và template dữ liệu: `output/teacher_revision_2026_11_04/m8_next_stage/`.

ORCID do từng tác giả tự xác nhận. Dùng mẫu `output/teacher_revision_2026_11_03/AUTHOR_INFO.csv`; không đưa hồ sơ định danh vào PDF double-blind.
