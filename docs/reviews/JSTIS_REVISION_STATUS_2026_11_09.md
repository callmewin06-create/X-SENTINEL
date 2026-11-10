# Trạng thái triển khai bản sửa X SENTINEL ngày 09 tháng 11 năm 2026

**Bản ghi lịch sử, đã có cập nhật10/11:** thí nghiệm và ghép Word đã xong. Xem [kết quả hoàn tất](JSTIS_COMPLETED_RESULTS_2026_11_10.md); phần “đang chạy” dưới đây không còn là trạng thái hiện tại.

Đã triển khai sửa code, phân tích cache và Word theo hướng evaluation đã chốt. **Chưa hoàn tất M3 hoặc bản nộp báo.** Batch thí nghiệm mới đang chạy; kết quả Search không được dùng thay cho kết quả held-out.

## Bản Word hiện tại

`output/jstis_revision_2026_11_09/X_SENTINEL_Anonymous_Working_2026_11_09.docx`

Đã sửa title giới hạn LightGBM; Abstract dùng recall tại ngưỡng calibration 35,75%/48,33%; thêm Abstract tiếng Việt (EN132 từ, VI141 từ); làm rõ thiên vị geometry; bổ sung C2 attribution và direct-evasion restoration; phân tích rank ties; chuyển hai công thức VMCnorm/MAX sang thảo luận hướng phát triển; đánh lại số công thức và cross-reference; bỏ dải latency thiếu provenance; giải thích phạm vi Spectral/Activation; bổ sung raw novelty trong Table I. Bản gốc 04/11 được giữ nguyên. Bản sửa là working draft, chưa ghép kết quả formal mới và chưa chuyển hoàn toàn sang layout JSTIS.

## Bằng chứng đã chạy

- `outputs/jstis_revision_2026_11_09/cache_audit`: tái tạo headline, sensitivity ASR cutoffs 0,4/0,5/0,6; before/after SHA256 của 216 file primary trùng nhau.
- `outputs/jstis_revision_2026_11_09/c2_attribution`: 20 score rows, hai model × hai fixture × năm inputs; phi/view shares/VMC. Với model poisoned, physical-minus-ideal ΔVMC là +0,002414 native, +0,004246 managed; physical-minus-original là +0,101915 và −0,092192. Đây là chẩn đoán n=2 với adapter hiện đại, chưa có legacy parity hoặc malware ASR/recall.
- `outputs/jstis_revision_2026_11_09/direct_evasion`: 100 Development malware IDs/dataset chọn theo lexical trước query; tất cả 54 frozen configurations, restore từng coordinate và view. Không dùng final để tối ưu.
- `outputs/jstis_revision_2026_11_09/score_tails`: rank resolution/saturation/ties, calibration/final tails. Reduced 0/54, Full 6/54 point-estimate FPR >1%; Full worst 227/10000.
- `outputs/jstis_revision_2026_11_09/TEST_RESULTS.xml`: 44 tests passed; gồm source-selector comparisons, ties, feedback-dependent trajectory, strict feasibility, canonical fingerprint, infrastructure failure, Unicode model I/O và barrier trước khi mở held-out. Tests phần mềm không phải kết quả effectiveness.

## Dữ liệu mới và code M3

Steward metadata ở `outputs/jstis_revision_2026_11_09/fresh_metadata_v2`; exclusion ledger gồm 622688 known historical SHA256. Cả hai dataset đã đủ bảy roles theo budget. Không có ID trùng giữa các roles của từng dataset, với ledger đã kiểm kê, hoặc giữa hai tập roles được chọn. Không suy ra độc lập theo family/time hoặc loại hết lịch sử bên ngoài workspace.

`data/jstis_revision_2026_11_09/{EMBER2018,EMBER2024}/attacker` đã materialize fit200K balanced, selection10K balanced và development10K balanced. V3 có 80/220000 original is_pe=0, được giữ nguyên theo scope dữ liệu PE chính thức; không tự sửa cờ hoặc giả nhận mọi binary đã được kiểm chứng. Confirmation/reference/calibration/final mới chưa được materialize/mở cho optimizer.

Đã thêm ba selector adaptations, hai domain R10/A10 không quota, supplementary trigger family không nới validation cũ. Independent MinPopulation giữ tie theo first observation; CountAbsSHAP dùng sum; signed conditioned helper giữ feature ties theo lower index như adaptation đã mô tả. Không nhận là tái tạo nguyên xi trên mọi tie hoặc schema khác.

`src/xsentinel/attacks/sequential.py` thực hiện trajectory dùng feedback; hai incumbent độc lập, 16 candidates/arm, fixed poison IDs/objective IDs, canonical float32 trigger và không trả infeasible fallback. Các candidate được fit lại với learner cố định.

## Batch đang chạy

Output hợp lệ hiện tại: `outputs/jstis_revision_2026_11_09/attacks_v2`.

