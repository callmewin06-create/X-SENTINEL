# Bàn giao sửa giao diện ngày 16/10/2026

**Yêu cầu và triển khai bổ sung ngày 20/10/2026:** [UI-11 đến UI-14](UI_FOLLOWUP_2026_10_20.md) đã được sửa trong code; đọc [bằng chứng và giới hạn mới](IMPLEMENTATION_2026_10_20.md) cho UI/PDF và latency A+B. Bằng chứng ngày 16/10 bên dưới được giữ làm lịch sử, không dùng thay kết quả kiểm tra cho lần sửa mới.

Đã triển khai theo yêu cầu người dùng từ UI-01 đến UI-10. Docker hiện tại đã được rebuild và chạy bản sửa tại http://127.0.0.1:8501. Chưa commit/push GitHub trong lượt này. Báo cáo Word và kết quả nghiên cứu không được viết lại bởi đợt sửa giao diện.

**Cập nhật ghi chú ngày 16/10/2026:** bản sửa đã có commit `35c0e82` — `Fix Vietnamese UI, explanations, demo labels and PDF export`. Khi kiểm tra để ghi chú, HEAD và ref `origin/main` lưu trên máy cùng ở commit này; cây làm việc sạch trước lần cập nhật tài liệu này. Chưa fetch để xác minh GitHub trực tiếp trong lượt ghi chú. Các kết quả kiểm chứng bên dưới là bằng chứng của lần triển khai, không phải kiểm thử được chạy lại mỗi lần đọc tài liệu.

## Những gì đã thay đổi

| Mục | Bản sửa hiện tại |
|---|---|
| UI-01 | Ô kết luận, chữ, chú thích và phần mở rộng có màu phù hợp với Sáng/Tối; bỏ nền trắng cố định trên ô kết luận. |
| UI-02 | Biểu đồ nhóm có tên đầy đủ, chữ lớn hơn, phần trăm cạnh thanh; tên được xuống dòng khi cửa sổ nhỏ. Đặc trưng có phần mô tả bằng chữ bên ngoài bảng kỹ thuật. |
| UI-03 | “Vì sao có kết quả này?” so điểm với đúng ngưỡng phân loại và ngưỡng trigger riêng. Trình bày các đặc trưng đẩy về lành/mã độc bằng tiếng Việt, không suy diễn hành vi chạy từ dữ liệu tĩnh. |
| UI-04 | Chọn Reduced/Full ngay tại Phân tích. Đổi chế độ bỏ kết quả cũ không còn phù hợp; hai biến thể vẫn dùng đúng bundle và phương pháp tương ứng. |
| UI-05 | “Xuất PDF kết quả” tạo PDF từ kết quả đang xem, sau đó “Tải file PDF” tải file thật. Font tiếng Việt nằm trong gói cài đặt. Không dự đoán lại khi tạo PDF. |
| UI-06 | “Tùy chọn ứng dụng” → “Giới thiệu” có liên kết GitHub của nhóm. |
| UI-07 | Menu Streamlit mặc định và Developer options được ẩn khỏi luồng demo. Đây là thay đổi trình bày, không phải phân quyền. |
| UI-08 | Có điều khiển riêng bằng tiếng Việt: Tải lại giao diện, Giới thiệu, Giao diện Sáng/Tối/Theo hệ thống và Quay video màn hình. Không sửa thư viện gốc hay nâng phiên bản Streamlit. |
| UI-09 | Không hiện đường dẫn bundle nội bộ trên giao diện và PDF; vẫn giữ tên dataset/chế độ/cấu hình. |
| UI-10 | Mẫu demo có nhãn gốc được xác minh theo nội dung và nguồn, kèm đúng/sai khi so với dự đoán. File upload và mẫu không xác minh không được tự gán nhãn. |

Nhãn gốc của mẫu demo chỉ dùng để đối chiếu phân loại lành/mã độc, không dùng để chấm cảnh báo trigger đúng/sai. Mẫu EMBER2024 hiện có trường hợp nhãn gốc lành nhưng mô hình dự đoán mã độc; giao diện hiển thị rõ dự đoán nhầm và giữ nguyên mẫu này.

## Cách dùng

