"""Write a Vietnamese handoff and traceable response to the approved 15 choices."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
root=Path('outputs/revision_2026_10_13');out=Path('output/revision_2026_10_13')
s=json.loads((root/'summary.json').read_text(encoding='utf-8'))
tests=ET.parse(root/'tests.xml').getroot()[0].attrib
choices=[
('1 Giữ phương pháp trong code','Đã sửa Method theo M3 view mass, M4R gated Behavioral SHAP, M4F probability gap và fusion trung bình rank. Không đổi sang polarity conflict rồi gắn số cũ cho nó.','Báo cáo mục 3 và công thức Word'),
('2 Làm rõ PE only','Đã ghi sáu archive cụ thể, pin nguồn Hugging Face và code GitHub, bảng cả bảy role. PE theo tên archive khác với parse thành công is_pe=1.','Bảng nguồn mục 4 và current_audit.json'),
('3 Kiểm tra ảnh hưởng dữ liệu','Đã giữ nguyên model và làm bốn điều kiện: gốc, lọc final, lọc calibration, lọc cả hai. Không gọi đây là train lại trên dữ liệu đã lọc.','supplement/sensitivity.csv; mục 5 4'),
('4 Tách cross khỏi kết quả chính','Bảng chính dùng concentrated/spread; cross có bảng stress riêng. EMBER2024 restricted chỉ có ba run spread ở rate 2%. Tất cả 54 cấu hình còn trong phụ lục.','Mục 5 1, 5 2 và Appendix A'),
('5 Bỏ Behavioral bất biến','Imports/exports là dấu hiệu tĩnh, có thể bị sửa và không đại diện toàn bộ hành vi. Không thay lời bảo đảm cũ bằng một lời bảo đảm monotone khác chưa chứng minh.','Mục 3 2 và Discussion'),
('6 Khai báo tài nguyên full và shadow','Bảng nêu rõ full có clean view models học từ 200.000 fit sạch. Shadow dùng clean full model 500 rounds cùng fit, đặt ngưỡng từ calibration benign. Shadow thắng thì báo thật, không cấp ngầm cho reduced.','Bảng access, baselines và fresh scores'),
('7 Kiểm tra chiều STRIP bằng dữ liệu mới','Giữ STRIP gốc 1-H; thêm H với ngưỡng mới từ benign calibration. Có đồ thị entropy và đo trên 2.000 source IDs mới mỗi dataset, không tuning theo kết quả mới.','Mục 5 5; validation_results/fresh_summary.json'),
('8 Kiểm tra attacker biết cảnh báo','Đã khóa Structural-only, 100 mẫu malware/run, tối đa 32 queries, giữ trigger gốc, giá trị đề xuất từ benign selection. Bộ chạy đầu dùng whitelist có Metadata của V2 đã bị rút và không dùng làm bằng chứng.','adaptive_structural/protocol.json và adaptive_summary.json'),
('9 Giữ phụ thuộc khi tính độ chắc','Bootstrap 1.000 lượt theo source ID, giữ các lần xuất hiện của cùng ID cùng nhau. Khoảng này chỉ áp dụng cho models/cohort đã khóa, không suy rộng mọi seed.','analysis/cluster_intervals.json; mục 5 3'),
('10 Đặt tên đúng mẫu số và AUROC','Có all triggered, eligible, successful eligible và paired new evasion. Báo ba AUROC riêng và ASR trước/sau. Không nhân các cột trung bình để suy ra ASR sau.','analysis/cell_metrics.csv; bảng denominators'),
('11 Phân tích ablation trước khi đổi fusion','Đã xuất M3, M4R, M4F, XR, XF, TADR, STRIP; catch/miss theo từng run và tương quan rank. Giữ fusion đã khóa, không học trọng số từ final.','analysis/catch_miss.csv và rank_correlations.csv'),
('12 Bỏ bảo đảm FPR tương lai','Ngưỡng cho tối đa 20 exceedances strict trong calibration 2.000 mẫu. Final FPR đo riêng. Có chẩn đoán Beta-binomial tính bất định của ngưỡng, kèm giới hạn ties và giả định IID.','analysis/fpr_diagnostics.csv; mục 3 4 và 5 4'),
('13 Đo riêng từng phần thời gian','Đã đo classifier, core reduced/full, STRIP và suite reduced/full trên cùng 100 input/run. Nêu rõ warm, không gồm extraction/API/database. Mục tiêu 10 ms không bị biến thành bảo đảm.','supplement/latency.json; mục 5 7'),
('14 RQ3 và M5','M5 không có trong phương pháp đã kiểm chứng. Chuyển cơ chế này sang hướng tiếp theo; bản nghiên cứu dùng các câu hỏi đã có thí nghiệm. Rubric môn học vẫn cần thầy xác nhận nếu bắt buộc RQ cũ.','Mục 1 1, 3 5 và Conclusion'),
('15 Word references và artifact','Bản mới là DOCX theo yêu cầu mới nhất, có 58 references, công thức Word, caption và cross-reference tự động, hình tạo lại từ số. Gói kiểm chứng gồm code/model/scores/hashes/IDs; không công bố hay gửi ai.','X_SENTINEL_Report_Revised.docx; reproduction package')]
lines=['# Bàn giao bản sửa X SENTINEL','',
'Bản này thực hiện phương án đã được bạn duyệt. Báo cáo làm bằng Word, không chuyển sang LaTeX. Report 2.docx trong Downloads, models, thresholds và outputs/primary được giữ nguyên.','',
'## Điều cần hiểu trước khi trình bày','',
'Các số cũ không tự sai chỉ vì thầy phản biện. Lỗi lớn là công thức trong bài khác code, câu kết luận mạnh hơn bằng chứng và gộp các nhóm tấn công khác nhau. Bản mới sửa các điểm này bằng số đã đo.','',
'Shadow được cấp thêm model sạch nên không phải lựa chọn miễn phí cho mọi người dùng. Tuy nhiên, khi giả định full cho phép dữ liệu sạch, việc giấu kết quả shadow mạnh hơn sẽ làm bài mất độ tin cậy.','',
f'Kiểm thử: {tests["tests"]} tests; {tests["failures"]} failures; {tests["errors"]} errors. Nhánh file thật: một chương trình lành tự xây, ba bản sửa, bốn kiểm tra chức năng mỗi bản. V3 trích được vector đúng 2.568 cột và khớp xử lý raw của upstream; chưa chứng minh tấn công trên malware binary.','',
'## 15 quyết định đã triển khai','']
for name,action,evidence in choices:lines.extend(['### '+name,'',action,'','Bằng chứng: '+evidence+'.',''])
lines+=['## Phạm vi còn cần quyết định từ thầy hoặc tác giả','',
'- Thầy có cho điều chỉnh câu hỏi M5 đã đăng ký trong môn học hay vẫn yêu cầu làm thêm để chấm môn. Bản nghiên cứu không tuyên bố đã trả lời M5.',
'- Nếu thầy yêu cầu lọc cả fit rồi huấn luyện lại, đó là protocol mới; sensitivity hiện tại giữ weights cũ và không tự biến thành toàn bộ matrix train lại.',
'- Tấn công trên binary malware thật cần nguồn file được phép sử dụng và môi trường xác minh chức năng phù hợp. Prototype lành không thay bước đó.',
'- Người liên hệ, ORCID, đích nộp, quy tắc ẩn danh và công bố artifact chưa có thông tin để tự điền.',
'', 'Các mục trên không ngăn hoàn thành bản Word và kiểm chứng đã duyệt. Không có DOI, public release hoặc gửi thầy trong lần này.','',
'## Cách đọc file','',
'- Báo cáo: `X_SENTINEL_Report_Revised.docx` cùng thư mục này.',
'- Tóm tắt số học chính xác: `outputs/revision_2026_10_13/summary.json`.',
'- Mỗi thí nghiệm mới có protocol/code hash và cache riêng. Kết quả adaptive sơ bộ bị rút được đánh dấu rõ trong `validation_results/adaptive_preliminary_invalid.json`.',
'- Đồ thị và bảng được tạo từ scores đã lưu. Chạy lại bảng không đồng nghĩa huấn luyện lại từ raw.',
'']
(out/'Ban_giao_va_phan_hoi_gop_y.md').write_text('\n'.join(lines),encoding='utf-8')
manifest={'source_report':{'path':'C:/Users/win9tui/Downloads/Report 2.docx','sha256':hashlib.sha256(Path('C:/Users/win9tui/Downloads/Report 2.docx').read_bytes()).hexdigest()},
          'source_report_original_sha256':'3145ade00201f02e27df9eade36fe6ad65d3dd5ec4acf10629f783c8149a2035','tests':tests,
          'new_outputs':str(root),'format':'docx','published':False,'teacher_sent':False}
assert manifest['source_report']['sha256']==manifest['source_report_original_sha256']
(out/'verification.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Vietnamese feedback ledger completed')
