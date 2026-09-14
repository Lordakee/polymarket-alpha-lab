"""Complete bounded inventory of execution claims in one private read snapshot.

Uses the existing local transaction, claim decoder and captured-result binding.
No scheduler, worker-liveness inference, repair, scoring or new persistence.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime

from polymarket_alpha_lab import research_capture_psycopg as db
from polymarket_alpha_lab import research_execution_psycopg as execution
from polymarket_alpha_lab.research_execution import CapturedResearchExecution
from polymarket_alpha_lab.team_research_agent_types import integer

MAX_CLAIMS = 1000
STATES = ("result_not_captured", "captured_intake_blocked", "captured_completed",
          "captured_failed", "captured_blocked")
_JOIN = " FROM research_capture.attempts a JOIN research_capture.execution_claims c ON c.record_id=a.record_id"


@dataclass(frozen=True, slots=True)
class ResearchExecutionInventory:
    generated_at: datetime
    executions: tuple[CapturedResearchExecution, ...] = field(repr=False)
    unclaimed_attempt_count: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", db._utc("inventory clock", self.generated_at))
        integer("unclaimed_attempt_count", self.unclaimed_attempt_count, 0, 2**63 - 1)
        if (type(self.executions) is not tuple or len(self.executions) > MAX_CLAIMS
                or any(type(item) is not CapturedResearchExecution for item in self.executions)):
            raise ValueError("research_execution_inventory_invalid")
        items = tuple(replace(item) for item in self.executions)
        if len({item.request.record_id for item in items}) != len(items):
            raise ValueError("research_execution_inventory_duplicate")
        for item in items:
            if item.status not in ("incomplete", "already_captured"):
                raise ValueError("research_execution_inventory_unpersisted")
            if (item.claimed_at > self.generated_at
                    or (item.record is not None and item.record.recorded_at > self.generated_at)):
                raise db.ResearchCaptureConflict("research_execution_inventory_future_record")
        object.__setattr__(self, "executions", tuple(sorted(items,
            key=lambda item: (item.claimed_at, item.request.record_id))))

    def to_dict(self) -> dict:
        # Reuse the reviewed metadata-only single-record exporter; never export
        # source bodies/probabilities or sum model scores across unrelated tasks.
        from polymarket_alpha_lab.research_execution_cli import execution_summary
        validated = replace(self)
        rows = [execution_summary(item, record_id=item.request.record_id) for item in validated.executions]
        counts = {state: sum(row["inspection_status"] == state for row in rows) for state in STATES}
        incomplete = counts["result_not_captured"]
        return dict(generated_at=validated.generated_at.isoformat(),
            inventory_status="no_claims" if not rows else "incomplete_claims_present" if incomplete else "all_claims_have_results",
            claim_count=len(rows), captured_result_count=len(rows)-incomplete,
            incomplete_claim_count=incomplete, state_counts=counts, executions=rows,
            unclaimed_attempt_count=validated.unclaimed_attempt_count,
            unclaimed_attempts_decoded=False, claim_inventory_complete=True,
            incomplete_claims_block_evaluation=incomplete > 0, entire_history_checked=False,
            worker_liveness="unknown", automatic_retry_permitted=False,
            scoring_performed=False, forecast_approval_performed=False,
            paper_only=True, report_only=True, readonly=True)


def _stats(cursor, query: str, at: datetime) -> tuple[int, int]:
    cursor.execute(query)
    count, size, latest = cursor.fetchone()
    integer("inventory count", count, 0, 2**63 - 1)
    integer("inventory bytes", size, 0, 2**63 - 1)
    if not count:
        if size or latest is not None:
            raise ValueError("research_execution_inventory_invalid_stats")
    elif latest is None or not size:
        raise ValueError("research_execution_inventory_invalid_stats")
    elif db._utc("latest receipt", latest) > at:
        # Do not silently omit a future receipt and present a falsely complete
        # current inventory after a database-clock regression or corrupt stamp.
        raise db.ResearchCaptureConflict("research_execution_inventory_future_record")
    return count, size


def _rows(cursor, query: str, count: int, size: int) -> tuple:
    cursor.execute(query)
    rows = tuple(cursor.fetchall())
    if (len(rows) != count or any(type(row) is not tuple or len(row) != 14
                                 or type(row[9]) is not str for row in rows)
            or sum(len(row[9].encode("utf-8")) for row in rows) != size):
        raise ValueError("research_execution_inventory_snapshot_mismatch")
    return rows


def load_execution_inventory_with_psycopg(dsn: str, *, max_records: int = MAX_CLAIMS) -> ResearchExecutionInventory:
    """All visible claims plus matching attempts, or fail before loading bodies.

    Not a historical view or paginated sample. Counts and payloads use one
    existing read-only repeatable-read transaction; there is no per-row lookup.
    A missing result is retained, regardless of market settlement. Standalone
    attempts without a claim are counted separately but NOT decoded or scored.
    """
    integer("max_records", max_records, 1, MAX_CLAIMS)

    def operation(cursor):
        cursor.execute("SELECT clock_timestamp()")
        at = db._utc("inventory clock", cursor.fetchone()[0])
        count, claim_bytes = _stats(cursor,
            "SELECT count(*),coalesce(sum(octet_length(request_payload)),0),max(claimed_at) "
            "FROM research_capture.execution_claims", at)
        if count > max_records or claim_bytes > db.MAX_READ_BYTES:
            raise db.ResearchCaptureConflict("research_execution_inventory_limit")
        captured, result_bytes = _stats(cursor,
            "SELECT count(*),coalesce(sum(octet_length(a.payload)),0),max(a.recorded_at)" + _JOIN, at)
        if captured > count:
            raise ValueError("research_execution_inventory_invalid_stats")
        if claim_bytes + result_bytes > db.MAX_READ_BYTES:
            raise db.ResearchCaptureConflict("research_execution_inventory_limit")
        cursor.execute("SELECT count(*) FROM research_capture.attempts a WHERE NOT EXISTS "
                       "(SELECT 1 FROM research_capture.execution_claims c WHERE c.record_id=a.record_id)")
        unclaimed = cursor.fetchone()[0]
        integer("unclaimed attempts", unclaimed, 0, 2**63 - 1)
        claim_rows = _rows(cursor, "SELECT " + execution._CLAIM_COLUMNS +
            ' FROM research_capture.execution_claims ORDER BY claimed_at,record_id COLLATE "C"', count, claim_bytes)
        record_rows = _rows(cursor, "SELECT " + ",".join("a." + name for name in db._RECORD_COLUMNS.split(",")) +
            _JOIN + ' ORDER BY a.record_id COLLATE "C"', captured, result_bytes)
        claims = tuple(execution._claim_row(row) for row in claim_rows)
        ids = {item.request.record_id for item in claims}
        records = {}
        for row in record_rows:
            record = db._record(row)
            if record.record_id not in ids or record.record_id in records:
                raise ValueError("research_execution_inventory_record_scope_invalid")
            records[record.record_id] = record
        states = tuple(item if item.request.record_id not in records else
            replace(item, status="already_captured", record=records[item.request.record_id]) for item in claims)
        return ResearchExecutionInventory(at, states, unclaimed)

    return db._local_transaction(dsn, operation, readonly=True)


__all__ = ("ResearchExecutionInventory", "load_execution_inventory_with_psycopg")
