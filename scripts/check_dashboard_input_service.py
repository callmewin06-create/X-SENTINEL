"""PE -> vector -> API -> history checks with one reviewed benign fixture."""
import argparse
import json
from pathlib import Path
import sys
import time
import uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from xsentinel.dashboard_input import prepare_input
from xsentinel.service.registry import BundleRegistry
from xsentinel.service.scoring import score_input


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture', required=True); parser.add_argument('--base', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args(); out = Path(args.out)
    if out.exists(): raise FileExistsError('Existing evidence preserved')
    data = Path(args.fixture).read_bytes(); registry = BundleRegistry()
    def call(path, payload=None):
        body = json.dumps(payload, allow_nan=False).encode() if payload is not None else None
        request = Request(args.base.rstrip('/') + path, data=body, headers={'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=90) as response: return response.status, json.load(response)
        except HTTPError as error: return error.code, json.loads(error.read())
    cases = []
    prefix = 'delivery_pe_' + uuid.uuid4().hex
    for dataset in ('EMBER2018', 'EMBER2024'):
        for variant in ('reduced', 'full'):
            start = time.perf_counter()
            entry = next(e for e in registry.entries.values() if e['dataset'] == dataset and e['variant'] == variant)
            detector, _ = registry.loaded(entry['id'])
            prepared = prepare_input('pe', data, 'ReviewedBenignFixture.exe', detector.schema.version)
            method = 'X_primary_' + variant
            direct = score_input(detector, prepared['x'], method)
            payload = {'bundle_id': entry['id'], 'features': prepared['x'][0].tolist(), 'method': method,
                       'request_id': prefix + '_' + dataset + '_' + variant, 'demo_mode': False,
                       'input_metadata': prepared['metadata']}
            rpc_start = time.perf_counter(); status, result = call('/v1/analyze/vector', payload)
            rpc_ms = (time.perf_counter() - rpc_start) * 1000
            assert status == 200, result
            for field in ('scores', 'view_contributions', 'view_predictions', 'view_signed_shap',
                          'malware_probability', 'main_classification', 'backdoor_alert', 'top_features'):
                assert direct[field] == result[field], field
            assert result['input_metadata'] == prepared['metadata']
            assert call('/v1/analyses/' + payload['request_id'])[1] == result
            assert call('/v1/analyze/vector', {**payload, 'input_metadata': {**prepared['metadata'], 'extraction_ms': 999}})[1] == result
            assert call('/v1/analyze/vector', {**payload, 'input_metadata': {**prepared['metadata'], 'name': 'different.exe'}})[0] == 409
            assert call('/v1/analyze/vector', {**payload, 'request_id': prefix + '_mismatch_' + variant,
                        'input_metadata': {**prepared['metadata'], 'schema': 'invalid'}})[0] == 422
            cases.append({'dataset': dataset, 'variant': variant, 'request_id': payload['request_id'],
                          'metadata_preserved': True, 'direct_scores_match': True, 'retry_idempotent': True,
                          'different_file_name_conflicts': True, 'schema_mismatch_rejected': True,
                          'extraction_ms': prepared['metadata']['extraction_ms'], 'predict_ms': result['elapsed_ms'],
                          'api_roundtrip_ms': rpc_ms, 'validation_case_ms': (time.perf_counter() - start) * 1000})
    # An overlay makes a valid reviewed fixture larger than the previous 20 MiB limit.
    large = data + b'\0' * (21 * 1024 * 1024 - len(data))
    large_prepared = prepare_input('pe', large, 'ReviewedBenignFixture_21MiB.exe', detector.schema.version)
    assert large_prepared['metadata']['size_bytes'] == 21 * 1024 * 1024
    result = {'cases': cases, 'real_21mib_pe_v3_extraction_passed': True,
              'large_extraction_ms': large_prepared['metadata']['extraction_ms'],
              'scope': 'Fixture bytes parsed, never executed. API timings are smoke observations, not browser rendering or final research latency.'}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
