# Kế hoạch hoàn thiện M3 và chuẩn bị bài JSTIS

**Cập nhật 10/11/2026:** train, fresh held-out evaluation, summary, arithmetic/hash audit và ghép kết quả vào Word đã hoàn tất. Xem [kết quả và phản hồi17mục](../reviews/JSTIS_COMPLETED_RESULTS_2026_11_10.md). Layout JSTIS cuối/hồ sơ tác giả/upload vẫn còn. Các mô tả “chưa triển khai” bên dưới ghi lại trạng thái tại thời điểm duyệt kế hoạch; không dùng chúng thay cho trạng thái mới.

Ngày lập và rà soát: 09/11/2026. Trạng thái: **định vị nghiên cứu đã được người dùng chốt; kế hoạch đã rà soát, chưa triển khai code, train model hoặc sửa manuscript trong lượt rà soát này**. Việc đồng ý giữ hướng nghiên cứu không được diễn giải thành lệnh bắt đầu batch training.

## 1. Căn cứ và lựa chọn định vị

Nguồn chính là PDF sáu trang `G4 Hoan thien nop ở JSTIS .pdf` do người dùng cung cấp, SHA256 `8dae52e52fa5c850d645d0939a9e51758ad78b4cfca5403f16750d47e3894ee4`. Đây là góp ý chuẩn bị nộp của thầy; không tự coi là quyết định phản biện chính thức từ JSTIS.

Ba vấn đề thầy ưu tiên ở mục 5 là: thiên vị trong thiết kế tấn công (§3.2), headline dùng ngưỡng hồi cứu (§3.4), và khoảng cách feature-space/problem-space (§3.5). Mục 7 liệt kê bảy yêu cầu phải có câu trả lời cụ thể. Hoàn thiện M3 một mình chưa đáp ứng toàn bộ PDF mới.

**Đã chốt hướng evaluation/negative results**, giới hạn ở LightGBM PE classifiers. Không đặt điều kiện nghiệm thu là phải tìm ra một fusion vượt baseline. Tiêu đề dự kiến: **Evaluating Feature-View Attribution Concentration for Backdoor Triage in LightGBM PE Classifiers**. Có thể giữ X-SENTINEL làm tên framework trong thân bài; không dùng tên đó để ngụ ý một sản phẩm phát hiện đã chứng minh hiệu quả phổ quát.

Câu hỏi nghiên cứu được giữ nhất quán: (RQ1) concentration và conflict signals có giá trị trong điều kiện nào so với đối chứng cùng quyền truy cập; (RQ2) selector, allowed domain và adaptive poisoning-time làm thay đổi kết quả ra sao; (RQ3) collateral changes trên binary ảnh hưởng tín hiệu thế nào trong audit giới hạn. Hướng này không chuyển sang phát hiện hành vi runtime, không mặc định Behavioral mạnh nhất và không phát triển một defender mới trong vòng sửa này.

Giữ 54 cấu hình primary và lịch sử pilot nguyên vẹn. Mọi nghiên cứu mới có protocol, dữ liệu và thư mục riêng; không thay kết quả cũ bằng kết quả mới mà bỏ dấu vết. Tạo manifest trước/sau cho models, triggers, predictions và result files của primary54; thay đổi hash ngoài danh sách dự kiến phải dừng và điều tra.

## 2. Trạng thái thực tế trước khi sửa

| Hạng mục | Đã có | Còn thiếu |
|---|---|---|
| M3 poisoning-time | Pilot V3/seed17/40K fit, bốn trigger được train lại; có VMC-aware selection | Proposal chưa dùng feedback; chưa có formal sequential search và held-out evaluation mới |
| Pilot hai objective | Cả ASR-only/VMC-aware chọn candidate3 | Không chứng minh lợi ích tăng thêm của VMC-aware; đây không phải lý do để tăng budget đến khi hai nhánh khác nhau |
| Selector | `legacy_rare` và helper `signed_shap_conditioned` | Chưa có benchmark đủ ba cấu hình Severi được chốt fidelity và cùng điều kiện |
| Abstract | 37,69%/52,82% ở retrospective final-FPR cap | Cần đưa calibrated-threshold results lên chính |
| Binary C2 | Hai fixture, tám variants, đủ target; Wine20/20 và Mono20/20 PASS; có raw logs | Chưa có quantitative SHAP/VMC comparison giữa target-only vector và binary edit; chưa có functioning-malware backdoor evaluation |
| Word hiện tại | Bản 04/11 đã anonymous và cập nhật V-L | Nhận xét M8 trong PDF dựa trên snapshot cũ; cần trả lời bằng bằng chứng mới và giữ đúng giới hạn |
| VMC_norm/MAX | Có đề xuất và một số exploration MAX lịch sử | Chưa có held-out validation cho hai mở rộng này như yêu cầu mới |
| JSTIS | Đã xác minh website đúng là isj.vn | Cần đọc template thực tế, đổi format và chuẩn bị hồ sơ riêng cho review/author information |

Trong kế hoạch này, **M3** là hạng mục phản biện adaptive poisoning-time; `M3_view_mass` trong code là tên điểm VMC. Hai nghĩa không được dùng thay thế nhau.

## 3. Phạm vi đề xuất để chốt trước khi triển khai

