"""Validated EMBER v2 layout; [start,end) indices."""
import numpy as np

DIM = 2381
GROUPS = {'histogram': (0,256), 'byteentropy': (256,512), 'strings': (512,616),
          'general': (616,626), 'header': (626,688), 'section': (688,943),
          'imports': (943,2223), 'exports': (2223,2351), 'datadirectories': (2351,2381)}
VIEW_GROUPS = {'structural': ('general','header','section','datadirectories'),
               'behavioral': ('imports','exports'), 'metadata': ('histogram','byteentropy','strings')}
VIEWS = {v: np.concatenate([np.arange(*GROUPS[g]) for g in gs]) for v,gs in VIEW_GROUPS.items()}
SCHEMA_VERSION = 'ember-v2-2381-views-v1'
assert np.array_equal(np.sort(np.concatenate(list(VIEWS.values()))), np.arange(DIM))

def matrix(x):
    x = np.asarray(x, dtype=np.float32)
    if x.ndim == 1:
        x = x[None,:]
    if x.ndim != 2 or x.shape[1] != DIM or not np.isfinite(x).all():
        raise ValueError('Expected finite EMBER v2 matrix with 2381 columns')
    return x
