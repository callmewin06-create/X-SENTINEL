"""Paired primary comparison; only evaluator receives clean-model controls/IDs."""
import hashlib
import numpy as np
from xsentinel.detection.detector import Detector
from xsentinel.detection.components import PRIMARY_PROTOCOL
from xsentinel.evaluation.metrics import rate,auc,paired_bootstrap


def calibrate_pair(main, reference, calibration, view_models, config, schema):
    """Same suspicious main and ref/cal, extra views only supplied to full."""
    if config.get('enable_m5',False): raise ValueError('Primary pair excludes supplementary M5')
    reduced=Detector(main,reference,config=config,schema=schema).fit(calibration)
    full=Detector(main,reference,view_models,config,schema=schema).fit(calibration)
    if not full.views: raise ValueError('Full pair requires three clean view models')
    return reduced,full


def outcome_metrics(scores, thresholds, benign_scores, clean_malware_p, trigger_p, clean_trigger_p, t):
    """Fixed eligibility and original denominator, including every flagged sample."""
    clean_malware_p=np.asarray(clean_malware_p); trigger_p=np.asarray(trigger_p)
    clean_trigger_p=np.asarray(clean_trigger_p)
    if (trigger_p.ndim!=1 or clean_malware_p.shape!=trigger_p.shape or clean_trigger_p.shape!=trigger_p.shape or
            not all(np.isfinite(p).all() and np.all((p>=0)&(p<=1)) for p in (trigger_p,clean_malware_p,clean_trigger_p))):
        raise ValueError('Mismatched control/prediction pools')
    eligible=clean_malware_p>=t; success=eligible&(trigger_p<t)
    before=clean_trigger_p[eligible]<t; after=trigger_p[eligible]<t
    if set(scores)!=set(thresholds) or set(scores)!=set(benign_scores): raise ValueError('Detector method mismatch')
    metrics={}
    for method,positive in scores.items():
        positive=np.asarray(positive); negative=np.asarray(benign_scores[method])
        if positive.shape!=trigger_p.shape or negative.ndim!=1 or not np.isfinite(positive).all() or not np.isfinite(negative).all():
            raise ValueError('Invalid paired score pools')
        flags=positive>thresholds[method]; benign_flags=negative>thresholds[method]
        metrics[method]={'recall_all_triggered':rate(flags),'recall_successful_eligible':rate(flags[success]),
            'benign_fpr':rate(benign_flags),'post_defense_asr':rate((trigger_p[eligible]<t)&~flags[eligible]),
            'auroc_trigger_vs_benign':auc(positive,negative),'threshold':thresholds[method]}
    return {'n_malware':len(trigger_p),'n_eligible':int(eligible.sum()),'n_successful_eligible':int(success.sum()),
        'asr_all':rate(trigger_p<t),'asr_eligible':rate(after),'clean_trigger_asr_eligible':rate(before),
        'paired_new_evasions':rate(after&~before),'paired_lost_evasions':rate(before&~after),'methods':metrics}


def _scores(detector,X,batch_size):
    gathered={}; probabilities=[]
    for start in range(0,len(X),batch_size):
        scores,details=detector.scores(X[start:start+batch_size])
        for k,v in scores.items(): gathered.setdefault(k,[]).append(v)
        probabilities.append(details['malware_probability'])
    return {k:np.concatenate(v) for k,v in gathered.items()},np.concatenate(probabilities)


def _paired_rate(a,b,repeats,seed):
    diff=np.asarray(a,dtype=float)-np.asarray(b,dtype=float)
    if not len(diff): return {'difference':None,'ci95':[None,None],'n':0}
    rng=np.random.default_rng(seed)
    draws=[float(diff[rng.integers(0,len(diff),len(diff))].mean()) for _ in range(repeats)]
    return {'difference':float(diff.mean()),'ci95':np.quantile(draws,[.025,.975]).tolist(),'n':len(diff)}


