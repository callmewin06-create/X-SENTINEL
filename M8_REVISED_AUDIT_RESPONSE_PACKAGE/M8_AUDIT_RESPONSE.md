# BÁO CÁO GIẢI TRÌNH & ĐỐI CHIẾU NGUỒN GỐC DỮ LIỆU ĐẦU VÀO (TASK M8)
## Response to Audit Inquiries regarding Problem-Space Real PE Binary Feasibility

- **Dự án**: X-SENTINEL: Cross-View Semantic Backdoor Detection in Malware Classifiers
- **Nhiệm vụ kiểm toán**: Task M8 — Problem-Space Real PE Watermark & Static Header Feasibility
- **Tác giả thực nghiệm M8**: Phạm Nguyễn Hoàng Phúc (PhucPNHSE203815)
- **Môi trường thực thi thực địa**: Kali GNU/Linux Rolling 2026.2 (`6.19.14+kali-amd64`), Hostname: `PhucPNHSE203815` (IP: `192.168.115.128`)
- **Tài liệu kiểm kê liên đới**: `m8_report_01` (`M8_REPORT_KALI.zip`, 22/22 PE_HEADER_OK), `BODMAS_16_PROVENANCE_MAPPING.csv`
- **Phiên bản build nghiệm thu mới**: `fixtures-build-20261103T151542Z-YVhvBv` (`COMPLETE_BUILD_ONLY`)
- **Thời gian cập nhật hiệu chỉnh**: 03/11/2026

---

## I. XÁC NHẬN NGUỒN GỐC VÀ TÌNH TRẠNG 16 MẪU MALWARE BODMAS

### 1. Nguồn gốc xuất xứ và mức độ chứng cứ (Provenance & Audit Scope)
- **Khai báo từ người bàn giao**: Toàn bộ 16 tệp PE malware được sử dụng trong đợt kiểm kê Task M8 được lấy từ bản phân phối **BODMAS Disarmed Malware Binaries** do nhóm tác giả Limin Yang et al. công bố tại *IEEE Deep Learning and Security Workshop (DLS 2021)*, tổ chức đồng thời cùng Hội nghị *IEEE Symposium on Security and Privacy (S&P 2021)* (nguồn chính thức: `https://github.com/whyisyoung/BODMAS`).
- **Kho lưu trữ tại chỗ (Local Archive)**:
  - Tệp nén gốc: `BODMAS_disarmed_malware_binaries.zip` lưu tại máy trạm thực địa `/home/phucpnhse203815/Downloads/` (kích thước vật lý 72,932,177,367 bytes ~ 67.92 GiB, gồm 57,293 tệp PE nằm trong thư mục `altered/`).
  - Nhật ký giải nén: Được 7-Zip ghi nhận tại `/home/phucpnhse203815/unzip.log`.
  - Trên máy ảo Kali Linux: Các tệp giải nén được lưu trữ tại `/home/phucpnhse203815/xsentinel-bodmas-work/samples/malware/altered/`.
- **Đối chiếu nội bộ từng tệp (Local CRC32 Verification)**:
  - Nhóm nghiên cứu đã thực hiện đối chiếu trực tiếp 16 tệp trong tập mẫu `m8_samples/malware/` với archive gốc bằng lệnh `7z l -slt BODMAS_disarmed_malware_binaries.zip altered/<hash>.exe`.
  - **Kết quả**: 16/16 tệp khớp chính xác 100% về kích thước tệp, timestamp lưu trữ (`2021-05-01 05:03:56`) và mã kiểm tra CRC32 lưu trong archive.
- **Phân định mức độ chứng cứ kiểm toán**: Do tệp archive có dung lượng quá lớn (68 GB) chưa thể chuyển giao toàn bộ qua gói audit, thông tin này được xếp vào diện **"nguồn do người bàn giao khai báo kèm chứng cứ đối chiếu tại chỗ"**; chưa ghi nhận là đã được bên thứ ba độc lập kiểm chứng nếu chưa trực tiếp nhận tệp archive gốc hoặc bản kiểm tra độc lập từ bên ngoài.

