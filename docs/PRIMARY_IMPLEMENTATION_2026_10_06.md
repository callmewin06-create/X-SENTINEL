# Triển khai X-SENTINEL bản chính ngày 06/10/2026

**Cập nhật sau bản ghi này:** xem [tiến độ và workflow ngày 07/10](PRIMARY_RUN_GUIDE_2026_10_07.md), [review kết quả đã hoàn tất](results/PRIMARY_RESULTS_REVIEW_2026_10_07.md) và [dashboard/Docker đã kiểm chứng](DASHBOARD_DOCKER_CHECK_2026_10_07.md). Các phần “chưa có CLI orchestration”, “mới có một ZIP” và 41 tests dưới đây ghi lại mốc cũ. Kết quả lịch sử không bị sửa.

Đã bắt đầu triển khai bản mới theo bàn giao và các câu trả lời trực tiếp trong chat này. Nền tảng hai schema, detector và so sánh paired đã có code và kiểm tra; chưa có kết quả detector của ma trận chính. Các kết quả, model, split và tài liệu lịch sử được giữ nguyên. Chưa commit, push hoặc upload.

## 1. Những lựa chọn đã chốt trong chat này

Mỗi dataset: fit 200.000 cân bằng; selection/development/confirmation mỗi 10.000 cân bằng; reference 500 benign; calibration 2.000 benign; final 20.000 cân bằng. Pilot fit 40.000 dùng đo tài nguyên. Poison rates 0,5% / 1% / 2% tính trên tổng fit; seeds 17 / 29 / 43.

Ba family chính: `concentrated_structural` 2 feature restricted; `spread_structural` 10 feature restricted; `cross_3view_stress` 8 Structural + 8 Behavioral + 8 Metadata. Không thêm cross hai view hay Metadata-only stress. Whitelist là ràng buộc thao tác vector, không chứng minh giữ chức năng PE.

Strong screen: eligible ≥1.000, ASR ≥50%, paired gain ≥20 điểm %. Stealth dùng accuracy loss **strict <0,5 điểm %**. Tối đa hai vòng protocol development mỗi dataset. M5 để sau phần chính.

So `legacy_rare` và `signed_shap_conditioned` trên development. Khóa **một selector chung cho hai dataset** trước confirmation: ưu tiên số run đạt strong + stealth, rồi paired gain trung bình, hòa tiếp chọn signed conditioned. Run yếu, lỗi và unsupported vẫn phải có trong bảng. Với run lỗi không có prediction, paired gain không xác định: báo mean trên run hoàn tất kèm mẫu số và số run lỗi; không gán số liệu gain giả. Khi cả hai selector không có run hoàn tất, code từ chối khóa.

Cấu hình quyết định: `configs/primary_protocol.json`. Ma trận chính dự kiến 27 poisoned + 3 clean main + 9 clean view = **39 model/dataset, 78 cho hai dataset**, không nhân đôi poisoned main khi so full/reduced. Đây là số model theo scope, chưa phải số đã train. Development/pilot là ngân sách khác.

## 2. Bước schema giúp tránh dùng nhầm model

`src/xsentinel/schema.py` có ba schema: legacy V2 `ember-v2-2381-views-v1`, primary V2 `ember-v2-2381-views-v2`, primary V3 `ember-v3-2568-views-v1`. Mỗi schema ghi tên/order/type, group, view và whitelist; fingerprint khóa toàn bộ mapping.

V2 primary có đủ 17 index dẫn xuất, thêm 684 đúng tên `header.optional.minor_subsystem_version`. Code attack legacy vẫn giữ whitelist 16 đã thực dùng. Các model và báo cáo cũ không đổi tên thành primary.

V3 được khóa theo extractor commit `0ef753e81d98bf209f71b03cd331dfc190b5b54d`, kèm checksum source và bảng PE warnings. General.size/is_pe/start bytes thuộc Structural; General.entropy thuộc Metadata; imports/exports và các count của chúng thuộc Behavioral. Header/section/directories/Rich/Authenticode/warnings thuộc Structural. V3 có 467 Structural, 1.411 Behavioral, 690 Metadata. Categorical indices là 2–6, 701, 702; train helper ánh xạ lại vị trí khi train từng view.

Whitelist V3 hiện là 13 field Structural tương ứng về ý nghĩa với V2; cần kiểm tra biến thiên trên selection chính trước chọn trigger. Không giả định Metadata/MZ_count V2 có tương đương V3. Không đủ 10 feature biến thiên thì ghi unsupported, không mở whitelist ngầm.