- `run_jstis_matrix.py` chạy serial sáu dataset–seed cells, mỗi lần một fit.
- `finish_jstis_after_matrix.py` đang chờ đủ sáu cell receipts. Sau đó gọi global lock, evaluator materialization, calibration-only evaluation và summary. Nếu có recorded infrastructure failure, bước đánh giá dừng và giữ sealed barrier.
- `complete_jstis_followup.py` là entrypoint resume toàn pipeline; **không chạy thêm một bản khi driver hiện tại còn hoạt động**.
- Global gate phải khóa 36 static attempts và 12 adaptive arms trước khi release held-out. Unconfirmed static vẫn đánh giá, adaptive no-valid trả N/A. Full dùng một clean Behavioral auxiliary, raw-kNN-top32 dùng cùng access.
- Cache và score outputs có hashes; mới có code/test của evaluation, chưa có kết quả fresh held-out. Chưa được điền recall mới vào paper.

Lượt `attacks` ban đầu dừng ở RAM gate trước poison fit. Đã giữ log INCOMPLETE_INFRASTRUCTURE và chuyển sang file-backed buffer, không giảm N/rounds/budget. Clean/Behavioral models và clean-selection phi được reuse với exact hashes, có `REUSED_CLEAN_FROM.json`. Peak memory từ launcher trong launch receipt đầu không đại diện worker; dùng `process_memory` ghi bên trong worker. Candidate poisoned đầu ở v2 đã hoàn tất, fit135,89 giây, worker peak working set6,23GB/peak commit3,20GB; đây không phải dự báo tổng wall time.

## Ma trận 17 mục góp ý

| Mục | Trạng thái | Bằng chứng hoặc việc còn lại |
|---|---|---|
| Major3.1 Đóng góp nghiên cứu | Đã sửa định vị, chờ kết luận cuối | Title/Abstract/Discussion giới hạn evaluation và LightGBM |
| Major3.2 Thiên vị attacker, M3 | Đang chạy | Selector/search/barrier code và tests đã có; chưa đủ formal matrix |
| Major3.3 Cohort nhỏ | Một phần | Sensitivity đã chạy, giới hạn seed đã viết; fresh attempts đang chạy |
| Major3.4 Headline threshold | Đã sửa và tái tạo | Abstract35,75/48,33; cap là secondary |
| Major3.5 Problem-space | Đã có diagnostic trong scope n2 | C2 SHAP/VMC và giới hạn; functioning-malware evaluation vẫn chưa có |
| Major3.6 Defender budgets | Đã giữ tradeoff và nêu coupling | Table I, Discussion, Appendix C; Shadow200K không gọi independent |
| Major3.7 Direct evasion | Đã chạy diagnostic | Coordinate/value/view CSV và restoration; main text nêu fixed Development subset |
| Major3.8 VMCnorm/MAX | Đã chuyển Future Work | Công thức12/13 trong Discussion, không claim cải thiện |
| Minor4.1 Rank resolution/ties | Đã chạy và viết | Reference500 khác calibration2000; rank_tails.csv |
| Minor4.2 FPR tails | Đã chạy audit | 6/54, worst227/10000, không gán nguyên nhân thiếu bằng chứng |
| Minor4.3 Split/time | Đã thu hẹp claim | Official source/random roles; không claim temporal robustness |
| Minor4.4 Model scope | Đã sửa | Title LightGBM, không nhận đã test MalConv/MLP |
| Minor4.5 Spectral/Activation | Đã giải thích scope | Có thể dùng SHAP/leaf representation nhưng chưa đánh giá; IF training defense được tách rõ |
| Minor4.6 Văn phong | Một phần | Đã sửa các đoạn chính; cần biên tập sau khi ghép formal results |
| Minor4.7 Table/ref/layout | Working draft đã QA | Cần QA lại sau merge results và chuyển template |
| Minor4.8 Double-blind/author files | Một phần | Word anonymous; hồ sơ tác giả và audit repo bản upload còn thiếu |
| Minor4.9 Latency | Đã bỏ con số không đủ provenance | Không thay bằng timing từ cấu hình khác |

## Phần nộp báo còn lại

Đã tải Word, LaTeX và author-response templates từ [trang chính thức](https://isj.vn/index.php/journal_STIS/information/authors), lưu trong `output/jstis_revision_2026_11_09/journal_templates`. Hướng dẫn [submission](https://isj.vn/index.php/journal_STIS/about/submissions) yêu cầu abstract EN/VI khoảng120–150 từ và keywords hai ngôn ngữ. Nhóm làm LaTeX theo template chính thức sau khi nhận nội dung Word hoàn thiện.

Còn: hoàn thành và diễn giải fresh matrix; ghép bảng/kết luận vào Word; response17mục có trang cuối cùng; rà citations/reference order theo template; author order/corresponding author/affiliation/email/ORCID/bio/ảnh do nhóm cung cấp, xác nhận funding/conflicts; kiểm anonymity repo/artifact metadata của bản thực sự upload. Chưa gửi bài, email, commit hoặc push.
