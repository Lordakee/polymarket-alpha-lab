"""Node 7 BTC forecast orchestration service (paper-only, report-only, readonly).

Evaluates the Node 6 BTC evidence policy, reduces the projected canonical
records through the Node 2C aggregation reducer under the evaluation's own
pinned configuration, composes the service-level publication gate -- blocked
when either the policy or aggregation status is blocked, watch when neither
is blocked and either is watch, ready only when both are ready -- with the
sorted duplicate-free union of the predecessor reason codes, builds and
validates the Node 3 envelope, and persists exactly one envelope through
Node 5's sole atomic local Supabase/Postgres writer. Packets are projected
from the caller's legacy templates only when both gates are ready; every
other combination builds a packetless envelope through the Node 3 external
policy publication gate carrying the exact policy status and reason codes.

The module is orchestration only: no SQL, no psycopg connection logic, no
environment reads, no loaders, no latest-attempt selection, no
strategy-cycle wiring, and no side selection. All durable attempts go
through the injected or default Node 5 writer with the caller's Node 4
configuration. Phase 1: paper-only, report-only, readonly; no live trading,
authentication, credential, wallet, signing, order, execution, exchange
mutation, or account access.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Final, final

from polymarket_alpha_lab.crypto_btc_evidence_policy import (
    CryptoBtcEvidenceEvaluation,
    CryptoBtcEvidenceInput,
    evaluate_crypto_btc_evidence,
)
from polymarket_alpha_lab.crypto_btc_evidence_resolution import (
    CryptoBtcIncidentGates,
    CryptoBtcResolutionContract,
)
from polymarket_alpha_lab.supabase_team_evidence_aggregation_config import (
    SupabaseTeamEvidenceAggregationConfig,
)
from polymarket_alpha_lab.team_evidence_aggregation import (
    build_team_evidence_aggregation_result,
    validate_team_evidence_aggregation_result,
)
from polymarket_alpha_lab.team_evidence_aggregation_attempt_psycopg import (
    insert_team_evaluation_attempts_with_psycopg,
)
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationInput,
    TeamEvidenceAggregationResult,
)
from polymarket_alpha_lab.team_forecast_build_envelope import (
    TeamForecastBuildEnvelope,
    TeamForecastEvaluationScope,
    TeamForecastEvaluatorReceipt,
    TeamForecastPolicyPublicationGate,
    TeamForecastRunMetadata,
    build_team_forecast_build_envelope,
    validate_team_forecast_build_envelope,
)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
)

__all__ = (
    "CryptoBtcForecastServiceInput",
    "CryptoBtcForecastServiceResult",
    "evaluate_and_persist_crypto_btc_forecast",
)

PUBLICATION_STATUSES: Final = ("blocked", "ready", "watch")
HARD_FLAG_NAMES: Final = ("paper_only", "report_only", "readonly")
_PUBLIC_CLASS_NAMES: Final = (
    "CryptoBtcForecastServiceInput",
    "CryptoBtcForecastServiceResult",
)


class _SealedServiceDataclass:
    """Reject every subclass of the public service dataclasses."""

    __slots__ = ()

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if (
            cls.__bases__ != (_SealedServiceDataclass,)
            or cls.__name__ not in _PUBLIC_CLASS_NAMES
        ):
            raise TypeError(
                "public crypto BTC forecast service dataclasses do not "
                "support subclassing"
            )


def _hard_flags(path: str, value: object) -> None:
    for flag_name in HARD_FLAG_NAMES:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{path}.{flag_name} must be exact True")
    return None


def _canonical_string(path: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{path} must be a canonical nonblank string")
    return value


def _aware_datetime(path: str, value: object) -> datetime:
    if (
        type(value) is not datetime
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(f"{path} must be an exact aware datetime")
    return value


def _combined_publication_status(
    policy_status: str,
    aggregation_status: str,
) -> str:
    """blocked over watch over ready across the two predecessor statuses."""
    if policy_status == "blocked" or aggregation_status == "blocked":
        return "blocked"
    if policy_status == "watch" or aggregation_status == "watch":
        return "watch"
    return "ready"


def _composed_reason_codes(
    policy_reason_codes: tuple[str, ...],
    aggregation_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    """Sorted duplicate-free union of the predecessor reason codes."""
    merged = set(policy_reason_codes) | set(aggregation_reason_codes)
    return tuple(sorted(merged))


def _validate_input_contract(
    service_input: CryptoBtcForecastServiceInput,
) -> None:
    """Validate every input field exactly once, before any activity."""
    if type(service_input) is not CryptoBtcForecastServiceInput:
        raise ValueError(
            "service_input must be exactly CryptoBtcForecastServiceInput"
        )
    _canonical_string("condition_id", service_input.condition_id)
    _canonical_string("market_slug", service_input.market_slug)
    _canonical_string("event_template", service_input.event_template)
    resolution_contract = service_input.resolution_contract
    if type(resolution_contract) is not CryptoBtcResolutionContract:
        raise ValueError(
            "resolution_contract must be exactly CryptoBtcResolutionContract"
        )
    _hard_flags("resolution_contract", resolution_contract)
    incident_gates = service_input.incident_gates
    if type(incident_gates) is not CryptoBtcIncidentGates:
        raise ValueError("incident_gates must be exactly CryptoBtcIncidentGates")
    _hard_flags("incident_gates", incident_gates)
    evidence_inputs = service_input.evidence_inputs
    if type(evidence_inputs) is not tuple:
        raise ValueError("evidence_inputs must be an exact tuple")
    for index, evidence_input in enumerate(evidence_inputs):
        if type(evidence_input) is not CryptoBtcEvidenceInput:
            raise ValueError(
                f"evidence_inputs[{index}] must be exactly CryptoBtcEvidenceInput"
            )
        _hard_flags(f"evidence_inputs[{index}]", evidence_input)
    _aware_datetime("evaluated_at", service_input.evaluated_at)
    scope = service_input.scope
    if type(scope) is not TeamForecastEvaluationScope:
        raise ValueError("scope must be exactly TeamForecastEvaluationScope")
    _hard_flags("scope", scope)
    run_metadata = service_input.run_metadata
    if type(run_metadata) is not TeamForecastRunMetadata:
        raise ValueError("run_metadata must be exactly TeamForecastRunMetadata")
    _hard_flags("run_metadata", run_metadata)
    evaluator_receipts = service_input.evaluator_receipts
    if type(evaluator_receipts) is not tuple:
        raise ValueError("evaluator_receipts must be an exact tuple")
    for index, receipt in enumerate(evaluator_receipts):
        if type(receipt) is not TeamForecastEvaluatorReceipt:
            raise ValueError(
                f"evaluator_receipts[{index}] must be exactly "
                "TeamForecastEvaluatorReceipt"
            )
        _hard_flags(f"evaluator_receipts[{index}]", receipt)
    legacy_forecast_packet = service_input.legacy_forecast_packet
    if legacy_forecast_packet is not None:
        if type(legacy_forecast_packet) is not TeamForecastPacket:
            raise ValueError(
                "legacy_forecast_packet must be exactly TeamForecastPacket"
            )
        _hard_flags("legacy_forecast_packet", legacy_forecast_packet)
    legacy_evidence_packets = service_input.legacy_evidence_packets
    if type(legacy_evidence_packets) is not tuple:
        raise ValueError("legacy_evidence_packets must be an exact tuple")
    for index, evidence_packet in enumerate(legacy_evidence_packets):
        if type(evidence_packet) is not TeamForecastEvidencePacket:
            raise ValueError(
                f"legacy_evidence_packets[{index}] must be exactly "
                "TeamForecastEvidencePacket"
            )
        _hard_flags(f"legacy_evidence_packets[{index}]", evidence_packet)
    persistence_config = service_input.persistence_config
    if type(persistence_config) is not SupabaseTeamEvidenceAggregationConfig:
        raise ValueError(
            "persistence_config must be exactly "
            "SupabaseTeamEvidenceAggregationConfig"
        )
    if persistence_config.enabled is not True:
        raise ValueError(
            "persistence_config.enabled must be exact True to persist the "
            "paper attempt"
        )
    if type(persistence_config.dsn) is not str or not persistence_config.dsn:
        raise ValueError(
            "persistence_config.dsn must be a nonempty local Postgres DSN"
        )
    _hard_flags("service_input", service_input)
    return None


@final
@dataclass(frozen=True, slots=True)
class CryptoBtcForecastServiceInput(_SealedServiceDataclass):
    """Fully validated caller request for one BTC forecast service run."""

    condition_id: str
    market_slug: str
    event_template: str
    resolution_contract: CryptoBtcResolutionContract
    incident_gates: CryptoBtcIncidentGates
    evidence_inputs: tuple[CryptoBtcEvidenceInput, ...]
    evaluated_at: datetime
    scope: TeamForecastEvaluationScope
    run_metadata: TeamForecastRunMetadata
    evaluator_receipts: tuple[TeamForecastEvaluatorReceipt, ...]
    legacy_forecast_packet: TeamForecastPacket | None
    legacy_evidence_packets: tuple[TeamForecastEvidencePacket, ...]
    persistence_config: SupabaseTeamEvidenceAggregationConfig
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CryptoBtcForecastServiceInput:
            raise ValueError(
                "crypto_btc_forecast_service_input must be exactly "
                "CryptoBtcForecastServiceInput"
            )
        _validate_input_contract(self)


@final
@dataclass(frozen=True, slots=True)
class CryptoBtcForecastServiceResult(_SealedServiceDataclass):
    """One completed paper-only forecast evaluation and persistence attempt."""

    policy_evaluation: CryptoBtcEvidenceEvaluation
    aggregation_result: TeamEvidenceAggregationResult
    publication_status: str
    reason_codes: tuple[str, ...]
    envelope: TeamForecastBuildEnvelope
    write_results: tuple[object, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CryptoBtcForecastServiceResult:
            raise ValueError(
                "crypto_btc_forecast_service_result must be exactly "
                "CryptoBtcForecastServiceResult"
            )
        policy_evaluation = self.policy_evaluation
        if type(policy_evaluation) is not CryptoBtcEvidenceEvaluation:
            raise ValueError(
                "policy_evaluation must be exactly CryptoBtcEvidenceEvaluation"
            )
        _hard_flags("policy_evaluation", policy_evaluation)
        aggregation_result = self.aggregation_result
        if type(aggregation_result) is not TeamEvidenceAggregationResult:
            raise ValueError(
                "aggregation_result must be exactly TeamEvidenceAggregationResult"
            )
        _hard_flags("aggregation_result", aggregation_result)
        publication_status = self.publication_status
        if (
            type(publication_status) is not str
            or publication_status not in PUBLICATION_STATUSES
        ):
            raise ValueError(
                "publication_status must be one of the closed publication "
                "statuses"
            )
        if publication_status != _combined_publication_status(
            policy_evaluation.status, aggregation_result.status
        ):
            raise ValueError(
                "publication_status must follow the combined precedence"
            )
        reason_codes = self.reason_codes
        if type(reason_codes) is not tuple:
            raise ValueError("reason_codes must be an exact tuple")
        for code in reason_codes:
            if type(code) is not str or not code:
                raise ValueError(
                    "reason_codes must be nonempty canonical strings"
                )
        if reason_codes != _composed_reason_codes(
            policy_evaluation.reason_codes, aggregation_result.reason_codes
        ):
            raise ValueError(
                "reason_codes must equal the sorted duplicate-free union of "
                "the predecessor reason codes"
            )
        envelope = self.envelope
        if type(envelope) is not TeamForecastBuildEnvelope:
            raise ValueError(
                "envelope must be exactly TeamForecastBuildEnvelope"
            )
        _hard_flags("envelope", envelope)
        write_results = self.write_results
        if type(write_results) is not tuple or len(write_results) != 1:
            raise ValueError("write_results must hold exactly one write result")
        _hard_flags("crypto_btc_forecast_service_result", self)


def evaluate_and_persist_crypto_btc_forecast(
    service_input: CryptoBtcForecastServiceInput,
    *,
    evaluator: Callable[..., CryptoBtcEvidenceEvaluation] | None = None,
    writer: Callable[..., tuple[object, ...]] | None = None,
) -> CryptoBtcForecastServiceResult:
    """Run one paper-only BTC forecast evaluation and persistence attempt.

    Every input field is validated exactly once before any evaluator or
    writer activity; invalid input, a disabled Node 4 configuration, a
    missing DSN, malformed evaluator output, an unvalidated aggregation, an
    unvalidated envelope, or a writer that does not return exactly one
    write result fails closed. The default bindings are the Node 6 policy
    evaluator and Node 5's sole atomic local Supabase/Postgres writer;
    injection exists only for deterministic tests and never creates an
    alternate production persistence path.
    """
    _validate_input_contract(service_input)
    bound_evaluator = (
        evaluate_crypto_btc_evidence if evaluator is None else evaluator
    )
    bound_writer = (
        insert_team_evaluation_attempts_with_psycopg if writer is None else writer
    )
    if not callable(bound_evaluator):
        raise ValueError("evaluator must be callable")
    if not callable(bound_writer):
        raise ValueError("writer must be callable")
    evaluation = bound_evaluator(
        condition_id=service_input.condition_id,
        market_slug=service_input.market_slug,
        event_template=service_input.event_template,
        resolution_contract=service_input.resolution_contract,
        incident_gates=service_input.incident_gates,
        evidence_inputs=service_input.evidence_inputs,
        evaluated_at=service_input.evaluated_at,
    )
    if type(evaluation) is not CryptoBtcEvidenceEvaluation:
        raise ValueError(
            "the evaluator must return exactly CryptoBtcEvidenceEvaluation"
        )
    _hard_flags("policy_evaluation", evaluation)
    aggregation_input = TeamEvidenceAggregationInput(
        evaluated_at=evaluation.evaluated_at,
        records=evaluation.records,
        current_revisions=evaluation.current_selections,
    )
    aggregation_result = build_team_evidence_aggregation_result(
        aggregation_input,
        config=evaluation.config,
    )
    validate_team_evidence_aggregation_result(
        aggregation_result,
        aggregation_input=aggregation_input,
        config=evaluation.config,
    )
    publication_status = _combined_publication_status(
        evaluation.status,
        aggregation_result.status,
    )
    reason_codes = _composed_reason_codes(
        evaluation.reason_codes,
        aggregation_result.reason_codes,
    )
    policy_publication_gate: TeamForecastPolicyPublicationGate | None = None
    legacy_forecast_packet: TeamForecastPacket | None = (
        service_input.legacy_forecast_packet
    )
    legacy_evidence_packets: tuple[TeamForecastEvidencePacket, ...] = (
        service_input.legacy_evidence_packets
    )
    if publication_status != "ready":
        policy_publication_gate = TeamForecastPolicyPublicationGate(
            status=evaluation.status,
            reason_codes=evaluation.reason_codes,
        )
        legacy_forecast_packet = None
        legacy_evidence_packets = ()
    envelope = build_team_forecast_build_envelope(
        aggregation_result,
        aggregation_input=aggregation_input,
        config=evaluation.config,
        scope=service_input.scope,
        run_metadata=service_input.run_metadata,
        evaluator_receipts=service_input.evaluator_receipts,
        legacy_forecast_packet=legacy_forecast_packet,
        legacy_evidence_packets=legacy_evidence_packets,
        policy_publication_gate=policy_publication_gate,
    )
    validate_team_forecast_build_envelope(
        envelope,
        result=aggregation_result,
        aggregation_input=aggregation_input,
        config=evaluation.config,
        scope=service_input.scope,
        run_metadata=service_input.run_metadata,
        evaluator_receipts=service_input.evaluator_receipts,
        legacy_forecast_packet=legacy_forecast_packet,
        legacy_evidence_packets=legacy_evidence_packets,
        policy_publication_gate=policy_publication_gate,
    )
    write_results = bound_writer(
        service_input.persistence_config.dsn,
        (envelope,),
        table_name=service_input.persistence_config.table_name,
    )
    if type(write_results) is not tuple or len(write_results) != 1:
        raise ValueError("the writer must return exactly one write result")
    return CryptoBtcForecastServiceResult(
        policy_evaluation=evaluation,
        aggregation_result=aggregation_result,
        publication_status=publication_status,
        reason_codes=reason_codes,
        envelope=envelope,
        write_results=write_results,
    )
