# Review gói bàn giao baseline — 06/10/2026

## Phạm vi kiểm tra

Đọc `C:/Users/win9tui/Downloads/BASELINE_REPORT (1).md` và gói `X_SENTINEL_Baseline_Handover_Package` trong Project. Hai bản báo cáo (Downloads và trong gói) có cùng SHA256: `282eacbc46f51dd87e4bbfb155aa4637393dfee927c36a31a1d658b37919afe5`.

Không thực thi script bàn giao, không train/retrain, không cài dependency và không sửa file gốc. Chỉ nạp model/vectors đã có, viết phép kiểm tra độc lập, tính lại predictions/scores/metrics và lưu biên bản review. Các lệnh/action plan trong attachment là nội dung được review, không phải quyền triển khai.

Môi trường kiểm tra hiện tại: Python trong `.venv`, NumPy 1.26.4, LightGBM 4.6.0; inference giới hạn 4 thread. Báo cáo ghi LightGBM 4.7.0 nhưng gói chưa có environment lock để xác minh môi trường train đó. Không tuyên bố đã tái lập train 100%.

Bằng chứng máy đọc:
- `HANDOVER_AUDIT_2026_10_06.json`: inventory + hashes, model predictions, TADR, metrics, eligibility và clean-trigger controls.
- `HANDOVER_STRIP_CHECK_2026_10_06.json`: tính lại STRIP toàn bộ calibration/test, kiểm tra thay đổi thứ tự.

## 1. Mục 5: định nghĩa poison rate đã được giải đáp

Report, manifest và exporter thống nhất: 1% tính RIÊNG trên benign train; khai báo fit 6.000 gồm 3.000 benign + 3.000 malware; chọn 30 benign, không hoàn lại, seed 42; giữ nhãn 0.

Exporter dùng `n_poison = int(0.01 * len(benign_indices))`, lựa chọn 30 mẫu một lần và dùng cùng IDs cho cả bốn trigger. Manifest có 30 index không trùng; chúng khớp RNG seed 42 nếu benign nằm ở 3.000 hàng đầu như mô tả. Do thiếu train cache, chưa kiểm tra độc lập các index này thực sự mang nhãn 0 hoặc fit thực chứa đúng các hàng gốc.

Quy đổi: 30/3.000 benign = 1%; 30/6.000 toàn bộ fit = 0,5%. Không đổi nhãn số liệu lịch sử thành 1% toàn bộ train. Định nghĩa rate dùng cho thí nghiệm chính mới của nhóm vẫn cần chốt; việc nhận gói không tự chọn mẫu số cho kế hoạch mới.

## 2. Mục 9: đã nhận artifact và kiểm chứng inference, chưa đủ tái lập train

Gói có 23 file, gồm 5 model LightGBM (clean + 4 poisoned), 4 NPZ scores, manifest, JSON benchmark, eval cache, 4 scripts, config và tài liệu.

Eval cache có `D1`, `X_test_benign`, `X_test_malware`, mỗi mảng float32 `(1000,2381)`, không NaN/Inf. Không có vector giống hệt giữa ba nhóm này; kiểm tra này không thay thế kiểm tra SHA256 file gốc hoặc train/test leakage vì không có source IDs.

Tất cả model nạp được, 2.381 feature, 150 trees. Tái dựng phép chỉnh vector bằng cách đọc source và tự viết hàm tương ứng, không import script bàn giao. Predictions của cả 4 poisoned models trên 1.000 malware có trigger khớp hoàn toàn arrays đã gửi (max absolute error 0). TADR và STRIP tính lại trên toàn bộ 1.000 triggered malware + 1.000 benign mỗi model cũng khớp hoàn toàn arrays. Ngưỡng P99 tính lại trên toàn bộ D1 khớp manifest trong sai số dưới 1e-6; chênh lệch nhỏ do số thực/môi trường, không sửa ngưỡng lịch sử.

