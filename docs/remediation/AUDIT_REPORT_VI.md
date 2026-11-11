# Đánh giá X-SENTINEL — 10/11/2026

Repo: https://github.com/concatapchay123/X-SENTINEL  
Checkout: `G:\IAM301t\X-SENTINEL`  
Nhánh: `main`  
Commit: `bb92effa7ae88a54381eca91b6cc567c73a0eccb`  
Commit local khớp `git ls-remote origin HEAD` tại lúc clone và lúc kiểm tra cuối.

Đây là đánh giá mã nguồn, cấu hình và kiểm tra cục bộ. Không sửa code dự án, không push, không quét tấn công máy chủ bên ngoài, không chạy mẫu PE. Các probe dữ liệu dùng SQLite in-memory và thư mục tạm. Repo vẫn sạch sau kiểm tra. Thư mục audit đặt riêng bên ngoài repo.

## Kết luận

X-SENTINEL có phần lõi phân tích vector EMBER 2.381 chiều, các module detector M1–M5, persistence SQL Server và AI advisory. Tuy nhiên, đường API hiện tại vẫn là demo; các cơ chế xác thực, tính toàn vẹn bằng chứng và xác nhận release chưa đủ để triển khai cho nhiều người dùng trên một mạng không tin cậy.

Vấn đề ưu tiên là quyền truy cập, nguy cơ mất dữ liệu, giao dịch audit và bằng chứng release. Dọn file, rút gọn folder và giảm dependency nên thực hiện sau khi khóa các lỗi này. Không có cơ sở để coi mọi tài liệu trong repo là rác, hay kết luận toàn bộ thuật toán có time complexity kém chỉ từ số lượng file.

## Kiểm chứng bốn nhận định ban đầu

| Nhận định | Kết quả | Bằng chứng và giới hạn |
|---|---|---|
| Nhiều file ngoài code | Đúng về sự pha trộn mục đích; chưa đúng nếu gọi repo quá lớn | 437 file, tổng 4.237.683 byte theo working tree; 1 DOCX, 2 TXT, 0 PDF. Word nguồn 934.586 byte; `docs/` 173 file, 807.779 byte; `artifacts/` 48 file, 700.711 byte. |
| Tổ chức và code thừa | Có các vùng cần hợp nhất, nhưng không nên xóa theo cảm tính | API dùng AnalysisService demo riêng, trong khi có DetectionPipeline riêng; các script release tự tạo chứng nhận; module runtime monitoring nằm ngoài package. History đã dùng truy vấn batch nên không có cơ sở cáo buộc N+1 ở đoạn đó. |
| Docker bị nhồi quá nhiều | Đúng ở dependency và phạm vi image; Dockerfile không dài | Backend Dockerfile 54 dòng, frontend 26 dòng tính theo splitlines ở checkout. Cả hai `pip install .` cùng dependency ML/DB/UI. Chưa đo kích thước image do Docker daemon không chạy. |
| Nhiều bug hệ thống | Đã xác nhận | Probe độc lập tái hiện lỗi auth, alert ownership, xóa dữ liệu theo prefix, audit commit, digest đầu vào, ép kiểu và tăng bộ nhớ metrics. Không đồng nhất mọi test fail với bug sản phẩm. |

Tài liệu thiết kế, migration, runbook, README, test fixture và checksum có thể thuộc phạm vi kỹ thuật hợp lệ. Đề xuất tách báo cáo học thuật/nguồn biên soạn ra release attachment hoặc kho tài liệu; giữ tài liệu cần để build, vận hành và tái lập. Các script `baseline_audit.py` và `validate_v3_package.py` đang phụ thuộc một số tài liệu, nên phải sửa hợp đồng kiểm tra tương ứng trước khi dọn.

## Các phát hiện theo mức ưu tiên

P1: cần xử lý trước triển khai; P2: cần xử lý cho tính đúng, độ tin cậy hoặc khả năng bảo trì. Mức độ áp dụng giả định hệ thống nhiều người dùng; một demo cô lập không có cùng mức phơi nhiễm.

