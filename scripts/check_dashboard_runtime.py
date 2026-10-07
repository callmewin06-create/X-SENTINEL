"""Smoke test the deployed dashboard with real bundles, including Linux Docker."""
import argparse
import json
import os
from pathlib import Path
import platform
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from streamlit.testing.v1 import AppTest
from xsentinel.dashboard_catalog import primary_catalog
from xsentinel.utils import write_json


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--out')
    args=parser.parse_args()
    results=[]
    app=AppTest.from_file('dashboard/app.py').run(timeout=60)
    connected=bool(os.getenv('XS_API_BASE_URL'))
    for dataset in ('EMBER2018','EMBER2024'):
        if len(primary_catalog(dataset))!=27: raise ValueError('Expected all 27 completed primary experiments')
        app.sidebar.selectbox[0].set_value(dataset).run(timeout=60)
        for variant in ('reduced','full'):
            app.sidebar.selectbox[3].set_value(variant).run(timeout=60)
            if connected:
                app.button[0].click().run(timeout=90)
            if app.exception or app.error or len(app.metric)!=3:
                raise AssertionError('Dashboard failed for '+dataset+'/'+variant)
            if app.sidebar.selectbox[4].value!='X_primary_'+variant:
                raise AssertionError('Wrong preferred primary method')
            results.append({'dataset':dataset,'variant':variant,'metrics':{m.label:m.value for m in app.metric},
                'method':app.sidebar.selectbox[4].value,'scores':app.dataframe[0].value.to_dict(orient='records')})
    wrong=next(iter(primary_catalog('EMBER2018').values()))['full']
    app.sidebar.text_input[0].set_value(wrong).run(timeout=60)
    rejected=not app.exception and not app.metric and any('Bundle dataset mismatch' in w.value for w in app.warning)
    if not rejected: raise AssertionError('Wrong dataset was not rejected')
    history_ok=None
    if connected:
        app.sidebar.radio[0].set_value('Lịch sử').run(timeout=60)
        history_ok=not app.error and not app.exception and len(app.dataframe[0].value)>=4
        if not history_ok: raise AssertionError('Saved history page failed')
    result={'platform':platform.platform(),'python':platform.python_version(),'uid':os.getuid() if hasattr(os,'getuid') else None,
        'cases':results,'wrong_dataset_rejected':True,'raw_dataset_mounted':Path('data/ember2024_archives').exists(),
        'api_connected':connected,'history_page_ok':history_ok}
    if args.out:
        dest=Path(args.out)
        if dest.exists(): raise FileExistsError('Existing validation preserved')
        write_json(dest,result)
    print(json.dumps(result,ensure_ascii=True),flush=True)


if __name__=='__main__': main()
