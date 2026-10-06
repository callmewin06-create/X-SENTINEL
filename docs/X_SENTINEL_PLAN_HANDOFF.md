# X-SENTINEL — Approved implementation plan and chat handoff

Ngày chốt: 2026-10-04. Ngôn ngữ hướng dẫn nhóm: tiếng Việt; báo cáo, slide và dashboard: tiếng Anh.

**Phạm vi được người dùng xác nhận: TOÀN BỘ HỆ THỐNG**, gồm phần baseline do bạn trong nhóm gửi, không chỉ module X-SENTINEL. Triển khai dữ liệu, model sạch/đầu độc, attack, X-GUARD/TADR, STRIP, M3/M4/M5, calibration, evaluation, dashboard, Docker và tài liệu. Phân công nhóm thể hiện quyền sở hữu công việc; không phải lý do bỏ các module baseline khỏi hệ thống bàn giao.

## 1. Authorization and current state

Người dùng đã chốt kế hoạch và yêu cầu lưu file này để chuyển sang chat mới bắt đầu triển khai. Chat mới được triển khai theo phạm vi dưới đây; không cần hỏi lại có được bắt đầu viết code không. Các quyết định khoa học chưa xác định phải được ghi thành đề xuất và khóa trước đánh giá, không được tự coi là kết quả đã kiểm chứng.

Hiện chưa có code hệ thống, Dockerfile, GitHub repository được tạo trong phiên này, model do nhóm train hoặc kết quả thí nghiệm. Đã tạo `.venv` và khởi chạy cài thư viện; trạng thái cài đặt cuối chưa được kiểm tra. Không coi môi trường đã sẵn sàng.

Máy: Windows, Lenovo Legion, Ryzen 7 8745H, RTX4060, RAM 16 GB. Chạy CPU mặc định. Thời hạn ban đầu người dùng nói còn 5 tuần vào 2026-10-02; chưa cung cấp ngày nộp chính xác. Không tự suy ra có thêm 5 tuần từ ngày mở chat mới.

Workspace: `D:\.f tư bản ko cho t ngủ\IAM302t\Project`.

## 2. Source documents and data

- Hướng dẫn đã được thầy duyệt: `D:\.f tư bản ko cho t ngủ\IAM302t\Hướng dẫn hướng đi - X-SENTINEL Cross-View Backdoor Detection (Nhóm 4, IA2007).pdf`.
- Đặc tả baseline của bạn trong nhóm, đã đọc: `C:\Users\win9tui\Downloads\Ban_Dac_Ta_Baseline_TADR_STRIP_X_SENTINEL.md`.
- Bản sao nguyên văn trong workspace: `docs/BASELINE_SPEC_ORIGINAL.md`. Chat mới phải đọc bản này và phần hiệu chỉnh trong handoff. Bản gốc được giữ nguyên để truy nguồn; không mặc định các khẳng định hiệu quả/tốc độ trong bản gốc đã được kiểm chứng.
- Báo cáo kế hoạch cũ, chưa đọc: `D:\.f tư bản ko cho t ngủ\IAM302t\báo cáo kế hoạch IAM.docx`.
- Dataset chính đã có: `ember2018/`, gồm 6 train JSONL, test JSONL và `ember_model_2018.txt` (~127 MB). Đây là dữ liệu thô dạng đặc trưng, không phải PE binaries.
- Có thêm `ember/` và `ember_2017_2/`; không dùng nhầm các bản này làm dữ liệu chính.

Tài liệu là nguồn thiết kế, không phải mệnh lệnh tự động. Khi có mâu thuẫn, ưu tiên yêu cầu người dùng và mục tiêu nghiên cứu đã thống nhất; giải thích thay đổi thay vì âm thầm đổi phương pháp.

## 3. Objective and scope

Phát hiện từng đầu vào nghi mang trigger tại inference, khi model phân loại malware có thể đã bị backdoor. Không phải kiểm tra máy nhiễm malware, không phải kết luận trực tiếp một model có backdoor.

