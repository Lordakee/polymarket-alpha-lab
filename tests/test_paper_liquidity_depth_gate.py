from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_liquidity_depth_gate import (
    PaperLiquidityDepthGateConfig,
    PaperLiquidityDepthGateInput,
    PaperLiquidityDepthGateReport,
    PaperLiquidityDepthGateRow,
    build_paper_liquidity_depth_gate_report,
)


GENERATED_AT = datetime(2026, 6, 19, 13, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def depth_input(
    *,
    market_slug: str = "event-alpha",
    side: str = "yes",
    action: str = "recommend",
    requested_paper_shares: Decimal = d("100.000000"),
    executable_paper_shares: Decimal = d("100.000000"),
    max_executable_shares: Decimal = d("100.000000"),
    side_price: Decimal = d("0.570000"),
    spread_cost_per_share: Decimal = d("0.002000"),
    reason_codes: tuple[str, ...] = ("side_edge_recommend",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperLiquidityDepthGateInput:
    return PaperLiquidityDepthGateInput(
        market_slug=market_slug,
        side=side,
        action=action,
        requested_paper_shares=requested_paper_shares,
        executable_paper_shares=executable_paper_shares,
        max_executable_shares=max_executable_shares,
        side_price=side_price,
        spread_cost_per_share=spread_cost_per_share,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(
    *,
    min_depth_fill_ratio: Decimal = d("0.750000"),
    max_spread_cost_per_share: Decimal = d("0.010000"),
    shallow_depth_penalty_per_share: Decimal = d("0.004000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperLiquidityDepthGateConfig:
    return PaperLiquidityDepthGateConfig(
        config_version="paper-liquidity-depth-gate-v0",
        min_depth_fill_ratio=min_depth_fill_ratio,
        max_spread_cost_per_share=max_spread_cost_per_share,
        shallow_depth_penalty_per_share=shallow_depth_penalty_per_share,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    *inputs: PaperLiquidityDepthGateInput,
    gate_config: PaperLiquidityDepthGateConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperLiquidityDepthGateReport:
    return build_paper_liquidity_depth_gate_report(
        inputs,
        config=gate_config or config(),
        generated_at=generated_at,
    )


def field_values(instance):
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_depth_gate_passes_full_depth_and_preserves_report_only_flags():
    report = build_report(
        depth_input(
            market_slug="event-pass",
            requested_paper_shares=d("100.000000"),
            executable_paper_shares=d("100.000000"),
            max_executable_shares=d("120.000000"),
            spread_cost_per_share=d("0.002000"),
            reason_codes=("ranked", "side_edge_recommend"),
        ),
    )

    assert type(report) is PaperLiquidityDepthGateReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-liquidity-depth-gate-v0"
    assert report.input_count == 1
    assert report.row_count == 1
    assert report.pass_count == 1
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    row = report.rows[0]
    assert row.market_slug == "event-pass"
    assert row.side == "yes"
    assert row.action == "recommend"
    assert row.requested_paper_shares == d("100.000000")
    assert row.executable_paper_shares == d("100.000000")
    assert row.max_executable_shares == d("120.000000")
    assert row.side_price == d("0.570000")
    assert row.spread_cost_per_share == d("0.002000")
    assert row.fill_ratio == d("1.000000")
    assert row.liquidity_status == "pass"
    assert row.liquidity_cost_per_share == d("0.002000")
    assert row.reason_codes == (
        "liquidity_depth_pass",
        "ranked",
        "side_edge_recommend",
    )
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_depth_gate_watches_shallow_but_executable_depth_with_penalty_cost():
    report = build_report(
        depth_input(
            market_slug="event-watch",
            requested_paper_shares=d("100.000000"),
            executable_paper_shares=d("50.000000"),
            max_executable_shares=d("50.000000"),
            spread_cost_per_share=d("0.003000"),
        ),
    )

    row = report.rows[0]
    assert row.fill_ratio == d("0.500000")
    assert row.liquidity_status == "watch"
    assert row.liquidity_cost_per_share == d("0.007000")
    assert row.reason_codes == (
        "below_min_depth_fill_ratio",
        "side_edge_recommend",
    )
    assert report.pass_count == 0
    assert report.watch_count == 1
    assert report.blocked_count == 0


def test_depth_gate_blocks_zero_depth_and_reject_actions():
    report = build_report(
        depth_input(
            market_slug="zero-depth",
            requested_paper_shares=d("100.000000"),
            executable_paper_shares=ZERO,
            max_executable_shares=ZERO,
            spread_cost_per_share=d("0.001000"),
        ),
        depth_input(
            market_slug="upstream-reject",
            action="reject",
            requested_paper_shares=d("100.000000"),
            executable_paper_shares=d("100.000000"),
            max_executable_shares=d("100.000000"),
        ),
    )

    zero_depth = next(row for row in report.rows if row.market_slug == "zero-depth")
    assert zero_depth.fill_ratio == ZERO
    assert zero_depth.liquidity_status == "blocked"
    assert zero_depth.liquidity_cost_per_share == d("0.005000")
    assert zero_depth.reason_codes == (
        "no_executable_depth",
        "side_edge_recommend",
    )

    upstream_reject = next(
        row for row in report.rows if row.market_slug == "upstream-reject"
    )
    assert upstream_reject.fill_ratio == d("1.000000")
    assert upstream_reject.liquidity_status == "blocked"
    assert upstream_reject.reason_codes == (
        "liquidity_depth_pass",
        "side_edge_recommend",
        "upstream_reject_action",
    )
    assert report.blocked_count == 2


def test_depth_gate_marks_wide_spread_as_watch_after_passing_depth():
    report = build_report(
        depth_input(
            market_slug="wide-spread",
            requested_paper_shares=d("100.000000"),
            executable_paper_shares=d("100.000000"),
            max_executable_shares=d("100.000000"),
            spread_cost_per_share=d("0.012000"),
        ),
    )

    row = report.rows[0]
    assert row.fill_ratio == d("1.000000")
    assert row.liquidity_status == "watch"
    assert row.liquidity_cost_per_share == d("0.012000")
    assert row.reason_codes == (
        "side_edge_recommend",
        "spread_cost_above_limit",
    )


def test_depth_gate_sorts_rows_deterministically_by_status_depth_cost_and_identity():
    report = build_report(
        depth_input(
            market_slug="zeta-pass",
            executable_paper_shares=d("100.000000"),
            max_executable_shares=d("100.000000"),
            spread_cost_per_share=d("0.001000"),
        ),
        depth_input(
            market_slug="alpha-watch",
            executable_paper_shares=d("50.000000"),
            max_executable_shares=d("50.000000"),
            spread_cost_per_share=d("0.003000"),
        ),
        depth_input(
            market_slug="beta-watch",
            executable_paper_shares=d("50.000000"),
            max_executable_shares=d("50.000000"),
            spread_cost_per_share=d("0.002000"),
        ),
        depth_input(
            market_slug="delta-blocked",
            executable_paper_shares=ZERO,
            max_executable_shares=ZERO,
            spread_cost_per_share=d("0.001000"),
        ),
    )

    assert tuple((row.liquidity_status, row.market_slug) for row in report.rows) == (
        ("pass", "zeta-pass"),
        ("watch", "beta-watch"),
        ("watch", "alpha-watch"),
        ("blocked", "delta-blocked"),
    )


def test_depth_gate_quantizes_decimals_and_normalizes_generated_at_to_utc():
    eastern = timezone(timedelta(hours=-4))
    report = build_paper_liquidity_depth_gate_report(
        [
            depth_input(
                requested_paper_shares=d("3.0000004"),
                executable_paper_shares=d("1.0000004"),
                max_executable_shares=d("1.0000004"),
                side_price=d("0.5700004"),
                spread_cost_per_share=d("0.0010004"),
            ),
        ],
        config=config(
            min_depth_fill_ratio=d("0.333334"),
            max_spread_cost_per_share=d("0.0100004"),
            shallow_depth_penalty_per_share=d("0.0040004"),
        ),
        generated_at=datetime(2026, 6, 19, 9, 0, tzinfo=eastern),
    )

    row = report.rows[0]
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert row.requested_paper_shares == d("3.000000")
    assert row.executable_paper_shares == d("1.000000")
    assert row.max_executable_shares == d("1.000000")
    assert row.side_price == d("0.570000")
    assert row.spread_cost_per_share == d("0.001000")
    assert row.fill_ratio == d("0.333333")
    assert row.liquidity_cost_per_share == d("0.005000")
    assert row.liquidity_status == "watch"


def test_depth_gate_rejects_non_decimal_and_inconsistent_share_values():
    with pytest.raises(ValueError, match="side_price"):
        replace(depth_input(), side_price=0.57)
    with pytest.raises(ValueError, match="spread_cost_per_share"):
        replace(depth_input(), spread_cost_per_share=Decimal("-0.000001"))
    with pytest.raises(ValueError, match="min_depth_fill_ratio"):
        config(min_depth_fill_ratio=Decimal("1.000001"))
    with pytest.raises(ValueError, match="shallow_depth_penalty_per_share"):
        config(shallow_depth_penalty_per_share=0.004)
    with pytest.raises(ValueError, match="executable_paper_shares"):
        depth_input(
            requested_paper_shares=d("100.000000"),
            executable_paper_shares=d("120.000000"),
            max_executable_shares=d("120.000000"),
        )
    with pytest.raises(ValueError, match="max_executable_shares"):
        depth_input(
            requested_paper_shares=d("100.000000"),
            executable_paper_shares=d("90.000000"),
            max_executable_shares=d("80.000000"),
        )


def test_depth_gate_direct_constructors_validate_consistency_and_flags():
    report = build_report(depth_input())
    rebuilt_row = PaperLiquidityDepthGateRow(**field_values(report.rows[0]))
    assert rebuilt_row == report.rows[0]
    sorted_report = build_report(
        depth_input(market_slug="zeta-pass"),
        depth_input(
            market_slug="alpha-watch",
            executable_paper_shares=d("50.000000"),
            max_executable_shares=d("50.000000"),
        ),
    )

    with pytest.raises(ValueError, match="fill_ratio"):
        replace(report.rows[0], fill_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="liquidity_cost_per_share"):
        replace(report.rows[0], liquidity_cost_per_share=d("0.999999"))
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=2)
    with pytest.raises(ValueError, match="rows"):
        replace(sorted_report, rows=tuple(reversed(sorted_report.rows)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(depth_input(), readonly=False)


def test_depth_gate_dataclasses_are_frozen_and_build_rejects_bad_public_types():
    input_row = depth_input()
    cfg = config()
    report = build_report(input_row)

    with pytest.raises(FrozenInstanceError):
        input_row.side = "no"
    with pytest.raises(FrozenInstanceError):
        cfg.min_depth_fill_ratio = d("0.500000")
    with pytest.raises(FrozenInstanceError):
        report.rows[0].liquidity_status = "blocked"
    with pytest.raises(FrozenInstanceError):
        report.rows = ()

    with pytest.raises(ValueError, match="config"):
        build_paper_liquidity_depth_gate_report(
            [input_row],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_liquidity_depth_gate_report(
            [input_row],
            config=cfg,
            generated_at="2026-06-19T13:00:00Z",
        )
    with pytest.raises(ValueError, match="inputs"):
        build_paper_liquidity_depth_gate_report(
            [object()],
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        build_paper_liquidity_depth_gate_report(
            [input_row],
            config=replace(cfg, paper_only=False),
            generated_at=GENERATED_AT,
        )


def test_depth_gate_returns_empty_report_for_empty_safe_input():
    report = build_report()

    assert report.input_count == 0
    assert report.row_count == 0
    assert report.pass_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.rows == ()
    assert report.generated_at == GENERATED_AT
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
