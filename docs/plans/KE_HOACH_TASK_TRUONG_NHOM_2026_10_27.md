# Kế hoạch task trưởng nhóm: baseline và đánh giá bổ sung

Ngày lập: 27/10/2026. Hạn nộp thầy nhóm đã cung cấp: 29/10/2026. Cập nhật: nhóm yêu cầu chốt nội bộ lúc **20:00 ngày 27/10/2026**.

**Bản điều phối mới:** `docs/plans/CHECKLIST_CHOT_NHOM_20H_2026_10_27.md` phủ toàn bộ góp ý và phân công cả nhóm. Lịch và ưu tiên trong bản mới thay các phần xung đột ở dưới; phần kỹ thuật baseline/same-FPR vẫn dùng được. Đặc biệt, adaptive nhiều view là ưu tiên chính theo mục5 của thầy; Full/Shadow theo ngân sách sạch là hướng bổ sung, còn 1.1 cho phép chọn Reduced làm đóng góp chính. Không hiểu các nhánh dưới đây chỉ được xử lý bằng viết giới hạn.

Trạng thái: kế hoạch đề xuất để triển khai. Lượt lập kế hoạch chỉ kiểm tra code/tài liệu/kết quả đã lưu; chưa thực hiện baseline hoặc thí nghiệm mới.

## Kế hoạch thực thi riêng của bạn và Codex

Đích bàn giao nghiên cứu: **18:00 ngày 27/10**. Đích duyệt nội dung kỹ thuật trong bản cuối: **20:00**. Khoảng 18:00–20:00 dành cho ghép/kiểm bài; không coi đó là thời gian còn trống để mở phương pháp mới.

### Phân vai

- **Codex:** kiểm input; viết/sửa code; kiểm thử; chạy thí nghiệm trong môi trường hiện có; xuất bảng/hình/log; viết phương pháp/kết quả/giới hạn bằng tiếng Anh và giải thích bằng tiếng Việt; đối chiếu số trong bản ghép cuối. Không giao lại cho bạn những lệnh mà công cụ hiện có chạy được.
- **Bạn:** điều phối nhóm; thống nhất một bản Word chính; chuyển các gói bàn giao cho Quân/Phú; nhận kết quả từ Phúc; nắm các kết luận và duyệt cách diễn đạt cuối. Không phải tự viết lại code hay tính lại bảng để thay phần Codex.
- Các nội dung trigger trên file, rà toàn bộ bibliography và dàn Word vẫn do người đã nhận task làm; chúng chỉ xuất hiện ở điểm nhận/bàn giao dưới đây.

### Danh sách việc của hai bên và đầu ra

| Thứ tự | Việc Codex thực hiện | Góp ý | Đầu ra phải có |
|---|---|---|---|
| 0 | Ghi nhận code/input hiện tại, giữ tài sản cũ, khóa dữ liệu/model/tham số/cách tính trước khi chạy phần mới | Nền tảng cho mọi bảng | Protocol, hash, danh sách cấu hình và các tập dữ liệu |
| 1 | Triển khai SHAP-IF và kiểm chiều điểm baseline cũ; pilot kỹ thuật rồi chạy phạm vi đã khóa | 1.5 | Điểm benign/malware gốc/triggered; ngưỡng từ calibration riêng; count/n; bảng fixed-threshold và same-FPR |
| 2 | Tái phân tích cùng FPR, Cross confirmation/final, độ dao động seed, FPR/AUC và phạm vi timing từ cache | 1.2,1.4,1.6,mục3 | Bảng theo từng run và tổng hợp, biểu đồ FPR thấp, giải thích Cross2018, bảng min/max/SD |
| 2B | **Task riêng EMBER2024:** đánh giá baseline/cùng FPR trên 2024, thống kê các seed hiện có và triển khai thêm hai seed mới tại spread Structural 2% | 1.6, đồng thời1.4/1.5 | Bảng từng seed trước/sau bổ sung, count/n, trạng thái confirmation, kết quả detection và phạm vi thực chạy |
| 3 | Làm phép đánh giá adaptive qua nhiều view; khóa phạm vi thay đổi/nhóm dữ liệu/ngân sách/phương pháp trước, kiểm bằng pilot rồi chạy | 1.2 | Protocol, code, log và bảng trước/sau; rõ số model/input thực chạy; ghi đây là vector experiment |
| 4 | Viết lại lập luận Reduced/Full/Shadow và bảng tài nguyên; dùng bảng cùng FPR; giữ kết quả bất lợi | 1.1 | Bảng nguồn lực và nội dung EN cho Abstract/Introduction/Scope/Results/Conclusion |
| 5 | Chọn một phòng thủ ở mức tập train từ nguồn gốc để đối chiếu; mô tả dữ liệu/quyền truy cập/cách lọc/retrain và phạm vi khác per-input | 1.5 | Bảng bối cảnh có nguồn. Nếu thực nghiệm thêm, cần kết quả thực; nếu không, ghi literature comparison |
| 6 | Kiểm số, thống nhất tên mô tả của thành phần, viết 3–4 đóng góp, giải thích giới hạn và xuất gói ghép bài | Mục 2 và 3 | CSV/hình, PAPER_INSERTS_EN.md, README_VI.md và bảng trả lời từng góp ý |
| 7 | Đối chiếu nội dung Phúc gửi và bản Word/PDF Quân ghép với gói số liệu đã duyệt | 1.3 và kiểm cuối | Danh sách sửa cuối; Abstract/Conclusion không vượt bằng chứng |

