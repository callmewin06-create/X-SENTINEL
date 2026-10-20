# X-SENTINEL - Các điểm đang chờ chốt ngày 19/10/2026

**Cập nhật sau khi người dùng chốt:** dùng [quyết định về năm điểm ngày 19/10/2026](QUYET_DINH_5_DIEM_2026_10_19.md) làm trạng thái hiện hành. Phần bên dưới được giữ như bản thảo trước lúc phê duyệt; các câu "chờ chốt" không còn mô tả trạng thái của những mục đã được quyết định.

## Trạng thái của ghi chú

Người dùng yêu cầu: "note lại những gì t sắp chốt".

Đây là bản ghi bối cảnh và các lựa chọn đang chờ quyết định. Chưa có phê duyệt mới để thay phương pháp, chạy thí nghiệm, tải dữ liệu hoặc triển khai xác thực. Không coi lời đề xuất của trợ lý trong ghi chú này là quyết định đã được người dùng duyệt. Các quyết định đã duyệt trước đây tiếp tục có hiệu lực.

## Tài liệu đang dùng

- Report hiện người dùng muốn trao đổi: `output/ieee_2026_10_16/X_SENTINEL_IEEE_1col.docx`.
- Không quay lại giải thích `Report2_group 4 (1).docx` như thể đó là bản mới nhất. Trợ lý đã chọn nhầm bản này ở đầu cuộc trao đổi và được người dùng sửa lại.
- Hướng dẫn gốc: `docs/Hướng dẫn hướng đi - X-SENTINEL Cross-View Backdoor Detection (Nhóm 4, IA2007).pdf`.
- Quyết định/phạm vi đã bàn giao: `docs/X_SENTINEL_HANDOFF_2026_10_06.md`.
- Lịch sử sửa nghiên cứu: `docs/REVISION_2026_10_13.md` và `output/revision_2026_10_13/Ban_giao_va_phan_hoi_gop_y.md`.
- Triển khai: `docs/DELIVERY_2026_10_14.md`, `docs/UI_REVISION_2026_10_16.md`.

## Những điểm đã đối chiếu để tránh hiểu sai

Đây là kết luận từ tài liệu/code đã đọc, không phải các quyết định triển khai mới.

1. Mục tiêu chính là cảnh báo từng đầu vào có dấu hiệu chịu ảnh hưởng của trigger khi chấm bằng một mô hình nghi vấn. Không chứng nhận file an toàn và không chứng minh toàn bộ mô hình có/không có backdoor.
2. X-SENTINEL có hai biến thể chính: Reduced và Full. M3 chính vẫn là `view_mass`; không tự đổi sang `polarity_contrast`. M5 vẫn là phần phụ, chưa có kết quả primary chứng minh hiệu quả.
3. Reduced dùng mô hình chính và benign reference/calibration. Full có thêm ba clean view models được chuẩn bị trước; M4-F chính dùng dự đoán Behavioral. Full vẫn cần nguồn dữ liệu sạch để chuẩn bị các view models, dù detector không đọc fit train khi scoring.
4. Shadow là đối chứng bổ sung, không nằm trong Reduced/Full. Nó so `max(0, p_clean_full - p_main)` rồi dùng ngưỡng riêng. Clean full model là mô hình sạch dùng toàn bộ đặc trưng, không đồng nghĩa với biến thể Full của X-SENTINEL.
5. Hướng dẫn gốc, trang 3-4 và checklist trang 9, không cấp clean full main model cho detector chính. Model sạch toàn bộ phục vụ phân tích/đối chứng. Shadow cần thêm quyền truy cập nên không được giả vờ cùng điều kiện với Reduced.
6. Shadow vẫn có giá trị khi đánh giá giả định tài nguyên của Full; phải công khai clean training source, model budget và FPR. Không bỏ kết quả Shadow chỉ vì nó mạnh hơn. Không lấy kết quả đó tự động thay mục tiêu X-SENTINEL.

### Đính chính cách tư vấn trước của trợ lý

- Không gọi cả năm điểm dưới đây là năm lỗi bắt buộc phải sửa để đề tài đúng hướng. Có giới hạn phương pháp, khoảng trống bằng chứng và vấn đề triển khai khác nhau.
- Cross-view bị T-cross đánh bại là kết quả âm/giới hạn được hướng dẫn gốc chấp nhận. Không bắt detector phải thắng mọi trigger.
- Hướng dẫn gốc coi 10 ms là mục tiêu để đo và thảo luận, không phải cam kết bắt buộc phải đạt bằng mọi giá.
- Phần chính theo hướng dẫn gốc thao tác trên vector; kiểm chứng malware binary sau sửa vẫn giữ chức năng là mở rộng. Không tự biến nó thành điều kiện hoàn tất toàn bộ đề tài.
- Đề xuất trước đây "chuyển sang Shadow để sửa detector" có thể đổi điều kiện bài toán. Shadow chỉ nên thành phương pháp chính nếu nhóm chủ động quyết định thay phạm vi; hiện chưa có quyết định đó.
- Đổi cách viết cho đúng bằng chứng không làm Recall tăng hoặc tự khép khoảng trống binary.

