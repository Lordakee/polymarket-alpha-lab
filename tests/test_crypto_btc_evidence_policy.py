"""Node 6 red/green tests for the review-pinned BTC evidence policy module.

Covers every pinned policy literal, requirement tuple ordering, fail-closed
unknown source/record/digest handling, duplicate rejection, selected-current
projection through a temporary Node 2A input contract, caller-record
preservation, policy status mapping, deterministic output under hostile
Decimal contexts, AST/spy proof that Node 2C, Node 3, packet, and
persistence surfaces are never touched, and frozen/slotted/final
dataclass plus constructor-bypass tamper checks.
"""
from __future__ import annotations

import ast
from dataclasses import MISSING, FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, DivisionByZero, Inexact, InvalidOperation, Overflow, Rounded, ROUND_UP, getcontext, setcontext
from pathlib import Path
from typing import get_type_hints

import pytest

import polymarket_alpha_lab.crypto_btc_evidence_policy as policy_module
from polymarket_alpha_lab import crypto_btc_evidence_catalog as catalog_module
from polymarket_alpha_lab import crypto_btc_evidence_registry as registry_module
from polymarket_alpha_lab import crypto_btc_evidence_resolution as resolution_module
from polymarket_alpha_lab.crypto_btc_evidence_policy import (
    CRYPTO_BTC_EVIDENCE_POLICY_CONFIG_VERSION,
    CryptoBtcEvidenceEvaluation,
    CryptoBtcEvidenceInput,
    build_crypto_btc_evidence_policy_config,
    evaluate_crypto_btc_evidence,
)
from polymarket_alpha_lab.crypto_btc_evidence_resolution import (
    CryptoBtcIncidentGates,
    CryptoBtcResolutionContract,
)
from polymarket_alpha_lab.team_evidence_aggregation import TeamEvidenceAggregationResult
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig,
    TeamEvidenceAggregationRecord,
    TeamEvidenceAssessmentRevision,
    TeamEvidenceCapture,
    TeamEvidenceCurrentRevisionSelection,
    TeamEvidenceRequirement,
    TeamEvidenceRevision,
    TeamEvidenceSourceLineage,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "crypto_btc_evidence_policy.py"
HARD_FLAGS = ("paper_only", "report_only", "readonly")
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
CLOSE_TIME = datetime(2027, 1, 1, 0, 0, tzinfo=UTC)
CAPTURED = datetime(2026, 7, 13, 10, 34, tzinfo=UTC)
RECORDED = datetime(2026, 7, 13, 10, 35, tzinfo=UTC)
ASSESSED = datetime(2026, 7, 13, 10, 36, tzinfo=UTC)
FRESHNESS_ANCHOR = datetime(2026, 7, 13, 10, 30, tzinfo=UTC)
BLOCKING_GATE_FLAGS = (
    "source_outage",
    "index_dislocation",
    "chain_reorg",
    "resolution_rule_change",
    "market_halt",
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

CATALOG_BY_SOURCE: dict[str, object] = {}
for _catalog_record in catalog_module.trusted_crypto_btc_source_catalog():
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
        "close_time": CLOSE_TIME,
        "resolution_catalog_record_id": record_id,
        "resolution_catalog_record_digest": record_digest,
        "contract_version": resolution_module.CRYPTO_BTC_RESOLUTION_CONTRACT_VERSION,
    }
    values.update(overrides)
    return CryptoBtcResolutionContract(**values)


def btc_record(
    source_id: str,
    *,
    suffix: str = "1",
    seed: int | None = None,
    previous_evidence: tuple[str, str] | None = None,
    previous_assessment: tuple[str, str] | None = None,
    requirement_ids: tuple[str, ...] | None = None,
) -> TeamEvidenceAggregationRecord:
    base = (SOURCE_SEEDS[source_id] if seed is None else seed) * 10
    lineage_id = f"lineage.{source_id}"
    lineage_digest = digest_hex(base + 1)
    content_digest = digest_hex(base + 3)
    evidence_id = f"evidence.{source_id}.{suffix}"
    evidence_digest = digest_hex(base + 4)
    assessment_id = f"assessment.{source_id}.{suffix}"
    assessment_digest = digest_hex(base + 5)
    capture = dict(
        capture_id=f"capture.{source_id}.{suffix}",
        capture_digest=digest_hex(base + 2),
        source_lineage_id=lineage_id,
        source_lineage_digest=lineage_digest,
        content_digest=content_digest,
        captured_at=CAPTURED,
    )
    evidence = dict(
        evidence_revision_id=evidence_id,
        evidence_revision_digest=evidence_digest,
        previous_evidence_revision_id=previous_evidence[0] if previous_evidence else None,
        previous_evidence_revision_digest=previous_evidence[1] if previous_evidence else None,
        source_lineage_id=lineage_id,
        source_lineage_digest=lineage_digest,
        content_digest=content_digest,
        requirement_ids=requirement_ids or (REQUIREMENT_BY_SOURCE[source_id],),
        freshness_anchor_at=FRESHNESS_ANCHOR,
        recorded_at=RECORDED,
    )
    assessment = dict(
        assessment_revision_id=assessment_id,
        assessment_revision_digest=assessment_digest,
        previous_assessment_revision_id=previous_assessment[0] if previous_assessment else None,
        previous_assessment_revision_digest=previous_assessment[1] if previous_assessment else None,
        evidence_revision_id=evidence_id,
        evidence_revision_digest=evidence_digest,
        assessed_at=ASSESSED,
        probability_yes=Decimal("0.640000"),
        requested_weight=Decimal("0.400000"),
        rationale_digest=digest_hex(base + 6),
        independence_key=f"independence.{source_id}.{suffix}",
        correlation_key=f"correlation.{source_id}",
    )
    return TeamEvidenceAggregationRecord(
        source_lineage=TeamEvidenceSourceLineage(
            source_lineage_id=lineage_id, source_lineage_digest=lineage_digest
        ),
        capture=TeamEvidenceCapture(**capture),
        evidence_revision=TeamEvidenceRevision(**evidence),
        assessment_revision=TeamEvidenceAssessmentRevision(**assessment),
    )


