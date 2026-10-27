"""Read-only local PE checks. Never downloads, extracts archives or executes samples.

Labels are user declarations, not independently verified ground truth. The output
describes classifier predictions and trigger alerts, not backdoor recall.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import random
import re
import stat
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from xsentinel.dashboard_catalog import preferred_method
from xsentinel.data.limits import MAX_UPLOAD_BYTES
from xsentinel.data.pe_isolation import ExtractionError, extract_pe_isolated, timeout_seconds
from xsentinel.schema import V2_PRIMARY, V3_PRIMARY
from xsentinel.service.registry import BundleRegistry
from xsentinel.service.scoring import score_input


MANIFEST_VERSION = 'xsentinel-static-selection-v1'
LABEL_VERIFICATION = 'USER_DECLARED_NOT_INDEPENDENTLY_VERIFIED'
CSV_FIELDS = [
    'sequence', 'relative_path', 'size_bytes', 'file_sha256', 'manifest_file_sha256',
    'declared_label', 'label_source', 'label_verification', 'scan_status',
    'parse_status', 'schema', 'extractor', 'extractor_provenance', 'bundle_id',
    'dataset', 'variant', 'method', 'malware_probability', 'main_classification',
    'score', 'threshold', 'trigger_alert', 'extraction_ms', 'prediction_ms',
    'file_total_ms', 'error_code', 'error',
]


class InputRejected(ValueError):
    def __init__(self, code, message, size=None):
        super().__init__(message)
        self.code, self.size = code, size


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('utf8')


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + '\n', encoding='utf8')


def _is_link(st):
    return stat.S_ISLNK(st.st_mode) or bool(
        getattr(st, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))


def _no_links(path):
    """Reject symlinks and Windows junctions/reparse points in every component."""
    for part in reversed((path, *path.parents)):
        try:
            if _is_link(part.lstat()):
                raise InputRejected('symlink_or_reparse_point', 'Symlinks and reparse points are not accepted')
        except FileNotFoundError:
            continue


def _root(path):
    path = Path(path).expanduser().absolute()
    _no_links(path)
    if not path.is_dir():
        raise ValueError('Expected an existing directory: ' + str(path))
    return path.resolve(strict=True)


def _safe_path(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative:
        raise InputRejected('path_escape', 'Manifest paths must be canonical relative POSIX paths')
    rel = PurePosixPath(relative)
    if rel.is_absolute() or '..' in rel.parts or str(rel) != relative or relative == '.':
        raise InputRejected('path_escape', 'Manifest path escapes the input directory or is not canonical')
    path = root.joinpath(*rel.parts)
    _no_links(path)
    try:
        path.resolve(strict=True).relative_to(root)
    except ValueError as exc:
        raise InputRejected('path_escape', 'Input resolves outside the input directory') from exc
    return path


def _read_file(root, relative):
    """Bounded read with link/regular-file/identity checks; no sample execution."""
    try:
        path = _safe_path(root, relative)
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise InputRejected('not_regular_file', 'Input is not a regular file')
        if before.st_size > MAX_UPLOAD_BYTES:
            raise InputRejected('oversize', 'Input exceeds the 50 MiB size limit', before.st_size)
        flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, 'rb') as stream:
            opened = os.fstat(stream.fileno())
            if (not stat.S_ISREG(opened.st_mode) or _is_link(opened) or
                    (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)):
                raise InputRejected('input_changed', 'Input identity changed before reading')
            data = stream.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            raise InputRejected('oversize', 'Input exceeds the 50 MiB size limit', len(data))
        _safe_path(root, relative)
        after = path.lstat()
        if ((after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) !=
                (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) or
                len(data) != before.st_size):
            raise InputRejected('input_changed', 'Input changed while reading')
        return data, {'size_bytes': len(data), 'file_sha256': hashlib.sha256(data).hexdigest()}
    except InputRejected:
        raise
    except OSError as exc:
        raise InputRejected('unreadable', str(exc)) from exc


def _candidates(root):
    paths = []

    def failed(error):
        paths.append(Path(error.filename).relative_to(root).as_posix())

    for current, dirs, files in os.walk(root, followlinks=False, onerror=failed):
        current = Path(current)
        for name in sorted(dirs):
            child = current / name
            try:
                linked = _is_link(child.lstat())
            except OSError:
                linked = True
            if linked:
                paths.append(child.relative_to(root).as_posix())
                dirs.remove(name)
        dirs.sort()
        paths.extend((current / name).relative_to(root).as_posix() for name in sorted(files))
    return sorted(set(paths))


def _manifest_digest(value):
    return hashlib.sha256(_json_bytes({k: v for k, v in value.items() if k != 'manifest_sha256'})).hexdigest()


def _new_manifest(root, limit, seed, declaration):
    population = _candidates(root)
    if not population:
        raise ValueError('Input directory contains no candidate files')
    selected = sorted(random.Random(seed).sample(population, min(limit, len(population))))
    entries = []
    for relative in selected:
        row = {'relative_path': relative, 'size_bytes': None, 'file_sha256': None,
               'input_status': 'ready', 'error_code': '', 'error': ''}
        try:
            _, info = _read_file(root, relative)
            row.update(info)
        except InputRejected as exc:
            row.update(input_status='rejected', error_code=exc.code, error=str(exc), size_bytes=exc.size)
        entries.append(row)
    manifest = {
        'format': MANIFEST_VERSION, 'requested_limit': limit, 'seed': seed,
        'population_count': len(population), 'selected_count': len(entries),
        'selection_policy': 'Sorted relative paths; seeded sample without replacement; fixed before predictions',
        'label_declaration': declaration, 'entries': entries,
    }
    manifest['manifest_sha256'] = _manifest_digest(manifest)
    return manifest


def _load_manifest(path, root, limit, seed, declaration):
    value = json.loads(Path(path).read_text(encoding='utf8'))
    if (not isinstance(value, dict) or value.get('format') != MANIFEST_VERSION or
            value.get('manifest_sha256') != _manifest_digest(value)):
        raise ValueError('Invalid manifest format or checksum')
    if value.get('requested_limit') != limit or value.get('seed') != seed:
        raise ValueError('--limit and --seed must match the reused manifest; no resampling is allowed')
    if value.get('label_declaration') != declaration:
        raise ValueError('Label declaration must match the reused manifest')
    entries = value.get('entries')
    if (not isinstance(entries, list) or not entries or len(entries) > limit or
            value.get('selected_count') != len(entries)):
        raise ValueError('Invalid manifest entry count')
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or entry.get('input_status') not in ('ready', 'rejected'):
            raise ValueError('Invalid manifest entry')
        relative = entry.get('relative_path')
        # Validate the lexical path even for a previously rejected/missing file.
        if not isinstance(relative, str):
            raise ValueError('Invalid manifest relative path')
        rel = PurePosixPath(relative)
        if (not relative or relative == '.' or '\\' in relative or ':' in relative or
                rel.is_absolute() or '..' in rel.parts or str(rel) != relative or relative in seen):
            raise ValueError('Unsafe or duplicate manifest relative path')
        seen.add(relative)
        if entry['input_status'] == 'ready':
            if (not isinstance(entry.get('size_bytes'), int) or isinstance(entry['size_bytes'], bool) or
                    not 0 <= entry['size_bytes'] <= MAX_UPLOAD_BYTES or
                    not isinstance(entry.get('file_sha256'), str) or
                    re.fullmatch('[0-9a-f]{64}', entry['file_sha256']) is None):
                raise ValueError('Invalid manifest size or file hash')
    return value


def _extract(data, schema):
    return extract_pe_isolated(data, schema)


def list_bundles(bundle_root):
    root = _root(bundle_root)
    registry = BundleRegistry(root)
    bundles = []
    for item in registry.listing():
        state = registry.entry(item['id'])['state']
        bundles.append({**item, 'schema': state['schema'],
                        'method': preferred_method(state['thresholds'], item['variant'])})
    return {'bundle_root': str(root), 'bundles': bundles,
            'scope': 'Manifest listing only; model loading and scanning have not been tested by this command'}


def scan(*, input_dir, bundle_root, bundle_id, out, limit, seed=17,
         declared_label='unknown', label_source, manifest=None):
    if limit < 1 or declared_label not in ('unknown', 'benign', 'malware') or not label_source.strip():
        raise ValueError('Use a positive --limit, a supported declared label and a nonempty label source')
    root, bundle_root = _root(input_dir), _root(bundle_root)
    output = Path(out).expanduser().absolute()
    _no_links(output)
    output = output.resolve()
    if output.exists():
        raise FileExistsError('Output directory must be fresh; existing evidence is preserved')
    if output.is_relative_to(root) or output.is_relative_to(bundle_root):
        raise ValueError('Output directory must be outside the input and primary bundle directories')
    registry = BundleRegistry(bundle_root)
    entry = registry.entry(bundle_id)
    schema = entry['state']['schema']
    if schema not in (V2_PRIMARY, V3_PRIMARY):
        raise ValueError('Only primary V2/V3 bundles are supported')
    method = preferred_method(entry['state']['thresholds'], entry['variant'])
    declaration = {'label': declared_label, 'source': label_source,
                   'verification': LABEL_VERIFICATION}
    selection = (_load_manifest(manifest, root, limit, seed, declaration) if manifest else
                 _new_manifest(root, limit, seed, declaration))
    output.mkdir(parents=True, exist_ok=False)
    # Persist the complete sample selection and source hashes BEFORE loading/scoring.
    _write_json(output / 'manifest.json', selection)
    started = time.perf_counter()
    load_error = None
    try:
        detector, lock = registry.loaded(bundle_id)
    except Exception as exc:
        load_error = exc
    model_load_ms = (time.perf_counter() - started) * 1000
    records = []
    with (output / 'results.csv').open('x', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for index, selected in enumerate(selection['entries'], 1):
            row = dict.fromkeys(CSV_FIELDS)
            row.update(sequence=index, relative_path=selected['relative_path'],
                       size_bytes=selected['size_bytes'], file_sha256=selected['file_sha256'],
                       manifest_file_sha256=selected['file_sha256'], declared_label=declared_label,
                       label_source=label_source, label_verification=LABEL_VERIFICATION,
                       schema=schema, extractor=('V3 pinned upstream' if schema == V3_PRIMARY else
                                                'V2 experimental modern-LIEF'),
                       bundle_id=bundle_id, dataset=entry['dataset'], variant=entry['variant'],
                       method=method, scan_status='input_rejected', parse_status='not_attempted',
                       error_code='', error='')
            file_start = time.perf_counter()
            try:
                if selected['input_status'] == 'rejected':
                    raise InputRejected(selected['error_code'], selected['error'], selected['size_bytes'])
                data, info = _read_file(root, selected['relative_path'])
                row.update(info)
                if info['file_sha256'] != selected['file_sha256'] or info['size_bytes'] != selected['size_bytes']:
                    raise InputRejected('changed_since_manifest', 'File bytes differ from the fixed sample manifest')
                if load_error is not None:
                    row['scan_status'] = 'bundle_load_failed'
                    raise load_error
                row.update(scan_status='parse_failed', parse_status='failed')
                parse_start = time.perf_counter()
                try:
                    vector, provenance = _extract(data, schema)
                    vector = detector.schema.matrix(vector)
                    row['extractor_provenance'] = provenance
                finally:
                    row['extraction_ms'] = (time.perf_counter() - parse_start) * 1000
                row.update(parse_status='ok', scan_status='prediction_failed')
                with lock:
                    result = score_input(detector, vector, method)
                selected_score = next(item for item in result['scores'] if item['Method'] == method)
                row.update(scan_status='ok', malware_probability=result['malware_probability'],
                           main_classification=result['main_classification'], score=selected_score['Score'],
                           threshold=selected_score['Threshold'], trigger_alert=result['backdoor_alert'],
                           prediction_ms=result['elapsed_ms'])
            except InputRejected as exc:
                row.update(scan_status='input_rejected', error_code=exc.code, error=str(exc))
            except ExtractionError as exc:
                row.update(scan_status=exc.code if exc.code in ('timeout', 'worker_crashed', 'busy') else 'parse_failed',
                           parse_status='failed', error_code=exc.code, error=str(exc)[:2000])
            except Exception as exc:
                row.update(error_code=type(exc).__name__, error=str(exc)[:2000])
            row['file_total_ms'] = (time.perf_counter() - file_start) * 1000
            records.append(row)
            csv_row = {**row, 'extractor_provenance': json.dumps(row['extractor_provenance'], ensure_ascii=True)}
            writer.writerow(csv_row)
            stream.flush()
    count = len(records)
    ok = sum(row['scan_status'] == 'ok' for row in records)
    alerts = sum(row['trigger_alert'] is True for row in records)
    summary = {
        'format': 'xsentinel-static-check-v2', 'completed_utc': datetime.now(timezone.utc).isoformat(),
        'extraction_policy': {'worker': 'pe-worker-v1', 'timeout_seconds': timeout_seconds()},
        'status': 'completed' if ok == count else 'completed_with_errors',
        'execution': 'Samples were read for static extraction only; NEVER EXECUTED',
        'input_dir': str(root), 'bundle_root': str(bundle_root), 'bundle_id': bundle_id,
        'dataset': entry['dataset'], 'variant': entry['variant'], 'schema': schema, 'method': method,
        'manifest_sha256': selection['manifest_sha256'], 'manifest_reused': manifest is not None,
        'label_declaration': declaration, 'selected_count': count, 'scored_count': ok,
        'error_count': count - ok,
        'status_counts': {key: sum(row['scan_status'] == key for row in records)
                          for key in sorted({row['scan_status'] for row in records})},
        'classification_counts': {key: sum(row['main_classification'] == key for row in records)
                                  for key in ('BENIGN', 'MALWARE')},
        'classification_unavailable_count': count - ok,
        'trigger_alert_rate': {'numerator': alerts, 'denominator': count, 'value': alerts / count},
        'scope': [
            'Labels are USER_DECLARED, not independently verified; unknown is never converted to a label.',
            'Alert rate uses ALL selected samples, including errors; errors are not negative predictions.',
            'A trigger alert is suspicion, not verified backdoor presence or backdoor recall.',
            'No accuracy, backdoor recall, attack success or future false-positive guarantee is claimed.',
            'V2 modern-LIEF extraction is experimental; V3 fixture parity is not original BODMAS parity.',
            'Current Detector.predict computes all available methods including STRIP; selected method chooses the reported alert.',
            'Times are local observations, not research benchmarks; model loading and manifest creation are excluded from per-file times.',
        ],
        'model_load_ms': model_load_ms, 'records': records,
    }
    _write_json(output / 'summary.json', summary)
    return summary


def _positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError('Must be at least 1')
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    listing = commands.add_parser('list-bundles', help='List primary bundle IDs without scanning inputs')
    listing.add_argument('--bundle-root', default='outputs/primary')
    check = commands.add_parser('scan', help='Read an already-extracted directory; never execute its files')
    for name in ('input-dir', 'bundle-id', 'out', 'label-source'):
        check.add_argument('--' + name, required=True)
    check.add_argument('--bundle-root', default='outputs/primary')
    check.add_argument('--limit', type=_positive, required=True)
    check.add_argument('--seed', type=int, default=17)
    check.add_argument('--declared-label', choices=('unknown', 'benign', 'malware'), required=True)
    check.add_argument('--manifest', help='Reuse manifest.json with identical limit, seed and declaration')
    args = parser.parse_args(argv)
    try:
        if args.command == 'list-bundles':
            print(json.dumps(list_bundles(args.bundle_root), indent=2, ensure_ascii=True))
            return 0
        options = vars(args).copy()
        options.pop('command')
        summary = scan(**options)
        print(json.dumps({k: v for k, v in summary.items() if k != 'records'}, indent=2, ensure_ascii=True))
        return 0 if summary['error_count'] == 0 else 1
    except (ValueError, KeyError, OSError) as exc:
        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
