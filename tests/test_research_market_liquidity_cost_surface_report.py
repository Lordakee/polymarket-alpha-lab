from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_liquidity_cost_surface_report import (
    LiquidityCostSurfaceConfig,
    LiquidityCostSurfaceObservation,
    LiquidityCostSurfaceReport,
    LiquidityCostSurfaceReportDigest,
    build_research_market_liquidity_cost_surface_report,
    research_market_liquidity_cost_surface_report_digest,
    research_market_liquidity_cost_surface_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> LiquidityCostSurfaceConfig:
    values = {
        "config_version": "research-market-liquidity-cost-surface-report-v0",
        "watch_total_cost_threshold": d("0.030000"),
        "block_total_cost_threshold": d("0.060000"),
        "watch_settlement_wait_seconds": d("3600"),
        "block_settlement_wait_seconds": d("86400"),
    }
    values.update(overrides)
    return LiquidityCostSurfaceConfig(**values)


def observation(
    index: int,
    *,
    fee_rate: Decimal = d("0.005000"),
    spread_cost: Decimal = d("0.004000"),
    depth_cost: Decimal = d("0.003000"),
    slippage_cost: Decimal = d("0.004000"),
    settlement_wait_seconds: Decimal = d("900"),
    manual_review_required: bool = False,
    source_missing: bool = False,
    upstream_reason_codes: tuple[str, ...] = (),
) -> LiquidityCostSurfaceObservation:
    return LiquidityCostSurfaceObservation(
        public_surface_key=f"surface-{index:03d}",
        observed_at=GENERATED_AT,
        fee_rate=fee_rate,
        spread_cost=spread_cost,
        depth_cost=depth_cost,
        slippage_cost=slippage_cost,
        settlement_wait_seconds=settlement_wait_seconds,
        manual_review_required=manual_review_required,
        source_missing=source_missing,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(
    rows: tuple[LiquidityCostSurfaceObservation, ...],
    *,
    cfg: LiquidityCostSurfaceConfig | None = None,
) -> LiquidityCostSurfaceReport:
    return build_research_market_liquidity_cost_surface_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_low_cost_surface_passes_with_deterministic_public_payload() -> None:
    surface_report = report(
        (
            observation(2, upstream_reason_codes=("thin_order_book",)),
            observation(1),
        ),
    )

    payload = research_market_liquidity_cost_surface_report_payload(surface_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert type(surface_report) is LiquidityCostSurfaceReport
    assert surface_report.status == "pass"
    assert surface_report.input_count == d("2")
    assert surface_report.row_count == d("2")
    assert surface_report.pass_count == d("2")
    assert surface_report.watch_count == d("0")
    assert surface_report.blocked_count == d("0")
    assert surface_report.max_total_cost == d("0.016000")
    assert surface_report.max_settlement_wait_seconds == d("900")
    assert surface_report.reason_codes == ("liquidity_cost_surface_pass",)
    assert tuple(row.public_surface_key for row in surface_report.rows) == (
        "surface-001",
        "surface-002",
    )
    assert surface_report.rows[0].total_cost == d("0.016000")
    assert surface_report.rows[0].status == "pass"
    assert surface_report.rows[0].reason_codes == (
        "liquidity_cost_surface_pass",
    )
    assert surface_report.rows[1].reason_codes == (
        "liquidity_cost_surface_pass",
        "input_thin_order_book",
    )
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["total_cost"] == "0.016000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded


def test_watch_surface_combines_fees_spread_depth_slippage_and_wait() -> None:
    surface_report = report(
        (
            observation(
                1,
                fee_rate=d("0.010000"),
                spread_cost=d("0.012000"),
                depth_cost=d("0.008000"),
                slippage_cost=d("0.005000"),
                settlement_wait_seconds=d("7200"),
            ),
        ),
    )

    row = surface_report.rows[0]

    assert surface_report.status == "watch"
    assert surface_report.watch_count == d("1")
    assert surface_report.blocked_count == d("0")
    assert surface_report.reason_codes == (
        "liquidity_cost_surface_watch",
        "settlement_wait_watch",
    )
    assert row.total_cost == d("0.035000")
    assert row.status == "watch"
    assert row.reason_codes == (
        "liquidity_cost_surface_watch",
        "settlement_wait_watch",
    )


def test_block_surface_for_high_cost_missing_source_and_manual_review() -> None:
    surface_report = report(
        (
            observation(
                1,
                fee_rate=d("0.020000"),
                spread_cost=d("0.015000"),
                depth_cost=d("0.014000"),
                slippage_cost=d("0.012000"),
                settlement_wait_seconds=d("90000"),
                manual_review_required=True,
                source_missing=True,
                upstream_reason_codes=("operator_review",),
            ),
        ),
    )

    row = surface_report.rows[0]

    assert surface_report.status == "block"
    assert surface_report.blocked_count == d("1")
    assert surface_report.reason_codes == (
        "liquidity_cost_surface_block",
        "manual_review_required",
        "settlement_wait_block",
        "source_missing",
    )
    assert row.total_cost == d("0.061000")
    assert row.status == "block"
    assert row.reason_codes == (
        "liquidity_cost_surface_block",
        "input_operator_review",
        "manual_review_required",
        "settlement_wait_block",
        "source_missing",
    )


def test_decimal_type_rejection_and_datetime_validation_are_strict() -> None:
    with pytest.raises(ValueError, match="fee_rate"):
        observation(1, fee_rate=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_cost"):
        observation(1, spread_cost=_DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="observed_at"):
        replace(observation(1), observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_market_liquidity_cost_surface_report(
            (observation(1),),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="manual_review_required"):
        replace(observation(1), manual_review_required=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_total_cost_threshold"):
        config(watch_total_cost_threshold=d("0.070000"))


def test_public_leak_rejection_blocks_sensitive_keys_values_and_language() -> None:
    forbidden_values = (
        ("public_surface_key", "candidate-123"),
        ("public_surface_key", "market-slug-abc"),
        ("public_surface_key", "question: will event happen"),
        ("upstream_reason_codes", ("source_url",)),
        ("upstream_reason_codes", ("wallet_exposure",)),
        ("upstream_reason_codes", ("buy_signal",)),
    )

    for field_name, unsafe_value in forbidden_values:
        with pytest.raises(ValueError):
            replace(observation(1), **{field_name: unsafe_value})

    surface_report = report((observation(1),))
    payload = research_market_liquidity_cost_surface_report_payload(surface_report)
    unsafe_payload = dict(payload)
    unsafe_payload["wallet_address"] = "0xabc"
    with pytest.raises(ValueError, match="unsafe"):
        research_market_liquidity_cost_surface_report_payload(unsafe_payload)  # type: ignore[arg-type]


def test_hard_flags_are_required_for_config_rows_report_and_digest() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(observation(1), report_only=False)

    surface_report = report((observation(1),))

    with pytest.raises(ValueError, match="readonly"):
        replace(surface_report, readonly=False)

    surface_digest = research_market_liquidity_cost_surface_report_digest(surface_report)
    with pytest.raises(ValueError, match="paper_only"):
        replace(surface_digest, paper_only=False)


def test_payload_digest_and_report_are_deterministic_and_consistent() -> None:
    left = report(
        (
            observation(3, fee_rate=d("0.001000")),
            observation(1, fee_rate=d("0.001000")),
            observation(2, fee_rate=d("0.001000")),
        ),
    )
    right = report(
        (
            observation(2, fee_rate=d("0.001000")),
            observation(3, fee_rate=d("0.001000")),
            observation(1, fee_rate=d("0.001000")),
        ),
    )

    left_payload = research_market_liquidity_cost_surface_report_payload(left)
    right_payload = research_market_liquidity_cost_surface_report_payload(right)
    left_digest = research_market_liquidity_cost_surface_report_digest(left)
    right_digest = research_market_liquidity_cost_surface_report_digest(right)

    assert left_payload == right_payload
    assert type(left_digest) is LiquidityCostSurfaceReportDigest
    assert left_digest == right_digest
    assert left_digest.report_digest == left.derived_validation_digest
    assert left_digest.report_status == left.status
    assert left_digest.reason_codes == left.reason_codes
    assert left_digest.payload == research_market_liquidity_cost_surface_report_payload(
        left_digest,
    )

    with pytest.raises(ValueError, match="match report"):
        replace(left, derived_validation_digest="0" * 64)


def test_public_dataclasses_are_frozen() -> None:
    surface_report = report((observation(1),))

    with pytest.raises(FrozenInstanceError):
        surface_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        surface_report.rows[0].total_cost = d("0")  # type: ignore[misc]


def test_owned_module_has_no_network_filesystem_wallet_or_order_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_liquidity_cost_surface_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "dsn",
        "token",
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
