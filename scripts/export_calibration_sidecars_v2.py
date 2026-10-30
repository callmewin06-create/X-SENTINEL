"""Attach versioned opt-in thresholds to immutable original Full bundles."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.revision.calibration_v2 import POLICY
from analyze_fusion_overlap import ROOT,cells

def main():
    designs=read_json(ROOT/'frozen_audit/calibration_policies.json')
    for path in cells():
        r=read_json(path);cell=path.parent
        for endpoints in [1,378]:
            selected=[p for p in designs if all(p[k]==r[k] for k in ['dataset','seed','family','rate']) and p['endpoints']==endpoints]
            assert len(selected)==7
            dest=ROOT/'calibration_sidecars'/r['dataset']/cell.relative_to(Path('outputs/primary')/r['dataset']/'protocol_v2')/f'endpoints_{endpoints}.json'
            write_json(dest,dict(policy=POLICY,operator='>',original_bundle=str(cell/'bundle_full'),
                original_bundle_sha256=sha256(cell/'bundle_full/bundle.json'),thresholds={p['method']:p['threshold'] for p in selected},
                designs=selected,scope='Retrospective research calibration; independence assumptions not verified; no deployment certification',
                simultaneous_family='378 cached method-cell endpoints only' if endpoints==378 else 'Pointwise only'))
    print('Exported 108 opt-in calibration sidecars; original bundles unchanged')

if __name__=='__main__':main()
