"""Reconstruct identical removal counts from saved IDs, without retraining."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from scipy.stats import hypergeom
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.revision.training_filters import random_removal_control,CONTROL_SEED
from analyze_fusion_overlap import ROOT,csv_out

def main():
    rows=[];patterns=[]
    for ds in ['EMBER2018','EMBER2024']:
        root=Path('outputs/teacher_revision_2026_10_27/training_defense_v2')/ds
        attack=Path('outputs/primary')/ds/'protocol_v2/seed_17/spread_structural/rate_0.02/attack.json'
        with np.load(root/'selection.npz',allow_pickle=False) as z:
            ids=z['benign_ids'].astype(str);removed=z['random_control_removed_ids'].astype(str)
        poisons=np.asarray(read_json(attack)['poison_source_ids'],dtype=str)
        idx=random_removal_control(np.arange(len(ids)),5000)
        assert np.array_equal(ids[idx],removed)
        poison_positions=np.flatnonzero(np.isin(ids,poisons));assert len(poison_positions)==len(poisons)==4000
        count=int(np.isin(removed,poisons).sum());patterns.append((idx,poison_positions))
        rows.append(dict(dataset=ds,pool=len(ids),poisons=len(poisons),removed=len(removed),observed=count,
            expectation=len(removed)*len(poisons)/len(ids),hypergeom_lower_tail=float(hypergeom.cdf(count,len(ids),len(poisons),len(removed))),
            selection_sha256=sha256(root/'selection.npz'),attack_sha256=sha256(attack)))
    csv_out(ROOT/'random_control_audit.csv',rows)
    write_json(ROOT/'random_control_audit.json',dict(rows=rows,poison_seed=17,control_seed=CONTROL_SEED,
        same_removal_positions=bool(np.array_equal(patterns[0][0],patterns[1][0])),
        same_poison_positions=bool(np.array_equal(patterns[0][1],patterns[1][1])),
        interpretation='Same RNG and equal pool sizes induce matching rank-position draws across datasets; do not treat duplicated controls as independent replications',
        code_sha256=sha256(__file__)))

if __name__=='__main__':main()
