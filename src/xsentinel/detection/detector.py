"""Blind detector: no attack manifests, labels or clean-model dependency."""
import time
from pathlib import Path
import lightgbm as lgb
import numpy as np
from xsentinel.schema import matrix,VIEWS,SCHEMA_VERSION
from xsentinel.baselines.scores import contributions,tadr,strip
from xsentinel.detection.calibration import rank,threshold
from xsentinel.utils import sha256,read_json,write_json

class Detector:
    def __init__(self,model,reference,view_models=None,config=None):
        self.model=model; self.reference=matrix(reference); self.views=view_models or {}
        self.config=config or {'strip_n':50,'strip_alpha':0.5,'seed':17,'malware_threshold':0.5,'fpr':0.01}
        self.candidates=np.arange(515,611)
        self.low,self.high=np.quantile(self.reference[:,self.candidates],[0.01,0.99],axis=0)
        self.rank_reference=None; self.thresholds={}

    def components(self,x,include_strip=True):
        x=matrix(x); p=np.asarray(self.model.predict(x,num_threads=4))
        phi=contributions(self.model,x); total=np.abs(phi).sum(axis=1)
        mass={v:np.abs(phi[:,idx]).sum(axis=1) for v,idx in VIEWS.items()}
        frac={v:np.divide(a,total,out=np.zeros(len(x)),where=total>1e-9) for v,a in mass.items()}
        g=phi[:,VIEWS['behavioral']].sum(axis=1)
        m4r=(1-p)*np.divide(np.maximum(g,0),total,out=np.zeros(len(x)),where=total>1e-9)
        rare=(x[:,self.candidates]<self.low)|(x[:,self.candidates]>self.high)
        negative=np.maximum(-phi,0); benign_mass=negative.sum(axis=1)
        rare_mass=(negative[:,self.candidates]*rare).sum(axis=1)
        share=np.divide(rare_mass,benign_mass,out=np.zeros(len(x)),where=benign_mass>1e-9)
        m5=np.where((p<self.config['malware_threshold'])&(share>0.8),(1-p)*share,0)
        scores={'TADR':tadr(phi),'M3':np.max(np.stack(list(frac.values())),axis=0),'M4_reduced':m4r,'M5_limited':m5}
        view_p={v:np.asarray(m.predict(x[:,VIEWS[v]],num_threads=4)) for v,m in self.views.items()}
        if 'behavioral' in view_p: scores['M4_full']=(1-p)*view_p['behavioral']
        if include_strip: scores['STRIP']=strip(self.model,x,self.reference,self.config['strip_n'],self.config['strip_alpha'],self.config['seed'])
        details={'malware_probability':p,'view_contributions':frac,'view_signed_shap':{v:phi[:,idx].sum(axis=1) for v,idx in VIEWS.items()},
                 'view_predictions':view_p,'m5_rare_benign_share':share,'m5_sensitive_branch':'unsupported_group_only',
                 'top_features':np.argsort(-np.abs(phi),axis=1)[:,:10], 'phi':phi}
        return scores,details

    def scores(self,x):
        scores,details=self.components(x)
        if self.rank_reference is not None:
            for variant in ('reduced','full'):
                m4='M4_'+variant
                if m4 not in scores: continue
                parts=[rank(self.rank_reference[k],scores[k]) for k in ('M3',m4)]
                scores['X_'+variant]=np.mean(parts,axis=0)
                scores['X_'+variant+'_M5_limited']=np.mean(parts+[rank(self.rank_reference['M5_limited'],scores['M5_limited'])],axis=0)
        return scores,details

    def fit(self,calibration):
        ref,_=self.components(self.reference)
        self.rank_reference={k:np.sort(v) for k,v in ref.items()}
        cal,_=self.scores(calibration)
        self.thresholds={k:threshold(v,self.config['fpr']) for k,v in cal.items()}
        self.calibration_fpr={k:float(np.mean(v>self.thresholds[k])) for k,v in cal.items()}
        self.calibration_size=len(calibration)
        return self

    def predict(self,x):
        if not self.thresholds: raise RuntimeError('Detector not calibrated')
        start=time.perf_counter(); scores,details=self.scores(x)
        flags={k:v>self.thresholds[k] for k,v in scores.items()}
        return scores,flags,details,(time.perf_counter()-start)*1000

    def save(self,directory,main_path,view_paths=None):
        if not self.thresholds: raise RuntimeError('Cannot export uncalibrated detector')
        p=Path(directory); p.mkdir(parents=True,exist_ok=True)
        import shutil
        shutil.copyfile(main_path,p/'main.txt')
        hashes={'main.txt':sha256(p/'main.txt')}
        for v,path in (view_paths or {}).items():
            shutil.copyfile(path,p/f'view_{v}.txt'); hashes[f'view_{v}.txt']=sha256(p/f'view_{v}.txt')
        np.savez(p/'reference.npz',X=self.reference,low=self.low,high=self.high,
                 **{'rank_'+k:v for k,v in self.rank_reference.items()})
        hashes['reference.npz']=sha256(p/'reference.npz')
        write_json(p/'bundle.json',{'schema':SCHEMA_VERSION,'config':self.config,'thresholds':self.thresholds,
            'hashes':hashes,'calibration_fpr':self.calibration_fpr,'calibration_size':self.calibration_size,
            'm5_scope':'limited; sensitive API/string branch unsupported', 'pe_extraction':'experimental_lief_0.16.6'})

    @classmethod
    def load(cls,directory):
        p=Path(directory); state=read_json(p/'bundle.json')
        if state['schema']!=SCHEMA_VERSION: raise ValueError('Bundle schema mismatch')
        if not {'main.txt','reference.npz'}.issubset(state['hashes']): raise ValueError('Bundle hashes incomplete')
        for name,h in state['hashes'].items():
            if Path(name).name!=name or sha256(p/name)!=h: raise ValueError('Bundle checksum mismatch: '+name)
        main=lgb.Booster(model_file=str(p/'main.txt'))
        views={v:lgb.Booster(model_file=str(p/f'view_{v}.txt')) for v in VIEWS if f'view_{v}.txt' in state['hashes']}
        if main.num_feature()!=2381: raise ValueError('Main model must have 2381 features')
        if any(m.num_feature()!=len(VIEWS[v]) for v,m in views.items()): raise ValueError('View model feature mismatch')
        with np.load(p/'reference.npz',allow_pickle=False) as a:
            obj=cls(main,a['X'].copy(),views,state['config'])
            obj.low=a['low'].copy(); obj.high=a['high'].copy()
            obj.rank_reference={k[5:]:a[k].copy() for k in a.files if k.startswith('rank_')}
        obj.thresholds=state['thresholds']; obj.calibration_fpr=state['calibration_fpr']; obj.calibration_size=state['calibration_size']
        return obj
