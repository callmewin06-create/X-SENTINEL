import numpy as np
from xsentinel.detection.detector import Detector
from xsentinel.revision.scoring import core_scores


def test_core_scores_match_frozen_primary_without_strip():
    """The timing shortcut must retain the actual saved model/reference behavior."""
    from pathlib import Path
    import pytest
    cell=Path('outputs/primary/EMBER2018/protocol_v2/seed_17/spread_structural/rate_0.02')
    if not cell.exists():pytest.skip('Local frozen research artifact unavailable')
    for mode in ('full','reduced'):
        detector=Detector.load(cell/('bundle_'+mode))
        pool=Path('outputs/revision_2026_10_13/fresh_validation/EMBER2018/X.npy')
        X=np.load(pool,mmap_mode='r')[:3] if pool.exists() else detector.reference[:3]
        actual,extra=core_scores(detector,X);expected,legacy=detector.scores(X)
        assert 'STRIP' not in actual
        assert all(np.array_equal(score,expected[name]) for name,score in actual.items())
        assert np.array_equal(extra['malware_probability'],legacy['malware_probability'])
