"""Read-only equality and API checks against a separately restored PostgreSQL DB."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from sqlalchemy import select
from sqlalchemy.engine import make_url
from fastapi.testclient import TestClient
from xsentinel.storage.connection import database_engine, readiness
from xsentinel.storage.base import Base
import xsentinel.storage.models
from xsentinel.service.api import create_app
from xsentinel.service.registry import BundleRegistry


def snapshot(engine):
    tables = {}
    with engine.connect() as conn:
        for table in Base.metadata.sorted_tables:
            rows = [json.dumps(dict(row), sort_keys=True, default=str, ensure_ascii=True)
                    for row in conn.execute(select(table)).mappings()]
            tables[table.name] = {'count': len(rows),
                                 'sha256': hashlib.sha256('\n'.join(sorted(rows)).encode()).hexdigest()}
    return tables


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', required=True)
    args = parser.parse_args()
    if not args.database.startswith('xsentinel_restore_20261014_') or not args.database.replace('_', '').isalnum():
        raise ValueError('Only the named isolated restore namespace is accepted')
    original = database_engine()
    clone_url = make_url(os.environ['XS_DATABASE_URL']).set(database=args.database)
    restored = database_engine(clone_url.render_as_string(hide_password=False))
    before, after = snapshot(original), snapshot(restored)
    assert before == after, 'Live/restored table snapshots differ; retry with a quiet database'
    assert readiness(restored)['ok']
    registry = BundleRegistry()
    with TestClient(create_app(engine=original, registry=registry)) as live, TestClient(create_app(engine=restored, registry=registry)) as clone:
        rows = live.get('/v1/analyses?limit=100').json()
        assert clone.get('/ready').status_code == 200
        assert clone.get('/v1/analyses?limit=100').json() == rows
        for row in rows:
            path = '/v1/analyses/' + row['request_id']
            assert clone.get(path).json() == live.get(path).json()
    print(json.dumps({'restore_database': args.database, 'tables': after,
                      'all_table_snapshots_equal': True, 'api_history_and_details_equal': True,
                      'api_details_checked': len(rows), 'live_database_overwritten': False}))


if __name__ == '__main__':
    main()
