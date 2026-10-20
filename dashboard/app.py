"""Vietnamese demo UI. Rendering saved explanations never reruns the detector."""
import hashlib
import html
import json
import os
from pathlib import Path
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import pandas as pd
import streamlit as st
from xsentinel.detection.detector import Detector
from xsentinel.dashboard_catalog import primary_catalog, experiment_label, preferred_method
from xsentinel.dashboard_input import context_key, prepare_input, reader_signature
from xsentinel.dashboard_presentation import explain_result, feature_rows, friendly_error, method_name, format_size, VIEW_NAMES, VIEW_HELP
from xsentinel.dashboard_chrome import controls, contribution_chart, render_verdict_card
from xsentinel.demo_provenance import demo_ground_truth, demo_comparison
from xsentinel.service.client import api_request
from xsentinel.service.scoring import score_input,input_digest
from xsentinel.data.limits import MAX_UPLOAD_BYTES
from xsentinel.dashboard_exports import (snapshot_digest,input_hash_rows,local_timestamp,
    classification_label,trigger_label,timing_description)

st.set_page_config(page_title='X-SENTINEL · Phân tích PE', layout='wide', initial_sidebar_state='collapsed')
api_base = os.getenv('XS_API_BASE_URL', '')
page = controls(api_connected=bool(api_base))


@st.cache_resource(max_entries=4, show_spinner=False)
def load_detector(path, signature, dataset):
    load_path = os.path.relpath(path) if os.name == 'nt' else path
    return Detector.load(load_path, expected_dataset=dataset), threading.RLock()


def bundle_signature(path, state):
    digest = hashlib.sha256((path / 'bundle.json').read_bytes())
    for name in sorted(state['hashes']):
        stat = (path / name).stat()
        digest.update(f'{name}:{stat.st_size}:{stat.st_mtime_ns}'.encode())
    return digest.hexdigest()


def show_error(error):
    st.error(friendly_error(error))
    with st.expander('Chi tiết lỗi kỹ thuật'):
        st.code(str(error))


def render_pdf_export(result,key_prefix):
    pdf_key='pdf_'+key_prefix
    identity=snapshot_digest(result)
    if st.session_state.get(pdf_key+'_snapshot')!=identity:
        st.session_state.pop(pdf_key,None)
        st.session_state[pdf_key+'_snapshot']=identity
    if st.button('Xuất PDF lần phân tích này' if key_prefix.startswith('history_') else 'Xuất PDF kết quả',key='export_'+key_prefix):
        from xsentinel.result_pdf import result_pdf
        with st.spinner('Đang tạo PDF từ kết quả đã có…'):
            st.session_state[pdf_key]=result_pdf(result)
    if pdf_key in st.session_state:
        st.download_button('Tải file PDF',data=st.session_state[pdf_key],file_name='X_SENTINEL_ket_qua.pdf',
            mime='application/pdf',on_click='ignore',key='download_'+key_prefix)


def themed_table(frame):
    # HTML tables inherit the app palette, including OS changes in automatic mode.
    # Streamlit's canvas dataframes use a separate, fixed native theme.
    st.markdown('<div class="xs-data-table">'+frame.to_html(index=False,escape=True,border=0)+'</div>',unsafe_allow_html=True)


