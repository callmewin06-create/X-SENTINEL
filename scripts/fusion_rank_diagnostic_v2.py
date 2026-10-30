"""Explain dilution/rescue with cached ECDF ranks, not fitted new weights."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from xsentinel.utils import read_json,write_json
from xsentinel.revision.analysis import attack_groups
from xsentinel.detection.calibration import rank,threshold
from analyze_fusion_overlap import ROOT,cells,csv_out

def main():
    rows=[];bins=np.linspace(0,1,26);hist={ds:np.zeros((25,25)) for ds in ['EMBER2018','EMBER2024']}
    for path in cells():
        r=read_json(path);cell=path.parent
        with np.load(cell/'paired_predictions.npz',allow_pickle=False) as z:a={k:v.copy() for k,v in z.items()}
        with np.load(cell/'bundle_full/reference.npz',allow_pickle=False) as refs:
            v=rank(refs['rank_M3_view_mass'],a['full_trigger_M3_view_mass'])
            b=rank(refs['rank_M4_shap_behavioral_conflict'],a['full_trigger_M4_shap_behavioral_conflict'])
        assert np.allclose((v+b)/2,a['full_trigger_X_primary_reduced'],atol=1e-12,rtol=0)
        mask=attack_groups(a['clean_malware_p'],a['triggered_main_p'],a['clean_trigger_p'])['successful_eligible']
        vf=a['full_trigger_M3_view_mass']>threshold(a['full_benign_M3_view_mass'])
        ff=a['full_trigger_X_primary_reduced']>threshold(a['full_benign_X_primary_reduced'])
        for name,m in [('all_successful',mask),('vmc_lost',mask&vf&~ff),('fusion_rescue',mask&~vf&ff)]:
            rows.append({**{k:r[k] for k in ['dataset','seed','family','rate']},'confirmed':r['independently_confirmed_strong_and_stealth'],
                'group':name,'n':int(m.sum()),'mean_vmc_rank':float(v[m].mean()) if m.any() else None,
                'mean_bgs_rank':float(b[m].mean()) if m.any() else None,
                'spearman':float(spearmanr(v[m],b[m]).statistic) if m.sum()>2 and len(np.unique(v[m]))>1 and len(np.unique(b[m]))>1 else None,
                'vmc_unique_ranks':len(np.unique(v[m])),'bgs_unique_ranks':len(np.unique(b[m]))})
        if r['independently_confirmed_strong_and_stealth'] and r['family']!='cross_3view_stress':hist[r['dataset']]+=np.histogram2d(v[mask],b[mask],bins=(bins,bins))[0]
    out=ROOT/'frozen_audit';csv_out(out/'fusion_rank_diagnostics.csv',rows)
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,(ds,h) in zip(axes,hist.items()):
        im=ax.imshow(np.log1p(h.T),origin='lower',extent=[0,1,0,1],aspect='auto',cmap='viridis')
        ax.set_xlabel('VMC reference rank');ax.set_ylabel('BGS reference rank');ax.set_title(ds+' restricted confirmed')
        fig.colorbar(im,ax=ax,label='log(1 + run-sample count)')
    fig.tight_layout();fig.savefig(ROOT/'figures/fusion_rank_distribution.png',dpi=180);plt.close(fig)

if __name__=='__main__':main()
