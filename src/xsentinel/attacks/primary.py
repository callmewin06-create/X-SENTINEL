"""Schema-bound vector edits. Geometry is explicit; no implicit research defaults."""
from dataclasses import dataclass
import math
import numpy as np
from xsentinel.schema import get_schema


@dataclass(frozen=True)
class VectorTrigger:
    family: str
    profile: str
    schema_version: str
    schema_sha256: str
    indices: tuple
    values: tuple

    def validate(self, schema):
        schema=get_schema(schema)
        if schema.version!=self.schema_version or schema.fingerprint!=self.schema_sha256:
            raise ValueError('Trigger/schema mismatch')
        indices=np.asarray(self.indices)
        values=np.asarray(self.values,dtype=float)
        if (indices.ndim!=1 or not len(indices) or indices.dtype.kind not in 'iu' or
                len(set(self.indices))!=len(indices) or np.any((indices<0)|(indices>=schema.dim)) or
                values.shape!=indices.shape or not np.isfinite(values).all()):
            raise ValueError('Invalid trigger indices/values')
        counts={v:sum(schema.view_labels[j]==v for j in indices) for v in schema.views}
        if self.profile=='feature_restricted':
            if not set(indices).issubset(schema.restricted):
                raise ValueError('Restricted trigger outside versioned whitelist; no silent relaxation')
        elif self.profile!='vector_stress':
            raise ValueError('Unknown vector attack profile')
        if self.family in ('concentrated_structural','spread_structural'):
            if self.profile!='feature_restricted' or counts['structural']!=len(indices):
                raise ValueError('Structural core family requires restricted Structural features')
        elif self.family=='cross_3view_stress':
            if self.profile!='vector_stress' or not all(counts.values()):
                raise ValueError('Cross-three-view stress must cover all three views')
        elif self.family=='cross_2view_restricted':
            if self.profile!='feature_restricted' or sum(n>0 for n in counts.values())!=2:
                raise ValueError('Cross-two-view restricted requires exactly two views')
        else:
            raise ValueError('Unknown primary family; Metadata-only stress is supplementary')
        return counts

    def apply(self, x, schema):
        self.validate(schema); schema=get_schema(schema)
        out=schema.matrix(x).copy(); out[:,self.indices]=self.values
        return out


def poison_primary(X, y, trigger, rate, seed, *, denominator, schema):
    """Retain labels/count; explicitly declare denominator and count rounding."""
    schema=get_schema(schema); X=schema.matrix(X); trigger.validate(schema)
    y=np.asarray(y)
    if y.shape!=(len(X),) or not np.isin(y,[0,1]).all():
        raise ValueError('Expected matching binary fit labels')
    if not 0<rate<1 or denominator not in ('all_fit','benign_fit'):
        raise ValueError('Explicit poison denominator and rate required')
    benign=np.flatnonzero(y==0)
    base=len(X) if denominator=='all_fit' else len(benign)
    count=math.floor(rate*base)
    if count<1 or count>len(benign): raise ValueError('Poison count outside benign pool')
    ids=np.random.default_rng(seed).choice(benign,count,replace=False)
    out=X.copy(); out[np.ix_(ids,trigger.indices)]=trigger.values
    return out,ids,{'n_poison':count,'n_benign_fit':len(benign),'n_total_fit':len(X),
        'rate_denominator':denominator,'requested_rate':rate,'rounding':'floor',
        'rate_of_benign':count/len(benign),'rate_of_all_fit':count/len(X),
        'view_feature_counts':trigger.validate(schema),'space':'vector stress/restricted; PE functionality unverified'}
