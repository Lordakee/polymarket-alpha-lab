from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_research_decision_bundle_v7.py"
)
GENERATED_AT = datetime(2026, 7, 6, 18, 30, tzinfo=timezone(timedelta(hours=2)))


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_research_decision_bundle_v7",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {"config_version": "strategy-research-decision-bundle-v7-test"}
    values.update(overrides)
    return module.StrategyResearchDecisionBundleV7Config(**values)


def readiness(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-alpha",
        "market_slug": "fed-cut-by-september",
        "readiness_status": "ready",
        "candidate_count": d("1"),
        "ready_count": d("1"),
        "watch_count": d("0"),
        "blocked_count": d("0"),
        "reason_codes": ("research_packet_ready",),
    }
    values.update(overrides)
    return module.StrategyResearchDecisionBundleV7ReadinessSummary(**values)


def watchlist(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-alpha",
        "market_slug": "fed-cut-by-september",
        "watchlist_status": "clear",
        "next_review_minutes": d("0"),
        "reason_codes": ("watchlist_clear",),
    }
    values.update(overrides)
    return module.StrategyResearchDecisionBundleV7WatchlistSummary(**values)


def mispricing(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-alpha",
        "market_slug": "fed-cut-by-september",
        "window_status": "open",
        "mispriced_side": "yes",
        "probability_gap": d("0.110000"),
        "abs_probability_gap": d("0.110000"),
        "cost_adjusted_edge": d("0.025000"),
        "reason_codes": ("mispricing_window_open",),
    }
    values.update(overrides)
    return module.StrategyResearchDecisionBundleV7MispricingWindowSummary(**values)


def source_reliability(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-alpha",
        "market_slug": "fed-cut-by-september",
        "source_count": d("3"),
        "pass_count": d("3"),
        "watch_count": d("0"),
        "block_count": d("0"),
        "average_source_weight": d("0.881250"),
        "reliability_status": "pass",
        "reason_codes": ("source_weight_pass",),
    }
    values.update(overrides)
    return module.StrategyResearchDecisionBundleV7SourceReliabilitySummary(**values)


def sizing(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-alpha",
        "market_slug": "fed-cut-by-september",
        "sizing_status": "pass",
        "binding_capacity": d("1500.000000"),
        "paper_notional": d("1200.000000"),
        "resolution_risk": d("0.200000"),
        "reason_codes": ("strategy_sizing_risk_budget_v4_pass",),
    }
    values.update(overrides)
    return module.StrategyResearchDecisionBundleV7SizingSummary(**values)


def audit_packet(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-alpha",
        "market_slug": "fed-cut-by-september",
        "packet_status": "ready",
        "recommendation": "enter",
        "forecast_edge": d("0.110000"),
        "cost_adjusted_edge": d("0.025000"),
        "source_quality_score": d("0.900000"),
        "resolution_risk_score": d("0.200000"),
        "required_human_review": False,
        "reason_codes": ("audit_packet_ready",),
    }
    values.update(overrides)
    return module.StrategyResearchDecisionBundleV7AuditPacketSummary(**values)