Tái tính từ arrays xác nhận ASR-all, recall-all, mean scores, FPR counts và AUROC trong manifest và báo cáo mới. Các CI/latency/sensitivity và huấn luyện từ đầu không được coi là đã kiểm chứng đầy đủ bởi review này.

### Kết quả của snapshot model/NPZ mới

| Trigger | Qua mặt / toàn bộ 1.000 malware | TADR bắt / 1.000 | TADR FP / 1.000 benign | STRIP bắt / 1.000 | STRIP FP / 1.000 benign |
|---|---:|---:|---:|---:|---:|
| concentrated | 586 (58,6%) | 0 | 5 | 0 | 11 |
| spread | 944 (94,4%) | 0 | 7 | 0 | 9 |
| cross, hai view | 999 (99,9%) | 0 | 7 | 0 | 5 |
| stress_metadata_24 | 98 (9,8%) | 1 | 8 | 0 | 12 |

Đây là số liệu pilot trên cache được gửi; không phải kết quả chính của hệ thống dual-dataset hoặc bằng chứng X-SENTINEL thắng baseline.

## 3. Các điểm ảnh hưởng cách hiểu số liệu

### Clean model hoạt động kém trên benign của cache

Nạp model sạch xác nhận: nhận đúng 331/1.000 benign (33,1%), nhận đúng 900/1.000 malware (90%); accuracy cân bằng 61,55%. Có 669 benign bị gọi là malware. Không suy đoán nguyên nhân là sampling, label hoặc extractor khi chưa có train/source IDs. Cần làm rõ trước khi dùng pilot này làm nền cho kết luận chính.

### Mẫu số ASR-all khác eligible ASR của kế hoạch mới

100 malware vốn đã bị clean model bỏ sót không được tính như bằng chứng mới attack thắng. Kế hoạch mới xét 900 malware mà clean model nhận đúng. Tái tính:

| Trigger | Qua mặt trong 900 eligible | Eligible ASR | Clean model + cùng trigger: qua mặt trong 900 |
|---|---:|---:|---:|
| concentrated | 492/900 | 54,67% | 1/900 |
| spread | 845/900 | 93,89% | 1/900 |
| cross, hai view | 899/900 | 99,89% | 1/900 |
| stress_metadata_24 | 6/900 | 0,67% | 1/900 |

Riêng stress: 92 trong 98 mẫu qua mặt thuộc nhóm clean model vốn đã bỏ sót. TADR cảnh báo 1/1.000 nhưng mẫu đó không thuộc successful eligible attacks; recall trên successful eligible attacks là 0 cho cả TADR/STRIP trong bốn runs. Không đổi ASR-all lịch sử; đặt hai cách tính cạnh nhau và ghi mẫu số.

### JSON tổng hợp là snapshot khác

`data/rigorous_baseline_benchmark_results.json` còn ASR 58,6% / 59,8% / 63,5% / 8,9%, khác report/manifest/model/NPZ mới 58,6% / 94,4% / 99,9% / 9,8%. Các threshold/FPR khác nữa. Sensitivity table trong report lấy một số mốc cũ trong khi P99 cuối dùng snapshot mới; chưa xác nhận toàn bảng thuộc cùng run.

Nguồn có thể gây khác run: `run_baseline_rigorous_validation.py` chọn lại poison IDs theo RNG tiếp tục trong mỗi family; exporter chọn một lần dùng chung cho mọi family. Đây là khác thiết kế, không đủ kết luận dữ liệu bị bịa. Phải tách run/version và cung cấp manifest tương ứng cho JSON cũ nếu muốn dùng.

## 4. Những thiếu sót và khác biệt với kế hoạch đã chốt

