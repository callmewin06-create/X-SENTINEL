# Hiểu và chạy X-SENTINEL từng bước

## 1. Bài toán thực sự

Model chính trả lời “malware hay benign?”. Detector trả lời “input có tín hiệu đáng nghi giống trigger không?”. Hai câu hỏi khác nhau: malware bình thường có thể không bị detector đánh dấu, và benign hiếm có thể bị đánh dấu. PASS không có nghĩa file an toàn.

## 2. Đối chiếu tài liệu trước khi code

METHOD_SPEC ghi các điểm thay đổi giữa báo cáo cũ, hướng dẫn thầy và handoff. Công thức trong handoff là cấu hình khởi đầu đã chốt, không phải kết quả. Không giữ các câu khẳng định baseline chắc chắn tốt hay chạy nhanh khi chưa đo. Bản full dùng view models chuẩn bị từ train sạch, nên có giả định dữ liệu bổ sung khác reduced.

## 3. Đọc JSONL và biến thành vector

Mỗi dòng EMBER chứa histogram, strings, header, imports và các nhóm khác; chưa phải 2.381 số cuối cùng. `data/vectorizer.py` chuẩn hóa histogram và dùng FeatureHasher theo upstream. Bản batch phải bằng tuyệt đối bản xử lý từng dòng trên mẫu thật. Mapping phủ 2.381 cột đúng một lần, kể cả datadirectories.

`prepare` đọc từng batch, ghi `.npy` dạng memory map, dùng SQLite kiểm tra ID trùng để không giữ hàng triệu ID trong RAM. Mẫu nhãn -1 bị loại. Official train/test giữ nguyên. Pilot lấy đầu mỗi shard nên không đại diện; chỉ dùng kiểm tra pipeline.

## 4. Tách tập benign trước khi thử detector

D1-reference xây phân bố/rank và làm nguồn STRIP. D1-calibration chọn ngưỡng. Final benign đo FPR thật. Ba phần không giao nhau; SHA256 và seed được lưu. Nếu dùng cùng một tập để vừa chọn chuẩn vừa báo kết quả, kết quả dễ lạc quan hơn thực tế.

## 5. Model sạch và attack

Train LightGBM sạch, sau đó chọn feature/value trigger từ train. Random benign train được gắn trigger nhưng nhãn vẫn 0. Poison rate tính trên toàn bộ số mẫu train có nhãn. Model đầu độc train trên tập đó. Malware final test được model sạch phát hiện đúng tạo mẫu số ASR; model sạch không đi vào detector.

Mã Severi gốc dùng v1 2.351 cột và danh sách feasible không có Behavioral hash. Vì vậy T-cross ba view và T-spread 24 Metadata cần profile `vector_stress`, khác profile `feasible`. Không thể gọi stress-test là đã chứng minh chỉnh được PE. Nếu ASR thấp, cần sửa/đánh giá attack bằng development từ train, không tối ưu bằng final test.

### 5.1. Kiểm chứng attack bằng development từ train

Lệnh `develop-attack` chỉ mở các file `*_train.npy`, không mở test, reference hoặc calibration. Nó lấy mẫu ngẫu nhiên phân tầng từ toàn bộ train thành ba phần cân bằng, không giao nhau:

1. **Fit: 40.000 mẫu.** Train model sạch và các model đầu độc; 0,5%/1%/2% nghĩa là đầu độc 200/400/800 mẫu benign, tính trên 40.000 mẫu fit.
2. **Selection: 5.000 mẫu.** Chọn hai cột Metadata feasible và giá trị trigger. So cách cũ chọn từng giá trị hiếm với cách thử nghiệm chọn cả cặp giá trị đã xuất hiện trên benign, hiếm và có tổng SHAP âm. Hai cách dùng cùng cặp cột để so việc chọn giá trị. Đây là adaptation, chưa phải tái lập đúng thuật toán Severi.
3. **Development: 10.000 mẫu.** Sau khi khóa các trigger và cấu hình, đo ASR trên malware được model sạch phát hiện đúng; đồng thời đo accuracy/TPR/FPR trên dữ liệu chưa gắn trigger.

Gắn cùng trigger vào malware rồi cho **model sạch** dự đoán là đối chứng quan trọng. Nếu model sạch cũng bị lừa nhiều, ASR cao của model đầu độc có thể chỉ phản ánh trigger gây né phân loại trực tiếp. Vì vậy báo cả ASR của hai model, số mẫu mới bị lừa, số mẫu hết bị lừa và chênh lệch trên cùng các malware eligible.

Quy tắc screening được định trước: ít nhất 1.000 malware eligible, ASR >=50%, mức tăng so đối chứng >=20 điểm phần trăm, accuracy/TPR giảm và FPR tăng không quá 2 điểm phần trăm. Đây là tiêu chí development do nhóm thử nghiệm, không phải tiêu chuẩn bắt buộc của bài Severi hoặc chứng minh backdoor. Không hạ tiêu chí sau khi thấy kết quả để biến run thất bại thành thành công.