def bundle(**overrides: object):
    module = api()
    values = {
        "readiness": readiness(),
        "watchlist": watchlist(),
        "mispricing_window": mispricing(),
        "source_reliability": source_reliability(),
        "sizing": sizing(),
        "audit_packet": audit_packet(),
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return module.build_strategy_research_decision_bundle_v7(**values)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_ready_inputs_build_readonly_decision_bundle_without_human_review() -> None:
    result = bundle()

    assert is_dataclass(result)
    assert result.generated_at == datetime(2026, 7, 6, 16, 30, tzinfo=UTC)
    assert result.config_version == "strategy-research-decision-bundle-v7-test"
    assert result.candidate_id == "candidate-alpha"
    assert result.market_slug == "fed-cut-by-september"
    assert result.bundle_status == "ready"
    assert result.required_human_review is False
    assert result.reason_codes == (
        "strategy_research_decision_bundle_v7_ready",
        "readiness_ready",
        "watchlist_clear",
        "mispricing_window_open",
        "source_reliability_pass",
        "sizing_pass",
        "audit_packet_ready",
        "research_packet_ready",
        "source_weight_pass",
        "strategy_sizing_risk_budget_v4_pass",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    with pytest.raises(FrozenInstanceError):
        result.bundle_status = "watch"  # type: ignore[misc]


def test_watch_bundle_requires_human_review_for_nonblocking_component_watch() -> None:
    result = bundle(
        mispricing_window=mispricing(window_status="watch"),
        source_reliability=source_reliability(
            reliability_status="watch",
            pass_count=d("2"),
            watch_count=d("1"),
            average_source_weight=d("0.621500"),
            reason_codes=("source_weight_watch",),
        ),
        sizing=sizing(
            sizing_status="watch",
            paper_notional=d("216.000000"),
            resolution_risk=d("0.400000"),
            reason_codes=("strategy_sizing_risk_budget_v4_watch",),
        ),
    )

    assert result.bundle_status == "watch"
    assert result.required_human_review is True
    assert result.reason_codes[:7] == (
        "strategy_research_decision_bundle_v7_watch",
        "human_review_required",
        "readiness_ready",
        "watchlist_clear",
        "mispricing_window_watch",
        "source_reliability_watch",
        "sizing_watch",
    )


def test_blocked_bundle_requires_human_review_when_any_material_component_blocks() -> None:
    result = bundle(
        readiness=readiness(
            readiness_status="blocked",
            ready_count=d("0"),
            blocked_count=d("1"),
            reason_codes=("forecast_missing",),
        ),
        watchlist=watchlist(
            watchlist_status="wait_for_source",
            next_review_minutes=d("360"),
            reason_codes=("source_count_below_minimum",),
        ),
        mispricing_window=mispricing(
            window_status="closed",
            reason_codes=("mispricing_window_closed",),
        ),
        source_reliability=source_reliability(
            reliability_status="blocked",
            pass_count=d("0"),
            block_count=d("3"),
            average_source_weight=d("0.342500"),
            reason_codes=("source_weight_block",),
        ),
        sizing=sizing(
            sizing_status="blocked",
            binding_capacity=d("0.000000"),
            paper_notional=d("0.000000"),
            reason_codes=("strategy_sizing_risk_budget_v4_block",),
        ),
        audit_packet=audit_packet(
            packet_status="blocked",
            recommendation="skip",
            required_human_review=True,
            reason_codes=("audit_packet_blocked",),
        ),
    )

    assert result.bundle_status == "blocked"
    assert result.required_human_review is True
    assert result.reason_codes[:8] == (
        "strategy_research_decision_bundle_v7_blocked",
        "human_review_required",
        "readiness_blocked",
        "watchlist_wait_for_source",
        "mispricing_window_closed",
        "source_reliability_blocked",
        "sizing_blocked",
        "audit_packet_blocked",
    )
    assert "forecast_missing" in result.reason_codes
    assert "source_count_below_minimum" in result.reason_codes


def test_validation_rejects_float_subclass_mismatched_candidate_and_bad_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        bundle(config=object())

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        source_reliability(source_count=3)

    with pytest.raises(ValueError, match="average_source_weight must be exactly Decimal"):
        source_reliability(average_source_weight=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        bundle(generated_at=datetime(2026, 7, 6, 16, 30))

    with pytest.raises(ValueError, match="component identity must match readiness"):
        bundle(watchlist=watchlist(candidate_id="candidate-beta"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        readiness(paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(bundle(), readonly=False)

    with pytest.raises(ValueError, match="bundle_status"):
        module.StrategyResearchDecisionBundleV7(
            generated_at=GENERATED_AT,
            config_version="strategy-research-decision-bundle-v7-test",
            candidate_id="candidate-alpha",
            market_slug="fed-cut-by-september",
            bundle_status="ready",
            required_human_review=True,
            readiness=readiness(),
            watchlist=watchlist(),
            mispricing_window=mispricing(),
            source_reliability=source_reliability(),
            sizing=sizing(),
            audit_packet=audit_packet(),
            reason_codes=("strategy_research_decision_bundle_v7_ready",),
        )


def test_public_numeric_fields_are_decimal_only_and_payload_has_decimal_strings() -> None:
    module = api()
    result = bundle()
    payload = module.strategy_research_decision_bundle_v7_payload(result)

    numeric_fields = {
        "candidate_count",
        "ready_count",
        "watch_count",
        "blocked_count",
        "next_review_minutes",
        "probability_gap",
        "abs_probability_gap",
        "cost_adjusted_edge",
        "source_count",
        "pass_count",
        "block_count",
        "average_source_weight",
        "binding_capacity",
        "paper_notional",
        "resolution_risk",
        "forecast_edge",
        "source_quality_score",
        "resolution_risk_score",
    }

    for cls in (
        module.StrategyResearchDecisionBundleV7ReadinessSummary,
        module.StrategyResearchDecisionBundleV7WatchlistSummary,
        module.StrategyResearchDecisionBundleV7MispricingWindowSummary,
        module.StrategyResearchDecisionBundleV7SourceReliabilitySummary,
        module.StrategyResearchDecisionBundleV7SizingSummary,
        module.StrategyResearchDecisionBundleV7AuditPacketSummary,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in numeric_fields:
                assert hints[item.name] is Decimal

    assert payload["generated_at"] == "2026-07-06T16:30:00+00:00"
    assert payload["bundle_status"] == "ready"
    assert payload["required_human_review"] is False
    assert payload["readiness"]["candidate_count"] == "1"
    assert payload["mispricing_window"]["probability_gap"] == "0.110000"
    assert payload["source_reliability"]["average_source_weight"] == "0.881250"
    assert payload["sizing"]["paper_notional"] == "1200.000000"
    assert payload["audit_packet"]["source_quality_score"] == "0.900000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_module_scope_is_paper_report_readonly_with_no_io_or_execution_surface() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "requests",
        "httpx",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "socket",
        "urllib",
        "clob",
        "wallet",
        "private_key",
        "submit",
        "cancel",
        "broker",
        "execute(",
        "open(",
        "fast",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
