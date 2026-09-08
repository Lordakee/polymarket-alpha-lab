"""Offline red-batch contract tests for the Node 3 team forecast build envelope.

Governing plan: docs/superpowers/plans/2026-07-13-team-forecast-build-envelope.md
Scope: the test side of Tasks 2, 3, and 4 - scope/run/receipt contracts,
canonical Node 2 fragments, domain-separated tea:tfr:tfe identifiers, legacy
projection, and the ready-only packet boundary. The production module
``src/polymarket_alpha_lab/team_forecast_build_envelope.py`` is implemented by
Worker A against this red batch; until it exists, collection fails with an
ImportError, which is the expected red state.

Spy contract pinned here (mirrors the Node 2C test file): the production
module must bind the consumed predecessor functions
(``validate_team_evidence_aggregation_result`` and the three Node 2 codec
payload functions) as plain module-level names, because the monkeypatch spies
patch those names inside the
``polymarket_alpha_lab.team_forecast_build_envelope`` namespace and delegate
to the real implementations.

Contract details the plan leaves unnamed are pinned here so Worker A can
green this batch in one pass (field names follow the plan's own wording):
- Envelope fields: ``tea_id``, ``tfr_id``, ``evaluation_scope_payload``,
  ``legacy_forecast_packet``, ``legacy_evidence_packets``,
  ``evidence_replay_records``, plus the three literal hard flags.
- Scope payload top-level keys (exact set): ``scope_version``,
  ``domain_context``, ``provenance``, ``run_metadata``, ``evaluator_receipts``,
  ``node2_config``, ``node2_input``, ``node2_result``. Every canonical
  receipt entry exposes ``evaluator_input_id``, ``input_digest``, and
  ``classification`` keys; ``domain_context`` is a plain JSON object.
- Receipt identities use the Node 2C four-field order (source_lineage_id,
  capture_id, evidence_revision_id, assessment_revision_id).
- ID helpers: ``team_evidence_aggregation_id(evaluation_scope_payload)``,
  ``team_forecast_run_id(tea_id, run_metadata_payload)``,
  ``team_forecast_evidence_id(tea_id, receipt_payload,
  legacy_payload_sha256)``, and
  ``team_forecast_legacy_payload_sha256(legacy_payload_dict)`` using the
  exact historical JSON encoding without an ``ensure_ascii`` argument.
- ``team_forecast_evaluation_scope_payload(envelope)`` re-surfaces the
  envelope's canonical evaluation-scope payload.
- Ready-only packet construction: the output forecast packet is the supplied
  template with ``forecast_id`` replaced by the ``tfr:v1`` ID and
  ``forecast_probability`` replaced by ``result.publishable_probability_yes``;
  each output evidence packet is the supplied template with ``evidence_id``
  replaced by its ``tfe:v1`` ID, in canonical accepted-receipt order. Replay
  legacy payloads and hashes are the existing payload projection of the
  supplied template packets, since the ``tfe:v1`` ID is derived from that hash.
"""

from __future__ import annotations

import inspect
import json
import re
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from typing import Any, NamedTuple

import pytest

import polymarket_alpha_lab.team_forecast_build_envelope as tfe_envelope
from polymarket_alpha_lab.team_forecast_build_envelope import (
    TeamForecastEvaluationScope,
    TeamForecastEvaluatorReceipt,
    TeamForecastRunMetadata,
    build_team_forecast_build_envelope,
    team_evidence_aggregation_id,
    team_forecast_evidence_id,
    team_forecast_legacy_payload_sha256,
    team_forecast_run_id,
    validate_team_forecast_build_envelope,
)
import polymarket_alpha_lab.team_evidence_aggregation as team_evidence_aggregation
from polymarket_alpha_lab.team_evidence_aggregation import (
    build_team_evidence_aggregation_result,
)
from polymarket_alpha_lab.team_evidence_aggregation_codec import (
    team_evidence_aggregation_config_digest,
    team_evidence_aggregation_config_payload,
    team_evidence_aggregation_input_payload,
    team_evidence_aggregation_payload,
)
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig,
    TeamEvidenceAggregationInput,
    TeamEvidenceAggregationRecord,
    TeamEvidenceAggregationResult,
    TeamEvidenceCurrentRevisionSelection,
    TeamEvidenceAssessmentRevision,
    TeamEvidenceCapture,
    TeamEvidenceRequirement,
    TeamEvidenceRevision,
    TeamEvidenceSourceLineage,
)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
    team_forecast_packet_payload,
)

real_validate = team_evidence_aggregation.validate_team_evidence_aggregation_result
build = build_team_forecast_build_envelope
validate = validate_team_forecast_build_envelope

BASE_TIME = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
EVALUATED_AT = BASE_TIME + timedelta(seconds=100)
RUN_STARTED_AT = datetime(2026, 7, 13, 9, 0, 0, tzinfo=timezone.utc)
RUN_COMPLETED_AT = datetime(2026, 7, 13, 9, 5, 0, tzinfo=timezone.utc)
RECEIPT_TIME = datetime(2026, 7, 13, 8, 59, 30, tzinfo=timezone.utc)
SCOPE_VERSION = "team-forecast-build-envelope-v1"
HEX64 = re.compile(r"[0-9a-f]{64}")
V1_KEYS = (
    "tea_id", "tfr_id", "tfe_id", "tea:v1", "tfr:v1", "tfe:v1",
    "evaluation_scope", "evidence_replay_records",
)
SCOPE_PAYLOAD_KEYS = {
    "scope_version", "domain_context", "provenance", "run_metadata",
    "evaluator_receipts", "node2_config", "node2_input", "node2_result",
}


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(label: str) -> str:
    return sha256(label.encode("ascii")).hexdigest()


def canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload, allow_nan=False, ensure_ascii=True, sort_keys=True,
        separators=(",", ":")).encode("utf-8")


def historical_legacy_bytes(payload: dict[str, Any]) -> bytes:
    """The exact historical legacy encoding pinned by the plan."""
    return json.dumps(
        payload, allow_nan=False, separators=(",", ":"), sort_keys=True,
    ).encode("utf-8")


