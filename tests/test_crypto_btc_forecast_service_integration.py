"""Fake-writer integration tests for the Node 7 crypto BTC forecast service.

Governing plan: docs/superpowers/plans/2026-07-13-crypto-btc-forecast-service.md
Scope: integration coverage that exercises the FULL REAL predecessor chain with
only the Node 5 writer faked (the evaluator stays real). Every scenario builds
real Node 6 inputs from the trusted crypto BTC registry/catalog/resolution
surfaces (fixture idioms mirrored from tests/test_crypto_btc_evidence_policy.py,
never imported from it), runs the real ``evaluate_crypto_btc_evidence``, then
calls ``evaluate_and_persist_crypto_btc_forecast`` with a recording fake
writer, and asserts the recorded call payload is a real
``TeamForecastBuildEnvelope`` produced by the real Node 2 aggregation and the
real Node 3 envelope builder including the external policy publication gate
amendment path. Persistability is proven offline: the recorded envelope's
``evaluation_scope_payload`` must pass Node 4's real
``team_evaluation_attempt_to_db_row`` plus
``team_evaluation_attempt_row_parameters`` conversion, and must satisfy Node
5's public orphan run-binding identities, without any database, disposable DB,
network, or filesystem persistence.

The production module ``src/polymarket_alpha_lab/crypto_btc_forecast_service.py``
is implemented by a parallel worker against the plan's pinned interface; until
it exists, collection fails with an ImportError, which is the expected red
state.

Covered matrix (plan packet/persistence table, post-amendment):
- policy ready + aggregation ready -> packeted envelope with tfr:v1/tfe:v1
  projections, writer called exactly once;
- policy watch + aggregation ready -> packetless gated envelope that still
  converts to a row, writer called exactly once (the amendment path);
- policy blocked (unapproved source) + aggregation blocked -> packetless
  envelope, writer called exactly once;
- invalid service input (disabled persistence, ghost receipt, packet-count
  mismatch) -> ValueError with the fake writer never touched;
- combined publication status precedence and the sorted duplicate-free reason
  union across all three scenarios;
- determinism: identical inputs through two fresh fakes reproduce identical
  domain-separated envelope identifiers.
"""
from __future__ import annotations

import inspect
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from typing import NamedTuple

import pytest

from polymarket_alpha_lab.crypto_btc_evidence_catalog import (
    trusted_crypto_btc_source_catalog,
)
from polymarket_alpha_lab.crypto_btc_evidence_policy import (
    CryptoBtcEvidenceEvaluation,
    CryptoBtcEvidenceInput,
    evaluate_crypto_btc_evidence,
)
from polymarket_alpha_lab.crypto_btc_evidence_resolution import (
    CRYPTO_BTC_RESOLUTION_CONTRACT_VERSION,
    CryptoBtcIncidentGates,
    CryptoBtcResolutionContract,
)
from polymarket_alpha_lab.crypto_btc_forecast_service import (
    CryptoBtcForecastServiceInput,
    CryptoBtcForecastServiceResult,
    evaluate_and_persist_crypto_btc_forecast,
)
from polymarket_alpha_lab.supabase_team_evidence_aggregation_config import (
    SupabaseTeamEvidenceAggregationConfig,
)
from polymarket_alpha_lab.team_evidence_aggregation import (
    TeamEvidenceAggregationResult,
    build_team_evidence_aggregation_result,
)
from polymarket_alpha_lab.team_evidence_aggregation_db_row import (
    TeamEvaluationAttemptDbRow,
    team_evaluation_attempt_row_parameters,
    team_evaluation_attempt_to_db_row,
)
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationInput,
    TeamEvidenceAggregationRecord,
    TeamEvidenceAssessmentRevision,
    TeamEvidenceCapture,
    TeamEvidenceRevision,
    TeamEvidenceSourceLineage,
)
from polymarket_alpha_lab.team_forecast_build_envelope import (
    TeamForecastBuildEnvelope,
    TeamForecastEvaluationScope,
    TeamForecastEvaluatorReceipt,
    TeamForecastPolicyPublicationGate,
    TeamForecastRunMetadata,
    build_team_forecast_build_envelope,
    team_evidence_aggregation_id,
    team_forecast_evaluation_scope_payload,
    team_forecast_run_id,
    validate_team_forecast_build_envelope,
)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
)

