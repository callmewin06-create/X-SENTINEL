# Kế hoạch nhiệm vụ Thắng theo góp ý G4 phiên bản 2

Ngày lập: 30/10/2026. Người phụ trách: Trần Đặng Hữu Thắng.

**Trạng thái: ĐÃ DUYỆT TRIỂN KHAI ngày 30/10/2026.** Xem docs/THANG_REVISION_V2_HANDOFF_2026_10_30.md và coverage trong output để biết tiến độ thực. Nội dung sau lưu lại kế hoạch trước duyệt. Lượt này chỉ đọc tài liệu, kiểm kê mã nguồn/kết quả và lập kế hoạch. Chưa thay thuật toán, hiệu chỉnh ngưỡng, huấn luyện model, chạy thí nghiệm, sửa manuscript hoặc commit/push. Các tên đầu ra phía dưới đều là dự kiến.

## 1. Căn cứ và phạm vi

- Góp ý thầy: `C:\Users\win9tui\Downloads\gop ý G4_v2.pdf`, 5 trang. SHA256: `85a8b6ce2c3ceb5d93e01d2a9919b9aca766500df5bc9d7d5a0b428aed195002`.
- Phân công: `C:\Users\win9tui\Downloads\TASK_THANG.docx.md`. SHA256: `fda1840f80342c6e041f00d86f71ce5a29c2325a5a15f48beba12cdbd7b9c7b3`.
- Mốc code đã đọc: `4d0783c5c30f04732a66adf7b5c07b6089ac6987`. Trạng thái xóa file/chưa commit có sẵn và hai ZIP fixture hiện tại phải được giữ nguyên.
- File phân công giao 6 nhóm việc thuộc M1, M2, M4, M5, M6, M7. Các mã này là mã trong PDF mới, không phải M1-M5 của một số tài liệu thuật toán cũ.
- Phạm vi chính: thuật toán, calibration, baseline và thống kê. Không mặc định nhận toàn bộ M3/M8/M9 hay phần xuất bản/ẩn danh của cả nhóm.

PDF xác nhận các phép cộng và số liệu chính đã đúng, nhưng vẫn nêu 9 vấn đề lớn. Hoàn thành riêng phần Thắng chưa đồng nghĩa giải quyết hết phản biện hoặc đạt một venue cụ thể.

## 2. Ba điều chỉnh cần duyệt trước khi triển khai

### 2.1. Sửa tiêu chí M6

Không dùng tiêu chí: "Clopper-Pearson 95% bảo đảm FPR trên mọi final pool luôn <=1%; không cấu hình nào vượt".

Tiêu chí đề xuất: policy calibration có lập luận kiểm soát FPR population ở mức 1% với confidence đã khai báo, dưới giả định lấy mẫu/cùng phân bố thích hợp; ngưỡng được chọn không nhìn final; báo cáo final FPR, cận tin cậy, số endpoint vượt 1% và thay đổi recall. FPR quan sát của một final pool hữu hạn vẫn có thể vượt 1%, kể cả khi xác suất population không vượt mục tiêu.

Phải phân biệt confidence 95% cho từng endpoint với confidence đồng thời cho cả họ endpoint. 54 cấu hình, 108 Reduced/Full endpoints và số endpoint sau khi thêm comparator không phải cùng một mẫu số.

### 2.2. Sửa tiêu chí thắng baseline

Không lấy "chứng minh X-SENTINEL vượt trội" làm điều kiện nghiệm thu. Điều kiện đúng là so sánh công bằng, cùng quyền truy cập và mẫu đánh giá, tái lập được, giữ cả kết quả phương pháp đề xuất thua. Nếu rarity/raw-feature/view-only thắng, kết luận và phạm vi đóng góp phải thay đổi theo dữ liệu.

### 2.3. Chẩn đoán fusion trước, chưa mặc định thay core

Thầy cho phép ba hướng: giải thích overlap; đề xuất fusion có nguyên tắc; hoặc thừa nhận VMC là tín hiệu chính và BGS phụ thuộc schema. Vì vậy dynamic fusion là nhánh có điều kiện, không phải bước bắt buộc trước khi hiểu lỗi. Không chọn trọng số dựa trên final đã quan sát rồi gọi là validation mới.

