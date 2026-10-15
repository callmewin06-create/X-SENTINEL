"""Export labels for existing reference demos; no model/data/research changes."""
import json
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from xsentinel.demo_provenance import catalogue_key, vector_digest
from xsentinel.dashboard_catalog import primary_catalog
from xsentinel.utils import sha256
from xsentinel.schema import get_schema


def build():
    entries = {}
    for dataset in ('EMBER2018', 'EMBER2024'):
        directory = Path('data/primary') / dataset / 'protocol_v2'
        state = json.loads((directory / 'roles.json').read_text(encoding='utf-8'))
        source = Path(state['source_directory'])
        assert sha256(directory / 'roles.npz') == state['roles_sha256']
        assert sha256(source / 'dataset.json') == state['source_dataset_sha256']
        assert state['schema_sha256'] == get_schema(state['schema']).fingerprint
        split = state['role_partitions']['reference']
        for prefix in ('y', 'ids'):
            name = f'{prefix}_{split}.npy'
            assert sha256(source / name) == state['source_array_sha256'][name]
        with np.load(directory / 'roles.npz', allow_pickle=False) as roles:
            indices = roles['reference'].copy()
        labels = np.load(source / f'y_{split}.npy', mmap_mode='r', allow_pickle=False)[indices]
        ids = np.load(source / f'ids_{split}.npy', mmap_mode='r', allow_pickle=False)[indices].astype(str)
        assert ids.tolist() == state['ids']['reference'] and np.all(labels == 0)
        reference = np.asarray(np.load(source / f'X_{split}.npy', mmap_mode='r', allow_pickle=False)[indices], dtype='<f4')
        for variants in primary_catalog(dataset).values():
            for path in variants.values():
                bundle = Path(path)
                manifest = json.loads((bundle / 'bundle.json').read_text(encoding='utf-8'))
                assert manifest['schema'] == state['schema']
                assert sha256(bundle / 'reference.npz') == manifest['hashes']['reference.npz']
                with np.load(bundle / 'reference.npz', allow_pickle=False) as archive:
                    assert np.array_equal(archive['X'], reference)
                entries[catalogue_key(manifest)] = {
                    'label': 'BENIGN', 'source': dataset + ' · tập tham chiếu lành đã đối chiếu nguồn',
                    'schema': state['schema'], 'sample_id': str(ids[0]), 'reference_row': 0,
                    'vector_sha256': vector_digest(reference[:1]),
                    'roles_sha256': state['roles_sha256'],
                    'source_dataset_sha256': state['source_dataset_sha256'],
                    'label_array_sha256': state['source_array_sha256'][f'y_{split}.npy'],
                }
    target = Path('src/xsentinel/assets/demo_catalog.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({'version': 1, 'entries': entries}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Verified demo provenance: {len(entries)} unique bundle/reference identities')


if __name__ == '__main__':
    build()
