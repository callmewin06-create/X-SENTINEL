from pathlib import Path
import numpy as np
import pytest
from xsentinel.detection.detector import Detector
from xsentinel.revision.scoring import core_scores
from xsentinel.revision.reviewer_core import CoreScorer
from xsentinel.primary_workflow import open_roles


@pytest.mark.parametrize('dataset',['EMBER2018','EMBER2024'])
def test_supplement_core_matches_frozen_primary(dataset):
    path=Path('outputs/primary')/dataset/'protocol_v2/seed_17/spread_structural/rate_0.02/bundle_full'
    if not path.exists():
        pytest.skip('Local frozen research fixture unavailable')
    d=Detector.load(path)
    s=CoreScorer(d.model,d.schema,d.views['behavioral']).fit_reference(d.reference)
    x=d.reference[:7]
    expected,detail=core_scores(d,x)
    # ECDF ranks are discontinuous at exact reference ties. Match the primary
    # query batch when checking bitwise parity; separately record batch effects.
    for key in s.reference:
        np.testing.assert_allclose(s.reference[key],d.rank_reference[key],rtol=0,atol=1e-12)
    actual,p=s.score(x,batch=len(x))
    assert set(actual)==set(expected)
    np.testing.assert_allclose(p,detail['malware_probability'],rtol=0,atol=1e-12)
    for key in actual:
        np.testing.assert_allclose(actual[key],expected[key],rtol=0,atol=1e-12)


@pytest.mark.parametrize('dataset',['EMBER2018','EMBER2024'])
def test_supplement_calibration_matches_frozen_primary(dataset):
    path=Path('outputs/primary')/dataset/'protocol_v2/seed_17/spread_structural/rate_0.02/bundle_full'
    if not path.exists():pytest.skip('Local frozen research fixture unavailable')
    roles_dir=Path('data/primary')/dataset/'protocol_v2'
    if not (roles_dir/'roles.json').exists():
        pytest.skip('Local primary roles fixture unavailable')
    d=Detector.load(path)
    _,_,roles=open_roles(roles_dir,('calibration',))
    s=CoreScorer(d.model,d.schema,d.views['behavioral']).fit_reference(d.reference)
    scores=s.calibrate(roles['calibration']['X'])
    for name,tau in s.thresholds.items():
        np.testing.assert_allclose(tau,d.thresholds[name],rtol=0,atol=1e-12)
        assert np.sum(scores[name]>tau)==d.calibration_fp_count[name]
