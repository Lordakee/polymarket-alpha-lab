from datetime import UTC, datetime
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.calibration_gate import (
    PaperCalibrationGateReport,
    PaperCalibrationGateRow,
)
from polymarket_alpha_lab.cost_health_gate import (
    PaperCostHealthGateReport,
    PaperCostHealthGateRow,
)
from polymarket_alpha_lab.exposure_gate import (
    PaperExposureGateReport,
    PaperExposureGateRow,
)
from polymarket_alpha_lab.liquidity_gate import (
    PaperLiquidityGateReport,
    PaperLiquidityGateRow,
)
from polymarket_alpha_lab.market_context_freshness import (
    PaperMarketContextFreshnessReport,
    PaperMarketContextFreshnessRow,
)
from polymarket_alpha_lab.paper_nav_liquidity_risk import (
    PaperNavLiquidityRiskMarketRow,
    PaperNavLiquidityRiskReport,
)
from polymarket_alpha_lab.paper_nav_settlement_risk_overlay import (
    PaperNavSettlementRiskOverlayReport,
    PaperNavSettlementRiskOverlayRow,
)
from polymarket_alpha_lab.settlement_freshness_gate import (
    PaperSettlementFreshnessGateReport,
    PaperSettlementFreshnessGateRow,
)
from polymarket_alpha_lab.strategy_readiness_state import PaperStrategyReadinessSignal


GENERATED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
SOURCE_GENERATED_AT = datetime(2026, 6, 18, 11, 0, tzinfo=UTC)


class _CalibrationReportSubclass(PaperCalibrationGateReport):
    pass


class _CostHealthReportSubclass(PaperCostHealthGateReport):
    pass


class _LiquidityReportSubclass(PaperLiquidityGateReport):
    pass


class _NavLiquidityRiskReportSubclass(PaperNavLiquidityRiskReport):
    pass


class _NavSettlementRiskOverlayReportSubclass(PaperNavSettlementRiskOverlayReport):
    pass


class _ExposureReportSubclass(PaperExposureGateReport):
    pass


class _FreshnessReportSubclass(PaperMarketContextFreshnessReport):
    pass


def _settlement_gate_report(
    *,
    status: str,
) -> PaperSettlementFreshnessGateReport:
    if status == "block":
        gate_rows = (
            PaperSettlementFreshnessGateRow(
                "checking_coverage",
                "pass",
                "Settlement checking coverage meets the configured floor.",
                4,
                2,
            ),
            PaperSettlementFreshnessGateRow(
                "pending_count",
                "block",
                "Pending settlement count exceeds the configured maximum.",
                3,
                1,
            ),
            PaperSettlementFreshnessGateRow(
                "unresolved_age",
                "pass",
                "Pending settlement outcomes are within the configured age.",
                Decimal("1.000000"),
                Decimal("4.000000"),
            ),
        )
    elif status == "watch":
        gate_rows = (
            PaperSettlementFreshnessGateRow(
                "checking_coverage",
                "watch",
                "Settlement checking coverage is below the configured floor.",
                1,
                2,
            ),
            PaperSettlementFreshnessGateRow(
                "pending_count",
                "pass",
                "Pending settlement count is within the configured maximum.",
                0,
                1,
            ),
            PaperSettlementFreshnessGateRow(
                "unresolved_age",
                "pass",
                "Pending settlement outcomes are within the configured age.",
                Decimal("1.000000"),
                Decimal("4.000000"),
            ),
        )
    else:
        gate_rows = (
            PaperSettlementFreshnessGateRow(
                "checking_coverage",
                "pass",
                "Settlement checking coverage meets the configured floor.",
                4,
                2,
            ),
            PaperSettlementFreshnessGateRow(
                "pending_count",
                "pass",
                "Pending settlement count is within the configured maximum.",
                0,
                1,
            ),
            PaperSettlementFreshnessGateRow(
                "unresolved_age",
                "pass",
                "Pending settlement outcomes are within the configured age.",
                Decimal("1.000000"),
                Decimal("4.000000"),
            ),
        )
    block_reasons = tuple(row.reason for row in gate_rows if row.status == "block")
    watch_reasons = tuple(row.reason for row in gate_rows if row.status == "watch")
    return PaperSettlementFreshnessGateReport(
        generated_at=GENERATED_AT,
        config_version="settlement-freshness-gate-v0",
        source_kind="outcome_freshness",
        source_report_count=1,
        latest_check_generated_at=SOURCE_GENERATED_AT,
        checked_market_count=4 if status != "watch" else 1,
        pending_count=3 if status == "block" else 0,
        stale_pending_count=0,
        latest_check_age_hours=Decimal("1.000000"),
        status=status,
        gate_count=len(gate_rows),
        pass_count=sum(1 for row in gate_rows if row.status == "pass"),
        watch_count=len(watch_reasons),
        block_count=len(block_reasons),
        gate_rows=gate_rows,
        block_reasons=block_reasons,
        watch_reasons=watch_reasons,
    )


