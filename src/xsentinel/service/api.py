import os
import uuid
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat
from sqlalchemy.exc import SQLAlchemyError
from xsentinel.dashboard_catalog import preferred_method
from xsentinel.storage.connection import database_engine,readiness
from xsentinel.storage.history import analyze_and_store,recent_analyses,analysis_detail,RequestConflict
from xsentinel.service.registry import BundleRegistry


class VectorRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    bundle_id: str = Field(min_length=64,max_length=64,pattern=r'^[0-9a-f]{64}$')
    features: list[FiniteFloat] = Field(min_length=2381,max_length=2568)
    method: str | None = Field(default=None,max_length=64)
    request_id: str = Field(default_factory=lambda:str(uuid.uuid4()),min_length=1,max_length=128,
                            pattern=r'^[A-Za-z0-9_.-]+$')
    demo_mode: bool = False


def create_app(engine=None, registry=None):
    engine = engine if engine is not None else database_engine()
    registry = registry if registry is not None else BundleRegistry(os.getenv('XS_BUNDLE_ROOT','outputs/primary'))
    app = FastAPI(title='X-SENTINEL calibrated analysis and history',version='0.2.0')

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        return JSONResponse(status_code=503,content={'detail':'Database operation failed; no saved result confirmed'})

    def require_ready():
        health = readiness(engine)
        if not health['ok']:
            raise HTTPException(503,detail=health)
        return health

    @app.get('/health')
    def health():
        return {'ok':True}

    @app.get('/ready')
    def ready():
        return require_ready()

    @app.get('/v1/bundles')
    def bundles():
        return registry.listing()

    @app.post('/v1/analyze/vector')
    def analyze(req:VectorRequest):
        require_ready()
        try:
            entry = registry.entry(req.bundle_id)
            method = req.method or preferred_method(entry['state']['thresholds'],entry['variant'])
            return analyze_and_store(engine,registry,req.bundle_id,req.features,method,req.request_id,req.demo_mode)
        except KeyError:
            raise HTTPException(404,'Unknown primary bundle')
        except RequestConflict as exc:
            raise HTTPException(409,str(exc))
        except (ValueError,FileNotFoundError) as exc:
            raise HTTPException(422,str(exc))
        except SQLAlchemyError:
            raise HTTPException(503,'Analysis was not saved: database error')

    @app.get('/v1/analyses')
    def history(limit:int=Query(default=50,ge=1,le=100)):
        require_ready()
        return recent_analyses(engine,limit)

    @app.get('/v1/analyses/{request_id}')
    def detail(request_id:str):
        require_ready()
        result = analysis_detail(engine,request_id)
        if result is None:
            raise HTTPException(404,'Analysis not found')
        return result

    return app