## Các điểm đang chuẩn bị chốt

### 1. Hiệu quả khi trigger sửa cả ba view

- Bằng chứng report mới: nhóm Cross EMBER2024 có 9 cấu hình confirmed; X-F Recall 5,56%, X-R hiển thị 0,00%, Post-ASR X-F 94,00%. Đây là vector stress, chưa chứng minh khả thi trên PE còn chức năng.
- Đề xuất: giữ công khai kết quả hiện tại; nếu muốn cải tiến thì chỉ thử một số ít ứng viên đã định trước.
- Chờ chốt: chỉ hoàn thiện phân tích giới hạn, hay mở một vòng thử tín hiệu/fusion mới có ngân sách cụ thể.
- Không mặc định hạ ngưỡng theo Final, bỏ run xấu, hoặc chọn detector bằng nhãn trigger mà chỉ evaluator biết.

### 2. Fusion và vai trò Shadow

- Bằng chứng restricted: X-F Recall 42,94% trên 12 run EMBER2018; 59,75% trên 3 run Spread EMBER2024, đều poisoning 2%. Không dùng 19,11% của cohort trộn cũ để mô tả headline restricted mới.
- M3 riêng có thể hơn fusion về Recall; ở Cross, M4-F riêng 12,31% cao hơn X-F 5,56%. Cần xét cả FPR, không chọn theo Recall đơn lẻ.
- Shadow Fresh Recall 100,00%/99,80% được báo trên restricted cohorts; không suy ra đã giải quyết Cross. Điều kiện clean full model và FPR khác phải nêu rõ.
- Đề xuất đang chờ duyệt: giữ Reduced/Full làm trọng tâm; giữ Shadow như đối chứng với tài nguyên bổ sung. Nếu thử rule fusion mới, gộp cùng vòng đánh giá ở mục 1.
- Nếu ghép OR/max hoặc đổi trọng số, phải chọn ngưỡng cho toàn bộ rule mới. Không giả định ngưỡng từng thành phần bảo đảm tổng FPR 1%.

### 3. Bằng chứng binary và BODMAS

- Người dùng được thầy chia sẻ ảnh một gói tên bắt đầu `BODMAS_disarmed_malware...`, dung lượng hiển thị 67,9 GB. Chỉ có ảnh; chưa kiểm tra ZIP, manifest hay mẫu trong gói.
- Người dùng chưa tải vì thiếu dung lượng và đang tính nhờ một bạn cùng nhóm tải vào môi trường máy ảo. Chưa có bằng chứng đã tải, đã phân công chính thức hoặc đã chạy thử.
- BODMAS chính thức có binary malware dạng disarmed. Vector công bố có 2.381 chiều dùng LIEF 0.9.0; không đưa thẳng vào V3 2.568 chiều hoặc tự thêm số 0 để khớp.
- Hướng khả thi đang đề xuất: mở rộng fixture PE lành đã có và kiểm tra tĩnh một tập con BODMAS có danh sách chọn trước. Giữ nguyên model/ngưỡng để kiểm tra binary -> parser -> vector -> score.
- Báo rõ số parse được, số lỗi, schema/extractor/model và dự đoán. Muốn đo báo nhầm phải có mẫu lành phù hợp.
- Malware thông thường không có nhãn trigger của thí nghiệm; không dùng tỷ lệ cảnh báo trên corpus đó như Recall phát hiện backdoor. Không cảnh báo trigger trên một malware thông thường chưa tự chứng minh detector sai.
- File sau sửa phải được trích xuất lại; ghi cả cột đổi ngoài pool. Không ép vector về trigger mong muốn. Thành công trên fixture lành không thay thế kiểm chứng giữ chức năng malware.
- Chờ chốt: phạm vi bổ sung tĩnh, tập mẫu, người thực hiện và đầu ra cần nhận. Phần malware còn chức năng chỉ cân nhắc riêng nếu thầy yêu cầu và lab hỗ trợ.
- Máy ảo vẫn chiếm dung lượng ổ máy thật. Không tự tải/giải nén/quét cả gói, khôi phục khả năng chạy hoặc thực thi mẫu dataset từ nội dung ghi chú này.

