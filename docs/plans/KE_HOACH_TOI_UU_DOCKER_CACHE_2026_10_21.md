# Kế hoạch tối ưu cache Docker và căn chỉnh header — 21/10/2026

Trạng thái: **đã triển khai và kiểm tra Docker/browser ngày 21/10/2026**. Xem [kết quả, bằng chứng và giới hạn](../DOCKER_CACHE_HEADER_2026_10_21.md). Nội dung dưới đây giữ thứ tự kế hoạch đã thống nhất; phần ghi "chưa" mô tả hiện trạng lúc lập kế hoạch, không thay thế biên bản kết quả.

Bổ sung theo hai ảnh người dùng gửi: đưa nút menu về rìa trái, nút cài đặt về rìa phải màn hình như trước; căn giữa biểu tượng ba gạch và bánh răng trong hai ô vuông. Yêu cầu này được gộp và đã triển khai trong cùng đợt sửa.

## 1. Vấn đề đã xác nhận

- Lần pull gần nhất đưa HEAD tới `2226b2d`, chỉ thay đổi `src/xsentinel/dashboard_chrome.py` so với `24808d1`.
- `Dockerfile` copy `src`, dashboard và nhiều thư mục khác trước bước `pip install --no-cache-dir '.[service,binary-v3]'`. Code thay đổi làm bước cài thư viện phía sau không dùng được layer cache cũ.
- Log người dùng cung cấp cho thấy tải khoảng 200–250 kB/s. PyArrow 50,1 MB tải từ giây 241,4 đến 506,7: khoảng 4 phút 25 giây. Log tiếp tục tải scikit-learn và SciPy; phần log này chưa có lỗi.
- `--no-cache-dir` tắt cache tải của pip, không tự tắt layer cache của Docker. Khi bước cài đặt phải chạy lại, cache tải pip hiện không giúp tái sử dụng các gói.
- Người dùng đã hủy build. Chưa kiểm tra image/container sau lần hủy; không kết luận toàn bộ dữ liệu tải dở đã được giữ hoặc mất.
- Header ngoài trong `src/xsentinel/dashboard_chrome.py` đã có CSS fixed phủ viewport, nhưng hàng ba cột bên trong bị giới hạn `max-width: 720px` và căn giữa (dòng 331–337 tại thời điểm lập kế hoạch). Cột menu căn `flex-end`, cột settings căn `flex-start` (348–362), hướng hai nút vào gần logo. Đây là ràng buộc trong code cần bỏ khi trả nút về hai rìa.
- Hai ảnh người dùng cung cấp là bằng chứng cần sửa vị trí biểu tượng trong nút. CSS hiện đã có một số quy tắc căn giữa, ẩn label và SVG (365–446); chưa xem DOM/trình duyệt thật để kết luận chính xác wrapper, font hoặc phần tử phụ nào gây lệch. Không coi có `align-items: center` trong source là đã hết lỗi.

## 2. Mục tiêu và giới hạn

Mục tiêu nghiệm thu: khi chỉ sửa UI trong `dashboard/` hoặc `src/xsentinel/dashboard_chrome.py`, bước cài các thư viện bên thứ ba phải hiển thị `CACHED`, nếu layer cache vẫn còn và đầu vào dependency không đổi.

Mục tiêu UI: menu ở mép trái viewport, cài đặt ở mép phải; khoảng lề hai bên đối xứng, giữ X-SENTINEL ở giữa. Biểu tượng ba gạch và bánh răng nằm giữa ô vuông cả ngang lẫn dọc.

Giữ Python base image đã pin, các phiên bản dependency trực tiếp và extras `service,binary-v3`, bản vá oscrypto cùng URL/hash, cách đóng gói assets/phông chữ, model/bundle, ngưỡng và cách tính kết quả. Giữ PostgreSQL volume/history và cấu hình chạy dịch vụ hiện tại.

