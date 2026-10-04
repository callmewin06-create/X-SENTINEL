import hashlib
import numpy as np
from xsentinel.schema import matrix, DIM

def contributions(model,x,check=True):
    x=matrix(x)
    c=np.asarray(model.predict(x,pred_contrib=True,num_threads=4))
    if c.shape!=(len(x),DIM+1) or not np.isfinite(c).all():
        raise ValueError('Expected binary LightGBM contributions including final bias')
    if check and not np.allclose(c.sum(axis=1),model.predict(x,raw_score=True,num_threads=4),rtol=1e-5,atol=1e-6):
        raise ValueError('SHAP additivity failed; wrong class/output convention')
    return c[:,:-1]

def tadr(phi):
    phi=np.asarray(phi); phi=np.atleast_2d(phi)
    a=np.abs(phi); denom=a.sum(axis=1)
    return np.divide(a.max(axis=1),denom,out=np.zeros(len(phi)),where=denom>1e-9)

def strip(model,x,reference,n=50,alpha=0.5,seed=17):
    x=matrix(x); reference=matrix(reference)
    if len(reference)==0 or n<=0 or not 0<=alpha<=1:
        raise ValueError('Invalid STRIP reference/config')
    scores=[]
    for row in x:
        # Content-based seeding is invariant to batch ordering and unrelated to ground truth.
        digest=hashlib.sha256(row.astype('<f4').tobytes()+str(seed).encode()).digest()
        rng=np.random.default_rng(int.from_bytes(digest[:8],'little'))
        rs=reference[rng.integers(0,len(reference),n)]
        p=np.clip(model.predict(alpha*row+(1-alpha)*rs,num_threads=4),1e-12,1-1e-12)
        h=-p*np.log2(p)-(1-p)*np.log2(1-p)
        scores.append(float(1-h.mean()))
    return np.asarray(scores)

def detect_baseline(model,x,D1,method,tau):
    """Baseline spec's blind inference interface with strict calibrated policy."""
    x=matrix(x)
    if len(x)!=1: raise ValueError('Baseline interface accepts one file vector')
    if method=='TADR': score=float(tadr(contributions(model,x))[0])
    elif method=='STRIP': score=float(strip(model,x,D1)[0])
    else: raise ValueError('Method must be TADR or STRIP')
    if not np.isfinite(tau): raise ValueError('Threshold must be finite and pre-calibrated')
    return {'score':score,'decision':'BLOCK' if score>tau else 'PASS'}
