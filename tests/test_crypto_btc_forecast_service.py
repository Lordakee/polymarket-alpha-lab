"""Node 7 red/green unit tests for the BTC forecast orchestration service.

Covers the exact public surface and default bindings, frozen/slotted/final
hard-flagged input and result dataclasses, the full invalid-shape input
battery (constructor and constructor-bypass forgery) proving every invalid
input fails before the evaluator and writer, the exact Node 6 keyword
evaluator call, aggregation input construction from the evaluation data and
validation before any writer activity, the combined blocked-over-watch-over
ready publication precedence with the sorted duplicate-free reason union,
the full three-by-three policy/aggregation packet and persistence matrix
(packets only when both gates are ready; the Node 3 policy publication gate
carries the exact policy status otherwise), non-ready packet-argument
fail-closed behavior at Node 3, malformed evaluator output, envelope
validation blocking the writer, writer argument shape and write-result
cardinality, and predecessor-object preservation without mutation.
"""
from __future__ import annotations

import dataclasses
from dataclasses import fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from typing import NamedTuple

import pytest

import polymarket_alpha_lab.crypto_btc_forecast_service as service_module
from polymarket_alpha_lab.crypto_btc_forecast_service import (
    CryptoBtcForecastServiceInput,
    CryptoBtcForecastServiceResult,
    evaluate_and_persist_crypto_btc_forecast,
)
from polymarket_alpha_lab.crypto_btc_evidence_policy import (
    CryptoBtcEvidenceEvaluation,
    CryptoBtcEvidenceInput,
    build_crypto_btc_evidence_policy_config,
    evaluate_crypto_btc_evidence,
)
from polymarket_alpha_lab.crypto_btc_evidence_resolution import (
    CryptoBtcIncidentGates,
    CryptoBtcResolutionAssessment,
    CryptoBtcResolutionContract,
)
from polymarket_alpha_lab.supabase_team_evidence_aggregation_config import (
    SupabaseTeamEvidenceAggregationConfig,
)
from polymarket_alpha_lab.team_evidence_aggregation import build_team_evidence_aggregation_result
from polymarket_alpha_lab.team_evidence_aggregation_attempt_psycopg import (
    insert_team_evaluation_attempts_with_psycopg,
)
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationInput,
    TeamEvidenceAggregationRecord,
    TeamEvidenceAssessmentRevision,
    TeamEvidenceCapture,
    TeamEvidenceCurrentRevisionSelection,
    TeamEvidenceRevision,
    TeamEvidenceSourceLineage,
)
from polymarket_alpha_lab.team_forecast_build_envelope import (
    TeamForecastEvaluationScope,
    TeamForecastEvaluatorReceipt,
    TeamForecastRunMetadata,
    build_team_forecast_build_envelope,
)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
)

HARD_FLAGS = ("paper_only", "report_only", "readonly")
BASE_TIME = datetime(2026, 7, 13, 10, 30, 0, tzinfo=timezone.utc)
EVALUATED_AT = BASE_TIME + timedelta(seconds=100)
RUN_STARTED_AT = datetime(2026, 7, 13, 9, 0, 0, tzinfo=timezone.utc)
RUN_COMPLETED_AT = datetime(2026, 7, 13, 9, 5, 0, tzinfo=timezone.utc)
RECEIPT_TIME = datetime(2026, 7, 13, 8, 59, 30, tzinfo=timezone.utc)
CLOSE_TIME = datetime(2027, 1, 1, 0, 0, tzinfo=timezone.utc)
LOCAL_DSN = "postgresql://postgres:postgres@localhost:5432/postgres"
CONDITION_ID = "condition-btc-node7-001"
MARKET_SLUG = "will-btc-node7-service-hold-2026"
EVENT_TEMPLATE = "crypto_price_threshold"
QUESTION_TEXT = (
    "Will Bitcoin trade above the pinned official reference threshold at the "
    "documented evaluation timestamp for this market window?")
RULES_SUMMARY = (
    "Resolves YES only if the official Polymarket-documented BTC reference "
    "price is at or above the pinned threshold at the documented close.")
GATE_PAYLOAD_KEY = "external_publication_gate"
POLICY_STATUSES = ("ready", "watch", "blocked")
INPUT_FIELD_NAMES = (
    "condition_id", "market_slug", "event_template", "resolution_contract", "incident_gates",
    "evidence_inputs", "evaluated_at", "scope", "run_metadata", "evaluator_receipts",
    "legacy_forecast_packet", "legacy_evidence_packets", "persistence_config",
    "paper_only", "report_only", "readonly")
RESULT_FIELD_NAMES = (
    "policy_evaluation", "aggregation_result", "publication_status", "reason_codes",
    "envelope", "write_results", "paper_only", "report_only", "readonly")


def digest_text(label: str) -> str:
    return sha256(label.encode("ascii")).hexdigest()


def forge(base: object, changes: dict[str, object]) -> object:
    """Constructor-bypass forgery of a frozen slotted dataclass."""
    forged = object.__new__(type(base))
    for name in type(base).__slots__:  # type: ignore[attr-defined]
        object.__setattr__(forged, name, getattr(base, name))
    for name, value in changes.items():
        object.__setattr__(forged, name, value)
    return forged