CONDITION_ID = "condition-btc-evidence-2026-001"
MARKET_SLUG = "will-btc-evidence-policy-hold-2026"
EVENT_TEMPLATE = "crypto-btc-evidence-policy"
QUESTION_TEXT = (
    "Will Bitcoin trade above the pinned official reference threshold at the "
    "documented evaluation timestamp for this market window?"
)
RULES_SUMMARY = (
    "Resolves YES only if the official Polymarket-documented BTC reference price "
    "is at or above the pinned threshold at the documented close, using the "
    "official primary source hierarchy."
)
EVIDENCE_SOURCES = (
    "btc_derivatives_reference",
    "btc_onchain_reference",
    "btc_spot_reference",
)
SOURCE_SEEDS = {
    "btc_spot_reference": 1,
    "btc_derivatives_reference": 2,
    "btc_onchain_reference": 3,
}
REQUIREMENT_BY_SOURCE = {
    "btc_spot_reference": "btc_spot",
    "btc_derivatives_reference": "btc_derivatives",
    "btc_onchain_reference": "btc_onchain",
}
HARD_FLAGS = ("paper_only", "report_only", "readonly")
LOCAL_DSN = "postgresql://postgres:local-secret@localhost:54322/postgres"
DEFAULT_TABLE_NAME = "team_evaluation_attempts"
GATE_PAYLOAD_KEY = "external_publication_gate"

CATALOG_BY_SOURCE: dict[str, object] = {}
for _catalog_record in trusted_crypto_btc_source_catalog():
    CATALOG_BY_SOURCE.setdefault(_catalog_record.source_id, _catalog_record)
for _source_id in (*EVIDENCE_SOURCES, "btc_resolution_rules"):
    assert _source_id in CATALOG_BY_SOURCE, f"trusted catalog must cover {_source_id}"


def digest_hex(value: int) -> str:
    return format(value, "064x")


def catalog_binding(source_id: str) -> tuple[str, str]:
    record = CATALOG_BY_SOURCE[source_id]
    return record.record_id, record.record_digest


def catalog_overlap_evaluated_at(*source_ids: str) -> datetime:
    records = [CATALOG_BY_SOURCE[source_id] for source_id in source_ids]
    start = max(record.valid_from for record in records)
    end = min(record.valid_until for record in records)
    assert start < end, "trusted catalog windows must overlap for the pinned sources"
    return start + (end - start) / 2


# Freshness-aligned record timeline: the aggregation must actually accept the
# policy-selected records (evidence age 60s <= 900s, capture lag 20s <= 120s,
# everything available at evaluation time).
EVALUATED_AT = catalog_overlap_evaluated_at(*EVIDENCE_SOURCES)
FRESHNESS_ANCHOR = EVALUATED_AT - timedelta(seconds=60)
CAPTURED = FRESHNESS_ANCHOR + timedelta(seconds=20)
RECORDED = CAPTURED + timedelta(seconds=5)
ASSESSED = RECORDED + timedelta(seconds=5)
RECEIPT_TIME = EVALUATED_AT - timedelta(seconds=90)
RUN_STARTED_AT = EVALUATED_AT - timedelta(seconds=120)
RUN_COMPLETED_AT = EVALUATED_AT + timedelta(seconds=30)


def gates(**overrides: bool) -> CryptoBtcIncidentGates:
    values: dict[str, bool] = {
        "source_outage": False,
        "index_dislocation": False,
        "chain_reorg": False,
        "resolution_rule_change": False,
        "market_halt": False,
        "derivatives_feed_degraded": False,
    }
    values.update(overrides)
    return CryptoBtcIncidentGates(**values)


def btc_resolution_contract(**overrides: object) -> CryptoBtcResolutionContract:
    record_id, record_digest = catalog_binding("btc_resolution_rules")
    values: dict[str, object] = {
        "condition_id": CONDITION_ID,
        "market_slug": MARKET_SLUG,
        "event_template": EVENT_TEMPLATE,
        "question_text": QUESTION_TEXT,
        "rules_summary": RULES_SUMMARY,
        "close_time": datetime(2027, 1, 1, 0, 0, tzinfo=UTC),
        "resolution_catalog_record_id": record_id,
        "resolution_catalog_record_digest": record_digest,
        "contract_version": CRYPTO_BTC_RESOLUTION_CONTRACT_VERSION,
    }
    values.update(overrides)
    return CryptoBtcResolutionContract(**values)


