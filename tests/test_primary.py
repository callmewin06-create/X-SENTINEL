"""Primary protocol checks use synthetic models/vectors, not research runs."""
import json
from pathlib import Path
import numpy as np
import lightgbm as lgb
import pytest
from sklearn.feature_extraction import FeatureHasher

from xsentinel.schema import get_schema,SCHEMA_VERSION,V2_PRIMARY,V3_PRIMARY
from xsentinel.data.vectorizer import Vectorizer
from xsentinel.data.v3_raw import raw_module
from xsentinel.data.protocol import primary_partitions,freeze_primary_splits
from xsentinel.attacks.screen import screen_primary,lock_common_selector
from xsentinel.baselines.scores import strip,contributions
from xsentinel.detection.calibration import threshold,rank
from xsentinel.detection.components import primary_components,PRIMARY_PROTOCOL,LEGACY_PROTOCOL
from xsentinel.detection.detector import Detector
from xsentinel.attacks.primary import VectorTrigger,poison_primary
from xsentinel.evaluation.primary import calibrate_pair,evaluate_pair,outcome_metrics
from xsentinel.attacks.selectors import signed_conditioned,SEVERI_SOURCE_SHA256


@pytest.mark.parametrize('version,dim',[ (SCHEMA_VERSION,2381),(V2_PRIMARY,2381),(V3_PRIMARY,2568)])
def test_schema_coverage_and_names(version,dim):
    s=get_schema(version)
    assert s.dim==dim and len(set(s.names))==dim
    np.testing.assert_array_equal(np.sort(np.concatenate(list(s.views.values()))),np.arange(dim))
    assert len(s.fingerprint)==64
    assert s.names[s.restricted[-1]].startswith('section.')
    if version==V2_PRIMARY:
        assert len(s.restricted)==17 and s.names[684]=='header.optional.minor_subsystem_version'
    elif version==V3_PRIMARY:
        assert s.names[0]=='general.size' and s.view_labels[1]=='metadata'
        assert s.names[710]=='header.optional.minor_subsystem_version'
        assert s.names[994]=='imports.num_imports'
        assert s.names[2276]=='exports.hashed_vector_length'
        assert all(s.view_labels[j]=='structural' for j in s.restricted)


def v3_record():
    mod=raw_module(); extractor=mod.PEFeatureExtractor()
    raw={f.name:f.raw_features(b'MZ example payload',None) for f in extractor.features}
    raw['general'].update(is_pe=1,size=12345,entropy=4.25,start_bytes=[77,90,0,0])
    raw['strings']['string_counts']={'url':7,'registry_key':3}
    h=mod.HeaderFileInfo()
    raw['header']={'coff':{k:0 for k in ('timestamp','number_of_sections','number_of_symbols','sizeof_optional_header','pointer_to_symbol_table')},
        'optional':{k:0 for k in ('major_image_version','minor_image_version','major_linker_version','minor_linker_version',
        'major_operating_system_version','minor_operating_system_version','major_subsystem_version','minor_subsystem_version',
        'sizeof_code','sizeof_headers','sizeof_image','sizeof_initialized_data','sizeof_uninitialized_data','sizeof_stack_reserve',
        'sizeof_stack_commit','sizeof_heap_reserve','sizeof_heap_commit','address_of_entrypoint','base_of_code','image_base',
        'section_alignment','checksum','number_of_rvas_and_sizes')},'dos':{k:0 for k in h._dos_members}}
    raw['header']['coff'].update(timestamp=123,machine='IMAGE_FILE_MACHINE_I386',characteristics=[])
    raw['header']['optional'].update(minor_subsystem_version=42,subsystem='IMAGE_SUBSYSTEM_WINDOWS_GUI',dll_characteristics=[])
    raw['imports']={'KERNEL32.dll':['CreateFileA','CloseHandle']}
    raw['exports']=['export_test']
    raw['richheader']=[1,2,3,4]
    raw['pefilewarnings']=[next(iter(mod.PEFormatWarnings(Path(mod.__file__).with_name('pefile_warnings.txt')).warning_ids))]
    return raw


