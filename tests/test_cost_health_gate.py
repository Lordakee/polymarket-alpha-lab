from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.edge_cost_summary_trend import (
    PaperEdgeCostSummaryTrendReport,
    PaperEdgeCostSummaryTrendStatusRow,
)
from polymarket_alpha_lab.paper_trade_cost_trend import (
    PaperTradeCostTrendReport,
    PaperTradeCostTrendStatusRow,
)


GENERATED_AT = datetime(2026, 6, 18, 16, 0, tzinfo=UTC)
SUMMARY_ROW_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


class _StringSubclass(str):
    pass


def _gate_module():
    return import_module("polymarket_alpha_lab.cost_health_gate")


def _config(**overrides):
    gate = _gate_module()
    values = {
        "config_version": "cost-health-gate-v0",
        "max_average_cost_drag": Decimal("0.030000"),
        "max_spread_drag": Decimal("0.010000"),
        "min_net_edge_after_cost": Decimal("0.010000"),
        "max_consecutive_negative_net_edge_periods": 0,
    }
    values.update(overrides)
    return gate.PaperCostHealthGateConfig(**values)


def _summary_row(**overrides):
    gate = _gate_module()
    values = {
        "observed_at": SUMMARY_ROW_AT,
        "average_cost_drag": Decimal("0.020000"),
        "spread_drag": Decimal("0.006000"),
        "net_edge_after_cost": Decimal("0.030000"),
    }
    values.update(overrides)
    return gate.PaperCostHealthSummaryRow(**values)


def _gate_report(source, **overrides):
    gate = _gate_module()
    return gate.build_paper_cost_health_gate_report(
        source,
        config=overrides.pop("config", _config()),
        generated_at=overrides.pop("generated_at", GENERATED_AT),
        **overrides,
    )


def _trade_cost_status_rows() -> tuple[PaperTradeCostTrendStatusRow, ...]:
    return (
        PaperTradeCostTrendStatusRow(
            "empty_cost_audit_history",
            0,
            Decimal("0.000000"),
        ),
        PaperTradeCostTrendStatusRow(
            "latest_cost_observed",
            1,
            Decimal("1.000000"),
        ),
        PaperTradeCostTrendStatusRow(
            "latest_negative_cost_adjusted_edges",
            0,
            Decimal("0.000000"),
        ),
    )


def _trade_cost_trend(**overrides) -> PaperTradeCostTrendReport:
    values = {
        "generated_at": datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        "config_version": "paper-trade-cost-trend-v0",
        "cost_audit_report_count": 1,
        "first_report_generated_at": datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        "latest_report_generated_at": datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        "latest_trade_count": 4,
        "latest_fill_rate": Decimal("1.000000"),
        "latest_mean_theoretical_edge": Decimal("0.060000"),
        "latest_mean_cost_adjusted_edge": Decimal("0.040000"),
        "latest_mean_edge_cost_drag": Decimal("0.020000"),
        "latest_total_edge_cost_drag": Decimal("8.000000"),
        "latest_partial_fill_count": 0,
        "latest_negative_cost_adjusted_edge_count": 0,
        "worst_observed_mean_edge_cost_drag": Decimal("0.020000"),
        "worst_observed_negative_cost_adjusted_edge_count": 0,
        "consecutive_negative_cost_adjusted_edge_count": 0,
        "status": "latest_cost_observed",
        "status_rows": _trade_cost_status_rows(),
    }
    values.update(overrides)
    return PaperTradeCostTrendReport(**values)


def _edge_cost_status_rows() -> tuple[PaperEdgeCostSummaryTrendStatusRow, ...]:
    return (
        PaperEdgeCostSummaryTrendStatusRow(
            "empty_edge_cost_history",
            0,
            Decimal("0.000000"),
        ),
        PaperEdgeCostSummaryTrendStatusRow(
            "insufficient_edge_cost_sample",
            0,
            Decimal("0.000000"),
        ),
        PaperEdgeCostSummaryTrendStatusRow(
            "edge_cost_evidence_observed",
            0,
            Decimal("0.000000"),
        ),
        PaperEdgeCostSummaryTrendStatusRow(
            "edge_cost_quality_flags",
            1,
            Decimal("1.000000"),
        ),
    )


