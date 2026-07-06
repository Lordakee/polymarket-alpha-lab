from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 59, 30, tzinfo=UTC)
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_fee_adjusted_position_sizing_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-fee-adjusted-position-sizing-gate-v2",
        "portfolio_nav_usdc": d("1000.000000"),
        "max_allocation_fraction_of_nav": d("0.100000"),
        "edge_allocation_unit": d("0.100000"),
        "min_cost_adjusted_edge": d("0.010000"),
        "min_confidence_score": d("0.500000"),
        "max_liquidity_take_share": d("0.250000"),
        "max_depth_take_share": d("0.250000"),
        "max_category_exposure_share": d("0.300000"),
        "max_settlement_lockup_share": d("0.200000"),
        "settlement_delay_penalty_rate": d("0.002000"),
        "settlement_lockup_days_weight": d("0.100000"),
        "min_position_size_usdc": d("5.000000"),
    }
    values.update(overrides)
    return module.StrategyFeeAdjustedPositionSizingGateV2Config(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-alpha",
        "market_slug": "market-alpha",
        "category": "elections-category",
        "question": "Will alpha happen?",
        "outcome": "yes",
        "observed_at": OBSERVED_AT,
        "forecast_probability": d("0.700000"),
        "market_probability": d("0.600000"),
        "taker_fee_rate": d("0.020000"),
        "spread_probability": d("0.010000"),
        "expected_slippage_probability": d("0.003000"),
        "available_liquidity_usdc": d("300.000000"),
        "available_depth_shares": d("400.000000"),
        "confidence_score": d("0.800000"),
        "current_category_exposure_usdc": d("250.000000"),
        "settlement_delay_days": d("2.000000"),
        "reason_codes": ("seed",),
    }
    values.update(overrides)
    return module.StrategyFeeAdjustedPositionSizingGateV2Candidate(**values)


