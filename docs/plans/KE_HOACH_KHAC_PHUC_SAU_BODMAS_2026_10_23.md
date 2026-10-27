# Kế hoạch khắc phục sau BODMAS — 23/10/2026

**Cập nhật sau phê duyệt: đã triển khai worker/timeout, xử lý lỗi, chẩn đoán benign/Cross, nghiệm thu và sửa report.** Xem [kết quả triển khai](../REPAIR_2026_10_23.md): 113 test đạt, 1 skip; 25 file BODMAS vẫn chờ dữ liệu trên Kali; Cross yếu và báo nhầm fixture 2024 chưa được giải quyết. Phần dưới giữ nguyên kế hoạch và bằng chứng tại thời điểm lập để truy lịch sử. Giữ local/shared history, Reduced/Full và W50.

Mục tiêu là làm demo ổn định hơn, tìm nguyên nhân kết quả đáng ngờ và mô tả đúng khả năng của nghiên cứu. Không đặt mục tiêu ép mọi file lành thành BENIGN hoặc ép BODMAS thành 100% thành công.

## 1. Điểm xuất phát và thứ tự ưu tiên

| Hạng mục | Điều đã biết | Ưu tiên và hướng xử lý |
|---|---|---|
| Đọc file có thể chờ quá lâu | Extractor chạy trực tiếp trong tiến trình giao diện; chưa có timeout riêng. Có mẫu BODMAS 2024 mất khoảng 21,6 giây trên VM; chưa tái hiện treo/crash. | P1: tách tác vụ đọc file, giới hạn thời gian, bảo đảm phân tích được file tiếp theo. |
| File lành bị gọi MALWARE | Cả ba chương trình C# tự viết bị cấu hình demo 2024 gọi MALWARE. Một file lành khai báo trong ZIP cũng bị gọi MALWARE, nhưng khác hash fixture gốc. | P1: điều tra pipeline và so model sạch/model đầu độc; sau đó kiểm tra thêm file lành đa dạng. |
| 25/200 BODMAS chưa chấm được | Cùng 25 file bị `Invalid PE signature/header offset` ở cả bốn cấu hình, trước LIEF. Lỗi không được biến thành nhãn lành. | P1, làm song song trên VM: xác định file không hợp lệ hay bộ đọc có lỗi; giữ cả kết quả thất bại. |
| Cross ba view còn yếu | Với W50, trung bình recall trên 9 run Cross2024 đã xác nhận trong đợt đánh giá bổ sung: Reduced 0%, Full khoảng 5,73%. W25 Full khoảng 10,84%, chưa giải quyết được hạn chế. | P2: kiểm tra nguyên nhân từ M3/M4 và phép ghép; chỉ thử tiếp khi có giả thuyết cụ thể và nguồn đánh giá phù hợp. |
| Xác thực/phân quyền chưa có | API và dashboard Compose bind `127.0.0.1`; lịch sử dùng chung. | Tạm hoãn theo quyết định trước. Giữ phạm vi local; lập nhánh riêng trước khi mở nhiều người/public. |

Lượt kiểm tra ngày 23/10 đạt 28 test, 1 test symlink bị bỏ qua do quyền Windows. Các test này kiểm tra đường tính, lỗi đầu vào và PDF/lịch sử giả lập; không thay thế nghiệm thu Docker/PostgreSQL thật hoặc chứng minh detector chính xác.

**Phân biệt hai loại báo nhầm:** classifier gọi file lành là MALWARE khác với detector cảnh báo nhầm backdoor. Mục tiêu báo nhầm 1% trong calibration của detector không có nghĩa classifier chỉ được sai 1% và cũng không bảo đảm tập thực tế đạt 1%.

## 2. Bước 0 — Chốt mốc trước khi sửa

Người phụ trách code/tổng hợp thực hiện trước các thay đổi:

