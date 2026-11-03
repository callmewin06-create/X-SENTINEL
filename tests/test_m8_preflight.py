import csv
import importlib.util
import json
from pathlib import Path
import struct
import pytest

spec = importlib.util.spec_from_file_location('preflight', Path(__file__).parents[1]/'scripts/m8_vm/m8_preflight.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


def fixture(path, x64=False):
    b = bytearray(512); b[:2] = b'MZ'; struct.pack_into('<I', b, 0x3c, 128)
    b[128:132] = b'PE\0\0'
    struct.pack_into('<H', b, 132, 0x8664 if x64 else 0x14c)
    size = 240 if x64 else 224
    struct.pack_into('<H', b, 148, size)
    struct.pack_into('<H', b, 152, 0x20b if x64 else 0x10b)
    struct.pack_into('<I', b, 152+(108 if x64 else 92), 16)
    path.write_bytes(b)


def test_inventory_keeps_invalid_files_and_never_infers_functionality(tmp_path):
    samples = tmp_path/'samples'; samples.mkdir()
    fixture(samples/'native.EXE', True); fixture(samples/'hash_without_extension')
    (samples/'broken.exe').write_bytes(b'MZ')
    out = tmp_path/'report'
    assert module.run(samples, out) == 2
    with (out/'binary_inventory.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3
    assert {r['architecture'] for r in rows} == {'', 'x86', 'x64'}
    assert sum(r['static_status'] == 'ERROR' for r in rows) == 1
    assert all(r['functional_status'] == 'NOT_RUN' and r['label'] == 'UNVERIFIED' for r in rows)
    assert json.loads((out/'environment.json').read_text())['sample_execution'] == 'NEVER'


def test_no_overwrite_and_no_report_in_sample_corpus(tmp_path):
    samples = tmp_path/'samples'; samples.mkdir(); fixture(samples/'ok.exe')
    with pytest.raises(ValueError): module.run(samples, samples/'report')
    out = tmp_path/'report'; assert module.run(samples, out) == 0
    with pytest.raises(FileExistsError): module.run(samples, out)


def test_empty_corpus_not_success(tmp_path):
    samples = tmp_path/'samples'; samples.mkdir()
    assert module.run(samples, tmp_path/'report') == 2


def test_symlink_not_followed(tmp_path):
    samples = tmp_path/'samples'; samples.mkdir(); target = tmp_path/'target.exe'; fixture(target)
    link = samples/'link.exe'
    try: link.symlink_to(target)
    except OSError: pytest.skip('Symlinks unavailable for this account')
    row = module.inspect_file(link, samples)
    assert row['static_status'] == 'SKIPPED_NONREGULAR' and not row['sha256']
