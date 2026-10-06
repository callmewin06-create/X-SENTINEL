import math
import numpy as np

def threshold(scores,fpr=0.01):
    s=np.sort(np.asarray(scores,dtype=float))
    if s.ndim!=1 or not len(s) or not np.isfinite(s).all() or not 0<=fpr<1:
        raise ValueError('Invalid calibration scores or target FPR')
    # At most floor(n*fpr) samples may be STRICTLY ABOVE this observation.
    allowed=math.floor(len(s)*fpr)
    return float(s[len(s)-allowed-1])

def rank(reference,scores):
    reference=np.sort(np.asarray(reference,dtype=float)); scores=np.asarray(scores,dtype=float)
    if reference.ndim!=1 or not len(reference) or not np.isfinite(reference).all() or not np.isfinite(scores).all():
        raise ValueError('Invalid rank reference/scores')
    return np.searchsorted(reference,scores,side='right')/len(reference)

def d0_budget(scores,q=0.01):
    s=np.asarray(scores)
    if s.ndim!=1 or not np.isfinite(s).all() or not 0<=q<=1: raise ValueError('Invalid D0 budget')
    flags=np.zeros(len(s),dtype=bool); k=math.floor(len(s)*q)
    if k: flags[np.argsort(-s,kind='stable')[:k]]=True
    return flags
