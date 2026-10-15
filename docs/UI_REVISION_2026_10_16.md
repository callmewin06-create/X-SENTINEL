# Bàn giao sửa giao diện ngày 16/10/2026

Đã triển khai theo yêu cầu người dùng từ UI-01 đến UI-10. Docker hiện tại đã được rebuild và chạy bản sửa tại http://127.0.0.1:8501. Chưa commit/push GitHub trong lượt này. Báo cáo Word và kết quả nghiên cứu không được viết lại bởi đợt sửa giao diện.

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
5. Đổi Sáng/Tối ở thanh bên. Các thao tác giới thiệu/làm mới nằm trong “Tùy chọn ứng dụng”.

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
