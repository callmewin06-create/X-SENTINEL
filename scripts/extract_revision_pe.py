"""Read one PE without execution and save its schema-bound feature vector."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from xsentinel.data.pe import extract_pe
from xsentinel.data.pe_v3 import extract_pe_v3
from xsentinel.utils import write_json

p=argparse.ArgumentParser();p.add_argument('--schema',choices=['V2','V3'],required=True)
p.add_argument('--input',required=True);p.add_argument('--out',required=True);a=p.parse_args()
source=Path(a.input);out=Path(a.out)
if out.exists() or Path(str(out)+'.json').exists():raise FileExistsError('Use a new vector output')
if source.stat().st_size>20*1024*1024:raise ValueError('PE exceeds 20 MiB read limit')
vector,metadata=(extract_pe if a.schema=='V2' else extract_pe_v3)(source.read_bytes())
out.parent.mkdir(parents=True,exist_ok=True)
with out.open('wb') as f:np.save(f,vector,allow_pickle=False)
write_json(Path(str(out)+'.json'),metadata)
print('Extracted',a.schema,len(vector),'features; input was never executed;',out)
