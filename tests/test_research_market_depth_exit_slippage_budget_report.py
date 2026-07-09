from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 45, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_market_depth_exit_slippage_budget_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_depth_exit_slippage_budget_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_DEPTH_EXIT_SLIPPAGE_BUDGET_REPORT_CONFIG_VERSION
        ),
        "minimum_depth_coverage_ratio": d("1.000000"),
        "depth_coverage_watch_threshold": d("0.750000"),
        "depth_coverage_block_threshold": d("0.350000"),
        "slippage_budget_utilization_watch_threshold": d("0.750000"),
        "slippage_budget_utilization_block_threshold": d("1.250000"),
        "spread_watch_threshold": d("0.030000"),
        "spread_block_threshold": d("0.070000"),
        "depth_decay_watch_threshold": d("0.200000"),
        "depth_decay_block_threshold": d("0.600000"),
        "exit_window_watch_hours": d("24.000000"),
        "exit_window_block_hours": d("72.000000"),
        "fee_drag_watch_threshold": d("0.015000"),
        "fee_drag_block_threshold": d("0.040000"),
        "watch_exit_slippage_budget_risk_score": d("0.350000"),
        "block_exit_slippage_budget_risk_score": d("0.700000"),
        "depth_coverage_weight": d("0.300000"),
        "slippage_budget_weight": d("0.300000"),
        "spread_weight": d("0.100000"),
        "depth_decay_weight": d("0.100000"),
        "exit_window_weight": d("0.100000"),
        "fee_drag_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchMarketDepthExitSlippageBudgetConfig(**values)


