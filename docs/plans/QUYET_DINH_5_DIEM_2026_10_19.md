# X-SENTINEL - Quyết định về năm điểm ngày 19/10/2026

## Trạng thái và căn cứ

Người dùng đã chốt năm lựa chọn dưới đây sau khi yêu cầu ghi lại các điểm chuẩn bị quyết định. Đây là phê duyệt định hướng công việc, không phải bằng chứng code đã được sửa hay thí nghiệm đã hoàn thành.

Ghi chú này thay trạng thái "chờ chốt" của [bản thảo cùng ngày](CAC_DIEM_CHO_CHOT_2026_10_19.md). Các quyết định và artifact đã khóa trước đó được giữ nguyên, trừ các bổ sung được nêu rõ tại đây.

## Nguyên văn quyết định của người dùng

> 1/ cứ theo hướng m đã đề xuất
>
> 2/ chắc vẫn theo hướng m nhưng nếu được thì cứ thử các hướng để tìm ra cách ghép tốt hơn cho M3 và M4
>
> 3/ vẫn giữ là giới hạnh nhưng vẫn làm thêm trên tập BODMAS
>
> 4/ chọn theo A kết hợp B của m không chọn C
>
> 5/ tạm thời bỏ qua tại nhóm t đang bất đồng ý kiến có đứa nó kêu khỏi cứ để chạy local trên máy xài lịch sử có sẵn trên database

## Phạm vi đã chốt

### 1. Cross-view stress: theo đề xuất đã trao đổi

- Giữ kết quả primary hiện tại và công khai giới hạn khi trigger sửa cả ba view. Không biến mục tiêu thành bắt buộc X-SENTINEL phải thắng mọi trigger.
- Có thể khảo sát cải tiến có giới hạn bằng các tín hiệu và model đang có; gộp với vòng thử fusion ở mục 2 để không làm hai ma trận trùng nhau.
- Full/Reduced vẫn là hai biến thể chính. Các thử nghiệm thêm dùng phiên bản và nơi lưu riêng.
- Shadow chỉ là đối chứng có thêm clean full model; không thay X-SENTINEL thành phương pháp chính. Không lấy số Shadow tốt trên restricted để kết luận nó đã giải quyết Cross.
- Chỉ giữ một cải tiến khi có bằng chứng phù hợp về Recall, báo nhầm và tài nguyên. Kết quả âm vẫn được giữ và báo cáo.

### 2. M3/M4: được thử các cách ghép để tìm phương án tốt hơn

- Người dùng cho phép thử các hướng ghép M3/M4, không giới hạn ở công thức trung bình hiện tại.
- Ưu tiên một tập ứng viên nhỏ, rõ ràng: giữ trung bình hiện tại làm mốc; xem xét các trọng số khác, max của điểm đã chuẩn hóa và các quy tắc kết hợp đơn giản. Thành phần riêng M3/M4 cũng phải được giữ để đối chiếu.
- Chốt danh sách ứng viên và quy tắc chọn trước khi chấm tập đánh giá cuối mới; không tìm kiếm mở vô hạn hoặc chọn kết quả đẹp sau khi xem đáp án.
- Chọn lại ngưỡng cho toàn bộ rule mới bằng benign calibration riêng. OR/max không được tự kế thừa tuyên bố FPR 1% từ các ngưỡng thành phần.
- So trên cùng input IDs và model; nêu rõ khác biệt quyền truy cập của Reduced, Full và Shadow. Không dùng nhãn trigger thật để chọn method lúc inference.
- Original Final và Fresh trong report đã được xem. Có thể dùng để phân tích/phát triển, nhưng bằng chứng đánh giá cuối cho phương pháp đã thay đổi cần nguồn chưa dùng khác. Nếu không có, chỉ gọi kết quả mới là thăm dò.
- Không tự sửa ngược M3/M4, trọng số hay threshold của các bundle primary đã khóa. Việc thử fusion không tự cho phép đổi M3 chính thành polarity contrast hoặc thêm M5.

### 3. Binary: giữ giới hạn, bổ sung kiểm tra BODMAS