### 1. P1 — Chế độ production vẫn cho phép anonymous có quyền admin và token công khai

Nguồn: `backend/src/x_sentinel/security/auth.py:77`, `:112`, `:173`, `:184`; `config.py:34`.

Mặc định `api_auth_mode=none` trả danh tính có admin/analyst/operator/evaluator. Không có ràng buộc cấm cấu hình này trong production. Khi bật auth, bộ resolver vẫn chấp nhận token cố định công khai như `token-admin`, không kiểm tra môi trường, hạn dùng hay trạng thái tài khoản từ DB.

Đã tái hiện với `settings.env='production'`: thiếu credentials vẫn lấy quyền admin khi auth none; bật bearer vẫn lấy admin bằng token định sẵn. Đây là thiết kế auth phục vụ development bị dùng ở runtime. Thay bằng cơ chế danh tính thực; production phải fail closed; token fixture chỉ tồn tại trong test dependency override.

### 2. P1 — Client có thể kích hoạt xóa job cũ bằng prefix request_id

Nguồn: `backend/src/x_sentinel/services/analysis_service.py:68–78`; API nhận `request_id` từ client tại `api/schemas.py:17` và truyền thẳng xuống service.

Với ID bắt đầu `req-be04-`, service xóa job tồn tại và commit ngay, không kiểm tra owner. Đây là ngoại lệ dành cho test lọt vào logic chạy thật. Probe tạo job cũ của người khác, dùng lại ID đó, gây lỗi inference: job cũ đã biến mất và không được rollback. Probe này xác nhận trên SQLite, không khẳng định toàn bộ hành vi cascade SQL Server đã chạy.

Xóa ngoại lệ prefix khỏi code sản phẩm. Duplicate request phải được xử lý nhất quán bằng unique constraint và chính sách idempotency/409; test tự cô lập dữ liệu.

### 3. P1 — Alert không có phạm vi owner tương ứng analysis

Nguồn: `api/routes.py:350–435`; `services/alert_service.py:33–103`; đối chiếu ownership ở `security/auth.py:279` và `services/history_service.py`.

Route kiểm tra role nhưng không truyền principal vào truy vấn/update alert. Probe qua FastAPI TestClient: analyst B mở analysis của A nhận 403, nhưng list alert theo job đó nhận 200 và PATCH alert sang acknowledged cũng nhận 200.

Nếu alert được thiết kế là hàng đợi dùng chung cho toàn SOC, phải định nghĩa quyền đó rõ ràng và tránh lộ dữ liệu của analysis bị cấm. Với quy tắc owner hiện hành của history, đây là sự không nhất quán kiểm soát đối tượng đã tái hiện. Dùng một chính sách job ownership/tenant hoặc quyền global-alert riêng cho cả list/detail/update.

### 4. P1 — Release verifier báo VERIFIED dù không có image; checklist in PASS cứng

Nguồn: `scripts/verify_release_tuple.py:79`, `:99–108`, `:173–178`, `:236`; `scripts/release_gate.py:222–234`.

Khi Docker inspect lỗi, image digest thành `sha256:candidate_build_local`. Model hash lấy từ `models/README.md`, không phải model artifact. Các cờ compatibility là True cố định. Chạy `python scripts/verify_release_tuple.py --verify-only` trên máy không có Docker daemon vẫn exit 0 và log VERIFIED.

Ngoài ra, đưa report tổng FAIL vào hàm ghi checklist trong thư mục tạm vẫn tạo đoạn `Build Test: PASS`, migration PASS và các checkbox sign-off. Nó có thể khiến người đọc tin nhầm rằng build/runtime/rollback đã được kiểm tra. Không có bằng chứng tác giả cố ý đánh lừa; vấn đề là logic sinh báo cáo.

Verifier phải từ chối khi thiếu artifact bắt buộc; tách candidate metadata khỏi release verified. Mỗi trạng thái báo cáo phải xuất phát từ kết quả kiểm tra thực, có SKIPPED/BLOCKED khi chưa chạy.

