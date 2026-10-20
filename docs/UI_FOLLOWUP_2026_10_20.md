# Yêu cầu sửa giao diện bổ sung ngày 20/10/2026

Người dùng đã yêu cầu triển khai các mục này, hoãn riêng BODMAS. Bốn mục đã được sửa trong code và kiểm tra chức năng bằng AppTest/PDF; trạng thái nghiệm thu trình duyệt và Docker thật ghi tại [bàn giao triển khai](IMPLEMENTATION_2026_10_20.md). Nội dung dưới giữ yêu cầu và tiêu chí, không tự chứng nhận các phần chưa kiểm tra. Các mục UI thuộc phần hoàn thiện phần mềm, không phải kết quả nghiên cứu mới.

## UI-11 Đồng bộ màu chữ giữa giao diện sáng và tối

Sửa màu chữ không đồng bộ với nền khi chọn Sáng, Tối và Theo hệ thống. Rà cả trang Phân tích, Lịch sử và Nghiên cứu; chú ý tiêu đề, chú thích, ô nhập/chọn, menu, phần mở rộng, thông báo, bảng và nội dung Bước 3.

Code hiện có hai bộ màu trong `src/xsentinel/dashboard_chrome.py`; đọc code chưa đủ xác nhận nguyên nhân từng lỗi người dùng thấy. Khi triển khai cần kiểm tra hiển thị trực tiếp, xử lý các thành phần còn giữ màu cố định hoặc không theo bộ màu đã chọn.

**Đạt khi:** chữ đọc rõ trên nền tương ứng ở cả ba chế độ, cả trang rộng và cửa sổ hẹp. Đổi giao diện giữ nguyên kết quả đang xem và không chạy lại detector.

## UI-12 Xuất PDF lịch sử phân tích

PDF của từng lần phân tích đã có qua `render_result` dùng chung tại `dashboard/app.py`. Cần làm thao tác này dễ thấy trong trang Lịch sử và bảo đảm file tải thuộc đúng bản ghi đang chọn.

Phần bổ sung là nút **Xuất PDF lịch sử đang hiển thị** để tải bảng tổng hợp. PDF có thời điểm tạo, số bản ghi và phạm vi được xuất; ghi riêng phân loại lành/mã độc và cảnh báo trigger. Danh sách hiện lấy tối đa 100 bản ghi gần nhất, nên không gọi đây là toàn bộ database. Nếu sau này có bộ lọc/phân trang, PDF phải theo đúng phạm vi người dùng chọn và mô tả phạm vi đó.

Xuất từ dữ liệu lịch sử đã lưu; không chạy lại model, không tạo thêm lần phân tích và không thay lịch sử cũ. Dữ liệu không được lưu phải ghi Chưa lưu, không dựng số 0 hoặc lấy ngưỡng của bundle hiện tại để điền cho bản ghi cũ.

**Đạt khi:** PDF tổng hợp khớp số dòng, thứ tự và nội dung danh sách; PDF chi tiết khớp bản ghi chọn; đổi bản ghi/làm mới không tải nhầm PDF cũ. Chữ tiếng Việt, tên dài và bảng nhiều trang đọc được.

## UI-13 Hiển thị đủ SHA-256 ở Bước 3

Hiện `dashboard/app.py` cắt `input_sha256` còn 16 ký tự rồi thêm dấu ba chấm. Sửa để hiển thị và sao chép đủ 64 ký tự, cho xuống dòng khi cần, không làm tràn giao diện.

Với file PE tải lên, SHA-256 của file lấy từ `input_metadata.file_sha256`. `input_sha256` là định danh vector dùng để chấm; không đổi nhãn nó thành hash file. Nếu cần hiện cả hai, ghi rõ SHA-256 file và SHA-256 vector. Mẫu demo vector không có file PE gốc thì không dựng hash file. Bản ghi cũ thiếu hash file ghi Chưa lưu.

**Đạt khi:** giá trị hiển thị/copy khớp đủ 64 ký tự với nguồn tương ứng ở kết quả mới và lịch sử; nhãn file/vector đúng; cửa sổ hẹp vẫn đọc được.

## UI-14 Bỏ biểu tượng trước ba góc nhìn

Trong phần tỷ trọng đóng góp theo ba góc nhìn, bỏ các biểu tượng trước tên Structural/Cấu trúc, Behavioral/Hành vi API và Metadata. Code hiện chèn ba biểu tượng trong `contribution_chart` tại `src/xsentinel/dashboard_chrome.py`.

**Đạt khi:** chỉ còn tên và mã nhóm; không để lại khoảng trống dành cho biểu tượng. Giữ nguyên thứ tự, tỷ trọng, thanh màu và số phần trăm. Yêu cầu chỉ áp dụng biểu tượng trước ba tên nhóm, không tự mở rộng thành bỏ mọi biểu tượng trong ứng dụng.

## Thứ tự thực hiện và giới hạn

### Sửa tiếp theo ảnh phản hồi ngày 20/10

- Sửa riêng phần hiển thị BaseWeb của toggle và radio: toggle tắt có nền xám/nút trắng, bật dùng màu accent; radio chưa chọn có nền theo theme và viền xám, đã chọn dùng accent. Không để input checkbox/radio nhận CSS nền/bo góc dành cho ô nhập chữ.
- Thêm viền focus khi điều khiển bằng bàn phím. Giữ hành vi bật/tắt và điều hướng hiện có.
- Đã kiểm tra trực tiếp trên localhost bằng trình duyệt: Sáng có toggle tắt/bật rõ, radio chưa chọn không còn chấm đen đặc; Tối vẫn đọc được cả hai trạng thái toggle. Điểm và thời gian phân tích giữ nguyên khi đổi theme/bật chi tiết. Đây là kiểm tra UI local, không phải nghiệm thu Docker/DB.
- Ảnh bằng chứng: `outputs/implementation_2026_10_20/browser/controls_light_fixed.jpg` và `controls_dark_fixed.jpg`.

Gộp UI-11, UI-13, UI-14 thành một lượt chỉnh trình bày; làm UI-12 trên luồng dữ liệu lịch sử hiện có. Nghiệm thu cả kết quả mới và bản ghi lịch sử trước buổi demo, cùng hai dataset và hai chế độ Reduced/Full khi có bundle phù hợp.

Không đổi model, công thức, threshold hoặc kết quả nghiên cứu để sửa UI. Không thêm auth, migration ownership hoặc xóa/reset database. Không dùng số test của lần sửa UI ngày 16/10 để xác nhận bốn mục này đã đạt. Lượt ghi yêu cầu ban đầu chưa sửa code; lượt triển khai tiếp theo và bằng chứng mới được ghi riêng trong bàn giao ngày 20/10.
