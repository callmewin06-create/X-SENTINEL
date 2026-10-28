"""Vietnamese explanations derived only from measured detector outputs."""
METHOD_NAMES = {
    'X_primary_reduced': 'X-SENTINEL Reduced', 'X_primary_full': 'X-SENTINEL Full',
    'M3_view_mass': 'VMC · Tỷ trọng SHAP theo nhóm',
    'M4_shap_behavioral_conflict': 'BGS · Tín hiệu SHAP Behavioral',
    'M4_prob_gap': 'BPG · Chênh lệch dự đoán Behavioral', 'TADR': 'TADR', 'STRIP': 'STRIP',
}
VIEW_NAMES = {'structural': 'Structural · Cấu trúc PE', 'behavioral': 'Behavioral · Import/export',
              'metadata': 'Metadata · Byte và chuỗi'}
VIEW_HELP = {
    'structural': 'Header, section và thông tin cấu trúc của file PE.',
    'behavioral': 'Import/export liên quan API. Không phải hành vi quan sát khi chạy file.',
    'metadata': 'Thống kê byte, entropy và chuỗi trong file.',
}


def method_name(value):
    return METHOD_NAMES.get(value, value)


def format_size(size):
    return f'{size / 1024:.1f} KiB' if size < 1024 * 1024 else f'{size / 1024 / 1024:.2f} MiB'


def decision_numbers(value, threshold):
    if value != threshold and f'{value:.6f}' == f'{threshold:.6f}':
        return format(value, '.17g'), format(threshold, '.17g')
    return f'{value:.6f}', f'{threshold:.6f}'


def explain_result(result):
    selected = next(row for row in result['scores'] if row['Method'] == result['method'])
    # The displayed alert must agree with the selected score and strict threshold.
    if bool(selected['Score'] > selected['Threshold']) != bool(result['backdoor_alert']):
        raise ValueError('Selected score and alert disagree')
    malware = result['main_classification'] == 'MALWARE'
    p, malware_threshold = result.get('malware_probability'), result.get('malware_threshold')
    classification_explanation = 'Bản ghi cũ chưa lưu ngưỡng phân loại; không tự suy lại ngưỡng từ nhãn dự đoán.'
    if p is not None and malware_threshold is not None:
        if bool(p >= malware_threshold) != malware:
            raise ValueError('Classification and malware threshold disagree')
        relation = '≥' if malware else '<'
        shown_p, shown_threshold = decision_numbers(p, malware_threshold)
        classification_explanation = (f"Điểm phân loại {shown_p} {relation} ngưỡng {shown_threshold}, "
                                      f"nên mô hình dự đoán {'mã độc' if malware else 'lành'}.")
    alert = bool(result['backdoor_alert'])
    interpretations = {
        (False, False): 'Mô hình chính dự đoán file lành; điểm phát hiện chưa vượt ngưỡng. Kết quả này chưa chứng nhận file an toàn.',
        (False, True): 'Mô hình chính dự đoán file lành, nhưng điểm phát hiện bất thường vượt ngưỡng. Hai kết quả cần được xem xét cùng nhau.',
        (True, False): 'Mô hình chính dự đoán mã độc; phương pháp đang chọn chưa cảnh báo dấu hiệu trigger. Không có cảnh báo trigger không phủ nhận dự đoán mã độc.',
        (True, True): 'Mô hình chính dự đoán mã độc và phương pháp đang chọn cũng phát cảnh báo dấu hiệu trigger. Cảnh báo chưa chứng minh file chứa backdoor.',
    }
    descriptions = {
        'X_primary_reduced': 'Reduced ghép VMC và BGS bằng trung bình hạng tham chiếu lành. VMC đo mức tập trung SHAP theo nhóm; BGS kết hợp dự đoán nghiêng về lành với tổng SHAP import/export dương. Chế độ này không cần mô hình sạch bổ trợ. Trigger phân tán hoặc thích nghi đa view vẫn có thể vượt qua các tín hiệu này.',
        'X_primary_full': 'Full ghép VMC và BPG bằng trung bình hạng tham chiếu lành. BPG lấy phần chênh lệch dương khi mô hình Behavioral sạch nghiêng về mã độc hơn mô hình chính. Full cần thêm tài nguyên sạch; không có ưu thế phổ quát trước Shadow hoặc trigger thích nghi.',
        'M3_view_mass': 'VMC đo tỷ trọng SHAP tuyệt đối của nhóm có ảnh hưởng lớn nhất đến mô hình chính. Đây là M3_view_mass trong định danh bundle; mức tập trung không tự chứng minh có trigger.',
        'M4_shap_behavioral_conflict': 'BGS kết hợp (1 − p_mã_độc) với phần dương của tổng SHAP Behavioral, chia cho tổng SHAP tuyệt đối. Tổng SHAP có dấu được cộng trước khi lấy phần dương; đây là M4_shap_behavioral_conflict trong bundle.',
        'M4_prob_gap': 'BPG = max(0, p_Behavioral_sạch − p_mô_hình_chính). Đây là M4_prob_gap trong bundle; dự đoán sạch bổ trợ dùng đặc trưng import/export tĩnh.',
        'TADR': 'TADR đo tỷ trọng SHAP tuyệt đối tập trung ở một đặc trưng mạnh nhất.',
        'STRIP': 'STRIP dùng 1 trừ entropy nhị phân trung bình khi trộn vector với mẫu reference. Các vector trộn chưa chắc tương ứng file PE hợp lệ.',
    }
    signal_lines = []
    contributions = result.get('view_contributions') or {}
    if result['method'].startswith('X_primary') and contributions:
        view = max(contributions, key=contributions.get)
        signal_lines.append(f"VMC: nhóm ảnh hưởng nhiều nhất là {VIEW_NAMES.get(view, view)}, chiếm {100*contributions[view]:.2f}% SHAP tuyệt đối.")
        component = 'M4_prob_gap' if result['method'] == 'X_primary_full' else 'M4_shap_behavioral_conflict'
        row = next((r for r in result['scores'] if r['Method'] == component), None)
        if row is not None:
            signal_lines.append(f"{method_name(component)}: điểm thành phần {row['Score']:.6f}.")
    selected_relation = '>' if alert else '≤'
    shown_score, shown_alert_threshold = decision_numbers(selected['Score'], selected['Threshold'])
    return {'classification': 'Dự đoán mã độc' if malware else 'Dự đoán lành',
            'classification_explanation': classification_explanation,
            'alert': 'Có cảnh báo' if alert else 'Chưa cảnh báo', 'interpretation': interpretations[malware, alert],
            'selected': selected, 'method_label': method_name(result['method']),
            'threshold_explanation': (f"Điểm cảnh báo {shown_score} {selected_relation} ngưỡng {shown_alert_threshold}, "
                                      + ('nên có cảnh báo trigger.' if alert else 'nên chưa có cảnh báo trigger.')),
            'method_explanation': descriptions.get(result['method'], 'Phương pháp thuộc bundle đang chọn; xem phiên bản và bảng điểm tại chi tiết nghiên cứu.'),
            'signal_lines': signal_lines}


