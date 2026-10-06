import sys
import io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
import streamlit as st
from xsentinel.detection.detector import Detector
from xsentinel.data.pe import extract_pe

st.set_page_config(page_title='X-SENTINEL',layout='wide')
st.title('X-SENTINEL')
st.caption('Per-input trigger suspicion on EMBER2018 / EMBER2024 features · research prototype')
st.info('The malware classification and trigger alert answer separate questions. PASS does not certify safety. Uploaded PE bytes are parsed, never executed.')
dataset=st.sidebar.selectbox('Dataset',['EMBER2018','EMBER2024'])
default_bundle='outputs/pilot/seed_17/concentrated_0.01/bundle' if dataset=='EMBER2018' else 'outputs/primary/EMBER2024/bundle'
bundle=st.sidebar.text_input('Detector bundle directory',default_bundle,key='bundle_'+dataset)
try:
    detector=Detector.load(bundle,expected_dataset=dataset)
except Exception as exc:
    st.warning(f'Not ready: {exc}'); st.stop()
st.sidebar.success('Model and reference checksums verified')
st.sidebar.caption(f'{detector.schema.version} · {detector.protocol}')
preferred='X_primary_reduced' if 'X_primary_reduced' in detector.thresholds else 'X_reduced'
method=st.sidebar.selectbox('Detector variant',list(detector.thresholds),index=list(detector.thresholds).index(preferred))
st.sidebar.write('Locked threshold',detector.thresholds[method])
st.sidebar.caption('M5 is supplementary. Primary bundles disable it by default; archived bundles retain their original limited proxy.')
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
        scores,flags,details,elapsed=detector.predict(x)
        p=float(details['malware_probability'][0]); alert=bool(flags[method][0])
        col1,col2,col3=st.columns(3)
        col1.metric('Malware probability',f'{p:.4f}')
        col2.metric('Main classification','MALWARE' if p>=detector.config['malware_threshold'] else 'BENIGN')
        col3.metric('Backdoor alert','ALERT' if alert else 'NO ALERT')
        st.write(f'Detection elapsed: {elapsed:.2f} ms (single observation, including STRIP)')
        if extraction_ms is not None: st.write(f'Experimental extraction: {extraction_ms:.2f} ms')
        rows=[{'Method':k,'Score':float(v[0]),'Threshold':detector.thresholds[k],'Flagged':bool(flags[k][0])} for k,v in scores.items()]
        st.dataframe(pd.DataFrame(rows),hide_index=True)
        st.subheader('View evidence')
        st.bar_chart(pd.DataFrame({'Absolute SHAP share':{k:float(v[0]) for k,v in details['view_contributions'].items()}}))
        st.write('View malware probabilities',{k:float(v[0]) for k,v in details['view_predictions'].items()})
        st.write('Signed SHAP totals (raw-margin direction)',{k:float(v[0]) for k,v in details['view_signed_shap'].items()})
        top=details['top_features'][0]
        st.dataframe(pd.DataFrame({'Feature index':top,'Feature name':[detector.schema.names[j] for j in top],
                                  'Feature value':x[0,top],'SHAP':details['phi'][0,top]}),hide_index=True)
        st.caption('No file deletion, quarantine, or operating-system policy is performed. Blended STRIP vectors may lie outside valid PE feature space.')
    except Exception as exc:
        st.error(f'Cannot score input: {exc}')