def btc_evidence_input(
    source_id: str,
    *,
    selected_current: bool = True,
    record: TeamEvidenceAggregationRecord | None = None,
    record_id: str | None = None,
    record_digest: str | None = None,
) -> CryptoBtcEvidenceInput:
    pinned_id, pinned_digest = catalog_binding(source_id)
    return CryptoBtcEvidenceInput(
        source_id=source_id,
        record_id=record_id if record_id is not None else pinned_id,
        record_digest=record_digest if record_digest is not None else pinned_digest,
        record=record if record is not None else btc_record(source_id),
        selected_current=selected_current,
    )


def evaluate_btc(
    evidence_inputs,
    *,
    resolution_contract=None,
    incident_gates=None,
    evaluated_at=None,
    **overrides: object,
) -> CryptoBtcEvidenceEvaluation:
    source_ids = tuple(dict.fromkeys(item.source_id for item in evidence_inputs)) or (
        "btc_spot_reference",
    )
    values: dict[str, object] = dict(
        condition_id=CONDITION_ID,
        market_slug=MARKET_SLUG,
        event_template=EVENT_TEMPLATE,
        resolution_contract=resolution_contract if resolution_contract is not None else btc_resolution_contract(),
        incident_gates=incident_gates if incident_gates is not None else gates(),
        evidence_inputs=tuple(evidence_inputs),
        evaluated_at=evaluated_at if evaluated_at is not None else catalog_overlap_evaluated_at(*source_ids),
    )
    values.update(overrides)
    return evaluate_crypto_btc_evidence(**values)


def default_inputs() -> tuple[CryptoBtcEvidenceInput, ...]:
    return tuple(btc_evidence_input(source_id) for source_id in EVIDENCE_SOURCES)


PINNED_CONFIG_FIELDS = (
    ("config_version", "crypto-btc-evidence-policy-v0", str),
    ("max_evidence_age_seconds", "900.000000", Decimal),
    ("max_capture_lag_seconds", "120.000000", Decimal),
    ("independence_group_weight_cap", "0.600000", Decimal),
    ("correlation_group_weight_cap", "0.750000", Decimal),
    ("max_requirement_assignments_per_evidence", 4, int),
    ("contradiction_no_probability_max", "0.350000", Decimal),
    ("contradiction_yes_probability_min", "0.650000", Decimal),
    ("contradiction_watch_score", "0.250000", Decimal),
    ("contradiction_block_score", "0.500000", Decimal),
    ("publish_probability_floor", "0.020000", Decimal),
    ("publish_probability_ceiling", "0.980000", Decimal),
    ("maximum_records", 64, int),
    ("maximum_requirements", 3, int),
    ("maximum_requirement_memberships", 12, int),
    ("maximum_witness_edges", 64, int),
)


def test_public_surface_is_exact() -> None:
    assert policy_module.__all__ == (
        "CryptoBtcEvidenceInput",
        "CryptoBtcEvidenceEvaluation",
        "build_crypto_btc_evidence_policy_config",
        "evaluate_crypto_btc_evidence",
    )
    assert policy_module.CRYPTO_BTC_EVIDENCE_POLICY_CONFIG_VERSION == "crypto-btc-evidence-policy-v0"
    assert policy_module.POLICY_GATE_STATUSES == ("blocked", "ready", "watch")
    assert policy_module.POLICY_REQUIREMENT_IDS == ("btc_derivatives", "btc_onchain", "btc_spot")


@pytest.mark.parametrize(("field_name", "literal", "kind"), PINNED_CONFIG_FIELDS)
def test_policy_config_pinned_literals(field_name: str, literal: object, kind: type) -> None:
    value = getattr(build_crypto_btc_evidence_policy_config(), field_name)
    assert type(value) is kind
    if kind is Decimal:
        assert str(value) == literal
        assert value.as_tuple().exponent == -6
    else:
        assert value == literal