1. Mở trang Phân tích, chọn bộ mô hình và Reduced/Full, rồi chọn đầu vào và bấm Phân tích.
2. Đọc hai kết luận riêng. Mở “Vì sao có kết quả này?” để thấy phép so điểm/ngưỡng và các đặc trưng ảnh hưởng.
3. Với demo đã xác minh, đọc nhãn gốc và câu đối chiếu ngay cạnh kết quả. Một mẫu đúng/sai không đại diện độ chính xác toàn hệ thống.
4. Bấm “Xuất PDF kết quả”, rồi “Tải file PDF”. Đây là báo cáo của lần phân tích đang xem, không phải báo cáo học phần Word của nhóm.
5. Bấm bánh răng ở bên phải banner để đổi Sáng/Tối, tải lại giao diện, xem Giới thiệu hoặc mở bảng quay video. Bấm nút ba gạch bên trái để chuyển Phân tích/Lịch sử/Nghiên cứu.

## Yêu cầu bố cục bổ sung — đã được duyệt triển khai

Người dùng ban đầu yêu cầu chỉ ghi chú, sau đó đã duyệt phương án bằng yêu cầu “làm đi”. Phần dưới lưu yêu cầu và phương án đã duyệt; trạng thái triển khai mới được ghi ngay sau phương án.

1. **Cài đặt bằng biểu tượng bánh răng ở góc trên bên phải:** dùng nút ⚙️ thay cho khối chọn giao diện và nút “Tùy chọn ứng dụng” hiện tại. Bấm nút mở menu chung chứa chọn Giao diện (Sáng/Tối/Theo hệ thống), Tải lại giao diện, Giới thiệu và Quay video màn hình; bỏ nhóm tùy chọn này khỏi thanh bên khi được triển khai. Giữ tên trợ năng “Cài đặt” để nút biểu tượng dễ nhận biết.
2. **Làm nổi bật tên hệ thống:** tăng kích thước X-SENTINEL và dòng “Phân tích PE và dấu hiệu trigger”; có thể trình bày thành banner lớn ở đầu trang. Chưa chốt chi tiết bố cục/màu của banner.
3. **Điều hướng bằng nút ba gạch ở góc trên bên trái:** dùng nút ☰ để mở/đóng vùng điều hướng chứa đúng ba mục Phân tích, Lịch sử và Nghiên cứu. Mặc định thu gọn để không chiếm một cột lớn; không hiện sẵn cả khối radio và cài đặt như thanh bên hiện tại. Điều hướng và Cài đặt là hai nút riêng, ở hai phía trên của giao diện.

**Trạng thái cả ba mục: đã sửa code và kiểm tra giao diện chạy thật.**

### Phương án bố cục đã duyệt

- Một banner ngang dùng chung cho cả ba trang: nút ☰ ở trái, tên X-SENTINEL và dòng mô tả ở giữa, nút ⚙ ở phải. Trên laptop dự kiến cao khoảng 110–140 px, tên 36–44 px, mô tả 16–18 px; đây là kích thước khởi điểm để kiểm tra khi triển khai. Trên cửa sổ nhỏ giảm cỡ chữ/khoảng đệm và cho mô tả xuống dòng.
- ☰ mở một menu điều hướng gọn phía trái do ứng dụng quản lý, chứa đúng Phân tích, Lịch sử, Nghiên cứu; đánh dấu trang hiện tại. Không hiển thị cột điều hướng lớn thường trực. Nếu chọn cách tiếp tục dùng sidebar, cần xác minh cách mở/đóng được hỗ trợ trên Streamlit 1.45.1 trước khi hứa nút tùy chỉnh điều khiển được sidebar.
- ⚙ mở menu Cài đặt ở phải: chọn Giao diện đặt đầu tiên, tiếp theo Tải lại giao diện, Giới thiệu và Quay video màn hình. Hai nút có tên trợ năng/tooltip “Điều hướng” và “Cài đặt”; kích thước bấm tối thiểu dự kiến 44 × 44 px.
- Nội dung phân tích, lịch sử hoặc nghiên cứu nằm bên dưới banner; không lặp lại tên X-SENTINEL ở thanh bên. Thông tin kết nối/lưu và giới hạn kết luận vẫn có vị trí đọc được, không bỏ mất khi thu gọn thanh bên.
- Mở/đóng menu và đổi Sáng/Tối phải giữ kết quả hiện tại và không gọi detector. “Tải lại giao diện” giữ đúng ý nghĩa làm mới phần hiển thị; không biến thành lệnh phân tích lại. Giữ key điều hướng/theme và đối chiếu dataset/chế độ/phương pháp sau thay bố cục.
- Kiểm tra Sáng/Tối, cửa sổ hẹp, bàn phím, chuyển cả ba trang và thao tác với kết quả đã có. Bộ quay video dùng iframe nên phải kiểm tra ảnh hưởng của rerun/đóng menu; chưa hứa bản quay vẫn tiếp tục nếu component bị tháo khỏi trang.

