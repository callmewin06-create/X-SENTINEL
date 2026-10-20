# X-SENTINEL — Kế hoạch triển khai và demo ngày 19/10/2026

**Nhật ký thực hiện ngày 20/10/2026:** người dùng yêu cầu triển khai, hoãn BODMAS chờ thành viên khác. Kế hoạch và các quyết định dưới đây được giữ để truy nguồn; tiến độ, kết quả mới và những phần chưa nghiệm thu ghi tại `docs/IMPLEMENTATION_2026_10_20.md`, không suy trạng thái hiện tại từ các câu chờ triển khai trong bản kế hoạch ban đầu.

**Trạng thái:** kế hoạch thực hiện theo năm quyết định đã chốt; không phải xác nhận code, thí nghiệm, dữ liệu BODMAS hoặc VM đã chạy thành công. Tên file giữ ngày bàn giao 19/10 dù phần chuẩn bị tài liệu tiếp tục sang 20/10/2026.

**Căn cứ:** `docs/plans/QUYET_DINH_5_DIEM_2026_10_19.md`, handoff ngày 06/10 và `output/ieee_2026_10_16/X_SENTINEL_IEEE_1col.docx`. Quyết định mới áp dụng cho phần bổ sung; artifact lịch sử giữ nguyên. Đây là năm lựa chọn xử lý, không phải năm lỗi đều bắt buộc khắc phục theo yêu cầu giảng viên.

**Bổ sung ngày 20/10/2026:** thêm bốn mục giao diện UI-11 đến UI-14: đồng bộ màu chữ Sáng/Tối, xuất PDF lịch sử, hiện SHA-256 đầy đủ tại Bước 3 và bỏ biểu tượng trước ba góc nhìn. Xem `docs/UI_FOLLOWUP_2026_10_20.md`. Đây là cập nhật phạm vi kế hoạch; chưa triển khai các sửa UI trong lượt ghi nhận này.

## 1. Mục tiêu và sản phẩm bàn giao

Hoàn thiện một bản local có lịch sử database hiện có, trình bày được quá trình phân tích PE và giải thích kết quả trung thực. Nghiên cứu bổ sung cần chỉ ra fusion M3/M4 có ích ở đâu, báo nhầm và chi phí ra sao, còn bỏ sót gì. Không đặt điều kiện X-SENTINEL phải thắng mọi trigger hoặc mọi đối chứng.

| Phần việc | Đã chốt thực hiện | Giới hạn phải giữ |
|---|---|---|
| Cross và fusion | Một vòng khảo sát nhỏ dùng tín hiệu/model hiện có | Không ghi đè primary; không tự huấn luyện lại ma trận |
| Shadow | Đối chứng bổ sung có clean full model | Không thay phương pháp chính; không gán tài nguyên này cho Reduced |
| Binary/BODMAS | Bổ sung đường đọc tĩnh binary đến kết quả | Chưa chứng minh backdoor trên malware giữ chức năng |
| Latency A+B | Tính phần cần dùng, đo và dùng lại kết quả phù hợp | Không chọn C: giảm model/đổi công thức/xấp xỉ SHAP để đạt tốc độ |
| Tài khoản | Tạm hoãn, local và lịch sử DB dùng chung | Không mở LAN/Internet, reset lịch sử hay tự thêm ownership |

Sản phẩm: protocol fusion; bảng kết quả và điểm từng mẫu; báo cáo BODMAS tĩnh; kiểm tra đường tính gọn; bảng thời gian có phạm vi đo; danh mục mẫu demo; checklist và hướng dẫn Kali riêng. Phần nghiên cứu mới dùng namespace riêng, dự kiến `outputs/fusion_binary_latency_2026_10_19/`; không sửa ngược báo cáo IEEE hoặc output primary.

## 2. Thứ tự làm và mốc phụ thuộc

| Mốc | Công việc | Điều kiện hoàn thành |
|---|---|---|
| P0 — giữ mốc cũ | Ghi code/config, hash bundle, ID đã dùng và trạng thái DB | Có danh sách để đối chiếu trước/sau |
| P1 — khóa nghiên cứu | Kiểm kê cache, nguồn chưa dùng; khóa ứng viên và cách chọn | Có protocol trước khi xem test mới |
| P2 — fusion, A+B và UI | Thử fusion trên Development; làm đường tính gọn riêng; bổ sung UI-11 đến UI-14 | Không thay primary; điểm/alert khớp; UI và PDF được nghiệm thu trước demo |
| P3 — kiểm tra mới | Đánh giá lựa chọn đã khóa trên source chưa dùng; đo thời gian | Có kết quả độc lập hoặc ghi rõ chỉ thăm dò |
| P4 — BODMAS Kali | Bạn phụ trách cung cấp tập con/metadata; chạy đọc tĩnh | Có manifest, lỗi và kết quả thực tế |
| P5 — tập demo | Pretest bộ PE thật, vector dự phòng và lịch sử/PDF | Biết trước kết quả, lỗi và cách giải thích |
| P6 — bàn giao | Kiểm tra theo tài liệu; tổng hợp bảng và log | Chỉ đánh dấu đạt phần có bằng chứng |

