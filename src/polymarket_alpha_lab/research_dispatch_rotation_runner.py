"""Explicit fair turns across an immutable bounded roster of persisted batches.

No daemon, time-based retries, provider choice, alternate execution ledger or
hidden credential lookup. A new turn ID is an explicit new bounded invocation.
"""
from dataclasses import dataclass, field, replace

from polymarket_alpha_lab import research_dispatch_runner as drain
from polymarket_alpha_lab.research_dispatch import ResearchBatchSnapshot
from polymarket_alpha_lab.research_dispatch_rotation import (
    StoredResearchRotationTurn, batch_ids, roster_inputs,
)
from polymarket_alpha_lab.research_dispatch_rotation_store import (
    _reserve, check_replay, inspect_research_turn_with_psycopg,
)
from polymarket_alpha_lab.research_dispatch_store import load_research_batch_with_psycopg
from polymarket_alpha_lab.team_research_agent_types import identifier, integer


@dataclass(frozen=True, slots=True)
class ResearchRotationReport:
    status: str
    stored: StoredResearchRotationTurn | None = field(default=None, repr=False)
    attempts: tuple[drain.DispatchAttempt, ...] = field(default=(), repr=False)
    stop_requested: bool = False

    def __post_init__(self):
        if (type(self.status) is not str or self.status not in
                ('stopped_before_reservation', 'turn_already_reserved', 'dispatched')
                or type(self.stop_requested) is not bool or type(self.attempts) is not tuple):
            raise ValueError('research_rotation_report_invalid')
        if self.status == 'stopped_before_reservation':
            if self.stored is not None or self.attempts or not self.stop_requested:
                raise ValueError('research_rotation_report_invalid')
            return
        if type(self.stored) is not StoredResearchRotationTurn:
            raise ValueError('research_rotation_receipt_missing')
        object.__setattr__(self, 'stored', replace(self.stored))
        if any(type(a) is not drain.DispatchAttempt for a in self.attempts):
            raise ValueError('research_rotation_attempt_invalid')
        attempts = tuple(replace(a) for a in self.attempts)
        object.__setattr__(self, 'attempts', attempts)
        if self.status == 'turn_already_reserved':
            if attempts:
                raise ValueError('research_rotation_replay_execution')
            return
        chosen = self.stored.turn.chosen
        if tuple(a.position for a in attempts) != chosen[:len(attempts)]:
            raise ValueError('research_rotation_attempt_order')
        for attempt in attempts:
            if attempt.execution is not None:
                request = attempt.execution.request
                if (request.record_id, request.content_sha256) != self.stored.turn.request_keys[attempt.position]:
                    raise ValueError('research_rotation_execution_binding_invalid')
        if not self.stop_requested and len(attempts) != len(chosen):
            raise ValueError('research_rotation_attempts_incomplete')
        if not self.stop_requested and any(a.status == 'stopped_before_start' for a in attempts):
            raise ValueError('research_rotation_stop_mismatch')

    def to_dict(self):
        self.__post_init__()
        rows = [dict(slot=a.position, status=a.status,
                     execution=None if a.execution is None else a.execution.to_dict()) for a in self.attempts]
        return dict(status=self.status, turn=None if self.stored is None else self.stored.to_dict(),
            stop_requested=self.stop_requested, attempts=rows,
            execution_invocations=sum(a.status != 'stopped_before_start' for a in self.attempts),
            operation_failure_count=sum(a.status == 'operation_failed' for a in self.attempts),
            cursor_written_here=self.status == 'dispatched',
            prior_execution_state_checked=False, final_database_state_checked=False,
            automatic_reclaim_permitted=False, hard_money_cap_enforced=False,
            market_fetch_performed=False,
            model_calls_possible=any(a.status != 'stopped_before_start' for a in self.attempts), paper_only=True, report_only=True, readonly=True)


def run_research_rotation_with_psycopg(dsn, *, rotation_id, turn_id, batch_ids_to_run,
        model_factory, allow_model_calls=False, max_tasks=10, max_workers=2, stop=None):
    """Persist a fair selection, then reuse the original bounded claim runner.

    The roster is fixed under rotation_id. Same turn_id replays only its original
    reservation and starts NOTHING, even after interrupted execution. A new turn
    advances from its predecessor's cursor, skipping captured/incomplete/expired
    requests. Failed unclaimed jobs are revisited only by a NEW explicit turn
    after the ring reaches them, never immediately retried within this call.
    """
    identifier('rotation_id', rotation_id)
    identifier('turn_id', turn_id)
    ids = batch_ids(batch_ids_to_run)
    integer('max_tasks', max_tasks, 1, 100)
    integer('max_workers', max_workers, 1, 8)
    if allow_model_calls is not True or not callable(model_factory):
        raise ValueError('research_rotation_model_opt_in_required')
    if stop is not None and type(stop) is not drain.ResearchDispatchStop:
        raise ValueError('research_rotation_stop_invalid')
    control = drain.ResearchDispatchStop() if stop is None else stop
    if control.is_stopped():
        return ResearchRotationReport('stopped_before_reservation', stop_requested=True)
    prior = inspect_research_turn_with_psycopg(dsn, rotation_id=rotation_id, turn_id=turn_id)
    if prior is not None:
        prior = check_replay(prior, ids, max_tasks, max_workers)
        return ResearchRotationReport('turn_already_reserved', prior, stop_requested=control.is_stopped())
    snapshots = []
    for batch_id in ids:
        if control.is_stopped():
            return ResearchRotationReport('stopped_before_reservation', stop_requested=True)
        value = load_research_batch_with_psycopg(dsn, batch_id=batch_id)
        if type(value) is not ResearchBatchSnapshot or value.stored.batch.batch_id != batch_id:
            raise ValueError('research_rotation_batch_not_found')
        snapshots.append(value)
        # Reject cumulative limits as each batch arrives, not after retaining
        # ten maximum-sized snapshots. No partial roster is ever reserved.
        roster, observed_at, states, requests = roster_inputs(tuple(snapshots))
    if control.is_stopped():
        return ResearchRotationReport('stopped_before_reservation', stop_requested=True)
    owned, stored = _reserve(dsn, rotation_id=rotation_id, turn_id=turn_id, roster=roster,
        observed_at=observed_at, states=states,
        request_keys=tuple((r.record_id, r.content_sha256) for r in requests),
        max_tasks=max_tasks, max_workers=max_workers)
    if not owned:
        return ResearchRotationReport('turn_already_reserved', stored, stop_requested=control.is_stopped())
    # Reservation is now committed. If interrupted here, a new turn (not replay
    # of this one) rotates onwards. The original claim still governs loop start.
    attempts = drain._drain_requests(dsn, requests, stored.turn.chosen,
                                     model_factory, max_workers, control)
    return ResearchRotationReport('dispatched', stored, attempts, control.is_stopped())