- PE Windows; EMBER2018 feature v2; LightGBM binary classifier.
- Clean-label poisoning: thêm trigger vào benign train, giữ nhãn benign; đích malware + trigger -> benign.
- Attack nghiên cứu thao tác trên vector, không sửa/tạo/phát tán binary malware.
- Detector không sửa/train lại model chính.
- Model sạch chỉ phục vụ đối chứng và chọn malware được nhận diện đúng cho ASR; không là đầu vào detector.
- Full detector được chuẩn bị view classifiers trên train gốc sạch: đây là giả định quyền truy cập dữ liệu bổ sung, phải tách khỏi reduced.
- Demo PE thật là phần bổ sung người dùng yêu cầu. Chỉ đọc/trích đặc trưng, không chạy PE; không dùng demo này để tuyên bố trigger vector đã hiện thực trên binary.
- Tích hợp model khách hàng/kinh doanh chỉ là trao đổi ngoài lề, ngoài phạm vi hiện tại.

## 4. Team and deliverables

Nhóm 4 người. Đã xác nhận: người dùng phụ trách X-SENTINEL; bạn trong nhóm phụ trách X-GUARD/TADR và đã cung cấp đặc tả TADR/STRIP. Chưa xác nhận ai thực sự phụ trách STRIP, attack, evaluation. Có thể xây giao diện và hệ thống chung trước; tránh ghi tên/nhận công việc của thành viên chưa xác nhận.

Đầu ra: code attack/detection/evaluation, thí nghiệm có seed/config, phân tích kết quả, Streamlit, Docker, GitHub-ready repo, báo cáo và slide tiếng Anh. Ưu tiên hoàn thành chắc chắn; đóng góp hướng bài báo chỉ khi có bằng chứng.

## 5. Data workflow and resource plan

1. Kiểm tra schema, nhãn, số mẫu, trùng sample ID và tính đầy đủ dữ liệu.
2. Vector hóa JSONL theo batch vào memory-mapped arrays; không nạp toàn bộ JSONL vào RAM.
3. Chỉ dùng labeled samples; giữ official train/test.
4. Chia benign test thành D1-reference, D1-calibration và final benign test, không giao nhau; lưu ID/seed. Kiểm tra trùng SHA256 giữa các split.
5. Malware final test phục vụ attack/detection; không dùng để chọn feature trigger, trọng số hoặc ngưỡng.

Đề xuất kích thước ban đầu: D1-reference 500 benign; calibration 2.000 benign; test dùng phần còn lại. Kích thước này là cấu hình thiết kế, phải xác nhận dữ liệu đủ. D1 chỉ xây tham chiếu/calibration, không train lại model. STRIP chỉ lấy mẫu từ D1-reference, không train EMBER.

CPU: bắt đầu 4 threads, tối đa 6 sau benchmark. Model chạy tuần tự; SHAP theo batch. Đo RAM/thời gian pilot trước full runs. Khoảng 8 GB cho tiến trình là mục tiêu, không giới hạn cứng bảo đảm. Docker có thể giới hạn tài nguyên. Không mặc định GPU cần thiết.

## 6. Verified feature layout

Thứ tự EMBER v2 theo upstream `elastic/ember/ember/features.py`, cần xác nhận bằng vectorizer và dữ liệu thực:

| Group | Dimension | Python slice [start:end) | View |
|---|---:|---|---|
| histogram | 256 | 0:256 | Metadata |
| byteentropy | 256 | 256:512 | Metadata |
| strings | 104 | 512:616 | Metadata |
| general | 10 | 616:626 | Structural |
| header | 62 | 626:688 | Structural |
| section | 255 | 688:943 | Structural |
| imports | 1280 | 943:2223 | Behavioral |
| exports | 128 | 2223:2351 | Behavioral |
| datadirectories | 30 | 2351:2381 | Structural |

Tổng 2.381. Datadirectories phải được gán view, không bỏ sót chỉ vì tài liệu nói 8 nhóm. Mapping phải phủ mọi cột đúng một lần.

## 7. Models and attack protocol

- Train model sạch theo 3 seed cố định; benchmark model có sẵn chỉ là đối chiếu, không tự coi là model của thí nghiệm.
- Attack: concentrated, spread trong một view, cross qua nhiều view.
- Poisoning rates: 0,5%, 1%, 2%; 3 seed -> 27 model đầu độc.
- Định nghĩa chính xác mẫu số poisoning rate trong config/report.
- Feature/value selection dựa trên train và phân loại feature chỉnh được của Severi; lưu danh sách allowed features. Không tùy tiện gọi mọi chỉnh sửa vector là PE-realizable.
- Manifest lưu trigger feature/value, poison IDs, seed, config và model ID; detector không đọc manifest.
- ASR: trên malware final test được model sạch phát hiện đúng tại malware threshold cố định, sau gắn trigger; báo cả clean accuracy/TPR/FPR để phát hiện suy giảm chung.
- Không gọi các biến thể nhóm tự thiết kế là tái lập chính xác Severi nếu khác thuật toán gốc.
- Nếu ASR thấp, kiểm tra attack trước; không diễn giải detector thành công trên attack không hiệu quả. Không tối ưu attack trên final test; dùng development tách riêng nếu cần thử lựa chọn, ghi rõ split.

