# BÁO CÁO GIẢI TRÌNH & XÁC THỰC NGUỒN GỐC DỮ LIỆU ĐẦU VÀO (TASK M8)
## Response to Audit Inquiries regarding Problem-Space Real PE Binary Feasibility

- **Dự án**: X-SENTINEL: Cross-View Semantic Backdoor Detection in Malware Classifiers
- **Nhiệm vụ kiểm toán**: Task M8 — Problem-Space Real PE Watermark & Static Header Feasibility
- **Tác giả thực nghiệm M8**: Phạm Nguyễn Hoàng Phúc (PhucPNHSE203815)
- **Môi trường thực thi thực địa**: Kali GNU/Linux Rolling 2026.2 (`6.19.14+kali-amd64`), Hostname: `PhucPNHSE203815` (IP: `192.168.115.128`)
- **Tài liệu kiểm kê liên đới**: `m8_report_01` (`M8_REPORT_KALI.zip`), `manifest.csv`, `BODMAS_16_PROVENANCE_MAPPING.csv`
- **Thời gian lập**: 03/11/2026

---

## I. XÁC NHẬN NGUỒN GỐC VÀ TÌNH TRẠNG 16 FILE MALWARE BODMAS

### 1. Xác nhận tình trạng Disarmed
- **Khẳng định**: Toàn bộ 16 tệp PE malware được sử dụng trong đợt kiểm kê `m8_preflight.py` **100% là bản BODMAS Disarmed nguyên bản**.
- **Nguồn gốc xuất xứ**:
  - Tệp được trích xuất trực tiếp từ kho nén chuẩn `BODMAS_disarmed_malware_binaries.zip` (dung lượng nén 67.9 GiB / 72.9 GB, gồm 57,293 tệp PE do nhóm tác giả bộ dữ liệu BODMAS — *Yang et al., IEEE S&P / arXiv 2021* phân phối chính thức).
  - Thư mục lưu trữ nguyên bản trong archive: `altered/`.
  - Trên máy ảo Kali Linux: Đặt tại `/home/phucpnhse203815/xsentinel-bodmas-work/samples/malware/altered/`.
- **Về việc can thiệp từ phía nhóm nghiên cứu**:
  - **Nhóm nghiên cứu hoàn toàn KHÔNG qua bất kỳ chỉnh sửa nào**.
  - Các tệp được giải nén trực tiếp bằng 7-Zip (`unzip.log`), giữ nguyên vẹn 100% từng byte dữ liệu, kích thước tệp và timestamp gốc lưu trữ từ ngày `2021-05-01 05:03:56`.

### 2. Cơ chế biến đổi Disarmed (Do chính tác giả bộ dữ liệu BODMAS thực hiện)
Nhóm tác giả BODMAS công bố cơ chế vô hiệu hóa an toàn nhằm phục vụ cộng đồng nghiên cứu trích xuất đặc trưng tĩnh (Static Analysis) mà không gây rủi ro lây nhiễm:
1. **Tên file chính là SHA-256 gốc của malware trước khi disarm**: Mỗi file được đặt tên theo định dạng `<original_sha256>.exe`.
2. **Triệt tiêu trường Machine trong COFF Header**: Trường `IMAGE_FILE_HEADER.Machine` (offset 4 sau chữ ký PE) được gán cố định về `0x0000` (thay vì `0x014C` cho x86 hay `0x8664` cho x64). Đây là lý do công cụ `m8_preflight.py` ghi nhận trường `machine: 0x0000` và `architecture: UNKNOWN`.
3. **Triệt tiêu Entry Point trong Optional Header**: Trường `IMAGE_OPTIONAL_HEADER.AddressOfEntryPoint` được gán về `0x00000000` nhằm ngăn chặn hệ điều hành Windows hoặc Wine nạp và thực thi mã nhị phân.
4. **Bảo toàn dữ liệu phân tích tĩnh**: Toàn bộ cấu trúc Section Headers, Import Tables, Export Tables, Raw Data, Byte Histogram và Shannon Entropy được giữ nguyên vẹn, tương thích hoàn toàn với các bộ trích xuất đặc trưng chuẩn như LIEF (v0.16.6) và pefile.

