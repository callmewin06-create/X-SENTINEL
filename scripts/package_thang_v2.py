"""Package review artifacts and new code, excluding datasets/secrets/test scratch."""
import sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from xsentinel.utils import read_json,write_json,sha256
from analyze_fusion_overlap import ROOT

def main():
    manifest=read_json(ROOT/'handoff/deliverable_manifest.json')
    assert manifest['verified_counts']=={'raw_baselines':54,'view3':54,'public_shadow':27}
    out=Path('output/thang_revision_v2_2026_10_30');out.mkdir(parents=True,exist_ok=True)
    archive=out/'THANG_REVIEW_V2_2026_10_30.zip'
    code=list(read_json(ROOT/'protocol.json')['code_hashes'])
    files=set(Path(p) for p in code)
    files.update([Path(__file__),Path('tests/test_revision_v2.py'),Path('docs/THANG_REVISION_V2_HANDOFF_2026_10_30.md'),Path('docs/plans/KE_HOACH_TASK_THANG_GOP_Y_V2_2026_10_30.md')])
    for p in ROOT.rglob('*'):
        if p.is_file() and not any(part.startswith('test_tmp') for part in p.parts) and p.suffix in ['.json','.csv','.md','.png','.pdf','.npz','.txt']:
            files.add(p)
    readme=('Review package for the six assigned Thang work packages, plus view3 and random-control audit.\n'
        'Includes saved scores, public Shadow model, tables, figures and new scripts.\n'
        'Original frozen primary models, EMBER arrays and downloaded BODMAS corpus are NOT bundled.\n'
        'To reproduce, use the original Project checkout and its frozen data/model artifacts.\n'
        'No new independent validation or production-FPR certification is claimed.\n'
        'M3/M8/M9 and additional original-Severi-selector experiments remain team dependencies.\n')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('README_REVIEW.txt',readme)
        for p in sorted(files):z.write(p,p.as_posix())
    write_json(out/'package_manifest.json',dict(archive=str(archive),sha256=sha256(archive),bytes=archive.stat().st_size,
        files={str(p):sha256(p) for p in sorted(files)},scope=readme))
    print(archive,archive.stat().st_size)

if __name__=='__main__':main()