FEATURE_HELP = {
    'general.imports': ('Số hàm import', 'Số hàm được ghi nhận trong bảng import của file; không phải số API đã được gọi khi chạy.'),
    'header.optional.major_subsystem_version': ('Phiên bản chính của môi trường chạy', 'Một trường phiên bản trong PE header; không tự xác nhận hệ điều hành đang dùng.'),
    'header.optional.major_image_version': ('Phiên bản chính của image PE', 'Trường phiên bản do file khai báo trong PE header.'),
    'header.coff.timestamp': ('Mốc thời gian trong COFF header', 'Trường thời gian do file khai báo; có thể thiếu hoặc bị thay đổi, không phải bằng chứng thời gian tạo thật.'),
    'strings.MZ': ('Số chuỗi MZ được ghi nhận', 'Thống kê chuỗi ký tự MZ trong file; riêng giá trị này không chứng minh có file độc hại nhúng bên trong.'),
    'datadirectories.1.virtual_address': ('Địa chỉ tương đối của vùng dữ liệu PE số 1', 'Trường địa chỉ trong bảng data directory của PE, không phải địa chỉ mạng.'),
    'header.coff.characteristic.DLL': ('Cờ đánh dấu DLL', 'Giá trị 1 nghĩa là cờ DLL được bật trong header; riêng cờ này không xác nhận file lành.'),
    'strings.entropy': ('Độ đa dạng ký tự trong chuỗi', 'Thống kê phân bố ký tự trong các chuỗi tìm được; không tự chứng minh mã hóa hay mã độc.'),
    'section.max_entropy': ('Độ đa dạng byte lớn nhất trong một section', 'Section là một vùng trong file PE; giá trị này tóm tắt phân bố byte của vùng có entropy lớn nhất.'),
    'section.num_write_sections': ('Số section có cờ cho phép ghi', 'Đây là cờ cấu trúc tĩnh, không phải số lần file ghi dữ liệu khi chạy.'),
    'header.optional.checksum': ('Giá trị checksum trong PE header', 'Một trường số trong cấu trúc file; không phải kết luận xác thực chữ ký.'),
    'header.optional.subsystem': ('Mã loại môi trường chạy của PE', 'Mã được ghi trong PE header; đây là dữ liệu tĩnh.'),
    'authenticode.latest_signing_time': ('Mốc thời gian ký được bộ đọc trích xuất', 'Giá trị 0 là giá trị mặc định khi chưa trích được thời điểm; không đủ để kết luận file không có chữ ký.'),
    'datadirectories.EXPORT.size': ('Kích thước bảng export', 'Độ lớn vùng thông tin export được khai báo trong file PE.'),
}


