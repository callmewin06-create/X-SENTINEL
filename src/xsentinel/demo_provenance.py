"""Resolve demo labels by verified content, never by client-declared names/labels."""
from functools import lru_cache
from importlib.resources import files
import hashlib
import json
import numpy as np


def vector_digest(x):
    return hashlib.sha256(np.asarray(x, dtype='<f4').tobytes()).hexdigest()


def catalogue_key(state):
    hashes = state.get('hashes', {})
    return ':'.join((state.get('schema', ''), hashes.get('main.txt', ''), hashes.get('reference.npz', '')))


@lru_cache(maxsize=1)
def _catalogue():
    return json.loads(files('xsentinel').joinpath('assets/demo_catalog.json').read_text(encoding='utf-8'))['entries']


def demo_ground_truth(state, x, requested=False):
    if not requested:
        return None
    entry = _catalogue().get(catalogue_key(state))
    if entry is None or entry['vector_sha256'] != vector_digest(x):
        return None
    return dict(entry)


def demo_comparison(result):
    truth = result.get('ground_truth')
    if not truth or truth.get('label') not in ('BENIGN', 'MALWARE'):
        return {'known': False, 'text': 'Chưa có nhãn đối chiếu được xác minh.'}
    expected = 'Lành' if truth['label'] == 'BENIGN' else 'Mã độc'
    matched = truth['label'] == result['main_classification']
    detail = 'Dự đoán đúng theo nhãn bộ dữ liệu.' if matched else (
        'Dự đoán nhầm mẫu lành thành mã độc.' if truth['label'] == 'BENIGN'
        else 'Dự đoán nhầm mẫu mã độc thành lành.')
    return {'known': True, 'expected': expected, 'matched': matched, 'text': detail,
            'source': truth.get('source', 'Nhãn bộ dữ liệu đã xác minh')}