### 5. P1 — DB commit trước khi ghi audit file gây trạng thái thành công/thất bại bất nhất

Nguồn: `services/analysis_service.py:203`, `:225`.

Sau commit DB, service mới gọi `self.audit.append(result)`. Khi file không ghi được, client nhận lỗi nhưng job/result/alert đã lưu. Retry cùng request_id bị coi duplicate. Probe giả lập đúng một lỗi append và xác nhận job vẫn tồn tại trong DB.

Chọn DB audit trong cùng transaction làm nguồn chính, rồi xuất JSONL qua outbox/retry có trạng thái; hoặc định nghĩa rõ JSONL phụ trợ và không trả thất bại cho transaction đã thành công. Chỉ đảo thứ tự hai lệnh không tạo giao dịch nguyên tử giữa file và DB.

### 6. P2 — Provenance trong canonical evidence là hằng số

Nguồn: `services/analysis_service.py:134–140`.

`code_commit`, build digest, model/config/view-map hash được ghi cứng, kể cả chuỗi `git_commit_hash_v3_canonical_0002`. Đổi code/config/model không tự đổi provenance. Hash của toàn evidence chỉ chứng minh payload nhất quán với chính nó, không xác nhận payload mô tả artifact thật.

Demo đã có nhãn không phải bằng chứng khoa học, nhưng các trường được đặt tên canonical vẫn cần đánh dấu unavailable/demo hoặc lấy từ artifact thực. Tính digest khi nạp artifact, ràng buộc vào bundle bất biến và ghi cùng từng analysis.

### 7. P2 — Hai đầu vào khác nhau có cùng input_sha256

Nguồn: `services/analysis_service.py:113–115`.

Service làm tròn 6 chữ số trước khi hash, trong khi model dùng vector chưa làm tròn. Probe vector toàn 0 và vector có phần tử đầu `0.0000001`: digest bằng nhau, malware_score khác nhau. Đây là va chạm do chuẩn hóa mất dữ liệu, không phải phá SHA-256.

Định nghĩa serialization duy nhất giữ đầy đủ dữ liệu mà detector thật sự sử dụng. Nếu quantization là chủ ý, phải version hóa và inference trên chính dữ liệu đã quantize.

### 8. P1 với mục tiêu detector thật — Đường API chưa tích hợp pipeline khoa học

Nguồn: `api/routes.py:59–67`; `services/analysis_service.py:36–48`, `:89–104`; `main.py:110–112`.

API tạo DemoModelService, chỉ tính M1/M3; M2/M4/M5 bị đặt 0. Scientific mode ném RuntimeError, readiness scientific luôn false. Có module DetectionPipeline/LightGBM/fusion riêng, nhưng không phải đường API đang phục vụ. Raw PE endpoint trả 501 có chủ ý.

Đây là tính năng chưa hoàn thiện có công bố trong README, không phải bằng chứng thuật toán sai. Tuy nhiên không thể gọi phiên bản này là detector production đã chạy đầy đủ M1–M5. Nối một pipeline đã freeze và được xác minh vào service, giữ demo thành chế độ riêng rõ ràng.

### 9. P2 — Metrics tăng bộ nhớ theo số URL lạ

Nguồn: `main.py:32–44`; `infrastructure/monitoring/metrics.py:69–77`, `:185–204`.

Các đường không thuộc mẫu nhận diện dùng raw URL làm nhãn endpoint. Counter/histogram giữ dict series không có giới hạn. Probe 20 URL 404 khác nhau tạo thêm đúng 20 counter series; histogram cũng nhận các nhãn đó.

Với N URL khác nhau, bộ nhớ series tăng O(N), dù không có một analysis hợp lệ nào. Dùng route template sau routing và một nhãn cố định cho unmatched; hạn chế cardinality của giá trị nhãn, không chỉ tên key.

### 10. P2 — end_to_end latency kết thúc trước persistence và audit

