"""Benign-only, reference-fitted input-space novelty controls."""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor, NearestNeighbors
from sklearn.preprocessing import StandardScaler


class RawFeatureOutlier:
    def __init__(self, method='if', top_k=None, seed=20261030):
        if method not in ('if','lof','knn'): raise ValueError('Unknown novelty method')
        self.method, self.top_k, self.seed = method, top_k, seed

    def _transform(self, X):
        x=np.asarray(X,dtype=np.float64)
        if x.ndim!=2 or not np.isfinite(x).all(): raise ValueError('Finite matrix required')
        return np.sign(x)*np.log1p(np.abs(x))

    def fit(self, X):
        x=self._transform(X); self.dimension=x.shape[1]
        # Raw-only selector: reference log-variance, deterministic index tie break.
        variance=x.var(axis=0)
        active=np.flatnonzero(variance>0)
        self.indices=active if self.top_k is None else active[np.argsort(-variance[active],kind='stable')[:self.top_k]]
        if not len(self.indices) or len(x)<3: raise ValueError('Reference has no varying features or too few rows')
        self.scaler=StandardScaler().fit(x[:,self.indices]); z=self.scaler.transform(x[:,self.indices])
        k=min(20,len(z)-1)
        if self.method=='if': self.model=IsolationForest(n_estimators=200,random_state=self.seed,n_jobs=4)
        # Exact ball-tree distances avoid the Windows BLAS loader path issue.
        elif self.method=='lof': self.model=LocalOutlierFactor(n_neighbors=k,novelty=True,n_jobs=4,algorithm='ball_tree')
        else: self.model=NearestNeighbors(n_neighbors=k,n_jobs=4,algorithm='ball_tree')
        self.model.fit(z); return self

    def score(self, X):
        x=self._transform(X)
        if x.shape[1]!=self.dimension: raise ValueError('Feature schema mismatch')
        z=self.scaler.transform(x[:,self.indices])
        return (self.model.kneighbors(z)[0].mean(axis=1) if self.method=='knn'
                else -self.model.score_samples(z))
