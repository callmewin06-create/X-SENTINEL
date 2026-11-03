# M8 preflight cho Kali/Linux

Gói này dùng Python 3.8+ và thư viện chuẩn, không cần pip, sudo, Wine hay PowerShell.
Script chỉ đọc file để tính SHA-256 và kiểm tra PE header. Không thực thi EXE, không
nhúng trigger, không kiểm chức năng Windows và không tính ASR/recall.

## Chạy

Giải nén ZIP, mở terminal tại thư mục vừa giải nén. Thay đường dẫn samples bằng thư mục
chứa các file PE gốc của nhóm. Thư mục output phải mới và nằm ngoài samples:

```bash
python3 self_test.py
python3 m8_preflight.py --samples "/home/kali/m8_samples" --output "/home/kali/m8_report_01"
```

self_test.py tạo các file header giả, không chạy executable. Báo lại nếu self-test lỗi.
Script đã được kiểm tra trên Windows và fixture PE thật bằng thao tác đọc tĩnh; chưa
được chạy trực tiếp trên Kali trong môi trường của người soạn. Self-test giúp kiểm tra
phần CLI, Unicode paths, header hỏng và symlink ngay trên máy Kali nhận bàn giao.

Không cần quyền root. Nếu output đã tồn tại, dùng tên mới để giữ nguyên lần audit trước.
Mặc định quét đệ quy EXE/DLL/SYS/SCR/OCX/CPL và file không có đuôi (tên SHA).
Không theo symlink, không giải nén archive. Dùng --all-files nếu cần kiểm cả đuôi khác.

## Gửi lại

- environment.json: hệ điều hành/Python và hash script.
- binary_inventory.csv: đường dẫn tương đối, size, SHA-256, machine, PE32/PE32+, CLR header và lỗi đọc.
- summary.json: số file, lỗi và thư mục không đọc được.

```bash
python3 -m zipfile -c M8_REPORT_KALI.zip /home/kali/m8_report_01
```

Gửi ZIP báo cáo, không gửi sample executable qua chat. Kiểm tra path/error text nếu có
thông tin riêng trước khi chia sẻ. Exit code 0: có PE đọc header được và không có lỗi quét;
code 2: cần xem lại, gồm trường hợp corpus rỗng, file hỏng hoặc thiếu quyền đọc.

PE_HEADER_OK không có nghĩa file benign, chạy được, giữ chức năng hay khớp trigger.
CLR header chưa đủ để kết luận assembly là x86-only hay AnyCPU. functional_status luôn
NOT_RUN. Kiểm chức năng Windows vẫn cần Windows VM và oracle riêng.

Gói chỉ chuẩn bị inventory đầu vào có provenance, chưa đủ để nghiệm thu M8.
