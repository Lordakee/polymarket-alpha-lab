from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_trade_cost_audit import PaperTradeCostAuditReport
from polymarket_alpha_lab.paper_trade_cost_trend import (
    PaperTradeCostTrendConfig,
    PaperTradeCostTrendReport,
    PaperTradeCostTrendStatusRow,
    build_paper_trade_cost_trend_report,
)


GENERATED_AT = datetime(2026, 6, 17, 16, 0, tzinfo=UTC)
COST_TREND_STATUSES = (
    "empty_cost_audit_history",
    "latest_cost_observed",
    "latest_negative_cost_adjusted_edges",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


class _StringSubclass(str):
    pass


def _cost_audit(**overrides) -> PaperTradeCostAuditReport:
    values = {
        "generated_at": datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
        "config_version": "paper-trade-cost-audit-v0",
        "trade_count": 4,
        "total_filled_size": Decimal("400.0000"),
        "total_requested_size": Decimal("400.0000"),
        "fill_rate": Decimal("1.000000"),
        "mean_theoretical_edge": Decimal("0.060000"),
        "mean_cost_adjusted_edge": Decimal("0.040000"),
        "mean_edge_cost_drag": Decimal("0.020000"),
        "total_edge_cost_drag": Decimal("8.000000"),
        "mean_research_slippage": Decimal("0.004000"),
        "mean_fill_slippage": Decimal("0.006000"),
        "partial_fill_count": 0,
        "negative_cost_adjusted_edge_count": 0,
        "largest_single_trade_cost_drag": Decimal("2.000000"),
    }
    values.update(overrides)
    return PaperTradeCostAuditReport(**values)


def _config(**overrides) -> PaperTradeCostTrendConfig:
    values = {"config_version": "paper-trade-cost-trend-v0"}
    values.update(overrides)
    return PaperTradeCostTrendConfig(**values)


def _trend_report(*reports: PaperTradeCostAuditReport) -> PaperTradeCostTrendReport:
    return build_paper_trade_cost_trend_report(
        reports,
        config=_config(),
        generated_at=GENERATED_AT,
    )


def test_cost_trend_empty_input_is_readonly_report_only():
    trend = _trend_report()

    assert isinstance(trend, PaperTradeCostTrendReport)
    assert trend.generated_at == GENERATED_AT
    assert trend.config_version == "paper-trade-cost-trend-v0"
    assert trend.cost_audit_report_count == 0
    assert trend.first_report_generated_at is None
    assert trend.latest_report_generated_at is None
    assert trend.latest_trade_count == 0
    assert trend.latest_fill_rate is None
    assert trend.latest_mean_theoretical_edge is None
    assert trend.latest_mean_cost_adjusted_edge is None
    assert trend.latest_mean_edge_cost_drag is None
    assert trend.latest_total_edge_cost_drag is None
    assert trend.latest_partial_fill_count == 0
    assert trend.latest_negative_cost_adjusted_edge_count == 0
    assert trend.worst_observed_mean_edge_cost_drag is None
    assert trend.worst_observed_negative_cost_adjusted_edge_count == 0
    assert trend.consecutive_negative_cost_adjusted_edge_count == 0
    assert trend.status == "empty_cost_audit_history"
    assert trend.status_rows == tuple(
        PaperTradeCostTrendStatusRow(status, 0, None)
        for status in COST_TREND_STATUSES
    )
    assert trend.paper_only is True
    assert trend.report_only is True
    assert trend.readonly is True


def test_cost_trend_preserves_append_order_for_first_latest_and_streaks():
    first_append = _cost_audit(
        generated_at=datetime(2026, 6, 17, 14, 0, tzinfo=UTC),
        trade_count=2,
        fill_rate=Decimal("0.500000"),
        mean_theoretical_edge=Decimal("0.030000"),
        mean_cost_adjusted_edge=Decimal("0.020000"),
        mean_edge_cost_drag=Decimal("0.010000"),
        total_edge_cost_drag=Decimal("1.000000"),
        partial_fill_count=1,
        negative_cost_adjusted_edge_count=0,
    )
    earlier_timestamp = _cost_audit(
        generated_at=datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
        trade_count=3,
        fill_rate=Decimal("0.666667"),
        mean_theoretical_edge=Decimal("0.060000"),
        mean_cost_adjusted_edge=Decimal("-0.010000"),
        mean_edge_cost_drag=Decimal("0.070000"),
        total_edge_cost_drag=Decimal("6.000000"),
        partial_fill_count=2,
        negative_cost_adjusted_edge_count=2,
    )
    latest_append = _cost_audit(
        generated_at=datetime(2026, 6, 17, 13, 0, tzinfo=UTC),
        trade_count=5,
        fill_rate=Decimal("0.800000"),
        mean_theoretical_edge=Decimal("0.080000"),
        mean_cost_adjusted_edge=Decimal("-0.020000"),
        mean_edge_cost_drag=Decimal("0.100000"),
        total_edge_cost_drag=Decimal("10.000000"),
        partial_fill_count=1,
        negative_cost_adjusted_edge_count=1,
    )

    trend = _trend_report(first_append, earlier_timestamp, latest_append)

    assert trend.cost_audit_report_count == 3
    assert trend.first_report_generated_at == first_append.generated_at
    assert trend.latest_report_generated_at == latest_append.generated_at
    assert trend.latest_trade_count == 5
    assert trend.latest_fill_rate == Decimal("0.800000")
    assert trend.latest_mean_theoretical_edge == Decimal("0.080000")
    assert trend.latest_mean_cost_adjusted_edge == Decimal("-0.020000")
    assert trend.latest_mean_edge_cost_drag == Decimal("0.100000")
    assert trend.latest_total_edge_cost_drag == Decimal("10.000000")
    assert trend.latest_partial_fill_count == 1
    assert trend.latest_negative_cost_adjusted_edge_count == 1
    assert trend.worst_observed_mean_edge_cost_drag == Decimal("0.100000")
    assert trend.worst_observed_negative_cost_adjusted_edge_count == 2
    assert trend.consecutive_negative_cost_adjusted_edge_count == 2
    assert trend.status == "latest_negative_cost_adjusted_edges"


def test_cost_trend_status_rows_count_latest_statuses_with_quantized_ratios():
    reports = (
        _cost_audit(
            generated_at=datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
            negative_cost_adjusted_edge_count=0,
        ),
        _cost_audit(
            generated_at=datetime(2026, 6, 17, 13, 0, tzinfo=UTC),
            negative_cost_adjusted_edge_count=1,
        ),
        _cost_audit(
            generated_at=datetime(2026, 6, 17, 14, 0, tzinfo=UTC),
            negative_cost_adjusted_edge_count=0,
        ),
    )

    trend = _trend_report(*reports)

    assert trend.status == "latest_cost_observed"
    assert trend.status_rows == (
        PaperTradeCostTrendStatusRow(
            "empty_cost_audit_history",
            0,
            Decimal("0.000000"),
        ),
        PaperTradeCostTrendStatusRow(
            "latest_cost_observed",
            2,
            Decimal("0.666667"),
        ),
        PaperTradeCostTrendStatusRow(
            "latest_negative_cost_adjusted_edges",
            1,
            Decimal("0.333333"),
        ),
    )


def test_cost_trend_ignores_unavailable_drag_when_finding_worst_observed_drag():
    trend = _trend_report(
        _cost_audit(
            generated_at=datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
            trade_count=0,
            mean_edge_cost_drag=None,
        ),
        _cost_audit(
            generated_at=datetime(2026, 6, 17, 13, 0, tzinfo=UTC),
            trade_count=2,
            mean_edge_cost_drag=Decimal("0.030000"),
        ),
    )

    assert trend.latest_mean_edge_cost_drag == Decimal("0.030000")
    assert trend.worst_observed_mean_edge_cost_drag == Decimal("0.030000")


def test_cost_trend_duplicate_timestamps_keep_append_order_latest():
    generated_at = datetime(2026, 6, 17, 12, 0, tzinfo=UTC)
    lower_drag = _cost_audit(
        generated_at=generated_at,
        trade_count=2,
        negative_cost_adjusted_edge_count=0,
        mean_edge_cost_drag=Decimal("0.010000"),
    )
    higher_drag = _cost_audit(
        generated_at=generated_at,
        trade_count=2,
        negative_cost_adjusted_edge_count=0,
        mean_edge_cost_drag=Decimal("0.020000"),
    )

    first = _trend_report(lower_drag, higher_drag)
    second = _trend_report(higher_drag, lower_drag)

    assert first.latest_mean_edge_cost_drag == Decimal("0.020000")
    assert second.latest_mean_edge_cost_drag == Decimal("0.010000")
    assert first.worst_observed_mean_edge_cost_drag == Decimal("0.020000")
    assert second.worst_observed_mean_edge_cost_drag == Decimal("0.020000")


def test_cost_trend_rejects_invalid_inputs():
    invalid_inputs = (
        object(),
        "not reports",
        b"not reports",
        {"report": _cost_audit()},
        (report for report in ()),
    )
    for reports in invalid_inputs:
        with pytest.raises(ValueError, match="reports must be a list or tuple"):
            build_paper_trade_cost_trend_report(
                reports,
                config=_config(),
                generated_at=GENERATED_AT,
            )

    with pytest.raises(ValueError, match="reports must contain"):
        build_paper_trade_cost_trend_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        build_paper_trade_cost_trend_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_paper_trade_cost_trend_report(
            (),
            config=_config(),
            generated_at=object(),
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only"))
def test_cost_trend_rejects_non_paper_report_only_cost_audits(flag_name):
    cost_audit = _cost_audit()
    object.__setattr__(cost_audit, flag_name, False)

    with pytest.raises(ValueError, match=f"reports must contain {flag_name}"):
        build_paper_trade_cost_trend_report(
            (cost_audit,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_cost_trend_rejects_source_reports_with_impossible_negative_edge_count():
    impossible = _cost_audit(
        generated_at=datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
        trade_count=0,
        negative_cost_adjusted_edge_count=1,
        mean_edge_cost_drag=None,
    )

    with pytest.raises(
        ValueError,
        match="negative_cost_adjusted_edge_count must not exceed trade_count",
    ):
        _trend_report(impossible)


def test_cost_trend_dataclasses_are_frozen_and_revalidate_flags():
    trend = _trend_report(_cost_audit())

    with pytest.raises(FrozenInstanceError):
        trend.status = "empty_cost_audit_history"
    with pytest.raises(ValueError, match="paper_only"):
        replace(trend, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(trend, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(trend, readonly=False)


def test_cost_trend_report_revalidates_empty_report_consistency():
    trend = _trend_report()

    with pytest.raises(ValueError, match="status"):
        replace(trend, status="latest_cost_observed")
    with pytest.raises(ValueError, match="latest_trade_count"):
        replace(trend, latest_trade_count=1)
    with pytest.raises(ValueError, match="first_report_generated_at"):
        replace(
            trend,
            first_report_generated_at=datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
        )


def test_cost_trend_report_revalidates_status_and_rows():
    trend = _trend_report(
        _cost_audit(
            negative_cost_adjusted_edge_count=1,
            mean_edge_cost_drag=Decimal("0.020000"),
        ),
    )

    with pytest.raises(ValueError, match="status"):
        replace(trend, status="latest_cost_observed")
    with pytest.raises(ValueError, match="status_rows"):
        replace(trend, status_rows=tuple(reversed(trend.status_rows)))
    drifted_row = replace(trend.status_rows[0])
    object.__setattr__(drifted_row, "status_ratio", Decimal("0.000001"))
    with pytest.raises(ValueError, match="status_rows ratios"):
        replace(
            trend,
            status_rows=(
                drifted_row,
                *trend.status_rows[1:],
            ),
        )
    with pytest.raises(ValueError, match="worst_observed_mean_edge_cost_drag"):
        replace(trend, worst_observed_mean_edge_cost_drag=None)


def test_cost_trend_config_and_rows_reject_invalid_values():
    with pytest.raises(ValueError, match="config_version"):
        PaperTradeCostTrendConfig(config_version=" paper-trade-cost-trend-v0 ")
    with pytest.raises(ValueError, match="cost trend status"):
        PaperTradeCostTrendStatusRow("unknown", 0, None)
    with pytest.raises(ValueError, match="status_ratio"):
        PaperTradeCostTrendStatusRow(
            "latest_cost_observed",
            1,
            Decimal("0.1"),
        )


def test_cost_trend_rejects_scalar_subclasses_at_boundaries():
    with pytest.raises(ValueError, match="config_version"):
        PaperTradeCostTrendConfig(
            config_version=_StringSubclass("paper-trade-cost-trend-v0"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_trade_cost_trend_report(
            (),
            config=_config(),
            generated_at=_DatetimeSubclass(2026, 6, 17, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="status_count"):
        PaperTradeCostTrendStatusRow(
            "latest_cost_observed",
            _IntSubclass(1),
            Decimal("1.000000"),
        )
    with pytest.raises(ValueError, match="status_count"):
        PaperTradeCostTrendStatusRow("latest_cost_observed", True, Decimal("1.000000"))
    with pytest.raises(ValueError, match="status_ratio"):
        PaperTradeCostTrendStatusRow(
            "latest_cost_observed",
            1,
            _DecimalSubclass("1.000000"),
        )