def _mixed_settlement_gate_report() -> PaperSettlementFreshnessGateReport:
    gate_rows = (
        PaperSettlementFreshnessGateRow(
            "checking_coverage",
            "watch",
            "Settlement checking coverage is below the configured floor.",
            3,
            4,
        ),
        PaperSettlementFreshnessGateRow(
            "pending_count",
            "block",
            "Pending settlement count exceeds the configured maximum.",
            3,
            1,
        ),
        PaperSettlementFreshnessGateRow(
            "unresolved_age",
            "pass",
            "Pending settlement outcomes are within the configured age.",
            Decimal("1.000000"),
            Decimal("4.000000"),
        ),
    )
    block_reasons = tuple(row.reason for row in gate_rows if row.status == "block")
    watch_reasons = tuple(row.reason for row in gate_rows if row.status == "watch")
    return PaperSettlementFreshnessGateReport(
        generated_at=GENERATED_AT,
        config_version="settlement-freshness-gate-v0",
        source_kind="outcome_freshness",
        source_report_count=1,
        latest_check_generated_at=SOURCE_GENERATED_AT,
        checked_market_count=3,
        pending_count=3,
        stale_pending_count=0,
        latest_check_age_hours=Decimal("1.000000"),
        status="block",
        gate_count=len(gate_rows),
        pass_count=sum(1 for row in gate_rows if row.status == "pass"),
        watch_count=len(watch_reasons),
        block_count=len(block_reasons),
        gate_rows=gate_rows,
        block_reasons=block_reasons,
        watch_reasons=watch_reasons,
    )


def _adapter_module():
    return import_module("polymarket_alpha_lab.strategy_signal_adapter")


def _calibration_report(
    report_type=PaperCalibrationGateReport,
    *,
    brier_status: str = "blocked",
) -> PaperCalibrationGateReport:
    gate_rows = (
        PaperCalibrationGateRow(
            "calibration_history",
            "passed",
            "calibration_history_ready",
            2,
            1,
        ),
        PaperCalibrationGateRow(
            "observation_count",
            "watch",
            "observation_count_insufficient",
            12,
            30,
        ),
        PaperCalibrationGateRow(
            "brier_score",
            brier_status,
            "brier_score_above_limit"
            if brier_status == "blocked"
            else "brier_score_within_limit",
            Decimal("0.260000") if brier_status == "blocked" else Decimal("0.120000"),
            Decimal("0.250000"),
        ),
        PaperCalibrationGateRow(
            "calibration_error",
            "passed",
            "calibration_error_within_limit",
            Decimal("0.060000"),
            Decimal("0.100000"),
        ),
    )
    blocked_count = sum(1 for row in gate_rows if row.status == "blocked")
    watch_count = sum(1 for row in gate_rows if row.status == "watch")
    passed_count = sum(1 for row in gate_rows if row.status == "passed")
    gate_status = "blocked" if blocked_count else ("watch" if watch_count else "passed")
    return report_type(
        generated_at=GENERATED_AT,
        config_version="paper-calibration-gate-v0",
        source_report_kind="forecast_calibration_trend",
        source_config_version="forecast-calibration-trend-v0",
        source_generated_at=SOURCE_GENERATED_AT,
        gate_status=gate_status,
        passed=gate_status == "passed",
        reason_codes=tuple(row.reason_code for row in gate_rows),
        gate_count=len(gate_rows),
        passed_gate_count=passed_count,
        watch_gate_count=watch_count,
        blocked_gate_count=blocked_count,
        gate_rows=gate_rows,
    )


def _passing_calibration_report() -> PaperCalibrationGateReport:
    gate_rows = (
        PaperCalibrationGateRow(
            "calibration_history",
            "passed",
            "calibration_history_ready",
            2,
            1,
        ),
        PaperCalibrationGateRow(
            "observation_count",
            "passed",
            "observation_count_ready",
            40,
            30,
        ),
        PaperCalibrationGateRow(
            "brier_score",
            "passed",
            "brier_score_within_limit",
            Decimal("0.120000"),
            Decimal("0.250000"),
        ),
        PaperCalibrationGateRow(
            "calibration_error",
            "passed",
            "calibration_error_within_limit",
            Decimal("0.060000"),
            Decimal("0.100000"),
        ),
    )
    return PaperCalibrationGateReport(
        generated_at=GENERATED_AT,
        config_version="paper-calibration-gate-v0",
        source_report_kind="forecast_calibration_trend",
        source_config_version="forecast-calibration-trend-v0",
        source_generated_at=SOURCE_GENERATED_AT,
        gate_status="passed",
        passed=True,
        reason_codes=tuple(row.reason_code for row in gate_rows),
        gate_count=len(gate_rows),
        passed_gate_count=4,
        watch_gate_count=0,
        blocked_gate_count=0,
        gate_rows=gate_rows,
    )


