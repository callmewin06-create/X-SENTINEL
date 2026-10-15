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

**Lỗi giao diện người dùng ghi nhận ngày 16/10/2026 — nhật ký trước khi sửa**

Người dùng đã chốt triển khai. Các dòng “chưa sửa/chờ chốt” trong nhật ký và phương án ban đầu bên dưới ghi trạng thái lúc đề xuất, không phải trạng thái hiện tại. Bản sửa đã triển khai và kiểm chứng trên máy hiện tại; xem [bàn giao sửa giao diện ngày 16/10](../UI_REVISION_2026_10_16.md) để biết kết quả và giới hạn kiểm chứng. Việc thử trên máy vật lý thứ hai/Kali vẫn cần thực hiện riêng.

- **UI-01 — Chữ kết quả gần như không đọc được khi bật Dark.** Vị trí: trang Phân tích → Kết quả phân tích → hai ô “Mô hình phân loại file” và “Dấu hiệu trigger”. Ảnh người dùng gửi cho thấy nền hai ô vẫn trắng trong khi chữ rất nhạt, khiến “Dự đoán lành”, “Chưa cảnh báo” và nhãn phía trên khó đọc. Đây là quan sát từ ảnh; chưa xác minh nguyên nhân trong CSS.
- **Hướng sửa đề xuất:** cho màu nền và màu chữ của các ô kết quả thay đổi phù hợp với chế độ sáng/tối; kiểm tra cả nhãn và nội dung chính, mọi trạng thái phân loại/cảnh báo, cùng trang lịch sử nếu dùng chung cách hiển thị.
- **Điều kiện hoàn thành:** các ô kết quả đọc rõ khi bật Light hoặc Dark và sau khi đổi qua lại giữa hai chế độ.
- **Trạng thái:** đã ghi nhận; chưa sửa code, chưa kiểm thử bản sửa. Chỉ triển khai sau khi người dùng chốt danh sách lỗi.
- **Ảnh đối chiếu:** [UI-01 — chữ nhạt trên nền trắng khi bật Dark](assets/UI-01_dark_result_low_contrast_2026_10_16.png).

- **UI-02 — Biểu đồ đặc trưng quá nhỏ, tên nhóm bị cắt.** Vị trí: trang Phân tích → “Xem đặc trưng ảnh hưởng đến kết quả” → biểu đồ đóng góp theo nhóm. Ảnh người dùng gửi cho thấy biểu đồ thấp, chữ nhãn/trục nhỏ và cả ba nhãn Behavioral, Metadata, Structural bị rút gọn bằng dấu “…”, không đọc được đầy đủ mô tả.
- **Hướng sửa đề xuất:** tăng chiều cao biểu đồ và cỡ chữ, dành đủ chỗ cho nhãn; cho phép tên nhóm xuống dòng hoặc trình bày tên/mô tả đầy đủ ở vùng riêng cạnh biểu đồ. Nội dung chính phải đọc được trực tiếp, không phụ thuộc hoàn toàn vào rê chuột.
- **Điều kiện hoàn thành:** tên ba nhóm và mô tả đọc đầy đủ, số trên trục rõ, biểu đồ cân đối trên màn hình laptop ở mức thu phóng 100%; kiểm tra cả Light/Dark và khi cửa sổ hẹp hơn.
- **Trạng thái:** đã ghi nhận; chưa sửa code, chưa kiểm thử bản sửa. Chỉ triển khai sau khi người dùng chốt danh sách lỗi.
- **Ảnh đối chiếu:** [UI-02 — biểu đồ nhỏ và nhãn bị cắt](assets/UI-02_feature_chart_small_truncated_labels_2026_10_16.png).

