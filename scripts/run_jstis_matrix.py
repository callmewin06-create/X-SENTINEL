"""Serial matrix driver with per-launch cost and peak Windows process memory.

No background scheduler or submission. A failed cell stops the batch and keeps
its exact artifacts for deterministic replay, without spending a new trial.
"""
import argparse
import ctypes
from ctypes import wintypes
from pathlib import Path
import subprocess
import sys
import time
import json

ROOT=Path(__file__).resolve().parents[1]


class COUNTERS(ctypes.Structure):
    _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[
        (name,ctypes.c_size_t) for name in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage',
         'QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',required=True);p.add_argument('--output',required=True)
    a=p.parse_args(); data=Path(a.data); output=Path(a.output); output.mkdir(parents=True,exist_ok=True)
    for dataset in ('EMBER2018','EMBER2024'):
        for seed in (17,29,43):
            cell=output/dataset/f'seed_{seed}'; cell.mkdir(parents=True,exist_ok=True)
            if (cell/'ATTACKS_LOCKED.json').exists():
                print('CELL_ALREADY_LOCKED',dataset,seed,flush=True);continue
            if not (data/dataset/'attacker/COMPLETE.json').exists():
                raise RuntimeError('Attacker materialization incomplete: '+dataset)
            attempt=1
            while (cell/f'launch_{attempt}.json').exists(): attempt+=1
            log=cell/f'launch_{attempt}.log'; start=time.perf_counter(); peak_ws=peak_private=0
            command=[sys.executable,str(ROOT/'scripts/run_jstis_attacks.py'),'--attacker',str(data/dataset/'attacker'),
                     '--output',str(cell),'--seed',str(seed),'--phase','all']
            print('CELL_LAUNCH',dataset,seed,'attempt',attempt,flush=True)
            with log.open('w',encoding='utf8') as stream:
                child=subprocess.Popen(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
                while child.poll() is None:
                    counters=COUNTERS(); counters.cb=ctypes.sizeof(counters)
                    if ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.c_void_p(int(child._handle)),
                                                               ctypes.byref(counters),counters.cb):
                        peak_ws=max(peak_ws,counters.PeakWorkingSetSize)
                        peak_private=max(peak_private,counters.PeakPagefileUsage)
                    time.sleep(.5)
            receipt={'dataset':dataset,'seed':seed,'attempt':attempt,'exit_code':child.returncode,
                     'elapsed_seconds':time.perf_counter()-start,'peak_working_set_bytes':peak_ws,
                     'peak_process_commit_bytes':peak_private,'log':str(log),
                     'status':'CELL_COMPLETE' if child.returncode==0 else 'INCOMPLETE_INFRASTRUCTURE'}
            (cell/f'launch_{attempt}.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
            print('CELL_EXIT',json.dumps(receipt),flush=True)
            if child.returncode: raise RuntimeError('Cell failed; do not classify as NO_VALID_ATTACK')
    print('MATRIX_TRAINING_COMPLETE_NOT_HELDOUT_EVALUATED',flush=True)


if __name__=='__main__':main()