def test_policy_config_requirement_tuple_is_exact_and_sorted() -> None:
    requirements = build_crypto_btc_evidence_policy_config().requirements
    assert tuple(
        (
            requirement.requirement_id,
            requirement.minimum_witness_count,
            str(requirement.minimum_effective_weight),
            requirement.unmet_status,
        )
        for requirement in requirements
    ) == (
        ("btc_derivatives", 1, "0.200000", "watch"),
        ("btc_onchain", 1, "0.150000", "watch"),
        ("btc_spot", 1, "0.300000", "blocked"),
    )
    assert all(type(requirement) is TeamEvidenceRequirement for requirement in requirements)
    assert tuple(requirement.requirement_id for requirement in requirements) == tuple(
        sorted(requirement.requirement_id for requirement in requirements)
    )


def test_policy_config_within_node2a_hard_maxima_and_repeatable() -> None:
    first = build_crypto_btc_evidence_policy_config()
    second = build_crypto_btc_evidence_policy_config()
    assert first == second
    assert first is not second
    assert type(first) is TeamEvidenceAggregationConfig
    assert first.maximum_records <= 128
    assert first.maximum_requirements <= 32
    assert first.maximum_requirement_memberships <= 1024
    assert first.maximum_witness_edges <= 256
    assert first.max_requirement_assignments_per_evidence <= 32
    assert len(first.requirements) == first.maximum_requirements == 3
    with pytest.raises(FrozenInstanceError):
        first.maximum_records = 65  # type: ignore[misc]
    assert not hasattr(first, "__dict__")
    for flag in HARD_FLAGS:
        assert getattr(first, flag) is True


def test_evidence_input_fields_have_no_vintage_or_tier_override() -> None:
    names = tuple(field.name for field in fields(CryptoBtcEvidenceInput))
    assert names == ("source_id", "record_id", "record_digest", "record", "selected_current") + HARD_FLAGS
    assert not any("vintage" in name or "tier" in name for name in names)
    hints = get_type_hints(CryptoBtcEvidenceInput)
    assert hints["source_id"] is str and hints["record_id"] is str and hints["record_digest"] is str
    assert hints["record"] is TeamEvidenceAggregationRecord and hints["selected_current"] is bool
    for field_entry in fields(CryptoBtcEvidenceInput):
        assert field_entry.default is (True if field_entry.name in HARD_FLAGS else MISSING)


def test_evidence_input_rejects_invalid_values() -> None:
    good = btc_evidence_input("btc_spot_reference")
    with pytest.raises(ValueError, match="source_id"):
        CryptoBtcEvidenceInput(**{**_input_values(good), "source_id": "BTC_SPOT"})
    with pytest.raises(ValueError, match="source_id"):
        CryptoBtcEvidenceInput(**{**_input_values(good), "source_id": ""})
    with pytest.raises(ValueError, match="record_id"):
        CryptoBtcEvidenceInput(**{**_input_values(good), "record_id": "record id with spaces"})
    with pytest.raises(ValueError, match="record_digest"):
        CryptoBtcEvidenceInput(**{**_input_values(good), "record_digest": "F" * 64})
    with pytest.raises(ValueError, match="record_digest"):
        CryptoBtcEvidenceInput(**{**_input_values(good), "record_digest": "abc"})
    with pytest.raises(ValueError, match="record"):
        CryptoBtcEvidenceInput(**{**_input_values(good), "record": object()})
    with pytest.raises(ValueError, match="selected_current"):
        CryptoBtcEvidenceInput(**{**_input_values(good), "selected_current": 1})
    with pytest.raises(ValueError, match="paper_only"):
        CryptoBtcEvidenceInput(**{**_input_values(good), "paper_only": False})


def _input_values(item: CryptoBtcEvidenceInput) -> dict[str, object]:
    return {name: getattr(item, name) for name in CryptoBtcEvidenceInput.__slots__}


def test_public_dataclasses_frozen_slotted_final() -> None:
    for cls in (CryptoBtcEvidenceInput, CryptoBtcEvidenceEvaluation):
        assert cls.__dataclass_params__.frozen is True
        assert cls.__slots__ is not None
        with pytest.raises(TypeError):
            class _Subclass(cls):  # type: ignore[misc, no-redef]
                pass
    item = btc_evidence_input("btc_spot_reference")
    with pytest.raises(FrozenInstanceError):
        item.selected_current = False  # type: ignore[misc]
    assert not hasattr(item, "__dict__")


def test_evaluation_fields_defaults_and_types() -> None:
    names = tuple(field.name for field in fields(CryptoBtcEvidenceEvaluation))
    assert names == (
        "evaluated_at",
        "status",
        "records",
        "current_selections",
        "config",
        "resolution_assessment",
        "reason_codes",
    ) + HARD_FLAGS
    hints = get_type_hints(CryptoBtcEvidenceEvaluation)
    assert hints["status"] is str
    assert hints["records"] == tuple[TeamEvidenceAggregationRecord, ...]
    assert hints["current_selections"] == tuple[TeamEvidenceCurrentRevisionSelection, ...]
    assert hints["config"] is TeamEvidenceAggregationConfig
    assert hints["resolution_assessment"] is resolution_module.CryptoBtcResolutionAssessment
    assert hints["reason_codes"] == tuple[str, ...]
    for field_entry in fields(CryptoBtcEvidenceEvaluation):
        assert field_entry.default is (True if field_entry.name in HARD_FLAGS else MISSING)


