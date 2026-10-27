"""Verify supplemental artifacts and metrics without training or changing models."""
import hashlib
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.revision.analysis import attack_groups,revised_metrics
from xsentinel.revision.training_filters import random_removal_control

ROOT=Path('outputs/teacher_revision_2026_10_27')


def check_hashes(mapping,base=None):
    for name,digest in mapping.items():
        path=Path(name) if base is None else base/name
        if sha256(path)!=digest:raise AssertionError(f'Hash mismatch: {path}')


def main():
    partial='--partial' in sys.argv
    originals=read_json(ROOT/'original_input_manifest.json')['sha256'];check_hashes(originals)
    check_hashes(read_json(ROOT/'shap_if/protocol.json')['code_hashes'])
    cells=list((ROOT/'shap_if').glob('*/seed_*/*/rate_*/result.json'))
    assert 0<len(cells)<=54 if partial else len(cells)==54
    for p in cells:
        r=read_json(p);check_hashes(r['source_hashes']);check_hashes(r['output_hashes'],p.parent)
        source=Path('outputs/primary')/r['dataset']/'protocol_v2'/f"seed_{r['seed']}"/r['family']/f"rate_{r['rate']}"
        with np.load(source/'paired_predictions.npz',allow_pickle=False) as a,np.load(p.parent/'scores.npz',allow_pickle=False) as z:
            np.testing.assert_array_equal(z['malware_ids'],a['malware_ids']);np.testing.assert_array_equal(z['benign_ids'],a['benign_ids'])
            groups=attack_groups(a['clean_malware_p'],a['triggered_main_p'],a['clean_trigger_p'])
            m=revised_metrics(z['triggered'],z['benign'],r['metrics']['threshold'],groups)
            assert m==r['metrics']
            assert int(np.sum(z['original_malware']>m['threshold']))==r['original_malware_alerts']
            assert np.sum(z['calibration']>m['threshold'])==r['calibration_fp']<=20
    adaptive=read_json(ROOT/'adaptive_multiview/results.json');assert len(adaptive)==24
    reproduction=[];idsets={}
    for r in adaptive:
        dest=ROOT/'adaptive_multiview'/r['dataset']/f"seed_{r['seed']}"/r['family']/f"rate_{r['rate']}"
        assert sha256(dest/'scores.npz')==r['scores_sha256']
        original=Path('outputs/primary')/r['dataset']/'protocol_v2'/dest.relative_to(ROOT/'adaptive_multiview'/r['dataset'])
        assert sha256(original/'result.json')==r['source_sha256']
        tau=read_json(original/'result.json')['evaluation']['results']['full']['methods']['X_primary_reduced']['threshold']
        with np.load(dest/'scores.npz',allow_pickle=False) as z:
            ids=z['ids'].astype(str);assert len(ids)==len(set(ids))==100
            if r['dataset'] in idsets:np.testing.assert_array_equal(ids,idsets[r['dataset']])
            idsets[r['dataset']]=ids
            eligible=z['clean_original']>=.5
            for prefix,phase in [('start','before'),('end','after')]:
                count=int(np.sum(eligible&(z['main_'+phase]<.5)&(z[phase+'_X_primary_reduced']<=tau)))
                assert count==r[prefix+'_joint_success']
            assert 1<=z['queries'].min()<=z['queries'].max()<=32
            assert z['changed_count'].max()<=24
        canonical=str(dest).replace('/','\\')
        reproduction.append(dict(relative_windows_path=canonical,rng_seed=int(hashlib.sha256(canonical.encode()).hexdigest()[:8],16)))
    write_json(ROOT/'adaptive_multiview/reproduction_seeds.json',dict(note='Explicit RNG seeds for original Windows path-derived sampling; preserve these seeds on other platforms',rows=reproduction))
    budget_paths=list((ROOT/'clean_budget').glob('*/seed_*/n_*/result.json'));assert len(budget_paths)==30
    budget=pd.read_csv(ROOT/'clean_budget/results.csv');assert len(budget)==810
    for p in budget_paths:
        r=read_json(p);check_hashes(r['sources']);assert sha256(p.parent/'scores.npz')==r['score_hash']
        assert sha256(p.parent/'fit_ids.npy')==r['fit_ids_hash'];assert len(r['rows'])==27
    for ds in ('EMBER2018','EMBER2024'):
        for seed in (17,29,43):
            last=set()
            for n in (1000,5000,10000,50000,200000):
                ids=set(np.load(ROOT/'clean_budget'/ds/f'seed_{seed}'/f'n_{n}'/'fit_ids.npy',allow_pickle=False).astype(str))
                assert len(ids)==n and last<=ids;last=ids
    for seed in (59,71):
        p=ROOT/'ember2024_seeds_v2'/f'seed_{seed}';r=read_json(p/'result.json');check_hashes(r['artifacts'],p)
        assert r['passes_original_screening_criteria']==all(x['strong_and_stealth'] for x in r['screens'].values())
        with np.load(p/'scores.npz',allow_pickle=False) as z:
            groups=attack_groups(z['clean_original'],z['poisoned_trigger'],z['clean_trigger'])
            for method,m in r['metrics'].items():
                assert revised_metrics(z['positive_'+method],z['negative_'+method],m['threshold'],groups)==m
    defense=pd.read_csv(ROOT/'training_defense_v2/results.csv');assert len(defense)==4
    for ds in ('EMBER2018','EMBER2024'):
        p=ROOT/'training_defense_v2'/ds;r=read_json(p/'result.json');check_hashes(r['artifacts'],p)
        with np.load(p/'selection.npz',allow_pickle=False) as z:
            chosen=random_removal_control(np.arange(len(z['benign_ids'])),5000)
            # The helper samples positions; ID order comparison is independent of the fit's integer positions.
            np.testing.assert_array_equal(z['random_control_removed_ids'],z['benign_ids'][chosen])
            assert len(set(z['random_control_removed_ids']))==5000
        for row in r['rows']:
            with np.load(p/(row['method']+'_predictions.npz'),allow_pickle=False) as z:
                eligible=z['clean_original']>=.5
                assert np.isclose(np.mean(z['before'][eligible]<.5),row['asr_before'])
                assert np.isclose(np.mean(z['after'][eligible]<.5),row['asr_after'])
    tests=ET.parse(ROOT/'tests_final.xml').getroot()
    suites=list(tests.iter('testsuite'));assert sum(int(s.attrib['failures'])+int(s.attrib['errors']) for s in suites)==0
    write_json(ROOT/('audit_partial.json' if partial else 'audit.json'),dict(status='incomplete_if' if partial else 'passed',original_assets_verified=len(originals),shap_if_cells=len(cells),
        adaptive_cells=24,adaptive_unique_sources={k:len(v) for k,v in idsets.items()},budget_checkpoints=30,budget_rows=810,
        additional_seed_attempts=2,training_defense_rows=4,regression_tests=sum(int(s.attrib['tests']) for s in suites),
        test_report_sha256=sha256(ROOT/'tests_final.xml'),source_sha256=sha256(__file__),
        limits='Cached metrics and artifact integrity audited; binary results and canonical Word integration pending teammates'))
    print('Partial audit verified; IF completion still pending' if partial else 'Research audit passed',flush=True)


if __name__=='__main__':main()
