"""Rebuild reviewer tables from frozen scores plus completed supplemental artifacts."""
import csv
import gc
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import numpy as np
import pandas as pd
import lightgbm as lgb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve
from collections import defaultdict
from xsentinel.utils import read_json, write_json, sha256
from xsentinel.primary_workflow import open_roles
from xsentinel.revision.analysis import attack_groups, revised_metrics
from xsentinel.revision.low_fpr import low_fpr_metrics
from xsentinel.detection.calibration import threshold

ROOT = Path('outputs/teacher_revision_2026_10_27')
METHODS = ['TADR','STRIP','M3_view_mass','M4_shap_behavioral_conflict','M4_prob_gap','X_primary_reduced','X_primary_full']
DISPLAY = dict(M3_view_mass='VMC',M4_shap_behavioral_conflict='BGS',M4_prob_gap='BPG',
               X_primary_reduced='Reduced',X_primary_full='Full',STRIP_inverse='STRIP inverse')


def main():
    out = ROOT / 'analysis'; out.mkdir(parents=True, exist_ok=True)
    shadow_root = ROOT / 'shadow_scores'
    rows, fixed, cross, manifest = [], [], [], {}
    curves=defaultdict(list); grid=np.linspace(0,.01,101)
    for dataset in ('EMBER2018', 'EMBER2024'):
        roles = None; cleans = {}
        for cell in sorted((Path('outputs/primary') / dataset / 'protocol_v2').glob('seed_*/*/rate_*')):
            r = read_json(cell/'result.json')
            for file,digest in r['artifact_sha256'].items():
                if sha256(cell/file) != digest:
                    raise ValueError('Changed original: '+str(cell/file))
            manifest[str(cell/'result.json')] = sha256(cell/'result.json')
            rel = Path(dataset) / cell.relative_to(Path('outputs/primary')/dataset/'protocol_v2')
            base = dict(dataset=dataset, seed=r['seed'], family=r['family'], rate=r['rate'],
                        confirmed=r['independently_confirmed_strong_and_stealth'],
                        cohort='cross' if r['family']=='cross_3view_stress' else 'restricted')
            with np.load(cell/'paired_predictions.npz', allow_pickle=False) as z:
                a = {k:v.copy() for k,v in z.items()}
            groups = attack_groups(a['clean_malware_p'], a['triggered_main_p'], a['clean_trigger_p'])
            taus = read_json(cell/'bundle_full/bundle.json')['thresholds']
            scores = {m:(a['full_trigger_'+m], a['full_benign_'+m], taus[m]) for m in METHODS}
            supplement = Path('outputs/revision_2026_10_13/supplement')/rel/'calibration.json'
            sr = read_json(supplement)
            scores['STRIP_inverse'] = (1-a['full_trigger_STRIP'], 1-a['full_benign_STRIP'], sr['strip_inverse']['tau'])
            dest = shadow_root/rel; dest.mkdir(parents=True, exist_ok=True)
            cached = dest/'scores.npz'; proof = dest/'source.json'
            sources = {str(p):sha256(p) for p in (cell/'result.json', cell/'bundle_full/main.txt', cell.parents[1]/'clean.txt', supplement)}
            if cached.exists() and proof.exists():
                provenance = read_json(proof)
                if provenance['sources'] != sources or provenance['cache_sha256'] != sha256(cached):
                    raise ValueError('Shadow cache changed')
                with np.load(cached, allow_pickle=False) as z:
                    sn, sc = z['benign'].copy(), z['calibration'].copy()
            else:
                if roles is None:
                    _, schema, roles = open_roles(Path('data/primary')/dataset/'protocol_v2', ('calibration','final'))
                    bf = roles['final']['y']==0
                if not np.array_equal(a['benign_ids'].astype(str), roles['final']['ids'][bf].astype(str)):
                    raise ValueError('Benign ID mismatch')
                if r['seed'] not in cleans:
                    clean = lgb.Booster(model_file=str(cell.parents[1]/'clean.txt'))
                    cleans[r['seed']] = (clean.predict(roles['calibration']['X'], num_threads=2),
                                         clean.predict(roles['final']['X'][bf], num_threads=2))
                cp, cb = cleans[r['seed']]
                main_model = lgb.Booster(model_file=str(cell/'bundle_full/main.txt'))
                sc = np.maximum(0, cp-main_model.predict(roles['calibration']['X'], num_threads=2))
                sn = np.maximum(0, cb-main_model.predict(roles['final']['X'][bf], num_threads=2))
                np.savez_compressed(cached, benign=sn, calibration=sc, benign_ids=a['benign_ids'])
                write_json(proof, dict(sources=sources, cache_sha256=sha256(cached)))
                del main_model
            st = threshold(sc, .01)
            if not np.isclose(st, sr['shadow']['tau'], rtol=0, atol=1e-10):
                raise ValueError('Shadow calibration does not reproduce')
            scores['Shadow'] = (np.maximum(0, a['clean_trigger_p']-a['triggered_main_p']), sn, st)
            ip = ROOT/'shap_if'/rel/'result.json'
            if ip.exists():
                ir = read_json(ip)
                if ir['output_hashes']['scores.npz'] != sha256(ip.parent/'scores.npz'):
                    raise ValueError('SHAP-IF cache changed')
                with np.load(ip.parent/'scores.npz', allow_pickle=False) as z:
                    if not np.array_equal(z['malware_ids'], a['malware_ids']) or not np.array_equal(z['benign_ids'], a['benign_ids']):
                        raise ValueError('IF ID mismatch')
                    scores['SHAP-IF'] = (z['triggered'].copy(), z['benign'].copy(), ir['metrics']['threshold'])
            for method,(ps,ns,tau) in scores.items():
                m = revised_metrics(ps, ns, tau, groups)
                if method in METHODS:
                    old=r['evaluation']['results']['full']['methods'][method]
                    for key in ('benign_fpr','recall_successful_eligible','post_defense_asr'):
                        if any(m[key][field]!=old[key][field] for field in ('count','n')):
                            raise ValueError('Original metric count mismatch')
                pos=ps[groups['successful_eligible']]
                if base['confirmed'] and len(pos):
                    fx,ty,_=roc_curve(np.r_[np.ones(len(pos)),np.zeros(len(ns))],np.r_[pos,ns],drop_intermediate=False)
                    curves[(dataset,base['cohort'],method)].append(ty[np.searchsorted(fx,grid,side='right')-1])
                fixed.append({**base, 'method':method, 'threshold':tau,
                              'recall':m['recall_successful_eligible']['rate'],
                              'fpr':m['benign_fpr']['rate'], 'post_asr':m['post_defense_asr']['rate'],
                              'n_successful':m['recall_successful_eligible']['n'],
                              'detected':m['recall_successful_eligible']['count'],
                              'fp':m['benign_fpr']['count'], 'n_benign':len(ns)})
                for group,mask in groups.items():
                    rows.append({**base, 'method':method, 'group':group, **low_fpr_metrics(ps[mask],ns)})
            eligible = groups['eligible']; before = a['clean_trigger_p']<.5; after = a['triggered_main_p']<.5
            cross.append({**base, 'pool':'final', 'n_eligible':int(eligible.sum()),
                          'clean_trigger_asr':float(before[eligible].mean()), 'poisoned_asr':float(after[eligible].mean()),
                          'paired_gain':float(after[eligible].mean()-before[eligible].mean()),
                          'paired_new_count':int(np.sum(eligible & after & ~before)),
                          'paired_lost_count':int(np.sum(eligible & before & ~after)),
                          'paired_new_rate':float(np.mean((after & ~before)[eligible])),
                          'paired_lost_rate':float(np.mean((before & ~after)[eligible]))})
            print('Analyzed', dataset, r['seed'], r['family'], r['rate'], flush=True)
        del roles, cleans
        gc.collect()
    df = pd.DataFrame(rows); ff = pd.DataFrame(fixed)
    df.to_csv(out/'same_fpr_per_run.csv', index=False)
    ff.to_csv(out/'fixed_threshold_per_run.csv', index=False)
    pd.DataFrame(cross).to_csv(out/'final_paired_metrics.csv', index=False)
    selected = df[df.confirmed]
    summary = selected.groupby(['dataset','cohort','method','group']).agg(
        runs=('seed','size'), valid_tpr_runs=('tpr','count'), tpr_mean=('tpr','mean'),
        fpr_mean=('fpr','mean'), standardized_partial_auc_mean=('standardized_partial_auc','mean')).reset_index()
    summary.to_csv(out/'same_fpr_summary.csv', index=False)
    ff.groupby(['dataset','family','rate','confirmed','method']).agg(
        runs=('seed','size'), recall_mean=('recall','mean'), recall_min=('recall','min'),
        recall_max=('recall','max'), recall_sd=('recall','std'), fpr_mean=('fpr','mean')).reset_index().to_csv(out/'seed_variability.csv', index=False)
    confirmations = []
    for dataset in ('EMBER2018','EMBER2024'):
        p = Path('outputs/primary_confirmation')/dataset/'round_1/results.json'
        if not p.exists():
            raise FileNotFoundError(p)
        for r in read_json(p)['rows']:
            if r['family'] == 'cross_3view_stress':
                confirmations.append(r)
    write_json(out/'cross_confirmation_original.json', confirmations)
    pd.DataFrame([dict(dataset=r['dataset'],seed=r['seed'],family=r['family'],rate=r['rate'],
        n_eligible=r['n_eligible'],clean_trigger_asr=r['clean_trigger_asr']['rate'],poisoned_asr=r['asr']['rate'],
        paired_gain=r['paired_gain'],paired_new_count=r['new_evasions']['count'],paired_lost_count=r['lost_evasions']['count'],
        paired_new_rate=r['new_evasions']['rate'],paired_lost_rate=r['lost_evasions']['rate'],
        accuracy_drop=r['accuracy_drop'],strong=r['strong'],stealth=r['stealth']) for r in confirmations]).to_csv(out/'cross_confirmation_diagnostics.csv',index=False)
    fig, axs = plt.subplots(1,2,figsize=(12,5),layout='constrained')
    for ax,dataset in zip(axs,('EMBER2018','EMBER2024')):
        q = summary[(summary.dataset==dataset)&(summary.cohort=='restricted')&(summary.group=='successful_eligible')]
        ax.barh([DISPLAY.get(m,m) for m in q.method],q.tpr_mean*100)
        ax.set(title=dataset, xlabel='Mean TPR at empirical FPR <= 1% (%)', xlim=(0,100))
        ax.grid(axis='x',alpha=.2)
    fig.savefig(out/'same_fpr_restricted.png',dpi=180)
    fig.savefig(out/'same_fpr_restricted.pdf')
    plt.close(fig)
    curve_rows=[]
    for dataset,cohort in [('EMBER2018','restricted'),('EMBER2024','restricted'),('EMBER2024','cross')]:
        fig,ax=plt.subplots(figsize=(7,5.6),layout='constrained')
        for (ds,co,method),values in curves.items():
            if ds!=dataset or co!=cohort:continue
            mean=np.mean(values,axis=0)
            ax.step(grid*100,mean*100,where='post',label=f'{DISPLAY.get(method,method)} (n={len(values)})')
            curve_rows.extend(dict(dataset=ds,cohort=co,method=method,runs=len(values),fpr_budget=float(x),mean_tpr=float(y)) for x,y in zip(grid,mean))
        ax.set(xlabel='Empirical FPR budget (%)',ylabel='Mean attainable TPR (%)',title=f'{dataset}: {cohort}',xlim=(0,1),ylim=(0,101))
        ax.grid(alpha=.2);ax.legend(fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.16),ncol=3)
        fig.savefig(out/f'low_fpr_{dataset}_{cohort}.png',dpi=180)
        fig.savefig(out/f'low_fpr_{dataset}_{cohort}.pdf');plt.close(fig)
    pd.DataFrame(curve_rows).to_csv(out/'low_fpr_step_curves.csv',index=False)
    if any(sha256(p)!=h for p,h in manifest.items()):
        raise ValueError('Original result changed during analysis')
    write_json(out/'manifest.json',dict(sources=manifest, source_code_sha256=sha256(__file__),
               cells=54, scope='Macro mean of per-run metrics; observed final reused; no deployment thresholds changed',
               partial_auc='sklearn standardized partial AUC at max_fpr=.01',
               seed_sd='Sample SD within dataset/family/rate/confirmation stratum, not between heterogeneous conditions',
               if_cells=int((ff.method=='SHAP-IF').sum())))


if __name__ == '__main__':
    main()
