"""Application-owned Vietnamese controls, modern cybersecurity theme, and rich presentation components."""
from html import escape
import streamlit as st
import streamlit.components.v1 as components

GITHUB = 'https://github.com/callmewin06-create/X-SENTINEL'

LIGHT = (
    '--xs-scheme:light;'
    '--xs-bg:#f8fafc;'
    '--xs-bg-ambient:radial-gradient(circle at 15% 10%, rgba(2, 132, 199, 0.05) 0%, transparent 40%), radial-gradient(circle at 85% 25%, rgba(99, 102, 241, 0.04) 0%, transparent 45%), #f8fafc;'
    '--xs-panel:rgba(255, 255, 255, 0.95);'
    '--xs-card:#ffffff;'
    '--xs-text:#0f172a;'
    '--xs-muted:#64748b;'
    '--xs-border:#e2e8f0;'
    '--xs-border-strong:#cbd5e1;'
    '--xs-soft:#f1f5f9;'
    '--xs-soft-hover:#e2e8f0;'
    '--xs-accent:#0369a1;'
    '--xs-on-accent:#ffffff;--xs-purple:#7e22ce;--xs-cyan:#0e7490;'
    '--xs-control-track:#64748b;--xs-control-thumb:#ffffff;'
    '--xs-accent-gradient:linear-gradient(135deg, #0369a1 0%, #1d4ed8 100%);'
    '--xs-accent-glow:rgba(2, 132, 199, 0.2);'
    '--xs-malware:#e11d48;'
    '--xs-malware-bg:rgba(225, 29, 72, 0.06);'
    '--xs-malware-border:rgba(225, 29, 72, 0.25);'
    '--xs-malware-gradient:linear-gradient(135deg, #e11d48 0%, #be123c 100%);'
    '--xs-benign:#059669;'
    '--xs-benign-bg:rgba(5, 150, 105, 0.06);'
    '--xs-benign-border:rgba(5, 150, 105, 0.25);'
    '--xs-benign-gradient:linear-gradient(135deg, #059669 0%, #047857 100%);'
    '--xs-alert:#d97706;'
    '--xs-alert-bg:rgba(217, 119, 6, 0.06);'
    '--xs-alert-border:rgba(217, 119, 6, 0.25);'
    '--xs-alert-gradient:linear-gradient(135deg, #d97706 0%, #b45309 100%);'
    '--xs-shadow:0 10px 30px -5px rgba(15, 23, 42, 0.08);'
    '--xs-card-shadow:0 2px 10px -1px rgba(15, 23, 42, 0.04), 0 1px 3px 0 rgba(15, 23, 42, 0.02);'
)

DARK = (
    '--xs-scheme:dark;'
    '--xs-bg:#080b11;'
    '--xs-bg-ambient:radial-gradient(circle at 15% 10%, rgba(14, 165, 233, 0.08) 0%, transparent 40%), radial-gradient(circle at 85% 25%, rgba(99, 102, 241, 0.07) 0%, transparent 45%), #080b11;'
    '--xs-panel:rgba(15, 23, 42, 0.75);'
    '--xs-card:rgba(30, 41, 59, 0.7);'
    '--xs-text:#f8fafc;'
    '--xs-muted:#94a3b8;'
    '--xs-border:rgba(255, 255, 255, 0.09);'
    '--xs-border-strong:rgba(56, 189, 248, 0.3);'
    '--xs-soft:rgba(24, 33, 47, 0.65);'
    '--xs-soft-hover:rgba(33, 46, 65, 0.8);'
    '--xs-accent:#38bdf8;'
    '--xs-on-accent:#06101f;--xs-purple:#c084fc;--xs-cyan:#22d3ee;'
    '--xs-control-track:#475569;--xs-control-thumb:#f8fafc;'
    '--xs-accent-gradient:linear-gradient(135deg, #38bdf8 0%, #60a5fa 100%);'
    '--xs-accent-glow:rgba(56, 189, 248, 0.25);'
    '--xs-malware:#ff3366;'
    '--xs-malware-bg:rgba(255, 51, 102, 0.09);'
    '--xs-malware-border:rgba(255, 51, 102, 0.35);'
    '--xs-malware-gradient:linear-gradient(135deg, #ff3366 0%, #c2185b 100%);'
    '--xs-benign:#10b981;'
    '--xs-benign-bg:rgba(16, 185, 129, 0.09);'
    '--xs-benign-border:rgba(16, 185, 129, 0.35);'
    '--xs-benign-gradient:linear-gradient(135deg, #10b981 0%, #059669 100%);'
    '--xs-alert:#f59e0b;'
    '--xs-alert-bg:rgba(245, 158, 11, 0.09);'
    '--xs-alert-border:rgba(245, 158, 11, 0.35);'
    '--xs-alert-gradient:linear-gradient(135deg, #f59e0b 0%, #d97706 100%);'
    '--xs-shadow:0 14px 40px -4px rgba(0, 0, 0, 0.65);'
    '--xs-card-shadow:0 4px 20px 0 rgba(0, 0, 0, 0.35), 0 1px 3px 0 rgba(0, 0, 0, 0.2);'
)


