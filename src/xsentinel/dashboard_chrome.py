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


def controls():
    choice = st.sidebar.selectbox('Giao diện', ['Theo hệ thống', 'Sáng', 'Tối'], key='appearance')
    with st.sidebar.popover('Tùy chọn ứng dụng', use_container_width=True):
        st.button('Tải lại giao diện', help='Làm mới phần hiển thị, giữ kết quả phân tích trong phiên.', key='refresh_app')
        if st.button('Giới thiệu', key='about_app'):
            about()
        if st.checkbox('Quay video màn hình', key='record_screen'):
            st.caption('Chọn tab hoặc cửa sổ cần quay. Video được tải trực tiếp bằng trình duyệt.')
            components.html(RECORDER, height=145)
    base = DARK if choice == 'Tối' else LIGHT
    automatic = f'@media(prefers-color-scheme:dark){{:root{{{DARK}}}}}' if choice == 'Theo hệ thống' else ''
    st.markdown('<style>:root{' + base + '}' + automatic + CSS + '</style>', unsafe_allow_html=True)


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
.block-container {max-width:1180px;padding-top:2rem;padding-bottom:3rem;}
h1 {letter-spacing:-0.035em;}
#MainMenu, [data-testid="stMainMenu"], .stAppDeployButton, .stDeployButton {display:none!important;}
[data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"] {background:var(--xs-bg)!important;color:var(--xs-text)!important;}
[data-testid="stSidebar"], [data-testid="stPopoverBody"], [role="dialog"] {background:var(--xs-panel)!important;color:var(--xs-text)!important;}
[data-testid="stPopoverBody"]>div {background:var(--xs-panel)!important;color:var(--xs-text)!important;}
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