### Kiểm chứng riêng cho banner/menu mới

- Banner X-SENTINEL ở đầu cả ba trang; menu Điều hướng bên trái và Cài đặt bên phải đều dùng popover của ứng dụng, không còn sidebar thường trực. Nhãn trợ năng/tooltip vẫn đọc được khi nút chỉ hiện biểu tượng.
- Theo yêu cầu bổ sung, banner được kéo gần sát hai mép cửa sổ, hai nút đi theo hai đầu banner; nội dung bên dưới giữ chiều rộng dễ đọc. Đã xem ở 1884 px và 390 px, không tràn ngang; menu Cài đặt vẫn nằm trong màn hình. Đây là thay đổi CSS, không chạy lại bộ kiểm tra mô hình.
- Yêu cầu tiếp theo: ghim thanh đầu trang khi cuộn và tiết kiệm chiều cao. Đã bỏ dòng mô tả dưới tên X-SENTINEL, giảm thanh xuống 72 px (64 px ở màn hình nhỏ), ghim ở mép trên và chừa khoảng cho nội dung đầu trang. Kiểm tra trình duyệt xác nhận cuộn nội dung nhưng thanh vẫn ở vị trí 0; menu Điều hướng/Cài đặt mở được khi đã cuộn, kể cả chế độ sáng trên màn hình 390 px. Lần chỉnh này chỉ thay phần trình bày, không chạy lại benchmark/model.
- Chỉnh tiếp theo yêu cầu: thanh ghim sát hoàn toàn hai mép (`left/right: 0`), góc vuông (`border-radius: 0`), chỉ giữ viền dưới. Đã xác nhận trên Docker ở kích thước 1280 px và 390 px; vẫn giữ chiều cao gọn và chức năng ghim khi cuộn.
- 19 kiểm tra liên quan đã pass: `tests/test_ui_revision.py`, `tests/test_primary_dashboard.py`, `tests/test_pipeline.py`. Log mới: `outputs/ui_header_2026_10_16/tests.xml`. Các kiểm tra cũ tham chiếu radio trong sidebar đã được cập nhật theo vị trí điều hướng mới.
- Đã xem trực tiếp cả ba trang, Sáng/Tối, mở menu bằng Enter và bố cục rộng 390 px. Menu cài đặt nằm trong màn hình; banner và hai nút không đè lên nhau.
- Bảng quay video nằm ngoài popover. Đã xác nhận đóng Cài đặt vẫn giữ iframe và nút Bắt đầu quay trên trang. Chưa cấp quyền/quay video thực; người dùng cần dừng và tải video trước khi tải lại trang hoặc tắt bảng quay.
- Kết quả phân tích được giữ khi đổi giao diện và xuất PDF; kiểm tra có đếm lượt gọi detector để bảo đảm không dự đoán lại chỉ để hiển thị.
- Đã rebuild và khởi động bản Docker mới tại cổng 8501. Kiểm tra Linux qua API thật đạt bốn cấu hình EMBER2018/EMBER2024 × Reduced/Full và trang lịch sử: `outputs/ui_header_2026_10_16/linux_runtime.json`. Đây là kiểm tra cùng máy vật lý, chưa thay thế nghiệm thu trên máy thành viên nhóm.
- Ảnh bản mới: `outputs/ui_header_2026_10_16/header_navigation_dark.jpg`, `header_settings_dark.jpg` và `settings_390.jpg`. Lượt sửa banner/menu chưa commit hoặc push GitHub.

Các kết quả 80 test của lần sửa trước bên dưới là bằng chứng lịch sử, không phải số test chạy lại cho thay đổi banner/menu này.

Máy khác chỉ nhận được bản sửa sau khi thay đổi này được đưa lên GitHub và máy đó pull rồi rebuild. Từ thư mục repository đã có `.env` và bộ mô hình, chạy:

```powershell
git pull
docker compose up -d --build
```

