from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_cost_shock_resilience_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_COST_SHOCK_RESILIENCE_REPORT_CONFIG_VERSION
        ),
        "max_pass_spread_widening": d("0.020000"),
        "max_watch_spread_widening": d("0.060000"),
        "max_pass_depth_decay": d("0.150000"),
        "max_watch_depth_decay": d("0.450000"),
        "max_pass_fee_drag": d("0.010000"),
        "max_watch_fee_drag": d("0.030000"),
        "min_pass_slippage_cushion": d("0.120000"),
        "min_watch_slippage_cushion": d("0.050000"),
        "max_pass_volatility": d("0.200000"),
        "max_watch_volatility": d("0.500000"),
        "max_pass_book_age_seconds": d("120.000000"),
        "max_watch_book_age_seconds": d("600.000000"),
        "max_pass_settlement_friction": d("0.010000"),
        "max_watch_settlement_friction": d("0.030000"),
        "pass_resilience_score": d("0.750000"),
        "watch_resilience_score": d("0.450000"),
        "spread_weight": d("0.150000"),
        "depth_weight": d("0.200000"),
        "fee_weight": d("0.150000"),
        "slippage_weight": d("0.150000"),
        "volatility_weight": d("0.150000"),
        "book_age_weight": d("0.100000"),
        "settlement_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchMarketCostShockResilienceConfig(**values)


