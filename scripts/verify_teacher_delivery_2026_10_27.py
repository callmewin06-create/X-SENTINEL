"""Check the final handoff archive and cross-table arithmetic."""
import hashlib
import sys
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
from xsentinel.utils import read_json,write_json,sha256


def main():
    root=Path('outputs/teacher_revision_2026_10_27');out=Path('output/teacher_revision_2026_10_27')
    manifest=read_json(out/'delivery_manifest.json');package=read_json(root/'package_verification.json')
    assert sha256(package['path'])==package['sha256']
    with zipfile.ZipFile(package['path']) as z:
        assert z.testzip() is None
        for name,digest in manifest['files'].items():
            assert sha256(out/name)==digest
            data=z.read('X_SENTINEL_REVIEW_2026_10_27/'+name.replace('\\','/'))
            assert hashlib.sha256(data).hexdigest()==digest
        assert z.read('X_SENTINEL_REVIEW_2026_10_27/delivery_manifest.json')==(out/'delivery_manifest.json').read_bytes()
        assert not any(Path(n).suffix.lower() in ('.exe','.dll','.joblib','.npz','.npy') for n in z.namelist())
    for name,count in [('fixed_threshold_per_run.csv',540),('same_fpr_per_run.csv',2160),('clean_budget_per_run.csv',810),('adaptive_per_run.csv',24),('ember2024_seed_runs.csv',5),('training_defense_results.csv',4)]:
        assert len(pd.read_csv(out/name))==count,(name,count)
    seeds=pd.read_csv(out/'ember2024_seed_runs.csv');assert seeds.confirmed.sum()==4 and not seeds[seeds.seed==71].confirmed.iloc[0]
    b=pd.read_csv(out/'clean_budget_summary.csv');s=pd.read_csv(out/'same_fpr_summary.csv')
    for r in b[b.budget==200000].itertuples(index=False):
        match=s[(s.dataset==r.dataset)&(s.cohort==r.cohort)&(s.method==r.method)&(s.group=='successful_eligible')].iloc[0]
        np.testing.assert_allclose([r.low_fpr_tpr,r.low_fpr_fpr],[match.tpr_mean,match.fpr_mean],rtol=0,atol=1e-12)
    assert '| EMBER2024 | cross | Reduced | 9 | 0.0023 |' in (out/'PAPER_INSERTS_EN.md').read_text(encoding='utf8')
    assert read_json(out/'audit.json')['regression_tests']==39
    write_json(root/'delivery_checks.json',dict(status='passed',archive_sha256=package['sha256'],
        files_verified=len(manifest['files'])+1,budget_endpoint_matches_original_comparison=True,
        low_nonzero_recall_preserved=True,raw_executables_and_model_weights_absent=True))
    print('Final archive and cross-table checks passed',flush=True)


if __name__=='__main__':main()
