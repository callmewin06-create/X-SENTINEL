# Hướng dẫn BODMAS trên máy ảo Kali Linux

X-SENTINEL • Bản bàn giao ngày 19/10/2026

## 1. Làm việc này để trả lời điều gì?

Mục tiêu là kiểm tra đường đi **file PE → đọc đặc trưng → model đã khóa → dự đoán và cảnh báo**, trên một phần dữ liệu được thầy cấp. Bạn phụ trách chỉ đọc file để phân tích tĩnh; không chạy malware, không sửa header để khôi phục khả năng chạy và không tạo trigger mới trong file.

Nói thẳng: có file malware thật không tự động giải quyết được giới hạn số 3. Nếu mẫu đã bị vô hiệu hóa (disarmed), kết quả chỉ chứng minh hệ thống xử lý những byte được cấp. Muốn chứng minh malware vẫn hoạt động sau khi cấy trigger là một thí nghiệm khác, chưa nằm trong hướng dẫn này.

Gói này giữ bốn bundle cố định: EMBER2018/EMBER2024, mỗi tập có Reduced/Full, seed 17, spread_structural, tỷ lệ đầu độc 0.02. Đây là bốn cấu hình kiểm tra, không phải toàn bộ ma trận nghiên cứu. Shadow không có trong lượt kiểm tra này. Công cụ đi kèm đang ở mức thử nghiệm, chưa được xác nhận chạy trọn luồng; phải qua bước thử file lành trước khi dùng cho BODMAS.

## 2. Chuẩn bị trước khi đưa dữ liệu vào

Đề xuất VM: 4 vCPU, RAM 8 GB nếu máy thật đáp ứng; dung lượng phải tính theo archive và phần giải nén thực tế. Đây là cấu hình đề xuất, chưa phải kết quả đo trên máy bạn. Container được giới hạn 2 CPU/4 GB RAM. Không hứa một mức dung lượng cố định sẽ đủ cho archive 67,9 GB.

Máy ảo vẫn chiếm ổ đĩa máy thật. Nếu tải cả archive vào VM, máy thật vẫn cần đủ chỗ cho archive, phần đã giải nén, Docker image và kết quả. Cách hợp lý là xin thầy hoặc người giữ dữ liệu tách một phần nhỏ từ trước; nếu dịch vụ lưu trữ cho phép, lấy riêng những file đã chọn.

Trước khi nhận mẫu: cập nhật Kali, cài Docker và build image khi còn mạng; tạo snapshot VM sạch. Sau khi nhận mẫu: tắt shared folders, kéo thả và clipboard chia sẻ với máy thật; không gắn USB hoặc ổ máy thật chứa dữ liệu cá nhân vào VM. Các tùy chọn container bên dưới giảm quyền truy cập; parser vẫn là phần mềm xử lý dữ liệu không tin cậy nên lớp VM vẫn cần thiết.

Không đưa archive/mẫu vào GitHub, Google Drive công khai hoặc gói kết quả gửi lại. Chỉ dùng dữ liệu đúng phạm vi thầy và nhóm nghiên cứu cho phép. Nếu chưa rõ quyền chia sẻ, gửi kết quả CSV/JSON thay cho mẫu.

## 3. Nhận và kiểm tra gói công cụ

Chuyển **BODMAS_VM_2026_10_19.zip** vào thư mục Downloads của Kali. Đây là gói công cụ và model, không chứa malware BODMAS. Tên thư mục giải nén là X_SENTINEL_BODMAS_VM. Mở Terminal của Kali; mỗi khối lệnh chạy theo thứ tự. Nếu thiếu unzip hoặc python3, cài trước bằng `sudo apt update` rồi `sudo apt install -y unzip python3`.

```bash
cd "$HOME/Downloads"
unzip BODMAS_VM_2026_10_19.zip
cd X_SENTINEL_BODMAS_VM
python3 scripts/bodmas_verify_kit.py
```

