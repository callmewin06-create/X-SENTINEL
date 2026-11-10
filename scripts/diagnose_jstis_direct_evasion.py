"""Fixed historical Development-only coordinate/view restoration diagnostic.

No optimization, retraining, or final-set access. Does not establish population
causality or problem-space realizability of restored feature vectors.
"""
import argparse
import csv
from pathlib import Path
import sys
import lightgbm as lgb
import numpy as np

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.primary_workflow import open_roles
from xsentinel.attacks.primary import VectorTrigger


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',required=True); a=p.parse_args()
    out=Path(a.output)
    if out.exists() and any(out.iterdir()): raise FileExistsError('Fresh output required')
    out.mkdir(parents=True,exist_ok=True); rows=[]; sources={}; chosen={}
    def load(path):
        sources[str(path.relative_to(ROOT))]=sha256(path)
        return lgb.Booster(model_str=path.read_text(encoding='utf8'))
    for dataset in ('EMBER2018','EMBER2024'):
        state,schema,roles=open_roles(ROOT/'data/primary'/dataset/'protocol_v2',['development'])
        dev=roles['development']; indices=np.flatnonzero(dev['y']==1)
        indices=indices[np.argsort(dev['ids'][indices])][:100]
        X=np.asarray(dev['X'][indices]); chosen[dataset]=dev['ids'][indices].tolist()
        # This ID selection is frozen before querying any clean/poisoned model.
        write_json(out/'fixed_development_ids.json',chosen)
        for seed in (17,29,43):
            root=ROOT/'outputs/primary'/dataset/'protocol_v2'/f'seed_{seed}'
            clean=load(root/'clean.txt'); eligible=clean.predict(X,num_threads=4)>=.5
            for attack in sorted(root.glob('*/rate_*/attack.json')):
                record=read_json(attack); trigger=VectorTrigger(**record['trigger']); base=trigger.apply(X,schema)
                poisoned=load(attack.parent/'poisoned.txt')
                sources[str(attack.relative_to(ROOT))]=sha256(attack)
                variants=[('original','',X),('full_trigger','',base)]
                for j in trigger.indices:
                    restored=base.copy(); restored[:,j]=X[:,j]
                    variants.append(('restore_coordinate',str(j),restored))
                for view in schema.views:
                    touched=[j for j in trigger.indices if schema.view_labels[j]==view]
                    if not touched: continue
                    restored=base.copy(); restored[:,touched]=X[:,touched]
                    variants.append(('restore_view',view,restored))
                for kind,restored,x in variants:
                    before=clean.predict(x,num_threads=4)<.5; after=poisoned.predict(x,num_threads=4)<.5
                    n=int(eligible.sum()); b=before[eligible]; q=after[eligible]
                    rows.append({'dataset':dataset,'seed':seed,'family':trigger.family,'rate':record['requested_rate'],
                        'variant':kind,'restored':restored,'subset_n':len(X),'eligible_n':n,
                        'clean_evasion_n':int(b.sum()),'poisoned_evasion_n':int(q.sum()),
                        'clean_asr':float(b.mean()) if n else None,'poisoned_asr':float(q.mean()) if n else None,
                        'paired_new_n':int((q&~b).sum()),'paired_lost_n':int((b&~q).sum()),
                        'paired_gain':float((q.astype(int)-b.astype(int)).mean()) if n else None,
                        'trigger_indices':','.join(map(str,trigger.indices)),
                        'trigger_values':','.join(map(str,trigger.values)),
                        'trigger_views':','.join(schema.view_labels[j] for j in trigger.indices)})
                print(dataset,seed,trigger.family,record['requested_rate'],flush=True)
    with (out/'restoration.csv').open('w',encoding='utf8',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    if any(sha256(ROOT/p)!=h for p,h in sources.items()): raise ValueError('Frozen artifact changed')
    write_json(out/'RESULTS.json',{'status':'HISTORICAL_DEVELOPMENT_DIAGNOSTIC_COMPLETE','rows':len(rows),
        'subset_rule':'100 lexical Development malware IDs per dataset before querying models',
        'heldout_features_opened':[],'model_sha256':sources,'code_sha256':sha256(__file__),
        'interpretation':'Feature restoration is a controlled model diagnostic, not a valid binary edit or population-causal estimate'})


if __name__=='__main__': main()
