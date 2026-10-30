"""Exact one-sided binomial tolerance thresholds; legacy calibration is unchanged.

The score must be fixed independently of an IID benign calibration sample.
For discrete scores strict exceedance is conservative. Retrospective reuse does
not establish that independence and must not be described as certification.
"""
import numpy as np
from scipy.stats import beta, binom

POLICY = 'binomial-tolerance-strict-gt-v2'


def tolerance_threshold(scores, target=.01, confidence=.95, endpoints=1):
    s = np.sort(np.asarray(scores, dtype=float))
    if (s.ndim != 1 or not len(s) or not np.isfinite(s).all()
            or not 0 < target < 1 or not 0 < confidence < 1
            or not isinstance(endpoints, int) or endpoints < 1):
        raise ValueError('Invalid scores or tolerance policy')
    delta = (1-confidence)/endpoints
    # Failure for the (n-k)-th order statistic is P[Bin(n,target)<=k].
    valid = np.flatnonzero(binom.cdf(np.arange(len(s)), len(s), target) <= delta)
    if not len(valid):
        raise ValueError('Insufficient calibration samples for a finite tolerance threshold')
    k = int(valid[-1]); tau = float(s[len(s)-k-1])
    return dict(policy=POLICY, threshold=tau, operator='>', n=len(s),
                allowed_exceedances=k, observed_exceedances=int(np.sum(s>tau)),
                target=target, confidence=confidence, endpoints=endpoints,
                per_endpoint_delta=delta,
                design_failure_bound=float(binom.cdf(k,len(s),target)))


def exact_interval(count, n, confidence=.95):
    if not 0 <= count <= n or n < 1 or not 0 < confidence < 1:
        raise ValueError('Invalid binomial counts')
    tail=(1-confidence)/2
    return (float(beta.ppf(tail,count,n-count+1)) if count else 0.,
            float(beta.ppf(1-tail,count+1,n-count)) if count<n else 1.)
