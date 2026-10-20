"""Evaluate locked choices and fixed controls once on new local source IDs."""
import gc,json,sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import lightgbm as lgb
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.detection.detector import Detector
from xsentinel.attacks.primary import VectorTrigger
from xsentinel.revision.scoring import core_scores
from xsentinel.revision.fusion import fusion_scores
from xsentinel.revision.analysis import attack_groups,revised_metrics
from explore_fusion_2026_10_20 import OUT,save_csv


def main():
    selection=read_json(OUT/'selection.json');protocol=read_json(OUT/'final_pool/protocol.json')
    assert sha256(OUT/'selection.json')==protocol['fusion_choice_sha256']
    assert sha256(OUT/'thresholds.json')==selection['thresholds_sha256']
    assert all(sha256(path)==digest for path,digest in selection['source_ledger'].items())
    thresholds=read_json(OUT/'thresholds.json');rows=[];ledger={}
    for dataset in ('EMBER2018','EMBER2024'):
        source=OUT/'final_pool'/dataset;state=read_json(source/'dataset.json')
        assert all(sha256(source/key)==value for key,value in state['hashes'].items())
        X=np.load(source/'X.npy');y=np.load(source/'y.npy');ids=np.load(source/'ids.npy')
        benign=X[y==0];malware=X[y==1];clean_models={}
        for cell in sorted((Path('outputs/primary')/dataset/'protocol_v2').glob('seed_*/*/rate_*')):
            old=read_json(cell/'result.json')
            cell_id=f"{dataset}/seed_{old['seed']}/{old['family']}/rate_{old['rate']}"
            dest=OUT/'final_results'/cell_id;dest.mkdir(parents=True,exist_ok=True)
            report=dest/'metrics.json'
            if report.exists():
                previous=read_json(report)
                assert previous['selection_sha256']==sha256(OUT/'selection.json')
                assert previous['source_manifest_sha256']==sha256(source/'dataset.json')
                assert previous['cache_sha256']==sha256(dest/'scores.npz')
                rows.extend(previous['rows']);continue
            detector=Detector.load(cell/'bundle_full')
            trigger=VectorTrigger(**read_json(cell/'attack.json')['trigger'])
            xt=trigger.apply(malware,detector.schema)
            positive,extra=core_scores(detector,xt);negative,_=core_scores(detector,benign)
            if old['seed'] not in clean_models:
                clean_models[old['seed']]=lgb.Booster(model_file=str(cell.parents[1]/'clean.txt'))
            clean=clean_models[old['seed']]
            groups=attack_groups(clean.predict(malware,num_threads=4),extra['malware_probability'],clean.predict(xt,num_threads=4))
            cell_rows=[];cache={'benign_ids':ids[y==0],'malware_ids':ids[y==1],
                               **{'group_'+key:value for key,value in groups.items()}}
            for variant,m4 in [('reduced','M4_shap_behavioral_conflict'),('full','M4_prob_gap')]:
                ps=fusion_scores(positive['M3_view_mass'],positive[m4],detector.rank_reference['M3_view_mass'],detector.rank_reference[m4])
                ns=fusion_scores(negative['M3_view_mass'],negative[m4],detector.rank_reference['M3_view_mass'],detector.rank_reference[m4])
                rules=list(dict.fromkeys([selection['choices'][variant],'W50','M3','M4']))
                for name in rules+['M3_raw','M4_raw']:
                    if name.endswith('_raw'):
                        component='M3_view_mass' if name=='M3_raw' else m4
                        p,n,tau=positive[component],negative[component],detector.thresholds[component]
                    else:p,n,tau=ps[name],ns[name],thresholds[cell_id+'/'+variant][name]
                    metric=revised_metrics(p,n,tau,groups)
                    cache[variant+'_positive_'+name]=p;cache[variant+'_negative_'+name]=n
                    row={'cell':cell_id,'dataset':dataset,'family':old['family'],'seed':old['seed'],'rate':old['rate'],
                         'confirmed':old['independently_confirmed_strong_and_stealth'],'variant':variant,'rule':name,
                         'selected':name==selection['choices'][variant],'tau':tau,
                         'recall':metric['recall_successful_eligible']['rate'],'successful_n':metric['recall_successful_eligible']['n'],
                         'caught_n':metric['recall_successful_eligible']['count'],'fpr':metric['benign_fpr']['rate'],
                         'false_positives':metric['benign_fpr']['count'],'benign_n':len(benign),
                         'post_asr':metric['post_defense_asr']['rate'],'eligible_n':int(groups['eligible'].sum()),
                         'unblocked_n':int(np.sum(groups['successful_eligible'] & ~(p>tau)))}
                    rows.append(row);cell_rows.append(row)
            np.savez_compressed(dest/'scores.npz',**cache)
            for path in (cell/'bundle_full/bundle.json',cell/'attack.json',source/'dataset.json'):
                ledger[path.as_posix()]=sha256(path)
            write_json(report,{'selection_sha256':sha256(OUT/'selection.json'),
                'source_manifest_sha256':sha256(source/'dataset.json'),'cache_sha256':sha256(dest/'scores.npz'),
                'primary_model_sha256':sha256(cell/'bundle_full/main.txt'),'rows':cell_rows})
            print('New Final',cell_id,flush=True)
            del detector,positive,negative,extra,xt;gc.collect()
        del X,benign,malware,clean_models;gc.collect()
    save_csv(OUT/'final_cells.csv',rows)
    groups=defaultdict(list)
    for row in rows:
        if row['confirmed']:
            groups[(row['dataset'],'cross' if row['family']=='cross_3view_stress' else 'restricted',row['variant'],row['rule'])].append(row)
    summary=[]
    for (dataset,cohort,variant,rule),items in groups.items():
        summary.append({'dataset':dataset,'cohort':cohort,'variant':variant,'rule':rule,'runs':len(items),
                        **{key:float(np.mean([x[key] for x in items if x[key] is not None]))
                           if any(x[key] is not None for x in items) else None for key in ('recall','fpr','post_asr')}})
    save_csv(OUT/'final_cohorts.csv',summary)
    write_json(OUT/'validation.json',{'scope':'New source IDs disjoint from known local primary/pilot/old Fresh roles; external observation history unavailable',
        'selected_choices':selection['choices'],'selection_sha256':sha256(OUT/'selection.json'),
        'rows':len(rows),'summary':summary,'source_ledger':ledger,'primary_policy':'Frozen W50 deployment unchanged; no tuning from this Final',
        'dependence':'Same 1000 benign and 1000 malware source IDs per dataset reused across fixed models; run averages are not independent replicates'})


if __name__=='__main__':main()
