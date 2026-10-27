# Kế hoạch tiếp nhận kết quả BODMAS — 23/10/2026

**Đã triển khai phần dùng kết quả hiện có ngày 23/10:** sau khi người dùng chốt “đủ rồi thì làm phần bodmas đi”, đã tổng hợp bằng chứng, tạo bảng và bản sao báo cáo có Appendix C. Đọc `docs/BODMAS_RESULTS_2026_10_23.md` để xem nghiệm thu. Các thông tin còn thiếu bên dưới được giữ thành giới hạn; chưa chạy lượt 50 file lành và chưa sửa ngược dữ liệu gốc.

Kế hoạch trước đã có trong `docs/HUONG_DAN_BODMAS_KALI_2026_10_19.md`. Tài liệu này là bước tiếp theo sau khi nhận `BODMAS_RESULTS.zip`: kiểm tra bằng chứng, tổng hợp đúng kết quả, bổ sung phần thiếu rồi đưa vào bài báo/demo. Chưa chạy lại mẫu, đổi model/ngưỡng hay sửa báo cáo IEEE trong lượt lập kế hoạch này.

## 1. Đã kiểm tra được gì từ ZIP?

- ZIP 419.573 byte, 74 mục; chỉ có CSV/JSON/ghi chú/log, không có file thực thi mẫu. Kiểm tra CRC của archive đạt. SHA-256 archive: `c528ef4931a672123d47bfd30b6e0bdc5ceb4b18d2cf5a5d296f030dc31d8a87`.
- Có đủ 16 lượt: smoke1, benign1, pilot20, bodmas200; mỗi nhóm có EMBER2018/2024 × Reduced/Full.
- Bốn lượt chính dùng cùng 200 hash file và cùng 25 mẫu lỗi. CSV khớp các dòng trong summary; thứ tự, hash và kích thước khớp manifest. Các manifest có checksum nội dung hợp lệ.
- 20 mẫu pilot nằm trong 200 mẫu chính: không cộng thành 220. Smoke và benign dùng cùng một hash file lành: không tính thành hai mẫu.
- Bundle ID, schema, method và ngưỡng được ghi trong kết quả khớp bốn bundle đã bàn giao. Thông tin mã nguồn extractor V3 được khai báo cũng khớp bản đóng gói. Điều này chưa thay thế việc kiểm tra hash các file model/code thực tế bên trong image đã chạy.

| Bộ model | Chế độ | Chấm được / đã chọn | Lỗi | Dự đoán MALWARE / chấm được | Dự đoán BENIGN | Cảnh báo trigger / chấm được |
|---|---|---:|---:|---:|---:|---:|
| EMBER2018 | Reduced | 175/200 | 25 | 162/175 | 13 | 2/175 |
| EMBER2018 | Full | 175/200 | 25 | 162/175 | 13 | 2/175 |
| EMBER2024 | Reduced | 175/200 | 25 | 175/175 | 0 | 0/175 |
| EMBER2024 | Full | 175/200 | 25 | 175/175 | 0 | 0/175 |

Tỷ lệ xử lý được là 87,5%, lỗi 12,5%. Hai cảnh báo của 2018 là cùng hai mẫu ở cả Reduced và Full; cả hai bị classifier gọi BENIGN. Chưa có nhãn trigger được xác minh nên không gọi đây là hai backdoor đã bắt được.

Hai cách ghi mẫu số phải được phân biệt: 2/175 = 1,14% trên mẫu chấm được; helper hiện lưu 2/200 = 1% trên toàn bộ mẫu chọn. 25 dòng lỗi vẫn là chưa chấm được, không phải 25 kết quả âm tính. Các tỷ lệ này không phải FPR hoặc recall phát hiện backdoor.

## 2. Việc cần làm theo thứ tự

### Bước 1 — Làm rõ bằng chứng đang lệch, trước khi đưa số vào bài

**Ưu tiên cao nhất; chưa cần chạy thêm 200 malware.**