- Ghi Git revision, trạng thái file đang sửa, phiên bản dependency, hash model/bundle/extractor và cấu hình hiện tại. Lưu snapshot các file sắp sửa để quay lại khi cần; không cần tự commit/push.
- Lưu danh sách input theo SHA-256 và kết quả gốc của ba file lành, bốn cấu hình demo và các trường hợp lỗi. Dùng đúng byte hiện có, không biên dịch lại rồi coi đó là cùng file.
- Giữ nguyên ZIP BODMAS, CSV/JSON gốc, paper gốc và model/ngưỡng primary. Kết quả kiểm tra mới có thư mục/version riêng.
- Đánh dấu rõ các tập đã xem: Original Final, Fresh và tập đánh giá fusion ngày 20/10 đều đã được quan sát. Chúng có thể dùng chẩn đoán, không còn là tập kiểm tra chưa từng xem cho phương pháp mới.

**Đầu ra:** manifest mốc ban đầu và danh sách ca kiểm tra. **Đạt khi:** truy ngược được mỗi kết quả về đúng file, schema, model, code và ngưỡng; có thể quay lại bản trước sửa.

## 3. Bước 1 — Chống kẹt khi đọc PE

**Hướng đề xuất:** một tiến trình phụ có thể dừng được để trích đặc trưng của một file. Tiến trình chính quản lý thời hạn, nhận vector hợp lệ rồi mới chấm model. Đây là cách giới hạn tác vụ; không tự coi là một môi trường cách ly bảo mật hoàn chỉnh.

Việc thực hiện:

1. Tạo bộ điều phối dùng chung cho đường upload và công cụ BODMAS phiên bản mới. Bộ đọc vẫn chỉ phân tích tĩnh.
2. Đặt timeout cấu hình được, đề xuất khởi đầu **60 giây/tác vụ**, tính cả khởi động tiến trình. Mức này có khoảng dự phòng so với mẫu 21,6 giây; đo lại trên máy demo và Kali trước khi chốt. Thử timeout bằng worker giả lập với hạn ngắn, không cần dùng malware để làm app treo.
3. Hết hạn phải dừng và thu hồi tiến trình, không chỉ ngừng chờ kết quả. Giới hạn số tác vụ đang chạy, không để bấm lại tạo thêm nhiều worker. Windows dùng cách khởi động tiến trình phù hợp và ẩn cửa sổ; Linux kiểm tra tương đương. Giới hạn CPU/RAM của Docker được giữ; đo tài nguyên trước khi bổ sung mức giới hạn riêng cho worker.
4. Phân biệt `timeout`, `parse_failed`, `worker_crashed`, `input_rejected`; tất cả hiển thị “Không phân tích được”, có lý do ngắn, không có điểm/nhãn giả. Tác vụ cũ kết thúc muộn không được ghi đè kết quả file mới.
5. Giữ kiểm tra 50 MiB, schema, số chiều và giá trị hữu hạn. Ràng buộc kết quả trả về với hash file/yêu cầu; không nhận output dở hoặc sai schema. Dọn dữ liệu tạm và worker sau thành công, lỗi hoặc hủy.
6. Giữ hash file/vector, metadata và kết quả chấm của file hợp lệ. Chỉ lưu bản phân tích thành công vào luồng lịch sử hiện tại; nếu bổ sung nhật ký lỗi thì phải tách trạng thái rõ, không giả thành một bản phân tích đã thành công.

**Nghiệm thu:**

- Worker chậm bị dừng trong thời hạn cấu hình cộng khoảng thu hồi đã đo; đặt mục tiêu thu hồi trong 2 giây trên máy nghiệm thu và báo lại nếu không đạt.
- Sau ca timeout/crash, file hợp lệ tiếp theo vẫn phân tích được; không còn worker mồ côi hoặc dữ liệu tạm bỏ quên.
- File lỗi không trả BENIGN/MALWARE, không tạo lịch sử thành công và không giữ kết quả cũ trên màn hình như kết quả của file lỗi.
- Cùng byte/schema/model: vector và các quyết định khớp bản trước; điểm chấm khớp trong sai số đã dùng ở kiểm tra đường selected. Đo thêm chi phí khởi động worker, không lấy thời gian chấm model thay thời gian upload đến kết quả.
- Kiểm tra trên Windows và Linux/Kali hoặc container Linux; ghi riêng nền tảng chưa được thử.

**Phạm vi code dự kiến:** `dashboard_input.py`, lời gọi trong `dashboard/app.py`, bộ điều phối/worker mới, `check_bodmas_static.py` bản mới và test liên quan. Không thay công thức detector để giải quyết timeout.

