# Kế hoạch tiếp tục X-SENTINEL và sửa giao diện

Ngày lập: 14/10/2026, theo giờ Việt Nam/Thái Lan.

**Trạng thái: người dùng đã yêu cầu bắt đầu triển khai ngày 14/10/2026.** Phần chính ở bước 1–5 và 7 được triển khai theo đề xuất đã gộp. Auth và các nhánh nghiên cứu ở bước 6 giữ điều kiện lựa chọn riêng; chưa có quyết định mới về các nhánh đó. Tài liệu này giữ mô tả và dự trù ban đầu, còn bằng chứng thực hiện được bàn giao riêng.

Đây là một kế hoạch chung cho phần hệ thống còn thiếu và phần giao diện. Upload, đọc PE, lưu lịch sử, giải thích kết quả và đo thời gian được thiết kế như một luồng; mỗi công việc chỉ được tính một lần.

**1. Những lựa chọn đã ghi nhận từ người dùng**

| Nội dung | Lựa chọn |
|---|---|
| Giới hạn upload | Tăng từ 20 lên 50 MB; chờ triển khai cùng kế hoạch. Quy ước kỹ thuật giữ kiểu hiện tại: 50 × 1024 × 1024 byte, tức 50 MiB. |
| Ngôn ngữ giao diện | Tiếng Việt, giữ tên kỹ thuật và có giải thích bên cạnh. |
| Trải nghiệm demo | Có phần giải thích quá trình và căn cứ kết quả, biểu đồ có ý nghĩa; màn hình đầu gọn. |
| Latency | Dùng lại kết quả đã tính; kiểm chứng ảnh hưởng của giao diện bằng đo trước và sau. |
| Báo cáo | Tiếp tục dùng Word DOCX. |
| Quyền triển khai | Đã được người dùng cho bắt đầu phần chính; các nhánh có điều kiện không tự trở thành bắt buộc. |

**2. Xuất phát từ phần đã hoàn thành**

Nguồn hiện trạng chính là `docs/REVISION_2026_10_13.md` và `output/revision_2026_10_13/Ban_giao_va_phan_hoi_gop_y.md`. Các kế hoạch ngày 04–06/10 là lịch sử; trạng thái cũ được đối chiếu lại với code và bàn giao mới.

- Đã có 54 cấu hình nghiên cứu, reduced/full cho hai dataset, ngưỡng riêng và các kết quả đã lưu.
- Đã xử lý 15 quyết định sửa góp ý trong bản Word và có gói code/model/scores phục vụ kiểm chứng.
- Đã có API, PostgreSQL, lưu/đọc lịch sử, Docker và bằng chứng vận hành trước đây. Các phần này cần hoàn thiện và nghiệm thu, không xây lại từ đầu.
- Đã có bộ đọc PE V3 phục vụ nghiên cứu. Dashboard hiện vẫn chặn upload PE với EMBER2024; bộ đọc V2 còn giới hạn tương thích đã công bố.
- Đã có các điểm, ngưỡng, SHAP, đóng góp theo nhóm và dự đoán mô hình phụ trong kết quả trả về. Phần giải thích giao diện ưu tiên tận dụng dữ liệu này.

Hoàn thiện hệ thống và nâng sức thuyết phục của nghiên cứu là hai mục tiêu riêng. Giao diện đẹp hơn không làm tỷ lệ phát hiện tăng. Việc bổ sung nghiên cứu phải xuất phát từ câu hỏi còn thiếu, không lấy yêu cầu X-SENTINEL phải thắng làm tiêu chí.

**3. Thứ tự triển khai và phạm vi**

