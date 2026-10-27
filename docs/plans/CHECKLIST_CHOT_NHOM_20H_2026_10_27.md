# Kế hoạch và bảng kiểm toàn nhóm — chốt 20:00 ngày 27/10/2026

Nguồn yêu cầu: `C:/Users/win9tui/Downloads/Góp ý Group 4 - IA2007.pdf`, 5 trang. Người dùng đã chốt mốc 20:00 ngày 27/10. Kế hoạch này thay lịch 28–29/10 của kế hoạch trưởng nhóm ở những chỗ xung đột.

Trạng thái lúc lập: đã đọc góp ý, kiểm tra code và các kết quả cũ, lập kế hoạch. Chưa có bằng chứng baseline/thí nghiệm mới hoàn tất trong đợt này. Các ô dưới đây là tiêu chí nghiệm thu, không phải xác nhận đã làm xong.

## 1. Điều chỉnh so với kế hoạch cũ

- Kế hoạch cũ tập trung vào phần trưởng nhóm, chưa phải bảng kiểm hoàn chỉnh của cả nhóm.
- Adaptive qua nhiều view phải chuyển vào ưu tiên chính: thầy yêu cầu rõ ở mục 5, ưu tiên số 2.
- Mục 1.5 có hai nhánh: outlier per-input trên SHAP và phòng thủ ở mức tập huấn luyện để làm bối cảnh. Không đánh dấu xong cả mục chỉ vì có SHAP-IF.
- Mục 1.1 đưa hai hướng thay thế. Với thời hạn 20:00, hướng nền tảng là đặt Reduced làm đóng góp chính, Full bổ sung, giải thích nguồn lực và đối chiếu Shadow. Đường kết quả theo lượng dữ liệu sạch vẫn là thí nghiệm đã đề xuất, nhưng không được chiếm mất thời gian của adaptive và baseline chính.
- Mục 1.3 cho phép nêu feature-space ngay Abstract nếu chưa có trigger binary được kiểm chứng; mục 5 xếp binary và thêm seed vào nhóm nếu có thời gian. Điều này cho phép xử lý phản biện bằng công bố đúng giới hạn, không chứng minh đã có trigger thật.
- Mục 1.6 cần bổ sung biến thiên hiện có. Thêm seed là tăng cường bằng chứng, không phải lý do trì hoãn việc báo min/max/SD của ba run đang có.
- Mọi thay đổi về phạm vi chạy phải dựa vào thời gian và tính hợp lệ, ghi trước khi xem kết quả mới; không bỏ run vì kết quả bất lợi.

## 2. Phân công và thứ tự

| Người | Phần chịu trách nhiệm | Có thể bắt đầu ngay | Đầu ra để chốt |
|---|---|---|---|
| Trưởng nhóm + Codex | Baseline, same-FPR, adaptive, Cross, seed, nguồn lực Full/Shadow, chẩn đoán FPR/AUC/timing, duyệt kết luận | Code và phân tích dữ liệu cũ; pilot thí nghiệm mới | Protocol, log, CSV, hình, count/n, nội dung EN, trạng thái từng góp ý |
| Phúc | Tính khả thi và trigger trên file trong phạm vi task được giao | Làm độc lập; thống nhất schema và giao diện kết quả | Quy trình, hash trước/sau, feature diff, kiểm tra file, kết quả X-R, giới hạn |
| Phú | Rà nguồn, thông tin xuất bản, citation, kiểm tra số và bảng phản hồi | Toàn bộ phần nguồn có thể làm ngay | Bảng nguồn đã xác minh, câu cần sửa, danh sách lỗi số/citation |
| Quân | Bản Word chính, cấu trúc, nội dung hệ thống tách riêng, bảng/hình/công thức | Dựng cấu trúc và dọn nội dung cũ ngay | Bản Word chính, phụ lục kỹ thuật, PDF đã kiểm tra layout |

Chỉ Quân giữ bản Word ghép chính của nhóm. Trưởng nhóm cung cấp nội dung và số đã duyệt; không để nhiều người sửa những bản khác nhau rồi ghép đè.

## 3. Phủ toàn bộ yêu cầu nghiên cứu

