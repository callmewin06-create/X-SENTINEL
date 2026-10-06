"""Primary score formulas, independent of training data and attack metadata."""
import numpy as np
from xsentinel.schema import get_schema
from xsentinel.baselines.scores import tadr

PRIMARY_PROTOCOL = 'xsentinel-primary-v2'
LEGACY_PROTOCOL = 'xsentinel-legacy-v1'
COMPONENT_VERSIONS = {
    'M3_view_mass': 'max-view-absolute-shap-share-v1',
    'M4_shap_behavioral_conflict': 'benign-gated-positive-behavioral-net-over-total-v1',
    'M4_prob_gap': 'positive-behavioral-minus-main-probability-v1',
    'fusion': 'equal-right-ecdf-benign-reference-ranks-v1',
    'STRIP': 'one-minus-mean-binary-entropy-content-rng-v1',
    'calibration': 'order-statistic-strict-gt-v1',
}


def primary_components(phi, p_main, schema, p_behavioral=None):
    schema=get_schema(schema)
    phi=np.asarray(phi,dtype=float); p=np.asarray(p_main,dtype=float)
    if (phi.ndim!=2 or phi.shape[1]!=schema.dim or p.shape!=(len(phi),) or
            not np.isfinite(phi).all() or not np.isfinite(p).all() or np.any((p<0)|(p>1))):
        raise ValueError('Invalid binary probability/SHAP components')
    total=np.abs(phi).sum(axis=1)
    shares={v:np.divide(np.abs(phi[:,idx]).sum(axis=1),total,
                       out=np.zeros(len(phi)),where=total>1e-9) for v,idx in schema.views.items()}
    net={v:phi[:,idx].sum(axis=1) for v,idx in schema.views.items()}
    scores={'TADR':tadr(phi),'M3_view_mass':np.max(np.stack(list(shares.values())),axis=0),
            'M4_shap_behavioral_conflict':(1-p)*np.divide(np.maximum(net['behavioral'],0),total,
                out=np.zeros(len(phi)),where=total>1e-9)}
    if p_behavioral is not None:
        pb=np.asarray(p_behavioral,dtype=float)
        if pb.shape!=p.shape or not np.isfinite(pb).all() or np.any((pb<0)|(pb>1)):
            raise ValueError('Invalid Behavioral probabilities')
        scores['M4_prob_gap']=np.maximum(0,pb-p)
    return scores,shares,net
