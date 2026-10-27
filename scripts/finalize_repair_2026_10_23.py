"""Verify preservation, exercise read-only follow-up, and package this supplement."""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zipfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / 'outputs/repair_2026_10_23'
OUT = ROOT / 'output/repair_2026_10_23'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf8')


def check_followup():
    folder = QA / 'followup_tool_qa'
    samples = folder / 'samples'
    samples.mkdir(parents=True, exist_ok=True)
    valid = bytearray(128)
    valid[:2] = b'MZ'
    struct.pack_into('<I', valid, 0x3c, 64)
    valid[64:68] = b'PE\0\0'
    invalid = bytearray(valid)
    struct.pack_into('<I', invalid, 0x3c, 9999)
    (samples/'valid.bin').write_bytes(valid)
    (samples/'invalid.bin').write_bytes(invalid)
    manifest = folder/'cases.csv'
    with manifest.open('w', newline='', encoding='utf8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['relative_path','file_sha256'])
        writer.writeheader()
        writer.writerows([
            {'relative_path':'valid.bin','file_sha256':sha(samples/'valid.bin')},
            {'relative_path':'invalid.bin','file_sha256':sha(samples/'invalid.bin')},
            {'relative_path':'valid.bin','file_sha256':'0'*64},
            {'relative_path':'../outside.bin','file_sha256':'0'*64},
        ])
    result = folder/f'result-{uuid.uuid4().hex[:8]}.json'
    # The CLI refuses overwrite; leave prior QA evidence intact on rerun.
    if not result.exists():
        subprocess.run([sys.executable,str(ROOT/'scripts/inspect_bodmas_failures.py'),
            '--input-dir',str(samples),'--errors-csv',str(manifest),'--out',str(result)], check=True)
    rows = json.loads(result.read_text())['rows']
    assert rows[0]['status']=='inspected' and rows[0]['passes_current_guard']
    assert rows[1]['status']=='inspected' and not rows[1]['passes_current_guard']
    assert rows[2]['status']=='unresolved' and not rows[2]['bytes_match']
    assert rows[3]['status']=='unresolved' and 'Invalid relative path' in rows[3]['error']
    rejected = subprocess.run([sys.executable,str(ROOT/'scripts/inspect_bodmas_failures.py'),
        '--input-dir',str(samples),'--errors-csv',str(manifest),'--out',str(samples/'refused.json')],
        capture_output=True, text=True)
    assert rejected.returncode != 0 and not (samples/'refused.json').exists()
    return {'synthetic_cases':4,'all_passed':True,'output_inside_samples_rejected':True,
            'real_25_bodmas_files_inspected':False}


def make_zip(path, entries):
    hashes = []
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as archive:
        for source,name in sorted(entries,key=lambda x:x[1]):
            archive.write(source,name)
            hashes.append(f'{sha(source)}  {name}')
        archive.writestr('SHA256SUMS.txt','\n'.join(hashes)+'\n')
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        for line in archive.read('SHA256SUMS.txt').decode().splitlines():
            digest,name = line.split('  ',1)
            assert hashlib.sha256(archive.read(name)).hexdigest()==digest
    return {'name':path.name,'files':len(entries),'sha256':sha(path),'crc_and_hashes_verified':True}


def main():
    before = json.loads((QA/'primary_before.json').read_text())
    mismatches = [name for name,digest in before.items() if not (ROOT/name).is_file() or sha(ROOT/name)!=digest]
    assert not mismatches,mismatches
    assert sha(ROOT/'BODMAS_RESULTS.zip')=='c528ef4931a672123d47bfd30b6e0bdc5ceb4b18d2cf5a5d296f030dc31d8a87'
    report = json.loads((QA/'report_preservation.json').read_text())
    assert sha(ROOT/'output/ieee_2026_10_16/X_SENTINEL_IEEE_1col.docx')==report['source_sha256']
    assert sha(Path(report['output']))==report['output_sha256']
    linux = json.loads((QA/'linux_acceptance/verification.json').read_text())
    windows = json.loads((QA/'benign_records.json').read_text())
    for case in linux['cases']:
        match = [r for r in windows if Path(r['path']).name=='ReviewedBenignFixture.exe'
                 and r['dataset']==case['dataset'] and r['variant']==case['variant']]
        assert len(match)==1 and match[0]['vector_sha256']==case['vector_sha256']
        assert match[0]['poisoned_p']==case['probability']
    proof = {'primary_files_checked':len(before),'primary_unchanged':True,
        'source_paper_unchanged':True,'bodmas_zip_unchanged':True,
        'windows_linux_fixture_vector_and_probability_match':True,
        'followup_tool':check_followup()}
    dump(QA/'final_preservation.json',proof)
    followup = OUT/'kali_followup'
    shutil.copy2(ROOT/'scripts/inspect_bodmas_failures.py',followup)
    shutil.copy2(ROOT/'outputs/bodmas_2026_10_23/unique_errors.csv',followup)
    packs=[make_zip(OUT/'BODMAS_FOLLOWUP_KALI.zip',[(p,p.name) for p in followup.iterdir() if p.is_file()])]
    names = ['.gitattributes','Dockerfile','dashboard/app.py','scripts/check_bodmas_static.py',
        'src/xsentinel/dashboard_input.py','src/xsentinel/dashboard_presentation.py',
        'src/xsentinel/data/pe_isolation.py','src/xsentinel/data/pe_worker.py',
        'tests/test_pe_isolation.py','tests/test_bodmas_static.py','docs/REPAIR_2026_10_23.md',
        'docs/plans/KE_HOACH_KHAC_PHUC_SAU_BODMAS_2026_10_23.md',
        'scripts/audit_repair_2026_10_23.py','scripts/diagnose_cross_2026_10_23.py',
        'scripts/inspect_bodmas_failures.py','scripts/verify_repair_runtime.py',
        'scripts/build_repair_report_2026_10_23.py','scripts/build_bodmas_report_2026_10_23.py',
        'scripts/render_repair_report_2026_10_23.ps1','scripts/render_repair_pages_2026_10_23.py',
        'scripts/finalize_repair_2026_10_23.py']
    evidence = ['benign_selection.json','benign_signatures.json','benign_records.json',
        'benign_summary.json','benign_summary.csv','benign_vectors.npz','cross_diagnosis.json',
        'pytest_verified.xml','linux_acceptance/verification.json','report_preservation.json',
        'final_preservation.json','report_visual_review.json']
    entries = [(ROOT/name,name) for name in names]
    entries += [(QA/name,'evidence/'+name) for name in evidence]
    entries += [(p,p.name) for p in OUT.iterdir() if p.is_file() and p.suffix in ('.md','.docx')]
    entries += [(OUT/'BODMAS_FOLLOWUP_KALI.zip','BODMAS_FOLLOWUP_KALI.zip')]
    packs.append(make_zip(OUT/'X_SENTINEL_REPAIR_HANDOFF.zip',entries))
    dump(QA/'package_verification.json',packs)
    print(json.dumps({'preservation':proof,'packages':packs},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