## 3. Kiểm kê hiện trạng chỉ đọc

| Đầu việc | Có thể dùng lại | Phần còn thiếu |
|---|---|---|
| M6 calibration | `src/xsentinel/detection/calibration.py`, cache calibration benign của 54 cấu hình | Policy CP/tolerance được version hóa và báo cáo FPR/CI tương ứng |
| M1 overlap | Điểm từng mẫu trong 54 `paired_predictions.npz`; `revision/analysis.py`; công cụ rank/fusion cũ | Bảng VMC-only/BGS-only/cả hai/fusion-only/lost-by-fusion và giải thích theo strata |
| M5 raw baselines | Vector và roles hai schema; framework signed-SHAP IF và low-FPR metrics | IF/LOF/kNN trực tiếp trên input, preprocessing và protocol công bằng |
| M5 rarity | `src/xsentinel/attacks/selectors.py::legacy_rare` | Detector rarity riêng, không đọc manifest trigger |
| M2 thống kê | Metrics từng run và bootstrap theo source-ID với model cố định | Bảng phân tầng, bootstrap run/seed có xét phụ thuộc và scatter Recall-ASR |
| M4/M7 Public-Shadow | `scripts/run_clean_budget_2026_10_27.py` | Public training corpus, pipeline độc lập và đánh giá chuyển nguồn sang EMBER2018 |

Năm file mới được MD đề nghị chưa tồn tại: `analyze_fusion_overlap.py`, `raw_feature_outlier.py`, `rarity_score.py`, `bootstrap_analytics.py`, `train_public_shadow_bodmas.py`.

Có đủ 54 paired-prediction caches và 54 calibration-score caches để tái phân tích nhiều mục mà không train lại main model hoặc tính lại toàn bộ SHAP. Caches này không chứa toàn bộ vector SHAP d chiều. Nếu baseline mới cần SHAP chưa được cache, phải có bước tính riêng sau duyệt.

Bộ dữ liệu BODMAS có features/labels đủ để train 20K-50K chưa được tìm thấy trong các thư mục dữ liệu hiện kiểm tra. Gói kết quả 200 binary/175 scored trước đây không thay thế được corpus đó. Nguồn chính thức công khai `bodmas.npz` và metadata; kế hoạch ưu tiên lấy vectors/labels, không cần executable để train Shadow.

## 4. Gói 0: khóa protocol chung và phụ thuộc

Thực hiện đầu tiên sau khi duyệt:

1. Ghi code/data/model/cache hashes, schema, source IDs, số attempted/confirmed và ngưỡng cũ.
2. Chốt các tập dùng để fit, chọn preprocessing/weights/top-k, calibration/certification và đánh giá. Final cũ chỉ là đánh giá bổ sung trên benchmark đã quan sát. Muốn tuyên bố validation mới cần tập chưa sử dụng và ghi nhận lịch sử tiếp xúc dữ liệu. Nếu benign calibration/certification cũ đã được dùng để lựa chọn score, weights hoặc policy theo cách thích nghi, cần một pool chứng nhận độc lập mới; nếu không có thì chỉ báo recalibration hồi cứu, không viện dẫn bảo đảm confidence như một đánh giá độc lập.
3. Chốt positives: successful-eligible là cohort chính hiện tại; paired-new-evasion và all-triggered là phân tích riêng. Dùng cùng masks khi so các detector trong một run.
4. Chốt confidence từng endpoint hay đồng thời; định nghĩa họ endpoint trước khi chạy M6.
5. Chốt M3 với nhóm: thu hẹp về honest-provider/data-poisoning, hoặc có người nhận adaptive poisoning-time. Optimizer 32 query hiện tại không thay thế attack tại thời điểm poisoning.
6. Kiểm kê BODMAS features, labels, metadata, nguồn/phiên bản và đường lấy dữ liệu ngay đầu tuần 1.
7. Dùng namespace kết quả mới, thí dụ `outputs/teacher_revision_v2_thang_2026_10_30/`; không ghi đè primary hoặc kết quả 27/10. Không tự commit/push.

Đầu ra dự kiến: `protocol.json`, `claim_task_matrix.csv`, `input_manifest.json`, danh sách mục phụ thuộc và người nhận do nhóm xác nhận.

## 5. Gói 1: M1 overlap và giải thích fusion (P0)

