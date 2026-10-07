# Ghép PostgreSQL và API vào X-SENTINEL — 07/10/2026

Gói đầu vào là `incoming/IAM301t.zip`. Đã nhập schema SQLAlchemy và migration đầu của bạn trong nhóm, rồi nối với `Detector.load/predict` của Project. Không nhập model demo, detector placeholder hoặc công thức fusion của gói đó. Model, ngưỡng, schema feature, M3 view_mass, M4 và kết quả primary giữ nguyên. M5 vẫn tắt; không train lại.

## Mở và sử dụng

Mở Docker Desktop và chạy tại gốc Project:

```powershell
docker compose up -d --build
docker compose ps
```

Trên máy này đã tạo `.env` chứa password ngẫu nhiên và bị Git/Docker build bỏ qua. Trên máy mới, tạo `.env` từ `.env.example`, đổi placeholder thành password ngẫu nhiên dạng hex trước khi chạy; giữ password này khi dùng lại database đã khởi tạo. Bundle primary phải có tại `outputs/primary`.

- UI: http://127.0.0.1:8501
- API docs: http://127.0.0.1:8000/docs
- PostgreSQL nằm trong mạng Docker, không mở cổng ra host. API/UI chỉ bind localhost.

Ở trang **Phân tích**, chọn dataset, cấu hình và reduced/full, nhập vector hoặc dùng reference demo, rồi nhấn **Phân tích và lưu**. Khi có thông báo **Đã lưu phân tích**, chuyển sang **Lịch sử** để đọc lại. Đổi dataset, vector hoặc method sẽ yêu cầu phân tích mới; không tự lưu thêm bản ghi khi giao diện chạy lại. Reference example được đánh dấu `demo_mode=true`.

Database lưu checksum đầu vào, bundle/model version, điểm từng method, ngưỡng, cờ, phân loại malware, cảnh báo backdoor, đóng góp view, top 10 feature, thời gian và audit. Không lưu toàn bộ vector/binary, dataset thô, poison manifests hay nhãn final evaluation. Phân loại malware và cảnh báo backdoor vẫn tách riêng.

Gửi lại cùng `request_id` và nội dung sẽ trả kết quả đã lưu. Cùng ID nhưng đổi nội dung trả 409. Yêu cầu sai schema/method hoặc thêm trường ground truth bị từ chối. Toàn bộ kết quả/score/alert/audit được lưu trong một transaction; lỗi database không được báo là đã lưu.

## Cấu trúc và migration

- `src/xsentinel/storage/`: SQLAlchemy models, kết nối/readiness và lịch sử.
- `src/xsentinel/service/`: catalog bundle được phép, adapter chấm điểm, FastAPI và HTTP client.
- `database/`: Alembic và schema SQL tham khảo ban đầu.
- `compose.yaml`: postgres → migrate → backend → dashboard.

Migration `0001_v2_multiuser` giữ nguyên từng byte từ ZIP. Migration mới `0002_primary_scores` sửa tên CHECK bị prefix hai lần trong migration đầu và lưu đúng tên từng score: TADR, STRIP, M3, hai M4 và hai fusion variants. Schema cũ chỉ có M1–M5 nên không đủ biểu diễn kết quả primary. Readiness yêu cầu đúng revision `0002_primary_scores`; không tự tạo bảng bằng `create_all` khi chạy ứng dụng.

```powershell
docker compose exec backend alembic -c database/alembic.ini current
docker compose exec backend alembic -c database/alembic.ini check
```

Nguồn nhập, SHA256 và các file đổi import namespace nằm trong `IMPORT_PROVENANCE_2026_10_07.json`. `database/schema/initial_schema.sql` và `ORIGINAL_DATA_DICTIONARY.md` là tham khảo bản đầu, không phải schema head để chạy thủ công.

## Giữ lịch sử và sao lưu

```powershell
docker compose stop
docker compose up -d
powershell -NoProfile -File scripts/backup_history.ps1
```

Lịch sử nằm trong Docker volume `project_primary_history`, không nằm trong Git hay dataset. Stop/start và recreate container giữ volume. **Không dùng `docker compose down -v` nếu muốn giữ lịch sử**, vì `-v` xóa volume. Backup tạo file custom-format dưới `backups/`, bị Git/Docker build bỏ qua; không đọc password ra terminal.

Nếu terminal chưa nhận `docker`, script backup nhận `-DockerCommand` là đường dẫn Docker CLI. Khôi phục backup là thao tác riêng cần chọn đích trước; không tự ghi đè database đang có.

## Kiểm chứng thực đã đạt

54 tests trên Windows đạt (15 cảnh báo deprecation). API so đúng điểm/ngưỡng/cờ với detector trực tiếp trên bốn reference cases (hai dataset × full/reduced). Test PostgreSQL kiểm tra sáu bản ghi, bao gồm request mới được gửi đồng thời chỉ tạo một job/audit và một trường hợp có alert. Request ID xung đột trả 409; vector V3 sai chiều, bundle lạ và trường ground truth bị từ chối.

Dashboard kết nối API đã thử bốn variants và trang lịch sử. Alembic check không tìm thấy schema drift. Bản ghi tạo từ trình duyệt đọc lại nguyên vẹn sau recreate container và restart PostgreSQL. Backup custom-format được tạo và pg_restore đọc được mục lục; chưa thực hiện restore đè database. Core source và hash JSON/CSV báo cáo primary không đổi.

## Phạm vi sử dụng

Đây là tích hợp lịch sử/API dùng local cho nhóm. Schema có users/roles nhưng **chưa có đăng nhập hoặc thực thi phân quyền**; chưa phải sản phẩm đa người dùng hoàn chỉnh. Không lấy các quyết định khoa học còn mở trong README gói gửi để thay protocol đã khóa. Binary PE V3 vẫn chưa được kiểm chứng.

Bằng chứng kiểm thử thực: `outputs/database_integration/check_2026_10_07/`. Tham khảo [Alembic về đối chiếu metadata/migration](https://alembic.sqlalchemy.org/en/latest/autogenerate.html) và [SQLAlchemy về PostgreSQL ON CONFLICT](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert).