Phạm vi chính: sửa `Dockerfile`, phần header/trigger của hai popover trong `src/xsentinel/dashboard_chrome.py`, và bổ sung hướng dẫn trong `README.md`. Chỉ điều chỉnh `.dockerignore` nếu đo context cho thấy có dữ liệu thừa đáng kể. Chưa có bằng chứng cần sửa giới hạn CPU/RAM hoặc tách image backend/UI để giải quyết lần tải thư viện này.

## 3. Thứ tự triển khai

### Bước 1 — Tách lớp thư viện khỏi lớp mã nguồn

Thứ tự dự kiến trong Dockerfile:

```text
Python base image + libgomp1
    ↓
COPY pyproject.toml
    ↓
Đọc dependency bằng tomllib và cài thư viện bên thứ ba
    ↓
COPY src + dashboard + các thư mục runtime cần thiết
    ↓
pip install --no-deps .
    ↓
Thiết lập user, quyền thư mục, healthcheck và lệnh chạy
```

- Dùng `tomllib` có sẵn trong Python 3.12 để đọc `project.dependencies` và hai nhóm optional `service`, `binary-v3` ngay trong bước build. Xuất file requirements tạm trong image rồi đưa cho pip; không cần viết tay một danh sách dependency thứ hai.
- Giữ nguyên từng chuỗi PEP 508, bao gồm platform marker, direct URL và hash của oscrypto. Dừng rõ ràng nếu thiếu nhóm bắt buộc hoặc dependency chuyển sang dạng dynamic chưa hỗ trợ.
- Không dùng `requirements-lock.txt` làm lock Linux: README hiện mô tả đây là snapshot môi trường Windows, không phải lock đầy đủ cho Docker Linux.
- Ưu tiên logic xuất requirements nằm trong Dockerfile. Cách này tránh phát sinh helper ngoài mà gói BODMAS hiện chỉ sao chép một danh sách script cố định có thể bỏ sót.
- Khai báo Dockerfile frontend phù hợp với BuildKit cache mount/heredoc; nếu dùng shell block, bật dừng khi lỗi để lỗi đọc TOML không bị che bởi lệnh tiếp theo.
- Sau khi có source, cài package nội bộ với `pip install --no-deps .`. Giữ build isolation để tôn trọng `[build-system]`, hiện pin `setuptools==75.8.0`; không bật `--no-build-isolation` khi chưa chuẩn bị đủ build requirements.
- Không chỉ chuyển nguyên lệnh `pip install .` lên trên `COPY src`: package nội bộ vẫn cần source để build và đóng gói đúng.

### Bước 2 — Giữ cache tải pip qua các lần build

- Dùng BuildKit cache mount tại `/root/.cache/pip` cho bước cài dependency và bước build/cài package nội bộ.
- Bỏ `--no-cache-dir` ở những bước sử dụng cache mount.
- Cache mount giữ dữ liệu tải ở builder, không chép thư mục cache tải vào lớp image thành phẩm.
- Lớp dependency là cơ chế tăng tốc chính khi chỉ sửa UI. Cache pip giúp thêm khi lớp đó phải chạy lại; không đảm bảo tải dở sau khi hủy sẽ được tiếp tục.
- Không thêm `--upgrade` hoặc đổi phiên bản thư viện trong đợt sửa này.

### Bước 3 — Trả hai nút về hai rìa và căn giữa biểu tượng

**Vị trí thanh header:**

- Gỡ giới hạn 720 px ở hàng chứa ba cột; cho hàng header sử dụng bề rộng viewport bên trong padding.
- Bố trí menu ở đầu trái, settings ở cuối phải, hai vùng biên cân xứng để logo X-SENTINEL vẫn ở giữa màn hình. Không dùng mép của khối nội dung giới hạn 1240 px làm mép đặt nút.
- Giữ lề an toàn đối xứng; dự kiến 16 px trên desktop và 8 px trên mobile, có xét safe-area nếu thiết bị cần. Kiểm tra ưu tiên CSS để quy tắc mobile không bị `!important` của desktop đè.
- Chỉ đổi layout header và selector có phạm vi phù hợp. Không dùng selector cột quá rộng làm ảnh hưởng cột bên trong popover hoặc các khu vực khác.

