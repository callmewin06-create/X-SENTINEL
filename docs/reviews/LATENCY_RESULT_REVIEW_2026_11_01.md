# Kiểm tra result.zip — kết quả latency Phúc gửi

Ngày: 01/11/2026. Checkout: `af777f3`. Đây là bổ sung cho audit ngày31/10: trước đây chưa có artifact latency ở checkout, nay đã có kết quả trong ZIP. Chưa sửa code hoặc chạy benchmark mới.

## Phạm vi gói nhận được

`result.zip` chứa ba file dữ liệu (ngoài entry thư mục):

SHA256 của ZIP: `90c3e3895e185a178de81e0a9d65daf68d0968d8264f288a9a08ecbbcc8e372d`.

- `result/benchmark_latency.json`
- `result/benchmark_latency.csv`
- `result/benchmark_latency_iterations.csv`

Không có script Python đã sửa, file model, fixture, thông tin CPU/RAM/OS/VM/thread count, phiên bản thư viện, hash code/model/fixture hoặc kết quả Public-Shadow/BODMAS/M8/M5/Docker trong gói này. Vì vậy việc bổ sung ZIP chỉ thay đổi trạng thái bằng chứng của phần latency, không đóng các mục audit khác.

## Kiểm tra số liệu

- ZIP CRC hợp lệ.
- Raw CSV có500 dòng =5 file khác nhau ×100 lần lặp/file; iteration IDs đầy đủ1–100, không thiếu giá trị hoặc thời gian không dương.
- Tính lại mean, std(ddof=0), median, p95, p99, min, max từ raw CSV khớp JSON; sai lệch lớn nhất khoảng1,42e-14ms do float.
- Summary CSV20 dòng khớp JSON và kích thước file đã ghi.

| File | Bytes | End-to-end mean ± SD (ms) |
|---|---:|---:|
| dotnet_original.exe | 4096 | 40,54 ±0,44 |
| native_original.exe | 43520 | 41,28 ±6,12 |
| cmd.exe | 339968 | 62,61 ±0,96 |
| notepad.exe | 360448 | 63,66 ±0,66 |
| curl.exe | 818512 | 97,82 ±1,15 |

Đây là5 file với100 lần đo lặp mỗi file, không phải500 file độc lập. Số liệu tổng hợp nhất quán nội bộ; audit arithmetic không chứng minh cách instrument pipeline hoặc nguồn thực thi.

## Chưa đủ để xác nhận hết lỗi đo

### 1. Chưa có source sửa double-SHAP

Metadata ZIP ghi `Fixed: Zero TreeSHAP duplicate computation`, nhưng đây là mô tả do người xuất file cung cấp. ZIP không kèm script để kiểm tra.

Ở checkout hiện tại, `scripts/benchmark_latency.py:107-108` vẫn gọi `pred_contrib=True` rồi `scorer.score()`. `CoreScorer._raw()` bên trong scorer còn tính TreeSHAP. Có thể Phúc đã sửa trên máy ảo nhưng chưa đưa source về project; không suy ra lỗi vẫn còn trong code mới chưa nhận được.

### 2. Native có chênh lệch lớn giữa stage means và total

Native stage means:

- Extraction12,137472ms.
- SHAP/inference18,836265ms.
- Rank/fusion0,714924ms.
- Tổng ba stage31,688661ms, trong khi end-to-end41,283968ms: chênh9,595307ms.

Nếu stage và end-to-end được đo trong các vòng lặp độc lập, các trung bình có thể khác vì môi trường đo thay đổi. Số chênh này tự nó không chứng minh double-SHAP hoặc số liệu sai. Tuy nhiên chưa được gọi chúng là phân rã không chồng lấp của cùng một lượt xử lý nếu chưa kiểm code/timer.

Raw native cũng cho thấy SHAP mean thay đổi theo nhóm lượt1–20 khoảng29,43ms, lượt41–100 khoảng13,7–13,9ms; cần giải thích cách warm-up/thứ tự đo/config threads và ghi trạng thái môi trường. Không kết luận nguyên nhân cụ thể từ CSV.

### 3. Câu manuscript vượt phạm vi bằng chứng

Câu trong JSON viết scoring latency "strictly bounded" và extraction "scales linearly with section complexity". Năm file này không đủ chứng minh hai khẳng định đó; chưa có phép đo section complexity hoặc thiết kế thí nghiệm kiểm quan hệ tuyến tính. Chưa đo gateway/API/load/concurrency. Không tự chuyển ms/file thành throughput vận hành thực tế.

