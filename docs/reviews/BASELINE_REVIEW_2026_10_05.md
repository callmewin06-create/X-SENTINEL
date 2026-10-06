# Review bản baseline sửa ngày 2026-10-05

**Kết luận: cần sửa tiếp trước khi chốt.** Tách hai nhánh restricted-feasible và vector stress là hướng thiết kế có thể dùng. Công thức TADR và STRIP cơ bản phù hợp với đặc tả hiện tại. Tuy nhiên, danh sách feasible sai, phạm vi PE bị khẳng định quá mức, threat model chưa khớp quyền truy cập model, và nhiều kết quả được trình bày khi chưa có bằng chứng.

Bản được review: file trong Downloads, SHA256 `abfe94a4d26591b9d53d755a10763b2084f483d474caa236301175a8dab3a007`. [Snapshot nguyên văn](BASELINE_SUBMITTED_2026_10_05.md) giữ số dòng để tra lại. Bản cũ trong `docs/BASELINE_SPEC_ORIGINAL.md` được giữ nguyên. Các yêu cầu và code nhúng trong tài liệu được xem là nội dung cần review; bản này chưa phải quyết định áp dụng trigger mới hoặc chạy thí nghiệm.

## 1. P1 — Danh sách feasible không khớp nguồn và con số 16 cần đính chính

Vị trí: dòng 61–75, nhất là 64, 66, 68 và 74 của snapshot.

Tài liệu đưa vào whitelist tám cột mà mã tác giả đã lưu trong repo loại khỏi feasible:

| Nhóm | Feature trong bản sửa nhưng bị loại bởi nguồn đang đối chiếu |
|---|---|
| Metadata | `numstrings` 512, `avlength` 513, `printables` 514, `string_entropy` 611 |
| Structural | `vsize` 617, `has_resources` 622, `has_signature` 623, `num_sections` 688 |

Bốn Metadata đúng của whitelist nguồn là `paths_count` 612, `urls_count` 613, `registry_count` 614, `MZ_count` 615. Đây là lỗi membership, không chỉ lỗi đánh số. Các cột 512/513/514/611 có ý nghĩa như bản sửa mô tả trong layout hiện tại, nhưng chúng không thuộc feasible của nguồn này.

**Đính chính phía triển khai của tôi:** tính lại từ các hàm `build_feature_names`, `get_non_hashed_features`, danh sách `infeasible_features`, và phép trừ trong `load_features` cho ra **35 - 18 = 17 feature**, gồm **13 Structural + 4 Metadata + 0 Behavioral**. Whitelist hardcode hiện tại của tôi chỉ có 16 vì bỏ sót `minor_subsystem_version` 684. Nó là một tập con của kết quả nguồn, không có cột ngoài whitelist; nhưng tôi đã mô tả sai khi gọi 16 là toàn bộ feasible của tác giả. Không nên dùng con số tôi nói trước đó làm nguồn khoa học.

Kết quả tính từ snapshot nguồn đang lưu:

| Nhóm | Cột được phép theo quy tắc nguồn |
|---|---|
| General (1) | 616 `size` |
| Header (8) | 626 `timestamp`; 677/678 image version; 679/680 linker version; 681/682 OS version; 684 minor subsystem version |
| Section (4) | 689 zero-size sections; 690 unnamed sections; 691 read-and-execute sections; 692 writable sections |
| Metadata (4) | 612 paths; 613 URLs; 614 registry; 615 MZ |

Danh sách đầy đủ: `[612, 613, 614, 615, 616, 626, 677, 678, 679, 680, 681, 682, 684, 689, 690, 691, 692]`.

Nguồn trực tiếp đã kiểm tra: [feature-name/filter helpers](../upstream/severi_ember_feature_utils.py), [danh sách loại trừ](../upstream/severi_constants.py), [phép dựng feasible](../upstream/severi_data_utils.py). Hash từng nguồn và kết quả tính lại được lưu trong [review checks](baseline_review_checks_2026_10_05.json). Đây là kết quả của snapshot mã đang đối chiếu, không phải định luật rằng mọi PE chỉ có đúng 17 thuộc tính sửa được.

