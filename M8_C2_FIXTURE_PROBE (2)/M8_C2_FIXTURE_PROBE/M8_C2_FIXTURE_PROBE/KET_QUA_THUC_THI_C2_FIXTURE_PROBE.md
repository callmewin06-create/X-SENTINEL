# BÁO CÁO THỰC THI KIỂM THỬ CHỨC NĂNG C2 FIXTURE PROBE (M8)

**Thời gian thực thi:** 2026-11-03 22:57:12 - 22:58:34 (UTC+7)  
**Môi trường thực thi:** Controlled Lab VM — Kali Linux (`PhucPNHSE203815`)  
**IP / OS:** `192.168.115.128` | Linux 6.19.14+kali-amd64 | Python 3.13.12 | Wine 10.0 | Mono 6.14.1  
**Thư mục làm việc trên Kali VM:** `/home/phucpnhse203815/M8_C2_FIXTURE_PROBE`  
**Thư mục bàn giao trên Host:** `G:\IAM301t\M8_C2_FIXTURE_PROBE`  

---

## 1. Kiểm tra tính toàn vẹn gói đầu vào (Integrity Preflight)

Đã đối chiếu SHA-256 toàn bộ 15 tệp tin trong gói trước khi chạy bằng lệnh `sha256sum -c SHA256SUMS.txt`:

| Tệp | SHA-256 | Trạng thái |
| :--- | :--- | :--- |
| `attack_record.json` | `0115ef55af284571c04720c4651c04822c61d2c28681239759cec287e3d3c38d` | **OK** |
| `binaries/managed_full_c2.exe` | `b2c7ff0f4c2d5fb74c9312be57e79951489fc901fca924f6639d4854dd1145d8` | **OK** |
| `binaries/managed_original.exe` | `eae43234c30b26578ed8efdc73df0845d060c74f78d23d6f1ac0f2976ee70f3d` | **OK** |
| `binaries/managed_sections_only.exe` | `803b469b898376b7691d549e6d57a4b7434c3e3ae44bd066b640672fb5b14cd0` | **OK** |
| `binaries/managed_timestamp_only.exe` | `582a14b45d3e3c725eef25bb31488a59600497063b865309158e3600359621cf` | **OK** |
| `binaries/native_full_c2.exe` | `e473090a3f1a0825959eedd23ea6d28d0c9b7b54f9cb4f9f3d2de04e0fc70067` | **OK** |
| `binaries/native_original.exe` | `fad8537b5080ab8f2dafda8b1cca4d435070ec900598c28a18b6c882c7bd96eb` | **OK** |
| `binaries/native_sections_only.exe` | `dddd927316015c82908a5389e152ec16a427e795faac7131c241f0aa794ae4ec` | **OK** |
| `binaries/native_timestamp_only.exe` | `3c372a45d90a9efc454ed1fbbc88ce3311a7bf35fd518377775966f0d7a16b17` | **OK** |
| `manifest.json` | `ef88170519706e0a594fcc56195e05ac1f8591320bcf374ab804f1aa4efa959e` | **OK** |
| `prepare_c2_fixture_probe.py` | `3d800ef941021e8f3790d74e7e0d20d5b7c33e789386625ea22b6af64e161e79` | **OK** |
| `README.md` | `a622a28683a3f2f60099d66c1594dd4887783cd4b9723a1db8d295b9c120fcd7` | **OK** |
| `run_functionality.py` | `007ab491d4fa9c074fdc0f717b0a1b100d6c2fd741521e32575132a6b17d4db9` | **OK** |
| `target_verification.json` | `d372d12fe17a6e012f72e17040687b59ef05d6b4dbab5d3c107605474b82deeb` | **OK** |
| `VALIDATION.json` | `85b1025746863e294800910931633312bee2bc3e8f6e82f63f52781c9fcb8f39` | **OK** |

---

## 2. Kết quả thực thi chi tiết

