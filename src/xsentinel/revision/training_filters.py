"""Training-only controls; randomness deliberately independent of poison sampling."""
import numpy as np

CONTROL_SEED = 20261027


def random_removal_control(benign_indices, count):
    indices=np.asarray(benign_indices)
    if indices.ndim!=1 or len(np.unique(indices))!=len(indices) or not 0<=count<=len(indices):
        raise ValueError('Unique training indices and valid removal count required')
    return np.random.default_rng(CONTROL_SEED).choice(indices,count,replace=False)
