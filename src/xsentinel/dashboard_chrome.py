"""Application-owned Vietnamese controls, modern cybersecurity theme, and rich presentation components."""
from html import escape
import streamlit as st
import streamlit.components.v1 as components

GITHUB = 'https://github.com/callmewin06-create/X-SENTINEL'

LIGHT = (
    '--xs-bg:#f8fafc;'
    '--xs-panel:#ffffff;'
    '--xs-card:#ffffff;'
    '--xs-text:#0f172a;'
    '--xs-muted:#64748b;'
    '--xs-border:#e2e8f0;'
    '--xs-border-strong:#cbd5e1;'
    '--xs-soft:#f1f5f9;'
    '--xs-accent:#0284c7;'
    '--xs-accent-gradient:linear-gradient(135deg, #0284c7 0%, #2563eb 100%);'
    '--xs-malware:#dc2626;'
    '--xs-malware-bg:#fef2f2;'
    '--xs-malware-border:#fca5a5;'
    '--xs-benign:#059669;'
    '--xs-benign-bg:#ecfdf5;'
    '--xs-benign-border:#6ee7b7;'
    '--xs-alert:#d97706;'
    '--xs-alert-bg:#fffbeb;'
    '--xs-alert-border:#fde68a;'
    '--xs-shadow:0 4px 20px -2px rgba(15, 23, 42, 0.08);'
    '--xs-card-shadow:0 2px 8px -1px rgba(15, 23, 42, 0.05);'
)

DARK = (
    '--xs-bg:#090d16;'
    '--xs-panel:#111827;'
    '--xs-card:#1e293b;'
    '--xs-text:#f8fafc;'
    '--xs-muted:#94a3b8;'
    '--xs-border:#293548;'
    '--xs-border-strong:#3b4b66;'
    '--xs-soft:#172033;'
    '--xs-accent:#38bdf8;'
    '--xs-accent-gradient:linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);'
    '--xs-malware:#f87171;'
    '--xs-malware-bg:rgba(239, 68, 68, 0.12);'
    '--xs-malware-border:rgba(239, 68, 68, 0.35);'
    '--xs-benign:#34d399;'
    '--xs-benign-bg:rgba(16, 185, 129, 0.12);'
    '--xs-benign-border:rgba(16, 185, 129, 0.35);'
    '--xs-alert:#fbbf24;'
    '--xs-alert-bg:rgba(245, 158, 11, 0.12);'
    '--xs-alert-border:rgba(245, 158, 11, 0.35);'
    '--xs-shadow:0 10px 30px -5px rgba(0, 0, 0, 0.5);'
    '--xs-card-shadow:0 4px 14px 0 rgba(0, 0, 0, 0.25);'
)


@st.dialog('Giới thiệu X-SENTINEL')
def about():
    st.markdown('''
    ### 🛡️ Hệ Thống Phòng Thủ X-SENTINEL
    **Phát hiện cửa hậu (Backdoor) trên bộ phân loại mã độc PE bằng tính nhất quán ngữ nghĩa đa góc nhìn.**

    - **Đơn vị thực hiện**: Nhóm 4 — Khoa An toàn Thông tin, Đại học FPT (Học kỳ Fall 2026).
    - **Cốt lõi khoa học**:
      1. Phân rã tệp PE thành 3 góc nhìn trực giao: **Cấu trúc ($V_S$)**, **Hành vi API ($V_B$)** và **Metadata ($V_M$)**.
      2. Module **M3 (View-Mass Dominance)**: Khắc phục sự sụp đổ của TADR trước đòn tấn công phân tán $T_{\\text{spread}}$.
      3. Module **M4 (Cross-View Semantic Consistency)**: Khai thác mâu thuẫn khi Header bị lừa là lành tính nhưng Import Table API kiên quyết tố cáo mã độc.
    - **Triển khai**: Backend FastAPI, Cơ sở dữ liệu kiểm toán PostgreSQL, Streamlit SOC Dashboard.
    ''')
    st.caption('Hai quyết định phân loại file và cảnh báo trigger được tính toán độc lập. Chưa có cảnh báo không đồng nghĩa file tuyệt đối an toàn.')
    st.link_button('Mở Repository GitHub của nhóm', GITHUB)