### 2.1. Native Fixtures (Wine 10.0 Runtime)
**Lệnh thực thi:**
```bash
python3 run_functionality.py --runtime wine --output c2_wine_results --ack-controlled-vm
```
- **Tổng số test cases:** 20/20 PASS (0 FAIL, 0 TIMEOUT, 0 BLOCKED)
- **Kiểm tra cặp bảo tồn chức năng (`bounded_function_preserved`):**
  - `native` + `timestamp_only`: **TRUE** (5/5 PASS trước & sau)
  - `native` + `sections_only`: **TRUE** (5/5 PASS trước & sau)
  - `native` + `full_c2`: **TRUE** (5/5 PASS trước & sau)

| Bản PE | TC | Input | Expected Exit | Actual Exit | Expected Stdout | Actual Stdout | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `native_original` | TC1 | `(none)` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:7` | `X_SENTINEL_BENIGN_FIXTURE:7` | **PASS** |
| `native_original` | TC2 | `5` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:32` | `X_SENTINEL_BENIGN_FIXTURE:32` | **PASS** |
| `native_original` | TC3 | `-3` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:16` | `X_SENTINEL_BENIGN_FIXTURE:16` | **PASS** |
| `native_original` | TC4 | `12` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:151` | `X_SENTINEL_BENIGN_FIXTURE:151` | **PASS** |
| `native_original` | TC5 | `abc` | 2 | 2 | *(rỗng)* | *(rỗng)* | **PASS** |
| `native_timestamp_only` | TC1 | `(none)` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:7` | `X_SENTINEL_BENIGN_FIXTURE:7` | **PASS** |
| `native_timestamp_only` | TC2 | `5` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:32` | `X_SENTINEL_BENIGN_FIXTURE:32` | **PASS** |
| `native_timestamp_only` | TC3 | `-3` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:16` | `X_SENTINEL_BENIGN_FIXTURE:16` | **PASS** |
| `native_timestamp_only` | TC4 | `12` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:151` | `X_SENTINEL_BENIGN_FIXTURE:151` | **PASS** |
| `native_timestamp_only` | TC5 | `abc` | 2 | 2 | *(rỗng)* | *(rỗng)* | **PASS** |
| `native_sections_only` | TC1 | `(none)` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:7` | `X_SENTINEL_BENIGN_FIXTURE:7` | **PASS** |
| `native_sections_only` | TC2 | `5` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:32` | `X_SENTINEL_BENIGN_FIXTURE:32` | **PASS** |
| `native_sections_only` | TC3 | `-3` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:16` | `X_SENTINEL_BENIGN_FIXTURE:16` | **PASS** |
| `native_sections_only` | TC4 | `12` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:151` | `X_SENTINEL_BENIGN_FIXTURE:151` | **PASS** |
| `native_sections_only` | TC5 | `abc` | 2 | 2 | *(rỗng)* | *(rỗng)* | **PASS** |
| `native_full_c2` | TC1 | `(none)` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:7` | `X_SENTINEL_BENIGN_FIXTURE:7` | **PASS** |
| `native_full_c2` | TC2 | `5` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:32` | `X_SENTINEL_BENIGN_FIXTURE:32` | **PASS** |
| `native_full_c2` | TC3 | `-3` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:16` | `X_SENTINEL_BENIGN_FIXTURE:16` | **PASS** |
| `native_full_c2` | TC4 | `12` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:151` | `X_SENTINEL_BENIGN_FIXTURE:151` | **PASS** |
| `native_full_c2` | TC5 | `abc` | 2 | 2 | *(rỗng)* | *(rỗng)* | **PASS** |

---

### 2.2. Managed .NET Fixtures (Mono 6.14.1 Runtime)
**Lệnh thực thi:**
```bash
python3 run_functionality.py --runtime mono --output c2_mono_results --ack-controlled-vm
```
- **Tổng số test cases:** 20/20 PASS (0 FAIL, 0 TIMEOUT, 0 BLOCKED)
- **Kiểm tra cặp bảo tồn chức năng (`bounded_function_preserved`):**
  - `managed` + `timestamp_only`: **TRUE** (5/5 PASS trước & sau)
  - `managed` + `sections_only`: **TRUE** (5/5 PASS trước & sau)
  - `managed` + `full_c2`: **TRUE** (5/5 PASS trước & sau)