### 2. Đính chính thực nghiệm về cơ chế biến đổi Disarmed
Nhóm nghiên cứu xin đính chính nhận định trước đây (vốn suy đoán sai rằng EntryPoint bị triệt tiêu về 0) sau khi đã tiến hành đọc tĩnh trực tiếp từ raw PE header của 16 tệp đã khóa hash:
1. **Tên file**: Được tác giả dataset đặt theo mã SHA-256 gốc của mẫu mã độc trước khi disarm (`<original_sha256>.exe`).
2. **Triệt tiêu trường Machine trong COFF Header**: Trường `IMAGE_FILE_HEADER.Machine` (offset 4 sau chữ ký PE `PE\0\0`) được tác giả dataset gán về `0x0000` (thay vì `0x014C` cho x86 hay `0x8664` cho x64). Đây là cơ chế chính khiến hệ điều hành Windows và Wine từ chối nhận diện kiến trúc phần cứng và dừng nạp ngay từ tầng nạp PE, đồng thời giải thích tại sao công cụ kiểm kê `m8_preflight.py` ghi nhận `machine: 0x0000` và `architecture: UNKNOWN`.
3. **Trường AddressOfEntryPoint được giữ nguyên vẹn**: Kết quả đo đạc thực tế từ `IMAGE_OPTIONAL_HEADER.AddressOfEntryPoint` (offset 40 sau PE signature) cho thấy **cả 16 mẫu đều có EntryPoint khác 0** (ví dụ `0x0002800A`, `0x00001240`, `0x00002752`,...). Tác giả BODMAS **không triệt tiêu EntryPoint**, mà chỉ triệt tiêu `Machine = 0x0000`. Toàn bộ 16 giá trị hex đo đạc thực tế đã được cập nhật chuẩn xác vào `BODMAS_16_PROVENANCE_MAPPING.csv`.
4. **Đặc trưng tĩnh (Static Features) & Giới hạn khẳng định**: Cấu trúc Section Headers, Import Tables, Export Tables và dữ liệu raw bytes vẫn được bảo toàn để các công cụ phân tích tĩnh chuẩn như LIEF (v0.16.6) và `pefile` phân tích cú pháp thành công (`PE_HEADER_OK`). Tuy nhiên, do 2 bytes `Machine` đã bị thay đổi thành `0x0000`, phân bố Byte Histogram toàn file có sự thay đổi cục bộ nhỏ (tăng 2 bytes giá trị 0x00). Nhóm **không tuyên bố** Histogram và Shannon Entropy giữ nguyên vẹn 100% từng byte khi chưa có kết quả trích xuất đối chiếu vector đặc trưng trước/sau disarm trên cùng phiên bản extractor.

---

## II. BẢNG ĐỐI CHIẾU 16 MẪU: HASH GỐC → SHA-256 DISARMED → ENTRYPOINT & CRC32

Bảng dưới đây ánh xạ chi tiết 16 mẫu malware BODMAS với các thông số kỹ thuật được đo đạc và đối chiếu độc lập trên dữ liệu nhị phân thực địa:

| STT | Item ID | SHA-256 Gốc (Tên File) | SHA-256 Disarmed Thực Tế | Size (B) | PE Format | Machine | AddressOfEntryPoint (Đo thực tế) | Archive CRC32 | Đối chiếu Archive |
|:---:|---|---|---|---:|:---:|:---:|:---:|:---:|:---:|
| 1 | `06b4b945e6a84cde` | `06b4b945e6a84cde65a74ae8...` | `d2be79be19faeacbfc70fae3...` | 25,471,672 | PE32 | `0x0000` | `0x0002800A` | `6A501F9A` | KHỚP (MATCH) |
| 2 | `0c61a4b549f38c7e` | `0c61a4b549f38c7ec9691c3d...` | `764749738eaea69f6aceaacf...` | 541,730 | PE32 | `0x0000` | `0x00001240` | `C72DDE05` | KHỚP (MATCH) |
| 3 | `20a8d5c9dbeee39e` | `20a8d5c9dbeee39e18fec61f...` | `2e9f4f5f6917f310ed5f9703...` | 5,768,666 | PE32 | `0x0000` | `0x00002752` | `F4A58E85` | KHỚP (MATCH) |
| 4 | `337f503219643765` | `337f503219643765078392eb...` | `8bf0c4d6bac4a88f18ca91b5...` | 25,782 | PE32 | `0x0000` | `0x00002320` | `FDD2090F` | KHỚP (MATCH) |
| 5 | `4f10945ea8917a48` | `4f10945ea8917a482ff8cd3f...` | `2fe620ed0373e012a0797902...` | 1,037,712 | PE32 | `0x0000` | `0x000038FC` | `CD1ACC15` | KHỚP (MATCH) |
| 6 | `5a38ffeced48c5a7` | `5a38ffeced48c5a71c734c94...` | `1007cda10e3879c662f567a3...` | 419,616 | PE32 | `0x0000` | `0x00055001` | `B42D4067` | KHỚP (MATCH) |
| 7 | `8c6c328a0aed6776` | `8c6c328a0aed6776999a4c16...` | `979b481285885150d1745ad8...` | 882,074 | PE32 | `0x0000` | `0x00015BD6` | `374CE55F` | KHỚP (MATCH) |
| 8 | `ad12d2ebe15b63a2` | `ad12d2ebe15b63a24c4950ef...` | `99f5c0c4fa2ec325954ba338...` | 408,861 | PE32 | `0x0000` | `0x00019B00` | `B8451219` | KHỚP (MATCH) |
| 9 | `b089a47a0ba71b5a` | `b089a47a0ba71b5a9e9c7c9d...` | `89789b144600c682f00dcebf...` | 421,376 | PE32 | `0x0000` | `0x0001AC01` | `AB11BA1C` | KHỚP (MATCH) |
| 10 | `b32f2bc895c406d3` | `b32f2bc895c406d344e0206e...` | `b959697e93e2d9d965d22675...` | 14,368,037 | PE32 | `0x0000` | `0x00001000` | `8525F10B` | KHỚP (MATCH) |
| 11 | `b830ebd21ba90375` | `b830ebd21ba90375f08b56f2...` | `1073c2d6cfc58e927f3a27e9...` | 6,768,811 | PE32 | `0x0000` | `0x00030000` | `9DF5D846` | KHỚP (MATCH) |
| 12 | `ce7acc13335c1a87` | `ce7acc13335c1a87f1c00656...` | `9d42862d3b6dcc8a21f04653...` | 2,055,761 | PE32 | `0x0000` | `0x00003799` | `0C0462FC` | KHỚP (MATCH) |
| 13 | `d9e0d18c9667cdbb` | `d9e0d18c9667cdbba627ee27...` | `28140dad68f51aed43a0d8cc...` | 200,949 | PE32 | `0x0000` | `0x00021430` | `961A5A6B` | KHỚP (MATCH) |
| 14 | `e048fa97092138db` | `e048fa97092138db2301298d...` | `dc1130e2cabeb641d22bf20c...` | 260,803 | PE32 | `0x0000` | `0x000013C8` | `89C7D3B0` | KHỚP (MATCH) |
| 15 | `e1256b3c82c7e334` | `e1256b3c82c7e3348e9b755b...` | `cc49f8d74d35bb5b652a7033...` | 46,108 | PE32 | `0x0000` | `0x00001AB1` | `A3EC21CE` | KHỚP (MATCH) |
| 16 | `f3332db58ac55dc6` | `f3332db58ac55dc615185571...` | `de49156b36159e8cd8261778...` | 66,971 | PE32 | `0x0000` | `0x00017310` | `DA1000FF` | KHỚP (MATCH) |

*(Dữ liệu đầy đủ kèm full hash được lưu tại `BODMAS_16_PROVENANCE_MAPPING.csv`).*

---

## III. MÃ NGUỒN VÀ QUY TRÌNH BIÊN DỊCH FIXTURE LÀNH TÍNH

Hai tệp fixture lành tính do nhóm tự phát triển làm chuẩn kiểm soát tính toán số học xác định $f(n) = n^2 + 7$, hoàn toàn không can thiệp tệp tin, mạng hay quyền quản trị. Mã nguồn C và C# được giữ nguyên vẹn từng byte dữ liệu.