| Bước | Công việc | Phạm vi | Điều kiện hoàn thành |
|---|---|---|---|
| 1 | Chốt yêu cầu nghiệm thu, cấu hình demo và ghi số đo ban đầu | Phần chính | Có danh sách việc bắt buộc, cấu hình demo rõ và số đo trước khi sửa. |
| 2 | Hoàn thiện luồng upload 50 MB, bộ đọc V2/V3 và thông tin đầu vào | Phần chính | Đầu vào phù hợp đi qua đọc file → phân tích → lưu → xem lại; đầu vào lỗi được xử lý rõ. |
| 3 | Sửa giao diện tiếng Việt, giải thích kết quả và trình bày lịch sử | Phần chính | Người mới thao tác được và hiểu hai kết luận; mở chi tiết dùng lại kết quả hiện có. |
| 4 | Kiểm chứng phục hồi backup; đăng nhập nếu cần nhiều tài khoản | Restore là phần chính; auth có điều kiện | Backup phục hồi khớp trong DB thử. Nếu có auth, tài khoản A không đọc được lịch sử B. |
| 5 | Đo toàn luồng và tối ưu phần chậm | Phần chính | Có số đo từng phần và tổng thời gian; thay đổi tối ưu giữ kết quả phân tích đúng. |
| 6 | Nghiên cứu bổ sung theo câu hỏi đã chốt | Có điều kiện | Thiết kế và ngân sách riêng được duyệt trước; kết luận đúng theo kết quả, kể cả khi đối chứng tốt hơn. |
| 7 | Nghiệm thu máy khác, cập nhật Word, slide và diễn tập | Phần chính | Thành viên khác chạy được theo hướng dẫn; demo và tài liệu khớp hành vi đã kiểm chứng. |

Bước 1–2 xác định dữ liệu và luồng cho giao diện ở bước 3. Việc phục hồi backup có thể làm song song khi phù hợp. Số đo trước sửa được lấy ở bước 1; bước 5 đo lại sau thay đổi. Nghiên cứu bổ sung không tự chặn các việc sản phẩm độc lập.

**4. Chi tiết bước 1: chốt phạm vi và số đo ban đầu**

Nhóm cần xác nhận với thầy ba yêu cầu ảnh hưởng lớn đến công sức: có bắt buộc M5/câu hỏi nghiên cứu cũ, tấn công trên malware binary thật, hoặc lọc fit rồi huấn luyện lại toàn bộ không. Việc liên hệ thầy do người dùng quyết định.

Đề xuất mặc định là giữ phương pháp hiện tại, M5 ở hướng mở rộng, và tách kiểm chứng malware binary thật cùng train lại toàn bộ thành các nhánh riêng. Khi chưa có yêu cầu mới, không tự tăng ma trận thí nghiệm.

Chọn một cấu hình demo cố định cho mỗi dataset và hiển thị rõ bộ mô hình/phương pháp đang dùng. Các cấu hình khác vẫn truy cập được trong khu nghiên cứu. Reduced/full giữ đúng ý nghĩa tài nguyên đang có, không dùng tên Full để hứa chất lượng cao hơn.

Ghi số đo ban đầu trên đầu vào, cấu hình và máy được xác định: thời gian đọc file, tính điểm, API/lưu, tổng thời gian đến kết quả chính. Tách lần đầu nạp hệ thống và các lần sau. Đây là việc sẽ làm khi triển khai được duyệt, chưa chạy trong lúc lập kế hoạch.

**5. Chi tiết bước 2: một luồng upload, không tách thành nhiều việc trùng**

Giới hạn 50 MiB phải đồng bộ ở Streamlit/Docker, kiểm tra dashboard và bộ kiểm tra PE dùng chung cho V2/V3. Có thông báo rõ giới hạn trên màn hình và lỗi khi vượt giới hạn. Tăng dung lượng cho phép không đồng nghĩa file lớn xử lý nhanh như file nhỏ.

Nối bộ đọc đúng với bộ mô hình đang chọn, bổ sung dependency V3 vào runtime dùng cho demo. Chỉ bật đường PE V3 khi luồng đã kiểm chứng. Giữ mô tả giới hạn tương thích của V2 và giới hạn bằng chứng của V3 ở phần thông tin liên quan.

Đầu vào thử gồm file PE lành do nhóm kiểm soát, file không phải PE/hỏng, file vượt giới hạn, vector sai schema và trường hợp API/database lỗi. File được đọc để trích đặc trưng, không được chạy qua luồng upload.

Nếu lịch sử cần tên file và dung lượng, bổ sung metadata thích hợp vào luồng API/database: tên hiển thị, dung lượng, loại đầu vào, checksum file khi có, schema và phiên bản bộ đọc. Checksum vector và checksum file là hai thông tin khác nhau. Không suy ra tên file từ một mã hash; không cần lưu toàn bộ binary để hiển thị lịch sử.