## 4. Bước 2 — Điều tra file lành bị báo độc

**Hướng đề xuất:** xác định nguyên nhân trước, rồi mới sửa đúng phần gây lỗi.

Các bundle nghiên cứu hiện dùng main model đã đầu độc có chủ đích. Full và Reduced của cùng thí nghiệm dùng chung main model, nên dự đoán BENIGN/MALWARE giống nhau là bình thường. Full có thêm tín hiệu cho cảnh báo backdoor, không mặc nhiên sửa lại nhãn của main model.

### 2A. Tái kiểm tra ba file đang có

- Kiểm tra hash/source, schema V2/V3, model thực nạp, ngưỡng phân loại và phiên bản extractor. So điểm trực tiếp với điểm API/UI của cùng vector để phát hiện sai nối dữ liệu hoặc hiển thị.
- Trích lại đặc trưng của cùng file trên các môi trường được nghiệm thu; lưu raw/vector và chênh lệch có giải thích. Với V3, kiểm tra tương đương binary/raw đang có; với V2, giữ rõ khoảng trống tương đương extractor legacy. Kiểm tra V3 dùng chung đường upstream không phải đối chiếu độc lập với binary gốc của dataset. Cùng số chiều không đủ chứng minh cách trích giống dữ liệu huấn luyện.
- Chấm cùng vector bằng **clean main tương ứng và poisoned main** với cùng schema/seed. Clean main chỉ dùng chẩn đoán đối chứng; không cấp thêm cho Reduced hoặc biến Shadow thành phương pháp chính.
- Xem đóng góp đặc trưng để tìm hướng điều tra, không coi SHAP là bằng chứng khẳng định nguyên nhân.

| Kết quả điều tra | Cách xử lý |
|---|---|
| Điểm trực tiếp khác API/UI, hoặc sai schema/model | Sửa bug nối dữ liệu/hiển thị, thêm ca kiểm tra tái hiện và tính lại đầu ra bị ảnh hưởng. |
| Extractor tạo vector sai so với quy tắc đã xác minh | Sửa extractor có version mới, giữ byte mẫu và kết quả cũ; tính lại toàn bộ cohort chịu ảnh hưởng. |
| Clean main gọi BENIGN, poisoned main gọi MALWARE | Ghi nhận khác biệt giữa hai model; kiểm tra trên nhiều mẫu trước khi gán cho đầu độc. Không chữa bằng thay main model trong nghiên cứu. |
| Cả hai gọi MALWARE, pipeline chưa thấy sai | Điều tra độ phù hợp dữ liệu/model, đặc biệt nhóm .NET/PE tự biên dịch; đây có thể là hạn chế học máy. Không có bảo đảm sửa code là hết. |

### 2B. Bổ sung tập lành có mục tiêu

- Đề xuất khoảng **50 file lành khác nhau** để chẩn đoán ban đầu, có nguồn rõ và nguồn/build hoặc thông tin phát hành để kiểm tra; gồm PE native và .NET, không chỉ nhiều bản build của một chương trình. Chữ ký số là một bằng chứng nguồn, không là bảo đảm tuyệt đối file lành.
- Khóa tiêu chí chọn và manifest trước khi chấm; các file đã xem dùng chẩn đoán phải được đánh dấu. Dùng cùng danh sách qua bốn cấu hình; báo số file duy nhất và lỗi đọc riêng.
- Báo riêng số classifier gọi nhầm MALWARE và số cảnh báo backdoor trên file lành. Có 0 lỗi trên 50 file cũng chưa đủ để chứng minh tỷ lệ lỗi chung dưới 1%.
- Không dùng tập này vừa chọn ngưỡng vừa công bố đánh giá độc lập. Nếu kết quả dẫn đến sửa model/ngưỡng, phải có version/phương án nghiên cứu riêng và dữ liệu đánh giá chưa dùng. Điều chỉnh model/ngưỡng không nằm trong phần sửa kỹ thuật mặc định của kế hoạch này.

