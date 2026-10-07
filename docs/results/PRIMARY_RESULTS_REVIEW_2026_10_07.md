# Đọc và đối chiếu kết quả primary — 07/10/2026

Đây là bản review mới, không sửa model, ngưỡng, dữ liệu, kết quả hoặc báo cáo đã khóa.

## Kiểm tra bằng chứng

- 54/54 final cells complete; cả 108 bundle reduced/full được nạp và kiểm tra checksum/schema.
- 20.000 final source IDs mỗi run khớp roles đã khóa; metrics/counts tái tính từ paired_predictions khớp kết quả lưu.
- CSV và JSON báo cáo tái dựng khớp bản đã xuất. Selector khóa được kiểm tra lại chỉ từ development.
- Selector chung: **legacy_rare**. Legacy có 24/54 development runs đạt; signed conditioned có 8/54.

## Attack đủ mạnh và kín theo heuristic

- EMBER2018: 12/27 run đạt cả development và confirmation. Các run còn lại vẫn được giữ.
- EMBER2024: 12/27 run đạt cả development và confirmation. Các run còn lại vẫn được giữ.

## Detector trên các run đã đạt confirmation

Bảng dưới lấy trung bình đều theo run đã đạt cả hai screen. Đơn vị là %, không gộp sample qua seeds. Đây là thống kê mô tả, không phải CI hoặc kiểm định thắng/thua chung. Recall tính trên attack thành công trong tập malware eligible.

| Dataset | Method | Runs | Benign FPR | Recall successful eligible | Post-defense ASR | AUROC |
|---|---|---:|---:|---:|---:|---:|
| EMBER2018 | TADR | 12 | 1.92 | 37.15 | 43.07 | 88.36 |
| EMBER2018 | STRIP | 12 | 0.61 | 0.00 | 69.04 | 11.73 |
| EMBER2018 | X_primary_reduced | 12 | 0.52 | 35.75 | 39.92 | 90.72 |
| EMBER2018 | X_primary_full | 12 | 0.78 | 42.94 | 35.22 | 89.09 |
| EMBER2024 | TADR | 12 | 0.73 | 0.00 | 88.85 | 38.90 |
| EMBER2024 | STRIP | 12 | 0.79 | 0.00 | 88.85 | 12.93 |
| EMBER2024 | X_primary_reduced | 12 | 0.76 | 12.08 | 81.98 | 69.87 |
| EMBER2024 | X_primary_full | 12 | 0.90 | 19.11 | 76.19 | 79.18 |

## Diễn giải

Trên 12 run confirmed mỗi dataset, recall trung bình của full cao hơn reduced: EMBER2018 42,94% so với 35,75%; EMBER2024 19,11% so với 12,08%. FPR của full cũng cao hơn: 0,78% so với 0,52% và 0,90% so với 0,76%. Đây là tradeoff mô tả trên các run đã khóa, không chứng minh full thắng mọi family hay có ý nghĩa thống kê chung. Recall ở 2024 vẫn thấp; đa số successful attacks chưa bị cảnh báo.

Thành phần confirmed khác nhau giữa hai bộ: EMBER2018 có 3 concentrated + 9 spread + 0 cross-three-view; EMBER2024 có 0 concentrated + 3 spread + 9 cross-three-view. Không coi các run cross-three-view yếu ở 2018 hoặc concentrated yếu ở 2024 là bằng chứng detector chống được attack mạnh.

STRIP có recall successful eligible bằng 0 trên toàn bộ 24 run confirmed ở ngưỡng đã khóa. TADR cũng có recall bằng 0 trên 12 run confirmed EMBER2024. Giữ nguyên các kết quả âm này, không đảo score hoặc chọn lại ngưỡng sau khi xem final.

Latency trung bình mô tả qua 27 run: EMBER2018 reduced 28,24 ms, full 28,65 ms; EMBER2024 reduced 22,93 ms, full 23,38 ms. Model bytes của full khoảng 1,90 lần reduced. Latency này đo cả detector (có STRIP), không tách riêng chi phí mỗi thành phần và không đảm bảo đạt tương tự trên máy khác.

Full/reduced được so trên cùng main, mẫu, reference và calibration. Full có thêm ba clean view models. Kết quả cần đọc theo family/rate/seed và paired CI từng run; không dùng bảng trung bình để nói mọi tình huống full tốt hơn.

FPR calibration mục tiêu 1% không đảm bảo FPR final. AUROC đo phân biệt triggered malware và benign, không đồng nghĩa recall tốt ở ngưỡng đã khóa.

M3 vẫn là view_mass; M5 và Metadata-only stress không nằm trong phần chính. Behavioral là imports/exports tĩnh; trigger là sửa vector, chưa chứng minh khả thi trên binary PE.

Whole-process peak RAM không tách được RAM riêng từng variant. Latency là warmed single-input, có STRIP, cùng mẫu và thứ tự alternating; không phải đo end-to-end upload/extraction.

Chi tiết family, mọi run yếu, ranges, paired CI và resource nằm trong review.json và artifacts gốc. Không retune dựa vào final.
