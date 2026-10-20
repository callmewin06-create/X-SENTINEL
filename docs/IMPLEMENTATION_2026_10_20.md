# Bàn giao triển khai ngày 20/10/2026

Đã triển khai UI-11 đến UI-14 và latency A+B; đã khảo sát fusion trên 54 cấu hình, khóa W25 trước khi kiểm tra tập mới. BODMAS chờ thành viên phụ trách. Auth tiếp tục tạm hoãn; không thay bundle primary hoặc reset database.

## Giao diện và lịch sử

- Màu chữ/nền dùng cùng bộ màu Sáng, Tối và Theo hệ thống; bảng HTML đọc dữ liệu dùng cùng palette, có cuộn khi rộng/dài. Bảng hiển thị này thay canvas dataframe để tránh hai theme khác nhau; hiện không có thao tác sắp xếp cột như dataframe cũ.
- Bước 3 hiện đủ SHA-256 file và vector, có nút copy của code block; file hash lấy từ metadata, không nhầm hash vector. Bản ghi cũ thiếu hash file ghi Chưa lưu.
- Bỏ đúng biểu tượng trước ba tên view, giữ tỷ trọng/thứ tự/màu.
- Có nút Xuất PDF lịch sử đang hiển thị, tối đa 100 bản gần nhất; PDF chi tiết đặt ngay đầu bản ghi lịch sử. Cache PDF gắn snapshot; làm mới hoặc đổi dữ liệu không tải nhầm file cũ.
- Không chạy detector khi đổi theme, xem giải thích, mở lịch sử hoặc xuất PDF. Bản ghi cũ thiếu ngưỡng không bị dựng ngưỡng 0.5; dữ liệu thiếu không bị biến thành 0/sạch.

## Đường tính gọn và tốc độ

API lưu kết quả và dashboard local gọi scope=selected; hàm score_input mặc định vẫn giữ suite để tương thích các script cũ và công cụ BODMAS đã bàn giao. Detector.predict giữ đường suite, predict_selected tính chính xác method được chọn. Full chỉ cần Behavioral model khi tính M4-F; STRIP chỉ chạy khi chọn STRIP. Danh sách method chưa tính được ghi riêng, không tạo điểm giả.

B đã cache chỉ số view bất biến trong mỗi detector và dùng lại phân rã SHAP; không đổi model, SHAP hoặc công thức. So với đúng source Detector và components ở HEAD trước sửa, 400 vector duy nhất trên bốn cấu hình cho cùng xác suất, SHAP, điểm thành phần được tính và flags với sai số điểm tối đa cho phép 1e-12.

| Dataset | Chế độ | Suite cũ trung bình ms | Core gọn trung bình ms | Giảm | P95 core ms |
|---|---|---:|---:|---:|---:|
| EMBER2018 | reduced | 25.46 | 20.35 | 20.1% | 21.35 |
| EMBER2018 | full | 26.05 | 20.62 | 20.9% | 21.46 |
| EMBER2024 | reduced | 23.87 | 18.42 | 22.9% | 19.36 |
| EMBER2024 | full | 24.19 | 18.69 | 22.7% | 19.42 |

Mỗi cấu hình đo 100 vector, xen kẽ warm trên cùng Windows host; 50 benign và 50 malware có vector trigger. Core chưa gồm upload, parse PE, API, DB, browser hoặc tạo PDF. Thời gian serialize đầy đủ của hàm Python, cold load và các phần classifier/SHAP/view/khác có trong latency.json. Không cộng các P95 thành P95 tổng. SHAP vẫn chiếm phần lớn thời gian; **chưa đạt mục tiêu 10 ms**, không hứa kết quả tương tự trên VM 2 vCPU.

## Fusion M3 M4

Đã khóa sáu rule W25/W50/W75/MAX/M3-rank/M4-rank, mỗi rule có ngưỡng riêng từ calibration benign cũ. Dùng Final cũ làm Development đã quan sát; không gọi đây là validation mới. Chọn một rule chung cho hai dataset ở mỗi biến thể theo macro recall trên ba cohort confirmed khả dụng, tie theo FPR và chi phí. Kết quả khóa: W25 cho cả Reduced và Full; khóa được ghi trước khi chuẩn bị/chấm tập mới.

Tập mới có 1.000 benign + 1.000 malware mỗi dataset, loại ID primary/pilot/Fresh cũ trước dự đoán. Kiểm kê bổ sung 14 nguồn lịch sử local sau đó cho overlap 0; không loại hoặc thay mẫu sau khi xem kết quả. EMBER2024 gồm Win32/Win64/.NET và giữ cả 2 hàng is_pe=0 theo chính sách đã khóa. Không biết đầy đủ lịch sử quan sát ngoài nhóm. Cùng source IDs được dùng lại qua các model; số run không phải số mẫu độc lập.

Các số dưới là trung bình run của cohort được xác nhận trong protocol gốc; Restricted2018 12 run, Restricted2024 3 run, Cross2024 9 run. Không có confirmed Cross2018.