Thứ tự trên là thứ tự phụ thuộc, không yêu cầu chờ chạy hết baseline mới làm phân tích. Code/phân tích/viết có thể làm song song; job nặng dùng CPU/RAM cần được điều phối dựa trên pilot.

### Những nhánh vẫn nằm trong phạm vi nhưng có điều kiện chạy

- **Full/Shadow theo lượng dữ liệu sạch:** tiếp tục hướng đã đề xuất; dùng cùng mẫu sạch/cùng ngân sách cho hai bên, báo M4-F và Full riêng. Mục1.1 có thể xử lý theo hướng Reduced trước; chưa có biểu đồ mới thì không nói Full đã được chứng minh hữu ích khi ít dữ liệu.
- **Training-level thực nghiệm:** nếu nguồn train, baseline và thời gian kiểm tra đủ thì triển khai phép lọc/retrain được khóa trước. Không cam kết retrain54model chỉ để bổ sung bối cảnh. Phần phương pháp và nguồn của nhánh này vẫn phải bàn giao dù thực nghiệm chưa hoàn tất.
- **EMBER2024 thêm seed:** chuyển thành task riêng 2B cần triển khai và đo thời gian sớm, không đợi làm xong mọi việc khác mới bắt đầu. Mục tiêu hai seed mới tại spread Structural 2%; vẫn phải kiểm tính hợp lệ và khả năng bàn giao trước18:00. Nếu chưa hoàn thành, ghi đúng số lượt hoàn tất/chưa xong, không ngầm loại khỏi phạm vi.

Đánh giá các nhánh này trước 16:00 bằng thời gian pilot và dữ liệu có sẵn. Chỉ mở lượt chạy nếu dự kiến hoàn tất và kiểm tra trước 18:00. Nếu không đủ thời gian, ghi thiếu cụ thể, không xóa khỏi danh sách.

### Lịch của hai bên hôm nay