@st.dialog('Giới thiệu X-SENTINEL')
def about():
    st.markdown('''
    ### 🛡️ Hệ Thống Phòng Thủ X-SENTINEL (Apex SOC)
    **Phát hiện cửa hậu (Backdoor) trên bộ phân loại mã độc PE bằng tính nhất quán ngữ nghĩa đa góc nhìn.**

    - **Đơn vị thực hiện**: Nhóm 4 — Khoa An toàn Thông tin, Đại học FPT (Học kỳ Fall 2026).
    - **Cốt lõi khoa học & Bằng chứng kiểm toán**:
      1. Phân rã tệp PE thành 3 góc nhìn trực giao: **Cấu trúc ($V_S$)**, **Hành vi API ($V_B$)** và **Metadata ($V_M$)**.
      2. Module **$M_3$ (View-Mass Dominance)**: Khắc phục sự sụp đổ của TADR trước đòn tấn công phân tán $T_{\\text{spread}}$.
      3. Module **$M_4$ (Cross-View Semantic Consistency)**: Khai thác mâu thuẫn khi Header bị lừa là lành tính nhưng Import Table API kiên quyết tố cáo mã độc.
    - **Kiến trúc phân tán**: Backend FastAPI hiệu năng cao, CSDL kiểm toán PostgreSQL, Streamlit SOC Dashboard.
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
            '<div class="xs-brand-wrapper">'
            '<span class="xs-brand-shield">🛡️</span>'
            '<div class="xs-brand-text-group">'
            '<span class="xs-brand-title">X-SENTINEL</span>'
            '<span class="xs-brand-badge">SOC APEX v2.4</span>'
            '</div>'
            '</div>'
            '<div class="xs-brand-sub">HỆ THỐNG PHÁT HIỆN CỬA HẬU MÃ ĐỘC PE BẰNG TÍNH NHẤT QUÁN NGỮ NGHĨA ĐA GÓC NHÌN</div>'
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

    # Live SOC Status & Telemetry Bar
    api_status_html = (
        '<div class="xs-telemetry-badge xs-pulse-green">'
        '<span class="xs-pulse-dot"></span><span class="xs-pulse-wave"></span>'
        '<span>API & PostgreSQL Trực tuyến</span>'
        '</div>'
        if api_connected else
        '<div class="xs-telemetry-badge xs-pulse-amber">'
        '<span class="xs-pulse-dot"></span><span class="xs-pulse-wave"></span>'
        '<span>Chế độ Local (Chưa kết nối DB)</span>'
        '</div>'
    )
    st.markdown(
        f'<div class="xs-status-bar">'
        f'<div class="xs-status-left">'
        f'{api_status_html}'
        f'<span class="xs-pill xs-pill-blue">🔒 Kiểm toán tĩnh (Zero-Execution)</span>'
        f'<span class="xs-pill xs-pill-purple">⚡ LightGBM TreeSHAP</span>'
        f'<span class="xs-pill xs-pill-cyan">🎯 3 Góc nhìn trực giao (Vs, Vb, Vm)</span>'
        f'</div>'
        f'<div class="xs-status-right">'
        f'<span class="xs-status-meta">Tệp tối đa: <strong>50 MB</strong></span>'
        f'<span class="xs-status-meta">FPR mục tiêu: <strong>&le; 1.0%</strong></span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    if st.session_state.get('record_screen'):
        with st.container(key='screen_recorder_panel', border=True):
            st.markdown('**🎬 Quay video màn hình để báo cáo / thuyết minh**')
            st.caption('Chọn tab hoặc cửa sổ cần quay. Video được lưu trực tiếp dưới dạng WebM qua trình duyệt. Nhớ dừng và tải video trước khi tải lại trang.')
            components.html(RECORDER.replace('<style>','<style>:root{'+base+'}'+automatic), height=145)
    return page


def render_verdict_card(title, subtitle, verdict_text, is_danger, score, threshold, score_text, note):
    """Render a visual verdict card for Classification or Backdoor Alert."""
    theme_class = 'xs-verdict-danger' if is_danger else 'xs-verdict-safe'
    icon = '🚨' if is_danger else '🛡️'
    tag_text = 'CẦN XEM XÉT' if is_danger else 'KẾT QUẢ MÔ HÌNH'
    tag_class = 'xs-tag-danger' if is_danger else 'xs-tag-safe'
    
    # Progress gauge calculation
    pct = max(0.0, min(100.0, float(score) * 100))
    threshold_pct = max(0.0, min(100.0, float(threshold) * 100)) if threshold is not None else None
    delta_text=f'{score-threshold:+.4f}' if threshold is not None else 'Chưa lưu ngưỡng'
    threshold_text=f'{threshold:.4f}' if threshold is not None else 'Chưa lưu'
    marker=(f'<div class="xs-gauge-marker" style="left:{threshold_pct:.2f}%;" title="Ngưỡng {threshold_text}"><div class="xs-marker-pointer"></div></div>'
            if threshold is not None else '')
    scale_marker=(f'<span style="left:{threshold_pct:.2f}%;position:absolute;transform:translateX(-50%);">τ = {threshold_text}</span>'
                  if threshold is not None else '')
    
    html_card = f'''
    <div class="xs-verdict-box {theme_class}">
        <div class="xs-verdict-header">
            <div class="xs-verdict-title-group">
                <span class="xs-verdict-title">{escape(title)}</span>
                <span class="xs-verdict-subtitle">{escape(subtitle)}</span>
            </div>
            <span class="xs-verdict-tag {tag_class}">{tag_text}</span>
        </div>
        <div class="xs-verdict-body">
            <div class="xs-verdict-badge">
                <div class="xs-verdict-icon-wrap">{icon}</div>
                <div class="xs-verdict-text-group">
                    <span class="xs-verdict-text">{escape(verdict_text)}</span>
                    <span class="xs-verdict-delta">Độ lệch so với ngưỡng: <strong>{delta_text}</strong></span>
                </div>
            </div>
            <div class="xs-gauge-wrap">
                <div class="xs-gauge-labels">
                    <span class="xs-gauge-score-label">{escape(score_text)}: <strong>{score:.4f}</strong></span>
                    <span class="xs-gauge-thresh-label">Ngưỡng &tau;: <strong>{threshold_text}</strong></span>
                </div>
                <div class="xs-gauge-track">
                    <div class="xs-gauge-fill" style="width: {pct:.2f}%;"></div>
                    {marker}
                </div>
                <div class="xs-gauge-scale">
                    <span>0.00</span>
                    {scale_marker}
                    <span>1.00</span>
                </div>
            </div>
            <div class="xs-verdict-note">
                <span class="xs-note-icon">ℹ️</span>
                <span>{escape(note)}</span>
            </div>
        </div>
    </div>
    '''
    return html_card


def contribution_chart(contributions, names):
    """Modern gradient multi-view distribution chart with orthogonal telemetry."""
    rows = []
    view_gradients = {
        'structural': 'linear-gradient(90deg, #0284c7 0%, #38bdf8 100%)',
        'behavioral': 'linear-gradient(90deg, #8b5cf6 0%, #c084fc 100%)',
        'metadata': 'linear-gradient(90deg, #059669 0%, #34d399 100%)',
    }
    view_codes = {
        'structural': 'V_S · Cấu trúc PE',
        'behavioral': 'V_B · Hành vi API',
        'metadata': 'V_M · Siêu dữ liệu',
    }

    for key, fraction in contributions.items():
        value = 100 * float(fraction)
        width = max(0.0, min(100.0, value))
        grad = view_gradients.get(key, 'var(--xs-accent-gradient)')
        label = names.get(key, key)
        code = view_codes.get(key, key)
        
        rows.append(
            f'<div class="xs-bar-row">'
            f'<div class="xs-bar-label">'
            f'<div class="xs-view-text-group">'
            f'<span class="xs-view-name">{escape(label)}</span>'
            f'<span class="xs-view-code">{escape(code)}</span>'
            f'</div>'
            f'</div>'
            f'<div class="xs-bar-track-wrap">'
            f'<div class="xs-bar-track"><div class="xs-bar-fill" style="width:{width:.4f}%; background:{grad};"></div></div>'
            f'</div>'
            f'<div class="xs-bar-value"><span class="xs-value-pill">{value:.2f}%</span></div>'
            f'</div>'
        )

    st.markdown(
        f'<div class="xs-chart-card">'
        f'<div class="xs-chart-head">'
        f'<div class="xs-chart-title-group">'
        f'<span class="xs-chart-title">📊 Tỷ Trọng Đóng Góp Theo 3 Góc Nhìn (View-Mass Distribution)</span>'
        f'<span class="xs-chart-sub">Đo lường phân bố khối lượng giải thích tuyệt đối TreeSHAP theo 3 không gian trực giao</span>'
        f'</div>'
        f'<span class="xs-chart-badge">M3 Metric · View Attribution</span>'
        f'</div>'
        f'<div class="xs-chart-body">{"".join(rows)}</div>'
        f'<div class="xs-chart-foot">'
        f'<strong>Cách đọc M3:</strong> lấy tỷ trọng SHAP tuyệt đối lớn nhất trong ba nhóm. '
        f'Tỷ trọng cao cho biết nhóm có ảnh hưởng lớn; riêng biểu đồ này chưa chứng minh file mang trigger hay backdoor.'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )


CSS = r'''
/* Google Fonts Import */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* Global Reset & Base Typography */
html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}