V3 raw adapter bỏ riêng imports thư viện parse binary không cần cho JSON; phương thức xử lý raw của upstream được giữ nguyên. Không cài pefile/signify và không cung cấp binary extraction V3. Hai chi tiết upstream đã ghi nhận và giữ nguyên: exports field đầu là độ dài vector hash (128), không phải số export thật; vòng DataDirectories bỏ phần tử cuối theo `range(1,len(raw_obj)-1)`. Đây là hành vi source đã pin, chưa tự sửa thành extractor khác.

## 3. Bước detector giữ công thức đã chọn

Protocol mới tên `xsentinel-primary-v2`. M3 chính vẫn là `view_mass`, không dùng contrast. M4 reduced là `(1-p_main)*max(Net_behavioral,0)/sum(abs(phi))`. M4 full là `max(0,p_behavioral-p_main)`. Hai thành phần gộp 50/50 theo right empirical CDF của benign reference. Mỗi variant có tau riêng. Rank không phải xác suất backdoor.

Native SHAP bỏ bias và kiểm tra tổng khớp raw margin. Zero mass cho TADR/M3/M4 reduced bằng 0; M4 full vẫn theo chênh xác suất của hai model. Điểm 0 không chứng nhận an toàn.

Reduced không nhận clean view model. Full nhận đủ ba view model; clean main chỉ ở evaluator. M5 mặc định tắt ở primary, không là điều kiện chạy hay kết luận chính. Bundle legacy được nhận diện riêng và vẫn dùng gate full `(1-p_main)*p_behavioral` cùng các tên score cũ. Primary reduced và legacy reduced trùng công thức thành phần/fusion; không trình bày như hai detector độc lập.

STRIP giữ N=50, alpha=0,5 và seed theo nội dung float32 của mẫu. Kiểm tra repeat, đảo thứ tự và chia batch không đổi score cho cả hai schema. Score là `1-mean(binary_entropy(p_mix))`, không phải entropy của mean probability. Vector trộn có thể không tương ứng PE hợp lệ.

Reference/calibration tách nhau. Detector từ chối overlap vector ở primary; organizer kiểm tra source SHA riêng. Tau dùng order statistic và strict `score>tau`. Bundle lưu FP count, size, FPR calibration, hash nguồn calibration, schema và component versions. Target FPR 1% không bảo đảm FPR final test.

## 4. Bước dữ liệu EMBER2018 đã làm thật

Theo yêu cầu dọn thư mục, nguồn JSONL đã chuyển từ `ember2018` ở gốc Project sang `data/ember2018`. Cả tám file giữ nguyên tên, kích thước và thời gian sửa. CLI, README và test dùng đường dẫn mới; các manifest/checksum lịch sử không sửa. `data/ember2018_relocation.json` ghi đường dẫn trước/sau để tra nguồn cũ. Mảng đã chuẩn bị vẫn ở `data/ember2018_full`.

Đã xác minh checksum sáu array của `data/ember2018_full`, tái sử dụng read-only, không vector hóa lại và không sửa split cũ. Namespace mới: `data/primary/EMBER2018/protocol_v2/roles.json` và `roles.npz`.

Split seed 17 là seed đầu trong danh sách đã duyệt. Các vai trò mới đúng ngân sách và không trùng source SHA. Ref/cal chỉ lấy từ official train; final chỉ lấy official test. Registry loại 84.586 ID đã biết từ historical pilot pools, development partitions và evaluation CSV local. Không thể bảo đảm tuyệt đối chưa ai xem vì gói bạn phụ trách baseline vẫn thiếu source IDs.

Pilot sạch mới chỉ train trên 40.000 hàng cân bằng lấy trong fit mới, seed 17; dùng các tham số model đang có để đo tài nguyên: 500 rounds, 64 leaves, 4 threads. Không dùng selection/development/confirmation/ref/cal/final để train hoặc đánh giá pilot này. Training mất **52,50 giây**; whole-process peak working set **1.474,53 MiB (~1,44 GiB)**, peak pagefile 1.872,19 MiB. Đo này không dự báo tuyến tính chi phí fit 200.000 hay toàn ma trận.

Evidence: `outputs/primary_resource/EMBER2018/seed_17/resource.json`, model `clean_resource_only.txt`. Model này chỉ đo tài nguyên; không gọi là main clean model của nghiên cứu, không tạo ASR hoặc kết quả detector từ nó.

## 5. Bước EMBER2024 đã làm thật