| Mốc | Codex | Bạn |
|---|---|---|
| Ngay–13:00 | Khóa protocol, kiểm dữ liệu, triển khai metric và pilot kỹ thuật baseline/adaptive; kiểm pipeline thêm seed EMBER2024 | Thông báo mốc 18:00 nhận đủ số liệu, 20:00 chốt; bảo đảm Quân có đúng bản Word chính |
| 13:00–16:00 | Chạy phạm vi hợp lệ gồm task EMBER2024, phân tích cache, hoàn thiện nguồn lực Full/Shadow và bối cảnh training-level | Làm việc điều phối và học cách giải thích kết quả; không cần chờ máy để bắt đầu phần mình |
| 16:00 | Báo tiến độ từng thí nghiệm và phạm vi có thể bàn giao; quyết định mở rộng dựa vào runtime | Nhận tình trạng và gói kết quả Phúc đã có để chuyển cho Codex đối chiếu |
| 16:00–18:00 | Kiểm count/n, log, bảng/hình; xuất nội dung EN và giải thích VI; chốt số đưa vào bài | Chuyển gói đã duyệt cho Quân/Phú, chốt các kết luận nhóm sẽ bảo vệ |
| 18:00–19:00 | Kiểm số và nội dung nghiên cứu trong bản Quân ghép; ghi sửa cụ thể | Bảo đảm nhóm dùng cùng một bản và xử lý danh sách sửa |
| 19:00–20:00 | Rà Abstract/Conclusion, giới hạn, tên bảng/hình và bảng trả lời phản biện | Duyệt bản cuối và giữ bản nộp thống nhất |

### Task EMBER2024 — chi tiết được tách riêng

1. **Đánh giá lại trên dữ liệu hiện có:** baseline SHAP-IF, so cùng mức báo nhầm, Reduced/Full/Shadow và Cross đều có phần EMBER2024 riêng; không chỉ chạy EMBER2018 rồi suy sang2024.
2. **Thống kê hiện có:** đối chiếu ba seed17,29,43; báo từng run, min/max và SD của cùng family/rate. Tách các cấu hình không qua confirmation khỏi cohort đã xác nhận, nhưng vẫn giữ chúng trong danh sách chạy.
3. **Mục tiêu thêm hai seed mới:** giữ spread Structural và poisoning rate2%, cùng cách chia dữ liệu và protocol gốc. Khóa hai seed trước khi chạy; không thay seed sau khi biết kết quả. Dùng namespace mới, giữ nguyên54 cấu hình lịch sử.
4. **Chạy đủ quy trình:** model sạch và model bị đầu độc tương ứng, bước confirmation theo tiêu chí gốc rồi đánh giá detector. Không gọi việc chấm lại một model cũ là thêm seed.
5. **Không bảo đảm có năm run được xác nhận:** ba run cũ cộng hai lượt thử mới chỉ thành năm run đã xác nhận nếu cả hai mới đều đạt. Báo cả pass/fail; không giảm tiêu chí để đủ số lượng.
6. **Bảng bàn giao:** seed, family/rate, confirmation pass/fail và lý do, ASR clean/poisoned, paired gain, recall, FPR, số mẫu; tổng hợp cũ/mới và mức dao động đúng nhóm.
7. **Giới hạn:** thêm seed ở spread2% kiểm độ dao động trong điều kiện đó, chưa chứng minh mọi kiểu trigger. Rate3–4% là điều kiện khác, không dùng thay thế số lần lặp ở2%. Dùng lại final cũ phải ghi là đánh giá bổ sung trên benchmark đã quan sát.

Các tên đầu ra dự kiến: `ember2024_seed_runs.csv`, `ember2024_seed_summary.csv`, `ember2024_seed_completion.json` và đoạn EN giải thích kết quả. Chưa tạo hoặc chạy trong lượt cập nhật kế hoạch này.

### Tiêu chí xong của task này

- Mỗi bảng mới truy được tới model/input/score, có count/n và phạm vi run.
- Baseline và adaptive được ghi đúng mức: code đã viết, pilot hợp lệ hay đánh giá hoàn tất; không nhập các trạng thái này thành một.
- Các ý1.1/1.2/1.4/1.5/1.6 đều có kết quả, nội dung xử lý hoặc mục còn thiếu được chỉ rõ.
- Có gói nội dung tiếng Anh để ghép và giải thích tiếng Việt để bạn trình bày.
- Không hứa phương pháp sẽ thắng baseline hoặc sửa được điểm yếu Cross chỉ vì đã thêm thí nghiệm.

Các phần phía dưới giữ chi tiết kỹ thuật để triển khai; lịch hiện hành là lịch 20:00 ở trên. Lịch là mục tiêu điều phối, không phải số đo chứng minh mọi job nặng chắc chắn chạy kịp.

## 1. Mục tiêu và phạm vi

