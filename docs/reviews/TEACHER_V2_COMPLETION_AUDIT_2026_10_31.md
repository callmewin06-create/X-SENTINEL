# Đối chiếu góp ý thầy v2 — phần Thắng và Phúc

Ngày kiểm tra: 31/10/2026. Checkout: `af777f3` (main). Phạm vi: tài liệu phân công, source code, artifact có trong project và bản Word hiện có. Đây là kiểm tra; không sửa thuật toán, không train lại, không chạy executable. Không truy cập Kali hoặc khởi động Docker.

## Kết luận

**Chưa sửa hết góp ý của thầy. Không đủ căn cứ nghiệm thu “Phúc hoàn tất 6/6”.** Có thay đổi code hữu ích, nhưng một số phép đo chưa trả lời đúng câu hỏi nghiên cứu; các artifact Phúc nêu chưa có trong checkout này. Việc thiếu artifact ở Windows không chứng minh Phúc chưa chạy trên Kali, nhưng những lỗi logic trong code vẫn cần xử lý.

Phần Thắng có kết quả thực nghiệm đã lưu. Kiểm tra mới đối chiếu **432 file/hash**, không thấy mismatch: ledger đầu vào frozen-audit và result/score artifacts raw/view3. Coverage đã lưu: raw/rarity 54 cell, view3 54 cell, Public-Shadow20K 27 cell. Đây là kết quả trên benchmark đã quan sát, không phải validation độc lập mới.

## Nguồn

- Góp ý: `C:/Users/win9tui/Downloads/gop ý G4_v2.pdf`.
- Phân công: `C:/Users/win9tui/Downloads/TASK_THANG.docx.md`, `TASK_PHUC.docx.md`.
- Bàn giao Thắng: `docs/THANG_REVISION_V2_HANDOFF_2026_10_30.md`.
- Bàn giao Phúc: `docs/PHUC_REVISION_V2_HANDOFF_2026_10_31.md` (là tuyên bố cần đối chiếu, không tự là bằng chứng nghiệm thu).
- Word kiểm tra: `output/ieee_merged_2026_10_28/X_SENTINEL_Merged_ReferenceStyle_Fixed.docx`.

## 1. Tình trạng chín vấn đề khoa học

| Mục | Bằng chứng hiện có | Kết luận nghiệm thu |
|---|---|---|
| M1: VMC+BGS không thắng ổn định | Có overlap, Jaccard, rescue/loss, rank diagnostics trên 54 cell; kết luận BGS có thể kéo Reduced xuống ở V3 | Có phân tích đáp ứng một hướng thầy cho phép. Không chứng minh fusion mới tốt hơn; cần tích hợp kết luận giới hạn vào bài |
| M2: gộp run không đồng nhất, ít seed | Có bảng phân tầng, Recall-ASR, bootstrap seed theo stratum | Phần phân tích đã có. Chỉ 3 seed/stratum, chưa tăng số lần train; chưa thấy bản Word tích hợp kết quả mới |
| M3: threat model không khớp | Word vẫn mở đầu bằng externally supplied pretrained classifier; chưa có poisoning-time adaptive attack mới hoặc bản viết lại chốt honest-provider | Chưa giải quyết |
| M4: public clean data | Thắng có public BODMAS20K, SHA256 disjoint các role, đánh giá 27 cell EMBER2018. Phúc thêm script50K nhưng thiếu artifact và chỉ đo BODMAS holdout/reference drift | Có thí nghiệm tối thiểu cho phản biện; chưa nghiệm thu mục50K của Phúc |
| M5: baseline thiếu | Thắng có IF/LOF/kNN full/top32, rarity, signed-view3 IF đủ54 cell; có mô tả legacy_rare | Đã bổ sung các comparator chính. Original Severi-selector attack benchmark còn thiếu; batch BODMAS mới của Phúc không thay thế đánh giá backdoor |
| M6: FPR/calibration | Có tolerance policy version riêng, CP intervals và số endpoint vượt1%; 108 sidecars | Đã có recalibration hồi cứu. Chưa có certification pool mới; web/default bundles vẫn dùng ngưỡng cũ. Không hứa FPR tương lai luôn≤1% |
| M7: Shadow tuần hoàn | Public20K là model riêng, giữ eligibility gốc, không tái dùng evaluator | Đã có comparator độc lập mới. Chưa thấy bài sửa để dùng nó làm đối chứng chính và đưa Shadow200K cũ xuống phụ lục |
| M8: feature-space vs PE thật | Có engine/runner mới, nhưng logic target/masks/pass-rate sai; thiếu artifact PE mới | Chưa đạt yêu cầu thầy |
| M9: SentiNet/đóng góp/tên | Không thấy SentiNet trong Word kiểm tra | Chưa giải quyết trong bản hiện có |