def _cost_health_report(
    report_type=PaperCostHealthGateReport,
) -> PaperCostHealthGateReport:
    gate_rows = (
        PaperCostHealthGateRow(
            "data_completeness",
            "pass",
            2,
            ">0",
            ("data_available",),
        ),
        PaperCostHealthGateRow(
            "average_cost_drag",
            "pass",
            Decimal("0.020000"),
            Decimal("0.030000"),
            ("average_cost_drag_within_threshold",),
        ),
        PaperCostHealthGateRow(
            "spread_drag",
            "watch",
            None,
            Decimal("0.010000"),
            ("spread_drag_missing",),
        ),
        PaperCostHealthGateRow(
            "net_edge_after_cost",
            "pass",
            Decimal("0.030000"),
            Decimal("0.010000"),
            ("net_edge_after_cost_within_threshold",),
        ),
        PaperCostHealthGateRow(
            "negative_net_edge_streak",
            "pass",
            0,
            0,
            ("negative_net_edge_streak_within_threshold",),
        ),
    )
    return report_type(
        generated_at=GENERATED_AT,
        config_version="cost-health-gate-v0",
        source_report_kind="summary_rows",
        source_report_count=2,
        first_source_generated_at=SOURCE_GENERATED_AT,
        latest_source_generated_at=GENERATED_AT,
        status="paper_cost_health_watch",
        gate_rows=gate_rows,
        reason_codes=("spread_drag_missing",),
    )


def _passing_cost_health_report() -> PaperCostHealthGateReport:
    gate_rows = (
        PaperCostHealthGateRow(
            "data_completeness",
            "pass",
            2,
            ">0",
            ("data_available",),
        ),
        PaperCostHealthGateRow(
            "average_cost_drag",
            "pass",
            Decimal("0.020000"),
            Decimal("0.030000"),
            ("average_cost_drag_within_threshold",),
        ),
        PaperCostHealthGateRow(
            "spread_drag",
            "pass",
            Decimal("0.006000"),
            Decimal("0.010000"),
            ("spread_drag_within_threshold",),
        ),
        PaperCostHealthGateRow(
            "net_edge_after_cost",
            "pass",
            Decimal("0.030000"),
            Decimal("0.010000"),
            ("net_edge_after_cost_within_threshold",),
        ),
        PaperCostHealthGateRow(
            "negative_net_edge_streak",
            "pass",
            0,
            0,
            ("negative_net_edge_streak_within_threshold",),
        ),
    )
    return PaperCostHealthGateReport(
        generated_at=GENERATED_AT,
        config_version="cost-health-gate-v0",
        source_report_kind="summary_rows",
        source_report_count=2,
        first_source_generated_at=SOURCE_GENERATED_AT,
        latest_source_generated_at=GENERATED_AT,
        status="paper_cost_health_pass",
        gate_rows=gate_rows,
        reason_codes=(),
    )


def _liquidity_report(
    report_type=PaperLiquidityGateReport,
) -> PaperLiquidityGateReport:
    row = PaperLiquidityGateRow(
        market_slug="alpha-market",
        selected_side="yes",
        spread=Decimal("0.0200"),
        selected_ask_size=None,
        status="blocked",
        reason_codes=("missing_selected_ask_size",),
    )
    return report_type(
        generated_at=GENERATED_AT,
        config_version="paper-liquidity-gate-v0",
        status="blocked",
        reason_codes=("insufficient_depth_ready_count",),
        market_count=1,
        pass_count=0,
        watch_count=0,
        blocked_count=1,
        depth_ready_count=0,
        missing_depth_count=1,
        rows=(row,),
    )


def _empty_nav_liquidity_risk_report(
    report_type=PaperNavLiquidityRiskReport,
) -> PaperNavLiquidityRiskReport:
    return report_type(
        generated_at=GENERATED_AT,
        config_version="paper-nav-liquidity-risk-v0",
        nav_snapshot_count=0,
        first_marked_at=None,
        last_marked_at=None,
        latest_open_position_count=0,
        latest_fully_executable_count=0,
        latest_partially_executable_count=0,
        latest_no_exit_depth_count=0,
        latest_total_open_size=None,
        latest_total_cost_basis=None,
        latest_unfilled_size=None,
        latest_unfilled_open_size_share=None,
        latest_unexecutable_cost_basis=None,
        latest_unexecutable_cost_basis_share=None,
        latest_weighted_slippage=None,
        latest_widest_spread=None,
        largest_unexecutable_condition_id=None,
        largest_unexecutable_market_slug=None,
        largest_unexecutable_cost_basis=None,
        consecutive_unexecutable_snapshot_count=0,
        worst_observed_unexecutable_cost_basis_share=None,
        status="empty_nav_liquidity_risk_history",
        market_rows=(),
    )


