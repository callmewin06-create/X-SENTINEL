import hashlib
import json
import importlib.util
from pathlib import Path
import numpy as np
import pytest
from xsentinel.revision.jstis_gate import inventory,verify_global_lock,file_hash,DATASETS,SEEDS
from xsentinel.experiment import train
from xsentinel.schema import V2_PRIMARY


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding='utf8')


def fixture_matrix(root):
    for dataset in DATASETS:
        for seed in SEEDS:
            cell=root/dataset/f'seed_{seed}'
            put(cell/'static_attempts.json',[{'profile':p,'selector':s} for p in ('feature_restricted','vector_stress')
                 for s in ('min_population','count_abs_shap','signed_shap_conditioned')])
            for arm in ('asr_only','vmc_aware'):
                put(cell/f'{arm}.json',{'arm':arm,'budget_completed':16,'trajectory':[{}]*16,
                    'status':'NO_VALID_ATTACK','selected':None})
            put(cell/'ATTACKS_LOCKED.json',{'status':'CELL_ATTACKS_LOCKED_NOT_EVALUATED','heldout_roles_opened':[],
                'protocol_digest':'test','artifacts':{p.name:file_hash(p) for p in cell.glob('*.json')}})


def test_no_cell_can_release_heldout_early(tmp_path):
    with pytest.raises(ValueError,match='Global held-out barrier'):
        inventory(tmp_path)
    fixture_matrix(tmp_path)
    lock=tmp_path/'GLOBAL.json';put(lock,inventory(tmp_path))
    assert verify_global_lock(tmp_path,lock)['static_attempts']==36
    cell=tmp_path/'EMBER2024/seed_43'; state=json.loads((cell/'vmc_aware.json').read_text())
    state['budget_completed']=15;put(cell/'vmc_aware.json',state)
    with pytest.raises(ValueError,match='artifact changed'):
        verify_global_lock(tmp_path,lock)


def test_native_unicode_model_paths_roundtrip(tmp_path):
    path=tmp_path/'mô hình có dấu.txt'
    X=np.zeros((12,2381),dtype=np.float32);X[:,0]=np.arange(12);y=np.arange(12)%2
    cfg={'params':{'objective':'binary','num_threads':1,'num_leaves':2,'min_data_in_leaf':1,'verbosity':-1},
         'rounds':2,'view_rounds':1}
    model=train(X,y,path,cfg,17,schema=V2_PRIMARY)
    saved=file_hash(path);loaded=train(X,y,path,cfg,17,schema=V2_PRIMARY)
    np.testing.assert_allclose(model.predict(X),loaded.predict(X))
    assert file_hash(path)==saved


@pytest.mark.parametrize('script',['materialize_jstis_evaluator.py','evaluate_jstis_followup.py'])
def test_evaluator_never_opens_arrays_before_global_barrier(tmp_path,monkeypatch,script):
    path=Path(__file__).parents[1]/'scripts'/script
    spec=importlib.util.spec_from_file_location('sealed_evaluator',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    lock=tmp_path/'global.json';put(lock,{})
    args=[script,'--attacks',str(tmp_path/'incomplete'),'--global-lock',str(lock),
          '--dataset','EMBER2018','--output',str(tmp_path/'out')]
    args+=['--manifest' if script.startswith('materialize') else '--evaluator',str(tmp_path/'sealed')]
    monkeypatch.setattr('sys.argv',args)
    def forbidden(*args,**kwargs):raise AssertionError('Heldout array opened before barrier')
    monkeypatch.setattr(np,'load',forbidden)
    with pytest.raises(ValueError,match='Global held-out barrier'):module.main()


def test_zero_success_denominator_is_na():
    path=Path(__file__).parents[1]/'scripts/evaluate_jstis_followup.py'
    spec=importlib.util.spec_from_file_location('metric_evaluator',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.counted([])=={'count':0,'n':0,'rate':None,'pointwise_cp95':None}