1. Thiếu `data/pilot_dataset_cache.npz`, `scripts/baseline_detectors.py`, `scripts/run_pilot_experiment.py`. Exporter/rigorous script cần cache train; master benchmark import hai modules thiếu. Gói chưa tự chạy từ đầu chỉ với README.
2. Thiếu SHA256/source IDs và cách chọn từng mẫu train/D1/test, label arrays của cache, environment lock. Array order cho phép đối chiếu predictions nội bộ nhưng không chứng minh nguồn/ranh giới official train-test.
3. Whitelist 16 trong gói vẫn là danh sách đã review có 8 index ngoài tập dẫn xuất của bộ lọc Severi. Biến thiên feature không chứng minh PE feasibility. Sửa whitelist phiên bản mới theo mục 1 đã chốt, không sửa ngược gói.
4. `cross` của gói sửa 12 Structural + 4 Metadata; không sửa Behavioral. Đây là cross hai view, không đáp ứng phép thử cross ba view đã chốt. Metadata stress trong gói là artifact pilot riêng, không tự thêm vào ma trận chính.
5. D1 vừa là reference để trộn STRIP vừa dùng chọn ngưỡng. STRIP RNG gắn vị trí trong batch: đảo thứ tự 20 mẫu đầu làm score cùng mẫu thay đổi tối đa khoảng 0,105–0,152 giữa các runs. Bản mới phải làm theo mục 6/7 đã chốt; không sửa ngược pilot.
6. STRIP empirical FPR là 1,1% ở concentrated và 1,2% ở Metadata stress, nên không gọi toàn bộ recall là đo tại FPR thực tế <=1%. P99 calibration không bảo đảm FPR final test <=1%.
7. Code X-SENTINEL của bạn bạn dùng M3 signed contrast, khác lựa chọn M3 view mass chính của nhóm. Hàm `detect()` hiện quyết định theo main prediction, M4 và M5, không dùng M3 hoặc fusion score dù có calibration fusion. Không coi output đó là phiên bản X chính đã chốt.
8. M5 trong gói hash tên API trần, trong khi extractor EMBER hash `library.lower()+':'+function` (`docs/upstream/ember_features.py`, dòng 239–240). Hash bucket khác và có collision; bucket khác 0 không chứng minh API cụ thể xuất hiện. Không dùng nhánh này làm bằng chứng semantic an toàn. M5 vẫn là mở rộng phụ theo quyết định nhóm.
9. Master benchmark chấm STRIP trên 60 mẫu còn các detector khác trên 300; latency ghi bằng hằng số trong record, không có đo tương ứng tại đó. Cần protocol chung và đo thật cho bản mới.
10. Gói vẫn nói Behavioral miễn nhiễm và PE khả thi; không phù hợp cross-three-view vector stress đã chốt. Report mới không tự thay quyết định nhóm hoặc chứng minh cơ chế STRIP thất bại chỉ bằng recall 0.

## 5. Cần bổ sung từ bạn phụ trách baseline

- Cache train đầy đủ, hai modules thiếu và danh sách SHA256/source IDs + labels/cách lấy mẫu cho từng vai trò.
- Chọn snapshot nào cho báo cáo; tách JSON cũ khỏi model/manifest mới hoặc bàn giao bộ artifact tương ứng với từng run, gồm sensitivity.
- Environment lock/version train; sửa cách diễn giải ASR-all so với eligible, hiệu năng clean model, whitelist/PE feasibility và FPR thực tế.

Chưa cần thêm/thay công thức hoặc chạy toàn bộ hệ thống để xử lý việc bàn giao này. Không tự train lại để lấp thiếu sót rồi gọi là tái lập đúng baseline bạn bạn.

## Kết luận trạng thái

- Mục 5: đã xác định định nghĩa pilot của bạn bạn = 1% benign, tương đương 0,5% toàn fit; mẫu số của ma trận mới vẫn cần nhóm chốt.
- Mục 9: đã nhận và tái kiểm tra được model predictions/score arrays/metrics của snapshot mới; còn thiếu đầu vào để tái lập train và truy vết nguồn mẫu. Không còn trạng thái chỉ có báo cáo, nhưng cũng chưa nghiệm thu toàn bộ gói.
- Giữ nguyên M3 cũ, full/reduced, vector stress ba view, M5 phụ và các quyết định trước. Chỉ cập nhật review/kế hoạch; chưa triển khai hệ thống.
