"""Serial resumable entrypoint: train -> global lock -> release -> evaluate -> summarize.

Does not publish, push, run PE files, or claim a manuscript is submission-ready.
Do not run concurrently with another matrix driver using the same output root.
"""
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from xsentinel.revision.jstis_gate import verify_global_lock


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--attacks',required=True);p.add_argument('--manifest',required=True)
    p.add_argument('--data',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    def run(script,*args):
        subprocess.run([sys.executable,str(ROOT/'scripts'/script),*map(str,args)],cwd=ROOT,check=True)
    output=Path(a.output);output.mkdir(parents=True,exist_ok=True);lock=output/'GLOBAL_ATTACKS_LOCK.json'
    run('run_jstis_matrix.py','--data',a.data,'--output',a.attacks)
    if not lock.exists():run('lock_jstis_attacks.py','--attacks',a.attacks,'--output',lock)
    verify_global_lock(a.attacks,lock)
    for dataset in ('EMBER2018','EMBER2024'):
        data=Path(a.data)/dataset/'evaluator'
        if not (data/'COMPLETE.json').exists():
            run('materialize_jstis_evaluator.py','--manifest',a.manifest,'--attacks',a.attacks,
                '--global-lock',lock,'--dataset',dataset,'--output',data)
        run('evaluate_jstis_followup.py','--attacks',a.attacks,'--global-lock',lock,
            '--evaluator',data,'--dataset',dataset,'--output',output/'evaluations'/dataset)
    run('summarize_jstis_followup.py','--evaluations',output/'evaluations','--output',output/'summary')
    print('EXPERIMENTS_COMPLETE_MANUSCRIPT_INTERPRETATION_AND_FINAL_QA_STILL_REQUIRED',flush=True)


if __name__=='__main__':main()