- **UI-03 — Xem biểu đồ và chi tiết vẫn không hiểu vì sao ra nhãn.** Vị trí: Kết quả phân tích, “Vì sao có kết quả này?”, “Xem đặc trưng ảnh hưởng đến kết quả” và “Xem chi tiết nghiên cứu”. Người dùng thấy điểm, tên đặc trưng, SHAP và JSON nhưng chưa có lời giải nối chúng với nhãn phân loại. Khung giải thích hiện chủ yếu mô tả cảnh báo trigger, chưa giải thích đủ quyết định lành/mã độc.
- **Đối chiếu ảnh với code hiện tại:** điểm phân loại 0.5255 vượt ngưỡng malware 0.5 nên gán mã độc; chỉ vượt 0.0255, không được diễn giải thành mức chắc chắn cao hoặc xác suất thực tế đã được kiểm chứng. Điểm X-SENTINEL Reduced 0.586 không vượt ngưỡng riêng 0.945 nên chưa cảnh báo trigger. Đây là hai quyết định khác nhau. Dữ liệu hiển thị đã làm tròn; quyết định phải dùng giá trị đầy đủ.
- **Hướng sửa đề xuất:** giải thích thành ba phần có câu ngắn bám đúng số thực: (1) vì sao mô hình phân loại lành/mã độc, hiện điểm và ngưỡng phân loại lấy từ bundle; (2) các đặc trưng đẩy về mã độc và đẩy về lành, với tên dễ hiểu, giá trị, chiều ảnh hưởng và lý do đọc được từ dữ liệu; (3) vì sao có/chưa có cảnh báo trigger, so riêng điểm với ngưỡng của phương pháp đang chọn. Không tự đổi công thức, ngưỡng hay thêm mức tin cậy chưa được kiểm chứng.
- **Bảng đặc trưng:** bổ sung mô tả tiếng Việt và cột “Đẩy dự đoán về”, phân biệt giá trị đặc trưng với mức ảnh hưởng SHAP; tên dài phải đọc đủ. Ví dụ trong ảnh: cờ DLL bằng 1 có SHAP -2.0418, đẩy về lành; strings.entropy bằng 6.2335 có SHAP +0.5147, đẩy về mã độc trong mô hình này. Không kết luận một cờ DLL, entropy hoặc thiếu thông tin chữ ký tự nó chứng minh mã độc/an toàn. Trường chưa có ánh xạ đáng tin cậy phải ghi rõ giới hạn, không bịa ý nghĩa.
- **Cách đọc biểu đồ:** tỷ trọng ảnh hưởng tuyệt đối cho biết nhóm nào ảnh hưởng nhiều, không cho biết hướng ảnh hưởng. Structural chiếm khoảng 52.59% trong ảnh không có nghĩa 52.59% khả năng mã độc. Nếu trình bày phép cộng để tái hiện điểm cuối, phải có mốc ban đầu của mô hình và phần đóng góp ngoài top 10; không cộng trực tiếp các số SHAP vào xác suất.
- **Nguồn mẫu demo:** ảnh ghi “Mẫu reference demo”. Code hiện lấy vector đầu tiên từ reference, và quy trình primary chỉ cho reference nhãn lành. Với nguồn primary đúng quy trình này, dự đoán mã độc cho mẫu demo là dự đoán nhầm theo nhãn dữ liệu; không phải bằng chứng đã thử file ransomware. Đề xuất hiển thị nguồn mẫu và nhãn gốc đã xác minh bên cạnh nhãn dự đoán; với file upload chưa biết nhãn gốc thì ghi “chưa xác minh”, không tự gán. Không thay mẫu để che trường hợp dự đoán nhầm. Yêu cầu hiển thị và đối chiếu nhãn được ghi chi tiết tại UI-10; không cộng trùng công việc với mục này.
- **Chi tiết nghiên cứu:** giữ bảng phương pháp/SHAP kỹ thuật/JSON trong phần mở rộng; phần kết quả chính phải hiểu được mà không cần đọc JSON hoặc biết công thức. Giải thích dùng kết quả đã tính; không gọi lại detector chỉ để tạo lời giải. Nếu bổ sung mốc ban đầu, lấy cùng lượt tính đóng góp hiện có và đối chiếu tính nhất quán trước khi dùng.
- **Điều kiện hoàn thành:** người mới trả lời được vì sao có nhãn phân loại, đặc trưng nào đẩy mỗi hướng và vì sao cảnh báo trigger có thể khác; các ví dụ/chiều ảnh hưởng/điểm/ngưỡng khớp dữ liệu thật, cả khi xem lại lịch sử; kết quả khoa học không bị thay đổi bởi cách trình bày.
- **Trạng thái:** đã ghi nhận và đề xuất; chưa sửa code, chưa kiểm thử bản sửa. Chỉ triển khai sau khi người dùng chốt danh sách lỗi.
- **Ảnh đối chiếu:** [UI-03 — kết quả](assets/UI-03_01_result_2026_10_16.png), [chi tiết nghiên cứu](assets/UI-03_02_research_2026_10_16.png), [biểu đồ và bảng đặc trưng](assets/UI-03_03_features_2026_10_16.png).