Đối với M6: trên 108 Reduced/Full endpoints, final-FPR violations cũ6/108, tolerance pointwise0/108. Trên 378 endpoints của7 cached methods, vẫn còn13 violations pointwise và3 family-adjusted. Họ378 không bao gồm baseline mới. Đây là quan sát của final hiện có, có đánh đổi recall, không phải chứng nhận thực địa.

## 2. Sáu nhiệm vụ Phúc

### T1 — Có sửa đúng code và kiểm chứng local

- `tests/test_reviewer_core.py:22` chuyển sang `assert_allclose(rtol=0, atol=1e-12)`.
- Chạy lại test core ở hai schema: **2 passed**.
- Đây là bằng chứng local Windows; không thay log PASS trong Docker mà file task yêu cầu.

### T2 — Mới xử lý một phần, skip không phải pass

- `tests/test_reviewer_core.py:35-36` bỏ qua calibration test khi thiếu roles.
- `compose.yaml:37,63` mount `data/primary` vào backend/dashboard; không có service `xsentinel-test` trong compose này.
- `open_roles()` còn đọc `source_directory` và dataset/raw X/y/ids arrays; roles hiện có ghi đường dẫn Windows tuyệt đối. Chỉ mount roles chưa đủ để xác nhận Linux test container đọc được raw source.
- Không có log Docker test mới trong checkout. Docker Engine hiện không truy cập được qua pipe desktopLinuxEngine trong lần kiểm tra.
- DoD cần: raw source/path resolution đúng và các test bắt buộc thực sự chạy; báo rõ test nào skipped và lý do.

### M8 — Lỗi khoa học và kiểm chứng nghiêm trọng

1. **Không có artifact ở checkout:** `outputs/pe_real_watermark/` vắng mặt. Chưa kiểm chứng được 22 file, 16 malware, drift376,4 hoặc recall.
2. **PASS bị gán sẵn:** `run_pe_watermark_experiment.py:303` ghi `wine_benign_pass_rate: 1.0`, không tính từ kết quả thực thi.
3. **Không chạy vẫn gắn PASS:** dòng137-138 thiếu Wine → `PASS_STRUCTURAL_VALIDATED`; dòng167-168 .NET → `PASS_STRUCTURAL_DOTNET`. GUI còn sống1,5s không chứng minh toàn bộ chức năng được giữ. Không có runner Windows riêng trong phần code này.
4. **“17” thực ra16:** dòng184 có16 indices, khác bộ17 source-derived ở schema. Danh sách còn chứa các feature bị upstream Severi xếp vào infeasible. Cần mapping chính xác theo tên/schema, không tự đặt nhãn Severi.
5. **Không khớp backdoor model:** engine đặt image/linker versions6/14/29, trong khi trigger của model frozen được chọn có các target22/75/38. Chưa có poisoning train mới cho watermark này, cũng chưa kiểm đủ target vector trích xuất lại.
6. **Recall sai đối tượng:** dòng289-291 tính tỷ lệ alert trên toàn bộ malware đã chỉnh. Chưa xác định eligible, backdoor-successful, hay clean-counterfactual. Tỷ lệ alert này không tự là backdoor recall.
7. **Nuốt lỗi section injection:** engine dòng91-93 quay về bytes chỉ sửa header khi lỗi và không báo bước watermark bị thiếu.

Chạy `tests/test_pe_real_watermark.py` trong lượt kiểm tra: **4 skipped**, do thiếu CSV/fixture. Chưa xác nhận được “4/4 passed” trên checkout này.

Nghiệm thu: cần artifact/log/hashes từ Kali, pass-rate tính đúng, kiểm đủ tọa độ target, cohort/attack đúng model và kiểm chức năng trước/sau phù hợp. Nếu chưa làm được, thầy cho phép thu binary audit còn một đoạn và giới hạn kết luận.

### M4 — 50K chưa trả lời câu hỏi transfer/backdoor

- `scripts/train_public_shadow_50k.py` có train50K/validation10K, nhưng evaluation chỉ trên BODMAS và drift500 benign reference.
- Không có loop đánh giá triggered EMBER2018 với threshold, recall/FPR/pAUC theo cùng masks của bảng chính.
- Bỏ mất bộ lọc cross-EMBER SHA256 overlap của pipeline20K. Tái dựng split chỉ từ metadata/labels cho thấy **3 train IDs và1 validation ID trùng EMBER2018 fit**; không thấy trùng final ở split này. Đây là thiếu độc lập dữ liệu training, không phải phát hiện test-final leakage.
- Comment “matching primary configuration” không đúng với leaves31/fractions0,8 so với64/0,9 của primary. Đổi params được phép nếu khai báo và giữ protocol so sánh rõ.
- Không có `outputs/public_shadow/` hoặc model/log/metrics50K ở checkout, nên số99,59% và drift0,0651 chưa kiểm chứng được.
- Thí nghiệm20K của Thắng vẫn có giá trị trong phạm vi đã khai báo; không gộp nó với kết quả50K chưa có bằng chứng.

