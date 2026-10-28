# Đồng bộ web demo ngày 28/10/2026

## Thay đổi

- Đổi nhãn hiển thị M3/M4-R/M4-F sang VMC/BGS/BPG; giữ nguyên khóa bundle, công thức, phân loại `>=` và cảnh báo `>`.
- Reduced hiển thị VMC + BGS; Full hiển thị VMC + BPG và giải thích mô hình Behavioral sạch. Hai đầu ra phân loại và cảnh báo là hai kết quả riêng, không được gọi là độc lập.
- Sửa Giới thiệu, biểu đồ và lịch sử: bỏ khẳng định khắc phục mọi trigger phân tán, dùng import/export tĩnh, gọi các nhãn lịch sử là dự đoán. Badge API chỉ xác nhận đã cấu hình, không giả định API/PostgreSQL online. Giới hạn hiển thị là 50 MiB; FPR 1% được giới hạn rõ ở calibration.
- Trang Nghiên cứu thêm số liệu đã chốt: primary 54 cấu hình/108 bundles, matched-FPR/pAUC, ngân sách sạch, adaptive, seed 59/71 và audit binary. Giữ cả kết quả thất bại; không biến các số tổng hợp thành độ chính xác của mẫu đang chọn.
- Dữ liệu tổng hợp được tạo từ CSV bằng `scripts/build_research_status_2026_10_28.py`, ghi nguồn/hash vào JSON đóng gói. Runtime dùng `assets/research_status_2026_10_28.json`, không cần mount output nghiên cứu. Loader báo thiếu/hỏng thay vì tạo số liệu giả.
- PDF kết quả dùng cùng tên/giải thích và bổ sung giới hạn calibration/adaptive. Không thay schema database hoặc viết lại lịch sử cũ.

## Kiểm tra

- 37 kiểm thử liên quan đạt, gồm loader dữ liệu nghiên cứu, dashboard, provenance demo, ranh giới ngưỡng, xuất PDF và đổi chế độ/theme không chấm lại. Có 13 cảnh báo deprecation của thư viện plotting.
- Đối chiếu 44 kết quả suy luận: 4 bundle EMBER2018/2024 × Reduced/Full, mỗi bundle một fixture PE lành và 10 mẫu reference. Tất cả đầu ra quyết định, điểm và ngưỡng trùng baseline khi loại các trường thời gian đo. Script baseline cũ chỉ loại elapsed_ms nên phép so thô ban đầu khác ở phase_timings_ms; không sửa scoring để làm cho kiểm tra qua.
- Baseline SHA256 ghi đủ 752 file primary. Bằng chứng và log ở `outputs/web_sync_2026_10_28/`.
- Kiểm tra trình duyệt thật ở chế độ local: trang Phân tích và Nghiên cứu, số liệu binary, bố cục sáng/tối. Ảnh chụp `research-binary-light.png`, `research-binary.png` và `research-overview.png` trong thư mục bằng chứng.

Docker engine chưa kết nối được trong lần kiểm tra này; không tuyên bố đã rebuild hoặc nghiệm thu stack Docker/API/PostgreSQL. Đã mở bản local tại http://127.0.0.1:8501 bằng môi trường Python hiện có, không ghi/xóa dữ liệu lịch sử. Khi dùng Docker trở lại, cần dừng server local đang giữ cổng 8501 rồi chạy `docker compose up -d --build`, giữ volume PostgreSQL.

## Đính chính mô tả schema trong manuscript

Khi đối chiếu web với source, phát hiện một câu trong bản Word đang xếp file size và section-hash tails vào Metadata. Theo `src/xsentinel/schema.py`, file size và section features thuộc Structural; Metadata gồm byte/entropy và chuỗi (các phần bổ sung V3 theo schema). Không sao chép câu đó sang web. Đây là mô tả cần chỉnh trong manuscript; lần đồng bộ web này không sửa DOCX hoặc thay phân nhóm thực tế.

Câu thay thế cho đoạn đó: “Structural includes file size and section statistics, while Metadata includes byte and entropy histograms and string statistics; exact feature membership follows the versioned schema.”

Không commit/push trong lần đồng bộ này.