P1 và chuẩn bị A+B/công cụ BODMAS làm được trong khi chờ dữ liệu. Thiếu BODMAS không ngăn phần độc lập, nhưng chưa được ghi đã chạy BODMAS. Thời gian từng mốc phụ thuộc dữ liệu và máy thực tế; không hứa một ngày hoàn thành khi chưa đo.

**Vai trò đề xuất, chưa phải phân công đã xác nhận:** người giữ protocol/kết quả; người phụ trách BODMAS/VM Kali; người phụ trách API/UI/latency; người chạy lại và tập trình bày. Nhóm xác nhận tên người trước phần việc phụ thuộc; có thể kiêm nhiệm.

## 3. Gộp khảo sát Cross với thử fusion M3/M4

### 3.1. Giữ đúng tín hiệu và tài nguyên

M3 chính là tỷ trọng SHAP tuyệt đối lớn nhất của một view, không phải polarity contrast. Reduced dùng M4-R từ mô hình chính; Full dùng M4-F là khoảng lệch xác suất dương giữa Behavioral model sạch và main model. Không tự thêm M5 hoặc đổi công thức thành phần trong lượt fusion này.

Reduced nhận suspicious main cùng reference/calibration. Full có thêm ba clean view models; M4 dùng Behavioral model. Shadow nhận thêm clean full model và chỉ là đối chứng với tài nguyên bổ sung. Kết quả Shadow trên restricted không chứng minh nó đã giải quyết Cross hoặc làm được điều đó khi thiếu clean model.

Các thành phần được đổi sang rank theo benign reference; rank không phải xác suất có backdoor. So rule trên cùng input IDs, model, trigger và calibration IDs; detector không được dùng nhãn trigger thật để chọn rule lúc inference.

### 3.2. Grid nhỏ đề xuất để khóa trước khi chạy

Đặt `a = rank_ref(M3)`, `b = rank_ref(M4)` của Reduced hoặc Full:

| Rule | Công thức | Ý nghĩa |
|---|---|---|
| W25 | `0.25*a + 0.75*b` | Ưu tiên M4 |
| W50 | `0.50*a + 0.50*b` | Mốc primary hiện tại |
| W75 | `0.75*a + 0.25*b` | Ưu tiên M3 |
| MAX | `max(a,b)` | Dùng tín hiệu nổi bật hơn |
| M3 riêng | `a` | Đối chiếu đóng góp của fusion |
| M4 riêng | `b` | Đối chiếu đóng góp của fusion |

Có sáu công thức khác nhau mỗi biến thể. W50 đã là mốc cũ, không đếm thêm thành một detector độc lập. Đây là đề xuất hữu hạn, chưa phải danh sách đã chạy; không có cải thiện phù hợp thì giữ baseline và báo kết quả âm.

### 3.3. Chọn và xác nhận phương án

1. Dùng Development/cache để khảo sát; báo riêng restricted và cross stress. Original Final và Fresh đã xem chỉ là nguồn phân tích/phát triển cho phương pháp thay đổi.
2. Khóa source IDs cho reference, calibration, development và một tập final mới chưa dùng. Kiểm tra trùng với vai trò chính, pilot và nguồn local đã dùng; không khẳng định biết lịch sử quan sát ngoài nhóm nếu không có ID.
3. Mỗi rule có threshold riêng trên benign calibration, cùng IDs và mục tiêu 1%; reference/calibration/test tách biệt. Giữ strict `score > tau`. MAX không thừa hưởng FPR từ các threshold thành phần. Primary giữ threshold cũ; threshold phục vụ so sánh mới lưu riêng, kể cả baseline tính lại.
4. Ghi quy tắc chọn trước test: ưu tiên recall Development ở cùng mục tiêu calibration; khóa cách tính trung bình/cân trọng số run và cohort. Báo đồng thời benign FPR; hòa điểm ưu tiên FPR thấp hơn, rồi chi phí thấp hơn. Không chọn một rule riêng theo nhãn tấn công thật lúc inference.
5. Khóa một lựa chọn cho Reduced và một cho Full rồi mới kiểm tra final mới; giữ baseline, M3 và M4 làm đối chiếu. Không chỉnh tiếp bằng final rồi dùng chính final ấy xác nhận.
6. Nếu thiếu nguồn chưa dùng, vẫn làm khảo sát nhưng ghi **thăm dò**, không gọi đánh giá độc lập. Không thay nhãn nguồn cũ thành test mới.

