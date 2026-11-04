import importlib.util
from pathlib import Path
import numpy as np
import pytest
from xsentinel.schema import get_schema, V2_PRIMARY
spec = importlib.util.spec_from_file_location('targets', Path(__file__).parents[1]/'scripts/verify_m8_targets.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

def test_all_targets_must_match_and_names_are_bound_to_schema():
    schema = get_schema(V2_PRIMARY); x = np.zeros(schema.dim)
    targets = [{'index': 0, 'name': schema.names[0], 'value': 0}, {'index': 1, 'name': schema.names[1], 'value': 5}]
    assert [r['matched'] for r in module.check_targets(x, targets, schema)] == [True, False]
    targets[0]['name'] = 'incorrect'
    with pytest.raises(ValueError): module.check_targets(x, targets, schema)

def test_empty_or_duplicate_targets_cannot_pass():
    schema = get_schema(V2_PRIMARY); x = np.zeros(schema.dim)
    with pytest.raises(ValueError): module.check_targets(x, [], schema)
    target = {'index': 0, 'name': schema.names[0], 'value': 0}
    with pytest.raises(ValueError): module.check_targets(x, [target, target], schema)


def test_partial_or_altered_locked_trigger_cannot_pass():
    schema = get_schema(V2_PRIMARY)
    attack = {'trigger': {'schema_version':schema.version, 'schema_sha256':schema.fingerprint,
                          'indices':[691,626], 'values':[12,1053454528]}}
    targets = [{'index':j,'name':schema.names[j],'value':v} for j,v in zip([691,626],[12,1053454528])]
    assert len(module.locked_targets(attack,schema,targets)) == 2
    with pytest.raises(ValueError): module.locked_targets(attack,schema,targets[1:])
    changed = [dict(t) for t in targets];changed[0]['value']=1
    with pytest.raises(ValueError): module.locked_targets(attack,schema,changed)
    changed = [dict(t) for t in targets];changed[0]['atol']=99
    with pytest.raises(ValueError): module.locked_targets(attack,schema,changed)
