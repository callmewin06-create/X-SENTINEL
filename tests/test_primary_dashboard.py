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


def test_dashboard_real_primary_bundles_and_wrong_dataset():
    if not all(primary_catalog(d) for d in ('EMBER2018','EMBER2024')):
        pytest.skip('Completed research bundles not present in this checkout')
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file('dashboard/app.py').run(timeout=45)
    for dataset in ('EMBER2018','EMBER2024'):
        app.sidebar.selectbox[0].set_value(dataset).run(timeout=45)
        assert app.sidebar.selectbox[1].value=='Primary research'
        for variant in ('reduced','full'):
            app.sidebar.selectbox[3].set_value(variant).run(timeout=45)
            assert not app.exception and not app.error and len(app.metric)==3
            assert app.sidebar.selectbox[4].value=='X_primary_'+variant
            assert 'Model and reference checksums verified' in app.sidebar.success[0].value
            assert app.metric[1].label=='Main classification' and app.metric[2].label=='Backdoor alert'
    wrong=next(iter(primary_catalog('EMBER2018').values()))['full']
    app.sidebar.text_input[0].set_value(wrong).run(timeout=45)
    assert not app.exception and not app.metric
    assert any('Bundle dataset mismatch' in x.value for x in app.warning)