**Nghiệm thu:** tái hiện được từng ca, loại trừ hoặc tìm được bug cụ thể, có bảng clean/poisoned và hai loại báo nhầm. Nếu chưa tìm thấy bug và vẫn báo nhầm, ghi “đã điều tra, còn hạn chế model”; không ghi “đã sửa xong” chỉ vì demo chọn một file khác.

## 5. Bước 3 — Làm rõ 25 lỗi BODMAS và nguồn kết quả

Bạn giữ mẫu trên Kali có thể làm phần này song song với bước 1–2; máy tổng hợp không cần tải gói 67,9 GB.

1. Giữ nguyên manifest 200 file và SHA-256 byte hiện tại. Với 25 file lỗi, kiểm tra tĩnh kích thước, MZ, giá trị offset trỏ tới header PE, offset có nằm trong file không và chữ ký PE có tồn tại đúng chỗ không.
2. Tạo bảng từng hash với điều kiện kiểm tra bị lỗi và metadata nguồn/disarmed nếu có. Bộ đọc thứ hai chỉ dùng đối chiếu tĩnh; việc nó “đọc được” chưa chứng minh file hợp lệ hoặc bộ đọc chính sai.
3. Phân loại: file không hợp lệ/đã biến đổi có bằng chứng; bug bộ đọc có ca tái hiện; hoặc chưa đủ bằng chứng. Không quy nguyên nhân cho disarming chỉ từ tên archive, không sửa header/khôi phục khả năng chạy hoặc thay mẫu khó bằng mẫu khác.
4. Nếu xác nhận bug bộ đọc: sửa trong version mới, kiểm tra lại đúng 25 mẫu và cả 175 mẫu đã đọc được để phát hiện ảnh hưởng ngoài ý muốn. Nếu chỉ là file không hợp lệ, giữ từ chối và cải thiện thông báo; không đặt điều kiện phải đạt 200/200.
5. Làm rõ `smoke.log`/`benign.log` lệch CSV/JSON; lấy stdout/stderr hoặc ghi chính xác log thuộc lượt nào. Làm rõ source/build/hash của file lành được gửi.
6. Thu hash code/model thật trong môi trường đã chạy, image ID, lệnh chạy và cấu hình container nếu còn; danh sách ứng viên dùng lấy mẫu, metadata nhãn/ID gốc để kiểm tra nguồn và overlap nếu có. Không dùng bundle ID thay kiểm tra mọi byte model, không coi tên file là hash byte disarmed.

**Gói bạn gửi lại:** bảng chẩn đoán 25 hash; log và manifest giữ nguyên; hash code/model và ghi chú môi trường; source/build/hash file lành; ghi chú UTF-8; kết quả lượt mới nếu có. Không cần gửi raw malware để tổng hợp báo cáo. Có thể kèm vector/raw phục vụ đối chiếu nếu được phép, nhưng chỉ số liệu/log không cho phép chấm lại binary độc lập.

**Nghiệm thu:** mọi mẫu vẫn có trạng thái và mẫu số; điểm lệch được giải thích hoặc ghi là chưa xác minh. Thiếu bằng chứng từ VM thì để phần đó chờ, không ngăn sửa worker/UI độc lập. Chưa chứng minh trigger có thể hiện thực trên PE và giữ chức năng malware vẫn là giới hạn nghiên cứu.

## 6. Bước 4 — Xử lý điểm yếu Cross ba view và M3/M4

**Hướng đề xuất:** một vòng chẩn đoán có giới hạn, không chạy lại vô hạn các tỷ trọng đã thử.

