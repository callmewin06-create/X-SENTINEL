"""Build one evidence summary for the revised Word manuscript and response ledger."""
import sys,json,csv,statistics
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from xsentinel.utils import read_json,write_json

def mean(values):
    values=[v for v in values if v is not None]
    return float(np.mean(values)) if values else None

def main():
    root=Path('outputs/revision_2026_10_13');a=read_json(root/'analysis/analysis.json')
    f=read_json(root/'validation_results/fresh_summary.json')['results']
    ad=read_json(root/'adaptive_structural/adaptive_summary.json')['results']
    latency=read_json(root/'supplement/latency.json')
    sensitivity=list(csv.DictReader((root/'supplement/sensitivity.csv').open()))
    supplement={k:list(csv.DictReader((root/f'supplement/{k}.csv').open())) for k in ('shadow','strip_inverse')}
    fresh=[];new_baselines=[];sens=[];timing=[];adapt=[]
    for dataset in ('EMBER2018','EMBER2024'):
        for cohort in ('restricted_confirmed','cross_confirmed','all_confirmed','all_configs'):
            def select(row,flag='confirmed_original'):
                return row['dataset']==dataset and (cohort=='all_configs' or row[flag]) and (
                    cohort not in ('restricted_confirmed','cross_confirmed') or
                    (row['family']=='cross_3view_stress')==(cohort=='cross_confirmed'))
            rows=[r for r in f if select(r)]
            if not rows:continue
            for method in rows[0]['metrics']:
                metrics=[r['metrics'][method] for r in rows]
                fresh.append({'dataset':dataset,'cohort':cohort,'method':method,'runs':len(rows),
                    'recall':mean([m['recall_successful_eligible']['rate'] for m in metrics]),
                    'fpr':mean([m['benign_fpr']['rate'] for m in metrics]),
                    'post_asr':mean([m['post_defense_asr']['rate'] for m in metrics]),
                    'asr_before':mean([m['asr_before']['rate'] for m in metrics]),
                    'auc_successful':mean([m['auroc_successful_eligible'] for m in metrics]),
                    'successful_min':min(r['groups']['successful_eligible'] for r in rows),
                    'successful_max':max(r['groups']['successful_eligible'] for r in rows)})
            for name,source in supplement.items():
                rows2=[r for r in source if select({**r,'confirmed_original':r['confirmed']=='True'})]
                new_baselines.append({'dataset':dataset,'cohort':cohort,'method':name,'runs':len(rows2),
                    **{k:mean([float(r[k]) for r in rows2]) for k in ('recall','fpr','post_asr')}})
        original=[r for r in sensitivity if r['dataset']==dataset and r['condition']=='original']
        for method in sorted(set(r['method'] for r in original)):
            orig={tuple(r[k] for k in ('seed','family','rate')):r for r in original if r['method']==method}
            after=[r for r in sensitivity if r['dataset']==dataset and r['condition']=='both_is_pe_1' and r['method']==method]
            sens.append({'dataset':dataset,'method':method,'runs':len(after),
                'max_abs_tau_delta':max(abs(float(r['tau_delta'])) for r in after),
                'max_abs_recall_delta':max(abs(float(r['recall'])-float(orig[tuple(r[k] for k in ('seed','family','rate'))]['recall'])) for r in after),
                'max_abs_fpr_delta':max(abs(float(r['fpr'])-float(orig[tuple(r[k] for k in ('seed','family','rate'))]['fpr'])) for r in after)})
        subset=[r for r in latency if r['dataset']==dataset]
        for scope in subset[0]['timings']:
            timing.append({'dataset':dataset,'scope':scope,'runs':len(subset),
                **{k:mean([r['timings'][scope][k] for r in subset]) for k in ('mean_ms','median_ms','p95_ms')}})
        rows=[r for r in ad if r['dataset']==dataset]
        adapt.append({'dataset':dataset,'runs':len(rows),'samples_per_run':100,
            'eligible_occurrences':sum(r['eligible'] for r in rows),
            'start_joint_occurrences':sum(r['start_joint_success'] for r in rows),
            'end_joint_occurrences':sum(r['end_joint_success'] for r in rows),
            'new_joint_occurrences':sum(r['new_joint_success'] for r in rows),
            'mean_queries':mean([r['mean_queries'] for r in rows]),'max_queries':max(r['max_queries'] for r in rows)})
    write_json(root/'summary.json',{'original_cohorts':a['cohorts'],'fresh_cohorts':fresh,'supplement_old_final':new_baselines,
        'sensitivity':sens,'timing':timing,'adaptive':adapt,'cluster':a['cluster'],
        'notes':['Fresh pools: 1000 benign and 1000 malware per dataset, shared source IDs across fixed models.',
        'All cohort summaries are equal-run means. Adaptive counts are repeated source/model occurrences, not independent samples.',
        'No final-based threshold/fusion/trigger selection; new baselines use original benign calibration.',
        'Fixed-model bootstrap does not quantify uncertainty over new seeds or attacks.']})
    print('Evidence summary completed')

if __name__=='__main__':main()
