import argparse
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description='X-SENTINEL feature-space research pipeline')
    sub=p.add_subparsers(dest='command',required=True)
    prep=sub.add_parser('prepare'); prep.add_argument('--raw',default='ember2018'); prep.add_argument('--out',required=True); prep.add_argument('--limit',type=int); prep.add_argument('--batch-size',type=int,default=128)
    split=sub.add_parser('split'); split.add_argument('--data',required=True); split.add_argument('--reference',type=int,default=500); split.add_argument('--calibration',type=int,default=2000); split.add_argument('--seed',type=int,default=17)
    run=sub.add_parser('run'); run.add_argument('--data',required=True); run.add_argument('--out',required=True); run.add_argument('--config',default='configs/pilot.json'); run.add_argument('--allow-vector-stress',action='store_true')
    run.add_argument('--resume',action='store_true')
    infer=sub.add_parser('score'); infer.add_argument('--bundle',required=True); infer.add_argument('--vector',required=True)
    d0=sub.add_parser('d0'); d0.add_argument('--model',required=True); d0.add_argument('--vectors',required=True); d0.add_argument('--q',type=float,default=.01)
    report=sub.add_parser('report'); report.add_argument('--run',required=True)
    a=p.parse_args()
    if a.command=='prepare':
        from xsentinel.data.prepare import prepare
        print(json.dumps(prepare(a.raw,a.out,a.limit,a.batch_size),indent=2))
    elif a.command=='split':
        from xsentinel.data.prepare import make_splits
        print({k:len(v) for k,v in make_splits(a.data,a.reference,a.calibration,a.seed).items()})
    elif a.command=='run':
        from xsentinel.experiment import run
        print(json.dumps(run(a.data,a.out,a.config,a.allow_vector_stress,a.resume),indent=2))
    elif a.command=='score':
        import numpy as np
        from xsentinel.detection.detector import Detector
        detector=Detector.load(a.bundle); x=np.load(a.vector,allow_pickle=False)
        scores,flags,details,elapsed=detector.predict(x)
        print(json.dumps({'malware_probability':details['malware_probability'].tolist(),'scores':{k:v.tolist() for k,v in scores.items()},
                          'flags':{k:v.tolist() for k,v in flags.items()},'elapsed_ms':elapsed},indent=2))
    elif a.command=='d0':
        import numpy as np
        import lightgbm as lgb
        from xsentinel.baselines.scores import contributions,tadr
        from xsentinel.schema import matrix,VIEWS
        from xsentinel.detection.calibration import d0_budget
        x=matrix(np.load(a.vectors,allow_pickle=False)); model=lgb.Booster(model_file=a.model)
        phi=contributions(model,x); total=np.abs(phi).sum(1); prob=model.predict(x,num_threads=4)
        scores={'TADR':tadr(phi),'M3':np.max(np.stack([np.abs(phi[:,v]).sum(1) for v in VIEWS.values()]),axis=0)/np.maximum(total,1e-9),
                'M4_reduced':(1-prob)*np.maximum(phi[:,VIEWS['behavioral']].sum(1),0)/np.maximum(total,1e-9)}
        print(json.dumps({'q':a.q,'calibrated_fpr':False,'scores':{k:v.tolist() for k,v in scores.items()},'budget_flags':{k:d0_budget(v,a.q).tolist() for k,v in scores.items()}},indent=2))
    elif a.command=='report':
        from xsentinel.reporting import generate
        print(generate(a.run))

if __name__=='__main__': main()