def forged_config(**changes: object) -> SupabaseTeamEvidenceAggregationConfig:
    """Constructor-bypass forgery of the frozen Node 4 configuration."""
    forged = object.__new__(SupabaseTeamEvidenceAggregationConfig)
    base = persistence_config_value()
    for name in ("enabled", "dsn", "table_name"):
        object.__setattr__(forged, name, getattr(base, name))
    for name, value in changes.items():
        object.__setattr__(forged, name, value)
    return forged


# --- caller-side fixtures built through the real public predecessors -------

def resolution_contract_value() -> CryptoBtcResolutionContract:
    return CryptoBtcResolutionContract(
        condition_id=CONDITION_ID, market_slug=MARKET_SLUG, event_template=EVENT_TEMPLATE,
        question_text=QUESTION_TEXT, rules_summary=RULES_SUMMARY, close_time=CLOSE_TIME,
        resolution_catalog_record_id="resolution-rules-node7",
        resolution_catalog_record_digest=digest_text("resolution-rules-node7"),
        contract_version="crypto-btc-resolution-contract-v0")


def incident_gates_value() -> CryptoBtcIncidentGates:
    return CryptoBtcIncidentGates(
        source_outage=False, index_dislocation=False, chain_reorg=False,
        resolution_rule_change=False, market_halt=False, derivatives_feed_degraded=False)


def node_record(
    stem: str,
    *,
    requirement_id: str,
    probability_yes: Decimal = Decimal("0.640000"),
    requested_weight: Decimal = Decimal("0.400000"),
) -> TeamEvidenceAggregationRecord:
    lineage_id = f"lineage.btc_{stem}"
    lineage_digest = digest_text(f"lineage:{stem}")
    content_digest = digest_text(f"content:{stem}")
    evidence_id = f"evidence.btc_{stem}"
    return TeamEvidenceAggregationRecord(
        source_lineage=TeamEvidenceSourceLineage(
            source_lineage_id=lineage_id, source_lineage_digest=lineage_digest),
        capture=TeamEvidenceCapture(
            capture_id=f"capture.btc_{stem}", capture_digest=digest_text(f"capture:{stem}"),
            source_lineage_id=lineage_id, source_lineage_digest=lineage_digest,
            content_digest=content_digest, captured_at=BASE_TIME + timedelta(seconds=5)),
        evidence_revision=TeamEvidenceRevision(
            evidence_revision_id=evidence_id, evidence_revision_digest=digest_text(f"evidence:{stem}"),
            previous_evidence_revision_id=None, previous_evidence_revision_digest=None,
            source_lineage_id=lineage_id, source_lineage_digest=lineage_digest,
            content_digest=content_digest, requirement_ids=(requirement_id,),
            freshness_anchor_at=BASE_TIME, recorded_at=BASE_TIME + timedelta(seconds=10)),
        assessment_revision=TeamEvidenceAssessmentRevision(
            assessment_revision_id=f"assessment.btc_{stem}",
            assessment_revision_digest=digest_text(f"assessment:{stem}"),
            previous_assessment_revision_id=None, previous_assessment_revision_digest=None,
            evidence_revision_id=evidence_id, evidence_revision_digest=digest_text(f"evidence:{stem}"),
            assessed_at=BASE_TIME + timedelta(seconds=15), probability_yes=probability_yes,
            requested_weight=requested_weight, rationale_digest=digest_text(f"rationale:{stem}"),
            independence_key=f"independence.btc_{stem}", correlation_key=f"correlation.btc_{stem}"))


RECORD_DERIVATIVES = node_record("derivatives", requirement_id="btc_derivatives")
RECORD_ONCHAIN = node_record("onchain", requirement_id="btc_onchain")
RECORD_SPOT = node_record("spot", requirement_id="btc_spot")
AGGREGATION_RECORDS: dict[str, tuple[TeamEvidenceAggregationRecord, ...]] = {
    "ready": (RECORD_DERIVATIVES, RECORD_ONCHAIN, RECORD_SPOT),
    "watch": (RECORD_SPOT,),
    "blocked": (RECORD_DERIVATIVES,),
}
AGGREGATION_REASON_CODES: dict[str, tuple[str, ...]] = {
    "ready": ("aggregation_ready",),
    "watch": ("watch_requirement_unmet",),
    "blocked": ("blocking_requirement_unmet", "watch_requirement_unmet"),
}


def _evaluation_record_key(record: TeamEvidenceAggregationRecord) -> tuple[object, ...]:
    return (
        record.assessment_revision.assessment_revision_id,
        record.evidence_revision.evidence_revision_id,
        record.capture.captured_at,
        record.capture.capture_id,
        record.source_lineage.source_lineage_id)


def _selection(record: TeamEvidenceAggregationRecord) -> TeamEvidenceCurrentRevisionSelection:
    return TeamEvidenceCurrentRevisionSelection(
        evidence_revision_id=record.evidence_revision.evidence_revision_id,
        evidence_revision_digest=record.evidence_revision.evidence_revision_digest,
        assessment_revision_id=record.assessment_revision.assessment_revision_id,
        assessment_revision_digest=record.assessment_revision.assessment_revision_digest)


