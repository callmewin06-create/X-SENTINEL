# Kết quả bản sửa và đối chiếu góp ý ngày 10 tháng 11 năm 2026

**Train, held-out evaluation, tổng hợp, kiểm số liệu và ghép nội dung Word đã hoàn tất.** Bản hiện tại: `output/jstis_revision_2026_11_10/X_SENTINEL_Anonymous_Completed_M3_2026_11_10.docx`. Đây là bản nội dung để nhóm/thầy review và đồng đội chuyển LaTeX, chưa phải bản đã hoàn tất mọi thủ tục nộp JSTIS.

## Kết quả cần hiểu đúng

36 static attempts và12adaptive arms đã hoàn tất trên hai dataset × ba seed. Có28/36static và12/12adaptive qua Search/Confirmation. Hai trajectory diverge trong cả6cells; có207unique poisoned fits và12clean/Behavioral models. 216fileprimary cũ không thay đổi. Toàn bộ model/trigger được khóa trước khi mở fresh held-out.

| Dataset | Objective | Mean ASR | Mean Reduced recall | Mean final benign FPR |
|---|---|---:|---:|---:|
| EMBER2018 | ASR-only |99,98%|63,10%|0,82%|
| EMBER2018 | VMC-aware |98,42%|0%|0,90%|
| EMBER2024 | ASR-only |99,62%|40,42%|0,78%|
| EMBER2024 | VMC-aware |95,60%|0%|0,75%|

Mỗi số là macro mean qua3seed. Word có sample SD, per-seed count/n và pointwise CP95. Cả6VMC-aware attacks vẫn qua confirmation nhưng VMC/Reduced TP đều bằng0 trên final successful inputs. Trên common-success intersection, Reduced của ASR-only còn62,96%/40,15%, còn VMC-aware vẫn0%; khác biệt không chỉ do đổi success denominator. Đây là bằng chứng về giới hạn trong bounded feature-space poisoning-time adaptation, không phải bảo đảm mọi attacker đều né được, cũng không phải kết quả bảo toàn chức năng malware.

Raw-kNN cùng access không là lời giải phổ quát: recall VMC-aware chỉ0,45% trênV2 và10,07% trênV3. Full đạt0,06%/0% trên hai VMC-aware cohorts. TADR có độ biến thiên và FPR khác; không bỏ FPR khi so sánh recall. Fresh Reduced có2/48point-estimate FPR vượt1% (worst107/10000), khác với frozen Reduced0/54. Không tune lại ngưỡng theo final để che exceedances.

Kết quả phù hợp định vị evaluation/negative results đã chốt. Công thức detector được giữ; protocol, phép đối chứng và phạm vi kết luận được sửa theo bằng chứng. Không giữ claim phòng thủ hiệu quả phổ quát.

## Đối chiếu 17 mục góp ý

Tên mục dưới đây là tóm tắt nội bộ, không phải trích nguyên văn thư phản biện. Số trang theo bản Word/PDF nội dung23trang ngày10/11; khi chuyển template phải cập nhật lại.

