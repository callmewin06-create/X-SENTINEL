# Bàn giao triển khai nhiệm vụ Thắng — góp ý G4 v2

Người dùng đã duyệt triển khai kế hoạch ngày 30/10/2026. Kết quả mới nằm trong `outputs/teacher_revision_v2_thang_2026_10_30/`. Không thay main models, bundle, threshold đang dùng ở web; không commit/push. Các kết quả mới là tái phân tích và bổ sung comparator trên benchmark đã quan sát, không phải validation độc lập mới.

**Đã hoàn tất và kiểm tra:** 54/54 raw/rarity, 54/54 view3, 27/27 Public-Shadow; 31 kiểm thử phần mềm đạt, smoke test policy trên cả hai schema đạt, counts/IDs được đối chiếu lại từ saved scores và hash nguồn gốc không đổi. Xem `outputs/teacher_revision_v2_thang_2026_10_30/handoff/results_for_paper_en.md` để lấy bảng Results cuối. Hoàn tất sáu gói được giao không đồng nghĩa đã giải quyết hết chín góp ý của thầy.

## Cách đọc kết quả

- `frozen_audit/`: M1 overlap và M6 threshold; đủ 54 cấu hình. `manifest.json` kiểm hash đầu vào trước/sau.
- `calibration_sidecars/`: 108 policy files = 54 Full bundles × 2 policies; mỗi file chứa ngưỡng cho 7 methods, bao gồm Reduced/Full. `CalibratedBundle` là đường dùng thử riêng; không ghi đè bundle và không tích hợp mặc định vào web.
- `raw_baselines/`: M5 IF/LOF/kNN full và top32, rarity; mỗi cell có scores và result để tiếp tục khi gián đoạn. `complete.json` là mốc hoàn tất, không suy ra hoàn tất từ việc có script.
- `view3/`: IF trên ba tổng signed-SHAP chuẩn hóa. `shard_*_complete.json` ghi hoàn tất từng phần; coverage cuối nằm trong `handoff/completion_audit.json`.
- `statistics/`: M2 phân tầng, seed-cluster CI và Recall-ASR; CI có ít nhất hạn chế nghiêm trọng là chỉ ba seed mỗi stratum.
- `public_shadow/`: M4/M7 mô hình public độc lập 20K, validation 5K, kiểm SHA256 trùng và 27 cell EMBER2018; không áp dụng sang V3.
- `random_control_audit.json`: giải thích số 169 bằng IDs thực.
- `handoff/`: bảng so sánh chung, coverage, paired CI. Kiểm coverage trước khi lấy số vào manuscript.

## Các quyết định khoa học

1. **Không tự đổi fusion.** Phân tích EMBER2024 restricted-confirmed tại operating point final-FPR-cap cho thấy BGS bắt riêng 669 lượt mẫu, trong khi fusion làm mất 3.550 lượt VMC vốn bắt được. Đây là tổng lượt qua ba model, không phải 16.483 file độc lập. Cần trình bày VMC là tín hiệu mạnh hơn trong cohort này; chưa có cơ sở chọn dynamic weights từ final.
2. **Không hứa FPR final luôn dưới 1%.** Policy exact binomial-tolerance được thêm riêng, giữ strict `>`, không sửa semantics `threshold()` cũ. 378 endpoint = 54 cell × 7 phương pháp cached. Bảo đảm đồng thời minh họa chỉ dành cho họ này, không mở rộng ngầm sang các baseline mới.
3. **Lịch sử calibration chưa chứng minh độc lập.** Vì vậy các số ngưỡng mới được ghi là retrospective recalibration. Lý thuyết coverage yêu cầu score cố định và benign calibration IID độc lập; không được lấy thí nghiệm hiện tại làm chứng nhận thực địa.
   Roles hiện tại đặt calibration trong source partition `train`, còn final trong `test` ở cả hai schema. Việc tách partition không tự chứng minh hai phân bố khác nhau, nhưng cũng không chứng nhận giả định cùng phân bố. Bảo đảm tolerance không áp dụng tự động khi có source/time shift.
4. **Không bắt baseline phải thua.** Raw, rarity, view3 và Public-Shadow dùng cùng masks successful-eligible. Kết quả bất lợi cho proposed method phải giữ.
5. **Public-Shadow độc lập ở training.** Nguồn BODMAS có 7 ID không phải SHA256 và 9 SHA256 trùng roles EMBER: đã loại cả 16 trước chia train/validation. Chỉ một model 20K/seed mới; 27 lượt áp dụng không phải 27 public models độc lập. Phân tích nhiều seed/ngân sách public còn là hướng mở rộng, không được tự nhận đã làm.
   Chín overlap gồm 8 mẫu ở fit và 1 ở development. Dedup chỉ theo SHA256 chính xác, chưa kiểm near-duplicate hoặc family overlap. BODMAS validation dùng chia ngẫu nhiên cân bằng lớp, không phải temporal holdout.
