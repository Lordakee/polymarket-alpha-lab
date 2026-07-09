from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_liquidity_exit_cost_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_LIQUIDITY_EXIT_COST_DECAY_REPORT_CONFIG_VERSION
        ),
        "max_pass_exit_cost_rate": d("0.030000"),
        "max_watch_exit_cost_rate": d("0.070000"),
        "max_pass_liquidity_decay_ratio": d("0.250000"),
        "max_watch_liquidity_decay_ratio": d("0.600000"),
        "max_pass_quote_age_seconds": d("300.000000"),
        "max_watch_quote_age_seconds": d("900.000000"),
        "min_pass_exit_depth_ratio": d("0.750000"),
        "min_watch_exit_depth_ratio": d("0.400000"),
        "pass_liquidity_exit_cost_decay_score": d("0.750000"),
        "watch_liquidity_exit_cost_decay_score": d("0.450000"),
        "exit_cost_pressure_weight": d("0.350000"),
        "liquidity_decay_weight": d("0.250000"),
        "quote_freshness_weight": d("0.200000"),
        "exit_depth_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchMarketLiquidityExitCostDecayConfig(**values)


def observation(
    internal_liquidity_ref: str = "liquidity-ref-pass",
    *,
    observed_at: datetime | None = None,
    exit_fee_rate: Decimal = d("0.005000"),
    exit_spread_rate: Decimal = d("0.005000"),
    exit_slippage_rate: Decimal = d("0.005000"),
    baseline_exit_depth: Decimal = d("1000.000000"),
    current_exit_depth: Decimal = d("850.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketLiquidityExitCostDecayObservation(
        internal_liquidity_ref=internal_liquidity_ref,
        observed_at=observed_at or GENERATED_AT - timedelta(seconds=120),
        exit_fee_rate=exit_fee_rate,
        exit_spread_rate=exit_spread_rate,
        exit_slippage_rate=exit_slippage_rate,
        baseline_exit_depth=baseline_exit_depth,
        current_exit_depth=current_exit_depth,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_liquidity_exit_cost_decay_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_liquidity_exit_cost_decay_review() -> None:
    module = api()
    decay_report = report()

    assert module.MARKET_LIQUIDITY_EXIT_COST_DECAY_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "MARKET_LIQUIDITY_EXIT_COST_DECAY_STATUSES",
        "DEFAULT_RESEARCH_MARKET_LIQUIDITY_EXIT_COST_DECAY_REPORT_CONFIG_VERSION",
        "ResearchMarketLiquidityExitCostDecayConfig",
        "ResearchMarketLiquidityExitCostDecayObservation",
        "ResearchMarketLiquidityExitCostDecayReasonCodeCount",
        "ResearchMarketLiquidityExitCostDecayReport",
        "ResearchMarketLiquidityExitCostDecayRow",
        "build_research_market_liquidity_exit_cost_decay_report",
        "research_market_liquidity_exit_cost_decay_report_digest",
        "research_market_liquidity_exit_cost_decay_report_payload",
    )
    assert type(decay_report) is module.ResearchMarketLiquidityExitCostDecayReport
    assert is_dataclass(decay_report)
    assert decay_report.generated_at == GENERATED_AT
    assert decay_report.config_version == (
        "research-market-liquidity-exit-cost-decay-report-v0"
    )
    assert decay_report.observation_count == ZERO
    assert decay_report.pass_count == ZERO
    assert decay_report.watch_count == ZERO
    assert decay_report.block_count == ZERO
    assert decay_report.average_total_exit_cost_rate is None
    assert decay_report.average_liquidity_decay_ratio is None
    assert decay_report.average_liquidity_exit_cost_decay_score is None
    assert decay_report.max_quote_age_seconds == ZERO
    assert decay_report.max_total_exit_cost_rate == ZERO
    assert decay_report.max_liquidity_decay_ratio == ZERO
    assert decay_report.min_exit_depth_ratio == ZERO
    assert decay_report.status == "block"
    assert decay_report.reason_codes == ("no_liquidity_exit_cost_decay_observations",)
    assert decay_report.reason_code_counts == (
        module.ResearchMarketLiquidityExitCostDecayReasonCodeCount(
            reason_code="no_liquidity_exit_cost_decay_observations",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert decay_report.rows == ()
    assert decay_report.paper_only is True
    assert decay_report.report_only is True
    assert decay_report.readonly is True


def test_scores_pass_watch_and_block_liquidity_exit_cost_decay_observations() -> None:
    decay_report = report(
        observation(
            "liquidity-ref-watch",
            observed_at=GENERATED_AT - timedelta(seconds=420),
            exit_fee_rate=d("0.010000"),
            exit_spread_rate=d("0.015000"),
            exit_slippage_rate=d("0.010000"),
            baseline_exit_depth=d("600.000000"),
            current_exit_depth=d("300.000000"),
        ),
        observation(
            "liquidity-ref-block",
            observed_at=GENERATED_AT - timedelta(seconds=1200),
            exit_fee_rate=d("0.030000"),
            exit_spread_rate=d("0.030000"),
            exit_slippage_rate=d("0.030000"),
            baseline_exit_depth=d("100.000000"),
            current_exit_depth=d("20.000000"),
            reason_codes=("manual_decay_review",),
        ),
        observation("liquidity-ref-pass"),
    )

    assert decay_report.observation_count == d("3.000000")
    assert decay_report.pass_count == d("1.000000")
    assert decay_report.watch_count == d("1.000000")
    assert decay_report.block_count == d("1.000000")
    assert decay_report.average_total_exit_cost_rate == d("0.046667")
    assert decay_report.average_liquidity_decay_ratio == d("0.483333")
    assert decay_report.average_liquidity_exit_cost_decay_score == d("0.448611")
    assert decay_report.max_quote_age_seconds == d("1200.000000")
    assert decay_report.max_total_exit_cost_rate == d("0.090000")
    assert decay_report.max_liquidity_decay_ratio == d("0.800000")
    assert decay_report.min_exit_depth_ratio == d("0.200000")
    assert decay_report.status == "block"

    block_row, watch_row, pass_row = decay_report.rows
    assert tuple(row.public_row_ref for row in decay_report.rows) == (
        "liquidity_exit_cost_decay_row_001",
        "liquidity_exit_cost_decay_row_002",
        "liquidity_exit_cost_decay_row_003",
    )
    assert tuple(row.status for row in decay_report.rows) == ("block", "watch", "pass")
    assert block_row.quote_age_seconds == d("1200.000000")
    assert block_row.total_exit_cost_rate == d("0.090000")
    assert block_row.exit_depth_ratio == d("0.200000")
    assert block_row.liquidity_decay_ratio == d("0.800000")
    assert block_row.exit_cost_score == ZERO
    assert block_row.quote_freshness_score == ZERO
    assert block_row.exit_depth_score == d("0.266667")
    assert block_row.liquidity_exit_cost_decay_score == d("0.053333")
    assert block_row.reason_codes == (
        "exit_cost_pressure_block",
        "exit_depth_block",
        "input_manual_decay_review",
        "liquidity_decay_block",
        "liquidity_exit_cost_decay_block",
        "quote_freshness_block",
    )
    assert watch_row.total_exit_cost_rate == d("0.035000")
    assert watch_row.exit_depth_ratio == d("0.500000")
    assert watch_row.liquidity_decay_ratio == d("0.500000")
    assert watch_row.exit_cost_score == d("0.500000")
    assert watch_row.liquidity_decay_score == d("0.166667")
    assert watch_row.quote_freshness_score == d("0.533333")
    assert watch_row.exit_depth_score == d("0.666667")
    assert watch_row.liquidity_exit_cost_decay_score == d("0.456667")
    assert watch_row.reason_codes == (
        "exit_cost_pressure_watch",
        "exit_depth_watch",
        "liquidity_decay_watch",
        "liquidity_exit_cost_decay_watch",
        "quote_freshness_watch",
    )
    assert pass_row.total_exit_cost_rate == d("0.015000")
    assert pass_row.exit_depth_ratio == d("0.850000")
    assert pass_row.liquidity_decay_ratio == d("0.150000")
    assert pass_row.exit_cost_score == d("0.785714")
    assert pass_row.liquidity_decay_score == d("0.750000")
    assert pass_row.quote_freshness_score == d("0.866667")
    assert pass_row.exit_depth_score == d("1.000000")
    assert pass_row.liquidity_exit_cost_decay_score == d("0.835833")
    assert pass_row.reason_codes == (
        "exit_cost_pressure_pass",
        "exit_depth_pass",
        "liquidity_decay_pass",
        "liquidity_exit_cost_decay_pass",
        "quote_freshness_pass",
    )


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        observation("private-liquidity-ref-z", reason_codes=("zeta", "alpha")),
        observation("private-liquidity-ref-a"),
    )
    second = report(
        observation("private-liquidity-ref-a"),
        observation("private-liquidity-ref-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_liquidity_exit_cost_decay_report_payload(first)
    second_payload = module.research_market_liquidity_exit_cost_decay_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert module.research_market_liquidity_exit_cost_decay_report_digest(first) == (
        module.research_market_liquidity_exit_cost_decay_report_digest(second)
    )
    assert len(module.research_market_liquidity_exit_cost_decay_report_digest(first)) == 64
    int(module.research_market_liquidity_exit_cost_decay_report_digest(first), 16)
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["rows"][0]["public_row_ref"] == (
        "liquidity_exit_cost_decay_row_001"
    )
    assert first_payload["rows"][0]["exit_depth_ratio"] == "0.850000"
    assert first_payload["rows"][0]["liquidity_decay_ratio"] == "0.150000"
    assert first_payload["rows"][0]["liquidity_exit_cost_decay_score"] == "0.835833"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert "private-liquidity-ref-a" not in encoded
    assert "private-liquidity-ref-z" not in encoded
    assert not any(
        _has_forbidden_public_surface_key(key)
        for key in _walk_payload_keys(first_payload)
    )
    assert module.research_market_liquidity_exit_cost_decay_report_payload(
        dict(first_payload),
    ) == first_payload

    tampered = dict(first_payload)
    tampered["status"] = "block"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_liquidity_exit_cost_decay_report_payload(tampered)
    unsafe = dict(first_payload)
    unsafe["market_id"] = "0xabc"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_market_liquidity_exit_cost_decay_report_payload(unsafe)
    extra_safe_named_field = json.loads(json.dumps(first_payload))
    extra_safe_named_field["evidence"] = "0xabc123"
    _refresh_payload_digest(extra_safe_named_field)
    with pytest.raises(ValueError, match="public schema"):
        module.research_market_liquidity_exit_cost_decay_report_payload(
            extra_safe_named_field,
        )
    nested_extra_safe_named_field = json.loads(json.dumps(first_payload))
    nested_extra_safe_named_field["rows"][0]["evidence"] = "0xabc123"
    _refresh_payload_digest(nested_extra_safe_named_field)
    with pytest.raises(ValueError, match="public schema"):
        module.research_market_liquidity_exit_cost_decay_report_payload(
            nested_extra_safe_named_field,
        )
    nested_bad_flag = json.loads(json.dumps(first_payload))
    nested_bad_flag["rows"][0]["paper_only"] = False
    _refresh_payload_digest(nested_bad_flag)
    with pytest.raises(ValueError, match="paper_only"):
        module.research_market_liquidity_exit_cost_decay_report_payload(nested_bad_flag)


def test_validation_rejects_non_decimal_values_bad_flags_and_digest_tampering() -> None:
    module = api()
    populated = report(observation())

    for value in (config(), observation(), populated, *populated.rows, *populated.reason_code_counts):
        assert is_dataclass(value)
    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].liquidity_exit_cost_decay_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="exit_fee_rate"):
        observation(exit_fee_rate=0.005)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="exit_spread_rate"):
        observation(exit_spread_rate=DecimalSubclass("0.005000"))
    with pytest.raises(ValueError, match="baseline_exit_depth"):
        observation(baseline_exit_depth=DecimalSubclass("100.000000"))
    with pytest.raises(ValueError, match="current_exit_depth"):
        observation(current_exit_depth=d("1001.000000"))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            observation(),
            generated_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="reason_codes"):
        observation(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="unsafe public"):
        observation(reason_codes=("market_id",))
    with pytest.raises(ValueError, match="internal_liquidity_ref"):
        report(observation("duplicate-ref"), observation("duplicate-ref"))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="row_validation_digest"):
        replace(populated.rows[0], row_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(populated.rows[0], status="blocked")
    with pytest.raises(TypeError):
        type("ConfigSubclass", (module.ResearchMarketLiquidityExitCostDecayConfig,), {})


def test_owned_module_has_no_db_network_wallet_execution_or_decision_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_liquidity_exit_cost_decay_report.py"
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
        "wallet",
        "private_key",
        "auth",
        "place_order",
        "cancel_order",
        "order_size",
        "live_trading",
        "trade_recommendation",
        "sizing",
        "buy_",
        "sell_",
        "connect(",
        "open(",
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
        "buy",
        "sell",
        "size",
        "sizing",
        "recommendation",
    )
    return any(fragment in normalized for fragment in forbidden_fragments)


def _refresh_payload_digest(payload: dict[str, object]) -> None:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload["derived_validation_digest"] = sha256(encoded.encode("utf-8")).hexdigest()