def btc_record(source_id: str, *, suffix: str = "1") -> TeamEvidenceAggregationRecord:
    base = SOURCE_SEEDS[source_id] * 10
    lineage_id = f"lineage.{source_id}"
    lineage_digest = digest_hex(base + 1)
    content_digest = digest_hex(base + 3)
    evidence_id = f"evidence.{source_id}.{suffix}"
    evidence_digest = digest_hex(base + 4)
    assessment_id = f"assessment.{source_id}.{suffix}"
    assessment_digest = digest_hex(base + 5)
    return TeamEvidenceAggregationRecord(
        source_lineage=TeamEvidenceSourceLineage(
            source_lineage_id=lineage_id, source_lineage_digest=lineage_digest),
        capture=TeamEvidenceCapture(
            capture_id=f"capture.{source_id}.{suffix}", capture_digest=digest_hex(base + 2),
            source_lineage_id=lineage_id, source_lineage_digest=lineage_digest,
            content_digest=content_digest, captured_at=CAPTURED),
        evidence_revision=TeamEvidenceRevision(
            evidence_revision_id=evidence_id, evidence_revision_digest=evidence_digest,
            previous_evidence_revision_id=None, previous_evidence_revision_digest=None,
            source_lineage_id=lineage_id, source_lineage_digest=lineage_digest,
            content_digest=content_digest,
            requirement_ids=(REQUIREMENT_BY_SOURCE[source_id],),
            freshness_anchor_at=FRESHNESS_ANCHOR, recorded_at=RECORDED),
        assessment_revision=TeamEvidenceAssessmentRevision(
            assessment_revision_id=assessment_id, assessment_revision_digest=assessment_digest,
            previous_assessment_revision_id=None, previous_assessment_revision_digest=None,
            evidence_revision_id=evidence_id, evidence_revision_digest=evidence_digest,
            assessed_at=ASSESSED, probability_yes=Decimal("0.640000"),
            requested_weight=Decimal("0.400000"), rationale_digest=digest_hex(base + 6),
            independence_key=f"independence.{source_id}.{suffix}",
            correlation_key=f"correlation.{source_id}"),
    )


def btc_evidence_input(source_id: str, *, selected_current: bool = True) -> CryptoBtcEvidenceInput:
    pinned_id, pinned_digest = catalog_binding(source_id)
    return CryptoBtcEvidenceInput(
        source_id=source_id,
        record_id=pinned_id,
        record_digest=pinned_digest,
        record=btc_record(source_id),
        selected_current=selected_current,
    )


def default_evidence_inputs() -> tuple[CryptoBtcEvidenceInput, ...]:
    return tuple(btc_evidence_input(source_id) for source_id in EVIDENCE_SOURCES)


def unapproved_source_input() -> CryptoBtcEvidenceInput:
    spot_id, spot_digest = catalog_binding("btc_spot_reference")
    return CryptoBtcEvidenceInput(
        source_id="btc_unapproved_reference",
        record_id=spot_id,
        record_digest=spot_digest,
        record=btc_record("btc_spot_reference"),
        selected_current=True,
    )


# ---------------------------------------------------------------------------
# Node 3 input fixtures (idioms mirrored from tests/test_team_forecast_build_
# envelope.py; built only through the real public constructors).
# ---------------------------------------------------------------------------

SCOPE_VERSION = "crypto-btc-forecast-service-integration-v1"


def make_scope() -> TeamForecastEvaluationScope:
    return TeamForecastEvaluationScope(
        scope_version=SCOPE_VERSION,
        domain_context=(("team_id", "crypto_btc"), ("market_slug", MARKET_SLUG)),
        provenance=(
            f"gamma:market/{CONDITION_ID}",
            "clob:book/0xnode7-integration",
        ),
    )


def make_metadata() -> TeamForecastRunMetadata:
    return TeamForecastRunMetadata(
        run_label="node7-integration-run-001",
        generator_version="team-forecast-generator-v1",
        prompt_version="team-forecast-prompt-v3",
        started_at=RUN_STARTED_AT,
        completed_at=RUN_COMPLETED_AT,
    )


def record_identity(record: TeamEvidenceAggregationRecord) -> tuple[str, str, str, str]:
    return (
        record.source_lineage.source_lineage_id,
        record.capture.capture_id,
        record.evidence_revision.evidence_revision_id,
        record.assessment_revision.assessment_revision_id,
    )


