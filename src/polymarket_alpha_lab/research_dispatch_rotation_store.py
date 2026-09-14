"""Append-only cursor advancement through the original managed transaction API.

Selection receipts are not claims or evidence that any model call took place.
Only a caller receiving a newly COMMITTED receipt dispatches its selected work.
"""
from dataclasses import replace

from polymarket_alpha_lab import research_capture_psycopg as db
from polymarket_alpha_lab.research_dispatch_rotation import (
    MAX_TURN_BYTES, ResearchRotationTurn, StoredResearchRotationTurn, decode_turn,
)
from polymarket_alpha_lab.team_research_agent_types import identifier

_TABLE = 'research_capture.dispatch_turns'
_COLUMNS = ('rotation_id,turn_id,turn_number,start_slot,next_slot,roster_sha256,'
            'payload,payload_sha256,reserved_at,paper_only,report_only,readonly')


def _row(row):
    if type(row) is not tuple or len(row) != 12 or any(f is not True for f in row[9:]):
        raise ValueError('research_rotation_row_invalid')
    turn = decode_turn(row[6], row[7])
    if (any(type(row[i]) is not int for i in (2, 3, 4)) or row[:6] !=
            (turn.rotation_id, turn.turn_id, turn.turn_number, turn.start_slot,
             turn.next_slot, turn.roster_sha256)):
        raise ValueError('research_rotation_row_mismatch')
    return StoredResearchRotationTurn(turn, row[8])


def _load(cursor, rotation_id, turn_id=None):
    # Closed query fragments, never caller SQL. Latest lookup is index-bounded.
    where = 'WHERE rotation_id=%s'
    args = (rotation_id,)
    if turn_id is not None:
        where += ' AND turn_id=%s'
        args += (turn_id,)
    where += ' ORDER BY turn_number DESC LIMIT 1'
    cursor.execute(f'SELECT octet_length(payload) FROM {_TABLE} {where}', args)
    size = cursor.fetchone()
    if size is None:
        return None
    if type(size[0]) is not int or not 1 <= size[0] <= MAX_TURN_BYTES:
        raise db.ResearchCaptureConflict('research_rotation_payload_limit')
    cursor.execute(f'SELECT {_COLUMNS} FROM {_TABLE} {where}', args)
    result = _row(cursor.fetchone())
    if (result.turn.rotation_id != rotation_id
            or (turn_id is not None and result.turn.turn_id != turn_id)):
        raise ValueError('research_rotation_lookup_mismatch')
    return result


def inspect_research_turn_with_psycopg(dsn, *, rotation_id, turn_id):
    """Original reservation only; missing is not a statement about execution."""
    identifier('rotation_id', rotation_id)
    identifier('turn_id', turn_id)
    return db._local_transaction(dsn, lambda cur: _load(cur, rotation_id, turn_id), readonly=True)


def check_replay(stored, ids, max_tasks, max_workers):
    stored = replace(stored)
    turn = stored.turn
    if (tuple(r[0] for r in turn.roster), turn.max_tasks, turn.max_workers) != (ids, max_tasks, max_workers):
        raise db.ResearchCaptureConflict('research_rotation_turn_conflict')
    return stored


def _reserve(dsn, *, rotation_id, turn_id, roster, observed_at, states, request_keys, max_tasks, max_workers):
    # Validate the entire proposed metadata before a transaction starts.
    proposal = ResearchRotationTurn(rotation_id, turn_id, 1, roster, observed_at,
                                   states, request_keys, 0, max_tasks, max_workers)

    def operation(cursor):
        cursor.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',
                       ('polymarket/research_rotation/' + rotation_id,))
        prior = _load(cursor, rotation_id, turn_id)
        if prior is not None:
            check_replay(prior, tuple(r[0] for r in roster), max_tasks, max_workers)
            if prior.turn.roster != roster:
                raise db.ResearchCaptureConflict('research_rotation_roster_conflict')
            return False, prior
        previous = _load(cursor, rotation_id)
        if previous is not None and (previous.turn.roster != roster
                                     or previous.turn.request_keys != request_keys):
            raise db.ResearchCaptureConflict('research_rotation_roster_conflict')
        turn = replace(proposal,
            turn_number=1 if previous is None else previous.turn.turn_number + 1,
            start_slot=0 if previous is None else previous.turn.next_slot)
        cursor.execute(f'INSERT INTO {_TABLE} '
            '(rotation_id,turn_id,turn_number,start_slot,next_slot,roster_sha256,payload,payload_sha256) '
            f'VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING {_COLUMNS}',
            (rotation_id, turn_id, turn.turn_number, turn.start_slot, turn.next_slot,
             turn.roster_sha256, turn.payload, turn.content_sha256))
        result = _row(cursor.fetchone())
        if result.turn.payload != turn.payload:
            raise ValueError('research_rotation_insert_mismatch')
        return True, result
    # The helper does not return until COMMIT and connection cleanup succeed.
    return db._local_transaction(dsn, operation)
