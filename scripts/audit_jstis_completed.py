"""Arithmetic and provenance audit of the completed follow-up; no fitting."""
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from xsentinel.utils import sha256,read_json,write_json
from xsentinel.revision.jstis_gate import verify_global_lock
from xsentinel.detection.calibration import threshold

r=ROOT/'outputs/jstis_revision_2026_11_09';f=r/'followup';out=r/'completed_audit';out.mkdir(exist_ok=True)
verify_global_lock(r/'attacks_v2',f/'GLOBAL_ATTACKS_LOCK.json')
for p in read_json(r/'cache_audit/PRIMARY_BEFORE.json'):
    assert sha256(ROOT/p['path'])==p['sha256']
df=pd.read_csv(f/'summary/all_attempts.csv');assert len(df)==240
assert len(df.drop_duplicates(['dataset','seed','kind','label']))==48
sources={};adaptive=[];static=[];actual_fits=0;fit_seconds=0.;diverged=0
for dataset in ('EMBER2018','EMBER2024'):
 for seed in (17,29,43):
    cell=r/'attacks_v2'/dataset/f'seed_{seed}'
    paths=list(cell.glob('candidates/*/result.json'));actual_fits+=len(paths)
    for p in paths:fit_seconds+=read_json(p.parent/'poisoned.training.json')['elapsed_seconds']
    arms={arm:read_json(cell/f'{arm}.json') for arm in ('asr_only','vmc_aware')}
    assert all(a['budget_completed']==16 and len(a['trajectory'])==16 for a in arms.values())
    assert arms['asr_only']['trajectory'][0]['fingerprint']==arms['vmc_aware']['trajectory'][0]['fingerprint']
    if [x['fingerprint'] for x in arms['asr_only']['trajectory']]!=[x['fingerprint'] for x in arms['vmc_aware']['trajectory']]:diverged+=1
    statics=read_json(cell/'static_attempts.json')
    init=next(s for s in statics if s['profile']=='vector_stress' and s['selector']=='count_abs_shap')
    assert init['fingerprint']==arms['asr_only']['trajectory'][0]['fingerprint']
    specs=[{'kind':'static','label':s['profile']+'/'+s['selector'],'fingerprint':s['fingerprint']} for s in statics]
    specs +=[{'kind':'adaptive','label':arm,'fingerprint':a['selected']['fingerprint']} for arm,a in arms.items()]
    for spec in specs:
      path=f/'evaluations'/dataset/f'seed_{seed}'/spec['fingerprint'];e=read_json(path/'RESULTS.json')
      assert sha256(path/'scores.npz')==e['scores_sha256']
      assert sha256(cell/'candidates'/spec['fingerprint']/'poisoned.txt')==e['model_sha256']
      sources[str(path.relative_to(ROOT))]=sha256(path/'RESULTS.json')
      with np.load(path/'scores.npz') as z:
       success=z['eligible']&(z['triggered_p']<.5);assert np.array_equal(success,z['successful'])
       for method,m in e['methods'].items():
        assert np.isclose(threshold(z['calibration_'+method]),m['tau'],atol=1e-12,rtol=0)
        fp=int((z['benign_'+method]>m['tau']).sum())
        tp=int((z['triggered_'+method][success]>m['tau']).sum())
        assert fp==m['benign_fpr']['count'] and tp==m['successful_recall']['count']
        assert int(success.sum())==m['successful_recall']['n']
        row=df[(df.dataset==dataset)&(df.seed==seed)&(df.kind==spec['kind'])&(df.label==spec['label'])&(df.method==method)].iloc[0]
        assert np.isclose(row.recall,m['successful_recall']['rate']) and row.fp==fp
      record={'dataset':dataset,'seed':seed,'kind':spec['kind'],'label':spec['label'],'fingerprint':spec['fingerprint'],
          'confirmed':bool(df[(df.dataset==dataset)&(df.seed==seed)&(df.label==spec['label'])].iloc[0].confirmed),
          'asr':e['asr']['rate'],'eligible_n':e['eligible_n'],'success_n':e['asr']['count'],
          'paired_gain':e['paired_gain'],'clean_trigger_asr':e['clean_trigger_asr']['rate'],
          'confirmation_asr':e['confirmation']['asr']['rate'],
          'methods':e['methods']}
      (adaptive if spec['kind']=='adaptive' else static).append(record)
assert len(adaptive)==12 and len(static)==36 and diverged==6
assert all(x['confirmed'] for x in adaptive)
aware=[x for x in adaptive if x['label']=='vmc_aware']
assert all(x['methods']['X_primary_reduced']['successful_recall']['count']==0 for x in aware)
summary={'status':'ARITHMETIC_AND_PROVENANCE_VERIFIED','static_attempts':36,'static_confirmed':sum(x['confirmed'] for x in static),
 'adaptive_arms':12,'adaptive_confirmed':12,'trajectory_divergence_cells':diverged,'actual_unique_poisoned_fits':actual_fits,
 'poisoned_fit_seconds_sum':fit_seconds,'primary216_unchanged':True,'adaptive':adaptive,'static':static,'sources':sources,
 'new_fpr_exceedances':{method:{'cells':len(g),'above_1pct':int((g.fpr>.01).sum()),'worst_fp':int(g.fp.max())}
     for method,g in df.groupby('method')},'code_sha256':sha256(__file__)}
write_json(out/'VERIFIED_RESULTS.json',summary)
print({k:v for k,v in summary.items() if k not in ('adaptive','static','sources')})
