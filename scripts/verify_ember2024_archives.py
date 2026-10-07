"""Validate pinned PE ZIPs without extracting them or opening any models."""
import argparse
from pathlib import Path
import sys
import time
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from xsentinel.utils import read_json, write_json, sha256


def verify(directory, manifest_path, output):
    output = Path(output)
    if output.exists():
        raise FileExistsError('Existing verification evidence is preserved')
    manifest = read_json(manifest_path)
    rows = []
    started = time.perf_counter()
    for entry in manifest['files']:
        path = Path(directory) / entry['name']
        print('Checking ' + path.name, flush=True)
        if path.stat().st_size != entry['bytes'] or sha256(path) != entry['sha256']:
            raise ValueError('Archive size/SHA256 mismatch: ' + path.name)
        split = 'train' if path.name.endswith('_train.zip') else 'test'
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if not members or any(not m.filename.endswith('_' + split + '.jsonl') for m in members):
                raise ValueError('Unexpected ZIP members: ' + path.name)
            rows.append({**entry, 'path': str(path.resolve()), 'split': split,
                         'members': [{'name': m.filename, 'bytes': m.file_size, 'crc': m.CRC} for m in members],
                         'uncompressed_bytes': sum(m.file_size for m in members)})
    result = {'dataset': 'EMBER2024', 'repository': manifest['repository'],
              'revision': manifest['revision'], 'source_manifest_sha256': sha256(manifest_path),
              'files': rows, 'checks': 'All six PE archive sizes and SHA256 verified; member names checked',
              'elapsed_seconds': time.perf_counter() - started}
    write_json(output, result)
    print('Verified all six PE archives', flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', required=True)
    parser.add_argument('--manifest', default='configs/ember2024_sources.json')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    verify(args.directory, args.manifest, args.out)
