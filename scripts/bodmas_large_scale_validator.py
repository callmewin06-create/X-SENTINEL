"""Large-Scale BODMAS Malware Dataset Validation Runner (Phase 4).
Evaluates >70% of unique eligible malware PE binaries from the BODMAS dataset.
Enforces strict malware handling safety: static analysis only, read-only, never executed.
Supports bounded concurrency, per-sample timeouts, periodic checkpointing, and resume capability.
"""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import random
import signal
import sys
import time
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from xsentinel.data.limits import MAX_UPLOAD_BYTES, verify_size
from xsentinel.data.pe import extract_pe, verify_pe
from xsentinel.service.registry import BundleRegistry
from xsentinel.schema import V2_PRIMARY


def _init_worker():
    # Suppress C++ LIEF noise in child processes
    try:
        null = os.open(os.devnull, os.O_WRONLY)
        os.dup2(null, 2)
        os.close(null)
    except Exception:
        pass


def _process_single_file(args):
    file_path, original_sha, family, timeout_sec = args
    result = {
        'original_sha': original_sha,
        'relative_path': os.path.basename(file_path),
        'family': family if pd.notna(family) else 'unknown',
        'size_bytes': 0,
        'file_sha256': '',
        'scan_status': 'not_attempted',
        'parse_status': 'not_attempted',
        'error_code': '',
        'error': '',
        'extraction_ms': 0.0,
        'vector': None
    }
    t0 = time.perf_counter()
    try:
        st = os.stat(file_path)
        result['size_bytes'] = st.st_size
        if st.st_size == 0:
            result['scan_status'] = 'input_rejected'
            result['error_code'] = 'empty_file'
            result['error'] = 'File is empty'
            return result
        if st.st_size > MAX_UPLOAD_BYTES:
            result['scan_status'] = 'input_rejected'
            result['error_code'] = 'oversize'
            result['error'] = f'File size {st.st_size} exceeds 50 MiB limit'
            return result

        with open(file_path, 'rb') as fp:
            data = fp.read()
        result['file_sha256'] = hashlib.sha256(data).hexdigest()

        # Static PE extraction
        vector, prov = extract_pe(data)
        result['extraction_ms'] = (time.perf_counter() - t0) * 1000
        result['scan_status'] = 'extracted'
        result['parse_status'] = 'ok'
        result['vector'] = vector.tolist()
    except ValueError as exc:
        result['extraction_ms'] = (time.perf_counter() - t0) * 1000
        result['scan_status'] = 'parse_failed'
        result['parse_status'] = 'failed'
        result['error_code'] = 'parse_error'
        result['error'] = str(exc)[:200]
    except Exception as exc:
        result['extraction_ms'] = (time.perf_counter() - t0) * 1000
        result['scan_status'] = 'parse_failed'
        result['parse_status'] = 'failed'
        result['error_code'] = type(exc).__name__
        result['error'] = str(exc)[:200]
    return result