def test_evaluation_constructor_validates_invariants() -> None:
    baseline = evaluate_btc(default_inputs())
    values = {name: getattr(baseline, name) for name in CryptoBtcEvidenceEvaluation.__slots__}
    assert CryptoBtcEvidenceEvaluation(**values) == baseline
    with pytest.raises(ValueError, match="status"):
        CryptoBtcEvidenceEvaluation(**{**values, "status": "passed"})
    with pytest.raises(ValueError, match="sorted"):
        CryptoBtcEvidenceEvaluation(**{**values, "records": tuple(reversed(values["records"]))})
    with pytest.raises(ValueError, match="duplicate"):
        CryptoBtcEvidenceEvaluation(**{**values, "records": (*values["records"], values["records"][0])})
    unresolvable = TeamEvidenceCurrentRevisionSelection(
        evidence_revision_id="evidence.unknown.1",
        evidence_revision_digest=digest_hex(901),
        assessment_revision_id="assessment.unknown.1",
        assessment_revision_digest=digest_hex(902),
    )
    with pytest.raises(ValueError, match="resolve"):
        CryptoBtcEvidenceEvaluation(**{**values, "current_selections": (unresolvable,)})
    with pytest.raises(ValueError, match="config_version"):
        CryptoBtcEvidenceEvaluation(**{**values, "config": replace(values["config"], config_version="other-policy-v0")})
    with pytest.raises(ValueError, match="requirements"):
        CryptoBtcEvidenceEvaluation(**{**values, "config": replace(values["config"], requirements=())})
    with pytest.raises(ValueError, match="resolution_assessment"):
        CryptoBtcEvidenceEvaluation(**{**values, "resolution_assessment": values["config"]})
    with pytest.raises(ValueError, match="reason_codes"):
        CryptoBtcEvidenceEvaluation(**{**values, "reason_codes": ()})
    with pytest.raises(ValueError, match="reason_codes"):
        CryptoBtcEvidenceEvaluation(**{**values, "reason_codes": ("policy.ready", "policy.ready")})
    with pytest.raises(ValueError, match="reason_codes"):
        CryptoBtcEvidenceEvaluation(**{**values, "reason_codes": ("not.a.closed.code", "policy.ready")})
    with pytest.raises(ValueError, match="terminal"):
        CryptoBtcEvidenceEvaluation(**{**values, "reason_codes": ("policy.blocked",)})


def test_evaluate_ready_projects_canonical_records_and_selections() -> None:
    inputs = default_inputs()
    evaluated_at = catalog_overlap_evaluated_at(*EVIDENCE_SOURCES)
    evaluation = evaluate_btc(inputs, evaluated_at=evaluated_at)
    assert evaluation.status == "ready"
    assert evaluation.evaluated_at == evaluated_at
    assert evaluation.evaluated_at.tzinfo is UTC
    assert evaluation.config == build_crypto_btc_evidence_policy_config()
    assert evaluation.config.config_version == CRYPTO_BTC_EVIDENCE_POLICY_CONFIG_VERSION
    assert not isinstance(evaluation, TeamEvidenceAggregationResult)
    assert tuple(
        record.assessment_revision.assessment_revision_id for record in evaluation.records
    ) == tuple(sorted(record.assessment_revision.assessment_revision_id for record in evaluation.records))
    assert tuple(record.source_lineage.source_lineage_id for record in evaluation.records) == (
        "lineage.btc_derivatives_reference",
        "lineage.btc_onchain_reference",
        "lineage.btc_spot_reference",
    )
    assert tuple(
        selection.evidence_revision_id for selection in evaluation.current_selections
    ) == (
        "evidence.btc_derivatives_reference.1",
        "evidence.btc_onchain_reference.1",
        "evidence.btc_spot_reference.1",
    )
    for selection in evaluation.current_selections:
        matches = [
            record
            for record in evaluation.records
            if record.evidence_revision.evidence_revision_id == selection.evidence_revision_id
            and record.evidence_revision.evidence_revision_digest == selection.evidence_revision_digest
            and record.assessment_revision.assessment_revision_id == selection.assessment_revision_id
            and record.assessment_revision.assessment_revision_digest == selection.assessment_revision_digest
        ]
        assert len(matches) == 1
    assert evaluation.reason_codes[-1] == "policy.ready"
    assert all(
        f"resolution.{code}" in evaluation.reason_codes
        for code in evaluation.resolution_assessment.reason_codes
    )
    for flag in HARD_FLAGS:
        assert getattr(evaluation, flag) is True


def test_evaluate_watch_only_for_derivatives_degradation() -> None:
    evaluation = evaluate_btc(default_inputs(), incident_gates=gates(derivatives_feed_degraded=True))
    assert evaluation.status == "watch"
    assert evaluation.reason_codes[-1] == "policy.watch"
    assert len(evaluation.records) == 3
    assert evaluation.resolution_assessment.resolution_contract_status == "watch"
    assert "resolution.incident_derivatives_feed_degraded" in evaluation.reason_codes