Bảng phải ghi Recall trên successful eligible attacks; post-ASR giữ mẫu số eligible; FPR dùng mẫu lành. FPR final được đo riêng, không được bảo đảm ≤1%. Source lặp qua nhiều model không phải các mẫu độc lập. Giữ các ca thất bại, số đếm và kết quả âm; không dùng cải thiện restricted để che việc Cross vẫn yếu.

## 4. BODMAS trên Kali: kiểm tra binary tĩnh

### 4.1. Dữ liệu và gói bàn giao

Bạn cùng nhóm dùng **Kali Linux trong VM**. Hướng dẫn thao tác riêng: `docs/HUONG_DAN_BODMAS_KALI_2026_10_19.md`. Gói công cụ bàn giao dự kiến `BODMAS_VM_2026_10_19.zip` chứa mã nguồn/cấu hình build Docker/helper, fixture lành tự xây dựng và bốn bundle cố định: hai schema × Reduced/Full, seed 17, Spread, poison rate 0.02. Đây là subset kiểm tra, không phải toàn bộ ma trận; Shadow không có trong lượt này. Image cần được build theo guide khi còn mạng; gói ZIP không đồng nghĩa đã có runtime/image hoạt động. Cần xác nhận gói/hash và kết quả thực tế khi bàn giao.

Gói dữ liệu được nhắc đến khoảng 67,9 GB chưa có tại máy để xác nhận nội dung hoặc kết quả chạy. Không tự tải toàn bộ vào máy người dùng. VM vẫn dùng ổ host; phải tính archive, phần giải nén, ổ VM, Docker image, kết quả và snapshot. Ưu tiên xin/tách tập con phù hợp từ người có dữ liệu thay vì cho rằng VM giải quyết được thiếu dung lượng.

Trước khi chạy, ghi nguồn cấp, tên archive, hash nếu có, metadata và đường dẫn thực tế. Khóa quy tắc chọn tập con trước dự đoán; ví dụ lấy theo ID trong các nhóm nguồn đã định. Báo mẫu trùng/loại và mọi parse lỗi; không chỉ giữ mẫu mô hình dự đoán tốt. Ngân sách mẫu phụ thuộc nguồn và máy, chưa tự chốt bằng số lượng tùy ý.

### 4.2. Schema và kết quả cần lấy

BODMAS công bố vector 2.381 chiều theo EMBER/LIEF cũ. Không đưa thẳng vào V3 2.568 chiều hoặc thêm số 0. Nếu trích V3 từ binary, ghi extractor/schema/hash riêng. Chưa mặc định vector tái trích khớp vector gốc nếu chưa có cùng binary và hiểu cách disarm.

Luồng kiểm tra: **binary → kiểm tra/parse → vector đúng schema → bundle đã khóa → prediction và alert → kết quả/lỗi**. Không khôi phục khả năng chạy, không thực thi malware, không tạo trigger trên malware từ phạm vi này.

Mỗi mẫu cần ID/hash, nhãn nguồn, thông tin disarmed theo nguồn, parse/error, schema/extractor, xác suất/class, điểm/ngưỡng/alert và thời gian đúng phạm vi đo. Ghi thiếu dữ liệu là thiếu; không đổi lỗi thành verdict sạch.

Malware thông thường không có nhãn trigger của nhóm: tỷ lệ bị cảnh báo chỉ là **tỷ lệ cảnh báo**, không phải backdoor recall. Muốn đo báo nhầm phải có mẫu lành ngoài đi cùng pipeline; tách FPR phân loại malware và FPR cảnh báo trigger. BODMAS là kiểm tra bổ sung, không trộn vào 54 cấu hình primary.

### 4.3. Giới hạn binary vẫn còn

Có thể mở rộng fixture lành đã có bằng chương trình nguồn rõ, phép sửa xác định trước và đầu ra mong đợi. Sau sửa phải trích lại từ byte thật, đếm đặc trưng đổi theo view/ngoài pool; không ép vector về trigger mong muốn. So điểm model đã khóa trước/sau, kể cả không né được hoặc bị báo nhầm.

Byte sửa làm nhiều đặc trưng khác đổi là kết quả cần giữ. Chương trình lành chạy đúng vài trường hợp không chứng minh mọi hành vi được bảo toàn, càng không chứng minh payload malware còn chức năng. **Giới hạn này được giữ trong báo cáo; không bắt hoàn tất vector study phải có thử nghiệm malware còn hoạt động.**

