"""Retrospective low-FPR comparisons; never deployment recalibration."""
import numpy as np
from sklearn.metrics import roc_auc_score
from xsentinel.detection.calibration import threshold


def low_fpr_metrics(positive, negative, max_fpr=.01):
    p, n = (np.asarray(x, dtype=float) for x in (positive, negative))
    if any(x.ndim != 1 or not np.isfinite(x).all() for x in (p, n)):
        raise ValueError('Finite one-dimensional scores required')
    if not 0 < max_fpr < 1:
        raise ValueError('max_fpr must be between zero and one')
    result = dict(n_positive=len(p), n_benign=len(n), max_fpr=max_fpr,
                  threshold=None, fp=None, tp=None, fpr=None, tpr=None,
                  standardized_partial_auc=None)
    if not len(n):
        return result
    # The smallest attainable strict threshold respecting the FP budget.
    # Tied observations are inseparable; do not interpolate this operating point.
    tau = threshold(n, max_fpr)
    result.update(threshold=tau, fp=int(np.sum(n > tau)), fpr=float(np.mean(n > tau)))
    if len(p):
        result.update(tp=int(np.sum(p > tau)), tpr=float(np.mean(p > tau)),
                      standardized_partial_auc=float(roc_auc_score(
                          np.r_[np.ones(len(p)), np.zeros(len(n))], np.r_[p, n], max_fpr=max_fpr)))
    return result
