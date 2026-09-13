"""Atomic resolution evidence + outcome storage through the existing local driver.

No connection implementation, credential discovery, network call or model here.
Use ProjectResearchSession for enforced project-private instance binding.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from hashlib import sha256

from polymarket_alpha_lab import research_capture_psycopg as capture
from polymarket_alpha_lab.research_resolution import MAX_REVIEW_AGE_SECONDS, ResolutionSubmission, assess_resolution, utc
from polymarket_alpha_lab.research_resolution_codec import decode_resolution, encode_resolution
from polymarket_alpha_lab.team_research_agent_types import hard_flags, identifier
from polymarket_alpha_lab.team_research_evaluation import ResearchEvaluationOutcome

_REFERENCE = "urn:polymarket-alpha-lab:resolution-review:"
_COLUMNS = "review_id,condition_id,market_slug,checked_at,recorded_at,status,reason_code,actual_yes,resolved_at,payload,payload_sha256,paper_only,report_only,readonly"


@dataclass(frozen=True, slots=True)
class StoredResolutionReview:
    submission: ResolutionSubmission = field(repr=False)
    recorded_at: datetime
    outcome: ResearchEvaluationOutcome | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        hard_flags(self)
        payload = encode_resolution(self.submission)
        item = decode_resolution(payload, expected_sha256=sha256(payload.encode()).hexdigest())
        object.__setattr__(self, "submission", item)
        object.__setattr__(self, "recorded_at", utc("recorded_at", self.recorded_at))
        if not timedelta(0) <= self.recorded_at - item.checked_at <= timedelta(seconds=MAX_REVIEW_AGE_SECONDS):
            raise ValueError("resolution_receipt_time_invalid")
        ready = assess_resolution(item).status == "ready"
        if ready != (self.outcome is not None):
            raise ValueError("resolution_outcome_link_invalid")
        if ready:
            outcome = self.outcome
            if type(outcome) is not ResearchEvaluationOutcome:
                raise ValueError("resolution_outcome_link_invalid")
            outcome.__post_init__()
            if (outcome.condition_id != item.condition_id
                    or outcome.market_slug != item.snapshot.market_slug
                    or outcome.actual_yes is not item.confirmation.actual_yes
                    or outcome.resolved_at != item.confirmation.resolved_at
                    or outcome.recorded_at < self.recorded_at
                    or outcome.source_reference != _REFERENCE + item.review_id
                    or outcome.source_content_sha256 != sha256(payload.encode()).hexdigest()):
                raise ValueError("resolution_outcome_link_invalid")


def _outcome(cursor, condition_id):
    cursor.execute(f"SELECT {capture._OUTCOME_COLUMNS} FROM research_capture.outcomes WHERE condition_id=%s", (condition_id,))
    row = cursor.fetchone()
    return None if row is None else ResearchEvaluationOutcome(*row)


def _decode_row(cursor, row) -> StoredResolutionReview:
    if type(row) is not tuple or len(row) != 14 or any(flag is not True for flag in row[11:]):
        raise ValueError("resolution_row_invalid")
    item = decode_resolution(row[9], expected_sha256=row[10])
    result = assess_resolution(item)
    ready = result.status == "ready"
    expected = (item.review_id, item.condition_id, item.snapshot.market_slug, item.checked_at,
        row[4], result.status, result.reason_code,
        item.confirmation.actual_yes if ready else None,
        item.confirmation.resolved_at if ready else None)
    if row[:9] != expected or (ready and type(row[7]) is not bool):
        raise ValueError("resolution_row_invalid")
    return StoredResolutionReview(item, row[4], _outcome(cursor, item.condition_id) if ready else None)


def record_resolution_review_with_psycopg(dsn: str, *, submission: ResolutionSubmission) -> StoredResolutionReview:
    """Record pending/blocked/unconfirmed checks too; promote only confirmed ones.

    Repeats require the SAME review ID and exact content. Promotion and retained
    evidence commit together. No market is automatically registered or re-timed.
    """
    payload = encode_resolution(submission)
    payload_hash = sha256(payload.encode()).hexdigest()
    item = decode_resolution(payload, expected_sha256=payload_hash)
    assessment = assess_resolution(item)
    ready = assessment.status == "ready"

    def operation(cursor):
        capture._lock(cursor, item.condition_id)
        market = capture._market(cursor, item.condition_id)
        if market is None or market.market_slug != item.snapshot.market_slug:
            raise capture.ResearchCaptureConflict("research_market_not_registered")
        cursor.execute(f"SELECT {_COLUMNS} FROM research_capture.resolution_reviews WHERE review_id=%s", (item.review_id,))
        existing = cursor.fetchone()
        if existing is not None:
            if existing[9] != payload:
                raise capture.ResearchCaptureConflict("research_resolution_review_conflict")
            return _decode_row(cursor, existing)
        cursor.execute("SELECT clock_timestamp()")
        now = utc("database clock", cursor.fetchone()[0])
        if not timedelta(0) <= now - item.checked_at <= timedelta(seconds=MAX_REVIEW_AGE_SECONDS):
            raise capture.ResearchCaptureConflict("research_resolution_capture_time_invalid")
        if ready:
            if item.confirmation.resolved_at < market.forecast_cutoff_at:
                raise capture.ResearchCaptureConflict("research_resolution_before_cutoff")
            if _outcome(cursor, item.condition_id) is not None:
                raise capture.ResearchCaptureConflict("research_outcome_conflict")
        cursor.execute("INSERT INTO research_capture.resolution_reviews "
            "(review_id,condition_id,market_slug,checked_at,status,reason_code,actual_yes,resolved_at,payload,payload_sha256) "
            f"VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING {_COLUMNS}",
            (item.review_id, item.condition_id, item.snapshot.market_slug, item.checked_at,
             assessment.status, assessment.reason_code,
             item.confirmation.actual_yes if ready else None,
             item.confirmation.resolved_at if ready else None, payload, payload_hash))
        row = cursor.fetchone()
        if ready:
            cursor.execute("INSERT INTO research_capture.outcomes "
                "(condition_id,market_slug,resolved_at,actual_yes,source_reference,source_content_sha256) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (item.condition_id, item.snapshot.market_slug, item.confirmation.resolved_at,
                 item.confirmation.actual_yes, _REFERENCE + item.review_id, payload_hash))
        return _decode_row(cursor, row)
    return capture._local_transaction(dsn, operation)


def load_resolution_review_with_psycopg(dsn: str, *, review_id: str) -> StoredResolutionReview | None:
    """Read raw evidence and recompute its assessment in one read-only snapshot."""
    identifier("review_id", review_id)

    def operation(cursor):
        cursor.execute(f"SELECT {_COLUMNS} FROM research_capture.resolution_reviews WHERE review_id=%s", (review_id,))
        row = cursor.fetchone()
        return None if row is None else _decode_row(cursor, row)
    return capture._local_transaction(dsn, operation, readonly=True)
