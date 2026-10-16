"""Application-owned Vietnamese controls and theme; no Streamlit internals."""
from html import escape
import streamlit as st
import streamlit.components.v1 as components

GITHUB = 'https://github.com/callmewin06-create/X-SENTINEL'
LIGHT = '--xs-bg:#f7f9fc;--xs-panel:#ffffff;--xs-text:#172b4d;--xs-muted:#52667a;--xs-border:#ced8e4;--xs-soft:#eaf4f6;--xs-accent:#087f8c;'
DARK = '--xs-bg:#0e1117;--xs-panel:#19212c;--xs-text:#eef3fa;--xs-muted:#becbda;--xs-border:#405069;--xs-soft:#163a42;--xs-accent:#53ccd0;'


@st.dialog('Giới thiệu X-SENTINEL')
def about():
    st.write('Phân tích cấu trúc file PE bằng mô hình học máy và kiểm tra dấu hiệu trigger theo phương pháp nghiên cứu của nhóm.')
    st.caption('Hai kết luận phân loại file và cảnh báo trigger được trình bày riêng. Không có cảnh báo không chứng nhận file an toàn.')
    st.link_button('Mở GitHub của nhóm', GITHUB)


def controls(api_connected=False):
    with st.container(key='app_header'):
        with st.container(key='nav_menu'):
            with st.popover('Điều hướng', icon=':material/menu:', help='Điều hướng'):
                with st.container(key='nav_items'):
                    page = st.radio('Điều hướng', ['Phân tích', 'Lịch sử', 'Nghiên cứu'], key='page', label_visibility='collapsed')
        st.markdown('<div class="xs-brand" role="banner" aria-label="X-SENTINEL">'
                    '<div class="xs-brand-name">X-SENTINEL</div></div>', unsafe_allow_html=True)
        with st.container(key='settings_menu'):
            with st.popover('Cài đặt', icon=':material/settings:', help='Cài đặt'):
                choice = st.selectbox('Giao diện', ['Theo hệ thống', 'Sáng', 'Tối'], key='appearance')
                st.button('Tải lại giao diện', help='Làm mới phần hiển thị, giữ kết quả phân tích trong phiên.', key='refresh_app')
                if st.button('Giới thiệu', key='about_app'):
                    about()
                st.checkbox('Quay video màn hình', key='record_screen')
    base = DARK if choice == 'Tối' else LIGHT
    automatic = f'@media(prefers-color-scheme:dark){{:root{{{DARK}}}}}' if choice == 'Theo hệ thống' else ''
    st.markdown('<style>:root{' + base + '}' + automatic + CSS + '</style>', unsafe_allow_html=True)
    connection = 'API + lịch sử dùng chung' if api_connected else 'Local · kết quả chưa lưu database'
    st.caption(connection + ' · File được đọc, không được thực thi. Chưa có cảnh báo không chứng nhận an toàn.')
    if st.session_state.get('record_screen'):
        # Keep the recorder outside the popover so closing settings does not remove its iframe.
        with st.container(key='screen_recorder_panel', border=True):
            st.markdown('**Quay video màn hình**')
            st.caption('Chọn tab hoặc cửa sổ cần quay. Video được tải trực tiếp bằng trình duyệt. Dừng và tải video trước khi tải lại trang hoặc tắt bảng quay.')
            components.html(RECORDER, height=145)
    return page


def contribution_chart(contributions, names):
    rows = []
    for key, fraction in contributions.items():
        value = 100 * float(fraction)
        width = max(0, min(100, value))
        rows.append(f'<div class="xs-bar-row"><div class="xs-bar-label">{escape(names.get(key, key))}</div>'
                    f'<div class="xs-bar-track"><div class="xs-bar-fill" style="width:{width:.6f}%"></div></div>'
                    f'<strong class="xs-bar-value">{value:.2f}%</strong></div>')
    st.markdown('<div class="xs-chart" role="img" aria-label="Tỷ trọng ảnh hưởng tuyệt đối theo nhóm">'
                '<div class="xs-chart-title">Tỷ trọng ảnh hưởng theo nhóm</div>' + ''.join(rows) +
                '<div class="xs-chart-foot">Độ dài thanh theo thang 0–100%; ảnh hưởng nhiều không đồng nghĩa nghiêng về mã độc.</div></div>',
                unsafe_allow_html=True)


