import lightgbm as lgb
import numpy as np
import pytest

from xsentinel.attacks.development import (
    _screen, joint_benign_trigger, run_development, stratified_partitions,
)
from xsentinel.attacks.trigger import Trigger
from xsentinel.schema import DIM, SCHEMA_VERSION
from xsentinel.utils import read_json, sha256, write_json


def test_train_partitions_are_disjoint_balanced_and_reproducible():
    y = np.r_[np.zeros(120), np.ones(120)].astype('int8')
    sizes = {'fit': 100, 'selection': 40, 'development': 60}
    parts = stratified_partitions(y, sizes, 731)
    other = stratified_partitions(y, sizes, 731)
    all_ids = np.concatenate(list(parts.values()))
    assert len(np.unique(all_ids)) == sum(sizes.values())
    for name, indices in parts.items():
        np.testing.assert_array_equal(indices, other[name])
        assert len(indices) == sizes[name] and y[indices].sum() == sizes[name] // 2
    with pytest.raises(ValueError, match='Insufficient'):
        stratified_partitions(y, {'fit': 242}, 731)


def test_joint_trigger_is_observed_benign_tuple_and_negative():
    rng = np.random.default_rng(6)
    X = np.zeros((200, DIM), dtype='float32')
    X[:, 612:614] = rng.normal(size=(200, 2))
    y = (X[:, 612] + X[:, 613] > 0).astype('int8')
    model = lgb.train({'objective': 'binary', 'num_threads': 2, 'verbosity': -1,
                       'num_leaves': 7, 'min_data_in_leaf': 5}, lgb.Dataset(X, label=y), 15)
    trigger, diagnostics = joint_benign_trigger(
        model, X, y, Trigger('concentrated', [612, 613], [0, 0], 'feasible'), .2)
    assert np.any(np.all(X[y == 0][:, trigger.indices] == trigger.values, axis=1))
    assert diagnostics['selected_mean_joint_shap'] < 0
    assert diagnostics['selected_support'] <= diagnostics['rarity_count_cutoff']
    with pytest.raises(ValueError, match='No benign'):
        joint_benign_trigger(model, X, np.ones(len(y)), trigger, .2)


def test_screen_uses_fixed_clean_eligibility_and_direct_evasion_control():
    rules = {'malware_threshold': .5, 'min_eligible': 2, 'min_asr': .5,
             'min_paired_gain': .2, 'max_accuracy_drop': .02,
             'max_tpr_drop': .02, 'max_fpr_increase': .02}
    y = np.array([0, 0, 1, 1, 1])
    clean = np.array([.1, .2, .9, .8, .3])
    trigger = np.array([.1, .2, .1])
    result = _screen(clean, clean, trigger, trigger, y, rules)
    assert result['eligible_count'] == 2  # Third malware never enters the denominator.
    assert result['attack_asr']['count'] == 2
    assert result['paired_gain'] == 0 and not result['screen_pass']
    assert not result['screen_checks']['paired_gain_over_clean_trigger']
    improved = _screen(clean, clean, np.array([.9, .8, .1]), trigger, y, rules)
    assert improved['paired_gain'] == 1 and improved['screen_pass']
    empty = _screen(np.full(len(y), .2), clean, trigger, trigger, y, rules)
    assert empty['eligible_count'] == 0 and empty['attack_asr']['rate'] is None
    assert empty['paired_gain'] is None and not empty['screen_pass']


def test_development_runs_without_test_files_and_locks_candidates(tmp_path, monkeypatch):
    source = tmp_path/'data'; source.mkdir()
    rng = np.random.default_rng(6)
    X = np.zeros((400, DIM), dtype='float32'); X[:, 612:614] = rng.normal(size=(400, 2))
    y = (X[:, 612] + X[:, 613] > 0).astype('int8')
    for kind, values in {'X': X, 'y': y, 'ids': np.array([f'{i:064x}' for i in range(len(y))], dtype='S64')}.items():
        np.save(source/f'{kind}_train.npy', values)
    write_json(source/'dataset.json', {'schema': SCHEMA_VERSION, 'pilot': False,
        'array_sha256': {f.name: sha256(f) for f in source.glob('*.npy')}})
    config = {'name': 'test', 'seed': 17, 'split_seed': 731, 'fit_rows': 100,
              'selection_rows': 40, 'development_rows': 60, 'selection_samples': 40,
              'attack_profile': 'feasible', 'trigger': 'concentrated',
              'selectors': ['legacy_rare', 'joint_benign_rare'], 'rare_tuple_quantile': .2,
              'rates': [.1], 'rounds': 5, 'view_rounds': 5,
              'development_history': {'reuse': 'Synthetic observed development fixture'},
              'params': {'objective': 'binary', 'num_threads': 2, 'verbosity': -1,
                         'num_leaves': 5, 'min_data_in_leaf': 5},
              'screen': {'malware_threshold': .5, 'min_eligible': 1, 'min_asr': .5,
                         'min_paired_gain': .2, 'max_accuracy_drop': .02,
                         'max_tpr_drop': .02, 'max_fpr_increase': .02}}
    config_path = tmp_path/'config.json'; write_json(config_path, config)
    original_load = np.load; opened = []
    def guarded_load(path, *args, **kwargs):
        opened.append(str(path))
        assert '_test' not in str(path) and 'splits' not in str(path)
        return original_load(path, *args, **kwargs)
    monkeypatch.setattr(np, 'load', guarded_load)
    output = tmp_path/'run'; results = run_development(source, output, config_path)
    assert len(opened) == 3 and len(results) == 2
    lock = read_json(output/'candidate_lock.json')
    assert set(lock['triggers']) == set(config['selectors'])
    for result in results:
        dest = output/f"{result['selector']}_0.1"
        manifest = read_json(dest/'attack_manifest.json')
        assert manifest['candidate_lock_sha256'] == sha256(output/'candidate_lock.json')
        assert manifest['poison_count'] == 10
        assert manifest['trigger'] == lock['triggers'][result['selector']]
    assert read_json(output/'run_manifest.json')['status'] == 'complete'
    assert (output/'source_snapshot.zip').is_file() and (output/'report.md').is_file()
    assert 'Synthetic observed development fixture' in (output/'report.md').read_text()
    with pytest.raises(FileExistsError): run_development(source, output, config_path)