| Mục | Việc phải xử lý | Người | Bằng chứng để nghiệm thu | Khi chưa có thí nghiệm mới |
|---|---|---|---|---|
| 1.1 Full/Shadow | Đặt Reduced chính; giải thích Full có thêm dữ liệu/model sạch; so Shadow ở cùng mức FPR; không khẳng định Full tốt hơn khi số liệu không hỗ trợ | Trưởng nhóm + Quân | Abstract/Introduction/Scope/Results/Conclusion thống nhất; bảng nguồn lực và số liệu | Có thể hoàn thành hướng Reduced mà thầy cho phép; không nhận đã chứng minh lợi ích của Full khi ít dữ liệu |
| 1.1 bổ sung đã đề xuất | Cùng tập sạch và cùng ngân sách cho model Behavioral và Shadow; giữ main model cố định, reference/calibration/final riêng; báo M4-F, Full, Shadow | Trưởng nhóm | Protocol, mẫu số, runtime, biểu đồ và phạm vi cấu hình | Nếu chưa chạy, ghi thí nghiệm ngân sách sạch chưa hoàn thành; không biến đề xuất thành kết quả |
| 1.2 Cross | Đưa thất bại Cross vào kết quả chính; tách confirmation và final; giải thích 2018 bằng clean-trigger ASR, paired gain, paired-new/paired-lost | Trưởng nhóm + Quân | Hai bảng theo hai pool, truy được count/n và nguồn từng run | Phân tích cache là hợp lệ, nhưng chưa thay thế adaptive mới |
| 1.2 adaptive | Thực hiện phép thử thích nghi qua nhiều view với protocol riêng; định rõ mẫu, quyền truy cập, ngân sách và cách đánh giá; không gọi script Structural cũ là multiview | Trưởng nhóm | Code, protocol, log, score/kết quả và phạm vi thực chạy | Nếu chưa có kết quả hợp lệ thì mục này còn thiếu; câu giới hạn không làm nó thành đã xong |
| 1.3 binary | Kiểm chứng biến đổi file, feature diff và X-R; phân biệt thao tác được file với hiện thực đúng trigger và chứng minh backdoor | Phúc; trưởng nhóm duyệt | Artifact/manifest, kiểm tra file, trước/sau và kết quả đúng pipeline | Ghi toàn bộ kết quả chính là feature-space ngay Abstract và Scope, theo phương án thầy cho phép |
| 1.4 cùng FPR | TPR tại empirical FPR <=1% và/hoặc standardized partial AUC vùng <=1%; giữ bảng threshold calibration cũ; giải thích FPR drift bằng bằng chứng | Trưởng nhóm | CSV từng run, count/n, ties policy, nhóm positive và biểu đồ | Chưa có bảng mới thì chưa xong; không đưa ngưỡng ROC từ final vào bundle rồi gọi xác nhận độc lập |
| 1.5 SHAP outlier | SHAP-IF fit 500 benign reference, calibration 2.000 riêng; đối chứng malware chưa trigger; so cùng nhóm và mức báo nhầm | Trưởng nhóm | Baseline chạy hợp lệ, score/threshold, source ID, bảng và test | Pilot hoặc code chưa chạy xong không bằng baseline đã đánh giá |
| 1.5 training-level | Có một phương pháp phòng thủ ở mức tập train để đối chiếu bối cảnh; nêu quyền truy cập và phân biệt với per-input; nếu chạy thực nghiệm thì cần quy tắc lọc, retrain, utility và ASR | Trưởng nhóm; Phú hỗ trợ nguồn | Bảng phương pháp/nguồn; nếu tuyên bố thực nghiệm thì phải có protocol và kết quả lọc/retrain | Chỉ khảo sát tài liệu được ghi literature comparison; không ghi đã chạy training-level defense |
| 1.6 độ dao động | Báo từng seed, min/max/SD đúng cùng family/rate; ghi rõ CI bootstrap điều kiện trên model cố định | Trưởng nhóm | Bảng có số run và các run fail; chú thích CI đúng | Có thể hoàn thành thống kê hiện có; vẫn giữ giới hạn ba run 2024 |
| 1.6 bổ sung — task EMBER2024 riêng | Mục tiêu thêm hai seed mới tại spread Structural2%; kiểm pipeline và runtime sớm; rate3–4% nếu làm là điều kiện mới | Trưởng nhóm | Hai seed khóa trước, mọi kết quả confirmation và detection; không chỉ giữ run pass | Ghi số lượt đã thử/hoàn tất/được xác nhận; không mặc định thêm hai seed sẽ có năm run xác nhận |

## 4. Cấu trúc và cách viết — mục 2