| Tham số | Phương án đề xuất |
|---|---|
| Dataset | EMBER2018 V2 và EMBER2024 V3 |
| Seeds | 17, 29, 43; cùng một split mới mỗi dataset, thay model/search seed |
| Fit | 200.000 records cân bằng mỗi dataset |
| Learner | LightGBM 500 rounds; hyperparameters primary giữ cố định |
| Poisoning | Clean-label, sửa 2% toàn bộ fit = 4.000 benign records; poison IDs cố định trong từng dataset–seed |
| Static selectors | Ba cấu hình Severi, hai allowed domains, K=10, không ép quota view |
| Adaptive | A10 domain, hai trajectory ASR-only/VMC-aware, 16 logical candidate evaluations/arm gồm initialization |
| Attacker access | Biết fit/selection/search data, learner và công thức VMC; được mô phỏng retraining và TreeSHAP; không thấy defender reference/calibration/confirmation/final |
| Defender và đối chứng | VMC, Reduced, TADR và raw-kNN-top32 cùng reference/calibration mới; Full là phân tích phụ có clean Behavioral model |
| Mở rộng | Đưa VMC_norm và MAX sang Future Work thay vì mở thêm một nhánh tối ưu phương pháp |
| Cohort nhỏ | Giảm mức khẳng định và báo đủ attempts; không hứa mở rộng được số run confirmed chỉ bằng chạy thêm |

Các con số 16, K10, 200K và ba seed là **thiết kế nhóm đề xuất**, không phải nguyên văn yêu cầu của thầy. Nghiên cứu là bounded feature-space study, không thay thế M8.

## 4. Đợt A — sửa luận điểm và phân tích cache trước

### A1. Sửa Abstract, Conclusion và cách gọi operating point

Tái tính từ `outputs/teacher_revision_v2_thang_2026_10_30/handoff/all_methods_per_run.csv` và records primary, giữ macro-averaging như bản gốc:

- Reduced calibrated-threshold recall: **35,75%** trên 12 restricted-confirmed cells EMBER2018; final benign FPR khoảng **0,522%**.
- EMBER2024: **48,33%**, ba restricted-confirmed cells; final benign FPR khoảng **0,777%**.
- Viết “threshold calibrated for a nominal 1% FPR target”; không viết observed FPR luôn bằng hoặc dưới 1% cho mọi detector/run.
- Giữ 37,69%/52,82% trong phân tích **retrospective final-FPR cap**, không làm headline triển khai.
- Giữ Cross-view failure và số cohort trong Abstract/Conclusion. Không dùng một kết quả restricted để đại diện toàn bộ 54 cấu hình.

**Nghiệm thu:** một script tái tạo bảng từ cache, đối chiếu count/n và averaging; không chọn lại threshold từ final. Không train model cho bước này.

### A2. Cohort và confirmation sensitivity

Giữ model, selector và detector thresholds. Lọc bằng **confirmation metrics**, không phải final ASR. Dùng grid min confirmation ASR **0,40 / 0,50 / 0,60**; giữ min eligible1000, net paired gain0,20 và clean-accuracy drop<0,005.

Audit sơ bộ cho thấy số V3 restricted-confirmed cells lần lượt có thể là 8/3/0; đây là số cells, chưa phải recall sensitivity hoàn chỉnh. Phải tái tạo đầy đủ trước khi viết bài. ASR47,19% mà thầy dẫn là final summary; không dùng nó thay confirmation ASR để xác nhận attack.

Báo số attempts/confirmed theo family, rate, seed và calibrated recall/FPR tương ứng; giữ cutoff0,50 là protocol cũ. Bảng sensitivity là post-review diagnostic, không dùng để chọn cutoff có kết quả đẹp nhất. Ba model seeds không trở thành hàng nghìn thí nghiệm độc lập nhờ bootstrap samples.

### A3. Full, Shadow, ties và FPR tails

- Đưa clean-budget analysis vào main Discussion. Tách Shadow200K tái sử dụng eligibility model thành **coupled control**, không trình bày như independent baseline ngang hàng. Public-Shadow20K là model khác, chỉ có bằng chứng V2 hiện tại.
- Không viết Full luôn hợp lý nhất ở ngân sách≤5K: cache cho thấy V3/5K Shadow đã hơn Full. Báo tradeoff cùng ngân sách và đúng operating point.
- Từ reference/calibration/final-score caches, tính tỷ lệ rank=1, số unique ranks/fused scores, ties tại threshold và rank distributions trong nhóm mất phát hiện do fusion.
- R_ref có bước1/500, còn threshold thực được chọn từ calibration2000 và score fusion. Không diễn đạt như thể thuật toán đơn giản lấy điểm thứ năm từ reference để đặt threshold.
- Kiểm 6/54 Full FPR exceedances, worst227/10000=2,27%; so calibration/final score tails và input mix khi có metadata. Chỉ gọi là diagnostic association; chưa gán nguyên nhân chắc chắn là distribution shift hoặc ties.

### A4. Direct evasion và thời gian

- Từ cached paired predictions, tách clean-original eligibility, clean-trigger evasion, poisoned-trigger evasion, paired-new và paired-lost cho cả C/S/X.
- Bắt buộc có bảng coordinate/index/name/value/view liên quan tới clean-model evasion. Khóa một subset development theo ID trước phép chẩn đoán, giữ clean model cố định; so full trigger với các bản khôi phục từng coordinate về giá trị original và khôi phục theo nhóm view cho C/S/X. Báo delta clean evasion và paired case IDs, kể cả hiệu ứng tương tác khiến các delta không cộng được. Đây là counterfactual diagnostic trên tập đã khai báo, không train thêm và không dùng final để chọn coordinate. Mọi phép tính thêm trên final phải ghi rõ retrospective diagnostic và không dùng để tối ưu trigger.
- Công khai role split là random/stratified hay temporal theo code thật. Trích dẫn TESSERACT không tự biến split thành temporal validation; dùng ngày tháng metadata để mô tả nếu có.
- Microbenchmark40,5–97,8ms: chỉ giữ nếu lấy được hardware/runtime/thread/model/fixture provenance của đúng lượt đo. Không mượn hardware.json từ một benchmark khác. Đề xuất bỏ số này khỏi kết luận chính nếu chưa có provenance.

## 5. Đợt B — chuẩn bị dữ liệu và ba cấu hình Severi