Hoàn thành một gói kết quả có thể kiểm tra để trả lời góp ý 1.1, 1.2, 1.4, 1.5, 1.6 và các vấn đề AUC/FPR/timing ở mục 3. Trưởng nhóm chịu trách nhiệm phần nghiên cứu; Phúc phụ trách trigger trên file, Phú kiểm tra nguồn và theo dõi phản hồi, Quân giữ Word chính.

Mục tiêu trước hạn là cải thiện bằng chứng so sánh và độ chính xác của kết luận. Không đặt tiêu chí phải tăng recall hoặc bắt buộc phương pháp đề xuất thắng baseline.

### Phần ưu tiên hoàn tất trước hạn

1. Tái phân tích 54 cấu hình ở cùng mức báo nhầm.
2. Báo cáo Cross theo đúng giai đoạn confirmation/final và nhóm paired.
3. Báo cáo từng seed và độ dao động trong từng family/rate.
4. Bổ sung một baseline Isolation Forest trên SHAP với tài nguyên tương đương Reduced.
5. Làm rõ nguồn lực Full/Shadow, FPR vượt mục tiêu, chiều điểm STRIP/TADR và phạm vi đo thời gian.
6. Xuất gói bảng, hình, nội dung tiếng Anh và bảng trạng thái phản biện để Phú/Quân sử dụng.

### Các nhánh bổ sung vẫn do trưởng nhóm phụ trách

- **Ưu tiên chính theo bản cập nhật:** phép thử thích nghi qua nhiều view, do thầy đặt ở ưu tiên2 mục5.
- Phòng thủ ở mức tập huấn luyện, có lọc dữ liệu và huấn luyện lại.
- Thêm seed EMBER2024 tại cùng điều kiện spread 2%.
- Thí nghiệm Full/Shadow theo lượng dữ liệu sạch.

Đây là các thí nghiệm mới. Nếu chưa thực hiện, phải ghi rõ chưa hoàn thành; phân tích từ dữ liệu cũ hoặc viết thêm giới hạn không thay thế những thí nghiệm này.

## 2. Đầu vào đã kiểm tra

- `configs/primary_protocol.json`: 2 dataset, 3 family, 3 rate và 3 seed mỗi dataset; reference 500 benign, calibration 2.000 benign, final 20.000 mẫu mỗi dataset.
- `outputs/primary/*/protocol_v2/seed_*/*/rate_*/paired_predictions.npz`: có 54 cache. Mỗi cache chứa source ID, xác suất clean/main và các điểm detector; không chứa vector SHAP đầy đủ.
- `outputs/primary_confirmation/`: bằng chứng quyết định một cấu hình có được xác nhận hay không.
- `outputs/revision_2026_10_13/supplement/`: 54 cache calibration, kết quả Shadow/inverse STRIP và phép đo bổ sung.
- `outputs/revision_2026_10_13/analysis/`: `cell_metrics.csv`, `cohort_metrics.csv`, `fpr_diagnostics.csv`, `calibration_final_curves.json`, `cluster_intervals.json`.
- `data/primary/{EMBER2018,EMBER2024}/protocol_v2/roles.json` và các nguồn array được khai báo: đầu vào cho reference/calibration/final.
- `scripts/analyze_primary_revision.py`, `scripts/run_revision_supplement.py`, `src/xsentinel/revision/analysis.py`: logic có thể tái sử dụng.
- `src/xsentinel/baselines/scores.py::contributions()` và `src/xsentinel/detection/calibration.py::threshold()`: tái dùng kiểm tra SHAP/raw margin và cách đặt ngưỡng. Tái tạo vector triggered từ `VectorTrigger` trong `attack.json` của đúng cell.
- `scripts/run_revision_adaptive.py`: phép thử cũ chỉ trong Structural, không phải adaptive nhiều view.
- `docs/REPAIR_2026_10_23.md`: chẩn đoán Cross, file lành và phạm vi bằng chứng vận hành ngày 23/10.

Môi trường dự án khai báo scikit-learn 1.6.1 và LightGBM 4.6.0. Cần kiểm tra phiên bản thực trong môi trường trước khi chạy; không tự nâng thư viện cho task này.

