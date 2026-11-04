# M8 — kiểm chức năng trước/sau cho C2 trên fixture lành tính

## Mục đích và trạng thái

Gói chứa đúng hai fixture số học đã được bàn giao, mỗi fixture có bốn bản: `original`, `timestamp_only`, `sections_only`, `full_c2`. Không chứa mẫu malware. Không cần build lại.

Hai bản full C2 đã khớp đủ target sau khi trích xuất lại bằng adapter của project:

- `section.num_read_and_execute_sections = 12`.
- `header.coff.timestamp = 1053454528`.

Record nguồn là V2/EMBER2018/seed17/concentrated_structural/rate0.02; file `attack_record.json` và fingerprint nằm trong manifest. Các bản chỉ sửa một yếu tố phục vụ đối chứng. Không sửa frozen attack/model hoặc số liệu primary.

Đã kiểm giữ nguyên nội dung, RVA, virtual size và flags của mọi section gốc, cùng entrypoint RVA. Những kiểm tra này chưa chứng minh chương trình chạy đúng. LIEF có cảnh báo `Can't read the padding` trong quá trình đọc/build; cảnh báo được ghi nhận, không chuyển thành PASS chức năng. Adapter dùng LIEF 0.16.6, chưa kiểm tương đương vector trên cùng binary với legacy LIEF 0.9. Không dùng gói này để tuyên bố malware giữ chức năng hoặc báo ASR/recall.

## Chạy trên Kali VM

Giải nén gói, mở terminal trong thư mục `M8_C2_FIXTURE_PROBE` có README này. Dùng Kali VM đã có Wine/Mono; hai lệnh sau sẽ thực thi các fixture số học trong gói. Không chạy trên Windows host đang làm việc.

```bash
python3 run_functionality.py --runtime wine --output c2_wine_results --ack-controlled-vm
python3 run_functionality.py --runtime mono --output c2_mono_results --ack-controlled-vm
```

- Lệnh Wine kiểm native: bốn bản × năm ca = 20 ca.
- Lệnh Mono kiểm managed .NET: bốn bản × năm ca = 20 ca.
- Không lấy kết quả Mono thay cho kết quả Wine/.NET. Gói này không chạy managed bằng Wine vì cấu hình Wine trước đã báo 5/5 FAIL; kết luận managed ở đây phải ghi runtime Mono.
- Trường hợp môi trường Windows VM riêng đã chuẩn bị, có thể chạy `python run_functionality.py --runtime windows --output c2_windows_results --ack-controlled-vm` để kiểm cả hai fixture, 40 ca. Đây là tùy chọn, không bắt buộc để gửi kết quả Kali.

`--ack-controlled-vm` ghi nhận người chạy đã chọn môi trường lab; script không tự xác minh bạn đang ở VM. Runner chỉ cho chạy các bytes được khóa hash trong gói này, không nhận corpus/file tùy ý.

Nếu thư mục kết quả đã tồn tại, dùng một tên mới. Nếu thiếu runtime, có FAIL, timeout hoặc chương trình bị policy chặn, giữ nguyên log và gửi lại. Không tắt chính sách bảo vệ để biến kết quả thành PASS.

## Gửi lại

Nén nguyên hai thư mục `c2_wine_results` và `c2_mono_results`, gửi lại. Mỗi thư mục có:

- `environment.json`: runtime/version, hệ điều hành, hash runner/manifest.
- `execution.json`: lệnh, thời điểm, thời gian và kết quả từng ca.
- `raw/`: stdout/stderr nguyên bytes của từng ca.
- `functionality.csv`: 20 dòng kết quả.
- `summary.json`: tổng trạng thái và kiểm tra cặp trước/sau.

Oracle giới hạn: không đối số → 7; `5` → 32; `-3` → 16; `12` → 151; `abc` → exit 2. Các ca hợp lệ exit 0. Runner so stdout sau khi bỏ whitespace đầu/cuối, vẫn lưu bytes gốc; lỗi đầu vào native còn phải có thông báo stderr dự kiến. Chỉ ghi `bounded_function_preserved` nếu cả năm ca gốc lẫn năm ca bản sửa đều PASS trong cùng runtime. Chưa chạy thì giữ `NOT_RUN`; thiếu runtime là `BLOCKED_ENV`.

## Bằng chứng chuẩn bị gói

- `manifest.json`: hash mọi binary, target đầy đủ, kiểm section gốc/entrypoint và các đặc trưng khác bị thay đổi.
- `target_verification.json`: đọc lại bytes độc lập qua entry point kiểm target đã buộc đủ toàn bộ trigger. Chỉ hai full C2 được báo `COMPLETE_TARGET_MATCH`; đây là trạng thái tĩnh.
- `prepare_c2_fixture_probe.py`: source tạo bản sửa, chỉ chấp nhận hai hash fixture đã biết. Để tái tạo cần repo/dependencies tương ứng; không cần chạy script này để kiểm chức năng.
- `VALIDATION.json`: kết quả kiểm tra chuẩn bị; không phải kết quả thực thi PE.
- `SHA256SUMS.txt`: kiểm tra gói bằng `sha256sum -c SHA256SUMS.txt` trước khi chạy.

Giới hạn: chỉ hai fixture lành tính với miền đầu vào nhỏ. Sau khi có kết quả trước/sau, M8 vẫn cần thiết kế và đánh giá backdoor trên cohort phù hợp cùng extractor/model/controls thống nhất. Không suy recall từ số ca số học PASS.

API dùng để build section: [LIEF PE documentation](https://lief.re/doc/latest/formats/pe/python.html); code đã kiểm theo API LIEF 0.16.6 cài trong project, không giả định API mới nhất giống hệt.