| Dataset và nhóm | Chế độ | Recall W50 | Recall W25 | FPR W50 | FPR W25 |
|---|---|---:|---:|---:|---:|
| EMBER2018 restricted | reduced | 35.76% | 51.24% | 0.400% | 0.900% |
| EMBER2018 restricted | full | 43.62% | 54.72% | 0.900% | 1.425% |
| EMBER2024 restricted | reduced | 52.00% | 45.70% | 0.933% | 0.767% |
| EMBER2024 restricted | full | 60.51% | 65.95% | 0.867% | 0.867% |
| EMBER2024 cross | reduced | 0.00% | 0.00% | 1.000% | 0.778% |
| EMBER2024 cross | full | 5.73% | 10.84% | 1.233% | 1.011% |

**Giữ W50 làm primary.** W25 cải thiện Full trong các cohort trên nhưng FPR tăng ở restricted2018; Reduced bị giảm recall trên restricted2024. Cross vẫn yếu: Full W25 khoảng 10.84% recall, còn thấp hơn M4-F raw riêng khoảng 13.29%; Reduced vẫn 0% ở cohort Cross. Đây là tradeoff có bằng chứng, không phải bản sửa giải quyết được mọi attack. W25 chỉ là supplement được version riêng, chưa gắn vào UI hoặc thay bundle/report đã khóa.

Điểm/ngưỡng, ID, số đếm, cohort, post-ASR, controls M3/M4 rank và raw có trong outputs/fusion_binary_latency_2026_10_20. Raw và rank là hai control khác nhau; ECDF có thể bão hòa/tie nên không được gọi M3-rank là đúng detector M3 raw cũ. Không huấn luyện lại model nghiên cứu. Shadow vẫn chỉ là đối chứng bổ sung có thêm model; không thay Reduced/Full.

## Kiểm chứng và giới hạn vận hành

- 87 tests pass trong lượt tổng, thêm 1 API readiness test pass sau khi được cấp quyền chạy ngoài sandbox: tổng 88 kiểm tra không thuộc BODMAS đạt. Sandbox trước đó kẹt ở socketpair/Windows asyncio trước logic API; không sửa logic API để né lỗi môi trường. Sau sửa cuối, 24 test UI/đường chọn method được chạy lại và đạt. Có cảnh báo cleanup thư mục tạm của sandbox sau khi pytest đã báo pass; các báo cáo JUnit và mã thoát của lượt đạt được giữ lại.
- AppTest kiểm tra hai dataset × hai biến thể, đổi theme/chi tiết/PDF không rescore, history dùng snapshot giả lập đúng route đọc; snapshot đổi vô hiệu PDF cũ. Đây không thay thế DB thật.
- PDF chi tiết 2 trang và lịch sử 5 trang đã render, đọc text và xem đủ 7 ảnh: tiếng Việt, hash đầy đủ, tên dài và ký tự <>&, bảng lặp header, dữ liệu thiếu và thứ tự 45 bản ghi đều đạt. Đây là dữ liệu QA, không phải lịch sử DB thật.
- Hash 752 file primary giữ nguyên sau benchmark. Chưa commit/push; báo cáo IEEE không được viết lại.
- Trình duyệt thật đã kiểm tra Sáng/Tối/Theo hệ thống (OS đang dark), kích thước 1280 và 390 px: hash file/vector đủ 64 ký tự, ba view không còn icon trước tên, không tràn ngang ở 390 px, màu chữ chuyển đúng palette và kết quả giữ nguyên khi đổi theme. Đã upload fixture lành tự xây dựng vào server localhost, đọc tĩnh rồi tải PDF thật; nội dung PDF tải về khớp cả hai hash. Ảnh và dữ liệu DOM kiểm chứng ở browser/; server xem thử chỉ bind 127.0.0.1:8510, chế độ local chưa nối DB.
- Docker daemon hiện không hoạt động; chưa rebuild stack hoặc kiểm tra PostgreSQL thật. Không lấy API readiness dùng DB giả hoặc history AppTest làm bằng chứng DB thật đã được nghiệm thu.

## Demo và bàn giao

Ba file lành cùng mã nguồn/hash/kết quả đã chuẩn bị tại output/demo_2026_10_20. Hai chương trình mới đã chạy chức năng đơn giản; cả ba được phân tích tĩnh trên bốn bundle cố định. EMBER2024 báo nhầm cả ba chương trình lành trong cấu hình này; giữ kết quả và nguồn nhãn, không dùng bộ demo để ước lượng accuracy/FPR. File độc/disarmed và kết quả BODMAS vẫn chờ bạn phụ trách; không tải hay thực thi malware trong lượt này.

Để cập nhật máy demo dùng Docker sau khi daemon hoạt động, chạy docker compose up -d --build tại repository có .env và model hiện có. Không xóa volume. Gói BODMAS đã gửi trước được giữ nguyên snapshot; không tự đưa các thí nghiệm fusion vào gói ấy.
