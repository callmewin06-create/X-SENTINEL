# Dashboard và Docker đã kiểm chứng — 07/10/2026

**Cập nhật sau khi ghép ZIP của nhóm:** Compose hiện có PostgreSQL/API và trang lịch sử. Trên máy mới cần `.env`; xem [hướng dẫn tích hợp mới](database/INTEGRATION_2026_10_07.md). Bằng chứng và mô tả kiểm tra bên dưới giữ mốc dashboard trước khi ghép database.

Đã đọc lại kết quả, kiểm tra bundle mới và chạy dashboard thật trong Docker Desktop trên máy này. Không train lại, sửa model/ngưỡng/kết quả cũ, commit, push hay upload dataset. [Bản đọc kết quả](results/PRIMARY_RESULTS_REVIEW_2026_10_07.md) trình bày cả kết quả âm và giới hạn.

## Những việc đã kiểm tra

- Đối chiếu 54 final cells, nạp cả 108 bundle, tái tính metrics từ predictions và tái dựng báo cáo; khớp bằng chứng gốc.
- Toàn bộ 50 tests trên Windows đạt; 14 cảnh báo deprecation từ thư viện.
- Dashboard tìm đủ 27 cấu hình mỗi dataset; chọn đúng reduced/full và phương pháp mặc định tương ứng. Bundle sai dataset bị từ chối.
- Docker image build thành công; container `project-dashboard-1` healthy. Linux Python 3.12.10, UID 1000; Windows Python 3.12.14.
- Bốn trường hợp smoke test trên Windows và Linux (hai dataset × hai variant) có điểm số, ngưỡng, cờ và ba metrics giống nhau; sai khác điểm/ngưỡng tối đa 0. Đây là kiểm tra bốn reference examples, không bảo đảm mọi môi trường hoặc mọi đầu vào đều giống từng bit.
- Trong trình duyệt thật, đã đổi dataset/variant và thử nhập vector V3 hợp lệ. Vector 2381 chiều bị từ chối khi chọn EMBER2024 cần 2568 chiều.
- Docker chỉ mount `outputs/primary` read-only, không mount dataset; cổng chỉ mở tại `127.0.0.1:8501`. Giới hạn 4 CPU, RAM 8 GiB là giới hạn tối đa, không phải lượng luôn sử dụng. Có healthcheck và no-new-privileges.

Bằng chứng nằm tại `outputs/primary_review/review_2026_10_07/`: `review.json`, `dashboard_windows.json`, `dashboard_linux.json`, `platform_comparison.json`, `docker_status.json`, `docker_mounts.json`, `linux_dependencies.txt`, `deployment_verification.json` và ảnh giao diện. Các file này là bằng chứng mới; không ghi đè artifacts nghiên cứu.

## Mở và tắt trên máy này

Mở Docker Desktop, chờ engine sẵn sàng, rồi chạy PowerShell:

```powershell
Set-Location -LiteralPath 'D:\.f tư bản ko cho t ngủ\IAM302t\Project'
docker compose up -d --build
docker compose ps
```

Mở [dashboard local](http://127.0.0.1:8501). Hiện đã có container chạy, bạn có thể mở ngay. `--build` dùng khi code thay đổi; lần sau có thể chỉ chạy `docker compose up -d`.

Nếu PowerShell chưa nhận lệnh `docker`, mở terminal mới hoặc thay từ `docker` đầu mỗi lệnh bằng:

```powershell
& "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe"
```

Ví dụ đầy đủ:

```powershell
& "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe" compose ps
```

Khi không dùng demo, dừng để giảm tài nguyên:

```powershell
docker compose stop
```

Lệnh này dừng dashboard, giữ nguyên image và dữ liệu/bundle. Mở lại bằng `docker compose up -d`. Không cần chạy lại pipeline nghiên cứu.

## Dùng dashboard

1. Chọn Dataset, `Primary research`, family/seed/poison rate trong `Research experiment`, rồi `Bundle variant` reduced hoặc full. Có đủ 27 cấu hình mỗi dataset, kể cả attack không đạt heuristic.
2. `Example reference vector` là demo từ reference benign; không phải kiểm chứng trên một mẫu độc lập. Có thể vẫn bị main model dự đoán malware: đó là false positive thực của model, không phải lý do để sửa nhãn hoặc ngưỡng. Cảnh báo backdoor là câu hỏi riêng.
3. Muốn thử vector riêng, chọn `EMBER vector (.npy)` và nhập đúng một vector hữu hạn: 2381 chiều cho EMBER2018, 2568 cho EMBER2024, đúng thứ tự schema. Không lấy tùy ý file NPY bất kỳ trong dataset vì nhiều file là batch lớn.
4. `Raw EMBER record (.json)` cần đúng schema dataset. Binary PE V2 vẫn là đường experimental; V3 chưa có binary extraction được kiểm chứng. Không xem demo này là sản phẩm antivirus hoàn chỉnh.

Bạn trong nhóm cần code/runtime tương ứng và toàn bộ bundle nguyên vẹn dưới `outputs/primary/EMBER2018/...` và `outputs/primary/EMBER2024/...`. Clone Git đơn thuần chưa có model vì outputs/models đang bị Git bỏ qua. Demo không cần tải dataset thô; không commit/push dataset để chia sẻ.

## Phạm vi xác nhận

Đã kiểm tra Windows + Docker Linux/WSL2 trên máy này, không phải mọi kiến trúc. Base Python được pin digest trong Dockerfile, các dependency trực tiếp đã pin; `linux_dependencies.txt` ghi phiên bản thực của image đã thử. Apt và dependency gián tiếp chưa khóa hoàn toàn, nên build tương lai có thể khác. M5 và kiểm chứng binary PE nằm ngoài đợt này.
