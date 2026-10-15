"""Meaningful decision, provenance, export and UI-state regression checks."""
import copy
import json
from pathlib import Path
import numpy as np
import pytest
from xsentinel.dashboard_presentation import explain_result, feature_rows
from xsentinel.demo_provenance import demo_ground_truth, demo_comparison
from xsentinel.service.registry import BundleRegistry


def sample(p=.5, score=.5):
    return {'main_classification': 'MALWARE' if p >= .5 else 'BENIGN',
            'malware_probability': p, 'malware_threshold': .5,
            'backdoor_alert': score > .5, 'method': 'TADR',
            'scores': [{'Method': 'TADR', 'Score': score, 'Threshold': .5}],
            'top_features': [], 'elapsed_ms': 20, 'dataset': 'EMBER2024'}


@pytest.mark.parametrize('p', [.49999999, .5, .50000001])
@pytest.mark.parametrize('score', [.49999999, .5, .50000001])
def test_two_decision_boundaries_do_not_use_rounded_display(p, score):
    result = sample(p, score)
    text = explain_result(result)
    assert text['classification'] == ('Dự đoán mã độc' if p >= .5 else 'Dự đoán lành')
    assert text['alert'] == ('Có cảnh báo' if score > .5 else 'Chưa cảnh báo')
    with pytest.raises(ValueError):
        explain_result({**result, 'main_classification': 'BENIGN' if p >= .5 else 'MALWARE'})


def test_old_results_do_not_invent_threshold_or_truth():
    result = sample()
    del result['malware_threshold']
    assert 'chưa lưu ngưỡng' in explain_result(result)['classification_explanation']
    result['demo_mode'] = True
    assert not demo_comparison(result)['known']


def test_ground_truth_requires_verified_content_not_demo_claim():
    registry = BundleRegistry()
    for dataset in ('EMBER2018', 'EMBER2024'):
        entry = next(e for e in registry.entries.values() if e['dataset'] == dataset and e['variant'] == 'reduced')
        detector, _ = registry.loaded(entry['id'])
        x = detector.reference[:1]
        truth = demo_ground_truth(entry['state'], x, True)
        assert truth['label'] == 'BENIGN' and len(truth['sample_id']) == 64
        assert demo_ground_truth(entry['state'], x, False) is None
        changed = x.copy(); changed[0, 0] += 1
        assert demo_ground_truth(entry['state'], changed, True) is None
        state = copy.deepcopy(entry['state']); state['hashes']['reference.npz'] = 'a' * 64
        assert demo_ground_truth(state, x, True) is None
        assert not demo_comparison({'main_classification': 'MALWARE', 'demo_mode': True})['known']
        assert not demo_comparison({'main_classification': 'MALWARE', 'ground_truth': truth})['matched']
        assert demo_comparison({'main_classification': 'BENIGN', 'ground_truth': truth})['matched']


def test_feature_explanation_preserves_sign_and_unknown_meaning():
    result = sample()
    result['top_features'] = [
        {'Feature name': 'header.coff.characteristic.DLL', 'Feature value': 1, 'SHAP': -2.0418},
        {'Feature name': 'unknown.hash.1', 'Feature value': 1, 'SHAP': .123},
    ]
    rows = feature_rows(result)
    assert rows[0]['direction'] == 'Đẩy về lành' and rows[1]['direction'] == 'Đẩy về mã độc'
    assert 'Chưa có mô tả' in rows[1]['description']


def test_pdf_escape_long_vietnamese_names_and_legacy_result():
    from xsentinel.result_pdf import result_pdf
    result = sample()
    result['input_metadata'] = {'name': '<b>mẫu & thử</b>' + 'tên_rất_dài_' * 20}
    result['top_features'] = [{'Feature name': 'unknown.' + 'long_' * 70, 'Feature value': 0, 'SHAP': .1}]
    data = result_pdf(result)
    assert data.startswith(b'%PDF-') and len(data) > 10000
    del result['malware_threshold']
    assert result_pdf(result).startswith(b'%PDF-')


def test_analysis_full_theme_and_pdf_do_not_rescore(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from xsentinel.detection.detector import Detector
    monkeypatch.delenv('XS_API_BASE_URL', raising=False)
    predict = Detector.predict
    calls = []
    def counted(self, x):
        calls.append(True)
        return predict(self, x)
    monkeypatch.setattr(Detector, 'predict', counted)
    app = AppTest.from_file('dashboard/app.py').run(timeout=60)
    app.selectbox(key='dataset').set_value('EMBER2024').run(timeout=60)
    assert app.selectbox(key='variant_EMBER2024').value == 'reduced'
    app.radio(key='mode_Phân tích').set_value('Dùng mẫu demo').run(timeout=60)
    app.button(key='analyze').click().run(timeout=60)
    assert not app.exception and not app.error
    result = copy.deepcopy(app.session_state['analysis']['result'])
    assert result['ground_truth']['label'] == 'BENIGN'
    assert result['malware_threshold'] == .5
    before = len(calls)
    for theme in ('Tối', 'Sáng', 'Theo hệ thống'):
        app.selectbox(key='appearance').set_value(theme).run(timeout=60)
        assert not app.exception and app.session_state['analysis']['result'] == result
    prefix = app.session_state['active_context']
    app.button(key='export_' + prefix).click().run(timeout=60)
    assert not app.exception and app.session_state['pdf_' + prefix].startswith(b'%PDF-')
    assert len(calls) == before
    assert not any('outputs/primary/' in item.value for item in app.markdown)
    app.selectbox(key='variant_EMBER2024').set_value('full').run(timeout=60)
    assert not app.exception and not app.metric
    app.button(key='analyze').click().run(timeout=60)
    assert not app.exception
    full = app.session_state['analysis']['result']
    assert full['method'] == 'X_primary_full'
    assert full['malware_probability'] == result['malware_probability']
    assert full['ground_truth'] == result['ground_truth']
