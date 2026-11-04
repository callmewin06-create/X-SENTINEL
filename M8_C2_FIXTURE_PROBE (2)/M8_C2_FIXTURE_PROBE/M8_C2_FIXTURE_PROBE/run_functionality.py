"""Run the hash-locked arithmetic fixtures only in an explicitly chosen lab VM."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

# Filled when packaging the reviewed benign fixtures. No arbitrary PE corpus input.
EXPECTED_MANIFEST_SHA256 = 'ef88170519706e0a594fcc56195e05ac1f8591320bcf374ab804f1aa4efa959e'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def oracle(fixture, argument):
    invalid = argument == 'abc'
    n = 0 if argument is None else (0 if invalid else int(argument))
    return (2 if invalid else 0, '' if invalid else f'X_SENTINEL_BENIGN_FIXTURE:{n*n+7}',
            "Error: Invalid integer input 'abc'" if invalid and fixture == 'native' else '')
def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', required=True, choices=['wine','mono','windows'])
    p.add_argument('--output', required=True)
    p.add_argument('--ack-controlled-vm', action='store_true')
    a = p.parse_args()
    if not a.ack_controlled_vm: p.error('Run in your controlled lab VM with --ack-controlled-vm')
    base = Path(__file__).resolve().parent
    manifest_path = base/'manifest.json'
    if sha(manifest_path) != EXPECTED_MANIFEST_SHA256: raise ValueError('Package manifest changed')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    for v in manifest['variants']:
        candidate = (base/v['path']).resolve()
        if base not in candidate.parents or sha(candidate) != v['sha256']:
            raise ValueError('Binary path or bytes differ from reviewed package')
    if a.runtime == 'windows' and platform.system() != 'Windows': p.error('Windows runtime requires Windows')
    command = None if a.runtime == 'windows' else shutil.which(a.runtime)
    selected = [v for v in manifest['variants'] if a.runtime == 'windows' or
                v['fixture'] == ('native' if a.runtime == 'wine' else 'managed')]
    out = Path(a.output).resolve()
    if out == base or base/'binaries' == out or base/'binaries' in out.parents:
        raise ValueError('Results must not overwrite package binaries')
    out.mkdir(parents=True, exist_ok=False)
    (out/'raw').mkdir()
    metadata = {'utc':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),
                'python':sys.version,'runtime':a.runtime,'runtime_path':command,
                'manifest_sha256':sha(manifest_path),'runner_sha256':sha(Path(__file__)),
                'scope':'Two benign arithmetic fixtures only; no malware/ASR/recall'}
    if command:
        try:
            version = subprocess.run([command,'--version'],capture_output=True,timeout=15)
            metadata['runtime_version']={'exit':version.returncode,
                'stdout':version.stdout.decode(errors='replace'),'stderr':version.stderr.decode(errors='replace')}
        except Exception as error: metadata['runtime_version_error']=str(error)
    rows=[]; raw=[]
    for v in selected:
        binary=(base/v['path']).resolve()
        for j,arg in enumerate([None,'5','-3','12','abc'],1):
            expected_exit,expected_stdout,expected_stderr=oracle(v['fixture'],arg)
            cmd=([str(binary)] if a.runtime=='windows' else [command or a.runtime,str(binary)])
            if arg is not None: cmd.append(arg)
            key=f"{v['fixture']}_{v['variant']}_TC{j}"
            row={'fixture':v['fixture'],'variant':v['variant'],'file_sha256':sha(binary),
                 'runtime':a.runtime,'test_case':f'TC{j}','input_args':'(none)' if arg is None else arg,
                 'expected_exit':expected_exit,'expected_stdout':expected_stdout,
                 'expected_stderr_contains':expected_stderr,'actual_exit':None,
                 'actual_stdout':'','actual_stderr':'','status':'NOT_RUN'}
            event={'id':key,'command':cmd,'utc':datetime.now(timezone.utc).isoformat()}
            start=time.monotonic()
            stdout=stderr=b''
            try:
                if row['file_sha256']!=v['sha256']: raise ValueError('Binary changed since package check')
                if a.runtime!='windows' and not command:
                    row['status']='BLOCKED_ENV'
                    event['error']='Selected runtime executable not found'
                else:
                    result=subprocess.run(cmd,capture_output=True,timeout=15,cwd=base)
                    stdout,stderr=result.stdout,result.stderr
                    actual_stdout=stdout.decode('utf-8',errors='replace').strip()
                    actual_stderr=stderr.decode('utf-8',errors='replace')
                    passed=(result.returncode==expected_exit and actual_stdout==expected_stdout
                            and (not expected_stderr or expected_stderr in actual_stderr))
                    row.update(actual_exit=result.returncode,actual_stdout=actual_stdout,
                               actual_stderr=actual_stderr,status='PASS' if passed else 'FAIL')
            except subprocess.TimeoutExpired as error:
                stdout,stderr=error.stdout or b'',error.stderr or b''
                row['status']='TIMEOUT'; event['error']=str(error)
            except Exception as error:
                row['status']='ERROR';event['error']=str(error)
            event.update(duration_seconds=time.monotonic()-start,result=row)
            (out/'raw'/f'{key}.stdout').write_bytes(stdout)
            (out/'raw'/f'{key}.stderr').write_bytes(stderr)
            raw.append(event);rows.append(row)
    (out/'environment.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    (out/'execution.json').write_text(json.dumps(raw,indent=2)+'\n',encoding='utf-8')
    with (out/'functionality.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    # Report paired preservation only when original AND edited cases passed.
    paired=[]
    for fixture in sorted({r['fixture'] for r in rows}):
        for variant in ['timestamp_only','sections_only','full_c2']:
            before=[r for r in rows if r['fixture']==fixture and r['variant']=='original']
            after=[r for r in rows if r['fixture']==fixture and r['variant']==variant]
            paired.append({'fixture':fixture,'variant':variant,
                'bounded_function_preserved':len(before)==len(after)==5 and all(r['status']=='PASS' for r in before+after),
                'before_statuses':[r['status'] for r in before],'after_statuses':[r['status'] for r in after]})
    summary={'counts':{s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})},
             'paired_checks':paired,'asr':None,'backdoor_recall':None,
             'meaning':'Arithmetic checks on benign fixtures, not malware function preservation or detector evaluation.'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))
    return 0 if all(r['status']=='PASS' for r in rows) else 1
if __name__=='__main__': sys.exit(main())