code, kbd, samp, pre, .xs-mono {
    font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace !important;
}

h1, h2, h3, h4, h5, h6, .xs-brand-title, .xs-verdict-title, .xs-chart-title {
    font-family: 'Outfit', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

.block-container {
    max-width: 1240px;
    padding-top: 6.8rem;
    padding-bottom: 4rem;
}
[data-testid="stMain"] {
    scroll-padding-top: 6.8rem;
    background: var(--xs-bg-ambient) !important;
}

/* Header bar */
.st-key-app_header {
    position: fixed !important;
    top: 0; left: 0; right: 0;
    width: 100% !important; max-width: none !important;
    height: 78px; min-height: 78px;
    padding: 10px 80px !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    z-index: 999991;
    border: 0;
    border-bottom: 1px solid var(--xs-border);
    border-radius: 0;
    background: var(--xs-panel);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    box-shadow: var(--xs-shadow);
}

/* 2 buttons at the far left and far right edges */
.st-key-nav_menu, .st-key-settings_menu {
    position: absolute !important;
    top: 15px !important;
    width: 48px !important;
    height: 48px !important;
    min-width: 48px !important;
    max-width: 48px !important;
    min-height: 48px !important;
    max-height: 48px !important;
    z-index: 999992 !important;
    margin: 0 !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
.st-key-nav_menu {
    left: 24px !important;
    right: auto !important;
}
.st-key-settings_menu {
    right: 24px !important;
    left: auto !important;
}

/* Ensure inner popover wrappers have exact 48x48 size */
.st-key-nav_menu > div,
.st-key-settings_menu > div,
.st-key-nav_menu [data-testid="stPopover"],
.st-key-settings_menu [data-testid="stPopover"],
.st-key-nav_menu [data-testid="stPopoverButton"],
.st-key-settings_menu [data-testid="stPopoverButton"] {
    width: 48px !important;
    height: 48px !important;
    min-width: 48px !important;
    min-height: 48px !important;
    max-width: 48px !important;
    max-height: 48px !important;
    margin: 0 !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Force the button element to 48x48 square with ZERO padding and ZERO gap */
.st-key-nav_menu button,
.st-key-settings_menu button,
.st-key-nav_menu [data-testid^="baseButton"],
.st-key-settings_menu [data-testid^="baseButton"],
.st-key-nav_menu [data-testid*="Button"],
.st-key-settings_menu [data-testid*="Button"] {
    width: 48px !important;
    height: 48px !important;
    min-width: 48px !important;
    min-height: 48px !important;
    max-width: 48px !important;
    max-height: 48px !important;
    padding: 0 !important;
    margin: 0 !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
    border-radius: 12px !important;
    border: 1px solid var(--xs-border) !important;
    background: var(--xs-soft) !important;
    color: var(--xs-text) !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    gap: 0 !important;
    box-sizing: border-box !important;
    line-height: 1 !important;
    overflow: hidden !important;
    position: relative !important;
}

.st-key-nav_menu button:hover,
.st-key-settings_menu button:hover,
.st-key-nav_menu [data-testid^="baseButton"]:hover,
.st-key-settings_menu [data-testid^="baseButton"]:hover {
    border-color: var(--xs-accent) !important;
    background: var(--xs-soft-hover) !important;
    box-shadow: 0 0 16px var(--xs-accent-glow) !important;
    transform: translateY(-1px) !important;
}

/* Completely remove/hide any label text or chevron SVG from popover button */
.st-key-nav_menu button [data-testid="stMarkdownContainer"],
.st-key-settings_menu button [data-testid="stMarkdownContainer"],
.st-key-nav_menu button p,
.st-key-settings_menu button p,
.st-key-nav_menu button svg,
.st-key-settings_menu button svg,
.st-key-nav_menu button div:has(svg),
.st-key-settings_menu button div:has(svg) {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    position: absolute !important;
}

/* Center all child spans (the icon wrapper and the icon glyph) */
.st-key-nav_menu button span,
.st-key-settings_menu button span {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 auto !important;
    padding: 0 !important;
    width: 24px !important;
    height: 24px !important;
    line-height: 24px !important;
    text-align: center !important;
    vertical-align: middle !important;
}

/* Material symbol glyph text itself ('menu' / 'settings') */
.st-key-nav_menu button span span,
.st-key-settings_menu button span span,
.st-key-nav_menu [data-testid="stIconMaterial"],
.st-key-settings_menu [data-testid="stIconMaterial"] {
    font-size: 24px !important;
    line-height: 24px !important;
    width: 24px !important;
    height: 24px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 auto !important;
    padding: 0 !important;
    text-align: center !important;
}

.xs-menu-title {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.1em;
    color: var(--xs-muted);
    margin-bottom: 10px;
    text-transform: uppercase;
}
.st-key-nav_items [role="radiogroup"] label {
    min-height: 44px;
    align-items: center;
    font-size: 14.5px;
    font-weight: 600;
    border-radius: 10px;
    padding: 6px 12px;
    transition: all 0.2s ease;
}
.st-key-nav_items [role="radiogroup"] label:hover {
    background: var(--xs-soft);
    color: var(--xs-accent);
}

/* Brand header */
.xs-brand {
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    white-space: nowrap !important;
    padding: 0 4px;
}
.xs-brand-wrapper {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    white-space: nowrap !important;
}
.xs-brand-shield {
    font-size: 25px;
    filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.4));
}
.xs-brand-text-group {
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap !important;
}
.xs-brand-title {
    font-size: 26px;
    font-weight: 900;
    letter-spacing: 0.03em;
    line-height: 1;
    background: var(--xs-accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    white-space: nowrap !important;
}
.xs-brand-badge {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.08em;
    padding: 2px 7px;
    border-radius: 6px;
    background: rgba(56, 189, 248, 0.12);
    color: var(--xs-accent);
    border: 1px solid rgba(56, 189, 248, 0.3);
    text-transform: uppercase;
    white-space: nowrap !important;
}
.xs-brand-sub {
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.06em;
    color: var(--xs-muted);
    text-transform: uppercase;
    margin-top: 2px;
    white-space: nowrap !important;
}

@media(max-width: 768px) {
    .block-container {padding-top: 5.8rem;}
    .st-key-app_header {padding: 8px 60px; height: 68px; min-height: 68px;}
    .st-key-nav_menu {left: 12px !important; top: 10px !important;}
    .st-key-settings_menu {right: 12px !important; top: 10px !important;}
    .xs-brand-title {font-size: 21px;}
    .xs-brand-badge {display: none;}
    .xs-brand-sub {display: none;}
}

/* Live Telemetry Status Bar */
.xs-status-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    padding: 10px 18px;
    border-radius: 12px;
    background: var(--xs-soft);
    border: 1px solid var(--xs-border);
    margin-bottom: 24px;
    font-size: 13px;
    color: var(--xs-text);
    box-shadow: var(--xs-card-shadow);
}
.xs-status-left {display: flex; align-items: center; gap: 8px; flex-wrap: wrap;}
.xs-status-right {display: flex; align-items: center; gap: 14px; color: var(--xs-muted); font-size: 12.5px;}
.xs-status-meta strong {color: var(--xs-text);}

.xs-telemetry-badge {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 700;
}
.xs-pulse-green {
    background: var(--xs-benign-bg);
    color: var(--xs-benign);
    border: 1px solid var(--xs-benign-border);
}
.xs-pulse-amber {
    background: var(--xs-alert-bg);
    color: var(--xs-alert);
    border: 1px solid var(--xs-alert-border);
}
.xs-pulse-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: currentColor;
    position: relative;
    z-index: 2;
}
.xs-pulse-wave {
    position: absolute;
    left: 12px; top: 50%;
    width: 8px; height: 8px;
    border-radius: 50%;
    background: currentColor;
    transform: translateY(-50%);
    animation: sonar-wave 1.8s cubic-bezier(0.24, 0, 0.38, 1) infinite;
    z-index: 1;
}