def _nav_liquidity_risk_report(
    report_type=PaperNavLiquidityRiskReport,
    *,
    zero_cost_basis: bool = False,
) -> PaperNavLiquidityRiskReport:
    cost_basis = Decimal("0.0000") if zero_cost_basis else Decimal("10.0000")
    unexecutable_cost_basis = Decimal("0") if zero_cost_basis else Decimal("5.0000")
    unexecutable_cost_basis_share = (
        None if zero_cost_basis else Decimal("0.500000")
    )
    largest_condition_id = None if zero_cost_basis else "condition-risky"
    largest_market_slug = None if zero_cost_basis else "market-risky"
    largest_cost_basis = None if zero_cost_basis else Decimal("5.0000")
    worst_share = None if zero_cost_basis else Decimal("0.500000")
    row = PaperNavLiquidityRiskMarketRow(
        condition_id="condition-risky",
        market_slug="market-risky",
        token_count=1,
        open_size=Decimal("10.0000"),
        cost_basis=cost_basis,
        exit_filled_size=Decimal("5.0000"),
        exit_unfilled_size=Decimal("5.0000"),
        exit_value=Decimal("2.5000"),
        unfilled_open_size_share=Decimal("0.500000"),
        unexecutable_cost_basis=unexecutable_cost_basis,
        unexecutable_cost_basis_share=unexecutable_cost_basis_share,
        weighted_slippage=Decimal("0.010000"),
        widest_spread=Decimal("0.0200"),
        fully_executable_count=0,
        partially_executable_count=1,
        no_exit_depth_count=0,
    )
    return report_type(
        generated_at=GENERATED_AT,
        config_version="paper-nav-liquidity-risk-v0",
        nav_snapshot_count=1,
        first_marked_at=SOURCE_GENERATED_AT,
        last_marked_at=SOURCE_GENERATED_AT,
        latest_open_position_count=1,
        latest_fully_executable_count=0,
        latest_partially_executable_count=1,
        latest_no_exit_depth_count=0,
        latest_total_open_size=Decimal("10.0000"),
        latest_total_cost_basis=cost_basis,
        latest_unfilled_size=Decimal("5.0000"),
        latest_unfilled_open_size_share=Decimal("0.500000"),
        latest_unexecutable_cost_basis=unexecutable_cost_basis,
        latest_unexecutable_cost_basis_share=unexecutable_cost_basis_share,
        latest_weighted_slippage=Decimal("0.010000"),
        latest_widest_spread=Decimal("0.0200"),
        largest_unexecutable_condition_id=largest_condition_id,
        largest_unexecutable_market_slug=largest_market_slug,
        largest_unexecutable_cost_basis=largest_cost_basis,
        consecutive_unexecutable_snapshot_count=1,
        worst_observed_unexecutable_cost_basis_share=worst_share,
        status="latest_nav_has_unexecutable_liquidity",
        market_rows=(row,),
    )


def _settlement_nav_overlay_row(
    *,
    condition_id: str,
    market_slug: str,
    overlay_status: str,
    exit_value: Decimal,
    reason_codes: tuple[str, ...],
) -> PaperNavSettlementRiskOverlayRow:
    settlement_timing_status = overlay_status
    timing_cost_per_share = Decimal("0.000000")
    adjusted_edge = Decimal("0.050000")
    if overlay_status != "acceptable":
        timing_cost_per_share = Decimal("0.020000")
        adjusted_edge = Decimal("0.010000")
    return PaperNavSettlementRiskOverlayRow(
        condition_id=condition_id,
        market_slug=market_slug,
        token_count=1,
        open_size=Decimal("100.0000"),
        cost_basis=Decimal("100.0000"),
        exit_value=exit_value,
        share_of_exit_nav=Decimal("0.009950"),
        overlay_status=overlay_status,
        settlement_timing_status=settlement_timing_status,
        timing_cost_per_share=timing_cost_per_share,
        adjusted_net_probability_edge=adjusted_edge,
        reason_codes=reason_codes,
    )


def _settlement_nav_overlay_report(
    status: str,
    report_type=PaperNavSettlementRiskOverlayReport,
    *,
    blocked_or_missing_exit_nav_share: Decimal | None | object = object(),
    rows: tuple[PaperNavSettlementRiskOverlayRow, ...] | None = None,
) -> PaperNavSettlementRiskOverlayReport:
    if rows is None:
        if status == "empty_nav_settlement_risk_overlay":
            rows = ()
        elif status == "settlement_nav_risk_clear":
            rows = (
                _settlement_nav_overlay_row(
                    condition_id="condition-clear",
                    market_slug="market-clear",
                    overlay_status="acceptable",
                    exit_value=Decimal("100.0000"),
                    reason_codes=("settlement_timing_clear",),
                ),
            )
        elif status == "settlement_nav_risk_watch":
            rows = (
                _settlement_nav_overlay_row(
                    condition_id="condition-watch",
                    market_slug="market-watch",
                    overlay_status="watch",
                    exit_value=Decimal("100.0000"),
                    reason_codes=("settlement_timing_risk",),
                ),
            )
        else:
            rows = (
                _settlement_nav_overlay_row(
                    condition_id="condition-blocked",
                    market_slug="market-blocked",
                    overlay_status="blocked",
                    exit_value=Decimal("100.0000"),
                    reason_codes=("settlement_timing_risk",),
                ),
            )
    acceptable_exit_value = sum(
        (row.exit_value for row in rows if row.overlay_status == "acceptable"),
        Decimal("0"),
    )
    watch_exit_value = sum(
        (row.exit_value for row in rows if row.overlay_status == "watch"),
        Decimal("0"),
    )
    blocked_exit_value = sum(
        (
            row.exit_value
            for row in rows
            if row.settlement_timing_status == "blocked"
        ),
        Decimal("0"),
    )
    missing_settlement_exit_value = sum(
        (
            row.exit_value
            for row in rows
            if row.settlement_timing_status is None
        ),
        Decimal("0"),
    )
    blocked_or_missing_exit_value = (
        blocked_exit_value + missing_settlement_exit_value
    )
    if not isinstance(blocked_or_missing_exit_nav_share, (Decimal, type(None))):
        blocked_or_missing_exit_nav_share = (
            None
            if status == "empty_nav_settlement_risk_overlay"
            else Decimal("0.150000")
            if status == "settlement_nav_risk_blocked"
            else Decimal("0.000000")
        )
    return report_type(
        generated_at=GENERATED_AT,
        config_version="paper-nav-settlement-risk-overlay-v0",
        nav_risk_config_version="paper-nav-risk-metrics-v0",
        settlement_timing_config_version="paper-settlement-timing-v0",
        nav_snapshot_count=0 if not rows else 1,
        first_marked_at=None if not rows else SOURCE_GENERATED_AT,
        last_marked_at=None if not rows else SOURCE_GENERATED_AT,
        settlement_row_count=len(rows),
        exposure_row_count=len(rows),
        acceptable_count=sum(1 for row in rows if row.overlay_status == "acceptable"),
        watch_count=sum(1 for row in rows if row.overlay_status == "watch"),
        blocked_count=sum(1 for row in rows if row.overlay_status == "blocked"),
        missing_settlement_count=sum(
            1 for row in rows if row.settlement_timing_status is None
        ),
        acceptable_exit_value=acceptable_exit_value,
        watch_exit_value=watch_exit_value,
        blocked_exit_value=blocked_exit_value,
        missing_settlement_exit_value=missing_settlement_exit_value,
        blocked_or_missing_exit_value=blocked_or_missing_exit_value,
        blocked_or_missing_exit_nav_share=blocked_or_missing_exit_nav_share,
        max_blocked_settlement_exposure_share=Decimal("0.100000"),
        status=status,
        rows=rows,
    )