6. **169 không phải số copy nhầm.** Reconstructed masks khớp IDs lưu. Hai dataset có cùng vị trí poison và random removal trong pool benign 100.000 mẫu. Kỳ vọng là 200; quan sát 169. Không coi hai random controls này là hai lần rút vị trí độc lập. Hypergeometric lower-tail ~0,01062 chỉ là mô tả dưới giả định rút ngẫu nhiên cố định, không phải bằng chứng gian lận hay sai số liệu.

## Kết quả đã xác minh trước khi tích hợp manuscript

| Nội dung | Kết quả | Cách diễn giải |
|---|---|---|
| FPR >1% trên 108 Reduced/Full endpoints | Ngưỡng cũ: 6/108; tolerance pointwise: 0/108 | Chỉ là quan sát của final hiện có, không bảo đảm 0 vi phạm trong tương lai |
| FPR >1% trên 378 endpoints của 7 cached methods | Cũ: 79; pointwise: 13; family-adjusted: 3 | Cần giữ cả endpoint vượt; họ 378 không bao gồm baseline mới |
| EMBER2024 restricted Reduced, ngưỡng cũ → tolerance pointwise | Recall 48,33% → 38,53%; FPR 0,777% → 0,407% | Đổi lấy giảm FPR bằng mất recall; không phải cải thiện ranking |
| Public-Shadow20K, BODMAS validation → EMBER2018 final | Accuracy 99,50% → 83,06% | Cross-source utility suy giảm; chưa chỉ ra duy nhất nguyên nhân |
| EMBER2018 restricted-confirmed tại empirical final-FPR-cap | Public-Shadow20K recall 16,17%; Reduced 37,69%; Full 44,72% | Một public model 20K, 12 suspicious-model cells; không suy rộng thành mọi public-data defender |

Abstract và bảng kết quả phải giữ sự thật: EMBER2024 có 12 cấu hình confirmed, trong đó 9 thuộc Cross. Reduced gần như không bắt được cohort Cross. Không chỉ đưa ba cấu hình restricted-confirmed vào câu kết luận chung cho EMBER2024.

## Methods — đoạn tiếng Anh để người biên tập dùng

We added reference-only input-space novelty baselines using Isolation Forest, Local Outlier Factor in novelty mode, and mean 20-nearest-neighbor distance. Each baseline was fitted on the same 500 benign reference records. Input preprocessing used a signed log-one-plus transform and reference-fitted standardization; constant reference coordinates were removed for these controls. We evaluated both all remaining coordinates and the 32 largest reference log-variance coordinates, without using SHAP or attack metadata for feature selection. A marginal rarity baseline used exact categories for coordinates with at most 20 reference values and reference quantile boundaries otherwise, with Laplace smoothing and the mean of the ten largest marginal surprisals. Quantile bucket assignment uses left insertion: values at the reference minimum share the lower bucket, and values above the reference maximum enter the upper bucket. These choices were fixed before scoring the benchmark for the new baselines.

The legacy_rare attack selector first restricts candidate coordinates to the permitted schema and view geometry, excluding coordinates constant in the selection pool. Within each view quota, it selects coordinates by descending mean absolute SHAP, breaking ties by coordinate index. For each selected coordinate, it chooses the least frequent observed value; ties are broken by the smaller mean signed SHAP among rows carrying that value, then by the smaller numeric value. The marginal rarity detector does not access this selector's manifest or selected trigger values.

For the view-level comparator, we formed a three-dimensional vector by summing signed native TreeSHAP values within each view and dividing each sum by total absolute attribution. We fitted an Isolation Forest on the 500 benign reference vectors. All detectors used the original successful-eligible masks; empirical calibration operating points and retrospective final-pool FPR-cap comparisons are reported separately.

We additionally evaluated a strict-exceedance binomial tolerance threshold. For calibration sample size n, target alpha, and failure probability delta, the allowed exceedance count k is the largest integer satisfying P[Binomial(n, alpha) <= k] <= delta. The threshold is the (n-k)-th ascending calibration order statistic. Ties are conservative under a strict decision rule. This construction requires an independently fixed scoring rule and an IID benign calibration sample. Because previous adaptive use of the existing calibration data cannot be excluded, the present recalibration results are retrospective and are not claimed as independent population-FPR certification.

