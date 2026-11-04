"""Re-extract target checks from original/edited PE bytes; no PE execution."""
import argparse
from pathlib import Path
import sys
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from xsentinel.data.pe import extract_pe
from xsentinel.schema import get_schema, V2_PRIMARY
from xsentinel.utils import read_json, write_json, sha256


def check_targets(vector, targets, schema):
    if not targets:
        raise ValueError('Empty trigger is not complete target matching')
    rows = []
    seen = set()
    for target in targets:
        j = target['index']
        if not isinstance(j, int) or j in seen or not 0 <= j < schema.dim:
            raise ValueError('Invalid or duplicate target index')
        seen.add(j)
        if target['name'] != schema.names[j]:
            raise ValueError('Canonical feature name/index mismatch')
        tolerance = float(target.get('atol', 0))
        expected = float(np.float32(target['value']))
        if tolerance < 0 or not np.isfinite([expected, tolerance]).all():
            raise ValueError('Invalid predeclared tolerance/target')
        actual = float(vector[j])
        rows.append(dict(index=j, name=target['name'], expected=expected, actual=actual,
                         atol=tolerance, matched=bool(abs(actual-expected) <= tolerance)))
    return rows


def locked_targets(attack, schema, declared):
    """Require the whole trigger, rather than any convenient subset of it."""
    trigger = attack['trigger']
    if trigger['schema_version'] != schema.version or trigger['schema_sha256'] != schema.fingerprint:
        raise ValueError('Attack/schema fingerprint mismatch')
    indices, values = trigger['indices'], trigger['values']
    if not indices or len(indices) != len(values) or len(set(indices)) != len(indices):
        raise ValueError('Invalid locked trigger')
    expected = [{'index': j, 'name': schema.names[j], 'value': float(np.float32(v)), 'atol': 0}
                for j, v in zip(indices, values)]
    if len(declared) != len(expected):
        raise ValueError('Declared targets omit part of the locked trigger')
    by_index = {t['index']: t for t in declared}
    if len(by_index) != len(expected):
        raise ValueError('Duplicate declared target')
    for target in expected:
        actual = by_index.get(target['index'])
        if (actual is None or actual['name'] != target['name'] or
                float(actual.get('atol', 0)) != 0 or
                float(np.float32(actual['value'])) != target['value']):
            raise ValueError('Declared targets differ from the locked trigger')
    return expected


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest'); p.add_argument('--output', required=True)
    a = p.parse_args(); manifest = read_json(a.manifest)
    schema = get_schema(manifest['schema'])
    if schema.version != V2_PRIMARY or manifest['schema_sha256'] != schema.fingerprint:
        raise ValueError('This extractor entry point is V2 only; require matching schema fingerprint')
    attack_path = Path(manifest['attack_record'])
    if sha256(attack_path) != manifest['attack_record_sha256']:
        raise ValueError('Attack bytes differ from locked manifest')
    attack = read_json(attack_path)
    out = Path(a.output)
    if out.exists(): raise FileExistsError('Preserve prior audits: choose a fresh output file')
    records = []
    for pair in manifest['pairs']:
        row = {'original_path': pair['original_path'], 'edited_path': pair['edited_path'],
               'functional_status': 'NOT_RUN', 'backdoor_recall': None}
        try:
            original, edited = Path(pair['original_path']), Path(pair['edited_path'])
            row.update(original_sha256=sha256(original), edited_sha256=sha256(edited))
            if row['original_sha256'] != pair['original_sha256'] or row['edited_sha256'] != pair['edited_sha256']:
                raise ValueError('Bytes differ from locked manifest')
            x, meta0 = extract_pe(original.read_bytes()); xt, meta1 = extract_pe(edited.read_bytes())
            x, xt = np.asarray(x, dtype=np.float32), np.asarray(xt, dtype=np.float32)
            if x.shape != (schema.dim,) or xt.shape != x.shape:
                raise ValueError('Extractor shape mismatch')
            targets = locked_targets(attack, schema, pair['targets'])
            checks = check_targets(xt, targets, schema)
            row.update(status='COMPLETE_TARGET_MATCH' if all(t['matched'] for t in checks) else 'TARGET_MISMATCH',
                       targets=checks, changed_indices=np.flatnonzero(x != xt).tolist(),
                       original_extractor_metadata=meta0, edited_extractor_metadata=meta1)
        except Exception as error:
            row.update(status='ERROR', error=str(error))
        records.append(row)
    write_json(out, {'scope': 'static target checks only; not functionality or attack success',
                    'attack_record_sha256': sha256(attack_path), 'model_evaluation': 'NOT_RUN',
                    'manifest_sha256': sha256(a.manifest), 'script_sha256': sha256(__file__), 'records': records})


if __name__ == '__main__': main()