### 1. Phân định lịch sử hash nhị phân và nguyên tắc truy vết
Nhóm nghiên cứu ghi nhận rõ tính biến thiên của mã băm (SHA-256) qua các môi trường và phiên bản biên dịch:
- **Bản binary cũ (27/10/2026)**: `native_original.exe` mang hash `d8f8741fa1b0a0c7364137501e93b6161a50a78d5e32fc5a28b9d1ca749954f5` (được dùng trong file `functionality_results.csv` cũ trên Windows).
- **Bản binary preflight M8 (28/10/2026)**: `native_original.exe` mang hash `1c7b297387433f8237effba502fb9c5bc1eae80bf42151da4ea45bc271023689` (trong `m8_samples/benign`).
- **Bản binary mới nghiệm thu độc lập (03/11/2026)**: Được biên dịch bằng builder gia cố `fixtures_src/build_fixtures.sh` trên máy chủ Kali Linux thực địa (`PhucPNHSE203815`), tạo thư mục cách ly `fixtures-build-20261103T151542Z-YVhvBv`:
  - `native_original.exe`: SHA-256 `fad8537b5080ab8f2dafda8b1cca4d435070ec900598c28a18b6c882c7bd96eb` (43,520 bytes)
  - `ReviewedBenignFixture.exe`: SHA-256 `eae43234c30b26578ed8efdc73df0845d060c74f78d23d6f1ac0f2976ee70f3d` (3,072 bytes)
  - Trạng thái biên dịch: `COMPLETE_BUILD_ONLY` (Ghi nhận biên dịch thành công, không tự động kích hoạt PE).
- **Nguyên tắc kiểm toán**: Tuyệt đối không hoán đổi, gán ghép hay chuyển giao kết quả PASS của các binary cũ sang binary mới. Mọi đánh giá chức năng phải gắn chặt với đúng mã SHA-256 của từng tệp thực tế.

### 2. Thông tin mã nguồn & Compiler Toolchain
- **Managed .NET Fixture (`fixtures_src/ReviewedBenignFixture.cs`)**:
  - Mã nguồn: Tính toán $f(n) = n^2 + 7$, trả về exit code 2 khi chuỗi nhập không phải số nguyên.
  - Trình biên dịch: Mono C# Compiler `mcs` (v6.14.1.0) trên Linux (`/usr/bin/mcs`) hoặc Roslyn `csc` trên Windows.
  - Lệnh biên dịch chuẩn: `mcs -target:exe -platform:x86 -optimize+ -out:ReviewedBenignFixture.exe ReviewedBenignFixture.cs`
- **Native C Fixture (`fixtures_src/native_benign_fixture.c`)**:
  - Mã nguồn: Sử dụng `strtoll` phân tích cú pháp số nguyên, in stdout và trả về exit code 2 nếu có ký tự lạ.
  - Trình biên dịch: MinGW-w64 GCC (`x86_64-w64-mingw32-gcc` v15-win32 trên Kali Linux).
  - Lệnh biên dịch chuẩn: `x86_64-w64-mingw32-gcc -O2 -s -Wl,--build-id=none native_benign_fixture.c -o native_original.exe`

---

## IV. BẰNG CHỨNG KIỂM THỬ CHỨC NĂNG CHO BẢN BUILD MỚI (BOUNDED INPUT DOMAIN)

Thực hiện theo chỉ dẫn của người kiểm toán, nhóm đã tiến hành kiểm chứng chức năng độc lập cho đúng mã SHA-256 của bản build mới (`fad8537b...` và `eae43234...`) trên miền đầu vào số học giới hạn đã xác định trước ($n \in \{0, 5, -3, 12, \text{"abc"}\}$):

### 1. Kết quả kiểm thử trên Windows 11 Native (`functionality_validation_new_build.csv`)
- **Native (`native_original.exe` - `fad8537b...`)**:
  - TC1 (không tham số): Exit 0, stdout `X_SENTINEL_BENIGN_FIXTURE:7` $\rightarrow$ **PASS**
  - TC2 ($n=5$): Exit 0, stdout `X_SENTINEL_BENIGN_FIXTURE:32` $\rightarrow$ **PASS**
  - TC3 ($n=-3$): Exit 0, stdout `X_SENTINEL_BENIGN_FIXTURE:16` $\rightarrow$ **PASS**
  - TC4 ($n=12$): Exit 0, stdout `X_SENTINEL_BENIGN_FIXTURE:151` $\rightarrow$ **PASS**
  - TC5 ($n=\text{"abc"}$): Exit 2, stderr `Error: Invalid integer input 'abc'` $\rightarrow$ **PASS**
