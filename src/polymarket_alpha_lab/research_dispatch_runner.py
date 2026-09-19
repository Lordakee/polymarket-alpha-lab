"""Explicit bounded drain of one durable batch; no daemon or model selection.

Stop is cooperative at admission, never a thread/process kill. Already admitted
operations finish; lost results remain incomplete. Callers must bound model I/O.
"""
from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextvars import copy_context
from dataclasses import dataclass, field, replace
from threading import Lock

from polymarket_alpha_lab.research_dispatch import ResearchBatchSnapshot
from polymarket_alpha_lab.research_dispatch_store import load_research_batch_with_psycopg
from polymarket_alpha_lab.research_execution import CapturedResearchExecution
from polymarket_alpha_lab.research_execution_psycopg import run_captured_research_with_psycopg
from polymarket_alpha_lab.team_research_agent_types import identifier, integer


class ResearchDispatchStop:
    """One-way stop for one or more explicitly associated dispatch invocations.

    request_stop returning prevents subsequent admissions. An operation admitted
    before it may still enter its claim/model call afterward. No persistent cancel.
    """
    __slots__ = ('_lock', '_stopped')

    def __init__(self):
        self._lock = Lock()
        self._stopped = False

    def request_stop(self) -> None:
        with self._lock:
            self._stopped = True

    def is_stopped(self) -> bool:
        with self._lock:
            return self._stopped

    def _admit(self) -> bool:
        with self._lock:
            return not self._stopped


@dataclass(frozen=True, slots=True)
class DispatchAttempt:
    position: int
    status: str
    execution: CapturedResearchExecution | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        integer('position', self.position, 0, 99)
        if type(self.status) is not str or self.status not in ('returned', 'operation_failed', 'stopped_before_start'):
            raise ValueError('research_dispatch_status_invalid')
        if self.status == 'returned':
            if type(self.execution) is not CapturedResearchExecution:
                raise ValueError('research_dispatch_execution_missing')
            object.__setattr__(self, 'execution', replace(self.execution))
        elif self.execution is not None:
            raise ValueError('research_dispatch_unexpected_execution')


@dataclass(frozen=True, slots=True)
class ResearchDispatchReport:
    snapshot: ResearchBatchSnapshot = field(repr=False)
    attempts: tuple[DispatchAttempt, ...] = field(repr=False)
    max_tasks: int
    max_workers: int
    stop_requested: bool

    def __post_init__(self) -> None:
        integer('max_tasks', self.max_tasks, 1, 100)
        integer('max_workers', self.max_workers, 1, 8)
        if (type(self.snapshot) is not ResearchBatchSnapshot or type(self.attempts) is not tuple
                or type(self.stop_requested) is not bool or any(type(a) is not DispatchAttempt for a in self.attempts)):
            raise ValueError('research_dispatch_report_invalid')
        snapshot = replace(self.snapshot)
        attempts = tuple(replace(a) for a in self.attempts)
        positions = [a.position for a in attempts]
        pending = [i for i, state in enumerate(snapshot.states()) if state == 'pending']
        if len(positions) > self.max_tasks or positions != pending[:len(positions)]:
            raise ValueError('research_dispatch_report_scope_invalid')
        if not self.stop_requested and len(positions) != min(len(pending), self.max_tasks):
            raise ValueError('research_dispatch_report_incomplete')
        for attempt in attempts:
            if (attempt.execution is not None and attempt.execution.request.payload !=
                    snapshot.stored.batch.requests[attempt.position].payload):
                raise ValueError('research_dispatch_execution_mismatch')
            if attempt.status == 'stopped_before_start' and not self.stop_requested:
                raise ValueError('research_dispatch_stop_mismatch')
        object.__setattr__(self, 'snapshot', snapshot)
        object.__setattr__(self, 'attempts', attempts)

    def to_dict(self) -> dict:
        self.__post_init__()
        requests = self.snapshot.stored.batch.requests
        rows = [dict(position=a.position, record_id=requests[a.position].record_id, status=a.status,
                     execution=None if a.execution is None else a.execution.to_dict()) for a in self.attempts]
        started = sum(a.status != 'stopped_before_start' for a in self.attempts)
        return dict(batch_id=self.snapshot.stored.batch.batch_id,
            batch_sha256=self.snapshot.stored.batch.content_sha256,
            selected_at=self.snapshot.generated_at.isoformat(), max_tasks=self.max_tasks,
            max_workers=self.max_workers, stop_requested=self.stop_requested,
            pending_at_selection=self.snapshot.states().count('pending'), execution_invocations=started,
            not_invoked_pending_count=self.snapshot.states().count('pending') - started,
            operation_failure_count=sum(a.status == 'operation_failed' for a in self.attempts),
            attempts=rows, final_database_state_checked=False, automatic_reclaim_permitted=False,
            market_fetch_performed=False, model_calls_possible=started > 0,
            hard_money_cap_enforced=False, paper_only=True, report_only=True, readonly=True)