Tập `fresh_validation` ngày 13/10 đã được quan sát. Dùng lại được để đối chiếu nhưng phải gọi là tập bổ sung đã sử dụng, không phải holdout mới cho baseline ngày 27/10.

## 3. Bước A: ghi nhận đầu vào và khóa cách đánh giá

Ước lượng: 0,5–1 giờ công.

- Ghi commit, các thay đổi chưa commit, phiên bản thư viện và hash các input thực dùng. Checkout hiện có thay đổi cũ; không reset/stash tự động hoặc lấy HEAD làm đại diện cho toàn bộ code đang chạy.
- Tạo namespace kết quả riêng, dự kiến `outputs/teacher_revision_2026_10_27/`.
- Tạo protocol trước khi chạy: danh sách cấu hình, các pool, phương pháp, tham số, chiều điểm, cách đặt ngưỡng, nhóm positive và quy tắc tổng hợp.
- Lưu lịch sử tập đánh giá đã được xem. Mọi so sánh mới trên final/fresh cũ được ghi là phân tích bổ sung sau phản biện.
- Kiểm tra ID, hash, schema, số chiều, nhãn và các tập reference/calibration/final không trùng nhau theo manifest.
- Định nghĩa cột count/n cho mọi tỷ lệ; nhóm rỗng xuất null kèm lý do, không xuất 0 giả.

Hoàn tất khi protocol và manifest đủ để người khác xác định chính xác dữ liệu/model được dùng.

## 4. Bước B: phân tích từ điểm đã lưu

Ước lượng: 3–5 giờ công; thời gian tính dự kiến ngắn, phải đo khi triển khai.

### B1. Cùng mức FPR — góp ý 1.4

- Giữ bảng ngưỡng calibration gốc để thể hiện hành vi khi dùng ngưỡng cố định.
- Thêm TPR cao nhất tại empirical FPR <= 1% trên từng run, trên các nhóm `successful_eligible` và `paired_new_evasion`; bảng phụ có thể báo `all_triggered`.
- Giữ các điểm bằng nhau thành một nhóm. Không tách ties tùy tiện để đạt đúng 1%; báo FPR thực đạt được và quy tắc score > tau.
- Đây là điểm vận hành dùng cho phân tích ROC trên tập đánh giá, không thay tau trong bundle.
- Thêm standardized partial AUC với `max_fpr=0.01`; ghi đúng tên và không nhầm với diện tích thô vùng 0–0,01.
- Tính từng run rồi lấy trung bình đồng trọng số theo cohort. Không gộp tất cả hàng lặp thành các file độc lập.
- So sánh TADR, STRIP, M3, M4-R, M4-F, X-R, X-F, inverse STRIP, Shadow và IF-SHAP khi có điểm.
- Cache primary không có đầy đủ điểm Shadow benign/calibration. Nếu thiếu, tính lại xác suất bằng các model cố định; không huấn luyện lại để dựng điểm Shadow.

Đầu ra: `same_fpr_per_run.csv`, `same_fpr_summary.csv`, hình đường ROC vùng FPR thấp; có số run và mẫu số.

### B2. Cross — góp ý 1.2

- Bảng confirmation: số eligible, ASR clean trên triggered input, ASR poisoned, paired gain và từng điều kiện pass/fail.
- Bảng final: số successful-eligible, số paired-new-evasion, số paired-lost-evasion, recall và post-ASR của từng detector.
- Không dùng final thay confirmation để giải thích việc lựa chọn cohort.
- Paired gain = chênh lệch ASR; paired new evasion là một nhóm chuyển trạng thái. Hai đại lượng chỉ trùng trong những điều kiện riêng, không giả định đồng nhất.
- Giữ Cross ở kết quả chính và giải thích giới hạn. Cách gọi stress test không được dùng để né kết quả bất lợi.

Đầu ra: `cross_confirmation_diagnostics.csv`, `cross_final_paired_metrics.csv` và đoạn giải thích tiếng Anh.

### B3. Độ dao động — góp ý 1.6