## Trạng thái nghiệm thu P4

**Đã nhận và kiểm tra được dữ liệu latency mới. Chưa xác nhận source đã sửa đúng double-SHAP và cách chia timer.** Kết quả mới không còn chỉ là số trong handoff, nhưng chưa đủ đóng hoàn toàn P4.

Cần Phúc bổ sung:

1. Script benchmark đã sửa và các helper thay đổi, kèm hash/commit nếu có.
2. Cho biết stage/total được đo cùng lượt hay các loop độc lập; mỗi lượt end-to-end tính SHAP đúng một lần và tái dùng outputs đã tính.
3. Thông tin máy/VM/threads/library versions, model/bundle và fixture hashes; scope bao gồm những bước nào.
4. Sửa câu manuscript theo số đo quan sát, bỏ các khẳng định bounded/linear/gateway chưa được kiểm chứng.

Câu mô tả dữ liệu tạm thời, chỉ dùng sau khi xác minh code và cấu hình: “Across five PE files ranging from4.1 to818.5kB, with100 repeated measurements per file, the measured mean pipeline latency ranged from40.5 to97.8ms per file on the benchmark host.” Cần bổ sung cấu hình host và scope pipeline vào paper; đây không phải kết luận tổng quát về mọi PE.

Không sửa thuật toán, không thay ngưỡng, không chạy executable trong lượt kiểm tra này.

## Bổ sung sau khi kiểm tra các nhánh Git vừa tải về

Đã tìm thấy `origin/fix/p4-latency-benchmark` tại commit `5124cbf`. Nhánh `main` của workspace vẫn ở `af777f3`; bản sửa đã có dưới dạng remote-tracking branch nhưng chưa được đưa vào main. Không checkout/merge trong lượt kiểm tra.

### Cập nhật kết luận về source

**Đã xác nhận lỗi double-SHAP được sửa trong source của5124cbf:**

- Stage3 truyền `phi,p,pb` tính sẵn vào `scorer.score()`.
- Helper `_raw()` chỉ tính những thành phần chưa được cung cấp.
- End-to-end gọi `extract_pe()` rồi `scorer.score()` một lần, không có lệnh tính SHAP thừa bên ngoài.
- Không kiểm chứng bằng việc chạy100 vòng benchmark hoặc chạy executable: nạp helper từ Git vào bộ nhớ và dùng7 vector reference của model frozen để kiểm tra. Default scoring gọi contributions1 lần/batch; supplied-input scoring gọi0 lần. Điểm số default, supplied-input và helper cũ khớp hoàn toàn trong kiểm tra này (max absolute difference0).

Như vậy nhận xét trước “chưa có source để kiểm tra” đã được bổ sung bằng source của nhánh mới. Kết quả ZIP có cùng schema/fixtures/câu manuscript với script mới; thiếu hash execution nên chưa thể chứng nhận tuyệt đối ZIP được sinh bởi đúng commit đó.

### Các điểm còn phải sửa trong mô tả benchmark

- Stage1,2,3,total chạy ở4 loop độc lập. Cột cùng iteration trong CSV không phải các khoảng timer ghép trong cùng một lượt pipeline; đây giải thích khả năng chênh tổng stage và total, không phải bằng chứng double-SHAP còn tồn tại.
- `docs/BENCHMARK_LATENCY_REPORT.md` trên nhánh mới ghi sai lệch cộng dồn<0,5ms. Số liệu thực: native9,595ms, curl1,249ms, cmd0,550ms (absolute gaps).
- Câu “partitioned into” và quan hệ cộng gần chính xác cần đổi để nói rõ các phép đo stage độc lập.
- Bỏ khẳng định latency “cố định tuyệt đối/strictly bounded”, và “linear with section complexity” khi chưa có thiết kế đo hỗ trợ. Native SHAP mean18,84±7,18ms cũng không phù hợp tuyên bố tất cả file đều~29ms.
- Script chỉ warm-up fixture đầu tiên; chưa lưu thông tin host/VM/library/thread/hash model và fixture. Cần bổ sung để kết quả có thể tái lập và mô tả scope đúng.

**Trạng thái mới: lỗi tính SHAP trùng đã được xác minh sửa trên nhánh5124cbf; main chưa áp dụng nhánh đó. Dữ liệu latency nhất quán nội bộ. P4 còn phần mô tả thống kê/provenance cần hoàn thiện trước khi đưa nguyên văn vào paper.**
