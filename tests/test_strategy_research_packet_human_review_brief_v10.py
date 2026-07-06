from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.strategy_research_packet_human_review_brief_v10",
    )


def candidate(**overrides: Any):
    values: dict[str, Any] = {
        "market_id": "market-alpha",
        "decision_readiness": d("0.910000"),
        "packet_status": "complete",
        "top_risks": (),
        "top_evidence_points": (
            "official-rule-match",
            "source-quorum-confirmed",
        ),
        "missing_sections_count": d("0"),
        "cost_adjusted_edge_bps": d("42.500000"),
        "time_to_resolution_minutes": d("1440.000000"),
    }
    values.update(overrides)
    return api().StrategyResearchPacketHumanReviewBriefV10Input(**values)


def build(subject: object | None = None):
    return api().build_strategy_research_packet_human_review_brief_v10(
        candidate() if subject is None else subject,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_approval_ready_brief_compresses_packet_into_payload() -> None:
    module = api()

    result = build()

    assert result == module.StrategyResearchPacketHumanReviewBriefV10Result(
        market_id="market-alpha",
        decision_readiness=d("0.910000"),
        packet_status="complete",
        top_risks=(),
        top_evidence_points=(
            "official-rule-match",
            "source-quorum-confirmed",
        ),
        missing_sections_count=d("0"),
        cost_adjusted_edge_bps=d("42.500000"),
        time_to_resolution_minutes=d("1440.000000"),
        brief_status="approval_ready",
        review_questions=(
            "Confirm the evidence still supports the positive cost-adjusted edge.",
        ),
        approval_blockers=(),
        summary_points=(
            "market-alpha packet complete with readiness 0.910000.",
            "Cost-adjusted edge is 42.500000 bps with 1440.000000 minutes to resolution.",
            "Evidence highlights: official-rule-match; source-quorum-confirmed.",
            "No top risks supplied.",
        ),
        reason_codes=(
            "packet_status_complete",
            "decision_readiness_ready",
            "evidence_present",
            "positive_cost_adjusted_edge",
            "no_top_risks",
            "approval_ready",
        ),
    )
    assert type(result.decision_readiness) is Decimal
    assert type(result.missing_sections_count) is Decimal
    assert type(result.cost_adjusted_edge_bps) is Decimal
    assert type(result.time_to_resolution_minutes) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = result.payload
    assert payload["brief_status"] == "approval_ready"
    assert payload["decision_readiness"] == "0.910000"
    assert payload["cost_adjusted_edge_bps"] == "42.500000"
    assert payload["top_evidence_points"] == [
        "official-rule-match",
        "source-quorum-confirmed",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_blocked_brief_surfaces_questions_blockers_and_reason_codes() -> None:
    result = build(
        candidate(
            decision_readiness=d("0.550000"),
            packet_status="blocked",
            top_risks=("ambiguous-resolution", "thin-liquidity"),
            top_evidence_points=(),
            missing_sections_count=d("2"),
            cost_adjusted_edge_bps=d("-5.000000"),
            time_to_resolution_minutes=d("30.000000"),
        ),
    )

    assert result.brief_status == "blocked"
    assert result.approval_blockers == (
        "Resolve packet status blocked before approval.",
        "Complete 2 missing research packet sections.",
        "Raise decision readiness to at least 0.700000.",
        "Add at least one evidence point.",
        "Cost-adjusted edge must be positive before approval.",
    )
    assert result.review_questions == (
        "Which missing sections are blocking the research packet?",
        "What evidence resolves the top risk: ambiguous-resolution?",
        "What evidence resolves the top risk: thin-liquidity?",
        "Why is the cost-adjusted edge still acceptable after costs?",
        "Is 30.000000 minutes enough time for manual review?",
    )
    assert result.summary_points == (
        "market-alpha packet blocked with readiness 0.550000.",
        "Cost-adjusted edge is -5.000000 bps with 30.000000 minutes to resolution.",
        "Missing sections: 2.",
        "Top risks: ambiguous-resolution; thin-liquidity.",
    )
    assert result.reason_codes == (
        "packet_status_blocked",
        "missing_sections_present",
        "decision_readiness_low",
        "evidence_missing",
        "nonpositive_cost_adjusted_edge",
        "risks_present",
        "near_resolution",
        "approval_blocked",
    )
    assert result.payload["approval_blockers"] == list(result.approval_blockers)


def test_review_required_when_packet_has_risks_but_no_approval_blockers() -> None:
    result = build(
        candidate(
            decision_readiness=d("0.760000"),
            top_risks=("headline-volatility",),
            cost_adjusted_edge_bps=d("8.250000"),
            time_to_resolution_minutes=d("180.000000"),
        ),
    )

    assert result.brief_status == "review_required"
    assert result.approval_blockers == ()
    assert result.review_questions == (
        "What evidence resolves the top risk: headline-volatility?",
        "Confirm the evidence still supports the positive cost-adjusted edge.",
    )
    assert result.reason_codes == (
        "packet_status_complete",
        "decision_readiness_ready",
        "evidence_present",
        "positive_cost_adjusted_edge",
        "risks_present",
        "human_review_required",
    )


def test_dataclasses_are_frozen_and_numeric_inputs_must_be_decimal() -> None:
    subject = candidate()

    with pytest.raises(FrozenInstanceError):
        subject.market_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="decision_readiness must be a Decimal"):
        candidate(decision_readiness=0.91)
    with pytest.raises(ValueError, match="missing_sections_count must be a Decimal"):
        candidate(missing_sections_count=0)
    with pytest.raises(ValueError, match="cost_adjusted_edge_bps must be a Decimal"):
        candidate(cost_adjusted_edge_bps=42.5)
    with pytest.raises(ValueError, match="time_to_resolution_minutes must be a Decimal"):
        candidate(time_to_resolution_minutes=1440)
    with pytest.raises(ValueError, match="paper_only must be True"):
        candidate(paper_only=False)


def test_module_is_pure_readonly_report_only_and_unwired_from_io_or_execution() -> None:
    module = api()
    source = inspect.getsource(module)

    assert module.StrategyResearchPacketHumanReviewBriefV10Input.__dataclass_params__.frozen
    assert module.StrategyResearchPacketHumanReviewBriefV10Result.__dataclass_params__.frozen
    assert module.__all__ == (
        "BRIEF_STATUSES",
        "PACKET_STATUSES",
        "REASON_CODES",
        "StrategyResearchPacketHumanReviewBriefV10Input",
        "StrategyResearchPacketHumanReviewBriefV10Result",
        "build_strategy_research_packet_human_review_brief_v10",
        "strategy_research_packet_human_review_brief_v10_payload",
    )

    forbidden_terms = (
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "supabase",
        "clob",
        "wallet",
        "private_key",
        "signing",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
    )
    assert all(term not in source for term in forbidden_terms)