def accepted_receipt(record: TeamEvidenceAggregationRecord) -> TeamForecastEvaluatorReceipt:
    return TeamForecastEvaluatorReceipt(
        evaluator_input_id=f"evaluator:{record.capture.capture_id}",
        input_digest=sha256(
            f"evaluator-input:{record.capture.capture_id}".encode("ascii")
        ).hexdigest(),
        receipt_time=RECEIPT_TIME,
        classification="accepted",
        accepted_record_identity=record_identity(record),
        reason_codes=("evaluator_submitted",),
    )


def rejected_receipt(
    evaluator_input_id: str = "evaluator:rejected-1",
) -> TeamForecastEvaluatorReceipt:
    return TeamForecastEvaluatorReceipt(
        evaluator_input_id=evaluator_input_id,
        input_digest=sha256(
            f"evaluator-input:{evaluator_input_id}".encode("ascii")
        ).hexdigest(),
        receipt_time=RECEIPT_TIME,
        classification="rejected",
        accepted_record_identity=None,
        reason_codes=("format_rejected",),
    )


def default_receipts() -> tuple[TeamForecastEvaluatorReceipt, ...]:
    return tuple(
        accepted_receipt(btc_record(source_id)) for source_id in EVIDENCE_SOURCES
    ) + (rejected_receipt(),)


def forecast_template() -> TeamForecastPacket:
    return TeamForecastPacket(
        forecast_id="forecast-template-node7-001",
        team_id="crypto_btc",
        condition_id=CONDITION_ID,
        market_slug=MARKET_SLUG,
        question="Will BTC close above the pinned official reference threshold?",
        category_id="finance.crypto.btc",
        event_template=EVENT_TEMPLATE,
        selected_side="yes",
        forecast_probability=Decimal("0.500000"),
        confidence=Decimal("0.700000"),
        evidence_quality=Decimal("0.650000"),
        data_freshness_score=Decimal("0.900000"),
        resolution_risk=Decimal("0.120000"),
        base_rate=Decimal("0.540000"),
        market_implied_probability_observed=Decimal("0.570000"),
        reason_codes=("aggregation_ready",),
        memory_references=("btc-memory-2026-q2",),
        source_references=("source-etf-flow-dashboard",),
        known_failure_modes=("weekend_liquidity_gap",),
        config_version="team-forecast-v0",
        prompt_version="team-forecast-prompt-v3",
        generated_at=RUN_STARTED_AT,
    )


def evidence_template(record: TeamEvidenceAggregationRecord) -> TeamForecastEvidencePacket:
    return TeamForecastEvidencePacket(
        evidence_id="evidence-template-node7-001",
        team_id="crypto_btc",
        market_slug=MARKET_SLUG,
        source_id=f"source-{record.source_lineage.source_lineage_id}",
        source_type="team_evaluator",
        data_timestamp=RECEIPT_TIME,
        data_freshness_seconds=60,
        evidence_type="team_assessment",
        evidence_text="Evaluator assessment bound to the accepted record identity.",
        weight=record.assessment_revision.requested_weight,
        reason_codes=("evaluator_submitted",),
    )


def default_evidence_packets() -> tuple[TeamForecastEvidencePacket, ...]:
    return tuple(
        evidence_template(btc_record(source_id)) for source_id in EVIDENCE_SOURCES
    )


# ---------------------------------------------------------------------------
# Persistence config and the recording fake writer (no database anywhere).
# ---------------------------------------------------------------------------


def enabled_config(**overrides: object) -> SupabaseTeamEvidenceAggregationConfig:
    values: dict[str, object] = dict(enabled=True, dsn=LOCAL_DSN)
    values.update(overrides)
    return SupabaseTeamEvidenceAggregationConfig(**values)  # type: ignore[arg-type]


class WriteResult(NamedTuple):
    inserted: bool
    attempt: str


DEFAULT_WRITE_RESULTS = (WriteResult(inserted=True, attempt="node7-integration-001"),)


class RecordingWriter:
    """Fake Node 5 writer: records the exact call, returns canned results."""

    def __init__(
        self, results: tuple[object, ...] = DEFAULT_WRITE_RESULTS
    ) -> None:
        self.results = results
        self.calls: list[tuple[str, tuple[TeamForecastBuildEnvelope, ...], str]] = []

    def __call__(
        self,
        dsn: str,
        envelopes: tuple[TeamForecastBuildEnvelope, ...],
        *,
        table_name: str = DEFAULT_TABLE_NAME,
    ) -> tuple[object, ...]:
        self.calls.append((dsn, envelopes, table_name))
        return self.results