Phải thấy `status: OK`. Nếu FAIL, dừng và gửi tên file lỗi cho người chuẩn bị gói. Kiểm kê hash giúp phát hiện file thiếu/bị đổi so với gói; nó không thay chữ ký xác thực nguồn gửi. Đối chiếu SHA-256 của ZIP với file SHA256SUMS do người gửi bàn giao riêng nếu cần.

Từ đây, **mọi lệnh chạy tại thư mục X_SENTINEL_BODMAS_VM**, trừ khi có ghi khác. Nếu đóng Terminal, quay lại bằng:

```bash
cd "$HOME/Downloads/X_SENTINEL_BODMAS_VM"
```

## 4. Cài Docker và build khi còn mạng

Theo hướng dẫn chính thức của Kali, dùng package docker.io. Không thêm kho Ubuntu vào Kali. Đây là bước cài phụ thuộc; chưa đọc mẫu BODMAS.

```bash
sudo apt update
sudo apt install -y docker.io unzip python3
sudo systemctl enable docker --now
sudo docker version
sudo docker build -t xsentinel-bodmas:20261019 .
sudo docker image inspect xsentinel-bodmas:20261019 > image_inspect.json
```

Nếu thiếu lệnh docker sau khi cài, kiểm tra thông báo APT/package của bản Kali đang dùng; gửi nguyên lỗi trước khi tự thêm kho hoặc đổi phiên bản thư viện. Image dùng các phiên bản thư viện đã pin trong dự án. Không tự nâng LIEF/LightGBM để chữa lỗi đọc một file.

Build xong có thể ngắt card mạng VM. Mỗi lượt chấm điểm còn có `--network none`, thư mục mẫu/model chỉ đọc, không mở cổng và không kết nối database. Gói không cần Docker Desktop, Compose, PostgreSQL hoặc file .env.

## 5. Tạo nơi chứa mẫu và thử đường chạy bằng file lành

Lưu mẫu/kết quả ngoài thư mục build. Lệnh export cần chạy lại nếu mở Terminal mới. Biến này là thư mục làm việc, không thay biến HOME của hệ thống.

```bash
export BODMAS_WORK_ROOT="$HOME/xsentinel-bodmas-work"
mkdir -p "$BODMAS_WORK_ROOT/samples/smoke"
mkdir -p "$BODMAS_WORK_ROOT/samples/malware"
mkdir -p "$BODMAS_WORK_ROOT/samples/benign"
mkdir -p "$BODMAS_WORK_ROOT/results"
cp fixtures/ReviewedBenignFixture.exe "$BODMAS_WORK_ROOT/samples/smoke/"
bash scripts/bodmas_run_static.sh catalog
bash scripts/bodmas_run_matrix.sh smoke smoke1 1 benign "self-built reviewed fixture"
```

File EXE đi kèm là chương trình lành do dự án tự biên dịch, có mã nguồn C# và hash trong fixtures. Lượt này chỉ đọc EXE. Không gọi Wine, Mono hay mở EXE để chạy.

Mỗi bundle phải tạo đủ ba file trong thư mục kết quả: manifest.json, results.csv, summary.json. Lệnh có thể in cảnh báo parser; đọc scan_status và error trong CSV để phân biệt cảnh báo với lỗi. Cả bốn lượt dùng cùng một manifest chọn file.

Đừng yêu cầu model bắt buộc dự đoán BENIGN mới gọi là smoke test thành công. Một mẫu lành có thể bị báo nhầm; mục tiêu ở bước này là xác nhận đường đọc/chấm/ghi kết quả hoạt động. Dự đoán sai vẫn phải giữ lại. Nhãn thật lấy từ nguồn file, không lấy từ câu trả lời của model.

## 6. Chuẩn bị phần BODMAS được cấp

Chưa có archive thực tế để kiểm tra cấu trúc, mật khẩu hay định dạng nén. Tên trong ảnh chỉ gợi ý đây là bản disarmed; cần đối chiếu metadata/tài liệu của thầy, không coi tên file là bằng chứng đầy đủ.