def forge(base: object, changes: dict[str, object]) -> object:
    """Constructor-bypass forgery of a frozen slotted dataclass."""
    forged = object.__new__(type(base))
    for name in type(base).__slots__:  # type: ignore[attr-defined]
        object.__setattr__(forged, name, getattr(base, name))
    for name, value in changes.items():
        object.__setattr__(forged, name, value)
    return forged


# ---------------------------------------------------------------------------
# Node 2C fixture block (local idioms mirroring tests/test_team_evidence_
# aggregation.py; genuine results come from the real reviewed builder).
# ---------------------------------------------------------------------------

BASE_CONFIG_VALUES: dict[str, object] = {
    "config_version": "generic-test-v1",
    "max_evidence_age_seconds": d("60.000000"), "max_capture_lag_seconds": d("20.000000"),
    "independence_group_weight_cap": d("1.000000"), "correlation_group_weight_cap": d("1.000000"),
    "max_requirement_assignments_per_evidence": 2,
    "contradiction_no_probability_max": d("0.250000"), "contradiction_yes_probability_min": d("0.750000"),
    "contradiction_watch_score": d("0.250000"), "contradiction_block_score": d("0.750000"),
    "publish_probability_floor": d("0.110000"), "publish_probability_ceiling": d("0.890000"),
    "maximum_records": 128, "maximum_requirements": 32,
    "maximum_requirement_memberships": 1024, "maximum_witness_edges": 256,
    "requirements": (),
}


def node2_config(**changes: object) -> TeamEvidenceAggregationConfig:
    values = dict(BASE_CONFIG_VALUES)
    values.update(changes)
    return TeamEvidenceAggregationConfig(**values)


def requirement(
    requirement_id: str,
    *,
    minimum_witness_count: int = 1,
    minimum_effective_weight: Decimal = d("0.000000"),
    unmet_status: str = "watch",
) -> TeamEvidenceRequirement:
    return TeamEvidenceRequirement(
        requirement_id=requirement_id, minimum_witness_count=minimum_witness_count,
        minimum_effective_weight=minimum_effective_weight, unmet_status=unmet_status)


WATCH_REQUIREMENT = requirement("req:watch", unmet_status="watch")
BLOCKED_REQUIREMENT = requirement("req:blocked", unmet_status="blocked")


def root_record(
    stem: str,
    *,
    freshness_anchor_offset: int = 50,
    captured_offset: int = 55,
    recorded_offset: int = 60,
    assessed_offset: int = 65,
    probability_yes: Decimal = d("0.600000"),
    requested_weight: Decimal = d("0.200000"),
) -> TeamEvidenceAggregationRecord:
    source_lineage_id = f"lineage:{stem}"
    source_lineage_digest = digest(f"lineage-digest:{stem}")
    content_digest = digest(f"content:{stem}")
    evidence_revision_id = f"evidence:{stem}"
    evidence_revision_digest = digest(f"evidence-digest:{stem}")
    lineage = TeamEvidenceSourceLineage(
        source_lineage_id=source_lineage_id, source_lineage_digest=source_lineage_digest)
    capture = TeamEvidenceCapture(
        capture_id=f"capture:{stem}", capture_digest=digest(f"capture-digest:{stem}"),
        source_lineage_id=source_lineage_id, source_lineage_digest=source_lineage_digest,
        content_digest=content_digest, captured_at=BASE_TIME + timedelta(seconds=captured_offset))
    evidence_revision = TeamEvidenceRevision(
        evidence_revision_id=evidence_revision_id, evidence_revision_digest=evidence_revision_digest,
        previous_evidence_revision_id=None, previous_evidence_revision_digest=None,
        source_lineage_id=source_lineage_id, source_lineage_digest=source_lineage_digest,
        content_digest=content_digest, requirement_ids=(),
        freshness_anchor_at=BASE_TIME + timedelta(seconds=freshness_anchor_offset),
        recorded_at=BASE_TIME + timedelta(seconds=recorded_offset))
    assessment_revision = TeamEvidenceAssessmentRevision(
        assessment_revision_id=f"assessment:{stem}",
        assessment_revision_digest=digest(f"assessment-digest:{stem}"),
        previous_assessment_revision_id=None, previous_assessment_revision_digest=None,
        evidence_revision_id=evidence_revision_id, evidence_revision_digest=evidence_revision_digest,
        assessed_at=BASE_TIME + timedelta(seconds=assessed_offset),
        probability_yes=probability_yes, requested_weight=requested_weight,
        rationale_digest=digest(f"rationale:{stem}"),
        independence_key=f"ind:{stem}", correlation_key=f"corr:{stem}")
    return TeamEvidenceAggregationRecord(
        source_lineage=lineage, capture=capture, evidence_revision=evidence_revision,
        assessment_revision=assessment_revision)


def selection(record: TeamEvidenceAggregationRecord) -> TeamEvidenceCurrentRevisionSelection:
    return TeamEvidenceCurrentRevisionSelection(
        evidence_revision_id=record.evidence_revision.evidence_revision_id,
        evidence_revision_digest=record.evidence_revision.evidence_revision_digest,
        assessment_revision_id=record.assessment_revision.assessment_revision_id,
        assessment_revision_digest=record.assessment_revision.assessment_revision_digest)


def aggregation_input_value(
    records: tuple[TeamEvidenceAggregationRecord, ...],
) -> TeamEvidenceAggregationInput:
    return TeamEvidenceAggregationInput(
        evaluated_at=EVALUATED_AT, records=records,
        current_revisions=tuple(selection(record) for record in records))


def record_identity(record: TeamEvidenceAggregationRecord) -> tuple[str, str, str, str]:
    """The Node 2C four-field identity order: lineage, capture, evidence, assessment."""
    return (
        record.source_lineage.source_lineage_id,
        record.capture.capture_id,
        record.evidence_revision.evidence_revision_id,
        record.assessment_revision.assessment_revision_id)


# ---------------------------------------------------------------------------
# Node 1 legacy packet templates built through the real public constructors.
# ---------------------------------------------------------------------------

