import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

REVISION = '0002_primary_scores'


def database_engine(url=None):
    url = url or os.environ.get('XS_DATABASE_URL')
    if not url or not url.startswith('postgresql+psycopg://'):
        raise RuntimeError('XS_DATABASE_URL must point to PostgreSQL using psycopg')
    return create_engine(url, pool_pre_ping=True, pool_size=4, max_overflow=4,
                         connect_args={'connect_timeout':5})


def readiness(engine):
    try:
        with engine.connect() as conn:
            revisions = list(conn.execute(text('SELECT version_num FROM alembic_version')).scalars())
        return {'ok':revisions == [REVISION], 'revision':revisions, 'expected_revision':REVISION}
    except SQLAlchemyError:
        return {'ok':False, 'revision':[], 'expected_revision':REVISION,
                'error':'Database unavailable or migration missing'}