@pytest.mark.parametrize("blocking_flag", BLOCKING_GATE_FLAGS)
def test_evaluate_blocked_for_each_blocking_incident(blocking_flag: str) -> None:
    evaluation = evaluate_btc(default_inputs(), incident_gates=gates(**{blocking_flag: True}))
    assert evaluation.status == "blocked"
    assert evaluation.reason_codes[-1] == "policy.blocked"
    assert evaluation.resolution_assessment.resolution_contract_status == "blocked"
    assert "policy.watch" not in evaluation.reason_codes


def test_evaluate_blocked_incident_takes_precedence_over_watch() -> None:
    evaluation = evaluate_btc(
        default_inputs(),
        incident_gates=gates(derivatives_feed_degraded=True, market_halt=True),
    )
    assert evaluation.status == "blocked"
    assert evaluation.reason_codes[-1] == "policy.blocked"


def test_evaluate_unknown_source_fails_closed() -> None:
    spot_id, spot_digest = catalog_binding("btc_spot_reference")
    unknown = CryptoBtcEvidenceInput(
        source_id="btc_unapproved_reference",
        record_id=spot_id,
        record_digest=spot_digest,
        record=btc_record("btc_spot_reference"),
        selected_current=True,
    )
    evaluation = evaluate_btc(
        (unknown,),
        evaluated_at=catalog_overlap_evaluated_at("btc_spot_reference"),
    )
    assert evaluation.status == "blocked"
    assert "evidence.source.unapproved" in evaluation.reason_codes
    assert evaluation.records == ()
    assert evaluation.current_selections == ()


def test_evaluate_unknown_record_and_digest_fail_closed() -> None:
    unknown_record = btc_evidence_input("btc_spot_reference", record_id="record.unknown.value.v0")
    evaluation = evaluate_btc((unknown_record,))
    assert evaluation.status == "blocked"
    assert "evidence.record.unresolved" in evaluation.reason_codes
    wrong_digest = btc_evidence_input("btc_spot_reference", record_digest=digest_hex(999))
    evaluation = evaluate_btc((wrong_digest,))
    assert evaluation.status == "blocked"
    assert "evidence.record.unresolved" in evaluation.reason_codes
    assert evaluation.records == ()


def test_evaluate_expired_catalog_record_fails_closed() -> None:
    expired_at = CATALOG_BY_SOURCE["btc_spot_reference"].valid_until + timedelta(seconds=1)
    evaluation = evaluate_btc((btc_evidence_input("btc_spot_reference"),), evaluated_at=expired_at)
    assert evaluation.status == "blocked"
    assert "evidence.record.unresolved" in evaluation.reason_codes


def test_evaluate_source_family_mismatch_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    entry = registry_module.require_approved_crypto_btc_source("btc_derivatives_reference")
    real_resolve = policy_module.resolve_trusted_crypto_btc_source_record

    def mismatched(source_id: str, record_id: str, record_digest: str, *, evaluated_at: datetime):
        resolved = real_resolve(source_id, record_id, record_digest, evaluated_at=evaluated_at)
        forged = object.__new__(type(resolved))
        for name in type(resolved).__slots__:
            object.__setattr__(forged, name, getattr(resolved, name))
        object.__setattr__(forged, "source_family", f"{entry.source_family}-family-mismatch-probe")
        return forged

    monkeypatch.setattr(policy_module, "resolve_trusted_crypto_btc_source_record", mismatched)
    evaluation = evaluate_btc((btc_evidence_input("btc_derivatives_reference"),))
    assert evaluation.status == "blocked"
    assert "evidence.source_family.mismatch" in evaluation.reason_codes


def test_evaluate_duplicate_record_and_digest_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    duplicated = (btc_evidence_input("btc_spot_reference"), btc_evidence_input("btc_spot_reference"))
    evaluation = evaluate_btc(duplicated)
    assert evaluation.status == "blocked"
    assert "evidence.record.duplicate" in evaluation.reason_codes
    assert "evidence.record_digest.duplicate" in evaluation.reason_codes

    real_resolve = policy_module.resolve_trusted_crypto_btc_source_record
    spot_id, spot_digest = catalog_binding("btc_spot_reference")

    def aliased(source_id: str, record_id: str, record_digest: str, *, evaluated_at: datetime):
        return real_resolve("btc_spot_reference", spot_id, spot_digest, evaluated_at=evaluated_at)

    monkeypatch.setattr(policy_module, "resolve_trusted_crypto_btc_source_record", aliased)
    aliased_inputs = (
        btc_evidence_input("btc_spot_reference"),
        btc_evidence_input(
            "btc_spot_reference",
            record_id="record.alias.spot.v0",
            record=btc_record("btc_spot_reference", suffix="9", seed=19),
            selected_current=False,
        ),
    )
    evaluation = evaluate_btc(aliased_inputs)
    assert evaluation.status == "blocked"
    assert "evidence.record_digest.duplicate" in evaluation.reason_codes
    assert "evidence.record.duplicate" not in evaluation.reason_codes