| Mục | Việc | Chủ trì | Tiêu chí xong |
|---|---|---|---|
| 2.1 | Kiểm tra tiêu đề bản Word nhóm thật sự chốt; nếu còn Semantic/Consistency không đúng nội dung thì đổi hoặc giải thích bằng định nghĩa phù hợp | Quân + trưởng nhóm | Tiêu đề khớp tín hiệu thực đo; không đổi chỉ vì một bản cũ bị thầy góp ý |
| 2.2 | Xóa nhật ký revision, course rubric, after review, member supplied, require teacher confirmation khỏi bài chính | Quân | Tìm toàn văn và đọc lại ngữ cảnh; lịch sử chuyển sang tài liệu nội bộ |
| 2.3 | Gom quyền truy cập/giả định vào Threat Model & Scope và giới hạn vào Limitations | Quân + trưởng nhóm | Không rải lại nhiều câu phủ định ở mỗi đoạn; vẫn giữ giới hạn thiết yếu cạnh kết quả |
| 2.4 | Viết 3–4 đóng góp cụ thể ở cuối Introduction | Trưởng nhóm viết, Quân ghép | Mỗi đóng góp trỏ tới bằng chứng; kết quả Cross bất lợi được nêu rõ |
| 2.5 | Chuyển Docker/DB/restore/upload/UI/regression và nhật ký hệ thống sang artifact appendix/technical report | Quân | Bài lõi tập trung nghiên cứu; nhắm 10–12 trang với định dạng đã thống nhất, kiểm tra sau render |
| 2.6 | Dùng tên mô tả thay cho chỉ M3/M4, có bảng ánh xạ tên cũ | Trưởng nhóm chốt, Quân áp dụng | Tên trong văn bản/công thức/bảng/hình thống nhất; không bắt buộc đổi key API hay bundle trong lượt sửa bài |

## 5. Lỗi cụ thể — mục 3

Phú đối chiếu số, Quân sửa Word, trưởng nhóm duyệt kỹ thuật. Phải xác minh trên đúng bản Word cuối; không sửa mù theo số bảng của bản cũ.

- [ ] Seeds: 17, 29, 43; nếu bản hiện tại đã đúng, ghi đã xác minh, không bịa một thay đổi mới.
- [ ] BODMAS: 200 file, 175 có kết quả, 25 lỗi; kiểm tra alert2 thay vì lỗi đánh máy212 nếu còn. Không tự đổi dữ liệu thực.
- [ ] Header bảng: làm rõ `is_pe=0: benign/malware`, định nghĩa tử/mẫu của các cặp số.
- [ ] TADR/STRIP AUC dưới0,5: kiểm chiều score và kết quả đảo hướng; không coi AUC thấp tự động chứng minh lỗi code.
- [ ] Timing19,28 và27,28ms: ghi đúng phạm vi, số input, điều kiện đo; không tự suy nguyên nhân.
- [ ] "Core timing near28ms" và bảng21–32ms: đồng nhất phạm vi đo, không ép các số của phép đo khác nhau bằng nhau.
- [ ] Fixture benign bị V3 gọi malware: đưa bằng chứng vào giới hạn phân loại, không chỉ caption demo.
- [ ] Công thức(1)–(5): kiểm chỉ số tổng, tên view, font và ký hiệu trên PDF xuất từ Word.
- [ ] Poisoning rate: ghi thống nhất mẫu số là toàn bộ fit; 1.000/2.000/4.000 trên200.000 tương ứng0,5/1/2%.
- [ ] Sau khi thêm/bớt bảng: đánh số bảng/hình, dẫn chiếu trong bài, đơn vị%, dấu thập phân, chú thích và mẫu số đồng bộ.

## 6. Tài liệu tham khảo — mục 4

Phú dùng bài/website xuất bản chính thức để xác minh, không dùng câu trả lời của AI làm bằng chứng. Các mục dưới là danh sách thầy yêu cầu rà, chưa phải metadata đã xác minh trong lượt lập bảng này. Số citation phải đối chiếu lại sau khi ghép bài.

- [ ] Severi[6], SHAP[12], BadNets[21], TESSERACT[19], Dos and Don'ts[18].
- [ ] STRIP[40], Spectral Signatures[41], Tramer[31], Athalye[32], Goodfellow[29].
- [ ] SPECTRE[43], ABL/NAD/DBD[47–49], Conformal Risk Control[52].
- [ ] Kiểm tên bài/tác giả/năm/venue/trang/DOI hoặc URL; không lấy năm arXiv thay năm xuất bản khi trích bản chính thức.
- [ ] Kiểm bài nguồn thật sự hỗ trợ câu được trích; không chỉ sửa định dạng danh mục.
- [ ] Rút gọn đoạn nói về conformal khi phương pháp không sử dụng nó.
- [ ] Bổ sung bối cảnh phòng thủ backdoor cho malware từ nghiên cứu gốc, đặc biệt phần phòng thủ của Severi.

