import gc
import json
import os
import sys
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from xsentinel.data.pe import extract_pe
from xsentinel.detection.detector import Detector
from xsentinel.revision.reviewer_core import CoreScorer
from xsentinel.baselines.scores import contributions

def main():
    fixture_path = ROOT / 'ReviewedBenignFixture.exe'
    pe_bytes = fixture_path.read_bytes()
    bundle_path = ROOT / 'outputs/primary/EMBER2018/protocol_v2/seed_17/spread_structural/rate_0.02/bundle_full'
    detector = Detector.load(bundle_path)
    scorer = CoreScorer(detector.model, detector.schema, detector.views['behavioral']).fit_reference(detector.reference)

    # Warmup
    vec, _ = extract_pe(pe_bytes)
    x = vec.reshape(1, -1)
    _ = contributions(detector.model, x, schema=detector.schema)
    _ = scorer.score(x)
    gc.collect()

    N = 100

    # 1. Baseline: score(x) without precomputed components (recalculates TreeSHAP and predictions inside scorer)
    lat_unopt_stage3 = []
    lat_unopt_total = []
    for _ in range(N):
        t0 = time.perf_counter()
        # Stage 2: Feature attribution
        phi = contributions(detector.model, x, schema=detector.schema)
        p = detector.model.predict(x, num_threads=4)
        pb = scorer.behavioral.predict(x[:, detector.schema.views['behavioral']], num_threads=4)
        t_stage2 = time.perf_counter()

        # Stage 3 unoptimized: recalculates TreeSHAP inside scorer
        t3_0 = time.perf_counter()
        _ = scorer.score(x)
        t3_1 = time.perf_counter()
        lat_unopt_stage3.append((t3_1 - t3_0) * 1000)
        lat_unopt_total.append((t3_1 - t0) * 1000)

    # 2. Optimized: score(x, phi=phi, p=p, pb=pb) with precomputed passthrough (BUG-05 fix)
    lat_opt_stage3 = []
    lat_opt_total = []
    for _ in range(N):
        t0 = time.perf_counter()
        # Stage 2: Feature attribution
        phi = contributions(detector.model, x, schema=detector.schema)
        p = detector.model.predict(x, num_threads=4)
        pb = scorer.behavioral.predict(x[:, detector.schema.views['behavioral']], num_threads=4)
        t_stage2 = time.perf_counter()

        # Stage 3 optimized: reuses phi, p, pb
        t3_0 = time.perf_counter()
        _ = scorer.score(x, phi=phi, p=p, pb=pb)
        t3_1 = time.perf_counter()
        lat_opt_stage3.append((t3_1 - t3_0) * 1000)
        lat_opt_total.append((t3_1 - t0) * 1000)

    res = {
        'unoptimized': {
            'stage3_mean_ms': round(float(np.mean(lat_unopt_stage3)), 2),
            'stage3_p95_ms': round(float(np.percentile(lat_unopt_stage3, 95)), 2),
            'stage2_plus_3_mean_ms': round(float(np.mean(lat_unopt_total)), 2),
            'stage2_plus_3_p95_ms': round(float(np.percentile(lat_unopt_total, 95)), 2)
        },
        'optimized': {
            'stage3_mean_ms': round(float(np.mean(lat_opt_stage3)), 2),
            'stage3_p95_ms': round(float(np.percentile(lat_opt_stage3, 95)), 2),
            'stage2_plus_3_mean_ms': round(float(np.mean(lat_opt_total)), 2),
            'stage2_plus_3_p95_ms': round(float(np.percentile(lat_opt_total, 95)), 2)
        },
        'improvement': {
            'stage3_speedup_ratio': round(float(np.mean(lat_unopt_stage3) / np.mean(lat_opt_stage3)), 2),
            'stage3_saved_ms': round(float(np.mean(lat_unopt_stage3) - np.mean(lat_opt_stage3)), 2),
            'total_latency_reduction_pct': round(float((np.mean(lat_unopt_total) - np.mean(lat_opt_total)) / np.mean(lat_unopt_total) * 100), 2)
        }
    }
    print(json.dumps(res, indent=2))
    with open(ROOT / 'outputs/optimization_benchmark.json', 'w') as f:
        json.dump(res, f, indent=2)

if __name__ == '__main__':
    main()