def fake_evaluation(
    policy_status: str,
    records: tuple[TeamEvidenceAggregationRecord, ...],
) -> CryptoBtcEvidenceEvaluation:
    ordered = tuple(sorted(records, key=_evaluation_record_key))
    return CryptoBtcEvidenceEvaluation(
        evaluated_at=EVALUATED_AT, status=policy_status, records=ordered,
        current_selections=tuple(_selection(record) for record in ordered),
        config=build_crypto_btc_evidence_policy_config(),
        resolution_assessment=CryptoBtcResolutionAssessment(
            condition_id=CONDITION_ID, market_slug=MARKET_SLUG, event_template=EVENT_TEMPLATE,
            resolution_contract_status="pass",
            reason_codes=("crypto_btc_resolution_contract_passed",)),
        reason_codes=(f"policy.{policy_status}",))


def make_scope() -> TeamForecastEvaluationScope:
    return TeamForecastEvaluationScope(
        scope_version="crypto-btc-forecast-service-v1",
        domain_context=(("team_id", "crypto_btc"), ("market_slug", MARKET_SLUG)),
        provenance=("gamma:market/12345", "clob:book/0xabc"))


def make_metadata() -> TeamForecastRunMetadata:
    return TeamForecastRunMetadata(
        run_label="node7-service-run-001", generator_version="crypto-btc-forecast-service-v1",
        prompt_version="team-forecast-prompt-v3", started_at=RUN_STARTED_AT,
        completed_at=RUN_COMPLETED_AT)


def _record_identity(record: TeamEvidenceAggregationRecord) -> tuple[str, str, str, str]:
    return (
        record.source_lineage.source_lineage_id,
        record.capture.capture_id,
        record.evidence_revision.evidence_revision_id,
        record.assessment_revision.assessment_revision_id)


def accepted_receipt_value(record: TeamEvidenceAggregationRecord) -> TeamForecastEvaluatorReceipt:
    return TeamForecastEvaluatorReceipt(
        evaluator_input_id=f"evaluator:{record.capture.capture_id}",
        input_digest=digest_text(f"evaluator-input:{record.capture.capture_id}"),
        receipt_time=RECEIPT_TIME, classification="accepted",
        accepted_record_identity=_record_identity(record),
        reason_codes=("evaluator_submitted",))


def rejected_receipt_value() -> TeamForecastEvaluatorReceipt:
    return TeamForecastEvaluatorReceipt(
        evaluator_input_id="evaluator:rejected-1",
        input_digest=digest_text("evaluator-input:rejected-1"),
        receipt_time=RECEIPT_TIME, classification="rejected",
        accepted_record_identity=None, reason_codes=("format_rejected",))


def forecast_template_value() -> TeamForecastPacket:
    return TeamForecastPacket(
        forecast_id="forecast-template-node7-001", team_id="crypto_btc",
        condition_id="0xnode7condition", market_slug=MARKET_SLUG,
        question="Will BTC close above $105,000 on July 4?",
        category_id="finance.crypto.btc", event_template=EVENT_TEMPLATE,
        selected_side="yes", forecast_probability=Decimal("0.500000"),
        confidence=Decimal("0.700000"), evidence_quality=Decimal("0.650000"),
        data_freshness_score=Decimal("0.900000"), resolution_risk=Decimal("0.120000"),
        base_rate=Decimal("0.540000"),
        market_implied_probability_observed=Decimal("0.570000"),
        reason_codes=("aggregation_ready",), memory_references=("btc-memory-2026-q2",),
        source_references=("source-etf-flow-dashboard",),
        known_failure_modes=("weekend_liquidity_gap",), config_version="team-forecast-v0",
        prompt_version="team-forecast-prompt-v3", generated_at=RUN_STARTED_AT)


def evidence_template_value(record: TeamEvidenceAggregationRecord) -> TeamForecastEvidencePacket:
    return TeamForecastEvidencePacket(
        evidence_id=f"evidence-template-{record.capture.capture_id}", team_id="crypto_btc",
        market_slug=MARKET_SLUG,
        source_id=f"source-{record.source_lineage.source_lineage_id}",
        source_type="team_evaluator", data_timestamp=RECEIPT_TIME,
        data_freshness_seconds=60, evidence_type="team_assessment",
        evidence_text="Evaluator assessment bound to the accepted record identity.",
        weight=record.assessment_revision.requested_weight,
        reason_codes=("evaluator_submitted",))


def persistence_config_value(**overrides: object) -> SupabaseTeamEvidenceAggregationConfig:
    values: dict[str, object] = dict(enabled=True, dsn=LOCAL_DSN)
    values.update(overrides)
    return SupabaseTeamEvidenceAggregationConfig(**values)  # type: ignore[arg-type]


def evidence_input_value(stem: str) -> CryptoBtcEvidenceInput:
    record = AGGREGATION_RECORDS["ready"][("derivatives", "onchain", "spot").index(stem)]
    return CryptoBtcEvidenceInput(
        source_id=f"btc_{stem}_reference", record_id=f"record.btc_{stem}.1",
        record_digest=digest_text(f"record:node7:{stem}"), record=record,
        selected_current=True)