### Công việc

- Tách theo dataset, trigger family, poison rate, seed và confirmation status trước khi lấy trung bình.
- Với cùng IDs, xác định mẫu VMC bắt riêng, BGS bắt riêng, cả hai bắt và cả hai bỏ; báo số đếm/mẫu số và Jaccard.
- Bổ sung mẫu fusion bắt được khi cả hai component chưa vượt ngưỡng riêng, và mẫu VMC bắt được nhưng fusion bỏ. Fusion trung bình rank không phải phép OR, nên một Venn hai tập chưa giải thích hết.
- Làm cả phía triggered malware và benign; phân biệt original calibration thresholds với retrospective empirical-FPR-cap operating points.
- Đối chiếu nguyên nhân V3: phân bố score/rank, ties, contribution của BGS và từng strata. Không suy ra nguyên nhân từ macro mean đơn thuần.
- Tái dùng W25/W50/W75/MAX/M3/M4 như ứng viên hữu hạn nếu cần. Tài liệu fusion cũ đã dùng final quan sát phải được ghi đúng lịch sử.

### Nhánh fusion mới có điều kiện

Chỉ mở nếu overlap chỉ ra tín hiệu bổ sung đáng kiểm tra. Chốt score/weights bằng tập development phù hợp trước calibration; không dùng final để chọn. Nếu không có cải thiện đáng tin cậy, bàn giao kết luận VMC là tín hiệu chính trên V3 thay vì cố tạo công thức phức tạp.

### Nghiệm thu và đầu ra

- Counts/masks khớp cached scores, đúng IDs và strict threshold.
- Bảng theo strata, hình overlap và rank/score distribution.
- Dự kiến: `fusion_overlap_per_run.csv`, `fusion_rescue_loss.csv`, `fusion_overlap_summary.csv`, `fusion_findings_en.md`.

## 6. Gói 2: M6 calibration có kiểm soát thống kê (P0)

### Thiết kế đề xuất

- Giữ scoring function, preprocessing và weights cố định trước khi dùng calibration.
- Kiểm tra lịch sử sử dụng tập calibration/certification. Bảo đảm confidence chỉ được viện dẫn khi việc lựa chọn score/weights/policy không dùng tập đó theo cách thích nghi; nếu điều kiện không đạt thì lấy pool chứng nhận độc lập mới hoặc giới hạn kết quả ở phân tích hồi cứu.
- Ưu tiên một policy exact binomial order-statistic/tolerance, tương thích với rank scores có ties. Với mục tiêu alpha và sai số delta, chọn số exceedance cho phép bằng binomial-tail rule trước khi nhìn final; lấy order statistic tương ứng và giữ `score > tau`.
- Một phương án khác là chọn threshold trên tập selection rồi chứng nhận bằng CP trên benign set độc lập. Không lặp chỉnh threshold theo chính certification set rồi dùng lại CI như thể chưa lựa chọn.
- Dùng cận trên một phía 95% khi thiết kế yêu cầu một phía; phân biệt với CI hai phía dùng mô tả FPR final.
- Nếu bảo đảm đồng thời, xác định số endpoint thực và điều chỉnh delta theo một thủ tục đã chốt. Không tự coi 95% pointwise là 95% cho toàn bộ bảng.
- Báo trade-off recall khi threshold bảo thủ hơn. Calibration đổi operating point; không tự cải thiện ranking/pAUC nếu score không đổi.

### Tích hợp và kiểm thử sau duyệt

- Không viết đè semantics `threshold()` toàn hệ thống. `revision/low_fpr.py` đang dùng hàm này cho empirical FPR cap; hai mục đích phải tách rõ.
- Version policy mới, lưu confidence/target/n/calibration-source/hash/operator. `Detector.load` hiện kiểm tra cứng `COMPONENT_VERSIONS`, nên phải giữ khả năng tái lập bundle v1 và có đường đọc policy mới rõ ràng.
- Xuất thresholds/bundles mới riêng; calibrate comparators theo cùng quy tắc tương ứng.
- Kiểm thử coverage/design bằng dữ liệu tổng hợp sau duyệt, cùng các trường hợp ties, zero/all exceedances, n nhỏ, NaN và score biên. Đó là kiểm thử phương pháp; kết quả benchmark thật vẫn phải báo riêng.
- Audit final một lần theo protocol khóa; báo count/n, FPR, CI và số cấu hình vượt 1% theo method/dataset. Không chỉnh final để ép số vượt về 0.

