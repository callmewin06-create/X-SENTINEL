"""Pure revised metrics; never changes trained models or locked thresholds."""
import numpy as np
from sklearn.metrics import roc_auc_score
from xsentinel.evaluation.metrics import rate


def attack_groups(clean_original, poisoned_trigger, clean_trigger, cutoff=.5):
    arrays=[np.asarray(p,dtype=float) for p in (clean_original,poisoned_trigger,clean_trigger)]
    if arrays[0].ndim!=1 or any(p.shape!=arrays[0].shape or not np.isfinite(p).all() or
                              np.any((p<0)|(p>1)) for p in arrays):
        raise ValueError('Matching finite probability vectors required')
    eligible=arrays[0]>=cutoff
    success=eligible & (arrays[1]<cutoff)
    return {'all_triggered':np.ones(len(eligible),dtype=bool),'eligible':eligible,
            'successful_eligible':success,'paired_new_evasion':success & (arrays[2]>=cutoff)}


def ranking_auc(positive,negative):
    p=np.asarray(positive,dtype=float); n=np.asarray(negative,dtype=float)
    if p.ndim!=1 or n.ndim!=1 or not np.isfinite(p).all() or not np.isfinite(n).all():
        raise ValueError('Finite score vectors required')
    if not len(p) or not len(n): return None
    return float(roc_auc_score(np.r_[np.ones(len(p)),np.zeros(len(n))],np.r_[p,n]))


def revised_metrics(positive,negative,tau,groups):
    p=np.asarray(positive); n=np.asarray(negative)
    if p.ndim!=1 or n.ndim!=1 or not np.isfinite(p).all() or not np.isfinite(n).all() or not np.isfinite(tau):
        raise ValueError('Invalid scores/threshold')
    if any(np.asarray(mask).shape!=p.shape for mask in groups.values()):
        raise ValueError('Attack group shape mismatch')
    flags=p>tau; success=groups['successful_eligible']; eligible=groups['eligible']
    return {'threshold':float(tau),'benign_fpr':rate(n>tau),
            'recall_successful_eligible':rate(flags[success]),
            'recall_paired_new_evasion':rate(flags[groups['paired_new_evasion']]),
            'asr_before':rate(success[eligible]),
            'post_defense_asr':rate((success & ~flags)[eligible]),
            'auroc_all_triggered':ranking_auc(p,n),
            'auroc_successful_eligible':ranking_auc(p[success],n),
            'auroc_paired_new_evasion':ranking_auc(p[groups['paired_new_evasion']],n)}


def catch_miss(first,second,groups):
    a=np.asarray(first,dtype=bool); b=np.asarray(second,dtype=bool)
    if a.shape!=b.shape or a.ndim!=1: raise ValueError('Matching flag vectors required')
    return {name:{'n':int(np.sum(mask)),
                 'both':int(np.sum(mask&a&b)),'first_only':int(np.sum(mask&a&~b)),
                 'second_only':int(np.sum(mask&~a&b)),'neither':int(np.sum(mask&~a&~b))}
            for name,mask in groups.items()}


def fixed_model_cluster_difference(success,eligible,first,second,first_benign,second_benign,
                                   repeats=1000,seed=20261013):
    """Resample each source ID once, retaining its observations across all models.

    Inputs are run x source matrices sharing source-ID order. This estimates
    uncertainty conditional on these fixed trained models and selected cohort;
    it does not resample seeds or certify generalization to new models.
    """
    arrays=[np.asarray(x,dtype=float) for x in (success,eligible,first,second,first_benign,second_benign)]
    s,e,a,b,ab,bb=arrays
    if (s.ndim!=2 or not s.shape[0] or not s.shape[1] or
            any(x.shape!=s.shape for x in (e,a,b)) or ab.shape!=bb.shape or
            ab.ndim!=2 or ab.shape[0]!=s.shape[0] or not ab.shape[1] or repeats<1 or
            any(not np.isfinite(x).all() or np.any((x!=0)&(x!=1)) for x in arrays) or np.any(s>e)):
        raise ValueError('Binary, aligned run/source matrices required')
    def divide(n,d):
        return np.divide(n,d,out=np.full(np.asarray(n).shape,np.nan),where=d>0)
    def estimate(wm,wb):
        ns=wm@s.T; ne=wm@e.T
        recall=np.nanmean(divide(wm@(s*(b-a)).T,ns),axis=1)
        post=np.nanmean(divide(wm@(s*(a-b)).T,ne),axis=1)
        fpr=np.mean((wb@(bb-ab).T)/wb.sum(axis=1)[:,None],axis=1)
        return recall,post,fpr
    point=estimate(np.ones((1,s.shape[1])),np.ones((1,ab.shape[1])))
    draws=[[],[],[]]; rng=np.random.default_rng(seed)
    for start in range(0,repeats,50):
        count=min(50,repeats-start)
        wm=rng.multinomial(s.shape[1],np.full(s.shape[1],1/s.shape[1]),size=count)
        wb=rng.multinomial(ab.shape[1],np.full(ab.shape[1],1/ab.shape[1]),size=count)
        for dest,value in zip(draws,estimate(wm,wb)): dest.extend(value.tolist())
    result={'scope':'Source-ID cluster bootstrap conditional on fixed models/cohort; second minus first',
            'runs':s.shape[0],'malware_sources':s.shape[1],'benign_sources':ab.shape[1],
            'repeats':repeats,'seed':seed}
    for key,point_value,values in zip(('recall','post_defense_asr','benign_fpr'),point,draws):
        values=np.asarray(values); finite=values[np.isfinite(values)]
        result[key]={'difference':float(point_value[0]) if np.isfinite(point_value[0]) else None,
                     'ci95':np.quantile(finite,[.025,.975]).tolist() if len(finite) else [None,None],
                     'valid_draws':len(finite)}
    return result
