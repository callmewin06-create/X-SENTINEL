# Quy Trình Tái Lập Thử Nghiệm: Kiểm Tra & Tái Lập Trigger Trên File PE (TASK 2 — Phúc)

Tài liệu này hướng dẫn chi tiết cách tái lập 100% các phép kiểm tra, trích xuất đặc trưng và chấm điểm mô hình đối với các biến thể PE nhị phân lành trong dự án X-SENTINEL.

---

## 1. Yêu Cầu Môi Trường & Phiên Bản Công Cụ

Thử nghiệm có thể chạy trên cả hai môi trường:
1. **Linux (Kali Linux Rolling / Ubuntu / Debian)**:
   - Python: `3.12` (hoặc chạy trong Docker container `xsentinel-test:3.12`)
   - MinGW-w64: `x86_64-w64-mingw32-gcc` (biên dịch mã nguồn Native C thành file PE Win64)
   - Wine: `wine` (chạy phép kiểm tra chức năng PE trên Linux)
   - Docker & Docker Compose: phục vụ môi trường cách ly chuẩn hóa
2. **Windows (Windows 10/11 x86_64)**:
   - Python: `3.12`
   - Thư viện cần thiết: `lightgbm==4.6.0`, `lief==0.16.6`, `pefile==2024.8.26`, `signify==0.7.1`, `numpy==1.26.4`, `scipy==1.17.1`, `scikit-learn==1.6.1`

---

## 2. Cấu Trúc Thư Mục

```text
experiments/phuc_pe_validation/
├── fixtures/
│   ├── src/
│   │   ├── native_benign_fixture.c    # Mã nguồn C thuần, hàm n^2 + 7, an toàn tuyệt đối
│   │   └── dotnet_benign_fixture.cs   # Mã nguồn C# .NET tương đương
│   ├── variants/                      # Thư mục chứa 10 biến thể PE sinh tự động
│   ├── native_benign_fixture.exe      # File PE Native C đã biên dịch
│   ├── dotnet_benign_fixture.exe      # File PE .NET đã biên dịch
│   └── BUILD.md                       # Hướng dẫn toolchain và lệnh build
├── scripts/
│   ├── build_variants.py              # Sinh 10 biến thể PE và tạo manifest.csv
│   ├── test_functionality.py          # Kiểm tra 4 test cases I/O trên Windows
│   ├── test_functionality_linux.py    # Kiểm tra 4 test cases I/O trên Linux Wine
│   ├── extract_and_diff.py            # Trích xuất vector V2/V3 và so sánh sai lệch
│   ├── score_variants.py              # Chấm điểm qua 24 bundle mô hình đóng băng
│   └── generate_feasibility_matrices.py # Tạo các ma trận khả thi của Severi và Trigger
└── tests/
    └── test_pe_validation.py          # Bộ kiểm thử tự động pytest cho suite này

outputs/phuc_pe_trigger_2026_10_27/
├── environment.json                   # Thông số hệ điều hành và công cụ thực tế
├── feasibility_2026-10-27.md          # Báo cáo đánh giá công cụ Severi và tính khả thi
├── severi_compatibility_matrix.csv    # Bảng đối chiếu Severi et al. vs X-SENTINEL
├── trigger_feasibility_matrix.csv     # Bảng khả thi từng đặc trưng trên binary PE
├── manifest.csv                       # Danh mục 10 biến thể kèm SHA256 và thông số PE
├── vectors/                           # File npy chứa vector đặc trưng 2381 và 2568 chiều
├── feature_changes.csv                # 1.333 dòng thay đổi đặc trưng chi tiết
├── feature_change_summary.csv         # Tổng hợp trôi dạt đặc trưng theo từng biến thể
├── functionality_results.csv          # Kết quả chạy chức năng trên Windows
├── functionality_results_linux.csv    # Kết quả chạy chức năng trên Linux Wine
├── xsentinel_scores.csv               # Kết quả chấm điểm 240 cặp biến thể x mô hình
├── evidence_index.md                  # Bản đồ đối chiếu khẳng định khoa học -> bằng chứng
├── results_summary.md                 # Báo cáo tổng kết nghiệm thu tiếng Việt
├── manuscript_paragraph_en.md         # Đoạn văn khoa học tiếng Anh bàn giao cho Quân
├── handover_for_quan_and_phu.md       # Biên bản bàn giao cho Quân, Phú, Thắng
└── remaining_work.md                  # Theo dõi các đầu mối công việc còn lại
```

---

## 3. Các Lệnh Thực Thi Tái Lập (Copy-Paste Commands)

### Bước 1: Biên dịch chương trình lành từ mã nguồn (Native C)
```bash
# Trên Linux (hoặc môi trường có mingw-w64)
x86_64-w64-mingw32-gcc -O2 -s -Wl,--build-id=none \
    experiments/phuc_pe_validation/fixtures/src/native_benign_fixture.c \
    -o experiments/phuc_pe_validation/fixtures/native_benign_fixture.exe
```

### Bước 2: Sinh 10 biến thể PE và tạo manifest
```bash
python experiments/phuc_pe_validation/scripts/build_variants.py
```
*Đầu ra*: Tạo 10 file `.exe` tại `experiments/phuc_pe_validation/fixtures/variants/` và file `outputs/phuc_pe_trigger_2026_10_27/manifest.csv`.

### Bước 3: Kiểm tra chức năng bảo toàn hành vi (4 Test Cases)
```bash
# Trên Windows:
python experiments/phuc_pe_validation/scripts/test_functionality.py

# Trên Linux (qua Wine):
python experiments/phuc_pe_validation/scripts/test_functionality_linux.py
```
*Đầu ra*: Ghi nhận kết quả thực thi vào `functionality_results.csv` và `functionality_results_linux.csv`.

### Bước 4: Trích xuất vector đặc trưng V2 (2.381 chiều) & V3 (2.568 chiều) và so sánh toàn bộ đặc trưng
```bash
python experiments/phuc_pe_validation/scripts/extract_and_diff.py
```
*Đầu ra*: Lưu các vector `.npy` vào `outputs/phuc_pe_trigger_2026_10_27/vectors/`, tạo `feature_changes.csv` và `feature_change_summary.csv`.

### Bước 5: Chấm điểm trên 24 bundle mô hình đóng băng thực tế
```bash
python experiments/phuc_pe_validation/scripts/score_variants.py
```
*Đầu ra*: Xuất kết quả 240 lượt chấm điểm vào `outputs/phuc_pe_trigger_2026_10_27/xsentinel_scores.csv`.

### Bước 6: Chạy kiểm thử tự động xác nhận toàn bộ quy trình
```bash
pytest experiments/phuc_pe_validation/tests/test_pe_validation.py -v
```

---

## 4. Các Giới Hạn Cần Lưu Ý
- **Không suy diễn sang Malware**: Kết quả bảo toàn chức năng trên chương trình lành nhỏ (tính $n^2 + 7$) không đồng nghĩa các kỹ thuật này có thể bảo toàn hành vi của mã độc phức tạp (vốn phụ thuộc vào chuỗi API và tính toàn vẹn chữ ký).
- **Phân biệt Alert và Classification**: Điểm phân loại mã độc của classifier ($p_{\text{main}}$) và cờ báo động backdoor của X-SENTINEL ($X_R > \tau_{XR}$) là hai đại lượng độc lập.
- **Không gian vector vs Không gian file**: Toàn bộ trigger backdoor trong nghiên cứu gốc và X-SENTINEL thuộc không gian vector; chưa có trigger problem-space khả thi nào được xác lập trên binary thực tế.
