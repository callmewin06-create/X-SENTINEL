"""Frozen-model SHAP-IF evaluation, resumable by cell, no original mutations."""
import argparse
import gc
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import joblib
import numpy as np
import lightgbm as lgb
import sklearn
from xsentinel.utils import read_json, write_json, sha256
from xsentinel.primary_workflow import open_roles
from xsentinel.baselines.scores import contributions
from xsentinel.baselines.shap_outlier import PARAMETERS, fit_shap_outlier, outlier_scores
from xsentinel.detection.calibration import threshold
from xsentinel.revision.analysis import attack_groups, revised_metrics
from xsentinel.revision.low_fpr import low_fpr_metrics
from xsentinel.attacks.primary import VectorTrigger


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pilot', action='store_true')
    ap.add_argument('--dataset', choices=['EMBER2018', 'EMBER2024'])
    ap.add_argument('--confirmed-only', action='store_true')
    ap.add_argument('--batch', type=int, default=256)
    ap.add_argument('--out', default='outputs/teacher_revision_2026_10_27/shap_if')
    args = ap.parse_args()
    if args.batch < 1:
        raise ValueError('Positive batch size required')
    out = Path(args.out)
    if out.resolve().is_relative_to(Path('outputs/primary').resolve()):
        raise ValueError('Protected original output')
    out.mkdir(parents=True, exist_ok=True)
    code = [Path(__file__), Path('src/xsentinel/baselines/shap_outlier.py'),
            Path('src/xsentinel/revision/low_fpr.py'), Path('src/xsentinel/baselines/scores.py')]
    lock = dict(version='shap-if-v1', parameters=PARAMETERS, batch=args.batch,
                sklearn=sklearn.__version__, lightgbm=lgb.__version__,
                code_hashes={str(p): sha256(p) for p in code},
                reference_n=500, calibration_n=2000, score='-score_samples(signed native SHAP excluding bias)',
                threshold='benign calibration order statistic; strict score>tau; target=.01',
                scope='Post-review evaluation on previously observed frozen final pool; not new independent validation',
                target='54 original configurations; runtime-only fallback: 24 previously confirmed cells',
                pilot='seed17/spread_structural/rate0.02 on each dataset; no result-based tuning',
                original_malware='Matched-ID control; alert rate is not benign FPR')
    lp = out / 'protocol.json'
    if lp.exists() and read_json(lp) != lock:
        raise ValueError('Protocol/code changed: use another output namespace')
    write_json(lp, lock)
    for dataset in ([args.dataset] if args.dataset else ['EMBER2018', 'EMBER2024']):
        print('Verifying roles', dataset, flush=True)
        state, schema, roles = open_roles(Path('data/primary') / dataset / 'protocol_v2',
                                          ('reference', 'calibration', 'final'))
        for a, b in [('reference', 'calibration'), ('reference', 'final'), ('calibration', 'final')]:
            if set(roles[a]['ids']) & set(roles[b]['ids']):
                raise ValueError('Role overlap')
        final = roles['final']; benign = final['y'] == 0
        xb, xm = final['X'][benign], final['X'][~benign]
        for cell in sorted((Path('outputs/primary') / dataset / 'protocol_v2').glob('seed_*/*/rate_*')):
            r = read_json(cell / 'result.json')
            if args.pilot and (r['seed'] != 17 or r['family'] != 'spread_structural' or r['rate'] != .02):
                continue
            if args.confirmed_only and not r['independently_confirmed_strong_and_stealth']:
                continue
            dest = out / dataset / cell.relative_to(Path('outputs/primary') / dataset / 'protocol_v2')
            dest.mkdir(parents=True, exist_ok=True)
            sources = {str(cell / name): sha256(cell / name) for name in
                       ('result.json', 'paired_predictions.npz', 'attack.json', 'bundle_reduced/main.txt')}
            for name, digest in r['artifact_sha256'].items():
                if sha256(cell / name) != digest:
                    raise ValueError('Original artifact mismatch: ' + name)
            rp = dest / 'result.json'
            if rp.exists():
                old = read_json(rp)
                if old['source_hashes'] != sources or any(sha256(dest / k) != v for k,v in old['output_hashes'].items()):
                    raise ValueError('Resume artifact mismatch')
                print('Resumed', dest, flush=True)
                continue
            started = time.perf_counter()
            print('Starting', dest, flush=True)
            model = lgb.Booster(model_file=str(cell / 'bundle_reduced/main.txt'))
            with np.load(cell / 'paired_predictions.npz', allow_pickle=False) as z:
                a = {k: v.copy() for k,v in z.items()}
            if not (np.array_equal(a['benign_ids'].astype(str), final['ids'][benign].astype(str)) and
                    np.array_equal(a['malware_ids'].astype(str), final['ids'][~benign].astype(str))):
                raise ValueError('Final ID ordering mismatch')
            forest = fit_shap_outlier(contributions(model, roles['reference']['X'], schema=schema))
            joblib.dump(forest, dest / 'if.joblib')
            spec = read_json(cell / 'attack.json')['trigger']
            xt = VectorTrigger(**spec).apply(xm, schema)
            scores = {}
            timings = {}
            for name, x in [('calibration', roles['calibration']['X']), ('benign', xb),
                            ('original_malware', xm), ('triggered', xt)]:
                t = time.perf_counter()
                scores[name] = np.concatenate([outlier_scores(forest, contributions(model, x[i:i+args.batch], schema=schema))
                                               for i in range(0, len(x), args.batch)])
                timings[name] = time.perf_counter() - t
                print(name, len(x), round(timings[name], 2), 'seconds', flush=True)
            tau = threshold(scores['calibration'], .01)
            groups = attack_groups(a['clean_malware_p'], a['triggered_main_p'], a['clean_trigger_p'])
            np.savez_compressed(dest / 'scores.npz', **scores, benign_ids=a['benign_ids'], malware_ids=a['malware_ids'])
            result = dict(dataset=dataset, seed=r['seed'], family=r['family'], rate=r['rate'],
                          confirmed=r['independently_confirmed_strong_and_stealth'], source_hashes=sources,
                          roles_sha256=sha256(Path('data/primary') / dataset / 'protocol_v2/roles.json'),
                          calibration_fp=int(np.sum(scores['calibration'] > tau)), calibration_n=2000,
                          metrics=revised_metrics(scores['triggered'], scores['benign'], tau, groups),
                          low_fpr={g: low_fpr_metrics(scores['triggered'][m], scores['benign']) for g,m in groups.items()},
                          original_malware_alerts=int(np.sum(scores['original_malware'] > tau)),
                          original_malware_n=len(xm),
                          triggered_minus_original_mean=float(np.mean(scores['triggered'] - scores['original_malware'])),
                          timings_seconds=timings, elapsed_seconds=time.perf_counter() - started,
                          output_hashes={n: sha256(dest/n) for n in ('if.joblib', 'scores.npz')})
            if result['calibration_fp'] > 20 or any(sha256(p) != h for p,h in sources.items()):
                raise ValueError('Calibration or immutability invariant failed')
            write_json(rp, result)
            print('Completed', dataset, r['seed'], r['family'], r['rate'], result['elapsed_seconds'], flush=True)
            del model, forest, a, scores, xt
            gc.collect()
        del roles, xb, xm
        gc.collect()


if __name__ == '__main__':
    main()