### B1. Dữ liệu mới với ledger lịch sử

Không coi final cũ là mới chỉ vì script pilot không mở nó. Dựng exclusion ledger tập trung từ tất cả role IDs, pilot, fresh-validation cũ, public-shadow và các thí nghiệm fusion/latency đã dùng. Đặc biệt thêm `outputs/fusion_binary_latency_2026_10_20/final_pool/{dataset}/ids.npy`, bị bỏ sót ở audit trước.

Metadata audit hiện cho thấy còn đủ dữ liệu để dựng **một split mới mỗi dataset**. V2 còn khoảng140.880 benign/154.033 malware train; official test81.976/82.024. V3 còn khoảng1.052.451/1.054.945 train và257.940/258.000 test. Tính lại các số này ở implementation gate; đây là “new-to-known-local-history”, không bảo đảm chưa từng được nhóm quan sát ngoài các artifact đã kiểm.

Role đề xuất: Fit200K; Selection10K; Search/Development10K; Confirmation10K; Reference500 benign; Calibration2000 benign; Final20K. Fit, Selection, Search, Confirmation và Final cân bằng hai lớp; riêng Confirmation gồm5000/5000 và Final gồm10000/10000. Fit/selection/search/confirmation/reference/calibration lấy từ official train; final từ official test. Ba seed dùng cùng split để so sánh cặp, không cần ba fit datasets200K rời nhau.

V2 có source arrays đầy đủ. V3 cần metadata-first selection rồi bounded vectorization từ sáu archive đã có; không giải nén toàn bộ ~96,9GiB. Khóa source, parser, schema, ID manifests và luật duplicate/conflicting-label trước khi đọc dữ liệu evaluation. Dừng nếu overlap, schema sai hoặc không đủ lớp/số lượng.

Ledger phải xuất inventory đường dẫn+hash của mọi nguồn ID đã xét, exclusion reason, số bị loại theo nguồn/lớp và báo cáo overlap thực tế giữa mọi role. Chọn ID/label bằng metadata/SQLite trước khi materialize vectors. Không dùng nguyên `freeze_primary_splits`/`load_data` để cấp role mới nếu đường chạy đó mở source test X/y ngoài access policy. Steward chuẩn bị metadata có thể cần label để stratify; optimizer không được đọc label/vector của các role held-out. Kiểm SHA-disjoint không đồng nghĩa family-, group- hoặc time-disjoint; không gán các đặc tính chưa kiểm cho split.

Khóa luật xử lý schema/categorical values/parse-status trước chọn roles, dùng đồng nhất cho cả hai arm và mọi selector; báo số dòng bị loại theo lý do. Không thay luật sau khi thấy detector scores. Observed coordinate values không chứng minh tổ hợp vector là binary hợp lệ; R10/A10 vẫn là vector studies và ghi rõ tính khả thi problem-space chưa được xác lập.

### B2. Ba cấu hình nguyên tắc từ Severi

Thầy nêu tên các thành phần lựa chọn, không phải năm attack độc lập. Đề xuất đánh giá:

1. **Independent: LargeAbsSHAP × MinPopulation** — topK theo tổng absolute SHAP; mỗi value có exact population count nhỏ nhất.
2. **Independent: LargeAbsSHAP × CountAbsSHAP** — cùng feature selector; value tối thiểu `1/count + tổng absolute SHAP trên các hàng có value đó`.
3. **Greedy Combined** — chọn feature có tổng signed SHAP nhỏ nhất trong pool đã conditioning; chọn value theo `1/count + tổng signed SHAP`, giữ các hàng tương ứng rồi lặp.

Dùng cùng mixed selection10K và clean-model SHAP; không đổi sang benign-only cho một strategy. Giữ hệ số nguồnα=β=1, tổng SHAP, thứ tự conditioning và value-count semantics. Khóa upstream commit/hash; kiểm parity với code tác giả trên toy arrays, cả ties và cache. Tên class HistogramBin không có nghĩa được tự thay exact-value count bằng binning.

Đây là adaptations sang schema V2/V3; repo nguồn dùng2351 features. `legacy_rare` có quota/filter/tie riêng, không được đổi tên thành original Severi. `signed_conditioned` đã có một phần Combined nhưng wrapper hiện bắt geometry; cần wrapper/family mới, không gọi mọi trigger quota-free là Cross rồi bắt nó có đủ ba view.