Khi đổi file, dataset, bundle hoặc phương pháp, bỏ kết quả cũ đang hiển thị và yêu cầu phân tích đầu vào mới. Khóa dùng lại kết quả cần gắn với nội dung đầu vào, schema, bộ đọc, phiên bản bundle và phương pháp; không để tên file mới xuất hiện cùng kết quả của file trước. Chỉ xác nhận đã lưu sau khi API/database xác nhận thành công.

Đọc PE V3 thành công là khả năng xử lý đầu vào. Nó chưa chứng minh trigger nghiên cứu có thể tạo được trên malware binary và giữ chức năng của malware.

**6. Chi tiết bước 3: bố cục giao diện và giải thích cho demo**

Đề xuất có ba khu: **Phân tích**, **Lịch sử**, **Nghiên cứu**. Khu nghiên cứu giữ các lựa chọn và dữ liệu kỹ thuật, tránh trải tất cả lên màn hình phân tích.

Trang Phân tích đi theo luồng: chọn bộ mô hình → chọn đầu vào → nhấn Phân tích → đọc kết quả → mở giải thích nếu cần.

Màn hình ban đầu chỉ cần bộ mô hình đang dùng, tải PE/dùng mẫu demo, tên và dung lượng đầu vào, giới hạn 50 MB và nút phân tích thống nhất cho local/API. Mẫu demo có nhãn riêng; vector NPY và raw JSON nằm trong khu nghiên cứu. Local/API phải báo rõ kết quả có được lưu hay không.

Sau phân tích, kết quả chính có hai phần đứng riêng:

| Phần | Người xem cần hiểu |
|---|---|
| Mô hình phân loại file | Mô hình chính dự đoán lành hay mã độc. Điểm dự đoán là đầu ra mô hình, không phải bảo đảm về thực tế. |
| Cảnh báo dấu hiệu trigger | Phương pháp đang chọn có điểm vượt ngưỡng hay không. Chưa cảnh báo không chứng nhận file an toàn. |

Mỗi cặp kết quả có câu giải thích phù hợp. Ví dụ minh họa khi phân loại lành nhưng có cảnh báo: “Mô hình chính dự đoán file lành. Tuy nhiên, điểm phát hiện bất thường vượt ngưỡng của phương pháp đang chọn. Hai kết quả này cần được xem xét cùng nhau.”

Giữ bảng tất cả phương pháp trong phần mở rộng. Cảnh báo chính lấy theo phương pháp đang chọn; không gộp cờ của các phương pháp khác thành một cảnh báo mới.

Ba lớp chi tiết:

| Lớp | Nội dung |
|---|---|
| Vì sao có cảnh báo? | Điểm của phương pháp đang chọn, ngưỡng và quan hệ điểm > ngưỡng; một câu giải thích từ dữ liệu thật. |
| Đặc trưng ảnh hưởng đến kết quả | Biểu đồ đóng góp theo nhóm và các đặc trưng ảnh hưởng mạnh, kèm mô tả cách đọc. |
| Chi tiết nghiên cứu | Tất cả method/score/threshold, SHAP, dự đoán mô hình phụ, schema/protocol, checksum và cấu hình thí nghiệm. |

Những mục khó hiểu được giải thích bằng tiếng Việt:

| Tên hiện có | Ý nghĩa và cách trình bày |
|---|---|
| Dataset | Đổi nhãn thành Bộ mô hình; giải thích bộ dữ liệu và schema tương ứng. |
| Model collection | Mặc định bản nghiên cứu chính; bản thử cũ và bundle tự nhập ở khu nghiên cứu, theo khả năng local/API thực có. |
| Research experiment | Loại trigger, seed và tỷ lệ đầu độc là thông tin của lần huấn luyện/thí nghiệm, không phải thao tác đang áp dụng lên file upload. |
| Reduced / Full | Reduced dùng mô hình đang kiểm tra; Full nhận thêm các mô hình sạch theo nhóm đặc trưng. |
| Detection method | Phương pháp được chọn để quyết định cảnh báo. Mặc định theo cấu hình demo đã chốt. |
| Bundle directory | Đường dẫn bộ model/config, chuyển vào chi tiết kỹ thuật; luồng cơ bản chọn từ danh sách hợp lệ. |
| Locked threshold | Ngưỡng cảnh báo đã cố định. Không thêm thanh kéo ngưỡng làm thay đổi quyết định đã kiểm chứng. |
| Structural | Thông tin cấu trúc PE, như header và section. |
| Behavioral | Thông tin import/export liên quan API; không phải hành vi quan sát khi chạy file. |
| Metadata | Thống kê byte, entropy và chuỗi trong file. Giữ đúng tên view Metadata của phương pháp. |
| SHAP | Mức ảnh hưởng của đặc trưng tới điểm của mô hình. Dấu dương/âm theo hướng tăng/giảm raw margin, không phải số phần trăm xác suất. |
| Tỷ lệ đóng góp theo nhóm | Tỷ trọng ảnh hưởng tuyệt đối theo nhóm; không phải tỷ lệ file độc hại hay bằng chứng nguyên nhân backdoor. |
| View predictions | Dự đoán của mô hình sạch theo từng nhóm, chỉ có khi bộ mô hình cung cấp. Reduced không hiển thị số 0 giả thay cho dữ liệu vắng. |
| M5 | Phần bổ sung chưa được kiểm chứng trong primary; hiển thị trạng thái tại chi tiết nghiên cứu khi có liên quan. |

Thông tin checksum, protocol, cấu hình attack chưa qua confirmation và compatibility vẫn xem được ở nơi liên quan. Dòng cấu hình đang dùng luôn rõ để người xem biết nguồn kết quả.

Trạng thái xử lý bám công việc thật: chờ đầu vào → kiểm tra/đọc PE → trích đặc trưng → phân tích → có kết quả. Trạng thái lưu là riêng. Không tạo tiến trình theo thời gian giả để kéo dài demo. Nếu scorer không phát tín hiệu từng giai đoạn, hiển thị trạng thái thực mà backend cung cấp.

Thông báo lỗi bằng tiếng Việt, có hướng xử lý tiếp: file quá lớn, PE không đọc được, dữ liệu sai schema, bộ mô hình chưa sẵn sàng hoặc chưa lưu được do database. Traceback và JSON kỹ thuật chuyển sang khu chi tiết phù hợp.

Lịch sử có bảng ngắn: thời gian, tên/định danh đầu vào, bộ mô hình, phân loại và cảnh báo. Mở một lần phân tích sẽ dùng lại bố cục kết quả. Tên file/dung lượng chỉ hiển thị nếu metadata đã được bổ sung ở bước 2; bản ghi cũ có nhãn thiếu thông tin phù hợp.

Phong cách đề xuất: nền sáng, một màu nhấn, khoảng cách rõ, màu nổi bật cho trạng thái cần chú ý. Không dùng chữ “An toàn” hoặc dấu hiệu chứng nhận an toàn cho BENIGN/NO ALERT. Kiểm tra bằng giao diện chạy thật trên màn hình laptop; hiện bản kế hoạch được lập từ code, chưa phải đánh giá hình ảnh sau khi sửa.

**7. Chi tiết bước 4: backup và tài khoản**

Backup đã có, còn thiếu bài phục hồi thực. Restore vào database thử riêng, đối chiếu số bản ghi và nội dung, rồi xác minh luồng đọc qua API. Không ghi đè database đang dùng để thử phục hồi.

Đăng nhập/phân quyền chỉ thuộc gói triển khai khi nhóm chọn dùng nhiều tài khoản hoặc rubric bắt buộc. Khi chọn nhánh này, backend xác thực danh tính, người dùng xem lịch sử của mình, quản trị viên có quyền đã định nghĩa. Kiểm tra tài khoản A không đọc được lịch sử B bằng UI và gọi API trực tiếp. Nếu chỉ demo local chung cho nhóm, ghi rõ lịch sử dùng chung và giới hạn vận hành.

**8. Chi tiết bước 5: bảo vệ latency khi thêm giải thích**

