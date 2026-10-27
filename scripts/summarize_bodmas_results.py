"""Audit member-supplied JSON/CSV and build a static BODMAS supplement.

No archive program is imported, no binary is extracted, and no detector runs.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import statistics
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'BODMAS_RESULTS.zip'
OUT = ROOT / 'outputs/bodmas_2026_10_23'
DELIVERY = ROOT / 'output/bodmas_2026_10_23'
KIT = ROOT / 'output/bodmas_demo_2026_10_19/X_SENTINEL_BODMAS_VM'
PREFIX = 'BODMAS_RESULTS/results/'
ALIASES = ('2018-reduced', '2018-full', '2024-reduced', '2024-full')
GROUPS = ('smoke1', 'benign1', 'pilot20', 'bodmas200')
EXPECTED_ARCHIVE_SHA256 = 'c528ef4931a672123d47bfd30b6e0bdc5ceb4b18d2cf5a5d296f030dc31d8a87'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('utf8')


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                               allow_nan=False) + '\n', encoding='utf8')


def write_csv(name, rows):
    require(bool(rows), 'Empty output: ' + name)
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=True) if isinstance(v, (dict, list))
                             else v for k, v in row.items()})


def percentile(values, q):
    """Linear interpolation at (n-1)*q, separately for each measured phase."""
    values = sorted(values)
    at = (len(values) - 1) * q
    lo, hi = math.floor(at), math.ceil(at)
    return values[lo] + (values[hi] - values[lo]) * (at - lo)


def csv_value(value):
    if value is None:
        return ''
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=True)
    return str(value)


def validate_run(summary, manifest, csv_rows, expected, bundle):
    """Fail closed on inconsistent counts, pairing, score rules or metadata."""
    expected_digest = digest(canonical({k: v for k, v in manifest.items()
                                        if k != 'manifest_sha256'}))
    require(manifest['manifest_sha256'] == expected_digest, 'Manifest checksum mismatch')
    require(summary['manifest_sha256'] == expected_digest, 'Summary manifest mismatch')
    records, entries = summary['records'], manifest['entries']
    n = len(records)
    require(n == len(entries) == len(csv_rows) == summary['selected_count']
            == manifest['selected_count'], 'Inconsistent selected counts')
    require(len({r['file_sha256'] for r in records}) == n, 'Duplicate input hashes')
    for key, catalog_key in [('bundle_id', 'id'), ('schema', 'schema'),
                              ('method', 'method'), ('variant', 'variant'), ('dataset', 'dataset')]:
        require(summary[key] == expected[catalog_key], f'Unexpected {key}')
    for i, (record, entry, row) in enumerate(zip(records, entries, csv_rows), 1):
        require(record['sequence'] == i, 'Record sequence mismatch')
        require(set(record) == set(row), 'CSV columns mismatch')
        for key, value in record.items():
            if key == 'extractor_provenance':
                require(json.loads(row[key]) == value, f'CSV nested field mismatch: {key}')
            else:
                require(row[key] == csv_value(value), f'CSV/JSON mismatch: {key}')
        for key in ('relative_path', 'size_bytes', 'file_sha256'):
            require(record[key] == entry[key], f'Manifest/record mismatch: {key}')
        require(record['manifest_file_sha256'] == entry['file_sha256'], 'Changed input hash')
        for key in ('bundle_id', 'schema', 'method', 'dataset', 'variant'):
            require(record[key] == summary[key], f'Record metadata mismatch: {key}')
        if record['scan_status'] == 'ok':
            for key in ('malware_probability', 'score', 'threshold', 'prediction_ms',
                        'extraction_ms', 'file_total_ms'):
                require(isinstance(record[key], (int, float)) and math.isfinite(record[key]),
                        f'Invalid numeric field: {key}')
            require(record['threshold'] == bundle['thresholds'][summary['method']], 'Changed threshold')
            require(record['trigger_alert'] == (record['score'] > record['threshold']), 'Alert rule mismatch')
            label = 'MALWARE' if record['malware_probability'] >= bundle['config']['malware_threshold'] else 'BENIGN'
            require(record['main_classification'] == label, 'Classification rule mismatch')
        else:
            require(record['main_classification'] is None and record['trigger_alert'] is None,
                    'An error must not become a negative prediction')
    ok = sum(r['scan_status'] == 'ok' for r in records)
    alerts = sum(r['trigger_alert'] is True for r in records)
    require(summary['scored_count'] == ok and summary['error_count'] == n - ok,
            'Scored/error count mismatch')
    require(summary['classification_unavailable_count'] == n - ok, 'Unavailable count mismatch')
    for label in ('BENIGN', 'MALWARE'):
        require(summary['classification_counts'][label] == sum(r['main_classification'] == label for r in records),
                'Classification count mismatch')
    counts = {s: sum(r['scan_status'] == s for r in records) for s in {r['scan_status'] for r in records}}
    require(summary['status_counts'] == counts, 'Status counts mismatch')
    rate = summary['trigger_alert_rate']
    require(rate['numerator'] == alerts and rate['denominator'] == n
            and abs(rate['value'] - alerts / n) < 1e-12, 'Alert rate mismatch')


def read_runs():
    require(digest(ARCHIVE.read_bytes()) == EXPECTED_ARCHIVE_SHA256,
            'Archive changed: create a new versioned review before reusing report prose')
    catalog = json.loads((KIT / 'bundle_catalog.json').read_text(encoding='utf8'))
    runs, inventory = {}, []
    with ZipFile(ARCHIVE) as archive:
        infos = archive.infolist()
        require(len({i.filename for i in infos}) == len(infos), 'Duplicate archive names')
        require(sum(i.file_size for i in infos) < 64 * 1024**2, 'Archive exceeds audit size limit')
        for item in infos:
            path = PurePosixPath(item.filename)
            require(not path.is_absolute() and '..' not in path.parts and '\\' not in item.filename,
                    'Unsafe archive path')
            require(not item.flag_bits & 1 and item.file_size < 20 * 1024**2, 'Unreadable/oversized member')
            if not item.is_dir():
                require(path.suffix.lower() in {'.json', '.csv', '.md', '.txt', '.log'}, 'Unexpected member type')
                data = archive.read(item)
                inventory.append({'path': item.filename, 'bytes': len(data), 'sha256': digest(data)})
        require(archive.testzip() is None, 'CRC error')
        for group in GROUPS:
            for alias in ALIASES:
                run = group + '_' + alias.replace('-', '_')
                prefix = PREFIX + run + '/'
                summary = json.loads(archive.read(prefix + 'summary.json'))
                require(summary['selected_count'] == {'smoke1': 1, 'benign1': 1, 'pilot20': 20, 'bodmas200': 200}[group],
                        'Run size differs from the locked report scope')
                manifest = json.loads(archive.read(prefix + 'manifest.json'))
                rows = list(csv.DictReader(io.StringIO(archive.read(prefix + 'results.csv').decode('utf-8-sig'))))
                entry = catalog[alias]
                bundle = json.loads((KIT / 'outputs/primary' / entry['relative_path'] / 'bundle.json').read_text())
                validate_run(summary, manifest, rows, entry, bundle)
                runs[run] = {'summary': summary, 'manifest': manifest, 'alias': alias, 'group': group}
        logs = {name: archive.read('BODMAS_RESULTS/logs/' + name).decode('utf8')
                for name in ('smoke.log', 'benign.log')}
    return runs, inventory, logs, len(infos)


def make_blocks(summary_rows, timing_rows):
    return [
        {'kind': 'heading1', 'text': 'APPENDIX C SUPPLEMENTARY STATIC BODMAS CHECK'},
        {'kind': 'p', 'text': 'The member-supplied BODMAS check extends the evidence for the binary input pipeline. It does not change the frozen vector-attack experiments, model weights, W50 fusion or calibrated thresholds. The supplied records are dated 22 October 2026; the archive was audited on 23 October 2026. No BODMAS binaries or feature vectors were included, so the audit recomputes tables from saved records rather than independently repeating extraction or inference.'},
        {'kind': 'heading2', 'text': 'A Setup and evidence source'},
        {'kind': 'p', 'text': 'The member reports teacher-supplied disarmed BODMAS files [3], sampled from 57,293 candidate paths using seed 17. The manifest records sorting the paths and sampling without replacement before scoring. The full population list, original metadata and pre-run timestamps are unavailable for independent verification. Labels remain user-declared; dataset overlap with EMBER training or calibration has not been independently checked. This is a supplementary static check, not a new independent backdoor test set.'},
        {'kind': 'p', 'text': 'The four frozen configurations are EMBER2018 and EMBER2024, each with Reduced and Full, at seed 17, spread Structural poisoning and rate 0.02. EMBER2018 uses the experimental modern-LIEF V2 reader; EMBER2024 uses the pinned V3 reader. The member reports Kali Linux and Docker. Bundle IDs, schemas, methods, declared V3 source hashes and thresholds agree with the original kit. This metadata agreement does not independently establish the actual image/model bytes or container runtime restrictions used on the VM.'},
        {'kind': 'heading2', 'text': 'B Processing and model decisions'},
        {'kind': 'caption', 'text': 'TABLE C-I\nSTATIC RESULTS ON THE SAME 200 DECLARED MALWARE FILES'},
        {'kind': 'table', 'widths': [1.0, .8, .7, .7, .65, .9, .8, .7],
         'rows': [['Dataset', 'Variant', 'Selected', 'Scored', 'Errors', 'MALWARE', 'BENIGN', 'Alerts']] +
                 [[r['dataset'].replace('EMBER', ''), r['variant'].title(), str(r['selected']), str(r['scored']),
                   str(r['errors']), str(r['predicted_malware']), str(r['predicted_benign']), str(r['alerts'])] for r in summary_rows]},
        {'kind': 'p', 'text': 'All four configurations use the same 200 distinct file hashes and score the same 175 inputs (87.5%); 25 inputs (12.5%) have no decision. CSV fields agree with the corresponding JSON records and manifest entries. EMBER2018 predicts MALWARE for 162/175 scored inputs (92.57%); EMBER2024 predicts MALWARE for 175/175. The latter is a prediction count conditional on successful processing, not 100% system accuracy. There are 200 distinct declared-malware inputs, not 800; the 20 pilot inputs are a subset of these 200.'},
        {'kind': 'p', 'text': 'Within each dataset, Reduced and Full produce the same class and alert decisions on this sample, although suspicion scores differ. The two EMBER2018 alerts concern the same two hashes in both variants; both are classified BENIGN by the main model. No verified trigger labels are available, so these alerts do not establish backdoor detection. Their frequency is 2/175 (1.14%) among scored inputs or 2/200 (1.00%) among all selected inputs. Errors remain unavailable decisions, not negative alerts. EMBER2024 has zero alerts among its 175 scored inputs.'},
        {'kind': 'heading2', 'text': 'C Header failures and the benign control'},
        {'kind': 'p', 'text': 'All 25 failed hashes report ValueError: Invalid PE signature/header offset in both schemas. This guard precedes LIEF parsing. The records do not establish whether disarming caused the failures; unassigned relocation/section warnings in aggregate logs cannot establish a cause for these particular files. No failed input was replaced or repaired during aggregation.'},
        {'kind': 'p', 'text': 'Smoke and benign runs reuse one declared-benign file, not two independent controls. Both EMBER2018 variants classify it BENIGN (p = 0.044262), while both EMBER2024 variants classify it MALWARE (p = 0.957886); none raises a trigger alert. This is an apparent classification false positive against the declared label, not a trigger false positive. One input is insufficient to estimate a population false-positive rate. Its hash, 72524cf3...1e4485, differs from the original kit fixture d5a4dc25...db9d23a; the source/build correspondence of the received file remains unverified.'},
        {'kind': 'heading2', 'text': 'D Timing boundaries'},
        {'kind': 'caption', 'text': 'TABLE C-II\nOBSERVED MEDIAN AND P95 TIMES IN MILLISECONDS FOR 175 SCORED FILES'},
        {'kind': 'table', 'widths': [1.0, .8, 1.25, 1.55, 1.3, 1.35],
         'rows': [['Dataset', 'Variant', 'Prediction median', 'Extraction median', 'File total median', 'File total P95']] +
                 [[r['dataset'].replace('EMBER', ''), r['variant'].title(), f"{r['prediction_median_ms']:.2f}",
                   f"{r['extraction_median_ms']:.2f}", f"{r['file_total_median_ms']:.2f}", f"{r['file_total_p95_ms']:.2f}"] for r in timing_rows]},
        {'kind': 'p', 'text': 'Each statistic uses the 175 scored inputs of that run. The supplied kit uses the suite path, including available STRIP computation; the selected method determines the reported alert. Per-file times exclude model loading and manifest creation and are not API, database, upload or browser timings. These VM observations cannot be compared directly with the selected-path benchmark on another host. P95 uses linear interpolation for each measured quantity separately.'},
        {'kind': 'heading2', 'text': 'E Audit discrepancies and limits'},
        {'kind': 'p', 'text': 'The smoke.log and benign.log summaries give probabilities 0.169/0.748, which conflict with their CSV/JSON values 0.044262/0.957886. Tables use the internally consistent structured records; the discrepant logs are retained and unresolved. The evidence does not include the actual runtime code/model inventory, a full source-label mapping or the complete candidate list. These limitations prevent a claim of independent reproduction or representative BODMAS performance.'},
        {'kind': 'p', 'text': 'The supplied records support successful processing for 175 of the 200 selected declared-malware files. They do not establish realizable feature-vector triggers, preserved malware functionality after transformation, backdoor recall, general false-positive control or deployment security. Those limits remain part of the study.'},
    ]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    DELIVERY.mkdir(parents=True, exist_ok=True)
    runs, inventory, logs, entry_count = read_runs()
    main_runs = [runs['bodmas200_' + alias.replace('-', '_')] for alias in ALIASES]
    ref = main_runs[0]['summary']['records']
    hashes = [r['file_sha256'] for r in ref]
    for run in main_runs:
        require([r['file_sha256'] for r in run['summary']['records']] == hashes, 'Main inputs not paired')
    summary_rows, timing_rows, all_records, alert_rows, benign_rows = [], [], [], [], []
    all_run_rows = []
    for name, run in runs.items():
        s = run['summary']
        all_run_rows.append({'run': name, 'selected': s['selected_count'], 'scored': s['scored_count'],
                             'errors': s['error_count'], 'manifest_sha256': s['manifest_sha256']})
    for run in main_runs:
        s = run['summary']
        records = s['records']
        ok = [r for r in records if r['scan_status'] == 'ok']
        alerts = sum(r['trigger_alert'] is True for r in records)
        row = {'dataset': s['dataset'], 'variant': s['variant'], 'selected': len(records), 'scored': len(ok),
               'errors': len(records) - len(ok), 'processing_rate': len(ok) / len(records),
               'predicted_malware': sum(r['main_classification'] == 'MALWARE' for r in ok),
               'predicted_benign': sum(r['main_classification'] == 'BENIGN' for r in ok), 'alerts': alerts,
               'alert_rate_among_scored': alerts / len(ok), 'alert_rate_all_selected': alerts / len(records),
               'bundle_id': s['bundle_id'], 'method': s['method'], 'threshold': ok[0]['threshold']}
        summary_rows.append(row)
        time_row = {'dataset': s['dataset'], 'variant': s['variant'], 'n_scored': len(ok)}
        for source, label in [('prediction_ms', 'prediction'), ('extraction_ms', 'extraction'), ('file_total_ms', 'file_total')]:
            values = [r[source] for r in ok]
            time_row.update({label + '_median_ms': statistics.median(values), label + '_p95_ms': percentile(values, .95),
                             label + '_max_ms': max(values)})
        timing_rows.append(time_row)
        all_records.extend(records)
        alert_rows.extend(r for r in records if r['trigger_alert'] is True)
        benign_rows.extend(runs['benign1_' + run['alias'].replace('-', '_')]['summary']['records'])
    paired, errors = [], []
    for i, record in enumerate(ref):
        row = {k: record[k] for k in ('relative_path', 'file_sha256', 'size_bytes', 'declared_label', 'label_verification')}
        for run in main_runs:
            result = run['summary']['records'][i]
            for key in ('scan_status', 'main_classification', 'malware_probability', 'score', 'threshold',
                        'trigger_alert', 'error_code', 'error'):
                row[run['alias'].replace('-', '_') + '_' + key] = result[key]
        paired.append(row)
        if record['scan_status'] != 'ok':
            require(all(run['summary']['records'][i]['scan_status'] != 'ok' for run in main_runs), 'Different error cohorts')
            errors.append(row)
    pilot = {r['file_sha256'] for r in runs['pilot20_2018_reduced']['summary']['records']}
    require(pilot <= set(hashes), 'Pilot not subset of main; revise deduplication statement')
    control_hashes = {r['file_sha256'] for r in benign_rows}
    require(len(control_hashes) == 1, 'Expected one unique benign control')
    for group in ('smoke1', 'benign1'):
        for alias in ALIASES:
            require({r['file_sha256'] for r in runs[group + '_' + alias.replace('-', '_')]['summary']['records']}
                    == control_hashes, 'Control hash differs by run')
    issues = [
        {'id': 'LOG_PROBABILITY_CONFLICT', 'status': 'unresolved',
         'evidence': 'smoke.log and benign.log: 0.169/0.748; corresponding CSV/JSON: 0.044261703395332086/0.9578862681721813',
         'handling': 'Use validated CSV/JSON for tables; retain conflicting source logs unchanged.'},
        {'id': 'BENIGN_BYTES_CHANGED', 'status': 'unresolved', 'received_sha256': next(iter(control_hashes)),
         'original_fixture_sha256': 'd5a4dc25d186619d001dcf5c970d8b07aa74b71a8d0e370431cfe00ebdb9d23a',
         'handling': 'Keep source/build correspondence unverified; do not substitute an original fixture result.'},
        {'id': 'SOURCE_AND_RUNTIME_EVIDENCE', 'status': 'incomplete',
         'missing': ['original label/ID mapping and disarm evidence', 'complete candidate path list',
                     'runtime model/code hash inventory', 'actual container invocation or container inspect',
                     'original malware binaries or feature vectors for independent rescoring'],
         'handling': 'Report member-supplied static results; not independent reproduction.'},
    ]
    for filename, text in logs.items():
        require('0.169' in text and '0.748' in text, 'Log discrepancy changed; review narrative')
    write_csv('main_summary.csv', summary_rows)
    write_csv('main_records.csv', all_records)
    write_csv('paired_main_results.csv', paired)
    write_csv('unique_errors.csv', errors)
    write_csv('alerts_by_configuration.csv', alert_rows)
    write_csv('benign_control.csv', benign_rows)
    write_csv('timing.csv', timing_rows)
    write_csv('all_run_inventory.csv', all_run_rows)
    audit = {'format': 'xsentinel-bodmas-aggregation-v1', 'review_date': '2026-10-23',
             'archive_sha256': digest(ARCHIVE.read_bytes()), 'archive_entries': entry_count,
             'archive_files': len(inventory),
             'validated_runs': len(runs), 'main_unique_inputs': len(set(hashes)), 'unique_errors': len(errors),
             'unique_main_alert_inputs': len({r['file_sha256'] for r in alert_rows}),
             'pilot_is_main_subset': True, 'pilot_unique_inputs': len(pilot), 'unique_benign_controls': 1,
             'manifest_csv_summary_consistent': True, 'new_inference_executed': False,
             'labels_independently_verified': False, 'binaries_or_feature_vectors_supplied': False,
             'main_summary': summary_rows, 'timing': timing_rows, 'issues': issues,
             'archive_members': inventory}
    write_json(OUT / 'audit.json', audit)
    write_json(OUT / 'report_blocks.json', make_blocks(summary_rows, timing_rows))
    blocks = make_blocks(summary_rows, timing_rows)
    lines = []
    for block in blocks:
        if block['kind'] == 'table':
            rows = block['rows']
            lines.append('| ' + ' | '.join(rows[0]) + ' |')
            lines.append('|' + '|'.join('---' for _ in rows[0]) + '|')
            lines.extend('| ' + ' | '.join(row) + ' |' for row in rows[1:])
        else:
            prefix = '# ' if block['kind'] == 'heading1' else '## ' if block['kind'] == 'heading2' else ''
            lines.append(prefix + block['text'].replace('\n', ' '))
        lines.append('')
    (DELIVERY / 'BODMAS_REPORT_SECTION_EN.md').write_text('\n'.join(lines), encoding='utf8')
    print(json.dumps({k: v for k, v in audit.items() if k not in ('archive_members', 'main_summary', 'timing', 'issues')}, indent=2))


if __name__ == '__main__':
    main()