### M5 — Batch mới đo novelty trên malware thường, không đo backdoor detection

- `scripts/run_batch_new_baselines.py:85-90` chọn BODMAS malware thường làm positives; không apply trigger hoặc dùng eligibility/success masks.
- Không chấm X-SENTINEL trên cùng cohort, nhưng README tại dòng185 có sẵn kết luận X-SENTINEL recall cao hơn. Kết luận này không được hỗ trợ bởi script.
- Fallback dòng94-97 dùng benign reference làm positive và sử dụng lại dữ liệu fit: không được dùng làm kết quả malware/backdoor.
- Dòng132-134/140-142 thay exception bằng pAUC0/AUC0,5: có thể biến lỗi phần mềm thành số liệu có vẻ hợp lệ.
- Không có `outputs/new_baselines/` ở checkout. Bảng đúng-cohort của Thắng đã có54 cell; batch BODMAS này chỉ có thể là thí nghiệm novelty khác nếu báo đúng mục tiêu.

### P4 — Phân rã latency đang đếm SHAP trùng

- `benchmark_latency.py:97` gọi `scorer.score()` cho stage3.
- `reviewer_core.py:18-20,42` cho thấy lệnh đó tính lại SHAP, main và Behavioral predictions, chứ không chỉ rank VMC/BGS.
- `benchmark_latency.py:107-108` total gọi explicit SHAP rồi scorer tính SHAP thêm lần nữa.
- Script chọn một file đầu tiên và lặp100 lần, nhưng sinh câu “realistic PE executables” số nhiều và “confirming real-time gateway throughput”. Chưa đo throughput/load/concurrency/API.
- Không có `outputs/latency/` hay iteration logs để xác minh34,98ms.
- Cần đo một pipeline tính SHAP đúng một lần; timer trên intermediate outputs cho từng stage; ghi scope/file hash/hardware/threads, nhiều file khi muốn suy rộng. Chưa dùng câu latency hiện tại trong paper.

## 3. Bài báo và phần trình bày

Bản Word đang có ở `output/ieee_merged_2026_10_28/` vẫn chứa:

- Động cơ “externally supplied, pre-trained ... may be trojaned” (chưa thu hẹp M3).
- Appendix D về demonstration implementation.
- Tên/email tác giả; chưa thấy SentiNet hoặc LLM disclosure trong nội dung được kiểm tra.
- Đoạn169 cũ, chưa có giải thích position masks mới.

Chưa tìm được bản Word mới tích hợp kết quả30–31/10. Các nội dung khác như hyphenation, Abstract, công thức, ghi rõ Android cho Jigsaw Puzzle cần người biên tập kiểm và render; audit này không xác nhận layout Word đã sửa.

Số169 đã được giải thích bằng artifact Thắng: cùng vị trí poison/removal trên pool100.000 benign, kỳ vọng200; không sửa số quan sát169 thành kỳ vọng. Cần đưa lời giải thích vào manuscript.

## 4. Ưu tiên tiếp theo

1. Phúc bàn giao artifact/log/model/split IDs từ Kali; ghi PASS/FAIL/SKIP đúng, tránh trạng thái hoàn thành chỉ dựa trên handoff.
2. Sửa logic M8, M5, P4 trước khi chạy lại để tránh tốn thời gian cho số đo sai mục tiêu.
3. Hoàn thiện Public50K: dedup theo role, lưu split IDs/hashes, đánh giá transfer trên27 cell EMBER2018 với cùng masks/calibration; giữ nguyên kết quả20K để đối chiếu.
4. Nhóm chốt M3 và phương án M8; phân người nhận M9/original Severi selector benchmark.
5. Biên tập tích hợp Methods/Results/Limitations và kiểm bản render; tách việc bài báo đã sửa với việc code/thí nghiệm đã có.

## 5. Kiểm tra thực hiện trong lượt audit

- `git status --short`: sạch trước audit. HEAD `af777f3`.
- 432 file/hash trong ledger Thắng:0 mismatch.
- Test command: `.venv/Scripts/python.exe -m pytest tests/test_reviewer_core.py tests/test_pe_real_watermark.py -k 'supplement_core or watermark' -q -p no:cacheprovider --basetemp <writable ASCII path> --tb=short`.
- Kết quả: **2 passed,4 skipped,2 deselected**,14,83s. Hai calibration tests bị deselect có chủ ý; không suy ra chúng pass hoặc fail từ lệnh này. Không chạy full Docker suite.
- Không chạy chương trình PE, không huấn luyện model, không sửa code để làm test xanh trong lượt audit.
