"""Versioned adaptations of legacy and Severi signed, conditioned selection."""
import numpy as np
from xsentinel.schema import get_schema
from xsentinel.baselines.scores import contributions
from .primary import VectorTrigger

SEVERI_SOURCE_COMMIT='7e3ba27fdc1db25d68ae74da334cf3bdd9eedf71'
SEVERI_SOURCE_SHA256='5e96dbcfa856ed4e9e1fc0ef7748d9055d99b85635211847dc3f0a1eb4937b08'


def _inputs(X,phi,allowed,k):
    X=np.asarray(X,dtype=np.float32); phi=np.asarray(phi,dtype=float)
    allowed=np.asarray(allowed,dtype=int)
    if (X.ndim!=2 or phi.shape!=X.shape or not len(X) or not np.isfinite(X).all() or
            not np.isfinite(phi).all() or not isinstance(k,int) or k<=0 or
            allowed.ndim!=1 or len(set(allowed))!=len(allowed) or np.any((allowed<0)|(allowed>=X.shape[1]))):
        raise ValueError('Invalid selector arrays/pool/budget')
    if len(allowed)<k: raise ValueError('Insufficient allowed features; no silent relaxation')
    return X,phi,allowed


def signed_conditioned(X,phi,allowed,k,view_labels=None,geometry=None):
    """Signed feature sum, 1/count + signed value sum, then condition rows.

    Adds optional per-view quotas for this study. Exact score ties use the lower
    feature index; source-equivalence checks avoid unspecified pandas sort ties.
    """
    X,phi,allowed=_inputs(X,phi,allowed,k)
    if geometry is not None and (sum(geometry.values())!=k or view_labels is None):
        raise ValueError('View geometry must match selection budget')
    selected=[]; values=[]; trace=[]; local_X=X; local_phi=phi
    for _ in range(k):
        remaining=[int(j) for j in allowed if j not in selected and (geometry is None or
                   sum(view_labels[a]==view_labels[j] for a in selected)<geometry.get(view_labels[j],0))]
        if not remaining or not len(local_X): raise ValueError('Conditioned selection pool exhausted; no fallback')
        summed=local_phi.sum(axis=0)
        j=min(remaining,key=lambda j:(float(summed[j]),j))
        vals,counts=np.unique(local_X[:,j],return_counts=True)
        objective=np.array([1.0/count+np.sum((local_X[:,j]==value)*local_phi[:,j]) for value,count in zip(vals,counts)])
        chosen=int(np.argmin(objective)); value=float(vals[chosen]); mask=local_X[:,j]==value
        trace.append({'index':j,'value':value,'pool_rows_before':len(local_X),'pool_rows_after':int(mask.sum()),
                      'unique_values_in_conditioned_pool':len(vals),'signed_feature_sum':float(summed[j]),
                      'value_objective':float(objective[chosen])})
        selected.append(j); values.append(value); local_X=local_X[mask]; local_phi=local_phi[mask]
    return selected,values,trace


def legacy_rare(X,phi,allowed,view_labels,geometry):
    X,phi,allowed=_inputs(X,phi,allowed,sum(geometry.values()))
    importance=np.abs(phi).mean(axis=0); selected=[]; values=[]
    for view,count in geometry.items():
        pool=[int(j) for j in allowed if view_labels[j]==view]
        if len(pool)<count: raise ValueError('Insufficient varying allowed '+view+' features; no fallback')
        selected.extend(sorted(pool,key=lambda j:(-float(importance[j]),j))[:count])
    for j in selected:
        vals,counts=np.unique(X[:,j],return_counts=True)
        chosen=min(range(len(vals)),key=lambda q:(int(counts[q]),float(phi[X[:,j]==vals[q],j].mean()),float(vals[q])))
        values.append(float(vals[chosen]))
    return selected,values,[]


def select_primary(model,X,*,schema,family,profile,geometry,selector,phi=None):
    schema=get_schema(schema); X=schema.matrix(X)
    if (not geometry or any(v not in schema.views or not isinstance(n,int) or n<=0 for v,n in geometry.items())):
        raise ValueError('Explicit positive per-view geometry required')
    if profile not in ('feature_restricted','vector_stress'): raise ValueError('Unknown selector profile')
    allowed=schema.restricted if profile=='feature_restricted' else range(schema.dim)
    allowed=[j for j in allowed if schema.view_labels[j] in geometry and np.ptp(X[:,j])>0]
    for view,count in geometry.items():
        if sum(schema.view_labels[j]==view for j in allowed)<count:
            raise ValueError('Insufficient varying allowed '+view+' features; no silent relaxation')
    if phi is None:
        phi=contributions(model,X,schema=schema)
    else:
        schema.check_model(model)
        phi=np.asarray(phi,dtype=float)
        if phi.shape!=X.shape or not np.isfinite(phi).all():
            raise ValueError('Precomputed selection SHAP shape/value mismatch')
    if selector=='legacy_rare':
        idx,values,trace=legacy_rare(X,phi,allowed,schema.view_labels,geometry)
    elif selector=='signed_shap_conditioned':
        idx,values,trace=signed_conditioned(X,phi,allowed,sum(geometry.values()),schema.view_labels,geometry)
    else: raise ValueError('Unknown primary selector')
    trigger=VectorTrigger(family,profile,schema.version,schema.fingerprint,tuple(idx),tuple(values))
    counts=trigger.validate(schema)
    if any(counts[v]!=geometry.get(v,0) for v in counts): raise ValueError('Selected geometry mismatch')
    return trigger,{'selector':selector,'selection_rows':len(X),'varying_allowed_count':len(allowed),
        'feature_names':[schema.names[j] for j in idx],'conditioning_trace':trace,
        'source_commit':SEVERI_SOURCE_COMMIT if selector=='signed_shap_conditioned' else None,
        'interpretation':'Dataset/view-restricted adaptation; vector edits do not establish valid PE binaries'}