Nguồn: `services/analysis_service.py:119`, `:178–225`.

Timer dừng trước khi tạo evidence, ghi DB, commit, ghi file và fsync. Probe thêm độ trễ flush: wall time khoảng 175 ms nhưng evidence end_to_end khoảng 43 ms. Một phần dedup query có nằm trong timer; không phải toàn bộ DB bị loại, nhưng giai đoạn ghi lâu nhất nằm sau timer.stop.

Đặt tên inference_only nếu chỉ đo compute. Đo request end-to-end ở ranh giới hoàn tất xử lý; tách compute, queue, persistence và audit. Không dùng giá trị hiện hành làm bằng chứng đáp ứng SLO end-to-end.

### 11. P1 — Compose thiếu bước tạo database trên volume mới

Nguồn: `docker-compose.yml:30–40`; `database/migrations/env.py:54–61`; `scripts/ensure_database.py`.

SQL Server service được healthcheck bằng SELECT 1, sau đó migrate kết nối thẳng database xsentinel và chạy Alembic. SQL Server image không tự tạo database tùy biến này từ cấu hình compose; script ensure_database có trong repo nhưng không được gọi ở luồng Compose. Alembic kết nối vào DB đích trước khi chạy migration nên không thể tự tạo DB đang thiếu.

Đây là lỗi được xác định từ cấu hình, chưa chạy thử volume sạch do Docker daemon không khả dụng. Thêm bước provision database idempotent trước migration; phân biệt quyền provision, migration và runtime.

### 12. P1 — CI mới nhất fail ở DB, không chạy đến build/test

Nguồn: `.github/workflows/ci.yml:20`, `:35–38`, `:52`; https://github.com/concatapchay123/X-SENTINEL/actions/runs/38765835797.

GitHub API xác nhận run của đúng HEAD kết thúc failure ở Gate 3 — Wait for Database Service; migration, Ruff/mypy, Docker build và pytest sau đó đều skipped. Năm run mới nhất truy vấn được đều failure.

Workflow chỉ cài unixodbc-dev nhưng connection string cần Microsoft ODBC Driver 17. Đây là thiếu prerequisite cụ thể trong YAML; metadata run chứng minh bước fail nhưng không tự chứng minh toàn bộ nội dung log/root cause của run. Cần thêm driver phù hợp và readiness, rồi chạy lại CI mới có bằng chứng release.

### 13. P2 — Dependency gộp làm cả hai Docker image mang quá nhiều chức năng

Nguồn: `pyproject.toml:13–32`; `infrastructure/docker/frontend.Dockerfile:9–13`; `backend.Dockerfile:14–19`, `:29–35`.

Frontend chỉ dùng streamlit/httpx/json/os nhưng cài cả LightGBM, SHAP, scipy, scikit-learn, SQLAlchemy, Alembic và hai hệ driver Python DB. Backend cài Streamlit. Backend system layer giữ unixodbc-dev và cả msodbcsql17/msodbcsql18, trong khi compose chọn driver17. Frontend còn copy backend source.

Tách dependency theo api/ml/ui/dev, chọn driver DB thực dùng, copy đúng package/runtime asset. Chỉ thêm multi-stage khi thực sự có build toolchain cần bỏ. Tài liệu `docs/` và `source_materials/` đã bị .dockerignore loại, nên file Word không phải nguyên nhân trực tiếp làm image hiện hành lớn. Chưa đo số MB image hay mức tiết kiệm.

### 14. P2 — Validation API ép kiểu, vô hiệu hóa luật từ chối bool/string của domain

Nguồn: `api/schemas.py:9`; `data/schema.py` trong validate_vector.

`features: list[float]` của Pydantic không strict: true thành 1.0; chuỗi "1.25" thành 1.25. Domain validator từ chối bool/string nếu nhận trực tiếp, nhưng khi qua request schema thì nguồn gốc kiểu đã mất. Đã tái hiện cả hai trường hợp.