MARKET_SLUG = "will-btc-close-above-105k-on-july-4"


def forecast_template(
    *,
    forecast_id: str = "forecast-template-001",
    forecast_probability: Decimal = d("0.500000"),
) -> TeamForecastPacket:
    return TeamForecastPacket(
        forecast_id=forecast_id,
        team_id="crypto_btc",
        condition_id="0xredbatchcondition",
        market_slug=MARKET_SLUG,
        question="Will BTC close above $105,000 on July 4?",
        category_id="finance.crypto.btc",
        event_template="crypto_price_threshold",
        selected_side="yes",
        forecast_probability=forecast_probability,
        confidence=d("0.700000"),
        evidence_quality=d("0.650000"),
        data_freshness_score=d("0.900000"),
        resolution_risk=d("0.120000"),
        base_rate=d("0.540000"),
        market_implied_probability_observed=d("0.570000"),
        reason_codes=("aggregation_ready",),
        memory_references=("btc-memory-2026-q2",),
        source_references=("source-etf-flow-dashboard",),
        known_failure_modes=("weekend_liquidity_gap",),
        config_version="team-forecast-v0",
        prompt_version="team-forecast-prompt-v3",
        generated_at=RUN_STARTED_AT,
    )


def evidence_template(
    record: TeamEvidenceAggregationRecord,
    *,
    evidence_id: str = "evidence-template-001",
) -> TeamForecastEvidencePacket:
    return TeamForecastEvidencePacket(
        evidence_id=evidence_id,
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


# ---------------------------------------------------------------------------
# Node 3 input fixtures.
# ---------------------------------------------------------------------------

def make_scope(**changes: object) -> TeamForecastEvaluationScope:
    values: dict[str, object] = dict(
        scope_version=SCOPE_VERSION,
        domain_context=(("team_id", "crypto_btc"), ("market_slug", MARKET_SLUG)),
        provenance=("gamma:market/12345", "clob:book/0xabc"),
    )
    values.update(changes)
    return TeamForecastEvaluationScope(**values)  # type: ignore[arg-type]


def make_metadata(**changes: object) -> TeamForecastRunMetadata:
    values: dict[str, object] = dict(
        run_label="node3-red-batch-001",
        generator_version="team-forecast-generator-v1",
        prompt_version="team-forecast-prompt-v3",
        started_at=RUN_STARTED_AT,
        completed_at=RUN_COMPLETED_AT,
    )
    values.update(changes)
    return TeamForecastRunMetadata(**values)  # type: ignore[arg-type]


REJECTED_INPUT_ID = "evaluator:rejected-1"
REJECTED_INPUT_DIGEST = digest("evaluator-input:rejected-1")


def rejected_receipt(**changes: object) -> TeamForecastEvaluatorReceipt:
    values: dict[str, object] = dict(
        evaluator_input_id=REJECTED_INPUT_ID,
        input_digest=REJECTED_INPUT_DIGEST,
        receipt_time=RECEIPT_TIME,
        classification="rejected",
        accepted_record_identity=None,
        # deliberately unsorted and duplicated to exercise canonical sorting
        reason_codes=("format_rejected", "evaluator_declined", "format_rejected"),
    )
    values.update(changes)
    return TeamForecastEvaluatorReceipt(**values)  # type: ignore[arg-type]


def accepted_receipt(
    record: TeamEvidenceAggregationRecord,
    **changes: object,
) -> TeamForecastEvaluatorReceipt:
    values: dict[str, object] = dict(
        evaluator_input_id=f"evaluator:{record.capture.capture_id}",
        input_digest=digest(f"evaluator-input:{record.capture.capture_id}"),
        receipt_time=RECEIPT_TIME,
        classification="accepted",
        accepted_record_identity=record_identity(record),
        reason_codes=("evaluator_submitted",),
    )
    values.update(changes)
    return TeamForecastEvaluatorReceipt(**values)  # type: ignore[arg-type]


class EnvelopeCase(NamedTuple):
    result: TeamEvidenceAggregationResult
    aggregation_input: TeamEvidenceAggregationInput
    config: TeamEvidenceAggregationConfig
    records: tuple[TeamEvidenceAggregationRecord, ...]
    scope: TeamForecastEvaluationScope
    run_metadata: TeamForecastRunMetadata
    receipts: tuple[TeamForecastEvaluatorReceipt, ...]
    forecast_packet: TeamForecastPacket | None
    evidence_packets: tuple[TeamForecastEvidencePacket, ...]


def make_case(
    *,
    mode: str = "ready",
    second_record: bool = False,
    probability: Decimal = d("0.600000"),
    template_probability: Decimal = d("0.500000"),
) -> EnvelopeCase:
    if mode == "ready":
        config_value = node2_config()
    elif mode == "watch":
        config_value = node2_config(requirements=(WATCH_REQUIREMENT,))
    elif mode == "blocked":
        config_value = node2_config(requirements=(BLOCKED_REQUIREMENT,))
    else:
        raise AssertionError(f"unknown mode {mode}")
    records = [root_record("alpha", probability_yes=probability)]
    if second_record:
        records.append(root_record("beta", probability_yes=d("0.800000"), requested_weight=d("0.300000")))
    input_value = aggregation_input_value(tuple(records))
    result = build_team_evidence_aggregation_result(input_value, config=config_value)
    canonical_receipts = sorted(
        [accepted_receipt(record) for record in records] + [rejected_receipt()],
        key=lambda receipt: receipt.evaluator_input_id)
    ready = mode == "ready"
    return EnvelopeCase(
        result=result,
        aggregation_input=input_value,
        config=config_value,
        records=tuple(records),
        scope=make_scope(),
        run_metadata=make_metadata(),
        # supplied deliberately unsorted to exercise canonical receipt sorting
        receipts=tuple(reversed(canonical_receipts)),
        forecast_packet=forecast_template(forecast_probability=template_probability) if ready else None,
        evidence_packets=tuple(evidence_template(record) for record in records) if ready else (),
    )


def ready_case(**kwargs: object) -> EnvelopeCase:
    return make_case(mode="ready", **kwargs)  # type: ignore[arg-type]


def non_ready_case(mode: str) -> EnvelopeCase:
    assert mode in ("watch", "blocked")
    return make_case(mode=mode)


def build_case(case: EnvelopeCase, **overrides: object):
    kwargs: dict[str, object] = dict(
        aggregation_input=case.aggregation_input,
        config=case.config,
        scope=case.scope,
        run_metadata=case.run_metadata,
        evaluator_receipts=case.receipts,
        legacy_forecast_packet=case.forecast_packet,
        legacy_evidence_packets=case.evidence_packets,
    )
    kwargs.update(overrides)
    return build(case.result, **kwargs)  # type: ignore[arg-type]


def validator_kwargs(case: EnvelopeCase) -> dict[str, object]:
    return dict(
        aggregation_input=case.aggregation_input,
        config=case.config,
        scope=case.scope,
        run_metadata=case.run_metadata,
        evaluator_receipts=case.receipts,
        legacy_forecast_packet=case.forecast_packet,
        legacy_evidence_packets=case.evidence_packets,
    )


def accepted_receipts_of(case: EnvelopeCase) -> list[TeamForecastEvaluatorReceipt]:
    return sorted(
        (receipt for receipt in case.receipts if receipt.classification == "accepted"),
        key=lambda receipt: receipt.evaluator_input_id)


def receipt_entry_for(scope_payload: dict[str, object], evaluator_input_id: str) -> object:
    matches = [
        entry for entry in scope_payload["evaluator_receipts"]  # type: ignore[index,index]
        if entry.get("evaluator_input_id") == evaluator_input_id
    ]
    assert len(matches) == 1
    return matches[0]


def assert_lowercase_hex_id(value: object, prefix: str) -> None:
    assert type(value) is str
    assert value.startswith(prefix)
    assert HEX64.fullmatch(value[len(prefix):]) is not None


def assert_no_v1_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            assert key not in V1_KEYS
            assert_no_v1_keys(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_v1_keys(item)


# Task 3 prelude: the locked public surface is exactly the reviewed one.
LOCKED_ALL = (
    "TeamForecastEvaluationScope",
    "TeamForecastRunMetadata",
    "TeamForecastEvaluatorReceipt",
    "TeamForecastEvidenceReplayRecord",
    "TeamForecastBuildEnvelope",
    "build_team_forecast_build_envelope",
    "validate_team_forecast_build_envelope",
    "team_forecast_evaluation_scope_payload",
    "team_evidence_aggregation_id",
    "team_forecast_run_id",
    "team_forecast_evidence_id",
    "team_forecast_legacy_payload_sha256",
)
LOCKED_BUILDER_PARAMETERS = [
    "result", "aggregation_input", "config", "scope", "run_metadata",
    "evaluator_receipts", "legacy_forecast_packet", "legacy_evidence_packets",
]


def test_locked_public_surface_is_exact() -> None:
    assert tfe_envelope.__all__ == LOCKED_ALL
    for name in LOCKED_ALL:
        assert getattr(tfe_envelope, name, None) is not None
    builder_parameters = inspect.signature(build).parameters
    assert list(builder_parameters) == LOCKED_BUILDER_PARAMETERS
    assert builder_parameters["result"].kind in (
        inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    for name in LOCKED_BUILDER_PARAMETERS[1:]:
        assert builder_parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
    validator_parameters = inspect.signature(validate).parameters
    assert list(validator_parameters) == ["envelope", *LOCKED_BUILDER_PARAMETERS]
    assert validator_parameters["envelope"].kind in (
        inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    for name in LOCKED_BUILDER_PARAMETERS:
        assert validator_parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
    case = ready_case()
    envelope = build_case(case)
    resurfaced = tfe_envelope.team_forecast_evaluation_scope_payload(envelope)
    assert resurfaced == envelope.evaluation_scope_payload


# Task 2: receipt, scope, and run-metadata contracts.
def test_receipt_list_contains_accepted_and_rejected_inputs() -> None:
    case = ready_case()
    envelope = build_case(case)
    entries = envelope.evaluation_scope_payload["evaluator_receipts"]
    assert isinstance(entries, list)
    assert len(entries) == len(case.receipts) == 2
    by_id = {entry["evaluator_input_id"]: entry for entry in entries}
    accepted = accepted_receipts_of(case)[0]
    assert by_id[accepted.evaluator_input_id]["classification"] == "accepted"
    assert by_id[accepted.evaluator_input_id]["input_digest"] == accepted.input_digest
    assert by_id[REJECTED_INPUT_ID]["classification"] == "rejected"
    assert by_id[REJECTED_INPUT_ID]["input_digest"] == REJECTED_INPUT_DIGEST
    assert set(by_id) == {accepted.evaluator_input_id, REJECTED_INPUT_ID}


def test_receipts_are_canonically_sorted_and_unique() -> None:
    case = ready_case()
    envelope = build_case(case)
    entries = envelope.evaluation_scope_payload["evaluator_receipts"]
    ids = [entry["evaluator_input_id"] for entry in entries]
    assert ids == sorted(ids)
    assert set(ids) == {receipt.evaluator_input_id for receipt in case.receipts}
    # duplicate evaluator IDs fail closed
    original = accepted_receipts_of(case)[0]
    twin = accepted_receipt(
        case.records[0],
        evaluator_input_id=original.evaluator_input_id,
        input_digest=digest("evaluator-input:twin"),
    )
    with pytest.raises(ValueError):
        build_case(case, evaluator_receipts=(original, twin, rejected_receipt()))


def test_rejected_receipts_never_enter_node2_fragments() -> None:
    case = ready_case()
    envelope = build_case(case)
    scope_payload = envelope.evaluation_scope_payload
    receipt_bytes = canonical_json_bytes(scope_payload["evaluator_receipts"])
    assert b"evaluator:rejected" in receipt_bytes
    assert REJECTED_INPUT_DIGEST.encode("ascii") in receipt_bytes
    assert b"evaluator_declined" in receipt_bytes
    for fragment_name in ("node2_input", "node2_result", "node2_config"):
        fragment_bytes = canonical_json_bytes(scope_payload[fragment_name])
        assert b"evaluator:rejected" not in fragment_bytes
        assert REJECTED_INPUT_DIGEST.encode("ascii") not in fragment_bytes
        assert b"evaluator_declined" not in fragment_bytes
    # the Node 2 fragments stay byte-identical to the real predecessor payloads
    assert scope_payload["node2_config"] == team_evidence_aggregation_config_payload(case.config)
    assert scope_payload["node2_input"] == team_evidence_aggregation_input_payload(case.aggregation_input)
    assert scope_payload["node2_result"] == team_evidence_aggregation_payload(case.result)


def test_receipt_identity_and_digest_validation_fails_closed() -> None:
    case = ready_case()
    # an accepted identity that matches no supplied Node 2 record
    ghost = TeamForecastEvaluatorReceipt(
        evaluator_input_id="evaluator:ghost",
        input_digest=digest("evaluator-input:ghost"),
        receipt_time=RECEIPT_TIME,
        classification="accepted",
        accepted_record_identity=(
            "lineage:ghost", "capture:ghost", "evidence:ghost", "assessment:ghost"),
        reason_codes=("evaluator_submitted",),
    )
    with pytest.raises(ValueError):
        build_case(case, evaluator_receipts=(ghost, rejected_receipt()))
    # a supplied Node 2 record missing its accepted receipt
    with pytest.raises(ValueError):
        build_case(case, evaluator_receipts=(rejected_receipt(),))
    # an accepted receipt missing its four-field identity
    identity_less = accepted_receipt(
        case.records[0], evaluator_input_id="evaluator:identity-less", accepted_record_identity=None)
    with pytest.raises(ValueError):
        build_case(case, evaluator_receipts=(identity_less, rejected_receipt()))
    # a rejected receipt carrying a Node 2 record identity
    carrying = rejected_receipt(
        evaluator_input_id="evaluator:rejected-carrying",
        accepted_record_identity=record_identity(case.records[0]))
    with pytest.raises(ValueError):
        build_case(case, evaluator_receipts=(accepted_receipts_of(case)[0], carrying))
    # digest aliases across two distinct evaluator inputs
    two = make_case(mode="ready", second_record=True)
    first, second = accepted_receipts_of(two)
    aliased = accepted_receipt(
        two.records[1],
        evaluator_input_id=second.evaluator_input_id,
        input_digest=first.input_digest,
    )
    with pytest.raises(ValueError):
        build_case(two, evaluator_receipts=(first, aliased))
    # noncanonical digests and evaluator IDs
    with pytest.raises(ValueError):
        accepted_receipt(case.records[0], input_digest=digest("x").upper())
    with pytest.raises(ValueError):
        accepted_receipt(case.records[0], input_digest="0123")
    with pytest.raises(ValueError):
        accepted_receipt(case.records[0], evaluator_input_id="Not Canonical")


def test_scope_run_metadata_and_receipt_types_canonicalize_and_fail_closed() -> None:
    # canonical sorting inside the immutable types
    scope = make_scope()
    assert scope.domain_context == (("market_slug", MARKET_SLUG), ("team_id", "crypto_btc"))
    assert scope.provenance == ("clob:book/0xabc", "gamma:market/12345")
    metadata = make_metadata(completed_at=None)
    assert metadata.completed_at is None
    receipt = accepted_receipt(root_record("zeta"))
    assert receipt.reason_codes == ("evaluator_submitted",)
    unsorted_receipt = TeamForecastEvaluatorReceipt(
        evaluator_input_id="evaluator:unsorted",
        input_digest=digest("evaluator-input:unsorted"),
        receipt_time=RECEIPT_TIME,
        classification="accepted",
        accepted_record_identity=record_identity(root_record("unsorted")),
        reason_codes=("z_reason", "a_reason", "m_reason"),
    )
    assert unsorted_receipt.reason_codes == ("a_reason", "m_reason", "z_reason")
    assert rejected_receipt().reason_codes == ("evaluator_declined", "format_rejected")
    # false hard flags fail closed on every public Node 3 type
    for flags in ({"paper_only": False}, {"report_only": False}, {"readonly": False}):
        with pytest.raises(ValueError):
            make_scope(**flags)
        with pytest.raises(ValueError):
            make_metadata(**flags)
        with pytest.raises(ValueError):
            accepted_receipt(root_record("flags"), **flags)
        with pytest.raises(ValueError):
            rejected_receipt(**flags)
    # naive datetimes fail closed
    naive = datetime(2026, 7, 13, 9, 0, 0)
    with pytest.raises(ValueError):
        make_metadata(started_at=naive)
    with pytest.raises(ValueError):
        make_metadata(completed_at=naive)
    with pytest.raises(ValueError):
        accepted_receipt(root_record("naive"), receipt_time=naive)
    # noncanonical scope, run, and receipt strings fail closed
    with pytest.raises(ValueError):
        make_scope(scope_version="")
    with pytest.raises(ValueError):
        make_scope(provenance=(" bad ",))
    with pytest.raises(ValueError):
        make_scope(domain_context=(("k", "v"), ("k", "other")))
    with pytest.raises(ValueError):
        make_metadata(run_label=" padded ")
    with pytest.raises(ValueError):
        make_metadata(generator_version="")
    with pytest.raises(ValueError):
        make_metadata(prompt_version="\t")


# Task 3: validator-first ordering, config-digest handoff, fragments, and IDs.
def test_validator_is_called_before_any_scope_or_id_work(monkeypatch) -> None:
    case = ready_case()
    order: list[str] = []
    validator_calls: list[tuple[object, object, object]] = []

    def validator_spy(result_arg, *, aggregation_input, config):
        order.append("validator")
        validator_calls.append((result_arg, aggregation_input, config))
        return real_validate(result_arg, aggregation_input=aggregation_input, config=config)

    def config_payload_spy(config):
        order.append("config_payload")
        return team_evidence_aggregation_config_payload(config)

    def input_payload_spy(aggregation_input):
        order.append("input_payload")
        return team_evidence_aggregation_input_payload(aggregation_input)

    def result_payload_spy(result):
        order.append("result_payload")
        return team_evidence_aggregation_payload(result)

    monkeypatch.setattr(tfe_envelope, "validate_team_evidence_aggregation_result", validator_spy)
    monkeypatch.setattr(tfe_envelope, "team_evidence_aggregation_config_payload", config_payload_spy)
    monkeypatch.setattr(tfe_envelope, "team_evidence_aggregation_input_payload", input_payload_spy)
    monkeypatch.setattr(tfe_envelope, "team_evidence_aggregation_payload", result_payload_spy)
    envelope = build_case(case)
    assert order[0] == "validator"
    assert set(order[1:]) == {"config_payload", "input_payload", "result_payload"}
    assert validator_calls == [(case.result, case.aggregation_input, case.config)]
    assert_lowercase_hex_id(envelope.tea_id, "tea:v1:")

    # a failing Node 2 validator blocks every later operation
    order.clear()

    def failing_validator(result_arg, *, aggregation_input, config):
        order.append("validator")
        raise ValueError("upstream validation failed")

    monkeypatch.setattr(tfe_envelope, "validate_team_evidence_aggregation_result", failing_validator)
    with pytest.raises(ValueError, match="upstream validation failed"):
        build_case(case)
    assert order == ["validator"]


def test_config_digest_must_equal_result_config_digest(monkeypatch) -> None:
    case = ready_case()
    validator_calls: list[tuple[object, object, object]] = []
    fragment_calls: dict[str, list[object]] = {"config": [], "input": [], "result": []}

    def permissive_validator(result_arg, *, aggregation_input, config):
        validator_calls.append((result_arg, aggregation_input, config))
        return None

    def config_payload_spy(config):
        fragment_calls["config"].append(config)
        return team_evidence_aggregation_config_payload(config)

    def input_payload_spy(aggregation_input):
        fragment_calls["input"].append(aggregation_input)
        return team_evidence_aggregation_input_payload(aggregation_input)

    def result_payload_spy(result):
        fragment_calls["result"].append(result)
        return team_evidence_aggregation_payload(result)

    monkeypatch.setattr(tfe_envelope, "validate_team_evidence_aggregation_result", permissive_validator)
    monkeypatch.setattr(tfe_envelope, "team_evidence_aggregation_config_payload", config_payload_spy)
    monkeypatch.setattr(tfe_envelope, "team_evidence_aggregation_input_payload", input_payload_spy)
    monkeypatch.setattr(tfe_envelope, "team_evidence_aggregation_payload", result_payload_spy)
    # the gate passes when the digests are exactly equal
    assert team_evidence_aggregation_config_digest(case.config) == case.result.config_digest
    envelope = build_case(case)
    assert validator_calls == [(case.result, case.aggregation_input, case.config)]
    assert len(fragment_calls["config"]) == 1
    # a tampered config_digest raises at the handoff, after the validator and
    # before any Node 2 fragment is bound
    validator_calls.clear()
    for calls in fragment_calls.values():
        calls.clear()
    tampered_result = forge(case.result, {"config_digest": "0" * 64})
    with pytest.raises(ValueError, match="config_digest"):
        build(tampered_result, **validator_kwargs(case))  # type: ignore[arg-type]
    assert validator_calls == [(tampered_result, case.aggregation_input, case.config)]
    assert fragment_calls == {"config": [], "input": [], "result": []}


def test_three_node2_fragments_are_bound_once_and_separately(monkeypatch) -> None:
    case = ready_case()
    calls: dict[str, list[object]] = {"config": [], "input": [], "result": []}
    returned: dict[str, dict[str, object]] = {}

    def config_payload_spy(config):
        calls["config"].append(config)
        returned["config"] = team_evidence_aggregation_config_payload(config)
        return returned["config"]

    def input_payload_spy(aggregation_input):
        calls["input"].append(aggregation_input)
        returned["input"] = team_evidence_aggregation_input_payload(aggregation_input)
        return returned["input"]

    def result_payload_spy(result):
        calls["result"].append(result)
        returned["result"] = team_evidence_aggregation_payload(result)
        return returned["result"]

    monkeypatch.setattr(tfe_envelope, "team_evidence_aggregation_config_payload", config_payload_spy)
    monkeypatch.setattr(tfe_envelope, "team_evidence_aggregation_input_payload", input_payload_spy)
    monkeypatch.setattr(tfe_envelope, "team_evidence_aggregation_payload", result_payload_spy)
    envelope = build_case(case)
    # each predecessor payload function is called exactly once, with the
    # exact predecessor value
    assert calls["config"] == [case.config]
    assert calls["input"] == [case.aggregation_input]
    assert calls["result"] == [case.result]
    scope_payload = envelope.evaluation_scope_payload
    assert set(scope_payload) == SCOPE_PAYLOAD_KEYS
    # each fragment is a fresh, separate, unflattened copy of its payload
    for fragment_name, payload_name in (
        ("node2_config", "config"), ("node2_input", "input"), ("node2_result", "result"),
    ):
        fragment = scope_payload[fragment_name]
        assert fragment == returned[payload_name]
        assert fragment is not returned[payload_name]
    fragments = [scope_payload[name] for name in ("node2_config", "node2_input", "node2_result")]
    assert fragments[0] is not fragments[1]
    assert fragments[1] is not fragments[2]
    assert fragments[0] is not fragments[2]
    # the predecessor payload objects were never mutated by the build
    assert returned["config"] == team_evidence_aggregation_config_payload(case.config)
    assert returned["input"] == team_evidence_aggregation_input_payload(case.aggregation_input)
    assert returned["result"] == team_evidence_aggregation_payload(case.result)
    # the scope's own components bind the caller-supplied scope and metadata
    assert scope_payload["scope_version"] == case.scope.scope_version
    assert scope_payload["domain_context"] == {"team_id": "crypto_btc", "market_slug": MARKET_SLUG}
    assert scope_payload["provenance"] == ["clob:book/0xabc", "gamma:market/12345"]


def test_domain_separated_ids_are_prefixes_with_exact_preimages() -> None:
    case = ready_case()
    envelope = build_case(case)
    assert_lowercase_hex_id(envelope.tea_id, "tea:v1:")
    assert_lowercase_hex_id(envelope.tfr_id, "tfr:v1:")
    assert envelope.tea_id != envelope.tfr_id
    scope_payload = envelope.evaluation_scope_payload
    expected_tea = "tea:v1:" + sha256(
        b"tea:v1\x00" + canonical_json_bytes(scope_payload)).hexdigest()
    assert envelope.tea_id == expected_tea
    assert team_evidence_aggregation_id(scope_payload) == envelope.tea_id
    run_metadata_payload = scope_payload["run_metadata"]
    expected_tfr = "tfr:v1:" + sha256(b"tfr:v1\x00" + canonical_json_bytes({
        "tea_id": envelope.tea_id,
        "run_metadata": run_metadata_payload,
    })).hexdigest()
    assert envelope.tfr_id == expected_tfr
    assert team_forecast_run_id(envelope.tea_id, run_metadata_payload) == envelope.tfr_id
    for replay in envelope.evidence_replay_records:
        assert_lowercase_hex_id(replay.evidence_id, "tfe:v1:")
        assert replay.evidence_id not in (envelope.tea_id, envelope.tfr_id)
        accepted = accepted_receipts_of(case)[0]
        receipt_payload = receipt_entry_for(scope_payload, accepted.evaluator_input_id)
        expected_tfe = "tfe:v1:" + sha256(b"tfe:v1\x00" + canonical_json_bytes({
            "tea_id": envelope.tea_id,
            "receipt": receipt_payload,
            "legacy_payload_sha256": replay.legacy_payload_sha256,
        })).hexdigest()
        assert replay.evidence_id == expected_tfe
        assert team_forecast_evidence_id(
            envelope.tea_id, receipt_payload, replay.legacy_payload_sha256,
        ) == replay.evidence_id
    # identical complete inputs deterministically rebuild the same envelope
    assert build_case(case) == envelope


def test_core_digest_is_never_used_as_an_identity() -> None:
    case = ready_case()
    envelope_one = build_case(case)
    # the same validated result under a different scope changes every ID while
    # the core digest stays identical, so IDs are not core-digest functions
    alternate_scope = make_scope(
        domain_context=(("team_id", "crypto_btc"), ("market_slug", MARKET_SLUG), ("run", "second")),
        provenance=("clob:book/0xabc", "gamma:market/12345", "ws:market/live"),
    )
    envelope_two = build_case(case, scope=alternate_scope)
    assert case.result.core_digest == build_team_evidence_aggregation_result(
        case.aggregation_input, config=case.config).core_digest
    assert envelope_one.tea_id != envelope_two.tea_id
    assert envelope_one.tfr_id != envelope_two.tfr_id
    # the core digest occurs exactly once in the canonical scope bytes: only
    # as the validated field inside the full node2_result fragment
    scope_bytes = canonical_json_bytes(envelope_one.evaluation_scope_payload)
    assert scope_bytes.count(case.result.core_digest.encode("ascii")) == 1
    assert envelope_one.evaluation_scope_payload["node2_result"]["result"]["core_digest"] == (
        case.result.core_digest)


# Task 4: legacy projection and the ready-only packet boundary.
def test_legacy_payload_hash_is_byte_for_byte_compatible() -> None:
    # the existing signed-zero compatibility fixture from the Node 1 packet
    # tests, flowing through the exact historical encoding
    signed_zero = forecast_template(forecast_probability=d("-0.000000"))
    signed_zero_payload = team_forecast_packet_payload(signed_zero)
    assert signed_zero_payload["forecast_probability"] == "-0.000000"
    assert team_forecast_legacy_payload_sha256(signed_zero_payload) == sha256(
        historical_legacy_bytes(signed_zero_payload)).hexdigest()
    forecast_payload = team_forecast_packet_payload(forecast_template())
    assert team_forecast_legacy_payload_sha256(forecast_payload) == sha256(
        historical_legacy_bytes(forecast_payload)).hexdigest()
    evidence_payload = team_forecast_packet_payload(evidence_template(root_record("alpha")))
    assert team_forecast_legacy_payload_sha256(evidence_payload) == sha256(
        historical_legacy_bytes(evidence_payload)).hexdigest()
    # the envelope-stored replay records project the caller-supplied template
    # packets byte-for-byte: the tfe:v1 ID is computed from the template's
    # legacy hash, so the replay payload is the existing payload projection of
    # the template, never the reconstructed output packet
    case = ready_case()
    envelope = build_case(case)
    for replay, template in zip(
        envelope.evidence_replay_records, case.evidence_packets, strict=True,
    ):
        payload = team_forecast_packet_payload(template)
        assert replay.legacy_payload == payload
        assert replay.legacy_payload_sha256 == team_forecast_legacy_payload_sha256(payload)
        assert replay.legacy_payload_sha256 == sha256(historical_legacy_bytes(payload)).hexdigest()


def test_v1_keys_are_absent_from_legacy_forecast_and_evidence_payloads() -> None:
    case = ready_case()
    envelope = build_case(case)
    forecast_payload = team_forecast_packet_payload(envelope.legacy_forecast_packet)
    assert_no_v1_keys(forecast_payload)
    assert set(forecast_payload) == set(team_forecast_packet_payload(case.forecast_packet))
    for packet, template in zip(
        envelope.legacy_evidence_packets, case.evidence_packets, strict=True,
    ):
        payload = team_forecast_packet_payload(packet)
        assert_no_v1_keys(payload)
        assert set(payload) == set(team_forecast_packet_payload(template))
    for replay in envelope.evidence_replay_records:
        assert_no_v1_keys(replay.legacy_payload)
        assert set(replay.legacy_payload) == {"evidence_id", "team_id", "market_slug", "source_id",
            "source_type", "data_timestamp", "data_freshness_seconds", "evidence_type",
            "evidence_text", "weight", "reason_codes", "paper_only", "report_only", "readonly"}


def test_ready_result_builds_forecast_and_evidence_packets_with_v1_ids() -> None:
    case = ready_case()
    assert case.result.status == "ready"
    envelope = build_case(case)
    assert envelope.legacy_forecast_packet.forecast_id == envelope.tfr_id
    assert envelope.legacy_forecast_packet == replace(
        case.forecast_packet,
        forecast_id=envelope.tfr_id,
        forecast_probability=case.result.publishable_probability_yes,
    )
    accepted = accepted_receipts_of(case)
    assert len(envelope.legacy_evidence_packets) == len(accepted) == 1
    for packet, template, replay in zip(
        envelope.legacy_evidence_packets, case.evidence_packets,
        envelope.evidence_replay_records, strict=True,
    ):
        assert packet.evidence_id == replay.evidence_id
        assert packet == replace(template, evidence_id=replay.evidence_id)
    # a ready build with a mismatched evidence-template count fails closed
    with pytest.raises(ValueError):
        build_case(case, legacy_evidence_packets=())


@pytest.mark.parametrize("mode", ("watch", "blocked"))
def test_non_ready_result_produces_no_packets(mode: str) -> None:
    case = non_ready_case(mode)
    assert case.result.status == mode
    assert case.result.publishable_probability_yes is None
    envelope = build_case(case)
    assert envelope.legacy_forecast_packet is None
    assert envelope.legacy_evidence_packets == ()
    assert envelope.evidence_replay_records == ()
    assert_lowercase_hex_id(envelope.tea_id, "tea:v1:")
    assert_lowercase_hex_id(envelope.tfr_id, "tfr:v1:")


@pytest.mark.parametrize("mode", ("watch", "blocked"))
def test_non_ready_packet_arguments_fail_closed(mode: str) -> None:
    case = non_ready_case(mode)
    with pytest.raises(ValueError):
        build_case(case, legacy_forecast_packet=forecast_template())
    with pytest.raises(ValueError):
        build_case(case, legacy_evidence_packets=(evidence_template(case.records[0]),))
    with pytest.raises(ValueError):
        build_case(
            case,
            legacy_forecast_packet=forecast_template(),
            legacy_evidence_packets=(evidence_template(case.records[0]),),
        )


def test_ready_probability_matches_publishable_probability() -> None:
    case = ready_case()
    # the template carries a different probability on purpose
    assert case.forecast_packet.forecast_probability == d("0.500000")
    assert case.result.publishable_probability_yes == d("0.600000")
    envelope = build_case(case)
    assert envelope.legacy_forecast_packet.forecast_probability == d("0.600000")
    # a ceiling-bounded publishable probability flows through unchanged
    bounded = make_case(mode="ready", probability=d("0.950000"), template_probability=d("0.500000"))
    assert bounded.result.publishable_probability_yes == d("0.890000")
    assert "publish_probability_ceiling_applied" in bounded.result.reason_codes
    bounded_envelope = build_case(bounded)
    assert bounded_envelope.legacy_forecast_packet.forecast_probability == d("0.890000")


def test_evidence_replay_records_match_accepted_receipts() -> None:
    case = make_case(mode="ready", second_record=True)
    envelope = build_case(case)
    accepted = accepted_receipts_of(case)
    assert len(accepted) == 2
    assert len(envelope.evidence_replay_records) == len(accepted)
    replays = envelope.evidence_replay_records
    for replay, receipt in zip(replays, accepted, strict=True):
        assert replay.accepted_record_identity == receipt.accepted_record_identity
        entry = receipt_entry_for(envelope.evaluation_scope_payload, receipt.evaluator_input_id)
        expected_tfe = "tfe:v1:" + sha256(b"tfe:v1\x00" + canonical_json_bytes({
            "tea_id": envelope.tea_id,
            "receipt": entry,
            "legacy_payload_sha256": replay.legacy_payload_sha256,
        })).hexdigest()
        assert replay.evidence_id == expected_tfe
    # one unique replay ID per accepted receipt, never for the rejected input
    evidence_ids = [replay.evidence_id for replay in replays]
    assert len(set(evidence_ids)) == len(evidence_ids)
    assert len(evidence_ids) == sum(
        1 for receipt in case.receipts if receipt.classification == "accepted")
    for replay, template in zip(replays, case.evidence_packets, strict=True):
        assert replay.legacy_payload == team_forecast_packet_payload(template)


def test_validator_rejects_envelope_and_input_tampering() -> None:
    case = ready_case()
    envelope = build_case(case)
    kwargs = validator_kwargs(case)
    assert validate(envelope, result=case.result, **kwargs) is None  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        validate(
            forge(envelope, {"tea_id": "tea:v1:" + "f" * 64}),
            result=case.result, **kwargs)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        validate(
            forge(envelope, {"tfr_id": "tfr:v1:" + "f" * 64}),
            result=case.result, **kwargs)  # type: ignore[arg-type]
    missing_fragment = dict(envelope.evaluation_scope_payload)
    del missing_fragment["node2_input"]
    with pytest.raises(ValueError):
        validate(
            forge(envelope, {"evaluation_scope_payload": missing_fragment}),
            result=case.result, **kwargs)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        validate(
            forge(envelope, {"readonly": False}),
            result=case.result, **kwargs)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        validate(
            forge(envelope, {"legacy_forecast_packet": replace(
                case.forecast_packet, confidence=d("0.111111"))}),
            result=case.result, **kwargs)  # type: ignore[arg-type]
    tampered_hash = forge(
        envelope.evidence_replay_records[0], {"legacy_payload_sha256": "f" * 64})
    with pytest.raises(ValueError):
        validate(
            forge(envelope, {"evidence_replay_records": (tampered_hash,)}),
            result=case.result, **kwargs)  # type: ignore[arg-type]
    # input mismatches fail closed through rematerialization
    with pytest.raises(ValueError):
        validate(
            envelope, result=case.result,
            **{**kwargs, "evaluator_receipts": (rejected_receipt(),)})  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        validate(
            envelope, result=case.result,
            **{**kwargs, "legacy_evidence_packets": ()})  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        validate(
            envelope, result=case.result,
            **{**kwargs, "scope": make_scope(
                domain_context=(("team_id", "crypto_btc"),))})  # type: ignore[arg-type]
