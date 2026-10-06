import json
from pathlib import Path
import numpy as np
import pytest
from xsentinel.data.prepare import prepare,make_splits,load_data
from xsentinel.data.pe import verify_pe

def test_pe_verification_rejects_invalid():
    for data in (b'',b'MZ'+b'\0'*100,b'not an executable'):
        with pytest.raises(ValueError): verify_pe(data)

def test_streaming_duplicate_and_split_rules(tmp_path):
    # Upstream-valid raw records can be drawn from local data without using their
    # research labels inside a detector. This validates actual streaming wiring.
    raw=Path(__file__).resolve().parents[1]/'data/ember2018/test_features.jsonl'
    if not raw.exists(): pytest.skip('Real raw dataset unavailable')
    with raw.open(encoding='utf8') as f: rows=[json.loads(next(f)) for _ in range(30)]
    source=tmp_path/'source'; source.mkdir()
    for i in range(6):
        (source/f'train_features_{i}.jsonl').write_text(json.dumps(rows[i])+'\n',encoding='utf8')
    (source/'test_features.jsonl').write_text('\n'.join(json.dumps(r) for r in rows[6:]),encoding='utf8')
    output=tmp_path/'out'; info=prepare(source,output)
    assert info['counts']['train']==6
    splits=make_splits(output,2,3)
    indices=np.concatenate(list(splits.values()))
    assert len(indices)==24 and len(np.unique(indices))==24
    with pytest.raises(FileExistsError): make_splits(output,2,3)
    (source/'test_features.jsonl').write_text(json.dumps(rows[0])+'\n',encoding='utf8')
    with pytest.raises(ValueError,match='Duplicate SHA256'): prepare(source,tmp_path/'duplicate')

def test_dashboard_real_bundle():
    bundle=Path('outputs/pilot/seed_17/concentrated_0.01/bundle')
    if not bundle.exists(): pytest.skip('Pilot bundle not present in CI')
    from streamlit.testing.v1 import AppTest
    a=AppTest.from_file('dashboard/app.py').run(timeout=30)
    assert not a.exception and len(a.metric)==3
    a.sidebar.text_input[0].set_value('missing_bundle_for_test').run(timeout=30)
    assert not a.exception and 'Not ready' in a.warning[0].value
