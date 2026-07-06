from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "strategy-research-packet-completeness-v10"


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module("polymarket_alpha_lab.strategy_research_packet_completeness_v10")


def packet(**overrides: Any):
    values: dict[str, Any] = {
        "packet_id": "packet-alpha",
        "market_slug": "fed-cut-by-september",
        "research_generated_at": GENERATED_AT - timedelta(minutes=15),
        "source_count": d("3"),
        "required_source_count": d("3"),
        "resolution_contract_present": True,
        "forecast_rationale_present": True,
        "cost_model_present": True,
        "risk_sizing_present": True,
        "exit_readiness_present": True,
        "human_review_status": "approved",
    }
    values.update(overrides)
    return api().StrategyResearchPacketCompletenessV10Packet(**values)


def evaluate(*, subject: object | None = None):
    return api().evaluate_strategy_research_packet_completeness_v10(
        packet() if subject is None else subject,
        generated_at=GENERATED_AT,
    )


def test_complete_packet_scores_one_and_exposes_readonly_payload() -> None:
    module = api()

    result = evaluate()

    assert result == module.StrategyResearchPacketCompletenessV10Result(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        packet_id="packet-alpha",
        market_slug="fed-cut-by-september",
        research_generated_at=GENERATED_AT - timedelta(minutes=15),
        source_count=d("3"),
        required_source_count=d("3"),
        source_quorum_met=True,
        resolution_contract_present=True,
        forecast_rationale_present=True,
        cost_model_present=True,
        risk_sizing_present=True,
        exit_readiness_present=True,
        human_review_status="approved",
        completeness_score=d("1.000000"),
        missing_sections=(),
        packet_status="complete",
        reason_codes=("complete",),
    )
    assert type(result.completeness_score) is Decimal
    assert type(result.source_count) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.payload["completeness_score"] == "1.000000"
    assert result.payload["source_count"] == "3"
    assert result.payload["paper_only"] is True
    assert result.payload["missing_sections"] == []
    with pytest.raises(FrozenInstanceError):
        result.packet_status = "blocked"  # type: ignore[misc]


def test_missing_sections_drive_blocked_status_reason_codes_and_score() -> None:
    result = evaluate(
        subject=packet(
            source_count=d("1"),
            resolution_contract_present=False,
            forecast_rationale_present=False,
            risk_sizing_present=False,
            human_review_status="pending_review",
        ),
    )

    assert result.completeness_score == d("0.285714")
    assert result.packet_status == "blocked"
    assert result.missing_sections == (
        "resolution_contract",
        "source_quorum",
        "forecast_rationale",
        "risk_sizing",
        "human_review_status",
    )
    assert result.reason_codes == (
        "resolution_contract_missing",
        "source_quorum_missing",
        "forecast_rationale_missing",
        "risk_sizing_missing",
        "human_review_not_approved",
    )
    assert result.source_quorum_met is False


def test_human_review_rejected_is_rejected_even_when_other_sections_are_present() -> None:
    result = evaluate(subject=packet(human_review_status="rejected"))

    assert result.completeness_score == d("0.857143")
    assert result.packet_status == "rejected"
    assert result.missing_sections == ("human_review_status",)
    assert result.reason_codes == ("human_review_rejected",)


def test_inputs_reject_non_decimal_numbers_future_research_and_unsafe_flags() -> None:
    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        packet(source_count=3)
    with pytest.raises(ValueError, match="required_source_count must be a Decimal"):
        packet(required_source_count=3.0)
    with pytest.raises(ValueError, match="research_generated_at must not be after generated_at"):
        evaluate(subject=packet(research_generated_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only must be True"):
        packet(paper_only=False)


def test_module_is_pure_report_only_and_unwired_from_io_or_execution() -> None:
    source = inspect.getsource(api())

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
        "submit_order",
        "cancel_order",
        "place_order",
    )
    assert all(term not in source for term in forbidden_terms)
