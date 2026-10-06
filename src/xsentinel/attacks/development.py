"""Train-only attack screening. Never opens official test arrays or detector state."""
import csv
import gc
import time
import zipfile
from dataclasses import asdict
from pathlib import Path

import numpy as np

from xsentinel.attacks.trigger import FEASIBLE, Trigger, poison, select_trigger
from xsentinel.baselines.scores import contributions
from xsentinel.evaluation.metrics import rate
from xsentinel.experiment import performance_from_predictions, train
from xsentinel.schema import DIM, SCHEMA_VERSION
from xsentinel.utils import read_json, sha256, write_json


def stratified_partitions(y, sizes, seed):
    """Disjoint balanced subsets; random sampling across all original train shards."""
    y = np.asarray(y)
    if y.ndim != 1 or not np.isin(y, [0, 1]).all():
        raise ValueError('Expected labeled binary training rows')
    if any(not isinstance(n, int) or n < 2 or n % 2 for n in sizes.values()):
        raise ValueError('Partition sizes must be positive even integers >= 2')
    rng = np.random.default_rng(seed)
    pools = {label: rng.permutation(np.flatnonzero(y == label)) for label in (0, 1)}
    if any(len(pool) < sum(sizes.values()) // 2 for pool in pools.values()):
        raise ValueError('Insufficient training rows per class for disjoint partitions')
    result = {}; offset = 0
    for name, n in sizes.items():
        result[name] = np.sort(np.concatenate([pool[offset:offset+n//2] for pool in pools.values()]))
        offset += n // 2
    return result


def joint_benign_trigger(model, X, y, legacy, rare_quantile):
    """Use the same feature pair, but a rare observed benign tuple pulling benign.

    Rank rare tuples by their mean signed joint SHAP (most negative first), then
    frequency and lexicographic values. This is an experimental adaptation, not
    Severi's combined greedy selector or proof of PE realizability.
    """
    if not 0 < rare_quantile <= 1:
        raise ValueError('Rare tuple quantile must be in (0,1]')
    benign = np.asarray(X[np.asarray(y) == 0])
    if not len(benign):
        raise ValueError('No benign selection rows')
    pair = legacy.indices
    tuples, inverse, counts = np.unique(benign[:, pair], axis=0, return_inverse=True, return_counts=True)
    signed = contributions(model, benign)[:, pair].sum(axis=1)
    means = np.bincount(inverse, weights=signed, minlength=len(tuples)) / counts
    cutoff = float(np.quantile(counts, rare_quantile))
    candidates = np.flatnonzero((counts <= cutoff) & (means < 0))
    if not len(candidates):
        raise ValueError('No rare observed benign tuple with negative joint SHAP; no fallback')
    chosen = min(candidates, key=lambda k: (float(means[k]), int(counts[k]), tuple(tuples[k])))
    trigger = Trigger(legacy.kind, list(pair), tuples[chosen].astype(float).tolist(), legacy.profile,
                      'train_selection_observed_benign_tuple_rare_negative_joint_shap')
    diagnostics = {'benign_selection_rows': len(benign), 'distinct_tuples': len(tuples),
                   'rarity_count_cutoff': cutoff, 'candidate_count': len(candidates),
                   'selected_support': int(counts[chosen]), 'selected_mean_joint_shap': float(means[chosen])}
    return trigger, diagnostics


def _screen(clean_p, poisoned_p, clean_trigger_p, poisoned_trigger_p, y, rules):
    t = rules['malware_threshold']; malware = y == 1
    eligible = clean_p[malware] >= t
    before = clean_trigger_p[eligible] < t; after = poisoned_trigger_p[eligible] < t
    clean_perf = performance_from_predictions(clean_p, y, t)
    poison_perf = performance_from_predictions(poisoned_p, y, t)
    n = int(eligible.sum())
    gain = float(np.mean(after.astype(int) - before.astype(int))) if n else None
    checks = {
        'enough_eligible': n >= rules['min_eligible'],
        'asr': n > 0 and float(after.mean()) >= rules['min_asr'],
        'paired_gain_over_clean_trigger': gain is not None and gain >= rules['min_paired_gain'],
        'accuracy_preserved': clean_perf['accuracy'] - poison_perf['accuracy'] <= rules['max_accuracy_drop'],
        'tpr_preserved': clean_perf['tpr']['rate'] - poison_perf['tpr']['rate'] <= rules['max_tpr_drop'],
        'fpr_preserved': poison_perf['fpr']['rate'] - clean_perf['fpr']['rate'] <= rules['max_fpr_increase'],
    }
    return {'clean_performance': clean_perf, 'poisoned_clean_performance': poison_perf,
            'eligible_count': n, 'attack_asr': rate(after), 'clean_trigger_asr': rate(before),
            'new_evasions': rate(after & ~before), 'lost_evasions': rate(before & ~after),
            'paired_gain': gain, 'screen_checks': checks, 'screen_pass': all(checks.values())}


def _peak_memory():
    """Native whole-process peak, including NumPy/LightGBM allocations."""
    import sys
    if sys.platform == 'win32':
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('page_faults', wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in ('peak_working_set', 'working_set',
                'peak_paged_pool', 'paged_pool', 'peak_nonpaged_pool', 'nonpaged_pool',
                'pagefile', 'peak_pagefile')]
        counters = Counters(); counters.cb = ctypes.sizeof(counters)
        kernel = ctypes.WinDLL('kernel32'); kernel.GetCurrentProcess.restype = wintypes.HANDLE
        query = ctypes.WinDLL('psapi').GetProcessMemoryInfo
        query.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        if query(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            return {'peak_working_set_mib': counters.peak_working_set / 2**20,
                    'peak_pagefile_mib': counters.peak_pagefile / 2**20,
                    'method': 'Windows GetProcessMemoryInfo; whole process, including native allocations'}
        return {'measurement_unavailable': True}
    import resource
    scale = 2**20 if sys.platform == 'darwin' else 1024
    return {'peak_working_set_mib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / scale,
            'method': 'getrusage whole-process peak RSS'}


def run_development(directory, output, config_path):
    config = read_json(config_path)
    # Intentionally restricted: vector-stress and larger trigger families are separate decisions.
    if config['attack_profile'] != 'feasible' or config['trigger'] != 'concentrated':
        raise ValueError('Development screen supports feasible concentrated triggers only')
    selectors = config['selectors']
    if not selectors or len(set(selectors)) != len(selectors) or set(selectors) - {'legacy_rare', 'joint_benign_rare'}:
        raise ValueError('Unknown or duplicate selector')
    rates = config['rates']
    if not rates or len(set(rates)) != len(rates) or any(not 0 < r < 1 for r in rates):
        raise ValueError('Invalid or duplicate poison rates')
    root = Path(output)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError('Use a fresh development output directory')
    root.mkdir(parents=True, exist_ok=True)
    source = Path(directory); meta = read_json(source/'dataset.json')
    if meta['schema'] != SCHEMA_VERSION:
        raise ValueError('Dataset schema mismatch')
    # No call to load_data(): that helper opens both train and test.
    data = {}
    for kind in ('X', 'y', 'ids'):
        filename = f'{kind}_train.npy'
        if sha256(source/filename) != meta['array_sha256'][filename]:
            raise ValueError('Training checksum mismatch: '+filename)
        data[kind] = np.load(source/filename, mmap_mode='r', allow_pickle=False)
    if data['X'].shape != (len(data['y']), DIM) or len(data['ids']) != len(data['y']):
        raise ValueError('Training shape mismatch')
    sizes = {'fit': config['fit_rows'], 'selection': config['selection_rows'],
             'development': config['development_rows']}
    partitions = stratified_partitions(data['y'], sizes, config['split_seed'])
    if config['selection_samples'] != sizes['selection']:
        raise ValueError('Selection sample count must equal the locked selection partition size')
    np.savez(root/'partitions.npz', **partitions)
    write_json(root/'partitions.json', {'split_seed': config['split_seed'], 'sizes': sizes,
        'class_balance': 'equal benign/malware in each training-derived partition',
        'ids': {k: data['ids'][v].astype(str).tolist() for k, v in partitions.items()},
        'sha256': sha256(root/'partitions.npz')})
    package = Path(__file__).resolve().parents[1]
    sources = {f.as_posix(): f for f in sorted(package.rglob('*.py'))}
    with zipfile.ZipFile(root/'source_snapshot.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for f in sources.values(): archive.write(f, f.relative_to(package.parent).as_posix())
    manifest = {'status': 'running', 'purpose': 'development screen, not final detector evaluation',
        'config': config, 'config_sha256': sha256(config_path), 'dataset_sha256': sha256(source/'dataset.json'),
        'training_sha256': {k: meta['array_sha256'][f'{k}_train.npy'] for k in data},
        'partition_sha256': sha256(root/'partitions.npz'), 'source_snapshot_sha256': sha256(root/'source_snapshot.zip'),
        'source_sha256': {f.relative_to(package).as_posix(): sha256(f) for f in sources.values()},
        'feasible_indices': FEASIBLE.tolist(), 'test_arrays_opened': False,
        'original_dataset_pilot': meta['pilot'], 'results_scope': 'one-seed subsampled train development',
        'poison_rate_denominator': 'all labeled rows in the fit partition',
        'screen_rule_note': 'Predeclared development heuristics; passing is not proof of a backdoor or final validation'}
    write_json(root/'run_manifest.json', manifest)
    started = time.perf_counter()
    try:
        fit_ids = partitions['fit']; selection_ids = partitions['selection']; dev_ids = partitions['development']
        X = np.asarray(data['X'][fit_ids]); y = np.asarray(data['y'][fit_ids])
        selection = np.asarray(data['X'][selection_ids]); sy = np.asarray(data['y'][selection_ids])
        print(f'Clean fit: {len(y)} rows; selection: {len(sy)}; development: {len(dev_ids)}. Official test is closed.', flush=True)
        clean = train(X, y, root/'clean.txt', config, config['seed'])
        legacy = select_trigger(clean, selection, sy, config['trigger'], config['seed'],
                                config['attack_profile'], config['selection_samples'])
        candidates = {}; selection_failures = {}
        for selector in selectors:
            try:
                trigger, details = (legacy, {}) if selector == 'legacy_rare' else joint_benign_trigger(
                    clean, selection, sy, legacy, config['rare_tuple_quantile'])
                candidates[selector] = trigger
                write_json(root/f'trigger_{selector}.json', {'trigger': asdict(trigger), 'diagnostics': details,
                    'selection_partition_sha256': sha256(root/'partitions.npz'),
                    'clean_model_sha256': sha256(root/'clean.txt')})
            except ValueError as exc:
                selection_failures[selector] = str(exc)
        # Lock all candidates before any development predictions; no adaptive candidate additions.
        write_json(root/'candidate_lock.json', {'config_sha256': sha256(config_path),
            'triggers': {k: asdict(v) for k, v in candidates.items()}, 'selection_failures': selection_failures})
        del selection; gc.collect()
        dev = np.asarray(data['X'][dev_ids]); dy = np.asarray(data['y'][dev_ids])
        clean_p = clean.predict(dev, num_threads=4); malware = dy == 1
        results = []
        for selector, trigger in candidates.items():
            triggered = trigger.apply(dev[malware]); clean_trigger_p = clean.predict(triggered, num_threads=4)
            for poison_rate in rates:
                dest = root/f'{selector}_{poison_rate:g}'; dest.mkdir()
                print(f'Attack development: {selector}, poison={poison_rate}', flush=True)
                Xp, poison_ids = poison(X, y, trigger, poison_rate, config['seed'])
                write_json(dest/'attack_manifest.json', {'trigger': asdict(trigger), 'seed': config['seed'],
                    'poison_rate': poison_rate, 'fit_rows': len(y), 'poison_count': len(poison_ids),
                    'poison_ids': data['ids'][fit_ids[poison_ids]].astype(str).tolist(),
                    'clean_model_sha256': sha256(root/'clean.txt'), 'candidate_lock_sha256': sha256(root/'candidate_lock.json')})
                model = train(Xp, y, dest/'poisoned.txt', config, config['seed']); del Xp; gc.collect()
                poison_p = model.predict(dev, num_threads=4); trigger_p = model.predict(triggered, num_threads=4)
                result = _screen(clean_p, poison_p, clean_trigger_p, trigger_p, dy, config['screen'])
                result.update(selector=selector, poison_rate=poison_rate, model_sha256=sha256(dest/'poisoned.txt'))
                write_json(dest/'evaluation.json', result); results.append(result)
                with (dest/'predictions.csv').open('w', newline='', encoding='utf8') as f:
                    writer = csv.writer(f); writer.writerow(['sample_id', 'label', 'clean_p', 'poisoned_p', 'clean_trigger_p', 'poisoned_trigger_p'])
                    j = 0
                    for sid, label, cp, pp in zip(data['ids'][dev_ids].astype(str), dy, clean_p, poison_p):
                        writer.writerow([sid, int(label), cp, pp, clean_trigger_p[j] if label == 1 else '', trigger_p[j] if label == 1 else ''])
                        if label == 1: j += 1
                write_json(root/'progress.json', results)
                print(f"ASR={result['attack_asr']['rate']}; clean-trigger={result['clean_trigger_asr']['rate']}; screen_pass={result['screen_pass']}", flush=True)
                del model; gc.collect()
        manifest.update(status='complete', elapsed_seconds=time.perf_counter()-started,
                        completed_models=len(results), selection_failures=selection_failures,
                        memory=_peak_memory())
        write_json(root/'run_manifest.json', manifest)
        _report(root, config, results, selection_failures)
        return results
    except Exception as exc:
        manifest.update(status='failed', error=str(exc), elapsed_seconds=time.perf_counter()-started)
        write_json(root/'run_manifest.json', manifest)
        raise


def _report(root, config, results, failures):
    fields = ['selector', 'poison_rate', 'asr', 'eligible', 'clean_trigger_asr', 'paired_gain',
              'clean_accuracy', 'poisoned_accuracy', 'poisoned_tpr', 'poisoned_fpr', 'screen_pass']
    rows = [{'selector': r['selector'], 'poison_rate': r['poison_rate'], 'asr': r['attack_asr']['rate'],
             'eligible': r['eligible_count'], 'clean_trigger_asr': r['clean_trigger_asr']['rate'],
             'paired_gain': r['paired_gain'], 'clean_accuracy': r['clean_performance']['accuracy'],
             'poisoned_accuracy': r['poisoned_clean_performance']['accuracy'],
             'poisoned_tpr': r['poisoned_clean_performance']['tpr']['rate'],
             'poisoned_fpr': r['poisoned_clean_performance']['fpr']['rate'], 'screen_pass': r['screen_pass']} for r in results]
    with (root/'results.csv').open('w', newline='', encoding='utf8') as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    lines = ['# Train-only attack development', '',
             f"Seed {config['seed']}; fit/selection/development = {config['fit_rows']}/{config['selection_rows']}/{config['development_rows']}, balanced stratified subsets of official train.", '',
             'Official test arrays were not opened. All selectors, rates and screen rules were locked before development predictions. This is exploratory training development, not final research evidence.', '',
             '| Selector | Poison rate | ASR | Clean-trigger ASR | Paired gain | Clean accuracy after poisoning | Screen pass |',
             '|---|---:|---:|---:|---:|---:|---|']
    for r in rows:
        def pct(value): return f'{value:.2%}' if value is not None else 'undefined'
        lines.append(f"| {r['selector']} | {pct(r['poison_rate'])} | {pct(r['asr'])} | {pct(r['clean_trigger_asr'])} | {pct(r['paired_gain'])} | {pct(r['poisoned_accuracy'])} | {r['screen_pass']} |")
    lines += ['', 'The joint selector uses an observed benign tuple and negative joint SHAP; it remains an adaptation and does not prove binary realizability. Feasible spread/cross are still unsupported.', '',
              'Screen rules (heuristics, not statistical proof):', '```json', __import__('json').dumps(config['screen'], indent=2), '```', '',
              'Preserve this run. Any subsequent change needs a new config/output and must document reuse of development data. A passing candidate still needs independent confirmation and full-size training; a failing screen does not establish defense efficacy.']
    if failures: lines += ['', 'Selection failures: '+str(failures)]
    if config.get('development_history'):
        lines += ['', 'Development history (observed data reuse; not independent confirmation):',
                  '```json', __import__('json').dumps(config['development_history'], indent=2), '```']
    (root/'report.md').write_text('\n'.join(lines)+'\n', encoding='utf8')