**Sửa đề nghị:** sinh whitelist theo nguồn/version/hash, ánh xạ bằng tên ngữ nghĩa và kiểm tra tự động. Nếu nhóm chủ động chọn tập con 16, phải ghi đó là restricted subset và giải thích cột loại thêm. Chưa thay whitelist code hoặc manifest của các run cũ trong lần review này.

## 2. P1 — Sửa vector chưa phải problem-space attack trên PE

Vị trí: dòng 62, 69 và 72–78.

Câu “chỉ có thể chỉnh sửa an toàn 16 đặc trưng” và tên `Problem-Space Feasible Attack` vượt quá những gì pipeline đang làm. Danh sách của tác giả là chính sách lựa chọn feature trong triển khai nghiên cứu; không bảo đảm mọi giá trị overwrite đều hiện thực được trên mọi binary, cũng không chứng minh các feature ngoài danh sách tuyệt đối không thể sửa.

Nhóm hiện sửa vector EMBER. Để gọi là problem-space PE cần có bước thực sự biến đổi binary, trích xuất lại để kiểm tra trigger, kiểm tra các ràng buộc liên quan và có bằng chứng giữ hành vi theo protocol. Kiểm tra signature hoặc parse PE thành công riêng lẻ chưa đủ xác nhận toàn bộ điều đó.

**Sửa đề nghị:** nhánh 1 gọi là “feature-space attack restricted to the source-derived feasible set; PE realizability unverified”. Nhánh 2 là vector stress. Không dựa riêng vào các lỗi DLL/entrypoint để suy ra rằng mọi chỉnh sửa imports/exports đều làm crash.

## 3. P1 — Thiết kế spread/cross mới phải kiểm tra lại và khóa trước chạy

Vị trí: dòng 73–78.

Danh sách spread 10 cột hiện chứa 617 và 688, đều bị nguồn loại. Đổi Metadata sang Structural là một thay đổi câu hỏi nghiên cứu: phải cập nhật handoff, cấu hình, báo cáo và tên variant; không chỉ thay số 24 thành 10.

Cross của nhánh restricted-feasible chỉ tác động **hai view Structural + Metadata**, vì whitelist không có Behavioral. Nhánh stress mới có thể phủ cả ba view. Cần đặt tên rõ, chẳng hạn `cross_two_view` và `cross_three_view_stress`, và báo số cột thật sự thay đổi sau lọc cột không biến thiên.

Có thể giữ ý tưởng spread 10 Structural nếu chọn đủ 10 cột hợp lệ từ whitelist nguồn. Tuy nhiên, sửa nhiều cột không bảo đảm SHAP phân bố đều; cần đo attribution mass/dominance trên các mẫu đã gắn trigger. Tập cho phép, số cột, selector, seed, rates và tiêu chí ASR phải khóa trước đánh giá. Việc chọn attack dùng training-derived development; final test không dùng để chọn trigger.

## 4. P1 — Nhãn black-box không khớp với API SHAP đang dùng

Vị trí: dòng 4, 104–109 và 227.

