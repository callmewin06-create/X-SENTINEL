import argparse
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description='X-SENTINEL feature-space research pipeline')
    sub=p.add_subparsers(dest='command',required=True)
    prep=sub.add_parser('prepare'); prep.add_argument('--raw',default='data/ember2018'); prep.add_argument('--out',required=True); prep.add_argument('--limit',type=int); prep.add_argument('--batch-size',type=int,default=128)
    prep_v3=sub.add_parser('prepare-v3',help='Audit all six verified PE ZIPs and materialize only the approved primary role budget')
    prep_v3.add_argument('--archives',required=True); prep_v3.add_argument('--out',required=True)
    prep_v3.add_argument('--verification',required=True); prep_v3.add_argument('--config',default='configs/primary_protocol.json')
    prep_v3.add_argument('--history-root',default='.'); prep_v3.add_argument('--resume',action='store_true')
    prep_v3.add_argument('--duplicate-policy',help='Explicit approved source duplicate policy JSON')
    prep_v3.add_argument('--vector-policy',help='Explicit approved policy for official PE records with is_pe=0')
    split=sub.add_parser('split'); split.add_argument('--data',required=True); split.add_argument('--reference',type=int,default=500); split.add_argument('--calibration',type=int,default=2000); split.add_argument('--seed',type=int,default=17)
    run=sub.add_parser('run'); run.add_argument('--data',required=True); run.add_argument('--out',required=True); run.add_argument('--config',default='configs/pilot.json'); run.add_argument('--allow-vector-stress',action='store_true')
    run.add_argument('--resume',action='store_true')
    develop=sub.add_parser('develop-attack',help='Screen feasible attacks using official train only')
    develop.add_argument('--data',required=True); develop.add_argument('--out',required=True)
    develop.add_argument('--config',default='configs/attack_development.json')
    infer=sub.add_parser('score'); infer.add_argument('--bundle',required=True); infer.add_argument('--vector',required=True)
    infer.add_argument('--dataset',choices=['EMBER2018','EMBER2024']); infer.add_argument('--schema')
    schema_cmd=sub.add_parser('schema',help='Inspect registered schema, view mapping and restricted feature names')
    schema_cmd.add_argument('--schema',required=True)
    calibrate=sub.add_parser('calibrate-primary',help='Calibrate frozen main/view models with disjoint benign reference/calibration vectors')
    calibrate.add_argument('--schema',required=True); calibrate.add_argument('--model',required=True)
    calibrate.add_argument('--reference',required=True); calibrate.add_argument('--calibration',required=True)
    calibrate.add_argument('--out',required=True); calibrate.add_argument('--seed',type=int,required=True)
    calibrate.add_argument('--view',action='append',default=[],metavar='VIEW=PATH')
    primary_split=sub.add_parser('split-primary',help='Freeze explicit primary train roles and official-test final IDs in a fresh namespace')
    primary_split.add_argument('--data',required=True); primary_split.add_argument('--out',required=True)
    primary_split.add_argument('--schema',required=True); primary_split.add_argument('--config',required=True)
    primary_split.add_argument('--seed',type=int,required=True); primary_split.add_argument('--history-root',required=True)
    resource_cmd=sub.add_parser('resource-pilot',help='Fit-only resource pilot from frozen primary fit IDs; no final scoring')
    resource_cmd.add_argument('--roles',required=True); resource_cmd.add_argument('--out',required=True)
    resource_cmd.add_argument('--config',required=True); resource_cmd.add_argument('--seed',type=int,required=True)
    for command in ('develop-primary','confirm-primary','run-primary'):
        primary=sub.add_parser(command,help='Execute checkpointed primary '+command.split('-')[0]+' phase')
        primary.add_argument('--roles',required=True); primary.add_argument('--out',required=True)
        primary.add_argument('--protocol',default='configs/primary_protocol.json')
        primary.add_argument('--execution',default='configs/primary_execution.json'); primary.add_argument('--resume',action='store_true')
        if command=='develop-primary':
            primary.add_argument('--round',type=int,default=1); primary.add_argument('--max-new-cells',type=int)
        else:
            primary.add_argument('--development',required=True); primary.add_argument('--selector-lock',required=True)
        if command=='run-primary':
            primary.add_argument('--confirmation',required=True); primary.add_argument('--max-new-cells',type=int)
    selector_lock_cmd=sub.add_parser('lock-selector',help='Lock one selector from complete development tables of both datasets')
    selector_lock_cmd.add_argument('--development',action='append',required=True)
    selector_lock_cmd.add_argument('--protocol',default='configs/primary_protocol.json'); selector_lock_cmd.add_argument('--out',required=True)
    primary_report=sub.add_parser('report-primary',help='Evidence-bound primary CSV/report with explicit missing and failed cells')
    primary_report.add_argument('--run',action='append',required=True); primary_report.add_argument('--out',required=True)
    primary_report.add_argument('--protocol',default='configs/primary_protocol.json')
    d0=sub.add_parser('d0'); d0.add_argument('--model',required=True); d0.add_argument('--vectors',required=True); d0.add_argument('--q',type=float,default=.01)
    report=sub.add_parser('report'); report.add_argument('--run',required=True)
    a=p.parse_args()
    if a.command=='report-primary':
        from xsentinel.primary_reporting import report_primary
        print(json.dumps(report_primary(a.run,a.protocol,a.out),indent=2))
    elif a.command in ('develop-primary','confirm-primary','run-primary'):
        from xsentinel.primary_workflow import run_primary_development,run_primary_confirmation,run_primary_final
        if a.command=='develop-primary':
            result=run_primary_development(a.roles,a.out,a.protocol,a.execution,resume=a.resume,
                                           round_number=a.round,max_new_cells=a.max_new_cells)
        elif a.command=='confirm-primary':
            result=run_primary_confirmation(a.roles,a.development,a.selector_lock,a.out,a.protocol,a.execution,resume=a.resume)
        else:
            result=run_primary_final(a.roles,a.development,a.confirmation,a.selector_lock,a.out,a.protocol,a.execution,
                                    resume=a.resume,max_new_cells=a.max_new_cells)
        print(json.dumps(result,indent=2))
    elif a.command=='lock-selector':
        from xsentinel.primary_workflow import lock_primary_selector
        print(json.dumps(lock_primary_selector(a.development,a.protocol,a.out),indent=2))
    elif a.command=='prepare-v3':
        from xsentinel.data.ember2024 import prepare_ember2024
        print(json.dumps(prepare_ember2024(a.archives,a.out,a.verification,a.config,a.history_root,
                         resume=a.resume,duplicate_policy_path=a.duplicate_policy,vector_policy_path=a.vector_policy),indent=2))
    elif a.command=='resource-pilot':
        from xsentinel.data.resource_pilot import resource_pilot
        print(json.dumps(resource_pilot(a.roles,a.out,a.config,a.seed),indent=2))
    elif a.command=='split-primary':
        from xsentinel.data.protocol import collect_seen_ids,freeze_primary_splits
        state=json.loads(Path(a.config).read_text(encoding='utf8'))
        seen,sources=collect_seen_ids(a.history_root)
        print(json.dumps(freeze_primary_splits(a.data,a.out,a.schema,state['sample_sizes'],a.seed,seen,sources),indent=2))
    elif a.command=='schema':
        from xsentinel.schema import get_schema
        s=get_schema(a.schema)
        print(json.dumps({'dataset':s.dataset,'schema':s.version,'schema_sha256':s.fingerprint,'dimension':s.dim,
            'groups':s.groups,'view_sizes':{v:len(i) for v,i in s.views.items()},'categorical_indices':s.categorical,
            'restricted_features':[{'index':i,'name':s.names[i],'view':s.view_labels[i]} for i in s.restricted],
            'restricted_status':s.restricted_status,'extractor_commit':s.extractor_commit},indent=2))
    elif a.command=='calibrate-primary':
        import numpy as np
        import lightgbm as lgb
        from xsentinel.detection.detector import Detector
        from xsentinel.schema import get_schema
        s=get_schema(a.schema); paths={}
        for item in a.view:
            name,sep,path=item.partition('=')
            if not sep or name not in s.views or name in paths or not path:
                p.error('--view requires a unique structural/behavioral/metadata=PATH')
            paths[name]=path
        models={v:lgb.Booster(model_file=path) for v,path in paths.items()}
        detector=Detector(lgb.Booster(model_file=a.model),np.load(a.reference,allow_pickle=False),models,
                          {'seed':a.seed},schema=s).fit(np.load(a.calibration,allow_pickle=False))
        detector.save(a.out,a.model,paths)
        print(json.dumps({'bundle':str(Path(a.out).resolve()),'dataset':s.dataset,'protocol':detector.protocol,
            'thresholds':detector.thresholds,'calibration_fp_count':detector.calibration_fp_count,
            'calibration_size':detector.calibration_size,'m5_enabled':detector.enable_m5},indent=2))
    elif a.command=='prepare':
        from xsentinel.data.prepare import prepare
        print(json.dumps(prepare(a.raw,a.out,a.limit,a.batch_size),indent=2))
    elif a.command=='split':
        from xsentinel.data.prepare import make_splits
        print({k:len(v) for k,v in make_splits(a.data,a.reference,a.calibration,a.seed).items()})
    elif a.command=='run':
        from xsentinel.experiment import run
        print(json.dumps(run(a.data,a.out,a.config,a.allow_vector_stress,a.resume),indent=2))
    elif a.command=='develop-attack':
        from xsentinel.attacks.development import run_development
        results=run_development(a.data,a.out,a.config)
        print(json.dumps({'completed_models':len(results),'screen_passes':sum(r['screen_pass'] for r in results),
                          'report':str(Path(a.out)/'report.md')},indent=2))
    elif a.command=='score':
        import numpy as np
        from xsentinel.detection.detector import Detector
        detector=Detector.load(a.bundle,expected_schema=a.schema,expected_dataset=a.dataset); x=np.load(a.vector,allow_pickle=False)
        scores,flags,details,elapsed=detector.predict(x)
        print(json.dumps({'dataset':detector.schema.dataset,'schema':detector.schema.version,'protocol':detector.protocol,
                          'malware_probability':details['malware_probability'].tolist(),
                          'malware_prediction':(details['malware_probability']>=detector.config['malware_threshold']).astype(int).tolist(),
                          'scores':{k:v.tolist() for k,v in scores.items()},'backdoor_alerts':{k:v.tolist() for k,v in flags.items()},
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