def _passing_nav_liquidity_risk_report(
    report_type=PaperNavLiquidityRiskReport,
) -> PaperNavLiquidityRiskReport:
    row = PaperNavLiquidityRiskMarketRow(
        condition_id="condition-liquid",
        market_slug="market-liquid",
        token_count=1,
        open_size=Decimal("10.0000"),
        cost_basis=Decimal("10.0000"),
        exit_filled_size=Decimal("10.0000"),
        exit_unfilled_size=Decimal("0.0000"),
        exit_value=Decimal("5.0000"),
        unfilled_open_size_share=Decimal("0.000000"),
        unexecutable_cost_basis=Decimal("0"),
        unexecutable_cost_basis_share=Decimal("0.000000"),
        weighted_slippage=Decimal("0.010000"),
        widest_spread=Decimal("0.0200"),
        fully_executable_count=1,
        partially_executable_count=0,
        no_exit_depth_count=0,
    )
    return report_type(
        generated_at=GENERATED_AT,
        config_version="paper-nav-liquidity-risk-v0",
        nav_snapshot_count=1,
        first_marked_at=SOURCE_GENERATED_AT,
        last_marked_at=SOURCE_GENERATED_AT,
        latest_open_position_count=1,
        latest_fully_executable_count=1,
        latest_partially_executable_count=0,
        latest_no_exit_depth_count=0,
        latest_total_open_size=Decimal("10.0000"),
        latest_total_cost_basis=Decimal("10.0000"),
        latest_unfilled_size=Decimal("0.0000"),
        latest_unfilled_open_size_share=Decimal("0.000000"),
        latest_unexecutable_cost_basis=Decimal("0"),
        latest_unexecutable_cost_basis_share=Decimal("0.000000"),
        latest_weighted_slippage=Decimal("0.010000"),
        latest_widest_spread=Decimal("0.0200"),
        largest_unexecutable_condition_id=None,
        largest_unexecutable_market_slug=None,
        largest_unexecutable_cost_basis=None,
        consecutive_unexecutable_snapshot_count=0,
        worst_observed_unexecutable_cost_basis_share=Decimal("0.000000"),
        status="latest_nav_liquidity_observed",
        market_rows=(row,),
    )


def _exposure_report(
    report_type=PaperExposureGateReport,
) -> PaperExposureGateReport:
    row = PaperExposureGateRow(
        market_slug="alpha-market",
        exposure_amount=Decimal("25.000000"),
        status="pass",
        reason_codes=(),
    )
    return report_type(
        generated_at=GENERATED_AT,
        config_version="paper-exposure-gate-v0",
        status="pass",
        position_count=1,
        total_exposure=Decimal("25.000000"),
        cash_buffer=Decimal("100.000000"),
        rows=(row,),
        reason_codes=(),
    )


def _freshness_report(
    report_type=PaperMarketContextFreshnessReport,
) -> PaperMarketContextFreshnessReport:
    row = PaperMarketContextFreshnessRow(
        market_slug="alpha-market",
        report_generated_at=SOURCE_GENERATED_AT,
        report_age_seconds=Decimal("90"),
        status="watch",
        reason_codes=("stale_market_context",),
    )
    return report_type(
        generated_at=GENERATED_AT,
        config_version="market-context-freshness-v0",
        max_report_age_seconds=60,
        min_context_count=1,
        context_count=1,
        status="watch",
        reason_codes=("stale_market_context",),
        rows=(row,),
    )