- Xuất từng seed, min/max, mean và sample SD theo dataset/family/rate/method.
- Ghi rõ số run được xác nhận và các run không đạt.
- Nếu tổng hợp 12 run khác family/rate, gọi đó là biến thiên giữa cấu hình, không gọi tất cả là biến thiên do seed.
- Giữ nhãn khoảng bootstrap: thay đổi đầu vào với model cố định, không đại diện mọi model/seed tương lai.

Đầu ra: `seed_variability.csv` và bảng nhỏ cho Quân.

## 5. Bước C: baseline Isolation Forest trên SHAP — góp ý 1.5

Ước lượng: 6–10 giờ công. Chưa chốt thời gian máy: phải đo hai pilot rồi dự phóng số cấu hình còn lại, phân biệt thời gian SHAP, fit và chấm điểm. Không suy từ thời gian training classifier cũ.

### Thiết kế đề xuất khóa trước khi chạy

- Mỗi poisoned main model có một IF-SHAP tương ứng; không dùng clean full model hoặc nhãn trigger để học baseline.
- Tính native SHAP có dấu từ chính main model; bỏ cột bias. Dùng toàn bộ cột đặc trưng, không chọn top-k theo final, không chọn PCA theo kết quả cuối.
- Fit Isolation Forest trên đúng 500 mẫu benign reference; đặt ngưỡng trên 2.000 benign calibration riêng.
- Tham số đề xuất: `n_estimators=200`, `max_samples=256`, `max_features=1.0`, `bootstrap=False`, `contamination='auto'`, `random_state=17`, `n_jobs=4`.
- Điểm nghi ngờ là `-score_samples`, vì điểm gốc càng thấp càng bất thường. Không dùng nhãn của `predict()` làm quyết định; áp dụng ngưỡng calibration riêng và score > tau.
- Ngưỡng lấy cùng quy tắc order statistic của hệ thống. Với 2.000 calibration và mục tiêu 1%, số vượt ngưỡng calibration không quá 20; điều này không bảo đảm FPR final.
- Tính SHAP theo batch (dự kiến 128 hoặc 256, chốt bằng kiểm tra tài nguyên); lưu điểm và metadata, hạn chế lưu toàn bộ ma trận SHAP của các pool lớn.
- Lưu checkpoint theo cell để tiếp tục sau lỗi; không khởi chạy nhiều model đồng thời trước khi đo RAM/thời gian pilot.
- Dùng cùng model, đầu vào và mask positive với các phương pháp đối chiếu.
- Có thêm malware chưa gắn trigger làm đối chứng. Báo rõ đây là tỷ lệ cảnh báo trên malware gốc, không gọi là benign FPR. Đối chiếu trước/sau trên cùng source ID để tránh diễn giải mọi bất thường malware là dấu hiệu backdoor.

### Pilot và mở rộng

1. Chọn trước seed 17, spread Structural 2% của EMBER2018 và EMBER2024 để kiểm tra kỹ thuật.
2. Đầu tiên chỉ kiểm tra fit/reference/calibration và tính theo batch: schema, finite values, số cột, tính lặp lại, chiều điểm và thời gian.
3. Không đổi tham số để làm đẹp recall sau khi xem kết quả đánh giá. Nếu phát hiện lỗi implementation, ghi sửa lỗi và chạy lại mọi phần bị ảnh hưởng.
4. Mục tiêu là đủ 54 cấu hình. Fallback được ghi trước: 24 cấu hình đã xác nhận từ nghiên cứu cũ, gồm 12 restricted 2018, 3 restricted 2024 và 9 Cross 2024. Việc dùng fallback chỉ dựa trên thời gian/tài nguyên, không theo kết quả IF.
5. Nếu chỉ hoàn thành subset, bảng phải ghi số run đã chạy, chưa chạy và lý do; không trình bày thành kết quả đủ 54 cấu hình.

Đầu ra: protocol/model IF, score theo source ID, ngưỡng và count/n, bảng fixed-threshold + same-FPR, đối chứng malware gốc, timing và manifest nguồn.

## 6. Bước D: diễn giải các điểm phản biện còn lại

Ước lượng: 1–2 giờ công.

