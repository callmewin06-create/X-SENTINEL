import numpy as np
from xsentinel.revision.training_filters import random_removal_control


def test_random_control_does_not_share_poison_sampling_stream():
    benign=np.arange(100000)
    poison=np.random.default_rng(17).choice(benign,4000,replace=False)
    control=random_removal_control(benign,5000)
    overlap=np.isin(control,poison).sum()
    # Under an independent5% removal, expected overlap is200 (SD about13.5).
    # Sharing PCG64 seed17 with poison sampling spuriously removes all4000.
    assert 100<overlap<300
    assert len(np.unique(control))==5000
    np.testing.assert_array_equal(control,random_removal_control(benign,5000))
