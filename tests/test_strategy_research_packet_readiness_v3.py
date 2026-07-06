from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "strategy-research-packet-readiness-v3"


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module("polymarket_alpha_lab.strategy_research_packet_readiness_v3")


def candidate(**overrides: Any):
    values: dict[str, Any] = {
        "candidate_id": "candidate-alpha",
        "market_slug": "fed-cut-by-september",
        "research_generated_at": GENERATED_AT - timedelta(minutes=15),
        "forecast_probability": d("0.620000"),
        "source_count": d("3"),
        "required_source_count": d("3"),
        "resolution_contract_present": True,
        "cost_model_present": True,
        "team_memory_present": True,
        "audit_packet_present": True,
    }
    values.update(overrides)
    return api().StrategyResearchPacketReadinessV3Input(**values)


def report(*candidates: object):
    return api().build_strategy_research_packet_readiness_v3_report(
        candidates,
        generated_at=GENERATED_AT,
    )


def test_ready_candidate_preserves_typed_decimal_readonly_packet_surface() -> None:
    module = api()

    result = report(candidate())

    assert result == module.StrategyResearchPacketReadinessV3Report(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        readiness_status="ready",
        missing_sections=(),
        reason_codes=(),
        candidate_count=d("1"),
        ready_count=d("1"),
        watch_count=d("0"),
        blocked_count=d("0"),
        rows=(
            module.StrategyResearchPacketReadinessV3Row(
                candidate_id="candidate-alpha",
                market_slug="fed-cut-by-september",
                research_generated_at=GENERATED_AT - timedelta(minutes=15),
                forecast_probability=d("0.620000"),
                source_count=d("3"),
                required_source_count=d("3"),
                forecast_present=True,
                source_quorum_met=True,
                resolution_contract_present=True,
                cost_model_present=True,
                team_memory_present=True,
                audit_packet_present=True,
                readiness_status="ready",
                missing_sections=(),
                reason_codes=(),
            ),
        ),
    )
    assert type(result.candidate_count) is Decimal
    assert type(result.rows[0].forecast_probability) is Decimal
    assert type(result.rows[0].source_count) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    with pytest.raises(FrozenInstanceError):
        result.rows[0].readiness_status = "blocked"  # type: ignore[misc]


def test_blocked_candidate_lists_blocking_missing_sections_and_reason_codes() -> None:
    result = report(
        candidate(
            candidate_id="candidate-blocked",
            forecast_probability=None,
            source_count=d("1"),
            required_source_count=d("3"),
            resolution_contract_present=False,
            cost_model_present=False,
            audit_packet_present=False,
        ),
    )

    assert result.readiness_status == "blocked"
    assert result.missing_sections == (
        "forecast",
        "source_quorum",
        "resolution_contract",
        "cost_model",
        "audit_packet",
    )
    assert result.reason_codes == (
        "forecast_missing",
        "source_quorum_missing",
        "resolution_contract_missing",
        "cost_model_missing",
        "audit_packet_missing",
    )
    assert result.ready_count == d("0")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("1")
    assert result.rows[0].readiness_status == "blocked"
    assert result.rows[0].missing_sections == result.missing_sections
    assert result.rows[0].reason_codes == result.reason_codes


def test_team_memory_gap_only_yields_watch_before_recommendation() -> None:
    result = report(candidate(team_memory_present=False))

    assert result.readiness_status == "watch"
    assert result.missing_sections == ("team_memory",)
    assert result.reason_codes == ("team_memory_missing",)
    assert result.ready_count == d("0")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("0")
    assert result.rows[0].readiness_status == "watch"


def test_empty_input_is_blocked_with_all_material_sections_missing() -> None:
    result = report()

    assert result.readiness_status == "blocked"
    assert result.missing_sections == (
        "forecast",
        "source_quorum",
        "resolution_contract",
        "cost_model",
        "team_memory",
        "audit_packet",
    )
    assert result.reason_codes == (
        "empty_input",
        "forecast_missing",
        "source_quorum_missing",
        "resolution_contract_missing",
        "cost_model_missing",
        "team_memory_missing",
        "audit_packet_missing",
    )
    assert result.candidate_count == d("0")
    assert result.rows == ()


def test_inputs_reject_non_decimal_numeric_and_unsafe_flags() -> None:
    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        candidate(forecast_probability=0.62)
    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        candidate(source_count=3)
    with pytest.raises(ValueError, match="paper_only must be True"):
        candidate(paper_only=False)


def test_module_is_pure_report_only_and_unwired_from_io_or_execution() -> None:
    source = inspect.getsource(api())

    forbidden_terms = (
        "requests",
        "httpx",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "clob",
        "wallet",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
    )
    assert all(term not in source for term in forbidden_terms)