Đầu ra dự kiến: `calibration_policy.json`, `calibration_comparison_per_run.csv`, `final_fpr_ci.csv`, `fpr_exceedance_summary.csv`, ghi chú giả định và tương thích bundle.

## 7. Gói 3: M5 baseline raw-feature IF/LOF/kNN (P0)

### Công việc

- Fit các novelty detectors trên đúng 500 benign reference records; calibration trên 2.000 benign riêng; cùng IDs/cohort với proposed method.
- Chốt preprocessing bằng dữ liệu được phép trước final. Kiểm tra scale của size/timestamp/count/hash; không để khoảng cách bị một thang đo lớn chi phối. Mọi scaler/transform phải có fit scope và version.
- Định nghĩa rõ kNN anomaly score và chiều điểm; với LOF dùng novelty mode cho đầu vào mới, không lấy nhãn training mặc định thay calibration ngoài.
- Có cấu hình full-feature và cấu hình top-k được khai báo trước nếu chọn làm. Top-k thuần raw không ngầm dùng SHAP; nếu dùng SHAP để chọn thì ghi thành baseline có attribution riêng.
- Pilot kỹ thuật một cấu hình mỗi schema để kiểm shape, score direction, runtime và fairness trước khi mở cả 54 cấu hình.
- Cache fit/score dùng chung khi thật sự cùng schema/reference/preprocessing, nhưng vẫn giữ từng trigger/mask/model của từng run.

### Nghiệm thu và đầu ra

- Có scores từng mẫu, threshold provenance, FP/TP/count/n, TPR/FPR và standardized pAUC đúng định nghĩa.
- Báo cả calibration operating point và retrospective comparison riêng; bảo toàn ties.
- Bảng bao phủ 54 attempted configurations, đồng thời tách confirmed restricted/Cross và failed runs.
- Dự kiến: `raw_baseline_protocol.json`, `raw_baseline_per_run.csv`, `raw_baseline_summary.csv`, `raw_baseline_scores/`.

## 8. Gói 4: M5 rarity và baseline ba view (P1, cần chốt phạm vi bổ sung)

### Rarity trong phân công

- Định nghĩa `legacy_rare` đúng code: chọn feature bằng mean absolute SHAP trong pool được phép, rồi chọn giá trị có count thấp với tie-break đã định nghĩa. Tên hàm không phải toàn bộ thuật toán.
- Xây rarity detector từ benign reference, không được đọc giá trị trigger/attack manifest hoặc chọn feature theo final attacks.
- Chốt cách xử lý binary/categorical/count/continuous/hash, smoothing và binning. Không coi mọi continuous value chưa thấy là bằng chứng mạnh như nhau.
- So cùng dữ liệu, calibration và metric; cho phép rarity thắng proposed method.

### Baseline thầy yêu cầu nhưng MD bỏ sót

PDF trang 4 yêu cầu SHAP gộp thành vector ba view, dùng IF hoặc Mahalanobis. Đề xuất bổ sung một baseline ba chiều có định nghĩa mass/normalization rõ. Nếu dùng covariance, có xử lý suy biến/regularization; fit chỉ bằng reference.

Đầu ra dự kiến: `rarity_protocol.json`, `rarity_per_run.csv`, `view3_baseline_per_run.csv`, bảng đối chiếu raw/input rarity/SHAP-view/proposed. Việc triển khai baseline ba view chỉ nằm trong phạm vi sau khi người dùng duyệt bổ sung.

## 9. Gói 5: M2 phân tầng, bootstrap và Recall-ASR (P1)

### Công việc

