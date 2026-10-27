# Bàn giao phần BODMAS ngày 23 tháng 10 năm 2026

Đã hoàn thành phần tổng hợp từ `BODMAS_RESULTS.zip` theo yêu cầu dùng kết quả hiện có. Người phụ trách đã chạy trên VM; lượt này kiểm toán CSV/JSON và biên tập báo cáo, không chấm lại binary. Các khoảng trống nguồn/môi trường được giữ thành giới hạn, không coi là đã xác minh.

## Kết quả để trình bày

| Bộ model | Chế độ | Đã chọn | Chấm được | Lỗi | Gọi MALWARE | Gọi BENIGN | Cảnh báo trigger |
|---|---|---:|---:|---:|---:|---:|---:|
| EMBER2018 | Reduced | 200 | 175 | 25 | 162 | 13 | 2 |
| EMBER2018 | Full | 200 | 175 | 25 | 162 | 13 | 2 |
| EMBER2024 | Reduced | 200 | 175 | 25 | 175 | 0 | 0 |
| EMBER2024 | Full | 200 | 175 | 25 | 175 | 0 | 0 |

Đây là cùng 200 file qua bốn cấu hình. Có 175/200 = 87,5% file chấm được, 25/200 = 12,5% chưa có quyết định. Hai cảnh báo 2018 cùng thuộc hai file ở cả hai biến thể; cả hai file bị classifier gọi BENIGN. Chưa có nhãn trigger xác minh nên không gọi đây là hai backdoor đã phát hiện.

2018 gọi MALWARE cho 162/175 = 92,57% số chấm được; 2024 gọi MALWARE cho 175/175. Nhãn do người chạy khai báo. Không ghi “độ chính xác hệ thống 100%”; vẫn còn 25 file lỗi và không có bộ lành đại diện.

20 file pilot đã nằm trong 200 file chính. Smoke và benign là cùng một file lành. Không cộng thành 220 malware hay hai file lành.

## Đã thực hiện

- Kiểm tra CRC và checksum nội dung của 16 manifest; đối chiếu toàn bộ CSV với summary và manifest. Đối chiếu bundle ID, schema, method và ngưỡng với kit gốc.
- Tạo bảng bốn cấu hình, 800 bản ghi theo cấu hình, bảng ghép 200 hash, danh sách 25 lỗi duy nhất, các cảnh báo, file lành và thời gian. `main_records.csv` có 800 dòng vì mỗi file xuất hiện bốn lần, không có nghĩa là 800 file.
- Tạo `BODMAS_REPORT_SECTION_EN.md` và chèn Appendix C vào bản sao `output/bodmas_2026_10_23/X_SENTINEL_IEEE_1col_BODMAS_2026_10_23.docx`. Appendix C ở trang 19–20.
- Trong nội dung gốc chỉ đổi hai đoạn dẫn: phần mở đầu trước nói BODMAS chỉ là nền tảng tham khảo, và đoạn kết luận nay dẫn thêm Appendix C. Toàn bộ ảnh, style, công thức, bảng cũ, bibliography và các phần package khác giữ nguyên. File Word gốc không bị ghi đè.
- Kiểm tra cả 20 trang của bản Word bằng ảnh render từ PDF do Microsoft Word xuất đọc-only. Hai bảng mới không bị cắt; bảng thời gian giữ cùng trang. Renderer đóng gói thiếu LibreOffice trên Windows, nên dùng Word có sẵn và pypdfium2 để kiểm tra.
- Thử bốn trường hợp dữ liệu sai: tổng số chấm bị đổi, manifest bị sửa, ngưỡng bị đổi, file lỗi bị biến thành không cảnh báo. Công cụ từ chối cả bốn. 752 file và tập đường dẫn primary khớp snapshot hash đã giữ trước đó.
- Chuẩn bị hướng dẫn trình bày bằng kết quả lưu sẵn và bốn trường hợp minh họa theo hash. Không tạo hay gửi raw malware trong gói bàn giao.

## Các giới hạn đã đưa thẳng vào báo cáo

1. Tất cả 25 lỗi là `Invalid PE signature/header offset`, ở bước trước LIEF. Chưa xác minh nguyên nhân do disarming; không gán cảnh báo relocation trong log cho những file này.
2. `smoke.log` và `benign.log` ghi 0,169/0,748, khác CSV/JSON 0,044262/0,957886. Bảng dùng dữ liệu có cấu trúc đã đối chiếu; log gốc giữ nguyên và đánh dấu chưa giải thích được.
3. File lành `72524cf3...1e4485` khác byte fixture gốc `d5a4dc25...db9d23a`; chưa đối chiếu được source/build. Cả hai bản 2024 gọi file này MALWARE và không cảnh báo trigger. Chỉ một file không cho phép kết luận FPR.
4. Chưa xác minh đầy đủ model/code byte thực dùng trong VM, lệnh/container inspect, danh sách toàn bộ ứng viên và metadata nhãn gốc. ID model khớp chưa chứng minh mọi byte model ở VM khớp.
5. ZIP không có binary/vector để chấm lại độc lập; chưa kiểm tra trùng BODMAS với dữ liệu huấn luyện/calibration. Đây là kết quả tĩnh do thành viên bàn giao có kiểm toán nội bộ.
6. Timing thuộc đường suite có STRIP trên VM, không so trực tiếp với đường selected đã tối ưu trên Windows. Tính median/P95 từ 175 file thành công của từng lượt, không cộng P95 các pha.
7. Chưa chứng minh trigger vector hiện thực được trên PE, malware còn chức năng sau sửa, hay recall phát hiện backdoor trên binary.

Không có lượt mới trên 50 file lành, không train lại và không chọn ngưỡng bằng BODMAS. Những đề xuất mở rộng trong kế hoạch được giữ cho công việc sau; chúng không bị ghi thành kết quả đã làm.

## Nơi lưu và tái tạo

- Thành phẩm và hướng dẫn demo: `output/bodmas_2026_10_23/`.
- CSV, audit, bằng chứng bảo toàn và render QA: `outputs/bodmas_2026_10_23/`.
- Tổng hợp lại từ ZIP, không chạy model: `scripts/summarize_bodmas_results.py`.
- Tạo lại bản sao Word: `scripts/build_bodmas_report_2026_10_23.py`, cần python-docx và lxml. Bản đã bàn giao được tạo bằng runtime tài liệu đóng gói của Codex.
- Render Word đọc-only: `scripts/render_bodmas_report_2026_10_23.ps1`; raster QA: `scripts/render_bodmas_pages_2026_10_23.py`.

Không ghi database, không sửa model/ngưỡng, không commit/push trong lượt này. ZIP gốc có SHA-256 `c528ef4931a672123d47bfd30b6e0bdc5ceb4b18d2cf5a5d296f030dc31d8a87` và được giữ nguyên.