The public-data Shadow was trained independently on 20,000 class-balanced BODMAS feature vectors using a new seed and the original 500-round training configuration. We excluded public records overlapping any EMBER role by SHA256 and excluded records without valid SHA256 identifiers. A separate 5,000-record BODMAS validation set was not used to select training rounds. Eligibility remained defined by the original frozen evaluator. The comparator score was the positive part of the public model's malware probability minus that of the suspicious classifier. This experiment applies only to the compatible EMBER V2 feature schema; cross-source extraction and temporal differences remain limitations.

We report dataset-by-family-by-rate results before aggregate means. Within each stratum, paired bootstrap resampling uses the training seed as the cluster and retains the same draw across methods. The intervals are descriptive and unstable with only three seed clusters; more bootstrap repetitions do not increase the effective number of independent training runs. No pooled cross-stratum interval is inferred from these separate intervals.

Here, the seed cluster refers to the suspicious classifier and attack configuration. The reference-only raw and rarity fits are shared across cells of a schema, and the Public-Shadow model is trained only once. These intervals therefore do not quantify uncertainty from independently refitting the raw baseline or public model. All source records remain fixed; source-sampling uncertainty is a separate analysis.

## Công thức và notation bàn giao

Đặt `phi_j(x)` là signed TreeSHAP, `A(x)=sum_j |phi_j(x)|`, các view S/B/M phân hoạch feature. Nếu `A<=1e-9`, đặt các tỷ lệ bằng 0.

- `VMC(x) = max_v [sum_(j in v) |phi_j(x)| / A(x)]`.
- `BGS(x) = (1-p_main(x)) × max(sum_(j in B) phi_j(x),0) / A(x)`.
- `BPG(x) = max(p_behavioral(x)-p_main(x),0)`.
- `r_m(s) = #{z in reference: score_m(z)<=s}/n_reference`.
- `Reduced(x) = [r_VMC(VMC(x))+r_BGS(BGS(x))]/2`.
- `Full(x) = [r_VMC(VMC(x))+r_BPG(BPG(x))]/2`.
- `View3(x) = (sum_S phi, sum_B phi, sum_M phi)/A(x)`.
- Quyết định detector: `score > tau`; phân loại malware: `p_main >= 0.5`.

File size và section thuộc **Structural**, không phải Metadata. Behavioral là các đặc trưng static imports/exports, không phải quan sát hành vi runtime. Đánh số phương trình và kiểm render do người biên tập manuscript thực hiện.

## Phần chưa được tự coi là đã giải quyết

- M3: nhóm chưa chốt thu hẹp threat model hay thêm adaptive poisoning-time attack; bounded inference-time optimizer không thay thế việc này.
- Phần M5 ngoài sáu task đã chia: chưa chạy benchmark tấn công mới với toàn bộ original Severi selectors. Code `signed_shap_conditioned` hiện có là adaptation với ràng buộc geometry; không được coi riêng việc tồn tại code là đã đáp ứng yêu cầu thực nghiệm này.
- M8: chưa bổ sung binary feasibility experiment. Không tuyên bố sửa nhiều section là bất khả thi.
- M9 và biên tập: SentiNet citation/name, abstract, hyphenation, bỏ Appendix D, disclosure, ẩn danh cần người nhận riêng.
- Chưa có benign certification pool mới hoặc benchmark chưa dùng; không tuyên bố coverage thực địa hay khắc phục mọi dataset shift.
- Baseline/threshold mới là nghiên cứu trong namespace riêng. Web đang phục vụ bundle cũ; cập nhật web/manuscript phải dùng đúng bảng và policy tương ứng, không đổi tên ngưỡng cũ thành v2.

## Chạy lại / tiếp tục

Từ thư mục project, dùng `.venv\Scripts\python.exe`:

```powershell
.\.venv\Scripts\python.exe scripts/run_raw_baselines_v2.py
.\.venv\Scripts\python.exe scripts/train_public_shadow_bodmas.py
.\.venv\Scripts\python.exe scripts/run_view3_baseline_v2.py --shard 0 --shards 3
.\.venv\Scripts\python.exe scripts/run_view3_baseline_v2.py --shard 1 --shards 3
.\.venv\Scripts\python.exe scripts/run_view3_baseline_v2.py --shard 2 --shards 3
.\.venv\Scripts\python.exe scripts/bootstrap_analytics.py
.\.venv\Scripts\python.exe scripts/summarize_thang_v2.py
```

Không chạy hai tiến trình cùng shard. Không sửa protocol sau khi có kết quả rồi resume như cũ. Script overlap yêu cầu thư mục output mới để không ghi đè audit. Khi đổi phương pháp/preprocessing, tạo namespace mới và giữ kết quả cũ.