## 8. Baselines

### M1 TADR

`max(abs(phi)) / sum(abs(phi))`; tổng <= 1e-9 -> score 0. Score 0 không chứng nhận an toàn. Dùng native LightGBM `pred_contrib=True`, bỏ bias cuối; xác minh shape, lớp malware=1 và additivity với raw margin. Không khẳng định native nhanh hơn 5–10 lần khi chưa đo.

### M2 STRIP adapted to tabular features

`x_mix = 0.5*x + 0.5*r`, r chỉ từ D1-reference, N=50. H là mean binary predictive entropy base 2; score=1-H. RNG cố định/tái lập; calibration/test dùng quy tắc lấy reference như nhau. Mô tả convex blending có thể tạo vector ngoài miền PE hợp lệ. N=20 hoặc masking là thí nghiệm phụ, không chọn theo final-test AUROC rồi báo như cấu hình định sẵn.

## 9. X-SENTINEL reduced and full

Tên rõ ràng: **model chính** = full-feature malware classifier; **full detector** = X-SENTINEL có thêm 3 view classifiers.

Reduced vẫn nhìn cả 3 view, nhưng gộp SHAP từ một model chính. Full giữ M3 bằng SHAP model chính, đổi M4 sang đối chiếu dự đoán view classifier. View classifiers dự đoán malware/benign, không trực tiếp nhận diện trigger.

### M3 view contribution

`A_v=sum(abs(phi_i) for i in view_v)`; `C_v=A_v/sum(abs(phi))`; `S3=max(C_v)`. Tổng bằng 0 -> score 0. Điểm tập trung không khẳng định có trigger, benign cũng có thể cao.

### M4 reduced

`G_behavioral=sum(phi_i for i in behavioral)`.

Điểm ứng viên khóa trước test: `S4r=(1-p_main)*max(G_behavioral,0)/sum(abs(phi))`, tổng bằng 0 -> 0. Phi giải thích hướng malware trên raw output; p_main là xác suất malware. G_v không là xác suất model view và tổng view SHAP còn bias mới thành raw prediction.

### M4 full

Train 3 LightGBM nhỏ trên same clean train labels nhưng mỗi cái chỉ nhận feature view mình. Dùng lại view models cho các poisoned models cùng seed. Điểm chính ứng viên: `S4f=(1-p_main)*p_behavioral`. Lưu/hiển thị predictions cả Structural, Behavioral, Metadata. Behavioral là đối chiếu chính theo giả thuyết thầy; không âm thầm đổi sang max-disagreement sau nhìn test.

### M5 semantic plausibility — correction that MUST carry forward

Hướng dẫn thầy có **hai nhánh**, khi model chính quyết định benign:

1. Import/string thuộc danh sách nhạy cảm cố định, được khóa trước thí nghiệm.
2. Quyết định dựa gần như hoàn toàn vào feature Metadata hiếm, ít liên quan bảo mật.

Trước đây assistant đề xuất chỉ đo Metadata outlier; người dùng phát hiện không sát tài liệu. **Không gọi Metadata outlier đơn thuần là triển khai đầy đủ M5.** Nhánh 2 cần cả rarity và contribution kéo về benign; nhánh 1 liên quan imports/strings, không chỉ Metadata.

Người dùng đã chọn M5 ở mức nhóm feature, không truy ngược API. EMBER imports/exports bị hash; strings là aggregate statistics, không giữ toàn bộ nội dung chuỗi. Do đó không thể tuyên bố nhóm-feature score xác nhận API cụ thể. Nếu dùng hashing danh sách định trước, phải trình bày collisions/ambiguity và cách tạo bucket đúng extractor; không gọi khớp bucket là chứng cứ API chắc chắn.

