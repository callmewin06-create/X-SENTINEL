# Chạy phần nghiên cứu chính — 07/10/2026

Tài liệu này bổ sung tiến độ sau bản ghi ngày 06/10, không thay các kết quả lịch sử. Các lệnh chạy từ gốc Project bằng PowerShell. **Cập nhật hoàn tất:** xem [đọc kết quả](results/PRIMARY_RESULTS_REVIEW_2026_10_07.md) và [kiểm chứng dashboard/Docker](DASHBOARD_DOCKER_CHECK_2026_10_07.md). Các mốc đang chạy dưới đây giữ lại để tra lịch sử.

## Mốc hoàn tất ngày 07/10

Pipeline ghi `complete` lúc 11:24 UTC (18:24 Asia/Bangkok), tại `outputs/primary_pipeline/manual_20261007_110222/status.json`. Development đủ 54/54 mỗi dataset; selector chung `legacy_rare` đã khóa trước confirmation. Confirmation và final đủ 27/27 mỗi dataset, không failed/unsupported/not_run. Báo cáo gốc ở `outputs/primary_reports/report_2026_10_06/`; tên thư mục giữ ngày protocol, không phải thời điểm hoàn tất.

Review độc lập đã đối chiếu 54 final cells và 108 bundles, tái tính metrics và tái dựng báo cáo khớp bản gốc. Dashboard mới dùng các bundle primary; 50 tests Windows đạt và Docker Linux đã build/chạy healthy. M3 vẫn view_mass, M5 tắt; chưa push Git. Các số liệu recall/FPR và giới hạn nằm trong bản đọc kết quả.

## Quy trình và dữ liệu

1. Kiểm tra SHA256 cả sáu ZIP PE EMBER2024. Đã hoàn tất; bằng chứng ở `data/primary/EMBER2024/archive_verification.json`.
2. Đọc trực tiếp JSONL trong ZIP, audit toàn bộ ID, gộp bản trùng có cùng split/nhãn/type/raw feature và loại ID xung đột theo quyết định đã duyệt. Chỉ vector hóa ngân sách được duyệt: 232.500 train và 20.000 test. Giữ phạm vi PE chính thức, bao gồm `general.is_pe=0` khi vector 2.568 chiều hữu hạn; giữ nguyên feature/cờ upstream. Audit theo split, loại file, nhãn và is_pe, tách raw occurrences, unique representatives và materialized samples. Không giải nén toàn bộ ZIP.
3. Khóa các vai trò fit/selection/development/confirmation/reference/calibration/final. Development chỉ mở vai trò thuộc official train; confirmation và final không dùng để chọn lại selector.
4. Development so hai selector, ba family, ba rates và ba seeds: 54 cấu hình mỗi dataset. Candidate của từng seed khóa trước khi xem dự đoán development. Run yếu, lỗi hoặc unsupported vẫn được giữ.
5. Khi cả hai bảng development đủ 54 cấu hình, chọn một selector chung bằng quy tắc đã duyệt. Sau đó chạy confirmation độc lập.
6. Tái sử dụng đúng model đã khóa, train ba clean view mỗi seed, hiệu chỉnh từng bundle full/reduced bằng reference/calibration riêng, rồi đánh giá paired trên final. M3 vẫn là view_mass; M5 tắt. Không thêm Metadata-only stress.
7. Xuất bảng và báo cáo từ bằng chứng thật. Báo cáo không coi các seed dùng lại ID là mẫu độc lập và không suy ra ưu thế RAM của từng variant từ peak RAM của cả tiến trình.

## Lệnh mới

```powershell
.venv/Scripts/python.exe scripts/xsentinel.py prepare-v3 --help
.venv/Scripts/python.exe scripts/xsentinel.py develop-primary --help
.venv/Scripts/python.exe scripts/xsentinel.py lock-selector --help
.venv/Scripts/python.exe scripts/xsentinel.py confirm-primary --help
.venv/Scripts/python.exe scripts/xsentinel.py run-primary --help
.venv/Scripts/python.exe scripts/xsentinel.py report-primary --help
```

`configs/primary_protocol.json` khóa thiết kế nghiên cứu. `configs/primary_execution.json` khóa tham số model, detector, bootstrap và latency. Các lệnh legacy `run`/`develop-attack` không chạy ma trận mới.

Mỗi phase lưu cấu hình, checksum source, snapshot source, manifest và checkpoint. `--resume` chỉ dùng khi bằng chứng còn khớp. Không sửa source lõi hoặc cấu hình giữa run; nếu cần thay thiết kế, tạo namespace mới. Không khởi động một worker khác ghi vào thư mục đang có worker chạy.

## Bằng chứng đang có

