"""Claim -> model/tools -> capture on local Supabase/Postgres, explicitly invoked.

Only the call that commits a NEW immutable claim starts a model. No TTL,
reclaim, automatic retries, long model-running transaction or new DB backend.
A crash may leave an incomplete claim: at-most-once LOOP START, not exactly-once
remote delivery or guaranteed completion. Caller must retain original inputs.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from polymarket_alpha_lab import research_capture_psycopg as db
from polymarket_alpha_lab.research_execution import (
    CapturedResearchExecution, CapturedResearchRequest, bind_execution_run,
    copy_request, decode_execution_request,
)
from polymarket_alpha_lab.team_research_agent import ResearchModel, run_team_research_agent
from polymarket_alpha_lab.team_research_agent_types import TeamResearchResult, identifier
from polymarket_alpha_lab.team_research_market_pipeline import MarketTeamResearchRun

_CLAIM_COLUMNS = "record_id,condition_id,market_slug,team_id,model_id,protocol_version,task_id,data_as_of,claimed_at,request_payload,request_sha256,paper_only,report_only,readonly"


def _claim_row(row) -> CapturedResearchExecution:
    if type(row) is not tuple or len(row) != 14 or any(flag is not True for flag in row[11:]):
        raise ValueError("invalid execution claim row")
    request = decode_execution_request(row[9], row[10])
    i = request.intake
    if row[:8] != (request.record_id, i.condition_id, i.market_slug, i.team_id,
                   request.model_id, request.protocol_version, i.task_id, i.as_of):
        raise ValueError("claim metadata mismatch")
    return CapturedResearchExecution(request, row[8], "incomplete")


def _lookup(cursor, record_id):
    cursor.execute(f"SELECT {_CLAIM_COLUMNS} FROM research_capture.execution_claims WHERE record_id=%s", (record_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    state = _claim_row(row)
    cursor.execute(f"SELECT {db._RECORD_COLUMNS} FROM research_capture.attempts WHERE record_id=%s", (record_id,))
    record = cursor.fetchone()
    return state if record is None else replace(state, status="already_captured", record=db._record(record))


def _claim(dsn, request):
    payload = request.payload
    i = request.intake

    def operation(cursor):
        db._lock(cursor, i.condition_id)
        existing = _lookup(cursor, request.record_id)
        if existing is not None:
            if existing.request.payload != payload:
                raise db.ResearchCaptureConflict("research_execution_request_conflict")
            return False, existing
        identity = (i.team_id, request.model_id, request.protocol_version, i.task_id)
        cursor.execute("SELECT record_id FROM research_capture.execution_claims WHERE "
                       "team_id=%s AND model_id=%s AND protocol_version=%s AND task_id=%s", identity)
        if cursor.fetchone() is not None:
            raise db.ResearchCaptureConflict("research_execution_task_conflict")
        cursor.execute("SELECT record_id FROM research_capture.attempts WHERE record_id=%s OR "
                       "(team_id=%s AND model_id=%s AND protocol_version=%s AND task_id=%s)",
                       (request.record_id, *identity))
        if cursor.fetchone() is not None:
            raise db.ResearchCaptureConflict("research_execution_identity_used")
        cursor.execute("SELECT c.record_id FROM research_capture.execution_claims c "
                       "LEFT JOIN research_capture.attempts a ON a.record_id=c.record_id "
                       "WHERE c.team_id=%s AND c.model_id=%s AND c.protocol_version=%s "
                       "AND c.condition_id=%s AND a.record_id IS NULL",
                       (i.team_id, request.model_id, request.protocol_version, i.condition_id))
        if cursor.fetchone() is not None:
            raise db.ResearchCaptureConflict("research_execution_prior_incomplete")
        market = db._market(cursor, i.condition_id)
        if market is None:
            cursor.execute("INSERT INTO research_capture.markets (condition_id,market_slug,forecast_cutoff_at) "
                           f"VALUES (%s,%s,%s) RETURNING {db._MARKET_COLUMNS}",
                           (i.condition_id, i.market_slug, request.forecast_cutoff_at))
            market = db.RegisteredResearchMarket(*cursor.fetchone())
        if (market.market_slug, market.forecast_cutoff_at) != (i.market_slug, request.forecast_cutoff_at):
            raise db.ResearchCaptureConflict("research_market_conflict")
        cursor.execute("SELECT clock_timestamp()")
        now = db._utc("server clock", cursor.fetchone()[0])
        if not i.as_of <= now < request.forecast_cutoff_at or (now-i.as_of).total_seconds() > request.max_start_delay_seconds:
            raise db.ResearchCaptureConflict("research_execution_not_startable")
        cursor.execute("INSERT INTO research_capture.execution_claims "
                       "(record_id,condition_id,market_slug,team_id,model_id,protocol_version,task_id,data_as_of,request_payload,request_sha256) "
                       f"VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING {_CLAIM_COLUMNS}",
                       (request.record_id, i.condition_id, i.market_slug, i.team_id, request.model_id,
                        request.protocol_version, i.task_id, i.as_of, payload, request.content_sha256))
        state = _claim_row(cursor.fetchone())
        if state.request.payload != payload:
            raise ValueError("claim readback mismatch")
        return True, state
    # Existing transaction helper centrally validates the DSN, imports psycopg
    # lazily, commits before returning, and bounds connection/SQL/lock waits.
    return db._local_transaction(dsn, operation)


def inspect_captured_research_with_psycopg(dsn: str, *, record_id: str) -> CapturedResearchExecution | None:
    """Read a single claim/result without starting a model or changing history."""
    identifier("record_id", record_id)
    return db._local_transaction(dsn, lambda cursor: _lookup(cursor, record_id), readonly=True)


def _capture(dsn, state, run):
    request = state.request
    run = bind_execution_run(request, run)
    try:
        record = db.capture_research_with_psycopg(dsn, record_id=request.record_id,
            model_id=request.model_id, protocol_version=request.protocol_version, run=run)
        return replace(state, status="captured", record=record, pending_run=None)
    except Exception:
        # Retain the ORIGINAL result in memory for explicit capture-only retry.
        # It is not a committed success; no DB/HTTP exception details escape.
        return replace(state, status="capture_failed", record=None, pending_run=run)


def retry_research_capture_with_psycopg(
    dsn: str, *, request: CapturedResearchRequest, run: MarketTeamResearchRun,
) -> CapturedResearchExecution:
    """Retry saving the original result only. Never accepts/constructs a model.

    Useful after a known capture failure or uncertain COMMIT acknowledgement.
    Do not manufacture a replacement report for a lost result; leave the claim
    incomplete for investigation. Identical committed retries keep DB time.
    """
    request = copy_request(request)
    run = bind_execution_run(request, run)
    state = inspect_captured_research_with_psycopg(dsn, record_id=request.record_id)
    if state is None or state.request.payload != request.payload:
        raise db.ResearchCaptureConflict("research_execution_request_conflict")
    if state.record is not None:
        if state.record.run != run:
            raise db.ResearchCaptureConflict("research_record_conflict")
        return state
    return _capture(dsn, state, run)


def _execute(request, model_factory):
    intake = request.intake
    if intake.status == "blocked":
        return MarketTeamResearchRun(intake, None)
    try:
        model = model_factory(intake.team_id)
        if not callable(getattr(model, "complete", None)):
            raise ValueError("invalid model client")
    except Exception:
        research = TeamResearchResult(intake.task_id, intake.team_id, intake.condition_id,
            intake.market_slug, intake.as_of, "failed", "model_factory_failed")
    else:
        research = run_team_research_agent(intake.task, model=model, limits=request.limits,
                                          required_source_ids=request.required_source_ids)
    return MarketTeamResearchRun(intake, research)


def run_captured_research_with_psycopg(
    dsn: str, *, request: CapturedResearchRequest, model_factory: Callable[[str], ResearchModel],
) -> CapturedResearchExecution:
    """Explicit synchronous application runner; only a committed NEW claim runs.

    Inputs are an existing validated Gamma intake (optionally from matched
    Coinbase/Kraken evidence), not raw URLs or an arbitrary executable callback.
    Capture regular model/factory failures and blocked intake as well as success.
    Outstanding claims never expire/restart automatically, even after a crash.
    Network/model calls are outside DB transactions and never enabled implicitly.
    """
    request = copy_request(request)
    if not callable(model_factory):
        raise ValueError("model_factory must be callable")
    owned, state = _claim(dsn, request)
    if not owned:
        return state
    try:
        run = _execute(state.request, model_factory)
    except Exception:
        # An unexpected runner/contract failure has no trustworthy complete run.
        # Claim remains visible and blocks complete-history scoring; no retry.
        return state
    return _capture(dsn, state, run)


def load_captured_research_evaluation_with_psycopg(
    dsn: str, *, generated_at: datetime | None = None, max_records: int = 10000,
    bucket_count: int = 10, min_sample_count: int = 30, min_bin_count: int = 5,
):
    """Score only a complete visible execution history, in one read snapshot."""
    return db.load_research_evaluation_with_psycopg(
        dsn, generated_at=generated_at, max_records=max_records, bucket_count=bucket_count,
        min_sample_count=min_sample_count, min_bin_count=min_bin_count,
        require_execution_complete=True,
    )


__all__ = ("load_captured_research_evaluation_with_psycopg", "run_captured_research_with_psycopg", "inspect_captured_research_with_psycopg",
           "retry_research_capture_with_psycopg")
