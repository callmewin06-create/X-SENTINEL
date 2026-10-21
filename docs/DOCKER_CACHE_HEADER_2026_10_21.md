# Docker cache và căn chỉnh header — 21/10/2026

Đã triển khai theo [kế hoạch](plans/KE_HOACH_TOI_UU_DOCKER_CACHE_2026_10_21.md). Người dùng yêu cầu đưa bản đã nghiệm thu lên GitHub ngày 21/10/2026; trạng thái đồng bộ và commit cụ thể xem lịch sử Git.

## Thay đổi

- `Dockerfile`: cài dependency bên thứ ba trước khi copy source; đọc trực tiếp core + extras `service,binary-v3` từ `pyproject.toml` bằng `tomllib`. Giữ nguyên marker Linux, URL/hash oscrypto và các phiên bản trực tiếp đã khai báo.
- Thêm BuildKit pip cache mount cho hai bước cài đặt. Sau khi copy source, cài package nội bộ bằng `pip install --no-deps .`, giữ build isolation/backend pin. Copy dashboard sau bước này để thay dashboard không nhất thiết phải đóng gói lại package.
- `src/xsentinel/dashboard_chrome.py`: bỏ giới hạn header 720 px; dùng grid ba cột, hai biên 44 px bằng nhau. Dùng đúng DOM `stColumn` thay selector `column` cũ và giới hạn selector vào hàng header trực tiếp.
- Menu về trái viewport, settings về phải; lề desktop 16 px và mobile 8 px có safe-area. Logo ở giữa; subtitle dài được cắt bằng ellipsis khi cần, các ẩn/hiện mobile hiện có được giữ.
- Xóa margin-right 8 px ở wrapper Material icon; giữ icon 22×22 px ở tâm nút 44×44 px. Ẩn riêng chevron, giữ label tiếng Việt trong accessibility tree thay vì `display:none`. Thu hẹp CSS trigger để không áp kích thước nút vuông lên các nút bên trong popover.
- README bổ sung cách build/start riêng và giới hạn cache. Compose, `pyproject.toml`, database schema, model và logic phân tích không đổi trong diff.

## Kiểm tra thực tế

Máy Windows hiện tại, Docker Desktop engine 29.7.2, Linux containers; đây không phải nghiệm thu trên máy vật lý thứ hai.

| Kiểm tra | Kết quả |
|---|---|
| Build image mới | Thành công; `outputs/docker_cache_2026_10_21/build_initial.log` |
| Chỉ thay comment ở bản sao `src/xsentinel/dashboard_chrome.py` | Lớp dependency `CACHED`; 11,276 giây wall time |
| Chỉ thay comment ở bản sao `dashboard/app.py` | Lớp dependency `CACHED`; 9,551 giây wall time |
| Source gốc trước/sau thử cache | Hash hai file không đổi bởi phép thử |
| `pip check` trong image | Không có dependency hỏng |
| Import runtime, entry point, font/JSON assets | Đạt trong container backend |
| Migration | Exited 0 |
| PostgreSQL, backend, dashboard | Healthy |
| Regression dashboard/delivery | 10 passed, 13 cảnh báo deprecation của dependency |
| Phân tích qua API + PostgreSQL thật | 4 reference demo: EMBER2018/2024 × Reduced/Full; save/readback và retry giống nhau |
| History cũ | 3 bản ghi lấy mẫu trước phép thử còn nguyên khi đọc lại |
| PDF | Tạo PDF cho 4 kết quả demo; trang history Docker tạo và tải PDF qua trình duyệt thành công |
| Browser UI | 1440, 768, 390 px × Sáng/Tối; đã lưu ảnh và đo DOM |

Hai phép thử cache dùng context sao chép trong thư mục bằng chứng, tag `project-dashboard:cache-check-20261021`; không ghi comment vào code làm việc và không thay tag `latest` đang chạy. Thời gian này chỉ là hai phép đo với cache trên máy hiện tại, không bảo đảm mọi lần build hoặc lần tải đầu có cùng tốc độ.

Trong sáu cấu hình browser, hai nút đều 44×44 px, offset giữa tâm hộp icon và tâm nút bằng 0 trong sai số số thực. Lề trái/phải là 16 px ở 1440 px, khoảng 8 px ở 768/390 px; sai lệch tâm brand tối đa khoảng 0,2 CSS px do làm tròn kích thước. Document không tràn ngang ở các phép đo ổn định. Ảnh cận cho thấy icon nằm giữa ô vuông.

Menu/settings mở được ở hai mép. Ở mobile, popover menu và settings nằm trong viewport; menu chuyển sang Lịch sử và settings đổi theme được. Enter mở settings và Tab chuyển tới nút Tải lại giao diện. Escape chưa đóng popover trong phiên thử; vẫn đóng được bằng trigger. Đợt sửa này không thêm xử lý phím riêng thay hành vi popover của Streamlit.

Các lần chạy pytest đầu bị lỗi quyền thư mục tạm/cache của môi trường. Lần nghiệm thu dùng thư mục tạm mới nằm trong workspace và tắt cacheprovider, kết quả 10/10 đạt; không sửa test để bỏ lỗi chức năng.

## Bằng chứng

Thư mục `outputs/docker_cache_2026_10_21/` (được Git bỏ qua):

- `cache_verification.json`, `build_initial.log`, `build_cache_src.log`, `build_cache_dashboard.log`.
- `pytest_verified.xml`, `stack_verification.json`, `compose_status.json`, `linux_dependencies.txt`.
- `browser_geometry.json`, `docker-header-{1440,768,390}-{light,dark}.jpg`.
- `docker-menu-mobile-dark.jpg`, `docker-settings-mobile-dark.jpg`, `history-browser-download.pdf`.
- `validate_cache.py`, `validate_stack.py` là script nghiệm thu của lần chạy, không phải dependency runtime của Dockerfile.

Image mới: `sha256:312acdd948bff8f9d9a610a04b5ebb63fb10683f8695aaab59c5126ebd60c9f7`. Image trước sửa được giữ ở `project-dashboard:before-cache-20261021` nếu cần quay lại. Stack hiện dùng `project-dashboard:latest` và volume PostgreSQL cũ.

Đã thêm bốn bản ghi có tiền tố request ID `docker-cache-qa-20261021-` và tên đầu vào `KIEM THU DOCKER CACHE ...` để nghiệm thu save/readback. Không xóa history cũ hoặc volume; không chạy lại training/nghiên cứu.

## Giới hạn

- Lần build đầu/máy mới/cache bị dọn vẫn phải tải dependency; BuildKit cache không bảo đảm tiếp tục được file tải dở sau khi hủy.
- Dependency bắc cầu Linux chưa được lock đầy đủ. Danh sách phiên bản thực tế đã lưu riêng; không gọi đây là môi trường tái lập hoàn toàn hoặc build offline.
- Các ca demo và kiểm tra PDF ở đây là kiểm tra vận hành sau thay đổi Docker/CSS, không phải đo độ chính xác hay benchmark detector. Không kiểm tra lại bố cục từng trang PDF trong đợt này.
- Chưa thử trên máy bạn cùng nhóm hoặc Kali VM. CSS header dựa vào DOM của Streamlit 1.45.1; nâng phiên bản cần kiểm tra browser lại.