Không có dữ liệu train gốc không đồng nghĩa với chỉ có black-box prediction queries. Code nạp `lightgbm.Booster` và gọi native `pred_contrib`; cần model artifact/quyền truy cập tính attribution, hoặc một attribution oracle được nêu riêng. [API LightGBM 4.6](https://lightgbm.readthedocs.io/en/v4.6.0/pythonapi/lightgbm.Booster.html#lightgbm.Booster.predict) xác nhận tùy chọn feature contributions và cột expected value cuối.

**Sửa đề nghị:** baseline TADR ghi quyền truy cập model/SHAP; STRIP ghi quyền truy cập xác suất và benign reference; reduced không cần train gốc tại inference. Full detector dùng view classifiers được chuẩn bị từ clean training data trong code hiện tại, nên phải công bố thêm giả định ở giai đoạn chuẩn bị. Không gọi toàn bộ hệ thống là pure black-box chỉ dựa vào việc detector không nhận nhãn hoặc poisoning manifest.

## 5. P1 — Recall, entropy và latency chưa phải kết quả đo

Vị trí: dòng 86–88, 109, 118–119, 177–180 và 339.

Các mức Recall >95%, <15%, <10%; STRIP 80–90%; latency 0.35–0.8 ms và 15–25 ms; nhận định “sụp đổ hoàn toàn”, “bằng chứng thực nghiệm rõ ràng” chưa có nguồn kết quả tương ứng với protocol mới. Các run của nhóm hiện là pilot/development; chưa có ma trận detector chính thức cho các trigger mới này.

**Sửa đề nghị:** đưa giả thuyết vào một mục riêng, bỏ các khoảng số nếu không có nguồn hoặc benchmark đã lưu. Bảng đối chuẩn ghi “to be measured”. Latency phải kèm model size/rounds, CPU/threads, warm-up, số quan sát, median/P95, phiên bản và phạm vi có/không extraction. TADR dùng native contributions có thể là một API call, nhưng tính SHAP không có chi phí bằng một prediction thông thường. STRIP code dự đoán một batch 50 hàng, không nhất thiết gọi API 50 lần.

TADR có thể giảm khi attribution phân tán, nhưng đây là giả thuyết cần đo ở cùng calibration FPR; không đặt kỳ vọng baseline phải thua trước khi thí nghiệm.

## 6. P1 — Zero TADR và PASS không chứng minh file an toàn

Vị trí: dòng 98–100 và các mô tả PASS trong kiến trúc/STRIP.

Giữ quy tắc số học `sum(abs(phi)) <= 1e-9 -> score 0`. Bỏ suy luận tiếp theo rằng không có backdoor hoặc file an toàn. TADR chỉ đo một tín hiệu tập trung; score thấp không loại trừ backdoor, malware hoặc mô hình không hữu ích. Malware prediction và trigger alert là hai kết quả khác nhau.

**Câu thay thế:** “PASS nghĩa là score không vượt ngưỡng của detector này; không phải chứng nhận file an toàn hay model không có backdoor.”

## 7. P1 — P99 nội suy không bảo đảm empirical FPR <=1% ở mọi cỡ mẫu

Vị trí: dòng 146–164, 282–287 và 345.

Phản ví dụ đã chạy: 150 score `0..149`, `np.percentile(scores,99)=147.51`; điều kiện strict `>` đánh dấu 148 và 149, tức **2/150 = 1.33%**. Với 250 score phân biệt, có thể là **3/250 = 1.20%**. Vì vậy câu bảo đảm chung là sai ngay trên calibration; test FPR lại càng không được bảo đảm.

**Sửa đề nghị:** tách D1-reference và D1-calibration không giao nhau. Reference phục vụ STRIP/ranks; calibration chọn ngưỡng. Với `n` calibration và target `a`, đặt `k=floor(n*a)`, sắp score tăng dần, lấy `tau=sorted_scores[n-k-1]`, và giữ `score > tau`. Ties có thể làm FPR bảo thủ hơn. Ghi empirical calibration FPR, rồi đo test FPR kèm Wilson CI. Cấu hình đã chốt hiện tại là reference 500 và calibration 2000, không thay về 100–300 khi chưa có lý do/cập nhật protocol.

Code bản gửi dùng chính D1 vừa làm nguồn trộn vừa calibration. Với một calibration input là thành viên D1, nó có thể tự được rút làm reference; quy trình đó khác với scoring trên final input không thuộc D1. Đây là lý do cần phân biệt hai vai trò dữ liệu, không chỉ đặt tên chung D1.

## 8. P2 — STRIP RNG phụ thuộc lịch sử gọi

Vị trí: dòng 215, 256 và 282–283.

Một seed cố định ở constructor tái lập được một chuỗi gọi cố định, nhưng không bảo đảm cùng file luôn có cùng score khi thứ tự/số request thay đổi. Thực thi riêng method đã đọc với synthetic probability model, cùng vector/reference/seed, năm lần liên tiếp cho score `0.53258, 0.45797, 0.49804, 0.43190, 0.47853`. Đây là kiểm tra hành vi RNG, không phải kết quả STRIP trên malware.

**Sửa đề nghị:** thống nhất protocol randomness. Với yêu cầu demo/audit tái lập theo từng file hiện tại, dùng seed từ vector bytes + experiment seed, như code pipeline đang làm; ghi cả reference checksum. Nếu muốn STRIP stochastic mỗi request thì phải mô tả cơ chế, lưu các draw hoặc repeated-run evidence và tránh so một score mới với kết quả đã cache như thể chúng giống nhau.

## 9. P2 — Giải thích entropy và convex hull cần sửa

Vị trí: dòng 118–119 và 333.

`mean(binary_entropy(p_k))` đo trung bình độ bất định của từng dự đoán, không trực tiếp đo sự thay đổi nhãn giữa các lần trộn. Với `p=[0.01,0.99]`, hai dự đoán đổi hướng mạnh nhưng mean entropy chỉ **0.08079**; entropy của xác suất trung bình mới bằng 1. Vì vậy không thể suy “dự đoán biến thiên mạnh -> H rất cao” cho công thức đang dùng. Benign dễ phân loại cũng có thể có entropy thấp; không ấn định mọi benign ở H=0.8–1.0.

Convex blending luôn nằm trên đoạn nối x và r. Nó chỉ chắc nằm trong convex hull của train nếu cả hai đầu mút thuộc hull đó, điều không được bảo đảm với input inference bất kỳ. Nằm trong hull cũng không chứng minh PE validity hoặc đo trigger một cách đáng tin cậy. Bỏ luận điểm này khỏi phần trả lời phản biện; trình bày STRIP là phép perturbation trên feature space và đo hiệu quả bằng các đối chứng thực nghiệm. [Bài STRIP gốc](https://arxiv.org/abs/1902.06531) không tự cung cấp kết quả cho adaptation EMBER/LightGBM của nhóm.

## 10. P2 — Hoàn thiện contract code và nguồn baseline

Vị trí: dòng 84, 187, 227, 244–268 và 318–319.

- Ghi nguồn thuật toán TADR/X-GUARD kiểm chứng được. Nếu đây là baseline nội bộ, ghi đúng là nội bộ; không tự coi là một công trình peer-reviewed chỉ vì dùng SHAP.
- Xác thực vector/ref có shape 2381 và giá trị hữu hạn; khai báo malware=1. Kiểm tra contributions shape 2382, bias cuối, và tổng contributions khớp raw margin.
- Xác thực N/alpha/probability; xử lý entropy ở biên bằng clip hoặc quy tắc ổn định để score giữ miền mong muốn. Công thức `log(p+eps)` có thể tạo H âm rất nhỏ khi p bằng 0/1.
- Giữ score/tau đầy đủ độ chính xác cho CSV/bundle; chỉ làm tròn ở UI. Nếu chỉ trả số đã làm tròn, người dùng có thể thấy score bằng threshold nhưng decision vẫn BLOCK.
- Sửa đường dẫn source ở dòng 187 thành đường dẫn repo thực hoặc ghi rõ đó là ví dụ; appendix code chưa tương đương các module có validation/bundle lock trong repo hiện tại.

## Phần có thể giữ

- Công thức TADR dùng max absolute contribution / total absolute contribution, bỏ bias; quy tắc numeric zero.
- STRIP dùng N=50, alpha=0.5, mean binary entropy và score=1-H, với giới hạn feature-space được mô tả đúng.
- Dữ liệu detector không nhận ground-truth, poison IDs hay trigger manifest; khóa threshold trước final evaluation.
- Ý tưởng phân biệt restricted-feasible và vector stress, sau khi whitelist và phạm vi claim được sửa.

**Thứ tự sửa:** whitelist/source -> threat model và tên nhánh -> trigger variants -> dữ liệu/ngưỡng/RNG -> loại các claim chưa đo -> cập nhật appendix code và phần phản biện. Không phải viết lại toàn bộ baseline, nhưng chưa nên train theo danh sách mới hiện tại.