- Đưa bảng dataset x family x rate lên trước macro mean; báo attempted, confirmed, số seed và mẫu số positives của từng nhóm.
- Scatter một điểm mỗi run, màu theo family/rate và ký hiệu confirmed/failed. Tách dataset; run không có successful positives nhận NA đúng định nghĩa, không tự điền recall 0.
- Báo tương quan mô tả trong strata khi đủ quan sát; không biến tương quan Recall-ASR thành quan hệ nhân quả.
- Phân biệt CI theo source-ID với model cố định (đã có) và CI theo training run/seed (cần bổ sung).
- Bootstrap seed-cluster giữ các cell liên quan trong cùng seed; giữ strata/weights đã chốt. Khi so method A-B, dùng paired resampling. Nếu bổ sung source resampling, cùng source IDs phải đi cùng nhau qua model.
- Công bố estimand, đơn vị cluster, n run/n seed/n source, RNG và số lần lặp. Chỉ có ba seed ở nhiều strata nên CI phải kèm per-seed/range/SD và giới hạn; tăng số bootstrap draws không tăng số cluster.

### Nội dung phải bàn giao cho người sửa paper

- Abstract cần nói rõ 9/12 confirmed EMBER2024 configurations thuộc Cross và detector rất yếu trên cohort này.
- Không gộp 49,82% mean recall với ASR49,82% của seed71; gắn nhãn metric/cohort rõ.
- Dự kiến: `stratified_results.csv`, `clustered_ci.csv`, `paired_method_differences.csv`, `recall_asr.csv`, hình scatter và ghi chú EN về phạm vi CI.

## 10. Gói 6: M4/M7 Public-Shadow độc lập (P1; kiểm dữ liệu ngay từ P0)

### Điều kiện đầu vào

- Nguồn chính thức: `bodmas.npz`, labels và `bodmas_metadata.csv` có IDs/hash/timestamp.
- Kiểm tra feature order, hashing/preprocessing và LIEF/schema V2. Cùng 2.381 chiều chưa đủ xác nhận tương thích. Không pad sang V3.
- Tập train phải có cả benign và malware, dedup SHA256 trong public data và với các role EMBER liên quan. Lưu danh sách overlap/loại bỏ.
- Có thể lấy bộ vectors công khai sau khi duyệt; không cần tải hoặc chạy malware binaries để train comparator này.

### Thực hiện sau duyệt

- Khóa public train/validation split và training seeds độc lập trước đánh giá. Pilot ngân sách 20K; cân nhắc thêm 50K theo protocol đã chốt và runtime.
- Không tái dùng clean evaluator/eligibility model; chỉ đổi seed trên cùng fit không giải quyết đầy đủ vấn đề độc lập.
- Giữ eligibility masks gốc cố định. Comparator score dự kiến: `max(0, p_public_shadow - p_main)`.
- Có thể dùng cùng benign calibration EMBER để công bằng về calibration access, nhưng phải nói rõ public độc lập ở phần training và không dùng làm evaluator.
- Đánh giá clean-classification utility và detector TPR/FPR/pAUC trên EMBER2018. Giữ cả kết quả bất lợi do source/time shift.
- Đề xuất đưa Shadow 200K cũ xuống phụ lục khi người sửa bài tích hợp; Public-Shadow/Shadow độc lập mới là đối chiếu chính cho M4/M7.

Đầu ra dự kiến: `public_shadow_data_manifest.json`, `public_overlap_audit.csv`, protocol/model mới, `public_shadow_per_run.csv`, `public_shadow_utility.csv`, bảng nguồn lực.

## 11. Các việc bổ sung cần phân người nhận

| Việc | Đề xuất trách nhiệm/phụ thuộc |
|---|---|
| Audit hai random controls cùng 169 poison | Thắng kiểm mask/seed/index layout và counts; người biên tập cập nhật diễn giải |
| Sửa công thức, đánh số và vị trí | Thắng bàn giao công thức/notation chuẩn; người biên tập sửa Word/LaTeX và kiểm bản render |
| Threat model M3, thêm selector/poisoning-time attack | Nhóm phải chốt hướng và người thực hiện; không coi adaptive 32 query hiện tại đã giải quyết |
| Binary feasibility M8 | Cần người phụ trách binary hoặc quyết định thu audit còn một đoạn; không đưa vào train Public-Shadow |
| SentiNet/tên bài, related work M9 | Người phụ trách literature và trưởng nhóm |
| Dấu gạch nối, Abstract, phụ lục D, LLM disclosure, repo ẩn danh, trích dẫn Android | Người biên tập và trưởng nhóm, dùng số/phương pháp Thắng bàn giao |

