"""Real PostgreSQL/API roundtrip checks using reference vectors, never final labels."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import uuid
from urllib.request import Request,urlopen
from urllib.error import HTTPError

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from xsentinel.service.registry import BundleRegistry
from xsentinel.service.scoring import score_input
from xsentinel.storage.connection import database_engine,readiness
from xsentinel.storage.models import AnalysisJob,AnalysisResultRecord,DetectorScore,AuditEvent,Alert


def run(base):
    def call(path,body=None):
        req=Request(base+path,data=json.dumps(body).encode() if body is not None else None,
                    headers={'Content-Type':'application/json'})
        try:
            with urlopen(req,timeout=90) as response: return response.status,json.load(response)
        except HTTPError as exc: return exc.code,json.loads(exc.read())
    engine=database_engine(); registry=BundleRegistry()
    assert readiness(engine)['ok'] and call('/ready')[0]==200
    assert len(call('/v1/bundles')[1])==108
    cases=[]; bodies=[]; results=[]
    prefix='integration_'+uuid.uuid4().hex
    for dataset in ('EMBER2018','EMBER2024'):
        for variant in ('reduced','full'):
            entry=next(e for e in registry.entries.values() if e['dataset']==dataset and e['variant']==variant)
            detector,_=registry.loaded(entry['id']); x=detector.reference[:1]
            direct=score_input(detector,x,'X_primary_'+variant)
            body={'bundle_id':entry['id'],'features':x[0].tolist(),'method':'X_primary_'+variant,
                  'request_id':prefix+'_'+dataset+'_'+variant,'demo_mode':True}
            status,result=call('/v1/analyze/vector',body); assert status==200,result
            for field in ('scores','view_contributions','view_predictions','view_signed_shap',
                          'malware_probability','main_classification','backdoor_alert','top_features'):
                assert result[field]==direct[field],field
            assert call('/v1/analyses/'+body['request_id'])[1]==result
            bodies.append(body); results.append(result)
            cases.append({'dataset':dataset,'variant':variant,'request_id':body['request_id'],
                          'saved':True,'all_scores_match_direct_detector':True})
    with ThreadPoolExecutor(max_workers=4) as pool:
        retries=list(pool.map(lambda _:call('/v1/analyze/vector',bodies[0]),range(4)))
    assert all(status==200 and result==results[0] for status,result in retries)
    fresh={**bodies[0],'request_id':prefix+'_concurrent'}
    with ThreadPoolExecutor(max_workers=4) as pool:
        fresh_retries=list(pool.map(lambda _:call('/v1/analyze/vector',fresh),range(4)))
    assert all(status==200 and result==fresh_retries[0][1] for status,result in fresh_retries)
    bodies.append(fresh); results.append(fresh_retries[0][1])
    entry=registry.entry(bodies[0]['bundle_id']); detector,_=registry.loaded(entry['id'])
    scores,flags,_,_=detector.predict(detector.reference)
    alert_index=next(i for i,v in enumerate(flags[bodies[0]['method']]) if v)
    alerted={**bodies[0],'request_id':prefix+'_alert','features':detector.reference[alert_index].tolist()}
    status,alert_result=call('/v1/analyze/vector',alerted)
    assert status==200 and alert_result['backdoor_alert']
    bodies.append(alerted); results.append(alert_result)
    conflict={**bodies[0],'method':'TADR'}
    assert call('/v1/analyze/vector',conflict)[0]==409
    invalid={**bodies[3],'request_id':prefix+'_invalid','features':[0.0]*2381}
    assert call('/v1/analyze/vector',invalid)[0]==422
    unknown={**bodies[0],'request_id':prefix+'_unknown','bundle_id':'0'*64}
    assert call('/v1/analyze/vector',unknown)[0]==404
    assert call('/v1/analyze/vector',{**bodies[0],'ground_truth':'malicious'})[0]==422
    assert call('/v1/analyses?limit=101')[0]==422
    history=call('/v1/analyses?limit=100')[1]
    assert {b['request_id'] for b in bodies}.issubset({r['request_id'] for r in history})
    with Session(engine) as session:
        jobs=session.scalars(select(AnalysisJob).where(AnalysisJob.request_id.like(prefix+'%'))).all()
        assert len(jobs)==6
        for job,result in zip(sorted(jobs,key=lambda j:j.request_id),sorted(results,key=lambda r:r['request_id'])):
            assert session.get(AnalysisResultRecord,job.id).result_json==result
            assert session.scalar(select(func.count()).select_from(DetectorScore).where(DetectorScore.analysis_job_id==job.id))==len(result['scores'])
            assert session.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.request_id==job.request_id))==1
            assert session.scalar(select(func.count()).select_from(Alert).where(Alert.analysis_job_id==job.id))==int(result['backdoor_alert'])
    return {'checks':cases,'concurrent_retries_created_duplicates':False,'conflict_rejected':True,
            'invalid_inputs_not_saved':True,'alert_record_written':True,'records_created':6,
            'raw_vectors_not_stored':True,'revision':readiness(engine),
            'note':'Reference smoke records retained with demo_mode=true; not research results'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--base',default='http://127.0.0.1:8000')
    parser.add_argument('--out'); args=parser.parse_args()
    result=run(args.base.rstrip('/'))
    if args.out:
        path=Path(args.out)
        if path.exists(): raise FileExistsError('Existing evidence preserved')
        path.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result))
