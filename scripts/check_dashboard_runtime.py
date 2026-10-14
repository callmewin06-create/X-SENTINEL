"""Portable AppTest smoke checks for the revised UI and real scoring/history."""
import argparse
import json
import os
from pathlib import Path
import platform
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from streamlit.testing.v1 import AppTest
from xsentinel.dashboard_catalog import primary_catalog
from xsentinel.service.scoring import score_input
from xsentinel.detection.detector import Detector
from xsentinel.utils import write_json


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--out')
    args = parser.parse_args()
    app = AppTest.from_file('dashboard/app.py').run(timeout=60)
    if app.exception:
        raise AssertionError('Initial dashboard failed')
    connected = bool(os.getenv('XS_API_BASE_URL'))
    app.sidebar.radio(key='page').set_value('Nghiên cứu').run(timeout=60)
    cases = []
    for dataset in ('EMBER2018', 'EMBER2024'):
        if len(primary_catalog(dataset)) != 27:
            raise ValueError('Expected all 27 experiments')
        app.selectbox(key='dataset').set_value(dataset).run(timeout=60)
        for variant in ('reduced', 'full'):
            app.selectbox(key='variant_' + dataset).set_value(variant).run(timeout=60)
            assert app.selectbox(key='method_' + dataset).value == 'X_primary_' + variant
            app.radio(key='mode_Nghiên cứu').set_value('Dùng mẫu demo').run(timeout=60)
            start = time.perf_counter()
            app.button(key='analyze').click().run(timeout=90)
            app_run_ms = (time.perf_counter() - start) * 1000
            if app.exception or app.error or len(app.metric) != 2:
                raise AssertionError('Dashboard failed for ' + dataset + '/' + variant)
            record = app.session_state['analysis']
            result = record['result']
            result_before_details = json.loads(json.dumps(result))
            app.toggle[0].set_value(True).run(timeout=60)
            assert not app.exception, [error.message for error in app.exception]
            app.toggle[1].set_value(True).run(timeout=60)
            assert not app.exception
            assert app.session_state['analysis']['result'] == result_before_details
            assert app.session_state['analysis']['timings'] == record['timings']
            cases.append({'dataset': dataset, 'variant': variant, 'method': result['method'],
                          'metrics': {m.label: m.value for m in app.metric},
                          'predict_ms': result['elapsed_ms'], 'ui_script_run_ms': app_run_ms,
                          'application_timings': record['timings'],
                          'details_reuse_existing_result': True,
                          'input_metadata_present': result['input_metadata']['kind'] == 'demo',
                          'request_id': result.get('request_id'), 'saved': result.get('saved', False)})
        # Dataset change must not show the previous result.
        other = 'EMBER2024' if dataset == 'EMBER2018' else 'EMBER2018'
        app.selectbox(key='dataset').set_value(other).run(timeout=60)
        assert not app.metric
    history_ok = None
    if connected:
        app.sidebar.radio(key='page').set_value('Lịch sử').run(timeout=60)
        history_ok = not app.exception and not app.error and len(app.dataframe[0].value) >= 4
        assert history_ok
        assert app.dataframe[0].value['Bộ mô hình'].isin(['EMBER2018', 'EMBER2024']).all()
    result = {'platform': platform.platform(), 'python': platform.python_version(),
              'uid': os.getuid() if hasattr(os, 'getuid') else None, 'cases': cases,
              'api_connected': connected, 'history_page_ok': history_ok,
              'source_data_mounted': Path('data/ember2024_archives').exists(),
              'scope': 'Real model + AppTest script roundtrip; ui_script_run_ms includes AppTest overhead, excludes actual browser rendering/upload. Not a second physical machine.'}
    if args.out:
        destination = Path(args.out)
        if destination.exists(): raise FileExistsError('Existing validation preserved')
        write_json(destination, result)
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == '__main__': main()
