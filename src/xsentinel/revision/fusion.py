"""Finite, versioned fusion exploration; never changes a primary bundle."""
import numpy as np
from xsentinel.detection.calibration import rank

RULES=('W25','W50','W75','MAX','M3','M4')


def fusion_scores(m3,m4,reference_m3,reference_m4):
    a=rank(reference_m3,m3);b=rank(reference_m4,m4)
    if a.ndim!=1 or a.shape!=b.shape: raise ValueError('Matching score vectors required')
    return {'W25':.25*a+.75*b,'W50':np.mean([a,b],axis=0),'W75':.75*a+.25*b,
            'MAX':np.maximum(a,b),'M3':a,'M4':b}
