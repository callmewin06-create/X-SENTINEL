"""Display dated research evidence without scoring inputs or changing bundles."""
import html
import pandas as pd
import streamlit as st
from xsentinel.research_status import load_research_status


def pct(value):
    return f'{100 * value:.2f}%'


def render_research_summary(table):
    loaded = load_research_status()
    if loaded['state'] != 'ready':
        st.warning(loaded['message'])
        return
    data = loaded['snapshot']
    with st.container(border=True):
        st.subheader('Kết quả nghiên cứu đã chốt · 28/10/2026')
        st.caption('Bản tổng hợp cố định; không phải điểm của mẫu đang chọn hoặc trạng thái dịch vụ hiện tại.')
        primary, seeds = data['primary'], data['seeds']
        cards = [('Cấu hình primary', primary['configuration_count']),
                 ('Bundle Reduced / Full', primary['bundle_count']),
                 ('Seed bổ sung', len(seeds['additional_seeds'])),
                 ('Đạt confirmation ở điều kiện bổ sung', f"{seeds['confirmed_count']}/{seeds['attempt_count']}")]
        st.markdown('<div class="xs-kpi-grid">'+''.join(
            '<div class="xs-kpi-card"><div class="xs-kpi-label">'+html.escape(label)+
            '</div><div class="xs-kpi-val">'+html.escape(str(value))+'</div></div>'
            for label, value in cards)+'</div>', unsafe_allow_html=True)
        tabs = st.tabs(['Kết quả chính', 'Cùng FPR', 'Ngân sách sạch', 'Adaptive và seed', 'Audit binary'])
        with tabs[0]:
            st.write('**Reduced: VMC + BGS. Full: VMC + BPG, dùng dự đoán Behavioral sạch.**')
            rows = [r for r in data['fixed_threshold']['rows'] if r['cohort'] == 'restricted']
            table(pd.DataFrame([{'Dataset': r['dataset'], 'Chế độ': r['method'], 'Số run': r['runs'],
                'Recall': pct(r['recall']), 'FPR final': pct(r['fpr'])} for r in rows]))
            st.caption('Trung bình theo run trên cohort restricted đã xác nhận. Recall tính trên tấn công successful-eligible; dùng ngưỡng calibration gốc, không phải accuracy toàn hệ thống.')
            st.warning('Cross và thích nghi đa view vẫn là điểm yếu. Full không luôn hơn Shadow; cần đối chiếu cùng tài nguyên sạch và cùng FPR.')
            table(pd.DataFrame([{'Dataset': r['dataset'], 'ASR clean có trigger': pct(r['clean_asr']),
                'ASR poisoned': pct(r['poisoned_asr']), 'Né mới do đầu độc (paired)': pct(r['new_evasion'])}
                for r in data['cross_confirmation']['rows']]))
            st.caption('Bảng Cross dùng pool confirmation và mẫu số clean-original eligible. ASR poisoned cao không tự chứng minh toàn bộ mức né là do đầu độc.')
        with tabs[1]:
            rows = data['same_fpr']['rows']
            dataset = st.selectbox('Dataset của bảng cùng FPR', sorted({r['dataset'] for r in rows}), key='summary_fpr_dataset')
            cohorts = sorted({r['cohort'] for r in rows if r['dataset'] == dataset})
            cohort = st.selectbox('Cohort của bảng cùng FPR', cohorts, key='summary_fpr_cohort')
            table(pd.DataFrame([{'Phương pháp': r['method'], 'Số run': r['runs'], 'TPR': pct(r['tpr']),
                'FPR thực tế': pct(r['fpr']), 'pAUC chuẩn hóa': f"{r['pauc']:.4f}"}
                for r in rows if r['dataset'] == dataset and r['cohort'] == cohort]))
            st.caption('So sánh hồi cứu tại FPR final ≤1%, positives successful-eligible. pAUC được chuẩn hóa với max_fpr=0.01. Final đã được quan sát; đây không phải ngưỡng triển khai mới.')
        with tabs[2]:
            dataset = st.selectbox('Dataset của bảng ngân sách', [r['dataset'] for r in primary['datasets']], key='summary_budget_dataset')
            rows = [r for r in data['clean_budgets']['rows'] if r['dataset'] == dataset]
            frame = pd.DataFrame([{'Mẫu fit sạch': r['budget'], 'Phương pháp': r['method'], 'TPR (%)': round(100*r['tpr'], 2)} for r in rows])
            table(frame.pivot(index='Phương pháp', columns='Mẫu fit sạch', values='TPR (%)').reset_index())
            st.caption('Cohort restricted, FPR final cap 1%. Ngân sách fit chứa cả lành và mã độc; reference/calibration là tài nguyên riêng. Ở 200.000 mẫu, Shadow dùng mô hình sạch cũng xác định eligibility, nên cần giữ ranh giới diễn giải này.')
        with tabs[3]:
            table(pd.DataFrame([{'Dataset': r['dataset'], 'Cohort': r['cohort'], 'Né cả hai trước': pct(r['before']),
                'Né cả hai sau': pct(r['after']), 'Tăng (điểm %)': round(r['gain_pp'], 2)} for r in data['adaptive']['rows']]))
            st.caption('Né cả mô hình phân loại và cảnh báo Reduced. Tối đa 32 lần gọi kể cả điểm ban đầu; tìm kiếm giới hạn trên cả ba view, trong không gian đặc trưng.')
            table(pd.DataFrame([{'Seed': r['seed'], 'Nguồn': 'Bổ sung' if r['origin'] == 'additional' else 'Gốc',
                'Đạt confirmation': 'Có' if r['confirmed'] else 'Không', 'ASR confirmation': pct(r['confirmation_asr']),
                'Recall Reduced': pct(r['reduced_recall']), 'Recall Full': pct(r['full_recall'])} for r in seeds['rows']]))
            st.caption('Chỉ điều kiện EMBER2024 / spread Structural / 2%. Hai seed mới 59 và 71 không tạo thêm hai ma trận primary; giữ cả seed không đạt.')
            with st.expander('Lọc dữ liệu huấn luyện · hai cấu hình'):
                table(pd.DataFrame([{'Dataset': r['dataset'], 'Phương pháp': r['method'], 'Số mẫu loại': r['removed'],
                    'Poison bị loại': r['poisons_removed'], 'ASR trước': pct(r['asr_before']), 'ASR sau': pct(r['asr_after'])}
                    for r in data['training_filtering']['rows']]))
                st.caption('Có retraining và đối chứng loại ngẫu nhiên độc lập. Đây không phải recall của detector theo từng đầu vào.')
        with tabs[4]:
            b = data['binary_audit']
            st.write(f"**{b['variant_count']} biến thể = {b['original_count']} bản gốc + {b['modified_count']} bản sửa; overlay tăng {b['overlay_bytes']} byte.**")
            st.write(f"Windows: **{b['windows_pass']} PASS / {b['windows_error']} ERROR**. Các lỗi Application Control không chứng minh file vẫn chạy đúng; không có bằng chứng chạy Wine trong gói đã nhận.")
            st.write(f"{b['scoring_rows']} hàng chấm điểm tương ứng {b['unique_file_main_model_pairs']} cặp file/model chính, lặp giữa hai chế độ. Reduced có {b['reduced_alerts']} cảnh báo; Full có {b['full_alerts']} trên {b['full_scored_rows']} hàng được tính.")
            st.warning('Đây là file lành và các chỉnh sửa đơn tọa độ. Zero alert không phải recall backdoor. Gói thiếu source/EXE nên chưa rebuild hoặc chạy lại độc lập; chưa chứng minh trigger benchmark đầy đủ trên malware hoạt động.')
            if b.get('feature_shift_rows'):
                with st.expander('Chi tiết thay đổi đặc trưng V2 / V3'):
                    table(pd.DataFrame(b['feature_shift_rows']))
        with st.expander('Nguồn và phạm vi số liệu'):
            for limitation in data['limitations']:
                st.write('• '+limitation)
            st.caption('Nguồn được ghi nhận khi tạo bản tổng hợp; không kiểm tra lại các CSV gốc trên máy chạy demo.')
            table(pd.DataFrame(data['provenance']['sources']))

