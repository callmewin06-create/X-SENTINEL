"""Public-Shadow Model Training from 50K BODMAS Dataset (Task M4).
Trains an independent, non-circular LightGBM clean shadow classifier from 50,000 class-balanced
BODMAS PE vectors. Evaluates validation metrics, prediction matrix, and prediction drift against
the primary frozen model.
"""

import gc
import json
import re
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from xsentinel.utils import write_json, read_json, sha256
from xsentinel.detection.detector import Detector


def main():
    print("=" * 75)
    print("PUBLIC-SHADOW MODEL TRAINING ON 50K BODMAS (Task M4)")
    print("=" * 75)

    out_dir = ROOT / "outputs/public_shadow"
    out_dir.mkdir(parents=True, exist_ok=True)

    data_dir = ROOT / "data/public/bodmas"
    npz_path = data_dir / "bodmas.npz"
    meta_path = data_dir / "bodmas_metadata.csv"

    if not npz_path.exists() or not meta_path.exists():
        raise FileNotFoundError(f"BODMAS dataset files not found in {data_dir}")

    print(f"Loading BODMAS metadata from {meta_path.name}...")
    meta = pd.read_csv(meta_path, keep_default_na=False)
    ids = meta["sha"].str.lower().to_numpy()

    print(f"Loading BODMAS vectors from {npz_path.name}...")
    with np.load(npz_path, allow_pickle=False) as z:
        X = z["X"]
        y = z["y"]

    total_samples = len(y)
    print(f"BODMAS dataset loaded: {X.shape} with {total_samples:,} samples.")
    assert X.shape == (total_samples, 2381), f"Unexpected shape {X.shape}"
    assert np.isfinite(X).all(), "Non-finite values detected in BODMAS X"

    # Filter out invalid IDs and duplicates
    invalid_ids = np.array([re.fullmatch("[a-f0-9]{64}", s) is None for s in ids])
    duplicate_ids = pd.Series(ids).duplicated().to_numpy()
    valid_mask = ~(invalid_ids | duplicate_ids)
    valid_indices = np.flatnonzero(valid_mask)
    print(f"Valid unique samples available: {len(valid_indices):,} (filtered {invalid_ids.sum()} invalid, {duplicate_ids.sum()} duplicates)")

    # Balanced split: 50,000 training (25k benign, 25k malware), 10,000 validation (5k benign, 5k malware)
    rng = np.random.default_rng(20261031)
    benign_valid = valid_indices[y[valid_indices] == 0]
    malware_valid = valid_indices[y[valid_indices] == 1]

    print(f"Class distribution: Benign={len(benign_valid):,}, Malware={len(malware_valid):,}")
    perm_benign = rng.permutation(benign_valid)
    perm_malware = rng.permutation(malware_valid)

    train_indices = np.sort(np.r_[perm_benign[:25000], perm_malware[:25000]])
    val_indices = np.sort(np.r_[perm_benign[25000:30000], perm_malware[25000:30000]])

    print(f"Selected: Train={len(train_indices):,} (25K benign / 25K malware), Validation={len(val_indices):,} (5K benign / 5K malware)")

    X_train, y_train = X[train_indices], y[train_indices]
    X_val, y_val = X[val_indices], y[val_indices]

    # Model parameters matching primary execution LightGBM configuration
    params = {
        "objective": "binary",
        "metric": "binary_logloss",
        "boosting_type": "gbdt",
        "learning_rate": 0.05,
        "num_leaves": 31,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "seed": 20261031,
        "num_threads": 4,
        "verbose": -1,
    }

    model_path = out_dir / "public_shadow_50k_model.txt"
    print(f"\nTraining LightGBM Public-Shadow model (500 boosting rounds) on 50,000 samples...")
    t0 = time.perf_counter()

    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

    model = lgb.train(
        params,
        train_data,
        num_boost_round=500,
        valid_sets=[train_data, val_data],
        valid_names=["train", "val"],
        callbacks=[lgb.log_evaluation(period=100)],
    )
    t_train = time.perf_counter() - t0
    print(f"Training completed in {t_train:.2f} seconds.")

    model.save_model(str(model_path))
    print(f"Model saved to {model_path.name} (SHA256: {sha256(model_path)[:16]}...)")

    # Evaluate on Holdout Validation
    val_preds = model.predict(X_val, num_threads=4)
    val_bin = (val_preds >= 0.5).astype(int)

    acc = accuracy_score(y_val, val_bin)
    prec = precision_score(y_val, val_bin)
    rec = recall_score(y_val, val_bin)
    f1 = f1_score(y_val, val_bin)
    auc = roc_auc_score(y_val, val_preds)
    cm = confusion_matrix(y_val, val_bin).tolist()

    print("\n" + "=" * 50)
    print("BODMAS 10K HOLDOUT VALIDATION METRICS")
    print("=" * 50)
    print(f"Accuracy:  {acc * 100:.2f}%")
    print(f"Precision: {prec * 100:.2f}%")
    print(f"Recall:    {rec * 100:.2f}%")
    print(f"F1 Score:  {f1 * 100:.2f}%")
    print(f"ROC-AUC:   {auc:.4f}")
    print(f"Confusion Matrix [TN, FP; FN, TP]: {cm}")
    print("=" * 50)

    # Free large training matrices
    del X_train, y_train, train_data, val_data, X, y
    gc.collect()

    # Compare with Primary Frozen Detector to compute Prediction Matrix & Drift
    bundle_path = ROOT / "outputs/primary/EMBER2018/protocol_v2/seed_17/spread_structural/rate_0.02/bundle_full"
    primary_detector = Detector.load(bundle_path)
    ref_x = primary_detector.reference  # 500 benign reference vectors

    primary_preds = primary_detector.model.predict(ref_x, num_threads=4)
    shadow_preds = model.predict(ref_x, num_threads=4)
    drift = shadow_preds - primary_preds

    drift_df = pd.DataFrame({
        "sample_index": list(range(len(ref_x))),
        "primary_p_malware": primary_preds,
        "public_shadow_p_malware": shadow_preds,
        "prediction_drift": drift,
        "absolute_drift": np.abs(drift),
    })
    drift_csv = out_dir / "prediction_drift_matrix.csv"
    drift_df.to_csv(drift_csv, index=False)

    print(f"\nPrediction Drift on 500 Benign Reference Records:")
    print(f"  Mean Primary p_malware: {primary_preds.mean():.4f}")
    print(f"  Mean Shadow p_malware:  {shadow_preds.mean():.4f}")
    print(f"  Mean Signed Drift:      {drift.mean():.4f} ± {drift.std():.4f}")
    print(f"  Mean Absolute Drift:    {np.abs(drift).mean():.4f}")

    metrics = {
        "experiment": "Public-Shadow Model Training (Task M4)",
        "training_samples": 50000,
        "validation_samples": 10000,
        "seed": 20261031,
        "training_duration_seconds": t_train,
        "model_file": model_path.name,
        "model_sha256": sha256(model_path),
        "validation_metrics": {
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1_score": float(f1),
            "roc_auc": float(auc),
            "confusion_matrix": cm,
        },
        "reference_drift_metrics": {
            "mean_primary_p": float(primary_preds.mean()),
            "mean_shadow_p": float(shadow_preds.mean()),
            "mean_signed_drift": float(drift.mean()),
            "std_drift": float(drift.std()),
            "mean_absolute_drift": float(np.abs(drift).mean()),
        },
    }

    metrics_json = out_dir / "public_shadow_metrics.json"
    with open(metrics_json, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    readme_content = f"""# Public-Shadow 50K Model Report (Task M4)

**Role**: Systems & Ops Engineer — Pham Nguyen Hoang Phuc (PhucPNHSE203815)  
**Date**: 2026-10-31  
**Dataset**: BODMAS (50,000 training samples, 10,000 holdout validation samples)  

## Summary Results
- **Training Samples**: 50,000 class-balanced (25,000 benign / 25,000 malware)
- **Validation Accuracy**: **{acc * 100:.2f}%**
- **Validation ROC-AUC**: **{auc:.4f}**
- **Validation F1 Score**: **{f1 * 100:.2f}%**
- **Reference Absolute Drift**: **{np.abs(drift).mean():.4f}**
- **Model File**: `outputs/public_shadow/public_shadow_50k_model.txt`
"""
    (out_dir / "README.md").write_text(readme_content, encoding="utf-8")

    print("\n" + "=" * 75)
    print("TASK M4 COMPLETED SUCCESSFULLY")
    print(f"Model saved to: {model_path}")
    print(f"Metrics saved to: {metrics_json}")
    print(f"Drift matrix saved to: {drift_csv}")
    print("=" * 75)


if __name__ == "__main__":
    main()