def controls(api_connected=False):
    with st.container(key='app_header'):
        with st.container(key='nav_menu'):
            with st.popover('Điều hướng', icon=':material/menu:', help='Mở menu điều hướng'):
                with st.container(key='nav_items'):
                    st.markdown('<div class="xs-menu-title">CHUYỂN PHÂN KHU</div>', unsafe_allow_html=True)
                    page = st.radio('Điều hướng', ['Phân tích', 'Lịch sử', 'Nghiên cứu'], key='page', label_visibility='collapsed')
        
        # Center Brand
        st.markdown(
            '<div class="xs-brand" role="banner" aria-label="X-SENTINEL">'
            '<div class="xs-brand-logo">🛡️ <span class="xs-brand-title">X-SENTINEL</span></div>'
            '<div class="xs-brand-sub">HỆ THỐNG PHÁT HIỆN CỬA HẬU MÃ ĐỘC PE ĐA GÓC NHÌN</div>'
            '</div>',
            unsafe_allow_html=True
        )

        with st.container(key='settings_menu'):
            with st.popover('Cài đặt', icon=':material/settings:', help='Tùy chỉnh hệ thống'):
                st.markdown('<div class="xs-menu-title">TÙY CHỈNH GIAO DIỆN</div>', unsafe_allow_html=True)
                choice = st.selectbox('Chủ đề hiển thị', ['Theo hệ thống', 'Sáng', 'Tối'], key='appearance')
                st.button('Tải lại giao diện', help='Làm mới phần hiển thị, giữ nguyên kết quả phân tích trong phiên.', key='refresh_app')
                if st.button('Giới thiệu đề tài', key='about_app'):
                    about()
                st.divider()
                st.checkbox('Bảng quay video màn hình', key='record_screen')

    base = DARK if choice == 'Tối' else LIGHT
    automatic = f'@media(prefers-color-scheme:dark){{:root{{{DARK}}}}}' if choice == 'Theo hệ thống' else ''
    st.markdown('<style>:root{' + base + '}' + automatic + CSS + '</style>', unsafe_allow_html=True)

    # Status Bar
    api_status_html = (
        '<span class="xs-pill xs-pill-green">🟢 API & PostgreSQL Đã kết nối</span>'
        if api_connected else
        '<span class="xs-pill xs-pill-yellow">🟡 Chế độ Local (Chưa kết nối DB)</span>'
    )
    st.markdown(
        f'<div class="xs-status-bar">'
        f'<div class="xs-status-left">{api_status_html} '
        f'<span class="xs-pill xs-pill-blue">🔒 Kiểm toán tĩnh (Không chạy file)</span> '
        f'<span class="xs-pill xs-pill-purple">⚡ LightGBM TreeSHAP</span></div>'
        f'<div class="xs-status-right">Giới hạn tải file PE: <strong>50 MB</strong></div>'
        f'</div>',
        unsafe_allow_html=True
    )

    if st.session_state.get('record_screen'):
        with st.container(key='screen_recorder_panel', border=True):
            st.markdown('**🎬 Quay video màn hình để báo cáo / thuyết minh**')
            st.caption('Chọn tab hoặc cửa sổ cần quay. Video được lưu trực tiếp dưới dạng WebM qua trình duyệt. Nhớ dừng và tải video trước khi tải lại trang.')
            components.html(RECORDER, height=145)
    return page


def render_verdict_card(title, subtitle, verdict_text, is_danger, score, threshold, score_text, note):
    """Render a visual verdict card for Classification or Backdoor Alert."""
    theme_class = 'xs-verdict-danger' if is_danger else 'xs-verdict-safe'
    icon = '🚨' if is_danger else '🛡️'
    
    # Progress gauge calculation
    pct = max(0.0, min(100.0, float(score) * 100))
    threshold_pct = max(0.0, min(100.0, float(threshold) * 100))
    
    html_card = f'''
    <div class="xs-verdict-box {theme_class}">
        <div class="xs-verdict-header">
            <span class="xs-verdict-title">{escape(title)}</span>
            <span class="xs-verdict-subtitle">{escape(subtitle)}</span>
        </div>
        <div class="xs-verdict-body">
            <div class="xs-verdict-badge">
                <span class="xs-verdict-icon">{icon}</span>
                <span class="xs-verdict-text">{escape(verdict_text)}</span>
            </div>
            <div class="xs-gauge-wrap">
                <div class="xs-gauge-labels">
                    <span>{escape(score_text)}: <strong>{score:.4f}</strong></span>
                    <span>Ngưỡng: <strong>{threshold:.4f}</strong></span>
                </div>
                <div class="xs-gauge-track">
                    <div class="xs-gauge-fill" style="width: {pct:.2f}%;"></div>
                    <div class="xs-gauge-marker" style="left: {threshold_pct:.2f}%;" title="Ngưỡng phân loại"></div>
                </div>
            </div>
            <div class="xs-verdict-note">{escape(note)}</div>
        </div>
    </div>
    '''
    return html_card