Dùng validation strict tại request boundary và giới hạn chính xác 2.381 phần tử trước khi inference. Kiểm tra source_name/request_id theo giới hạn cột DB. max_upload_bytes hiện không thể thay thế giới hạn body/vector ở lớp HTTP; chưa thực hiện thử tải lớn.

### 15. P2 — Frontend không sử dụng được khi bật xác thực API

Nguồn: `frontend/app.py:36–40`; `security/auth.py:173–194`.

Mọi request của Streamlit đều không gửi Authorization, không có login/session/token input hay adapter cho identity. Khi auth bật, POST analysis nhận 401. Không sửa bằng cách đưa token admin công khai vào frontend.

Tích hợp identity/session phù hợp và chuyển credentials theo người dùng. Frontend này cũng chỉ là màn demo; không coi việc thiếu toàn bộ màn hình trong plan là bug runtime đã tái hiện.

### 16. P2 — Manifest không nhất quán giữa Git, line ending và artifact phân phối

Nguồn: `SHA256SUMS.txt`; `.editorconfig`; thiếu `.gitattributes`; `scripts/verify_sha256sums.py`.

Verifier trên checkout Windows: 79 verified, 357 failed, 9 missing. Phân tích tiếp trực tiếp Git blob: 360 khớp, 76 chỉ khác LF/CRLF, 0 khác biệt nội dung khác sau xét hai kiểu newline; 9 mục không được Git theo dõi. Vì vậy không kết luận 357 file bị sửa/hỏng.

Các mục missing gồm audit events, performance reports và release manifests. Một manifest của gói phát hành chứa runtime artifacts không đồng nghĩa manifest của source checkout. Khóa newline bằng .gitattributes hoặc hash byte từ một gói phát hành có định nghĩa; tách source manifest khỏi artifact manifest và kiểm tra trong CI.

### 17. P2 — Chưa tái lập được môi trường và test concurrency có hành vi không ổn định

Nguồn: `pyproject.toml` dependency ranges; `.github/workflows/ci.yml`; `tests/integration/test_be16_database_resilience.py:259–291`.

Không có dependency lock hay image digest bất biến. Bộ test chạy bằng môi trường sẵn có: pytest 9.0.3 trong khi pyproject yêu cầu pytest <9. Không cài thêm package trong lượt audit; kết quả này không thay thế một clean install theo khai báo.

Test concurrency dùng cùng một SQLAlchemy Session/repository cho nhiều thread. Full run fail IndexError, chạy riêng lại pass. Đây là test không ổn định; không đủ để kết luận production bị cùng lỗi race, cũng không đủ để chứng minh production thread-safe. Dùng session riêng cho mỗi worker và DB chia sẻ đúng mô hình runtime.

### 18. P2 — Runtime và kiểm tra package bị ràng buộc với layout repo; tối ưu cần bắt đầu từ đường thật

Nguồn: `pyproject.toml:47–51`; imports `infrastructure.monitoring` trong `main.py` và `analysis_service.py`; `api/routes.py:59–67`; `data/views.py`.

Setuptools chỉ đóng package trong backend/src, nhưng runtime import infrastructure ngoài package và đọc configs tương đối cwd. Chạy từ repo root hoặc Docker PYTHONPATH có thể che lấp vấn đề phân phối wheel/working directory. Cần kiểm chứng wheel trong thư mục sạch trước khi khẳng định cài đặt độc lập được hỗ trợ.

Mỗi request tạo AnalysisService và đọc YAML view map lại. Vector bị duyệt/convert ở request schema, service và model. Đây là chi phí lặp O(d) và I/O/config lặp, không phải bằng chứng O(d²). Có thể nạp bundle immutable một lần theo version, tái sử dụng service/model an toàn và validation một lần ở boundary. Chưa có benchmark detector thật hay dữ liệu EMBER nên không đưa phần trăm tăng tốc.

## Kết quả kiểm tra thực tế

