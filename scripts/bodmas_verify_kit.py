"""Verify the delivery file inventory using Python's standard library only."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'kit_manifest.json').read_text(encoding='utf8'))
    failures = []
    for item in manifest['files']:
        rel = PurePosixPath(item['path'])
        if rel.is_absolute() or '..' in rel.parts or '\\' in item['path'] or ':' in item['path']:
            raise ValueError('Unsafe inventory path')
        path = root.joinpath(*rel.parts)
        if any(p.is_symlink() for p in (path, *path.parents)):
            failures.append(item['path'] + ': symbolic link')
        elif not path.is_file():
            failures.append(item['path'] + ': missing')
        elif path.stat().st_size != item['size_bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            failures.append(item['path'] + ': changed')
    print(json.dumps({'status': 'FAIL' if failures else 'OK', 'checked_files': len(manifest['files']), 'failures': failures}, indent=2))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