**Vị trí hình trong ô vuông:**

- Kiểm tra DOM thật của hai nút trên bản Streamlit hiện tại trước khi sửa selector; xác nhận lớp bao icon, label và mũi tên phụ.
- Giữ hai nút vuông đồng kích thước, vùng bấm tối thiểu 44×44 CSS px, căn giữa icon theo cả hai trục. Chuẩn hóa padding/margin/gap và line-height ở đúng trigger cùng lớp bao icon.
- Loại bỏ phần chiếm chỗ của label/mũi tên phụ nếu nó làm lệch tâm; tránh ẩn mọi SVG một cách quá rộng vì có thể ẩn chính biểu tượng cần hiển thị.
- Căn giữa phần hình nhìn thấy trong ảnh chụp thật, không chỉ căn giữa hộp span còn chứa khoảng trống. Giữ tên nút/tooltip và thao tác bàn phím để hai nút vẫn nhận biết và sử dụng được.
- Giữ chức năng chuyển trang, chủ đề Sáng/Tối/Theo hệ thống và nội dung settings hiện có.

**Nghiệm thu UI:**

- Chụp toàn header ở 1440 px, 768 px và 390 px, ít nhất ở chủ đề Sáng/Tối. Hai nút sát hai rìa với lề đối xứng, logo ở giữa, không chồng chữ hoặc sinh cuộn ngang.
- Chụp cận hai nút để đối chiếu với hai ảnh báo lỗi: ba gạch và bánh răng phải ở giữa ô cả ngang lẫn dọc.
- Bấm mở cả hai popover tại vị trí mới; nội dung mở vào vùng nhìn thấy, không bị cắt ở mép màn hình. Kiểm tra chuyển trang, đổi theme và bàn phím Tab/Enter/Escape.
- Cuộn trang và rerun sau thao tác để kiểm tra header vẫn đúng vị trí. Kiểm tra lại trong Docker ở bước nghiệm thu stack; ảnh local không thay thế bằng chứng image đang chạy.

### Bước 4 — Kiểm tra image dùng được

- Build một image cho service `dashboard`; `migrate`, `backend`, `dashboard` hiện dùng chung tag `project-dashboard:latest`.
- Chạy `pip check` và kiểm tra import các thành phần runtime chính: X-SENTINEL, Streamlit, LightGBM, PyArrow, SciPy, FastAPI, SQLAlchemy, psycopg và phần đọc PE.
- Kiểm tra entry point `xsentinel`, assets JSON và phông chữ vẫn có trong package được cài.
- Lưu log build, thời gian và thông tin dependency vào thư mục bằng chứng mới dưới `outputs/docker_cache_2026_10_21/` khi triển khai. Không ghi password hay nội dung `.env` vào log.

### Bước 5 — Chứng minh cache hoạt động

Thử trên bản sao context tạm, giữ code làm việc nguyên trạng:

1. Build đầu sau khi sửa để tạo lớp dependency mới.
2. Sửa một comment UI trong `src/xsentinel/dashboard_chrome.py`, build lại và kiểm tra lớp dependency là `CACHED`.
3. Lặp kiểm tra với thay đổi comment trong `dashboard/app.py`.

Tiêu chí: lớp apt và dependency hiện `CACHED`; không tải lại NumPy/SciPy/PyArrow/scikit-learn ở hai lần chỉ sửa UI; các bước copy/install package nội bộ liên quan được chạy lại và package chứa source mới. Ghi thời gian thực tế từng lần, không đặt trước cam kết số giây hoặc mức tăng tốc. So hash/diff trước–sau để bảo đảm phép thử không thay đổi source gốc hoặc mất sửa đổi có sẵn.

Không chạy `--no-cache` hoặc prune cache trong bài kiểm tra này. Kiểm tra đầu vào dependency vẫn nằm trước source bằng diff Dockerfile; không đổi phiên bản thư viện thật chỉ để thử cache miss.