- **UI-04 — Trang Phân tích không có chỗ chọn Reduced/Full.** Người dùng chỉ thấy “EMBER2024 · Reduced · X-SENTINEL Reduced”, nên tưởng trang này không hỗ trợ Full. Code hiện khởi tạo Reduced mặc định và chỉ hiển thị bộ chọn biến thể tại trang Nghiên cứu. Cấu hình được giữ trong preferences theo dataset: theo code, chọn Full ở Nghiên cứu rồi quay lại Phân tích sẽ dùng cấu hình Full đó. Đây là cách bố trí giao diện, không phải hạn chế đầu vào PE hoặc thiếu Full trong hệ thống; đường thao tác này mới được đối chiếu bằng đọc code trong lượt ghi nhận, chưa thử trực tiếp trên máy người dùng.
- **Hướng sửa đề xuất:** đưa bộ chọn Reduced/Full lên trang Phân tích, cạnh Bộ mô hình; giữ Reduced mặc định và kèm mô tả ngắn. Reduced dùng mô hình chính để tính các tín hiệu; Full dùng thêm các mô hình sạch theo nhóm, với thành phần M4-F sử dụng dự đoán Behavioral sạch. Trong cùng cấu hình thí nghiệm, hai bundle dùng chung mô hình chính, nên cần giải thích việc đổi biến thể chủ yếu thay cách tính cảnh báo trigger; không mặc định tuyên bố Full phân loại file chính xác hơn.
- **Điều kiện hoàn thành:** chọn được cả hai chế độ ngay tại Phân tích cho các bundle thực có; bộ mô hình, phương pháp và ngưỡng cập nhật đúng; đổi chế độ không giữ nhầm kết quả trước đó, không phải sang Nghiên cứu để đổi. Kiểm tra cùng một đầu vào/cấu hình: điểm phân loại của mô hình chính nhất quán giữa hai biến thể, còn điểm/ngưỡng cảnh báo theo đúng bundle; lịch sử giữ rõ chế độ đã dùng. Không hứa Full nhanh hơn hoặc chính xác hơn khi chưa có bằng chứng phù hợp.
- **Trạng thái:** đã ghi nhận và đề xuất; chưa sửa code, chưa kiểm thử bản sửa. Chỉ triển khai sau khi người dùng chốt danh sách lỗi.
- **Ảnh đối chiếu:** [UI-04 — trang Phân tích chỉ hiện Reduced](assets/UI-04_analysis_missing_variant_selector_2026_10_16.png).

- **UI-05 — Thay thao tác Print bằng xuất file PDF.** Yêu cầu người dùng: “Print sửa lại thành xuất file PDF”. Hướng triển khai dự kiến là thao tác “Xuất PDF” tải báo cáo của kết quả phân tích đang xem, tránh phải chọn máy in. Bản xuất gồm thông tin đầu vào thực có, bộ mô hình/chế độ, nhãn phân loại, cảnh báo trigger, các điểm/ngưỡng tương ứng, giải thích và giới hạn kết luận. Không xuất toàn bộ menu/JSON kỹ thuật mặc định. Chỉ tạo file khi bấm xuất và dùng kết quả đã có; không chạy lại detector. Kiểm tra tiếng Việt, bảng/biểu đồ không bị cắt, bản xuất dễ đọc dù trang đang Light hay Dark, và không gán dữ liệu thiếu thành giá trị giả. Print hiện là mục mặc định của Streamlit; API menu_items công khai không cung cấp cách đổi riêng mục Print, nên khi triển khai cần bố trí nút xuất riêng hoặc menu phù hợp, không mặc định coi việc đổi tên đã tạo được PDF. **Trạng thái:** đã ghi nhận yêu cầu; chưa sửa code, chờ chốt triển khai.

