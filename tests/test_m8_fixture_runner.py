import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('fixture_runner', Path(__file__).parents[1]/'scripts/m8_vm/run_c2_fixture_functionality.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

def package(tmp_path, monkeypatch):
    base=tmp_path/'package';base.mkdir()
    script=base/'run_functionality.py';script.write_text('inert test placeholder')
    variants=[]
    for fixture in ['native','managed']:
        for variant in ['original','timestamp_only','sections_only','full_c2']:
            path=base/f'{fixture}_{variant}.exe'
            # Inert bytes, not an actual PE or executable test payload.
            path.write_bytes(f'{fixture}/{variant}'.encode())
            variants.append({'fixture':fixture,'variant':variant,'path':path.name,'sha256':runner.sha(path)})
    manifest=base/'manifest.json';manifest.write_text(json.dumps({'variants':variants}))
    monkeypatch.setattr(runner,'__file__',str(script))
    monkeypatch.setattr(runner,'EXPECTED_MANIFEST_SHA256',runner.sha(manifest))
    monkeypatch.setattr(runner.shutil,'which',lambda name:None)
    monkeypatch.setattr(runner.platform,'platform',lambda:'TEST_NO_RUNTIME')
    def forbidden(*args,**kwargs): raise AssertionError('No subprocess should be invoked')
    monkeypatch.setattr(runner.subprocess,'run',forbidden)
    return base

def test_missing_runtime_never_becomes_functional_pass(tmp_path,monkeypatch):
    package(tmp_path,monkeypatch)
    output=tmp_path/'results'
    monkeypatch.setattr(runner.sys,'argv',['runner','--runtime','mono','--output',str(output),'--ack-controlled-vm'])
    assert runner.main()==1
    result=json.loads((output/'summary.json').read_text())
    assert result['counts']=={'BLOCKED_ENV':20}
    assert not any(r['bounded_function_preserved'] for r in result['paired_checks'])

def test_binary_tamper_stops_before_any_runtime(tmp_path,monkeypatch):
    base=package(tmp_path,monkeypatch)
    (base/'native_full_c2.exe').write_bytes(b'changed')
    monkeypatch.setattr(runner.sys,'argv',['runner','--runtime','mono','--output',str(tmp_path/'results'),'--ack-controlled-vm'])
    with pytest.raises(ValueError,match='bytes differ'):
        runner.main()