def make_service_input(**changes: object) -> CryptoBtcForecastServiceInput:
    values: dict[str, object] = dict(
        condition_id=CONDITION_ID, market_slug=MARKET_SLUG, event_template=EVENT_TEMPLATE,
        resolution_contract=resolution_contract_value(), incident_gates=incident_gates_value(),
        evidence_inputs=(evidence_input_value("derivatives"), evidence_input_value("onchain"),
                         evidence_input_value("spot")),
        evaluated_at=EVALUATED_AT, scope=make_scope(), run_metadata=make_metadata(),
        evaluator_receipts=(rejected_receipt_value(),),
        legacy_forecast_packet=forecast_template_value(), legacy_evidence_packets=(),
        persistence_config=persistence_config_value())
    values.update(changes)
    return CryptoBtcForecastServiceInput(**values)  # type: ignore[arg-type]


class ServiceCase(NamedTuple):
    policy_status: str
    aggregation_mode: str
    input_value: CryptoBtcForecastServiceInput
    evaluation: CryptoBtcEvidenceEvaluation
    records: tuple[TeamEvidenceAggregationRecord, ...]


def rescope_input(case: ServiceCase, **changes: object) -> ServiceCase:
    carried: dict[str, object] = dict(
        evaluator_receipts=case.input_value.evaluator_receipts,
        legacy_evidence_packets=case.input_value.legacy_evidence_packets,
        legacy_forecast_packet=case.input_value.legacy_forecast_packet)
    carried.update(changes)
    return ServiceCase(
        policy_status=case.policy_status, aggregation_mode=case.aggregation_mode,
        input_value=make_service_input(**carried), evaluation=case.evaluation,
        records=case.records)


def make_case(policy_status: str, aggregation_mode: str) -> ServiceCase:
    records = AGGREGATION_RECORDS[aggregation_mode]
    input_value = make_service_input(
        evaluator_receipts=tuple(
            [accepted_receipt_value(record) for record in records]
            + [rejected_receipt_value()]),
        legacy_evidence_packets=tuple(evidence_template_value(record) for record in records))
    return ServiceCase(
        policy_status=policy_status, aggregation_mode=aggregation_mode,
        input_value=input_value, evaluation=fake_evaluation(policy_status, records),
        records=records)


def combined_status(policy_status: str, aggregation_status: str) -> str:
    if "blocked" in (policy_status, aggregation_status):
        return "blocked"
    if "watch" in (policy_status, aggregation_status):
        return "watch"
    return "ready"


class SpyEvaluator:
    def __init__(self, evaluation: CryptoBtcEvidenceEvaluation) -> None:
        self.evaluation = evaluation
        self.calls: list[dict[str, object]] = []

    def __call__(self, **kwargs: object) -> CryptoBtcEvidenceEvaluation:
        self.calls.append(kwargs)
        return self.evaluation


class SpyWriter:
    def __init__(self, results: object = None) -> None:
        self.first: object = object()
        self.results = (self.first,) if results is None else results
        self.calls: list[dict[str, object]] = []

    def __call__(self, dsn: str, envelopes: tuple[object, ...], *, table_name: str):
        self.calls.append({"dsn": dsn, "envelopes": envelopes, "table_name": table_name})
        return self.results


def run_case(
    case: ServiceCase, *, writer_results: object = None,
) -> tuple[CryptoBtcForecastServiceResult, SpyEvaluator, SpyWriter]:
    evaluator = SpyEvaluator(case.evaluation)
    writer = SpyWriter(writer_results)
    result = evaluate_and_persist_crypto_btc_forecast(
        case.input_value, evaluator=evaluator, writer=writer)
    return result, evaluator, writer


def base_case() -> ServiceCase:
    return make_case("ready", "ready")


# --- public surface, default bindings, and dataclass shape -----------------

def test_module_public_surface_is_exact() -> None:
    assert service_module.__all__ == (
        "CryptoBtcForecastServiceInput",
        "CryptoBtcForecastServiceResult",
        "evaluate_and_persist_crypto_btc_forecast")
    for name in service_module.__all__:
        assert getattr(service_module, name, None) is not None
    assert service_module.evaluate_crypto_btc_evidence is evaluate_crypto_btc_evidence
    assert (service_module.insert_team_evaluation_attempts_with_psycopg
            is insert_team_evaluation_attempts_with_psycopg)


def _assert_hard_flagged_shape(dataclass_type: type, field_names: tuple[str, ...]) -> None:
    assert [field.name for field in fields(dataclass_type)] == list(field_names)
    defaults = {field.name: field.default for field in fields(dataclass_type)
                if field.name in HARD_FLAGS}
    assert defaults == dict.fromkeys(HARD_FLAGS, True)
    assert dataclass_type.__dataclass_params__.frozen is True
    assert dataclass_type.__dataclass_params__.slots is True
    assert getattr(dataclass_type, "__final__", False) is True
    with pytest.raises(TypeError):
        type("Forbidden", (dataclass_type,), {})