Việc đầu tiên khi triển khai M5: viết đặc tả chi tiết có source cho từng nhánh, nêu cái nào thực hiện được với JSONL/vector, cái nào chỉ proxy hoặc chưa hỗ trợ. Có thể triển khai group-level proxy cho nhánh 2 bằng độ hiếm so D1-reference kết hợp benign-directed Metadata attribution. Định nghĩa dấu, normalization, cutoff và tiêu chí “ít liên quan bảo mật” trước test. Không tự đặt toàn bộ Metadata là ít liên quan bảo mật.

Nếu nhánh 1 chưa thể thực hiện đúng trong phạm vi đã chọn, báo rõ limited M5, đo ablation và giữ limitation; không tự mở rộng sang BODMAS/PE-sensitive API để thay scope. M5 không mặc định giúp ích; benign hiếm có thể kích hoạt.

### Combined scores and threshold

Thiết kế khởi đầu: biến từng component score thành empirical rank theo D1-reference; equal weights cho M3+M4 và M3+M4+M5; không tối ưu weights trên final test. D1 chỉ benign không đủ để chọn weights tối ưu recall; muốn tối ưu phải thêm development có nhãn trigger riêng và công bố giả định.

Calibrate từng phương pháp/variant riêng trên D1-calibration, mục tiêu FPR 1%. Order-statistic threshold với strict `score > tau` để BLOCK và xử lý ties; không mặc định percentile interpolation + >= bảo đảm empirical FPR <=1%. Khóa threshold/config trước final evaluation. FPR 1% calibration không bảo đảm 1% test. 0,1% và 5% là phụ nếu còn thời gian; cỡ calibration nhỏ làm tail estimates không ổn định.

## 10. Evaluation and scientific controls

- E0: distribution TADR/view scores trên model sạch/đầu độc, benign/malware/trigger.
- E1: ASR + clean model performance theo 27 configs.
- E2: TADR, STRIP, M3, M4, combined X-SENTINEL theo trigger.
- E3: paired catch/miss table; TADR misses caught by cross-view và ngược lại; case studies.
- E4: reduced vs full và with/without M5. Giữ cùng model, samples, trigger, seed; threshold riêng ở cùng calibration FPR target. Có thể ablate từng nhánh M5 nếu thực hiện được.
- E5: FPR + Wilson CI; latency mean/median/P95; rare benign cohorts.

AUROC chính: trigger vs benign; thêm trigger vs unmodified malware (ưu tiên cặp cùng malware trước/sau trigger) và clean-model controls để kiểm tra có chỉ nhận ra malware/đặc điểm phụ. Định nghĩa negative pools rõ ràng, không lẫn label malware với label trigger.

Bootstrap CIs và paired differences cùng samples; báo 3 seed, không trộn coi các lần lặp một sample là độc lập. ASR sau detector tính trên same original eligible denominator, giữ riêng recall trên toàn trigger và trên attack-successful samples.

Rare benign: entropy top 10% và size relative to import count là đề xuất; chốt exact rules từ reference trước test. Không gọi cohort “packed” nếu không có packed ground truth.

Latency: warm-up, per-file measurement; tách extraction, SHAP, view predictions/score, STRIP và end-to-end. Không gọi batch-average throughput là per-file P95. 10 ms chỉ mục tiêu tham khảo.

Negative results hợp lệ: cross-view không hơn STRIP, TADR không hữu ích, M5 không giúp, T-cross đánh bại detector. Không ép kết quả theo giả thuyết.

## 11. Dashboard and operational meaning

English Streamlit: PE upload -> verify PE -> compatible EMBER vector -> main model probability -> SHAP/view scores -> locked detector threshold -> PASS/BLOCK.

Hiển thị riêng main model malware probability/label và trigger suspicion flag. PASS chỉ nghĩa không vượt threshold; không chứng nhận an toàn. BLOCK là detector alert/policy demo, không tự xóa file hay can thiệp máy.

Không execute uploaded PE; giới hạn upload, xử lý lỗi, không giữ binaries trong repo. Missing model/calibration -> báo not ready, không fake predictions.

LIEF version compatibility: EMBER2018 originally extracted with LIEF 0.9.x. Modern LIEF adapter phải kiểm tra differences; không coi vector length đúng là tương thích hoàn toàn. Demo vector fallback có sẵn; PE extraction chưa xác minh phải được ghi experimental.