CSS = r'''
.block-container {max-width:1180px;padding-top:6rem;padding-bottom:3rem;}
[data-testid="stMain"] {scroll-padding-top:6rem;}
/* Reserve space above the page and keep menus below Streamlit's popover layer. */
.st-key-app_header {position:fixed!important;top:0;left:0;right:0;width:auto!important;max-width:none!important;height:72px;min-height:72px;padding:12px 76px;justify-content:center;z-index:999991;border:0;border-bottom:1px solid var(--xs-border);border-radius:0;background:linear-gradient(115deg,var(--xs-panel),var(--xs-soft));box-shadow:0 4px 14px #00000020;}
.st-key-nav_menu,.st-key-settings_menu {position:absolute!important;top:11px;width:48px!important;z-index:2;}
.st-key-nav_menu {left:16px;}
.st-key-settings_menu {right:16px;}
.st-key-nav_menu [data-testid="stPopover"] button,.st-key-settings_menu [data-testid="stPopover"] button {width:48px;height:48px;padding:0;justify-content:center;border-radius:12px;}
.st-key-nav_menu [data-testid="stPopover"] button [data-testid="stMarkdownContainer"],.st-key-settings_menu [data-testid="stPopover"] button [data-testid="stMarkdownContainer"] {position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap;}
.st-key-nav_menu [data-testid="stPopoverButton"]>div:has(svg),.st-key-settings_menu [data-testid="stPopoverButton"]>div:has(svg) {display:none;}
.st-key-nav_items [role="radiogroup"] label {min-height:40px;align-items:center;}
.st-key-app_header [data-testid="stMarkdownContainer"]:has(>.xs-brand) {margin-bottom:0;}
.xs-brand {text-align:center;}
.xs-brand-name {font-size:30px;font-weight:800;letter-spacing:0.035em;line-height:1.2;color:var(--xs-text);}
@media(max-width:650px){.block-container{padding-top:5.5rem}[data-testid="stMain"]{scroll-padding-top:5.5rem}.st-key-app_header{padding:8px 60px;height:64px;min-height:64px}.st-key-nav_menu{left:8px}.st-key-settings_menu{right:8px}.xs-brand-name{font-size:clamp(20px,5.4vw,26px)}.st-key-nav_menu,.st-key-settings_menu{top:7px}}
h1 {letter-spacing:-0.035em;}
#MainMenu, [data-testid="stMainMenu"], .stAppDeployButton, .stDeployButton {display:none!important;}
[data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"] {background:var(--xs-bg)!important;color:var(--xs-text)!important;}
[data-testid="stSidebar"], [data-testid="stPopoverBody"], [role="dialog"] {background:var(--xs-panel)!important;color:var(--xs-text)!important;}
[data-testid="stPopoverBody"]>div {background:var(--xs-panel)!important;color:var(--xs-text)!important;}
[data-baseweb="tooltip"],[data-baseweb="tooltip"]>div {background:var(--xs-panel)!important;color:var(--xs-text)!important;}
[role="dialog"]>div, [role="dialog"]>button {color:var(--xs-text)!important;}
[data-testid="stLinkButton"] a {background:var(--xs-panel)!important;color:var(--xs-text)!important;border-color:var(--xs-border)!important;}
[data-testid="stExpander"] summary svg {color:var(--xs-text)!important;}
[data-testid="stSidebar"] {border-right:1px solid var(--xs-border);}
[data-testid="stMarkdownContainer"], [data-testid="stHeading"], [data-testid="stWidgetLabel"], [data-testid="stMetricLabel"], [data-testid="stMetricValue"], [data-testid="stStatusWidget"], [data-testid="stExpander"] summary {color:var(--xs-text)!important;}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3, [data-testid="stWidgetLabel"] p {color:inherit!important;}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {color:var(--xs-muted)!important;opacity:1!important;}
[data-testid="stMetric"] {background:var(--xs-panel);border:1px solid var(--xs-border);border-radius:12px;padding:18px;color:var(--xs-text);}
[data-testid="stMetricValue"] {font-size:1.65rem;}
[data-testid="stMetricLabel"] p, [data-testid="stMetricValue"] div {color:var(--xs-text)!important;}
[data-testid="stExpander"] {border-color:var(--xs-border)!important;}
[data-baseweb="select"]>div, [data-baseweb="input"], input, textarea {background:var(--xs-panel)!important;color:var(--xs-text)!important;border-color:var(--xs-border)!important;}
[data-baseweb="select"] span {color:var(--xs-text)!important;}
[data-testid="stFileUploaderDropzone"] {background:var(--xs-panel)!important;color:var(--xs-text)!important;border-color:var(--xs-border)!important;}
button[kind="secondary"], [data-testid="stPopover"] button {background:var(--xs-panel)!important;color:var(--xs-text)!important;border-color:var(--xs-border)!important;}
[data-testid="stRadio"] label, [data-testid="stCheckbox"] label {color:var(--xs-text)!important;}
[data-testid="stFileUploaderDropzone"] button {font-size:0;}
[data-testid="stFileUploaderDropzone"] button::after {content:"Chọn file";font-size:14px;}
[data-testid="stFileUploaderDropzoneInstructions"]>div>span {font-size:0;}
[data-testid="stFileUploaderDropzoneInstructions"]>div>span::after {content:"Kéo và thả file vào đây";font-size:14px;}
[data-testid="stFileUploaderDropzoneInstructions"] small {font-size:0;}
[data-testid="stFileUploaderDropzoneInstructions"] small::after {content:"Tối đa 50 MB mỗi file";font-size:12px;}
.xs-chart {padding:20px;border:1px solid var(--xs-border);border-radius:12px;background:var(--xs-panel);margin:8px 0 16px;}
.xs-chart-title {font-size:18px;font-weight:600;margin-bottom:16px;color:var(--xs-text);}
.xs-bar-row {display:grid;grid-template-columns:minmax(180px,260px) minmax(80px,1fr) 76px;gap:16px;align-items:center;min-height:64px;}
.xs-bar-label {font-size:16px;line-height:1.5;white-space:normal;overflow-wrap:anywhere;color:var(--xs-text);}
.xs-bar-track {height:25px;border-radius:5px;background:var(--xs-soft);overflow:hidden;}
.xs-bar-fill {height:100%;background:var(--xs-accent);border-radius:5px;}
.xs-bar-value {text-align:right;font-size:16px;color:var(--xs-text);}
.xs-chart-foot {font-size:14px;color:var(--xs-muted);margin-top:16px;line-height:1.5;}
@media(max-width:650px){.xs-bar-row{grid-template-columns:1fr 70px;gap:8px;margin-bottom:16px}.xs-bar-label{grid-column:1/-1}.xs-bar-track{grid-column:1}.xs-bar-value{grid-column:2}}
'''