def test_v3_raw_mapping_wrappers_hashes_and_no_label_leakage():
    s=get_schema(V3_PRIMARY); v=Vectorizer(s); raw=v3_record()
    x=v.transform(raw)
    assert x.shape==(2568,)
    assert x[0]==12345 and x[1]==4.25 and x[2]==1 and x[696]==123 and x[710]==42
    assert x[s.names.index('strings.regex_count.url')]==7
    assert x[s.names.index('strings.regex_count.registry_key')]==3
    assert x[994]==2 and x[995]==1 and x[2276]==128 # preserve pinned upstream behavior
    expected=FeatureHasher(1024,input_type='string',alternate_sign=False).transform([
        ['kernel32.dll:CreateFileA','kernel32.dll:CloseHandle']]).toarray()[0]
    np.testing.assert_array_equal(x[1252:2276],expected)
    np.testing.assert_array_equal(v.transform({'features':raw,'label':1,'family':'unused','av_ratio':1}),x)
    np.testing.assert_array_equal(v.transform_batch([raw,raw]),np.stack([x,x]))
    with pytest.raises((KeyError,ValueError)): Vectorizer(V2_PRIMARY).transform(raw)


@pytest.mark.parametrize('version',[V2_PRIMARY,V3_PRIMARY])
def test_primary_formulas_distinguish_mass_net_and_probability_gap(version):
    s=get_schema(version); phi=np.zeros((3,s.dim))
    st,bh,md=[s.views[v][0] for v in ('structural','behavioral','metadata')]
    phi[0,[st,bh,md]]=[-2,1,-1]
    phi[1,[st,bh,md]]=[-1,1,-1]
    ss,shares,net=primary_components(phi,[.2,.7,.3],s,[.6,.6,.9])
    np.testing.assert_allclose(ss['M3_view_mass'],[.5,1/3,0])
    np.testing.assert_allclose(ss['M4_shap_behavioral_conflict'],[.2,.1,0])
    np.testing.assert_allclose(ss['M4_prob_gap'],[.4,0,.6])
    assert not np.isclose(ss['M4_prob_gap'][0],(1-.2)*.6)
    assert net['behavioral'][0]==1


class ProbabilityFixture:
    def __init__(self,dim): self.dim=dim
    def num_feature(self): return self.dim
    def predict(self,x,**kwargs): return np.resize([.01,.99],len(x))


def test_strip_is_mean_entropy_not_entropy_of_mean():
    s=get_schema(V3_PRIMARY); x=np.zeros((1,s.dim)); ref=np.ones((2,s.dim))
    value=strip(ProbabilityFixture(s.dim),x,ref,n=50,schema=s)[0]
    h=-.01*np.log2(.01)-.99*np.log2(.99)
    assert value==pytest.approx(1-h)
    assert value>.9 # entropy(mean([.01,.99])) would give score zero


@pytest.fixture(params=[V2_PRIMARY,V3_PRIMARY])
def models(request):
    s=get_schema(request.param); rng=np.random.default_rng(91)
    X=rng.normal(size=(120,s.dim)).astype('float32')
    y=(X[:,s.views['behavioral'][0]]+X[:,s.views['metadata'][0]]>0).astype(int)
    params={'objective':'binary','num_threads':2,'verbosity':-1,'min_data_in_leaf':3,'num_leaves':5,'seed':91}
    main=lgb.train(params,lgb.Dataset(X,label=y),num_boost_round=5)
    views={v:lgb.train(params,lgb.Dataset(X[:,idx],label=y),num_boost_round=5) for v,idx in s.views.items()}
    return s,main,views,X


def test_primary_pair_reduced_resources_and_separate_tau(models):
    s,main,views,X=models
    r,f=calibrate_pair(main,X[:15],X[15:35],views,{'seed':91},s)
    assert not r.views and not r.enable_m5 and not f.enable_m5
    rs,rd=r.scores(X[35:39]); fs,fd=f.scores(X[35:39])
    assert 'M4_prob_gap' not in rs and 'X_primary_full' not in rs
    assert not any('M5' in k for k in rs)
    for k in rs:
        np.testing.assert_array_equal(rs[k],fs[k])
        assert r.thresholds[k]==f.thresholds[k]
    np.testing.assert_allclose(rs['X_primary_reduced'],.5*rank(r.rank_reference['M3_view_mass'],rs['M3_view_mass'])+
                               .5*rank(r.rank_reference['M4_shap_behavioral_conflict'],rs['M4_shap_behavioral_conflict']))
    assert 'X_primary_full' in f.thresholds
    with pytest.raises(ValueError,match='overlap'): Detector(main,X[:15],schema=s).fit(X[10:20])
    with pytest.raises(ValueError,match='all three'): Detector(main,X[:15],{'behavioral':views['behavioral']},schema=s)


