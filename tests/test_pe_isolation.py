"""Actual child-process lifecycle checks using only owned benign/synthetic data."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import pytest

from xsentinel.data import pe_isolation as module
from xsentinel.schema import V2_PRIMARY, V3_PRIMARY


def fixture_bytes():
    path = Path('output/demo_2026_10_20/benign/ReviewedBenignFixture.exe')
    if not path.exists():
        pytest.skip('Owned fixture absent')
    return path.read_bytes()


@pytest.mark.parametrize('schema', [V2_PRIMARY, V3_PRIMARY])
def test_disposable_worker_matches_direct_extraction(schema):
    from xsentinel.data.pe import extract_pe
    from xsentinel.data.pe_v3 import extract_pe_v3
    data = fixture_bytes()
    expected, _ = (extract_pe if schema == V2_PRIMARY else extract_pe_v3)(data)
    actual, provenance = module.extract_pe_isolated(data, schema)
    np.testing.assert_array_equal(actual, expected)
    assert provenance['process_separation'] == module.VERSION
    assert provenance['execution'] == 'never executed'


def replace_child(monkeypatch, code):
    original = subprocess.Popen
    processes = []
    def spawn(command, **kwargs):
        process = original([sys.executable, '-c', code], **kwargs)
        processes.append(process)
        return process
    monkeypatch.setattr(module.subprocess, 'Popen', spawn)
    return processes


def test_timeout_kills_child_and_releases_slot(monkeypatch):
    with monkeypatch.context() as context:
        children = replace_child(context, 'import time; time.sleep(30)')
        started = time.perf_counter()
        with pytest.raises(module.ExtractionError) as error:
            module.extract_pe_isolated(fixture_bytes(), V2_PRIMARY, timeout=.15)
        assert error.value.code == 'timeout'
        assert time.perf_counter() - started < 2.5
        assert children[0].poll() is not None
    # Recovery uses the real worker, not a fake scoring result.
    assert module.extract_pe_isolated(fixture_bytes(), V2_PRIMARY)[0].shape == (2381,)


def test_crash_and_invalid_response_do_not_create_vectors(monkeypatch):
    for code, expected in [('import os; os._exit(7)', 'worker_crashed'),
                           ('print("{}")', 'invalid_output')]:
        with monkeypatch.context() as context:
            children = replace_child(context, code)
            with pytest.raises(module.ExtractionError) as error:
                module.extract_pe_isolated(fixture_bytes(), V2_PRIMARY)
            assert error.value.code == expected
            assert children[0].poll() is not None


def test_busy_and_invalid_header_do_not_launch_child(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Unexpected child')
    monkeypatch.setattr(module.subprocess, 'Popen', forbidden)
    assert module._SLOT.acquire(blocking=False)
    try:
        with pytest.raises(module.ExtractionError) as error:
            module.extract_pe_isolated(fixture_bytes(), V2_PRIMARY)
        assert error.value.code == 'busy'
    finally:
        module._SLOT.release()
    with pytest.raises(module.ExtractionError) as error:
        module.extract_pe_isolated(b'harmless text', V2_PRIMARY)
    assert error.value.code == 'invalid_header'


@pytest.mark.parametrize('value', ['nan', 'inf', '0', '-1', '301', 'bad'])
def test_invalid_config_cannot_disable_deadline(monkeypatch, value):
    monkeypatch.setenv('XS_PE_TIMEOUT_SECONDS', value)
    with pytest.raises(ValueError):
        module.timeout_seconds()


def test_failed_retry_removes_previous_result(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from xsentinel.service import scoring
    monkeypatch.delenv('XS_API_BASE_URL', raising=False)
    app = AppTest.from_file('dashboard/app.py').run(timeout=60)
    app.radio(key='mode_Phân tích').set_value('Dùng mẫu demo').run(timeout=60)
    app.button(key='analyze').click().run(timeout=60)
    assert not app.exception and 'analysis' in app.session_state
    def fail(*args, **kwargs):
        raise module.ExtractionError('timeout', 'synthetic failure')
    monkeypatch.setattr(scoring, 'score_input', fail)
    app.button(key='analyze').click().run(timeout=60)
    assert not app.exception and 'analysis' not in app.session_state
    assert any('quá thời hạn' in item.value for item in app.error)