Nguồn: [paper tác giả](https://www.usenix.org/system/files/sec21-severi.pdf), [feature selectors](https://github.com/ClonedOne/MalwareBackdoors/blob/main/mw_backdoor/feature_selectors.py), [attack runner](https://github.com/ClonedOne/MalwareBackdoors/blob/main/backdoor_attack.py).

### B3. Ma trận gọn để kiểm thiên vị selection/domain

| Domain | Allowed coordinates | Hình học |
|---|---|---|
| R10 | Versioned restricted pool, có biến thiên trên selection | K10, không ép quota view |
| A10 | Tất cả coordinate hợp lệ có biến thiên | K10, không ép quota view |

**3 configurations × 2 domains × 2 datasets × 3 seeds = 36 attempted static cells.** Chạy rate2%, learner500 rounds; giữ failures và unsupported conditioning. Kiểm đủK trước khóa protocol; không âm thầm nới pool khi thiếu feature hoặc hết conditioning rows.

Vì fit/pools/geometry của nghiên cứu mới khác primary54, không quy chênh lệch cũ–mới hoàn toàn cho selector. Các so sánh matched giữa selector/domain trong protocol mới mới hỗ trợ kết luận hẹp về hai yếu tố đó. Báo riêng benchmark cũ và follow-up mới, không gộp thành số run độc lập lớn hơn.

V2 restricted hiện17 gồm13Structural+4Metadata; V3 restricted hiện13 và toàn Structural. Vì thế nhánh R10/V3 vẫn mang ràng buộc một view dù không có quota. Nhánh A10 mới tháo ép Structural; báo số coordinate và attribution mass từng view thực đo, không ép A10 phải dùng cả ba view.

Có thể thêm12 fits `legacy_rare_globalK10_ablation` nếu cần kết luận riêng về khác biệt local selector/tie trong cùng thiết lập quota-free. Nó không cô lập tác động quota; muốn kết luận nhân quả riêng về quota phải có arm matched-quota khác. Đây là tùy chọn, không thuộc mức tối thiểu36cells và không thay 54 primary cells.

## 6. Đợt C — hoàn chỉnh M3 adaptive poisoning-time

### C1. Hai trajectory và feedback thật

Dùng A10, K10, **không ép quota4/3/3 của pilot cũ**; cùng miền feature/value cho hai arm. Attacker được chọn phân tán view thay vì bị buộc ở Structural. Khóa warm start là Independent LargeAbsSHAP × CountAbsSHAP trước khi xem kết quả. Sáu model A10 tương ứng ở B3 có thể làm initialization nếu data/learner/poison IDs/trigger/hash hoàn toàn khớp.

- ASR-only: proposal từ incumbent được cập nhật theo ASR, với constraints giống arm kia.
- VMC-aware: proposal từ incumbent được cập nhật theo mean VMC, giữ attack strength và clean utility.
- Mỗi candidate thay một coordinate hoặc một value, xác suất đề xuất0,5/0,5. Khi thay coordinate, chọn đều từ allowed pool ngoài trigger hiện tại rồi chọn value từ catalogue của coordinate mới; khi thay value, chọn một coordinate hiện có và một observed value khác. Catalogue là các unique float32 values từ cùng mixed selection pool, chứa warm-start values; không cho một arm chỉ dùng rare4 còn arm kia toàn bộ values. Khóa RNG/proposal policy trước chạy.
- Mỗi lần đánh giá candidate phải poison lại cùng source IDs rồi train lại model từ đầu. Learner/loss/labels không thay. Không chỉ đổi đầu vào sau training.
- Candidate vòng sau dùng incumbent/feedback của vòng trước; cần log parent và lý do update. Đoạn `proposed=list(base)` của pilot không đáp ứng thiết kế này.

Đây là **bounded full-knowledge training simulation**, không gọi black-box hoặc malicious-provider toàn quyền. Attacker biết VMC nhưng không được xem trusted defender reference/calibration hoặc outcome held-out.

M3 ở đây tối ưu **thành phần VMC**, không trực tiếp tối ưu Reduced/Full hay một policy cảnh báo end-to-end. Kết quả không được diễn giải là chứng minh khả năng chống mọi adaptive attacker nhắm toàn bộ X-SENTINEL.

### C2. Objective, constraints và budget

Tập clean-original eligible trên Search cố định trước search. Đề xuất lấy một subset1000 ID eligible, khóa theo ID/seed, làm objective VMC để giới hạn TreeSHAP; ASR/utility/screen dùng toàn Search pool. Đây là sample budget phải ghi trong protocol, không thay sau khi thấy kết quả. Báo thêm VMC trên toàn eligible pool sau khi khóa selected model.

Trong các candidate hợp lệ:

- ASR-only tối đa ASR; tie theo paired gain rồi trigger fingerprint.
- VMC-aware tối thiểu mean VMC trên **fixed objective pool**, tie theo ASR, paired gain rồi fingerprint.
- Screen đề xuất giữ primary: eligible≥1000, ASR≥0,50, net paired gain≥0,20, clean-accuracy drop<0,005.
- Trước khi có feasible candidate, hai arm dùng cùng ranking: ít điều kiện screen bị vi phạm hơn, rồi tổng mức vi phạm đã chuẩn hóa theo cutoff, rồi ASR cao hơn, paired gain cao hơn và fingerprint. Dùng chính cờ strict-screen để phát hiện equality tại clean-drop0,005 là fail; tổng violation bằng0 không tự làm candidate thành valid. Khóa công thức chi tiết trong protocol/test trước chạy, không chỉnh theo confirmation/final.
- VMC là concentration surrogate; giảm mean VMC không tự chứng minh joint evasion hoặc recall cải thiện. Lưu per-view shares, total attribution mass và tỷ lệ zero-attribution để kiểm degenerate scores.

**16 logical evaluations/arm gồm initialization.** Trong arm không dùng duplicate trigger để lấp budget. Fingerprint trigger phải canonicalize theo cặp index/value float32 đã sắp xếp, để đổi thứ tự coordinate không thành candidate mới. Cross-arm duplicate có thể dùng cache đúng full key, nhưng vẫn tính logical budget đã dùng và báo actual unique fits. Cache key gồm schema/data roles/fit IDs/poison IDs/trigger/learner/seed/code hashes; không cache chỉ theo feature ID.

Tách model-fit cache khỏi objective-score cache: cache score phải thêm Search/objective-ID và input digest, định nghĩa VMC, scoring-code version và batch/numerical settings. Không dùng score từ pool hoặc model khác chỉ vì trigger giống nhau.

Phân biệt schema-invalid proposal, duplicate proposal, training failure và completed evaluation. Retry lỗi hạ tầng chỉ dùng đúng candidate/lock cũ, log riêng số process launches và cost; không sinh thêm trigger để bù vượt budget. Chưa xử lý được lỗi hạ tầng thì cell là `INCOMPLETE_INFRASTRUCTURE`, không phải `NO_VALID_ATTACK`. Tên trạng thái search không tìm được attack hợp lệ chỉ dùng sau khi budget đã được đánh giá theo protocol; thiếu reference/calibration hoặc model không tạo thành bằng chứng robustness.

Các trajectory có thể giống nhau hoặc không tìm được valid attack. Đó là kết quả được giữ lại; không tăng budget đến khi VMC-aware thắng.

### C3. Khóa lựa chọn và evaluation

1. Dùng **global evaluation barrier**: khóa manifest của cả36static attempts và12adaptive arm outcomes, bao gồm search histories, mọi trigger/model/status và code hashes, trước khi mở bất kỳ confirmation/final X/y mới nào. Không xem final của static block rồi quay lại đổi adaptive search. Reference/calibration cũng chỉ do evaluator độc lập về code path đọc sau lock; không phản hồi sang optimizer.
2. Confirmation chỉ screen classifier/attack strength và clean utility của các attack đã khóa; **không tính detector recall hoặc retune detector tại bước này**. Không thay winner nếu fail. Báo đủ status `NO_VALID_DEVELOPMENT_ATTACK` hoặc `LOCKED_ATTACK_NOT_CONFIRMED`. Mọi static model đã train hoàn chỉnh đều được đánh giá và giữ trong bảng all-attempted, kể cả không confirmed; không chọn lại static winners trên final. Adaptive arm có locked winner vẫn được final evaluation nếu confirmation fail, với cờ unconfirmed rõ ràng; không drop mất arm đó. Arm không có valid development attack giữ status và mẫu số thiếu làN/A, không thay bằng best-infeasible rồi gọi thành selected valid attack.
3. Tạo reference ranks và thresholds **riêng cho từng poisoned main model**, trên các role trusted không đưa vào search. Clean Behavioral model cho Full dùng clean fit, không dùng poison.
4. Dùng strict `score > tau`; final chỉ được dùng đánh giá. Một lần chạy bị lỗi kỹ thuật được resume đúng hash, không coi thư mục tên mới là một heldout mới.
5. Báo VMC/Reduced, TADR, **raw-kNN-top32** và Full-secondary ở threshold đã khóa. Không cần chạy lại toàn bộ baseline cũ. Raw-kNN-top32 dùng implementation hiện có: signed-log1p transform, chọn top32 theo variance từ reference benign, standardize trên reference, mean distance tới20neighbors; cấu hình được khóa trước, không dùng attack labels/SHAP để chọn feature. Fit trên cùng reference500, threshold trên cùng calibration2000 và đánh giá đúng eligible/success masks mới. Không so trực tiếp điểm24,75% từ cohort cũ với attack mới. Vì raw-kNN không phụ thuộc main model, được reuse khi schema/reference/calibration hashes và config khớp, kèm manifest; nó không thêm LightGBM fits.

Mẫu số và bảng bắt buộc:

- Classifier threshold cố định0,5. Eligible: malware được clean model nhận là malware trên original. Mỗi dataset–seed dùng cùng clean model và cùng final source IDs nên mọi static/adaptive attack trong cell có cùng eligible denominator.
- ASR: poisoned model nhận triggered input là benign trên eligible.
- Paired-new/lost và clean-trigger ASR để tách direct evasion khỏi poisoning.
- Recall trên successful-eligible và trên paired-new; N/A khi mẫu số0.
- Post-defense ASR trên fixed eligible, benign detector FPR, clean accuracy/TPR/FPR.
- So sánh chính giữa hai adaptive arms là chênh lệch post-defense ASR trên eligible denominator chung; mean VMC là objective/surrogate. Không chỉ so conditional recall khi số successful attacks giữa hai arm khác nhau.
- Thêm detector-alert rate trên unmodified malware làm control; không gọi nó là benign FPR. Tách raw-novelty phát hiện thay đổi đầu vào với chứng cứ riêng cho backdoor.
- Mean/tail VMC và shares trên fixed pool và trên successful subset; thêm common-success intersection khi so recall giữa hai arm có cohort khác nhau.
- Mọi rate có count/n; bảng từng seed, mean/SD giữa ba seed và chi phí. Đăng ký pointwise95% Clopper–Pearson intervals cho FPR/ASR/recall theo giả định nhị thức; đây là khoảng conditional theo pool/model, không thay thế between-seed uncertainty hoặc chứng nhận population FPR. Không coi source ID lặp giữa model là các mẫu độc lập mới, không gọi pointwise intervals là simultaneous family coverage.

## 7. Đợt D — binary collateral và VMC bằng dữ liệu đang có

Không cần chạy lại PE đã nghiệm thu. Cache đọc tĩnh đã cho full C2 native đổi533 coordinate, trong đó531 ngoài target; managed đổi291, trong đó289 ngoài target. Đây là thay đổi trên hai fixture, không suy thành kết luận về corpus malware.

Sau duyệt, khóa đúng hai frozen V2C2 models đã kiểm đọc được trong `output/teacher_revision_2026_11_04/m8_next_stage/READINESS.json` (clean và poisoned,500trees/2381features), hash mỗi model trong diagnostic manifest. Phân tích từng model riêng, không gộp thành population effect; không chọn model sau khi xem ΔVMC. So ba đầu vào cho mỗi fixture:

1. `x`: original vector.
2. `T(x)`: vector giả định chỉ thay hai target.
3. `x_binary`: vector trích từ full-C2 binary, có các thay đổi phụ.

Giữ timestamp-only/sections-only controls. Tính main probability, absolute SHAP mass/share theoS/B/M, argmax view, VMC, `VMC(T(x))-VMC(x)` và `VMC(x_binary)-VMC(T(x))`. Báo feature-change counts theo view; không suy hướng VMC chỉ từ số coordinate đổi. Behavioral feature không đổi cũng không đảm bảo Behavioral attribution không đổi vì có tương tác model.

Đây là within-adapter diagnostic dùng modern LIEF0.16.6. Legacy identical-binary parity chưa có; không gọi kết quả là xác nhận primary binary-performance. Không tính ASR/recall malware từ hai fixture. Giữ việc chưa có malware-function oracle là Threats to Validity, không tự biến nó thành điều kiện phải có live-malware experiment mới được làm các sửa JSTIS khác.

## 8. Các sửa editorial và cách trả lời phần còn lại

- Chuyển VMC_norm/MAX ra khỏi Methods thành Future Work; bỏ phương trình/số thứ tự và cập nhật cross-reference tương ứng. Không viết “chưa từng có MAX experiment”: đã có exploration lịch sử, nhưng chưa có heldout validation được hỏi.
- Đưa định nghĩa restricted, eligible, successful-eligible đủ sớm; Abstract viết rõ nghĩa thay vì nhồi thuật ngữ chưa định nghĩa.
- Gộp các giới hạn vào Threats to Validity, giữ qualification ngắn tại kết quả khi cần để không làm người đọc hiểu sai. Rút lặp ở extra-seed và random-removal169; không xóa failure evidence.
- Phạm vi title/Methods là LightGBM. MLP/MalConv chỉ là giới hạn/hướng kiểm tra, chưa lên kế hoạch train thêm.
- Với Spectral Signatures/Activation Clustering: giải thích adaptation sang SHAP/leaf embedding và giới hạn so sánh; không gọi là không thể áp dụng cho GBDT, cũng không gọi SHAP-IF chính là hai phương pháp đó. Đề xuất không thêm nhánh adaptation mới ở vòng này vì thầy cho phép giải thích lý do bỏ qua.
- Sửa TableI, widths/wrapping/caption, đồng bộ mọi tham chiếu bảng/phụ lục theo caption sau khi ghép bản cuối. Nhận xét thầy có số bảng theo bản cũ; không sửa máy móc theo số đó.
- Lập bảng trả lời từng góp ý: yêu cầu, hành động, trang/bảng mới, artifact chứng minh và giới hạn còn lại. Không đánh dấu thí nghiệm hoàn tất chỉ vì code/test phần mềm qua.

## 9. Chuẩn bị hồ sơ JSTIS theo nguồn chính thức

Đã xác minh website đúng: Journal of Science and Technology on Information Security, **isj.vn**, ISSN2615-9570. Không dùng template/quy định của JTIS, JSTS hoặc jst.vn.

- Bài tiếng Anh theo template chính thức; chuẩn bị abstract tiếng Anh **và tiếng Việt**, khoảng120–150 từ; keywords hai ngôn ngữ theo hướng dẫn “no more than10 words”. Đọc template thực tế trước format, không tự hiểu thành10phrases dài.
- References số theo thứ tự xuất hiện; sources online có access date. Checklist nêu single spacing,12pt và hình/bảng đặt trong thân bài; cần đối chiếu với template cụ thể khi chuyển Word/LaTeX.
- Chính sách công khai xác nhận **double-blind**. Chuẩn bị review manuscript ẩn danh và hồ sơ tác giả/bio riêng. Trang hướng dẫn cũng yêu cầu author names/bio/ảnh; chốt vị trí upload hai nhóm thông tin với thầy/ban thư ký trước nộp, không đưa cả vào bản reviewer.
- Hồ sơ tác giả gồm thứ tự tên, cơ quan, corresponding author, thông tin liên hệ và bio/ảnh theo yêu cầu. ORCID giữ theo chỉ dẫn trước của thầy. LLM disclosure giữ đúng công cụ và trách nhiệm thực tế; chưa tìm thấy quy định ORCID/LLM riêng trong các trang JSTIS đã kiểm.
- Chuẩn bị conflicts-of-interest và funding statements theo Ethics của tạp chí, để tác giả xác nhận đúng thực tế; không tự ghi “none”. Trước nộp, nhóm xác nhận originality, exclusive submission và thống nhất authorship/thứ tự tác giả theo checklist chính thức.
- Trang authors hỗ trợ Word và LaTeX. Nếu nhóm chuyển LaTeX, gói nộp có source+PDF+assets trongZIP/RAR. Theo lựa chọn người dùng, phần nội dung sửa trên Word; bạn trong nhóm chuyển sang template LaTeX chính thức.
- Tạp chí có template response-to-reviewer; chuẩn bị response-to-teacher để duyệt trước, dùng template reviewer khi đúng giai đoạn.
- Hiện website thông báo tạm dừng tự đăng ký tài khoản; người cần account được hướng dẫn liên hệ ban thư ký. Thầy/người nộp xử lý bước này; lượt lập kế hoạch không gửi email hoặc nộp bài.
- Chưa xác minh được page cap từ các trang đã đọc; không tự đặt giới hạn6/8/10trang. Trang phí công khai nêu không có submission/publication charges. Điều này không phải cam kết thời gian nhận hoặc đăng bài.

Nguồn chính thức đã kiểm ngày09/11/2026:

- [Submission guidelines](https://isj.vn/index.php/journal_STIS/about/submissions)
- [Publication ethics và double-blind](https://isj.vn/index.php/journal_STIS/DDXB)
- [Author page và template](https://isj.vn/index.php/journal_STIS/information/authors)
- [Word template](https://isj.vn/adsbanner/upload/images/Template_Word.docx)
- [LaTeX template](https://isj.vn/adsbanner/upload/images/Template_ISJ.zip)
- [Response template](https://isj.vn/adsbanner/upload/images/1611908806-Author_response_English.docx)
- [Publication fee](https://isj.vn/index.php/journal_STIS/PXB)

Các file template mới xác minh link, chưa kiểm nội dung bên trong trong lượt lập kế hoạch này. Nếu template và web checklist khác nhau, ghi khác biệt và xác nhận trước bước nộp.

## 10. Thứ tự triển khai và tiêu chí nghiệm thu

| Gate | Công việc | Đầu ra và điều kiện qua |
|---|---|---|
| G0 | Định vị đã chốt; khóa scope/budget, xuất phát từ bản Word04/11 | Protocol draft, issue matrix, primary54 hash snapshot; chưa thay primary |
| G1 | Tái tạo calibrated numbers, sensitivity, score diagnostics; audit data history | Count/n và cache hashes khớp; ledger không overlap; đủ class/domain |
| G2 | Cài selectors/quota-free family và sequential search; đo tài nguyên | Tests fidelity/tie/cache, feedback-dependent trajectory, role access, failure handling; benchmark hệ thống trên development-only |
| G3 | Khóa protocol/code/role IDs; chạy36static cells và hai adaptive arms | Đủ mọi attempt, models/triggers/fit-cost/trace; global lock cả36static+12arms; không dùng trusted/final feedback |
| G4 | Confirmation, model-specific calibration và final sau global lock | Đánh giá mọi completed static cell, giữ weak/unconfirmed; calibrated same-access raw-kNN comparator; prediction/score arrays và đủ mẫu số |
| G5 | Quantitative C2/VMC, tổng hợp kết quả và sửa Word | Bảng selector/adaptive/collateral, response matrix; kết luận không vượt dữ liệu |
| G6 | JSTIS formatting và hồ sơ | Word đã render/kiểm toàn bộ; LaTeX/PDF/assets nếu dùng; bản blind riêng; thầy duyệt nội dung trước nộp |

Tests quan trọng: original source parity cho ba selectors; forward proposal thay khi feedback/incumbent thay; ASR-only optimizer không nhận VMC feedback; global barrier cho static và adaptive, không đọc heldout X/y trong search; poison IDs/labels bất biến; trigger permutations không lách duplicate budget; cache không lẫn schema/model/data; resume không đổi lock; threshold strictness/ties; masks và count/n tính lại độc lập; zero-success raN/A; lỗi hạ tầng không thành no-valid/success; raw-kNN selector/scaler chỉ fit trên reference và không có final/attack-label selection.

Không bắt buộc VMC-aware phải thắng, cohort phải tăng, hay detector phải có recall cao mới hoàn tất. Nghiệm thu bằng protocol được thi hành và báo đủ kết quả, kể cả âm. Không suy thành chứng minh robustness phổ quát hoặc bảo đảm JSTIS chấp nhận.

## 11. Tài nguyên và file dự kiến

36static poisoned fits; adaptive6cells×31unique=186 tối đa, trong đó6initialization có thể dùng lại từstatic. Khi reuse đủ6initialization đúng hash, tổng **216 unique poisoned fits**, cộng6clean main và6Behavioral = **228 LightGBM fits** tối đa trước các cache collisions khác. Nếu không reuse được initialization từstatic, trần là **222poisoned và234LightGBM fits tổng**. Hai arm adaptive vẫn phải dùng cùng initialization trong từng cell. Legacy global ablation tùy chọn tăng12. Logical adaptive evaluations vẫn192, không đổi budget khi cache làm giảm physical fits. Báo actual fits và lý do mọi khác biệt với dự toán.

Historical200K fits gợi ý riêng training có thể cỡ9–10giờ cho phạm vi228fits, nhưng dữ liệu mới, TreeSHAP, reference/calibration, I/O và evaluation chưa nằm trong đó. Cần đo throughput/peak memory trước khi hứa thời gian hoàn thành. Static36models cộng tối đa12adaptive winners có thể cần calibration/evaluation cho48main models: ref500+cal2000+final benign10K+triggered malware10K = **1,08triệu SHAP input rows**, chưa gồm search. Nếu thêm mandatory unmodified-malware control10K/model, tổng lên **1,56triệu rows** trước search/full-Search diagnostics. Dùng batch và cache một lần contributions cho VMC/BGS/TADR/Full, không gọi SHAP riêng cho từng score. Benchmark throughput cho cả train lẫn SHAP/cal/eval ởG2 và project disk peak; không coi tổng công việc là chỉ216lượttrain. Raw-kNN có thêm reference fitting/scoring cost nhưng không đổi228–234LightGBM-fit accounting; retries được báo riêng.

D: còn khoảng23,8GiB khi rà soát. Chọn bounded materialization, memmap và một fit tại một thời điểm,4threads ban đầu; lưu model/trigger/IDs/scores thay vì lưu một full poisoned matrix cho mỗi candidate. G2 phải xuất ước lượng peak incremental disk bytes gồm roles/models/bundles/scores/temp/checkpoints, available bytes và reserve trước chạy; yêu cầu free space lớn hơn peak estimate cộng reserve (đề xuất reserve=max(2GiB,20%peak estimate), khóa trước batch). Đo peak RAM và dự phòng với một fit/SHAP batch trước toàn bộ matrix. Nếu thiếu tài nguyên thì `RESOURCE_GATE_FAILED` và cập nhật phương án trước evaluation; không tự xóa dữ liệu hoặc giảm fit/budget âm thầm.

File sẽ bổ sung/sửa **sau khi duyệt**: protocol riêng; audit/prepare role scripts; selector wrappers và quota-free trigger validation; sequential search/evaluator/summarizer; tests nêu trên; Word nội dung+response matrix. Giữ các script pilot và frozen54cells để tái lập lịch sử. Không commit/push hoặc nộp journal tự động.

**Kế hoạch được xem là hoàn chỉnh khi mọi góp ý có action và acceptance ở trên; công việc chỉ được xem là hoàn thành sau khi có artifact chạy thật và bản Word cuối đã kiểm.**

## 12. Bảng đối chiếu toàn bộ góp ý mới

| ID trong PDF | Hướng xử lý | Điều kiện đóng mục |
|---|---|---|
| Major3.1, Request7.6 | Định vị evaluation/negative results; title giới hạn LightGBM | Title/Abstract/contributions/Conclusion nhất quán; không hứa fusion vượt trội |
| Major3.2, Request7.2 | Ba cấu hình Severi + M3 hai trajectory | Bảng36attemptedstaticcells và adaptive12arms có protocol/hashes/failures/heldout results |
| Major3.3, Request7.3 | Báo cohort nhỏ và sensitivity; giảm khẳng định thay vì hứa confirmed cohort lớn | Có attempted/confirmed counts, từng seed; không pool lịch sử và nghiên cứu mới để thổi sample size |
| Major3.4, Request7.1 | Calibrated numbers làm headline | Tái tạo35,75/48,33 và FPR/cohort; retrospective cap chỉ secondary |
| Major3.5, Request7.4 | Cập nhật C2 mới và quantitative collateral/VMC | Có x/T(x)/x_binary, SHAP view shares/ΔVMC, hash/model/adapter và giới hạn n2 |
| Major3.6 | Full vs clean budgets; tách coupled Shadow200K | Main Discussion có tradeoff; bảng không gọi coupled endpoint là independent baseline |
| Major3.7 | Phân tích direct evasion theo coordinates/values/views | Bảng coordinate/value/view và drop-one/view-restoration trên development khóa trước, cộng clean-trigger/poisoned-trigger và paired-new/lost cho C/S/X; không suy population causality từ diagnostic |
| Major3.8, Request7.5 | Đưa VMC_norm/MAX sang Future Work | Methods và equation/cross-reference đã cập nhật; không có claim improvement chưa validation |
| Minor4.1 | Phân tích rank resolution, saturation/ties và fusion loss | Có actual ranks/threshold counts; phân biệt reference500 và calibration2000 |
| Minor4.2 | FPR-tail diagnostics và exceedance counts | Báo6/54 vàworst227/10000, score-tail comparison; không gán nguyên nhân khi chưa đủ chứng cứ |
| Minor4.3 | Mô tả split chính xác, ngày tháng khi có metadata | Random/stratified/official source split công khai; không claim temporal robustness chưa đo |
| Minor4.4 | Giới hạn LightGBM | Title/threats đúng phạm vi; MLP/MalConv không được nhận là đã đánh giá |
| Minor4.5 | Giải thích chưa thêm Spectral/Activation adaptations | Nêu khả năng SHAP/leaf embedding, lý do scope và training-defense hiện có; không đánh tráo tên baseline |
| Minor4.6, Request7.7 | Gọn văn phong, gom Threats to Validity | Xóa lặp ởextra-seed/random169; vẫn giữ failure evidence và qualification cần thiết |
| Minor4.7 | Sửa TableI và cross-references; định nghĩa thuật ngữ sớm | Render/kiểm toàn bộ final Word và PDF sau ghép template; caption/ref không lệch |
| Minor4.8 | Double-blind + hồ sơ tác giả riêng | Review file/repo/metadata không lộ danh tính; author/bio upload theo hướng dẫn được xác nhận |
| Minor4.9 | Bỏ headline latency thiếu provenance hoặc đo mới đúng scope | Mỗi số latency giữ lại có đúngrun/hardware/runtime/thread/model/fixture hashes; không mượn cấu hình từrunkhác |

Những mục có lựa chọn “đánh giá hoặc chuyển hướng phát triển”, “mở rộng hoặc giảm khẳng định”, “bổ sung hoặc giải thích” đã được chọn phương án cụ thể trong kế hoạch này. Thầy vẫn là người duyệt phạm vi bản sửa trước khi gửi; không tự khẳng định mọi lựa chọn sẽ được phản biện chấp nhận.

## 13. Kết quả rà soát sau khi người dùng chốt giữ hướng nghiên cứu

Kết luận: kế hoạch phù hợp hướng evaluation đã chọn và đủ làm cơ sở triển khai sau các gate dữ liệu/tài nguyên. Không cần thêm một nhánh defender mới, mô hình MLP/MalConv, runtime behavior detection hoặc live-malware execution để thực hiện các phần hiện đã chốt. M8 functioning-malware vẫn là giới hạn mở riêng; hoàn thành bản sửa trong scope này không tự đóng giới hạn đó.

Đã siết thêm: (1) same-access raw-kNN comparator cho dữ liệu mới; (2) bảng coordinate/value và restoration diagnostic; (3) global heldout barrier cho36static+12arms; (4) không drop static/unconfirmed runs; (5) tách infrastructure failure khỏi no-valid attack; (6) canonical cache/budget accounting; (7) score-cost/RAM/disk gate và count/n/intervals; (8) C2model hashes và primary54 before/after integrity.

Gói nghiệm thu cuối phải có sáu nhóm:

1. Protocol/code/role/data-access locks, exclusion ledger và hashes.
2. Bảng36static attempts/12adaptive arms, mọi fail/no-valid, model/trigger histories và prediction/score arrays.
3. Calibrated same-access comparisons, count/n, seed variation và actual cost.
4. Sensitivity/ties/FPR-tail/direct-evasion diagnostics và C2collateral/SHAP/VMC.
5. Word/PDF review ẩn danh đã QA; hồ sơ tác giả riêng; source/assets JSTIS theo lựa chọn nhóm.
6. Response matrix17mục với trang/bảng/artifact tương ứng và giới hạn còn lại.

Nếu một cell chưa có kết quả do lỗi hệ thống/dữ liệu, ghi incomplete và xử lý nguyên nhân; không tuyên bố hoàn tất formal matrix chỉ vì mỗi cell đã có một dòng status. Ngược lại, kết quả thuật toán không tìm được valid attack trong budget đã đánh giá đầy đủ là một outcome hợp lệ. Lượt rà soát này chỉ sửa tài liệu kế hoạch; không chạy batch training hoặc đổi công thức X-SENTINEL.