- EMBER2018: roles ở `data/primary/EMBER2018/protocol_v2`; development thật đang chạy tại `outputs/primary_development/EMBER2018/round_1`.
- Seed 17: model sạch 200.000 mẫu đã train xong, mất khoảng 140 giây. Đây là model nghiên cứu thật, khác pilot tài nguyên 40.000 mẫu.
- Kết quả development đầu tiên của legacy selector/concentrated: ASR lần lượt khoảng 15,92% / 29,35% / 56,59% ở rates 0,5% / 1% / 2%. Run 2% đạt heuristic strong + stealth. Spread 0,5% đạt ASR khoảng 52,03% và heuristic strong + stealth. Đây là kết quả development; chưa phải confirmation hoặc kết quả detector.
- EMBER2024: audit ID hoàn tất ở `data/ember2024_primary_source_v2/audit_summary.json`: 2.880.060 duplicate occurrences, 2.879.940 duplicate IDs, 104 known-seen IDs, 0 cross-dataset matches và 0 ID xung đột theo policy hiện tại. Preparation từng dừng khi gặp record official PE có `general.is_pe=0`. Ngày 07/10, người dùng duyệt giữ record nếu vector hợp lệ; đã tiếp tục từ checkpoint với policy này. Không dùng is_pe để lấy bù/chọn lại ID. Chưa có dataset.json hay frozen roles hoàn chỉnh ở thời điểm khởi động lại.
- Bộ điều phối, confirmation, calibration, final và báo cáo đã chạy xuyên suốt trên fixture nhỏ V2/V3. Fixture chỉ kiểm tra code, không tính là kết quả nghiên cứu.
- Toàn bộ test suite hiện tại: **47 passed**, 14 warning deprecation từ thư viện plotting/UI. Đã kiểm tra dataset và baseline data tiếp tục bị Git bỏ qua, trong khi các file Python ở `src/xsentinel/data/` có thể được version control; cache Python vẫn bị bỏ qua. Trước đây rule `data/` còn che cả thư mục code này.
- Sau quyết định is_pe=0: **5 preparation tests passed**, gồm test mới đối chiếu toàn bộ vector đã giữ với upstream, kiểm tra raw/unique/selected audit, resume và từ chối đổi policy/corrupt audit. Không thay code lõi của development 2018 đang chạy.

Các số trên là mốc tại thời điểm viết. Đếm tiến độ mới trong `results.json`; chỉ có `completion.json` mới chứng minh phase hoàn tất.

### Mốc 00:36 ngày 07/10 (Asia/Bangkok)

Preparation EMBER2024 đã hoàn tất cả 192 member, audit 5.760.000 raw occurrences và vector hóa đủ 232.500 train + 20.000 test. `dataset.json` và audit `is_pe_audit.json` đã có; các roles V3 cũng đã khóa tại `data/primary/EMBER2024/protocol_v2`. Giữ nguyên feature/cờ theo policy đã duyệt. Worker preparation đã kết thúc. Bộ điều phối chuyển sang `waiting_for_2018_development`.

Development EMBER2018 đã hoàn tất 17/54 cấu hình ở thời điểm kiểm tra này. Chưa khóa selector chung, chưa chạy confirmation/final. Preparation V3 hoàn tất không đồng nghĩa đã train model V3 hoặc có kết quả detector.

## Nối các bước và theo dõi

`scripts/continue_primary_pipeline.py` đã khởi động, nối các bước tuần tự sau worker preparation và development 2018 bằng PID thực đã xác minh. Nó chờ preparation hoàn tất, khóa roles V3, chờ worker 2018 kết thúc rồi mới đo pilot/train V3 để tránh hai job native training cạnh tranh tài nguyên. Driver chưa hoàn tất nghiên cứu; trạng thái hiện tại đọc trong status.json.

Driver lưu `pipeline.lock.json` và `status.json` ở `outputs/primary_pipeline/run_2026_10_06`. `needs_attention` là dừng có lỗi, không phải hoàn tất; đọc log và checkpoint trước khi tiếp tục. Driver không push Git, upload dataset, hay tạo lịch chạy lặp lại.

Quy tắc vector nằm ở `configs/ember2024_vector_policy.json`, được khóa riêng trong `data/ember2024_primary_source_v2/vectorization.lock.json` cùng checksum preparer, vectorizer, upstream và danh sách ID đã chọn. Preparation lock và audit ID cũ giữ nguyên. Ba member đã hoàn tất trước khi dừng chỉ chứa vector is_pe=1 nên được tái sử dụng, đồng thời đọc lại để bổ sung audit toàn nguồn. Member đang dở được tính lại. Snapshot preparer trước sửa và lý do nằm ở `outputs/primary_preparation_repairs/is_pe_policy_2026_10_07/`; chưa sửa kết quả hoàn tất cũ.

```powershell
.venv/Scripts/python.exe scripts/xsentinel.py prepare-v3 --archives data/ember2024_archives --out data/ember2024_primary_source_v2 --verification data/primary/EMBER2024/archive_verification.json --history-root . --duplicate-policy configs/ember2024_preparation.json --vector-policy configs/ember2024_vector_policy.json --resume
Get-Content outputs/primary_pipeline/run_2026_10_06/status.json
```

Lệnh preparation trên chỉ dùng khi worker hiện tại đã dừng. Sau hoàn tất, số đếm theo loại/nhãn nằm trong `data/ember2024_primary_source_v2/is_pe_audit.json`; trong lúc chạy, `is_pe_audit_members.json` là audit từng member đã xử lý, chưa phải toàn dataset.

Docker chưa được build/run vì terminal chưa có executable. Binary extraction V3 chưa xác thực; đường vector/raw JSON là phạm vi hiện có. M5 để sau theo quyết định đã duyệt. Gói baseline ngoài vẫn thiếu source ID lịch sử, nên không tuyên bố mọi mẫu hoàn toàn chưa từng được quan sát.
