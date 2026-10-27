"""Local-stack acceptance with owned benign fixtures and four marked QA rows."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import numpy as np
from xsentinel.data import pe_isolation as worker
from xsentinel.data.pe import extract_pe
from xsentinel.data.pe_v3 import extract_pe_v3
from xsentinel.dashboard_input import prepare_input
from xsentinel.service.registry import BundleRegistry
from xsentinel.service.scoring import score_input
from xsentinel.result_pdf import result_pdf, history_pdf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture', required=True)
    parser.add_argument('--base', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists():
        raise FileExistsError('Keep prior acceptance evidence')
    out.mkdir(parents=True)
    data = Path(args.fixture).read_bytes()
    def call(path, payload=None):
        body = json.dumps(payload,allow_nan=False).encode() if payload is not None else None
        with urlopen(Request(args.base+path,data=body,headers={'Content-Type':'application/json'}),timeout=90) as response:
            return json.load(response)
    old = call('/v1/analyses?limit=100')
    old_details = {row['request_id']: call('/v1/analyses/'+row['request_id']) for row in old}
    ready = call('/ready')
    registry = BundleRegistry()
    cases, stored = [], []
    prefix = 'repair-qa-20261023-' + uuid.uuid4().hex[:8]
    entries = [e for e in registry.entries.values() if e['family']=='spread_structural' and e['seed']==17 and e['rate']==.02]
    for entry in entries:
        detector, lock = registry.loaded(entry['id'])
        prepared = prepare_input('pe',data,'QA repair ReviewedBenignFixture.exe',detector.schema.version)
        direct_vector, _ = (extract_pe if entry['dataset']=='EMBER2018' else extract_pe_v3)(data)
        np.testing.assert_array_equal(prepared['x'][0], direct_vector)
        method = 'X_primary_'+entry['variant']
        with lock:
            direct = score_input(detector,prepared['x'],method,scope='selected')
        payload = {'bundle_id':entry['id'],'method':method,'features':prepared['x'][0].tolist(),
                   'request_id':prefix+'-'+entry['dataset']+'-'+entry['variant'],
                   'input_metadata':prepared['metadata'],'demo_mode':False}
        result = call('/v1/analyze/vector',payload)
        for name in ('scores','malware_probability','main_classification','backdoor_alert','view_signed_shap'):
            assert result[name] == direct[name], name
        assert call('/v1/analyze/vector',payload) == result
        assert call('/v1/analyses/'+payload['request_id']) == result
        pdf = result_pdf(result)
        assert pdf.startswith(b'%PDF-')
        (out / (entry['dataset']+'-'+entry['variant']+'.pdf')).write_bytes(pdf)
        cases.append({'dataset':entry['dataset'],'variant':entry['variant'], 'request_id':payload['request_id'],
                      'vector_sha256':hashlib.sha256(np.asarray(prepared['x'],dtype='<f4').tobytes()).hexdigest(),
                      'probability':result['malware_probability'],'classification':result['main_classification'],
                      'extraction_ms':prepared['metadata']['extraction_ms'], 'selected_api_and_direct_match':True,
                      'retry_readback_pdf_ok':True})
        stored.append(result)
    for request_id, before in old_details.items():
        assert call('/v1/analyses/'+request_id) == before
    (out/'history.pdf').write_bytes(history_pdf(stored))
    # Faults use controlled helper programs, never a corpus executable.
    real_popen = worker.subprocess.Popen
    lifecycle = []
    for code, timeout, expected in [('import time; time.sleep(30)', .2, 'timeout'),
                                    ('import os; os._exit(7)', 10, 'worker_crashed')]:
        children=[]
        def spawn(command, **kwargs):
            p=real_popen([sys.executable,'-c',code],**kwargs);children.append(p);return p
        worker.subprocess.Popen=spawn
        start=time.perf_counter()
        try:
            worker.extract_pe_isolated(data,detector.schema.version,timeout=timeout)
            raise AssertionError('Expected worker failure')
        except worker.ExtractionError as error:
            assert error.code==expected
            assert children[0].poll() is not None
            lifecycle.append({'error':error.code,'wall_ms':(time.perf_counter()-start)*1000,'child_reaped':True})
        finally:
            worker.subprocess.Popen=real_popen
    worker.extract_pe_isolated(data,detector.schema.version)
    result={'platform':sys.platform,'ready':ready,'cases':cases,'old_rows_verified_unchanged':len(old),
            'new_qa_rows':len(cases),'lifecycle':lifecycle,'recovery_ok':True,
            'timing_scope':'Smoke observations including worker startup; concurrent diagnostic work may be running; not latency benchmark'}
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