def evaluate_pair(reduced,full,clean_model,benign,malware,triggered,benign_ids,malware_ids,
                  *,batch_size=128,bootstrap_repeats=1000,seed=17,artifacts=None):
    """Does not tune or train. Caller must lock protocol/tau before supplying final pools."""
    if reduced.protocol!=PRIMARY_PROTOCOL or full.protocol!=PRIMARY_PROTOCOL or reduced.views or not full.views:
        raise ValueError('Expected primary reduced/full pair with distinct resource access')
    if reduced.schema.fingerprint!=full.schema.fingerprint or reduced.config!=full.config:
        raise ValueError('Paired schema/config mismatch')
    if reduced.model.model_to_string()!=full.model.model_to_string() or not np.array_equal(reduced.reference,full.reference):
        raise ValueError('Primary pair must share main model and benign reference')
    if not reduced.calibration_content_sha256 or reduced.calibration_content_sha256!=full.calibration_content_sha256:
        raise ValueError('Primary pair must use the same benign calibration pool')
    shared=set(reduced.thresholds)
    if not shared or any(reduced.thresholds[k]!=full.thresholds[k] for k in shared):
        raise ValueError('Primary pair shared-method calibration mismatch')
    if batch_size<1 or bootstrap_repeats<1: raise ValueError('Positive batch/bootstrap budget required')
    s=reduced.schema; s.check_model(clean_model)
    xb=s.matrix(benign); xm=s.matrix(malware); xt=s.matrix(triggered)
    bi=np.asarray(benign_ids).astype(str); mi=np.asarray(malware_ids).astype(str)
    if (not len(xb) or not len(xm) or len(xt)!=len(xm) or bi.shape!=(len(xb),) or mi.shape!=(len(xm),) or
            len(set(bi))!=len(bi) or len(set(mi))!=len(mi) or set(bi)&set(mi)):
        raise ValueError('Expected disjoint unique paired source IDs and nonempty matching pools')
    t=reduced.config['malware_threshold']
    clean_p=clean_model.predict(xm,num_threads=4); clean_trigger_p=clean_model.predict(xt,num_threads=4)
    results={}; raw={}
    for name,detector in (('reduced',reduced),('full',full)):
        bs,bp=_scores(detector,xb,batch_size); ts,tp=_scores(detector,xt,batch_size)
        results[name]=outcome_metrics(ts,detector.thresholds,bs,clean_p,tp,clean_trigger_p,t)
        raw[name]=(ts,bs,tp)
    tr,br,pr=raw['reduced']; tf,bf,pf=raw['full']
    if not np.array_equal(pr,pf): raise ValueError('Paired main predictions differ')
    eligible=clean_p>=t; success=eligible&(pr<t)
    rf=tr['X_primary_reduced']>reduced.thresholds['X_primary_reduced']
    ff=tf['X_primary_full']>full.thresholds['X_primary_full']
    rb=br['X_primary_reduced']>reduced.thresholds['X_primary_reduced']
    fb=bf['X_primary_full']>full.thresholds['X_primary_full']
    comparison={
        'auroc_full_minus_reduced':paired_bootstrap(tf['X_primary_full'],bf['X_primary_full'],tr['X_primary_reduced'],br['X_primary_reduced'],bootstrap_repeats,seed),
        'recall_successful_full_minus_reduced':_paired_rate(ff[success],rf[success],bootstrap_repeats,seed),
        'benign_fpr_full_minus_reduced':_paired_rate(fb,rb,bootstrap_repeats,seed),
        'post_defense_asr_full_minus_reduced':_paired_rate((pf[eligible]<t)&~ff[eligible],(pr[eligible]<t)&~rf[eligible],bootstrap_repeats,seed),
        'successful_full_only_ids':mi[success&ff&~rf].tolist(),
        'successful_reduced_only_ids':mi[success&rf&~ff].tolist(),
    }
    comparison['auroc_full_minus_reduced']['difference']=auc(tf['X_primary_full'],bf['X_primary_full'])-auc(tr['X_primary_reduced'],br['X_primary_reduced'])
    if artifacts is not None:
        from pathlib import Path
        dest=Path(artifacts)
        if dest.exists(): raise FileExistsError('Existing paired predictions preserved')
        dest.parent.mkdir(parents=True,exist_ok=True)
        arrays={'benign_ids':bi.astype('S64'),'malware_ids':mi.astype('S64'),
                'clean_malware_p':clean_p,'clean_trigger_p':clean_trigger_p,'triggered_main_p':pr}
        for variant,(ts,bs,tp) in raw.items():
            arrays.update({variant+'_trigger_'+k:v for k,v in ts.items()})
            arrays.update({variant+'_benign_'+k:v for k,v in bs.items()})
        np.savez_compressed(dest,**arrays)
    return {'dataset':s.dataset,'schema':s.version,'protocol':PRIMARY_PROTOCOL,'schema_sha256':s.fingerprint,
        'main_model_sha256':hashlib.sha256(reduced.model.model_to_string().encode()).hexdigest(),
        'source_ids_sha256':hashlib.sha256(('\n'.join(bi)+'\n'+'\n'.join(mi)).encode()).hexdigest(),
        'results':results,'paired_comparison':comparison,
        'interpretation':'Within-dataset paired estimates; extra clean view models only for full; FPR target is not a test guarantee.'}