RECORDER = '''<!doctype html><html lang="vi"><meta charset="utf-8"><style>body{font:14px sans-serif;color:#172b4d;background:#fff;margin:4px}button,a{padding:9px;margin:3px;border-radius:6px;border:1px solid #aab8c6;cursor:pointer}#status{margin:8px;line-height:1.4}</style>
<button id="start">Bắt đầu quay</button><button id="stop" disabled>Dừng quay</button><div id="status">Chưa bắt đầu quay.</div><a id="save" hidden>Tải video</a>
<script>
let recorder,stream,url;const start=document.querySelector('#start'),stop=document.querySelector('#stop'),status=document.querySelector('#status'),save=document.querySelector('#save');
start.onclick=async()=>{try{if(!navigator.mediaDevices?.getDisplayMedia||!window.MediaRecorder)throw Error('Trình duyệt chưa hỗ trợ quay màn hình.');stream=await navigator.mediaDevices.getDisplayMedia({video:true,audio:false});const chunks=[];recorder=new MediaRecorder(stream);recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};recorder.onstop=()=>{if(url)URL.revokeObjectURL(url);url=URL.createObjectURL(new Blob(chunks,{type:recorder.mimeType}));save.href=url;save.download='X_SENTINEL_demo.webm';save.hidden=false;stream.getTracks().forEach(t=>t.stop());start.disabled=false;stop.disabled=true;status.textContent='Đã quay xong. Bấm Tải video để lưu.'};stream.getVideoTracks()[0].onended=()=>{if(recorder.state==='recording')recorder.stop()};save.hidden=true;recorder.start();start.disabled=true;stop.disabled=false;status.textContent='Đang quay màn hình đã chọn. Giữ trang này mở.'}catch(e){status.textContent='Không bắt đầu quay được. Hãy cấp quyền chia sẻ màn hình hoặc dùng trình duyệt có hỗ trợ.'}};
stop.onclick=()=>{if(recorder?.state==='recording')recorder.stop()};window.addEventListener('pagehide',()=>stream?.getTracks().forEach(t=>t.stop()));
</script></html>'''
