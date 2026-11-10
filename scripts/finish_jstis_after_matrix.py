"""Continue this local experiment pipeline after the already-running matrix.

Waits for exact cell receipts, stops on recorded infrastructure failure, then
executes global locking and evaluation. Never starts a competing fit process.
"""
import argparse,json,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
for name in ('attacks','manifest','data','output'):p.add_argument('--'+name,required=True)
a=p.parse_args();root=Path(a.attacks);last=None
while True:
    complete=[]
    for dataset in ('EMBER2018','EMBER2024'):
        for seed in (17,29,43):
            cell=root/dataset/f'seed_{seed}'
            if (cell/'ATTACKS_LOCKED.json').exists():complete.append(f'{dataset}/{seed}');continue
            launches=sorted(cell.glob('launch_*.json'),key=lambda p:int(p.stem.split('_')[-1]))
            if launches and json.loads(launches[-1].read_text(encoding='utf8'))['status']=='INCOMPLETE_INFRASTRUCTURE':
                raise RuntimeError('Training failed: '+str(launches[-1])+'; evaluation remains sealed')
    if complete!=last:print('LOCKED_CELLS',len(complete),complete,flush=True);last=complete
    if len(complete)==6:break
    time.sleep(5)
subprocess.run([sys.executable,str(ROOT/'scripts/complete_jstis_followup.py'),
    '--attacks',a.attacks,'--manifest',a.manifest,'--data',a.data,'--output',a.output],cwd=ROOT,check=True)
