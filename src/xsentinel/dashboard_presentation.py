"""Vietnamese explanations derived only from measured detector outputs."""
METHOD_NAMES = {
    'X_primary_reduced': 'X-SENTINEL Reduced', 'X_primary_full': 'X-SENTINEL Full',
    'M3_view_mass': 'M3 · Tỷ trọng SHAP theo nhóm',
    'M4_shap_behavioral_conflict': 'M4-R · Bất đồng từ SHAP',
    'M4_prob_gap': 'M4-F · Chênh lệch dự đoán', 'TADR': 'TADR', 'STRIP': 'STRIP',
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
    return f'{size / 1024:.1f} KB' if size < 1024 * 1024 else f'{size / 1024 / 1024:.2f} MB'


def explain_result(result):
    selected = next(row for row in result['scores'] if row['Method'] == result['method'])
    # The displayed alert must agree with the selected score and strict threshold.
    if bool(selected['Score'] > selected['Threshold']) != bool(result['backdoor_alert']):
        raise ValueError('Selected score and alert disagree')
    malware = result['main_classification'] == 'MALWARE'
    alert = bool(result['backdoor_alert'])
    interpretations = {
        (False, False): 'Mô hình chính dự đoán file lành; điểm phát hiện chưa vượt ngưỡng. Kết quả này chưa chứng nhận file an toàn.',
        (False, True): 'Mô hình chính dự đoán file lành, nhưng điểm phát hiện bất thường vượt ngưỡng. Hai kết quả cần được xem xét cùng nhau.',
        (True, False): 'Mô hình chính dự đoán mã độc; phương pháp đang chọn chưa cảnh báo dấu hiệu trigger. Không có cảnh báo trigger không phủ nhận dự đoán mã độc.',
        (True, True): 'Mô hình chính dự đoán mã độc và phương pháp đang chọn cũng phát cảnh báo dấu hiệu trigger. Cảnh báo chưa chứng minh file chứa backdoor.',
    }
    descriptions = {
        'X_primary_reduced': 'Reduced ghép M3 và M4-R bằng thứ hạng trên mẫu reference lành rồi lấy trung bình. M4-R dùng SHAP của chính mô hình đang kiểm tra.',
        'X_primary_full': 'Full ghép M3 và M4-F bằng thứ hạng trên mẫu reference lành rồi lấy trung bình. M4-F dùng thêm mô hình sạch theo nhóm Behavioral.',
        'M3_view_mass': 'M3 đo tỷ trọng SHAP tuyệt đối của nhóm có ảnh hưởng lớn nhất đến mô hình chính.',
        'M4_shap_behavioral_conflict': 'M4-R kết hợp dự đoán nghiêng về lành với tổng SHAP Behavioral dương; tổng dương đẩy raw margin về mã độc.',
        'M4_prob_gap': 'M4-F đo phần chênh lệch dương giữa dự đoán mã độc của mô hình Behavioral sạch và mô hình chính.',
        'TADR': 'TADR đo tỷ trọng SHAP tuyệt đối tập trung ở một đặc trưng mạnh nhất.',
        'STRIP': 'STRIP dùng 1 trừ entropy nhị phân trung bình khi trộn vector với mẫu reference. Các vector trộn chưa chắc tương ứng file PE hợp lệ.',
    }
    signal_lines = []
    contributions = result.get('view_contributions') or {}
    if result['method'].startswith('X_primary') and contributions:
        view = max(contributions, key=contributions.get)
        signal_lines.append(f"M3: nhóm ảnh hưởng nhiều nhất là {VIEW_NAMES.get(view, view)}, chiếm {100*contributions[view]:.2f}% SHAP tuyệt đối.")
        component = 'M4_prob_gap' if result['method'] == 'X_primary_full' else 'M4_shap_behavioral_conflict'
        row = next((r for r in result['scores'] if r['Method'] == component), None)
        if row is not None:
            signal_lines.append(f"{method_name(component)}: điểm thành phần {row['Score']:.6f}.")
    return {'classification': 'Dự đoán mã độc' if malware else 'Dự đoán lành',
            'alert': 'Có cảnh báo' if alert else 'Chưa cảnh báo', 'interpretation': interpretations[malware, alert],
            'selected': selected, 'method_label': method_name(result['method']),
            'threshold_explanation': 'Điểm vượt ngưỡng nên có cảnh báo.' if alert else 'Điểm chưa vượt ngưỡng nên chưa có cảnh báo.',
            'method_explanation': descriptions.get(result['method'], 'Phương pháp thuộc bundle đang chọn; xem phiên bản và bảng điểm tại chi tiết nghiên cứu.'),
            'signal_lines': signal_lines}


def friendly_error(error):
    text = str(error)
    if 'exceeds' in text or '50 MiB' in text:
        return 'File vượt giới hạn 50 MB. Hãy chọn file nhỏ hơn.'
    if 'MZ' in text or 'PE signature' in text or 'parse' in text or 'LIEF' in text:
        return 'Không đọc được cấu trúc PE của file. Hãy kiểm tra định dạng .exe, .dll hoặc .sys.'
    if 'finite' in text or 'schema' in text.lower() or 'dataset mismatch' in text or 'columns' in text or 'one vector' in text:
        return 'Dữ liệu không khớp bộ mô hình. Kiểm tra dataset, số chiều và các giá trị của đầu vào.'
    if 'API' in text or 'reach' in text or 'Database' in text:
        return 'Chưa xác nhận lưu được kết quả. Kiểm tra API/database rồi thử lại; hệ thống không tự chuyển sang lưu local.'
    return 'Không thể hoàn thành phân tích. Hãy kiểm tra đầu vào và cấu hình; chi tiết kỹ thuật nằm bên dưới.'
