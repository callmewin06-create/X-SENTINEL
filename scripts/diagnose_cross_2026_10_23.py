"""Audit existing Cross caches; no new method selection, training or thresholds."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from xsentinel.detection.detector import Detector
from xsentinel.detection.calibration import rank
from xsentinel.attacks.primary import VectorTrigger
from xsentinel.revision.scoring import core_scores


def main():
    base = ROOT / 'outputs/fusion_binary_latency_2026_10_20'
    pool = base / 'final_pool/EMBER2024'
    X, y = np.load(pool / 'X.npy'), np.load(pool / 'y.npy')
    checks, details, paired = [], [], []
    shared_ids = None
    for folder in sorted((base / 'final_results/EMBER2024').glob('seed_*/cross_3view_stress/rate_*')):
        meta = json.loads((folder / 'metrics.json').read_text())
        assert hashlib.sha256((folder / 'scores.npz').read_bytes()).hexdigest() == meta['cache_sha256']
        rows = meta['rows']
        assert all(r['confirmed'] for r in rows)
        cell = ROOT / 'outputs/primary/EMBER2024/protocol_v2' / folder.relative_to(base / 'final_results/EMBER2024')
        detector = Detector.load((cell / 'bundle_full').relative_to(ROOT))
        trigger = VectorTrigger(**json.loads((cell / 'attack.json').read_text())['trigger'])
        fresh, _ = core_scores(detector, trigger.apply(X[y == 1][:32], detector.schema))
        with np.load(folder / 'scores.npz', allow_pickle=False) as a:
            ids = a['malware_ids']
            if shared_ids is None:
                shared_ids = ids.copy()
            np.testing.assert_array_equal(shared_ids, ids)
            group = a['group_successful_eligible'].astype(bool)
            for variant, component in [('reduced', 'M4_shap_behavioral_conflict'), ('full', 'M4_prob_gap')]:
                for side in ('positive', 'negative'):
                    key = variant + '_' + side + '_'
                    np.testing.assert_allclose(a[key+'W50'], .5*a[key+'M3']+.5*a[key+'M4'], atol=1e-12, rtol=0)
                    np.testing.assert_allclose(a[key+'W25'], .25*a[key+'M3']+.75*a[key+'M4'], atol=1e-12, rtol=0)
                    np.testing.assert_array_equal(a[key+'M3'], rank(detector.rank_reference['M3_view_mass'], a[key+'M3_raw']))
                    np.testing.assert_array_equal(a[key+'M4'], rank(detector.rank_reference[component], a[key+'M4_raw']))
                np.testing.assert_allclose(a[variant+'_positive_M3_raw'][:32], fresh['M3_view_mass'], atol=1e-12, rtol=0)
                np.testing.assert_allclose(a[variant+'_positive_M4_raw'][:32], fresh[component], atol=1e-12, rtol=0)
                for row in [r for r in rows if r['variant'] == variant]:
                    p = a[variant+'_positive_'+row['rule']]
                    n = a[variant+'_negative_'+row['rule']]
                    assert int(((p > row['tau']) & group).sum()) == row['caught_n']
                    assert int((n > row['tau']).sum()) == row['false_positives']
                    assert int(group.sum()) == row['successful_n']
                    checks.append(row)
                details.append({'cell': rows[0]['cell'], 'variant': variant, 'successful_n': int(group.sum()),
                    **{f'{side}_{score}_median': float(np.median(a[variant+'_'+side+'_'+score][group if side=='positive' else slice(None)]))
                       for side in ('positive', 'negative') for score in ('M3_raw', 'M4_raw', 'M3', 'M4', 'W50')},
                    'successful_m4_zero_fraction': float(np.mean(a[variant+'_positive_M4_raw'][group] == 0))})
            tau = {r['rule']: r['tau'] for r in rows if r['variant']=='full'}
            paired.append((group, (a['full_positive_W25']>tau['W25']) & group,
                           (a['full_positive_W50']>tau['W50']) & group))
    rng = np.random.default_rng(23)
    masks = np.asarray([v[0] for v in paired], dtype=float)
    differences = np.asarray([v[1].astype(float)-v[2] for v in paired])
    weights = rng.multinomial(len(shared_ids), np.ones(len(shared_ids))/len(shared_ids), size=1000).T
    bootstrap = np.mean((differences @ weights) / (masks @ weights), axis=0)
    result = {'scope': 'Diagnostic reuse of previously observed Cross2024 source IDs; not new independent validation',
              'runs': len(paired), 'metric_rows_verified': len(checks), 'raw_score_rechecks_per_run': 32,
              'primary_formula_and_rank_checks_passed': True, 'details': details,
              'full_W25_minus_W50': {'mean_recall_difference': float(np.mean(differences.sum(1)/masks.sum(1))),
                  'source_paired_bootstrap_percentile95': np.quantile(bootstrap,[.025,.975]).tolist(),
                  'replicates':1000, 'scope':'Resample shared source IDs together across 9 fixed models; not model/seed uncertainty'},
              'decision':'Keep W50 primary. No implementation discrepancy found in audited caches/replayed subset. Existing signals and fusion remain weak on Cross; no new candidate justified or promoted in this repair.'}
    out = ROOT / 'outputs/repair_2026_10_23/cross_diagnosis.json'
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='details'},indent=2))


if __name__ == '__main__':
    main()