Mở archive bằng Archive Manager **để xem danh sách**, không nhấp chạy file bên trong. Nếu có mật khẩu, nhập trong hộp thoại của công cụ; xin thầy riêng, không ghi mật khẩu vào lệnh, báo cáo hay lịch sử Terminal. Nếu công cụ không hỗ trợ kiểu nén, ghi lỗi và dùng công cụ giải nén phù hợp trong VM; không đổi byte/header mẫu để “sửa lỗi”.

Ưu tiên một phần nhỏ được thầy tách sẵn. Nếu phải tự chọn từ archive, chốt quy tắc trước khi chạy model: ví dụ sắp đường dẫn theo thứ tự tên và lấy 200 mẫu đầu, hoặc lấy theo danh sách ID đã bốc thăm có seed. Ghi rõ đây là cách chọn thực tế. Lấy 200 file ở một thư mục đầu archive không cho phép gọi là ngẫu nhiên trên toàn BODMAS.

Giải nén **chỉ phần đã chọn** vào samples/malware của thư mục làm việc. Giữ tên file gốc; có thể giữ thư mục con. Không đặt ZIP, metadata, README, CSV hoặc ảnh trong thư mục đầu vào vì helper có thể chọn chúng rồi báo lỗi không phải PE. Không giải nén toàn bộ chỉ để lấy vài mẫu.

Tạo file ghi chú riêng selection_notes.md ở thư mục làm việc, ghi tối thiểu:

- Nguồn: thầy cấp, tên archive, ngày nhận, mô tả disarmed từ tài liệu nguồn.
- Quy tắc chọn, tổng số file trong phần nhận được và số file sẽ chấm; đánh dấu pilot hay lượt chính.
- ID/nhãn gốc theo metadata và nguồn xác nhận nhãn; không tự suy nhãn theo tên đuôi.
- Nếu có: hash archive, phiên bản dữ liệu và việc vô hiệu hóa đã được mô tả ra sao.
- Cấu hình VM/Kali, Docker image ID, lỗi giải nén hoặc file bị thiếu.

Hash file disarmed có thể khác hash malware gốc trong metadata. Ghi cả ID gốc và hash byte thực tế nếu đối chiếu được; nếu không khớp, ghi chưa xác minh thay vì khẳng định là cùng một bản byte. Helper chỉ lưu nhãn bạn khai báo, không tự xác nhận nhãn từ metadata.

## 7. Chạy pilot rồi lượt kiểm tra chính

Đề xuất pilot 20 mẫu, sau đó lượt chính tối đa 200 malware và 50 file lành nếu có nguồn hợp lệ. Đây là mức khởi đầu cho kiểm tra bổ sung, không đủ để tuyên bố đại diện toàn bộ hệ sinh thái malware.

Đầu tiên, chạy trên 20 file được helper chọn với seed 17 từ thư mục đầu vào hiện có:

```bash
bash scripts/bodmas_run_matrix.sh malware pilot20 20 malware "teacher-supplied BODMAS; see selection_notes.md"
```

Nếu nhãn/nguồn chưa đối chiếu được, thay đối số malware sau số 20 bằng unknown, và ghi nguồn đúng tình trạng. Chữ malware đầu tiên là tên thư mục, không phải nhãn; đối số sau số lượng mới là nhãn khai báo.

Đọc CSV, kiểm tra schema, số file, lỗi và cả bốn bundle. Nếu cần sửa công cụ sau pilot, lưu phiên bản và lý do; không lặng lẽ bỏ file lỗi rồi tuyên bố parser xử lý hết. Không sửa model/ngưỡng để làm đẹp kết quả BODMAS.

Khi đường chạy ổn, giữ nguyên bộ file đã chốt và chạy lượt chính với tên mới:

```bash
bash scripts/bodmas_run_matrix.sh malware bodmas200 200 malware "teacher-supplied BODMAS; see selection_notes.md"
```

Lệnh chọn tối đa số lượng yêu cầu; nếu thư mục chỉ có 83 file thì không được báo đã thử 200. Từng bộ bốn lượt dùng lại manifest của 2018-reduced, kiểm tra hash trước khi chấm các bundle còn lại. Không thêm/đổi file trong lúc chạy. File thay đổi so với manifest được ghi changed_since_manifest; thay đổi ngay trong lúc đọc được ghi input_changed.