def _edge_cost_trend(**overrides) -> PaperEdgeCostSummaryTrendReport:
    values = {
        "generated_at": datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        "config_version": "edge-cost-summary-trend-v0",
        "edge_cost_report_count": 1,
        "first_report_generated_at": datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        "latest_report_generated_at": datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        "latest_status": "edge_cost_quality_flags",
        "latest_edge_observation_count": 4,
        "latest_mean_theoretical_edge_ratio": Decimal("0.040000"),
        "latest_mean_executable_edge_ratio": Decimal("-0.005000"),
        "latest_mean_edge_cost_drag": Decimal("0.045000"),
        "latest_mean_fill_probability": Decimal("0.700000"),
        "latest_mean_residual_exposure_ratio": Decimal("0.100000"),
        "latest_mean_paper_return_ratio": Decimal("-0.010000"),
        "latest_negative_executable_edge_count": 1,
        "latest_negative_executable_edge_rate": Decimal("0.250000"),
        "latest_low_fill_probability_count": 0,
        "latest_low_fill_probability_rate": Decimal("0.000000"),
        "latest_high_residual_exposure_count": 0,
        "latest_high_residual_exposure_rate": Decimal("0.000000"),
        "latest_positive_paper_return_count": 0,
        "latest_positive_paper_return_rate": Decimal("0.000000"),
        "largest_negative_executable_edge_count": 1,
        "largest_low_fill_probability_count": 0,
        "largest_high_residual_exposure_count": 0,
        "worst_observed_mean_edge_cost_drag": Decimal("0.045000"),
        "worst_observed_mean_residual_exposure_ratio": Decimal("0.100000"),
        "consecutive_quality_flag_count": 1,
        "consecutive_insufficient_sample_count": 0,
        "status_rows": _edge_cost_status_rows(),
    }
    values.update(overrides)
    return PaperEdgeCostSummaryTrendReport(**values)


