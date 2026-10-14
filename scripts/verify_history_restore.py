"""Dump and restore into a fresh database; never drops or overwrites the live DB."""
import argparse
import json
from pathlib import Path
import subprocess
import uuid


def run(*args):
    result = subprocess.run(['docker', 'compose', *args], text=True, encoding='utf8',
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('Docker restore step failed: ' + result.stderr[-1500:])
    return result.stdout


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--out', required=True)
    args = parser.parse_args(); out = Path(args.out)
    if out.exists(): raise FileExistsError('Existing restore evidence is preserved')
    token = uuid.uuid4().hex[:12]
    database = 'xsentinel_restore_20261014_' + token
    dump = '/tmp/xsentinel_restore_' + token + '.dump'
    run('exec', '-T', 'postgres', 'pg_dump', '-U', 'xsentinel', '-d', 'xsentinel', '-Fc', '-f', dump)
    run('exec', '-T', 'postgres', 'createdb', '-U', 'xsentinel', database)
    run('exec', '-T', 'postgres', 'pg_restore', '-U', 'xsentinel', '--exit-on-error', '-d', database, dump)
    result = json.loads(run('exec', '-T', 'backend', 'python', 'scripts/check_restored_history.py', '--database', database))
    backup = Path('backups') / ('history_verified_' + token + '.dump')
    backup.parent.mkdir(exist_ok=True)
    run('cp', 'postgres:' + dump, str(backup))
    result['backup_path'] = str(backup)
    result['backup_bytes'] = backup.stat().st_size
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
