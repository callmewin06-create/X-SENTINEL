import ast
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from xsentinel.attacks.selectors import independent_large_abs, signed_conditioned
from xsentinel.attacks.sequential import canonical, fingerprint, ranking, run_search
from xsentinel.attacks.primary import VectorTrigger
from xsentinel.schema import get_schema, V2_PRIMARY


def source_symbols():
    # Execute only selector definitions from the locally pinned author source;
    # no imports, file I/O or multiprocessing from that upstream module.
    path=Path(__file__).parents[1]/'docs/upstream/severi_feature_selectors.py'
    names={'ShapleyFeatureSelector','HistogramBinValueSelector','CombinedShapSelector',
           '_process_one_shap_linear_combination'}
    tree=ast.parse(path.read_text(encoding='utf8'))
    nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
    scope={'np':np,'pd':pd,'collections':__import__('collections')}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),scope)
    return scope


def test_independent_matches_pinned_source_with_value_ties():
    scope=source_symbols(); rng=np.random.default_rng(17)
    X=rng.integers(0,5,(40,9)).astype(np.float32); phi=rng.normal(size=X.shape)
    # Equal rare counts, first observation is deliberately not the lowest value.
    X[:,8]=np.arange(40)[::-1]
    selector=scope['ShapleyFeatureSelector'](pd.DataFrame(phi),'shap_largest_abs',list(range(9)))
    expected=selector.get_features(4)
    for mode in ['min_population','count_abs_shap']:
        indices,values,_=independent_large_abs(X,phi,range(9),4,mode)
        assert indices==expected
        if mode=='min_population':
            val_selector=scope['HistogramBinValueSelector']('min_population',5); val_selector.X=X
            assert values==val_selector.get_feature_values(indices)
        else:
            f=scope['_process_one_shap_linear_combination']
            assert values==[float(f((q,j,X[:,j],np.abs(phi[:,j]),1.,1.))[2]) for q,j in enumerate(indices)]


def test_combined_matches_source_away_from_unspecified_feature_ties():
    scope=source_symbols(); rng=np.random.default_rng(29)
    X=rng.integers(0,3,(80,8)).astype(np.float32); phi=rng.normal(size=X.shape)
    source=scope['CombinedShapSelector'](pd.DataFrame(phi),'combined_shap',fixed_features=list(range(8)))
    source.X=X
    idx,val,_=signed_conditioned(X,phi,range(8),4)
    assert (idx,val)==source.get_feature_values(4)


def test_no_cross_dataset_value_cache_and_float_canonicalization():
    p=np.array([[1.],[2.],[2.]])
    assert independent_large_abs(p,np.ones_like(p),[0],1,'min_population')[1]==[1.]
    assert independent_large_abs(p+7,np.ones_like(p),[0],1,'min_population')[1]==[8.]
    assert fingerprint(((1,0.),(0,1.)))==fingerprint(((0,1.+1e-9),(1,-0.)))


def test_feature_and_countabs_tie_policies_are_explicit():
    scope=source_symbols();X=np.tile([2.,1.,2.,1.],(8,1)).T
    phi=np.ones_like(X)
    expected=scope['ShapleyFeatureSelector'](pd.DataFrame(phi),'shap_largest_abs',list(range(8))).get_features(3)
    indices,values,_=independent_large_abs(X,phi,range(8),3,'count_abs_shap')
    assert indices==expected and values==[1.]*3
    # Existing signed adaptation explicitly resolves feature ties by lower index.
    indices,_,_=signed_conditioned(X,np.zeros_like(X),range(8),3)
    assert indices==[0,1,2]


def test_quota_free_does_not_relax_historical_family():
    schema=get_schema(V2_PRIMARY); j=schema.views['metadata'][0]
    args=('vector_stress',schema.version,schema.fingerprint,(int(j),),(0.,))
    VectorTrigger('supplementary_noquota',*args).validate(schema)
    with pytest.raises(ValueError): VectorTrigger('cross_3view_stress',*args).validate(schema)


def metrics(asr=.8,vmc=.4,drop=.001):
    return dict(eligible=1200,asr=asr,paired_gain=.3,accuracy_drop=drop,mean_vmc=vmc)


def test_strict_accuracy_screen_and_infeasible_outcome():
    assert ranking(metrics(drop=.005),'asr_only','a')[0]==1
    out=run_search(((0,0.),),{0:[0.,1.],1:[0.,1.],2:[0.,1.]},
                   lambda t,d:metrics(drop=.02),arm='vmc_aware',seed=17,budget=3)
    assert out['status']=='NO_VALID_ATTACK' and out['selected'] is None


def test_feedback_changes_trajectory_and_budget():
    catalogue={j:[0.,1.,2.] for j in range(12)}
    count=[0]
    def evaluate(t,d):
        count[0]+=1
        return metrics(asr=.7+count[0]*.001,vmc=.1+count[0]*.01)
    a=run_search(((0,0.),(1,0.)),catalogue,evaluate,arm='asr_only',seed=43,budget=16)
    count[0]=0
    b=run_search(((0,0.),(1,0.)),catalogue,evaluate,arm='vmc_aware',seed=43,budget=16)
    assert a['budget_completed']==b['budget_completed']==16
    assert len({r['fingerprint'] for r in a['trajectory']})==16
    assert a['trajectory'][2]['parent']!=b['trajectory'][2]['parent']
    assert a['trajectory'][2]['trigger']!=b['trajectory'][2]['trigger']


def test_infrastructure_failure_not_negative_science():
    def broken(t,d): raise OSError('disk full')
    with pytest.raises(OSError,match='disk full'):
        run_search(((0,0.),),{0:[0.,1.],1:[0.,1.]},broken,arm='asr_only',seed=17)
