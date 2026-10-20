"""One transaction per analysis: model, job, scores, result, alert and audit."""
from datetime import datetime, timezone
import hashlib
import uuid
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from xsentinel.storage.models import (ModelVersion, AnalysisJob, AnalysisResultRecord,
                                      DetectorScore, Alert, AuditEvent)
from xsentinel.service.scoring import input_digest,score_input
from xsentinel.service.input_metadata import stable_metadata
from xsentinel.demo_provenance import demo_ground_truth


class RequestConflict(ValueError):
    pass


def analyze_and_store(engine, registry, identity, features, method, request_id, demo_mode=False, input_metadata=None):
    entry = registry.entry(identity)
    detector,lock = registry.loaded(identity)
    x = detector.schema.matrix(features)
    if len(x)!=1 or method not in detector.thresholds:
        raise ValueError('Exactly one vector and a valid method are required')
    digest = input_digest(x)
    model_id = uuid.uuid5(uuid.NAMESPACE_URL,identity)
    # Serialize only equal request IDs. Retries cannot create duplicate analyses.
    advisory = int.from_bytes(hashlib.sha256(request_id.encode()).digest()[:8],'big',signed=True)
    with Session(engine) as session, session.begin():
        session.execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':advisory})
        old = session.scalar(select(AnalysisJob).where(AnalysisJob.request_id==request_id))
        if old:
            old_result = session.get(AnalysisResultRecord,old.id).result_json
            if (old.input_sha256!=digest or old.model_version_id!=model_id or
                    old.config_version!=method or old.demo_mode!=demo_mode or
                    stable_metadata(old_result.get('input_metadata')) != stable_metadata(input_metadata)):
                raise RequestConflict('Request ID was already used for a different analysis')
            return old_result
        started = datetime.now(timezone.utc)
        with lock:
            result = score_input(detector,x,method,scope='selected')
        result['ground_truth'] = demo_ground_truth(entry['state'], x, demo_mode)
        job_id = uuid.uuid4()
        result.update({'request_id':request_id,'analysis_id':str(job_id),'bundle_id':identity,
                       'input_sha256':digest,'demo_mode':demo_mode,'saved':True,
                       'experiment':{k:entry[k] for k in ('dataset','family','seed','rate','variant')},
                       'created_at':started.isoformat()})
        if input_metadata is not None:
            result['input_metadata'] = input_metadata
        state = entry['state']
        config_hash = hashlib.sha256((entry['path']/'bundle.json').read_bytes()).hexdigest()
        session.execute(insert(ModelVersion).values(id=model_id,name=entry['dataset']+'_'+entry['variant'],
            version=identity,sha256=state['hashes']['main.txt'],config_hash=config_hash,
            metadata_json={'schema':state['schema'],'protocol':state['method_version'],
                           **{k:entry[k] for k in ('dataset','family','seed','rate','variant')},
                           'bundle_path':entry['relative_path'],'hashes':state['hashes']}
            ).on_conflict_do_nothing(index_elements=['name','version']))
        job = AnalysisJob(id=job_id,request_id=request_id,model_version_id=model_id,
            status='completed',input_mode='raw_pe' if input_metadata and input_metadata['kind']=='pe' else 'vector',input_sha256=digest,config_version=method,
            demo_mode=demo_mode,started_at=started,completed_at=datetime.now(timezone.utc))
        session.add(job); session.flush()
        selected = next(s for s in result['scores'] if s['Method']==method)
        session.add(AnalysisResultRecord(analysis_job_id=job_id,malware_score=result['malware_probability'],
            suspicion_score=selected['Score'],threshold=selected['Threshold'],decision=result['decision'],
            latency_ms=result['elapsed_ms'],view_contributions=result['view_contributions'],result_json=result))
        for row in result['scores']:
            session.add(DetectorScore(analysis_job_id=job_id,detector_code=row['Method'],score=row['Score'],
                diagnostics={'threshold':row['Threshold'],'flagged':row['Flagged']}))
        if result['backdoor_alert']:
            session.add(Alert(analysis_job_id=job_id,reason=method+' exceeded its locked threshold'))
        session.add(AuditEvent(request_id=request_id,event_type='analysis.completed',
            entity_type='analysis_job',entity_id=str(job_id),payload={'bundle_id':identity,'method':method,
                'input_sha256':digest,'demo_mode':demo_mode,'decision':result['decision']}))
        return result


def recent_analyses(engine, limit=50):
    with Session(engine) as session:
        rows = session.execute(select(AnalysisJob,AnalysisResultRecord,ModelVersion)
            .join(AnalysisResultRecord,AnalysisResultRecord.analysis_job_id==AnalysisJob.id)
            .join(ModelVersion,ModelVersion.id==AnalysisJob.model_version_id)
            .order_by(AnalysisJob.created_at.desc(),AnalysisJob.id.desc()).limit(limit)).all()
        return [{'request_id':j.request_id,'created_at':j.created_at.isoformat(),'model':m.name,
                 **{k:(m.metadata_json.get(k) or r.result_json.get('experiment', {}).get(k)
                       or r.result_json.get(k)) for k in ('dataset','family','seed','rate','variant')},
                 'bundle_id':m.version,'method':j.config_version,'demo_mode':j.demo_mode,
                 'malware_probability':r.malware_score,'main_classification':r.result_json['main_classification'],
                 'backdoor_alert':r.result_json['backdoor_alert'],'elapsed_ms':r.latency_ms,
                 'input_metadata':r.result_json.get('input_metadata')}
                for j,r,m in rows]


def analysis_detail(engine, request_id):
    with Session(engine) as session:
        result = session.scalar(select(AnalysisResultRecord).join(AnalysisJob)
                                .where(AnalysisJob.request_id==request_id))
        return result.result_json if result else None
