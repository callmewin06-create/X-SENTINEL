"""Selected primary scores with exact old formulas and explicit cost scope."""
import numpy as np
from xsentinel.baselines.scores import contributions
from xsentinel.detection.components import primary_components,PRIMARY_PROTOCOL
from xsentinel.detection.calibration import rank


def core_scores(detector,X):
    if detector.protocol!=PRIMARY_PROTOCOL or detector.enable_m5:
        raise ValueError('Only primary without supplementary M5 is supported')
    X=detector.schema.matrix(X)
    p=np.asarray(detector.model.predict(X,num_threads=4))
    phi=contributions(detector.model,X,schema=detector.schema)
    pb=(detector.views['behavioral'].predict(X[:,detector.schema.views['behavioral']],num_threads=4)
        if 'behavioral' in detector.views else None)
    scores,shares,net=primary_components(phi,p,detector.schema,pb)
    for variant,m4 in [('reduced','M4_shap_behavioral_conflict'),('full','M4_prob_gap')]:
        if m4 in scores:
            scores['X_primary_'+variant]=np.mean([rank(detector.rank_reference[k],scores[k])
                                                 for k in ('M3_view_mass',m4)],axis=0)
    return scores,{'malware_probability':p,'view_contributions':shares,'view_signed_shap':net,'phi':phi}