- **Managed .NET (`ReviewedBenignFixture.exe` - `eae43234...`)**:
  - TC1..TC4: Đúng kết quả số học, Exit 0 $\rightarrow$ **PASS**
  - TC5 ($n=\text{"abc"}$): Exit 2 $\rightarrow$ **PASS**
- **Tổng kết trên Windows Native**: **10/10 PASS**.

### 2. Kết quả kiểm thử trên Kali Linux (`Wine 10.0` & `Mono Runtime 6.14`)
- **Native (`native_original.exe`) trên Wine 10.0**: 5/5 **PASS** (hoạt động hoàn hảo dưới hệ thống tương thích PE của Wine).
- **Managed .NET (`ReviewedBenignFixture.exe`) trên Wine 10.0**: Trả về Exit Code 255 (**FAIL**) do môi trường Wine mặc định trên Kali chưa cài gói `wine-mono` để nạp CIL assembly.
- **Managed .NET (`ReviewedBenignFixture.exe`) trên Mono Runtime 6.14.1**: 5/5 **PASS** (chạy trực tiếp qua máy ảo Mono CIL chuẩn).
- **Ý nghĩa kiểm toán**: Kết quả thực nghiệm giải thích rõ ràng tại sao không thể tuyên bố "100% PASS trên Wine" khi chưa chỉ định rõ ràng phiên bản runtime; đồng thời minh chứng tính trung thực tuyệt đối của báo cáo (Anti-Hallucination Contract).

---

## V. GHI NHẬN & CAM KẾT VỀ PHẠM VI NGHIỆM THU KIỂM TOÁN M8

Nhóm nghiên cứu cam kết áp dụng đầy đủ đoạn tuyên bố chuẩn hóa sau đây vào toàn bộ hồ sơ nghiệm thu Task M8:

> **Tuyên bố Phạm vi & Giới hạn Nghiệm thu M8**:  
> Người bàn giao xác nhận 16 file được lấy từ bản phân phối BODMAS disarmed. Bảng ánh xạ ID mẫu gốc sang SHA256 của bytes hiện tại đã được đối chiếu với inventory: 16/16 dòng khớp hash, kích thước, Machine và PE format; 16 ID gốc xuất hiện trong metadata BODMAS; 16/16 tệp khớp mã kiểm tra CRC32 trực tiếp với tệp nén gốc tại chỗ. Gói hiện tại đã bổ sung kết quả probe đọc tĩnh PE header trực tiếp (chứng minh Machine = 0x0000 trong khi AddressOfEntryPoint vẫn được bảo lưu) và thư mục build nghiệm thu mới (`COMPLETE_BUILD_ONLY`) kèm kiểm chứng chức năng có log cho đúng bản build mới trên môi trường kiểm soát.  
> Tuy nhiên, kết quả này thuần túy được sử dụng làm **Hồ sơ Nguồn mẫu và Kiểm kê Tĩnh (Input Provenance & Static Inventory)**; **TUYỆT ĐỐI CHƯA ĐƯỢC DÙNG** để kết luận malware nguyên bản hoạt động trước/sau disarm, trigger được hiện thực đầy đủ hay detector recall trong problem space. Việc hai fixture lành tính thực thi thành công chỉ chứng minh tính toán số học trên fixture, không thay thế bằng chứng chức năng của malware. Task M8 tiếp tục duy trì giới hạn kiểm toán cho đến khi toàn bộ learned trigger được trích xuất lại đặc trưng và đánh giá đầy đủ trên đúng cohort nghiên cứu.

---
*Báo cáo giải trình đã được hiệu chỉnh và chuẩn hóa đồng bộ phục vụ công tác nghiệm thu Task M8 — Dự án X-SENTINEL.*
