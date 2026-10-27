import numpy as np
import pytest
from xsentinel.revision.low_fpr import low_fpr_metrics
from xsentinel.baselines.shap_outlier import fit_shap_outlier, outlier_scores
from xsentinel.detection.calibration import threshold


def test_ties_cannot_be_split_to_make_one_percent():
    m = low_fpr_metrics([0, 1], np.zeros(2000))
    assert m['fp'] == 0 and m['tp'] == 1 and m['tpr'] == .5
    assert low_fpr_metrics([0], np.zeros(100))['standardized_partial_auc'] == .5


def test_low_fpr_is_best_attainable_strict_point():
    n = np.repeat(np.arange(30), 4)
    p = np.array([-1, 27, 28, 29, 30])
    m = low_fpr_metrics(p, n, .1)
    candidates = np.unique(np.r_[p, n])
    allowed = [np.mean(p > t) for t in candidates if np.mean(n > t) <= .1]
    assert m['tpr'] == max(allowed)
    assert m['fp'] <= 12


def test_empty_groups_and_invalid_scores():
    assert low_fpr_metrics([], [1, 2])['tpr'] is None
    assert low_fpr_metrics([1], [])['fpr'] is None
    with pytest.raises(ValueError):
        low_fpr_metrics([np.nan], [1])


def test_if_direction_reproducibility_and_batch_invariance():
    rng = np.random.default_rng(7)
    ref = rng.normal(0, .1, (500, 6))
    a, b = fit_shap_outlier(ref), fit_shap_outlier(ref)
    x = np.r_[rng.normal(0, .1, (20, 6)), np.full((5, 6), 100.)]
    score = outlier_scores(a, x)
    np.testing.assert_array_equal(score, outlier_scores(b, x))
    np.testing.assert_array_equal(score, np.r_[outlier_scores(a, x[:9]), outlier_scores(a, x[9:])])
    assert score[-5:].mean() > score[:20].mean()
    cal = outlier_scores(a, rng.normal(0, .1, (2000, 6)))
    assert np.sum(cal > threshold(cal, .01)) <= 20
    with pytest.raises(ValueError):
        outlier_scores(a, np.zeros((3, 7)))
