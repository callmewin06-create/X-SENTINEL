"""Research figures from audited CSV, never manually entered results."""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze_fusion_overlap import ROOT

def main():
    out=ROOT/'figures';out.mkdir(parents=True,exist_ok=True)
    df=pd.read_csv(ROOT/'frozen_audit/calibration_comparison_per_run.csv')
    methods=['M3_view_mass','M4_shap_behavioral_conflict','M4_prob_gap','X_primary_reduced','X_primary_full','TADR','STRIP']
    labels=['VMC','BGS','BPG','Reduced','Full','TADR','STRIP']
    fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
    for ax,ds in zip(axes,['EMBER2018','EMBER2024']):
        for j,(policy,name) in enumerate([('legacy','Original'),('tolerance_pointwise','Tolerance pointwise'),('tolerance_simultaneous_378','Tolerance family 378')]):
            values=df[(df.dataset==ds)&(df.policy==policy)].groupby('method').exceeds_1pct.sum().reindex(methods)
            ax.bar(np.arange(7)+(j-1)*.25,values,.25,label=name)
        ax.set_xticks(np.arange(7),labels,rotation=30);ax.set_title(ds);ax.set_ylim(0,28);ax.set_ylabel('Final FPR >1% endpoints (out of 27)')
    axes[1].legend(fontsize=7);fig.suptitle('Retrospective recalibration; not independent certification');fig.tight_layout()
    fig.savefig(out/'fpr_exceedances.png',dpi=180);fig.savefig(out/'fpr_exceedances.pdf');plt.close(fig)
    overlaps=pd.read_csv(ROOT/'frozen_audit/fusion_overlap_per_run.csv')
    selected=overlaps[(overlaps.group=='successful_eligible') & overlaps.confirmed & (overlaps.operating_point=='retrospective_final_cap')].copy()
    selected['cohort']=np.where(selected.family=='cross_3view_stress','Cross','Restricted')
    counts=selected.groupby(['dataset','cohort'])[['n','vmc_only','bgs_only','both','neither','fusion_only','vmc_lost_by_fusion']].sum()
    counts.to_csv(out/'fusion_plot_counts.csv')
    fig,ax=plt.subplots(figsize=(9,4));bottom=np.zeros(len(counts))
    for key,label,color in [('vmc_only','VMC only','#207ca5'),('bgs_only','BGS only','#d68d1c'),('both','Both','#40976d'),('neither','Neither','#c4c4c4')]:
        values=100*counts[key]/counts.n;ax.bar(range(len(counts)),values,bottom=bottom,label=label,color=color);bottom+=values
    ax.set_xticks(range(len(counts)),[f'{ds}\n{cohort}\nn={int(row.n):,} run-sample observations' for (ds,cohort),row in counts.iterrows()],fontsize=8)
    ax.set_ylabel('Successful-eligible observations (%)');ax.set_title('VMC/BGS overlap at retrospective FPR cap; shared sources across models')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.22),ncol=4);fig.tight_layout()
    fig.savefig(out/'fusion_overlap.png',dpi=180,bbox_inches='tight');fig.savefig(out/'fusion_overlap.pdf',bbox_inches='tight');plt.close(fig)

if __name__=='__main__':main()