def run_research_batch_with_psycopg(dsn: str, *, batch_id: str, model_factory,
                                  allow_model_calls: bool = False, max_tasks: int = 10,
                                  max_workers: int = 2, stop: ResearchDispatchStop | None = None,
                                  model_budget_id: str | None = None, uncapped_authorization=None,
                                  allow_uncapped_costs=False) -> ResearchDispatchReport:
    """Run a bounded pending prefix; later explicit rounds skip existing claims.

    All batch inputs are persisted BEFORE this operation. Snapshot/transactions
    finish before worker execution. Each worker inherits the managed instance
    binding in a distinct Context; existing per-request claims govern duplicate
    dispatchers. Limits are per invocation, NOT fleet/provider monetary budgets.

    FIFO submission (not guaranteed wall-clock start order); simultaneously admitted same-cohort jobs can be refused by
    the original prior-incomplete guard, never bypassed. An operation failure may
    be an uncertain commit: inspect the durable batch before any next round.
    capture_failed retains pending_run in the returned execution for the existing
    explicit capture-only recovery API. No automatic model or capture retries.
    """
    from polymarket_alpha_lab.research_uncapped_runner import validate_uncapped_choice
    uncapped_authorization = validate_uncapped_choice(uncapped_authorization, allow_uncapped_costs, model_budget_id)
    identifier('batch_id', batch_id)
    if model_budget_id is not None:
        identifier('model_budget_id', model_budget_id)
    integer('max_tasks', max_tasks, 1, 100)
    integer('max_workers', max_workers, 1, 8)
    if allow_model_calls is not True or not callable(model_factory):
        raise ValueError('research_dispatch_model_opt_in_required')
    if stop is not None and type(stop) is not ResearchDispatchStop:
        raise ValueError('research_dispatch_stop_invalid')
    stop = stop if stop is not None else ResearchDispatchStop()
    snapshot = load_research_batch_with_psycopg(dsn, batch_id=batch_id)
    if snapshot is None:
        raise ValueError('research_dispatch_batch_not_found')
    if type(snapshot) is not ResearchBatchSnapshot or snapshot.stored.batch.batch_id != batch_id:
        raise ValueError('research_dispatch_snapshot_invalid')
    snapshot = replace(snapshot)
    pending = [i for i, state in enumerate(snapshot.states()) if state == 'pending'][:max_tasks]
    options = {}
    if uncapped_authorization is not None:
        for position in pending:
            uncapped_authorization.bind_request(snapshot.stored.batch.requests[position])
        options = dict(uncapped_authorization=uncapped_authorization)
    attempts = _drain_requests(dsn, snapshot.stored.batch.requests, pending,
                               model_factory, max_workers, stop, model_budget_id=model_budget_id, **options)
    return ResearchDispatchReport(snapshot, attempts, max_tasks, max_workers, stop.is_stopped())


def _drain_requests(dsn, requests, pending, model_factory, max_workers, stop, *, model_budget_id=None,
                    uncapped_authorization=None):
    """Shared bounded execution mechanics; callers supply a validated selection.

    Preserve selection order, including a cyclic order chosen by durable rotation.
    The original per-request claim remains the only authority to start a loop.
    """
    if model_budget_id is not None and uncapped_authorization is not None:
        raise ValueError('research_uncapped_mode_conflict_or_not_approved')
    results = {}

    def invoke(position):
        if not stop._admit():
            return DispatchAttempt(position, 'stopped_before_start')
        request = requests[position]
        try:
            if uncapped_authorization is not None:
                from polymarket_alpha_lab.research_uncapped_runner import run_uncapped_research_with_psycopg
                receipt = run_uncapped_research_with_psycopg(dsn, request=request,
                    authorization=uncapped_authorization, model_factory=model_factory,
                    allow_model_calls=True, allow_uncapped_costs=True, stop=stop)
            elif model_budget_id is None:
                receipt = run_captured_research_with_psycopg(dsn, request=request, model_factory=model_factory)
            else:
                from polymarket_alpha_lab.research_model_budget_runner import run_budgeted_research_with_psycopg
                receipt = run_budgeted_research_with_psycopg(dsn, request=request, model_factory=model_factory,
                    budget_id=model_budget_id, allow_model_calls=True)
            if type(receipt) is not CapturedResearchExecution or receipt.request.payload != request.payload:
                raise ValueError('unexpected receipt')
            return DispatchAttempt(position, 'returned', receipt)
        except Exception:
            # Never expose DSN/provider/SQL text or turn an uncertain failure into
            # a newly runnable job. Next invocation must reload real claim state.
            return DispatchAttempt(position, 'operation_failed')

    if pending and not stop.is_stopped():
        # At most max_workers futures exist; no hidden executor backlog of the
        # rest of the durable batch. Submit in FIFO order, return input order.
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            running, next_position = {}, 0
            try:
                while running or next_position < len(pending):
                    while (not stop.is_stopped() and next_position < len(pending)
                           and len(running) < max_workers):
                        position = pending[next_position]
                        future = pool.submit(copy_context().run, invoke, position)
                        running[future] = position
                        next_position += 1
                    if not running:
                        break
                    done, _ = wait(running, return_when=FIRST_COMPLETED)
                    for future in done:
                        position = running.pop(future)
                        results[position] = future.result()
            except BaseException:
                stop.request_stop()
                # Context manager drains admitted workers before propagation.
                # No force-kill or assumption that a quiet provider has died.
                raise
    return tuple(results[i] for i in pending if i in results)


__all__ = ('ResearchDispatchStop', 'ResearchDispatchReport', 'run_research_batch_with_psycopg')
