"""One-shot historical confirmation audit for a completed pilot, never final data.

Rebuilds component reference ranks and thresholds for each selected model.
This is not fresh-data validation and cannot certify population FPR.
"""
import argparse
from pathlib import Path
import sys
import numpy as np
import lightgbm as lgb
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from xsentinel.primary_workflow import open_roles
from xsentinel.attacks.primary import VectorTrigger
from xsentinel.attacks.screen import screen_primary
from xsentinel.baselines.scores import contributions
from xsentinel.detection.components import primary_components
from xsentinel.detection.calibration import rank, threshold
from xsentinel.evaluation.metrics import rate
from xsentinel.utils import read_json, write_json, sha256


def raw(model, X, schema):
    probability, vmc, bgs = [], [], []
    for offset in range(0, len(X), 128):
        batch = X[offset:offset+128]
        p = np.asarray(model.predict(batch, num_threads=4))
        phi = contributions(model, batch, schema=schema.version)
        scores, _, _ = primary_components(phi, p, schema.version,
                    methods={'M3_view_mass', 'M4_shap_behavioral_conflict'})
        probability.extend(p); vmc.extend(scores['M3_view_mass']); bgs.extend(scores['M4_shap_behavioral_conflict'])
    return np.asarray(probability), {'VMC': np.asarray(vmc), 'BGS': np.asarray(bgs)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--search', required=True); p.add_argument('--output', required=True)
    p.add_argument('--acknowledge-historical-pools', action='store_true')
    a = p.parse_args()
    if not a.acknowledge_historical_pools:
        p.error('This pilot explicitly reuses historical pools; acknowledge scope')
    search = Path(a.search); results = read_json(search/'development_results.json')
    if results['status'] != 'complete': raise ValueError('Search must finish before confirmation')
    lock = read_json(search/'protocol.lock.json')
    state, schema, roles = open_roles(lock['args']['roles'], ['reference', 'calibration', 'confirmation'])
    if sha256(Path(lock['args']['roles'])/'roles.json') != lock['roles_sha256']:
        raise ValueError('Role manifest changed')
    attacker_ids = set(lock['fit_ids']+lock['selection_ids']+lock['development_ids'])
    for name, role in roles.items():
        if attacker_ids.intersection(role['ids'].astype(str)):
            raise ValueError('Attacker/evaluation source overlap: '+name)
    out = Path(a.output)
    if out.exists(): raise FileExistsError('One-shot confirmation: use a fresh output directory')
    out.mkdir(parents=True)
    clean = lgb.Booster(model_file=str(search/'clean.txt'))
    X, y = roles['confirmation']['X'], roles['confirmation']['y']
    xm = X[y == 1]; clean_original = clean.predict(X, num_threads=4)
    eligible = clean_original[y == 1] >= .5
    evaluated = {}; arms = {}
    for arm, chosen in results['arms'].items():
        number = chosen['selected']
        if number is None:
            arms[arm] = {'status': 'no_valid_development_attack'}; continue
        arms[arm] = {'candidate': number}
        if str(number) in evaluated: continue
        record = next(r for r in results['rows'] if r['candidate'] == number)
        folders = list(search.glob(f'candidate_{number:03d}_*'))
        if len(folders) != 1: raise ValueError('Ambiguous candidate directory')
        folder = folders[0]; t = read_json(folder/'trigger.json')
        if sha256(folder/'main.txt') != record['model_sha256']: raise ValueError('Model changed')
        trigger = VectorTrigger('cross_3view_stress', 'vector_stress', schema.version,
                    schema.fingerprint, tuple(t['indices']), tuple(t['values']))
        model = lgb.Booster(model_file=str(folder/'main.txt'))
        _, reference = raw(model, roles['reference']['X'], schema)
        _, calibration = raw(model, roles['calibration']['X'], schema)
        def fused(component):
            ranks = {k: rank(reference[k], v) for k, v in component.items()}
            return {'VMC': component['VMC'], 'Reduced': (ranks['VMC']+ranks['BGS'])/2}
        thresholds = {k: threshold(v, .01) for k, v in fused(calibration).items()}
        xt = trigger.apply(xm, schema)
        original_p = model.predict(X, num_threads=4)
        pt, trigger_raw = raw(model, xt, schema)
        _, benign_raw = raw(model, X[y == 0], schema)
        ct = clean.predict(xt, num_threads=4)
        success = eligible & (pt < .5)
        paired = success & (ct >= .5)
        metrics = {}
        positive, negative = fused(trigger_raw), fused(benign_raw)
        for method in thresholds:
            alerts = positive[method] > thresholds[method]
            metrics[method] = {'threshold': thresholds[method],
                 'successful_eligible_recall': rate(alerts[success]),
                 'paired_new_recall': rate(alerts[paired]),
                 'post_defense_asr': rate(((pt < .5) & ~alerts)[eligible]),
                 'benign_fpr': rate(negative[method] > thresholds[method])}
        np.savez_compressed(out/f'candidate_{number}_scores.npz', ids=roles['confirmation']['ids'],
             y=y, clean_original=clean_original, poison_original=original_p,
             clean_trigger=ct, poison_trigger=pt, eligible=eligible, success=success,
             paired_new=paired, **{'trigger_'+k:v for k,v in positive.items()},
             **{'benign_'+k:v for k,v in negative.items()})
        evaluated[str(number)] = {'model_sha256': record['model_sha256'], 'metrics': metrics,
            'confirmation_screen': screen_primary(clean_original, original_p, ct, pt, y, lock['screen'])}
        write_json(out/'results.json', {'scope': 'historical confirmation pilot; not independent final validation',
            'status': 'running', 'arms': arms, 'evaluated': evaluated, 'final_opened': False,
            'search_lock_sha256': sha256(search/'protocol.lock.json')})
    write_json(out/'results.json', {'scope': 'historical confirmation pilot; not independent final validation',
        'status': 'complete', 'arms': arms, 'evaluated': evaluated, 'final_opened': False,
        'search_lock_sha256': sha256(search/'protocol.lock.json')})


if __name__ == '__main__': main()
