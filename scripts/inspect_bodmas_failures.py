"""Read-only header diagnostics for exactly the failed hashes in a CSV.

Standard library only. Does not execute, restore, modify or extract any binary.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import struct


def inspect(data):
    result = {'size_bytes': len(data), 'has_mz': data[:2] == b'MZ', 'enough_dos_header': len(data) >= 64}
    if len(data) >= 64:
        offset = struct.unpack_from('<I', data, 0x3c)[0]
        result.update(pe_offset=offset, offset_at_least_64=offset >= 64,
                      header_fits=offset+24 <= len(data),
                      signature_hex=data[offset:offset+4].hex() if offset <= len(data) else None,
                      has_pe_signature=data[offset:offset+4] == b'PE\0\0')
    result['passes_current_guard'] = all(result.get(k, False) for k in
        ('has_mz','enough_dos_header','offset_at_least_64','header_fits','has_pe_signature'))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', required=True)
    parser.add_argument('--errors-csv', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path(args.input_dir).resolve(strict=True)
    out = Path(args.out).absolute()
    if out.exists() or out.resolve().is_relative_to(root):
        raise ValueError('Use a new output file outside the sample directory')
    with open(args.errors_csv, encoding='utf-8-sig', newline='') as stream:
        selected = list(csv.DictReader(stream))
    results = []
    for row in selected:
        result = {'relative_path': row['relative_path'], 'expected_sha256': row['file_sha256']}
        try:
            relative = PurePosixPath(row['relative_path'])
            if relative.is_absolute() or any(p in ('..','') for p in relative.parts) or '\\' in str(relative) or ':' in str(relative):
                raise ValueError('Invalid relative path')
            path = root.joinpath(*relative.parts)
            for part in (path, *path.parents):
                if part == root:
                    break
                if part.is_symlink() or getattr(part, 'is_junction', lambda: False)():
                    raise ValueError('Linked path rejected')
            path = path.resolve(strict=True)
            if not path.is_relative_to(root) or path.stat().st_size > 50*1024*1024:
                raise ValueError('Outside root or over 50 MiB')
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            result.update(sha256=digest, bytes_match=digest == row['file_sha256'])
            if not result['bytes_match']:
                raise ValueError('Bytes changed since original manifest')
            result.update(inspect(data), status='inspected')
        except Exception as error:
            result.update(status='unresolved', error=f'{type(error).__name__}: {error}')
        results.append(result)
    payload = {'execution':'read-only; never executed; no header repair',
               'source_csv_sha256':hashlib.sha256(Path(args.errors_csv).read_bytes()).hexdigest(),
               'rows':results, 'limitation':'Header checks cannot establish disarming cause or malware functionality'}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x', encoding='utf8') as stream:
        json.dump(payload,stream,indent=2)
    print(f'Wrote {len(results)} diagnostic rows to the requested JSON file')


if __name__ == '__main__':
    main()