Đã đọc metadata nguồn chính thức, khóa revision dataset `3d23efef7c0f0b702c5024400cfff4c3744a3832` và checksum sáu archive PE trong `configs/ember2024_sources.json`. Tổng file nén khoảng 23,10 GB theo metadata đã đọc. Để tránh nhân đôi dung lượng raw, preparation sẽ đọc JSONL trực tiếp trong ZIP, không giải nén toàn bộ dataset.

Đã tải riêng `Dot_Net_train.zip`: 937.108.923 bytes; checksum khớp manifest. Archive có 52 tuần, tổng raw bên trong 4.487.176.033 bytes. Con số này đo từ ZIP thật; không dùng bảng kích thước README như bảo đảm dung lượng thực tế.

Đã chấm kiểm tra schema trên 104 raw record đầu, hai record mỗi tuần, **không dùng model**. Tất cả vector float32 hữu hạn, đủ 2.568 chiều, fields General/Header được đối chiếu với raw. Labels/tags/AV metadata không nằm trong X. Các ID probe được lưu để loại khỏi vai trò đánh giá độc lập mới.

Evidence mới: `docs/reviews/V3_SCHEMA_AUDIT_2026_10_06.json`. Đây chỉ là kiểm chứng extractor trên .NET train; chưa chuẩn bị đủ Win32/Win64/.NET, chưa có pilot tài nguyên V3 hay kết quả nghiên cứu V3.

Nguồn: [extractor đã pin](https://github.com/FutureComputing4AI/EMBER2024/blob/0ef753e81d98bf209f71b03cd331dfc190b5b54d/src/thrember/features.py), [categorical handling của upstream](https://github.com/FutureComputing4AI/EMBER2024/blob/0ef753e81d98bf209f71b03cd331dfc190b5b54d/src/thrember/model.py), [dataset repository](https://huggingface.co/datasets/joyce8/EMBER2024).

## 6. Selector, so sánh và dashboard

Selector signed conditioned đã được đối chiếu với class `CombinedShapSelector` trích nguyên từ source commit `7e3ba27fdc1db25d68ae74da334cf3bdd9eedf71`, bằng tám fixture không có score tie. Local adapter thêm quota view, lọc feature biến thiên ban đầu và tie theo index nhỏ hơn; đây là adaptation, không tái lập toàn paper/dataset V1. Cả hai selector có code nhưng chưa chạy development mới.

Evaluator primary dùng cùng main, source samples, ref/cal/config trong mỗi cặp. Nó kiểm tra model/ref/cal khớp, giữ eligible denominator cho post-defense ASR, báo count/Wilson, recall successful eligible, benign FPR, AUROC và bootstrap paired full-minus-reduced. Chỉ evaluator nhận clean model/control và IDs. Không pair file hai dataset hoặc coi ID lặp qua seed là mẫu độc lập.

Dashboard đã có chọn dataset, nhận bundle đúng schema/protocol và hiển thị riêng malware prediction với backdoor alert. V3 thiếu bundle hiện Not ready. PE extraction V3 chưa xác thực thì từ chối. Không cảnh báo không chứng nhận file an toàn.

CLI mới: `schema`, `split-primary`, `resource-pilot`, `calibrate-primary`; `score` có thể yêu cầu dataset/schema. Các lệnh `prepare/split/run/develop-attack` cũ vẫn là workflow legacy V2; **không dùng `run --config configs/research.json` để chạy scope mới**. Chưa có CLI orchestration development/confirmation/main matrix primary.

## 7. Kiểm chứng và việc tiếp theo

Đã chạy `python -m pytest -q` trong `.venv`: **41 passed**, các warning hiện tại là deprecation từ thư viện plotting/UI. Bao gồm synthetic V2/V3 full/reduced, công thức và zero mass, mean entropy, repeat/order/batch STRIP, calibration ties/overlap, bundle round-trip/mismatch/checksum, poison denominator/geometry, disjoint train/test roles, nguồn selector, fixed eligible denominator và legacy/dashboard regression. Các fixture train nhỏ là kiểm tra code, không tính như thí nghiệm nghiên cứu.

Chưa có Docker executable trong terminal nên chưa build/run container. Không thay dependency hoặc cài Docker trong bước này.

Phần cần tiếp tục: preparation streaming PE V3 và audit ID trùng hai dataset; đo pilot V3; CLI primary development với lock/source snapshots/resume; so hai selectors trên development của cả hai bộ; khóa selector chung; confirmation mới; main training/calibration/final evaluation và báo cáo chung; cuối cùng Docker. Những lựa chọn nghiên cứu đã trả lời không cần hỏi lại. Nếu preparation phát hiện không đủ candidate/schema/resource hoặc cần đổi scope, hỏi trước bước phụ thuộc; tiếp tục các việc độc lập.