Không xóa volume database để cập nhật giao diện. Bản sửa lưu các trường bổ sung trong JSON kết quả hiện có, không cần migration schema mới.

## Kiểm chứng đã thực hiện

- Toàn bộ 80 test pass, gồm các trường hợp sát/bằng/vượt ngưỡng, dữ liệu cũ thiếu trường, demo giả, ý nghĩa/chiều SHAP, PDF và chuyển chế độ. Log: `outputs/ui_revision_2026_10_16/tests.xml`.
- So sánh bốn cấu hình thật EMBER2018/EMBER2024 × Reduced/Full: các trường kết quả cũ giữ nguyên, ngoại trừ thời gian đo. Hash của 752 file primary giữ nguyên. Log: `outputs/ui_revision_2026_10_16/verification.json`.
- API/database thật: bốn cấu hình lưu, gửi lại cùng request và đọc lịch sử khớp nhau; ba bản ghi lịch sử cũ đã đối chiếu giữ nguyên. Vector demo bị thay đổi không được gắn nhãn; nhãn do client tự khai bị từ chối. Log: `outputs/ui_revision_2026_10_16/stack.json`.
- Linux Docker: AppTest chạy bốn cấu hình thật, mở đặc trưng/chi tiết không đổi kết quả đã tính, trang lịch sử hoạt động. Không mount dữ liệu nguồn huấn luyện. Log: `outputs/ui_revision_2026_10_16/linux_runtime.json`.
- Tạo PDF trong container Linux thành công với font đóng gói. Trình duyệt tải PDF thật thành công. PDF mẫu hai trang đã được đọc text và xem hình từng trang: `output/pdf/X_SENTINEL_UI_Demo_2026_10_16.pdf`.
- Xem trực tiếp Sáng/Tối, hai ô kết luận, biểu đồ, hộp Giới thiệu; kiểm tra cửa sổ hẹp 760 và 600 px. Ảnh bằng chứng nằm trong `outputs/ui_revision_2026_10_16/`.
- Catalog demo có 108 định danh bundle/reference; nhãn được đối chiếu với role, ID và nhãn nguồn, đồng thời reference matrix được so với đúng các hàng nguồn. Nhãn chỉ gắn khi khớp schema, hash model/reference và hash vector. Không chạy thí nghiệm mới để tạo nhãn.

## Thời gian xử lý và giới hạn

Đo xen kẽ 15 lượt sau khi nạp model cho mỗi phía, cùng máy và cùng mẫu, cho thời gian tính điểm trước → sau:

| Cấu hình | Trước (ms) | Sau (ms) |
|---|---:|---:|
| EMBER2018 Reduced | 38.517 | 39.116 |
| EMBER2018 Full | 41.057 | 39.921 |
| EMBER2024 Reduced | 37.862 | 38.265 |
| EMBER2024 Full | 39.172 | 38.745 |

Đây là kiểm tra hồi quy trên máy hiện tại, không phải benchmark nghiên cứu mới. Không gồm upload, đọc PE, API/database hoặc render trình duyệt. Không kết luận hệ thống nhanh hơn hay đạt mục tiêu 10 ms. PDF mẫu tạo khoảng 94.67 ms trong một lượt đo riêng và chỉ tạo khi người dùng bấm xuất. Mở giải thích, đổi theme và xuất PDF không gọi lại detector, đã kiểm tra bằng đếm lượt gọi.

Các phần chưa xác nhận:

- Chưa nghiệm thu trên một máy vật lý thứ hai hoặc Kali của thành viên nhóm.
- Điều khiển quay video đã có nhưng chưa thử cấp quyền và quay thực tế. Việc này phụ thuộc trình duyệt và quyền chia sẻ màn hình; không quay âm thanh.
- Các thao tác do ứng dụng quản lý đã Việt hóa. Một số công cụ bảng, nhãn trợ năng và trạng thái chạy tạm thời của Streamlit vẫn có tiếng Anh. Không tuyên bố đã Việt hóa mọi chuỗi của framework.
- Theme dùng CSS trên Streamlit 1.45.1 đã cố định; cần kiểm tra lại selector khi nâng Streamlit trong tương lai.
- Dữ liệu lịch sử cũ thiếu ngưỡng phân loại/nhãn nguồn được báo thiếu dữ liệu; không tự thêm các giá trị đó vào bản ghi cũ.
