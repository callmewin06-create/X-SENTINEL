# Bàn giao triển khai JSTIS ngày 09 tháng 11 năm 2026

**Cập nhật10/11:** pipeline đã exit0; không còn cần theo dõi hoặc khởi động lại. Word mới tại `output/jstis_revision_2026_11_10/X_SENTINEL_Anonymous_Completed_M3_2026_11_10.docx`. Xem `docs/reviews/JSTIS_COMPLETED_RESULTS_2026_11_10.md` và QA của bản mới. Các session/status “đang chạy” dưới đây chỉ là lịch sử; không resume batch đã hoàn tất.

User đã duyệt triển khai toàn bộ plan trong `docs/plans/M3_JSTIS_REVISION_PLAN_2026_11_09.md`. Giữ hướng evaluation/negative results, LightGBM static PE. Không chuyển sang runtime behavior/general defender. Không chạy PE trên host, không auto commit/push/email/submit.

Trạng thái chi tiết và17mục góp ý: `docs/reviews/JSTIS_REVISION_STATUS_2026_11_09.md`.

Word mới: `output/jstis_revision_2026_11_09/X_SENTINEL_Anonymous_Working_2026_11_09.docx`; source04/11 nguyên vẹn. Đã QA20trang toàn bộ,32tables,13nativeequations trong `QA.json`. Working draft chưa ghép fresh M3; đồng đội chuyển LaTeX theo template chính thức đã tải. Không cần render/sửa lại nếu chưa có thay đổi nội dung.

## Tiến trình đang hoạt động lúc bàn giao

- Execsession3310: `run_jstis_matrix.py --data data/jstis_revision_2026_11_09 --output outputs/jstis_revision_2026_11_09/attacks_v2`.
- Execsession96201: `finish_jstis_after_matrix.py`, chờ đủ sáu cell receipts rồi global lock/release/evaluate/summarize vào `outputs/jstis_revision_2026_11_09/followup`.
- Materialization V2/V3 đã hoàn tất. Session4837 kết thúc thành công. Không khởi động driver thứ hai đồng thời.
- `attacks` v1 là lần dừng RAM trước poison fit, giữ lịch sử. `attacks_v2` là batch hiện tại với file-backed poison buffer, N/rounds/budget giữ nguyên. Sourcev1 lưu `implementation_v1`. Reuse clean/Behavioral/selectionSHAP có hashes tại seed17/REUSED_CLEAN_FROM.json.

Trước khi tiếp tục phải kiểm live receipts/log, không mặc định process còn chạy chỉ từ ghi chú này. Tool session có thể không còn truy cập được ở chat khác; đối chiếu file tiến độ/actual worker PID và owned process trước mọi hành động. Không giết process không xác minh thuộc batch này.

## Các bước tiếp theo

1. Theo dõi batch đến hoàn tất hoặc lỗi; giữ nguyên mã đã lock trong lúc run. Kiểm `launch_*.log`, candidate `result.json`, arm trajectory và `ATTACKS_LOCKED.json`.
2. Nếu infrastructure failure, xử lý đúng nguyên nhân; không ghi NO_VALID_ATTACK hoặc giảm budget. Driver stopped + follower sẽ dừng. Resume chỉ sau xác nhận không có driver còn hoạt động. Nếu đổi scientific code cần run root mới/provenance rõ ràng.
3. Global barrier khóa đủ36static+12arms trước held-out. New evaluator paths chưa tồn tại trước barrier. Không mở arrays confirmation/final để “kiểm thử” trước đó.
4. Các scripts `materialize_jstis_evaluator.py`, `evaluate_jstis_followup.py`, `summarize_jstis_followup.py` đã có code/compile và guard tests, chưa được chạy trên fresh held-out. Pipeline sẽ chạy sau global barrier nếu không lỗi; cần inspect runtime outputs và sửa lỗi kỹ thuật minh bạch.
5. Sau results, phân tích all attempts/unconfirmed/no-valid, seed variation/counts/CP/common success và raw-kNNsameaccess. Ghép bảng/M3 results/limitations/conclusion vào Word và response matrix; không suy new results từ pilot cũ.
6. Kiểm primary216 hashes lần nữa, anonymity bản upload, journal layout/bibliography/author info; không tự submit.

## Bằng chứng đã hoàn tất

- cache_audit, c2_attribution, direct_evasion, score_tails đều ở `outputs/jstis_revision_2026_11_09`.
- Headline calibration macro recall35.7461%/48.3268%, final benign FPR0.5217%/0.7767%.
- C2 poisoned physical-minus-ideal VMC+0.00241365/+0.00424567; original-to-physical+0.101915/-0.092192. n2benign,modernadapter,legacyparity chưa có.
- Fixed Development100IDs/dataset direct restoration tất cả54models; V2 Cross cleanASR93.88%, V3 18.37%, không dùng new held-out.
- Reduced FPR0/54>1%; Full6/54, worst227/10000.
- Test report44passed13warnings tại TEST_RESULTS.xml. Native Unicode model serialization đã sửa trong experiment.train; tests roundtrip passed.
- Worker memory phải đọc `process_memory` trong candidate/clean_profile. Launcher peak ~4MB từ driver không đại diện actual Python worker; đừng dùng con số đó làm resource result. First v2 poison fit135.89s, actualworkerpeakWS6.23GB/commit3.20GB.

## Paths và lưu ý

`scripts/revise_jstis_word.py` là builder Word; chạy bằng Python bundled document runtime, không dùng .venv thiếu python-docx. Đã mark_artifact_operation_started đúng một lần trong lượt này. Render helpers `render_jstis_word.ps1` (nativeWordread-onlyhidden, có thể cần sandbox escalation) và `render_jstis_word.py` (bundledrender_docx với native PDF). Khi Word thay đổi phải render và xem lại đủ trang.

Fresh exclusion ledger622688knownIDs; bảy roles được cấp từ metadata, sourceID crossdataset overlap0. Attacker cả hai dataset fit200K/selection10K/development10K balanced. V3 giữ80originalis_pe0/220000 records, không sửa flag. SHA disjoint không loại near duplicates/family/time/external exposure.

Không ghi global memory nếu user không yêu cầu. Đây chỉ là handoff trong project được user cho phép sửa.
