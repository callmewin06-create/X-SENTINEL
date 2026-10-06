"""Primary strong/stealth labels and common selector locking from development."""
import numpy as np
from xsentinel.experiment import performance_from_predictions
from xsentinel.evaluation.metrics import rate


def screen_primary(clean_p,poisoned_p,clean_trigger_p,poisoned_trigger_p,y,rules,t=.5):
    clean_p=np.asarray(clean_p); poisoned_p=np.asarray(poisoned_p); y=np.asarray(y)
    before_p=np.asarray(clean_trigger_p); after_p=np.asarray(poisoned_trigger_p)
    if clean_p.shape!=y.shape or poisoned_p.shape!=y.shape or not np.isin(y,[0,1]).all():
        raise ValueError('Mismatched labeled development pools')
    malware=y==1
    if before_p.shape!=(int(malware.sum()),) or after_p.shape!=before_p.shape:
        raise ValueError('Triggered pool must match development malware')
    if not all(np.isfinite(p).all() and np.all((p>=0)&(p<=1)) for p in (clean_p,poisoned_p,before_p,after_p)):
        raise ValueError('Invalid binary development predictions')
    eligible=clean_p[malware]>=t; before=before_p[eligible]<t; after=after_p[eligible]<t
    clean=performance_from_predictions(clean_p,y,t); poison=performance_from_predictions(poisoned_p,y,t)
    n=int(eligible.sum()); gain=float((after.astype(int)-before.astype(int)).mean()) if n else None
    delta_accuracy=clean['accuracy']-poison['accuracy']
    strong=n>=rules['min_eligible'] and n>0 and after.mean()>=rules['min_asr'] and gain>=rules['min_paired_gain']
    stealth=delta_accuracy<rules['strict_max_accuracy_drop']
    return {'n_eligible':n,'asr':rate(after),'clean_trigger_asr':rate(before),'paired_gain':gain,
        'new_evasions':rate(after&~before),'lost_evasions':rate(before&~after),
        'clean_performance':clean,'poisoned_clean_performance':poison,'accuracy_drop':delta_accuracy,
        'strong':bool(strong),'stealth':bool(stealth),'strong_and_stealth':bool(strong and stealth),
        'preserve_run':True,'interpretation':'Predeclared heuristics; weak or failed runs remain evidence'}


def lock_common_selector(rows,expected_cells):
    """One complete declared development table, no confirmation/final selection.

    Rows have dataset/family/rate/seed/selector, status, paired_gain and
    strong_and_stealth. Failed cells remain explicit and cannot count as passing.
    Their gain is undefined; report the completed-cell mean and its denominator.
    """
    candidates=('legacy_rare','signed_shap_conditioned'); cells=set(tuple(c) for c in expected_cells)
    if not cells: raise ValueError('Explicit nonempty expected development cells required')
    summaries={}
    for selector in candidates:
        selected=[r for r in rows if r['selector']==selector]
        keys=[(r['dataset'],r['family'],r['rate'],r['seed']) for r in selected]
        if len(keys)!=len(set(keys)) or set(keys)!=cells:
            raise ValueError('Incomplete or duplicate selector development table')
        if any(r.get('phase')!='development' for r in selected):
            raise ValueError('Selector lock only accepts development evidence')
        gains=[]; passes=0
        for r in selected:
            if r['status'] not in ('complete','failed','unsupported'): raise ValueError('Unknown development status')
            if r['status']=='complete':
                gain=r.get('paired_gain')
                if gain is None or not np.isfinite(gain): raise ValueError('Completed run requires finite paired gain')
                gains.append(float(gain)); passes+=bool(r['strong_and_stealth'])
        summaries[selector]={'strong_and_stealth_count':passes,'mean_paired_gain':float(np.mean(gains)) if gains else None,
                            'paired_gain_completed_cells':len(gains),
                            'declared_cells':len(cells),'failed_or_unsupported':sum(r['status']!='complete' for r in selected)}
    if not any(s['paired_gain_completed_cells'] for s in summaries.values()):
        raise ValueError('No completed development evidence; cannot lock a selector')
    winner=max(candidates,key=lambda c:(summaries[c]['strong_and_stealth_count'],
        summaries[c]['mean_paired_gain'] if summaries[c]['mean_paired_gain'] is not None else -2,c=='signed_shap_conditioned'))
    return {'chosen_selector':winner,'summaries':summaries,'scope':'one selector shared by both datasets',
            'phase':'locked after development, before confirmation','confirmation_used_to_choose':False}
