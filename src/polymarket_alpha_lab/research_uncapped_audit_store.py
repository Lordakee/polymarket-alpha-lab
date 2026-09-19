"""Same-project append-only permission/call evidence, no external I/O or retries.

Use the existing DSN/instance/transaction boundary. Commit a start before client
entry, and a separately immutable outcome before returning a validated reply.
"""
from dataclasses import replace
from hashlib import sha256

from polymarket_alpha_lab import research_capture_psycopg as db
from polymarket_alpha_lab import research_execution_psycopg as execution
from polymarket_alpha_lab.research_uncapped import MAX_AUTHORIZATION_BYTES, copy_authorization, decode_authorization
from polymarket_alpha_lab.research_uncapped_audit import (
    StoredUncappedAuthorization, UncappedCallStart, UncappedCallOutcome,
    UncappedAuditSnapshot, reply_fingerprint,
)
from polymarket_alpha_lab.team_research_agent_types import identifier, integer, strict_json

_AUTH = 'authorization_id,payload,payload_sha256,recorded_at,paper_only,report_only,readonly'
_START = ('authorization_id,authorization_sha256,record_id,request_sha256,call_number,'
          'message_sha256,message_bytes,max_output_tokens,started_at')


def _lock(cursor, key):
    cursor.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))', ('polymarket/uncapped_audit/'+key,))


def _auth_row(row):
    if type(row) is not tuple or len(row) != 7 or any(v is not True for v in row[4:]):
        raise ValueError('research_uncapped_audit_row_invalid')
    p = decode_authorization(row[1], row[2])
    if row[0] != p.authorization_id:
        raise ValueError('research_uncapped_audit_binding_invalid')
    return StoredUncappedAuthorization(p, row[3])


def _load(cursor, authorization_id):
    cursor.execute('SELECT octet_length(payload) FROM research_capture.uncapped_authorizations '
                   'WHERE authorization_id=%s', (authorization_id,))
    size = cursor.fetchone()
    if size is None:
        return None
    if type(size) is not tuple or len(size) != 1:
        raise ValueError('research_uncapped_audit_row_invalid')
    integer('payload_bytes', size[0], 1, MAX_AUTHORIZATION_BYTES)
    cursor.execute(f'SELECT {_AUTH} FROM research_capture.uncapped_authorizations WHERE authorization_id=%s',
                   (authorization_id,))
    stored = _auth_row(cursor.fetchone())
    if stored.authorization.authorization_id != authorization_id:
        raise ValueError('research_uncapped_audit_lookup_mismatch')
    return stored


def create_uncapped_authorization_with_psycopg(dsn, *, authorization, allow_authorization_write=False):
    if allow_authorization_write is not True:
        raise ValueError('research_uncapped_audit_write_opt_in_required')
    authorization = copy_authorization(authorization)
    payload = authorization.payload

    def operation(cursor):
        _lock(cursor, 'authorization/'+authorization.authorization_id)
        prior = _load(cursor, authorization.authorization_id)
        if prior is not None:
            if prior.authorization.payload != payload:
                raise db.ResearchCaptureConflict('research_uncapped_audit_authorization_conflict')
            return prior
        cursor.execute('INSERT INTO research_capture.uncapped_authorizations '
                       f'(authorization_id,payload,payload_sha256) VALUES (%s,%s,%s) RETURNING {_AUTH}',
                       (authorization.authorization_id, payload, authorization.content_sha256))
        result = _auth_row(cursor.fetchone())
        if result.authorization.payload != payload:
            raise ValueError('research_uncapped_audit_insert_mismatch')
        return result
    return db._local_transaction(dsn, operation)


def load_uncapped_authorization_with_psycopg(dsn, *, authorization_id):
    identifier('authorization_id', authorization_id)
    return db._local_transaction(dsn, lambda cursor: _load(cursor, authorization_id), readonly=True)


def require_authorization(dsn, authorization):
    authorization = copy_authorization(authorization)
    saved = load_uncapped_authorization_with_psycopg(dsn, authorization_id=authorization.authorization_id)
    if type(saved) is not StoredUncappedAuthorization or replace(saved).authorization.payload != authorization.payload:
        raise ValueError('research_uncapped_audit_authorization_required')


def _start_row(row):
    if type(row) is not tuple or len(row) != 12 or any(v is not True for v in row[9:]):
        raise ValueError('research_uncapped_audit_row_invalid')
    return UncappedCallStart(*row[:9])