Mỗi run có source snapshot, split/ID, config và model hash, danh sách poisoning, dự đoán từng mẫu và báo cáo tiếng Anh. Giữ nguyên run cũ; nếu sửa selector hoặc tăng cỡ mẫu/rounds, dùng config và thư mục mới, ghi rõ đó là vòng phát triển tiếp theo. Các kết quả development đã xem không còn là holdout độc lập để xác nhận lựa chọn cuối. Không dùng final test để chọn trigger hoặc chỉnh selector.

## 6. TADR và STRIP của baseline

SHAP là mức đóng góp vào raw margin lớp malware. `pred_contrib=True` trả thêm bias cuối; code bỏ bias và kiểm tra tổng khớp raw output. TADR lấy feature tuyệt đối lớn nhất chia tổng tuyệt đối. Tín hiệu chia đều trên nhiều feature có thể làm tỷ lệ này giảm; đó là giả thuyết.

STRIP trộn x với 50 benign reference: 0.5x+0.5r. Tính entropy nhị phân của từng lần dự đoán rồi lấy trung bình; score=1-H. Điểm cao nghĩa model ít bất định khi trộn. Random phụ thuộc nội dung vector và seed, không phụ thuộc nhãn/manifest, nên tái lập khi đổi thứ tự batch. Trộn vector có thể không tương ứng PE hợp lệ.

## 7. M3 và M4

M3 cộng tuyệt đối SHAP trong từng view rồi chia tổng. Khác TADR: nhiều feature nhỏ cùng view vẫn tạo tổng lớn. M4 reduced xét Behavioral SHAP kéo về malware trong khi model chính nghiêng benign: (1-p)*max(G_behavioral,0)/sum|phi|. Tổng view SHAP là đóng góp, không phải xác suất view.

M4 full dùng xác suất từ Behavioral classifier sạch: (1-p_main)*p_behavioral. Dashboard vẫn hiển thị cả ba xác suất view. M3 dùng SHAP model chính ở cả hai bản. View classifiers không trực tiếp dự đoán trigger.

## 8. M5 giới hạn, không thay đổi nghĩa âm thầm

Thầy có hai nhánh: import/string nhạy cảm khi main nói benign; hoặc quyết định benign phụ thuộc Metadata hiếm, ít liên quan bảo mật. Group-only vectors không xác nhận API cụ thể, nên nhánh đầu ghi unsupported.

Nhánh hai dùng printable-character distribution 515:611, khoảng [P1,P99] từ reference để xác định hiếm. Cộng riêng SHAP âm trên cột hiếm, chia toàn bộ SHAP âm. Chỉ kích hoạt khi main benign và tỷ trọng >80%. Như vậy có cả rarity, hướng kéo benign và mức chi phối, không phải chỉ outlier. Việc xem character distribution là ít đặc hiệu ngữ nghĩa vẫn là heuristic; cần báo limitation và ablation.

## 9. Kết hợp và khóa ngưỡng

Chuyển M3/M4/M5 thành rank so với reference rồi lấy trọng số bằng nhau. Ngưỡng được chọn riêng cho mỗi phương pháp trên calibration. Nếu n=2000, tối đa 20 score được phép lớn hơn tau; dùng order statistic và điều kiện strict `>` xử lý ties. Không chỉnh ngưỡng sau khi nhìn test. FPR calibration 1% không bảo đảm test 1%.

## 10. Đánh giá và hiểu kết quả

E0 xem phân bố với clean/poisoned model. E1 kiểm tra ASR và hiệu năng sạch. E2 AUROC trigger/benign, thêm trigger/malware để xem detector có chỉ phân biệt malware không. E3 lưu ID TADR bỏ sót nhưng M4 bắt và chiều ngược lại. E4 so reduced/full, có/không limited-M5. E5 đo FPR với Wilson CI, cohort entropy/size hiếm và latency từng file sau warm-up.

ASR sau defense vẫn dùng mẫu số eligible ban đầu. Recall trên toàn trigger khác recall chỉ trên attack thành công; báo cả hai. Bootstrap so hai phương pháp dùng cùng các mẫu được resample, giữ riêng từng seed. Không gọi cohort entropy cao là packed nếu chưa có ground truth.

## 11. Demo và đóng gói

Bundle mang main model, view models, reference/ranks, threshold/config và checksum. Bất kỳ model thay đổi làm bundle bị từ chối. Dashboard có đường vector đã kiểm chứng và PE experimental. PE chỉ parse, không chạy. Docker dùng CPU, volume data/model và giới hạn tài nguyên. Downloader chỉ dùng URL chia sẻ đã cấu hình, không tự đoán tài khoản Drive.

## 12. Đọc code theo thứ tự

`schema.py` → `data/vectorizer.py` → `data/prepare.py` → `attacks/trigger.py` → `attacks/development.py` → `baselines/scores.py` → `detection/detector.py` → `evaluation/metrics.py` → `experiment.py` → `dashboard/app.py`. Xem tests để biết quy tắc nào đã được kiểm tra. README chứa lệnh chạy và trạng thái thực tế nằm trong IMPLEMENTATION_STATUS.