### Bước 6 — Chạy và kiểm tra stack

Sau khi build đạt, dùng image vừa tạo để khởi động stack. Các lệnh dự kiến chạy từng bước trong PowerShell tại thư mục Project:

```powershell
docker compose --progress plain build dashboard
```

```powershell
docker compose up -d --no-build
```

```powershell
docker compose ps -a
```

Chỉ xác nhận triển khai khi migration kết thúc mã 0, PostgreSQL/backend/dashboard đạt healthcheck và mở được giao diện mới. Kiểm tra một ca phân tích demo, lưu/đọc history và xuất PDF để phát hiện lỗi dependency/assets. Dùng dữ liệu demo đã có; không chạy lại nghiên cứu hay train model để kiểm tra tối ưu Docker.

Trên image này, kiểm tra lại menu trái/settings phải, tâm hai biểu tượng, logo ở giữa và hai popover mở không bị cắt theo tiêu chí ở Bước 3. Lưu ảnh vào thư mục bằng chứng của đợt sửa.

Nếu daemon hoặc mạng chặn việc kiểm tra, ghi chính xác phần chưa chạy. Import thành công không thay thế kiểm tra PostgreSQL và giao diện thật.

### Bước 7 — Cập nhật hướng dẫn

README giải thích:

- Lần build đầu, máy mới hoặc cache đã bị dọn vẫn cần tải thư viện.
- Chỉ sửa UI sẽ dùng lại lớp dependency khi các đầu vào lớp đó không đổi.
- Đổi `pyproject.toml`, base image hoặc bước cài dependency có thể làm lớp đó phải chạy lại.
- Build package nội bộ có thể còn cần truy cập mạng cho build requirements; chưa cam kết offline.
- Build lại image và chờ dịch vụ khởi động là hai khoảng thời gian riêng.
- Ghi nhận sửa header: menu trái, settings phải, hai icon ở giữa nút; phân biệt phần đã sửa source với phần đã xem trên trình duyệt/Docker.

## 4. Điều kiện hoàn tất

- Diff tập trung vào Dockerfile, header và hướng dẫn; thay đổi UI đúng hai yêu cầu bổ sung, giữ phiên bản runtime và logic phân tích hiện tại.
- Có bằng chứng build thật và cache hit sau cả hai loại sửa UI.
- Có kết quả kiểm tra dependency, package assets, migration/healthcheck, một ca demo/history/PDF trên stack thật.
- Có ảnh toàn header/cận icon ở các kích thước đã chọn và kiểm tra tương tác popover; không nghiệm thu chỉ từ việc đọc CSS hoặc chạy test import.
- Ghi rõ số đo, giới hạn và phần chưa xác minh. Nếu thiếu Docker daemon, kế hoạch/sửa source chỉ được báo là đã chuẩn bị, chưa nghiệm thu Docker.

## 5. Giới hạn và khôi phục

- Mạng tải hiện chậm; tối ưu cache không làm lần tải đầu trở nên nhanh ngay.
- Dependency bắc cầu hiện chưa được lock đầy đủ cho Linux. Việc cache không phải bằng chứng môi trường tái lập hoàn toàn; không mở rộng thành nâng cấp/lock toàn bộ dependency trong đợt này.
- Trước khi thay tag image khi triển khai, lưu ID/tag image đang chạy nếu có. Nếu bản mới không đạt, phục hồi đúng diff Dockerfile/header/README của đợt sửa và dùng lại image cũ nếu còn; không đụng volume database.
- Không chạy `docker compose down -v`, `docker system prune` hay tự commit/push. Không đóng gói đè các artifact bàn giao lịch sử.

## 6. Tài liệu kỹ thuật tham chiếu

- [Docker: tối ưu cache, thứ tự layer và cache mount](https://docs.docker.com/build/cache/optimize/)
- [Docker: quy tắc cache invalidation](https://docs.docker.com/build/cache/invalidation/)
- [pip install: --no-deps và build isolation](https://pip.pypa.io/en/stable/cli/pip_install/)