- **UI-06 — About có GitHub của nhóm.** Yêu cầu người dùng: thêm đường dẫn GitHub nhóm vào phần About. URL đã đối chiếu với remote origin hiện tại: https://github.com/callmewin06-create/X-SENTINEL. Nội dung giới thiệu nêu tên X-SENTINEL, mô tả ngắn chức năng và liên kết có thể bấm; không tự thêm tên thành viên chưa được cung cấp. Có thể đặt nhãn tiếng Việt “Giới thiệu” nếu bố trí menu riêng. Streamlit hỗ trợ nội dung About dạng Markdown. **Điều kiện hoàn thành:** mở giới thiệu thấy đúng đường dẫn và truy cập được repo của nhóm. **Trạng thái:** đã ghi nhận yêu cầu; chưa sửa code, chờ chốt triển khai.

- **UI-07 — Developer options trông như nút nhưng là tiêu đề nhóm.** Người dùng hỏi vì sao bấm không có phản hồi. Trong menu mặc định, đây là nhãn phân nhóm cho các công cụ như Clear cache, không có thao tác riêng khi bấm. **Đề xuất:** ẩn nhóm công cụ phát triển khỏi giao diện demo cho người dùng, giữ chỗ truy cập phù hợp cho người bảo trì khi cần. Cấu hình toolbarMode viewer của Streamlit hỗ trợ ẩn các mục phát triển; khi triển khai phải kiểm tra theo phiên bản đang dùng, vẫn giữ cách đổi Light/Dark và truy cập Giới thiệu/Xuất PDF. Đây là chỉnh cách trình bày menu, không được coi là cơ chế phân quyền. **Trạng thái:** đã giải thích và ghi đề xuất; chưa sửa code, chờ chốt triển khai.

