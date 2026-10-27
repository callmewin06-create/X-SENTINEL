"""Reproducible diagnostic checks on existing owned/installed benign inputs.

Never executes input binaries, trains a model, edits a threshold or writes the DB.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
OUT = ROOT / 'outputs/repair_2026_10_23'


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + '\n', encoding='utf8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def prepare():
    path = OUT / 'benign_selection.json'
    if path.exists():
        raise FileExistsError('Keep the frozen selection; use the existing manifest')
    win = Path(os.environ.get('WINDIR', 'C:/Windows'))
    groups = [(win / 'System32', '*.exe', 30, 'Windows System32 EXE'),
              (win / 'System32', '*.dll', 10, 'Windows System32 DLL'),
              (win / 'Microsoft.NET/Framework64/v4.0.30319', '*.exe', 10, '.NET Framework tools')]
    rng = random.Random(23)
    selected, populations, seen = [], [], set()
    for folder, pattern, count, category in groups:
        candidates = sorted(p for p in folder.glob(pattern) if p.is_file() and not p.is_symlink()
                            and 64 <= p.stat().st_size <= 50 * 1024 * 1024)
        populations.append({'category': category, 'paths': [str(p) for p in candidates]})
        order = rng.sample(candidates, len(candidates))
        n = 0
        for p in order:
            data = p.read_bytes()
            digest = sha(data)
            if digest in seen:
                continue
            seen.add(digest)
            selected.append({'path': str(p), 'sha256': digest, 'size': len(data),
                             'category': category, 'label': 'declared_benign_installed_system_file'})
            n += 1
            if n == count:
                break
        if n != count:
            raise ValueError(f'Insufficient inputs for {category}')
    fixtures = []
    for item in json.loads((ROOT / 'output/demo_2026_10_20/catalog.json').read_text()):
        p = ROOT / 'output/demo_2026_10_20/benign' / item['name']
        assert sha(p.read_bytes()) == item['sha256']
        fixtures.append({'path': str(p), 'sha256': item['sha256'], 'size': p.stat().st_size,
                         'category': 'previously observed owned C# fixture', 'label': 'reviewed_source_benign'})
    write('benign_selection.json', {'protocol': 'diagnostic-only-v1', 'seed': 23,
        'rule': 'sorted paths; seeded full permutation; first unique byte hashes per group; no predictions used',
        'purpose': 'diagnosis, not untouched final evaluation or representative FPR estimation',
        'limitations': 'Installed origin is a label declaration; signatures collected separately; no independence from training established',
        'populations': populations, 'selected': selected, 'previously_observed_fixtures': fixtures})
    print('Frozen 50 installed inputs and 3 previously observed fixtures before scoring', flush=True)


def diagnose():
    import numpy as np
    import lightgbm as lgb
    from xsentinel.dashboard_input import prepare_input
    from xsentinel.data.pe_isolation import extract_pe_isolated
    from xsentinel.service.registry import BundleRegistry
    from xsentinel.service.scoring import score_input
    selection = json.loads((OUT / 'benign_selection.json').read_text())
    registry = BundleRegistry()
    entries = [e for e in registry.entries.values() if e['family'] == 'spread_structural'
               and e['seed'] == 17 and e['rate'] == .02]
    assert len(entries) == 4
    models = {}
    for dataset in ('EMBER2018', 'EMBER2024'):
        clean_path = ROOT / f'outputs/primary/{dataset}/protocol_v2/seed_17/clean.txt'
        # LightGBM's native Windows file loader cannot open this Unicode path.
        models[dataset] = lgb.Booster(model_str=clean_path.read_text(encoding='utf8'))
    rows, vectors = [], {}
    samples = selection['previously_observed_fixtures'] + selection['selected']
    for i, item in enumerate(samples, 1):
        data = Path(item['path']).read_bytes()
        assert sha(data) == item['sha256'], 'Input changed since frozen manifest'
        for dataset in ('EMBER2018', 'EMBER2024'):
            group = [e for e in entries if e['dataset'] == dataset]
            detector, _ = registry.loaded(group[0]['id'])
            schema = detector.schema.version
            start = time.perf_counter()
            try:
                vector, provenance = extract_pe_isolated(data, schema)
                x = detector.schema.matrix(vector)
                vectors[item['sha256'] + '_' + dataset] = x
                clean_p = float(models[dataset].predict(x, num_threads=4)[0])
                for entry in group:
                    model, lock = registry.loaded(entry['id'])
                    with lock:
                        result = score_input(model, x, 'X_primary_' + entry['variant'], scope='selected')
                        direct = float(model.model.predict(x, num_threads=4)[0])
                    assert abs(direct - result['malware_probability']) <= 1e-12
                    record = {**item, 'dataset': dataset, 'variant': entry['variant'],
                        'bundle_id': entry['id'], 'schema': schema, 'status': 'ok',
                        'clean_p': clean_p, 'poisoned_p': direct,
                        'clean_classification': 'MALWARE' if clean_p >= result['malware_threshold'] else 'BENIGN',
                        'poisoned_classification': result['main_classification'],
                        'trigger_alert': result['backdoor_alert'],
                        'vector_sha256': sha(np.asarray(x, dtype='<f4').tobytes()),
                        'provenance': provenance, 'scores': result['scores']}
                    rows.append(record)
            except Exception as error:
                rows.extend({**item, 'dataset': dataset, 'variant': e['variant'], 'status': 'error',
                             'error': f'{type(error).__name__}: {error}'} for e in group)
            for record in rows[-2:]:
                record['extraction_and_scoring_wall_ms'] = (time.perf_counter() - start) * 1000
        write('benign_records.json', rows)
        print(f'Diagnostic {i}/{len(samples)}: {Path(item["path"]).name}', flush=True)
    np.savez_compressed(OUT / 'benign_vectors.npz', **vectors)
    summaries = []
    for cohort in ('installed50', 'owned3'):
        for dataset in ('EMBER2018', 'EMBER2024'):
            for variant in ('reduced', 'full'):
                chosen = [r for r in rows if r['dataset'] == dataset and r['variant'] == variant
                          and (r['category'].startswith('previously') == (cohort == 'owned3'))]
                ok = [r for r in chosen if r['status'] == 'ok']
                summaries.append({'cohort': cohort, 'dataset': dataset, 'variant': variant,
                    'selected': len(chosen), 'scored': len(ok), 'errors': len(chosen)-len(ok),
                    'clean_called_malware': sum(r['clean_classification'] == 'MALWARE' for r in ok),
                    'poisoned_called_malware': sum(r['poisoned_classification'] == 'MALWARE' for r in ok),
                    'trigger_alerts': sum(r['trigger_alert'] for r in ok),
                    'label_scope': 'diagnostic declared benign; not representative or independently held out'})
    write('benign_summary.json', summaries)
    with (OUT / 'benign_summary.csv').open('w', newline='', encoding='utf8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summaries[0]))
        writer.writeheader(); writer.writerows(summaries)
    print(json.dumps(summaries, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'diagnose'))
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    {'prepare': prepare, 'diagnose': diagnose}[args.command]()
