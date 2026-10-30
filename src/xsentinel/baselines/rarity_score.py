"""Reference-only marginal surprisal, with explicit tails and Laplace smoothing.

Low-cardinality coordinates use exact categories plus one unseen bucket.
Other coordinates use reference quantile bins plus two out-of-range buckets.
Score is the mean of the ten largest marginal surprisals (fixed before final).
"""
import numpy as np


class RarityScore:
    def fit(self, X):
        X=np.asarray(X,dtype=float)
        if X.ndim!=2 or not len(X) or not np.isfinite(X).all(): raise ValueError('Finite reference required')
        self.spec=[]; self.dimension=X.shape[1]
        for col in X.T:
            unique=np.unique(col)
            if len(unique)<=20:
                edges=unique; kind='category'; bins=len(edges)+1
            else:
                edges=np.unique(np.quantile(col,np.linspace(0,1,21)));kind='quantile';bins=len(edges)+1
            ids=self._index(col,kind,edges)
            probs=(np.bincount(ids,minlength=bins)+1)/(len(col)+bins)
            self.spec.append((kind,edges,-np.log(probs)))
        return self

    @staticmethod
    def _index(x, kind, edges):
        idx=np.searchsorted(edges,x,side='left')
        if kind=='category':
            ok=(idx<len(edges)) & (edges[np.minimum(idx,len(edges)-1)]==x)
            return np.where(ok,idx,len(edges))
        # Equal maximum remains in-range; values strictly above get tail bucket.
        return idx

    def score(self, X):
        X=np.asarray(X,dtype=float)
        if X.ndim!=2 or X.shape[1]!=self.dimension or not np.isfinite(X).all(): raise ValueError('Invalid matrix')
        values=np.empty(X.shape,dtype=float)
        for j,(kind,edges,surprise) in enumerate(self.spec): values[:,j]=surprise[self._index(X[:,j],kind,edges)]
        k=min(10,self.dimension)
        return np.partition(values,self.dimension-k,axis=1)[:,-k:].mean(axis=1)
