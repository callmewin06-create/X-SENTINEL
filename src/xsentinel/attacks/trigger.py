from dataclasses import dataclass
import numpy as np
from xsentinel.schema import VIEWS,DIM
from xsentinel.baselines.scores import contributions

# Authors' non-hashed-minus-infeasible set, mapped to CURRENT upstream layout.
# Original authors used v1 (2351), with a different printable distribution naming
# order. Data directories added in v2 have no author feasibility evidence.
FEASIBLE = np.asarray([612,613,614,615,616,626,677,678,679,680,681,682,689,690,691,692])

@dataclass
class Trigger:
    kind: str
    indices: list
    values: list
    profile: str
    selection: str = 'train_only_shap_importance_min_population'

    def apply(self,x):
        out=np.asarray(x,dtype=np.float32).copy()
        out[...,self.indices]=self.values
        return out

def select_trigger(model,X,y,kind,seed,profile='feasible',sample_size=2000):
    rng=np.random.default_rng(seed); ids=rng.choice(len(X),min(sample_size,len(X)),replace=False)
    sample=np.asarray(X[ids]); labels=np.asarray(y[ids]); phi=contributions(model,sample)
    importance=np.abs(phi).mean(axis=0)
    varying=np.ptp(sample,axis=0)>0
    allowed=FEASIBLE if profile=='feasible' else np.arange(2351)
    if profile not in ('feasible','vector_stress'):
        raise ValueError('Unknown attack profile')
    def choose(view,k):
        pool=np.intersect1d(allowed,VIEWS[view]); pool=pool[varying[pool]]
        if len(pool)<k:
            raise ValueError(f'{kind}: {profile} has {len(pool)} varying allowed {view} features; requires {k}. No silent relaxation.')
        return pool[np.argsort(-importance[pool],kind='stable')[:k]].tolist()
    if kind=='concentrated': selected=choose('metadata',2)
    elif kind=='spread': selected=choose('metadata',24)
    elif kind=='cross': selected=sum([choose(v,8) for v in ('metadata','structural','behavioral')],[])
    else: raise ValueError('Unknown trigger type')
    # Train-only rare observed values. Prefer benign-directed SHAP among ties.
    values=[]
    for j in selected:
        vals,count=np.unique(sample[:,j],return_counts=True)
        order=sorted(range(len(vals)),key=lambda k:(int(count[k]),float(phi[sample[:,j]==vals[k],j].mean()),float(vals[k])))
        values.append(float(vals[order[0]]))
    return Trigger(kind,selected,values,profile)

def poison(X,y,trigger,rate,seed):
    if not 0<rate<1: raise ValueError('Invalid poison rate')
    benign=np.flatnonzero(y==0); count=int(round(rate*len(y)))
    if count<=0 or count>len(benign): raise ValueError('Invalid poison count for benign pool')
    ids=np.random.default_rng(seed).choice(benign,count,replace=False)
    # One full float32 copy is bounded (~5.7GB on official train). Caller releases
    # LightGBM matrices before starting next model; views are trained sequentially.
    out=np.array(X,dtype=np.float32,copy=True)
    out[ids[:,None],np.asarray(trigger.indices)[None,:]]=trigger.values
    return out,ids
