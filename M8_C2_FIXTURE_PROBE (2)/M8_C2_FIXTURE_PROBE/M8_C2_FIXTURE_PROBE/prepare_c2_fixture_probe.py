"""Create only allowlisted benign fixture controls; never execute PE files."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import struct
import sys
import lief
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from xsentinel.data.pe import extract_pe
from xsentinel.schema import get_schema, V2_PRIMARY

ALLOWED = {
    'native': ('native_original.exe', 'fad8537b5080ab8f2dafda8b1cca4d435070ec900598c28a18b6c882c7bd96eb'),
    'managed': ('ReviewedBenignFixture.exe', 'eae43234c30b26578ed8efdc73df0845d060c74f78d23d6f1ac0f2976ee70f3d'),
}
ATTACK = 'outputs/primary/EMBER2018/protocol_v2/seed_17/concentrated_structural/rate_0.02/attack.json'
ATTACK_HASH = '0115ef55af284571c04720c4651c04822c61d2c28681239759cec287e3d3c38d'
def digest(data): return hashlib.sha256(data).hexdigest()
def parse(data):
    binary = lief.PE.parse(io.BytesIO(data))
    if binary is None: raise ValueError('PE parsing failed')
    return binary
def rx(binary): return sum((s.characteristics & 0x60000000) == 0x60000000 for s in binary.sections)
def sections(data):
    binary = parse(data)
    return [{'name':s.name, 'rva':s.virtual_address, 'vsize':s.virtual_size,
             'flags':s.characteristics, 'content_sha256':digest(bytes(s.content))} for s in binary.sections]
def make_variant(data, add_sections, timestamp, target_rx, target_timestamp):
    result = data
    if add_sections:
        binary = parse(data)
        if rx(binary) > target_rx: raise ValueError('Existing RX count exceeds target')
        for j in range(target_rx - rx(binary)):
            section = lief.PE.Section(f'.xc{j:02d}')
            # Zero-filled inert data. No payload or original control-flow changes.
            section.content = [0] * 512
            section.characteristics = 0x60000040
            binary.add_section(section)
        builder = lief.PE.Builder(binary)
        builder.build_imports(False)
        builder.build_overlay(True)
        builder.build()
        result = bytes(builder.get_build())
    if timestamp:
        result = bytearray(result)
        offset = struct.unpack_from('<I', result, 0x3c)[0]
        struct.pack_into('<I', result, offset + 8, target_timestamp)
        result = bytes(result)
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fixtures', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    attack_path = ROOT / ATTACK
    assert digest(attack_path.read_bytes()) == ATTACK_HASH, 'Frozen attack changed'
    attack = json.loads(attack_path.read_text())
    schema = get_schema(V2_PRIMARY)
    t = attack['trigger']
    assert t['schema_sha256'] == schema.fingerprint
    assert t['indices'] == [691, 626] and t['values'] == [12.0, 1053454528.0]
    source = Path(a.fixtures)
    inputs = {key:(source/name).read_bytes() for key,(name,_) in ALLOWED.items()}
    for key, data in inputs.items():
        if digest(data) != ALLOWED[key][1]: raise ValueError('Only supplied benign fixtures are allowed')
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=False)
    (out/'binaries').mkdir()
    shutil.copyfile(attack_path, out/'attack_record.json')
    variants = []
    for key, original in inputs.items():
        original_sections = sections(original)
        original_entry = parse(original).optional_header.addressof_entrypoint
        x0, _ = extract_pe(original)
        for variant, add, ts in [('original',False,False),('timestamp_only',False,True),
                                 ('sections_only',True,False),('full_c2',True,True)]:
            data = make_variant(original, add, ts, 12, 1053454528)
            path = out/'binaries'/f'{key}_{variant}.exe'
            path.write_bytes(data)
            x, meta = extract_pe(data)
            current_sections = sections(data)
            preserved = current_sections[:len(original_sections)] == original_sections
            entry_preserved = parse(data).optional_header.addressof_entrypoint == original_entry
            checks = [{'index':j, 'name':schema.names[j], 'expected':float(v),
                       'actual':float(x[j]), 'matched':bool(np.float32(x[j])==np.float32(v))}
                      for j,v in zip(t['indices'], t['values'])]
            variants.append({'fixture':key, 'variant':variant,'path':path.relative_to(out).as_posix(),
                'sha256':digest(data),'original_sha256':digest(original),'bytes':len(data),
                'original_sections_preserved':preserved,'entrypoint_rva_preserved':entry_preserved,
                'targets':checks, 'all_targets_match':all(c['matched'] for c in checks),
                'changed_indices':np.flatnonzero(x0 != x).tolist(), 'extractor':meta,
                'functional_status':'NOT_RUN'})
            if not preserved or not entry_preserved: raise ValueError(f'Structural invariant changed: {key}/{variant}')
            if variant == 'full_c2' and not all(c['matched'] for c in checks):
                raise ValueError('Full C2 failed static target matching')
    report = {'scope':'Benign fixture feasibility only; not malware preservation, ASR or recall',
              'attack_record':'attack_record.json','attack_record_sha256':ATTACK_HASH,
              'schema':schema.version,'schema_sha256':schema.fingerprint,
              'producer_sha256':digest(Path(__file__).read_bytes()), 'variants':variants,
              'sample_execution':'NEVER','model_evaluation':'NOT_RUN'}
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(out), 'variants':len(variants),
                      'full_c2_static_match':sum(v['variant']=='full_c2' and v['all_targets_match'] for v in variants)}))
if __name__ == '__main__': main()
