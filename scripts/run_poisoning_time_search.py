"""Development-only random-search poisoning experiment; never opens final roles.

Both objective arms inspect the SAME candidate set (shared fits, equal logical
budget). This is a pilot, not an independent final evaluation or robustness claim.
"""
import argparse
import gc
import hashlib
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from xsentinel.primary_workflow import open_roles
from xsentinel.experiment import train
from xsentinel.attacks.primary import VectorTrigger, poison_primary
from xsentinel.attacks.screen import screen_primary
from xsentinel.baselines.scores import contributions
from xsentinel.detection.components import primary_components
from xsentinel.utils import read_json, write_json, sha256


def choose(rows, arm):
    valid = [r for r in rows if r['screen']['strong_and_stealth']]
    if not valid:
        return {'status': 'no_valid_attack', 'selected': None}
    if arm == 'asr_only':
        key = lambda r: (-r['screen']['asr']['rate'], -r['screen']['paired_gain'], r['candidate'])
    elif arm == 'vmc_aware':
        key = lambda r: (r['mean_vmc_eligible'], -r['screen']['asr']['rate'], r['candidate'])
    else:
        raise ValueError('Unknown objective')
    best = min(valid, key=key)
    return {'status': 'selected_on_development', 'selected': best['candidate']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--roles', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--seed', type=int, default=17)
    p.add_argument('--fit-rows', type=int, default=40000)
    p.add_argument('--candidates', type=int, default=4)
    p.add_argument('--rate', type=float, default=.02)
    a = p.parse_args()
    if a.candidates < 2 or a.fit_rows < 2 or a.fit_rows % 2 or not 0 < a.rate < 1:
        p.error('Invalid explicit budget')
    out = Path(a.output)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Use a new output directory; no ambiguous checkpoint resume')
    out.mkdir(parents=True, exist_ok=True)
    state, schema, roles = open_roles(a.roles, ['fit', 'selection', 'development'])
    rng = np.random.default_rng(a.seed)
    fit, sel, dev = (roles[k] for k in ['fit', 'selection', 'development'])
    if a.fit_rows > len(fit['y']):
        raise ValueError('Requested fit exceeds available role')
    ids = np.sort(np.concatenate([rng.choice(np.flatnonzero(fit['y'] == c), a.fit_rows//2, replace=False) for c in [0, 1]]))
    X, y = fit['X'][ids], fit['y'][ids]
    cfg = read_json(ROOT / 'configs/primary_execution.json')
    rules = read_json(ROOT / 'configs/primary_protocol.json')['attack_screen']
    lock = {'kind': 'development_only_pilot', 'args': vars(a), 'roles_sha256': sha256(Path(a.roles)/'roles.json'),
            'source_sha256': sha256(__file__), 'schema_sha256': schema.fingerprint,
            'fit_ids': fit['ids'][ids].tolist(), 'selection_ids': sel['ids'].tolist(),
            'development_ids': dev['ids'].tolist(), 'execution': cfg, 'screen': rules,
            'held_out_roles_opened': [], 'historical_pools_reused': True,
            'candidate_geometry': {'structural': 4, 'behavioral': 3, 'metadata': 3},
            'arms_share_candidates_and_fits': True, 'independent_validation': False}
    write_json(out/'protocol.lock.json', lock)
    clean = train(X, y, out/'clean.txt', cfg, a.seed, schema=schema.version)
    clean_p = clean.predict(dev['X'], num_threads=4)
    xm = dev['X'][dev['y'] == 1]
    eligible = clean_p[dev['y'] == 1] >= .5
    if eligible.sum() < rules['min_eligible']:
        raise ValueError('Insufficient development eligibility')
    benign = sel['X'][sel['y'] == 0]
    quota = lock['candidate_geometry']
    # Candidate values are observed benign values; no reference/calibration access.
    pools = {v: [int(j) for j in schema.views[v] if np.ptp(benign[:, j]) > 0] for v in quota}
    importance = np.abs(contributions(clean, benign[:500], schema=schema.version)).mean(axis=0)
    base = [j for v, k in quota.items() for j in sorted(pools[v], key=lambda j: (-importance[j], j))[:k]]
    def rare_value(j):
        values, counts = np.unique(benign[:, j], return_counts=True)
        order = np.lexsort((values, counts))[:min(4, len(values))]
        return float(values[rng.choice(order)])
    rows, seen = [], set()
    for n in range(a.candidates):
        for attempt in range(100):
            proposed = list(base)
            if n:
                position = int(rng.integers(len(proposed)))
                view = schema.view_labels[proposed[position]]
                choices = [j for j in pools[view] if j not in proposed]
                if choices:
                    proposed[position] = int(rng.choice(choices))
            indices = tuple(proposed)
            values = tuple(rare_value(j) for j in indices)
            digest = hashlib.sha256(json.dumps([indices, values]).encode()).hexdigest()
            if digest not in seen:
                seen.add(digest)
                break
        else:
            raise RuntimeError('Candidate domain exhausted')
        folder = out/f'candidate_{n:03d}_{digest[:12]}'
        folder.mkdir()
        trigger = VectorTrigger('cross_3view_stress', 'vector_stress', schema.version, schema.fingerprint, indices, values)
        xp, poison_ids, details = poison_primary(X, y, trigger, a.rate, a.seed, denominator='all_fit', schema=schema)
        write_json(folder/'trigger.json', {'indices': indices, 'values': values, 'sha256': digest,
                   'poison_source_ids': fit['ids'][ids[poison_ids]].tolist(), 'details': details})
        model = train(xp, y, folder/'main.txt', cfg, a.seed, schema=schema.version)
        xt = trigger.apply(xm, schema)
        pp = model.predict(dev['X'], num_threads=4)
        pt = model.predict(xt, num_threads=4)
        ct = clean.predict(xt, num_threads=4)
        screen = screen_primary(clean_p, pp, ct, pt, dev['y'], rules)
        vmc = []
        for start in range(0, len(xt), 128):
            batch = xt[start:start+128]
            phi = contributions(model, batch, schema=schema.version)
            scores, _, _ = primary_components(phi, pt[start:start+128], schema.version, methods={'M3_view_mass'})
            vmc.extend(scores['M3_view_mass'].tolist())
        vmc = np.asarray(vmc)
        np.savez_compressed(folder/'development_scores.npz', clean_original=clean_p,
                            clean_trigger=ct, poisoned_original=pp, poisoned_trigger=pt, vmc=vmc)
        row = {'candidate': n, 'trigger_sha256': digest, 'screen': screen,
               'mean_vmc_eligible': float(vmc[eligible].mean()), 'model_sha256': sha256(folder/'main.txt')}
        rows.append(row)
        write_json(out/'development_results.json', {'rows': rows, 'arms': {k: choose(rows, k) for k in ['asr_only', 'vmc_aware']},
                   'status': 'complete' if n+1 == a.candidates else 'running', 'not_final_evidence': True})
        print(json.dumps(row), flush=True)
        del xp, model, phi
        gc.collect()


if __name__ == '__main__':
    main()
