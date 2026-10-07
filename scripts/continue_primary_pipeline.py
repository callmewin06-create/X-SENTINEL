"""Finish the approved local pipeline sequentially after existing workers exit.

No scheduling, external uploads or Git mutations. Every scientific phase keeps
its own immutable lock/checkpoints. Failure stops the pipeline with evidence.
"""
import argparse
import ctypes
from datetime import datetime,timezone
import gc
import json
import os
from pathlib import Path
import sys
import time
import traceback

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.schema import V3_PRIMARY
from xsentinel.data.protocol import collect_seen_ids,freeze_primary_splits
from xsentinel.data.resource_pilot import resource_pilot
from xsentinel.primary_workflow import (run_primary_development,lock_primary_selector,
    run_primary_confirmation,run_primary_final,_source_hashes)
from xsentinel.primary_reporting import report_primary


def running(pid):
    if pid is None: return False
    if os.name!='nt': raise RuntimeError('External worker wait currently supports Windows only')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.restype=ctypes.c_void_p
    kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32]
    kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
    kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=kernel.OpenProcess(0x00100000,False,pid)
    if not handle:
        if ctypes.get_last_error() in (87,1168): return False
        raise OSError(ctypes.get_last_error(),'Cannot inspect owned worker process')
    try: return kernel.WaitForSingleObject(handle,0)==258
    finally: kernel.CloseHandle(handle)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--preparation-pid',type=int)
    parser.add_argument('--development-2018-pid',type=int)
    parser.add_argument('--state-dir',default='outputs/primary_pipeline/run_2026_10_06')
    args=parser.parse_args()
    out=Path(args.state_dir)
    if out.exists() and any(out.iterdir()): raise FileExistsError('Existing pipeline evidence preserved')
    out.mkdir(parents=True,exist_ok=True)
    protocol_path=Path('configs/primary_protocol.json'); execution_path=Path('configs/primary_execution.json')
    protocol=read_json(protocol_path)
    signature={'protocol_sha256':sha256(protocol_path),'execution_sha256':sha256(execution_path),
               'source_hashes':_source_hashes(),'pid':os.getpid(),'started_at':datetime.now(timezone.utc).isoformat(),
               'preparation_pid':args.preparation_pid,'development_2018_pid':args.development_2018_pid,
               'driver_sha256':sha256(__file__)}
    write_json(out/'pipeline.lock.json',signature)
    def status(phase,**details):
        value={'phase':phase,'updated_at':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),**details}
        write_json(out/'status.json',value); print(json.dumps(value,ensure_ascii=True),flush=True)
    def guard():
        if (sha256(protocol_path)!=signature['protocol_sha256'] or sha256(execution_path)!=signature['execution_sha256']
                or _source_hashes()!=signature['source_hashes']):
            raise ValueError('Frozen implementation/config changed while pipeline was running')
    try:
        source=Path('data/ember2024_primary_source_v2'); roles2024=Path('data/primary/EMBER2024/protocol_v2')
        status('waiting_for_2024_preparation')
        while not (source/'dataset.json').exists():
            guard()
            if args.preparation_pid is None or not running(args.preparation_pid):
                raise RuntimeError('Preparation stopped before dataset.json; inspect its checkpoint before resuming')
            time.sleep(15)
        guard(); status('freezing_2024_roles')
        if not (roles2024/'roles.json').exists():
            seen,sources=collect_seen_ids('.')
            freeze_primary_splits(source,roles2024,V3_PRIMARY,protocol['sample_sizes'],protocol['split_seed'],seen,sources)
            del seen,sources; gc.collect()
        development={'EMBER2018':Path('outputs/primary_development/EMBER2018/round_1'),
                     'EMBER2024':Path('outputs/primary_development/EMBER2024/round_1')}
        role_dirs={'EMBER2018':Path('data/primary/EMBER2018/protocol_v2'),'EMBER2024':roles2024}
        # Keep native training sequential and the V3 resource pilot free of the
        # existing 2018 worker's CPU/RAM contention.
        status('waiting_for_2018_development')
        while args.development_2018_pid is not None and running(args.development_2018_pid):
            guard(); time.sleep(15)
        if not (development['EMBER2018']/'completion.json').exists():
            if args.development_2018_pid is not None:
                raise RuntimeError('2018 worker exited without completion; inspect checkpoint before resuming')
            status('development_2018')
            run_primary_development(role_dirs['EMBER2018'],development['EMBER2018'],protocol_path,execution_path,
                                    resume=(development['EMBER2018']/'run.lock.json').exists())
        guard(); status('resource_pilot_2024')
        pilot=Path('outputs/primary_resource/EMBER2024/seed_17')
        if not (pilot/'resource.json').exists():
            resource_pilot(roles2024,pilot,'configs/resource_pilot_primary.json',17)
        gc.collect(); guard(); status('development_2024')
        run_primary_development(roles2024,development['EMBER2024'],protocol_path,execution_path,
                                resume=(development['EMBER2024']/'run.lock.json').exists())
        selector=out/'selector.lock.json'
        guard(); status('locking_common_selector')
        lock_primary_selector(list(development.values()),protocol_path,selector)
        chosen=read_json(selector)['chosen_selector']; status('selector_locked',selector=chosen)
        confirmations={}
        for dataset in protocol['datasets']:
            guard(); status('confirmation',dataset=dataset)
            dest=Path('outputs/primary_confirmation')/dataset/'round_1'; confirmations[dataset]=dest
            run_primary_confirmation(role_dirs[dataset],development[dataset],selector,dest,protocol_path,execution_path,
                                     resume=(dest/'run.lock.json').exists())
        finals=[]
        for dataset in protocol['datasets']:
            guard(); status('final_evaluation',dataset=dataset)
            dest=Path('outputs/primary')/dataset/'protocol_v2'; finals.append(dest)
            run_primary_final(role_dirs[dataset],development[dataset],confirmations[dataset],selector,dest,
                              protocol_path,execution_path,resume=(dest/'run.lock.json').exists())
        guard(); status('reporting')
        report=report_primary(finals,protocol_path,'outputs/primary_reports/report_2026_10_06')
        status('complete',report=report,git_mutations=False,external_uploads=False,
               remaining='Docker and validated binary extraction are separate environment/supplementary work')
    except Exception as exc:
        status('needs_attention',error=type(exc).__name__+': '+str(exc),results_policy='Existing evidence preserved')
        traceback.print_exc(); raise


if __name__=='__main__': main()
