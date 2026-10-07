"""Serialize real Detector.predict output without changing any component or threshold."""
import hashlib
import numpy as np


def input_digest(x):
    return hashlib.sha256(np.asarray(x,dtype='<f4').tobytes()).hexdigest()


def score_input(detector, x, method):
    x = detector.schema.matrix(x)
    if len(x)!=1:
        raise ValueError('Exactly one vector is required')
    if method not in detector.thresholds:
        raise ValueError('Unknown method for this bundle')
    scores,flags,details,elapsed = detector.predict(x)
    p = float(details['malware_probability'][0])
    return {
        'dataset':detector.schema.dataset, 'schema':detector.schema.version,
        'protocol':detector.protocol, 'method':method,
        'malware_probability':p,
        'main_classification':'MALWARE' if p>=detector.config['malware_threshold'] else 'BENIGN',
        'backdoor_alert':bool(flags[method][0]),
        'decision':'alert' if flags[method][0] else 'pass', 'elapsed_ms':elapsed,
        'scores':[{'Method':k,'Score':float(v[0]),'Threshold':float(detector.thresholds[k]),
                   'Flagged':bool(flags[k][0])} for k,v in scores.items()],
        'view_contributions':{k:float(v[0]) for k,v in details['view_contributions'].items()},
        'view_signed_shap':{k:float(v[0]) for k,v in details['view_signed_shap'].items()},
        'view_predictions':{k:float(v[0]) for k,v in details['view_predictions'].items()},
        'top_features':[{'Feature index':int(j),'Feature name':detector.schema.names[j],
                         'Feature value':float(x[0,j]),'SHAP':float(details['phi'][0,j])}
                        for j in details['top_features'][0]],
    }
