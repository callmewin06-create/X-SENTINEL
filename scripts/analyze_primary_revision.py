"""Reproduce additional tables from all frozen cells without model training."""
import argparse,csv,json,hashlib,platform,sys
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import spearmanr,betabinom
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.revision.analysis import attack_groups,revised_metrics,catch_miss,fixed_model_cluster_difference

METHODS=['TADR','STRIP','M3_view_mass','M4_shap_behavioral_conflict','M4_prob_gap','X_primary_reduced','X_primary_full']
SHORT=['TADR','STRIP','M3','M4-R','M4-F','X-R','X-F']


def csv_out(path,rows):
    if not rows: return
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='outputs/revision_2026_10_13/analysis')
    parser.add_argument('--bootstrap',type=int,default=1000);args=parser.parse_args()
    out=Path(args.out);root=Path('outputs/primary').resolve()
    if out.resolve()==root or root in out.resolve().parents: raise ValueError('Frozen research output is protected')
    if out.exists() and any(out.iterdir()): raise FileExistsError('Use a fresh revision output')
    out.mkdir(parents=True);fig=out/'figures';fig.mkdir()
    rows=[];cases=[];cohorts=defaultdict(list);ledger={};entropy=defaultdict(lambda:defaultdict(list))
    fp_checks=[];correlations=[]
    for path in sorted(Path('outputs/primary').glob('*/protocol_v2/seed_*/*/rate_*/result.json')):
        r=read_json(path);assert r['status']=='complete';cell=path.parent
        ledger[str(path)]=sha256(path)
        for filename,digest in r['artifact_sha256'].items():
            p=cell/filename;actual=sha256(p)
            if actual!=digest:raise ValueError('Frozen artifact changed: '+str(p))
            ledger[str(p)]=actual
        with np.load(cell/'paired_predictions.npz',allow_pickle=False) as archive:
            a={k:v.copy() for k,v in archive.items()}
        groups=attack_groups(a['clean_malware_p'],a['triggered_main_p'],a['clean_trigger_p'])
        thresholds=read_json(cell/'bundle_full/bundle.json')['thresholds'];state=read_json(cell/'bundle_full/bundle.json')
        cell_id=f"{r['dataset']}/{r['seed']}/{r['family']}/{r['rate']}"
        masks={'TADR':a['full_trigger_TADR']>thresholds['TADR'],
               'M4-F':a['full_trigger_M4_prob_gap']>thresholds['M4_prob_gap']}
        cm=catch_miss(masks['TADR'],masks['M4-F'],groups)
        for name,counts in cm.items():cases.append({'cell':cell_id,'dataset':r['dataset'],'family':r['family'],
            'rate':r['rate'],'seed':r['seed'],'confirmed':r['independently_confirmed_strong_and_stealth'],'group':name,**counts})
        for method,label in zip(METHODS,SHORT):
            p=a['full_trigger_'+method];n=a['full_benign_'+method]
            metric=revised_metrics(p,n,thresholds[method],groups)
            old=r['evaluation']['results']['full']['methods'][method]
            assert np.isclose(metric['auroc_all_triggered'],old['auroc_trigger_vs_benign'])
            for k in ('benign_fpr','recall_successful_eligible','post_defense_asr'):
                assert metric[k]['count']==old[k]['count'] and metric[k]['n']==old[k]['n']
            row={'dataset':r['dataset'],'family':r['family'],'rate':r['rate'],'seed':r['seed'],
                 'confirmed':r['independently_confirmed_strong_and_stealth'],'method':label,
                 'n_eligible':int(groups['eligible'].sum()),'n_successful':int(groups['successful_eligible'].sum()),
                 'n_paired_new_evasion':int(groups['paired_new_evasion'].sum()),
                 'asr_before':metric['asr_before']['rate'],'recall':metric['recall_successful_eligible']['rate'],
                 'paired_new_evasion_recall':metric['recall_paired_new_evasion']['rate'],
                 'fpr':metric['benign_fpr']['rate'],'post_asr':metric['post_defense_asr']['rate'],
                 'auc_all':metric['auroc_all_triggered'],'auc_successful':metric['auroc_successful_eligible'],
                 'auc_paired_new_evasion':metric['auroc_paired_new_evasion'],'tau':thresholds[method]}
            rows.append(row)
            # Continuous/exchangeable calibration null includes finite threshold uncertainty.
            # Ties make it inexact for these scores, so this is a diagnostic, not proof of shift.
            size=state['calibration_size'];allowed=int(np.floor(size*state['config']['fpr']))
            alpha=allowed+1;beta=size-allowed;count=old['benign_fpr']['count'];total=old['benign_fpr']['n']
            fp_checks.append({'cell':cell_id,'method':label,'fp':count,'n':total,
                'calibration_n':size,'calibration_exceedances':state['calibration_fp_count'][method],
                'continuous_null_beta_alpha':alpha,'continuous_null_beta_beta':beta,
                'upper_tail_beta_binomial_diagnostic':float(betabinom.sf(count-1,total,alpha,beta)),
                'scope':'Continuous IID order-statistic null only; ties, ECDF and cross-run dependence limit interpretation'})
        with np.load(cell/'bundle_full/reference.npz',allow_pickle=False) as refs:
            for view in ('M4_shap_behavioral_conflict','M4_prob_gap'):
                for group,mask in [('benign',None),('successful',groups['successful_eligible'])]:
                    suffix='benign' if mask is None else 'trigger'
                    scores=[a['full_'+suffix+'_'+m] if mask is None else a['full_'+suffix+'_'+m][mask]
                            for m in ('M3_view_mass',view)]
                    ranks=[np.searchsorted(refs['rank_'+m],v,side='right')/len(refs['rank_'+m])
                           for m,v in zip(('M3_view_mass',view),scores)]
                    corr=spearmanr(*ranks).statistic if all(len(np.unique(v))>1 for v in ranks) else None
                    correlations.append({'cell':cell_id,'group':group,'second_component':view,
                                         'n':len(ranks[0]),'spearman':None if corr is None else float(corr)})
        if r['independently_confirmed_strong_and_stealth']:
            cohorts[(r['dataset'],r['family'])].append((r,a,groups))
            for name,key,mask in [('benign','benign',None),('triggered','trigger',None),
                                  ('successful','trigger',groups['successful_eligible'])]:
                values=1-a['full_'+key+'_STRIP'];values=values if mask is None else values[mask]
                entropy[r['dataset']][name].append(values)
        print('Reanalyzed',cell_id,flush=True)
    assert len(ledger)>54 and len(rows)==54*len(METHODS)
    csv_out(out/'cell_metrics.csv',rows);csv_out(out/'catch_miss.csv',cases)
    csv_out(out/'rank_correlations.csv',correlations);csv_out(out/'fpr_diagnostics.csv',fp_checks)
    summaries=[]
    for dataset in ('EMBER2018','EMBER2024'):
        for cohort in ('restricted_confirmed','cross_confirmed','all_confirmed','all_configs'):
            selected=[x for x in rows if x['dataset']==dataset and
                      (cohort=='all_configs' or x['confirmed']) and
                      (cohort not in ('restricted_confirmed','cross_confirmed') or
                       ((x['family']=='cross_3view_stress')==(cohort=='cross_confirmed')))]
            for label in SHORT:
                xs=[x for x in selected if x['method']==label]
                if not xs:continue
                summaries.append({'dataset':dataset,'cohort':cohort,'method':label,'runs':len(xs),
                    **{key:float(np.mean([x[key] for x in xs if x[key] is not None])) if any(x[key] is not None for x in xs) else None
                       for key in ('asr_before','recall','fpr','post_asr','auc_all','auc_successful','auc_paired_new_evasion')}})
    csv_out(out/'cohort_metrics.csv',summaries)
    cluster=[]
    for dataset in ('EMBER2018','EMBER2024'):
        for name in ('restricted_confirmed','cross_confirmed','all_confirmed'):
            xs=[x for (d,f),items in cohorts.items() for x in items if d==dataset and
                (name=='all_confirmed' or ((f=='cross_3view_stress')==(name=='cross_confirmed')))]
            if not xs:continue
            first_ids=xs[0][1]
            assert all(np.array_equal(a['benign_ids'],first_ids['benign_ids']) and np.array_equal(a['malware_ids'],first_ids['malware_ids']) for _,a,_ in xs)
            def flags(method,pool):return np.stack([a['full_'+pool+'_'+method]>r['evaluation']['results']['full']['methods'][method]['threshold'] for r,a,g in xs])
            for first,second in [('M3_view_mass','X_primary_reduced'),('X_primary_reduced','X_primary_full'),('M4_prob_gap','X_primary_full')]:
                result=fixed_model_cluster_difference(np.stack([g['successful_eligible'] for _,a,g in xs]),
                    np.stack([g['eligible'] for _,a,g in xs]),flags(first,'trigger'),flags(second,'trigger'),
                    flags(first,'benign'),flags(second,'benign'),args.bootstrap)
                cluster.append({'dataset':dataset,'cohort':name,'first':first,'second':second,**result})
            print('Cluster inference',dataset,name,flush=True)
    write_json(out/'cluster_intervals.json',cluster)
    for dataset,groups in entropy.items():
        plt.figure(figsize=(7,4))
        for label,values in groups.items():plt.hist(np.concatenate(values),bins=np.linspace(0,1,41),density=True,histtype='step',linewidth=1.6,label=label)
        plt.xlabel('Mean binary predictive entropy');plt.ylabel('Density');plt.legend();plt.tight_layout()
        plt.savefig(fig/f'{dataset}_strip_entropy.png',dpi=180);plt.savefig(fig/f'{dataset}_strip_entropy.pdf');plt.close()
    for dataset in ('EMBER2018','EMBER2024'):
        xs=[x for x in summaries if x['dataset']==dataset and x['cohort']=='restricted_confirmed']
        labels=[x['method'] for x in xs];recall=[100*x['recall'] for x in xs];fpr=[100*x['fpr'] for x in xs]
        plt.figure(figsize=(7,4));plt.bar(labels,recall,color='#286b8d');plt.ylabel('Recall on successful eligible attacks (%)')
        plt.title(dataset+' restricted confirmed cohort');plt.tight_layout();plt.savefig(fig/f'{dataset}_restricted_recall.png',dpi=180)
        plt.savefig(fig/f'{dataset}_restricted_recall.pdf');plt.close()
    # Check immutable inputs again after all analysis.
    assert all(sha256(Path(p))==h for p,h in ledger.items())
    write_json(out/'analysis.json',{'protocol':'revision-post-review-v1','scope':'Fixed old scores/models/thresholds; no new independent validation',
        'bootstrap_scope':'Source ID clusters conditional on fixed models; not model/seed inference',
        'cells':54,'methods':SHORT,'cohorts':summaries,'cluster':cluster,'bootstrap_repeats':args.bootstrap,
        'source_ledger':ledger,'frozen_inputs_unchanged':True,'python':platform.python_version()})
    print('Complete',out,flush=True)


if __name__=='__main__':main()