1. Tận dụng kết quả W25/W50/W75/MAX/M3/M4 đã có. Kiểm tra score từng thành phần, dấu/độ lớn SHAP, reference ranks, ties, ngưỡng, sample IDs và mẫu số recall; xem tín hiệu yếu ở bản thân M3/M4 hay bị phép ghép làm giảm. Đối chiếu theo protocol/version trong bundle và code primary: M4-F hiện là `max(0, p_behavioral - p_main)`; một số tài liệu cũ còn mô tả công thức legacy. Kiểm tra paper đúng phiên bản, không sửa ngược kết quả lịch sử để khớp công thức mới.
2. Nếu là bug công thức/triển khai: thêm ca tái hiện, sửa version mới và tính lại các kết quả chịu ảnh hưởng. Nếu đúng công thức mà điểm không phân biệt được, ghi là hạn chế phương pháp.
3. Chỉ đề xuất vòng thử mới khi bước 1 cho một giả thuyết cụ thể. Tối đa một vòng, tối đa ba ứng viên ngoài W50; công thức, tài nguyên, ngưỡng/calibration và tiêu chí chọn phải được ghi trước khi chấm tập mới. Không thêm M5 hoặc clean main cho Reduced để cải thiện số.
4. Một ứng viên chỉ được xét nâng thành phương án chính nếu vừa cải thiện recall cần thiết, vừa giữ báo nhầm/nhóm tấn công khác/tài nguyên trong giới hạn đã khóa trước. Mỗi phương án có ngưỡng calibration riêng; không kế thừa “1%” của thành phần rồi áp cho OR/max.
5. Nguồn đánh giá độc lập phải được kiểm tra còn đủ và chưa dùng trước khi khóa vòng thử. Nếu không có nguồn phù hợp, chỉ báo thăm dò. So paired trên cùng source IDs; số run không phải số mẫu độc lập.

**Điểm dừng:** sau kiểm tra bug và tối đa một vòng có cơ sở, nếu không có cải thiện đáng giữ thì tiếp tục W50, lưu kết quả âm và thu hẹp kết luận. Không hứa đạt recall cao cho Cross chỉ bằng đổi tỷ trọng. Shadow tiếp tục là đối chứng có thêm model, tách rõ quyền truy cập.

**Nghiệm thu:** công thức và code khớp; mọi so sánh ghi recall, báo nhầm, tỷ lệ tấn công còn thành công sau cảnh báo theo đúng quy tắc đánh giá, mẫu số, tài nguyên và ảnh hưởng lên nhóm khác. Báo độ không chắc chắn của so sánh paired, không coi các run dùng lại source IDs là độc lập. Hạng mục có thể kết thúc bằng “giới hạn phương pháp đã kiểm chứng”, không đồng nghĩa điểm yếu đã được khắc phục.

## 7. Bước 5 — Giữ local; auth là nhánh có điều kiện

Phạm vi hiện tại tiếp tục local/shared history theo quyết định ngày 19/10. Kiểm tra cổng thực chạy và Compose còn giới hạn localhost; không xóa database/volume và không tự chia người sở hữu cho lịch sử cũ.

Nếu nhóm chuyển sang public hoặc nhiều người dùng, lập nhánh triển khai riêng: xác thực trước các endpoint; chọn lịch sử dùng chung có kiểm soát hay tách theo người dùng; kiểm tra quyền đọc từng bản ghi/PDF; giới hạn tải và số tác vụ; cấu hình HTTPS/triển khai và backup/restore. Cách gán dữ liệu cũ cần quyết định của nhóm, không tự suy đoán.

**Nghiệm thu local:** cổng đúng phạm vi, lịch sử cũ còn đọc được, PDF và lưu/đọc kết quả hoạt động. **Auth vẫn ghi tạm hoãn**, chưa gọi đã sửa.

## 8. Bước 6 — Nghiệm thu chung, paper và demo

- Chạy ca thành công, file không hợp lệ, quá lớn, timeout, worker crash và retry; sau mỗi lỗi phân tích tiếp file lành. Kiểm tra đổi file/bundle/theme, lịch sử và PDF không dùng nhầm kết quả hoặc tính lại ngoài ý muốn.
- Kiểm tra API + database thật bằng bản ghi QA được đánh dấu; giữ bản ghi cũ. Đo lại thời gian toàn luồng trên đúng máy trình bày, kèm cold/warm và chi phí trích đặc trưng; không hứa 10 ms toàn hệ thống.
- Giữ bộ demo có cả ca đúng và ca báo nhầm được giải thích. Thực hiện một lượt trình diễn liên tục trên máy dùng ở lớp; có kết quả lưu sẵn làm dự phòng.
- Khi biên tập paper: đưa thiết lập BODMAS vào Experimental Protocol, bảng chính vào Results và ý nghĩa/giới hạn vào Discussion. Appendix giữ chẩn đoán lỗi, provenance và timing chi tiết. Giữ tiêu đề người dùng đang dùng, nguồn gốc số liệu và file gốc; tạo bản sửa có ghi thay đổi. Đây là hạng mục dự kiến, chưa chuyển nội dung trong lượt lập kế hoạch.
- Tách ba nội dung khi trình bày: phân loại mã độc; cảnh báo backdoor; khả năng đọc file. Không lấy thành công ở một nội dung làm bằng chứng đã giải quyết hai nội dung còn lại.