def contribution_chart(contributions, names):
    """Modern gradient multi-view distribution chart."""
    rows = []
    view_gradients = {
        'structural': 'linear-gradient(90deg, #0284c7 0%, #38bdf8 100%)',
        'behavioral': 'linear-gradient(90deg, #7c3aed 0%, #c084fc 100%)',
        'metadata': 'linear-gradient(90deg, #059669 0%, #34d399 100%)',
    }
    view_icons = {
        'structural': '📐',
        'behavioral': '⚙️',
        'metadata': '🔤',
    }

    for key, fraction in contributions.items():
        value = 100 * float(fraction)
        width = max(0.0, min(100.0, value))
        grad = view_gradients.get(key, 'var(--xs-accent-gradient)')
        icon = view_icons.get(key, '📊')
        label = names.get(key, key)
        
        rows.append(
            f'<div class="xs-bar-row">'
            f'<div class="xs-bar-label"><span class="xs-view-icon">{icon}</span> {escape(label)}</div>'
            f'<div class="xs-bar-track"><div class="xs-bar-fill" style="width:{width:.4f}%; background:{grad};"></div></div>'
            f'<div class="xs-bar-value"><strong>{value:.2f}%</strong></div>'
            f'</div>'
        )

    st.markdown(
        f'<div class="xs-chart-card">'
        f'<div class="xs-chart-head">'
        f'<span class="xs-chart-title">📊 Tỷ Trọng Đóng Góp Theo 3 Góc Nhìn (View-Mass Distribution)</span>'
        f'<span class="xs-chart-badge">TreeSHAP Absolute Mass</span>'
        f'</div>'
        f'<div class="xs-chart-body">{"".join(rows)}</div>'
        f'<div class="xs-chart-foot">Góc nhìn Cấu trúc ($V_S$) thâu tóm phần lớn attribution là dấu hiệu then chốt để Module $M_3$ nhận diện trigger phân tán.</div>'
        f'</div>',
        unsafe_allow_html=True
    )


