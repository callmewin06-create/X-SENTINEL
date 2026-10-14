"""Prepare one dashboard input and give it a file-aware, versioned identity."""
import hashlib
import io
import json
from pathlib import Path
import time
import numpy as np
from xsentinel.data.limits import verify_size
from xsentinel.schema import get_schema, V3_PRIMARY


def reader_signature(schema_version):
    root = Path(__file__).parent
    files = ['data/pe.py', 'data/vectorizer.py', 'data/limits.py']
    files += ['data/pe_v3.py', 'data/v3_raw.py', 'thrember_upstream.py', 'pefile_warnings.txt'] if schema_version == V3_PRIMARY else ['ember_upstream.py']
    digest = hashlib.sha256(schema_version.encode())
    for name in files:
        digest.update((root / name).read_bytes())
    return digest.hexdigest()


def context_key(bundle_id, model_signature, method, kind, name, file_sha256, schema, reader_version):
    payload = (bundle_id, model_signature, method, kind, name, file_sha256, schema, reader_version)
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode()).hexdigest()


def prepare_input(kind, data, name, schema_version, reference=None):
    schema = get_schema(schema_version)
    name = name.replace('\\', '/').rsplit('/', 1)[-1][:255] or 'Đầu vào'
    start = time.perf_counter()
    provenance = {}
    if kind == 'demo':
        if reference is None:
            raise ValueError('Reference demo is unavailable')
        x = schema.matrix(reference[:1]).copy()
        extractor = 'reference-demo'
    else:
        verify_size(len(data))
        if kind == 'pe':
            if schema.version == V3_PRIMARY:
                from xsentinel.data.pe_v3 import extract_pe_v3
                vector, provenance = extract_pe_v3(data)
                extractor = 'EMBER2024 upstream ' + provenance['upstream_commit']
            else:
                from xsentinel.data.pe import extract_pe
                vector, provenance = extract_pe(data)
                extractor = 'EMBER2018 experimental LIEF ' + provenance['lief_version']
            x = schema.matrix(vector)
        elif kind == 'vector':
            x = schema.matrix(np.load(io.BytesIO(data), allow_pickle=False))
            extractor = 'provided-EMBER-vector'
        elif kind == 'raw_json':
            from xsentinel.data.vectorizer import Vectorizer
            raw = json.loads(data)
            if not isinstance(raw, dict):
                raise ValueError('Expected one raw EMBER JSON object')
            x = schema.matrix(Vectorizer(schema.version).transform(raw))
            extractor = 'raw-EMBER-vectorizer'
        else:
            raise ValueError('Unknown input kind')
    if len(x) != 1:
        raise ValueError('Exactly one vector is required')
    extraction_ms = (time.perf_counter() - start) * 1000
    metadata = {'kind': kind, 'name': name, 'size_bytes': len(data) if data is not None else None,
                'file_sha256': hashlib.sha256(data).hexdigest() if data is not None else None,
                'schema': schema.version, 'extractor': extractor, 'extraction_ms': extraction_ms}
    return {'x': x, 'metadata': metadata, 'provenance': provenance}
