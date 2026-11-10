"""Feedback-driven development search. This module cannot load held-out roles.

The evaluator callback must retrain/score on fit and Search only. Infrastructure
exceptions propagate; they are never converted to a scientific negative result.
"""
import hashlib
import json
import math
import numpy as np


def canonical(indices,values):
    if len(indices)!=len(values) or not len(indices):
        raise ValueError('Nonempty paired trigger required')
    if any(not isinstance(j,(int,np.integer)) or j<0 for j in indices):
        raise ValueError('Invalid feature index')
    pairs=sorted((int(j),float(np.float32(v))) for j,v in zip(indices,values))
    if len({j for j,v in pairs})!=len(pairs) or not all(math.isfinite(v) for j,v in pairs):
        raise ValueError('Invalid trigger')
    # Treat signed zero as the same feature value.
    return tuple((j,0.0 if v==0 else v) for j,v in pairs)


def fingerprint(trigger):
    pairs=canonical(*zip(*trigger))
    return hashlib.sha256(json.dumps(pairs,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def ranking(metrics,arm,digest):
    if arm not in ('asr_only','vmc_aware'):
        raise ValueError('Unknown search arm')
    eligible=metrics['eligible']; asr=metrics['asr']; gain=metrics['paired_gain']
    drop=metrics['accuracy_drop']; vmc=metrics['mean_vmc']
    if (not isinstance(eligible,(int,np.integer)) or eligible<0 or
        not all(math.isfinite(x) for x in (asr,gain,drop,vmc)) or
        not 0<=asr<=1 or not -1<=gain<=1 or not -1<=drop<=1 or not 0<=vmc<=1):
        raise ValueError('Invalid development metrics')
    violations=(eligible<1000,asr<.5,gain<.2,drop>=.005)
    if any(violations):
        magnitude=(max(0,1000-eligible)/1000+max(0,.5-asr)/.5+
                   max(0,.2-gain)/.2+max(0,drop-.005)/.005)
        return (1,sum(violations),magnitude,-asr,-gain,digest)
    return (0,-asr,-gain,digest) if arm=='asr_only' else (0,vmc,-asr,-gain,digest)


def propose(incumbent,catalogue,rng):
    """Equal-probability coordinate/value operators; uniform observed values."""
    pairs=list(incumbent); pos=int(rng.integers(len(pairs)))
    used={j for j,v in pairs}
    if rng.random()<.5:
        options=sorted(set(catalogue)-used)
        if not options:
            raise ValueError('Coordinate replacement pool empty')
        j=int(rng.choice(options)); v=float(rng.choice(catalogue[j]))
        pairs[pos]=(j,v)
    else:
        j,v=pairs[pos]; options=np.asarray(catalogue[j],dtype=np.float32)
        options=options[options!=np.float32(v)]
        if not len(options):
            raise ValueError('Value mutation pool empty')
        pairs[pos]=(j,float(rng.choice(options)))
    return canonical(*zip(*pairs))


def run_search(initial,catalogue,evaluate,*,arm,seed,budget=16,on_step=None):
    """Each arm has its own feedback-dependent incumbent and logical budget.

    Exact duplicate proposals are rejected before evaluation, not counted as new
    trials. Callback/cache owns fit reuse with complete provenance. No infeasible
    fallback winner is returned. Persist each step via on_step for auditability.
    """
    if not isinstance(budget,int) or budget<1:
        raise ValueError('Positive explicit candidate budget required')
    if arm not in ('asr_only','vmc_aware'):
        raise ValueError('Unknown search arm')
    initial=canonical(*zip(*initial))
    catalogue={int(j):np.unique(np.asarray(v,dtype=np.float32)) for j,v in catalogue.items()}
    if any(len(v)<2 or not np.isfinite(v).all() for v in catalogue.values()):
        raise ValueError('Catalogue must contain finite varying features')
    if any(j not in catalogue or np.float32(v) not in catalogue[j] for j,v in initial):
        raise ValueError('Initialization outside observed value catalogue')
    rng=np.random.default_rng(seed); rows=[]; seen=set(); incumbent=initial; best=None
    for step in range(budget):
        if step==0:
            candidate=initial
        else:
            for attempt in range(10000):
                candidate=propose(incumbent,catalogue,rng)
                if fingerprint(candidate) not in seen: break
            else:
                raise RuntimeError('Unique proposal pool exhausted before budget completion')
        digest=fingerprint(candidate); parent=fingerprint(incumbent)
        metrics=evaluate(candidate,digest)
        key=ranking(metrics,arm,digest)
        seen.add(digest)
        if best is None or key<best:
            incumbent=candidate; best=key
        row={'step':step,'fingerprint':digest,'parent':None if step==0 else parent,
             'trigger':candidate,'metrics':metrics,'incumbent':fingerprint(incumbent)}
        rows.append(row)
        if on_step: on_step(row)
    feasible=[r for r in rows if ranking(r['metrics'],arm,r['fingerprint'])[0]==0]
    winner=min(feasible,key=lambda r:ranking(r['metrics'],arm,r['fingerprint'])) if feasible else None
    return {'status':'SELECTED_ON_SEARCH' if winner else 'NO_VALID_ATTACK',
            'arm':arm,'budget_completed':budget,'selected':winner,'trajectory':rows}