# ---------------------------------------------------------------------------
# Service input builders for the three pinned scenarios.
# ---------------------------------------------------------------------------


def both_ready_input(**overrides: object) -> CryptoBtcForecastServiceInput:
    values: dict[str, object] = dict(
        condition_id=CONDITION_ID,
        market_slug=MARKET_SLUG,
        event_template=EVENT_TEMPLATE,
        resolution_contract=btc_resolution_contract(),
        incident_gates=gates(),
        evidence_inputs=default_evidence_inputs(),
        evaluated_at=EVALUATED_AT,
        scope=make_scope(),
        run_metadata=make_metadata(),
        evaluator_receipts=default_receipts(),
        legacy_forecast_packet=forecast_template(),
        legacy_evidence_packets=default_evidence_packets(),
        persistence_config=enabled_config(),
    )
    values.update(overrides)
    return CryptoBtcForecastServiceInput(**values)  # type: ignore[arg-type]


def policy_watch_input(**overrides: object) -> CryptoBtcForecastServiceInput:
    # A real caller still supplies templates; the service's combined gate must
    # keep them out of the packetless gated envelope.
    return both_ready_input(
        incident_gates=gates(derivatives_feed_degraded=True), **overrides
    )


def policy_blocked_input(**overrides: object) -> CryptoBtcForecastServiceInput:
    return both_ready_input(
        evidence_inputs=(unapproved_source_input(),),
        evaluator_receipts=(rejected_receipt("evaluator:btc-unapproved-1"),),
        legacy_forecast_packet=None,
        legacy_evidence_packets=(),
        **overrides,
    )


SCENARIO_INPUTS = {
    "ready": both_ready_input,
    "watch": policy_watch_input,
    "blocked": policy_blocked_input,
}


# ---------------------------------------------------------------------------
# Independent recomputation of the full real predecessor chain.
# ---------------------------------------------------------------------------


def real_chain(
    service_input: CryptoBtcForecastServiceInput,
) -> tuple[CryptoBtcEvidenceEvaluation, TeamEvidenceAggregationInput, TeamEvidenceAggregationResult]:
    evaluation = evaluate_crypto_btc_evidence(
        condition_id=service_input.condition_id,
        market_slug=service_input.market_slug,
        event_template=service_input.event_template,
        resolution_contract=service_input.resolution_contract,
        incident_gates=service_input.incident_gates,
        evidence_inputs=service_input.evidence_inputs,
        evaluated_at=service_input.evaluated_at,
    )
    aggregation_input = TeamEvidenceAggregationInput(
        evaluated_at=evaluation.evaluated_at,
        records=evaluation.records,
        current_revisions=evaluation.current_selections,
    )
    aggregation_result = build_team_evidence_aggregation_result(
        aggregation_input, config=evaluation.config
    )
    return evaluation, aggregation_input, aggregation_result


def combined_publication_status(
    policy_status: str, aggregation_status: str
) -> str:
    if "blocked" in (policy_status, aggregation_status):
        return "blocked"
    if "watch" in (policy_status, aggregation_status):
        return "watch"
    return "ready"


def policy_gate(evaluation: CryptoBtcEvidenceEvaluation) -> TeamForecastPolicyPublicationGate:
    return TeamForecastPolicyPublicationGate(
        status=evaluation.status, reason_codes=evaluation.reason_codes
    )


def expected_envelope(
    service_input: CryptoBtcForecastServiceInput,
    evaluation: CryptoBtcEvidenceEvaluation,
    aggregation_input: TeamEvidenceAggregationInput,
    aggregation_result: TeamEvidenceAggregationResult,
    *,
    gate: TeamForecastPolicyPublicationGate | None,
) -> TeamForecastBuildEnvelope:
    effective_ready = aggregation_result.status == "ready" and (
        gate is None or gate.status == "ready"
    )
    return build_team_forecast_build_envelope(
        aggregation_result,
        aggregation_input=aggregation_input,
        config=evaluation.config,
        scope=service_input.scope,
        run_metadata=service_input.run_metadata,
        evaluator_receipts=service_input.evaluator_receipts,
        legacy_forecast_packet=(
            service_input.legacy_forecast_packet if effective_ready else None
        ),
        legacy_evidence_packets=(
            service_input.legacy_evidence_packets if effective_ready else ()
        ),
        policy_publication_gate=gate,
    )


