"""Real exported bundles exercise the dashboard; no training or threshold changes."""
from pathlib import Path
import pytest
from xsentinel.dashboard_catalog import primary_catalog,preferred_method


def test_catalog_experiment_keeps_full_reduced_together(tmp_path):
    for variant in ('full','reduced'):
        p=tmp_path/'EMBER2024/protocol_v2/seed_29/spread_structural/rate_0.01'/f'bundle_{variant}'
        p.mkdir(parents=True); (p/'bundle.json').write_text('{}')
    catalog=primary_catalog('EMBER2024',tmp_path)
    assert list(catalog)==[('spread_structural',29,.01)]
    assert set(catalog[('spread_structural',29,.01)])=={'full','reduced'}
    assert preferred_method({'TADR':.1,'X_primary_full':.9},'full')=='X_primary_full'


def test_dashboard_real_primary_bundles_and_details_do_not_rescore(monkeypatch):
    if not all(primary_catalog(d) for d in ('EMBER2018','EMBER2024')):
        pytest.skip('Completed research bundles not present in this checkout')
    monkeypatch.delenv('XS_API_BASE_URL', raising=False)
    from streamlit.testing.v1 import AppTest
    from xsentinel.detection.detector import Detector
    original = Detector.predict_selected
    calls = []
    def counted(self, x, method):
        calls.append(self.schema.dataset)
        return original(self, x, method)
    monkeypatch.setattr(Detector, 'predict_selected', counted)
    app=AppTest.from_file('dashboard/app.py').run(timeout=45)
    assert not app.exception and not app.metric
    for dataset in ('EMBER2018','EMBER2024'):
        app.selectbox(key='dataset').set_value(dataset).run(timeout=45)
        app.radio(key='page').set_value('Nghiên cứu').run(timeout=45)
        for variant in ('reduced','full'):
            app.selectbox(key='variant_'+dataset).set_value(variant).run(timeout=45)
            assert app.selectbox(key='method_'+dataset).value=='X_primary_'+variant
            app.radio(key='mode_Nghiên cứu').set_value('Dùng mẫu demo').run(timeout=45)
            app.button(key='analyze').click().run(timeout=45)
            assert not app.exception and not app.error and len(app.metric)==2
            assert app.metric[0].label=='Mô hình phân loại file' and app.metric[1].label=='Dấu hiệu trigger'
            before=len(calls)
            app.toggle[0].set_value(True).run(timeout=45)
            app.toggle[1].set_value(True).run(timeout=45)
            assert not app.exception and len(calls)==before
            assert sum('xs-data-table' in item.value for item in app.markdown)>=2
    wrong=next(iter(primary_catalog('EMBER2018').values()))['full']
    app.checkbox(key='custom_enabled').set_value(True).run(timeout=45)
    app.text_input(key='custom_path').set_value(wrong).run(timeout=45)
    assert not app.exception and not app.metric
    assert any('không khớp' in x.value for x in app.error)