@keyframes sonar-wave {
    0% { transform: translateY(-50%) scale(1); opacity: 0.8; }
    100% { transform: translateY(-50%) scale(3.2); opacity: 0; }
}

.xs-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 600;
}
.xs-pill-blue {background: rgba(2, 132, 199, 0.12); color: var(--xs-accent); border: 1px solid rgba(2, 132, 199, 0.3);}
.xs-pill-purple {background: rgba(168, 85, 247, 0.12); color: var(--xs-purple); border: 1px solid rgba(168, 85, 247, 0.3);}
.xs-pill-cyan {background: rgba(6, 182, 212, 0.12); color: var(--xs-cyan); border: 1px solid rgba(6, 182, 212, 0.3);}

/* Dual Forensic Verdict Cards */
.xs-verdict-box {
    border-radius: 16px;
    padding: 22px 24px;
    margin-bottom: 16px;
    border: 1px solid var(--xs-border);
    background: var(--xs-panel);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: var(--xs-card-shadow);
    transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease;
    position: relative;
    overflow: hidden;
}
.xs-verdict-box:hover {
    transform: translateY(-3px);
    box-shadow: var(--xs-shadow);
}
.xs-verdict-danger {
    border-left: 6px solid var(--xs-malware);
    background: linear-gradient(180deg, var(--xs-panel) 0%, var(--xs-malware-bg) 100%);
    box-shadow: 0 4px 20px 0 rgba(255, 51, 102, 0.12);
}
.xs-verdict-safe {
    border-left: 6px solid var(--xs-benign);
    background: linear-gradient(180deg, var(--xs-panel) 0%, var(--xs-benign-bg) 100%);
    box-shadow: 0 4px 20px 0 rgba(16, 185, 129, 0.12);
}

