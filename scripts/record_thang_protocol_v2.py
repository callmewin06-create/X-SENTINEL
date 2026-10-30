"""Record execution inventory and sidecar smoke checks without changing core."""
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.revision.calibrated_bundle import CalibratedBundle
from xsentinel.primary_workflow import open_roles
from analyze_fusion_overlap import ROOT

def main():
    inputs={};smoke=[]
    for ds in ['EMBER2018','EMBER2024']:
        directory=Path('data/primary')/ds/'protocol_v2';state=read_json(directory/'roles.json')
        inputs[ds]=dict(roles_sha256=sha256(directory/'roles.json'),partition_sha256=sha256(directory/'roles.npz'),
            source_directory=state['source_directory'],source_array_sha256=state['source_array_sha256'],schema=state['schema'])
        _,_,roles=open_roles(directory,('reference',))
        relative=Path('seed_17/concentrated_structural/rate_0.005')
        bundle=Path('outputs/primary')/ds/'protocol_v2'/relative/'bundle_full'
        policy=ROOT/'calibration_sidecars'/ds/relative/'endpoints_1.json'
        obj=CalibratedBundle(bundle,policy);x=roles['reference']['X'][:2]
        for method in ['X_primary_reduced','X_primary_full']:
            a,flags,_,_=obj.predict_selected(x,method);b,_,_,_=obj.detector.predict_selected(x,method)
            assert all(np.array_equal(a[k],b[k]) for k in a)
            assert all(np.array_equal(flags[k],a[k]>obj.thresholds[k]) for k in a)
        smoke.append(dict(dataset=ds,old_scores_identical=True,new_threshold_decisions_verified=True,bundle_sha256=sha256(bundle/'bundle.json')))
    write_json(ROOT/'input_manifest.json',inputs)
    write_json(ROOT/'sidecar_smoke.json',smoke)
    sources=[*Path('scripts').glob('*v2.py'),Path('scripts/analyze_fusion_overlap.py'),Path('scripts/bootstrap_analytics.py'),Path('scripts/train_public_shadow_bodmas.py'),Path('scripts/download_bodmas_vectors.py'),
        Path('src/xsentinel/revision/calibration_v2.py'),Path('src/xsentinel/revision/calibrated_bundle.py'),
        Path('src/xsentinel/baselines/raw_feature_outlier.py'),Path('src/xsentinel/baselines/rarity_score.py')]
    write_json(ROOT/'protocol.json',dict(status='User approved implementation on 2026-10-30',
        kind='Execution inventory; stage-specific protocol files were written before each stage',
        git_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        code_hashes={str(p):sha256(p) for p in sources},primary_unchanged=True,
        final_scope='Previously observed original benchmark; no new independent validation',
        tuning='No dynamic-fusion selection on final; new baseline settings fixed before scoring',
        calibration='Retrospective empirical and tolerance policies; no claim of independent certification',
        dependencies={'M3':'Team threat model decision pending','M8':'Binary owner or manuscript scope decision','M9':'Literature/editorial owner'},
        public_shadow='20K class-balanced BODMAS training, 5K validation, one independent seed; no binary execution'))

if __name__=='__main__':main()
