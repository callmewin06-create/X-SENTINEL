"""Frozen-score comparison, measured overhead and a real Vietnamese PDF sample."""
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from xsentinel.service.registry import BundleRegistry
from xsentinel.service.scoring import score_input
from xsentinel.demo_provenance import demo_ground_truth
from xsentinel.result_pdf import result_pdf


def main():
    out = Path('outputs/ui_revision_2026_10_16'); out.mkdir(parents=True, exist_ok=True)
    previous = subprocess.run(['git', 'show', 'HEAD:src/xsentinel/service/scoring.py'], check=True, capture_output=True, encoding='utf-8').stdout
    old = {}; exec(compile(previous, '<previous scoring>', 'exec'), old)
    registry = BundleRegistry()
    cases = []
    for dataset in ('EMBER2018', 'EMBER2024'):
        for variant in ('reduced', 'full'):
            entry = next(e for e in registry.entries.values() if e['dataset'] == dataset and e['variant'] == variant)
            detector, _ = registry.loaded(entry['id'])
            x = detector.reference[:1]
            legacy = old['score_input'](detector, x, 'X_primary_' + variant)
            result = score_input(detector, x, 'X_primary_' + variant)
            for key in legacy:
                if key != 'elapsed_ms':
                    assert legacy[key] == result[key], (dataset, variant, key)
            before, after = [], []
            for _ in range(15):
                start = time.perf_counter(); old['score_input'](detector, x, 'X_primary_' + variant)
                before.append((time.perf_counter() - start) * 1000)
                start = time.perf_counter(); score_input(detector, x, 'X_primary_' + variant)
                after.append((time.perf_counter() - start) * 1000)
            result.update(ground_truth=demo_ground_truth(entry['state'], x, True), demo_mode=True,
                          input_metadata={'name': 'Mẫu tham chiếu demo'},
                          experiment={'variant': variant}, bundle_id=entry['id'])
            cases.append({'dataset': dataset, 'variant': variant, 'unchanged_existing_fields': True,
                          'mean_scoring_before_ms': statistics.mean(before), 'mean_scoring_after_ms': statistics.mean(after),
                          'n_each': len(before), 'ground_truth_verified': result['ground_truth'] is not None})
            if dataset == 'EMBER2024' and variant == 'reduced':
                pdf_path = Path('output/pdf/X_SENTINEL_UI_Demo_2026_10_16.pdf')
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                start = time.perf_counter(); pdf_path.write_bytes(result_pdf(result)); pdf_ms = (time.perf_counter() - start) * 1000
                (out / 'sample_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    frozen = json.loads((out / 'primary_before.json').read_text(encoding='utf-8'))
    for path, digest in frozen.items():
        with Path(path).open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == digest, path
    proof = {'cases': cases, 'primary_files_unchanged': len(frozen), 'pdf_creation_ms': pdf_ms,
             'timing_scope': 'Same physical host, same reference row, interleaved warm scoring; excludes upload/browser/DB. Not a new research benchmark.'}
    (out / 'verification.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print(json.dumps(proof, indent=2))


if __name__ == '__main__':
    main()