def test_evaluate_selected_current_projection() -> None:
    inputs = (
        btc_evidence_input("btc_derivatives_reference", selected_current=True),
        btc_evidence_input("btc_onchain_reference", selected_current=False),
        btc_evidence_input("btc_spot_reference", selected_current=True),
    )
    evaluation = evaluate_btc(inputs)
    assert evaluation.status == "ready"
    assert len(evaluation.records) == 3
    assert tuple(
        selection.evidence_revision_id for selection in evaluation.current_selections
    ) == ("evidence.btc_derivatives_reference.1", "evidence.btc_spot_reference.1")
    no_selections = evaluate_btc(
        tuple(btc_evidence_input(source_id, selected_current=False) for source_id in EVIDENCE_SOURCES)
    )
    assert no_selections.status == "ready"
    assert no_selections.current_selections == ()
    assert len(no_selections.records) == 3


def _alias_resolver(
    monkeypatch: pytest.MonkeyPatch, aliases: dict[str, tuple[str, str, str]]
) -> None:
    """Simulate additional trusted catalog records by aliasing record IDs.

    The real catalog pins one live record per evidence source, so Node 2A
    multi-record paths need aliased bindings that resolve to the same
    trusted record while keeping distinct record IDs and digests.
    """

    real_resolve = policy_module.resolve_trusted_crypto_btc_source_record

    def resolver(source_id: str, record_id: str, record_digest: str, *, evaluated_at: datetime):
        target = aliases.get(record_id)
        if target is not None:
            return real_resolve(target[0], target[1], target[2], evaluated_at=evaluated_at)
        return real_resolve(source_id, record_id, record_digest, evaluated_at=evaluated_at)

    monkeypatch.setattr(policy_module, "resolve_trusted_crypto_btc_source_record", resolver)


def test_evaluate_node2a_one_current_per_lineage_violation_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spot_id, spot_digest = catalog_binding("btc_spot_reference")
    _alias_resolver(
        monkeypatch,
        {"record.alias.spot.second": ("btc_spot_reference", spot_id, spot_digest)},
    )
    first = btc_record("btc_spot_reference")
    second = btc_record(
        "btc_spot_reference",
        suffix="2",
        seed=11,
        previous_evidence=(
            first.evidence_revision.evidence_revision_id,
            first.evidence_revision.evidence_revision_digest,
        ),
        previous_assessment=(
            first.assessment_revision.assessment_revision_id,
            first.assessment_revision.assessment_revision_digest,
        ),
    )
    inputs = (
        CryptoBtcEvidenceInput(source_id="btc_spot_reference", record_id=spot_id, record_digest=spot_digest, record=first, selected_current=True),
        CryptoBtcEvidenceInput(source_id="btc_spot_reference", record_id="record.alias.spot.second", record_digest=digest_hex(331), record=second, selected_current=True),
    )
    evaluation = evaluate_btc(inputs)
    assert evaluation.status == "blocked"
    assert "evidence.node2a_contract.violation" in evaluation.reason_codes
    assert evaluation.records == ()


def test_evaluate_node2a_requirement_overflow_fails_closed() -> None:
    record = btc_record(
        "btc_spot_reference",
        requirement_ids=("btc_derivatives", "btc_onchain", "btc_spot", "test.extra.one", "test.extra.two"),
    )
    evaluation = evaluate_btc((btc_evidence_input("btc_spot_reference", record=record),))
    assert evaluation.status == "blocked"
    assert "evidence.node2a_contract.violation" in evaluation.reason_codes


def test_evaluate_node2a_chain_fork_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    derivatives_id, derivatives_digest = catalog_binding("btc_derivatives_reference")
    _alias_resolver(
        monkeypatch,
        {
            "record.alias.derivatives.left": ("btc_derivatives_reference", derivatives_id, derivatives_digest),
            "record.alias.derivatives.right": ("btc_derivatives_reference", derivatives_id, derivatives_digest),
        },
    )
    first = btc_record("btc_derivatives_reference")
    forked_previous = (
        first.evidence_revision.evidence_revision_id,
        first.evidence_revision.evidence_revision_digest,
    )
    forked_assessment_previous = (
        first.assessment_revision.assessment_revision_id,
        first.assessment_revision.assessment_revision_digest,
    )
    left = btc_record(
        "btc_derivatives_reference",
        suffix="2a",
        seed=21,
        previous_evidence=forked_previous,
        previous_assessment=forked_assessment_previous,
    )
    right = btc_record(
        "btc_derivatives_reference",
        suffix="2b",
        seed=22,
        previous_evidence=forked_previous,
        previous_assessment=forked_assessment_previous,
    )
    inputs = (
        CryptoBtcEvidenceInput(source_id="btc_derivatives_reference", record_id=derivatives_id, record_digest=derivatives_digest, record=first, selected_current=True),
        CryptoBtcEvidenceInput(source_id="btc_derivatives_reference", record_id="record.alias.derivatives.left", record_digest=digest_hex(331), record=left, selected_current=False),
        CryptoBtcEvidenceInput(source_id="btc_derivatives_reference", record_id="record.alias.derivatives.right", record_digest=digest_hex(332), record=right, selected_current=False),
    )
    evaluation = evaluate_btc(inputs)
    assert evaluation.status == "blocked"
    assert "evidence.node2a_contract.violation" in evaluation.reason_codes
    assert evaluation.records == ()
    assert evaluation.current_selections == ()


