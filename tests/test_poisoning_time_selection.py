import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('poison_search', Path(__file__).parents[1]/'scripts/run_poisoning_time_search.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def row(i, asr, vmc, valid=True):
    return {'candidate': i, 'screen': {'strong_and_stealth': valid, 'asr': {'rate': asr}, 'paired_gain': .3}, 'mean_vmc_eligible': vmc}

def test_objective_changes_selection_without_accepting_invalid_attack():
    rows = [row(0, .9, .8), row(1, .8, .4), row(2, 1, .1, False)]
    assert module.choose(rows, 'asr_only')['selected'] == 0
    assert module.choose(rows, 'vmc_aware')['selected'] == 1

def test_no_valid_attack_is_not_reported_as_success():
    assert module.choose([row(0, .9, .1, False)], 'vmc_aware')['selected'] is None

def test_unknown_objective_rejected():
    with pytest.raises(ValueError):
        module.choose([row(0, .8, .4)], 'unknown')