Cho mẫu lành có nguồn kiểm chứng vào samples/benign. Giữ source/giấy phép/hash ở ngoài thư mục đầu vào. Không lấy 50 bản sao của cùng một EXE để giả thành 50 mẫu độc lập.

```bash
bash scripts/bodmas_run_matrix.sh benign benign50 50 benign "reviewed benign sources; see selection_notes.md"
```

Nếu chỉ có một fixture đi kèm thì ghi đúng một mẫu; chưa có đủ benign thì hoãn kết luận về tỷ lệ báo nhầm. Thiếu dữ liệu là giới hạn, không phải lý do để tự gán nhãn.

Mã thoát: 0 = mọi file được chấm thành công; 1 = chạy xong nhưng có file lỗi, vẫn có kết quả cần đọc; từ 2 trở lên = lỗi cấu hình/container, cần xử lý trước khi chạy tiếp. Không dùng `|| true` để che lỗi. Tên lượt đã tồn tại sẽ bị từ chối; đổi tên, không xóa kết quả cũ.

## 8. Đọc ba file đầu ra

manifest.json là danh sách file được chọn và hash trước dự đoán. results.csv là từng file và từng lỗi. summary.json tổng hợp đúng lượt chạy, không tự gọi đây là accuracy hoặc backdoor recall.

| Cột/nhóm | Hiểu đơn giản | Đừng hiểu nhầm |
| --- | --- | --- |
| relative_path, file_sha256 | File nào, byte thực tế nào đã đọc | Hash không tự chứng minh file là malware |
| declared_label, label_source | Nhãn và nguồn do người chạy khai | Không phải nhãn helper đã xác minh độc lập |
| scan_status, error_code, error | Chấm được hay lỗi ở đâu | File lỗi không được biến mất khỏi tổng số |
| schema, extractor, bundle_id | Đúng bộ đọc và model nào | Vector 2381 và 2568 không thay thế nhau |
| malware_probability, main_classification | Model chính nghi file độc đến mức nào | Không phải xác suất đã được hiệu chỉnh cho BODMAS |
| method, score, threshold, trigger_alert | Điểm nghi ngờ trigger và việc vượt ngưỡng | Cảnh báo không xác nhận có backdoor thật |
| extraction_ms, prediction_ms, file_total_ms | Thời gian phần đọc và phần chấm được đo | Không phải latency API/upload/database |

Muốn xem nhanh một lượt, mở summary.json và results.csv bằng trình soạn thảo/LibreOffice trong VM; không mở file mẫu. Có thể in summary bằng:

```bash
python3 -m json.tool "$BODMAS_WORK_ROOT/results/bodmas200_2018_reduced/summary.json"
```

Với bộ chỉ có malware, hãy báo: tổng file đã chọn, số đọc/chấm được, số lỗi; trong số chấm được có bao nhiêu bị classifier gọi MALWARE, bao nhiêu có cảnh báo trigger. Ghi rõ mẫu số của mỗi tỷ lệ. Một malware bị classifier gọi MALWARE nhưng không có cảnh báo trigger có thể hoàn toàn bình thường: mẫu đó chưa được chứng minh mang trigger của nhóm.

Với bộ lành đã xác minh nguồn, tách hai loại báo nhầm: classifier gọi MALWARE và detector báo nghi trigger. Không gộp chúng thành một con số. Các ngưỡng khóa được hiệu chỉnh trên dữ liệu cũ; không mặc định BODMAS/file lành mới cũng có FPR 1%.

EMBER2018 dùng bộ đọc V2 với LIEF hiện tại, chưa chứng minh trùng hoàn toàn với bộ đọc cũ trên cùng binary. V3 có bộ đọc upstream được pin nhưng chưa có bằng chứng khớp binary gốc toàn tập. Vì thế vẫn phải giữ các giới hạn parser và khác biệt dữ liệu trong báo cáo.

## 9. Lỗi thường gặp và cách xử lý

