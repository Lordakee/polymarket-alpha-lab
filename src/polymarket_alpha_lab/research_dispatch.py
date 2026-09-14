"""Immutable, bounded batches for explicit BTC/ETH research dispatch.

The batch is approved input, not a schedule that refreshes data or a model grant.
Canonical execution requests and receipts reuse the existing codecs unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from hashlib import sha256
import json

from polymarket_alpha_lab.research_execution import (
    CapturedResearchExecution, CapturedResearchRequest, copy_request, decode_execution_request,
)
from polymarket_alpha_lab.research_resolution import utc
from polymarket_alpha_lab.team_research_agent_types import hard_flags, identifier, strict_json

MAX_BATCH_REQUESTS = 100
MAX_BATCH_BYTES = 8 * 1024 * 1024
VERSION = 'research-dispatch-batch-v1'


def startable(request: CapturedResearchRequest, at: datetime) -> bool:
    """Selection hint only; the original claim transaction checks DB time again."""
    return (request.intake.as_of <= at < request.forecast_cutoff_at
            and (at - request.intake.as_of).total_seconds() <= request.max_start_delay_seconds)


@dataclass(frozen=True, slots=True)
class ResearchBatch:
    batch_id: str
    requests: tuple[CapturedResearchRequest, ...] = field(repr=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        identifier('batch_id', self.batch_id)
        hard_flags(self)
        if type(self.requests) is not tuple or not 1 <= len(self.requests) <= MAX_BATCH_REQUESTS:
            raise ValueError('research_batch_requests_invalid')
        requests = tuple(copy_request(item) for item in self.requests)
        if any(item.intake.team_id not in ('crypto_btc', 'crypto_eth') for item in requests):
            raise ValueError('research_batch_team_unsupported')
        identities = {(r.intake.team_id, r.model_id, r.protocol_version, r.intake.task_id) for r in requests}
        if len({r.record_id for r in requests}) != len(requests) or len(identities) != len(requests):
            raise ValueError('research_batch_duplicate_identity')
        object.__setattr__(self, 'requests', requests)
        if len(self.payload.encode('utf-8')) > MAX_BATCH_BYTES:
            raise ValueError('research_batch_too_large')

    @property
    def payload(self) -> str:
        # Strings retain each original canonical request exactly, not a parallel
        # request schema or a lossy deepcopy of datetime/timezone objects.
        return json.dumps(dict(schema_version=VERSION, batch_id=self.batch_id,
            requests=[r.payload for r in self.requests], paper_only=True, report_only=True, readonly=True),
            sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)

    @property
    def content_sha256(self) -> str:
        return sha256(self.payload.encode('utf-8')).hexdigest()


def copy_batch(batch: ResearchBatch) -> ResearchBatch:
    if type(batch) is not ResearchBatch:
        raise ValueError('research_batch_invalid')
    return replace(batch)


def decode_batch(payload: str, digest: str) -> ResearchBatch:
    try:
        if (type(payload) is not str or not 1 <= len(payload.encode('utf-8')) <= MAX_BATCH_BYTES
                or type(digest) is not str or sha256(payload.encode('utf-8')).hexdigest() != digest):
            raise ValueError
        data = strict_json(payload)
        if type(data) is not dict or data.pop('schema_version', None) != VERSION:
            raise ValueError
        bodies = data['requests']
        if type(bodies) is not list or not 1 <= len(bodies) <= MAX_BATCH_REQUESTS:
            raise ValueError
        if any(type(body) is not str for body in bodies):
            raise ValueError
        data['requests'] = tuple(decode_execution_request(body, sha256(body.encode('utf-8')).hexdigest())
                                 for body in bodies)
        batch = ResearchBatch(**data)
        if batch.payload != payload:
            raise ValueError
        return batch
    except Exception:
        raise ValueError('research_batch_payload_invalid') from None


@dataclass(frozen=True, slots=True)
class StoredResearchBatch:
    batch: ResearchBatch = field(repr=False)
    enqueued_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, 'batch', copy_batch(self.batch))
        object.__setattr__(self, 'enqueued_at', utc('enqueued_at', self.enqueued_at))
        if any(not startable(r, self.enqueued_at) for r in self.batch.requests):
            raise ValueError('research_batch_enqueue_time_invalid')


@dataclass(frozen=True, slots=True)
class ResearchBatchSnapshot:
    stored: StoredResearchBatch = field(repr=False)
    generated_at: datetime
    executions: tuple[CapturedResearchExecution | None, ...] = field(repr=False)

    def __post_init__(self) -> None:
        if type(self.stored) is not StoredResearchBatch:
            raise ValueError('research_batch_snapshot_invalid')
        object.__setattr__(self, 'stored', replace(self.stored))
        object.__setattr__(self, 'generated_at', utc('generated_at', self.generated_at))
        if self.generated_at < self.stored.enqueued_at:
            raise ValueError('research_batch_clock_regression')
        requests = self.stored.batch.requests
        if type(self.executions) is not tuple or len(self.executions) != len(requests):
            raise ValueError('research_batch_snapshot_incomplete')
        copied = []
        for request, execution in zip(requests, self.executions):
            if execution is None:
                copied.append(None)
                continue
            if type(execution) is not CapturedResearchExecution:
                raise ValueError('research_batch_execution_invalid')
            execution = replace(execution)
            if (execution.request.payload != request.payload
                    or execution.status not in ('already_captured', 'incomplete')
                    or execution.claimed_at > self.generated_at
                    or (execution.record is not None and execution.record.recorded_at > self.generated_at)):
                raise ValueError('research_batch_execution_mismatch')
            copied.append(execution)
        object.__setattr__(self, 'executions', tuple(copied))

    def states(self) -> tuple[str, ...]:
        self.__post_init__()
        return tuple(('captured' if e.record is not None else 'incomplete') if e is not None
                     else ('pending' if startable(r, self.generated_at) else 'expired')
                     for r, e in zip(self.stored.batch.requests, self.executions))

    def to_dict(self) -> dict:
        states = self.states()
        rows = []
        for position, (r, e, state) in enumerate(zip(self.stored.batch.requests, self.executions, states)):
            rows.append(dict(position=position, record_id=r.record_id, team_id=r.intake.team_id,
                request_sha256=r.content_sha256, state=state, forecast_cutoff_at=r.forecast_cutoff_at.isoformat(),
                execution=None if e is None else e.to_dict(),
                worker_liveness='unknown' if state == 'incomplete' else None))
        return dict(batch_id=self.stored.batch.batch_id, batch_sha256=self.stored.batch.content_sha256,
            enqueued_at=self.stored.enqueued_at.isoformat(), generated_at=self.generated_at.isoformat(),
            request_count=len(rows), state_counts={s: states.count(s) for s in ('pending','expired','incomplete','captured')},
            items=rows, automatic_reclaim_permitted=False, model_called=False, database_written=False,
            paper_only=True, report_only=True, readonly=True)


__all__ = ('ResearchBatch', 'StoredResearchBatch', 'ResearchBatchSnapshot')