- Vẫn ghi rõ chưa chứng minh trigger hiện thực được trên malware binary và giữ nguyên chức năng. Đây không phải điều kiện bắt buộc bổ sung cho toàn bộ nghiên cứu vector hiện tại.
- Đã đồng ý làm thêm trên tập BODMAS, trước mắt theo đường đọc và phân tích tĩnh: binary -> parser -> vector đúng schema -> model/ngưỡng đã khóa -> kết quả và lỗi.
- Chọn mẫu bằng quy tắc xác định trước và ghi nguồn/mã định danh; báo cả mẫu đọc lỗi. Không chọn chỉ những mẫu detector dự đoán tốt.
- Muốn đánh giá báo nhầm phải có mẫu lành đối chứng. Malware thông thường không có nhãn trigger của nhóm, nên không gọi tỷ lệ cảnh báo trên BODMAS là Recall phát hiện backdoor.
- Không khôi phục khả năng chạy hoặc thực thi malware từ phê duyệt này. BODMAS disarmed không tự chứng minh chức năng malware sau sửa.
- Người dùng thiếu dung lượng và đã nêu phương án nhờ một bạn trong nhóm tải vào môi trường máy ảo. Chưa xác nhận người thực hiện, đường dẫn ZIP/mẫu, metadata hoặc môi trường thực tế. Chưa có bằng chứng đã tải hay chạy; không tự tải toàn bộ 67,9 GB vào máy người dùng.
- Có thể chuẩn bị công cụ kiểm tra, quy trình chọn mẫu và mẫu kết quả trong lúc chờ dữ liệu. Chỉ hỏi bổ sung thông tin đầu vào còn thiếu khi cần, không hỏi lại việc có làm BODMAS hay không.

### 4. Latency: chọn A kết hợp B, loại C

- A: thiết kế đường tính gọn chỉ chạy thành phần cần cho method được chọn; giữ đường so sánh đầy đủ khi cần STRIP và các đầu ra phụ.
- B: đo riêng chi phí từng phần, tối ưu việc thực thi/dùng lại kết quả dựa trên đo đạc.
- Không chọn C: không đổi model, giảm mô hình hay thay SHAP bằng xấp xỉ chỉ để đạt mục tiêu tốc độ.
- Giữ nguyên phép tính, model và ngưỡng của method chính. Kiểm chứng điểm/alert khớp đường cũ trước khi dùng đường gọn.
- Response/history phải phản ánh đúng những phần đã tính; không điền 0 cho phần chưa tính. Giữ tính nhất quán khi mở giải thích/PDF và khi retry request.
- Đo tách warm/cold, core/complete và phần đọc file/API/database; không lấy cache hit làm thời gian suy luận mới.
- 10 ms vẫn là mục tiêu để đo và thảo luận, chưa có cam kết sẽ đạt. Không báo đã nhanh hơn khi chưa có phép đo mới.

### 5. Xác thực: tạm hoãn, giữ local và lịch sử database hiện có

- Nhóm chưa thống nhất về đăng nhập/phân quyền, nên người dùng yêu cầu tạm thời bỏ qua hạng mục này.
- Giữ cách chạy local, lịch sử dùng chung từ database hiện có. Bảo toàn lịch sử; không reset/xóa database hoặc tự chia owner cho dữ liệu cũ.
- Không tự triển khai login, API key, gateway hay migration ownership trong phạm vi hiện tại.
- Giữ giới hạn cổng local hiện có; không mở LAN/Internet để bù cho việc chưa có xác thực.
- Trạng thái phải ghi là "tạm hoãn/chưa triển khai", không phải "đã khắc phục" hoặc "không bao giờ cần". Nhóm có thể quyết định lại sau.

## Cách tổ chức công việc tiếp theo

1. Gộp khảo sát Cross và fusion M3/M4 thành một kế hoạch thử có số ứng viên hữu hạn và tiêu chí chọn rõ.
2. Khảo sát dữ liệu/score cache và nguồn chưa dùng sẵn có; khóa protocol và phiên bản trước khi chạy đánh giá mới.
3. Chuẩn bị phần BODMAS để bạn cùng nhóm có thể chạy kiểm tra tĩnh trên dữ liệu được cấp. Dữ liệu thực tế còn thiếu không ngăn phần chuẩn bị độc lập.
4. Thực hiện tối ưu latency A+B và kiểm tra tương đương kết quả; giữ riêng với các thí nghiệm đổi phương pháp ở mục 1-2.
5. Không đưa auth vào kế hoạch thực hiện hiện tại; giữ local/shared history.

## Các điều không được suy ra từ phê duyệt

- Không có phê duyệt thay Shadow thành detector chính, thêm M5, mở dataset/attack family mới ngoài nội dung trên hoặc huấn luyện lại toàn bộ ma trận chỉ để tìm số đẹp.
- Không thay các model/bundle primary đã khóa, không ghi đè report IEEE hiện tại và không gọi kết quả thăm dò là đánh giá độc lập.
- Không tự download toàn bộ gói malware, khôi phục khả năng chạy, thực thi mẫu, chia sẻ malware hoặc mở dịch vụ ra mạng.
- Không tự commit/push. Nghiệm thu trên máy vật lý khác, dữ liệu BODMAS và thời gian xử lý mới chỉ được công nhận khi có bằng chứng thực tế.
- Không dùng trạng thái công việc trong ghi chú thay cho kết quả đo, kiểm thử hoặc phê duyệt triển khai công khai.

## Nhật ký

- 19/10/2026: người dùng chốt năm lựa chọn; cập nhật tài liệu quyết định và đường dẫn handoff. Bước cập nhật này chưa sửa code, model, ngưỡng, database hoặc chạy nghiên cứu mới.
