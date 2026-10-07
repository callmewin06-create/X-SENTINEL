"""The operational adapter must preserve actual scientific predictions."""
import json
from pathlib import Path
import numpy as np
import pytest
from pydantic import ValidationError
from xsentinel.service.api import VectorRequest,create_app
from xsentinel.service.registry import BundleRegistry
from xsentinel.service.scoring import score_input,input_digest


def test_vector_request_rejects_nonfinite_and_extra_fields():
    args={'bundle_id':'a'*64,'features':[0.0]*2381}
    VectorRequest(**args)
    for value in (float('nan'),float('inf')):
        with pytest.raises(ValidationError):
            VectorRequest(**{**args,'features':[value]*2381})
    with pytest.raises(ValidationError):
        VectorRequest(**args,ground_truth=1)
    with pytest.raises(ValidationError):
        VectorRequest(**{**args,'bundle_id':'../bundle'})


def test_real_scoring_adapter_preserves_components_and_flags():
    registry=BundleRegistry()
    if not registry.entries: pytest.skip('Real bundles missing')
    for dataset in ('EMBER2018','EMBER2024'):
        for variant in ('reduced','full'):
            entry=next(e for e in registry.entries.values() if e['dataset']==dataset and e['variant']==variant)
            detector,_=registry.loaded(entry['id']); x=detector.reference[:1]
            scores,flags,details,_=detector.predict(x)
            output=score_input(detector,x,'X_primary_'+variant)
            assert output['malware_probability']==details['malware_probability'][0]
            assert output['backdoor_alert']==bool(flags['X_primary_'+variant][0])
            for row in output['scores']:
                assert row['Score']==scores[row['Method']][0]
                assert row['Flagged']==flags[row['Method']][0]
                assert row['Threshold']==detector.thresholds[row['Method']]
            assert not detector.enable_m5
            assert input_digest(x)==input_digest(x.astype(np.float64))
            json.dumps(output,allow_nan=False)
    with pytest.raises(KeyError): registry.entry('../data')


def test_api_readiness_failure_is_visible(monkeypatch):
    from fastapi.testclient import TestClient
    import xsentinel.service.api as api
    monkeypatch.setattr(api,'readiness',lambda engine:{'ok':False,'revision':[]})
    with TestClient(create_app(engine=object(),registry=BundleRegistry())) as client:
        assert client.get('/health').status_code==200
        assert client.get('/ready').status_code==503
        assert client.get('/v1/analyses').status_code==503


def test_imported_initial_migration_is_unchanged():
    import hashlib
    proof=json.loads(Path('docs/database/IMPORT_PROVENANCE_2026_10_07.json').read_text())
    record=next(r for r in proof['files'] if r['destination'].endswith('0001_v2_multiuser.py'))
    assert hashlib.sha256(Path(record['destination']).read_bytes()).hexdigest()==record['source_sha256']