- **Ảnh đối chiếu UI-05–UI-07:** [Menu ứng dụng người dùng đang xem](assets/UI-05_07_app_menu_2026_10_16.png). Tài liệu đối chiếu: [Streamlit app chrome](https://docs.streamlit.io/develop/concepts/architecture/app-chrome) và [st.set_page_config](https://docs.streamlit.io/develop/api-reference/configuration/st.set_page_config).

- **UI-08 — Menu tiếng Anh không thống nhất với giao diện tiếng Việt.** Người dùng yêu cầu phần menu góc trên dùng cùng ngôn ngữ với hệ thống. Phạm vi gồm tên thao tác, hộp thoại và thông báo liên quan mà người dùng gặp, không chỉ tên các trang chính.
- **Nhãn dự kiến:** Rerun → “Tải lại giao diện”; Settings → “Cài đặt”; Print → “Xuất PDF” theo chức năng đã ghi ở UI-05; Record a screencast → “Quay video màn hình”; About → “Giới thiệu”; Clear cache → “Xóa dữ liệu tạm” nếu còn hiển thị ở khu bảo trì. Lựa chọn theme ghi “Sáng”, “Tối”, “Theo hệ thống”. Nhóm Developer options xử lý theo đề xuất UI-07, không để tiêu đề tiếng Anh gây hiểu nhầm là nút.
- **Hướng triển khai:** kiểm tra khả năng tùy chỉnh menu của phiên bản Streamlit đang dùng; nếu menu mặc định không hỗ trợ thay nhãn đầy đủ, bố trí menu/điều khiển tiếng Việt riêng và xử lý phần menu mặc định tương ứng, giữ truy cập được các chức năng cần dùng. Không ghi nhận đã Việt hóa khi thực tế vẫn còn hộp thoại tiếng Anh trong luồng được chốt. Giữ tên riêng/thuật ngữ đã thống nhất như GitHub, PDF, SHAP, TADR, Reduced/Full và có giải thích tiếng Việt khi cần.
- **Điều kiện hoàn thành:** các thao tác menu và hộp thoại thuộc phạm vi giao diện nhóm kiểm soát dùng tiếng Việt nhất quán; Xuất PDF, Giới thiệu và đổi sáng/tối hoạt động sau khi chỉnh menu. Hộp thoại do trình duyệt hoặc hệ điều hành quản lý được phân biệt rõ, không hứa thay ngôn ngữ của các phần đó bằng code ứng dụng.
- **Trạng thái:** đã ghi nhận yêu cầu; chưa sửa code, chưa kiểm thử bản sửa. Chỉ triển khai sau khi người dùng chốt danh sách lỗi. **Ảnh đối chiếu:** dùng ảnh menu đã lưu cho UI-05–UI-07.

- **UI-09 — Ẩn đường dẫn thư mục bộ mô hình khỏi giao diện.** Người dùng không cần thấy dòng như `outputs/primary/EMBER2018/protocol_v2/seed_17/concentrated_structural/rate_0.005/bundle_reduced`. Khi triển khai, bỏ dòng hiển thị đường dẫn nội bộ tại “Thông tin bộ mô hình đang dùng”; giữ các thông tin giúp nhận biết bộ mô hình và hiểu kết quả như dataset, Reduced/Full, cấu hình thí nghiệm và ngưỡng. Chỉ thay cách hiển thị, không xóa thư mục hay đổi đường dẫn nạp model. Không đưa lại đường dẫn nội bộ vào bản PDF cho người dùng. **Trạng thái:** đã ghi nhận yêu cầu; chưa sửa code, chờ chốt triển khai. **Ảnh đối chiếu:** ảnh đường dẫn người dùng gửi ngày 16/10/2026.

- **UI-10 — Mẫu demo hiển thị nhãn gốc và đối chiếu dự đoán đúng/sai.** Người dùng muốn biết mẫu demo thực tế được gán nhãn gì để kiểm tra kết quả. Hiển thị ngay gần kết quả ba thông tin: “Nhãn gốc theo bộ dữ liệu”, “Mô hình dự đoán” và “Đối chiếu: khớp/không khớp nhãn gốc”. Có thể thêm cách nói dễ hiểu “Dự đoán đúng/sai theo nhãn bộ dữ liệu” và giải thích loại nhầm khi có dữ liệu. Ví dụ ảnh trước: nhãn gốc Lành, mô hình dự đoán Mã độc với điểm 0.5255 → không khớp, dự đoán nhầm mẫu lành thành mã độc.
- **Nguồn nhãn:** dùng nhãn có nguồn gốc kiểm chứng và gắn đúng mẫu/schema/bộ mô hình; không suy nhãn gốc từ kết quả mô hình hoặc tên file do người dùng đặt. Demo hiện tại lấy từ reference primary có nhãn lành. Bundle riêng hoặc nguồn chưa xác minh thì ghi “Chưa có nhãn đối chiếu”. Không mặc định mọi nguồn demo đều lành chỉ vì mang tên demo. Nhãn gốc chỉ phục vụ hiển thị/đối chiếu, không được đưa vào đặc trưng hay dùng để đổi dự đoán/ngưỡng. Thêm mẫu demo mã độc có nhãn xác minh là công việc riêng nếu được chọn, không tự suy rằng hệ thống đã có sẵn mẫu đó.
- **Phân biệt hai kết luận:** đúng/sai theo nhãn Lành/Mã độc chỉ áp dụng cho phân loại file. Chấm đúng/sai cảnh báo trigger cần nhãn trigger được xác minh riêng; không lấy nhãn Lành/Mã độc làm nhãn trigger. Với file upload không có nhãn gốc, hiện “Chưa có nhãn đối chiếu”, không tự tuyên bố đúng/sai.
- **Điều kiện hoàn thành:** nguồn/nhãn gốc và dự đoán được phân biệt rõ; đối chiếu chính xác khi nhãn khớp hoặc khác nhau và khi chưa có nhãn; đổi mẫu/bộ mô hình không giữ nhầm nhãn cũ. Xem lịch sử và xuất PDF giữ nguồn nhãn/đối chiếu nếu đã được xác minh; bản ghi cũ thiếu nhãn phải được ghi rõ. Dùng dự đoán đã tính, không chạy lại detector để so nhãn. Đối chiếu một mẫu demo không được trình bày như độ chính xác toàn hệ thống.
- **Trạng thái:** đã ghi nhận yêu cầu; chưa sửa code, chưa kiểm thử bản sửa. Chỉ triển khai sau khi người dùng chốt danh sách lỗi. Mục này tách rõ phần nhãn demo đã đề xuất trong UI-03, không phải phạm vi công việc cộng thêm hai lần.

**Phương án sửa 10 mục giao diện — bản đề xuất ngày 16/10/2026 đã được chốt**

Mục tiêu: người dùng đọc rõ kết quả, hiểu vì sao có nhãn/cảnh báo và đối chiếu được nhãn gốc của mẫu demo. Các yêu cầu được thực hiện trong cùng kế hoạch này. UI-03 và UI-10 dùng chung dữ liệu/giải thích, không cộng trùng công việc. Lượt đề xuất này chỉ chỉnh tài liệu; chưa triển khai các thay đổi ứng dụng.

| Mục | Phương pháp sửa đề xuất | Kết quả người dùng nhận được |
|---|---|---|
| UI-01 | Bỏ nền trắng cố định đang áp lên ô kết quả; dùng màu theo theme, kiểm tra cả nhãn, giá trị và chú thích. | Hai ô kết luận đọc rõ khi dùng Sáng/Tối, cả ở lịch sử. |
| UI-02 | Biểu đồ có chiều cao/cỡ chữ được cấu hình rõ; khởi điểm thử cao khoảng 280–320 px, chữ 14–16 px. Tên nhóm được hiện đủ hoặc xuống dòng, phần trăm ghi cạnh thanh. Tên đặc trưng dài có cách đọc đầy đủ. | Đọc trực tiếp tên/giá trị, không cần rê chuột để hiểu nội dung chính. |
| UI-03 | Dùng phần giải thích chung cho kết quả mới, lịch sử và PDF: so điểm phân loại với ngưỡng thật; so riêng điểm trigger với ngưỡng phương pháp; trình bày các đặc trưng đẩy về mỗi phía bằng tiếng Việt. | Hiểu vì sao có nhãn lành/mã độc và vì sao có/chưa có cảnh báo trigger. |
| UI-04 | Đặt bộ chọn Reduced/Full cạnh Bộ mô hình ngay trên trang Phân tích, lấy các lựa chọn thực có. Dùng chung lựa chọn giữa Phân tích/Nghiên cứu; đổi lựa chọn phải cập nhật đúng bundle/phương pháp/ngưỡng và bỏ kết quả cũ không còn phù hợp. | Chọn chế độ trực tiếp, không phải đổi trang; không nhầm Full là nhãn chứng nhận độ chính xác cao hơn. |
| UI-05 | Làm nút tải PDF thực, tạo từ kết quả hiện có khi được bấm; nhúng font tiếng Việt, dùng bố cục báo cáo riêng dễ đọc. | Nhận file PDF có thông tin đầu vào thực có, hai kết luận, điểm/ngưỡng, đối chiếu demo nếu có và giải thích. |
| UI-06 | Làm phần Giới thiệu bằng tiếng Việt, có tên/mô tả ngắn X-SENTINEL và link GitHub nhóm đã xác minh. | Tìm được thông tin dự án và mở repo đúng. |
| UI-07 | Ẩn nhóm công cụ phát triển khỏi giao diện demo bằng cấu hình phù hợp. Chỗ xử lý cache của người bảo trì nằm ngoài luồng phân tích thông thường. | Không thấy tiêu đề Developer options gây hiểu nhầm là nút. |
| UI-08 | Bố trí các thao tác tiếng Việt của ứng dụng; làm thử riêng giải pháp thay menu mặc định và đổi theme trước khi chốt cách ẩn menu. Rà soát cả hộp thoại thuộc ứng dụng. | Giao diện nhất quán tiếng Việt; các mục còn tiếng Anh phải được ghi rõ là chưa hoàn thành. |
| UI-09 | Bỏ dòng đường dẫn bundle khỏi giao diện kết quả và PDF; giữ tên bộ mô hình/chế độ/cấu hình để nhận biết kết quả. | Không phải đọc đường dẫn nội bộ dài. |
| UI-10 | Gắn nhãn gốc có nguồn xác minh với đúng mẫu demo; hiển thị nhãn gốc, dự đoán và khớp/không khớp. Nhãn thiếu ghi chưa có đối chiếu. | Biết mô hình đúng hay sai với mẫu đang xem theo nhãn bộ dữ liệu. |

**Bố cục kết quả đề xuất**

- Đầu trang: Bộ mô hình, Reduced/Full và đầu vào đang chọn.
- Với mẫu demo đã xác minh: hiện nhãn gốc gần tên mẫu; sau phân tích hiện đối chiếu với dự đoán.
- Hai ô kết luận: “Phân loại file” và “Dấu hiệu trigger”, mỗi ô có điểm/ngưỡng và câu giải thích riêng.
- Mục “Vì sao có kết quả này?”: giải thích phép so điểm/ngưỡng; các đặc trưng đẩy về mã độc và đẩy về lành có tên dễ đọc. SHAP dùng để mô tả ảnh hưởng trong mô hình, không biến thành khẳng định hành vi thật của file.
- Biểu đồ nhóm: tên và tỷ trọng rõ; ghi đây là mức ảnh hưởng, không phải xác suất mã độc. Bảng công thức/JSON nằm tại chi tiết nghiên cứu.
- Các thao tác rõ ràng: Xuất PDF kết quả, Giới thiệu và điều khiển giao diện phù hợp sau khi làm thử.

**Dữ liệu cần bổ sung và cách giữ kết quả nhất quán**

Hiện kết quả đã có điểm phân loại, nhãn dự đoán, bảng điểm/ngưỡng cảnh báo và SHAP. Cần thêm ngưỡng phân loại thực từ cấu hình bundle vào kết quả được lưu; tránh giao diện tự mặc định mọi bản ghi đều dùng 0.5. Phần giải thích đầu tiên chỉ cần phép so ngưỡng và ảnh hưởng có dấu đã tính, chưa cần thêm sơ đồ cộng SHAP tái hiện xác suất. Nếu bổ sung sơ đồ đó sau này, phải lưu mốc ban đầu và phần ngoài top 10 từ cùng lượt tính.

Nhãn demo được tra từ bảng thông tin mẫu đã xác minh, đối chiếu schema, hash bundle/reference và hash vector với nguồn dữ liệu gốc. Backend chỉ gắn nhãn khi khớp nguồn tin cậy; không tin nhãn tự khai từ giao diện hoặc chỉ dựa vào cờ demo. Với bundle riêng, nguồn chưa truy được hoặc file upload chưa có nhãn xác minh, ghi “Chưa có nhãn đối chiếu”. Local dùng cùng quy tắc. Giữ các bundle nghiên cứu hiện có; bảng nguồn demo được tách riêng và có phiên bản.

Các thông tin thêm có thể lưu trong result_json đang có, không cần đổi cấu trúc bảng chỉ để thêm các trường này. Lịch sử cũ thiếu ngưỡng/nhãn nguồn hiện thông báo thiếu dữ liệu; không tự bù nhãn chỉ vì bản ghi cũ mang cờ demo. PDF đọc cùng dữ liệu và quy tắc giải thích với giao diện.

**Điểm cần chỉnh lại trong đề xuất menu**

Dự án đang cố định Streamlit 1.45.1. API menu công khai chỉ tùy chỉnh Get help, Report a Bug và nội dung About; không hỗ trợ đổi hết Print/Settings/Rerun thành tên tiếng Việt. Cấu hình viewer ẩn công cụ phát triển nhưng vẫn giữ menu người xem. Chế độ minimal có thể làm mất cả Settings, và đổi theme.base lúc ứng dụng đang chạy không được hỗ trợ qua st.set_option. Vì vậy không coi Việt hóa toàn bộ menu là thao tác đổi vài nhãn.

Nút Xuất PDF và Giới thiệu tiếng Việt riêng là phương án cụ thể, độc lập với Print/About mặc định. Phần thay toàn bộ menu và đổi Sáng/Tối phải được làm thử trên đúng phiên bản, chứng minh vẫn hoạt động sau khi chạy lại trang rồi mới gộp vào bản triển khai. Nếu còn phải giữ Settings tiếng Anh để đổi theme, UI-08 phải được ghi rõ còn thiếu; không báo hoàn thành 100%. Không tự nâng cấp thư viện, sửa thư viện gốc hoặc vá chữ bằng JavaScript không được hỗ trợ mà coi như đã có giải pháp ổn định.

**Thứ tự triển khai đề xuất**

1. Chuẩn bị dữ liệu cho UI-03/UI-10: ngưỡng phân loại được lưu, nguồn nhãn demo và quy tắc giải thích chung. Đồng thời làm thử giới hạn menu/theme của UI-08 để nhận diện sớm phần chưa khả thi.
2. Sửa trải nghiệm phân tích: UI-01, UI-02, UI-03, UI-04, UI-09, UI-10; đối chiếu cùng kết quả ở trang lịch sử.
3. Hoàn thiện điều khiển và giới thiệu: UI-06, UI-07, UI-08 theo kết quả làm thử; chỉ ghi hoàn thành phần đã kiểm chứng.
4. Làm UI-05 từ dữ liệu/bố cục giải thích đã thống nhất, kiểm tra PDF tiếng Việt và tình huống dữ liệu cũ thiếu trường.
5. Nghiệm thu trên giao diện chạy thật, rebuild Docker và kiểm tra lại tại môi trường Kali của người dùng khi có thể.

**Kiểm tra cần thiết trước khi bàn giao**

- Sáng/Tối, màn hình laptop 100%, cửa sổ hẹp; cả kết quả mới và lịch sử đều rõ chữ, không cắt tên chính.
- Điểm sát, bằng và vượt ngưỡng: phân loại dùng >=, cảnh báo trigger dùng >. Hiển thị có làm tròn nhưng quyết định theo giá trị đầy đủ. Kiểm tra bốn tổ hợp lành/mã độc và có/chưa cảnh báo.
- Đổi dataset, biến thể và mẫu không giữ nhầm điểm/ngưỡng/nhãn gốc; cùng đầu vào và cặp Reduced/Full của một thí nghiệm giữ điểm phân loại chính nhất quán.
- Demo đúng, demo dự đoán nhầm, mẫu chưa xác minh, yêu cầu tự khai demo giả, và lịch sử cũ thiếu nhãn. Nhãn lành/mã độc không được dùng để chấm trigger đúng/sai.
- Xuất PDF và mở chi tiết dùng kết quả đã có, không phát sinh lượt dự đoán chỉ để giải thích; nội dung PDF khớp màn hình/lịch sử và không có đường dẫn nội bộ.
- Đo trước/sau trên cùng máy và mẫu, tách thời gian phân tích khỏi tạo PDF. Không hứa tổng thời gian không tăng hoặc mục tiêu latency đã đạt trước khi đo. Giữ mô hình, công thức, ngưỡng và các kết quả nghiên cứu hiện có.

Tài liệu đối chiếu: [Streamlit 1.45 — cấu hình menu](https://docs.streamlit.io/1.45.0/develop/api-reference/configuration/st.set_page_config), [biểu đồ Altair](https://docs.streamlit.io/1.45.0/develop/api-reference/charts/st.altair_chart), [nút tải file](https://docs.streamlit.io/1.45.0/develop/api-reference/widgets/st.download_button). Hạn chế menu/theme đã đối chiếu thêm source thư viện cài tại máy trong lượt đề xuất.

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
