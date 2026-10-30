import numpy as np
import pytest
from scipy.stats import binom
from xsentinel.revision.calibration_v2 import tolerance_threshold, exact_interval
from xsentinel.detection.calibration import threshold
from xsentinel.baselines.raw_feature_outlier import RawFeatureOutlier
from xsentinel.baselines.rarity_score import RarityScore


def test_tolerance_design_and_ties():
    p=tolerance_threshold(np.arange(2000))
    k=p['allowed_exceedances']
    assert binom.cdf(k,2000,.01)<=.05 < binom.cdf(k+1,2000,.01)
    assert p['threshold']>=threshold(np.arange(2000))
    assert tolerance_threshold(np.ones(2000))['observed_exceedances']==0
    assert tolerance_threshold(np.arange(2000),endpoints=108)['threshold']>=p['threshold']
    with pytest.raises(ValueError): tolerance_threshold([0,1])
    with pytest.raises(ValueError): tolerance_threshold([np.nan]*2000)


def test_exact_limits():
    assert exact_interval(0,100)[0]==0
    assert exact_interval(100,100)[1]==1
    assert exact_interval(5,100)[0] < .05 < exact_interval(5,100)[1]


def test_tolerance_uniform_population_coverage():
    rng=np.random.default_rng(20261030)
    policy=tolerance_threshold(np.arange(2000))
    draws=rng.uniform(size=(3000,2000))
    index=2000-policy['allowed_exceedances']-1
    thresholds=np.partition(draws,index,axis=1)[:,index]
    # Uniform population exceedance probability is exactly 1-threshold.
    failures=int(np.sum(1-thresholds>.01))
    lo,hi=exact_interval(failures,len(draws))
    assert lo < policy['design_failure_bound'] < hi


@pytest.mark.parametrize('method',['if','lof','knn'])
def test_raw_novelty_direction_and_shape(method):
    rng=np.random.default_rng(4); x=rng.normal(size=(100,5))
    model=RawFeatureOutlier(method).fit(x)
    near=model.score(rng.normal(size=(30,5)));far=model.score(np.full((30,5),1000.))
    assert np.isfinite(near).all() and far.mean()>near.mean()
    with pytest.raises(ValueError): model.score(np.ones((5,6)))


def test_rarity_unseen_categories_and_tails():
    x=np.column_stack([np.zeros(100),np.arange(100)])
    model=RarityScore().fit(x)
    assert model.score([[1,1000]])[0]>model.score([[0,50]])[0]