def report(*candidates: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_strategy_fee_adjusted_position_sizing_gate_v2_report(
        candidates,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def test_gate_computes_fee_adjusted_size_and_allocation_caps() -> None:
    result = report(
        candidate(candidate_id="ready", market_slug="market-ready"),
        candidate(
            candidate_id="watch",
            market_slug="market-watch",
            current_category_exposure_usdc=d("298.000000"),
        ),
        candidate(
            candidate_id="blocked",
            market_slug="market-blocked",
            forecast_probability=d("0.620000"),
        ),
    )

    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-fee-adjusted-position-sizing-gate-v2"
    assert result.candidate_count == d("3")
    assert result.row_count == d("3")
    assert result.ready_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.total_max_paper_allocation_usdc == d("52.000000")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64

    ready, watch, blocked = result.rows
    assert ready.candidate_id == "ready"
    assert ready.gross_probability_edge == d("0.100000")
    assert ready.taker_fee_cost_probability == d("0.012000")
    assert ready.spread_cost_probability == d("0.010000")
    assert ready.expected_slippage_probability == d("0.003000")
    assert ready.settlement_delay_cost_probability == d("0.004000")
    assert ready.total_cost_probability == d("0.029000")
    assert ready.cost_adjusted_edge == d("0.071000")
    assert ready.confidence_adjusted_edge == d("0.056800")
    assert ready.edge_budget_usdc == d("56.800000")
    assert ready.liquidity_cap_usdc == d("75.000000")
    assert ready.depth_cap_usdc == d("60.000000")
    assert ready.category_remaining_capacity_usdc == d("50.000000")
    assert ready.settlement_lockup_cap_usdc == d("166.666667")
    assert ready.max_paper_allocation_usdc == d("50.000000")
    assert ready.gate_status == "ready"
    assert ready.risk_label == "low_sizing_risk"
    assert "category_capacity_limited" in ready.reason_codes
    assert "allocation_ready" in ready.reason_codes
    assert len(ready.derived_validation_digest) == 64

    assert watch.candidate_id == "watch"
    assert watch.max_paper_allocation_usdc == d("2.000000")
    assert watch.gate_status == "watch"
    assert watch.risk_label == "medium_sizing_risk"
    assert "allocation_below_minimum" in watch.reason_codes
    assert "category_capacity_limited" in watch.reason_codes

    assert blocked.candidate_id == "blocked"
    assert blocked.cost_adjusted_edge == d("-0.009000")
    assert blocked.max_paper_allocation_usdc == d("0.000000")
    assert blocked.gate_status == "blocked"
    assert blocked.risk_label == "high_sizing_risk"
    assert "edge_not_positive_after_costs" in blocked.reason_codes


def test_payload_is_json_ready_decimal_strings_and_safe_public_content() -> None:
    result = report(candidate(candidate_id="payload"))

    payload = api().strategy_fee_adjusted_position_sizing_gate_v2_payload(result)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["rows"][0]["candidate_id"] == "payload"
    assert payload["rows"][0]["cost_adjusted_edge"] == "0.071000"
    assert payload["rows"][0]["max_paper_allocation_usdc"] == "50.000000"
    assert payload["rows"][0]["derived_validation_digest"] == (
        result.rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                assert isinstance(key, str)
                assert not any(fragment in key.lower() for fragment in FORBIDDEN_PUBLIC_FRAGMENTS)
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        else:
            assert not isinstance(value, Decimal)
            assert not isinstance(value, float)
            assert not (type(value) is int)
            if isinstance(value, str):
                assert not any(
                    fragment in value.lower() for fragment in FORBIDDEN_PUBLIC_FRAGMENTS
                )

    walk(payload)


def test_no_candidates_returns_empty_checked_report() -> None:
    result = report()

    assert result.candidate_count == d("0")
    assert result.row_count == d("0")
    assert result.ready_count == d("0")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("0")
    assert result.total_max_paper_allocation_usdc == d("0.000000")
    assert result.rows == ()
    assert result.reason_codes == ("missing_position_sizing_inputs",)
    assert len(result.derived_validation_digest) == 64


def test_frozen_flags_are_hard_and_digests_reject_tamper() -> None:
    result = report(candidate())
    row = result.rows[0]

    with pytest.raises(FrozenInstanceError):
        row.gate_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        config().min_cost_adjusted_edge = d("0.020000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(config(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, max_paper_allocation_usdc=d("49.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, ready_count=d("0"))


def test_rejects_decimal_subclasses_floats_datetimes_and_unsafe_surface() -> None:
    module = api()

    with pytest.raises(ValueError, match="forecast_probability"):
        candidate(forecast_probability=0.7)
    with pytest.raises(ValueError, match="forecast_probability"):
        candidate(forecast_probability=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate(), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        candidate(observed_at=datetime(2026, 7, 6, 11, 59, 30))
    with pytest.raises(ValueError, match="must not be after generated_at"):
        report(candidate(observed_at=datetime(2026, 7, 6, 12, 0, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="candidate_id"):
        candidate(candidate_id=_StringSubclass("candidate-alpha"))

    for field_name, bad_value in (
        ("candidate_id", "candidate-wallet"),
        ("market_slug", "market-network"),
        ("category", "category-trade"),
        ("question", "Should this mention buy?"),
        ("reason_codes", ("needs-auth",)),
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            candidate(**{field_name: bad_value})

    with pytest.raises(ValueError, match="unsafe public"):
        config(config_version="live-config")

    with pytest.raises(ValueError, match="unsafe public"):
        module.strategy_fee_adjusted_position_sizing_gate_v2_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "wallet": "x"},
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.strategy_fee_adjusted_position_sizing_gate_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "note": "needs-auth",
            },
        )

    assert set(module.__all__) == {
        "StrategyFeeAdjustedPositionSizingGateV2Candidate",
        "StrategyFeeAdjustedPositionSizingGateV2Config",
        "StrategyFeeAdjustedPositionSizingGateV2Report",
        "StrategyFeeAdjustedPositionSizingGateV2Row",
        "build_strategy_fee_adjusted_position_sizing_gate_v2_report",
        "strategy_fee_adjusted_position_sizing_gate_v2_payload",
    }


def test_validates_utc_conversion_config_and_report_consistency() -> None:
    module = api()
    eastern = timezone(timedelta(hours=-4))
    result = report(
        candidate(observed_at=datetime(2026, 7, 6, 7, 59, 30, tzinfo=eastern)),
        generated_at=datetime(2026, 7, 6, 8, 0, 0, tzinfo=eastern),
    )
    assert result.generated_at == GENERATED_AT
    assert result.rows[0].observed_at == OBSERVED_AT

    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_fee_adjusted_position_sizing_gate_v2_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="candidates"):
        module.build_strategy_fee_adjusted_position_sizing_gate_v2_report(
            "not-candidates",
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="Candidate"):
        module.build_strategy_fee_adjusted_position_sizing_gate_v2_report(
            (object(),),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="portfolio_nav_usdc"):
        config(portfolio_nav_usdc=d("0.000000"))
    with pytest.raises(ValueError, match="edge_allocation_unit"):
        config(edge_allocation_unit=d("0.000000"))
    with pytest.raises(ValueError, match="rows must be sorted"):
        module.StrategyFeeAdjustedPositionSizingGateV2Report(
            generated_at=GENERATED_AT,
            config_version="strategy-fee-adjusted-position-sizing-gate-v2",
            candidate_count=d("2"),
            row_count=d("2"),
            ready_count=d("1"),
            watch_count=d("1"),
            blocked_count=d("0"),
            total_max_paper_allocation_usdc=d("52.000000"),
            rows=(
                report(candidate(candidate_id="watch", current_category_exposure_usdc=d("298.000000"))).rows[0],
                report(candidate(candidate_id="ready")).rows[0],
            ),
            reason_codes=("allocation_ready",),
        )


def test_module_scope_has_no_io_or_action_surface() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8")
    lowered_source = source.lower()

    for forbidden in FORBIDDEN_PUBLIC_FRAGMENTS:
        assert forbidden not in lowered_source

    blocked_snippets = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "web3",
        "clob",
        "private_key",
        "secret",
        "place_",
        "execute",
        "subprocess",
        "open(",
        "Path(",
    )
    assert not any(snippet in lowered_source for snippet in blocked_snippets)

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