def feature_rows(result):
    rows = []
    for item in result.get('top_features', []):
        name = item['Feature name']
        if name.startswith('header.characteristics_hash_'):
            default = ('Ô tổng hợp cờ đặc tính PE #' + name.rsplit('_', 1)[-1], 'Các cờ trong header được gộp bằng phép băm; giá trị ô không cho biết riêng một cờ cụ thể.')
        elif name.startswith('strings.printabledist_'):
            default = ('Tỷ trọng ký tự in được, ô #' + name.rsplit('_', 1)[-1], 'Một phần của thống kê phân bố ký tự trong chuỗi; không phải mức nguy hiểm của file.')
        elif name.startswith(('imports.function_hash_', 'import_libraries.hash_')):
            default = ('Ô tổng hợp thông tin import #' + name.rsplit('_', 1)[-1], 'Thông tin tên hàm/thư viện được gộp bằng phép băm. Không thể suy riêng tên API hay hành vi chạy từ ô này.')
        elif name.startswith('pefilewarnings.warning.'):
            default = ('Cờ cảnh báo cấu trúc từ bộ đọc PE', 'Giá trị ghi nhận cảnh báo của bộ đọc cấu trúc file. Một cảnh báo hoặc việc không có cảnh báo không tự xác nhận file độc hại/an toàn.')
        else:
            default = (name, 'Chưa có mô tả tiếng Việt đã kiểm chứng cho đặc trưng này.')
        title, help_text = FEATURE_HELP.get(name, default)
        shap = float(item['SHAP'])
        direction = 'Đẩy về mã độc' if shap > 0 else 'Đẩy về lành' if shap < 0 else 'Không có ảnh hưởng trong lần này'
        rows.append({'name': name, 'title': title, 'description': help_text,
                     'value': float(item['Feature value']), 'shap': shap, 'direction': direction})
    return rows


def friendly_error(error):
    code = getattr(error, 'code', None)
    if code == 'timeout':
        return 'Không phân tích được: đọc file quá thời hạn nên tác vụ đã dừng. Bạn có thể thử file khác; chưa có kết luận lành hay độc cho file này.'
    if code == 'worker_crashed':
        return 'Không phân tích được: tiến trình đọc file đã dừng bất thường. Bạn có thể thử file khác; chưa có kết quả cho file này.'
    if code == 'busy':
        return 'Đang đọc một file khác. Hãy chờ tác vụ đó hoàn tất rồi thử lại.'
    if code == 'invalid_output':
        return 'Không phân tích được: dữ liệu trả về từ bộ đọc không hợp lệ. Hệ thống chưa chấm điểm file này.'
    text = str(error)
    if 'exceeds' in text or '50 MiB' in text:
        return 'File vượt giới hạn 50 MiB. Hãy chọn file nhỏ hơn.'
    if 'MZ' in text or 'PE signature' in text or 'parse' in text or 'LIEF' in text:
        return 'Không đọc được cấu trúc PE của file. Hãy kiểm tra định dạng .exe, .dll hoặc .sys.'
    if 'finite' in text or 'schema' in text.lower() or 'dataset mismatch' in text or 'columns' in text or 'one vector' in text:
        return 'Dữ liệu không khớp bộ mô hình. Kiểm tra dataset, số chiều và các giá trị của đầu vào.'
    if 'API' in text or 'reach' in text or 'Database' in text:
        return 'Chưa xác nhận lưu được kết quả. Kiểm tra API/database rồi thử lại; hệ thống không tự chuyển sang lưu local.'
    return 'Không thể hoàn thành phân tích. Hãy kiểm tra đầu vào và cấu hình; chi tiết kỹ thuật nằm bên dưới.'
