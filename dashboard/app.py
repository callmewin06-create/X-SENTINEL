import sys
import io
import os
import uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
import streamlit as st
from xsentinel.detection.detector import Detector
from xsentinel.data.pe import extract_pe
from xsentinel.dashboard_catalog import primary_catalog,experiment_label,preferred_method
from xsentinel.service.client import api_request
from xsentinel.service.scoring import score_input,input_digest

st.set_page_config(page_title='X-SENTINEL',layout='wide')
st.title('X-SENTINEL')
st.caption('Per-input trigger suspicion on EMBER2018 / EMBER2024 features · research prototype')
st.info('The malware classification and trigger alert answer separate questions. PASS does not certify safety. Uploaded PE bytes are parsed, never executed.')
api_base=os.getenv('XS_API_BASE_URL','')
if api_base:
    page=st.sidebar.radio('Trang',['Phân tích','Lịch sử'])
    if page=='Lịch sử':
        st.subheader('Lịch sử phân tích đã lưu')
        st.button('Làm mới lịch sử')
        try:
            history=api_request(api_base,'/v1/analyses?limit=100')
            if not history:
                st.info('Chưa có phân tích nào được lưu. Vào trang Phân tích và nhấn Phân tích và lưu.')
            else:
                st.dataframe(pd.DataFrame(history),hide_index=True)
                selected_request=st.selectbox('Xem chi tiết lần phân tích',[r['request_id'] for r in history])
                st.json(api_request(api_base,'/v1/analyses/'+selected_request))
        except RuntimeError as exc:
            st.error(str(exc))
        st.stop()
    st.sidebar.caption('Kết quả chỉ được lưu khi nhấn Phân tích và lưu. Database giữ lịch sử; không lưu toàn bộ vector/file.')
else:
    st.sidebar.caption('Chế độ local: chưa kết nối API/database; kết quả không được lưu vào lịch sử.')
dataset=st.sidebar.selectbox('Dataset',['EMBER2018','EMBER2024'])
catalog=primary_catalog(dataset)
legacy='outputs/pilot/seed_17/concentrated_0.01/bundle'
collections=['Primary research'] if catalog else []
if dataset=='EMBER2018' and Path(legacy,'bundle.json').exists(): collections.append('Archived pilot')
collections.append('Custom bundle')
collection=st.sidebar.selectbox('Model collection',collections,key='collection_'+dataset)
variant='reduced'; selection='custom'
if collection=='Primary research':
    selection=st.sidebar.selectbox('Research experiment',list(catalog),format_func=experiment_label,key='experiment_'+dataset)
    variants=[v for v in ('reduced','full') if v in catalog[selection]]
    variant=st.sidebar.selectbox('Bundle variant',variants,key='variant_'+dataset)
    default_bundle=catalog[selection][variant]
elif collection=='Archived pilot':
    default_bundle=legacy
else:
    default_bundle=''
bundle=st.sidebar.text_input('Detector bundle directory',default_bundle,key=f'bundle_{dataset}_{collection}_{selection}_{variant}')
try:
    detector=Detector.load(bundle,expected_dataset=dataset)
except Exception as exc:
    st.warning(f'Not ready: {exc}'); st.stop()
st.sidebar.success('Model and reference checksums verified')
st.sidebar.caption(f'{detector.schema.version} · {detector.protocol}')
preferred=preferred_method(detector.thresholds,variant)
method=st.sidebar.selectbox('Detection method',list(detector.thresholds),index=list(detector.thresholds).index(preferred),key=f'method_{dataset}_{collection}_{variant}')
st.sidebar.write('Locked threshold',detector.thresholds[method])
st.sidebar.caption('M5 is supplementary. Primary bundles disable it by default; archived bundles retain their original limited proxy.')
if collection=='Primary research':
    import json
    evidence_path=Path(default_bundle).parent/'result.json'
    if evidence_path.exists():
        evidence=json.loads(evidence_path.read_text(encoding='utf8'))
        if evidence.get('independently_confirmed_strong_and_stealth'):
            st.sidebar.caption('Attack passed the declared development and confirmation screens.')
        else:
            st.sidebar.warning('Attack did not pass both strong + stealth screens. Retained for analysis; interpret detection metrics with this context.')