---

## II. BẢNG ĐỐI CHIẾU 16 MẪU: HASH GỐC (TÊN FILE) → SHA-256 THỰC HIỆN TẠI

Bảng dưới đây ánh xạ chi tiết 16 mẫu malware được bốc thăm ngẫu nhiên có kiểm soát từ tập BODMAS sang mã SHA-256 thực tế của nhị phân disarmed hiện có trên hệ thống:

| STT | Item ID | SHA-256 Gốc (Trước Disarm / Tên File) | SHA-256 Byte Thực Tế (BODMAS Disarmed) | Dung lượng (bytes) | PE Format | Machine |
|:---:|---|---|---|---:|:---:|:---:|
| 1 | `20a8d5c9dbeee39e` | `20a8d5c9dbeee39e18fec61f9a574258adaffc2628bfc509fa22716961e9a700` | `2e9f4f5f6917f310ed5f97037c15abafe5b563d221ff827e9d09017bfa84a201` | 5,768,666 | PE32 | `0x0000` |
| 2 | `8c6c328a0aed6776` | `8c6c328a0aed6776999a4c169fdca092fb34a79dc8cb92924a1ec349f0de11d3` | `979b481285885150d1745ad8ec9febcaf934c502b7fcb19bf814e3282334785c` | 882,074 | PE32 | `0x0000` |
| 3 | `337f503219643765` | `337f503219643765078392eb686151454485f2aca658724dbb0632f16fdb78d6` | `8bf0c4d6bac4a88f18ca91b512eec98df3a06081d7681cbfd01c3fe0d20abbae` | 25,782 | PE32 | `0x0000` |
| 4 | `ce7acc13335c1a87` | `ce7acc13335c1a87f1c00656beda4f840fd2487eaa27ca53481f9b07bf527fe4` | `9d42862d3b6dcc8a21f046537b01ccc1a2e500e0756856fb42a67cf818a9436d` | 2,055,761 | PE32 | `0x0000` |
| 5 | `f3332db58ac55dc6` | `f3332db58ac55dc615185571dca717ecfe47af5f6b1f0942c81ade212f4a892a` | `de49156b36159e8cd8261778aa7574244111362dbde956a46d551dc26534e4ab` | 66,971 | PE32 | `0x0000` |
| 6 | `06b4b945e6a84cde` | `06b4b945e6a84cde65a74ae8e80c5333d255c29d26f334f69e04a1c146f18a2a` | `d2be79be19faeacbfc70fae37e265ef40d4af514ca0b57b91e2be262729baf99` | 25,471,672 | PE32 | `0x0000` |
| 7 | `e1256b3c82c7e334` | `e1256b3c82c7e3348e9b755bda2f38f3b596a5390bc405f20930f683139e9a3b` | `cc49f8d74d35bb5b652a70332d1308af4380cfcd40e6444a11ac1119fd3c5392` | 46,108 | PE32 | `0x0000` |
| 8 | `b089a47a0ba71b5a` | `b089a47a0ba71b5a9e9c7c9d74c45eca47392c8b89ed87f7bfbd2032608da270` | `89789b144600c682f00dcebfa3c6dd2f6a6da1baf329549d7c39fbea0635a96f` | 421,376 | PE32 | `0x0000` |
| 9 | `b830ebd21ba90375` | `b830ebd21ba90375f08b56f2f46e5dccbdd151c3d3fce58a8f33959d826ae5d2` | `1073c2d6cfc58e927f3a27e960467997b324c2d6a794a6797bedb11b5d0a6729` | 6,768,811 | PE32 | `0x0000` |
| 10 | `ad12d2ebe15b63a2` | `ad12d2ebe15b63a24c4950efde963d86dd1abc345051f0f460b392177d4f46f5` | `99f5c0c4fa2ec325954ba33880bcddcdeed4be09e49cd5ed584cec08b2ace634` | 408,861 | PE32 | `0x0000` |
| 11 | `0c61a4b549f38c7e` | `0c61a4b549f38c7ec9691c3d2f2060e01898590c61ca6c7df283b5a820924295` | `764749738eaea69f6aceaacfc5fbb141f8957987eba4952b2ade86ae9ffb9db3` | 541,730 | PE32 | `0x0000` |
| 12 | `b32f2bc895c406d3` | `b32f2bc895c406d344e0206e55da5c04d30bf053e7cb19d4ad72448b39a484cf` | `b959697e93e2d9d965d226750a76727521fbf08cd032cb3286226efbad3886f9` | 14,368,037 | PE32 | `0x0000` |
| 13 | `e048fa97092138db` | `e048fa97092138db2301298d79de221876600dc20fc06705503a44341dd7b6d2` | `dc1130e2cabeb641d22bf20c623c9dfecc6e3331d34ce85ab5882892f4aa7cbe` | 260,803 | PE32 | `0x0000` |
| 14 | `d9e0d18c9667cdbb` | `d9e0d18c9667cdbba627ee2735493a04d36155fb523bb7a1410eb7e01d8b1166` | `28140dad68f51aed43a0d8cc291ba671358777082f1009e8209542c2f2ae3a21` | 200,949 | PE32 | `0x0000` |
| 15 | `4f10945ea8917a48` | `4f10945ea8917a482ff8cd3fce5c2683de246fafa02a13475b0ccc461083c437` | `2fe620ed0373e012a0797902da9d748a77d822a183a3b248c8749224c9272b5d` | 1,037,712 | PE32 | `0x0000` |
| 16 | `5a38ffeced48c5a7` | `5a38ffeced48c5a71c734c94c23d39fa3212672a60d6a1ab30b48b221bcfd122` | `1007cda10e3879c662f567a3fac24a9fd0ea57d967f5decce180e1524e0a825a` | 419,616 | PE32 | `0x0000` |

