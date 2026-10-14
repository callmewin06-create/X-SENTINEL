"""Regression coverage for real PE inputs, explanation meaning and provenance."""
from pathlib import Path
import numpy as np
import pytest
from pydantic import ValidationError
from xsentinel.data.limits import MAX_UPLOAD_BYTES
from xsentinel.data.pe import verify_pe
from xsentinel.dashboard_input import context_key, prepare_input
from xsentinel.dashboard_presentation import explain_result
from xsentinel.service.input_metadata import InputMetadata, stable_metadata
from xsentinel.schema import V2_PRIMARY, V3_PRIMARY


def test_pe_above_old_limit_and_shared_50mb_boundary():
    def sized_pe(size):
        data = bytearray(size)
        data[:2] = b'MZ'
        data[0x3c:0x40] = (64).to_bytes(4, 'little')
        data[64:68] = b'PE\0\0'
        return data
    verify_pe(sized_pe(21 * 1024 * 1024))
    verify_pe(sized_pe(MAX_UPLOAD_BYTES))
    with pytest.raises(ValueError, match='50 MiB'):
        verify_pe(sized_pe(MAX_UPLOAD_BYTES + 1))
    with pytest.raises(ValueError, match='MZ'):
        verify_pe(b'not a PE')


@pytest.mark.parametrize('schema,dim', [(V2_PRIMARY, 2381), (V3_PRIMARY, 2568)])
def test_reviewed_fixture_upload_real_readers(schema, dim):
    path = Path('outputs/revision_2026_10_13/binary_validation/ReviewedBenignFixture.exe')
    if not path.exists(): pytest.skip('Reviewed benign fixture is not in checkout')
    prepared = prepare_input('pe', path.read_bytes(), path.name, schema)
    assert prepared['x'].shape == (1, dim) and np.isfinite(prepared['x']).all()
    metadata = InputMetadata(**prepared['metadata'])
    assert metadata.size_bytes == path.stat().st_size
    assert metadata.file_sha256 == prepared['provenance']['sha256']
    assert prepared['provenance']['execution'] == 'never executed'


def test_file_identity_and_metadata_retry_keep_provenance():
    base = ['bundle', 'model-v1', 'X_primary_reduced', 'pe', 'one.exe', 'a'*64, V2_PRIMARY, 'reader-v1']
    original = context_key(*base)
    for index, replacement in ((4, 'two.exe'), (5, 'b'*64), (1, 'model-v2'), (7, 'reader-v2'), (2, 'TADR')):
        changed = base.copy(); changed[index] = replacement
        assert context_key(*changed) != original
    meta = dict(kind='pe', name='one.exe', size_bytes=100, file_sha256='a'*64,
                schema=V2_PRIMARY, extractor='test', extraction_ms=1.0)
    assert stable_metadata(meta) == stable_metadata({**meta, 'extraction_ms': 4.0})
    assert stable_metadata(meta) != stable_metadata({**meta, 'name': 'two.exe'})
    for invalid in ({**meta, 'size_bytes': MAX_UPLOAD_BYTES+1}, {**meta, 'file_sha256': 'bad'},
                    {**meta, 'extraction_ms': float('inf')}, {**meta, 'raw_bytes': 'secret'}):
        with pytest.raises(ValidationError): InputMetadata(**invalid)


@pytest.mark.parametrize('classification', ['BENIGN', 'MALWARE'])
@pytest.mark.parametrize('alert', [False, True])
def test_explanation_keeps_two_decisions_and_strict_threshold(classification, alert):
    score = .6 if alert else .5
    result = {'main_classification': classification, 'backdoor_alert': alert,
              'method': 'TADR', 'scores': [{'Method': 'TADR', 'Score': score, 'Threshold': .5}]}
    explanation = explain_result(result)
    assert explanation['alert'] == ('Có cảnh báo' if alert else 'Chưa cảnh báo')
    assert explanation['classification'] == ('Dự đoán mã độc' if classification == 'MALWARE' else 'Dự đoán lành')
    assert 'an toàn' not in explanation['classification']
    with pytest.raises(ValueError): explain_result({**result, 'backdoor_alert': not alert})
