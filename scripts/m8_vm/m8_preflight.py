#!/usr/bin/env python3
"""Dependency-free static M8 inventory for Kali/Linux and Windows.

Never imports or executes a sample. Never invokes Wine, PowerShell or a shell.
Reports only environment, SHA256 and PE header facts, not functionality/labels.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import struct
import sys

FIELDS = ['relative_path', 'bytes', 'sha256', 'machine', 'architecture',
          'pe_format', 'clr_header_present', 'static_status', 'error',
          'functional_status', 'label']
EXTENSIONS = {'.exe', '.dll', '.sys', '.scr', '.ocx', '.cpl', ''}
MACHINES = {0x014c: 'x86', 0x8664: 'x64', 0xaa64: 'ARM64', 0x01c4: 'ARM'}


def pe_header(stream):
    size = os.fstat(stream.fileno()).st_size
    def read_at(offset, count):
        if offset < 0 or offset + count > size:
            raise ValueError('Truncated PE header')
        stream.seek(offset)
        data = stream.read(count)
        if len(data) != count:
            raise ValueError('File changed while reading')
        return data
    if read_at(0, 2) != b'MZ':
        raise ValueError('Missing MZ signature')
    offset = struct.unpack('<I', read_at(0x3c, 4))[0]
    if offset < 64 or read_at(offset, 4) != b'PE\0\0':
        raise ValueError('Invalid PE signature/offset')
    coff = read_at(offset + 4, 20)
    machine = struct.unpack_from('<H', coff)[0]
    optional_size = struct.unpack_from('<H', coff, 16)[0]
    optional = read_at(offset + 24, optional_size)
    if len(optional) < 2:
        raise ValueError('Missing optional header')
    magic = struct.unpack_from('<H', optional)[0]
    if magic not in (0x10b, 0x20b):
        raise ValueError('Unsupported optional header magic')
    number_offset, directory_offset = (92, 96) if magic == 0x10b else (108, 112)
    if len(optional) < directory_offset:
        raise ValueError('Truncated optional header')
    count = struct.unpack_from('<I', optional, number_offset)[0]
    clr = False
    if count > 14:
        if len(optional) < directory_offset + 15 * 8:
            raise ValueError('Truncated CLR data directory')
        rva, length = struct.unpack_from('<II', optional, directory_offset + 14 * 8)
        clr = bool(rva and length)
    return dict(machine='0x%04X' % machine,
                architecture=MACHINES.get(machine, 'UNKNOWN'),
                pe_format='PE32+' if magic == 0x20b else 'PE32',
                clr_header_present=clr)


def inspect_file(path, root):
    row = dict.fromkeys(FIELDS, '')
    row.update(relative_path=path.relative_to(root).as_posix(),
               functional_status='NOT_RUN', label='UNVERIFIED')
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode):
            row['static_status'] = 'SKIPPED_NONREGULAR'
            return row
        # O_NOFOLLOW blocks final-component symlinks on Linux.
        fd = os.open(str(path), os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0))
        with os.fdopen(fd, 'rb') as stream:
            start = os.fstat(stream.fileno())
            if (before.st_dev, before.st_ino) != (start.st_dev, start.st_ino):
                raise ValueError('File replaced while opening')
            row['bytes'] = start.st_size
            digest = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
            row['sha256'] = digest.hexdigest()
            row.update(pe_header(stream))
            end = os.fstat(stream.fileno())
            if (start.st_size, start.st_mtime_ns) != (end.st_size, end.st_mtime_ns):
                raise ValueError('File changed during inventory')
        row['static_status'] = 'PE_HEADER_OK'
    except Exception as exc:
        row.update(static_status='ERROR', error=str(exc))
    return row


def os_release():
    result = {}
    if sys.platform.startswith('linux'):
        try:
            for line in Path('/etc/os-release').read_text(encoding='utf-8').splitlines():
                key, sep, value = line.partition('=')
                if sep and key in ('ID', 'VERSION_ID', 'PRETTY_NAME'):
                    result[key] = value.strip('"')
        except OSError:
            pass
    return result


def run(samples, output, all_files=False):
    root = Path(samples).expanduser().resolve(strict=True)
    out = Path(output).expanduser().resolve()
    if not root.is_dir():
        raise ValueError('Samples must be a directory')
    if out == root or root in out.parents:
        raise ValueError('Output must be outside the sample directory')
    # Exclusive new report directory: never silently overwrite previous results.
    out.mkdir(parents=True, exist_ok=False)
    environment = dict(stage='static_preflight_only', utc=datetime.now(timezone.utc).isoformat(),
        os=platform.system(), os_release=platform.release(), distribution=os_release(),
        architecture=platform.machine(), python=sys.version,
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        sample_execution='NEVER', functional_validation='NOT_RUN',
        wine_execution='NOT_RUN', independent_backdoor_evaluation=False)
    (out/'environment.json').write_text(json.dumps(environment, indent=2), encoding='utf-8')
    counts = {}; traversal_errors = []; skipped_extensions = 0; skipped_directories = 0
    def walk_error(error):
        traversal_errors.append(str(error))
    with (out/'binary_inventory.csv').open('w', encoding='utf-8', newline='') as report:
        writer = csv.DictWriter(report, fieldnames=FIELDS); writer.writeheader()
        for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
            safe_dirs = [d for d in dirs if not (Path(directory)/d).is_symlink()]
            skipped_directories += len(dirs) - len(safe_dirs)
            dirs[:] = sorted(safe_dirs)
            for name in sorted(files):
                path = Path(directory)/name
                if not all_files and path.suffix.lower() not in EXTENSIONS:
                    skipped_extensions += 1
                    continue
                row = inspect_file(path, root)
                writer.writerow(row)
                status = row['static_status']; counts[status] = counts.get(status, 0) + 1
    success = counts.get('PE_HEADER_OK', 0)
    summary = dict(status='COMPLETE' if success and not traversal_errors and not counts.get('ERROR') else 'NEEDS_REVIEW',
        counts=counts, skipped_extensions=skipped_extensions, skipped_symlink_directories=skipped_directories,
        traversal_errors=traversal_errors, sample_execution='NEVER',
        meaning='PE_HEADER_OK means header parsing only, not functionality, benignness or trigger matching.')
    (out/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2)); print('Reports:', out)
    return 0 if summary['status'] == 'COMPLETE' else 2


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', required=True, help='Original research sample directory (read only)')
    parser.add_argument('--output', required=True, help='New report directory outside samples')
    parser.add_argument('--all-files', action='store_true', help='Include other extensions; does not unpack archives')
    args = parser.parse_args()
    try:
        return run(args.samples, args.output, args.all_files)
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    sys.exit(main())