CSS = r'''
/* Base Layout & Typography */
.block-container {max-width: 1200px; padding-top: 6.2rem; padding-bottom: 3.5rem;}
[data-testid="stMain"] {scroll-padding-top: 6.2rem;}

/* Header bar */
.st-key-app_header {
    position: fixed !important;
    top: 0; left: 0; right: 0;
    width: 100% !important; max-width: none !important;
    height: 74px; min-height: 74px;
    padding: 10px 80px;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 999991;
    border: 0;
    border-bottom: 1px solid var(--xs-border);
    border-radius: 0;
    background: var(--xs-panel);
    backdrop-filter: blur(16px);
    box-shadow: var(--xs-shadow);
}

.st-key-nav_menu, .st-key-settings_menu {
    position: absolute !important;
    top: 12px;
    width: 48px !important;
    z-index: 2;
}
.st-key-nav_menu {left: 20px;}
.st-key-settings_menu {right: 20px;}

.st-key-nav_menu [data-testid="stPopover"] button,
.st-key-settings_menu [data-testid="stPopover"] button {
    width: 48px; height: 48px;
    padding: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 12px;
    border: 1px solid var(--xs-border);
    background: var(--xs-soft) !important;
    color: var(--xs-text) !important;
    transition: all 0.2s ease;
}
.st-key-nav_menu [data-testid="stPopover"] button:hover,
.st-key-settings_menu [data-testid="stPopover"] button:hover {
    border-color: var(--xs-accent);
    box-shadow: 0 0 12px var(--xs-accent);
}

.st-key-nav_menu [data-testid="stPopover"] button [data-testid="stMarkdownContainer"],
.st-key-settings_menu [data-testid="stPopover"] button [data-testid="stMarkdownContainer"] {
    position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap;
}
.st-key-nav_menu [data-testid="stPopoverButton"]>div:has(svg),
.st-key-settings_menu [data-testid="stPopoverButton"]>div:has(svg) {display: none;}

.xs-menu-title {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--xs-muted);
    margin-bottom: 8px;
}
.st-key-nav_items [role="radiogroup"] label {
    min-height: 42px;
    align-items: center;
    font-size: 15px;
    font-weight: 500;
    border-radius: 8px;
    padding: 4px 8px;
    transition: background 0.15s ease;
}
.st-key-nav_items [role="radiogroup"] label:hover {
    background: var(--xs-soft);
}

/* Brand header */
.xs-brand {text-align: center;}
.xs-brand-logo {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: 0.04em;
    line-height: 1.2;
}
.xs-brand-title {
    background: var(--xs-accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.xs-brand-sub {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    color: var(--xs-muted);
    text-transform: uppercase;
    margin-top: 2px;
}

@media(max-width: 650px) {
    .block-container {padding-top: 5.6rem;}
    .st-key-app_header {padding: 8px 60px; height: 64px; min-height: 64px;}
    .st-key-nav_menu {left: 10px;}
    .st-key-settings_menu {right: 10px;}
    .xs-brand-logo {font-size: 20px;}
    .xs-brand-sub {display: none;}
    .st-key-nav_menu, .st-key-settings_menu {top: 8px;}
}

/* Status Bar */
.xs-status-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    padding: 10px 16px;
    border-radius: 10px;
    background: var(--xs-soft);
    border: 1px solid var(--xs-border);
    margin-bottom: 22px;
    font-size: 13px;
    color: var(--xs-text);
}
.xs-status-left {display: flex; align-items: center; gap: 8px; flex-wrap: wrap;}
.xs-status-right {color: var(--xs-muted); font-size: 12.5px;}

.xs-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 600;
}
.xs-pill-green {background: var(--xs-benign-bg); color: var(--xs-benign); border: 1px solid var(--xs-benign-border);}
.xs-pill-yellow {background: var(--xs-alert-bg); color: var(--xs-alert); border: 1px solid var(--xs-alert-border);}
.xs-pill-blue {background: rgba(2, 132, 199, 0.12); color: var(--xs-accent); border: 1px solid rgba(2, 132, 199, 0.3);}
.xs-pill-purple {background: rgba(168, 85, 247, 0.12); color: #a855f7; border: 1px solid rgba(168, 85, 247, 0.3);}

/* Modern Verdict Boxes */
.xs-verdict-box {
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 16px;
    border: 1px solid var(--xs-border);
    background: var(--xs-panel);
    box-shadow: var(--xs-card-shadow);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.xs-verdict-box:hover {
    transform: translateY(-2px);
    box-shadow: var(--xs-shadow);
}
.xs-verdict-danger {
    border-left: 5px solid var(--xs-malware);
    background: linear-gradient(180deg, var(--xs-panel) 0%, var(--xs-malware-bg) 100%);
}
.xs-verdict-safe {
    border-left: 5px solid var(--xs-benign);
    background: linear-gradient(180deg, var(--xs-panel) 0%, var(--xs-benign-bg) 100%);
}

.xs-verdict-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 12px;
}
.xs-verdict-title {
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--xs-muted);
}
.xs-verdict-subtitle {
    font-size: 12px;
    color: var(--xs-muted);
}
.xs-verdict-badge {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
}
.xs-verdict-icon {font-size: 26px;}
.xs-verdict-text {
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: var(--xs-text);
}
.xs-verdict-danger .xs-verdict-text {color: var(--xs-malware);}
.xs-verdict-safe .xs-verdict-text {color: var(--xs-benign);}

/* Gauge Bar */
.xs-gauge-wrap {margin-bottom: 12px;}
.xs-gauge-labels {
    display: flex;
    justify-content: space-between;
    font-size: 12.5px;
    color: var(--xs-muted);
    margin-bottom: 6px;
}
.xs-gauge-track {
    position: relative;
    height: 14px;
    border-radius: 999px;
    background: var(--xs-soft);
    border: 1px solid var(--xs-border);
    overflow: visible;
}
.xs-gauge-fill {
    height: 100%;
    border-radius: 999px;
    background: var(--xs-accent-gradient);
    transition: width 0.4s ease;
}
.xs-verdict-danger .xs-gauge-fill {
    background: linear-gradient(90deg, #f59e0b 0%, #ef4444 100%);
}
.xs-verdict-safe .xs-gauge-fill {
    background: linear-gradient(90deg, #06b6d4 0%, #10b981 100%);
}
.xs-gauge-marker {
    position: absolute;
    top: -4px;
    bottom: -4px;
    width: 3px;
    background: var(--xs-text);
    border-radius: 2px;
    box-shadow: 0 0 6px rgba(0, 0, 0, 0.4);
}
.xs-verdict-note {
    font-size: 13px;
    line-height: 1.5;
    color: var(--xs-muted);
}

/* Chart card */
.xs-chart-card {
    padding: 22px;
    border-radius: 14px;
    background: var(--xs-panel);
    border: 1px solid var(--xs-border);
    box-shadow: var(--xs-card-shadow);
    margin: 16px 0 20px;
}
.xs-chart-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
    flex-wrap: wrap;
    gap: 8px;
}
.xs-chart-title {
    font-size: 17px;
    font-weight: 700;
    color: var(--xs-text);
}
.xs-chart-badge {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 6px;
    background: var(--xs-soft);
    color: var(--xs-muted);
    border: 1px solid var(--xs-border);
}
.xs-bar-row {
    display: grid;
    grid-template-columns: 240px 1fr 70px;
    gap: 16px;
    align-items: center;
    min-height: 48px;
    padding: 6px 0;
}
.xs-bar-label {
    font-size: 14.5px;
    font-weight: 600;
    color: var(--xs-text);
    display: flex;
    align-items: center;
    gap: 8px;
}
.xs-bar-track {
    height: 18px;
    border-radius: 8px;
    background: var(--xs-soft);
    border: 1px solid var(--xs-border);
    overflow: hidden;
}
.xs-bar-fill {
    height: 100%;
    border-radius: 8px;
    transition: width 0.4s ease;
}
.xs-bar-value {
    text-align: right;
    font-size: 15px;
    color: var(--xs-text);
}
.xs-chart-foot {
    font-size: 12.5px;
    color: var(--xs-muted);
    margin-top: 14px;
    line-height: 1.5;
}
@media(max-width: 650px) {
    .xs-bar-row {grid-template-columns: 1fr 60px; gap: 8px;}
    .xs-bar-label {grid-column: 1 / -1;}
}

/* Feature Force Cards */
.xs-feature-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin: 12px 0 16px;
}
@media(max-width: 768px) {
    .xs-feature-grid {grid-template-columns: 1fr;}
}
.xs-force-col {
    padding: 16px;
    border-radius: 12px;
    background: var(--xs-soft);
    border: 1px solid var(--xs-border);
}
.xs-force-head {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 12px;
}
.xs-force-danger .xs-force-head {color: var(--xs-malware);}
.xs-force-safe .xs-force-head {color: var(--xs-benign);}
.xs-force-item {
    padding: 10px 12px;
    background: var(--xs-panel);
    border: 1px solid var(--xs-border);
    border-radius: 8px;
    margin-bottom: 8px;
}
.xs-force-item-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--xs-text);
    margin-bottom: 4px;
}
.xs-force-item-meta {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: var(--xs-muted);
}

/* Section Headings */
.xs-section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--xs-muted);
    margin: 22px 0 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--xs-border);
}
.xs-section-title span {
    display: inline-block;
    background: var(--xs-accent-gradient);
    color: #ffffff;
    font-size: 11px;
    font-weight: 800;
    padding: 2px 8px;
    border-radius: 6px;
    letter-spacing: 0.05em;
}

/* KPI Summary Cards */
.xs-kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 14px;
    margin-bottom: 22px;
}
.xs-kpi-card {
    background: var(--xs-panel);
    border: 1px solid var(--xs-border);
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: var(--xs-card-shadow);
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.xs-kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--xs-shadow);
}
.xs-kpi-label {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--xs-muted);
    margin-bottom: 6px;
}
.xs-kpi-val {
    font-size: 26px;
    font-weight: 800;
    color: var(--xs-text);
    line-height: 1.1;
    margin-bottom: 4px;
}
.xs-kpi-sub {
    font-size: 11.5px;
    color: var(--xs-muted);
}
.xs-kpi-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--xs-accent-gradient);
}
.xs-kpi-danger::before { background: var(--xs-malware); }
.xs-kpi-danger .xs-kpi-val { color: var(--xs-malware); }
.xs-kpi-alert::before { background: var(--xs-alert); }
.xs-kpi-alert .xs-kpi-val { color: var(--xs-alert); }
.xs-kpi-safe::before { background: var(--xs-benign); }
.xs-kpi-safe .xs-kpi-val { color: var(--xs-benign); }

/* Metadata Chips Bar */
.xs-meta-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-bottom: 16px;
    padding: 10px 14px;
    background: var(--xs-soft);
    border-radius: 10px;
    border: 1px solid var(--xs-border);
}
.xs-meta-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12.5px;
    color: var(--xs-text);
}
.xs-meta-chip strong {
    color: var(--xs-text);
}
.xs-meta-chip code {
    background: var(--xs-panel);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11.5px;
    border: 1px solid var(--xs-border);
}

/* Global Streamlit Component Overrides */
#MainMenu, [data-testid="stMainMenu"], .stAppDeployButton, .stDeployButton {display: none !important;}
[data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"] {
    background: var(--xs-bg) !important;
    color: var(--xs-text) !important;
}
[data-testid="stSidebar"], [data-testid="stPopoverBody"], [role="dialog"] {
    background: var(--xs-panel) !important;
    color: var(--xs-text) !important;
}
[data-testid="stPopoverBody"]>div {background: var(--xs-panel) !important;}

/* Metric default override */
[data-testid="stMetric"] {
    background: var(--xs-panel);
    border: 1px solid var(--xs-border);
    border-radius: 12px;
    padding: 16px;
    color: var(--xs-text);
    box-shadow: var(--xs-card-shadow);
}
[data-testid="stMetricLabel"] p {
    font-size: 13px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    color: var(--xs-muted) !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.7rem !important;
    font-weight: 800 !important;
    color: var(--xs-text) !important;
}

/* Card buttons & inputs */
[data-baseweb="select"]>div, [data-baseweb="input"], input, textarea {
    background: var(--xs-panel) !important;
    color: var(--xs-text) !important;
    border-color: var(--xs-border) !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: var(--xs-panel) !important;
    color: var(--xs-text) !important;
    border-color: var(--xs-border) !important;
    border-radius: 12px !important;
}
button[kind="primary"] {
    background: var(--xs-accent-gradient) !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    box-shadow: 0 4px 14px 0 rgba(2, 132, 199, 0.35) !important;
    transition: all 0.2s ease !important;
}
button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px 0 rgba(2, 132, 199, 0.5) !important;
}
button[kind="secondary"] {
    background: var(--xs-panel) !important;
    color: var(--xs-text) !important;
    border: 1px solid var(--xs-border) !important;
    border-radius: 10px !important;
}
'''

