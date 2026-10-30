"""Replay counts from saved scores and hash-check immutable inputs."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.revision.analysis import attack_groups
from xsentinel.revision.calibration_v2 import tolerance_threshold
from xsentinel.detection.calibration import threshold
from analyze_fusion_overlap import ROOT

def check_rows(rows,z,a,style):
    mask=attack_groups(a['clean_malware_p'],a['triggered_main_p'],a['clean_trigger_p'])['successful_eligible']
    for row in rows:
        prefix=row['method']+'_' if style=='raw' else ''
        cs=z[prefix+'calibration'];ns=z[prefix+'benign'];ps=z[prefix+'trigger']
        tau=threshold(cs) if row['policy']=='empirical_calibration' else tolerance_threshold(cs)['threshold']
        assert np.isclose(tau,row['tau'],rtol=0,atol=1e-12)
        assert int((ns>tau).sum())==row['fp'] and int((ps[mask]>tau).sum())==row['tp']
        assert len(ns)==row['n_benign'] and int(mask.sum())==row['n_successful']
    assert np.array_equal(z['malware_ids'].astype(str),a['malware_ids'].astype(str))
    assert np.array_equal(z['benign_ids'].astype(str),a['benign_ids'].astype(str))

def main():
    manifest=read_json(ROOT/'frozen_audit/manifest.json')
    assert all(sha256(p)==h for p,h in manifest['sources'].items())
    counts={};outputs={}
    for folder,style in [('raw_baselines','raw'),('view3','view')]:
        records=sorted((ROOT/folder).glob('*/seed_*/*/rate_*/result.json'));counts[folder]=len(records)
        for path in records:
            r=read_json(path);first=r['rows'][0]
            original=Path('outputs/primary')/first['dataset']/'protocol_v2'/f"seed_{first['seed']}"/first['family']/f"rate_{first['rate']}"
            assert r['source_hash']==sha256(original/'result.json') and r['score_hash']==sha256(path.parent/'scores.npz')
            with np.load(path.parent/'scores.npz',allow_pickle=False) as z,np.load(original/'paired_predictions.npz',allow_pickle=False) as a:check_rows(r['rows'],z,a,style)
            outputs[str(path)]=sha256(path);outputs[str(path.parent/'scores.npz')]=r['score_hash']
    df=pd.read_csv(ROOT/'public_shadow/public_shadow_per_run.csv')
    for key,g in df.groupby(['dataset','seed','family','rate']):
        ds,seed,family,rate=key;relative=Path(f'seed_{seed}')/family/f'rate_{rate}'
        with np.load(ROOT/'public_shadow'/relative/'scores.npz',allow_pickle=False) as z,np.load(Path('outputs/primary')/ds/'protocol_v2'/relative/'paired_predictions.npz',allow_pickle=False) as a:
            check_rows(g.to_dict('records'),z,a,'public')
    counts['public_shadow']=df.groupby(['dataset','seed','family','rate']).ngroups
    write_json(ROOT/'verification.json',dict(verified_counts=counts,original_sources_unchanged=True,
        new_score_counts_replayed=True,output_hashes=outputs,scope='Arithmetic/provenance checks, not evidence of independent validation',code_sha256=sha256(__file__)))
    print(counts)

if __name__=='__main__':main()