**Lưu ý audit 169:** code hiện tại thay thế 4.000 trong 100.000 benign fit, không thêm 4.000 thành 104.000. Nếu xác nhận đúng mask/pool, kỳ vọng random removal là `5.000 x 4.000 / 100.000 = 200`, khác phép minh họa ~192 của PDF. Phải giải trình 169 bằng dữ liệu/seed/index thực, không đổi số 169 thành kỳ vọng. Góp ý cần kiểm tra việc hai dataset có cùng 169 vẫn giữ nguyên giá trị.

## 12. Lịch đề xuất tính từ lúc duyệt

| Mốc | Công việc | Điều kiện nghiệm thu |
|---|---|---|
| Ngày1-2 | Chốt DoD/protocol/M3; kiểm caches; xác định nguồn BODMAS; M1 và bảng phân tầng ban đầu | Các quyết định dữ liệu/cohort/confidence rõ; danh sách dependency có người nhận |
| Phần còn lại tuần 1 | Overlap đầy đủ, audit 169, thiết kế và pilot calibration version mới | Giải thích được rescue/loss; policy không rò final; giữ tương thích primary |
| Tuần 2 | Pilot rồi chạy raw baselines, rarity/view3 theo phạm vi duyệt; train Public-Shadow khi đầu vào hợp lệ | Pilot đạt kiểm kỹ thuật/fairness trước mở rộng; có scores/counts/provenance |
| Tuần 3 | Hoàn tất các lượt đã khóa, clustered CI/scatter, kiểm tái lập và bàn giao | Bảng/figure từ CSV gốc; scope và các mục chưa đạt được ghi rõ |

Đây là dự kiến theo lộ trình 3 tuần của file phân công, không phải cam kết thời gian hoàn thành khi chưa đo runtime hoặc chưa có dữ liệu. M3 poisoning-time/binary validation nếu nhóm chọn làm có thể mở rộng scope đáng kể và cần lịch riêng.

## 13. Gói nghiệm thu cuối phần Thắng

1. Protocol và input/model/cache manifest, log và các cấu hình/thất bại đều được giữ.
2. CSV từng run cùng count/n, bảng phân tầng và summaries; định nghĩa rõ positives, confidence và clustering.
3. Hình overlap, recall-ASR, FPR/CI và bảng baseline/Public-Shadow phù hợp dữ liệu thực.
4. Các đoạn Methods/Results/Limitations tiếng Anh và hướng dẫn diễn giải tiếng Việt để bàn giao người sửa paper.
5. Bảng phản hồi M1/M2/M4/M5/M6/M7: đã làm, bằng chứng, giới hạn hoặc dependency chưa hoàn thành.
6. Kiểm tra hồi quy đảm bảo bundles cũ tái lập; không gọi test phần mềm là bằng chứng detector hiệu quả.

## 14. Ranh giới chờ duyệt

- Đề xuất duyệt 6 gói chính với DoD thống kê/thực nghiệm đã sửa.
- Đề xuất bổ sung baseline 3 view, bảng phân tầng, audit 169 và bàn giao công thức. Nhóm cần xác nhận người nhận các mục ngoài phần Thắng.
- Chưa coi M3 đã được chốt; khuyến nghị không mở dynamic fusion hoặc adaptive poisoning-time khi chưa thống nhất threat model/tuning data.
- Chỉ sau khi người dùng duyệt mới tạo/sửa code, lấy dữ liệu public, chạy pilot, train/evaluate hay hiệu chỉnh thresholds mới. Không tự triển khai vì file phân công có câu mệnh lệnh.

## 15. Nguồn phương pháp đã đọc để lập kế hoạch

- [SciPy: Clopper-Pearson exact confidence interval](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html).
- [NIST: exact binomial confidence limits](https://itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbici.htm).
- [Bates et al.: Risk-Controlling Prediction Sets](https://arxiv.org/abs/2101.02703).
- [scikit-learn 1.6.1: LOF novelty scoring](https://scikit-learn.org/1.6/modules/generated/sklearn.neighbors.LocalOutlierFactor.html).
- [BODMAS: dữ liệu vectors/labels, schema và metadata chính thức](https://whyisyoung.github.io/BODMAS/).

Các nguồn này phục vụ thiết kế; chưa có kết quả của phương pháp mới trong kế hoạch này.