def test_adapter_maps_report_statuses_to_readiness_signals():
    adapter = _adapter_module()

    calibration_signal = adapter.signals_from_calibration_gate_report(
        _calibration_report(),
    )[0]
    cost_signal = adapter.signals_from_cost_health_gate_report(
        _cost_health_report(),
    )[0]
    liquidity_signal = adapter.signals_from_liquidity_gate_report(
        _liquidity_report(),
    )[0]
    exposure_signal = adapter.signals_from_exposure_gate_report(
        _exposure_report(),
    )[0]
    freshness_signal = adapter.signals_from_market_context_freshness_report(
        _freshness_report(),
    )[0]

    assert calibration_signal == PaperStrategyReadinessSignal(
        source_name="calibration_gate",
        status="blocked",
        reason_codes=(
            "calibration_history_ready",
            "observation_count_insufficient",
            "brier_score_above_limit",
            "calibration_error_within_limit",
        ),
        severity=100,
        observed_value=1,
        threshold=0,
    )
    assert cost_signal == PaperStrategyReadinessSignal(
        source_name="cost_health_gate",
        status="watch",
        reason_codes=("spread_drag_missing",),
        severity=50,
        observed_value=1,
        threshold=0,
    )
    assert liquidity_signal == PaperStrategyReadinessSignal(
        source_name="liquidity_gate",
        status="blocked",
        reason_codes=("insufficient_depth_ready_count",),
        severity=100,
        observed_value=0,
        threshold=None,
    )
    assert exposure_signal == PaperStrategyReadinessSignal(
        source_name="exposure_gate",
        status="pass",
        reason_codes=("exposure_gate_passed",),
        severity=0,
        observed_value=Decimal("25.000000"),
        threshold=None,
    )
    assert freshness_signal == PaperStrategyReadinessSignal(
        source_name="market_context_freshness",
        status="watch",
        reason_codes=("stale_market_context",),
        severity=50,
        observed_value=Decimal("90"),
        threshold=60,
    )


def test_adapter_builds_signals_in_deterministic_readiness_order():
    adapter = _adapter_module()

    signals = adapter.build_paper_strategy_readiness_signals(
        _passing_calibration_report(),
        _freshness_report(),
        _liquidity_report(),
        _nav_liquidity_risk_report(),
        _settlement_nav_overlay_report("settlement_nav_risk_blocked"),
        _exposure_report(),
        _cost_health_report(),
    )

    assert tuple(signal.source_name for signal in signals) == (
        "liquidity_gate",
        "nav_liquidity_risk",
        "nav_settlement_risk_overlay",
        "cost_health_gate",
        "market_context_freshness",
        "calibration_gate",
        "exposure_gate",
    )
    assert tuple(signal.status for signal in signals) == (
        "blocked",
        "blocked",
        "blocked",
        "watch",
        "watch",
        "pass",
        "pass",
    )


@pytest.mark.parametrize(
    (
        "report_factory",
        "readiness_status",
        "severity",
        "reason_codes",
        "observed_value",
    ),
    (
        (
            _empty_nav_liquidity_risk_report,
            "watch",
            50,
            ("nav_liquidity_risk_history_empty",),
            None,
        ),
        (
            _passing_nav_liquidity_risk_report,
            "pass",
            0,
            ("nav_liquidity_risk_passed",),
            Decimal("0.000000"),
        ),
        (
            _nav_liquidity_risk_report,
            "blocked",
            100,
            ("nav_liquidity_risk_unexecutable_liquidity",),
            Decimal("0.500000"),
        ),
    ),
)
def test_adapter_builds_readiness_signals_from_nav_liquidity_risk_reports(
    report_factory,
    readiness_status,
    severity,
    reason_codes,
    observed_value,
):
    adapter = _adapter_module()
    report = report_factory()

    signals = adapter.signals_from_nav_liquidity_risk_report(report)

    assert signals == (
        PaperStrategyReadinessSignal(
            source_name="nav_liquidity_risk",
            status=readiness_status,
            reason_codes=reason_codes,
            severity=severity,
            observed_value=observed_value,
            threshold=None,
        ),
    )


def test_nav_liquidity_risk_signal_falls_back_to_unfilled_share_when_cost_basis_share_missing():
    adapter = _adapter_module()
    report = _nav_liquidity_risk_report(zero_cost_basis=True)

    signals = adapter.build_paper_strategy_readiness_signals(report)

    assert report.latest_unexecutable_cost_basis_share is None
    assert report.latest_unfilled_open_size_share == Decimal("0.500000")
    assert signals == (
        PaperStrategyReadinessSignal(
            source_name="nav_liquidity_risk",
            status="blocked",
            reason_codes=("nav_liquidity_risk_unexecutable_liquidity",),
            severity=100,
            observed_value=Decimal("0.500000"),
            threshold=None,
        ),
    )


