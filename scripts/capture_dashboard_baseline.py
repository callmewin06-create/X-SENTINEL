"""Capture unchanged demo predictions/timings before dashboard delivery work."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from xsentinel.service.registry import BundleRegistry
from xsentinel.service.scoring import score_input
from xsentinel.data.pe import extract_pe
from xsentinel.data.pe_v3 import extract_pe_v3


def semantic(result):
    return {k: v for k, v in result.items() if k != 'elapsed_ms'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--compare')
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists():
        raise FileExistsError('Existing baseline is preserved')
    out.mkdir(parents=True)
    fixture = Path('outputs/revision_2026_10_13/binary_validation/ReviewedBenignFixture.exe').read_bytes()
    registry = BundleRegistry()
    previous = json.loads(Path(args.compare).read_text(encoding='utf8')) if args.compare else None
    cases = []
    for dataset in ('EMBER2018', 'EMBER2024'):
        reader = extract_pe if dataset == 'EMBER2018' else extract_pe_v3
        extraction_start = time.perf_counter()
        vector, provenance = reader(fixture)
        extraction_ms = (time.perf_counter() - extraction_start) * 1000
        for variant in ('reduced', 'full'):
            entry = next(e for e in registry.entries.values() if e['dataset'] == dataset and e['variant'] == variant)
            load_start = time.perf_counter()
            detector, _ = registry.loaded(entry['id'])
            load_ms = (time.perf_counter() - load_start) * 1000
            method = 'X_primary_' + variant
            inputs = np.vstack([vector, detector.reference[:10]])
            score_input(detector, inputs[:1], method)
            rows = [score_input(detector, row, method) for row in inputs]
            timings = [r['elapsed_ms'] for r in rows]
            case = {'dataset': dataset, 'variant': variant, 'bundle_id': entry['id'],
                    'method': method, 'model_load_ms': load_ms, 'extraction_ms': extraction_ms,
                    'predict_mean_ms': float(np.mean(timings)), 'predict_p95_ms': float(np.quantile(timings, .95)),
                    'input_vector_sha256': hashlib.sha256(inputs.astype('<f4').tobytes()).hexdigest(),
                    'semantic_results': [semantic(r) for r in rows], 'provenance': provenance}
            if previous:
                old = next(c for c in previous['cases'] if c['dataset'] == dataset and c['variant'] == variant)
                assert case['input_vector_sha256'] == old['input_vector_sha256']
                assert case['bundle_id'] == old['bundle_id']
                assert case['semantic_results'] == old['semantic_results']
                case['matches_before_change'] = True
            cases.append(case)
    manifest_hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sorted(Path('outputs/primary').rglob('bundle.json'))}
    if previous:
        assert manifest_hashes == previous['bundle_manifest_hashes']
    result = {'cases': cases, 'bundle_manifest_hashes': manifest_hashes,
              'fixture_sha256': hashlib.sha256(fixture).hexdigest(),
              'scope': 'Predict timings include all detector scores/STRIP; exclude extraction/load/API/DB/browser. '
                       '11 inputs per case, one reviewed benign fixture + 10 reference rows; descriptive smoke timing, not final research latency.'}
    (out / 'baseline.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps([ {k: v for k, v in c.items() if k not in ('semantic_results', 'provenance')}
                      for c in cases], indent=2))


if __name__ == '__main__':
    main()
