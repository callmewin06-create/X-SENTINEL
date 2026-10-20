"""Calibrate six frozen candidates, develop on observed Final, lock a choice."""
import csv,json,sys
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.revision.fusion import fusion_scores,RULES
from xsentinel.detection.calibration import threshold
from xsentinel.revision.analysis import attack_groups,revised_metrics

OUT=Path('outputs/fusion_binary_latency_2026_10_20')


def save_csv(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    lock={'protocol':'fusion-grid-2026-10-20-v1','rules':list(RULES),
          'definitions':{'W25':'.25*a+.75*b','W50':'mean(a,b)','W75':'.75*a+.25*b','MAX':'max(a,b)','M3':'a','M4':'b'},
          'ranks':'Right empirical CDF on each frozen benign reference; a=M3,b=variant M4',
          'calibration':'Original disjoint benign calibration cache; rule-specific order statistic, strict >; target .01',
          'development':'Previously observed primary Final caches, explicitly repurposed as Development; NOT new validation',
          'selection':'One rule per variant shared by datasets: equal mean of available dataset x confirmed restricted/cross cohort mean recalls; ties within 1e-12 prefer lower macro FPR, then fewer components, then declared order',
          'cohorts':'Confirmed cells only for choice; preserve all 54 cells in output. Restricted/Cross reported separately.',
          'validation':'New local source-disjoint pool selected without predictions; external observation history unknown; no retuning after opening it',
          'primary_policy':'No writes to primary or deployment rule; W50 remains deployed',
          'script_sha256':sha256(__file__),'fusion_code_sha256':sha256('src/xsentinel/revision/fusion.py')}
    path=OUT/'protocol.json'
    if path.exists() and read_json(path)!=lock:raise ValueError('Protocol changed; use a fresh namespace')
    if not path.exists():write_json(path,lock)
    if (OUT/'selection.json').exists():raise FileExistsError('Frozen choice exists; do not select again')
    rows=[];thresholds={};ledger={}
    for path in sorted(Path('outputs/primary').glob('*/protocol_v2/seed_*/*/rate_*/result.json')):
        r=read_json(path);cell=path.parent
        supplement=Path('outputs/revision_2026_10_13/supplement')/r['dataset']/f"seed_{r['seed']}"/r['family']/f"rate_{r['rate']}"
        cache=supplement/'calibration_scores.npz'
        assert sha256(cache)==read_json(supplement/'calibration.json')['calibration_cache_sha256']
        for p in (path,cell/'paired_predictions.npz',cache,cell/'bundle_full/reference.npz',cell/'bundle_full/bundle.json'):
            ledger[p.as_posix()]=sha256(p)
        assert sha256(cell/'paired_predictions.npz')==r['artifact_sha256']['paired_predictions.npz']
        bundle=read_json(cell/'bundle_full/bundle.json')
        assert sha256(cell/'bundle_full/reference.npz')==bundle['hashes']['reference.npz']
        cell_id=f"{r['dataset']}/seed_{r['seed']}/{r['family']}/rate_{r['rate']}"
        with np.load(cache) as cal,np.load(cell/'paired_predictions.npz') as a,np.load(cell/'bundle_full/reference.npz') as ref:
            groups=attack_groups(a['clean_malware_p'],a['triggered_main_p'],a['clean_trigger_p'])
            for variant,m4 in [('reduced','M4_shap_behavioral_conflict'),('full','M4_prob_gap')]:
                def convert(m3_values,m4_values):return fusion_scores(m3_values,m4_values,ref['rank_M3_view_mass'],ref['rank_'+m4])
                c=convert(cal['M3_view_mass'],cal[m4])
                positive=convert(a['full_trigger_M3_view_mass'],a['full_trigger_'+m4])
                negative=convert(a['full_benign_M3_view_mass'],a['full_benign_'+m4])
                taus={name:threshold(values,.01) for name,values in c.items()}
                assert np.isclose(taus['W50'],bundle['thresholds']['X_primary_'+variant],rtol=0,atol=1e-12)
                thresholds[cell_id+'/'+variant]=taus
                for name in RULES:
                    metric=revised_metrics(positive[name],negative[name],taus[name],groups)
                    rows.append({'cell':cell_id,'dataset':r['dataset'],'family':r['family'],'seed':r['seed'],'rate':r['rate'],
                        'confirmed':r['independently_confirmed_strong_and_stealth'],'variant':variant,'rule':name,
                        'tau':taus[name],'calibration_n':len(c[name]),'calibration_fp':int(np.sum(c[name]>taus[name])),
                        'recall':metric['recall_successful_eligible']['rate'],'successful_n':metric['recall_successful_eligible']['n'],
                        'caught_n':metric['recall_successful_eligible']['count'],'fpr':metric['benign_fpr']['rate'],
                        'benign_n':metric['benign_fpr']['n'],'false_positives':metric['benign_fpr']['count'],
                        'post_asr':metric['post_defense_asr']['rate']})
        print('Fusion Development',cell_id,flush=True)
    save_csv(OUT/'development_cells.csv',rows)
    write_json(OUT/'thresholds.json',thresholds)
    groups=defaultdict(list)
    for row in rows:
        if row['confirmed']:
            cohort='cross' if row['family']=='cross_3view_stress' else 'restricted'
            groups[(row['dataset'],cohort,row['variant'],row['rule'])].append(row)
    summary=[]
    for (dataset,cohort,variant,rule),items in groups.items():
        summary.append({'dataset':dataset,'cohort':cohort,'variant':variant,'rule':rule,'runs':len(items),
                        'recall':float(np.mean([x['recall'] for x in items])),
                        'fpr':float(np.mean([x['fpr'] for x in items])),
                        'post_asr':float(np.mean([x['post_asr'] for x in items]))})
    save_csv(OUT/'development_cohorts.csv',summary)
    choices={};objectives=[]
    for variant in ('reduced','full'):
        candidates=[]
        for rule in RULES:
            items=[x for x in summary if x['variant']==variant and x['rule']==rule]
            candidates.append({'variant':variant,'rule':rule,'macro_recall':float(np.mean([x['recall'] for x in items])),
                'macro_fpr':float(np.mean([x['fpr'] for x in items])),'cohorts':len(items)})
        best_recall=max(x['macro_recall'] for x in candidates)
        tied=[x for x in candidates if abs(x['macro_recall']-best_recall)<=1e-12]
        tied.sort(key=lambda x:(x['macro_fpr'],1 if x['rule'] in ('M3','M4') else 2,RULES.index(x['rule'])))
        choices[variant]=tied[0]['rule'];objectives.extend(candidates)
    save_csv(OUT/'selection_objectives.csv',objectives)
    write_json(OUT/'selection.json',{'choices':choices,'protocol_sha256':sha256(OUT/'protocol.json'),
        'thresholds_sha256':sha256(OUT/'thresholds.json'),'development_rows':len(rows),'primary_unchanged':True,
        'source_ledger':ledger,'independent_validation_done':False})
    print(json.dumps({'choices':choices,'rows':len(rows),'cohorts':len(summary)}),flush=True)


if __name__=='__main__':main()
