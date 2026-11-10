"""Refuse held-out release until all 36 static attempts and 12 arms are locked."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from xsentinel.revision.jstis_gate import inventory

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--attacks',required=True);p.add_argument('--output',required=True)
a=p.parse_args();out=Path(a.output)
if out.exists():raise FileExistsError('Never replace an existing global lock')
state=inventory(a.attacks);out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(state,indent=2),encoding='utf8')
print('All 36 static attempts and 12 adaptive arms locked; evaluator access may begin.')