def test_evaluate_preserves_caller_records() -> None:
    inputs = default_inputs()
    originals = [item.record for item in inputs]
    twins = [btc_record(source_id) for source_id in EVIDENCE_SOURCES]
    evaluation = evaluate_btc(inputs)
    assert all(original == twin for original, twin in zip(originals, twins))
    assert {id(record) for record in evaluation.records} == {id(original) for original in originals}
    assert all(original == twin for original, twin in zip(originals, twins))


def test_evaluate_deterministic_and_input_order_independent() -> None:
    inputs = default_inputs()
    first = evaluate_btc(inputs)
    second = evaluate_btc(inputs)
    reversed_run = evaluate_btc(tuple(reversed(inputs)))
    assert first == second
    assert first == reversed_run
    assert len(set(first.reason_codes)) == len(first.reason_codes)
    assert first.reason_codes == second.reason_codes == reversed_run.reason_codes


def test_evaluate_empty_evidence_inputs_is_ready_with_note() -> None:
    evaluation = evaluate_btc(())
    assert evaluation.status == "ready"
    assert evaluation.records == ()
    assert evaluation.current_selections == ()
    assert "evidence.inputs.empty" in evaluation.reason_codes
    assert evaluation.reason_codes[-1] == "policy.ready"


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("condition_id", ""),
        ("condition_id", " padded "),
        ("market_slug", 7),
        ("event_template", None),
        ("evidence_inputs", ["not-a-tuple"]),
        ("evidence_inputs", ("not-an-input",)),
        ("evaluated_at", datetime(2026, 7, 13, 12, 0)),
        ("evaluated_at", "2026-07-13T12:00:00+00:00"),
    ),
)
def test_evaluate_structural_argument_errors_raise(field_name: str, bad_value: object) -> None:
    values: dict[str, object] = dict(
        condition_id=CONDITION_ID,
        market_slug=MARKET_SLUG,
        event_template=EVENT_TEMPLATE,
        resolution_contract=btc_resolution_contract(),
        incident_gates=gates(),
        evidence_inputs=default_inputs(),
        evaluated_at=catalog_overlap_evaluated_at(*EVIDENCE_SOURCES),
    )
    values[field_name] = bad_value
    with pytest.raises(ValueError):
        evaluate_crypto_btc_evidence(**values)


def test_evaluate_rejects_wrong_contract_and_gate_types() -> None:
    with pytest.raises(ValueError, match="resolution_contract"):
        evaluate_btc(default_inputs(), resolution_contract=gates())
    with pytest.raises(ValueError, match="incident_gates"):
        evaluate_btc(default_inputs(), incident_gates=btc_resolution_contract())


def test_constructor_bypassed_input_tampering_fails_closed() -> None:
    good = btc_evidence_input("btc_spot_reference")
    tampered = object.__new__(CryptoBtcEvidenceInput)
    for name in CryptoBtcEvidenceInput.__slots__:
        object.__setattr__(tampered, name, getattr(good, name))
    object.__setattr__(tampered, "record_digest", "F" * 64)
    evaluation = evaluate_btc((tampered,))
    assert evaluation.status == "blocked"
    assert "evidence.input.invalid" in evaluation.reason_codes
    assert evaluation.records == ()

    tampered_flags = object.__new__(CryptoBtcEvidenceInput)
    for name in CryptoBtcEvidenceInput.__slots__:
        object.__setattr__(tampered_flags, name, getattr(good, name))
    object.__setattr__(tampered_flags, "selected_current", 1)
    evaluation = evaluate_btc((tampered_flags,))
    assert evaluation.status == "blocked"
    assert "evidence.input.invalid" in evaluation.reason_codes


def _context_snapshot(context: Context) -> tuple[object, ...]:
    return (
        context.prec,
        context.rounding,
        context.Emin,
        context.Emax,
        context.capitals,
        context.clamp,
        frozenset(context.traps),
        frozenset(context.flags),
    )


def test_deterministic_under_hostile_decimal_context() -> None:
    inputs = default_inputs()
    baseline_config = build_crypto_btc_evidence_policy_config()
    baseline_evaluation = evaluate_btc(inputs)
    hostile = Context(
        prec=3,
        rounding=ROUND_UP,
        Emin=-9,
        Emax=9,
        traps=[InvalidOperation, DivisionByZero, Overflow, Inexact, Rounded],
    )
    hostile_snapshot = _context_snapshot(hostile)
    active_before = getcontext()
    active_snapshot = _context_snapshot(active_before)
    setcontext(hostile)
    try:
        hostile_config = build_crypto_btc_evidence_policy_config()
        hostile_evaluation = evaluate_btc(inputs)
    finally:
        setcontext(active_before)
    assert hostile_config == baseline_config
    assert hostile_evaluation == baseline_evaluation
    assert _context_snapshot(hostile) == hostile_snapshot
    assert _context_snapshot(getcontext()) == active_snapshot
    assert getcontext() is active_before


