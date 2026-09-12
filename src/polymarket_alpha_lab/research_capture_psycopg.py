"""Prospective, append-only capture on local Supabase/Postgres exclusively.

Every public operation validates its complete input before DSN validation and
lazy driver import. Each call owns one short transaction and closes it. No
schema creation, model call, credential discovery, retry or file journal.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import re

from polymarket_alpha_lab.research_capture_codec import (
    decode_research_capture, encode_research_capture, payload_sha256,
)
from polymarket_alpha_lab.research_probability_scores import ResearchProbabilityDiagnostics
from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn
from polymarket_alpha_lab.team_research_agent_types import aware, hard_flags, integer, strict_json, text
from polymarket_alpha_lab.team_research_evaluation import (
    MAX_RECORDS, ResearchEvaluationOutcome, ResearchEvaluationRecord, ResearchEvaluationReport,
)
from polymarket_alpha_lab.team_research_intake import require_market_slug
from polymarket_alpha_lab.team_research_market_pipeline import MarketTeamResearchRun

MAX_READ_BYTES = 33554432
_RECORD_COLUMNS = "record_id,condition_id,market_slug,team_id,model_id,protocol_version,task_id,data_as_of,recorded_at,payload,payload_sha256,paper_only,report_only,readonly"
_OUTCOME_COLUMNS = "condition_id,market_slug,forecast_cutoff_at,resolved_at,recorded_at,actual_yes,source_reference,source_content_sha256,paper_only,report_only,readonly"
_MARKET_COLUMNS = "condition_id,market_slug,forecast_cutoff_at,registered_at,paper_only,report_only,readonly"


class ResearchCaptureConflict(ValueError):
    """A fixed-code identity/content conflict; existing records are unchanged."""


@dataclass(frozen=True, slots=True)
class RegisteredResearchMarket:
    condition_id: str
    market_slug: str
    forecast_cutoff_at: datetime
    registered_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self):
        _identity(self.condition_id, self.market_slug)
        for name in ("forecast_cutoff_at", "registered_at"):
            object.__setattr__(self, name, _utc(name, getattr(self, name)))
        hard_flags(self)
        if self.registered_at >= self.forecast_cutoff_at:
            raise ValueError("research cutoff was not registered prospectively")


def _utc(name, value):
    aware(name, value)
    return value.astimezone(UTC)


def _identity(condition_id, market_slug):
    text("condition_id", condition_id)
    require_market_slug(market_slug)


def _local_transaction(dsn, operation, *, readonly=False):
    validate_local_postgres_dsn(dsn, env_var_name="POLYMARKET_ALPHA_LAB_RESEARCH_CAPTURE_DB_DSN")
    try:
        import psycopg
        # kwargs also prevent an unbounded connect_timeout in a supplied DSN.
        with psycopg.connect(dsn, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY" if readonly
                               else "SET TRANSACTION ISOLATION LEVEL READ COMMITTED READ WRITE")
                cursor.execute("SET LOCAL statement_timeout = '15s'")
                cursor.execute("SET LOCAL lock_timeout = '5s'")
                cursor.execute("SET LOCAL TIME ZONE 'UTC'")
                result = operation(cursor)
        # Do not return success until commit and context cleanup have completed.
        return result
    except ResearchCaptureConflict:
        raise
    except Exception:
        raise RuntimeError("research_capture_database_failed") from None


def _lock(cursor, condition_id):
    # Serialize application writers per event BEFORE the server stamps a row.
    cursor.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                   ("polymarket/research_capture/" + condition_id,))


def _market(cursor, condition_id):
    cursor.execute(f"SELECT {_MARKET_COLUMNS} FROM research_capture.markets WHERE condition_id=%s", (condition_id,))
    row = cursor.fetchone()
    return None if row is None else RegisteredResearchMarket(*row)


def _record(row):
    if type(row) is not tuple or len(row) != 14 or any(flag is not True for flag in row[11:]):
        raise ValueError("invalid capture row")
    record = decode_research_capture(row[9], recorded_at=row[8], expected_sha256=row[10])
    intake = record.run.intake
    expected = (record.record_id, intake.condition_id, intake.market_slug, intake.team_id,
                record.model_id, record.protocol_version, intake.task_id, intake.as_of.astimezone(UTC))
    if row[:8] != expected:
        raise ValueError("capture row metadata mismatch")
    return record


def register_research_market_with_psycopg(
    dsn: str, *, condition_id: str, market_slug: str, forecast_cutoff_at: datetime,
) -> RegisteredResearchMarket:
    """Fix a future cutoff before research. Exact repeat returns original row."""
    _identity(condition_id, market_slug)
    cutoff = _utc("forecast_cutoff_at", forecast_cutoff_at)

    def operation(cursor):
        _lock(cursor, condition_id)
        existing = _market(cursor, condition_id)
        if existing is not None:
            if (existing.market_slug, existing.forecast_cutoff_at) != (market_slug, cutoff):
                raise ResearchCaptureConflict("research_market_conflict")
            return existing
        cursor.execute(f"INSERT INTO research_capture.markets (condition_id,market_slug,forecast_cutoff_at) "
                       f"VALUES (%s,%s,%s) RETURNING {_MARKET_COLUMNS}", (condition_id, market_slug, cutoff))
        return RegisteredResearchMarket(*cursor.fetchone())
    return _local_transaction(dsn, operation)


def capture_research_with_psycopg(
    dsn: str, *, record_id: str, model_id: str, protocol_version: str, run: MarketTeamResearchRun,
) -> ResearchEvaluationRecord:
    """Capture success OR failure, stamped by DB time, never a caller's date.

    Submit immediately after research. Delayed imports keep their actual new DB
    time and cannot masquerade as prospective predictions. A byte-identical
    retry returns its original timestamp; changed content never overwrites it.
    """
    payload = encode_research_capture(record_id=record_id, model_id=model_id,
                                      protocol_version=protocol_version, run=run)
    stamp = datetime.fromisoformat(strict_json(payload)["run"]["intake"]["as_of"])
    copied = decode_research_capture(payload, recorded_at=stamp, expected_sha256=payload_sha256(payload))
    intake = copied.run.intake

    def operation(cursor):
        _lock(cursor, intake.condition_id)
        market = _market(cursor, intake.condition_id)
        if market is None or market.market_slug != intake.market_slug:
            raise ResearchCaptureConflict("research_market_not_registered")
        cursor.execute(f"SELECT {_RECORD_COLUMNS} FROM research_capture.attempts WHERE record_id=%s", (record_id,))
        existing = cursor.fetchone()
        if existing is not None:
            original = _record(existing)
            if existing[9] != payload:
                raise ResearchCaptureConflict("research_record_conflict")
            return original
        cursor.execute(f"INSERT INTO research_capture.attempts "
                       "(record_id,condition_id,market_slug,team_id,model_id,protocol_version,task_id,data_as_of,payload,payload_sha256) "
                       f"VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING {_RECORD_COLUMNS}",
                       (record_id, intake.condition_id, intake.market_slug, intake.team_id, model_id,
                        protocol_version, intake.task_id, intake.as_of, payload, payload_sha256(payload)))
        return _record(cursor.fetchone())
    return _local_transaction(dsn, operation)


def capture_research_outcome_with_psycopg(
    dsn: str, *, condition_id: str, market_slug: str, resolved_at: datetime,
    actual_yes: bool, source_reference: str, source_content_sha256: str,
) -> ResearchEvaluationOutcome:
    """Save a caller-confirmed binary outcome; derive cutoff from registration.

    Does not fetch or authenticate settlement. Unknown, void and unresolved must
    not be submitted as False. A conflicting confirmation is rejected, not updated.
    """
    _identity(condition_id, market_slug)
    resolved = _utc("resolved_at", resolved_at)
    if type(actual_yes) is not bool:
        raise ValueError("actual_yes must be exact bool")
    text("source_reference", source_reference, 1024)
    if type(source_content_sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", source_content_sha256) is None:
        raise ValueError("invalid outcome digest")

    def operation(cursor):
        _lock(cursor, condition_id)
        market = _market(cursor, condition_id)
        if market is None or market.market_slug != market_slug:
            raise ResearchCaptureConflict("research_market_not_registered")
        cursor.execute(f"SELECT {_OUTCOME_COLUMNS} FROM research_capture.outcomes WHERE condition_id=%s", (condition_id,))
        existing = cursor.fetchone()
        if existing is not None:
            original = ResearchEvaluationOutcome(*existing)
            if (original.market_slug, original.resolved_at, original.actual_yes,
                original.source_reference, original.source_content_sha256, original.forecast_cutoff_at) != (
                    market_slug, resolved, actual_yes, source_reference, source_content_sha256, market.forecast_cutoff_at):
                raise ResearchCaptureConflict("research_outcome_conflict")
            return original
        cursor.execute("INSERT INTO research_capture.outcomes "
                       "(condition_id,market_slug,resolved_at,actual_yes,source_reference,source_content_sha256) "
                       f"VALUES (%s,%s,%s,%s,%s,%s) RETURNING {_OUTCOME_COLUMNS}",
                       (condition_id, market_slug, resolved, actual_yes, source_reference, source_content_sha256))
        return ResearchEvaluationOutcome(*cursor.fetchone())
    return _local_transaction(dsn, operation)


def load_research_evaluation_with_psycopg(
    dsn: str, *, generated_at: datetime | None = None, max_records: int = MAX_RECORDS,
    bucket_count: int = 10, min_sample_count: int = 30, min_bin_count: int = 5,
) -> ResearchEvaluationReport:
    """Read one consistent DB snapshot; never silently score a truncated cohort.

    No success-only/recent-history filter. Limits apply to ALL visible attempts
    and outcomes; exceeding either or 32 MiB of payloads raises, before loading
    bodies. A historical cutoff is permitted; a future report time is rejected.
    """
    at = None if generated_at is None else _utc("generated_at", generated_at)
    integer("max_records", max_records, 1, MAX_RECORDS)
    ResearchProbabilityDiagnostics((), bucket_count, min_sample_count, min_bin_count)

    def operation(cursor):
        cursor.execute("SELECT clock_timestamp()")
        server_now = _utc("server clock", cursor.fetchone()[0])
        if at is not None and at > server_now:
            raise ResearchCaptureConflict("research_evaluation_from_future")
        cutoff = server_now if at is None else at
        cursor.execute("SELECT count(*),coalesce(sum(octet_length(payload)),0) FROM research_capture.attempts WHERE recorded_at<=%s", (cutoff,))
        count, size = cursor.fetchone()
        cursor.execute("SELECT count(*) FROM research_capture.outcomes WHERE recorded_at<=%s", (cutoff,))
        outcome_count = cursor.fetchone()[0]
        if count > max_records or outcome_count > max_records or size > MAX_READ_BYTES:
            raise ResearchCaptureConflict("research_capture_history_limit")
        cursor.execute(f"SELECT {_RECORD_COLUMNS} FROM research_capture.attempts WHERE recorded_at<=%s ORDER BY record_id", (cutoff,))
        records = tuple(_record(row) for row in cursor.fetchall())
        cursor.execute(f"SELECT {_OUTCOME_COLUMNS} FROM research_capture.outcomes WHERE recorded_at<=%s ORDER BY condition_id", (cutoff,))
        outcomes = tuple(ResearchEvaluationOutcome(*row) for row in cursor.fetchall())
        if len(records) != count or len(outcomes) != outcome_count:
            raise ValueError("inconsistent capture snapshot")
        return ResearchEvaluationReport(records, outcomes, cutoff, bucket_count, min_sample_count, min_bin_count)
    return _local_transaction(dsn, operation, readonly=True)


__all__ = (
    "RegisteredResearchMarket", "ResearchCaptureConflict", "register_research_market_with_psycopg",
    "capture_research_with_psycopg", "capture_research_outcome_with_psycopg", "load_research_evaluation_with_psycopg",
)