Hiện `elapsed_ms` đo `Detector.predict`, gồm tính các điểm và STRIP. Nó không gồm toàn bộ upload, nạp model, đọc PE, API/database và hiển thị giao diện; cũng không phải thời gian riêng của phương pháp đang chọn.

Các số cũ và một số ms trên một file không được dùng như thời gian cố định cho mọi đầu vào. Mốc 10 ms là mục tiêu tham khảo đã có trong kế hoạch trước; yêu cầu chấm môn cần được xác nhận rõ về phạm vi đo.

Quy tắc thiết kế:

- Tính kết quả một lần cho đầu vào/cấu hình đã xác định; giải thích và biểu đồ dùng dữ liệu đó.
- Viết giải thích bằng mẫu câu gắn với điểm/ngưỡng/trạng thái, không bổ sung mô hình giải thích nặng vào luồng chính.
- Mở chi tiết không gọi lại detector; dữ liệu vắng được ghi rõ, không tạo số giả.
- Bộ đọc/model được dùng lại khi đúng phiên bản. Khi thay file/schema/bộ đọc/bundle/method, khóa kết quả phải thay tương ứng.
- Phần chi tiết chỉ xử lý khi có thao tác mở phù hợp. Một khung expander đóng trong Streamlit chưa tự bảo đảm code bên trong không chạy.
- Đo đọc file, tính điểm, API/lưu, thời gian tới kết quả chính và thời gian hiển thị chi tiết nếu cần. Tách lần đầu và các lần sau; báo trung bình và P95 khi cỡ mẫu phù hợp.
- So trước/sau bằng cùng đầu vào, cấu hình và máy; tránh chạy jobs khoa học đồng thời khi đo. Không gọi một số đo per-input là trung bình toàn hệ thống.

Sau đo mới tối ưu phần chậm. Thay đổi tối ưu được đối chiếu với điểm/ngưỡng/cảnh báo gốc. Nếu thay số cây, công thức hoặc ngưỡng thì đó là thay phương pháp và cần đánh giá riêng, không gộp vào sửa giao diện.

File lớn tới 50 MiB có thể tăng thời gian đọc và RAM. Giao diện giải thích không được hứa không tăng tổng thời gian chờ; tác động thực phải được đo. Nếu vẫn vượt mục tiêu, báo kết quả và nguyên nhân, không loại các bước khỏi tổng thời gian để tạo số đẹp.

**9. Chi tiết bước 6: các nhánh nghiên cứu cần quyết định riêng**

| Nhánh | Vì sao xem xét | Đề xuất hiện tại |
|---|---|---|
| So sánh với mô hình sạch có ngân sách tương đương | Đối chứng sạch đang mạnh hơn trong kết quả đã đo; hai bên hiện khác số rounds và tài nguyên. | Ưu tiên nếu nhóm muốn tăng sức thuyết phục nghiên cứu. Chốt thông tin được cấp, huấn luyện và dữ liệu đánh giá trước. |
| File lành ít gặp | Cần hiểu cảnh báo nhầm ở các nhóm khó hơn. | Là phần thêm khi còn thời gian; quy tắc chọn nhóm được cố định trước đánh giá. Không gọi một nhóm là packed khi chưa có nhãn xác minh. |
| M5/câu hỏi nghiên cứu cũ | Có thể liên quan rubric ban đầu. | Để hướng mở rộng, trừ khi thầy bắt buộc. Chốt định nghĩa và thí nghiệm trước; hash bucket không chứng minh API cụ thể. |
| Trigger trên malware binary thật | Vector stress và fixture lành chưa chứng minh tấn công giữ chức năng malware. | Kế hoạch riêng khi có nguồn file được phép và môi trường xác minh phù hợp. |
| Lọc fit rồi huấn luyện lại | Sensitivity đã làm giữ model cũ; không thay cho retraining. | Chỉ mở protocol mới khi có yêu cầu và ngân sách. |

Bộ dữ liệu final và pool bổ sung đã xem không được gọi là xác nhận độc lập cho phương pháp được chọn sau khi xem chúng. Nhánh có thay phương pháp phải khóa thiết kế trước và dành dữ liệu chưa dùng để lựa chọn cho bước xác nhận phù hợp. Giữ kết quả cũ và mới có nhãn riêng.