*(Toàn bộ bảng dữ liệu trên cũng được lưu dưới dạng CSV tại `BODMAS_16_PROVENANCE_MAPPING.csv`).*

---

## III. MÃ NGUỒN VÀ QUY TRÌNH BIÊN DỊCH 2 FILE FIXTURE KIỂM SOÁT

Hai tệp này do nhóm tự phát triển làm mẫu chuẩn lành tính (Ground Truth Benign) độc lập, tự đóng gói, tính toán hàm số học $f(n) = n^2 + 7$, hoàn toàn không chứa mã lệnh can thiệp mạng, tệp tin hay quyền quản trị.

### 1. File `ReviewedBenignFixture.exe` (Managed .NET C#, 32-bit PE32)
- **Mục đích**: Đại diện cho phân khúc ứng dụng .NET Framework nhỏ (4 KB), có CLR Data Directory (`clr_header_present: True`).
- **Mã nguồn đầy đủ (`fixtures_src/ReviewedBenignFixture.cs`)**:
```csharp
using System;

/*
 * X-SENTINEL Research Artifact - Managed .NET C# Benign Fixture
 * Purpose: Baseline fixture for PE feature extraction & execution verification.
 * Safety: Read-only deterministic arithmetic f(n) = n^2 + 7. No network, no file I/O, no persistence.
 */
public class RevisionFixture {
    public static int Main(string[] args) {
        int n = 0;
        if (args.Length > 0 && !Int32.TryParse(args[0], out n)) return 2;
        Console.WriteLine("X_SENTINEL_BENIGN_FIXTURE:" + (n * n + 7));
        return 0;
    }
}
```
- **Lệnh biên dịch (Build Instructions)**:
  - *Trên Windows (Developer Command Prompt / MSBuild)*:
    ```cmd
    csc -target:exe -platform:x86 -optimize+ -out:ReviewedBenignFixture.exe ReviewedBenignFixture.cs
    ```
  - *Trên Linux (Mono C# Compiler)*:
    ```bash
    mcs -target:exe -platform:x86 -optimize+ -out:ReviewedBenignFixture.exe ReviewedBenignFixture.cs
    ```
- **Đặc tính kỹ thuật**:
  - Dung lượng: 4,096 bytes
  - SHA-256 byte: `72524cf3d72fe935d482300d4b9d7414dbea7ab9786b76723f3a7132331e4485`
  - Cấu trúc: PE32, Machine `0x014C` (x86), `clr_header_present: True`.

### 2. File `native_original.exe` (Native C, 64-bit PE32+)
- **Mục đích**: Đại diện cho phân khúc ứng dụng Native C/C++ thuần túy (43.5 KB), không có runtime ảo hóa.
- **Mã nguồn đầy đủ (`fixtures_src/native_benign_fixture.c`)**:
```c
/*
 * X-SENTINEL Research Artifact - Benign Native PE Fixture
 * Author: Pham Nguyen Hoang Phuc (PhucPNHSE203815) - TASK 2 PE Validation
 * Function: Computes f(n) = n^2 + 7 deterministically.
 * Safety: Read-only arithmetic, no network, no persistence, no file I/O.
 */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    long long n = 0;
    if (argc > 1) {
        char *endptr = NULL;
        n = strtoll(argv[1], &endptr, 10);
        if (*endptr != '\0') {
            fprintf(stderr, "Error: Invalid integer input '%s'\n", argv[1]);
            return 2;
        }
    }
    long long result = n * n + 7;
    printf("X_SENTINEL_BENIGN_FIXTURE:%lld\n", result);
    return 0;
}
```
- **Lệnh biên dịch (Build Instructions)**:
  - Biên dịch cross-platform bằng bộ công cụ MinGW-w64 x86_64:
    ```bash
    x86_64-w64-mingw32-gcc -O2 -s -Wl,--build-id=none \
        native_benign_fixture.c \
        -o native_original.exe
    ```
- **Đặc tính kỹ thuật**:
  - Dung lượng: 43,520 bytes
  - SHA-256 byte: `1c7b297387433f8237effba502fb9c5bc1eae80bf42151da4ea45bc271023689`
  - Cấu trúc: PE32+, Machine `0x8664` (x64), `clr_header_present: False`.

---

## IV. GHI NHẬN & CAM KẾT VỀ QUY TRÌNH NGHIỆM THU TASK M8

1. **Phạm vi bước kiểm kê tĩnh (Static Preflight)**:
   - Nhóm nghiên cứu hoàn toàn đồng thuận với đánh giá của người kiểm toán: Gói `m8_preflight.py` chỉ phục vụ mục đích **Xác thực Nguồn gốc Dữ liệu Đầu vào (Input Provenance Audit)**.
   - Trường trạng thái `functional_status: NOT_RUN` được thiết kế đúng theo chuẩn an toàn của gói: tuyệt đối không kích hoạt thực thi các mẫu không tin cậy trên môi trường kiểm kê tĩnh.
2. **Về kiểm chứng chức năng (Functional Verification)**:
   - Việc kiểm chứng khả năng thực thi và tính nguyên vẹn chức năng của các file lành tính (Sysinternals Process Explorer, Fritzing, Subnet Calculator, Native Fixture) đã được nhóm thực hiện riêng biệt trên môi trường Windows và Wine (đạt tỷ lệ 100% Pass) và được theo dõi trong hồ sơ nghiệm thu tổng thể (`manifest.csv`, `functionality_results.csv`).
3. **Kỷ luật dữ liệu nghiêm ngặt**:
   - Nhóm **giữ nguyên vẹn 100% hiện trạng dữ liệu và PE header** (`Machine = 0x0000`) của các mẫu BODMAS disarmed theo đúng chỉ đạo của người kiểm toán, tuyệt đối không tự ý vá header hay chạy lại inventory khi chưa có yêu cầu mới.

---
*Báo cáo được lập phục vụ công tác kiểm toán tính khả thi Problem-Space Real PE (Task M8) — Dự án X-SENTINEL.*