@pytest.mark.parametrize(
    (
        "overlay_status",
        "readiness_status",
        "severity",
        "reason_codes",
        "observed_value",
    ),
    (
        (
            "empty_nav_settlement_risk_overlay",
            "watch",
            50,
            ("nav_settlement_risk_overlay_empty",),
            Decimal("0"),
        ),
        (
            "settlement_nav_risk_clear",
            "pass",
            0,
            ("nav_settlement_risk_overlay_passed",),
            Decimal("0.000000"),
        ),
        (
            "settlement_nav_risk_watch",
            "watch",
            50,
            ("settlement_timing_risk",),
            Decimal("0.000000"),
        ),
        (
            "settlement_nav_risk_blocked",
            "blocked",
            100,
            ("settlement_timing_risk",),
            Decimal("0.150000"),
        ),
    ),
)
def test_adapter_builds_readiness_signals_from_nav_settlement_risk_overlay_reports(
    overlay_status,
    readiness_status,
    severity,
    reason_codes,
    observed_value,
):
    adapter = _adapter_module()
    report = _settlement_nav_overlay_report(overlay_status)

    signals = adapter.signals_from_nav_settlement_risk_overlay_report(report)

    assert signals == (
        PaperStrategyReadinessSignal(
            source_name="nav_settlement_risk_overlay",
            status=readiness_status,
            reason_codes=reason_codes,
            severity=severity,
            observed_value=observed_value,
            threshold=Decimal("0.100000"),
        ),
    )


def test_nav_settlement_risk_overlay_signal_uses_exit_value_when_nav_share_missing():
    adapter = _adapter_module()
    report = _settlement_nav_overlay_report(
        "settlement_nav_risk_blocked",
        blocked_or_missing_exit_nav_share=None,
    )

    signals = adapter.build_paper_strategy_readiness_signals(report)

    assert report.blocked_or_missing_exit_nav_share is None
    assert signals == (
        PaperStrategyReadinessSignal(
            source_name="nav_settlement_risk_overlay",
            status="blocked",
            reason_codes=("settlement_timing_risk",),
            severity=100,
            observed_value=Decimal("100.0000"),
            threshold=Decimal("0.100000"),
        ),
    )


def test_nav_settlement_risk_overlay_signal_uses_sorted_nonacceptable_reason_codes():
    adapter = _adapter_module()
    rows = (
        _settlement_nav_overlay_row(
            condition_id="condition-watch",
            market_slug="market-watch",
            overlay_status="watch",
            exit_value=Decimal("40.0000"),
            reason_codes=("z_settlement_risk", "a_settlement_risk"),
        ),
        _settlement_nav_overlay_row(
            condition_id="condition-clear",
            market_slug="market-clear",
            overlay_status="acceptable",
            exit_value=Decimal("60.0000"),
            reason_codes=("ignore_clear_row",),
        ),
    )
    report = _settlement_nav_overlay_report(
        "settlement_nav_risk_watch",
        rows=rows,
    )

    signals = adapter.signals_from_nav_settlement_risk_overlay_report(report)

    assert signals[0].reason_codes == ("a_settlement_risk", "z_settlement_risk")


@pytest.mark.parametrize(
    (
        "settlement_status",
        "readiness_status",
        "severity",
        "observed_value",
        "reason_codes_attr",
    ),
    (
        (
            "block",
            "blocked",
            100,
            1,
            "block_reasons",
        ),
        (
            "watch",
            "watch",
            50,
            1,
            "watch_reasons",
        ),
        (
            "pass",
            "pass",
            0,
            0,
            None,
        ),
    ),
)
def test_adapter_builds_readiness_signals_from_settlement_freshness_gate_reports(
    settlement_status,
    readiness_status,
    severity,
    observed_value,
    reason_codes_attr,
):
    adapter = _adapter_module()
    report = _settlement_gate_report(status=settlement_status)

    signals = adapter.build_paper_strategy_readiness_signals(
        report,
    )

    assert signals == (
        PaperStrategyReadinessSignal(
            source_name="settlement_freshness_gate",
            status=readiness_status,
            reason_codes=(
                ("settlement_freshness_gate_passed",)
                if reason_codes_attr is None
                else getattr(report, reason_codes_attr)
            ),
            severity=severity,
            observed_value=observed_value,
            threshold=0,
        ),
    )


def test_settlement_freshness_signal_uses_block_contract_for_mixed_report():
    adapter = _adapter_module()
    report = _mixed_settlement_gate_report()

    signals = adapter.signals_from_settlement_freshness_gate_report(report)

    assert report.status == "block"
    assert report.block_count == 1
    assert report.watch_count == 1
    assert report.watch_reasons == (
        "Settlement checking coverage is below the configured floor.",
    )
    assert signals == (
        PaperStrategyReadinessSignal(
            source_name="settlement_freshness_gate",
            status="blocked",
            reason_codes=report.block_reasons,
            severity=100,
            observed_value=report.block_count + report.watch_count,
            threshold=0,
        ),
    )


