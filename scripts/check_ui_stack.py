"""Verify new UI result fields through real API/database, retaining old history."""
import json
from pathlib import Path
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import uuid
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from xsentinel.service.registry import BundleRegistry


def api(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = Request('http://127.0.0.1:8000' + path, data=data, headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=90) as response:
        return json.load(response)


def main():
    registry = BundleRegistry()
    api('/ready')
    old = {row['request_id']: api('/v1/analyses/' + row['request_id']) for row in api('/v1/analyses?limit=3')}
    cases = []
    main_scores = {}
    for dataset in ('EMBER2018', 'EMBER2024'):
        for variant in ('reduced', 'full'):
            entry = next(e for e in registry.entries.values() if e['dataset'] == dataset and e['variant'] == variant)
            with np.load(entry['path'] / 'reference.npz', allow_pickle=False) as archive:
                vector = archive['X'][0].tolist()
            request = {'bundle_id': entry['id'], 'features': vector, 'method': 'X_primary_' + variant,
                       'demo_mode': True, 'request_id': 'ui-20261016-' + uuid.uuid4().hex,
                       'input_metadata': {'kind': 'demo', 'name': 'Nghiệm thu giao diện · ' + dataset + ' ' + variant,
                                          'schema': entry['state']['schema'], 'extractor': 'reference-demo'}}
            result = api('/v1/analyze/vector', request)
            assert result['ground_truth']['label'] == 'BENIGN' and result['malware_threshold'] == .5
            assert result == api('/v1/analyze/vector', request)
            assert result == api('/v1/analyses/' + request['request_id'])
            assert result['saved'] and result['explanation_version'] == 'vi-results-v2'
            if dataset in main_scores:
                assert result['malware_probability'] == main_scores[dataset]
            main_scores[dataset] = result['malware_probability']
            cases.append({'dataset': dataset, 'variant': variant, 'request_id': request['request_id'],
                          'classification': result['main_classification'], 'ground_truth': result['ground_truth']['label'],
                          'saved_readback_equal': True, 'retry_unchanged': True})
    forged = dict(request, features=vector.copy(), request_id='ui-forged-demo-' + uuid.uuid4().hex)
    forged['features'][0] += 1
    assert api('/v1/analyze/vector', forged)['ground_truth'] is None
    try:
        api('/v1/analyze/vector', dict(request, ground_truth={'label': 'MALWARE'}))
        raise AssertionError('Client-supplied ground truth was accepted')
    except HTTPError as error:
        assert error.code == 422
    assert all(api('/v1/analyses/' + request_id) == result for request_id, result in old.items())
    proof = {'cases': cases, 'unverified_demo_has_no_label': True,
             'client_label_rejected': True, 'previous_history_records_unchanged': len(old)}
    Path('outputs/ui_revision_2026_10_16/stack.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(proof, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