def observation(
    shock_case_key: str = "raw-market-id-pass",
    *,
    observed_at: datetime | None = None,
    last_book_update_at: datetime | None = None,
    current_spread: Decimal = d("0.020000"),
    stressed_spread: Decimal = d("0.030000"),
    baseline_depth: Decimal = d("100.000000"),
    stressed_depth: Decimal = d("90.000000"),
    fee_drag: Decimal = d("0.005000"),
    slippage_cushion: Decimal = d("0.150000"),
    volatility: Decimal = d("0.100000"),
    settlement_friction: Decimal = d("0.005000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketCostShockResilienceObservation(
        shock_case_key=shock_case_key,
        observed_at=observed_at or GENERATED_AT - timedelta(seconds=45),
        last_book_update_at=last_book_update_at or GENERATED_AT - timedelta(seconds=45),
        current_spread=current_spread,
        stressed_spread=stressed_spread,
        baseline_depth=baseline_depth,
        stressed_depth=stressed_depth,
        fee_drag=fee_drag,
        slippage_cushion=slippage_cushion,
        volatility=volatility,
        settlement_friction=settlement_friction,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_cost_shock_resilience_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_cost_shock_resilience_review() -> None:
    module = api()
    resilience = report()

    assert module.COST_SHOCK_RESILIENCE_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "COST_SHOCK_RESILIENCE_STATUSES",
        "DEFAULT_RESEARCH_MARKET_COST_SHOCK_RESILIENCE_REPORT_CONFIG_VERSION",
        "ResearchMarketCostShockResilienceConfig",
        "ResearchMarketCostShockResilienceObservation",
        "ResearchMarketCostShockResilienceReasonCodeCount",
        "ResearchMarketCostShockResilienceReport",
        "ResearchMarketCostShockResilienceRow",
        "build_research_market_cost_shock_resilience_report",
        "research_market_cost_shock_resilience_report_digest",
        "research_market_cost_shock_resilience_report_payload",
    )
    assert type(resilience) is module.ResearchMarketCostShockResilienceReport
    assert is_dataclass(resilience)
    assert resilience.generated_at == GENERATED_AT
    assert (
        resilience.config_version
        == "research-market-cost-shock-resilience-report-v0"
    )
    assert resilience.input_count == ZERO
    assert resilience.pass_count == ZERO
    assert resilience.watch_count == ZERO
    assert resilience.block_count == ZERO
    assert resilience.average_cost_shock_resilience_score is None
    assert resilience.max_spread_widening == ZERO
    assert resilience.max_depth_decay == ZERO
    assert resilience.max_fee_drag == ZERO
    assert resilience.min_slippage_cushion == ZERO
    assert resilience.max_volatility == ZERO
    assert resilience.max_book_age_seconds == ZERO
    assert resilience.max_settlement_friction == ZERO
    assert resilience.status == "block"
    assert resilience.reason_codes == ("no_cost_shock_resilience_observations",)
    assert resilience.reason_code_counts == (
        module.ResearchMarketCostShockResilienceReasonCodeCount(
            reason_code="no_cost_shock_resilience_observations",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert resilience.rows == ()
    assert resilience.paper_only is True
    assert resilience.report_only is True
    assert resilience.readonly is True


def test_scores_pass_watch_and_block_cost_shock_observations() -> None:
    resilience = report(
        observation(
            "raw-market-id-watch",
            last_book_update_at=GENERATED_AT - timedelta(seconds=180),
            current_spread=d("0.020000"),
            stressed_spread=d("0.050000"),
            baseline_depth=d("100.000000"),
            stressed_depth=d("80.000000"),
            fee_drag=d("0.015000"),
            slippage_cushion=d("0.090000"),
            volatility=d("0.300000"),
            settlement_friction=d("0.015000"),
        ),
        observation(
            "raw-market-id-block",
            last_book_update_at=GENERATED_AT - timedelta(seconds=700),
            current_spread=d("0.020000"),
            stressed_spread=d("0.090000"),
            baseline_depth=d("100.000000"),
            stressed_depth=d("40.000000"),
            fee_drag=d("0.040000"),
            slippage_cushion=d("0.030000"),
            volatility=d("0.700000"),
            settlement_friction=d("0.050000"),
            reason_codes=("manual_cost_review",),
        ),
        observation("raw-market-id-pass"),
    )

    assert resilience.input_count == d("3.000000")
    assert resilience.pass_count == d("1.000000")
    assert resilience.watch_count == d("1.000000")
    assert resilience.block_count == d("1.000000")
    assert resilience.average_cost_shock_resilience_score == d("0.480833")
    assert resilience.max_spread_widening == d("0.070000")
    assert resilience.max_depth_decay == d("0.600000")
    assert resilience.max_fee_drag == d("0.040000")
    assert resilience.min_slippage_cushion == d("0.030000")
    assert resilience.max_volatility == d("0.700000")
    assert resilience.max_book_age_seconds == d("700.000000")
    assert resilience.max_settlement_friction == d("0.050000")
    assert resilience.status == "block"

    block_row, pass_row, watch_row = resilience.rows
    assert tuple(row.resilience_group_ref for row in resilience.rows) == (
        "cost_shock_group_001",
        "cost_shock_group_002",
        "cost_shock_group_003",
    )
    assert tuple(row.status for row in resilience.rows) == ("block", "pass", "watch")
    assert block_row.spread_widening == d("0.070000")
    assert block_row.depth_decay == d("0.600000")
    assert block_row.book_age_seconds == d("700.000000")
    assert block_row.cost_shock_resilience_score == d("0.037500")
    assert block_row.reason_codes == (
        "book_age_block",
        "cost_shock_resilience_block",
        "depth_decay_block",
        "fee_drag_block",
        "input_manual_cost_review",
        "settlement_friction_block",
        "slippage_cushion_block",
        "spread_widening_block",
        "volatility_block",
    )
    assert pass_row.spread_widening == d("0.010000")
    assert pass_row.depth_decay == d("0.100000")
    assert pass_row.book_age_seconds == d("45.000000")
    assert pass_row.cost_shock_resilience_score == d("0.851389")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == (
        "book_age_pass",
        "cost_shock_resilience_pass",
        "depth_decay_pass",
        "fee_drag_pass",
        "settlement_friction_pass",
        "slippage_cushion_pass",
        "spread_widening_pass",
        "volatility_pass",
    )
    assert watch_row.spread_widening == d("0.030000")
    assert watch_row.depth_decay == d("0.200000")
    assert watch_row.book_age_seconds == d("180.000000")
    assert watch_row.cost_shock_resilience_score == d("0.553611")
    assert watch_row.status == "watch"
    assert "spread_widening_watch" in watch_row.reason_codes
    assert "depth_decay_watch" in watch_row.reason_codes
    assert "fee_drag_watch" in watch_row.reason_codes
    assert "slippage_cushion_watch" in watch_row.reason_codes
    assert "volatility_watch" in watch_row.reason_codes
    assert "book_age_watch" in watch_row.reason_codes
    assert "settlement_friction_watch" in watch_row.reason_codes


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        observation("raw-candidate-id-z", reason_codes=("zeta", "alpha")),
        observation("raw-candidate-id-a"),
    )
    second = report(
        observation("raw-candidate-id-a"),
        observation("raw-candidate-id-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_cost_shock_resilience_report_payload(first)
    second_payload = module.research_market_cost_shock_resilience_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert module.research_market_cost_shock_resilience_report_digest(first) == (
        module.research_market_cost_shock_resilience_report_digest(second)
    )
    assert len(module.research_market_cost_shock_resilience_report_digest(first)) == 64
    int(module.research_market_cost_shock_resilience_report_digest(first), 16)
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["rows"][0]["resilience_group_ref"] == "cost_shock_group_001"
    assert first_payload["rows"][0]["current_spread"] == "0.020000"
    assert first_payload["rows"][0]["cost_shock_resilience_score"] == "0.851389"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert "raw-candidate-id-a" not in encoded
    assert "raw-candidate-id-z" not in encoded
    assert "market-id" not in encoded
    assert not any(
        _has_forbidden_public_surface_key(key)
        for key in _walk_payload_keys(first_payload)
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_digest_tampering() -> None:
    module = api()
    populated = report(observation())

    for value in (config(), observation(), populated, *populated.rows, *populated.reason_code_counts):
        assert is_dataclass(value)
    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].cost_shock_resilience_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="current_spread"):
        observation(current_spread=0.02)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fee_drag"):
        observation(fee_drag=DecimalSubclass("0.005000"))
    with pytest.raises(ValueError, match="baseline_depth"):
        observation(baseline_depth=ZERO)
    with pytest.raises(ValueError, match="stressed_spread"):
        observation(current_spread=d("0.040000"), stressed_spread=d("0.030000"))
    with pytest.raises(ValueError, match="volatility"):
        observation(volatility=d("1.010000"))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 8, 16, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(), generated_at=DatetimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="reason_codes"):
        observation(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="unsafe public"):
        observation(reason_codes=("market_id",))
    with pytest.raises(ValueError, match="unsafe public"):
        observation(reason_codes=("execution_route",))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="shock_case_key"):
        report(observation("duplicate-case"), observation("duplicate-case"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(populated.rows[0], status="blocked")
    with pytest.raises(ValueError, match="unsafe public"):
        replace(populated.rows[0], resilience_group_ref="market-id-leak")
    with pytest.raises(TypeError):
        type("ReportSubclass", (module.ResearchMarketCostShockResilienceReport,), {})


def test_public_export_revalidates_semantics_numeric_types_and_nested_flags() -> None:
    module = api()

    inconsistent = report(observation())
    object.__setattr__(inconsistent, "input_count", d("2.000000"))
    with pytest.raises(ValueError, match="input_count"):
        module.research_market_cost_shock_resilience_report_payload(inconsistent)

    non_decimal = report(observation())
    object.__setattr__(non_decimal, "input_count", 1)
    object.__setattr__(
        non_decimal,
        "derived_validation_digest",
        module._derived_report_digest(non_decimal),
    )
    with pytest.raises(ValueError, match="input_count"):
        module.research_market_cost_shock_resilience_report_payload(non_decimal)
    with pytest.raises(ValueError, match="input_count"):
        module.research_market_cost_shock_resilience_report_digest(non_decimal)

    row_flag_tampered = report(observation())
    object.__setattr__(row_flag_tampered.rows[0], "report_only", False)
    object.__setattr__(
        row_flag_tampered,
        "derived_validation_digest",
        module._derived_report_digest(row_flag_tampered),
    )
    with pytest.raises(ValueError, match=r"rows\[0\]\.report_only"):
        module.research_market_cost_shock_resilience_report_payload(row_flag_tampered)

    count_flag_tampered = report(observation())
    object.__setattr__(
        count_flag_tampered.reason_code_counts[0],
        "readonly",
        False,
    )
    object.__setattr__(
        count_flag_tampered,
        "derived_validation_digest",
        module._derived_report_digest(count_flag_tampered),
    )
    with pytest.raises(ValueError, match=r"reason_code_counts\[0\]\.readonly"):
        module.research_market_cost_shock_resilience_report_digest(
            count_flag_tampered,
        )


@pytest.mark.parametrize(
    ("target_type_name", "error_match"),
    (
        (
            "ResearchMarketCostShockResilienceReport",
            "canonical report payload schema",
        ),
        (
            "ResearchMarketCostShockResilienceRow",
            "canonical row payload schema",
        ),
        (
            "ResearchMarketCostShockResilienceReasonCodeCount",
            "canonical reason code count payload schema",
        ),
    ),
)
def test_public_payload_rejects_canonical_schema_drift(
    monkeypatch: pytest.MonkeyPatch,
    target_type_name: str,
    error_match: str,
) -> None:
    module = api()
    target_type = getattr(module, target_type_name)
    original_payload_value = module._payload_value

    def payload_with_extra_field(value: object) -> object:
        payload = original_payload_value(value)
        if type(value) is target_type:
            assert type(payload) is dict
            return {**payload, "diagnostic_note": "safe"}
        return payload

    monkeypatch.setattr(module, "_payload_value", payload_with_extra_field)
    built = report(observation())

    with pytest.raises(ValueError, match=error_match):
        module.research_market_cost_shock_resilience_report_payload(built)


def test_owned_module_has_no_network_storage_or_decision_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_cost_shock_resilience_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "postgres",
        "private_key",
        "place_order",
        "cancel_order",
        "order_size",
        "live_trading",
        "trade_recommendation",
        "connect(",
        "open(",
        "buy",
        "sell",
        "position",
        "sizing",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _has_forbidden_public_surface_key(key: str) -> bool:
    normalized = key.lower()
    forbidden_fragments = (
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "position",
        "sizing",
        "recommendation",
    )
    return any(fragment in normalized for fragment in forbidden_fragments)