| Kiểm tra | Kết quả |
|---|---|
| Clone và đối chiếu remote HEAD | PASS, đúng commit nêu đầu báo cáo |
| Git status sau kiểm tra | Sạch; không sửa tracked source |
| pytest toàn repo | 946 passed, 5 failed, 42 skipped, 9 warnings, 87,28 giây |
| Phân loại 5 test fail | 2 thiếu ODBC/live DB; 2 bị Windows Application Control chặn executable Alembic; 1 test concurrency không ổn định |
| Rerun riêng concurrency test | 1 passed; không xóa failure của full run |
| Ruff theo lệnh CI | PASS |
| Mypy | BLOCKED: Windows Application Control chặn DLL của mypy, không phải đã xác minh typecheck pass/fail của repo |
| Docker Compose config --quiet | PASS cú pháp cấu hình |
| Docker build/runtime/volume sạch | BLOCKED: không có Docker daemon Linux đang chạy |
| baseline_audit / validate_v3_package / verify_no_vector_db | PASS; đây là guard cấu trúc, không chứng minh runtime |
| scan_secrets | PASS theo scanner của repo; scanner không phát hiện vấn đề resolver chấp nhận token fixture |
| SHA256 verifier | FAIL; nguyên nhân newline và 9 artifact missing được phân tích riêng |
| Release tuple verify-only | Exit 0 dù không có image; đây là lỗi verifier đã xác nhận |
| Probe độc lập | 10 record trong reproductions.json; bao gồm hai trường hợp ép kiểu |
| Model/dataset thật, benchmark khoa học, SQL Server roundtrip/rollback | Chưa xác minh được; thiếu service/artifacts/dataset |
| Browser UI/E2E, active pentest bên ngoài | Không thực hiện |

Các test deployment hiện có chủ yếu đọc text Dockerfile/YAML và kiểm tra chuỗi; chúng không thay thế build image hoặc chạy ứng dụng. Không tính skipped là passed. Không tuyên bố toàn bộ 164 file Python đã được review từng dòng: đã đọc sâu entrypoints, đường API analysis/history/alerts, auth/ownership, persistence/evidence/audit, metrics và cấu hình deploy/release; phần evaluation/guardrails/model có lấy mẫu và đọc liên kết liên quan, chưa audit đầy đủ mọi thuật toán.

## Thứ tự xử lý đề xuất

1. Khóa auth production; bỏ ngoại lệ xóa job; thống nhất alert ownership; tạo regression tests từ các probe.
2. Sửa transaction/audit, provenance và digest đầu vào; làm verifier/checklist fail closed.
3. Sửa CI ODBC và provision database; build/run trên volume sạch; ghi đúng passed/skipped/blocked.
4. Chốt rõ release demo hay detector thật. Với detector thật, tích hợp pipeline/artifacts đã freeze và kiểm chứng dataset.
5. Tách dependency/image UI/API/ML; đóng gói runtime đúng cách; giới hạn metrics/body input.
6. Sau đó mới dọn tài liệu, legacy plan và artifact theo chính sách phân phối. Đo image size, startup, p50/p95/p99 và bộ nhớ trước/sau. Giữ lịch sử nghiên cứu có giá trị ở nơi truy xuất được.

## Artifact audit

- `pytest.log`, `pytest.xml`: toàn bộ kết quả chạy test.
- `reproduce_findings.py`, `reproductions.log`, `reproductions.json`: probe độc lập và kết quả.
- `inventory.json`: thống kê file/byte/extension.
- `checksum_analysis.json`: đối chiếu hash Git và LF/CRLF.
- `github_latest_ci.json`: metadata jobs/steps của CI HEAD.
- `environment.json`: version dependency thực dùng khi audit.
- `ruff.log`, `mypy.log`, `checksums.log`, `release_tuple.log`, `concurrency_recheck.log`, `ocr-rules.json`: bằng chứng bổ sung.

Không có sửa lỗi sản phẩm, commit hoặc push trong lượt này. Không tự cài tool, package hay thay đổi cấu hình máy ảo.