def assert_single_persistable_call(
    fake: RecordingWriter,
) -> tuple[TeamForecastBuildEnvelope, TeamEvaluationAttemptDbRow]:
    """One exact writer call whose envelope survives Node 5's offline checks."""
    assert len(fake.calls) == 1
    dsn, envelopes, table_name = fake.calls[0]
    assert dsn == LOCAL_DSN
    assert table_name == DEFAULT_TABLE_NAME
    assert type(envelopes) is tuple
    assert len(envelopes) == 1
    envelope = envelopes[0]
    assert type(envelope) is TeamForecastBuildEnvelope
    payload = team_forecast_evaluation_scope_payload(envelope)
    # Node 5's public orphan run-binding contract, checked before any connect.
    assert envelope.tea_id == team_evidence_aggregation_id(payload)
    assert envelope.tfr_id == team_forecast_run_id(
        envelope.tea_id, payload["run_metadata"]
    )
    # Node 4's real row conversion plus insert parameters prove persistability.
    row = team_evaluation_attempt_to_db_row(
        tea_id=envelope.tea_id,
        tfr_id=envelope.tfr_id,
        evaluation_scope_payload=payload,
    )
    parameters = team_evaluation_attempt_row_parameters(row)
    assert parameters["tea_id"] == envelope.tea_id
    assert parameters["tfr_id"] == envelope.tfr_id
    assert parameters["paper_only"] is True
    assert parameters["report_only"] is True
    assert parameters["readonly"] is True
    return envelope, row


# ---------------------------------------------------------------------------
# Tests.
# ---------------------------------------------------------------------------


def test_injection_surface_is_pinned_for_integration_use() -> None:
    parameters = inspect.signature(evaluate_and_persist_crypto_btc_forecast).parameters
    assert list(parameters) == ["service_input", "evaluator", "writer"]
    assert parameters["evaluator"].default is None
    assert parameters["writer"].default is None
    for name in ("evaluator", "writer"):
        assert parameters[name].kind is inspect.Parameter.KEYWORD_ONLY


def test_both_ready_full_real_chain_writes_packeted_envelope_once() -> None:
    service_input = both_ready_input()
    fake = RecordingWriter()
    result = evaluate_and_persist_crypto_btc_forecast(service_input, writer=fake)
    assert type(result) is CryptoBtcForecastServiceResult
    evaluation, aggregation_input, aggregation_result = real_chain(service_input)
    assert evaluation.status == "ready"
    assert aggregation_result.status == "ready"
    assert aggregation_result.publishable_probability_yes == Decimal("0.640000")
    # the result carries the exact real predecessor objects of the chain
    assert result.policy_evaluation == evaluation
    assert result.aggregation_result == aggregation_result
    assert result.publication_status == "ready"
    assert result.reason_codes == tuple(
        sorted(set(evaluation.reason_codes) | set(aggregation_result.reason_codes))
    )
    assert "policy.ready" in result.reason_codes
    assert "aggregation_ready" in result.reason_codes
    for flag in HARD_FLAGS:
        assert getattr(result, flag) is True
    envelope, row = assert_single_persistable_call(fake)
    assert envelope is result.envelope
    assert result.write_results == DEFAULT_WRITE_RESULTS
    assert len(result.write_results) == 1
    # the envelope is byte-identical to the real Node 3 build of the real
    # chain; the service may bind the ready policy gate or stay legacy-quiet
    gated = expected_envelope(
        service_input, evaluation, aggregation_input, aggregation_result,
        gate=policy_gate(evaluation))
    ungated = expected_envelope(
        service_input, evaluation, aggregation_input, aggregation_result, gate=None)
    assert envelope in (gated, ungated)
    matched_gate = policy_gate(evaluation) if envelope == gated else None
    validate_team_forecast_build_envelope(
        envelope,
        result=aggregation_result,
        aggregation_input=aggregation_input,
        config=evaluation.config,
        scope=service_input.scope,
        run_metadata=service_input.run_metadata,
        evaluator_receipts=service_input.evaluator_receipts,
        legacy_forecast_packet=service_input.legacy_forecast_packet,
        legacy_evidence_packets=service_input.legacy_evidence_packets,
        policy_publication_gate=matched_gate,
    )
    # packeted v1-id projections over the caller's templates
    assert envelope.legacy_forecast_packet is not None
    assert envelope.legacy_forecast_packet.forecast_id == envelope.tfr_id
    assert envelope.legacy_forecast_packet.forecast_probability == (
        aggregation_result.publishable_probability_yes)
    assert envelope.legacy_forecast_packet == replace(
        service_input.legacy_forecast_packet,
        forecast_id=envelope.tfr_id,
        forecast_probability=aggregation_result.publishable_probability_yes,
    )
    accepted = tuple(
        receipt for receipt in service_input.evaluator_receipts
        if receipt.classification == "accepted"
    )
    assert len(envelope.legacy_evidence_packets) == len(accepted) == 3
    for packet, template, replay in zip(
        envelope.legacy_evidence_packets,
        service_input.legacy_evidence_packets,
        envelope.evidence_replay_records,
        strict=True,
    ):
        assert packet.evidence_id == replay.evidence_id
        assert packet.evidence_id.startswith("tfe:v1:")
        assert packet == replace(template, evidence_id=packet.evidence_id)
    # the caller's template objects were never mutated
    assert service_input.legacy_forecast_packet.forecast_id == (
        "forecast-template-node7-001")
    assert service_input.legacy_forecast_packet.forecast_probability == (
        Decimal("0.500000"))
    # the persisted row binds to the canonical Node 2 fields
    assert row.status == aggregation_result.status == "ready"
    assert row.attempted_at == evaluation.evaluated_at
    assert row.config_version == evaluation.config.config_version
    assert row.scope_version == service_input.scope.scope_version
    assert row.hard_flag == (
        aggregation_result.contradiction.status == "blocked")