def _begin_call(dsn, *, authorization, request, call_number, messages_json, max_output_tokens):
    p = copy_authorization(authorization)
    request = p.bind_request(request)
    integer('call_number', call_number, 1, request.limits.max_model_calls)
    integer('max_output_tokens', max_output_tokens, 1, request.limits.max_output_tokens)
    if type(messages_json) is not str or not 1 <= len(messages_json) <= request.limits.max_context_chars:
        raise ValueError('research_uncapped_audit_message_invalid')
    raw = messages_json.encode('utf-8')
    integer('message_bytes', len(raw), 1, 2000000)
    messages = strict_json(messages_json)
    if type(messages) is not list or not messages:
        raise ValueError('research_uncapped_audit_message_invalid')
    args = (p.authorization_id, p.content_sha256, request.record_id, request.content_sha256,
            call_number, sha256(raw).hexdigest(), len(raw), max_output_tokens)

    def operation(cursor):
        _lock(cursor, 'call/'+request.record_id)
        saved = _load(cursor, p.authorization_id)
        if saved is None or saved.authorization.payload != p.payload:
            raise db.ResearchCaptureConflict('research_uncapped_audit_authorization_conflict')
        claimed = execution._lookup(cursor, request.record_id)
        if claimed is None or claimed.request.payload != request.payload or claimed.record is not None:
            raise db.ResearchCaptureConflict('research_uncapped_audit_claim_required')
        # Unique (record_id,call_number) never grants permission to transmit again.
        cursor.execute('INSERT INTO research_capture.uncapped_call_starts '
                       '(authorization_id,authorization_sha256,record_id,request_sha256,call_number,'
                       'message_sha256,message_bytes,max_output_tokens) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) '
                       f'RETURNING {_START},paper_only,report_only,readonly', args)
        start = _start_row(cursor.fetchone())
        if tuple(getattr(start, key) for key in _START.split(',')[:-1]) != args:
            raise ValueError('research_uncapped_audit_start_mismatch')
        return start
    return db._local_transaction(dsn, operation)


def _finish_call(dsn, *, start, status, reply=None):
    if type(start) is not UncappedCallStart:
        raise ValueError('research_uncapped_audit_start_invalid')
    start = replace(start)
    tokens = checksum = None
    if reply is not None:
        copied, checksum = reply_fingerprint(reply)
        tokens = copied.total_tokens
    # Validate status/usage before connection; DB supplies the actual timestamp.
    UncappedCallOutcome(start, status, tokens, checksum, start.started_at)
    args = (start.record_id, start.call_number, status, tokens, checksum)

    def operation(cursor):
        _lock(cursor, 'call/'+start.record_id)
        cursor.execute(f'SELECT {_START},paper_only,report_only,readonly '
                       'FROM research_capture.uncapped_call_starts WHERE record_id=%s AND call_number=%s', args[:2])
        if _start_row(cursor.fetchone()) != start:
            raise db.ResearchCaptureConflict('research_uncapped_audit_start_conflict')
        columns = 'record_id,call_number,status,reported_total_tokens,reply_sha256,recorded_at,paper_only,report_only,readonly'
        cursor.execute(f'SELECT {columns} FROM research_capture.uncapped_call_outcomes '
                       'WHERE record_id=%s AND call_number=%s', args[:2])
        row = cursor.fetchone()
        if row is None:
            cursor.execute('INSERT INTO research_capture.uncapped_call_outcomes '
                           '(record_id,call_number,status,reported_total_tokens,reply_sha256) '
                           f'VALUES (%s,%s,%s,%s,%s) RETURNING {columns}', args)
            row = cursor.fetchone()
        if (type(row) is not tuple or len(row) != 9 or row[:5] != args
                or any(v is not True for v in row[6:])):
            raise db.ResearchCaptureConflict('research_uncapped_audit_outcome_conflict')
        return UncappedCallOutcome(start, status, tokens, checksum, row[5])
    return db._local_transaction(dsn, operation)


def inspect_uncapped_calls_with_psycopg(dsn, *, record_id):
    identifier('record_id', record_id)

    def operation(cursor):
        cursor.execute(f'SELECT {_START},paper_only,report_only,readonly '
                       'FROM research_capture.uncapped_call_starts WHERE record_id=%s ORDER BY call_number LIMIT 33',
                       (record_id,))
        calls = tuple(_start_row(row) for row in cursor.fetchall())
        if len(calls) > 32:
            raise ValueError('research_uncapped_audit_call_limit')
        outcomes = []
        for start in calls:
            cursor.execute('SELECT status,reported_total_tokens,reply_sha256,recorded_at,paper_only,report_only,readonly '
                           'FROM research_capture.uncapped_call_outcomes WHERE record_id=%s AND call_number=%s',
                           (record_id, start.call_number))
            row = cursor.fetchone()
            if row is not None:
                if type(row) is not tuple or len(row) != 7 or any(v is not True for v in row[4:]):
                    raise ValueError('research_uncapped_audit_row_invalid')
                outcomes.append(UncappedCallOutcome(start, *row[:4]))
        return UncappedAuditSnapshot(record_id, calls, tuple(outcomes))
    return db._local_transaction(dsn, operation, readonly=True)