## 12. Repo, Docker, model sharing

Suggested structure:

```text
src/xsentinel/{data,attacks,baselines,detection,evaluation}/
dashboard/
configs/
tests/
docs/
scripts/
Dockerfile
compose.yaml
README.md
```

Detector signatures nhận model, x, view/config, D1-derived reference, tau, và view models nếu full. Không ground-truth/manifest. Shared scores output: sample_id, method, variant, score, threshold, flagged, latency_ms; evaluation nối labels riêng.

GitHub giữ code/config/docs, .gitignore/.dockerignore chặn datasets, PE, models, artifacts lớn, .venv, secrets. Branch theo nhiệm vụ, PR trước merge. Docker CPU, fixed direct deps/lock, volume mounts cho data/models/outputs. CI unit/integration nhỏ, không tải full EMBER.

Người dùng đang xem xét Google Drive chung cho models; **Drive chưa được setup/confirmed access**. Model downloader đọc manifest URL/size/SHA256/version, profiles demo/research, tải temp, verify rồi rename, skip verified cached file. Không upload/download qua private auth bằng workaround. Public-link vs private authenticated cần người dùng chọn khi thực sự setup.

Mỗi người không cần tải tất cả datasets/models; dashboard chỉ cần demo bundle + calibration/config/reference/view models tùy detector. Shared model bundles phải version cùng threshold/schema; checksum model để phát hiện mismatch.

GitHub remote chưa được cung cấp. Chuẩn bị local repo trước; không tự suy đoán tên repo/account hoặc xuất bản dữ liệu.

## 13. Five-week milestones

| Week | Work | Completion evidence |
|---|---|---|
| 1 | Spec/M5 clarification, data schema/splits, repo/Docker, clean model, pilot attack, reduced | Small end-to-end run; SHAP additivity; no leakage |
| 2 | 3 trigger pilots, baselines, compute benchmark | Attack viability, clean-performance controls; full-run budget |
| 3 | 27 runs, reduced/full/M5, calibration | Locked method configs and thresholds; auditable run artifacts |
| 4 | E2–E5, statistical analysis, PE dashboard | Final tables/plots + tested demo |
| 5 | Docker on second machine, report/slides, rehearsal | Reproducible submission bundle |

Write report method/limitations early. If resources insufficient, measure and report, prioritize core experiments before visuals; no silently reduced matrix presented as complete.

## 14. First actions for the new chat

1. Read this handoff and instructor PDF/baseline spec relevant sections; inspect AGENTS.md if present.
2. Audit actual workspace/.venv and dataset metadata; do not redo successful setup without need.
3. Save English method specification including clarified M5, mapping, splits, interfaces and fixed candidate formulas before experiments.
4. Implement memory-aware data loader/vectorizer and core tests; verify real samples and model shapes.
5. Build reduced detector + baseline adapters, train/attack pilot and evaluation end-to-end.
6. Benchmark and continue full matrix/full/M5, Docker/dashboard, report/slides as data becomes available.

Explain each component to user in Vietnamese: purpose -> formula -> code -> checks -> interpretation. User wants to understand and defend the research, not just receive code. Do not repeatedly request permission for already approved scope. Ask only for genuinely missing essential choices while continuing independent work.

## 15. Prompt to paste in the new chat

> Đọc X_SENTINEL_PLAN_HANDOFF.md trong thư mục Project và tiếp tục dự án theo kế hoạch đã chốt. Hãy kiểm tra trạng thái môi trường/dataset rồi bắt đầu triển khai. Giải thích từng phần để tôi hiểu. Đặc biệt giữ M5 sát hai nhánh thầy mô tả; không thay bằng Metadata outlier đơn thuần rồi gọi là semantic plausibility đầy đủ. Không dùng final test để chỉnh phương pháp, không đưa dataset/model lớn lên GitHub và chưa có kết quả nghiên cứu nào để báo cáo.

> Phạm vi là toàn bộ hệ thống, bao gồm baseline X-GUARD/TADR và STRIP theo docs/BASELINE_SPEC_ORIGINAL.md, cùng dữ liệu, attack, X-SENTINEL, evaluation, Streamlit và Docker. Đọc cả hai file trước khi triển khai; áp dụng các hiệu chỉnh khoa học trong handoff khi đặc tả gốc có khẳng định chưa kiểm chứng.