1. Giữ ZIP gốc và hash; giữ riêng kết quả nhận từ bạn và phần nhóm tổng hợp. Không sửa ngược CSV/JSON để khớp ghi chú.
2. Xin bạn giải thích hai log `smoke.log` và `benign.log`: chúng ghi xác suất 0,169/0,748, trong khi CSV và JSON ghi khoảng 0,044262/0,957886. Xin stdout/stderr gốc hoặc xác nhận log tóm tắt đã lấy từ lượt khác. Hiện chỉ dùng CSV/JSON cho bảng số, đánh dấu log chưa đối chiếu xong.
3. Xin kết quả `bodmas_verify_kit.py` và hash code/model thực tế của image đã dùng; giữ image ID và lệnh/container inspect nếu còn. `image_inspect.json` cho biết cấu hình image, chưa chứng minh các tùy chọn giới hạn CPU/RAM/mạng của container khi chạy.
4. Làm rõ file lành đã dùng: hash `72524cf3...1e4485` khác fixture trong kit gốc `d5a4dc25...db9d23a`. Có thể do biên dịch lại, chưa đủ để kết luận sai. Cần mã nguồn, cách build và hash của đúng bản được chấm; tên file giống nhau không chứng minh byte giống nhau.
5. Xin danh sách đường dẫn ứng viên đã sắp xếp của 57.293 file hoặc bằng chứng chọn mẫu tương đương, cùng phiên bản Python. Manifest ghi seed 17 nhưng ZIP không chứa toàn bộ danh sách để bốc lại và xác minh lựa chọn trên máy tổng hợp.
6. Xin nguồn metadata/ánh xạ ID gốc nếu có để đối chiếu nhãn và kiểm tra trùng dữ liệu đã dùng. Tên file và hash byte disarmed khác nhau; không tự coi tên file là hash byte đang đọc. Nếu thiếu thì giữ nhãn là do người chạy khai báo và chưa xác minh việc tách biệt khỏi dữ liệu huấn luyện.

**Đạt khi:** giải thích được điểm lệch hoặc ghi rõ phần bằng chứng còn thiếu. Thiếu log gốc không tự làm mọi dòng CSV sai, nhưng không được viết rằng toàn bộ lượt chạy đã được tái lập độc lập.

### Bước 2 — Tổng hợp kết quả hiện có và sửa cách diễn giải

Người tổng hợp tạo bảng bốn cấu hình ở trên, bảng 25 lỗi và phần giới hạn; lưu thêm bảng theo hash để truy từng mẫu.

- Đổi câu “2024 chính xác 100%” thành “175/175 mẫu chấm được được model dự đoán MALWARE, theo nguồn nhãn do người chạy khai báo; 25/200 mẫu chưa chấm được”.
- 25 lỗi đều là `Invalid PE signature/header offset`, xuất hiện ở bước kiểm tra header trước LIEF. Chưa có bằng chứng đủ để kết luận chúng do disarming, relocation hỏng hay section hỏng. Các cảnh báo LIEF trong log không được gán cho 25 file này khi chưa có ánh xạ log theo file.
- Giữ cả 25 dòng lỗi trong báo cáo. Không sửa header, thay mẫu lỗi bằng mẫu dễ đọc hoặc bỏ lỗi để có bảng đẹp.
- Với một file lành: 2018 gọi BENIGN, 2024 gọi MALWARE, cả hai không cảnh báo trigger. Đây là một trường hợp báo nhầm theo nhãn khai báo, chưa đủ để ước lượng FPR của hệ thống.
- Không dùng thời gian trong kit để kết luận bản tối ưu mới nhanh/chậm hơn: kit ghi đường suite gồm STRIP; phép đo ngày 20/10 dùng đường selected, trên máy khác và phạm vi khác.

**Đạt khi:** mọi tỷ lệ có mẫu số; không trộn phân loại malware với phát hiện trigger; không cộng trùng pilot/smoke; lỗi và kết quả âm đều còn nguyên.

### Bước 3 — Bổ sung nhỏ, có mục tiêu

**Đề xuất của t:** giữ bộ 200 malware hiện tại làm kiểm tra đường đi binary; sau bước 1 mới ưu tiên thêm khoảng 50 file lành có nguồn rõ, đa dạng hơn một chương trình tự viết, dùng chung danh sách/hash cho cả bốn bundle. Đây là đề xuất lượt mới, chưa được thực hiện.