**10. Chi tiết bước 7: nghiệm thu và bàn giao**

Thử theo hướng dẫn trên một máy khác với code/runtime và bundle đúng phiên bản. Docker đã được kiểm tra trên Windows/Linux cùng máy trước đây; bước máy khác kiểm chứng khả năng bàn giao.

Kịch bản demo gồm đầu vào PE hợp lệ, đầu vào lỗi, mẫu demo được gắn nhãn, vector sai schema, kết quả có/chưa cảnh báo khi có mẫu phù hợp, xem lại lịch sử và phục hồi backup. Không chọn mẫu rồi tuyên bố các trường hợp đẹp đại diện mọi đầu vào.

Cập nhật Word, hướng dẫn chạy, slide và phần trả lời phản biện từ những chức năng/số đã kiểm chứng. Hai câu hỏi cần trả lời rõ là: hệ thống đã làm gì với file, và bằng chứng nào hỗ trợ cảnh báo của nó. Nội dung giải thích, hình và caption khớp phương pháp hiện tại.

**11. Tiêu chí nghiệm thu chung**

| Nhóm | Tiêu chí |
|---|---|
| Upload | Giới hạn 50 MiB được áp dụng nhất quán; lỗi dung lượng/định dạng/schema rõ ràng; đường V3 chỉ dùng bộ đọc tương ứng đã kiểm chứng. |
| Kết quả | Cùng đầu vào và cấu hình cho điểm, ngưỡng và cảnh báo khớp bản đã kiểm chứng; đổi đầu vào/cấu hình không giữ nhầm kết quả cũ. |
| Giải thích | Nêu đúng phương pháp đang chọn, quan hệ điểm/ngưỡng, vai trò SHAP và giới hạn của từng kết luận. |
| Giao diện | Người mới hoàn thành luồng, hiểu phân loại khác cảnh báo trigger và mở được chi tiết cần thiết. |
| Lịch sử | Trạng thái lưu đúng; bản ghi cũ vẫn đọc được; metadata mới không được tự suy từ hash. |
| Backup | DB thử phục hồi khớp và đọc lại được qua API. |
| Latency | Có số đo trước/sau, phạm vi từng số rõ; tổng thời gian không bị gắn nhãn nhầm từ thời gian tính điểm. |
| Bàn giao | Thành viên khác chạy được theo hướng dẫn; Word/slide/demo phản ánh đúng phần đã hoàn thành. |

**12. Dự trù công sức, không cộng trùng hai kế hoạch**

| Gói | Dự trù ngày làm việc |
|---|---|
| Chốt luồng/cấu hình và số đo ban đầu | 0,5 |
| Upload 50 MiB, PE V3, runtime và metadata đầu vào | 1,5–2,5 |
| Giao diện, giải thích, biểu đồ và trình bày lịch sử | 2–3 |
| Restore thử | 0,5–1 |
| Đo lại toàn luồng và tối ưu phù hợp | 1–2 |
| Máy khác, Word/slide, diễn tập và xử lý lỗi nghiệm thu | 1–2 |

Dự trù phần chính khoảng **8–12 ngày làm việc kể từ khi được chốt**, đã bao gồm sửa giao diện. Các khoảng trên là ước lượng, phụ thuộc lỗi tích hợp, thư viện, Docker và máy thử; không phải kết quả đo hay cam kết ngày hoàn thành. Đăng nhập cơ bản, nếu được chọn, dự trù thêm 1–2 ngày. Các nhánh nghiên cứu mới cần ngân sách riêng sau khi chốt thiết kế; không cộng M5, malware thật hoặc toàn bộ retraining vào gói chính khi chưa duyệt.

**Phạm vi đang triển khai:** phần chính ở bước 1–5 và 7; auth chỉ khi cần nhiều tài khoản; bước 6 chọn theo yêu cầu thầy và mục tiêu nghiên cứu. Số đo và trạng thái nghiệm thu thực tế sẽ được ghi riêng, không thay ước lượng thành kết quả đã đo.
