"""Summarize completed fresh evaluations without pooling reused IDs as samples."""
import argparse,itertools,json,sys
from pathlib import Path
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.revision.calibration_v2 import exact_interval


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evaluations',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();root=Path(a.evaluations);out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    frames=[];pair_rows=[];sources={};no_valid=[]
    for dataset in ('EMBER2018','EMBER2024'):
        directory=root/dataset
        if read_json(directory/'COMPLETE.json')['status']!='DATASET_EVALUATED_ALL_ATTEMPTS_RETAINED':raise ValueError('Dataset incomplete')
        df=pd.read_csv(directory/'per_attempt.csv');frames.append(df)
        no_valid.extend(read_json(directory/'NO_VALID_ARMS.json'))
        sources[str(directory/'per_attempt.csv')]=sha256(directory/'per_attempt.csv')
        for seed in (17,29,43):
            attempts=df[df.seed==seed][['kind','label','fingerprint']].drop_duplicates()
            cases=[]
            for r in attempts.to_dict('records'):
                path=directory/f'seed_{seed}'/r['fingerprint'];state=read_json(path/'RESULTS.json')
                if sha256(path/'scores.npz')!=state['scores_sha256']:raise ValueError('Score cache changed')
                with np.load(path/'scores.npz') as z:arrays={k:z[k] for k in z.files}
                cases.append((r,state,arrays))
            for left,right in itertools.combinations(cases,2):
                l,ls,la=left;r,rs,ra=right
                if not np.array_equal(la['malware_ids'],ra['malware_ids']):raise ValueError('Common-source alignment mismatch')
                common=la['successful']&ra['successful'];n=int(common.sum())
                for method in ls['methods']:
                    lf=la['triggered_'+method]>ls['methods'][method]['tau']
                    rf=ra['triggered_'+method]>rs['methods'][method]['tau']
                    lc=int(lf[common].sum());rc=int(rf[common].sum())
                    pair_rows.append({'dataset':dataset,'seed':seed,'left':l['kind']+'/'+l['label'],
                        'right':r['kind']+'/'+r['label'],'method':method,'common_success_n':n,
                        'left_tp':lc,'right_tp':rc,'left_recall':lc/n if n else None,'right_recall':rc/n if n else None,
                        'left_cp95':exact_interval(lc,n) if n else None,'right_cp95':exact_interval(rc,n) if n else None})
    df=pd.concat(frames,ignore_index=True);df.to_csv(out/'all_attempts.csv',index=False)
    summaries=[]
    for cohort in ('all_attempts','confirmed_only'):
        selected=df if cohort=='all_attempts' else df[df.confirmed]
        for key,group in selected.groupby(['dataset','kind','label','method']):
            summaries.append(dict(zip(['dataset','kind','label','method'],key),cohort=cohort,
                cells=len(group),seeds=group.seed.nunique(),macro_recall=group.recall.mean(),
                recall_sample_sd=group.recall.std(ddof=1),macro_fpr=group.fpr.mean(),
                fpr_sample_sd=group.fpr.std(ddof=1),macro_post_defense_asr=group.post_defense_asr.mean()))
    pd.DataFrame(summaries).to_csv(out/'macro_seed_summary.csv',index=False)
    pd.DataFrame(pair_rows).to_csv(out/'common_success_comparisons.csv',index=False)
    write_json(out/'NO_VALID_ARMS.json',no_valid)
    write_json(out/'RESULTS.json',{'status':'FRESH_EVALUATION_SUMMARIZED','rows':len(df),
        'pair_rows':len(pair_rows),'sources':sources,'code_sha256':sha256(__file__),
        'declared_static_attempts':36,'declared_adaptive_arms':12,'no_valid_arms':len(no_valid),
        'interpretation':'Macro over cells; sample SD across available seeds. No pooling of repeated IDs into independent binomial trials.',
        'zero_denominators':'N/A; excluded from numerical macro means, with cell counts retained in all_attempts.csv'})


if __name__=='__main__':main()