Mục đích là xem tình trạng 2024 báo nhầm có lặp lại trên nhiều file lành không. Báo riêng classifier gọi nhầm MALWARE và detector cảnh báo nhầm trigger. Không đổi ngưỡng bằng chính tập này; nếu cần phát triển phương pháp sau khi xem kết quả, phải tách lượt đánh giá mới.

Nếu chưa có bộ lành phù hợp, vẫn có thể hoàn thành phần kiểm tra tĩnh 200 mẫu với giới hạn rõ ràng. Không tự gọi một file lành là bộ đánh giá FPR. Chưa ưu tiên tăng lên hàng nghìn malware vì nó không trực tiếp giải quyết ba khoảng trống: bằng chứng môi trường, báo nhầm trên file lành và tính hiện thực của trigger.

Với 25 file lỗi, chỉ cần bạn kiểm tra lại read-only trên VM theo cùng danh sách hash, xác nhận kích thước/header và nguồn disarmed nếu cần. Không phục hồi khả năng chạy của malware. Nếu sửa bug parser sau này, phải giữ kết quả cũ và tạo lượt/version mới trên đúng mẫu cũ.

### Bước 4 — Đưa vào bài báo và chuẩn bị demo

- Thêm một mục riêng “Kiểm tra bổ sung trên BODMAS disarmed”: nguồn/chọn mẫu, bốn bundle cố định, bảng kết quả, lỗi và giới hạn. Giữ kết quả nghiên cứu chính và công thức W50 đã khóa.
- Kết luận được phép: kết quả hỗ trợ đường đi file PE → đặc trưng → model cho 175/200 mẫu đã chọn. Không kết luận mẫu đã cấy trigger, trigger có thể hiện thực trong PE, hoặc malware vẫn hoạt động sau khi cấy trigger.
- Demo tách hai nội dung: file thật/disarmed để minh họa đọc tĩnh và phân loại; vector có trigger để minh họa backdoor. Mẫu demo được chọn có chủ đích, không dùng vài file demo làm độ chính xác nghiên cứu.
- ZIP kết quả hiện không chứa mẫu malware để upload trực tiếp khi demo. Có thể dùng kết quả/ảnh đã lưu làm dự phòng; nếu cần demo trực tiếp, chuẩn bị mẫu được phép dùng trong VM và chỉ phân tích tĩnh, thử trước đúng bundle. Không phải gửi raw malware về máy tổng hợp để làm bảng hoặc sửa bài.
- Chỉ sửa báo cáo IEEE khi tới bước biên tập được yêu cầu; không ghi đè bản gốc từ lượt lập kế hoạch này.

## 3. Tin nhắn có thể gửi cho bạn phụ trách

> T đã nhận đủ CSV/JSON của bốn lượt 200 mẫu, chưa cần chạy lại toàn bộ. Bạn gửi thêm giúp t: (1) stdout/stderr gốc hoặc giải thích vì sao smoke.log/benign.log ghi xác suất khác CSV/JSON; (2) kết quả verify kit, hash code/model trong image, image ID và lệnh/container inspect của lượt chạy nếu còn; (3) source/cách build/hash của đúng file lành 72524cf3...1e4485; (4) danh sách 57.293 đường dẫn dùng để bốc mẫu và Python version, metadata ánh xạ ID gốc nếu có. Gửi lại selection_notes bản UTF-8 đúng vì bản hiện tại nhiều dấu đã thành ký tự ?. Không cần gửi raw malware. Giữ nguyên 25 lỗi, chưa sửa header hay chọn mẫu khác để thay.

## 4. Khuyến nghị chốt

Làm bước 1 và 2 trước, sau đó bổ sung file lành nếu nguồn/tài nguyên cho phép, rồi biên tập report/demo. Không train lại, không chỉnh ngưỡng và không mở rộng ma trận chỉ để cải thiện số đẹp. Kết quả BODMAS giúp phần kiểm tra binary có bằng chứng thực tế hơn; **giới hạn về trigger trên malware có chức năng vẫn phải giữ**.
