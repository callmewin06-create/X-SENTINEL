"""Local deployment package: all primary bundles, no secrets, DB dump or binary."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parent))
from package_revision_artifact import RESTORE

VERIFY = '''import argparse,hashlib,json,zipfile
p=argparse.ArgumentParser();p.add_argument('zip');a=p.parse_args()
with zipfile.ZipFile(a.zip) as z:
 m=json.loads(z.read('artifact_manifest.json'));seen=set()
 for name,info in m['files'].items():
  if name=='.env' or name.endswith(('.dump','.exe','.dll')):raise ValueError('Unexpected private/binary file')
  if info['entry'] not in seen:
   with z.open(info['entry']) as source:h=hashlib.file_digest(source,'sha256').hexdigest()
   if h!=info['sha256']:raise ValueError('Checksum mismatch: '+name)
   seen.add(info['entry'])
 bundles=[name for name in m['files'] if name.startswith('outputs/primary/') and name.endswith('/bundle.json')]
 if len(bundles)!=108:raise ValueError('Expected 108 primary bundles')
 print(json.dumps({'verified_unique_blobs':len(seen),'bundles':len(bundles),'files':len(m['files']),'secrets_included':False}))
'''


def main():
    out = Path('output/delivery_2026_10_14')
    target = out / 'X_SENTINEL_Deployment.zip'
    if target.exists(): raise FileExistsError('Existing package is preserved')
    paths = set()
    for folder, patterns in {'src':['*.py','*.txt'], 'dashboard':['*.py'], 'configs':['*.json'],
                             'database':['*.py','*.ini','*.mako'], 'tests':['*.py'],
                             'docs/upstream':['*.py','*.txt','*.md']}.items():
        for pattern in patterns: paths.update(Path(folder).rglob(pattern))
    for name in ('README.md','Dockerfile','compose.yaml','pyproject.toml','.env.example','.gitignore',
                 '.dockerignore','.streamlit/config.toml','docs/DELIVERY_2026_10_14.md',
                 'docs/REVISION_2026_10_13.md','docs/plans/KE_HOACH_TIEP_TUC_VA_GIAO_DIEN_2026_10_14.md'):
        paths.add(Path(name))
    paths.update(Path('scripts').glob('*.py'))
    paths.update(Path('scripts').glob('*.ps1'))
    bundles=list(Path('outputs/primary').rglob('bundle.json'))
    assert len(bundles)==108
    for bundle in bundles: paths.update(p for p in bundle.parent.iterdir() if p.is_file())
    for name in ('X_SENTINEL_Report_With_Deployment.docx','X_SENTINEL_Demo_Reviewed.pptx',
                 'ui_result.jpg','ui_history.jpg','ui_features.jpg'):
        paths.add(out/name)
    evidence=Path('outputs/delivery_2026_10_14/stack_v10')
    for name in ('verification.json','restore.json','pe_service.json','history_compatibility.json',
                 'dashboard_linux.json','dashboard_windows.json','after/baseline.json'):
        paths.add(evidence/name)
    paths.add(Path('outputs/delivery_2026_10_14/tests_final.xml'))
    records={};seen=set()
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
        for file in sorted(paths):
            if not file.is_file():raise FileNotFoundError(file)
            if '__pycache__' in file.parts or file.suffix.lower() in ('.exe','.dll','.dump'):raise ValueError(file)
            with file.open('rb') as source:digest=hashlib.file_digest(source,'sha256').hexdigest()
            blob='blobs/'+digest
            records[file.as_posix()]={'sha256':digest,'bytes':file.stat().st_size,'entry':blob}
            if digest not in seen:z.write(file,blob);seen.add(digest)
        manifest={'version':'xsentinel-local-deployment-20261014','files':records,'bundles':108,
                  'reference_vectors_included':True,'raw_archives_included':False,'secrets_included':False,
                  'database_backup_included':False,'binary_executables_included':False,'second_machine_tested':False}
        z.writestr('artifact_manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
        z.writestr('restore_deployment.py',RESTORE);z.writestr('verify_deployment.py',VERIFY)
        z.writestr('README.txt','Local deployment package. Reference vectors required by detector bundles are included.\nExtract verify_deployment.py and restore_deployment.py next to this ZIP, verify, then restore into an empty directory.\nRead docs/DELIVERY_2026_10_14.md in the restored project. Physical second-machine acceptance is pending.\nNo passwords, DB dump, PE binaries or raw data archives are included.\n')
    (out/'restore_deployment.py').write_text(RESTORE,encoding='utf8')
    (out/'verify_deployment.py').write_text(VERIFY,encoding='utf8')
    result=subprocess.run([sys.executable,str(out/'verify_deployment.py'),str(target)],capture_output=True,text=True)
    if result.returncode:raise RuntimeError(result.stderr)
    check=json.loads(result.stdout)
    with target.open('rb') as source:check['zip_sha256']=hashlib.file_digest(source,'sha256').hexdigest()
    check.update({'bytes':target.stat().st_size,'second_machine_tested':False})
    (out/'package_verification.json').write_text(json.dumps(check,indent=2),encoding='utf8')
    print(json.dumps(check,indent=2))


if __name__=='__main__':main()
