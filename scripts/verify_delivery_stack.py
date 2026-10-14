"""Sequential deployment acceptance; no parallel timing or live DB overwrite."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def execute(arguments, environment=None):
    print('Checking ' + ' '.join(arguments[:5]), flush=True)
    result = subprocess.run(arguments, cwd=ROOT, env=environment, capture_output=True, text=True, encoding='utf8')
    if result.returncode:
        raise RuntimeError(result.stdout[-2000:] + '\n' + result.stderr[-2000:])
    return result.stdout


def save_docker_json(out, name, arguments):
    text = execute(['docker', 'compose', *arguments])
    value = json.loads(text[text.index('{'):text.rfind('}') + 1])
    (out / name).write_text(json.dumps(value, indent=2), encoding='utf8')
    return value


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--out', required=True)
    args = parser.parse_args(); out = (ROOT / args.out).resolve()
    if ROOT not in out.parents: raise ValueError('Output must stay inside this workspace')
    if out.exists(): raise FileExistsError('Acceptance evidence is not overwritten')
    out.mkdir(parents=True)
    execute(['docker', 'compose', 'up', '-d', '--build', '--wait', '--wait-timeout', '180'])
    execute(['docker', 'compose', 'cp', 'outputs/revision_2026_10_13/binary_validation/ReviewedBenignFixture.exe',
             'dashboard:/tmp/ReviewedBenignFixture.exe'])
    pe = save_docker_json(out, 'pe_service.json', ['exec', '-T', 'dashboard', 'python',
        'scripts/check_dashboard_input_service.py', '--fixture', '/tmp/ReviewedBenignFixture.exe',
        '--base', 'http://backend:8000', '--out', '/tmp/delivery_pe_checks.json'])
    legacy = save_docker_json(out, 'history_compatibility.json', ['exec', '-T', 'backend', 'python',
        'scripts/check_history_service.py', '--base', 'http://127.0.0.1:8000', '--out', '/tmp/delivery_legacy_checks.json'])
    linux = save_docker_json(out, 'dashboard_linux.json', ['exec', '-T', 'dashboard', 'python',
        'scripts/check_dashboard_runtime.py', '--out', '/tmp/delivery_runtime.json'])
    environment = os.environ.copy(); environment['XS_API_BASE_URL'] = 'http://127.0.0.1:8000'
    execute([sys.executable, '-X', 'utf8', 'scripts/check_dashboard_runtime.py', '--out',
             str(out / 'dashboard_windows.json')], environment)
    execute([sys.executable, '-X', 'utf8', 'scripts/verify_history_restore.py', '--out', str(out / 'restore.json')])
    # Measure after builds/API/UI checks have finished, with no concurrent benchmark jobs.
    execute([sys.executable, '-X', 'utf8', 'scripts/capture_dashboard_baseline.py', '--out',
             str(out / 'after'), '--compare', 'outputs/delivery_2026_10_14/before/baseline.json'])
    preserved = 0
    with zipfile.ZipFile(ROOT / 'output/revision_2026_10_13/X_SENTINEL_Reproduction_Artifact.zip') as archive:
        old = json.loads(archive.read('artifact_manifest.json'))
        for name, info in old['files'].items():
            if not name.startswith('outputs/primary/'): continue
            path = ROOT / name
            with path.open('rb') as source:
                digest = hashlib.file_digest(source, 'sha256').hexdigest()
            if digest != info['sha256']: raise ValueError('Frozen primary file changed: ' + name)
            preserved += 1
    result = {'pe_cases': len(pe['cases']), 'real_21mib_pe_passed': pe['real_21mib_pe_v3_extraction_passed'],
              'legacy_api_checks_passed': len(legacy['checks']), 'linux_ui_cases': len(linux['cases']),
              'frozen_primary_files_checked_unchanged': preserved, 'live_db_overwritten': False,
              'second_physical_machine_tested': False,
              'note': 'Windows + Linux Docker on the same physical computer. Restore evidence is in restore.json.'}
    (out / 'verification.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__': main()
