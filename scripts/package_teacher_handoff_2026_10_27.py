"""Small shareable handoff: tables, figures, source snapshots; no binaries/models."""
import importlib.metadata
import platform
import shutil
import sys
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from xsentinel.utils import read_json,write_json,sha256

ROOT=Path('outputs/teacher_revision_2026_10_27')
OUT=Path('output/teacher_revision_2026_10_27')


def main():
    assert read_json(ROOT/'audit.json')['status']=='passed'
    files=list(Path('scripts').glob('*2026_10_27.py'))
    files += [Path('src/xsentinel')/p for p in ('revision/low_fpr.py','revision/reviewer_core.py','revision/training_filters.py','baselines/shap_outlier.py')]
    files += [Path('tests')/p for p in ('test_reviewer_core.py','test_reviewer_metrics.py','test_training_control.py')]
    for p in files:
        dest=OUT/'source_snapshot'/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    for sub in ('shap_if','adaptive_multiview','ember2024_seeds_v2','clean_budget','training_defense_v2'):
        source=ROOT/sub/'protocol.json'
        dest=OUT/'protocols'/(sub+'.json');dest.parent.mkdir(exist_ok=True);shutil.copy2(source,dest)
    evidence=OUT/'evidence';evidence.mkdir(exist_ok=True)
    for p in (ROOT/'original_input_manifest.json',ROOT/'adaptive_multiview/reproduction_seeds.json',ROOT/'analysis/manifest.json'):
        shutil.copy2(p,evidence/(p.parent.name+'_'+p.name))
    for sub in ('ember2024_seeds_v2','training_defense_v2'):
        for p in (ROOT/sub).glob('*/result.json'):
            shutil.copy2(p,evidence/(sub+'_'+p.parent.name+'.json'))
    write_json(OUT/'environment.json',dict(python=sys.version,platform=platform.platform(),
        versions={p:importlib.metadata.version(p) for p in ('numpy','pandas','scipy','scikit-learn','lightgbm','joblib','matplotlib','pytest')},
        note='Use the existing project, original data/models and .venv; source_snapshot is a review copy, not a standalone installation'))
    manifest=read_json(OUT/'delivery_manifest.json')
    manifest['files']={str(p.relative_to(OUT)):sha256(p) for p in OUT.rglob('*') if p.is_file() and p.name!='delivery_manifest.json'}
    write_json(OUT/'delivery_manifest.json',manifest)
    archive=OUT.parent/'X_SENTINEL_REVIEW_2026_10_27.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():z.write(p,'X_SENTINEL_REVIEW_2026_10_27/'+p.relative_to(OUT).as_posix())
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    write_json(ROOT/'package_verification.json',dict(path=str(archive),sha256=sha256(archive),bytes=archive.stat().st_size,
        files=len(manifest['files'])+1,contains_raw_binaries=False,contains_model_weights=False))
    audit=read_json(ROOT/'audit.json')
    note=f'''# Research revisions completed27 October2026

## Verified deliverables

- Signed SHAP Isolation Forest:54 original cells, matched unmodified-malware controls and separately calibrated thresholds.
- Retrospective empirical-FPR-cap comparisons and standardized partial AUC, with original deployment thresholds retained.
- Cross confirmation/final diagnostics and24-cell bounded multiview adaptation.
- EMBER2024 spread2% seeds59 and71: five attempts including the original three, four confirmed; unsuccessful seed retained.
- Five nested labelled-fit budgets on both datasets and three seeds:30 budget checkpoints and810 method/configuration rows.
- Two-cell training sanitization experiment with independently sampled random-removal control and retraining utility measurements.
- {audit['regression_tests']} regression tests passed; {audit['original_assets_verified']} original assets in the protection manifest rechecked; cached metrics and source IDs audited.

Delivery: output/teacher_revision_2026_10_27/ and output/X_SENTINEL_REVIEW_2026_10_27.zip.
Detailed score/model evidence remains in outputs/teacher_revision_2026_10_27/. The small shareable archive contains tables, figures, protocols and source snapshots, not raw executable samples or model weights.

## Corrections during implementation

ember2024_seeds_v2 supersedes v1 scoring. Exact training checkpoints and triggers were reused, with calibration scored as a whole2000-row batch and final core scoring in128-row batches to match primary conventions. Native floating-point differences can affect ECDF ranks at exact ties; no arbitrary-batch bit-invariance is claimed.

training_defense_v2 supersedes the invalid v1 random-removal control. The earlier control accidentally used the same PCG64 seed as poison selection and therefore removed all selected poisons. The corrected control uses independent fixed seed20261027. Valid IF masks and model checkpoints were matched and retained; invalid random-control results are excluded from delivery tables. Source snapshots and the invalidity note remain for provenance.

## Interpretation and outstanding work

These changes add evidence and repair the evaluation framing. They do not remove Cross/adaptive weaknesses or establish binary trigger realizability. Reduced is the proposed primary setting; Full has conditional data-budget behavior, with no universal advantage over Shadow.

Quân's canonical Word and Phúc's binary results were not available. English manuscript inserts, figure captions and integration instructions are supplied; canonical Word editing/render QA and binary integration remain pending those artifacts. Phú's complete bibliography audit remains a separate team task.

No commit or push was performed for this research package.
'''
    Path('docs/REVIEW_REPAIR_2026_10_27.md').write_text(note,encoding='utf8')
    print('Packaged',archive,archive.stat().st_size,'bytes',flush=True)


if __name__=='__main__':main()
