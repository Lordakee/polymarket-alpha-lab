"""Canonical durable round-robin selection receipts, not execution claims.

One finite roster interleaves batch positions. The cursor advances before model
work, so an unclaimed failure cannot indefinitely occupy the head of that roster.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from hashlib import sha256
import json
import re

from polymarket_alpha_lab.research_dispatch import ResearchBatchSnapshot, MAX_BATCH_BYTES
from polymarket_alpha_lab.research_capture_codec import encode_research_capture
from polymarket_alpha_lab.research_resolution import utc
from polymarket_alpha_lab.team_research_agent_types import hard_flags, identifier, integer, strict_json

MAX_TURN_BYTES = 131072
STATES = ('pending', 'expired', 'incomplete', 'captured')
VERSION = 'research-dispatch-turn-v1'


def _dump(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def batch_ids(values):
    if type(values) is not tuple or not 1 <= len(values) <= 10:
        raise ValueError('research_rotation_roster_invalid')
    for value in values:
        identifier('batch_id', value)
    if len(set(values)) != len(values):
        raise ValueError('research_rotation_duplicate_batch')
    return values


def slots(roster):
    """A0,B0,C0,A1,B1,...; unequal batch lengths do not create empty slots."""
    return tuple((b, p) for p in range(max(r[2] for r in roster))
                 for b, r in enumerate(roster) if p < r[2])


def selection(states, start, cap):
    chosen = []
    visited = 0
    while visited < len(states) and len(chosen) < cap:
        position = (start + visited) % len(states)
        visited += 1
        if states[position] == 'pending':
            chosen.append(position)
    return tuple(chosen), (start + visited) % len(states), visited


def roster_inputs(snapshots):
    """Validate all bounded snapshots before any reservation/model operation.

    These are separate per-batch snapshots, not an atomic whole-roster view.
    Subsequent execution still checks actual claim state and current DB time.
    """
    if (type(snapshots) is not tuple or not 1 <= len(snapshots) <= 10
            or any(type(s) is not ResearchBatchSnapshot for s in snapshots)):
        raise ValueError('research_rotation_snapshots_invalid')
    copied = tuple(replace(s) for s in snapshots)
    roster = tuple((s.stored.batch.batch_id, s.stored.batch.content_sha256,
                    len(s.stored.batch.requests)) for s in copied)
    batch_ids(tuple(r[0] for r in roster))
    if (sum(r[2] for r in roster) > 100
            or sum(len(s.stored.batch.payload.encode()) for s in copied) > MAX_BATCH_BYTES):
        raise ValueError('research_rotation_input_limit')
    ordered = slots(roster)
    requests = tuple(copied[b].stored.batch.requests[p] for b, p in ordered)
    if (len({r.record_id for r in requests}) != len(requests) or
            len({(r.intake.team_id, r.model_id, r.protocol_version, r.intake.task_id)
                 for r in requests}) != len(requests)):
        raise ValueError('research_rotation_duplicate_request')
    # Bound aggregate retained result data too; each individual snapshot was
    # already bounded by the original store before loading its bodies.
    result_bytes = sum(len(encode_research_capture(record_id=e.record.record_id,
        model_id=e.record.model_id, protocol_version=e.record.protocol_version,
        run=e.record.run).encode()) for s in copied for e in s.executions
        if e is not None and e.record is not None)
    if result_bytes > 33554432:
        raise ValueError('research_rotation_result_limit')
    per_batch_states = tuple(s.states() for s in copied)
    return (roster, tuple(s.generated_at for s in copied),
            tuple(per_batch_states[b][p] for b, p in ordered), requests)


@dataclass(frozen=True, slots=True)
class ResearchRotationTurn:
    rotation_id: str
    turn_id: str
    turn_number: int
    roster: tuple[tuple[str, str, int], ...]
    observed_at: tuple[datetime, ...]
    states: tuple[str, ...]
    request_keys: tuple[tuple[str, str], ...]
    start_slot: int
    max_tasks: int
    max_workers: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self):
        identifier('rotation_id', self.rotation_id)
        identifier('turn_id', self.turn_id)
        integer('turn_number', self.turn_number, 1, 1000000000)
        integer('max_tasks', self.max_tasks, 1, 100)
        integer('max_workers', self.max_workers, 1, 8)
        hard_flags(self)
        if (type(self.roster) is not tuple or not 1 <= len(self.roster) <= 10
                or any(type(r) is not tuple or len(r) != 3 for r in self.roster)):
            raise ValueError('research_rotation_roster_invalid')
        batch_ids(tuple(r[0] for r in self.roster))
        for _, digest, count in self.roster:
            if type(digest) is not str or re.fullmatch('[a-f0-9]{64}', digest) is None:
                raise ValueError('research_rotation_hash_invalid')
            integer('request_count', count, 1, 100)
        count = sum(r[2] for r in self.roster)
        if not 1 <= count <= 100:
            raise ValueError('research_rotation_input_limit')
        if (type(self.observed_at) is not tuple or len(self.observed_at) != len(self.roster)
                or type(self.states) is not tuple or len(self.states) != count
                or any(type(s) is not str or s not in STATES for s in self.states)):
            raise ValueError('research_rotation_state_invalid')
        if (type(self.request_keys) is not tuple or len(self.request_keys) != count
                or any(type(k) is not tuple or len(k) != 2 for k in self.request_keys)):
            raise ValueError('research_rotation_request_keys_invalid')
        for rid, digest in self.request_keys:
            identifier('record_id', rid)
            if type(digest) is not str or re.fullmatch('[a-f0-9]{64}', digest) is None:
                raise ValueError('research_rotation_hash_invalid')
        if len({k[0] for k in self.request_keys}) != count:
            raise ValueError('research_rotation_duplicate_request')
        object.__setattr__(self, 'observed_at', tuple(utc('observed_at', t) for t in self.observed_at))
        integer('start_slot', self.start_slot, 0, count - 1)

    @property
    def chosen(self):
        return selection(self.states, self.start_slot, self.max_tasks)[0]

    @property
    def next_slot(self):
        return selection(self.states, self.start_slot, self.max_tasks)[1]

    @property
    def roster_sha256(self):
        return sha256(_dump(self.roster).encode()).hexdigest()

    @property
    def payload(self):
        return _dump(dict(schema_version=VERSION, rotation_id=self.rotation_id,
            turn_id=self.turn_id, turn_number=self.turn_number, roster=self.roster,
            observed_at=[t.isoformat() for t in self.observed_at], states=self.states,
            request_keys=self.request_keys,
            start_slot=self.start_slot, max_tasks=self.max_tasks, max_workers=self.max_workers,
            paper_only=True, report_only=True, readonly=True))

    @property
    def content_sha256(self):
        return sha256(self.payload.encode()).hexdigest()


def decode_turn(payload, digest):
    try:
        if (type(payload) is not str or not 1 <= len(payload.encode()) <= MAX_TURN_BYTES
                or type(digest) is not str or sha256(payload.encode()).hexdigest() != digest):
            raise ValueError
        data = strict_json(payload)
        if type(data) is not dict or data.pop('schema_version', None) != VERSION:
            raise ValueError
        for key in ('roster', 'observed_at', 'states', 'request_keys'):
            if type(data[key]) is not list:
                raise ValueError
        if any(type(r) is not list for r in data['roster']):
            raise ValueError
        if any(type(k) is not list for k in data['request_keys']):
            raise ValueError
        data['request_keys'] = tuple(tuple(k) for k in data['request_keys'])
        data['roster'] = tuple(tuple(r) for r in data['roster'])
        data['observed_at'] = tuple(datetime.fromisoformat(t) for t in data['observed_at'])
        data['states'] = tuple(data['states'])
        result = ResearchRotationTurn(**data)
        if result.payload != payload:
            raise ValueError
        return result
    except Exception:
        raise ValueError('research_rotation_payload_invalid') from None


@dataclass(frozen=True, slots=True)
class StoredResearchRotationTurn:
    turn: ResearchRotationTurn = field(repr=False)
    reserved_at: datetime

    def __post_init__(self):
        if type(self.turn) is not ResearchRotationTurn:
            raise ValueError('research_rotation_turn_invalid')
        object.__setattr__(self, 'turn', replace(self.turn))
        object.__setattr__(self, 'reserved_at', utc('reserved_at', self.reserved_at))
        if max(self.turn.observed_at) > self.reserved_at:
            raise ValueError('research_rotation_clock_regression')

    def to_dict(self):
        self.__post_init__()
        t = self.turn
        return dict(rotation_id=t.rotation_id, turn_id=t.turn_id, turn_number=t.turn_number,
            reserved_at=self.reserved_at.isoformat(), payload_sha256=t.content_sha256,
            roster_sha256=t.roster_sha256, batch_ids=[r[0] for r in t.roster],
            start_slot=t.start_slot, next_slot=t.next_slot, selected_slots=list(t.chosen),
            selection_snapshots_at=[x.isoformat() for x in t.observed_at],
            max_tasks=t.max_tasks, max_workers=t.max_workers,
            reservation_is_execution_claim=False, final_database_state_checked=False,
            automatic_reclaim_permitted=False, hard_money_cap_enforced=False,
            paper_only=True, report_only=True, readonly=True)