## 5. Latency A+B, DB và phạm vi local

**A — chỉ tính phần cần:** X-R cần M3/M4-R; X-F cần M3/M4-F. Chạy STRIP khi chọn STRIP hoặc bộ so sánh đầy đủ. Giữ nguyên model, SHAP, phép tính và threshold; không chọn C để giảm model hay đổi phương pháp. Giữ đường suite làm đối chiếu.

**B — đo và dùng lại kết quả:** đo tách trích file, classifier, SHAP/thành phần, core, STRIP/suite, API và lưu DB. Tách cold/model load với warm prediction; dùng cùng mẫu/điều kiện cho đối chiếu. Không lấy cache hit làm thời gian suy luận mới, không cộng P95 thành P95 tổng. 10 ms vẫn là mục tiêu chưa hứa đạt.

Trước dùng đường gọn, kiểm tra prediction, score, threshold và alert khớp đường cũ với sai số công bố. Thành phần chưa tính phải ghi chưa tính/giá trị thiếu có nghĩa, không điền 0. Giải thích, PDF, history phải nhất quán với kết quả; retry không sinh bản ghi trùng. Chạy hồi quy phù hợp sau thay đổi trước khi công nhận kết quả.

Giữ database local và lịch sử dùng chung. Không reset/xóa lịch sử, tự gán owner, thêm login/API key/gateway hoặc mở LAN/Internet. Auth ghi **tạm hoãn**, không ghi đã giải quyết. Có điểm sao lưu trước thay đổi lưu trữ; kiểm tra VM dùng DB kiểm tra riêng khi cần, không ghi đè DB hiện có.

### Bổ sung sửa giao diện ngày 20/10/2026

| Mục | Việc cần sửa | Điều kiện hoàn thành |
|---|---|---|
| UI-11 — màu chữ | Đồng bộ chữ/nền khi chọn Sáng, Tối, Theo hệ thống trên ba trang và các thành phần tương tác | Chữ đọc rõ cả màn hình rộng/hẹp; đổi theme không chạy lại detector |
| UI-12 — PDF lịch sử | Làm nút PDF từng bản ghi dễ thấy; bổ sung PDF tổng hợp lịch sử đang hiển thị | Xuất đúng bản ghi/phạm vi, không dùng nhầm PDF cũ, không ghi thêm lịch sử |
| UI-13 — SHA-256 | Hiện/copy đủ 64 ký tự ở Bước 3; phân biệt hash file với hash vector | Khớp giá trị nguồn, không tràn giao diện; thiếu dữ liệu ghi Chưa lưu |
| UI-14 — tên ba view | Bỏ biểu tượng trước Cấu trúc, Hành vi API và Metadata trong phần tỷ trọng | Giữ tên/mã nhóm, thứ tự, thanh và phần trăm; không để khoảng trống thừa |

PDF từng bản ghi đã có trong code hiện tại, nên dùng lại luồng kết quả đã lưu. PDF tổng hợp mới phải ghi rõ phạm vi: danh sách hiện giới hạn tối đa 100 bản gần nhất, không phải toàn bộ database. Thiếu dữ liệu trong bản ghi cũ thì báo thiếu, không lấy kết quả model hiện tại để điền.

SHA-256 file PE lấy từ `input_metadata.file_sha256`; `input_sha256` là hash vector dùng chấm, không được gắn nhãn thành hash file. Các mục UI này được nghiệm thu riêng trên kết quả mới và lịch sử; không dùng kết quả kiểm thử UI cũ thay bằng chứng cho lần sửa mới. Chi tiết và tiêu chí: `docs/UI_FOLLOWUP_2026_10_20.md`.

## 6. Chuẩn bị demo PE thật trên lớp

| Bộ mẫu | Số lượng dự kiến | Phải biết trước | Mục đích |
|---|---:|---|---|
| PE lành tự viết/nguồn rõ | 2–3 | Nguồn, hash, kỳ vọng lành; fixture có đầu ra mong đợi | Minh họa đường PE và báo nhầm nếu xảy ra |
| BODMAS disarmed | 2–3 | ID nguồn, hash byte thực tế, tình trạng đối chiếu metadata, nhãn nguồn malware, parse/schema đã pretest | Minh họa phân tích tĩnh binary có nguồn mã độc |
| Vector tham chiếu dự phòng | Vài case | Dataset, chiều, bundle, kết quả đã biết | Dự phòng khi binary/môi trường lỗi |