def render_result(result, timings=None, key_prefix='result'):
    explanation = explain_result(result)
    metadata = result.get('input_metadata') or {}
    elapsed=result.get('elapsed_ms')
    elapsed_text=f'{elapsed:.2f} ms' if elapsed is not None else 'Chưa lưu'
    st.markdown('<div class="xs-section-title"><span>BƯỚC 3</span> KẾT QUẢ PHÂN TÍCH & BẰNG CHỨNG KIỂM TOÁN</div>', unsafe_allow_html=True)
    if metadata:
        name = html.escape(metadata.get('name', 'Mẫu phân tích'))
        size = metadata.get('size_bytes')
        size_str = format_size(size) if size is not None else 'Mẫu demo reference'
        st.markdown(f'''
        <div class="xs-meta-chips">
            <span class="xs-meta-chip"><strong>📄 Tệp:</strong> {name}</span>
            <span class="xs-meta-chip"><strong>💾 Kích thước:</strong> {size_str}</span>
            <span class="xs-meta-chip"><strong>⚡ Thời gian tính điểm:</strong> {elapsed_text}</span>
        </div>
        ''', unsafe_allow_html=True)
    for label,value in input_hash_rows(result):
        st.caption(label)
        st.code(value,language=None,wrap_lines=True)
    if key_prefix.startswith('history_'):
        render_pdf_export(result,key_prefix)
    comparison = demo_comparison(result)
    if comparison['known']:
        st.markdown('**Nhãn gốc theo bộ dữ liệu: ' + comparison['expected'] + '**')
        (st.success if comparison['matched'] else st.warning)('Đối chiếu: ' + comparison['text'])
        st.caption(comparison['source'] + ' · Đối chiếu này chỉ chấm phân loại file, không chấm trigger.')
    else:
        st.caption(comparison['text'])

    selected = explanation['selected']
    is_malware = result['main_classification'] == 'MALWARE'
    is_backdoor = bool(result['backdoor_alert'])

    left_card = render_verdict_card(
        title='Quyết định 1 · Phân Loại Tệp PE',
        subtitle='Mô hình chính (LightGBM)',
        verdict_text=explanation['classification'],
        is_danger=is_malware,
        score=result['malware_probability'],
        threshold=result.get('malware_threshold'),
        score_text='Xác suất mã độc p(x)',
        note=explanation['classification_explanation']
    )

    right_card = render_verdict_card(
        title='Quyết định 2 · Giám Sát Cửa Hậu',
        subtitle=explanation['method_label'],
        verdict_text=explanation['alert'],
        is_danger=is_backdoor,
        score=float(selected['Score']),
        threshold=float(selected['Threshold']),
        score_text='Điểm tín hiệu S(x)',
        note=f"Ngưỡng cảnh báo τ = {float(selected['Threshold']):.6f}. Mục tiêu calibration không bảo đảm FPR tương lai."
    )

    left, right = st.columns(2)
    left.markdown(left_card, unsafe_allow_html=True)
    right.markdown(right_card, unsafe_allow_html=True)

    left.metric('Mô hình phân loại file', explanation['classification'])
    right.metric('Dấu hiệu trigger', explanation['alert'])
    left.caption(f"Điểm dự đoán mã độc: {result['malware_probability']:.4f}. Gần 1 nghĩa là mô hình nghiêng về mã độc, gần 0 nghiêng về nhãn lành.")
    right.caption('Cảnh báo theo ' + explanation['method_label'])
    (st.warning if result['backdoor_alert'] else st.info)(explanation['interpretation'])
    with st.expander('Vì sao có kết quả này?', expanded=True):
        selected = explanation['selected']
        st.markdown('**1. Vì sao có nhãn phân loại này?**')
        st.write(explanation['classification_explanation'])
        st.caption('Điểm sát ngưỡng có thể đổi nhãn khi điểm thay đổi ít. Điểm mô hình không phải mức chắc chắn thực tế đã được kiểm chứng.')
        st.markdown('**2. Đặc điểm nào đẩy dự đoán về mỗi phía?**')
        features = feature_rows(result)
        malware_items = [row for row in features if row['shap'] > 0][:3]
        benign_items = [row for row in features if row['shap'] < 0][:3]

        def _render_force_box(items, is_danger):
            if not items:
                return '<div style="color:var(--xs-muted); font-size:12.5px; padding:8px 0;">Không có trong 10 đặc trưng ảnh hưởng mạnh nhất đang hiển thị.</div>'
            max_abs = max((abs(row['shap']) for row in items), default=1.0) or 1.0
            rendered = []
            for row in items:
                v = f"{row['value']:.6g}"
                s = f"{row['shap']:+.4f}"
                rel_width = min(100.0, max(8.0, (abs(row['shap']) / max_abs) * 100))
                pill_class = 'xs-shap-malware' if is_danger else 'xs-shap-benign'
                bar_color = 'var(--xs-malware)' if is_danger else 'var(--xs-benign)'
                rendered.append(
                    f'<div class="xs-force-item">'
                    f'<div class="xs-force-item-title">{html.escape(row["title"])}</div>'
                    f'<div style="height:4px; border-radius:2px; background:var(--xs-soft); margin:6px 0; overflow:hidden;">'
                    f'<div style="height:100%; width:{rel_width:.1f}%; background:{bar_color}; border-radius:2px;"></div>'
                    f'</div>'
                    f'<div class="xs-force-item-meta">'
                    f'<span>Giá trị: <strong>{v}</strong></span>'
                    f'<span class="xs-shap-pill {pill_class}">SHAP: {s}</span>'
                    f'</div></div>'
                )
            return ''.join(rendered)

        st.markdown(
            f'<div class="xs-feature-grid">'
            f'<div class="xs-force-col xs-force-danger">'
            f'<div class="xs-force-head">🚨 Đặc trưng Đẩy Về Phía MÃ ĐỘC (SHAP &gt; 0)</div>'
            f'{_render_force_box(malware_items, True)}'
            f'</div>'
            f'<div class="xs-force-col xs-force-safe">'
            f'<div class="xs-force-head">🛡️ Đặc trưng Kéo Về Phía LÀNH TÍNH (SHAP &lt; 0)</div>'
            f'{_render_force_box(benign_items, False)}'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        st.caption('Các đặc điểm có thể kéo về hai phía. Mô hình gộp tất cả đóng góp cùng mốc ban đầu để ra điểm cuối; các số SHAP không cộng trực tiếp vào xác suất.')
        st.markdown('**3. Vì sao có hoặc chưa có cảnh báo trigger?**')
        st.markdown(f"**{explanation['method_label']}** · Điểm **{selected['Score']:.6f}** · Ngưỡng **{selected['Threshold']:.6f}**")
        st.write(explanation['threshold_explanation'])
        st.write(explanation['method_explanation'])
        for signal in explanation['signal_lines']:
            st.write(signal)
        st.caption('Điểm cảnh báo không phải xác suất file chứa backdoor. Ngưỡng đã cố định từ calibration; mục tiêu tại calibration không bảo đảm tỷ lệ cảnh báo nhầm tương lai.')
    if st.toggle('Xem đặc trưng ảnh hưởng đến kết quả', key=key_prefix + '_features'):
        contributions = result['view_contributions']
        contribution_chart(contributions, VIEW_NAMES)
        st.caption('Tỷ trọng SHAP tuyệt đối của mô hình chính. Cột cao nghĩa là nhóm ảnh hưởng nhiều hơn, chưa chứng minh nhóm đó gây ra backdoor.')
        for view, description in VIEW_HELP.items():
            st.write('**' + VIEW_NAMES[view] + ':** ' + description)
        st.markdown('**Cách đọc từng đặc trưng**')
        for row in feature_rows(result):
            st.markdown(f"**{row['title']}** · {row['direction']} · Giá trị **{row['value']:.6g}** · SHAP **{row['shap']:+.6f}**")
            st.caption(row['name'] + ' — ' + row['description'])
        features = pd.DataFrame([{'Đặc trưng': row['name'], 'Giá trị': row['value'], 'SHAP': row['shap'],
                                  'Chiều ảnh hưởng': row['direction']} for row in feature_rows(result)])
        themed_table(features)
        st.caption('SHAP dương đẩy raw margin về mã độc; SHAP âm đẩy về nhãn lành. Giá trị SHAP không phải phần trăm xác suất.')
    if st.toggle('Xem chi tiết nghiên cứu', key=key_prefix + '_research'):
        rows = pd.DataFrame(result['scores']).copy()
        rows['Method'] = rows['Method'].map(method_name)
        rows['Flagged'] = rows['Flagged'].map({True: 'Có', False: 'Chưa'})
        themed_table(rows.rename(columns={'Method': 'Phương pháp', 'Score': 'Điểm',
                      'Threshold': 'Ngưỡng', 'Flagged': 'Cảnh báo'}))
        st.caption('Chỉ hiện các điểm đã tính, mỗi dòng có ngưỡng riêng. Kết luận chính theo phương pháp đang chọn.')
        if result.get('not_computed_methods'):
            st.caption('Chưa tính: '+', '.join(method_name(k) for k in result['not_computed_methods'])+'. Chọn STRIP tại Nghiên cứu nếu cần chạy STRIP.')
        predictions = result.get('view_predictions') or {}
        if predictions:
            st.write('**Dự đoán mã độc của mô hình sạch theo nhóm**')
            themed_table(pd.DataFrame([{'Nhóm': VIEW_NAMES.get(k, k), 'Điểm dự đoán': v}
                                      for k, v in predictions.items()]))
            if result.get('computation_scope')=='selected':
                st.caption('Đường tính gọn chỉ chạy mô hình nhóm cần cho phương pháp; nhóm không xuất hiện chưa được tính.')
        else:
            st.caption('Không tính dự đoán mô hình sạch theo nhóm trong lượt này.')
        st.write('Tổng SHAP có dấu theo nhóm', result['view_signed_shap'])
        st.json({k: result.get(k) for k in ('dataset', 'schema', 'protocol', 'method', 'bundle_id',
                                          'request_id', 'input_sha256', 'input_metadata')})
        st.caption('Metadata đầu vào do giao diện khai báo; checksum file khác checksum vector. Không lưu toàn bộ file/vector trong database.')
    st.caption(timing_description(result)+': '+elapsed_text+'. Chưa gồm upload, đọc file, API/lưu hoặc hiển thị trình duyệt.')
    if timings:
        st.caption(' · '.join(f'{name}: {value:.2f} ms' for name, value in timings.items()))
        st.caption('Thời gian xử lý sau khi bấm được đo phía ứng dụng, chưa gồm upload trước khi bấm và render của trình duyệt.')
    if result.get('saved'):
        st.success('Đã lưu vào lịch sử · ' + result['request_id'])
    else:
        st.caption('Kết quả local, chưa lưu vào database.')
    if not key_prefix.startswith('history_'):
        render_pdf_export(result,key_prefix)


if page == 'Lịch sử':
    st.title('Lịch sử phân tích')
    st.caption('Xem lại các bản ghi phân tích đã được lưu trữ an toàn trong PostgreSQL Audit Log.')
    if not api_base:
        st.info('Chế độ local chưa kết nối database. Kết quả của phiên hiện tại chưa có lịch sử lưu.')
        st.stop()
    st.button('Làm mới lịch sử', key='refresh_history')
    try:
        history = api_request(api_base, '/v1/analyses?limit=100')
        if not history:
            st.info('Chưa có kết quả. Vào Phân tích, chọn đầu vào và nhấn Phân tích.')
        else:
            total_scans = len(history)
            malware_count = sum(1 for row in history if row.get('main_classification') == 'MALWARE')
            backdoor_count = sum(1 for row in history if row.get('backdoor_alert'))
            benign_count = sum(1 for row in history if row.get('main_classification')=='BENIGN')
            malware_rate = (malware_count / total_scans * 100) if total_scans else 0

            st.markdown(f'''
            <div class="xs-kpi-grid">
                <div class="xs-kpi-card">
                    <div class="xs-kpi-label">🗄️ Tổng Lượt Phân Tích</div>
                    <div class="xs-kpi-val">{total_scans}</div>
                    <div class="xs-kpi-sub">Lưu trữ kiểm toán trong PostgreSQL</div>
                </div>
                <div class="xs-kpi-card xs-kpi-danger">
                    <div class="xs-kpi-label">🚨 Phát Hiện Mã Độc</div>
                    <div class="xs-kpi-val">{malware_count}</div>
                    <div class="xs-kpi-sub">{malware_rate:.1f}% tổng số tệp đã quét</div>
                </div>
                <div class="xs-kpi-card xs-kpi-alert">
                    <div class="xs-kpi-label">⚡ Cảnh Báo Backdoor</div>
                    <div class="xs-kpi-val">{backdoor_count}</div>
                    <div class="xs-kpi-sub">Vượt ngưỡng kiểm soát trigger &tau;</div>
                </div>
                <div class="xs-kpi-card xs-kpi-safe">
                    <div class="xs-kpi-label">🛡️ Tệp Lành Tính</div>
                    <div class="xs-kpi-val">{benign_count}</div>
                    <div class="xs-kpi-sub">Dự đoán lành theo bản ghi đã lưu</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

            table = []
            labels = {}
            for row in history:
                metadata = row.get('input_metadata') or {}
                name = metadata.get('name') or 'Bản ghi cũ · ' + row['request_id'][:16]
                timestamp = local_timestamp(row.get('created_at'))
                labels[row['request_id']] = timestamp + ' · ' + name
                table.append({'Thời gian': timestamp, 'Đầu vào': name, 'Bộ mô hình': row['dataset'],
                              'Phân loại': classification_label(row.get('main_classification')),
                              'Trigger': trigger_label(row.get('backdoor_alert'))})
            st.caption(f'Đang hiển thị {len(history)} bản ghi, tối đa 100 bản gần nhất; không phải toàn bộ database.')
            identity=snapshot_digest(history)
            if st.session_state.get('history_pdf_snapshot')!=identity:
                st.session_state.pop('history_pdf_bytes',None)
                for cached_key in list(st.session_state):
                    if cached_key.startswith('pdf_history_'):
                        del st.session_state[cached_key]
                st.session_state['history_pdf_snapshot']=identity
            if st.button('Xuất PDF lịch sử đang hiển thị',key='export_history_list'):
                from xsentinel.result_pdf import history_pdf
                st.session_state['history_pdf_bytes']=history_pdf(history)
            if 'history_pdf_bytes' in st.session_state:
                st.download_button('Tải PDF lịch sử',data=st.session_state['history_pdf_bytes'],
                    file_name='X_SENTINEL_lich_su.pdf',mime='application/pdf',on_click='ignore',key='download_history_list')
            themed_table(pd.DataFrame(table))
            record_ids=list(labels)
            previous=st.session_state.get('history_chosen_id')
            chosen = st.selectbox('Xem một lần phân tích',record_ids,
                index=record_ids.index(previous) if previous in record_ids else 0,
                format_func=lambda value: labels[value],key='history_record')
            st.session_state['history_chosen_id']=chosen
            render_result(api_request(api_base, '/v1/analyses/' + chosen), key_prefix='history_' + chosen)
    except Exception as error:
        show_error(error)
    st.stop()

st.title('Nghiên cứu' if page == 'Nghiên cứu' else 'Phân tích file PE')
st.caption('Chọn đầu vào, đọc hai kết luận và mở giải thích khi cần.')
st.markdown('<div class="xs-section-title"><span>BƯỚC 1</span> CẤU HÌNH BỘ MÔ HÌNH VÀ CHẾ ĐỘ PHÒNG THỦ</div>', unsafe_allow_html=True)
model_column, variant_column = st.columns(2)
dataset = model_column.selectbox('Bộ mô hình', ['EMBER2018', 'EMBER2024'], key='dataset',
                       help='EMBER2018 dùng schema V2 với 2.381 chiều; EMBER2024 dùng V3 với 2.568 chiều. Không dùng chéo model/schema.')
catalog = primary_catalog(dataset)
if not catalog:
    st.warning('Chưa có bộ mô hình nghiên cứu cho dataset này.')
    st.stop()
preferences = st.session_state.setdefault('preferences', {})
prefs = preferences.setdefault(dataset, {'experiment': next(iter(catalog)), 'variant': 'reduced', 'method': None})
custom_path = None
experiment = prefs['experiment']
if page == 'Nghiên cứu':
    st.info('Các lựa chọn bên dưới xác định mô hình của một thí nghiệm đã lưu; không đầu độc hoặc sửa file bạn đưa vào.')
    keys = list(catalog)
    experiment = st.selectbox('Cấu hình thí nghiệm', keys, index=keys.index(prefs['experiment']),
                              format_func=experiment_label, key='experiment_' + dataset,
                              help='Family là loại trigger khi huấn luyện; seed là mã khởi tạo; poison rate tính trên toàn fit.')
variants = [v for v in ('reduced', 'full') if v in catalog[experiment]]
variant = variant_column.selectbox('Chế độ', variants,
                        index=variants.index(prefs['variant']) if prefs['variant'] in variants else 0,
                        format_func=lambda value: 'Reduced · dùng mô hình chính' if value == 'reduced' else 'Full · thêm mô hình sạch theo nhóm',
                        key='variant_' + dataset,
                        help='Hai chế độ cùng thí nghiệm dùng chung mô hình phân loại chính. Full dùng thêm mô hình sạch để tính cảnh báo trigger.')
if experiment != prefs['experiment'] or variant != prefs['variant']:
    prefs['method'] = None
    st.session_state.pop('method_' + dataset, None)
prefs.update(experiment=experiment, variant=variant)
if page == 'Nghiên cứu':
    if not api_base:
        with st.expander('Bộ mô hình khác trong chế độ local'):
            if st.checkbox('Dùng đường dẫn bundle riêng', key='custom_enabled'):
                custom_path = st.text_input('Đường dẫn bundle', key='custom_path')
                st.caption('Bundle được kiểm tra schema và checksum. Bản archive giữ công thức riêng, không được gộp với primary.')
path = Path(custom_path) if custom_path is not None else Path(catalog[prefs['experiment']][prefs['variant']])
try:
    state = json.loads((path / 'bundle.json').read_text(encoding='utf8'))
    if state.get('dataset', 'EMBER2018') != dataset:
        raise ValueError('Bundle dataset mismatch')
    signature = bundle_signature(path, state)
    relative = path.resolve().relative_to(Path('outputs/primary').resolve()).as_posix() if api_base else str(path)
    identity = hashlib.sha256(relative.encode() + b'\0' + (path / 'bundle.json').read_bytes()).hexdigest()
    methods = list(state['thresholds'])
    preferred = prefs.get('method')
    if preferred not in methods:
        preferred = preferred_method(state['thresholds'], prefs['variant'])
    if page == 'Nghiên cứu':
        preferred = st.selectbox('Phương pháp cảnh báo', methods, index=methods.index(preferred),
                                 format_func=method_name, key='method_' + dataset)
    prefs['method'] = preferred
    method = preferred
    schema = state['schema']
    reader_version = reader_signature(schema)
except Exception as error:
    show_error(error)
    st.stop()

st.caption(dataset + ' · ' + prefs['variant'].capitalize() + ' · ' + method_name(method))
with st.expander('Thông tin bộ mô hình đang dùng'):
    st.write('Cấu hình thí nghiệm:', experiment_label(prefs['experiment']))
    st.write('Schema:', schema, '· Protocol:', state.get('method_version', 'archive'))
    st.write(f"Ngưỡng cảnh báo đã cố định: {state['thresholds'][method]:.6f}")
    st.caption('M5 không được kiểm chứng trong primary. Behavioral là import/export tĩnh, không phải nhật ký chạy file.')
    evidence_path = path.parent / 'result.json'
    if evidence_path.exists():
        evidence = json.loads(evidence_path.read_text(encoding='utf8'))
        st.caption('Cấu hình đã qua screening và confirmation.' if evidence.get('independently_confirmed_strong_and_stealth')
                   else 'Cấu hình chưa qua screening/confirmation strong-and-stealth. Giữ để thể hiện đầy đủ kết quả thí nghiệm.')

st.markdown('<div class="xs-section-title"><span>BƯỚC 2</span> CHỌN ĐẦU VÀO PHÂN TÍCH</div>', unsafe_allow_html=True)
labels = {'Tải file PE': 'pe', 'Dùng mẫu demo': 'demo'}
if page == 'Nghiên cứu':
    labels.update({'Vector EMBER (.npy)': 'vector', 'Raw EMBER (.json)': 'raw_json'})
mode = st.radio('Đầu vào', list(labels), horizontal=True, key='mode_' + page)
kind = labels[mode]
uploaded = None
if kind != 'demo':
    extensions = {'pe': ['exe', 'dll', 'sys'], 'vector': ['npy'], 'raw_json': ['json']}[kind]
    uploaded = st.file_uploader('Chọn một file · tối đa 50 MB', type=extensions, key='upload_' + page + '_' + kind)
    if uploaded is None:
        st.info('Chọn một file để bắt đầu. Bạn cũng có thể dùng mẫu demo.')
        st.stop()
    if uploaded.size > MAX_UPLOAD_BYTES:
        st.error('File vượt giới hạn 50 MB.')
        st.stop()
    marker = (uploaded.file_id, uploaded.name, uploaded.size)
    if st.session_state.get('file_marker') != marker:
        data = uploaded.getvalue()
        st.session_state['file_marker'] = marker
        st.session_state['file_data'] = data
        st.session_state['file_digest'] = hashlib.sha256(data).hexdigest()
    data = st.session_state['file_data']
    name = uploaded.name
    digest = st.session_state['file_digest']
    st.caption(name + ' · ' + format_size(uploaded.size))
else:
    data = None
    name = 'Mẫu reference demo'
    digest = 'reference:' + signature
    st.info('Mẫu reference có sẵn dùng để minh họa thao tác. Đây chưa phải kiểm chứng trên file độc lập.')

context = context_key(identity, signature, method, kind, name, digest, schema, reader_version)
if st.session_state.get('active_context') != context:
    st.session_state['active_context'] = context
    st.session_state.pop('analysis', None)
    st.session_state.pop('pending', None)

if st.button('Phân tích và lưu' if api_base else 'Phân tích', type='primary', key='analyze'):
    start = time.perf_counter()
    try:
        with st.status('Đang xử lý đầu vào', expanded=True) as status:
            st.write('1 · Nạp và kiểm tra bộ mô hình.')
            detector, lock = load_detector(str(path.resolve()), signature, dataset)
            st.write('2 · Đọc đầu vào và trích đặc trưng đúng schema.')
            prepared = prepare_input(kind, data, name, schema, detector.reference)
            st.write('3 · Tính điểm phân loại và cảnh báo.')
            rpc_ms = None
            if api_base:
                pending = st.session_state.get('pending') or {'context': context, 'request_id': str(uuid.uuid4())}
                st.session_state['pending'] = pending
                rpc_start = time.perf_counter()
                result = api_request(api_base, '/v1/analyze/vector', {
                    'bundle_id': identity, 'features': prepared['x'][0].tolist(), 'method': method,
                    'request_id': pending['request_id'], 'demo_mode': kind == 'demo',
                    'input_metadata': prepared['metadata']})
                rpc_ms = (time.perf_counter() - rpc_start) * 1000
                st.write('4 · API đã xác nhận lưu kết quả.')
                st.session_state.pop('pending', None)
            else:
                with lock:
                    result = score_input(detector, prepared['x'], method,scope='selected')
                    result['input_sha256']=input_digest(prepared['x'])
                result['input_metadata'] = prepared['metadata']
                result['ground_truth'] = demo_ground_truth(state, prepared['x'], kind == 'demo')
                result['demo_mode'] = kind == 'demo'
                result['bundle_id'] = identity
                result['created_at'] = datetime.now(timezone.utc).isoformat()
                result['experiment'] = {'dataset': dataset, 'variant': prefs['variant'],
                                        'family': prefs['experiment'][0], 'seed': prefs['experiment'][1], 'rate': prefs['experiment'][2]}
                st.write('4 · Kết quả local sẵn sàng, chưa lưu database.')
            timings = {'Đọc/trích đặc trưng': prepared['metadata']['extraction_ms']}
            if rpc_ms is not None:
                timings['API + tính điểm/lưu (gộp)'] = rpc_ms
            timings['Xử lý sau khi bấm'] = (time.perf_counter() - start) * 1000
            st.session_state['analysis'] = {'context': context, 'result': result, 'timings': timings,
                                            'provenance': prepared['provenance']}
            status.update(label='Đã có kết quả', state='complete', expanded=False)
    except Exception as error:
        show_error(error)
record = st.session_state.get('analysis')
if record and record['context'] == context:
    render_result(record['result'], record['timings'], key_prefix=context)
    if record['provenance']:
        with st.expander('Giới hạn bộ đọc PE'):
            st.caption('V2 còn experimental với LIEF hiện đại. V3 đã kiểm chứng fixture lành và xử lý binary/raw upstream, chưa đối chiếu binary gốc của dataset.')
            st.json(record['provenance'])
