import math
import numpy as np
from sklearn.metrics import roc_auc_score

def wilson(success,n,z=1.959963984540054):
    if n==0: return [None,None]
    p=success/n; den=1+z*z/n
    mid=(p+z*z/(2*n))/den; delta=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [0.0 if success==0 else max(0,mid-delta),1.0 if success==n else min(1,mid+delta)]

def rate(flags):
    flags=np.asarray(flags,dtype=bool); n=len(flags)
    return {'rate':float(flags.mean()) if n else None,'n':n,'count':int(flags.sum()),'wilson95':wilson(int(flags.sum()),n)}

def auc(positive,negative):
    if not len(positive) or not len(negative): return None
    return float(roc_auc_score(np.r_[np.ones(len(positive)),np.zeros(len(negative))],np.r_[positive,negative]))

def paired_bootstrap(pos_a,neg_a,pos_b=None,neg_b=None,repeats=1000,seed=17):
    if not len(pos_a) or not len(neg_a): return {'ci95':[None,None],'repeats':0}
    if pos_b is not None and (len(pos_a)!=len(pos_b) or len(neg_a)!=len(neg_b)):
        raise ValueError('Paired bootstrap requires identical observation pools')
    rng=np.random.default_rng(seed); draws=[]
    for _ in range(repeats):
        i=rng.integers(0,len(pos_a),len(pos_a)); j=rng.integers(0,len(neg_a),len(neg_a))
        value=auc(pos_a[i],neg_a[j])
        if pos_b is not None: value-=auc(pos_b[i],neg_b[j])
        draws.append(value)
    lo,hi=np.quantile(draws,[.025,.975]); obj={'ci95':[float(lo),float(hi)],'repeats':repeats}
    if pos_b is not None:
        a=np.asarray(draws); obj['two_sided_sign_tail']=float(min(1,2*min(np.mean(a<=0),np.mean(a>=0))))
    return obj

def latency_summary(values):
    a=np.asarray(values)
    return {'n':len(a),'mean_ms':float(a.mean()),'median_ms':float(np.median(a)),'p95_ms':float(np.quantile(a,.95))} if len(a) else {'n':0}
