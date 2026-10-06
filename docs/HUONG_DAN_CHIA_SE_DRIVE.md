# Chia sẻ model và demo X-SENTINEL qua Google Drive

## Gói gửi cho nhóm

File: `outputs/share/X_SENTINEL_DEMO_EMBER2018_2026_10_06.zip`.

Gói có code chạy tương ứng với bản local ngày 06/10, năm model baseline hiện có trong `models/` và bundle dashboard EMBER2018 ở `outputs/pilot/seed_17/concentrated_0.01/bundle/`. Không kèm dataset đầy đủ, môi trường `.venv` hay các kết quả nghiên cứu khác. Reference trong bundle là phần dữ liệu nhỏ cần cho detector.

Đây là demo của thí nghiệm trước, dùng schema `ember-v2-2381-views-v1`. Gói chưa có model của protocol mới fit 200.000 mẫu và chưa có model EMBER2024. Các phương pháp có tên M5 trong bundle là proxy lịch sử; không phải kết quả M5 mới.

Code local chưa push GitHub, nên ZIP kèm bản code tương ứng để người nhận chạy trực tiếp. Gói không thay thế repository nghiên cứu đầy đủ. Khi chạy các lệnh dưới đây, đứng ở thư mục có `pyproject.toml` và `dashboard/`.

## 1. Bạn upload lên Drive

1. Mở https://drive.google.com và tạo thư mục `X-SENTINEL Models`.
2. Chọn **Mới → Tải tệp lên**, chọn ZIP trên. Upload thêm file cùng tên có đuôi `.zip.sha256` nếu muốn người nhận kiểm tra checksum toàn gói.
3. Đợi upload xong. Nhấp phải ZIP → **Chia sẻ**.
4. Chọn **Quyền truy cập chung → Bất kỳ ai có đường liên kết → Người xem** nếu muốn gửi link trực tiếp cho nhóm. Có thể giữ quyền truy cập hạn chế và cấp quyền Người xem theo email của từng bạn.
5. Giữ quyền tải xuống cho Người xem, chọn **Sao chép đường liên kết**, rồi gửi link cho nhóm.

Nguồn Google: [upload](https://support.google.com/drive/answer/2424368?hl=en), [chia sẻ](https://support.google.com/drive/answer/2494822?hl=en), [tải xuống](https://support.google.com/drive/answer/2423534?hl=en).

## 2. Bạn trong nhóm tải về và đặt ở đâu

1. Mở link Drive → **Tải xuống** ZIP.
2. Nhấp phải ZIP trong Windows → **Extract All / Giải nén tất cả**. Chọn thư mục đích, ví dụ `D:\Demo`.
3. Mở thư mục `X-SENTINEL` nằm bên trong phần đã giải nén. Nếu Windows tạo thêm lớp thư mục mang tên ZIP, đi vào lớp đó trước. Thư mục đúng phải có `pyproject.toml`, `src`, `dashboard`, `models` và `outputs`.
4. Có thể giữ nguyên gói ở đó và chạy theo mục 3. Nếu muốn dùng repo đã tải từ GitHub, dùng bản code tương ứng trong ZIP; không trộn các file bundle từ các đợt thí nghiệm khác nhau.

Cấu trúc sau giải nén:

```text
X-SENTINEL/
  pyproject.toml
  src/xsentinel/
  dashboard/app.py
  scripts/xsentinel.py
  docs/HUONG_DAN_CHIA_SE_DRIVE.md
  models/
    model_clean.txt
    model_backdoor_concentrated.txt
    model_backdoor_spread.txt
    model_backdoor_cross.txt
    model_backdoor_stress_metadata_24.txt
  outputs/pilot/seed_17/concentrated_0.01/bundle/
    bundle.json
    main.txt
    reference.npz
    view_structural.txt
    view_behavioral.txt
    view_metadata.txt
```

`models/` chứa model baseline để dùng trong công việc baseline. Dashboard nạp **thư mục bundle**, không nạp riêng năm model baseline này. `reference.npz` và `bundle.json` phải đi cùng đúng model trong bundle.

## 3. Cài và chạy trên Windows

Cài Python 3.11 hoặc 3.12. Mở PowerShell tại thư mục `X-SENTINEL` vừa giải nén. Chạy lần lượt:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install .
.venv/Scripts/python.exe -m streamlit run dashboard/app.py
```

Nếu máy dùng Python Launcher, có thể thay dòng đầu bằng `py -3.12 -m venv .venv` khi đã cài Python 3.12. Cài dependency cần Internet ở lần đầu; không cần cài Git hay Docker để chạy cách này.

Mở địa chỉ Streamlit hiện trong terminal, thường là `http://localhost:8501`. Trên sidebar:

- Dataset: **EMBER2018**.
- Detector bundle directory: `outputs/pilot/seed_17/concentrated_0.01/bundle`.
- Detector variant: **X_reduced** hoặc **X_full**.
- Input: **Example reference vector** để kiểm tra hệ thống nạp và chấm điểm được ngay.

Example lấy từ benign reference của bundle, dùng thử giao diện; không phải đánh giá độc lập. Demo này chạy được mà không tải toàn bộ EMBER2018. Chọn EMBER2024 sẽ hiện chưa sẵn sàng vì gói chưa có bundle V3.

## 4. Khi hiện Not ready

- Kiểm tra đang đứng ở thư mục có `pyproject.toml`, không ở thư mục cha của `X-SENTINEL`.
- Kiểm tra `outputs/pilot/seed_17/concentrated_0.01/bundle/bundle.json` tồn tại.
- Nếu giải nén vào repo khác, giữ đúng cấu trúc `models/` và `outputs/` ở gốc repo; không đặt ZIP hay các model vào `src/`.
- Nếu báo checksum mismatch, tải/giải nén lại nguyên bundle; không chỉnh tay file model, reference hoặc ngưỡng.
- Model EMBER2018 không dùng để chấm vector EMBER2024.

## 5. Kiểm tra checksum ZIP nếu cần

Người gửi upload file `.zip.sha256` cùng ZIP. Người nhận đọc giá trị trong file đó và so với lệnh:

```powershell
Get-FileHash -LiteralPath 'C:\Users\TEN_BAN\Downloads\X_SENTINEL_DEMO_EMBER2018_2026_10_06.zip' -Algorithm SHA256
```

Thay đường dẫn bằng vị trí ZIP thực tế. Dashboard tự kiểm tra checksum các file trong bundle khi nạp.
