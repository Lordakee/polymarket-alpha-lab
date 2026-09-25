"""Typed reviewed assembly of exactly one audited uncapped Claude rotation.

This module is inert wiring over existing reviewed components. Importing or
constructing it performs no activation: no session is opened, no credential
store is read, no supplier is invoked, and no process is started. The caller
owns the already-open project-private research session, two reviewed immutable
single-request BTC/ETH batches, a reviewed Claude profile, and the existing
typed uncapped authorization. Freshness, claims, turn replay, audit commits,
and capture semantics remain governed by the existing stores and runners.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from polymarket_alpha_lab.research_claude_profile import (
    ClaudeExecProfile,
    claude_profile_factory,
)
from polymarket_alpha_lab.research_dispatch import (
    ResearchBatch,
    StoredResearchBatch,
    copy_batch,
)
from polymarket_alpha_lab.research_dispatch_rotation_runner import (
    ResearchRotationReport,
)
from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
from polymarket_alpha_lab.research_uncapped import (
    UncappedResearchAuthorization,
    copy_authorization,
)
from polymarket_alpha_lab.research_uncapped_audit import (
    StoredUncappedAuthorization,
)
from polymarket_alpha_lab.team_research_agent_types import identifier, integer

if TYPE_CHECKING:
    from polymarket_alpha_lab.project_postgres.research import (
        ProjectResearchSession,
    )


ApiKeySupplier = Callable[[], str]

_ASSEMBLY_TEAMS = ('crypto_btc', 'crypto_eth')


@dataclass(frozen=True, slots=True)
class ClaudeResearchAuditHandle:
    team_id: str
    batch_id: str
    batch_sha256: str
    record_id: str
    request_sha256: str


@dataclass(frozen=True, slots=True)
class ClaudeResearchOperatorResult:
    report: ResearchRotationReport = field(repr=False)
    authorization_receipt: StoredUncappedAuthorization = field(repr=False)
    rotation_id: str
    turn_id: str
    audit_handles: tuple[ClaudeResearchAuditHandle, ...]


def _canonical_reviewed_inputs(reviewed_batches, profile, authorization,
                               api_key_supplier, rotation_id, turn_id, stop,
                               max_tasks, max_workers):
    """Pure structural validation; no session, clock, process, or key use."""
    if type(reviewed_batches) is not tuple or len(reviewed_batches) != 2:
        raise ValueError('research_claude_operator_batches_invalid')
    # Canonical snapshots reuse the existing validated codecs unchanged, so
    # altered typed inputs, hard flags, and foreign objects fail closed here.
    permission = copy_authorization(authorization)
    if type(profile) is not ClaudeExecProfile:
        raise ValueError('research_claude_operator_inputs_invalid')
    candidate = replace(profile)
    batches = tuple(copy_batch(batch) for batch in reviewed_batches)
    if (batches[0].batch_id == batches[1].batch_id
            or any(len(batch.requests) != 1 for batch in batches)):
        raise ValueError('research_claude_operator_batches_invalid')
    requests = (batches[0].requests[0], batches[1].requests[0])
    for request, team in zip(requests, _ASSEMBLY_TEAMS):
        if (request.intake.team_id != team or request.intake.status != 'prepared'
                or request.model_id != candidate.model_id):
            raise ValueError('research_claude_operator_batches_invalid')
    if (len({request.record_id for request in requests}) != 2
            or len({(r.intake.team_id, r.model_id, r.protocol_version, r.intake.task_id)
                    for r in requests}) != 2):
        raise ValueError('research_claude_operator_batches_invalid')
    # The authorization must bind the entire reviewed roster in reviewed order
    # and the exact reviewed profile; omitted, altered, reordered, additional,
    # or differently-modelled keys are all refused before any session I/O.
    if (permission.request_keys != tuple((r.record_id, r.content_sha256) for r in requests)
            or permission.model_id != candidate.model_id
            or permission.adapter_contract_sha256 != candidate.contract_sha256):
        raise ValueError('research_claude_operator_authorization_binding_invalid')
    identifier('rotation_id', rotation_id)
    identifier('turn_id', turn_id)
    if not callable(api_key_supplier):
        raise ValueError('research_claude_operator_supplier_invalid')
    if type(stop) is not ResearchDispatchStop:
        raise ValueError('research_claude_operator_stop_invalid')
    # Non-boolean integers in 1..2 only; only 2/2 is the reviewed first-run
    # configuration, an explicit 1 stays visible to the existing runner.
    integer('max_tasks', max_tasks, 1, 2)
    integer('max_workers', max_workers, 1, 2)
    return permission, batches, requests, candidate


def run_claude_research_rotation(
    research: ProjectResearchSession,
    *,
    reviewed_batches: tuple[ResearchBatch, ResearchBatch],
    profile: ClaudeExecProfile,
    authorization: UncappedResearchAuthorization,
    api_key_supplier: ApiKeySupplier,
    rotation_id: str,
    turn_id: str,
    stop: ResearchDispatchStop,
    max_tasks: int = 2,
    max_workers: int = 2,
) -> ClaudeResearchOperatorResult:
    """Assemble and invoke exactly one audited uncapped Claude rotation.

    The caller owns an already-open project-private research session and
    supplies reviewed immutable BTC/ETH requests, a reviewed Claude profile,
    and the existing typed authorization containing the approved ID and fields.

    The supplier is an explicitly approved synchronous, finite, nonblocking,
    in-memory callable, safe for the selected concurrency. This function
    checks callability and forwards it without invoking it.

    Construction/import performs no activation. Invoking this function with
    a real session is side-effecting and requires the separately approved
    real-run prerequisites.

    Freshness, claims, turn replay, audit commits, and capture semantics
    remain governed by the existing stores and runners. Assembly is not one
    transaction; a later failure can leave earlier operations committed.

    Stop is cooperative. Preserve original IDs and inspect durable state
    after failure or interruption; never retry or replace identities here.

    Return the exact runner report object, preserving any pending_run.
    Audit handles are lookup references, not reconciled provenance.
    """
    permission, batches, requests, candidate = _canonical_reviewed_inputs(
        reviewed_batches, profile, authorization, api_key_supplier,
        rotation_id, turn_id, stop, max_tasks, max_workers)
    # Checkpoint (entry): a token already stopped at entry never reaches the
    # session, the builder, the supplier, or a process.
    if stop.is_stopped():
        raise ValueError('research_claude_operator_stopped')
    saved = research.create_uncapped_authorization(
        authorization=permission,
        allow_authorization_write=True,
    )
    # Keep a successful creation paired with read-only receipt inspection even
    # when stop was observed during the write; stop gates the next admission.
    stored = research.inspect_uncapped_authorization(
        authorization_id=permission.authorization_id,
    )
    if (type(saved) is not StoredUncappedAuthorization
            or type(stored) is not StoredUncappedAuthorization
            or stored != saved
            or stored.authorization.payload != permission.payload):
        raise ValueError('authorization_receipt_mismatch')
    # Checkpoint: after the paired create/inspect receipt validation.
    if stop.is_stopped():
        raise ValueError('research_claude_operator_stopped')
    for batch in batches:
        # Checkpoint: immediately before each enqueue admission.
        if stop.is_stopped():
            raise ValueError('research_claude_operator_stopped')
        queued = research.enqueue_research_batch(
            batch=batch,
            allow_queue_write=True,
        )
        if (type(queued) is not StoredResearchBatch
                or queued.batch.payload != batch.payload):
            raise ValueError('research_claude_operator_batch_receipt_mismatch')
    bound_authorization = stored.authorization
    # Checkpoint: before factory construction.
    if stop.is_stopped():
        raise ValueError('research_claude_operator_stopped')
    model_factory = claude_profile_factory(
        profile=candidate,
        authorization=bound_authorization,
        api_key_supplier=api_key_supplier,
        allow_process_start=True,
        allow_api_key_use=True,
        stop=stop,
    )
    # Checkpoint: before rotation invocation.
    if stop.is_stopped():
        raise ValueError('research_claude_operator_stopped')
    report = research.run_research_rotation(
        rotation_id=rotation_id,
        turn_id=turn_id,
        batch_ids_to_run=(batches[0].batch_id, batches[1].batch_id),
        model_factory=model_factory,
        allow_model_calls=True,
        max_tasks=max_tasks,
        max_workers=max_workers,
        stop=stop,
        uncapped_authorization=bound_authorization,
        allow_uncapped_costs=True,
        require_durable_audit=True,
    )
    handles = tuple(
        ClaudeResearchAuditHandle(
            team_id=request.intake.team_id,
            batch_id=batch.batch_id,
            batch_sha256=batch.content_sha256,
            record_id=request.record_id,
            request_sha256=request.content_sha256,
        )
        for batch, request in zip(batches, requests)
    )
    return ClaudeResearchOperatorResult(
        report=report,
        authorization_receipt=stored,
        rotation_id=rotation_id,
        turn_id=turn_id,
        audit_handles=handles,
    )