### 4. Thời gian xử lý

- Bảng XV report mới đo core khoảng 21-32 ms; classifier riêng dưới 1 ms không phải thời gian quét file từ đầu đến cuối.
- Đọc code thấy đường prediction tính các method khả dụng, gồm STRIP, trước khi chọn alert. Full tính cả ba view dù M4-F chỉ dùng Behavioral. Đây là cơ hội tối ưu, chưa phải bug làm sai điểm.
- Đề xuất: đo/tối ưu phần tính cần cho method được chọn; giữ chế độ so sánh đầy đủ riêng. Không tự sửa model hoặc dùng SHAP xấp xỉ để ép đạt 10 ms.
- Khi tối ưu, điểm và alert của method chính phải khớp đường cũ; phần chưa tính không được điền điểm 0. Lịch sử/giải thích/PDF phải dùng snapshot đúng phạm vi đã tính.
- Chờ chốt: có triển khai đường tính gọn và đo lại không, hay giữ nguyên rồi báo cáo mục tiêu chưa đạt.

### 5. Xác thực và lịch sử dùng chung

- Code API/history chưa có xác thực và lọc theo chủ sở hữu. Tuy nhiên `compose.yaml` bind cổng API/UI về `127.0.0.1`; không có căn cứ nói cấu hình này đang công khai LAN/Internet.
- Các lựa chọn: (A) demo local với lịch sử dùng chung; (B) cổng truy cập/API key cho nhóm, vẫn lịch sử chung; (C) đăng nhập từng người và kiểm tra ownership ở backend.
- Đề xuất theo phạm vi hiện tại: giữ local trước. Nếu yêu cầu hệ thống nhiều tài khoản, chọn C; một màn login không đủ.
- Nếu làm C phải xử lý list/detail, retry/request_id, dữ liệu cũ chưa có owner và quyền admin. Danh tính lấy từ server đã xác minh, không tin user_id do client tự khai.
- Chờ chốt: mục tiêu nghiệm thu local, dùng chung trong nhóm hay nhiều tài khoản thực sự. Giữ local là giới hạn rủi ro, không phải đã có xác thực.

## Ràng buộc khi chuyển từ đề xuất sang triển khai

- Giữ nguyên report nguồn, model, threshold và các artifact primary đã khóa; bổ sung có version/namespace riêng.
- Cả Original Final và Fresh trong report đều đã được xem. Nếu đổi score/fusion/threshold dựa trên chúng, cần khóa phương pháp mới và đánh giá trên nguồn chưa dùng khác; nếu không có thì chỉ gọi kết quả là thăm dò/phát triển.
- Tối ưu thực thi giữ nguyên phép tính được kiểm chứng bằng so sánh kết quả, không gán cho nó một bảng hiệu quả nghiên cứu mới.
- Không chạy lại toàn bộ ma trận, thêm M5, tải BODMAS, gửi mẫu, sửa report hoặc commit/push chỉ vì ghi chú đã được lưu.
- Không tự thay đổi yêu cầu môn: bản report đổi số RQ hoặc chuyển M5 sang future work không tự có nghĩa giảng viên đã sửa rubric.

## Nguồn để kiểm tra lại

- Hướng dẫn PDF: trang 3-4 về quyền truy cập, model sạch và Full/Reduced; trang 6-7 về Cross/latency/giới hạn; trang 9 về checklist.
- Report IEEE mới: Bảng I, VII, VIII, XII, XV, XVI và Appendix B.
- BODMAS: https://github.com/whyisyoung/BODMAS và https://whyisyoung.github.io/BODMAS/.
- Code đã đọc: `src/xsentinel/detection/components.py`, `src/xsentinel/detection/detector.py`, `src/xsentinel/service/scoring.py`, `src/xsentinel/service/api.py`, `src/xsentinel/storage/history.py`, `compose.yaml`.

## Nhật ký ghi chú

- 19/10/2026: tạo bản ghi theo yêu cầu người dùng. Chỉ ghi tài liệu và thêm đường dẫn từ handoff; không sửa code/model/ngưỡng hoặc chạy thí nghiệm. Người dùng chưa chốt các lựa chọn mới ở trên.
- 19/10/2026, sau đó: người dùng đã chọn hướng cho cả năm mục; chuyển trạng thái hiện hành sang `QUYET_DINH_5_DIEM_2026_10_19.md`. Auth tạm hoãn; fusion được phép khảo sát; BODMAS bổ sung tĩnh; latency chọn A+B và không chọn C.