def observation(
    internal_observation_ref: str,
    *,
    planned_exit_notional: Decimal,
    available_exit_depth: Decimal,
    estimated_exit_slippage_rate: Decimal,
    slippage_budget_rate: Decimal,
    bid_ask_spread_rate: Decimal,
    depth_decay_rate: Decimal,
    exit_window_hours: Decimal,
    fee_drag_rate: Decimal,
    observed_at: datetime = OBSERVED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketDepthExitSlippageBudgetObservation(
        internal_observation_ref=internal_observation_ref,
        observed_at=observed_at,
        planned_exit_notional=planned_exit_notional,
        available_exit_depth=available_exit_depth,
        estimated_exit_slippage_rate=estimated_exit_slippage_rate,
        slippage_budget_rate=slippage_budget_rate,
        bid_ask_spread_rate=bid_ask_spread_rate,
        depth_decay_rate=depth_decay_rate,
        exit_window_hours=exit_window_hours,
        fee_drag_rate=fee_drag_rate,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*observations: object, cfg: object | None = None):
    module = api()
    return module.build_research_market_depth_exit_slippage_budget_report(
        observations,
        config=config() if cfg is None else cfg,
        generated_at=GENERATED_AT,
    )


def walk_payload(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            yield from walk_payload(item)
        return
    yield value


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_exit_slippage_budget_report_scores_sorts_and_aggregates_statuses() -> None:
    module = api()
    result = build_report(
        observation(
            "candidate-pass market-slug question https://example.invalid token=secret",
            planned_exit_notional=d("100.000000"),
            available_exit_depth=d("150.000000"),
            estimated_exit_slippage_rate=d("0.005000"),
            slippage_budget_rate=d("0.020000"),
            bid_ask_spread_rate=d("0.010000"),
            depth_decay_rate=d("0.050000"),
            exit_window_hours=d("6.000000"),
            fee_drag_rate=d("0.005000"),
        ),
        observation(
            "candidate-block market-id question dsn=postgres table=events",
            planned_exit_notional=d("100.000000"),
            available_exit_depth=d("20.000000"),
            estimated_exit_slippage_rate=d("0.035000"),
            slippage_budget_rate=d("0.020000"),
            bid_ask_spread_rate=d("0.080000"),
            depth_decay_rate=d("0.800000"),
            exit_window_hours=d("96.000000"),
            fee_drag_rate=d("0.050000"),
        ),
        observation(
            "candidate-watch market-slug source text wallet order trade",
            planned_exit_notional=d("100.000000"),
            available_exit_depth=d("60.000000"),
            estimated_exit_slippage_rate=d("0.018000"),
            slippage_budget_rate=d("0.020000"),
            bid_ask_spread_rate=d("0.040000"),
            depth_decay_rate=d("0.250000"),
            exit_window_hours=d("30.000000"),
            fee_drag_rate=d("0.020000"),
        ),
    )

    assert module.MARKET_DEPTH_EXIT_SLIPPAGE_BUDGET_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert type(result) is module.ResearchMarketDepthExitSlippageBudgetReport
    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.observation_count == d("3.000000")
    assert result.pass_count == ONE
    assert result.watch_count == ONE
    assert result.block_count == ONE
    assert result.min_depth_coverage_ratio == d("0.200000")
    assert result.max_slippage_budget_utilization_ratio == d("1.750000")
    assert result.max_exit_slippage_budget_risk_score == d("0.940000")
    assert result.average_exit_slippage_budget_risk_score == d("0.523310")
    assert result.status == "block"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    block_row, watch_row, pass_row = result.rows
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    assert tuple(row.public_row_ref for row in result.rows) == (
        "exit_slippage_budget_row_001",
        "exit_slippage_budget_row_002",
        "exit_slippage_budget_row_003",
    )
    assert block_row.depth_coverage_ratio == d("0.200000")
    assert block_row.slippage_budget_utilization_ratio == d("1.750000")
    assert block_row.exit_slippage_budget_risk_score == d("0.940000")
    assert block_row.reason_codes == (
        "depth_coverage_block",
        "depth_decay_block",
        "exit_window_block",
        "fee_drag_block",
        "slippage_budget_block",
        "spread_block",
    )
    assert watch_row.exit_slippage_budget_risk_score == d("0.526477")
    assert watch_row.reason_codes == (
        "depth_coverage_watch",
        "depth_decay_watch",
        "exit_window_watch",
        "fee_drag_watch",
        "slippage_budget_watch",
        "spread_watch",
    )
    assert pass_row.exit_slippage_budget_risk_score == d("0.103452")
    assert pass_row.reason_codes == ("exit_slippage_budget_pass",)
    assert_digest(block_row.row_validation_digest)
    assert_digest(result.derived_validation_digest)


def test_public_payload_is_deterministic_digest_bound_decimal_only_and_safe() -> None:
    module = api()
    raw_ref = (
        "candidate-alpha market-id market-slug raw question text "
        "https://example.invalid source_url=https://example.invalid "
        "source_text=secret dsn=postgres table=events token=secret wallet order trade"
    )
    first = build_report(
        observation(
            raw_ref,
            planned_exit_notional=d("100.000000"),
            available_exit_depth=d("20.000000"),
            estimated_exit_slippage_rate=d("0.035000"),
            slippage_budget_rate=d("0.020000"),
            bid_ask_spread_rate=d("0.080000"),
            depth_decay_rate=d("0.800000"),
            exit_window_hours=d("96.000000"),
            fee_drag_rate=d("0.050000"),
        ),
    )
    second = build_report(
        observation(
            raw_ref,
            observed_at=OBSERVED_AT.astimezone(timezone(timedelta(hours=-4))),
            planned_exit_notional=d("100.000000"),
            available_exit_depth=d("20.000000"),
            estimated_exit_slippage_rate=d("0.035000"),
            slippage_budget_rate=d("0.020000"),
            bid_ask_spread_rate=d("0.080000"),
            depth_decay_rate=d("0.800000"),
            exit_window_hours=d("96.000000"),
            fee_drag_rate=d("0.050000"),
        ),
    )

    payload = module.research_market_depth_exit_slippage_budget_report_payload(first)
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    encoded_digest_payload = json.dumps(
        digest_payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    encoded_payload = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert payload == module.research_market_depth_exit_slippage_budget_report_payload(
        second,
    )
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert module.research_market_depth_exit_slippage_budget_report_digest(first) == (
        first.derived_validation_digest
    )
    assert hashlib.sha256(encoded_digest_payload.encode("utf-8")).hexdigest() == (
        first.derived_validation_digest
    )
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["rows"][0]["available_exit_depth"] == "20.000000"
    assert payload["rows"][0]["internal_observation_ref_digest"] == (
        first.rows[0].internal_observation_ref_digest
    )
    assert raw_ref not in encoded_payload
    assert all(
        fragment not in encoded_payload.lower()
        for fragment in (
            "candidate-alpha",
            "market-id",
            "market_id",
            "market-slug",
            "market_slug",
            "raw question",
            "source_url",
            "source_text",
            "https://example.invalid",
            "dsn=postgres",
            "table=events",
            "token=secret",
            "wallet",
            "order",
            "trade",
            "live",
            "recommend",
            "sizing",
        )
    )
    assert not any(type(value) in (float, int) for value in walk_payload(payload))


def test_empty_input_blocks_without_public_raw_identifier_surface() -> None:
    result = build_report()

    assert result.observation_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.min_depth_coverage_ratio == ZERO
    assert result.max_slippage_budget_utilization_ratio == ZERO
    assert result.max_exit_slippage_budget_risk_score == ZERO
    assert result.average_exit_slippage_budget_risk_score is None
    assert result.status == "block"
    assert result.rows == ()
    assert result.reason_codes == ("missing_depth_exit_slippage_budget_observations",)
    assert_digest(result.derived_validation_digest)


def test_validation_enforces_frozen_decimal_only_flags_and_digest_contract() -> None:
    module = api()
    result = build_report(
        observation(
            "internal-alpha",
            planned_exit_notional=d("100.000000"),
            available_exit_depth=d("150.000000"),
            estimated_exit_slippage_rate=d("0.005000"),
            slippage_budget_rate=d("0.020000"),
            bid_ask_spread_rate=d("0.010000"),
            depth_decay_rate=d("0.050000"),
            exit_window_hours=d("6.000000"),
            fee_drag_rate=d("0.005000"),
        ),
    )

    assert is_dataclass(module.ResearchMarketDepthExitSlippageBudgetConfig)
    assert is_dataclass(module.ResearchMarketDepthExitSlippageBudgetObservation)
    assert is_dataclass(module.ResearchMarketDepthExitSlippageBudgetRow)
    assert is_dataclass(module.ResearchMarketDepthExitSlippageBudgetReport)
    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        observation(
            "internal-flags",
            planned_exit_notional=d("100.000000"),
            available_exit_depth=d("150.000000"),
            estimated_exit_slippage_rate=d("0.005000"),
            slippage_budget_rate=d("0.020000"),
            bid_ask_spread_rate=d("0.010000"),
            depth_decay_rate=d("0.050000"),
            exit_window_hours=d("6.000000"),
            fee_drag_rate=d("0.005000"),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="planned_exit_notional"):
        observation(
            "internal-decimal",
            planned_exit_notional=100,  # type: ignore[arg-type]
            available_exit_depth=d("150.000000"),
            estimated_exit_slippage_rate=d("0.005000"),
            slippage_budget_rate=d("0.020000"),
            bid_ask_spread_rate=d("0.010000"),
            depth_decay_rate=d("0.050000"),
            exit_window_hours=d("6.000000"),
            fee_drag_rate=d("0.005000"),
        )
    with pytest.raises(ValueError, match="available_exit_depth"):
        observation(
            "internal-decimal-subclass",
            planned_exit_notional=d("100.000000"),
            available_exit_depth=_DecimalSubclass("150.000000"),
            estimated_exit_slippage_rate=d("0.005000"),
            slippage_budget_rate=d("0.020000"),
            bid_ask_spread_rate=d("0.010000"),
            depth_decay_rate=d("0.050000"),
            exit_window_hours=d("6.000000"),
            fee_drag_rate=d("0.005000"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_depth_exit_slippage_budget_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_depth_exit_slippage_budget_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="internal_observation_ref values"):
        build_report(
            observation(
                "internal-dupe",
                planned_exit_notional=d("100.000000"),
                available_exit_depth=d("150.000000"),
                estimated_exit_slippage_rate=d("0.005000"),
                slippage_budget_rate=d("0.020000"),
                bid_ask_spread_rate=d("0.010000"),
                depth_decay_rate=d("0.050000"),
                exit_window_hours=d("6.000000"),
                fee_drag_rate=d("0.005000"),
            ),
            observation(
                "internal-dupe",
                planned_exit_notional=d("100.000000"),
                available_exit_depth=d("150.000000"),
                estimated_exit_slippage_rate=d("0.005000"),
                slippage_budget_rate=d("0.020000"),
                bid_ask_spread_rate=d("0.010000"),
                depth_decay_rate=d("0.050000"),
                exit_window_hours=d("6.000000"),
                fee_drag_rate=d("0.005000"),
            ),
        )
    with pytest.raises(ValueError, match="status"):
        replace(result.rows[0], status="halt")
    with pytest.raises(ValueError, match="status"):
        replace(result.rows[0], status=_StringSubclass("pass"))
    with pytest.raises(ValueError, match="status"):
        replace(result, status=_StringSubclass("pass"))
    with pytest.raises(ValueError, match="row_validation_digest"):
        replace(result.rows[0], row_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)


def test_owned_module_has_no_runtime_side_effect_or_advice_surface() -> None:
    module_text = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
    )

    assert all(term not in module_text for term in forbidden_terms)
