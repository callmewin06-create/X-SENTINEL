from __future__ import annotations

import os
import subprocess
import sys

import pyodbc
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

pytestmark = [pytest.mark.integration, pytest.mark.db]


def _table_exists(conn, table_name: str) -> bool:
    query = text("SELECT count(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = :name")
    return conn.execute(query, {"name": table_name}).scalar_one() > 0


def test_offline_sql_upgrade_0001_to_0002() -> None:
    """Verifies Alembic can generate valid offline SQL upgrade script from 0001 to 0002."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "database/alembic.ini",
            "upgrade",
            "--sql",
            "0001_v2_multiuser:0002_v3_jev_ai_audit",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    sql_output = result.stdout
    assert "CREATE TABLE jev_ai_runs" in sql_output
    assert "CREATE TABLE jev_ai_feedback" in sql_output
    assert "ix_jev_ai_runs_analysis_job_id" in sql_output
    assert "ix_jev_ai_runs_analysis_created" in sql_output
    assert "ix_jev_ai_feedback_jev_ai_run_id" in sql_output
    assert "0002_v3_jev_ai_audit" in sql_output


def test_offline_sql_downgrade_0002_to_0001() -> None:
    """Verifies Alembic can generate valid offline SQL downgrade script from 0002 to 0001."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "database/alembic.ini",
            "downgrade",
            "--sql",
            "0002_v3_jev_ai_audit:0001_v2_multiuser",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    sql_output = result.stdout
    assert "DROP TABLE jev_ai_feedback" in sql_output
    assert "DROP TABLE jev_ai_runs" in sql_output
    assert "0001_v2_multiuser" in sql_output


def _is_sql_server_available() -> bool:
    try:
        conn = pyodbc.connect(
            "Driver={ODBC Driver 17 for SQL Server};Server=localhost;Trusted_Connection=yes;",
            timeout=2,
        )
        conn.close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(
    not _is_sql_server_available(), reason="SQL Server not accessible for live migration test"
)
def test_live_migration_upgrade_downgrade_cycle() -> None:
    """Executes upgrade -> downgrade -> upgrade cycle on an isolated scratch database."""
    test_db_name = "xsentinel_migration_cycle_test"
    master_conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost;Database=master;Trusted_Connection=yes;"
    )
    test_db_url = (
        f"mssql+pyodbc://localhost/{test_db_name}"
        "?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    )

    # Create fresh test DB
    conn = pyodbc.connect(master_conn_str, autocommit=True)
    cursor = conn.cursor()
    cursor.execute(f"IF DB_ID('{test_db_name}') IS NOT NULL DROP DATABASE {test_db_name};")
    cursor.execute(f"CREATE DATABASE {test_db_name};")
    conn.close()

    try:
        os.environ["XS_MIGRATION_DATABASE_URL"] = test_db_url
        cfg = Config("database/alembic.ini")
        cfg.set_main_option("sqlalchemy.url", test_db_url)

        # 1. Upgrade to 0001_v2_multiuser
        command.upgrade(cfg, "0001_v2_multiuser")

        engine = create_engine(test_db_url)
        with engine.connect() as c:
            v = c.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            assert v == "0001_v2_multiuser"
            assert not _table_exists(c, "jev_ai_runs")
            assert _table_exists(c, "users")
            assert _table_exists(c, "analysis_jobs")
        engine.dispose()

        # 2. Upgrade to 0002_v3_jev_ai_audit
        command.upgrade(cfg, "0002_v3_jev_ai_audit")

        engine = create_engine(test_db_url)
        with engine.connect() as c:
            v = c.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            assert v == "0002_v3_jev_ai_audit"
            assert _table_exists(c, "jev_ai_runs")
            assert _table_exists(c, "jev_ai_feedback")
        engine.dispose()

        # 3. Downgrade back to 0001_v2_multiuser
        command.downgrade(cfg, "0001_v2_multiuser")

        engine = create_engine(test_db_url)
        with engine.connect() as c:
            v = c.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            assert v == "0001_v2_multiuser"
            assert not _table_exists(c, "jev_ai_runs")
            assert not _table_exists(c, "jev_ai_feedback")
            assert _table_exists(c, "analysis_jobs")
        engine.dispose()

        # 4. Upgrade back to head
        command.upgrade(cfg, "head")

        engine = create_engine(test_db_url)
        with engine.connect() as c:
            v = c.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            assert v == "0002_v3_jev_ai_audit"
            assert _table_exists(c, "jev_ai_runs")
            assert _table_exists(c, "jev_ai_feedback")
        engine.dispose()

    finally:
        os.environ.pop("XS_MIGRATION_DATABASE_URL", None)
        conn = pyodbc.connect(master_conn_str, autocommit=True)
        cursor = conn.cursor()
        cursor.execute(
            f"IF DB_ID('{test_db_name}') IS NOT NULL "
            f"ALTER DATABASE {test_db_name} SET SINGLE_USER WITH ROLLBACK IMMEDIATE; "
            f"DROP DATABASE {test_db_name};"
        )
        conn.close()