def _module_tree() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"), filename=str(MODULE_PATH))


def _imported_modules(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
    return names


IMPORT_ALLOWLIST = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "re",
    "typing",
    "polymarket_alpha_lab.crypto_btc_evidence_catalog",
    "polymarket_alpha_lab.crypto_btc_evidence_registry",
    "polymarket_alpha_lab.crypto_btc_evidence_resolution",
    "polymarket_alpha_lab.team_evidence_aggregation_types",
}
FORBIDDEN_MODULE_COMPONENTS = frozenset((
    "db", "store", "stores", "supabase", "psycopg", "persist", "persistence", "sqlite", "redis",
    "mongo", "http", "socket", "os", "sys", "subprocess", "requests", "urllib", "secrets", "crypto",
))


def test_module_import_allowlist_is_exact() -> None:
    assert _imported_modules(_module_tree()) == IMPORT_ALLOWLIST


def test_module_never_imports_node2c_node3_packets_or_persistence() -> None:
    imported = _imported_modules(_module_tree())
    assert "polymarket_alpha_lab.team_evidence_aggregation" not in imported
    assert "polymarket_alpha_lab.team_forecast_build_envelope" not in imported
    assert "polymarket_alpha_lab.team_forecast_packet" not in imported
    for module in imported:
        components = module.split(".")
        assert not FORBIDDEN_MODULE_COMPONENTS.intersection(components), module


def test_module_has_no_floats_forbidden_calls_or_ambient_clock() -> None:
    forbidden_names = frozenset((
        "open", "print", "input", "eval", "exec", "compile", "float", "hash", "__import__",
        "random", "setcontext", "getcontext", "now", "utcnow", "today",
    ))
    forbidden_attributes = (forbidden_names | {"time", "timestamp", "total_seconds"}) - {"compile"}
    for node in ast.walk(_module_tree()):
        if isinstance(node, ast.Constant) and type(node.value) is float:
            pytest.fail("module must not contain float literals")
        if isinstance(node, ast.Attribute) and node.attr in ("now", "utcnow", "today"):
            pytest.fail(f"module must not access the ambient clock: {node.attr}")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_names, node.func.id
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_attributes, node.func.attr


def test_module_binds_sibling_functions_directly() -> None:
    assert policy_module.require_approved_crypto_btc_source is registry_module.require_approved_crypto_btc_source
    assert policy_module.resolve_trusted_crypto_btc_source_record is catalog_module.resolve_trusted_crypto_btc_source_record
    assert policy_module.check_crypto_btc_resolution_contract is resolution_module.check_crypto_btc_resolution_contract


def test_evaluate_never_calls_node2c_node3_or_packets(monkeypatch: pytest.MonkeyPatch) -> None:
    import polymarket_alpha_lab.team_evidence_aggregation as node2c_module
    import polymarket_alpha_lab.team_forecast_build_envelope as envelope_module
    import polymarket_alpha_lab.team_forecast_packet as packet_module

    forbidden: list[str] = []

    def bomb(name: str):
        def _bomb(*args: object, **kwargs: object) -> None:
            forbidden.append(name)
            raise AssertionError(f"forbidden call: {name}")

        return _bomb

    monkeypatch.setattr(node2c_module, "build_team_evidence_aggregation_result", bomb("node2c.build"))
    monkeypatch.setattr(node2c_module, "validate_team_evidence_aggregation_result", bomb("node2c.validate"))
    monkeypatch.setattr(envelope_module, "build_team_forecast_build_envelope", bomb("envelope.build"))
    monkeypatch.setattr(packet_module, "TeamForecastPacket", bomb("packet.forecast"))
    monkeypatch.setattr(packet_module, "TeamForecastEvidencePacket", bomb("packet.evidence"))
    evaluation = evaluate_btc(default_inputs())
    assert evaluation.status == "ready"
    assert forbidden == []


def test_evaluate_calls_identity_bound_resolution_checker_once(monkeypatch: pytest.MonkeyPatch) -> None:
    real_checker = policy_module.check_crypto_btc_resolution_contract
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def recorder(*args: object, **kwargs: object):
        calls.append((args, kwargs))
        return real_checker(*args, **kwargs)

    monkeypatch.setattr(policy_module, "check_crypto_btc_resolution_contract", recorder)
    contract = btc_resolution_contract()
    inputs = default_inputs()
    evaluated_at = catalog_overlap_evaluated_at(*EVIDENCE_SOURCES)
    evaluation = evaluate_btc(inputs, resolution_contract=contract, evaluated_at=evaluated_at)
    assert evaluation.status == "ready"
    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args[0] is contract
    assert kwargs["condition_id"] == CONDITION_ID
    assert kwargs["market_slug"] == MARKET_SLUG
    assert kwargs["event_template"] == EVENT_TEMPLATE
    assert kwargs["incident_gates"] is not None
    assert kwargs["evaluated_at"] == evaluated_at
