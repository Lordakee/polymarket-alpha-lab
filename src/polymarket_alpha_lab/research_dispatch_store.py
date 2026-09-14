"""Explicit append-only batch admission and one consistent DB snapshot.

No new driver, DSN handling, clocks supplied by callers, models or schema DDL.
A queued request is NOT an execution claim; only the existing runner claims it.
"""
from __future__ import annotations

from polymarket_alpha_lab import research_capture_psycopg as db
from polymarket_alpha_lab import research_execution_psycopg as execution
from polymarket_alpha_lab.research_dispatch import (
    MAX_BATCH_BYTES, ResearchBatch, ResearchBatchSnapshot, StoredResearchBatch,
    copy_batch, decode_batch, startable,
)
from polymarket_alpha_lab.research_resolution import utc
from polymarket_alpha_lab.team_research_agent_types import identifier

_COLUMNS = 'batch_id,request_count,enqueued_at,payload,payload_sha256,paper_only,report_only,readonly'


def _row(row) -> StoredResearchBatch:
    if type(row) is not tuple or len(row) != 8 or any(flag is not True for flag in row[5:]):
        raise ValueError('research_batch_row_invalid')
    batch = decode_batch(row[3], row[4])
    if type(row[1]) is not int or (row[0], row[1]) != (batch.batch_id, len(batch.requests)):
        raise ValueError('research_batch_row_mismatch')
    return StoredResearchBatch(batch, row[2])


def _load(cursor, batch_id: str) -> StoredResearchBatch | None:
    cursor.execute('SELECT octet_length(payload) FROM research_capture.dispatch_batches WHERE batch_id=%s', (batch_id,))
    size = cursor.fetchone()
    if size is None:
        return None
    if type(size[0]) is not int or not 1 <= size[0] <= MAX_BATCH_BYTES:
        raise db.ResearchCaptureConflict('research_batch_payload_limit')
    cursor.execute(f'SELECT {_COLUMNS} FROM research_capture.dispatch_batches WHERE batch_id=%s', (batch_id,))
    return _row(cursor.fetchone())


def enqueue_research_batch_with_psycopg(dsn: str, *, batch: ResearchBatch,
                                        allow_queue_write: bool = False) -> StoredResearchBatch:
    """Atomically persist all inputs; an exact retry returns the original receipt.

    Existing same-batch retries may occur after expiry. New admission uses DB
    time and refuses expired/future input. No markets or execution claims are
    created here. Source/provider/operator suitability remains the caller's duty.
    """
    if allow_queue_write is not True:
        raise ValueError('research_batch_queue_write_opt_in_required')
    batch = copy_batch(batch)

    def operation(cursor):
        cursor.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',
                       ('polymarket/research_dispatch/' + batch.batch_id,))
        existing = _load(cursor, batch.batch_id)
        if existing is not None:
            if existing.batch.payload != batch.payload:
                raise db.ResearchCaptureConflict('research_batch_identity_conflict')
            return existing
        cursor.execute('SELECT clock_timestamp()')
        now = utc('database clock', cursor.fetchone()[0])
        if any(not startable(r, now) for r in batch.requests):
            raise db.ResearchCaptureConflict('research_batch_not_startable')
        cursor.execute('INSERT INTO research_capture.dispatch_batches '
                       '(batch_id,request_count,payload,payload_sha256) VALUES (%s,%s,%s,%s) '
                       f'RETURNING {_COLUMNS}',
                       (batch.batch_id, len(batch.requests), batch.payload, batch.content_sha256))
        result = _row(cursor.fetchone())
        if result.batch.payload != batch.payload:
            raise ValueError('research_batch_insert_mismatch')
        return result
    return db._local_transaction(dsn, operation)


def load_research_batch_with_psycopg(dsn: str, *, batch_id: str) -> ResearchBatchSnapshot | None:
    """One bounded repeatable-read view. Missing batch is not an empty database.

    Verify the complete stored request/receipt binding. Read caps fail rather
    than truncate. Queue membership does not change existing scoring semantics.
    """
    identifier('batch_id', batch_id)

    def operation(cursor):
        cursor.execute('SELECT clock_timestamp()')
        now = utc('database clock', cursor.fetchone()[0])
        stored = _load(cursor, batch_id)
        if stored is None:
            return None
        ids = [r.record_id for r in stored.batch.requests]
        cursor.execute('SELECT coalesce(sum(octet_length(c.request_payload) + '
                       'coalesce(octet_length(a.payload),0)),0) FROM research_capture.execution_claims c '
                       'LEFT JOIN research_capture.attempts a ON a.record_id=c.record_id '
                       'WHERE c.record_id=ANY(%s)', (ids,))
        size = cursor.fetchone()[0]
        if type(size) is not int or not 0 <= size <= db.MAX_READ_BYTES:
            raise db.ResearchCaptureConflict('research_batch_execution_payload_limit')
        states = tuple(execution._lookup(cursor, request.record_id) for request in stored.batch.requests)
        return ResearchBatchSnapshot(stored, now, states)
    return db._local_transaction(dsn, operation, readonly=True)


__all__ = ('enqueue_research_batch_with_psycopg', 'load_research_batch_with_psycopg')