| Mục góp ý | Cách xử lý và kết quả | Vị trí bản mới | Trạng thái |
|---|---|---|---|
| Major3.1 Định vị đóng góp | Đổi title/Abstract và kết luận sang evaluation trong LightGBM; nêu failure mới, không nhận đã tạo defender mạnh hơn |tr1–3; V-M tr13–14; VII tr15|Đã sửa nội dung|
| Major3.2 Circularity/attacker bias và M3 | Ba selector adaptations × R10/A10, không quota;16candidate/arm có feedback; nguồn dữ liệu mới và global barrier; hai trajectory khác nhau ở6/6cells;6VMC-aware failures của detector được giữ nguyên |III-A tr3; IV-E tr7–8; TablesXI–XII tr13–14; XXII–XXIII tr22–23|Đã chạy và ghép kết quả|
| Major3.3 Cohort nhỏ | Giữ frozen attempted/confirmed counts và3seed; có sensitivity cutoffs và fresh36attempts/12arms. Không pool source IDs tái sử dụng thành independent files |V-A/C tr8–9; V-M tr13; VI tr14–15; AppendixF|Đã bổ sung; giới hạn n3 còn nguyên|
| Major3.4 Headline retrospective threshold | Abstract và Results chính dùng calibration recall35,75%/48,33%. Final-FPR-cap37,69%/52,82% chỉ là secondary retrospective comparison |Abstracttr1; TableVI tr8; V-E/TableX tr10–11|Đã sửa và tái tạo|
| Major3.5 Feature/problem-space gap | C2n2fixtures có target-only/physical SHAP/VMC diagnostic; giữ legacy-parity và functioning-malware limitations. Trigger82sections/file2495bytes có consistency check |V-L tr12|Đã xử lý trong phạm vi n2 đã chốt; chưa có functioning-malware proof|
| Major3.6 Clean-data budgets và Shadow coupling | TableI ghi access; Shadow200K là eligibility model được nêu rõ, PublicShadow20K tách riêng; giữ budget tradeoff và Full secondary mới |TableI/III-A tr3; V-G tr11; AppendixC tr19–20; TableXXII|Đã sửa phạm vi so sánh|
| Major3.7 Direct evasion | Fixed Development100IDs/dataset trước query;54models; coordinate/value/view và restore-one/view CSV. Nêu Structural restoration effect, không suy population causality |V-D tr10; `direct_evasion/restoration.csv`|Đã chạy và viết|
| Major3.8 VMCnorm/MAX | Chuyển hai extension và công thức12/13 sang Discussion/FutureWork; bỏ claim cải thiện chưa validation |VI tr14|Đã chuyển theo phương án chốt|
| Minor4.1 Rank resolution/ties/fusion loss | Phân biệt reference500/rankgrid501 với calibration2000; lượng hóa số rank/tie counts và fusion loss |V-F tr11; `score_tails/rank_tails.csv`|Đã audit và viết|
| Minor4.2 FPR tails | Frozen Full6/54,worst227/10000; fresh Full10/48,worst144/10000 và Reduced2/48,worst107/10000. Counts/CP và giới hạn calibration được giữ |V-H tr11; V-M tr14; AppendixE tr21–22; per-model JSON|Đã audit, không gán nguyên nhân thiếu chứng cứ|
| Minor4.3 Split/time | Mô tả official source partitions, seven roles, known-history SHA exclusion; không nhận random split là temporal robustness |IV-A tr6; IV-E tr7–8; VI tr14–15|Đã sửa claim; near-duplicate/family/time remain|
| Minor4.4 Model scope | Title và các kết luận giới hạn LightGBM; không nhận đã đánh giá MalConv/MLP |tr1; III-A; VI/VII|Đã sửa|
| Minor4.5 Spectral/Activation | Giải thích có thể dùng SHAP/leaf representations nhưng chưa đánh giá adaptations; training-levelIF filtering được nêu đúng tên |II-C tr2; V-K tr12; AppendixD tr20–21|Đã giải thích scope; không bịa baseline|
| Minor4.6 Văn phong/Threats | Đồng nhất Introduction, Abstract, Methods, Discussion và Conclusion với study mới; gom giới hạn về seeds, access, data reuse, binary constraints |tr1–3; VI/VII tr14–15|Đã biên tập nội dung; copyedit cuối sau LaTeX còn lại|
| Minor4.7 Table/ref/layout | Thêm4tables, đánh số liên tụcI–XXIII;13nativeequations; references first-use1–33; render và xem đủ23trang, sửa header wraps |Toàn bản; `output/jstis_revision_2026_11_10/QA.json`|Word đã QA; layout JSTIS cuối còn lại|
| Minor4.8 Double-blind/author files | Word coreAnonymous, không comments/author email; review copy tách hồ sơ tác giả. Chưa có author order/bio/photo/ORCID/funding/conflicts được nhóm xác nhận; chưa audit bản repo upload mới |tr1; `SUBMISSION_REMAINING.md`|Một phần, chưa chốt hồ sơ nộp|
| Minor4.9 Latency provenance | Bỏ dải40,5–97,8ms khỏi claim; không thay bằng benchmark khác. Training timer10,87h ghi rõ training-only, không phải walltime/latency |VI tr15; V-M tr13|Đã sửa|

## Artifacts kiểm chứng

- `outputs/jstis_revision_2026_11_09/completed_audit/VERIFIED_RESULTS.json`: global/model/score hashes, count/n, calibration thresholds và macro CSV đã đối chiếu.
- `followup/summary/all_attempts.csv`:240rows =48attempts ×5methods; `common_success_comparisons.csv`:840method-pair rows. Đây không phải240models hoặc840independent experiments.
- `followup/evaluations/{dataset}/seed_*/{fingerprint}/RESULTS.json` và `scores.npz`: per-model pointwise CP95, predictions, score arrays, FP/TP và thresholds.
- `attacks_v2/.../{asr_only,vmc_aware}.trajectory.jsonl`: lịch sử16logicalcandidates/arm; `protocol.lock.json`, `ATTACKS_LOCKED.json`, `GLOBAL_ATTACKS_LOCK.json` giữ provenance trước held-out.
- `TEST_RESULTS.xml`:44softwaretests đã qua. Audit hậu nghiệm đã chạy thành công; không dùng softwaretests thay effectiveness results.
- `output/jstis_revision_2026_11_10/QA.json`:Word23trang/36tables(gồm13equationtables),23data-table captions,13nativeequations,reforder và hashes.

Các cache trước ngày09/11 và Word nguồn được giữ nguyên. Không commit/push/upload/email/submit trong lượt sửa này.