- **Full/Shadow:** bảng tài nguyên của Reduced, Full, Shadow và IF-SHAP; dẫn kết quả cùng FPR. Không khẳng định Full có lợi thế khi dữ liệu chưa cho thấy điều đó. Đặt Reduced làm trọng tâm theo hướng bản sửa.
- **FPR:** đối chiếu calibration FP/n, final FP/n, số ties và phần đuôi điểm. Kết quả có thể vẫn là chưa xác định nguyên nhân; không tự gán cho ties hoặc dataset shift.
- **AUC STRIP/TADR:** giải thích chiều điểm; dẫn inverse STRIP đã có và FPR thấp. Nếu thử đảo hướng TADR sau khi xem final, ghi là biến thể bổ sung và hiệu chuẩn riêng.
- **Timing:** phân biệt benchmark 54 cấu hình, smoke 11 input/config có STRIP và thời gian đầy đủ đọc file/API. Giữ các số đo thật, bỏ lời khẳng định speedup không có cơ sở. Không tự giải thích 19,28 -> 27,28 ms là do nhiễu máy khi chưa đo.
- **Training-level defense:** chuẩn bị bảng bối cảnh từ nghiên cứu gốc, nêu quyền truy cập khác Reduced. Nếu chưa lọc/retrain thực nghiệm, ghi rõ literature comparison; yêu cầu baseline thực nghiệm ở mức training vẫn chưa hoàn thành.

Đầu ra: `resource_access_comparison.csv`, `diagnostic_notes_en.md` và trạng thái từng góp ý.

## 7. Adaptive và các thí nghiệm bổ sung: mốc quyết định riêng

Adaptive nhiều view thuộc phần ưu tiên chính, cần triển khai cùng kế hoạch baseline/đánh giá. Các nhánh khác có mốc đánh giá khả thi riêng theo thời gian máy và hạn bàn giao20:00. Ghi phạm vi trước khi xem kết quả mới. Mục1.5 cần có bối cảnh training-level; nếu chỉ đối chiếu tài liệu phải nói rõ chưa chạy thực nghiệm. Mục1.1 cho phép chọn Reduced chính, không bắt buộc thêm đường ngân sách sạch để hoàn thành hướng đó.

| Việc | Phạm vi tối thiểu phải chốt | Công dự trù | Nếu chưa làm |
|---|---|---:|---|
| Adaptive qua nhiều view | Protocol riêng, nguồn đầu vào, ngân sách và tiêu chí đánh giá; vẫn phân biệt vector với binary | 8–16 giờ + máy | Góp ý 1.2 chỉ xử lý phần phân tích, chưa hoàn tất yêu cầu adaptive |
| Training-level defense | Quyền xem tập train nghi bị đầu độc, quy tắc lọc, phần nhãn chỉ dùng đánh giá, retrain và đối chứng utility/ASR | 8–16 giờ trở lên + máy | Có bối cảnh tài liệu, chưa có baseline thực nghiệm |
| Seed mới EMBER2024 — task2B | Mục tiêu hai seed mới tại spread2%, khóa trước, chạy confirmation và đánh giá; giữ mọi kết quả pass/fail | Ước lượng cũ6–12 giờ công + máy; cần đo pipeline thực tế | Ghi số seed thật sự hoàn tất và số được xác nhận; giữ giới hạn tương ứng |
| Ngân sách dữ liệu sạch | Behavioral và Shadow dùng cùng các pool/ngân sách sạch để so sánh | 8–16 giờ + máy | Chưa chứng minh Full hữu ích ở ít dữ liệu sạch |

Không khởi chạy quá nhiều job nặng cùng lúc. Với hạn nội bộ20:00 ngày27/10, triển khai adaptive, SHAP baseline và task EMBER2024 sớm rồi phân bổ máy theo pilot; đường ngân sách sạch theo lịch còn lại. Không bỏ mục training-level hoặc seed EMBER2024 khỏi bảng phản hồi khi chưa hoàn tất.

## 8. Kiểm tra trước khi bàn giao