def test_input_dataclass_shape_frozen_slotted_final_hard_flagged() -> None:
    _assert_hard_flagged_shape(CryptoBtcForecastServiceInput, INPUT_FIELD_NAMES)
    base = base_case().input_value
    assert not hasattr(base, "__dict__")
    with pytest.raises(dataclasses.FrozenInstanceError):
        base.condition_id = "mutated"  # type: ignore[misc]


def test_result_dataclass_shape_frozen_slotted_final_hard_flagged() -> None:
    _assert_hard_flagged_shape(CryptoBtcForecastServiceResult, RESULT_FIELD_NAMES)
    result, _evaluator, _writer = run_case(base_case())
    assert not hasattr(result, "__dict__")
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.publication_status = "ready"  # type: ignore[misc]


# --- invalid-input battery: constructor and constructor-bypass forgery -----

INVALID_INPUT_OVERRIDES = (
    ("condition_id_empty", dict(condition_id="")),
    ("condition_id_padded", dict(condition_id=" padded")),
    ("condition_id_non_string", dict(condition_id=7)),
    ("market_slug_blank", dict(market_slug=" ")),
    ("event_template_non_string", dict(event_template=None)),
    ("resolution_contract_wrong_type", dict(resolution_contract=incident_gates_value())),
    ("incident_gates_wrong_type", dict(incident_gates=resolution_contract_value())),
    ("evidence_inputs_list", dict(evidence_inputs=[evidence_input_value("spot")])),
    ("evidence_inputs_wrong_element", dict(evidence_inputs=(make_scope(),))),
    ("evaluated_at_naive", dict(evaluated_at=datetime(2026, 7, 13, 10, 37))),
    ("evaluated_at_non_datetime", dict(evaluated_at="2026-07-13")),
    ("scope_wrong_type", dict(scope=make_metadata())),
    ("run_metadata_wrong_type", dict(run_metadata=make_scope())),
    ("receipts_list", dict(evaluator_receipts=[rejected_receipt_value()])),
    ("receipts_wrong_element", dict(evaluator_receipts=(make_scope(),))),
    ("forecast_packet_wrong_type", dict(legacy_forecast_packet="packet")),
    ("evidence_packets_list", dict(legacy_evidence_packets=[evidence_template_value(RECORD_SPOT)])),
    ("evidence_packets_wrong_element", dict(legacy_evidence_packets=(make_scope(),))),
    ("persistence_wrong_type", dict(persistence_config=("enabled", True))),
    ("persistence_disabled", dict(persistence_config=persistence_config_value(enabled=False, dsn=None))),
    ("paper_only_false", dict(paper_only=False)),
    ("report_only_false", dict(report_only=False)),
    ("readonly_false", dict(readonly=False)),
)


