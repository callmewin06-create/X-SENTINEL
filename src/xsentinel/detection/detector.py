"""Blind detector: no attack manifests, labels or clean-model dependency."""
import time
import hashlib
from pathlib import Path
import lightgbm as lgb
import numpy as np
from xsentinel.schema import get_schema,SCHEMA_VERSION,V2_PRIMARY,V3_PRIMARY
from xsentinel.baselines.scores import contributions,tadr,strip
from xsentinel.detection.calibration import rank,threshold
from xsentinel.utils import sha256,read_json,write_json
from xsentinel.detection.components import primary_components,PRIMARY_PROTOCOL,LEGACY_PROTOCOL,COMPONENT_VERSIONS

class Detector:
    def __init__(self,model,reference,view_models=None,config=None,schema=None,protocol=PRIMARY_PROTOCOL):
        if protocol not in (PRIMARY_PROTOCOL,LEGACY_PROTOCOL): raise ValueError('Unknown detector protocol')
        self.protocol=protocol
        self.schema=get_schema(schema or (SCHEMA_VERSION if protocol==LEGACY_PROTOCOL else V2_PRIMARY))
        if protocol==LEGACY_PROTOCOL and self.schema.version!=SCHEMA_VERSION:
            raise ValueError('Legacy detector only supports archived V2 schema')
        if protocol==PRIMARY_PROTOCOL and self.schema.version==SCHEMA_VERSION:
            raise ValueError('Primary detector requires a versioned primary schema')
        self.schema.check_model(model)
        self.model=model; self.reference=self.schema.matrix(reference).copy(); self.views=dict(view_models or {})
        if not len(self.reference): raise ValueError('Empty benign reference')
        if self.views and protocol==PRIMARY_PROTOCOL and set(self.views)!=set(self.schema.views):
            raise ValueError('Primary full requires all three clean view models')
        for v,m in self.views.items(): self.schema.check_model(m,v)
        self.config={'strip_n':50,'strip_alpha':0.5,'seed':17,'malware_threshold':0.5,'fpr':0.01}
        self.config.update(config or {})
        if not 0<=self.config['fpr']<1 or not 0<=self.config['malware_threshold']<=1:
            raise ValueError('Invalid detector thresholds/config')
        self.enable_m5=protocol==LEGACY_PROTOCOL or bool(self.config.get('enable_m5',False))
        if self.enable_m5 and self.schema.version==V3_PRIMARY:
            raise ValueError('M5 V3 is supplementary and not validated; use primary without M5')
        self.candidates=np.arange(515,611) if self.enable_m5 else np.array([],dtype=int)
        self.low,self.high=(np.quantile(self.reference[:,self.candidates],[0.01,0.99],axis=0)
                            if self.enable_m5 else (np.array([]),np.array([])))
        self.rank_reference=None; self.thresholds={}

    def components(self,x,include_strip=True):
        x=self.schema.matrix(x); p=np.asarray(self.model.predict(x,num_threads=4))
        if p.shape!=(len(x),) or not np.isfinite(p).all() or np.any((p<0)|(p>1)):
            raise ValueError('Main model must return binary malware probabilities')
        phi=contributions(self.model,x,schema=self.schema); total=np.abs(phi).sum(axis=1)
        views=self.schema.views
        mass={v:np.abs(phi[:,idx]).sum(axis=1) for v,idx in views.items()}
        frac={v:np.divide(a,total,out=np.zeros(len(x)),where=total>1e-9) for v,a in mass.items()}
        g=phi[:,views['behavioral']].sum(axis=1)
        m4r=(1-p)*np.divide(np.maximum(g,0),total,out=np.zeros(len(x)),where=total>1e-9)
        rare=(x[:,self.candidates]<self.low)|(x[:,self.candidates]>self.high)
        negative=np.maximum(-phi,0); benign_mass=negative.sum(axis=1)
        rare_mass=(negative[:,self.candidates]*rare).sum(axis=1)
        share=np.divide(rare_mass,benign_mass,out=np.zeros(len(x)),where=benign_mass>1e-9)
        m5=np.where((p<self.config['malware_threshold'])&(share>0.8),(1-p)*share,0)
        view_p={v:np.asarray(m.predict(x[:,views[v]],num_threads=4)) for v,m in self.views.items()}
        for pv in view_p.values():
            if pv.shape!=p.shape or not np.isfinite(pv).all() or np.any((pv<0)|(pv>1)):
                raise ValueError('View model must return binary malware probabilities')
        if self.protocol==PRIMARY_PROTOCOL:
            scores,frac,net=primary_components(phi,p,self.schema,view_p.get('behavioral'))
        else:
            scores={'TADR':tadr(phi),'M3':np.max(np.stack(list(frac.values())),axis=0),'M4_reduced':m4r}
            if 'behavioral' in view_p: scores['M4_full']=(1-p)*view_p['behavioral']
        if self.enable_m5: scores['M5_limited']=m5
        if include_strip: scores['STRIP']=strip(self.model,x,self.reference,self.config['strip_n'],self.config['strip_alpha'],self.config['seed'],schema=self.schema)
        details={'malware_probability':p,'view_contributions':frac,'view_signed_shap':{v:phi[:,idx].sum(axis=1) for v,idx in views.items()},
                 'view_predictions':view_p,'m5_rare_benign_share':share,'m5_sensitive_branch':'unsupported_group_only',
                 'top_features':np.argsort(-np.abs(phi),axis=1)[:,:10], 'phi':phi,
                 'dataset':self.schema.dataset,'schema':self.schema.version,'protocol':self.protocol,'m5_enabled':self.enable_m5}
        return scores,details

    def scores(self,x):
        scores,details=self.components(x)
        if self.rank_reference is not None:
            for variant in ('reduced','full'):
                primary=self.protocol==PRIMARY_PROTOCOL
                m3='M3_view_mass' if primary else 'M3'
                m4=({'reduced':'M4_shap_behavioral_conflict','full':'M4_prob_gap'}[variant] if primary else 'M4_'+variant)
                if m4 not in scores: continue
                parts=[rank(self.rank_reference[k],scores[k]) for k in (m3,m4)]
                name=('X_primary_' if primary else 'X_')+variant
                scores[name]=np.mean(parts,axis=0)
                if self.enable_m5:
                    scores[name+'_M5_limited']=np.mean(parts+[rank(self.rank_reference['M5_limited'],scores['M5_limited'])],axis=0)
        return scores,details

    def fit(self,calibration):
        calibration=self.schema.matrix(calibration)
        if not len(calibration): raise ValueError('Empty benign calibration')
        if self.protocol==PRIMARY_PROTOCOL:
            digest=lambda row:hashlib.sha256(row.astype('<f4').tobytes()).digest()
            ref_hashes={digest(row) for row in self.reference}
            if any(digest(row) in ref_hashes for row in calibration):
                raise ValueError('Reference/calibration overlap: use disjoint held-out benign samples')
        ref,_=self.components(self.reference)
        self.rank_reference={k:np.sort(v) for k,v in ref.items()}
        cal,_=self.scores(calibration)
        self.thresholds={k:threshold(v,self.config['fpr']) for k,v in cal.items()}
        self.calibration_fpr={k:float(np.mean(v>self.thresholds[k])) for k,v in cal.items()}
        self.calibration_fp_count={k:int(np.sum(v>self.thresholds[k])) for k,v in cal.items()}
        self.calibration_size=len(calibration)
        self.calibration_content_sha256=hashlib.sha256(calibration.astype('<f4').tobytes()).hexdigest()
        return self

    def predict(self,x):
        if not self.thresholds: raise RuntimeError('Detector not calibrated')
        start=time.perf_counter(); scores,details=self.scores(x)
        flags={k:v>self.thresholds[k] for k,v in scores.items()}
        return scores,flags,details,(time.perf_counter()-start)*1000

    def save(self,directory,main_path,view_paths=None):
        if not self.thresholds: raise RuntimeError('Cannot export uncalibrated detector')
        p=Path(directory)
        if p.exists() and any(p.iterdir()): raise FileExistsError('Use a fresh bundle directory; existing artifacts are preserved')
        p.mkdir(parents=True,exist_ok=True)
        if set(view_paths or {})!=set(self.views): raise ValueError('Export view paths must match detector view models')
        import shutil
        if lgb.Booster(model_file=str(main_path)).model_to_string()!=self.model.model_to_string():
            raise ValueError('Export main model differs from calibrated model')
        for v,path in (view_paths or {}).items():
            if lgb.Booster(model_file=str(path)).model_to_string()!=self.views[v].model_to_string():
                raise ValueError('Export view model differs from calibrated model: '+v)
        shutil.copyfile(main_path,p/'main.txt')
        hashes={'main.txt':sha256(p/'main.txt')}
        for v,path in (view_paths or {}).items():
            shutil.copyfile(path,p/f'view_{v}.txt'); hashes[f'view_{v}.txt']=sha256(p/f'view_{v}.txt')
        np.savez(p/'reference.npz',X=self.reference,low=self.low,high=self.high,
                 **{'rank_'+k:v for k,v in self.rank_reference.items()})
        hashes['reference.npz']=sha256(p/'reference.npz')
        write_json(p/'bundle.json',{'schema':self.schema.version,'dataset':self.schema.dataset,
            'schema_sha256':self.schema.fingerprint,'method_version':self.protocol,
            'component_versions':COMPONENT_VERSIONS if self.protocol==PRIMARY_PROTOCOL else {'legacy':'archived-v1'},
            'config':self.config,'thresholds':self.thresholds,
            'hashes':hashes,'calibration_fpr':self.calibration_fpr,'calibration_size':self.calibration_size,
            'calibration_fp_count':self.calibration_fp_count,'calibration_policy':'score>tau; order statistic; ties conservative',
            'calibration_content_sha256':self.calibration_content_sha256,
            'reference_calibration_check':'vector-disjoint; source SHA separation is organizer responsibility' if self.protocol==PRIMARY_PROTOCOL else 'legacy',
            'm5_scope':'supplementary limited proxy' if self.enable_m5 else 'disabled; supplementary only',
            'pe_extraction':'unavailable' if self.schema.version==V3_PRIMARY else 'experimental_lief_0.16.6'})

    @classmethod
    def load(cls,directory,expected_schema=None,expected_dataset=None):
        p=Path(directory); state=read_json(p/'bundle.json')
        schema=get_schema(state['schema'])
        if expected_schema is not None and schema.version!=get_schema(expected_schema).version:
            raise ValueError('Bundle schema mismatch')
        if expected_dataset is not None and schema.dataset!=expected_dataset:
            raise ValueError('Bundle dataset mismatch')
        protocol=state.get('method_version',LEGACY_PROTOCOL)
        if 'method_version' not in state and schema.version!=SCHEMA_VERSION:
            raise ValueError('Unversioned bundle requires archived V2 schema')
        if 'method_version' in state:
            if state.get('schema_sha256')!=schema.fingerprint or state.get('dataset')!=schema.dataset:
                raise ValueError('Bundle schema fingerprint/dataset mismatch')
            if protocol==PRIMARY_PROTOCOL and state.get('component_versions')!=COMPONENT_VERSIONS:
                raise ValueError('Bundle component version mismatch')
        if not {'main.txt','reference.npz'}.issubset(state['hashes']): raise ValueError('Bundle hashes incomplete')
        for name,h in state['hashes'].items():
            if Path(name).name!=name or sha256(p/name)!=h: raise ValueError('Bundle checksum mismatch: '+name)
        main=lgb.Booster(model_file=str(p/'main.txt'))
        views={v:lgb.Booster(model_file=str(p/f'view_{v}.txt')) for v in schema.views if f'view_{v}.txt' in state['hashes']}
        with np.load(p/'reference.npz',allow_pickle=False) as a:
            obj=cls(main,a['X'].copy(),views,state['config'],schema=schema,protocol=protocol)
            obj.low=a['low'].copy(); obj.high=a['high'].copy()
            obj.rank_reference={k[5:]:a[k].copy() for k in a.files if k.startswith('rank_')}
        obj.thresholds=state['thresholds']; obj.calibration_fpr=state['calibration_fpr']; obj.calibration_size=state['calibration_size']
        obj.calibration_fp_count=state.get('calibration_fp_count',{k:int(round(v*obj.calibration_size)) for k,v in obj.calibration_fpr.items()})
        obj.calibration_content_sha256=state.get('calibration_content_sha256')
        expected_scores,_=obj.scores(obj.reference[:1])
        if set(obj.thresholds)!=set(expected_scores) or not all(np.isfinite(v) for v in obj.thresholds.values()):
            raise ValueError('Bundle threshold method mismatch/nonfinite threshold')
        return obj