.xs-verdict-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
    gap: 12px;
}
.xs-verdict-title-group {display: flex; flex-direction: column; gap: 2px;}
.xs-verdict-title {
    font-size: 13.5px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--xs-muted);
}
.xs-verdict-subtitle {
    font-size: 12px;
    font-weight: 500;
    color: var(--xs-muted);
}
.xs-verdict-tag {
    font-size: 10.5px;
    font-weight: 800;
    letter-spacing: 0.06em;
    padding: 3px 9px;
    border-radius: 6px;
    text-transform: uppercase;
}
.xs-tag-danger {
    background: var(--xs-malware-bg);
    color: var(--xs-malware);
    border: 1px solid var(--xs-malware-border);
}
.xs-tag-safe {
    background: var(--xs-benign-bg);
    color: var(--xs-benign);
    border: 1px solid var(--xs-benign-border);
}

.xs-verdict-badge {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 16px;
}
.xs-verdict-icon-wrap {
    font-size: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.xs-verdict-text-group {display: flex; flex-direction: column; gap: 2px;}
.xs-verdict-text {
    font-size: 24px;
    font-weight: 800;
    letter-spacing: -0.01em;
    color: var(--xs-text);
    font-family: 'Outfit', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}
.xs-verdict-danger .xs-verdict-text {color: var(--xs-malware);}
.xs-verdict-safe .xs-verdict-text {color: var(--xs-benign);}
.xs-verdict-delta {
    font-size: 13px;
    color: var(--xs-muted);
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}
.xs-verdict-delta strong {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    font-weight: 700;
    color: var(--xs-text);
}

/* Gauge Bar */
.xs-gauge-wrap {margin-bottom: 14px;}
.xs-gauge-labels {
    display: flex;
    justify-content: space-between;
    font-size: 13.5px;
    color: var(--xs-muted);
    margin-bottom: 8px;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}
.xs-gauge-score-label strong {color: var(--xs-text); font-size: 14px; font-weight: 700; font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;}
.xs-gauge-thresh-label strong {color: var(--xs-text); font-size: 14px; font-weight: 700; font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;}

.xs-gauge-track {
    position: relative;
    height: 16px;
    border-radius: 999px;
    background: var(--xs-soft);
    border: 1px solid var(--xs-border);
    overflow: visible;
}
.xs-gauge-fill {
    height: 100%;
    border-radius: 999px;
    background: var(--xs-accent-gradient);
    transition: width 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
.xs-verdict-danger .xs-gauge-fill {
    background: linear-gradient(90deg, #f59e0b 0%, #ff3366 100%);
    box-shadow: 0 0 12px rgba(255, 51, 102, 0.4);
}
.xs-verdict-safe .xs-gauge-fill {
    background: linear-gradient(90deg, #06b6d4 0%, #10b981 100%);
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
}
.xs-gauge-marker {
    position: absolute;
    top: -5px;
    bottom: -5px;
    width: 3px;
    background: var(--xs-text);
    border-radius: 2px;
    box-shadow: 0 0 8px rgba(0, 0, 0, 0.5);
    z-index: 3;
}
.xs-marker-pointer {
    position: absolute;
    top: -6px;
    left: 50%;
    transform: translateX(-50%);
    width: 0; height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid var(--xs-text);
}
.xs-gauge-scale {
    display: flex;
    justify-content: space-between;
    position: relative;
    font-size: 11px;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    color: var(--xs-muted);
    margin-top: 6px;
}

.xs-verdict-note {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    font-size: 12.5px;
    line-height: 1.5;
    color: var(--xs-muted);
    background: var(--xs-soft);
    padding: 8px 12px;
    border-radius: 8px;
    border: 1px solid var(--xs-border);
}
.xs-note-icon {font-size: 14px;}

/* Multi-View Mass Chart Card */
.xs-chart-card {
    padding: 24px;
    border-radius: 16px;
    background: var(--xs-panel);
    border: 1px solid var(--xs-border);
    box-shadow: var(--xs-card-shadow);
    margin: 18px 0 22px;
    backdrop-filter: blur(16px);
}
.xs-chart-head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 12px;
}
.xs-chart-title-group {display: flex; flex-direction: column; gap: 3px;}
.xs-chart-title {
    font-size: 17.5px;
    font-weight: 800;
    color: var(--xs-text);
}
.xs-chart-sub {
    font-size: 12.5px;
    color: var(--xs-muted);
}
.xs-chart-badge {
    font-size: 11px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 8px;
    background: var(--xs-soft);
    color: var(--xs-accent);
    border: 1px solid var(--xs-border);
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.xs-bar-row {
    display: grid;
    grid-template-columns: 280px 1fr 85px;
    gap: 18px;
    align-items: center;
    min-height: 52px;
    padding: 8px 0;
    border-bottom: 1px dashed var(--xs-border);
}
.xs-bar-row:last-child {border-bottom: none;}
.xs-bar-label {
    display: flex;
    align-items: center;
    gap: 12px;
}
.xs-view-icon {font-size: 22px;}
.xs-view-text-group {display: flex; flex-direction: column;}
.xs-view-name {
    font-size: 14.5px;
    font-weight: 700;
    color: var(--xs-text);
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}
.xs-view-code {
    font-size: 12px;
    color: var(--xs-muted);
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    margin-top: 2px;
}

.xs-bar-track-wrap {width: 100%;}
.xs-bar-track {
    height: 18px;
    border-radius: 999px;
    background: var(--xs-soft);
    border: 1px solid var(--xs-border);
    overflow: hidden;
}
.xs-bar-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}
.xs-bar-value {text-align: right;}
.xs-value-pill {
    display: inline-block;
    padding: 3px 9px;
    border-radius: 6px;
    background: var(--xs-soft);
    border: 1px solid var(--xs-border);
    font-size: 13.5px;
    font-weight: 700;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    color: var(--xs-text);
}
.xs-chart-foot {
    font-size: 12.5px;
    color: var(--xs-muted);
    margin-top: 18px;
    line-height: 1.6;
    padding: 12px 14px;
    background: var(--xs-soft);
    border-radius: 10px;
    border: 1px solid var(--xs-border);
}

@media(max-width: 768px) {
    .xs-bar-row {grid-template-columns: 1fr 70px; gap: 8px;}
    .xs-bar-label {grid-column: 1 / -1;}
}

/* Feature Force Cards */
.xs-feature-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
    margin: 14px 0 18px;
}
@media(max-width: 768px) {
    .xs-feature-grid {grid-template-columns: 1fr;}
}
.xs-force-col {
    padding: 18px;
    border-radius: 14px;
    background: var(--xs-soft);
    border: 1px solid var(--xs-border);
}
.xs-force-head {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 800;
    margin-bottom: 14px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.xs-force-danger .xs-force-head {color: var(--xs-malware);}
.xs-force-safe .xs-force-head {color: var(--xs-benign);}
.xs-force-item {
    padding: 12px 14px;
    background: var(--xs-panel);
    border: 1px solid var(--xs-border);
    border-radius: 10px;
    margin-bottom: 10px;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.xs-force-item:hover {
    transform: translateY(-2px);
    border-color: var(--xs-border-strong);
}
.xs-force-item-title {
    font-size: 13.5px;
    font-weight: 700;
    color: var(--xs-text);
    margin-bottom: 5px;
}
.xs-force-item-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12.5px;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    color: var(--xs-muted);
}
.xs-shap-pill {
    padding: 2px 7px;
    border-radius: 5px;
    font-weight: 700;
}
.xs-shap-malware {background: var(--xs-malware-bg); color: var(--xs-malware); border: 1px solid var(--xs-malware-border);}
.xs-shap-benign {background: var(--xs-benign-bg); color: var(--xs-benign); border: 1px solid var(--xs-benign-border);}

/* Section Headings */
.xs-section-title {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--xs-muted);
    margin: 28px 0 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--xs-border);
}
.xs-section-title span {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: var(--xs-accent-gradient);
    color: var(--xs-on-accent);
    font-size: 11px;
    font-weight: 900;
    padding: 3px 9px;
    border-radius: 6px;
    letter-spacing: 0.05em;
    box-shadow: 0 2px 8px var(--xs-accent-glow);
}

/* KPI Summary Cards */
.xs-kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    margin-bottom: 26px;
}
.xs-kpi-card {
    background: var(--xs-panel);
    border: 1px solid var(--xs-border);
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: var(--xs-card-shadow);
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(16px);
    transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease;
}
.xs-kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--xs-shadow);
}
.xs-kpi-label {
    font-size: 12px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--xs-muted);
    margin-bottom: 8px;
}
.xs-kpi-val {
    font-size: 30px;
    font-weight: 900;
    color: var(--xs-text);
    line-height: 1.1;
    margin-bottom: 6px;
    font-family: 'Outfit', sans-serif !important;
}
.xs-kpi-sub {
    font-size: 12px;
    color: var(--xs-muted);
}
.xs-kpi-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: var(--xs-accent-gradient);
}
.xs-kpi-danger::before { background: var(--xs-malware-gradient); }
.xs-kpi-danger .xs-kpi-val { color: var(--xs-malware); }
.xs-kpi-alert::before { background: var(--xs-alert-gradient); }
.xs-kpi-alert .xs-kpi-val { color: var(--xs-alert); }
.xs-kpi-safe::before { background: var(--xs-benign-gradient); }
.xs-kpi-safe .xs-kpi-val { color: var(--xs-benign); }

