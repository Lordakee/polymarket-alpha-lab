"""Same-project append-only budgets and call reservations before provider entry.

Reuse the audited transaction/identity/DSN layer. No long-running transaction,
provider I/O, refunds, implicit policy writes or evidence transcript persistence.
"""
from dataclasses import replace
from hashlib import sha256

from polymarket_alpha_lab import research_capture_psycopg as db
from polymarket_alpha_lab import research_execution_psycopg as execution
from polymarket_alpha_lab.research_model_budget import (
    MAX_POLICY_BYTES, ModelBudgetSnapshot, StoredModelBudget, copy_budget, decode_budget,
)
from polymarket_alpha_lab.research_resolution import utc
from polymarket_alpha_lab.team_research_agent_types import identifier, integer, strict_json, text

_COLUMNS = 'budget_id,payload,payload_sha256,created_at,paper_only,report_only,readonly'


def _row(row):
    if type(row) is not tuple or len(row) != 7 or any(x is not True for x in row[4:]):
        raise ValueError('research_budget_row_invalid')
    policy = decode_budget(row[1], row[2])
    if row[0] != policy.budget_id:
        raise ValueError('research_budget_row_mismatch')
    return StoredModelBudget(policy, row[3])


def _load(cursor, budget_id):
    cursor.execute('SELECT octet_length(payload) FROM research_capture.model_budgets WHERE budget_id=%s', (budget_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    if type(row[0]) is not int or not 1 <= row[0] <= MAX_POLICY_BYTES:
        raise db.ResearchCaptureConflict('research_budget_payload_limit')
    cursor.execute(f'SELECT {_COLUMNS} FROM research_capture.model_budgets WHERE budget_id=%s', (budget_id,))
    result = _row(cursor.fetchone())
    if result.policy.budget_id != budget_id:
        raise ValueError('research_budget_lookup_mismatch')
    return result


def create_model_budget_with_psycopg(dsn, *, policy, allow_budget_write=False):
    if allow_budget_write is not True:
        raise ValueError('research_budget_write_opt_in_required')
    policy = copy_budget(policy)

    def operation(cursor):
        _lock(cursor, policy.budget_id)
        existing = _load(cursor, policy.budget_id)
        if existing is not None:
            if existing.policy.payload != policy.payload:
                raise db.ResearchCaptureConflict('research_budget_policy_conflict')
            return existing
        cursor.execute('INSERT INTO research_capture.model_budgets (budget_id,payload,payload_sha256) '
                       f'VALUES (%s,%s,%s) RETURNING {_COLUMNS}',
                       (policy.budget_id, policy.payload, policy.content_sha256))
        result = _row(cursor.fetchone())
        if result.policy.payload != policy.payload:
            raise ValueError('research_budget_insert_mismatch')
        return result
    return db._local_transaction(dsn, operation)


def _lock(cursor, budget_id):
    cursor.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',
                   ('polymarket/model_budget/' + budget_id,))


def load_model_budget_with_psycopg(dsn, *, budget_id):
    identifier('budget_id', budget_id)

    def operation(cursor):
        cursor.execute('SELECT clock_timestamp()')
        now = utc('database clock', cursor.fetchone()[0])
        stored = _load(cursor, budget_id)
        if stored is None:
            return None
        cursor.execute('SELECT count(*),coalesce(sum(reserved_micros),0),'
                       'coalesce(max(reservation_number),0) FROM research_capture.model_call_reservations '
                       'WHERE budget_id=%s', (budget_id,))
        count, amount, last = cursor.fetchone()
        # PostgreSQL sum(bigint) is exact numeric; do not round/truncate it.
        if type(count) is not int or type(last) is not int or count != last or amount != count*stored.policy.per_call_micros:
            raise ValueError('research_budget_accounting_invalid')
        return ModelBudgetSnapshot(stored, now, count, count*stored.policy.per_call_micros)
    return db._local_transaction(dsn, operation, readonly=True)


def _reserve_call(dsn, *, policy, request, call_number, messages_json, max_output_tokens):
    """Return True only for a newly committed permit; replay is always inert.

    A permit burns its full assumed charge even on an invalid reply, timeout or
    crash before sending. No release on uncertain acknowledgement or exceptions.
    """
    policy = copy_budget(policy)
    request = policy.bind_request(request)
    integer('call_number', call_number, 1, request.limits.max_model_calls)
    integer('max_output_tokens', max_output_tokens, 1, policy.max_output_tokens)
    text('messages_json', messages_json, 500000)
    raw = messages_json.encode('utf-8')
    if len(raw) > policy.max_message_bytes:
        raise ValueError('research_budget_message_limit')
    messages = strict_json(messages_json)
    if type(messages) is not list or not messages:
        raise ValueError('research_budget_message_invalid')
    checksum = sha256(raw).hexdigest()
    args = (policy.budget_id, request.record_id, request.content_sha256, call_number,
            checksum, len(raw), max_output_tokens)

    def operation(cursor):
        _lock(cursor, policy.budget_id)
        saved = _load(cursor, policy.budget_id)
        if saved is None or saved.policy.payload != policy.payload:
            raise db.ResearchCaptureConflict('research_budget_policy_conflict')
        cursor.execute('SELECT budget_id,request_sha256,message_sha256,message_bytes,max_output_tokens '
                       'FROM research_capture.model_call_reservations WHERE record_id=%s AND call_number=%s',
                       (request.record_id, call_number))
        prior = cursor.fetchone()
        if prior is not None:
            if prior != (policy.budget_id, request.content_sha256, checksum, len(raw), max_output_tokens):
                raise db.ResearchCaptureConflict('research_budget_call_conflict')
            return False
        claimed = execution._lookup(cursor, request.record_id)
        if (claimed is None or claimed.request.payload != request.payload or claimed.record is not None):
            raise db.ResearchCaptureConflict('research_budget_claim_required')
        # SQL trigger independently enforces aggregate caps, order, policy/claim
        # binding and DB time. The return value is checked before COMMIT returns.
        cursor.execute('INSERT INTO research_capture.model_call_reservations '
                       '(budget_id,record_id,request_sha256,call_number,message_sha256,message_bytes,max_output_tokens) '
                       'VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING budget_id,record_id,request_sha256,call_number, '
                       'message_sha256,message_bytes,max_output_tokens', args)
        if cursor.fetchone() != args:
            raise ValueError('research_budget_reservation_mismatch')
        return True
    return db._local_transaction(dsn, operation)