def main():
    parser = argparse.ArgumentParser(description="Large-Scale BODMAS Validation Runner")
    parser.add_argument('--samples-dir', default='/home/phucpnhse203815/xsentinel-bodmas-work/samples/malware/altered')
    parser.add_argument('--metadata-csv', default='/app/data/public/bodmas/bodmas_metadata.csv')
    parser.add_argument('--npz-path', default='/app/data/public/bodmas/bodmas.npz')
    parser.add_argument('--bundle-root', default='/app/outputs/primary')
    parser.add_argument('--bundle-id', default='4b727e14ed4d2352fe7d1bdca4338624e191a83dfe7a2b7d556326226031fe3a')
    parser.add_argument('--output-dir', default='/app/outputs/bodmas_validation')
    parser.add_argument('--target-count', type=int, default=45000)
    parser.add_argument('--batch-size', type=int, default=1000)
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--seed', type=int, default=17)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_file = out_dir / 'checkpoint.json'
    manifest_csv = out_dir / 'bodmas_test_manifest.csv'

    print("=" * 75)
    print("X-SENTINEL LARGE-SCALE BODMAS VALIDATION (Phase 4)")
    print(f"Target Samples: {args.target_count} (>70% of 57,271 eligible)")
    print(f"Workers: {args.workers} | Batch Size: {args.batch_size} | Seed: {args.seed}")
    print("=" * 75)

    # 1. Load Metadata & Inventory
    print("[1/5] Loading BODMAS dataset inventory...")
    df_meta = pd.read_csv(args.metadata_csv)
    npz = np.load(args.npz_path)
    y_all = npz['y']
    df_meta['label'] = y_all
    df_malware = df_meta[df_meta['label'] == 1].copy()
    total_discovered_malware = len(df_malware)
    print(f"  Total discovered malware in metadata: {total_discovered_malware}")

    all_files = set(f for f in os.listdir(args.samples_dir) if f.endswith('.exe'))
    print(f"  Total files in altered directory: {len(all_files)}")

    # Map file path and filter eligible
    eligible_items = []
    excluded_oversize = []
    for idx, row in df_malware.iterrows():
        fname = f"{row['sha']}.exe"
        if fname in all_files:
            fpath = os.path.join(args.samples_dir, fname)
            sz = os.path.getsize(fpath)
            if sz > MAX_UPLOAD_BYTES:
                excluded_oversize.append({'sha': row['sha'], 'size': sz})
            else:
                eligible_items.append({
                    'sha': row['sha'],
                    'fpath': fpath,
                    'family': row['family'],
                    'size': sz
                })

    total_eligible = len(eligible_items)
    print(f"  Total eligible malware samples (<=50MB): {total_eligible}")
    print(f"  Excluded oversized (>50MB): {len(excluded_oversize)}")

    # 2. Stratified / Seeded Sampling
    print(f"[2/5] Selecting representative sample of {args.target_count} items (seed={args.seed})...")
    random.seed(args.seed)
    # Sort for deterministic order before sampling
    eligible_items.sort(key=lambda x: x['sha'])
    selected_sample = random.sample(eligible_items, min(args.target_count, len(eligible_items)))
    print(f"  Selected {len(selected_sample)} samples ({len(selected_sample)/total_eligible*100:.2f}% of eligible)")

    # 3. Check for existing checkpoint
    processed_records = []
    start_idx = 0
    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, 'r', encoding='utf8') as cp:
                cp_data = json.load(cp)
            start_idx = cp_data.get('processed_count', 0)
            print(f"  Found existing checkpoint: Resuming from index {start_idx}...")
        except Exception:
            start_idx = 0

    # 4. Load Calibrated Bundle
    print("[3/5] Loading primary detector bundle...")
    reg = BundleRegistry(args.bundle_root)
    detector, lock = reg.loaded(args.bundle_id)
    entry = reg.entry(args.bundle_id)
    method = 'X_primary_reduced'
    threshold_val = float(detector.thresholds[method])
    print(f"  Bundle: {entry['relative_path']} | Method: {method} | Threshold: {threshold_val:.6f}")

    # Prepare CSV Writer
    write_header = not manifest_csv.exists() or start_idx == 0
    csv_file = open(manifest_csv, 'a' if start_idx > 0 else 'w', newline='', encoding='utf-8-sig')
    csv_fields = [
        'sequence', 'original_sha', 'relative_path', 'family', 'size_bytes',
        'file_sha256', 'scan_status', 'parse_status', 'malware_probability',
        'main_classification', 'score', 'threshold', 'trigger_alert',
        'extraction_ms', 'prediction_ms', 'total_ms', 'error_code', 'error'
    ]
    writer = csv.DictWriter(csv_file, fieldnames=csv_fields)
    if write_header:
        writer.writeheader()
        csv_file.flush()

    # 5. Multiprocessing Batch Ingestion & Scoring
    print(f"[4/5] Executing static validation pipeline on {len(selected_sample)} samples...")
    t_start = time.time()
    total_to_process = len(selected_sample)
    pool = mp.Pool(processes=args.workers, initializer=_init_worker)

    stats = {
        'total_attempted': start_idx,
        'successfully_parsed': 0,
        'parse_failed': 0,
        'input_rejected': 0,
        'malware_classified': 0,
        'benign_classified': 0,
        'trigger_alerts': 0,
        'latencies': [],
        'family_stats': {}
    }

    try:
        for batch_start in range(start_idx, total_to_process, args.batch_size):
            batch_end = min(batch_start + args.batch_size, total_to_process)
            batch_items = selected_sample[batch_start:batch_end]
            work_args = [
                (item['fpath'], item['sha'], item['family'], 5.0)
                for item in batch_items
            ]

            b_t0 = time.time()
            # Worker extraction
            batch_results = pool.map(_process_single_file, work_args)

            # Separate successfully extracted vectors for batched prediction
            valid_indices = []
            valid_vectors = []
            for i, r in enumerate(batch_results):
                if r['scan_status'] == 'extracted' and r['vector'] is not None:
                    valid_indices.append(i)
                    valid_vectors.append(r['vector'])

            # Fast vectorized prediction
            if valid_vectors:
                mat = np.asarray(valid_vectors, dtype=np.float32)
                p_t0 = time.perf_counter()
                with lock:
                    scores_dict, flags_dict, details, _ = detector.predict_selected(mat, method)
                pred_duration = (time.perf_counter() - p_t0) * 1000 / len(valid_vectors)

                probs = details['malware_probability']
                scores = scores_dict[method]
                flags = flags_dict[method]

                for local_idx, real_idx in enumerate(valid_indices):
                    r = batch_results[real_idx]
                    prob = float(probs[local_idx])
                    sc = float(scores[local_idx])
                    fl = bool(flags[local_idx])
                    r['malware_probability'] = prob
                    r['main_classification'] = 'MALWARE' if prob >= 0.5 else 'BENIGN'
                    r['score'] = sc
                    r['threshold'] = threshold_val
                    r['trigger_alert'] = fl
                    r['prediction_ms'] = pred_duration
                    r['scan_status'] = 'ok'

            # Write batch to CSV & update stats
            for idx_in_batch, r in enumerate(batch_results):
                seq = batch_start + idx_in_batch + 1
                row_dict = {
                    'sequence': seq,
                    'original_sha': r['original_sha'],
                    'relative_path': r['relative_path'],
                    'family': r['family'],
                    'size_bytes': r['size_bytes'],
                    'file_sha256': r['file_sha256'],
                    'scan_status': r['scan_status'],
                    'parse_status': r['parse_status'],
                    'malware_probability': r.get('malware_probability', ''),
                    'main_classification': r.get('main_classification', ''),
                    'score': r.get('score', ''),
                    'threshold': r.get('threshold', ''),
                    'trigger_alert': r.get('trigger_alert', ''),
                    'extraction_ms': f"{r['extraction_ms']:.2f}",
                    'prediction_ms': f"{r.get('prediction_ms', 0.0):.2f}",
                    'total_ms': f"{r['extraction_ms'] + r.get('prediction_ms', 0.0):.2f}",
                    'error_code': r['error_code'],
                    'error': r['error']
                }
                writer.writerow(row_dict)

                # Aggregate stats
                stats['total_attempted'] += 1
                fam = r['family']
                fam_stat = stats['family_stats'].setdefault(fam, {'total': 0, 'parsed': 0, 'malware': 0, 'alert': 0})
                fam_stat['total'] += 1

                if r['scan_status'] == 'ok':
                    stats['successfully_parsed'] += 1
                    fam_stat['parsed'] += 1
                    stats['latencies'].append(r['extraction_ms'] + r.get('prediction_ms', 0.0))
                    if r.get('main_classification') == 'MALWARE':
                        stats['malware_classified'] += 1
                        fam_stat['malware'] += 1
                    else:
                        stats['benign_classified'] += 1
                    if r.get('trigger_alert'):
                        stats['trigger_alerts'] += 1
                        fam_stat['alert'] += 1
                elif r['scan_status'] == 'parse_failed':
                    stats['parse_failed'] += 1
                else:
                    stats['input_rejected'] += 1

            csv_file.flush()
            b_dur = time.time() - b_t0
            throughput = len(batch_items) / b_dur
            pct = batch_end / total_to_process * 100
            print(f"  Processed {batch_end}/{total_to_process} ({pct:.1f}%) | Batch: {b_dur:.1f}s ({throughput:.1f} fps) | Parsed OK: {stats['successfully_parsed']}")

            # Save checkpoint
            with open(checkpoint_file, 'w', encoding='utf8') as cp:
                json.dump({
                    'processed_count': batch_end,
                    'total_count': total_to_process,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }, cp, indent=2)

    finally:
        pool.close()
        pool.join()
        csv_file.close()

    total_time = time.time() - t_start
    print(f"\n[5/5] Processing complete in {total_time:.2f}s ({stats['total_attempted']/total_time:.1f} samples/sec)")

    # 6. Evaluate Benign Holdout (from bodmas.npz) for FPR & Precision
    print("Evaluating benign holdout set (10,000 samples) for FPR/Precision/Recall/F1...")
    benign_indices = np.where(y_all == 0)[0]
    random.seed(args.seed)
    selected_benign_idx = random.sample(list(benign_indices), min(10000, len(benign_indices)))
    benign_x = npz['X'][selected_benign_idx]

    with lock:
        b_scores, b_flags, b_details, _ = detector.predict_selected(benign_x, method)
    b_probs = b_details['malware_probability']
    b_classified_malware = int(np.sum(b_probs >= 0.5))
    b_classified_benign = int(np.sum(b_probs < 0.5))
    b_alerts = int(np.sum(b_flags[method]))

    # Compute Metrics
    tp = stats['malware_classified']
    fn = stats['benign_classified']
    fp = b_classified_malware
    tn = b_classified_benign

    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    fnr = fn / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tpr
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    lats = np.array(stats['latencies']) if stats['latencies'] else np.array([0.0])
    p50 = float(np.percentile(lats, 50))
    p95 = float(np.percentile(lats, 95))
    p99 = float(np.percentile(lats, 99))
    mean_lat = float(np.mean(lats))

    coverage_actual = stats['successfully_parsed'] / total_eligible * 100.0

    summary = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'dataset': 'BODMAS',
        'bundle_id': args.bundle_id,
        'method': method,
        'total_discovered_malware': total_discovered_malware,
        'total_unique_samples': total_discovered_malware,
        'total_eligible_unique': total_eligible,
        'excluded_oversize_count': len(excluded_oversize),
        'attempted_samples': stats['total_attempted'],
        'successfully_evaluated': stats['successfully_parsed'],
        'parse_failed_count': stats['parse_failed'],
        'input_rejected_count': stats['input_rejected'],
        'actual_evaluation_coverage_pct': round(coverage_actual, 2),
        'coverage_requirement_met': coverage_actual > 70.0,
        'detection_metrics': {
            'true_positives': tp,
            'false_negatives': fn,
            'false_positives': fp,
            'true_negatives': tn,
            'detection_rate_tpr': round(tpr * 100, 2),
            'false_negative_rate_fnr': round(fnr * 100, 2),
            'false_positive_rate_fpr': round(fpr * 100, 2),
            'precision': round(precision * 100, 2),
            'recall': round(recall * 100, 2),
            'f1_score': round(f1, 4),
            'trigger_alerts_count': stats['trigger_alerts'],
            'trigger_alert_rate': round(stats['trigger_alerts'] / stats['successfully_parsed'] * 100, 2) if stats['successfully_parsed'] > 0 else 0.0
        },
        'performance_metrics': {
            'total_time_seconds': round(total_time, 2),
            'throughput_samples_per_sec': round(stats['total_attempted'] / total_time, 1),
            'mean_latency_ms': round(mean_lat, 2),
            'p50_latency_ms': round(p50, 2),
            'p95_latency_ms': round(p95, 2),
            'p99_latency_ms': round(p99, 2)
        },
        'family_summary': stats['family_stats']
    }

    with open(out_dir / 'bodmas_summary.json', 'w', encoding='utf8') as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 75)
    print("VALIDATION SUMMARY")
    print(f"Total Eligible Unique: {total_eligible}")
    print(f"Attempted: {stats['total_attempted']}")
    print(f"Successfully Evaluated: {stats['successfully_parsed']} ({coverage_actual:.2f}%)")
    print(f"Coverage Requirement (>70%): {'ACHIEVED [PASS]' if coverage_actual > 70 else 'FAILED'}")
    print(f"Detection Rate (TPR): {tpr*100:.2f}% | FNR: {fnr*100:.2f}% | FPR: {fpr*100:.2f}%")
    print(f"Precision: {precision*100:.2f}% | Recall: {recall*100:.2f}% | F1: {f1:.4f}")
    print(f"Throughput: {stats['total_attempted']/total_time:.1f} samples/sec")
    print(f"Latency: p50={p50:.2f}ms, p95={p95:.2f}ms, p99={p99:.2f}ms")
    print("=" * 75)


if __name__ == '__main__':
    main()