| Hiện tượng | Xử lý |
| --- | --- |
| Không có Docker daemon | Chạy lại systemctl ở bước 4; giữ nguyên lỗi nếu vẫn thất bại |
| Không tìm thấy image | Build khi có mạng trước; wrapper cố ý không tự tải image lúc chấm |
| Permission denied khi ghi kết quả | Kiểm tra thư mục results thuộc user Kali, không đặt trong shared folder; không chmod 777 toàn ổ |
| Bundle/schema không hợp lệ | Kiểm kê lại gói; không đổi tên bundle.json hoặc cắt vector để ép chạy |
| Không phải PE, quá 50 MiB hoặc parse lỗi | Giữ dòng lỗi và hash; đối chiếu mẫu/metadata, không tự sửa header |
| Container hết RAM hoặc bị dừng | Giữ log và kết quả dở; giảm số mẫu pilot nếu cần, kiểm tra RAM VM, chạy lại tên mới |
| Chạy lại báo output exists | Dùng tên lượt mới; bản cũ là bằng chứng cần giữ |

Nếu lệnh matrix dừng giữa chừng, ba file đầu ra có thể chưa hoàn tất ở lượt bị dừng. Đánh dấu incomplete, không cộng nó như một lượt chạy xong. Gửi lỗi nguyên văn và tên lượt; không gửi malware ra ngoài VM để nhờ kiểm tra.

## 10. Bàn giao và demo trước lớp

Bạn phụ trách gửi lại: selection_notes.md, image_inspect.json, cấu hình VM, toàn bộ thư mục results của các lượt hoàn tất và log lỗi. Không gửi raw malware trong ZIP kết quả. Người tổng hợp kiểm tra các lượt có cùng manifest/hash và nguồn nhãn trước khi đưa số vào report.

Demo dùng 2–3 file lành có nguồn và 2–3 mẫu disarmed được phép dùng, đã thử trước với đúng bundle trên máy demo. Đây là bộ minh họa được chọn có chủ đích; không lấy tỷ lệ đúng của vài file làm độ chính xác nghiên cứu. Có thể dùng một mẫu malware nguồn thật ở dạng disarmed để đọc tĩnh; không cần chạy malware trước lớp.

Giữ riêng phần demo vector có trigger nếu muốn giải thích backdoor. Đừng gọi một file malware bình thường là mẫu đã cấy trigger. Chuẩn bị ảnh/CSV kết quả cùng hash làm dự phòng nếu môi trường lớp không chạy được; nói rõ đó là kết quả đã ghi trước.

Câu có thể ghi vào report: “Chúng tôi bổ sung kiểm tra tĩnh trên N mẫu BODMAS dạng disarmed được chọn theo [quy tắc]. Có A/N mẫu được xử lý thành công và B/N mẫu lỗi. Kết quả đánh giá khả năng xử lý binary và hành vi dự đoán/cảnh báo trên các mẫu này; không chứng minh tính hiện thực hoặc bảo toàn chức năng của trigger trên malware thực thi.” Thay N/A/B bằng số đã đo, không dùng số đề xuất trong hướng dẫn.

## Trạng thái và nguồn tham khảo

Tài liệu và công cụ được chuẩn bị cho Kali Linux. Chưa nhận archive BODMAS thực tế; chưa chạy nghiệm thu trên VM Kali của bạn; chưa có số đo BODMAS mới. Xem VALIDATION.md trong gói để biết kiểm tra nào đã thực hiện khi đóng gói. Không dùng hướng dẫn như bằng chứng thí nghiệm đã hoàn tất.

- BODMAS, mô tả dữ liệu và điều kiện chia sẻ: https://whyisyoung.github.io/BODMAS/
- Cài Docker trên Kali: https://www.kali.org/docs/containers/installing-docker-on-kali/
- Docker network none: https://docs.docker.com/engine/network/drivers/none/
- Quyết định của nhóm: docs/plans/QUYET_DINH_5_DIEM_2026_10_19.md trong dự án gốc.

Nguồn kỹ thuật được đối chiếu ngày 19/10/2026. Quyền sử dụng phần dữ liệu do thầy cấp vẫn cần theo thỏa thuận nguồn của nhóm.