@pytest.mark.parametrize("label,overrides", INVALID_INPUT_OVERRIDES)
def test_input_constructor_rejects_invalid_shapes(
    label: str, overrides: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        make_service_input(**overrides)


FORGED_INPUT_LABELS = (
    "paper_only_false", "readonly_false", "condition_id_cleared", "evidence_inputs_list",
    "persistence_disabled", "dsn_none", "forecast_packet_swapped")


@pytest.mark.parametrize("label", FORGED_INPUT_LABELS)
def test_constructor_bypassed_input_tampering_fails_before_spies(label: str) -> None:
    case = base_case()
    changes: dict[str, object] = {
        "paper_only_false": {"paper_only": False},
        "readonly_false": {"readonly": False},
        "condition_id_cleared": {"condition_id": ""},
        "evidence_inputs_list": {"evidence_inputs": list(case.input_value.evidence_inputs)},
        "persistence_disabled": {"persistence_config": forged_config(enabled=False)},
        "dsn_none": {"persistence_config": forged_config(dsn=None)},
        "forecast_packet_swapped": {"legacy_forecast_packet": object()},
    }[label]
    evaluator = SpyEvaluator(case.evaluation)
    writer = SpyWriter()
    with pytest.raises(ValueError):
        evaluate_and_persist_crypto_btc_forecast(
            forge(case.input_value, changes), evaluator=evaluator, writer=writer)
    assert evaluator.calls == []
    assert writer.calls == []


def test_service_rejects_non_service_input() -> None:
    evaluator = SpyEvaluator(base_case().evaluation)
    writer = SpyWriter()
    with pytest.raises(ValueError):
        evaluate_and_persist_crypto_btc_forecast(
            object(), evaluator=evaluator, writer=writer)  # type: ignore[arg-type]
    assert evaluator.calls == []
    assert writer.calls == []


def test_input_requires_enabled_persistence_with_live_dsn() -> None:
    with pytest.raises(ValueError):
        make_service_input(persistence_config=SupabaseTeamEvidenceAggregationConfig(
            enabled=False, dsn=None))
    with pytest.raises(ValueError):
        make_service_input(persistence_config=forged_config(enabled=False))
    with pytest.raises(ValueError):
        make_service_input(persistence_config=forged_config(dsn=None))


def test_non_callable_injections_fail_closed() -> None:
    case = base_case()
    writer = SpyWriter()
    with pytest.raises(ValueError):
        evaluate_and_persist_crypto_btc_forecast(
            case.input_value, evaluator="not-callable", writer=writer)  # type: ignore[arg-type]
    evaluator = SpyEvaluator(case.evaluation)
    with pytest.raises(ValueError):
        evaluate_and_persist_crypto_btc_forecast(
            case.input_value, evaluator=evaluator, writer="not-callable")  # type: ignore[arg-type]
    assert writer.calls == []
    assert evaluator.calls == []


# --- evaluator call shape and predecessor-object preservation --------------

def test_evaluator_receives_exact_keyword_call() -> None:
    case = base_case()
    result, evaluator, writer = run_case(case)
    assert len(evaluator.calls) == 1
    call = evaluator.calls[0]
    assert set(call) == {
        "condition_id", "market_slug", "event_template", "resolution_contract",
        "incident_gates", "evidence_inputs", "evaluated_at"}
    assert call["condition_id"] is case.input_value.condition_id
    assert call["market_slug"] is case.input_value.market_slug
    assert call["event_template"] is case.input_value.event_template
    assert call["resolution_contract"] is case.input_value.resolution_contract
    assert call["incident_gates"] is case.input_value.incident_gates
    assert call["evidence_inputs"] is case.input_value.evidence_inputs
    assert call["evaluated_at"] is case.input_value.evaluated_at
    assert result.policy_evaluation is case.evaluation
    assert len(writer.calls) == 1


def test_aggregation_input_built_from_evaluation_data(
    monkeypatch: pytest.MonkeyPatch) -> None:
    case = base_case()
    build_calls: list[dict[str, object]] = []
    real_build = service_module.build_team_evidence_aggregation_result

    def build_spy(aggregation_input, *, config):
        build_calls.append({"aggregation_input": aggregation_input, "config": config})
        return real_build(aggregation_input, config=config)

    monkeypatch.setattr(service_module, "build_team_evidence_aggregation_result", build_spy)
    result, _evaluator, _writer = run_case(case)
    assert len(build_calls) == 1
    expected_input = TeamEvidenceAggregationInput(
        evaluated_at=case.evaluation.evaluated_at, records=case.evaluation.records,
        current_revisions=case.evaluation.current_selections)
    assert build_calls[0]["aggregation_input"] == expected_input
    assert build_calls[0]["config"] is case.evaluation.config
    assert result.aggregation_result.status == "ready"
    assert result.aggregation_result.config_version == case.evaluation.config.config_version


def test_operation_order_validates_before_writer(monkeypatch: pytest.MonkeyPatch) -> None:
    case = base_case()
    events: list[str] = []
    real_build = service_module.build_team_evidence_aggregation_result
    real_validate = service_module.validate_team_evidence_aggregation_result
    real_envelope_build = service_module.build_team_forecast_build_envelope
    real_envelope_validate = service_module.validate_team_forecast_build_envelope

    def build_spy(aggregation_input, *, config):
        events.append("aggregation:build")
        return real_build(aggregation_input, config=config)

    def validate_spy(result, *, aggregation_input, config):
        events.append("aggregation:validate")
        return real_validate(result, aggregation_input=aggregation_input, config=config)

    def envelope_build_spy(result, **kwargs):
        events.append("envelope:build")
        return real_envelope_build(result, **kwargs)

    def envelope_validate_spy(envelope, **kwargs):
        events.append("envelope:validate")
        return real_envelope_validate(envelope, **kwargs)

    monkeypatch.setattr(service_module, "build_team_evidence_aggregation_result", build_spy)
    monkeypatch.setattr(service_module, "validate_team_evidence_aggregation_result", validate_spy)
    monkeypatch.setattr(service_module, "build_team_forecast_build_envelope", envelope_build_spy)
    monkeypatch.setattr(service_module, "validate_team_forecast_build_envelope",
                        envelope_validate_spy)
    evaluator = SpyEvaluator(case.evaluation)
    writer = SpyWriter()

    def writer_spy(dsn, envelopes, *, table_name):
        events.append("writer")
        return writer(dsn, envelopes, table_name=table_name)

    evaluate_and_persist_crypto_btc_forecast(
        case.input_value, evaluator=evaluator, writer=writer_spy)
    assert events == [
        "aggregation:build", "aggregation:validate",
        "envelope:build", "envelope:validate", "writer"]


def test_aggregation_validation_failure_blocks_envelope_and_writer(
    monkeypatch: pytest.MonkeyPatch) -> None:
    case = base_case()
    real_build = service_module.build_team_evidence_aggregation_result
    real_envelope_build = service_module.build_team_forecast_build_envelope
    envelope_calls: list[object] = []

    def tampered_build(aggregation_input, *, config):
        return forge(real_build(aggregation_input, config=config), {"status": "watch"})

    def envelope_build_spy(result, **kwargs):
        envelope_calls.append(result)
        return real_envelope_build(result, **kwargs)

    monkeypatch.setattr(service_module, "build_team_evidence_aggregation_result", tampered_build)
    monkeypatch.setattr(service_module, "build_team_forecast_build_envelope", envelope_build_spy)
    evaluator = SpyEvaluator(case.evaluation)
    writer = SpyWriter()
    with pytest.raises(ValueError):
        evaluate_and_persist_crypto_btc_forecast(
            case.input_value, evaluator=evaluator, writer=writer)
    assert writer.calls == []
    assert envelope_calls == []


def test_envelope_validation_failure_blocks_writer(monkeypatch: pytest.MonkeyPatch) -> None:
    case = base_case()
    real_build = service_module.build_team_forecast_build_envelope

    def tampered_envelope_build(result, **kwargs):
        return forge(real_build(result, **kwargs), {"tea_id": "tea:v1:" + "f" * 64})

    monkeypatch.setattr(service_module, "build_team_forecast_build_envelope",
                        tampered_envelope_build)
    evaluator = SpyEvaluator(case.evaluation)
    writer = SpyWriter()
    with pytest.raises(ValueError):
        evaluate_and_persist_crypto_btc_forecast(
            case.input_value, evaluator=evaluator, writer=writer)
    assert writer.calls == []


def test_malformed_evaluator_output_fails_before_writer() -> None:
    case = base_case()
    writer = SpyWriter()

    def returning_string(**kwargs: object) -> object:
        return "not-an-evaluation"

    with pytest.raises(ValueError):
        evaluate_and_persist_crypto_btc_forecast(
            case.input_value, evaluator=returning_string, writer=writer)  # type: ignore[arg-type]
    evaluator_tampered = SpyEvaluator(forge(case.evaluation, {"paper_only": False}))  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        evaluate_and_persist_crypto_btc_forecast(
            case.input_value, evaluator=evaluator_tampered, writer=writer)
    assert writer.calls == []


# --- publication status, reason union, and the packet/persistence matrix ---

@pytest.mark.parametrize("policy_status", POLICY_STATUSES)
@pytest.mark.parametrize("aggregation_mode", POLICY_STATUSES)
def test_full_policy_aggregation_matrix(policy_status: str, aggregation_mode: str) -> None:
    case = make_case(policy_status, aggregation_mode)
    result, _evaluator, writer = run_case(case)
    assert result.aggregation_result.status == aggregation_mode
    expected_status = combined_status(policy_status, aggregation_mode)
    assert result.publication_status == expected_status
    expected_reasons = tuple(sorted(
        set((f"policy.{policy_status}",)) | set(AGGREGATION_REASON_CODES[aggregation_mode])))
    assert result.reason_codes == expected_reasons
    assert result.policy_evaluation is case.evaluation
    assert result.paper_only is True and result.report_only is True
    assert result.readonly is True
    assert result.write_results == (writer.first,)
    assert len(writer.calls) == 1
    call = writer.calls[0]
    assert call["dsn"] == case.input_value.persistence_config.dsn
    assert call["table_name"] == case.input_value.persistence_config.table_name
    assert type(call["envelopes"]) is tuple and len(call["envelopes"]) == 1
    assert call["envelopes"][0] is result.envelope
    run_metadata = result.envelope.evaluation_scope_payload["run_metadata"]
    assert type(run_metadata) is dict
    gate_entry = run_metadata.get(GATE_PAYLOAD_KEY)
    if expected_status == "ready":
        assert gate_entry is None
        assert result.envelope.legacy_forecast_packet is not None
        assert (result.envelope.legacy_forecast_packet.forecast_id
                == result.envelope.tfr_id)
        assert (result.envelope.legacy_forecast_packet.forecast_probability
                == result.aggregation_result.publishable_probability_yes)
        assert len(result.envelope.legacy_evidence_packets) == len(case.records)
        for packet in result.envelope.legacy_evidence_packets:
            assert packet.evidence_id.startswith("tfe:v1:")
        assert len(result.envelope.evidence_replay_records) == len(case.records)
    else:
        assert type(gate_entry) is dict
        assert gate_entry["status"] == policy_status
        assert gate_entry["reason_codes"] == [f"policy.{policy_status}"]
        assert result.envelope.legacy_forecast_packet is None
        assert result.envelope.legacy_evidence_packets == ()
        assert result.envelope.evidence_replay_records == ()


def test_policy_watch_with_aggregation_ready_gates_packets_and_persists() -> None:
    result, _evaluator, writer = run_case(make_case("watch", "ready"))
    assert result.publication_status == "watch"
    assert result.reason_codes == ("aggregation_ready", "policy.watch")
    gate_entry = result.envelope.evaluation_scope_payload["run_metadata"][GATE_PAYLOAD_KEY]
    assert gate_entry["status"] == "watch"
    assert result.envelope.legacy_forecast_packet is None
    assert result.envelope.legacy_evidence_packets == ()
    assert result.envelope.evidence_replay_records == ()
    assert len(writer.calls) == 1


def test_writer_forwards_custom_table_name() -> None:
    case = rescope_input(base_case(),
                         persistence_config=persistence_config_value(table_name="node7_attempts"))
    _result, _evaluator, writer = run_case(case)
    assert writer.calls[0]["table_name"] == "node7_attempts"


@pytest.mark.parametrize("bad_results", [(), (object(), object()), [object()]])
def test_writer_must_return_exactly_one_result(bad_results: object) -> None:
    case = base_case()
    evaluator = SpyEvaluator(case.evaluation)
    writer = SpyWriter(bad_results)
    with pytest.raises(ValueError):
        evaluate_and_persist_crypto_btc_forecast(
            case.input_value, evaluator=evaluator, writer=writer)


def test_both_ready_requires_forecast_template_before_writer() -> None:
    scoped = rescope_input(base_case(), legacy_forecast_packet=None)
    evaluator = SpyEvaluator(scoped.evaluation)
    writer = SpyWriter()
    with pytest.raises(ValueError):
        evaluate_and_persist_crypto_btc_forecast(
            scoped.input_value, evaluator=evaluator, writer=writer)
    assert writer.calls == []


def test_both_ready_requires_one_evidence_template_per_accepted_receipt() -> None:
    case = base_case()
    assert len(case.records) == 3
    scoped = ServiceCase(
        policy_status="ready", aggregation_mode="ready",
        input_value=make_service_input(
            evaluator_receipts=case.input_value.evaluator_receipts,
            legacy_evidence_packets=case.input_value.legacy_evidence_packets[:-1]),
        evaluation=case.evaluation, records=case.records)
    evaluator = SpyEvaluator(scoped.evaluation)
    writer = SpyWriter()
    with pytest.raises(ValueError):
        evaluate_and_persist_crypto_btc_forecast(
            scoped.input_value, evaluator=evaluator, writer=writer)
    assert writer.calls == []


def test_non_ready_aggregation_rejects_packet_arguments_at_node3() -> None:
    records = AGGREGATION_RECORDS["watch"]
    evaluation = fake_evaluation("ready", records)
    aggregation_input = TeamEvidenceAggregationInput(
        evaluated_at=evaluation.evaluated_at, records=evaluation.records,
        current_revisions=evaluation.current_selections)
    aggregation_result = build_team_evidence_aggregation_result(
        aggregation_input, config=evaluation.config)
    assert aggregation_result.status == "watch"
    receipts = (accepted_receipt_value(records[0]), rejected_receipt_value())
    with pytest.raises(ValueError):
        build_team_forecast_build_envelope(
            aggregation_result, aggregation_input=aggregation_input,
            config=evaluation.config, scope=make_scope(), run_metadata=make_metadata(),
            evaluator_receipts=receipts, legacy_forecast_packet=forecast_template_value(),
            legacy_evidence_packets=())
    with pytest.raises(ValueError):
        build_team_forecast_build_envelope(
            aggregation_result, aggregation_input=aggregation_input,
            config=evaluation.config, scope=make_scope(), run_metadata=make_metadata(),
            evaluator_receipts=receipts, legacy_forecast_packet=None,
            legacy_evidence_packets=(evidence_template_value(records[0]),))


def test_default_bindings_used_when_injections_omitted(
    monkeypatch: pytest.MonkeyPatch) -> None:
    case = base_case()
    events: list[str] = []

    def default_evaluator_spy(**kwargs: object):
        events.append("evaluator")
        return case.evaluation

    def default_writer_spy(dsn, envelopes, *, table_name):
        events.append("writer")
        return (object(),)

    monkeypatch.setattr(service_module, "evaluate_crypto_btc_evidence",
                        default_evaluator_spy)
    monkeypatch.setattr(service_module, "insert_team_evaluation_attempts_with_psycopg",
                        default_writer_spy)
    result = evaluate_and_persist_crypto_btc_forecast(case.input_value)
    assert events == ["evaluator", "writer"]
    assert result.publication_status == "ready"
    assert result.policy_evaluation is case.evaluation


# --- result contract validation --------------------------------------------

RESULT_INVALID_LABELS = (
    "policy_evaluation_wrong_type", "aggregation_result_wrong_type",
    "publication_status_unknown", "publication_status_inconsistent",
    "reason_codes_unsorted", "reason_codes_duplicated", "reason_codes_foreign",
    "envelope_wrong_type", "write_results_empty", "write_results_double",
    "paper_only_false", "report_only_false", "readonly_false")


@pytest.mark.parametrize("label", RESULT_INVALID_LABELS)
def test_result_constructor_rejects_invalid_shapes(label: str) -> None:
    result, _evaluator, _writer = run_case(base_case())
    changes: dict[str, object] = {
        "policy_evaluation_wrong_type": {"policy_evaluation": make_scope()},
        "aggregation_result_wrong_type": {"aggregation_result": make_metadata()},
        "publication_status_unknown": {"publication_status": "queued"},
        "publication_status_inconsistent": {"publication_status": "watch"},
        "reason_codes_unsorted": {"reason_codes": tuple(reversed(result.reason_codes))},
        "reason_codes_duplicated": {
            "reason_codes": result.reason_codes + (result.reason_codes[0],)},
        "reason_codes_foreign": {"reason_codes": result.reason_codes + ("service.secret",)},
        "envelope_wrong_type": {"envelope": make_scope()},
        "write_results_empty": {"write_results": ()},
        "write_results_double": {"write_results": result.write_results + (object(),)},
        "paper_only_false": {"paper_only": False},
        "report_only_false": {"report_only": False},
        "readonly_false": {"readonly": False},
    }[label]
    forged = forge(result, changes)
    values = {field.name: getattr(forged, field.name)
              for field in fields(CryptoBtcForecastServiceResult)}
    with pytest.raises(ValueError):
        CryptoBtcForecastServiceResult(**values)