def test_policy_watch_yields_packetless_gated_envelope_still_persistable() -> None:
    service_input = policy_watch_input()
    fake = RecordingWriter()
    result = evaluate_and_persist_crypto_btc_forecast(service_input, writer=fake)
    evaluation, aggregation_input, aggregation_result = real_chain(service_input)
    assert evaluation.status == "watch"
    assert len(evaluation.records) == 3
    assert aggregation_result.status == "ready"
    assert result.publication_status == "watch"
    assert result.policy_evaluation == evaluation
    assert result.aggregation_result == aggregation_result
    envelope, row = assert_single_persistable_call(fake)
    assert envelope is result.envelope
    # packetless: the caller's templates never leak into the gated envelope
    assert envelope.legacy_forecast_packet is None
    assert envelope.legacy_evidence_packets == ()
    assert envelope.evidence_replay_records == ()
    # the amendment gate rides inside run_metadata and still converts to a row
    payload = team_forecast_evaluation_scope_payload(envelope)
    gate_entry = payload["run_metadata"][GATE_PAYLOAD_KEY]
    assert gate_entry["status"] == "watch"
    assert gate_entry["reason_codes"] == sorted(set(evaluation.reason_codes))
    assert gate_entry["paper_only"] is True
    assert gate_entry["readonly"] is True
    # the only representable form: the real Node 3 build with the watch gate
    assert envelope == expected_envelope(
        service_input, evaluation, aggregation_input, aggregation_result,
        gate=policy_gate(evaluation))
    # the persisted row keeps the canonical Node 2 status while the service
    # reports the combined watch status
    assert row.status == "ready"
    assert row.attempted_at == evaluation.evaluated_at
    assert result.write_results == DEFAULT_WRITE_RESULTS


def test_policy_blocked_unapproved_source_writes_packetless_envelope() -> None:
    service_input = policy_blocked_input()
    fake = RecordingWriter()
    result = evaluate_and_persist_crypto_btc_forecast(service_input, writer=fake)
    evaluation, aggregation_input, aggregation_result = real_chain(service_input)
    assert evaluation.status == "blocked"
    assert evaluation.records == ()
    assert evaluation.current_selections == ()
    assert aggregation_result.status == "blocked"
    assert result.publication_status == "blocked"
    assert result.policy_evaluation == evaluation
    assert result.aggregation_result == aggregation_result
    assert "evidence.source.unapproved" in result.reason_codes
    assert "blocking_requirement_unmet" in result.reason_codes
    envelope, row = assert_single_persistable_call(fake)
    assert envelope is result.envelope
    assert envelope.legacy_forecast_packet is None
    assert envelope.legacy_evidence_packets == ()
    assert envelope.evidence_replay_records == ()
    payload = team_forecast_evaluation_scope_payload(envelope)
    assert payload["run_metadata"][GATE_PAYLOAD_KEY]["status"] == "blocked"
    assert envelope == expected_envelope(
        service_input, evaluation, aggregation_input, aggregation_result,
        gate=policy_gate(evaluation))
    assert row.status == "blocked"
    assert row.attempted_at == evaluation.evaluated_at
    assert row.diagnostic_record_count == 0


