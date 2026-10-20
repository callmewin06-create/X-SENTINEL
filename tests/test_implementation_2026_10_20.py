"""Selected-path equivalence and saved-history exports; no training/DB writes."""
import copy
from io import BytesIO
import numpy as np
import pytest
from xsentinel.service.registry import BundleRegistry
from xsentinel.service.scoring import score_input
from xsentinel.dashboard_exports import input_hash_rows,snapshot_digest


@pytest.mark.parametrize('dataset',['EMBER2018','EMBER2024'])
@pytest.mark.parametrize('variant',['reduced','full'])
def test_exact_selected_methods_match_frozen_suite(dataset,variant):
    registry=BundleRegistry()
    entry=next(e for e in registry.entries.values() if e['dataset']==dataset and e['variant']==variant
               and e['family']=='spread_structural' and e['seed']==17 and e['rate']==.02)
    detector,_=registry.loaded(entry['id'])
    x=detector.reference[:3]
    original,flags,details,_=detector.predict(x)
    for method in detector.thresholds:
        actual,actual_flags,actual_details,_=detector.predict_selected(x,method)
        for key,value in actual.items():
            np.testing.assert_allclose(value,original[key],rtol=0,atol=1e-12)
            np.testing.assert_array_equal(actual_flags[key],flags[key])
        np.testing.assert_array_equal(actual_details['malware_probability'],details['malware_probability'])
        np.testing.assert_array_equal(actual_details['phi'],details['phi'])
    result=score_input(detector,x[:1],'X_primary_'+variant,scope='selected')
    assert result['computation_scope']=='selected'
    assert 'STRIP' in result['not_computed_methods']
    assert 'STRIP' not in result['computed_methods']
    assert result['phase_timings_ms']['strip_ms'] is None


def test_selected_reduced_skips_strip_and_all_clean_views(monkeypatch):
    import xsentinel.detection.detector as module
    registry=BundleRegistry()
    entry=next(e for e in registry.entries.values() if e['dataset']=='EMBER2024' and e['variant']=='full')
    detector,_=registry.loaded(entry['id'])
    def forbidden(*args,**kwargs): raise AssertionError('Unneeded operation executed')
    monkeypatch.setattr(module,'strip',forbidden)
    for model in detector.views.values(): monkeypatch.setattr(model,'predict',forbidden)
    result=score_input(detector,detector.reference[:1],'X_primary_reduced',scope='selected')
    assert result['view_predictions']=={}
    assert set(result['computed_methods'])=={'M3_view_mass','M4_shap_behavioral_conflict','X_primary_reduced'}


def test_file_hash_is_distinct_from_vector_hash_and_cache_tracks_content():
    result={'input_sha256':'a'*64,'input_metadata':{'kind':'pe','file_sha256':'b'*64}}
    assert input_hash_rows(result)==[('SHA-256 file','b'*64),('SHA-256 vector','a'*64)]
    changed=copy.deepcopy(result);changed['input_metadata']['file_sha256']='c'*64
    assert snapshot_digest(result)!=snapshot_digest(changed)
    assert input_hash_rows({'input_sha256':'a'*64})[0][1]=='Chưa lưu'


def test_history_pdf_multi_page_snapshot_and_missing_data():
    from xsentinel.result_pdf import history_pdf
    import re
    rows=[{'request_id':f'REQUEST_{i:03}','created_at':'2026-10-20T00:00:00+00:00',
           'input_metadata':{'name':'mẫu <script>& '+str(i)},'dataset':'EMBER2024','variant':'full',
           'main_classification':'MALWARE' if i%2 else 'BENIGN','backdoor_alert':bool(i%3)} for i in range(45)]
    rows[1]['main_classification']=None;rows[1]['backdoor_alert']=None
    frozen=copy.deepcopy(rows)
    data=history_pdf(rows,created_at='2026-10-20T01:00:00+00:00')
    assert data.startswith(b'%PDF-') and len(re.findall(rb'/Type /Page\b',data))>1
    assert rows==frozen
    with pytest.raises(ValueError): history_pdf([])


def test_history_exports_follow_snapshot_and_never_rescore(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from xsentinel.service import client
    from xsentinel.detection.detector import Detector
    rows=[]
    for i in range(2):
        rows.append({'request_id':'history_test_'+str(i),'created_at':'2026-10-20T00:00:00+00:00',
            'dataset':'EMBER2024','variant':'reduced','method':'TADR','saved':True,
            'input_sha256':str(i)*64,'input_metadata':{'name':'mẫu '+str(i),'kind':'pe','file_sha256':'f'*64},
            'main_classification':'MALWARE','malware_probability':.8,'malware_threshold':.5,
            'backdoor_alert':True,'scores':[{'Method':'TADR','Score':.7,'Threshold':.5}],
            'elapsed_ms':12,'top_features':[]})
    del rows[1]['malware_threshold']
    del rows[1]['elapsed_ms']
    calls=[]
    def api(base,path,*args,**kwargs):
        calls.append(path)
        if path=='/v1/analyses?limit=100': return copy.deepcopy(rows)
        return copy.deepcopy(next(row for row in rows if path=='/v1/analyses/'+row['request_id']))
    def forbidden(*args,**kwargs): raise AssertionError('Export must not predict')
    monkeypatch.setattr(client,'api_request',api)
    monkeypatch.setattr(Detector,'predict_selected',forbidden)
    monkeypatch.setenv('XS_API_BASE_URL','http://history-test.invalid')
    app=AppTest.from_file('dashboard/app.py').run(timeout=60)
    app.radio(key='page').set_value('Lịch sử').run(timeout=60)
    assert not app.exception
    assert any(code.value=='f'*64 for code in app.code)
    app.button(key='export_history_list').click().run(timeout=60)
    assert app.session_state['history_pdf_bytes'].startswith(b'%PDF-')
    app.button(key='export_history_history_test_0').click().run(timeout=60)
    assert app.session_state['pdf_history_history_test_0'].startswith(b'%PDF-')
    selector=next(item for item in app.selectbox if item.label=='Xem một lần phân tích')
    selector.set_value('history_test_1').run(timeout=60)
    app.button(key='export_history_history_test_1').click().run(timeout=60)
    assert not app.exception
    assert app.session_state['pdf_history_history_test_1'].startswith(b'%PDF-')
    rows[1]['input_metadata']['name']='Đã đổi snapshot'
    app.button(key='refresh_history').click().run(timeout=60)
    assert 'history_pdf_bytes' not in app.session_state
    assert 'pdf_history_history_test_1' not in app.session_state
    assert all(path.startswith('/v1/analyses') for path in calls)
