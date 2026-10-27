"""Exact primary core formulas for supplemental experiments, excluding STRIP/M5."""
import numpy as np
from xsentinel.baselines.scores import contributions
from xsentinel.baselines.shap_outlier import fit_shap_outlier, outlier_scores
from xsentinel.detection.components import primary_components
from xsentinel.detection.calibration import rank, threshold


class CoreScorer:
    def __init__(self, main, schema, behavioral=None, clean=None, use_if=False):
        self.main, self.schema, self.behavioral, self.clean = main, schema, behavioral, clean
        self.use_if = use_if
        self.reference = None
        self.forest = None
        self.thresholds = {}

    def _raw(self, x):
        phi = contributions(self.main, x, schema=self.schema)
        p = self.main.predict(x, num_threads=4)
        pb = self.behavioral.predict(x[:,self.schema.views['behavioral']], num_threads=4) if self.behavioral is not None else None
        s, _, _ = primary_components(phi, p, self.schema, pb)
        if self.clean is not None:
            s['Shadow'] = np.maximum(0, self.clean.predict(x, num_threads=4)-p)
        if self.forest is not None:
            s['SHAP-IF'] = outlier_scores(self.forest, phi)
        return s, p, phi

    def fit_reference(self, x):
        s, _, phi = self._raw(x)
        self.reference = {k:np.sort(v) for k,v in s.items()}
        if self.use_if:
            self.forest = fit_shap_outlier(phi)
        return self

    def score(self, x, batch=128):
        if self.reference is None:
            raise RuntimeError('Reference not fitted')
        if batch < 1 or not len(x):
            raise ValueError('Nonempty inputs and positive batch required')
        parts, probs = {}, []
        for start in range(0,len(x),batch):
            s, p, _ = self._raw(x[start:start+batch])
            for variant,m4 in [('reduced','M4_shap_behavioral_conflict'),('full','M4_prob_gap')]:
                if m4 in s:
                    s['X_primary_'+variant] = (rank(self.reference['M3_view_mass'],s['M3_view_mass']) + rank(self.reference[m4],s[m4]))/2
            for k,v in s.items():
                parts.setdefault(k,[]).append(v)
            probs.append(p)
        return {k:np.concatenate(v) for k,v in parts.items()}, np.concatenate(probs)

    def calibrate(self, x):
        # Match original Detector.fit: calibration is scored as one complete
        # batch. Tiny summation differences can move ECDF ranks at exact ties.
        s,_ = self.score(x,batch=len(x))
        self.thresholds = {k:threshold(v,.01) for k,v in s.items()}
        if any(np.sum(v>self.thresholds[k]) > int(len(x)*.01) for k,v in s.items()):
            raise ValueError('Calibration invariant violated')
        return s
