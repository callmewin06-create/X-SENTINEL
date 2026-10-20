"""Package an explicit static-analysis kit. No downloads or sample execution."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/bodmas_demo_2026_10_19'
STAGE = OUT / 'X_SENTINEL_BODMAS_VM'
GUIDE = 'HUONG_DAN_BODMAS_KALI_2026_10_19'
PLAN = 'KE_HOACH_TRIEN_KHAI_VA_DEMO_2026_10_19'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage-only', action='store_true')
    args = parser.parse_args()
    STAGE.mkdir(parents=True, exist_ok=True)
    files = set()

    def copy(source, relative):
        source = Path(source)
        if source.is_symlink() or not source.is_file():
            raise ValueError('Expected ordinary source file: ' + str(source))
        target = STAGE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        files.add(target.relative_to(STAGE).as_posix())

    def write(relative, value):
        target = STAGE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding='utf8', newline='\n')
        files.add(target.relative_to(STAGE).as_posix())

    for dirname in ('src', 'docs/upstream', 'dashboard', '.streamlit', 'configs', 'database'):
        for path in sorted((ROOT / dirname).rglob('*')):
            if not path.is_file() or any(p in ('__pycache__', '.pytest_cache') for p in path.parts):
                continue
            if path.suffix in ('.pyc', '.pyo') or path.name == '.env':
                continue
            copy(path, path.relative_to(ROOT))
    for name in ('Dockerfile', 'pyproject.toml'):
        copy(ROOT / name, name)
    for name in ('check_bodmas_static.py', 'bodmas_run_static.sh', 'bodmas_run_matrix.sh', 'bodmas_verify_kit.py'):
        copy(ROOT / 'scripts' / name, Path('scripts') / name)
    copy(ROOT / 'tests/test_bodmas_static.py', 'tests/test_bodmas_static.py')
    copy(ROOT / 'docs' / (GUIDE + '.md'), Path('docs') / (GUIDE + '.md'))
    copy(ROOT / 'docs/plans' / (PLAN + '.md'), Path('docs') / (PLAN + '.md'))
    copy(ROOT / 'docs/plans/QUYET_DINH_5_DIEM_2026_10_19.md', 'docs/QUYET_DINH_5_DIEM_2026_10_19.md')
    for name in (GUIDE, PLAN):
        path = OUT / (name + '.docx')
        if path.exists():
            copy(path, Path('docs') / path.name)
        elif not args.stage_only:
            raise FileNotFoundError(path)
    catalog = {}
    for year in (2018, 2024):
        for variant in ('reduced', 'full'):
            rel = Path(f'EMBER{year}/protocol_v2/seed_17/spread_structural/rate_0.02/bundle_{variant}')
            source = ROOT / 'outputs/primary' / rel
            state_bytes = (source / 'bundle.json').read_bytes()
            state = json.loads(state_bytes)
            if state['method_version'] != 'xsentinel-primary-v2' or state.get('config', {}).get('enable_m5', False):
                raise ValueError('Unexpected bundle protocol')
            for path in sorted(source.iterdir()):
                if path.is_file():
                    copy(path, Path('outputs/primary') / rel / path.name)
            identity = hashlib.sha256(rel.as_posix().encode() + b'\0' + state_bytes).hexdigest()
            catalog[f'{year}-{variant}'] = {
                'id': identity, 'dataset': f'EMBER{year}', 'variant': variant,
                'schema': 'ember-v2-2381-views-v2' if year == 2018 else 'ember-v3-2568-views-v1',
                'method': f'X_primary_{variant}', 'relative_path': rel.as_posix(),
            }
    write('bundle_catalog.json', json.dumps(catalog, indent=2) + '\n')
    fixture_root = ROOT / 'outputs/revision_2026_10_13/binary_validation'
    old_validation = json.loads((fixture_root / 'validation.json').read_text(encoding='utf8'))
    for filename, key in (('ReviewedBenignFixture.exe', 'original_sha256'), ('ReviewedBenignFixture.cs', 'source_sha256')):
        if digest(fixture_root / filename) != old_validation[key]:
            raise ValueError('Reviewed fixture changed: ' + filename)
        copy(fixture_root / filename, Path('fixtures') / filename)
    write('fixtures/provenance.json', json.dumps({
        'kind': 'self-built reviewed benign .NET fixture',
        'source_sha256': old_validation['source_sha256'],
        'binary_sha256': old_validation['original_sha256'],
        'use': 'Static reading smoke test only; predictions may be false positives.',
        'malware_functionality_evidence': False,
    }, indent=2) + '\n')
    write('.dockerignore', '\n'.join((
        '.git', '.env', '.venv', '__pycache__', '**/__pycache__', '*.pyc',
        'outputs', 'output', 'data', 'samples', 'results', 'fixtures', 'tests',
        '*.zip', '*.7z', '*.rar', '*.exe', '*.dll', '*.sys', '*.docx', '*.pdf',
    )) + '\n')
    write('README.md', '# X-SENTINEL: BODMAS static checks on Kali\n\n'
          'Start with docs/' + GUIDE + '.docx (or .md).\n\n'
          'No BODMAS malware, dataset archive, credentials, .env or database history is included. '
          'One reviewed self-built benign fixture is included for static smoke testing. '
          'Four frozen primary bundles are included unchanged; this is not the complete research matrix.\n\n'
          '**Experimental helper: end-to-end scanning and Kali execution have not been validated. '
          'The included guide requires a benign smoke test before BODMAS use.**\n\n'
          'python3 scripts/bodmas_verify_kit.py\n\n'
          'Read VALIDATION.md for tested and untested boundaries. Do not execute samples or restore disarmed headers.\n')
    validation_path = OUT / 'VALIDATION.md'
    if validation_path.is_file():
        copy(validation_path, 'VALIDATION.md')
    elif not args.stage_only:
        raise FileNotFoundError(validation_path)
    manifest = {'format': 'xsentinel-bodmas-kit-v1', 'date': '2026-10-19', 'files': [
        {'path': rel, 'size_bytes': (STAGE / rel).stat().st_size, 'sha256': digest(STAGE / rel)}
        for rel in sorted(files)
    ]}
    write('kit_manifest.json', json.dumps(manifest, indent=2) + '\n')
    if args.stage_only:
        print(json.dumps({'stage': str(STAGE), 'files': len(files), 'bundles': catalog}, indent=2))
        return
    archive = OUT / 'BODMAS_VM_2026_10_19.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for rel in sorted(files):
            zf.write(STAGE / rel, STAGE.name + '/' + rel)
    sha = digest(archive)
    (OUT / 'SHA256SUMS.txt').write_text(sha + '  ' + archive.name + '\n', encoding='ascii')
    print(json.dumps({'zip': str(archive), 'bytes': archive.stat().st_size, 'sha256': sha, 'files': len(files)}, indent=2))


if __name__ == '__main__':
    main()