def test_strip_order_chunk_and_repeat_invariance_both_schemas(models):
    s,m,_,X=models
    a=strip(m,X[:5],X[10:20],schema=s)
    np.testing.assert_array_equal(a,strip(m,X[:5][::-1],X[10:20],schema=s)[::-1])
    np.testing.assert_array_equal(a,np.concatenate([strip(m,X[:2],X[10:20],schema=s),strip(m,X[2:5],X[10:20],schema=s)]))
    np.testing.assert_array_equal(a,strip(m,X[:5],X[10:20],schema=s))
    assert contributions(m,X[:3],schema=s).shape==(3,s.dim)
    other=V3_PRIMARY if s.version==V2_PRIMARY else V2_PRIMARY
    with pytest.raises(ValueError): contributions(m,np.zeros((1,get_schema(other).dim)),schema=other)


def test_versioned_bundle_roundtrip_schema_dataset_and_method_checks(models,tmp_path):
    s,m,views,X=models; main=tmp_path/'main.txt'; m.save_model(str(main))
    paths={}
    for v,model in views.items():
        paths[v]=tmp_path/(v+'.txt'); model.save_model(str(paths[v]))
    _,d=calibrate_pair(m,X[:15],X[15:35],views,{'seed':91},s)
    dest=tmp_path/'bundle'; d.save(dest,main,paths); loaded=Detector.load(dest,expected_schema=s,expected_dataset=s.dataset)
    for k,v in d.predict(X[35:38])[0].items(): np.testing.assert_array_equal(v,loaded.predict(X[35:38])[0][k])
    assert loaded.calibration_fp_count==d.calibration_fp_count
    with pytest.raises(FileExistsError): d.save(dest,main,paths)
    with pytest.raises(ValueError,match='dataset'): Detector.load(dest,expected_dataset='wrong')
    state=json.loads((dest/'bundle.json').read_text()); state['schema_sha256']='bad'
    (dest/'bundle.json').write_text(json.dumps(state))
    with pytest.raises(ValueError,match='fingerprint'): Detector.load(dest)


def test_archived_bundle_retains_legacy_gate_and_scores():
    p=Path('outputs/pilot/seed_17/concentrated_0.01/bundle')
    if not p.exists(): pytest.skip('Archived bundle absent')
    d=Detector.load(p); assert d.protocol==LEGACY_PROTOCOL and d.enable_m5
    ss,detail=d.scores(d.reference[:2])
    np.testing.assert_array_equal(ss['M4_full'],(1-detail['malware_probability'])*detail['view_predictions']['behavioral'])
    assert 'X_full' in ss and 'X_primary_full' not in ss


def test_primary_trigger_geometry_denominator_and_mismatch():
    s=get_schema(V2_PRIMARY)
    idx=(616,943,512); trigger=VectorTrigger('cross_3view_stress','vector_stress',s.version,s.fingerprint,idx,(5,6,7))
    assert trigger.validate(s)=={'structural':1,'behavioral':1,'metadata':1}
    X=np.zeros((20,s.dim)); y=np.r_[np.zeros(10),np.ones(10)]
    a,ai,am=poison_primary(X,y,trigger,.2,17,denominator='all_fit',schema=s)
    b,bi,bm=poison_primary(X,y,trigger,.2,17,denominator='benign_fit',schema=s)
    assert len(ai)==4 and len(bi)==2 and np.all(y[ai]==0) and am['rate_of_benign']==.4
    assert not X.any(); np.testing.assert_array_equal(a[np.ix_(ai,idx)],np.tile([5,6,7],(4,1)))
    with pytest.raises(ValueError,match='schema'): trigger.apply(np.zeros((1,2568)),V3_PRIMARY)
    bad=VectorTrigger('cross_3view_stress','vector_stress',s.version,s.fingerprint,(616,512),(1,2))
    with pytest.raises(ValueError,match='all three'): bad.validate(s)
    restricted=VectorTrigger('spread_structural','feature_restricted',s.version,s.fingerprint,(617,),(1,))
    with pytest.raises(ValueError,match='whitelist'): restricted.validate(s)