/* Metadata Chips Bar */
.xs-meta-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
    margin-bottom: 20px;
    padding: 12px 16px;
    background: var(--xs-soft);
    border-radius: 12px;
    border: 1px solid var(--xs-border);
    box-shadow: var(--xs-card-shadow);
}
.xs-meta-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: var(--xs-text);
}
.xs-meta-chip strong {
    color: var(--xs-muted);
    font-size: 11.5px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.xs-meta-chip code {
    background: var(--xs-panel);
    padding: 2px 7px;
    border-radius: 6px;
    font-size: 12px;
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
    backdrop-filter: blur(20px);
}
[data-testid="stPopoverBody"]>div {background: var(--xs-panel) !important;}

/* Metric default override */
[data-testid="stMetric"] {
    background: var(--xs-panel);
    border: 1px solid var(--xs-border);
    border-radius: 14px;
    padding: 18px 20px;
    color: var(--xs-text);
    box-shadow: var(--xs-card-shadow);
    transition: transform 0.2s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    border-color: var(--xs-border-strong);
}
[data-testid="stMetricLabel"] p {
    font-size: 12.5px !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    color: var(--xs-muted) !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.85rem !important;
    font-weight: 900 !important;
    font-family: 'Outfit', sans-serif !important;
    color: var(--xs-text) !important;
}

/* Form Controls & Inputs */
[data-baseweb="select"]>div, [data-baseweb="input"], input:not([type="checkbox"]):not([type="radio"]), textarea {
    background: var(--xs-panel) !important;
    color: var(--xs-text) !important;
    border-color: var(--xs-border) !important;
    border-radius: 10px !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
[data-baseweb="select"]>div:hover, [data-baseweb="input"]:hover, input:not([type="checkbox"]):not([type="radio"]):hover {
    border-color: var(--xs-border-strong) !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: var(--xs-panel) !important;
    color: var(--xs-text) !important;
    border: 2px dashed var(--xs-border) !important;
    border-radius: 14px !important;
    padding: 24px !important;
    transition: all 0.25s ease !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--xs-accent) !important;
    background: var(--xs-soft) !important;
    box-shadow: 0 0 16px var(--xs-accent-glow);
}
button[kind="primary"] {
    background: var(--xs-accent-gradient) !important;
    border: none !important;
    color: var(--xs-on-accent) !important;
    font-weight: 800 !important;
    letter-spacing: 0.03em !important;
    border-radius: 12px !important;
    padding: 12px 28px !important;
    box-shadow: 0 6px 18px 0 var(--xs-accent-glow) !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
button[kind="primary"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px 0 var(--xs-accent-glow) !important;
}
button[kind="secondary"] {
    background: var(--xs-panel) !important;
    color: var(--xs-text) !important;
    border: 1px solid var(--xs-border) !important;
    border-radius: 12px !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease !important;
}
button[kind="secondary"]:hover {
    background: var(--xs-soft) !important;
    border-color: var(--xs-border-strong) !important;
    transform: translateY(-1px);
}

/* Dataframe & Tables */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid var(--xs-border) !important;
    box-shadow: var(--xs-card-shadow) !important;
}
'''

CSS += r'''
/* App and native components share the selected palette, including OS mode. */
html {color-scheme:var(--xs-scheme);}
/* BaseWeb paints these controls itself; the OS/Streamlit theme can differ
   from our chosen palette. Style the visible track/dot, not hidden inputs. */
[data-baseweb="checkbox"]:has(>input[type="checkbox"])>div:first-child {
    background:var(--xs-control-track) !important;
    box-shadow:inset 0 0 0 1px var(--xs-control-track);
}
[data-baseweb="checkbox"]:has(>input[type="checkbox"])>div:first-child>div {
    background:var(--xs-control-thumb) !important;
    box-shadow:0 0 0 1px var(--xs-control-track);
}
[data-baseweb="checkbox"]:has(>input:checked)>div:first-child {
    background:var(--xs-accent) !important;
    box-shadow:inset 0 0 0 1px var(--xs-accent);
}
[data-baseweb="checkbox"]:has(>input:checked)>div:first-child>div {
    background:var(--xs-on-accent) !important;
    box-shadow:0 0 0 1px var(--xs-accent);
}
[data-baseweb="radio"]>div:first-child {
    background:var(--xs-card) !important;
    border:2px solid var(--xs-control-track) !important;
}
[data-baseweb="radio"]>div:first-child>div {background:transparent !important;}
[data-baseweb="radio"]:has(>input:checked)>div:first-child {
    background:var(--xs-accent) !important;
    border-color:var(--xs-accent) !important;
}
[data-baseweb="radio"]:has(>input:checked)>div:first-child>div {
    background:var(--xs-on-accent) !important;
}
[data-baseweb="checkbox"]:has(>input:focus-visible)>:first-child,
[data-baseweb="radio"]:has(>input:focus-visible)>:first-child {
    outline:2px solid var(--xs-accent);outline-offset:3px;
}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stWidgetLabel"] p,
[data-testid="stCheckbox"] label,
[data-testid="stRadio"] label,
[data-testid="stExpander"] summary,
[data-testid="stAlertContentInfo"], [data-testid="stAlertContentWarning"],
[data-testid="stAlertContentError"], [data-testid="stAlertContentSuccess"] {
    color:var(--xs-text) !important;
}
[data-testid="stCaptionContainer"] p {color:var(--xs-muted) !important;}
[data-baseweb="select"] span, [data-baseweb="select"] input,
[data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"], [role="option"] {
    color:var(--xs-text) !important;
    background-color:var(--xs-card) !important;
}
[role="option"]:hover, [aria-selected="true"][role="option"] {background:var(--xs-soft-hover) !important;}
[data-testid="stExpander"], [data-testid="stCode"], [data-testid="stCode"] pre,
[data-testid="stCode"] code, [data-testid="stJson"] {
    color:var(--xs-text) !important;
    background:var(--xs-soft) !important;
    border-color:var(--xs-border) !important;
}
[data-testid="stCode"] pre, [data-testid="stCode"] code {overflow-wrap:anywhere !important;white-space:pre-wrap !important;}
input::placeholder, textarea::placeholder {color:var(--xs-muted) !important;opacity:1;}
button[kind="secondary"] p, button[kind="secondary"] span {color:var(--xs-text) !important;}
button[kind="primary"] p, button[kind="primary"] span {color:var(--xs-on-accent) !important;}
[data-testid="stMarkdownContainer"] a {color:var(--xs-accent) !important;}
[data-testid="stCode"] button {color:var(--xs-text) !important;}
.xs-meta-chip, .xs-view-text-group {min-width:0;}
.xs-meta-chip code {overflow-wrap:anywhere;word-break:break-all;}
.xs-data-table {overflow:auto;max-height:580px;border:1px solid var(--xs-border);border-radius:10px;margin:10px 0 18px;background:var(--xs-panel);font-family:'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;}
.xs-data-table table {border-collapse:collapse;width:100%;font-size:13.5px;color:var(--xs-text);font-family:'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;}
.xs-data-table th {background:var(--xs-soft);color:var(--xs-text);position:sticky;top:0;text-align:left;font-size:12.5px !important;font-weight:700 !important;letter-spacing:0.03em !important;font-family:'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;}
.xs-data-table th,.xs-data-table td {padding:10px 14px;border-bottom:1px solid var(--xs-border);vertical-align:middle;overflow-wrap:anywhere;font-family:'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;}
.xs-data-table td {max-width:340px;min-width:90px;font-size:13.5px !important;}
.xs-data-table tr:hover td {background:var(--xs-soft-hover);}
'''

RECORDER = '''<!doctype html><html lang="vi"><meta charset="utf-8"><style>body{font:13px sans-serif;color:var(--xs-text);background:var(--xs-bg);margin:4px}button,a{padding:8px 12px;margin:3px;border-radius:6px;border:1px solid var(--xs-border);cursor:pointer;font-weight:600}#start{background:#0284c7;color:#fff;border-color:#0284c7}#stop{background:var(--xs-soft);color:var(--xs-text)}#save{background:#059669;color:#fff;text-decoration:none;display:inline-block}#status{margin:8px;font-size:12.5px;color:var(--xs-muted);line-height:1.4}</style>
<button id="start">▶ Bắt đầu quay</button><button id="stop" disabled>⏹ Dừng quay</button><div id="status">Sẵn sàng quay màn hình.</div><a id="save" hidden>💾 Tải video WebM</a>
<script>
let recorder,stream,url;const start=document.querySelector('#start'),stop=document.querySelector('#stop'),status=document.querySelector('#status'),save=document.querySelector('#save');
start.onclick=async()=>{try{if(!navigator.mediaDevices?.getDisplayMedia||!window.MediaRecorder)throw Error('Trình duyệt chưa hỗ trợ quay màn hình.');stream=await navigator.mediaDevices.getDisplayMedia({video:true,audio:false});const chunks=[];recorder=new MediaRecorder(stream);recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};recorder.onstop=()=>{if(url)URL.revokeObjectURL(url);url=URL.createObjectURL(new Blob(chunks,{type:recorder.mimeType}));save.href=url;save.download='X_SENTINEL_demo.webm';save.hidden=false;stream.getTracks().forEach(t=>t.stop());start.disabled=false;stop.disabled=true;status.textContent='Đã quay xong! Nhấn \"Tải video WebM\" để lưu về máy.'};stream.getVideoTracks()[0].onended=()=>{if(recorder.state==='recording')recorder.stop()};save.hidden=true;recorder.start();start.disabled=true;stop.disabled=false;status.textContent='🔴 Đang quay màn hình. Hãy thao tác trên ứng dụng, sau đó nhấn Dừng quay.'}catch(e){status.textContent='Không thể bắt đầu quay. Vui lòng cấp quyền chia sẻ màn hình.'}};
stop.onclick=()=>{if(recorder?.state==='recording')recorder.stop()};window.addEventListener('pagehide',()=>stream?.getTracks().forEach(t=>t.stop()));
</script></html>'''