## 7. Lịch chốt 20:00

Các mốc dưới đây là mốc điều phối, không phải cam kết thí nghiệm sẽ cho kết quả tốt hoặc chạy kịp. Tại lúc lập, giờ địa phương khoảng12:10 ngày27/10.

| Giờ | Trưởng nhóm + Codex | Phúc | Phú | Quân |
|---|---|---|---|---|
| Ngay–13:00 | Khóa protocol/phạm vi; phân tích cache; pilot kỹ thuật và đo thời gian | Kiểm đường chạy file/feature/schema | Bắt đầu xác minh nguồn | Chốt đúng bản Word; dựng cấu trúc và phụ lục |
| 13:00–16:00 | Baseline/cùngFPR/Cross; chạy phạm vi adaptive đã khóa; quyết định thí nghiệm ngân sách sạch/training-level theo pilot và tài nguyên | Chạy và ghi bằng chứng trước/sau | Rà citation và các lỗi bảng sẵn có | Dọn cấu trúc, công thức và tên thành phần; không điền số chưa có |
| 16:00 | Báo phần nào có kết quả hợp lệ, phần nào đang chạy/chưa xong; không mở nhánh dài mới dự kiến vượt bàn giao | Báo trigger hoàn tất tới mức nào hoặc fallbackfeature-space | Giao danh sách sửa nguồn | Nhận danh sách bảng/hình sẽ đưa vào |
| 16:00–18:00 | Kiểm kết quả, xuất bảng/hình/nội dungEN; sửa lỗi có ảnh hưởng số liệu | Giao gói có hash/log và giới hạn | Kiểm count/n, citation và bảng phản hồi | Ghép kết quả đã duyệt |
| 18:00 | Chốt dữ liệu cho bản nộp; nếu cần sửa lỗi trọng yếu sau mốc này phải cập nhật mọi bảng/câu liên quan | Chốt phần được phép tuyên bố | Chốt nguồn và mục còn thiếu | Dừng nhận kết quả nghiên cứu chưa kiểm tra |
| 18:00–19:00 | Rà Abstract/Conclusion và nhận xét đúng với số | Kiểm nội dung binary nhóm viết | Đối chiếu bảng phản hồi với bài | XuấtWord/PDF, kiểm layout và dẫn chiếu |
| 19:00–20:00 | Duyệt kỹ thuật cuối, chuẩn bị trả lời thầy | Rà phần mình | Rà độc lập số và nguồn | Chốt đúng phiên bản, không ghi đè lẫn các bản |

Không chạy nhiều job nặng cùng lúc trên một máy chỉ để gọi là song song. Dùng số liệu pilot để phân bổ RAM/CPU, tận dụng thời gian máy chạy cho việc viết và QA. Không tự yêu cầu tải thêm dataset lớn.

## 8. Tiêu chí tối nay được gọi là chốt

1. Có một bảnWord chính và PDF tương ứng đã kiểm tra; phần kỹ thuật hệ thống được lưu riêng hoặc ở appendix phù hợp.
2. Có gói bằng chứng của các kết quả mới thực sự đưa vào bài: protocol, input/model/sourceID, score/count/n, log, script và kiểm tra.
3. Có bảng trả lời từng góp ý, ghi đúng trạng thái: đã xử lý theo phương án thầy cho phép; thực nghiệm hoàn tất trong phạm vi nào; xử lý một phần; chưa hoàn thành.
4. Không có câu trong Abstract/Conclusion nói vượt quá thí nghiệm; không gọi sửa file được là đã chứng minh binarybackdoor, không gọi thí nghiệm vector là thực tế.
5. Không gọi tài liệu cũ đã xem là holdout mới; không gọi code chạy không lỗi là hiệu quả detector được chứng minh.
6. Mọi ô còn trống là việc chưa nghiệm thu. Chốt một bản báo cáo trung thực không đồng nghĩa mọi hạn chế khoa học đã được khắc phục.

Người dùng đã cho phép làm phần việc được giao; các mốc trên không tạo thêm yêu cầu xin phép đối với chỉnh sửa thông thường. Không commit/push hoặc gửi tin cho thành viên khác tự động.
