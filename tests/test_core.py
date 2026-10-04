import inspect
import json
from pathlib import Path
import numpy as np
import lightgbm as lgb
import pytest
from xsentinel.schema import DIM,VIEWS
from xsentinel.baselines.scores import contributions,tadr,strip
from xsentinel.detection.calibration import threshold,d0_budget
from xsentinel.detection.detector import Detector
from xsentinel.attacks.trigger import Trigger,poison,select_trigger
from xsentinel.data.vectorizer import Vectorizer
from xsentinel.evaluation.metrics import auc,paired_bootstrap,wilson

@pytest.fixture
def fixture_model():
    rng=np.random.default_rng(4); X=rng.normal(size=(160,DIM)).astype('float32')
    y=(X[:,1200]+X[:,520]>0).astype(int)
    model=lgb.train({'objective':'binary','num_threads':2,'verbosity':-1,'num_leaves':7,'min_data_in_leaf':5,'seed':4},lgb.Dataset(X,label=y),num_boost_round=15)
    return model,X,y

def test_mapping():
    indices=np.concatenate(list(VIEWS.values()))
    assert len(indices)==DIM and len(np.unique(indices))==DIM

def test_tadr_zero_and_distributed():
    assert tadr(np.zeros((1,DIM)))[0]==0
    phi=np.zeros((1,DIM)); phi[0,:4]=[1,-1,1,-1]
    assert tadr(phi)[0]==.25

def test_threshold_ties():
    for s in (np.arange(2000),np.ones(2000),np.r_[np.zeros(1998),[1,1]],np.arange(37)):
        tau=threshold(s,.01)
        assert np.mean(s>tau)<=.01
    assert d0_budget(np.ones(200),.01).sum()==2

def test_additivity_strip_reproducible(fixture_model):
    model,X,_=fixture_model
    phi=contributions(model,X[:3]); assert phi.shape==(3,DIM)
    a=strip(model,X[:2],X[10:30]); b=strip(model,X[:2][::-1],X[10:30])[::-1]
    np.testing.assert_array_equal(a,b)
    assert np.all((a>=0)&(a<=1))

def test_blind_api_and_m5_direction(fixture_model):
    model,X,_=fixture_model; detector=Detector(model,X[:40])
    assert not set(inspect.signature(Detector).parameters)&{'labels','manifest','clean_model'}
    ss,details=detector.components(X[:5],include_strip=False)
    assert details['m5_sensitive_branch']=='unsupported_group_only'
    assert np.all(ss['M5_limited'][details['malware_probability']>=.5]==0)

def test_bundle_roundtrip_and_corruption(fixture_model,tmp_path):
    model,X,_=fixture_model; main=tmp_path/'m.txt'; model.save_model(str(main))
    detector=Detector(model,X[:40]).fit(X[40:80]); bundle=tmp_path/'bundle'
    detector.save(bundle,main); loaded=Detector.load(bundle)
    a=detector.predict(X[80:83]); b=loaded.predict(X[80:83])
    for k in a[0]: np.testing.assert_array_equal(a[0][k],b[0][k])
    with (bundle/'main.txt').open('a') as f: f.write('\ncorrupt')
    with pytest.raises(ValueError,match='checksum'): Detector.load(bundle)

def test_poison_keeps_labels(fixture_model):
    _,X,y=fixture_model; trigger=Trigger('concentrated',[612,613],[8,9],'feasible')
    xp,ids=poison(X,y,trigger,.1,17)
    assert np.all(y[ids]==0) and len(ids)==16
    assert np.all(xp[ids,612]==8)
    other=np.setdiff1d(np.arange(len(X)),ids); np.testing.assert_array_equal(xp[other],X[other])

def test_feasible_cross_fails(fixture_model):
    model,X,y=fixture_model
    with pytest.raises(ValueError,match='No silent relaxation'): select_trigger(model,X,y,'cross',17,'feasible')

def test_vectorizer_real_against_upstream():
    root=Path(__file__).resolve().parents[1]
    raw=root/'ember2018/test_features.jsonl'
    if not raw.exists(): pytest.skip('Local real EMBER absent; CI uses synthetic core fixtures')
    with raw.open(encoding='utf8') as f: rows=[json.loads(next(f)) for _ in range(32)]
    v=Vectorizer(); expected=np.stack([v.transform(r) for r in rows]); actual=v.transform_batch(rows)
    np.testing.assert_allclose(actual,expected,rtol=0,atol=0)
    assert actual.shape==(32,DIM)

def test_paired_metrics():
    a=np.array([.9,.8,.7]); b=np.array([.1,.2,.3])
    assert auc(a,b)==1
    assert paired_bootstrap(a,b,a,b,50)['ci95']==[0,0]
    lo,hi=wilson(0,100); assert lo==0 and .03<hi<.04