## 9. Phân công và lịch dự kiến

| Chặng | Người thực hiện | Ước lượng chủ động | Phụ thuộc |
|---|---|---|---|
| Chốt mốc + tái hiện ba ca lành | Người phụ trách code/tổng hợp | Nửa đến một buổi | Code/model/file lành đang có |
| Worker, timeout, trạng thái lỗi và test | Người phụ trách code | 1–2 ngày làm việc | Chạy kiểm tra được trên Windows và Linux |
| Điều tra clean/poisoned + tập lành bổ sung | Người phụ trách model, phối hợp code | 1–2 ngày sau khi đủ input | Nguồn file lành, manifest và extractor |
| Chẩn đoán 25 BODMAS + đối chiếu log | Bạn giữ mẫu trên Kali | Song song; nửa đến một ngày nếu môi trường còn nguyên | Mẫu/log/runtime trên VM |
| Chẩn đoán Cross và quyết định có thử thêm | Người phụ trách nghiên cứu | Một buổi; thời gian vòng thử tính sau | Score cache; nếu thử mới cần tập chưa dùng |
| Nghiệm thu máy demo + cập nhật paper | Nhóm trình bày/code/report | Khoảng một ngày | Các kết quả đã khóa và máy demo |

Ước lượng là để chia việc, không phải thời hạn bảo đảm. Không chặn toàn bộ kế hoạch khi chờ bạn bên VM; bước worker và các file lành đang có làm độc lập được. Tải/tìm dữ liệu mới hoặc thay đổi phương pháp nghiên cứu có thể kéo dài hơn phần sửa kỹ thuật.

**Khuyến nghị thực hiện:** chốt mốc → làm worker và điều tra ba file lành song song với bạn kiểm tra BODMAS → kiểm tra tập lành bổ sung → chẩn đoán Cross có điểm dừng → nghiệm thu demo và sửa paper. Auth giữ ngoài lượt local này.

## 10. Quy tắc báo trạng thái

- **Đã sửa:** có bug/ca lỗi cụ thể, thay đổi và kiểm tra trước/sau đạt.
- **Đã giảm rủi ro:** như timeout/worker; vẫn nêu giới hạn.
- **Còn giới hạn nghiên cứu:** detector yếu, nguồn nhãn/trigger chưa đủ hoặc model còn báo nhầm khi chưa xác định bug.
- **Đang chờ bằng chứng:** dữ liệu/log/môi trường do thành viên giữ.
- **Tạm hoãn:** auth cho phạm vi chạy local.

Không dùng “đã hoàn thành kế hoạch” thay cho “đã xử lý hết điểm yếu”.

## Căn cứ kiểm tra

- `docs/IMPLEMENTATION_2026_10_20.md`: tối ưu đường tính, thử fusion và các ca demo báo nhầm.
- `docs/BODMAS_RESULTS_2026_10_23.md`, `outputs/bodmas_2026_10_23/`: số liệu và giới hạn BODMAS.
- `outputs/fusion_binary_latency_2026_10_20/final_cohorts.csv`: W50/W25 và control trên các cohort.
- `output/demo_2026_10_20/catalog.json`: hash/source và kết quả ba chương trình lành.
- `outputs/status_review_2026_10_23/pytest_verified.xml`: 28 passed, 1 skipped, 0 failed/error.
- `src/xsentinel/data/pe.py`, `pe_v3.py`, `dashboard_input.py`, `service/scoring.py`, `primary_workflow.py`, `compose.yaml`: luồng hiện tại và vai trò model.
- `docs/plans/QUYET_DINH_5_DIEM_2026_10_19.md`: phạm vi đã chốt và auth tạm hoãn.
