"""Safe synthetic inputs only: selection, containment and result accounting."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import threading

import numpy as np
import pytest


_SPEC = importlib.util.spec_from_file_location(
    'bodmas_static_check', Path(__file__).resolve().parents[1] / 'scripts' / 'check_bodmas_static.py')
check = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(check)

REDUCED = 'a' * 64
FULL = 'b' * 64
V3_FULL = 'c' * 64


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    samples, bundles = tmp_path / 'samples', tmp_path / 'primary'
    samples.mkdir()
    bundles.mkdir()
    calls = {'score': [], 'extract': [], 'load': []}
    entries = {}
    for identity, dataset, variant, schema in (
        (REDUCED, 'EMBER2018', 'reduced', check.V2_PRIMARY),
        (FULL, 'EMBER2018', 'full', check.V2_PRIMARY),
        (V3_FULL, 'EMBER2024', 'full', check.V3_PRIMARY),
    ):
        method = 'X_primary_' + variant
        entries[identity] = {'id': identity, 'dataset': dataset, 'variant': variant,
                             'family': 'spread_structural', 'seed': 17, 'rate': .02,
                             'relative_path': dataset + '/' + variant,
                             'state': {'schema': schema, 'thresholds': {method: .5}}}

    class Schema:
        def __init__(self, version):
            self.version = version

        def matrix(self, value):
            result = np.asarray(value, dtype=np.float32)
            return result[None, :] if result.ndim == 1 else result

    class Registry:
        def __init__(self, root):
            assert root == bundles.resolve()

        def entry(self, identity):
            return entries[identity]

        def listing(self):
            return [{k: v for k, v in entry.items() if k != 'state'} for entry in entries.values()]

        def loaded(self, identity):
            calls['load'].append(identity)
            hook = calls.get('before_load')
            if hook:
                hook()
            detector = type('Detector', (), {'schema': Schema(entries[identity]['state']['schema'])})()
            return detector, threading.Lock()

    def extract(data, schema):
        calls['extract'].append((data, schema))
        if data.startswith(b'bad'):
            raise ValueError('Synthetic parse failure')
        return np.zeros(2568 if schema == check.V3_PRIMARY else 2381), {
            'execution': 'never executed', 'test': 'synthetic only'}

    def score(detector, x, method):
        calls['score'].append(method)
        return {'malware_probability': .8, 'main_classification': 'MALWARE',
                'backdoor_alert': True, 'elapsed_ms': 1.25,
                'scores': [{'Method': method, 'Score': .7, 'Threshold': .5}]}

    monkeypatch.setattr(check, 'BundleRegistry', Registry)
    monkeypatch.setattr(check, '_extract', extract)
    monkeypatch.setattr(check, 'score_input', score)
    return samples, bundles, calls


def options(runtime, out, **changes):
    samples, bundles, _ = runtime
    return dict(input_dir=samples, bundle_root=bundles, bundle_id=REDUCED,
                out=out, limit=10, seed=17, declared_label='unknown',
                label_source='unknown; no independently verified metadata', **changes)


def test_manifest_is_fixed_before_loading_and_reused_across_variants(runtime, tmp_path):
    samples, _, calls = runtime
    for name in ('a', 'b', 'c', 'd'):
        (samples / name).write_bytes(('safe synthetic ' + name).encode())
    first = tmp_path / 'first'
    calls['before_load'] = lambda: assert_manifest(first)
    first_options = options(runtime, first)
    first_options['limit'] = 2
    result = check.scan(**first_options)
    assert result['selected_count'] == result['scored_count'] == 2
    assert all(row['declared_label'] == 'unknown' for row in result['records'])
    assert result['label_declaration']['verification'] == check.LABEL_VERIFICATION
    assert 'accuracy' not in result and 'backdoor_recall' not in result
    second = tmp_path / 'second'
    calls['before_load'] = lambda: assert_manifest(second)
    second_options = {**first_options, 'out': second, 'bundle_id': FULL,
                      'manifest': first / 'manifest.json'}
    reused = check.scan(**second_options)
    assert (first / 'manifest.json').read_bytes() == (second / 'manifest.json').read_bytes()
    assert [row['relative_path'] for row in result['records']] == [row['relative_path'] for row in reused['records']]
    assert reused['manifest_reused'] is True
    assert calls['score'] == ['X_primary_reduced'] * 2 + ['X_primary_full'] * 2
    third = check._new_manifest(samples, 2, 17, result['label_declaration'])
    assert third['manifest_sha256'] == result['manifest_sha256']


def assert_manifest(output):
    value = json.loads((output / 'manifest.json').read_text(encoding='utf8'))
    assert value['selected_count'] == len(value['entries'])
    assert all(entry['file_sha256'] for entry in value['entries'])


def test_parse_failure_stays_in_csv_and_all_selected_denominator(runtime, tmp_path):
    samples, _, calls = runtime
    (samples / 'good.bin').write_bytes(b'safe synthetic')
    (samples / 'bad.bin').write_bytes(b'bad synthetic')
    output = tmp_path / 'results'
    summary = check.scan(**options(runtime, output))
    assert summary['selected_count'] == 2 and summary['scored_count'] == 1
    assert summary['error_count'] == 1
    assert summary['status_counts'] == {'ok': 1, 'parse_failed': 1}
    assert summary['classification_counts'] == {'BENIGN': 0, 'MALWARE': 1}
    assert summary['classification_unavailable_count'] == 1
    assert summary['trigger_alert_rate'] == {'numerator': 1, 'denominator': 2, 'value': .5}
    assert len(calls['score']) == 1
    with (output / 'results.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2
    failure = next(row for row in rows if row['relative_path'] == 'bad.bin')
    assert failure['parse_status'] == 'failed'
    assert failure['score'] == failure['trigger_alert'] == ''
    assert failure['file_sha256'] == hashlib.sha256(b'bad synthetic').hexdigest()
    assert 'Synthetic parse failure' in failure['error']


def test_worker_timeout_remains_unavailable(runtime, tmp_path, monkeypatch):
    from xsentinel.data.pe_isolation import ExtractionError
    samples, _, calls = runtime
    (samples / 'slow.bin').write_bytes(b'synthetic only')
    def timeout(*args):
        raise ExtractionError('timeout', 'Synthetic deadline exceeded')
    monkeypatch.setattr(check, '_extract', timeout)
    result = check.scan(**options(runtime, tmp_path / 'timeout'))
    assert result['status_counts'] == {'timeout': 1}
    assert result['classification_unavailable_count'] == 1
    assert result['records'][0]['trigger_alert'] is None
    assert result['records'][0]['main_classification'] is None
    assert not calls['score']


def test_actual_non_pe_is_rejected_by_existing_reader_without_prediction(runtime, tmp_path, monkeypatch):
    samples, _, calls = runtime
    (samples / 'not-pe').write_bytes(b'This is harmless text, not an executable.')
    from xsentinel.data.pe import extract_pe
    monkeypatch.setattr(check, '_extract', lambda data, schema: extract_pe(data))
    summary = check.scan(**options(runtime, tmp_path / 'non-pe'))
    assert summary['records'][0]['scan_status'] == 'parse_failed'
    assert 'MZ' in summary['records'][0]['error']
    assert not calls['score']


def test_oversize_is_never_hashed_or_extracted(runtime, tmp_path, monkeypatch):
    samples, _, calls = runtime
    (samples / 'large.bin').write_bytes(b'x' * 9)
    monkeypatch.setattr(check, 'MAX_UPLOAD_BYTES', 8)
    result = check.scan(**options(runtime, tmp_path / 'oversize'))
    row = result['records'][0]
    assert row['scan_status'] == 'input_rejected' and row['error_code'] == 'oversize'
    assert row['file_sha256'] is None and row['size_bytes'] == 9
    assert row['parse_status'] == 'not_attempted'
    assert not calls['extract'] and not calls['score']
    assert result['trigger_alert_rate']['denominator'] == 1


def test_symlink_is_not_followed_or_extracted(runtime, tmp_path):
    samples, _, calls = runtime
    outside = tmp_path / 'outside.bin'
    outside.write_bytes(b'never read via link')
    try:
        (samples / 'linked.bin').symlink_to(outside)
    except OSError:
        pytest.skip('Symlink creation is not permitted on this Windows host')
    result = check.scan(**options(runtime, tmp_path / 'symlink'))
    assert result['records'][0]['error_code'] == 'symlink_or_reparse_point'
    assert result['records'][0]['file_sha256'] is None
    assert not calls['extract'] and not calls['score']


def test_changed_file_is_not_scored_when_reusing_manifest(runtime, tmp_path):
    samples, _, calls = runtime
    sample = samples / 'one.bin'
    sample.write_bytes(b'original')
    first = tmp_path / 'first'
    check.scan(**options(runtime, first))
    sample.write_bytes(b'replaced')
    calls['score'].clear()
    result = check.scan(**options(runtime, tmp_path / 'changed', manifest=first / 'manifest.json'))
    row = result['records'][0]
    assert row['error_code'] == 'changed_since_manifest' and row['parse_status'] == 'not_attempted'
    assert row['manifest_file_sha256'] != row['file_sha256']
    assert not calls['score']


@pytest.mark.parametrize('relative', ['../outside.bin', '/outside.bin', 'C:/outside.bin', 'sub\\outside.bin'])
def test_manifest_cannot_escape_directory(runtime, tmp_path, relative):
    samples, _, _ = runtime
    (samples / 'one.bin').write_bytes(b'synthetic')
    first = tmp_path / 'first'
    check.scan(**options(runtime, first))
    manifest = json.loads((first / 'manifest.json').read_text())
    manifest['entries'][0]['relative_path'] = relative
    manifest['manifest_sha256'] = check._manifest_digest(manifest)
    bad = tmp_path / 'bad-manifest.json'
    bad.write_text(json.dumps(manifest))
    output = tmp_path / 'escaped'
    with pytest.raises(ValueError, match='relative path'):
        check.scan(**options(runtime, output, manifest=bad))
    assert not output.exists()


def test_existing_or_overlapping_output_is_rejected(runtime, tmp_path):
    samples, bundles, calls = runtime
    (samples / 'one.bin').write_bytes(b'synthetic')
    existing = tmp_path / 'existing'
    existing.mkdir()
    evidence = existing / 'evidence.txt'
    evidence.write_text('preserve')
    with pytest.raises(FileExistsError):
        check.scan(**options(runtime, existing))
    for destination in (samples / 'results', bundles / 'results'):
        with pytest.raises(ValueError, match='outside'):
            check.scan(**options(runtime, destination))
        assert not destination.exists()
    assert evidence.read_text() == 'preserve'
    assert not calls['load']


def test_bundle_listing_does_not_load_models_and_v3_uses_matching_reader(runtime, tmp_path):
    samples, bundles, calls = runtime
    listed = check.list_bundles(bundles)
    assert len(listed['bundles']) == 3 and not calls['load']
    assert next(row for row in listed['bundles'] if row['id'] == V3_FULL)['schema'] == check.V3_PRIMARY
    (samples / 'v3.bin').write_bytes(b'synthetic')
    arguments = options(runtime, tmp_path / 'v3')
    arguments['bundle_id'] = V3_FULL
    result = check.scan(**arguments)
    assert result['schema'] == check.V3_PRIMARY
    assert calls['extract'][0][1] == check.V3_PRIMARY
    assert result['method'] == 'X_primary_full'


def test_cli_rejects_nonpositive_limit_before_touching_inputs(capsys):
    with pytest.raises(SystemExit) as exc:
        check.main(['scan', '--input-dir', 'unused', '--bundle-id', REDUCED, '--out', 'unused',
                    '--limit', '0', '--declared-label', 'unknown', '--label-source', 'unknown'])
    assert exc.value.code == 2
    assert 'at least 1' in capsys.readouterr().err
