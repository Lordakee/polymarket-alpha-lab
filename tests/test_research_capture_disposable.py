"""Opt-in proof against a fresh, dedicated local Supabase/Postgres test DB.

No connection unless explicitly enabled. Never creates/drops databases, never
uses the normal postgres database, and refuses a pre-existing capture schema.
The containing disposable database is removed by its operator/CI lifecycle.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from os import environ
from pathlib import Path
import time
from uuid import uuid4

import pytest

from polymarket_alpha_lab import research_capture_psycopg as db
from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn
from tests.test_research_capture_codec import make_run

GATE = "POLYMARKET_ALPHA_LAB_RUN_RESEARCH_CAPTURE_DISPOSABLE_DB"
DSN_ENV = "POLYMARKET_ALPHA_LAB_RESEARCH_CAPTURE_DB_DSN"
DB_NAME = "polymarket_research_capture_test"


def _connect(dsn):
    validate_local_postgres_dsn(dsn, env_var_name=DSN_ENV)
    import psycopg
    return psycopg.connect(dsn, connect_timeout=5)


def test_real_prospective_capture_constraints_concurrency_and_readback(monkeypatch):
    if environ.get(GATE) != "1":
        pytest.skip(f"set {GATE}=1 for the dedicated local Postgres proof")
    dsn = environ.get(DSN_ENV)
    if not dsn:
        pytest.fail("explicit local disposable database DSN required")
    validate_local_postgres_dsn(dsn, env_var_name=DSN_ENV)
    import psycopg
    # Assert the dedicated, fresh target before even applying this node's DDL.
    with _connect(dsn) as conn:
        actual = conn.execute("SELECT current_database(),to_regnamespace('research_capture')").fetchone()
        assert actual == (DB_NAME, None), "requires a fresh dedicated capture-test database"
    migration = Path(__file__).resolve().parents[1] / "supabase/migrations/20260912000000_research_evaluation_capture.sql"
    with _connect(dsn) as conn:
        conn.execute(migration.read_text(encoding="utf-8"))

    def server_now():
        with _connect(dsn) as conn:
            return conn.execute("SELECT clock_timestamp()").fetchone()[0]

    tag = uuid4().hex[:12]
    conditions = [f"{tag}-{kind}" for kind in ("failed", "success", "late")]
    cutoff = server_now() + timedelta(seconds=8)
    registered = []
    for condition in conditions:
        registered.append(db.register_research_market_with_psycopg(dsn, condition_id=condition,
            market_slug="market-" + condition, forecast_cutoff_at=cutoff))
    assert all(row.registered_at < cutoff for row in registered)

    def capture(condition, record_id, status="completed", **changes):
        args = dict(record_id=tag+record_id, model_id="synthetic-model", protocol_version="v1",
                    run=make_run(condition, tag+record_id, status=status))
        args.update(changes)
        return db.capture_research_with_psycopg(dsn, **args)

    # First failure is durable; a later success must not erase it in evaluation.
    failed = capture(conditions[0], "-failed", "failed")
    retried = capture(conditions[0], "-retry")
    # Concurrent identical submissions have one DB timestamp and one content hash.
    with ThreadPoolExecutor(max_workers=4) as pool:
        repeated = tuple(pool.map(lambda _: capture(conditions[1], "-success"), range(8)))
    success = repeated[0]
    assert all(row == success for row in repeated)
    assert failed.recorded_at < retried.recorded_at < cutoff
    assert registered[1].registered_at <= success.recorded_at < cutoff
    with pytest.raises(db.ResearchCaptureConflict):
        capture(conditions[1], "-success", model_id="different-model")
    with pytest.raises(db.ResearchCaptureConflict):
        db.register_research_market_with_psycopg(dsn, condition_id=conditions[0],
            market_slug="market-"+conditions[0], forecast_cutoff_at=cutoff+timedelta(days=1))

    # Future data cannot be disguised as an already completed captured report.
    with pytest.raises(RuntimeError, match="database_failed"):
        capture(conditions[1], "-future", run=make_run(conditions[1], tag+"-future", now=server_now()+timedelta(days=1)))
    # A readback/validation failure after INSERT must roll back the actual row.
    with monkeypatch.context() as patch:
        def reject(_): raise ValueError("synthetic corrupt readback")
        patch.setattr(db, "_record", reject)
        with pytest.raises(RuntimeError, match="database_failed"):
            capture(conditions[1], "-rollback")
    with _connect(dsn) as conn:
        assert conn.execute("SELECT count(*) FROM research_capture.attempts WHERE record_id=%s",
                            (tag+"-rollback",)).fetchone()[0] == 0
    # Genuine model failures are retained rather than rolled back as DB failures.
    with _connect(dsn) as conn:
        assert conn.execute("SELECT count(*) FROM research_capture.attempts").fetchone()[0] == 3

    pending = db.load_research_evaluation_with_psycopg(dsn)
    assert pending.groups[0].failed_or_blocked_count == 1
    assert pending.groups[0].outcome_pending_count == 1
    before_outcomes = pending.generated_at
    # Wait only for this test's predeclared cutoff; no timestamp backdating.
    remaining = (cutoff-server_now()).total_seconds()
    if remaining > 0: time.sleep(remaining + 0.05)
    late = capture(conditions[2], "-late")
    assert late.recorded_at >= cutoff
    # Idempotent registration retry still works once its cutoff is past.
    assert db.register_research_market_with_psycopg(dsn, condition_id=conditions[0],
        market_slug="market-"+conditions[0], forecast_cutoff_at=cutoff) == registered[0]

    outcomes = []
    for condition in conditions:
        args = dict(condition_id=condition, market_slug="market-"+condition,
                    resolved_at=server_now(), actual_yes=True,
                    source_reference="synthetic:confirmed-only", source_content_sha256="a"*64)
        value = db.capture_research_outcome_with_psycopg(dsn, **args)
        outcomes.append(value)
        assert value.forecast_cutoff_at == cutoff
        assert value.recorded_at >= value.resolved_at
        assert db.capture_research_outcome_with_psycopg(dsn, **args) == value
        with pytest.raises(db.ResearchCaptureConflict):
            db.capture_research_outcome_with_psycopg(dsn, **{**args, "actual_yes": False})
    report = db.load_research_evaluation_with_psycopg(dsn)
    decisions = {row.record_id:row.reason_code for row in report.decisions}
    assert decisions[failed.record_id] == "research_failed"
    assert decisions[retried.record_id] == "later_attempt"
    assert decisions[success.record_id] == "scored"
    assert decisions[late.record_id] == "not_pre_outcome"
    assert report.groups[0].scores.mean_brier_score == Decimal("0.09")
    assert report.groups[0].scores.sample_count == 1
    assert report.groups[0].late_count == report.groups[0].failed_or_blocked_count == 1
    historical = db.load_research_evaluation_with_psycopg(dsn, generated_at=before_outcomes)
    assert historical.to_dict() == pending.to_dict()
    with pytest.raises(db.ResearchCaptureConflict, match="history_limit"):
        db.load_research_evaluation_with_psycopg(dsn, max_records=1)

    # DB constraints are real: attempts to backdate preregistration or change
    # rows cannot succeed even through direct SQL on this dedicated test DB.
    with pytest.raises(psycopg.Error):
        with _connect(dsn) as conn:
            conn.execute("INSERT INTO research_capture.markets (condition_id,market_slug,forecast_cutoff_at,registered_at) VALUES (%s,%s,%s,%s)",
                (tag+"-backdated", "market-"+tag+"-backdated", cutoff, cutoff-timedelta(days=1)))
    for table in ("markets", "attempts", "outcomes"):
        for command in (f"UPDATE research_capture.{table} SET readonly=false",
                        f"DELETE FROM research_capture.{table}", f"TRUNCATE research_capture.{table}"):
            with pytest.raises(psycopg.Error):
                with _connect(dsn) as conn:
                    conn.execute(command)
    final = db.load_research_evaluation_with_psycopg(dsn, generated_at=report.generated_at)
    assert final.to_dict() == report.to_dict()
    print("local Postgres capture proof: server timestamps, 8 concurrent retries, conflict refusal, rollback, immutable rows, historical readback, first-failure retention, late exclusion; no live model or real outcome dataset")