- Tái tính số đếm từ score phải khớp CSV/bảng; kiểm tra mean từng run thay vì gộp sai mẫu số.
- Kiểm tra same-FPR với dữ liệu ties/toàn điểm giống nhau, không có positive, và nhóm không đạt được đúng 1%.
- Kiểm tra IF chỉ fit reference, calibration riêng; bỏ bias đúng; kết quả batch và chạy lặp phù hợp; dấu score không bị đảo.
- Kiểm tra source ID trước/sau trigger khớp và cùng các mask đã khóa.
- Kiểm tra đủ danh sách run đã khai báo, số run lỗi/thiếu và status rõ ràng.
- Kiểm tra hash tài sản primary trước/sau; kết quả mới ở namespace riêng.
- Test tập trung vào metric mới và pipeline baseline; mở rộng regression khi có thay đổi làm ảnh hưởng code dùng chung.

Các tên file code dự kiến, chưa được tạo trong lượt lập kế hoạch: `src/xsentinel/revision/low_fpr.py`, `src/xsentinel/baselines/shap_outlier.py`, `scripts/analyze_teacher_feedback_2026_10_27.py`, `scripts/run_shap_outlier_2026_10_27.py`, kèm test cho metric và pipeline mới.

## 9. Bàn giao cho nhóm

Gói dự kiến dưới `output/teacher_revision_2026_10_27/` (chưa tạo):

- `README_VI.md`: cách tái chạy, nguồn dữ liệu, phạm vi và trạng thái.
- `PAPER_INSERTS_EN.md`: phương pháp, kết quả, giới hạn và chú thích bảng để Quân ghép.
- Các CSV và hình PNG/PDF; mỗi bảng có nguồn, số run, count/n và đơn vị.
- `claim_evidence.csv`: câu kết luận, nguồn bằng chứng, cohort/pool, giới hạn.
- `review_response_status.csv`: đã xử lý/một phần/chưa làm cho từng ý thầy.
- Danh sách phần cần nhận từ Phúc; không biến kết quả vector thành bằng chứng binary.

Phú nhận bảng phản hồi và nguồn để kiểm tra. Quân nhận nội dung tiếng Anh và bảng/hình đã duyệt. Trưởng nhóm duyệt kết luận cuối trước khi nộp.

## 10. Lịch và tiêu chí dừng

- **Ngay–13:00 ngày27/10:** bước A, phân tích cache, protocol và pilot kỹ thuật; Quân/Phú sửa phần độc lập ngay.
- **13:00–16:00:** triển khai baseline/adaptive và đánh giá; pilot phải hợp lệ trước khi mở rộng. Nếu chạy đủ54 vượt thời gian bàn giao, dùng phạm vi fallback đã khóa theo runtime. Pipeline sai phải sửa hoặc ghi chưa hoàn tất, không giảm số cấu hình để thay việc sửa lỗi.
- **16:00–18:00:** kiểm tra, bàn giao bảng/hình/nội dungEN; chốt trạng thái từng góp ý và số liệu đưa vào bản tối nay.
- **18:00–20:00:** Quân ghép Word/xuấtPDF, cả nhóm kiểm số liệu/citation/layout/Abstract/Conclusion. Chốt lúc20:00; không tự chuyển các phần chưa xong sang trạng thái hoàn tất.

Ước lượng ban đầu của gói ưu tiên là12–20 giờ công cộng thời gian máy, chưa gồm adaptive mới và sửa Word. Mốc20:00 ngắn hơn lịch cũ: phải phân công song song, đo pilot và khai báo rõ phạm vi thực hoàn thành; không lấy số người hay cóCodex làm bảo đảm mọi lượt chạy sẽ xong. Không có cam kết baseline mới sẽ thắng, Cross sẽ được khắc phục hay bài sẽ được chấp nhận.

## Nguồn kỹ thuật

- Góp ý của thầy: `C:/Users/win9tui/Downloads/Góp ý Group 4 - IA2007.pdf`.
- scikit-learn 1.6.1 IsolationForest: https://scikit-learn.org/1.6/modules/generated/sklearn.ensemble.IsolationForest.html
- scikit-learn 1.6.1 roc_auc_score: https://scikit-learn.org/1.6/modules/generated/sklearn.metrics.roc_auc_score.html

