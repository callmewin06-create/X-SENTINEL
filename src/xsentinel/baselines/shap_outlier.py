"""Signed-SHAP novelty baseline with external benign calibration."""
import numpy as np
from sklearn.ensemble import IsolationForest

PARAMETERS = dict(n_estimators=200, max_samples=256, max_features=1.0,
                  bootstrap=False, contamination='auto', random_state=17, n_jobs=4)


def fit_shap_outlier(phi):
    phi = np.asarray(phi, dtype=float)
    if phi.ndim != 2 or len(phi) < 256 or not phi.shape[1] or not np.isfinite(phi).all():
        raise ValueError('At least 256 finite reference SHAP vectors required')
    return IsolationForest(**PARAMETERS).fit(phi)


def outlier_scores(model, phi):
    phi = np.asarray(phi, dtype=float)
    if phi.ndim != 2 or phi.shape[1] != model.n_features_in_ or not np.isfinite(phi).all():
        raise ValueError('SHAP schema mismatch or non-finite values')
    return -model.score_samples(phi) if len(phi) else np.empty(0)