def test_invalid_service_inputs_fail_before_the_writer_is_touched() -> None:
    # disabled persistence is rejected with no writer activity
    fake = RecordingWriter()
    with pytest.raises(ValueError):
        evaluate_and_persist_crypto_btc_forecast(
            both_ready_input(
                persistence_config=SupabaseTeamEvidenceAggregationConfig(
                    enabled=False, dsn=None)),
            writer=fake,
        )
    assert fake.calls == []
    # an accepted receipt bound to no aggregation record fails in the real
    # Node 3 contract before any writer activity
    ghost = TeamForecastEvaluatorReceipt(
        evaluator_input_id="evaluator:ghost",
        input_digest=sha256(b"evaluator-input:ghost").hexdigest(),
        receipt_time=RECEIPT_TIME,
        classification="accepted",
        accepted_record_identity=(
            "lineage:ghost", "capture:ghost", "evidence:ghost", "assessment:ghost"),
        reason_codes=("evaluator_submitted",),
    )
    fake = RecordingWriter()
    with pytest.raises(ValueError):
        evaluate_and_persist_crypto_btc_forecast(
            both_ready_input(evaluator_receipts=(ghost, rejected_receipt())),
            writer=fake,
        )
    assert fake.calls == []
    # a both-ready chain with a mismatched evidence-template count fails in
    # the real Node 3 packet boundary before any writer activity
    fake = RecordingWriter()
    with pytest.raises(ValueError):
        evaluate_and_persist_crypto_btc_forecast(
            both_ready_input(legacy_evidence_packets=()),
            writer=fake,
        )
    assert fake.calls == []


@pytest.mark.parametrize("label", ("ready", "watch", "blocked"))
def test_combined_status_and_reason_union(label: str) -> None:
    service_input = SCENARIO_INPUTS[label]()
    result = evaluate_and_persist_crypto_btc_forecast(
        service_input, writer=RecordingWriter())
    evaluation, _aggregation_input, aggregation_result = real_chain(service_input)
    assert result.publication_status == combined_publication_status(
        evaluation.status, aggregation_result.status)
    assert result.reason_codes == tuple(
        sorted(set(evaluation.reason_codes) | set(aggregation_result.reason_codes)))
    assert len(set(result.reason_codes)) == len(result.reason_codes)
    assert tuple(sorted(result.reason_codes)) == result.reason_codes
    # the predecessor reason tuples are never rewritten
    assert evaluation.reason_codes[-1] == f"policy.{evaluation.status}"
    assert ("aggregation_ready" in aggregation_result.reason_codes) == (
        aggregation_result.status == "ready")


def test_same_inputs_deterministically_reproduce_envelope_ids() -> None:
    service_input = both_ready_input()
    first_fake = RecordingWriter()
    second_fake = RecordingWriter()
    first = evaluate_and_persist_crypto_btc_forecast(
        service_input, writer=first_fake)
    second = evaluate_and_persist_crypto_btc_forecast(
        service_input, writer=second_fake)
    assert first.envelope == second.envelope
    assert (first.envelope.tea_id, first.envelope.tfr_id) == (
        second.envelope.tea_id, second.envelope.tfr_id)
    assert first.envelope.tea_id.startswith("tea:v1:")
    assert first.envelope.tfr_id.startswith("tfr:v1:")
    assert [replay.evidence_id for replay in first.envelope.evidence_replay_records] == [
        replay.evidence_id for replay in second.envelope.evidence_replay_records]
    assert first.publication_status == second.publication_status
    assert first.reason_codes == second.reason_codes
    assert first.policy_evaluation == second.policy_evaluation
    assert first.aggregation_result == second.aggregation_result
    assert len(first_fake.calls) == len(second_fake.calls) == 1
    assert first_fake.calls[0][1][0].tea_id == second_fake.calls[0][1][0].tea_id
    assert first_fake.calls[0][1][0].tfr_id == second_fake.calls[0][1][0].tfr_id
