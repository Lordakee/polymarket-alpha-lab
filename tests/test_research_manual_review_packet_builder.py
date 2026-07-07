from __future__ import annotations

import ast
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_manual_review_packet_builder as api
from polymarket_alpha_lab.research_manual_review_packet_builder import (
    ResearchManualReviewConflictState,
    ResearchManualReviewCostFrictionState,
    ResearchManualReviewEvidenceState,
    ResearchManualReviewNextStep,
    ResearchManualReviewPacket,
    ResearchManualReviewPacketPolicy,
    ResearchManualReviewPublicPayloadItem,
    ResearchManualReviewSettlementRiskState,
    build_research_manual_review_packet,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence(**overrides: object) -> ResearchManualReviewEvidenceState:
    values = {
        "evidence_status": "ready",
        "verified_item_count": d("4.000000"),
        "independent_note_count": d("3.000000"),
        "evidence_quality_score": d("0.840000"),
        "unresolved_gap_count": d("0.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ResearchManualReviewEvidenceState(**values)


def conflict(**overrides: object) -> ResearchManualReviewConflictState:
    values = {
        "conflict_status": "clear",
        "conflict_count": d("0.000000"),
        "conflict_severity_score": d("0.000000"),
        "unresolved_conflict_count": d("0.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ResearchManualReviewConflictState(**values)


def cost(**overrides: object) -> ResearchManualReviewCostFrictionState:
    values = {
        "cost_status": "low",
        "fee_friction_score": d("0.020000"),
        "spread_friction_score": d("0.030000"),
        "liquidity_friction_score": d("0.040000"),
        "total_friction_score": d("0.030000"),
        "unresolved_cost_issue_count": d("0.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ResearchManualReviewCostFrictionState(**values)


def settlement(**overrides: object) -> ResearchManualReviewSettlementRiskState:
    values = {
        "settlement_status": "low",
        "ambiguity_score": d("0.100000"),
        "rule_dependency_score": d("0.120000"),
        "arbiter_dependency_score": d("0.110000"),
        "settlement_risk_score": d("0.110000"),
        "unresolved_settlement_issue_count": d("0.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ResearchManualReviewSettlementRiskState(**values)


def step(**overrides: object) -> ResearchManualReviewNextStep:
    values = {
        "focus_code": "corroboration_follow_up",
        "priority_score": d("0.300000"),
        "blocks_review": False,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ResearchManualReviewNextStep(**values)


def packet(
    *,
    evidence_state: ResearchManualReviewEvidenceState | None = None,
    conflict_state: ResearchManualReviewConflictState | None = None,
    cost_friction_state: ResearchManualReviewCostFrictionState | None = None,
    settlement_risk_state: ResearchManualReviewSettlementRiskState | None = None,
    next_research_steps: tuple[ResearchManualReviewNextStep, ...] = (),
    public_payload: tuple[ResearchManualReviewPublicPayloadItem, ...] = (),
    policy: ResearchManualReviewPacketPolicy | None = None,
) -> ResearchManualReviewPacket:
    return build_research_manual_review_packet(
        generated_at=NOW,
        evidence_state=evidence_state or evidence(),
        conflict_state=conflict_state or conflict(),
        cost_friction_state=cost_friction_state or cost(),
        settlement_risk_state=settlement_risk_state or settlement(),
        next_research_steps=next_research_steps,
        public_payload=public_payload,
        policy=policy,
    )


def test_pass_packet_is_readonly_json_ready_and_digest_bound() -> None:
    report = packet(
        next_research_steps=(step(),),
        public_payload=(ResearchManualReviewPublicPayloadItem("review_scope", "macro event"),),
    )

    assert is_dataclass(report)
    assert report.packet_status == "pass"
    assert report.reason_codes == (
        "evidence_ready",
        "conflicts_clear",
        "cost_friction_low",
        "settlement_risk_low",
        "research_steps_logged",
        "manual_review_packet_ready",
    )
    assert report.review_sections == (
        "evidence_state",
        "conflict_review",
        "cost_friction_review",
        "settlement_risk_review",
        "next_research_steps",
        "safe_review_packet",
    )
    assert report.next_research_step_count == d("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["packet_status"] == "pass"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["next_research_step_count"] == "1.000000"
    assert payload["next_research_steps"][0]["priority_score"] == "0.300000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)


def test_watch_and_block_packets_explain_manual_review_state() -> None:
    watch_report = packet(
        evidence_state=evidence(
            evidence_status="limited",
            evidence_quality_score=d("0.610000"),
            unresolved_gap_count=d("1.000000"),
        ),
        conflict_state=conflict(
            conflict_status="minor",
            conflict_count=d("1.000000"),
            conflict_severity_score=d("0.300000"),
        ),
        cost_friction_state=cost(
            cost_status="elevated",
            fee_friction_score=d("0.180000"),
            spread_friction_score=d("0.150000"),
            liquidity_friction_score=d("0.120000"),
            total_friction_score=d("0.150000"),
            unresolved_cost_issue_count=d("1.000000"),
        ),
        settlement_risk_state=settlement(
            settlement_status="watch",
            ambiguity_score=d("0.300000"),
            rule_dependency_score=d("0.330000"),
            arbiter_dependency_score=d("0.300000"),
            settlement_risk_score=d("0.310000"),
            unresolved_settlement_issue_count=d("1.000000"),
        ),
        next_research_steps=(step(priority_score=d("0.900000")),),
    )
    block_report = packet(
        evidence_state=evidence(
            evidence_status="missing",
            verified_item_count=d("0.000000"),
            independent_note_count=d("0.000000"),
            evidence_quality_score=d("0.000000"),
        ),
        conflict_state=conflict(
            conflict_status="material",
            conflict_count=d("2.000000"),
            conflict_severity_score=d("0.800000"),
        ),
        cost_friction_state=cost(
            cost_status="high",
            fee_friction_score=d("0.700000"),
            spread_friction_score=d("0.800000"),
            liquidity_friction_score=d("0.900000"),
            total_friction_score=d("0.800000"),
        ),
        settlement_risk_state=settlement(
            settlement_status="high",
            ambiguity_score=d("0.700000"),
            rule_dependency_score=d("0.800000"),
            arbiter_dependency_score=d("0.750000"),
            settlement_risk_score=d("0.750000"),
        ),
        next_research_steps=(step(priority_score=d("0.950000"), blocks_review=True),),
    )

    assert watch_report.packet_status == "watch"
    assert watch_report.reason_codes == (
        "evidence_limited",
        "evidence_quality_watch",
        "evidence_gaps_open",
        "conflicts_minor",
        "cost_friction_elevated",
        "cost_issues_open",
        "settlement_risk_watch",
        "settlement_issues_open",
        "high_priority_research_step",
    )

    assert block_report.packet_status == "block"
    assert block_report.reason_codes == (
        "evidence_missing",
        "missing_verified_evidence",
        "insufficient_independent_notes",
        "conflicts_material",
        "conflict_score_above_limit",
        "cost_friction_high",
        "cost_friction_above_limit",
        "settlement_risk_high",
        "settlement_score_above_limit",
        "blocking_research_step_open",
    )


def test_dataclasses_are_frozen_decimal_only_and_exact_type_checked() -> None:
    report = packet()

    for value in (
        ResearchManualReviewPacketPolicy(),
        evidence(),
        conflict(),
        cost(),
        settlement(),
        step(),
        report,
    ):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="evidence_quality_score"):
        evidence(evidence_quality_score=_DecimalSubclass("0.840000"))
    with pytest.raises(ValueError, match="verified_item_count"):
        evidence(verified_item_count=d("1.500000"))
    with pytest.raises(ValueError, match="conflict_status"):
        conflict(conflict_status="done")
    with pytest.raises(ValueError, match="total_friction_score"):
        cost(total_friction_score=d("0.500000"))
    with pytest.raises(ValueError, match="settlement_risk_score"):
        settlement(settlement_risk_score=d("0.500000"))
    with pytest.raises(ValueError, match="priority_score"):
        step(priority_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_state"):
        build_research_manual_review_packet(
            generated_at=NOW,
            evidence_state=object(),  # type: ignore[arg-type]
            conflict_state=conflict(),
            cost_friction_state=cost(),
            settlement_risk_state=settlement(),
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_public_payload_filter_rejects_private_and_actionable_surfaces() -> None:
    for key in (
        "raw_ref",
        "source_url",
        "market_question",
        "dsn_ref",
        "table_ref",
        "token_ref",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchManualReviewPublicPayloadItem(key, "safe note")

    for value in (
        "https://example.test/item",
        "raw item",
        "market question wording",
        "dsn item",
        "table item",
        "token item",
        "b" "uy action",
        "se" "ll action",
        "pos" "ition action",
        "rec" "ommend action",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchManualReviewPublicPayloadItem("safe_note", value)

    with pytest.raises(ValueError, match="unsafe public"):
        step(focus_code="market_question")
    with pytest.raises(ValueError, match="report_only"):
        evidence(report_only=False)
    with pytest.raises(ValueError, match="payload"):
        replace(packet(), public_payload=(ResearchManualReviewPublicPayloadItem("safe_note", "changed"),))


def test_static_module_surface_is_safe_report_only_and_readonly() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_manual_review_packet_builder.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "raw_id",
        "source_url",
        "market_question",
        "dsn",
        "table",
        "token",
        "buy",
        "sell",
        "position",
        "recommend",
        "requests.",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "subprocess",
        "open(",
        "http://",
        "https://",
    ):
        assert forbidden not in lowered
    assert not re.search(r"\b(auth|broker|signing)\b", lowered)

    for public_name in api.__all__:
        lowered_name = public_name.lower()
        assert "raw" not in lowered_name
        assert "source_url" not in lowered_name
        assert "market_question" not in lowered_name
        assert "token" not in lowered_name

    for cls in (
        ResearchManualReviewPacketPolicy,
        ResearchManualReviewEvidenceState,
        ResearchManualReviewConflictState,
        ResearchManualReviewCostFrictionState,
        ResearchManualReviewSettlementRiskState,
        ResearchManualReviewNextStep,
        ResearchManualReviewPublicPayloadItem,
        ResearchManualReviewPacket,
    ):
        for field in fields(cls):
            lowered_name = field.name.lower()
            assert "raw" not in lowered_name
            assert "source_url" not in lowered_name
            assert "market_question" not in lowered_name
            assert "token" not in lowered_name

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