mode=st.radio('Input',['Example reference vector','EMBER vector (.npy)','Raw EMBER record (.json)','PE file (experimental extraction)'])
types=['npy'] if mode.startswith('EMBER') else ['json'] if mode.startswith('Raw') else ['exe','dll','sys']
upload=None if mode.startswith('Example') else st.file_uploader('Select one input',type=types)
if upload is not None or mode.startswith('Example'):
    try:
        if upload is not None and upload.size>20*1024*1024: raise ValueError('Upload exceeds 20 MiB')
        data=upload.getvalue() if upload is not None else None; extraction_ms=None
        if mode.startswith('Example'):
            x=detector.reference[:1]
            st.caption('Example from the benign reference set. This demonstration is not an independent evaluation.')
        elif mode.startswith('EMBER'):
            x=detector.schema.matrix(np.load(io.BytesIO(data),allow_pickle=False))
        elif mode.startswith('Raw'):
            import json
            from xsentinel.data.vectorizer import Vectorizer
            x=detector.schema.matrix(Vectorizer(detector.schema).transform(json.loads(data)))
        else:
            if dataset=='EMBER2024': raise ValueError('Not ready: V3 binary extraction has not been validated. Use a V3 vector or raw record.')
            import time
            start=time.perf_counter(); vector,meta=extract_pe(data); extraction_ms=(time.perf_counter()-start)*1000
            x=detector.schema.matrix(vector); st.warning(meta['compatibility']); st.json(meta)
        if len(x)!=1: raise ValueError('Dashboard accepts exactly one vector')
        if api_base:
            relative=Path(bundle).resolve().relative_to(Path('outputs/primary').resolve()).as_posix()
            import hashlib
            identity=hashlib.sha256(relative.encode()+b'\0'+Path(bundle,'bundle.json').read_bytes()).hexdigest()
            key=(identity,method,input_digest(x),mode.startswith('Example'))
            if st.button('Phân tích và lưu',type='primary'):
                pending=st.session_state.get('pending_analysis')
                rid=pending['id'] if pending and pending['key']==key else str(uuid.uuid4())
                st.session_state['pending_analysis']={'id':rid,'key':key}
                output=api_request(api_base,'/v1/analyze/vector',{'bundle_id':identity,
                    'features':x[0].tolist(),'method':method,'request_id':rid,'demo_mode':mode.startswith('Example')})
                st.session_state['saved_analysis']={'key':key,'result':output}
                st.session_state.pop('pending_analysis',None)
            saved=st.session_state.get('saved_analysis')
            if not saved or saved['key']!=key:
                st.info('Đầu vào đã sẵn sàng. Nhấn Phân tích và lưu để chấm điểm và ghi lịch sử.')
                st.stop()
            output=saved['result']
            st.success('Đã lưu phân tích: '+output['request_id'])
        else:
            output=score_input(detector,x,method)
        p=output['malware_probability']; alert=output['backdoor_alert']
        col1,col2,col3=st.columns(3)
        col1.metric('Malware probability',f'{p:.4f}')
        col2.metric('Main classification',output['main_classification'])
        col3.metric('Backdoor alert','ALERT' if alert else 'NO ALERT')
        st.write(f"Detection elapsed: {output['elapsed_ms']:.2f} ms (single observation, including STRIP)")
        if extraction_ms is not None: st.write(f'Experimental extraction: {extraction_ms:.2f} ms')
        st.dataframe(pd.DataFrame(output['scores']),hide_index=True)
        st.subheader('View evidence')
        st.bar_chart(pd.DataFrame({'Absolute SHAP share':output['view_contributions']}))
        st.write('View malware probabilities',output['view_predictions'])
        st.write('Signed SHAP totals (raw-margin direction)',output['view_signed_shap'])
        st.dataframe(pd.DataFrame(output['top_features']),hide_index=True)
        st.caption('No file deletion, quarantine, or operating-system policy is performed. Blended STRIP vectors may lie outside valid PE feature space.')
    except Exception as exc:
        st.error(f'Cannot score input: {exc}')
