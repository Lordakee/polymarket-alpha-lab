from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventSideResult,
    PaperCostAwareEventStrategyGateResult,
    PaperCostAwareEventStrategyReport,
)
from polymarket_alpha_lab.liquidity_gate import (
    PaperLiquidityGateConfig,
    PaperLiquidityGateReport,
    PaperLiquidityGateRow,
    build_paper_liquidity_gate_report,
)


GENERATED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
GATE_NAMES = (
    "data_integrity",
    "confidence",
    "spread",
    "resolution_risk",
    "yes_depth",
    "no_depth",
    "edge_threshold",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


class _StringSubclass(str):
    pass


def _side_result(
    side: str,
    *,
    ask_size: Decimal | None,
    executable_price: Decimal | None = Decimal("0.4500"),
) -> PaperCostAwareEventSideResult:
    return PaperCostAwareEventSideResult(
        side=side,
        fair_probability=Decimal("0.5500") if side == "yes" else Decimal("0.4500"),
        executable_price=executable_price,
        ask_size=ask_size,
        gross_edge_per_share=Decimal("0.100000") if executable_price is not None else None,
        fee_cost_per_share=Decimal("0.005000") if executable_price is not None else None,
        non_fee_cost_per_share=Decimal("0.001000") if executable_price is not None else None,
        total_cost_per_share=Decimal("0.006000") if executable_price is not None else None,
        net_edge_per_share=Decimal("0.094000") if executable_price is not None else None,
        reason_codes=("paper_edge_complete",),
    )


def _gate_results() -> tuple[PaperCostAwareEventStrategyGateResult, ...]:
    return tuple(
        PaperCostAwareEventStrategyGateResult(
            gate_name=gate_name,
            status="pass",
            reason_code=f"{gate_name}_ready",
            message=f"{gate_name} ready.",
            observed_value="observed",
            threshold="threshold",
        )
        for gate_name in GATE_NAMES
    )


def _cost_aware_report(
    *,
    market_slug: str = "alpha-market",
    selected_side: str = "yes",
    spread: Decimal = Decimal("0.0200"),
    yes_ask_size: Decimal | None = Decimal("25.0000"),
    no_ask_size: Decimal | None = Decimal("25.0000"),
    paper_only: bool = True,
    report_only: bool = True,
) -> PaperCostAwareEventStrategyReport:
    return PaperCostAwareEventStrategyReport(
        generated_at=GENERATED_AT,
        config_version="cost-aware-event-v0",
        market_slug=market_slug,
        question=f"{market_slug} question?",
        fair_probability_yes=Decimal("0.5500"),
        confidence=Decimal("0.8000"),
        yes_bid=Decimal("0.4400"),
        no_bid=Decimal("0.4300"),
        spread=spread,
        resolution_risk=Decimal("0.1000"),
        selected_side=selected_side,
        status="paper_review_ready" if selected_side != "none" else "watch",
        yes_result=_side_result("yes", ask_size=yes_ask_size),
        no_result=_side_result("no", ask_size=no_ask_size),
        gate_results=_gate_results(),
        paper_only=paper_only,
        report_only=report_only,
    )


def _config(**overrides) -> PaperLiquidityGateConfig:
    values = {
        "config_version": "paper-liquidity-gate-v0",
        "max_spread": Decimal("0.0500"),
        "min_ask_size": Decimal("10.0000"),
        "min_depth_ready_count": 1,
        "max_missing_depth_count": 0,
    }
    values.update(overrides)
    return PaperLiquidityGateConfig(**values)


def _liquidity_report(
    *reports: PaperCostAwareEventStrategyReport,
    config: PaperLiquidityGateConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperLiquidityGateReport:
    return build_paper_liquidity_gate_report(
        reports,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_liquidity_gate_passes_ready_market_and_sets_hard_flags():
    report = _liquidity_report(_cost_aware_report())

    assert isinstance(report, PaperLiquidityGateReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-liquidity-gate-v0"
    assert report.status == "pass"
    assert report.reason_codes == ("liquidity_gate_passed",)
    assert report.market_count == 1
    assert report.pass_count == 1
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.depth_ready_count == 1
    assert report.missing_depth_count == 0
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert len(report.rows) == 1
    row = report.rows[0]
    assert row.market_slug == "alpha-market"
    assert row.selected_side == "yes"
    assert row.spread == Decimal("0.0200")
    assert row.selected_ask_size == Decimal("25.0000")
    assert row.status == "pass"
    assert row.reason_codes == ("liquidity_ready",)


def test_liquidity_gate_marks_high_spread_as_watch_without_blocking_depth():
    report = _liquidity_report(
        _cost_aware_report(market_slug="wide-spread-market", spread=Decimal("0.0800")),
    )

    assert report.status == "watch"
    assert report.pass_count == 0
    assert report.watch_count == 1
    assert report.blocked_count == 0
    assert report.depth_ready_count == 1
    assert report.missing_depth_count == 0
    assert report.reason_codes == ("liquidity_gate_watch",)
    assert report.rows[0].status == "watch"
    assert report.rows[0].reason_codes == ("wide_spread",)


def test_liquidity_gate_blocks_missing_selected_ask_size():
    report = _liquidity_report(
        _cost_aware_report(
            market_slug="missing-depth-market",
            selected_side="yes",
            yes_ask_size=None,
        ),
    )

    assert report.status == "blocked"
    assert report.market_count == 1
    assert report.pass_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 1
    assert report.depth_ready_count == 0
    assert report.missing_depth_count == 1
    assert report.reason_codes == (
        "insufficient_depth_ready_count",
        "too_many_missing_depth",
    )
    assert report.rows[0].selected_ask_size is None
    assert report.rows[0].status == "blocked"
    assert report.rows[0].reason_codes == ("missing_selected_ask_size",)


def test_liquidity_gate_blocks_mixed_ready_and_insufficient_selected_ask_size():
    report = _liquidity_report(
        _cost_aware_report(
            market_slug="thin-market",
            selected_side="yes",
            yes_ask_size=Decimal("5.0000"),
        ),
        _cost_aware_report(market_slug="ready-market"),
    )

    assert report.status == "blocked"
    assert report.reason_codes == ("row_level_liquidity_block",)
    assert report.market_count == 2
    assert report.pass_count == 1
    assert report.watch_count == 0
    assert report.blocked_count == 1
    assert report.depth_ready_count == 1
    assert report.missing_depth_count == 0
    assert tuple((row.market_slug, row.status) for row in report.rows) == (
        ("thin-market", "blocked"),
        ("ready-market", "pass"),
    )
    assert report.rows[0].reason_codes == ("insufficient_selected_ask_size",)

    with pytest.raises(ValueError, match="status must not pass with blocked rows"):
        PaperLiquidityGateReport(
            generated_at=GENERATED_AT,
            config_version="paper-liquidity-gate-v0",
            status="pass",
            reason_codes=("liquidity_gate_passed",),
            market_count=2,
            pass_count=1,
            watch_count=0,
            blocked_count=1,
            depth_ready_count=1,
            missing_depth_count=0,
            rows=report.rows,
        )


def test_liquidity_gate_blocks_empty_input():
    report = _liquidity_report()

    assert report.status == "blocked"
    assert report.market_count == 0
    assert report.pass_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.depth_ready_count == 0
    assert report.missing_depth_count == 0
    assert report.rows == ()
    assert report.reason_codes == ("empty_input", "insufficient_depth_ready_count")


def test_liquidity_gate_rejects_direct_empty_pass_report():
    with pytest.raises(ValueError, match="depth_ready_count"):
        PaperLiquidityGateReport(
            generated_at=GENERATED_AT,
            config_version="paper-liquidity-gate-v0",
            status="pass",
            reason_codes=("liquidity_gate_passed",),
            market_count=0,
            pass_count=0,
            watch_count=0,
            blocked_count=0,
            depth_ready_count=999,
            missing_depth_count=0,
            rows=(),
        )

    with pytest.raises(ValueError, match="reason_codes"):
        PaperLiquidityGateReport(
            generated_at=GENERATED_AT,
            config_version="paper-liquidity-gate-v0",
            status="pass",
            reason_codes=("liquidity_gate_passed",),
            market_count=0,
            pass_count=0,
            watch_count=0,
            blocked_count=0,
            depth_ready_count=0,
            missing_depth_count=0,
            rows=(),
        )


def test_liquidity_gate_rejects_direct_row_count_and_status_inconsistencies():
    blocked_row = PaperLiquidityGateRow(
        market_slug="blocked-market",
        selected_side="yes",
        spread=Decimal("0.0200"),
        selected_ask_size=Decimal("5.0000"),
        status="blocked",
        reason_codes=("insufficient_selected_ask_size",),
    )
    watch_row = PaperLiquidityGateRow(
        market_slug="watch-market",
        selected_side="yes",
        spread=Decimal("0.0800"),
        selected_ask_size=Decimal("25.0000"),
        status="watch",
        reason_codes=("wide_spread",),
    )
    pass_row = PaperLiquidityGateRow(
        market_slug="pass-market",
        selected_side="yes",
        spread=Decimal("0.0200"),
        selected_ask_size=Decimal("25.0000"),
        status="pass",
        reason_codes=("liquidity_ready",),
    )

    with pytest.raises(ValueError, match="watch_count"):
        PaperLiquidityGateReport(
            generated_at=GENERATED_AT,
            config_version="paper-liquidity-gate-v0",
            status="watch",
            reason_codes=("liquidity_gate_watch",),
            market_count=1,
            pass_count=0,
            watch_count=0,
            blocked_count=0,
            depth_ready_count=1,
            missing_depth_count=0,
            rows=(watch_row,),
        )

    with pytest.raises(ValueError, match="depth_ready_count"):
        PaperLiquidityGateReport(
            generated_at=GENERATED_AT,
            config_version="paper-liquidity-gate-v0",
            status="watch",
            reason_codes=("liquidity_gate_watch",),
            market_count=1,
            pass_count=0,
            watch_count=1,
            blocked_count=0,
            depth_ready_count=0,
            missing_depth_count=0,
            rows=(watch_row,),
        )

    with pytest.raises(ValueError, match="missing_depth_count"):
        PaperLiquidityGateReport(
            generated_at=GENERATED_AT,
            config_version="paper-liquidity-gate-v0",
            status="blocked",
            reason_codes=("too_many_missing_depth",),
            market_count=1,
            pass_count=0,
            watch_count=0,
            blocked_count=1,
            depth_ready_count=0,
            missing_depth_count=1,
            rows=(blocked_row,),
        )

    with pytest.raises(ValueError, match="status"):
        PaperLiquidityGateReport(
            generated_at=GENERATED_AT,
            config_version="paper-liquidity-gate-v0",
            status="watch",
            reason_codes=("row_level_liquidity_block",),
            market_count=2,
            pass_count=1,
            watch_count=0,
            blocked_count=1,
            depth_ready_count=1,
            missing_depth_count=0,
            rows=(blocked_row, pass_row),
        )

    with pytest.raises(ValueError, match="reason_codes"):
        PaperLiquidityGateReport(
            generated_at=GENERATED_AT,
            config_version="paper-liquidity-gate-v0",
            status="pass",
            reason_codes=("liquidity_gate_watch",),
            market_count=1,
            pass_count=1,
            watch_count=0,
            blocked_count=0,
            depth_ready_count=1,
            missing_depth_count=0,
            rows=(pass_row,),
        )

    invalid_pass_row = PaperLiquidityGateRow(
        market_slug="invalid-pass-market",
        selected_side="yes",
        spread=Decimal("0.0200"),
        selected_ask_size=Decimal("25.0000"),
        status="pass",
        reason_codes=("wide_spread",),
    )

    with pytest.raises(ValueError, match="rows"):
        PaperLiquidityGateReport(
            generated_at=GENERATED_AT,
            config_version="paper-liquidity-gate-v0",
            status="pass",
            reason_codes=("liquidity_gate_passed",),
            market_count=1,
            pass_count=1,
            watch_count=0,
            blocked_count=0,
            depth_ready_count=1,
            missing_depth_count=0,
            rows=(invalid_pass_row,),
        )

    invalid_missing_depth_pass_row = PaperLiquidityGateRow(
        market_slug="missing-depth-pass-market",
        selected_side="yes",
        spread=Decimal("0.0200"),
        selected_ask_size=None,
        status="pass",
        reason_codes=("liquidity_ready",),
    )

    with pytest.raises(ValueError, match="rows"):
        PaperLiquidityGateReport(
            generated_at=GENERATED_AT,
            config_version="paper-liquidity-gate-v0",
            status="pass",
            reason_codes=("liquidity_gate_passed",),
            market_count=1,
            pass_count=1,
            watch_count=0,
            blocked_count=0,
            depth_ready_count=1,
            missing_depth_count=1,
            rows=(invalid_missing_depth_pass_row,),
        )


def test_liquidity_gate_orders_rows_by_status_severity_then_market_slug():
    report = _liquidity_report(
        _cost_aware_report(market_slug="zeta-pass"),
        _cost_aware_report(market_slug="alpha-watch", spread=Decimal("0.0800")),
        _cost_aware_report(market_slug="beta-blocked", yes_ask_size=None),
        _cost_aware_report(market_slug="alpha-blocked", selected_side="none"),
    )

    assert tuple((row.status, row.market_slug) for row in report.rows) == (
        ("blocked", "alpha-blocked"),
        ("blocked", "beta-blocked"),
        ("watch", "alpha-watch"),
        ("pass", "zeta-pass"),
    )


def test_liquidity_gate_validates_exact_scalar_types_and_report_inputs():
    with pytest.raises(ValueError, match="config_version"):
        PaperLiquidityGateConfig(config_version=_StringSubclass("v0"))

    with pytest.raises(ValueError, match="selected_side"):
        PaperLiquidityGateRow(
            market_slug="alpha-market",
            selected_side=_StringSubclass("yes"),
            spread=Decimal("0.0200"),
            selected_ask_size=Decimal("25.0000"),
            status="pass",
            reason_codes=("liquidity_ready",),
        )

    with pytest.raises(ValueError, match="status"):
        PaperLiquidityGateReport(
            generated_at=GENERATED_AT,
            config_version="paper-liquidity-gate-v0",
            status=_StringSubclass("pass"),
            reason_codes=("liquidity_gate_passed",),
            market_count=0,
            pass_count=0,
            watch_count=0,
            blocked_count=0,
            depth_ready_count=0,
            missing_depth_count=0,
            rows=(),
        )

    with pytest.raises(ValueError, match="max_spread"):
        PaperLiquidityGateConfig(
            config_version="v0",
            max_spread=0.05,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="min_ask_size"):
        PaperLiquidityGateConfig(
            config_version="v0",
            min_ask_size=_DecimalSubclass("1.0000"),
        )

    with pytest.raises(ValueError, match="min_depth_ready_count"):
        PaperLiquidityGateConfig(
            config_version="v0",
            min_depth_ready_count=True,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="min_depth_ready_count"):
        PaperLiquidityGateConfig(
            config_version="v0",
            min_depth_ready_count=0,
        )

    with pytest.raises(ValueError, match="max_missing_depth_count"):
        PaperLiquidityGateConfig(
            config_version="v0",
            max_missing_depth_count=_IntSubclass(1),
        )

    with pytest.raises(ValueError, match="generated_at"):
        _liquidity_report(
            _cost_aware_report(),
            generated_at=_DatetimeSubclass(2026, 6, 18, 12, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="reports"):
        build_paper_liquidity_gate_report(
            [object()],  # type: ignore[list-item]
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_liquidity_gate_normalizes_generated_at_to_utc():
    pacific_generated_at = datetime(
        2026,
        6,
        18,
        5,
        0,
        tzinfo=timezone(timedelta(hours=-7)),
    )

    report = _liquidity_report(
        _cost_aware_report(),
        generated_at=pacific_generated_at,
    )

    assert report.generated_at == datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    assert report.generated_at.tzinfo is UTC


def test_liquidity_gate_dataclasses_are_frozen_and_hard_flags_are_enforced():
    report = _liquidity_report(_cost_aware_report())

    with pytest.raises(FrozenInstanceError):
        report.status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        PaperLiquidityGateReport(
            generated_at=GENERATED_AT,
            config_version="paper-liquidity-gate-v0",
            status="blocked",
            reason_codes=("empty_input", "insufficient_depth_ready_count"),
            market_count=0,
            pass_count=0,
            watch_count=0,
            blocked_count=0,
            depth_ready_count=0,
            missing_depth_count=0,
            rows=(),
            paper_only=False,
        )

    with pytest.raises(ValueError, match="report_only"):
        PaperLiquidityGateReport(
            generated_at=GENERATED_AT,
            config_version="paper-liquidity-gate-v0",
            status="blocked",
            reason_codes=("empty_input", "insufficient_depth_ready_count"),
            market_count=0,
            pass_count=0,
            watch_count=0,
            blocked_count=0,
            depth_ready_count=0,
            missing_depth_count=0,
            rows=(),
            report_only=False,
        )

    with pytest.raises(ValueError, match="readonly"):
        PaperLiquidityGateReport(
            generated_at=GENERATED_AT,
            config_version="paper-liquidity-gate-v0",
            status="blocked",
            reason_codes=("empty_input", "insufficient_depth_ready_count"),
            market_count=0,
            pass_count=0,
            watch_count=0,
            blocked_count=0,
            depth_ready_count=0,
            missing_depth_count=0,
            rows=(),
            readonly=False,
        )