def test_primary_partitions_train_reference_calibration_seen_and_test_boundary():
    yt=np.r_[np.zeros(80),np.ones(80)]; yv=np.r_[np.zeros(20),np.ones(20)]
    it=np.array([f'{i:064x}' for i in range(160)]); iv=np.array([f'{i:064x}' for i in range(160,200)])
    sizes={'fit':40,'selection':10,'development':10,'confirmation':10,'reference':5,'calibration':10,'final':20}
    p=primary_partitions(yt,it,yv,iv,sizes,17,seen_ids=(it[0],iv[0]))
    train_idx=np.concatenate([p[k] for k in sizes if k!='final'])
    assert len(set(train_idx))==len(train_idx) and 0 not in train_idx and 0 not in p['final']
    assert not yt[p['reference']].any() and not yt[p['calibration']].any()
    assert yv[p['final']].sum()==10
    with pytest.raises(ValueError,match='overlap'): primary_partitions(yt,it,yv,it[:40],sizes,17)


def test_outcome_keeps_eligible_denominator_and_flags_only_successful():
    r=outcome_metrics({'X':np.array([1.,0,1,0])},{'X':.5},{'X':np.array([0.,1])},
                      [.9,.9,.9,.1],[.1,.1,.9,.1],[.9,.1,.9,.1],.5)
    assert r['n_eligible']==3 and r['n_successful_eligible']==2
    assert r['asr_eligible']['rate']==pytest.approx(2/3)
    assert r['methods']['X']['post_defense_asr']['n']==3
    assert r['methods']['X']['post_defense_asr']['count']==1
    assert r['methods']['X']['recall_successful_eligible']['rate']==.5
    empty=outcome_metrics({'X':np.zeros(2)},{'X':0},{'X':np.zeros(2)},[.1,.1],[.1,.1],[.1,.1],.5)
    assert empty['asr_eligible']['rate'] is None


def test_paired_evaluator_both_datasets(models):
    s,m,views,X=models; r,f=calibrate_pair(m,X[:15],X[15:35],views,{'seed':91},s)
    xt=X[45:55].copy(); xt[:,s.views['metadata'][0]]=3
    result=evaluate_pair(r,f,m,X[35:45],X[45:55],xt,[f'b{i}' for i in range(10)],
                         [f'm{i}' for i in range(10)],bootstrap_repeats=20)
    assert result['dataset']==s.dataset
    assert result['results']['reduced']['n_eligible']==result['results']['full']['n_eligible']
    assert result['results']['full']['methods']['X_primary_full']['post_defense_asr']['n']==result['results']['full']['n_eligible']
    with pytest.raises(ValueError,match='source IDs'): evaluate_pair(r,f,m,X[35:45],X[45:55],xt,
        ['duplicate']*10,[f'm{i}' for i in range(10)],bootstrap_repeats=20)


def test_threshold_small_calibration_ties_and_invalid_rank():
    for scores in (np.zeros(20),np.r_[np.zeros(19),1],np.arange(2000),np.r_[np.zeros(1998),1,1]):
        tau=threshold(scores,.01); assert np.sum(scores>tau)<=int(len(scores)*.01)
    for ref in ([],[np.nan],[[1,2]]):
        with pytest.raises(ValueError): rank(ref,[1])