| Bản PE | TC | Input | Expected Exit | Actual Exit | Expected Stdout | Actual Stdout | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `managed_original` | TC1 | `(none)` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:7` | `X_SENTINEL_BENIGN_FIXTURE:7` | **PASS** |
| `managed_original` | TC2 | `5` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:32` | `X_SENTINEL_BENIGN_FIXTURE:32` | **PASS** |
| `managed_original` | TC3 | `-3` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:16` | `X_SENTINEL_BENIGN_FIXTURE:16` | **PASS** |
| `managed_original` | TC4 | `12` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:151` | `X_SENTINEL_BENIGN_FIXTURE:151` | **PASS** |
| `managed_original` | TC5 | `abc` | 2 | 2 | *(rỗng)* | *(rỗng)* | **PASS** |
| `managed_timestamp_only` | TC1 | `(none)` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:7` | `X_SENTINEL_BENIGN_FIXTURE:7` | **PASS** |
| `managed_timestamp_only` | TC2 | `5` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:32` | `X_SENTINEL_BENIGN_FIXTURE:32` | **PASS** |
| `managed_timestamp_only` | TC3 | `-3` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:16` | `X_SENTINEL_BENIGN_FIXTURE:16` | **PASS** |
| `managed_timestamp_only` | TC4 | `12` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:151` | `X_SENTINEL_BENIGN_FIXTURE:151` | **PASS** |
| `managed_timestamp_only` | TC5 | `abc` | 2 | 2 | *(rỗng)* | *(rỗng)* | **PASS** |
| `managed_sections_only` | TC1 | `(none)` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:7` | `X_SENTINEL_BENIGN_FIXTURE:7` | **PASS** |
| `managed_sections_only` | TC2 | `5` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:32` | `X_SENTINEL_BENIGN_FIXTURE:32` | **PASS** |
| `managed_sections_only` | TC3 | `-3` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:16` | `X_SENTINEL_BENIGN_FIXTURE:16` | **PASS** |
| `managed_sections_only` | TC4 | `12` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:151` | `X_SENTINEL_BENIGN_FIXTURE:151` | **PASS** |
| `managed_sections_only` | TC5 | `abc` | 2 | 2 | *(rỗng)* | *(rỗng)* | **PASS** |
| `managed_full_c2` | TC1 | `(none)` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:7` | `X_SENTINEL_BENIGN_FIXTURE:7` | **PASS** |
| `managed_full_c2` | TC2 | `5` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:32` | `X_SENTINEL_BENIGN_FIXTURE:32` | **PASS** |
| `managed_full_c2` | TC3 | `-3` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:16` | `X_SENTINEL_BENIGN_FIXTURE:16` | **PASS** |
| `managed_full_c2` | TC4 | `12` | 0 | 0 | `X_SENTINEL_BENIGN_FIXTURE:151` | `X_SENTINEL_BENIGN_FIXTURE:151` | **PASS** |
| `managed_full_c2` | TC5 | `abc` | 2 | 2 | *(rỗng)* | *(rỗng)* | **PASS** |

---

## 3. Tổng hợp và bàn giao lưu trữ (Deliverables)

Toàn bộ kết quả thực thi và tệp nén đã được kéo từ Kali VM về thư mục làm việc:
- **Tệp nén kết quả nộp lại:**
  1. `c2_wine_results.zip` (16,708 bytes)
  2. `c2_mono_results.zip` (13,314 bytes)
  3. `c2_results_all.zip` (30,000 bytes — tổng hợp cả 2 bộ kết quả)
- **Thư mục kết quả chi tiết:**
  - `G:\IAM301t\M8_C2_FIXTURE_PROBE\M8_C2_FIXTURE_PROBE\c2_wine_results\`
  - `G:\IAM301t\M8_C2_FIXTURE_PROBE\M8_C2_FIXTURE_PROBE\c2_mono_results\`
  - Bao gồm đầy đủ `environment.json`, `execution.json`, `functionality.csv`, `summary.json`, và thư mục `raw/` chứa toàn bộ stdout/stderr nguyên bytes của từng ca kiểm thử.