RECORDER = '''<!doctype html><html lang="vi"><meta charset="utf-8"><style>body{font:13px sans-serif;color:#172b4d;background:#fff;margin:4px}button,a{padding:8px 12px;margin:3px;border-radius:6px;border:1px solid #cbd5e1;cursor:pointer;font-weight:600}#start{background:#0284c7;color:#fff;border-color:#0284c7}#stop{background:#f1f5f9;color:#475569}#save{background:#059669;color:#fff;text-decoration:none;display:inline-block}#status{margin:8px;font-size:12.5px;color:#64748b;line-height:1.4}</style>
<button id="start">▶ Bắt đầu quay</button><button id="stop" disabled>⏹ Dừng quay</button><div id="status">Sẵn sàng quay màn hình.</div><a id="save" hidden>💾 Tải video WebM</a>
<script>
let recorder,stream,url;const start=document.querySelector('#start'),stop=document.querySelector('#stop'),status=document.querySelector('#status'),save=document.querySelector('#save');
start.onclick=async()=>{try{if(!navigator.mediaDevices?.getDisplayMedia||!window.MediaRecorder)throw Error('Trình duyệt chưa hỗ trợ quay màn hình.');stream=await navigator.mediaDevices.getDisplayMedia({video:true,audio:false});const chunks=[];recorder=new MediaRecorder(stream);recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};recorder.onstop=()=>{if(url)URL.revokeObjectURL(url);url=URL.createObjectURL(new Blob(chunks,{type:recorder.mimeType}));save.href=url;save.download='X_SENTINEL_demo.webm';save.hidden=false;stream.getTracks().forEach(t=>t.stop());start.disabled=false;stop.disabled=true;status.textContent='Đã quay xong! Nhấn \"Tải video WebM\" để lưu về máy.'};stream.getVideoTracks()[0].onended=()=>{if(recorder.state==='recording')recorder.stop()};save.hidden=true;recorder.start();start.disabled=true;stop.disabled=false;status.textContent='🔴 Đang quay màn hình. Hãy thao tác trên ứng dụng, sau đó nhấn Dừng quay.'}catch(e){status.textContent='Không thể bắt đầu quay. Vui lòng cấp quyền chia sẻ màn hình.'}};
stop.onclick=()=>{if(recorder?.state==='recording')recorder.stop()};window.addEventListener('pagehide',()=>stream?.getTracks().forEach(t=>t.stop()));
</script></html>'''