def test_signed_conditioned_against_pinned_author_class():
    import ast
    import hashlib
    import pandas as pd
    path=Path('docs/upstream/severi_feature_selectors.py')
    assert hashlib.sha256(path.read_bytes()).hexdigest()==SEVERI_SOURCE_SHA256
    node=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='CombinedShapSelector')
    namespace={'np':np}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
    rng=np.random.default_rng(281)
    for _ in range(8):
        X=rng.integers(0,4,size=(35,7)).astype('float32'); phi=rng.normal(size=X.shape)
        author=namespace['CombinedShapSelector'](pd.DataFrame(phi),'combined_shap',fixed_features=[0,2,3,5,6])
        author.X=X
        expected_i,expected_v=author.get_feature_values(4)
        actual_i,actual_v,trace=signed_conditioned(X,phi,[0,2,3,5,6],4)
        assert actual_i==expected_i; np.testing.assert_array_equal(actual_v,expected_v)
        assert all(t['pool_rows_after']<=t['pool_rows_before'] for t in trace)


def test_signed_conditioned_quota_and_unsupported_pool():
    X=np.array([[0,0,1],[1,0,0],[1,1,0]],dtype='float32')
    phi=np.array([[-3,1,-1],[-1,-2,-2],[-1,-3,-2]],dtype=float)
    i,v,trace=signed_conditioned(X,phi,[0,1,2],2,('a','a','b'),{'a':1,'b':1})
    assert len(set(i))==2 and sum(j<2 for j in i)==1
    with pytest.raises(ValueError,match='Insufficient'): signed_conditioned(X,phi,[0],2)


def test_primary_screen_strict_stealth_and_common_selector_failure_accounting():
    rules={'min_eligible':2,'min_asr':.5,'min_paired_gain':.2,'strict_max_accuracy_drop':.005}
    r=screen_primary([.1,.1,.9,.9],[.1,.1,.9,.9],[.9,.9],[.1,.1],[0,0,1,1],rules)
    assert r['strong_and_stealth'] and r['paired_gain']==1
    exact_loss=screen_primary([.1,.1,.9,.9],[.1,.9,.9,.9],[.9,.9],[.1,.1],[0,0,1,1],
        dict(rules,strict_max_accuracy_drop=.25))
    assert not exact_loss['stealth'] # strict '<', not '<='
    cells=[('EMBER2018','cross',.01,17),('EMBER2024','cross',.01,17)]
    rows=[]
    for selector in ('legacy_rare','signed_shap_conditioned'):
        for dataset,family,rate,seed in cells:
            rows.append({'dataset':dataset,'family':family,'rate':rate,'seed':seed,'selector':selector,
                'phase':'development','status':'complete','strong_and_stealth':True,'paired_gain':.4})
    assert lock_common_selector(rows,cells)['chosen_selector']=='signed_shap_conditioned'
    rows[0].update(status='failed',paired_gain=None,strong_and_stealth=False)
    result=lock_common_selector(rows,cells)
    assert result['summaries']['legacy_rare']['failed_or_unsupported']==1
    with pytest.raises(ValueError,match='Incomplete'): lock_common_selector(rows[:-1],cells)
    rows[0]['phase']='confirmation'
    with pytest.raises(ValueError,match='development'): lock_common_selector(rows,cells)


def test_primary_split_freeze_reuses_arrays_and_preserves_source(tmp_path):
    from xsentinel.utils import write_json,sha256
    source=tmp_path/'source'; source.mkdir(); out=tmp_path/'primary'
    yt=np.r_[np.zeros(80),np.ones(80)]; yv=np.r_[np.zeros(20),np.ones(20)]
    for partition,y,start in (('train',yt,0),('test',yv,160)):
        np.save(source/f'X_{partition}.npy',np.zeros((len(y),2381),dtype='float32'))
        np.save(source/f'y_{partition}.npy',y.astype('int8'))
        np.save(source/f'ids_{partition}.npy',np.array([f'{i:064x}' for i in range(start,start+len(y))],dtype='S64'))
    hashes={p.name:sha256(p) for p in source.glob('*.npy')}
    write_json(source/'dataset.json',{'schema':SCHEMA_VERSION,'array_sha256':hashes})
    sizes={'fit':40,'selection':10,'development':10,'confirmation':10,'reference':5,'calibration':10,'final':20}
    freeze_primary_splits(source,out,V2_PRIMARY,sizes,17)
    assert (out/'roles.npz').exists() and not list(out.glob('X_*.npy'))
    assert hashes=={p.name:sha256(p) for p in source.glob('*.npy')}
    with pytest.raises(FileExistsError): freeze_primary_splits(source,out,V2_PRIMARY,sizes,17)