def test_cost_health_gate_passes_complete_summary_rows_in_deterministic_order():
    first = _summary_row(
        observed_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
        average_cost_drag=Decimal("0.010000"),
        spread_drag=Decimal("0.004000"),
        net_edge_after_cost=Decimal("0.020000"),
    )
    latest = _summary_row()

    report = _gate_report((first, latest))

    assert report.status == "paper_cost_health_pass"
    assert report.source_report_kind == "summary_rows"
    assert report.source_report_count == 2
    assert report.generated_at == GENERATED_AT
    assert report.first_source_generated_at == first.observed_at
    assert report.latest_source_generated_at == latest.observed_at
    assert report.reason_codes == ()
    assert tuple(row.gate_name for row in report.gate_rows) == (
        "data_completeness",
        "average_cost_drag",
        "spread_drag",
        "net_edge_after_cost",
        "negative_net_edge_streak",
    )
    assert tuple(row.status for row in report.gate_rows) == (
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
    )
    assert report.gate_rows[1].observed_value == Decimal("0.020000")
    assert report.gate_rows[1].threshold_value == Decimal("0.030000")
    assert report.gate_rows[2].observed_value == Decimal("0.006000")
    assert report.gate_rows[2].threshold_value == Decimal("0.010000")
    assert report.gate_rows[3].observed_value == Decimal("0.030000")
    assert report.gate_rows[3].threshold_value == Decimal("0.010000")
    assert report.gate_rows[4].observed_value == 0
    assert report.gate_rows[4].threshold_value == 0
    assert report.gate_rows[0].reason_codes == ("data_available",)
    assert report.gate_rows[1].reason_codes == (
        "average_cost_drag_within_threshold",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_cost_health_gate_blocks_high_average_cost_drag_from_cost_trend():
    trend = _trade_cost_trend(
        latest_mean_edge_cost_drag=Decimal("0.050000"),
        worst_observed_mean_edge_cost_drag=Decimal("0.050000"),
    )

    report = _gate_report(trend)
    rows = {row.gate_name: row for row in report.gate_rows}

    assert report.status == "paper_cost_health_blocked"
    assert report.source_report_kind == "paper_trade_cost_trend"
    assert rows["average_cost_drag"].status == "blocked"
    assert rows["average_cost_drag"].observed_value == Decimal("0.050000")
    assert rows["average_cost_drag"].threshold_value == Decimal("0.030000")
    assert rows["average_cost_drag"].reason_codes == (
        "average_cost_drag_above_threshold",
    )
    assert rows["spread_drag"].status == "watch"
    assert rows["spread_drag"].reason_codes == ("spread_drag_missing",)
    assert report.reason_codes == (
        "average_cost_drag_above_threshold",
        "spread_drag_missing",
    )


def test_cost_health_gate_blocks_negative_net_edge_from_edge_cost_trend():
    report = _gate_report(
        _edge_cost_trend(
            latest_mean_executable_edge_ratio=Decimal("-0.005000"),
            latest_mean_edge_cost_drag=Decimal("0.020000"),
            worst_observed_mean_edge_cost_drag=Decimal("0.020000"),
        ),
        config=_config(min_net_edge_after_cost=Decimal("0.000000")),
    )
    rows = {row.gate_name: row for row in report.gate_rows}

    assert report.status == "paper_cost_health_blocked"
    assert report.source_report_kind == "paper_edge_cost_summary_trend"
    assert rows["net_edge_after_cost"].status == "blocked"
    assert rows["net_edge_after_cost"].observed_value == Decimal("-0.005000")
    assert rows["net_edge_after_cost"].threshold_value == Decimal("0.000000")
    assert rows["net_edge_after_cost"].reason_codes == (
        "net_edge_after_cost_below_threshold",
    )
    assert rows["negative_net_edge_streak"].status == "watch"
    assert rows["negative_net_edge_streak"].reason_codes == (
        "negative_net_edge_streak_unsupported",
    )


def test_cost_health_gate_consumes_edge_cost_summary_trend_metrics_directly():
    first_generated_at = datetime(
        2026,
        6,
        18,
        10,
        0,
        tzinfo=timezone(timedelta(hours=-2)),
    )
    latest_generated_at = datetime(2026, 6, 18, 13, 30, tzinfo=UTC)
    trend = _edge_cost_trend(
        generated_at=datetime(2026, 6, 18, 15, 0, tzinfo=UTC),
        edge_cost_report_count=3,
        first_report_generated_at=first_generated_at,
        latest_report_generated_at=latest_generated_at,
        latest_mean_theoretical_edge_ratio=Decimal("0.044000"),
        latest_mean_executable_edge_ratio=Decimal("0.012000"),
        latest_mean_edge_cost_drag=Decimal("0.015000"),
        worst_observed_mean_edge_cost_drag=Decimal("0.029000"),
        largest_negative_executable_edge_count=4,
        consecutive_quality_flag_count=2,
        status_rows=(
            PaperEdgeCostSummaryTrendStatusRow(
                "empty_edge_cost_history",
                0,
                Decimal("0.000000"),
            ),
            PaperEdgeCostSummaryTrendStatusRow(
                "insufficient_edge_cost_sample",
                1,
                Decimal("0.333333"),
            ),
            PaperEdgeCostSummaryTrendStatusRow(
                "edge_cost_evidence_observed",
                0,
                Decimal("0.000000"),
            ),
            PaperEdgeCostSummaryTrendStatusRow(
                "edge_cost_quality_flags",
                2,
                Decimal("0.666667"),
            ),
        ),
    )

    report = _gate_report(
        trend,
        config=_config(
            max_average_cost_drag=Decimal("0.028000"),
            min_net_edge_after_cost=Decimal("0.010000"),
        ),
    )
    rows = {row.gate_name: row for row in report.gate_rows}

    assert report.status == "paper_cost_health_blocked"
    assert report.source_report_kind == "paper_edge_cost_summary_trend"
    assert report.source_report_count == 3
    assert report.first_source_generated_at == datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    assert report.latest_source_generated_at == latest_generated_at
    assert rows["data_completeness"].observed_value == 3
    assert rows["average_cost_drag"].status == "blocked"
    assert rows["average_cost_drag"].observed_value == Decimal("0.029000")
    assert rows["average_cost_drag"].threshold_value == Decimal("0.028000")
    assert rows["average_cost_drag"].reason_codes == (
        "average_cost_drag_above_threshold",
    )
    assert rows["net_edge_after_cost"].status == "pass"
    assert rows["net_edge_after_cost"].observed_value == Decimal("0.012000")
    assert rows["net_edge_after_cost"].threshold_value == Decimal("0.010000")
    assert rows["net_edge_after_cost"].reason_codes == (
        "net_edge_after_cost_within_threshold",
    )
    assert rows["spread_drag"].status == "watch"
    assert rows["spread_drag"].observed_value is None
    assert rows["spread_drag"].threshold_value == Decimal("0.010000")
    assert rows["spread_drag"].reason_codes == ("spread_drag_missing",)
    assert rows["negative_net_edge_streak"].status == "watch"
    assert rows["negative_net_edge_streak"].observed_value is None
    assert rows["negative_net_edge_streak"].threshold_value == 0
    assert rows["negative_net_edge_streak"].reason_codes == (
        "negative_net_edge_streak_unsupported",
    )
    assert report.reason_codes == (
        "average_cost_drag_above_threshold",
        "spread_drag_missing",
        "negative_net_edge_streak_unsupported",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    object.__setattr__(trend, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        _gate_report(trend)

    object.__setattr__(trend, "paper_only", True)
    object.__setattr__(trend, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        _gate_report(trend)

    object.__setattr__(trend, "report_only", True)
    object.__setattr__(trend, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        _gate_report(trend)


def test_cost_health_gate_empty_source_blocks_and_keeps_metrics_from_passing():
    report = _gate_report(())

    assert report.status == "paper_cost_health_blocked"
    assert report.source_report_count == 0
    assert tuple(row.status for row in report.gate_rows) == (
        "blocked",
        "watch",
        "watch",
        "watch",
        "watch",
    )
    assert report.gate_rows[0].reason_codes == ("empty_cost_health_source",)
    assert report.reason_codes == (
        "empty_cost_health_source",
        "average_cost_drag_missing",
        "spread_drag_missing",
        "net_edge_after_cost_missing",
        "negative_net_edge_streak_unsupported",
    )


@pytest.mark.parametrize("status", ("blocked", "watch"))
def test_cost_health_gate_rejects_non_pass_row_without_reason_codes(status):
    gate = _gate_module()

    with pytest.raises(ValueError, match="reason_codes"):
        gate.PaperCostHealthGateRow(
            gate_name="average_cost_drag",
            status=status,
            observed_value=Decimal("0.040000"),
            threshold_value=Decimal("0.030000"),
            reason_codes=(),
        )


@pytest.mark.parametrize("status", ("blocked", "watch"))
def test_cost_health_gate_rejects_report_with_non_pass_row_without_reason_codes(
    status,
):
    gate = _gate_module()
    rows = (
        gate.PaperCostHealthGateRow(
            gate_name="data_completeness",
            status="pass",
            observed_value=1,
            threshold_value=">0",
            reason_codes=("data_available",),
        ),
        gate.PaperCostHealthGateRow(
            gate_name="average_cost_drag",
            status=status,
            observed_value=Decimal("0.040000"),
            threshold_value=Decimal("0.030000"),
            reason_codes=("average_cost_drag_above_threshold",),
        ),
        gate.PaperCostHealthGateRow(
            gate_name="spread_drag",
            status="pass",
            observed_value=Decimal("0.006000"),
            threshold_value=Decimal("0.010000"),
            reason_codes=("spread_drag_within_threshold",),
        ),
        gate.PaperCostHealthGateRow(
            gate_name="net_edge_after_cost",
            status="pass",
            observed_value=Decimal("0.030000"),
            threshold_value=Decimal("0.010000"),
            reason_codes=("net_edge_after_cost_within_threshold",),
        ),
        gate.PaperCostHealthGateRow(
            gate_name="negative_net_edge_streak",
            status="pass",
            observed_value=0,
            threshold_value=0,
            reason_codes=("negative_net_edge_streak_within_threshold",),
        ),
    )
    object.__setattr__(rows[1], "reason_codes", ())
    report_status = (
        "paper_cost_health_blocked"
        if status == "blocked"
        else "paper_cost_health_watch"
    )

    with pytest.raises(ValueError, match="non-passing gate rows"):
        gate.PaperCostHealthGateReport(
            generated_at=GENERATED_AT,
            config_version="cost-health-gate-v0",
            source_report_kind="summary_rows",
            source_report_count=1,
            first_source_generated_at=SUMMARY_ROW_AT,
            latest_source_generated_at=SUMMARY_ROW_AT,
            status=report_status,
            gate_rows=rows,
            reason_codes=(),
        )


def test_cost_health_gate_rejects_exact_scalar_type_violations():
    gate = _gate_module()

    with pytest.raises(ValueError, match="config_version"):
        gate.PaperCostHealthGateConfig(
            config_version=_StringSubclass("cost-health-gate-v0"),
        )
    with pytest.raises(ValueError, match="max_average_cost_drag"):
        gate.PaperCostHealthGateConfig(
            config_version="cost-health-gate-v0",
            max_average_cost_drag=_DecimalSubclass("0.030000"),
        )
    with pytest.raises(ValueError, match="max_consecutive_negative_net_edge_periods"):
        gate.PaperCostHealthGateConfig(
            config_version="cost-health-gate-v0",
            max_consecutive_negative_net_edge_periods=_IntSubclass(0),
        )
    with pytest.raises(ValueError, match="max_consecutive_negative_net_edge_periods"):
        gate.PaperCostHealthGateConfig(
            config_version="cost-health-gate-v0",
            max_consecutive_negative_net_edge_periods=True,
        )
    with pytest.raises(ValueError, match="observed_at"):
        gate.PaperCostHealthSummaryRow(
            observed_at=_DatetimeSubclass(2026, 6, 18, 12, 0, tzinfo=UTC),
            average_cost_drag=Decimal("0.010000"),
            spread_drag=Decimal("0.001000"),
            net_edge_after_cost=Decimal("0.020000"),
        )
    with pytest.raises(ValueError, match="average_cost_drag"):
        gate.PaperCostHealthSummaryRow(
            observed_at=SUMMARY_ROW_AT,
            average_cost_drag=0.01,
            spread_drag=Decimal("0.001000"),
            net_edge_after_cost=Decimal("0.020000"),
        )
    with pytest.raises(ValueError, match="observed_value"):
        gate.PaperCostHealthGateRow(
            gate_name="average_cost_drag",
            status="pass",
            observed_value=True,
            threshold_value=Decimal("0.030000"),
            reason_codes=("average_cost_drag_within_threshold",),
        )
    with pytest.raises(ValueError, match="source"):
        _gate_report(object())


def test_cost_health_gate_normalizes_datetimes_to_utc():
    gate = _gate_module()
    observed_at = datetime(2026, 6, 18, 14, 0, tzinfo=timezone(timedelta(hours=2)))
    row = gate.PaperCostHealthSummaryRow(
        observed_at=observed_at,
        average_cost_drag=Decimal("0.010000"),
        spread_drag=Decimal("0.001000"),
        net_edge_after_cost=Decimal("0.020000"),
    )

    report = _gate_report(
        (row,),
        generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=timezone(timedelta(hours=-5))),
    )

    assert row.observed_at == datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    assert report.generated_at == GENERATED_AT
    assert report.first_source_generated_at == row.observed_at
    assert report.latest_source_generated_at == row.observed_at


def test_cost_health_gate_dataclasses_are_frozen_and_revalidate_hard_flags():
    gate = _gate_module()
    row = _summary_row()
    report = _gate_report((row,))

    with pytest.raises(FrozenInstanceError):
        report.status = "paper_cost_health_watch"
    with pytest.raises(FrozenInstanceError):
        row.net_edge_after_cost = Decimal("0.000000")
    with pytest.raises(FrozenInstanceError):
        report.gate_rows[0].status = "watch"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)

    trend = _trade_cost_trend()
    object.__setattr__(trend, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        gate.build_paper_cost_health_gate_report(
            trend,
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_cost_health_gate_reports_reason_codes_in_gate_order():
    rows = (
        _summary_row(
            observed_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
            average_cost_drag=Decimal("0.040000"),
            spread_drag=Decimal("0.011000"),
            net_edge_after_cost=Decimal("-0.001000"),
        ),
        _summary_row(
            observed_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
            average_cost_drag=Decimal("0.050000"),
            spread_drag=Decimal("0.012000"),
            net_edge_after_cost=Decimal("-0.002000"),
        ),
    )

    report = _gate_report(
        rows,
        config=_config(max_consecutive_negative_net_edge_periods=1),
    )

    assert tuple(row.gate_name for row in report.gate_rows) == (
        "data_completeness",
        "average_cost_drag",
        "spread_drag",
        "net_edge_after_cost",
        "negative_net_edge_streak",
    )
    assert report.reason_codes == (
        "average_cost_drag_above_threshold",
        "spread_drag_above_threshold",
        "net_edge_after_cost_below_threshold",
        "negative_net_edge_streak_above_threshold",
    )
    assert tuple(row.status for row in report.gate_rows) == (
        "pass",
        "blocked",
        "blocked",
        "blocked",
        "blocked",
    )
