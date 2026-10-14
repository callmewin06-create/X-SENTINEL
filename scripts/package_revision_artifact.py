"""Deduplicate model blobs and pack local review evidence without raw datasets."""
from pathlib import Path
import json,hashlib,zipfile,subprocess,sys

ROOT=Path('outputs/revision_2026_10_13');OUT=Path('output/revision_2026_10_13')
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

RESTORE='''from pathlib import Path
import argparse,json,zipfile,hashlib
p=argparse.ArgumentParser();p.add_argument('--zip',required=True);p.add_argument('--out',required=True);a=p.parse_args()
out=Path(a.out).resolve()
if out.exists() and any(out.iterdir()):raise ValueError('Restore only into an empty new directory')
out.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(a.zip) as z:
 m=json.loads(z.read('artifact_manifest.json'))
 for name,info in m['files'].items():
  dest=(out/name).resolve()
  if out not in dest.parents:raise ValueError('Unsafe relative path')
  data=z.read(info['entry'])
  if hashlib.sha256(data).hexdigest()!=info['sha256']:raise ValueError('Checksum mismatch: '+name)
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
print('Restored',len(m['files']),'verified files')
'''
VERIFY='''import zipfile,json,hashlib,statistics,argparse,csv,io
p=argparse.ArgumentParser();p.add_argument('zip');a=p.parse_args()
with zipfile.ZipFile(a.zip) as z:
 m=json.loads(z.read('artifact_manifest.json'));verified=set()
 for info in m['files'].values():
  if info['entry'] in verified:continue
  h=hashlib.sha256()
  with z.open(info['entry']) as f:
   for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
  if h.hexdigest()!=info['sha256']:raise ValueError('Corrupt entry '+info['entry'])
  verified.add(info['entry'])
 def read(path):return json.loads(z.read(m['files'][path]['entry']))
 summary=read('outputs/revision_2026_10_13/summary.json')
 cells=[read(p) for p in m['files'] if p.startswith('outputs/primary/') and p.endswith('/result.json')]
 if len(cells)!=54:raise ValueError('Expected 54 primary cells')
 aliases={'TADR':'TADR','STRIP':'STRIP','M3':'M3_view_mass','M4-R':'M4_shap_behavioral_conflict','M4-F':'M4_prob_gap','X-R':'X_primary_reduced','X-F':'X_primary_full'}
 checks=0
 for row in summary['original_cohorts']:
  chosen=[r for r in cells if r['dataset']==row['dataset'] and (row['cohort']=='all_configs' or r['independently_confirmed_strong_and_stealth']) and (row['cohort'] not in ('restricted_confirmed','cross_confirmed') or (r['family']=='cross_3view_stress')==(row['cohort']=='cross_confirmed'))]
  if len(chosen)!=row['runs']:raise ValueError('Cohort count mismatch')
  for key,stored in [('recall','recall_successful_eligible'),('fpr','benign_fpr'),('post_asr','post_defense_asr')]:
   values=[r['evaluation']['results']['full']['methods'][aliases[row['method']]][stored]['rate'] for r in chosen]
   if abs(statistics.mean(values)-row[key])>1e-12:raise ValueError('Mean mismatch')
   checks+=1
print(json.dumps({'verified_unique_entries':len(verified),'primary_cells':len(cells),'original_cohort_mean_checks':checks,'raw_data_included':False}))
'''
def main():
    out=OUT/'X_SENTINEL_Reproduction_Artifact.zip';files=set()
    files.update(Path('src').rglob('*.py'));files.update(Path('src').rglob('*_LICENSE.txt'))
    files.update(Path('tests').rglob('*.py'))
    files.add(Path('src/xsentinel/pefile_warnings.txt'))
    files.update(Path('scripts').glob('*revision*.py'));files.add(Path('scripts/render_revision_word_pages.ps1'))
    for name in ('README.md','pyproject.toml','requirements-lock.txt','configs/primary_protocol.json','configs/ember2024_sources.json','docs/REVISION_2026_10_13.md'):
        if Path(name).exists():files.add(Path(name))
    for result in Path('outputs/primary').glob('*/protocol_v2/seed_*/*/rate_*/result.json'):
        cell=result.parent
        for name in ('result.json','attack.json','paired_predictions.npz','poisoned.txt'):files.add(cell/name)
        for mode in ('bundle_full','bundle_reduced'):files.update(p for p in (cell/mode).iterdir() if p.is_file())
        files.add(cell.parents[1]/'clean.txt')
    for folder in Path('data/primary').glob('*/protocol_v2'):
        files.add(folder/'roles.json')
        for name in ('source_manifest.json','protocol.json'):
            if (folder/name).exists():files.add(folder/name)
    for p in ROOT.rglob('*'):
        if not p.is_file() or p.suffix not in ('.json','.csv','.npz','.xml','.pdf','.png'):continue
        if 'fresh_validation' in p.parts and p.name not in ('protocol.json','dataset.json','selection.json'):continue
        if 'validation_results' in p.parts and p.name in ('adaptive.json','adaptive_scores.npz'):continue
        files.add(p)
    files.update((ROOT/'fresh_validation').glob('*/ids.npy'))
    for p in OUT.rglob('*'):
        if p.name in ('artifact_package.json','artifact_verification.json'):continue
        if p.is_file() and p.suffix in ('.docx','.md','.json','.bib','.csv'):files.add(p)
    records={};seen=set()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
        for p in sorted(files):
            if not p.exists():raise FileNotFoundError(p)
            h=digest(p);entry='blobs/'+h
            records[p.as_posix()]={'sha256':h,'bytes':p.stat().st_size,'entry':entry}
            if h not in seen:z.write(p,entry);seen.add(h)
        manifest={'version':'xsentinel-local-review-artifact-v1','files':records,'unique_blobs':len(seen),
            'raw_data_included':False,'models_included':True,'public_release':False,
            'scope':'Reproduction from saved scores and fixed models; not raw-data training replication',
            'withdrawn_adaptive':'Preliminary Metadata-admitting output excluded; Structural-only v2 results included'}
        z.writestr('artifact_manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2));z.writestr('restore_artifact.py',RESTORE);z.writestr('verify_artifact.py',VERIFY)
        z.writestr('README.txt','Local research review package.\n1. python verify_artifact.py X_SENTINEL_Reproduction_Artifact.zip\n2. python restore_artifact.py --zip X_SENTINEL_Reproduction_Artifact.zip --out NEW_EMPTY_DIRECTORY\n3. Install the project environment to rerun scripts/analyze_primary_revision.py --out NEW_ANALYSIS_OUTPUT.\nRaw source data and fresh X arrays are excluded. Existing score tables, thresholds, models, source IDs and protocol evidence are included. Training replication requires licensed original archives and the original primary workflow.\n')
    (OUT/'restore_artifact.py').write_text(RESTORE,encoding='utf-8');(OUT/'verify_artifact.py').write_text(VERIFY,encoding='utf-8')
    (OUT/'artifact_package.json').write_text(json.dumps({'path':str(out),'bytes':out.stat().st_size,'sha256':digest(out),
        'files':len(records),'unique_blobs':len(seen),'models_included':True,'raw_data_included':False},indent=2),encoding='utf-8')
    print('Local artifact packed',out,out.stat().st_size,len(records),'paths',len(seen),'unique blobs',flush=True)
    check=subprocess.run([sys.executable,str(OUT/'verify_artifact.py'),str(out)],capture_output=True,text=True)
    print(check.stdout,flush=True)
    if check.returncode:raise RuntimeError(check.stderr)
    (OUT/'artifact_verification.json').write_text(check.stdout,encoding='utf-8')

if __name__=='__main__':main()
