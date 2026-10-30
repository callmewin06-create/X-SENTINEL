"""Stratified seed-cluster descriptive intervals on the observed benchmark."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from xsentinel.utils import write_json,sha256
from analyze_fusion_overlap import ROOT,csv_out

def main():
    p=argparse.ArgumentParser();p.add_argument('--repeats',type=int,default=10000);args=p.parse_args()
    source=ROOT/'frozen_audit/calibration_comparison_per_run.csv';out=ROOT/'statistics';out.mkdir(parents=True,exist_ok=True)
    df=pd.read_csv(source);df=df[df.policy=='legacy'].copy()
    df.to_csv(out/'recall_asr.csv',index=False)
    keys=['dataset','family','rate','method']
    df.groupby(keys).agg(attempted=('seed','size'),confirmed=('confirmed','sum'),n_seed=('seed','nunique'),
        recall_mean=('recall','mean'),recall_sd=('recall','std'),recall_min=('recall','min'),recall_max=('recall','max'),
        asr_mean=('asr','mean'),fpr_mean=('fpr','mean'),n_successful=('n_successful','sum')).to_csv(out/'stratified_results.csv')
    rng=np.random.default_rng(20261030);rows=[];paired=[]
    for keys0,group in df.groupby(['dataset','family','rate']):
        pivot=group.pivot(index='seed',columns='method',values='recall').sort_index()
        draws=rng.integers(0,len(pivot),(args.repeats,len(pivot)))
        for method in pivot:
            values=pivot[method].to_numpy();samples=values[draws];valid=np.isfinite(samples).sum(axis=1)
            means=np.divide(np.nansum(samples,axis=1),valid,out=np.full(args.repeats,np.nan),where=valid>0)
            good=means[np.isfinite(means)]
            rows.append(dict(zip(['dataset','family','rate'],keys0))|dict(method=method,n_seed=len(pivot),
                mean=float(np.nanmean(values)) if np.isfinite(values).any() else None,
                ci_low=float(np.quantile(good,.025)) if len(good) else None,ci_high=float(np.quantile(good,.975)) if len(good) else None,valid_draws=len(good)))
        for first,second in [('M3_view_mass','X_primary_reduced'),('X_primary_reduced','X_primary_full')]:
            d=(pivot[second]-pivot[first]).to_numpy();s=d[draws];n=np.isfinite(s).sum(axis=1)
            means=np.divide(np.nansum(s,axis=1),n,out=np.full(args.repeats,np.nan),where=n>0);v=means[np.isfinite(means)]
            paired.append(dict(zip(['dataset','family','rate'],keys0))|dict(first=first,second=second,n_seed=len(d),
                difference=float(np.nanmean(d)) if np.isfinite(d).any() else None,
                ci_low=float(np.quantile(v,.025)) if len(v) else None,ci_high=float(np.quantile(v,.975)) if len(v) else None))
    csv_out(out/'clustered_ci.csv',rows);csv_out(out/'paired_method_differences.csv',paired)
    for dataset in df.dataset.unique():
        fig,axes=plt.subplots(1,2,figsize=(11,4),sharex=True,sharey=True)
        for ax,method in zip(axes,['X_primary_reduced','X_primary_full']):
            g=df[(df.dataset==dataset)&(df.method==method)]
            for family,part in g.groupby('family'):
                for rate,part2 in part.groupby('rate'):
                    color={'concentrated_structural':'#1976a3','spread_structural':'#cb7200','cross_3view_stress':'#ad2860'}[family]
                    for confirmed,subset in part2.groupby('confirmed'):
                        ax.scatter(subset.asr*100,subset.recall*100,
                            label=f'{family} / {rate} / '+('confirmed' if confirmed else 'failed'),alpha=.8,
                            facecolors=color if confirmed else 'none',edgecolors=color,
                            marker={.005:'o',.01:'s',.02:'^'}[rate],s=45)
            ax.set_title(method);ax.set_xlabel('ASR (%)');ax.set_ylabel('Successful-eligible recall (%)')
        axes[1].legend(fontsize=5);fig.suptitle(dataset+' — observed benchmark, 3 seeds per stratum');fig.tight_layout()
        fig.savefig(out/(dataset+'_recall_asr.png'),dpi=180);plt.close(fig)
    write_json(out/'protocol.json',dict(source_sha256=sha256(source),code_sha256=sha256(__file__),repeats=args.repeats,seed=20261030,
        estimand='Equal-run mean within dataset/family/rate over all attempted seeds; paired method differences',
        scope='Seed-cluster resampling within each stratum; same draw for methods; no pooled cross-stratum CI',
        limitation='Only three seed clusters. Descriptive unstable intervals, conditional on observed benchmark and attack selection; no source resampling or new validation'))

if __name__=='__main__':main()