def test_adapter_rejects_unknown_and_subclassed_report_inputs():
    adapter = _adapter_module()

    with pytest.raises(ValueError, match="PaperCalibrationGateReport"):
        adapter.signals_from_calibration_gate_report(object())
    with pytest.raises(ValueError, match="PaperCalibrationGateReport"):
        adapter.signals_from_calibration_gate_report(
            _calibration_report(_CalibrationReportSubclass),
        )
    with pytest.raises(ValueError, match="PaperCostHealthGateReport"):
        adapter.signals_from_cost_health_gate_report(
            _cost_health_report(_CostHealthReportSubclass),
        )
    with pytest.raises(ValueError, match="PaperLiquidityGateReport"):
        adapter.signals_from_liquidity_gate_report(
            _liquidity_report(_LiquidityReportSubclass),
        )
    with pytest.raises(ValueError, match="PaperNavLiquidityRiskReport"):
        adapter.signals_from_nav_liquidity_risk_report(
            _nav_liquidity_risk_report(_NavLiquidityRiskReportSubclass),
        )
    with pytest.raises(ValueError, match="PaperNavSettlementRiskOverlayReport"):
        adapter.signals_from_nav_settlement_risk_overlay_report(object())
    with pytest.raises(ValueError, match="PaperNavSettlementRiskOverlayReport"):
        adapter.signals_from_nav_settlement_risk_overlay_report(
            _settlement_nav_overlay_report(
                "settlement_nav_risk_clear",
                _NavSettlementRiskOverlayReportSubclass,
            ),
        )
    with pytest.raises(ValueError, match="PaperExposureGateReport"):
        adapter.signals_from_exposure_gate_report(
            _exposure_report(_ExposureReportSubclass),
        )
    with pytest.raises(ValueError, match="PaperMarketContextFreshnessReport"):
        adapter.signals_from_market_context_freshness_report(
            _freshness_report(_FreshnessReportSubclass),
        )
    with pytest.raises(ValueError, match="supported paper gate report"):
        adapter.build_paper_strategy_readiness_signals(object())


@pytest.mark.parametrize(
    ("report_factory", "adapter_method_name", "flag_name"),
    (
        (_calibration_report, "signals_from_calibration_gate_report", "paper_only"),
        (_cost_health_report, "signals_from_cost_health_gate_report", "report_only"),
        (_liquidity_report, "signals_from_liquidity_gate_report", "readonly"),
        (
            _nav_liquidity_risk_report,
            "signals_from_nav_liquidity_risk_report",
            "paper_only",
        ),
        (
            _nav_liquidity_risk_report,
            "signals_from_nav_liquidity_risk_report",
            "report_only",
        ),
        (
            _nav_liquidity_risk_report,
            "signals_from_nav_liquidity_risk_report",
            "readonly",
        ),
        (
            lambda: _settlement_nav_overlay_report("settlement_nav_risk_clear"),
            "signals_from_nav_settlement_risk_overlay_report",
            "paper_only",
        ),
        (
            lambda: _settlement_nav_overlay_report("settlement_nav_risk_clear"),
            "signals_from_nav_settlement_risk_overlay_report",
            "report_only",
        ),
        (
            lambda: _settlement_nav_overlay_report("settlement_nav_risk_clear"),
            "signals_from_nav_settlement_risk_overlay_report",
            "readonly",
        ),
        (_exposure_report, "signals_from_exposure_gate_report", "paper_only"),
        (
            _freshness_report,
            "signals_from_market_context_freshness_report",
            "report_only",
        ),
        (
            lambda: _settlement_gate_report(status="pass"),
            "signals_from_settlement_freshness_gate_report",
            "paper_only",
        ),
        (
            lambda: _settlement_gate_report(status="pass"),
            "signals_from_settlement_freshness_gate_report",
            "report_only",
        ),
        (
            lambda: _settlement_gate_report(status="pass"),
            "signals_from_settlement_freshness_gate_report",
            "readonly",
        ),
    ),
)
def test_adapter_public_report_functions_reject_tampered_source_report_hard_flags(
    report_factory,
    adapter_method_name,
    flag_name,
):
    adapter = _adapter_module()
    report = report_factory()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=f"{flag_name} must be True"):
        getattr(adapter, adapter_method_name)(report)


def test_adapter_builder_rejects_tampered_source_report_hard_flags():
    adapter = _adapter_module()
    report = _settlement_gate_report(status="pass")
    object.__setattr__(report, "readonly", False)

    with pytest.raises(ValueError, match="readonly must be True"):
        adapter.build_paper_strategy_readiness_signals(report)


def test_adapter_exports_nav_settlement_risk_overlay_adapter():
    adapter = _adapter_module()

    assert (
        "signals_from_nav_settlement_risk_overlay_report"
        in adapter.__all__
    )


def test_adapter_does_not_mutate_source_reports():
    adapter = _adapter_module()
    report = _cost_health_report()
    original_gate_rows = report.gate_rows
    original_reason_codes = report.reason_codes
    original_report = report

    signals = adapter.signals_from_cost_health_gate_report(report)

    assert signals == (
        PaperStrategyReadinessSignal(
            source_name="cost_health_gate",
            status="watch",
            reason_codes=("spread_drag_missing",),
            severity=50,
            observed_value=1,
            threshold=0,
        ),
    )
    assert report == original_report
    assert report.gate_rows is original_gate_rows
    assert report.reason_codes is original_reason_codes
