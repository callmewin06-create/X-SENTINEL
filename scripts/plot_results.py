"""Publication-style static plots from recorded evaluations, never fake data."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def plot(run):
    root=Path(run); dest=root/'figures'; dest.mkdir(exist_ok=True)
    records=[]
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
    for path in sorted(root.glob('seed_*/*/evaluation/evaluation.json')):
        e=json.loads(path.read_text(encoding='utf8')); folder=path.parent; model=folder.parent
        trigger,rate=model.name.rsplit('_',1); seed=int(model.parent.name.split('_')[1]); records.append((trigger,float(rate),seed,e))
        with np.load(folder/'distributions.npz',allow_pickle=False) as a:
            fig,axes=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
            for ax,method in zip(axes,['TADR','M3']):
                for key,label in [('clean_benign_'+method,'Clean model / benign'),('clean_malware_'+method,'Clean model / malware'),('benign_'+method,'Poisoned / benign'),('trigger_'+method,'Poisoned / trigger')]:
                    ax.hist(a[key],bins=np.linspace(0,1,26),density=True,histtype='step',label=label,linewidth=1.8)
                ax.set(xlabel=f'{method} suspicion score',ylabel='Density',title=method)
            axes[1].legend(fontsize=8)
            fig.suptitle(f'E0 · seed {seed} · {trigger} · poison {rate}'+(' · PILOT' if e['evaluation_pilot'] else ''))
            fig.savefig(dest/f'E0_{seed}_{trigger}_{rate}.png'); plt.close(fig)
        latency=json.loads((folder/'latency.json').read_text(encoding='utf8'))
        names=list(latency); fig,ax=plt.subplots(figsize=(10,4),constrained_layout=True); ix=np.arange(len(names))
        ax.bar(ix-.18,[latency[k]['median_ms'] for k in names],width=.36,label='Median')
        ax.bar(ix+.18,[latency[k]['p95_ms'] for k in names],width=.36,label='P95')
        ax.set_xticks(ix,[k.replace('_','\n') for k in names],fontsize=9); ax.set(ylabel='Milliseconds per file',title=f'E5 · warm-up then {latency[names[0]]["n"]} individual observations')
        ax.legend(); fig.savefig(dest/f'E5_{seed}_{trigger}_{rate}.png'); plt.close(fig)
    if not records: raise ValueError('No completed evaluations found')
    methods=list(records[0][3]['metrics']); variants=sorted(set(r[0] for r in records)); values=np.full((len(methods),len(variants)),np.nan)
    for i,m in enumerate(methods):
        for j,t in enumerate(variants):
            values[i,j]=np.mean([r[3]['metrics'][m]['auroc_trigger_vs_benign'] for r in records if r[0]==t])
    fig,ax=plt.subplots(figsize=(max(7,len(variants)*2),7),constrained_layout=True)
    im=ax.imshow(values,vmin=0,vmax=1,cmap='viridis',aspect='auto'); fig.colorbar(im,ax=ax,label='AUROC')
    ax.set_xticks(range(len(variants)),variants); ax.set_yticks(range(len(methods)),methods)
    for i in range(len(methods)):
        for j in range(len(variants)): ax.text(j,i,f'{values[i,j]:.3f}',ha='center',va='center',color='white' if values[i,j]<.65 else 'black')
    ax.set_title('E2 · AUROC trigger versus benign\nMean over available configurations only'+(' · PILOT' if all(r[3]['evaluation_pilot'] for r in records) else ''))
    fig.savefig(dest/'E2_auroc.png'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,4),constrained_layout=True)
    for t in variants:
        rows=[r for r in records if r[0]==t]; x=np.arange(len(rows)); p=np.array([r[3]['attack_asr']['rate'] for r in rows]); lo=np.array([r[3]['attack_asr']['wilson95'][0] for r in rows]); hi=np.array([r[3]['attack_asr']['wilson95'][1] for r in rows])
        ax.errorbar(x,p,yerr=np.array([p-lo,hi-p]),fmt='o',capsize=4,label=t)
        ax.set_xticks(x,[f'{r[1]:.1%}, seed {r[2]}' for r in rows])
    ax.axhline(.5,color='gray',linestyle='--',label='50% viability diagnostic'); ax.set(ylim=(0,1),ylabel='Attack success rate',title='E1 · eligible malware denominator · Wilson 95% CI'); ax.legend()
    fig.savefig(dest/'E1_asr.png'); plt.close(fig)
    # Explicit reduced/full and limited-M5 comparisons, retaining each run.
    variants4=['X_reduced','X_reduced_M5_limited','X_full','X_full_M5_limited']
    fig,ax=plt.subplots(figsize=(9,4),constrained_layout=True)
    for index,(trigger,pr,seed,e) in enumerate(records):
        ax.plot(variants4,[e['metrics'][k]['auroc_trigger_vs_benign'] for k in variants4],marker='o',label=f'{trigger}, {pr:.1%}, seed {seed}')
    ax.set(ylim=(0,1),ylabel='AUROC trigger versus benign',title='E4 · reduced/full and limited-M5 ablation'); ax.tick_params(axis='x',labelsize=9)
    if len(records)<=6: ax.legend(fontsize=8)
    fig.savefig(dest/'E4_ablation.png'); plt.close(fig)
    return dest

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--run',required=True); a=p.parse_args(); print(plot(a.run))
