"""Within-adapter benign-fixture diagnostic, never executes a PE."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import lightgbm as lgb
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from xsentinel.data.pe import extract_pe
from xsentinel.schema import get_schema,V2_PRIMARY
from xsentinel.baselines.scores import contributions
from xsentinel.detection.components import primary_components
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    package=ROOT/'output/teacher_revision_2026_11_03/M8_C2_FIXTURE_PROBE'
    manifest=json.loads((package/'manifest.json').read_text(encoding='utf-8'))
    attack_path=package/'attack_record.json';attack=json.loads(attack_path.read_text(encoding='utf-8'))
    if sha(attack_path)!=manifest['attack_record_sha256']:raise ValueError('Attack record changed')
    schema=get_schema(V2_PRIMARY);vectors=[];metadata=[];extraction=[]
    for fixture in ['native','managed']:
        original=next(v for v in manifest['variants'] if v['fixture']==fixture and v['variant']=='original')
        original_path=package/original['path']
        if sha(original_path)!=original['sha256']:raise ValueError('Original changed')
        x0,_=extract_pe(original_path.read_bytes());ideal=x0.copy()
        ideal[attack['trigger']['indices']]=attack['trigger']['values']
        vectors.append(ideal);metadata.append((fixture,'target_only_vector'))
        for v in manifest['variants']:
            if v['fixture']!=fixture:continue
            path=package/v['path']
            if sha(path)!=v['sha256']:raise ValueError('Fixture bytes changed')
            x,meta=extract_pe(path.read_bytes());vectors.append(x);metadata.append((fixture,v['variant']))
            extraction.append(meta)
    X=np.asarray(vectors,dtype=np.float32);rows=[];models=[]
    readiness=json.loads((ROOT/'output/teacher_revision_2026_11_04/m8_next_stage/READINESS.json').read_text(encoding='utf-8'))
    for item in readiness['model_artifacts']:
        # Use paths under this checkout, avoiding absolute-path drift in historical notes.
        base=ROOT/'outputs/primary/EMBER2018/protocol_v2/seed_17'
        path=base/'clean.txt' if item['role']=='clean' else base/'concentrated_structural/rate_0.02/poisoned.txt'
        if sha(path)!=item['sha256']:raise ValueError('Model differs from reviewed readiness artifact')
        model=lgb.Booster(model_str=path.read_text(encoding='utf-8'));schema.check_model(model)
        prob=model.predict(X,num_threads=4);phi=contributions(model,X,schema=schema.version)
        scores,shares,_=primary_components(phi,prob,schema.version,methods={'M3_view_mass'})
        for i,(fixture,variant) in enumerate(metadata):
            row={'model':item['role'],'fixture':fixture,'variant':variant,'malware_probability':float(prob[i]),
                 'vmc':float(scores['M3_view_mass'][i]),'total_absolute_shap':float(np.abs(phi[i]).sum()),
                 'argmax_view':max(shares,key=lambda v:shares[v][i])}
            for view,indices in schema.views.items():
                row[view+'_absolute_mass']=float(np.abs(phi[i,indices]).sum());row[view+'_share']=float(shares[view][i])
            rows.append(row)
        models.append({'role':item['role'],'sha256':sha(path),'path':path.relative_to(ROOT).as_posix()})
        np.savez_compressed(out/(item['role']+'_attributions.npz'),X=X,phi=phi,probability=prob,
                            fixture=np.array([k[0] for k in metadata]),variant=np.array([k[1] for k in metadata]))
    deltas=[]
    for model in ['clean','poisoned']:
        for fixture in ['native','managed']:
            lookup={r['variant']:r for r in rows if r['model']==model and r['fixture']==fixture}
            deltas.append({'model':model,'fixture':fixture,'ideal_minus_original_vmc':lookup['target_only_vector']['vmc']-lookup['original']['vmc'],
                'physical_minus_ideal_vmc':lookup['full_c2']['vmc']-lookup['target_only_vector']['vmc'],
                'physical_minus_original_vmc':lookup['full_c2']['vmc']-lookup['original']['vmc']})
    with (out/'SCORES.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    report={'scope':'Within-model modern-adapter diagnostic on two benign fixtures; no malware ASR/recall or legacy-extractor parity claim',
        'models':models,'manifest_sha256':sha(package/'manifest.json'),'script_sha256':sha(Path(__file__)),
        'schema_sha256':schema.fingerprint,'extraction_metadata':extraction,'score_rows':rows,'deltas':deltas,
        'pe_execution':'NEVER','legacy_extractor_parity':'NOT_ESTABLISHED'}
    (out/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'deltas':deltas,'score_rows':len(rows),'output':str(out)}))
if __name__=='__main__':main()