Đây là **bộ tuyển chọn để trình bày**, không phải test ngẫu nhiên nghiên cứu. Pretest để biết thời gian/lỗi; ghi lý do chọn. Không gọi tỷ lệ đúng của vài ví dụ là accuracy hệ thống; ID demo đã xem không dùng lại như final chưa quan sát. Vector phải gắn nhãn “demo vector”, không đổi đuôi thành `.exe` để giả file thật.

Không hứa mọi PE lành đều được dự đoán lành hay BODMAS đều được dự đoán độc. Tách nhãn nguồn với prediction: fixture lành bị gọi malware là false positive trong case ấy. No alert không chứng nhận an toàn. Không tìm cho đủ case “bắt backdoor” từ BODMAS vì không có nhãn trigger của nhóm.

Lượt trình bày đề xuất 8–10 phút:

1. Nêu bài toán và hai kết quả riêng: phân loại malware và nghi ngờ trigger.
2. Giải thích Reduced/Full cùng tài nguyên; Shadow chỉ là đối chứng bổ sung.
3. Phân tích fixture lành: nguồn/hash, schema, prediction, điểm so với threshold.
4. Phân tích BODMAS đã pretest, nhấn mạnh đọc tĩnh. Nếu dữ liệu chưa đến, nói rõ còn chờ và dùng vector gắn nhãn đúng, không giả đã phân tích binary.
5. Mở lại lịch sử, giải thích và xuất PDF; cho thấy kết quả nhất quán.
6. Trình bày bảng nghiên cứu riêng: bắt được, bỏ sót, báo nhầm và thời gian; không thay bằng vài case demo.
7. Nêu giới hạn binary, mục tiêu tốc độ chưa đạt nếu số đo vẫn vượt và auth đang hoãn.

Mang danh mục mẫu và vector dự phòng; không phụ thuộc tải archive lớn ngay trên lớp. Không đưa malware vào gói chia sẻ công khai chỉ để tiện demo.

### 6.1. Hệ quả thực tế khi các giới hạn còn tồn tại

- Cross còn yếu: trigger sửa phối hợp nhiều view có thể không bị cảnh báo; không dùng no alert làm chứng nhận an toàn.
- Fusion không cải thiện: cách ghép có thể kém M3 hoặc M4 riêng; giữ baseline/thành phần tốt thay vì ép một fusion phải thắng.
- Binary chưa chứng minh giữ chức năng: chỉ báo được xử lý tĩnh những byte được cấp; không nhận đã có backdoor trên malware còn hoạt động.
- Latency vẫn trên mục tiêu: chưa có cơ sở nói đạt 10 ms; demo phải dự trù thời gian đọc file và round trip ngoài core.
- Auth hoãn: lịch sử dùng chung không có quyền sở hữu/cách ly từng người; chỉ dùng local theo phạm vi đã chốt.

## 7. Nghiệm thu, hệ quả và bằng chứng phải giữ

| Phần | Đánh dấu đạt khi | Nếu chưa đạt |
|---|---|---|
| Primary | Hash/model/bundle và mốc điểm kiểm tra được giữ | Điều tra khác biệt, không âm thầm thay |
| Fusion | Có protocol, điểm/mẫu số, threshold và test mới | Ghi thăm dò; không bắt buộc thắng |
| Cross | Báo riêng stress và giữ ca yếu/thất bại | Giữ giới hạn, không suy từ restricted |
| BODMAS | Có nguồn/manifest, parse/schema, kết quả/lỗi thực tế | Ghi chờ dữ liệu hoặc môi trường |
| Latency | Đường gọn tương đương, có đo đúng phạm vi | Không báo nhanh hơn/đạt 10 ms |
| Demo/history | PE thật pretest, metadata/retry/history/PDF nhất quán | Nêu lỗi và dùng vector dự phòng đúng nhãn |
| Kali/máy khác | Người nhận làm lại được theo guide, có log | Không coi Docker trên cùng host là máy vật lý thứ hai |

Giữ quyết định, protocol/config, manifest ID đã dùng, hash code/model/schema, điểm từng mẫu, bảng tổng hợp, số đo, danh mục demo và log kiểm tra. Tách tính lại bảng từ score có sẵn với huấn luyện lại từ dữ liệu gốc. Không đưa credentials, lịch sử DB thật hoặc archive malware vào gói chia sẻ mặc định. Kế hoạch không tự cho phép commit/push.

Báo trạng thái **chưa làm / đang làm / đã có bằng chứng / tạm hoãn**. Hiệu quả detector, độ hoàn thiện phần mềm và khả năng trình bày phải báo riêng; không gộp thành một tỷ lệ hoàn thành không có cơ sở.

