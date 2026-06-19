from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_recommendation_risk_budget import (
    PaperRecommendationRiskBudgetConfig,
    PaperRecommendationRiskBudgetReport,
    build_paper_recommendation_risk_budget_report,
)
from polymarket_alpha_lab.paper_strategy_selection_policy import (
    PaperStrategySelectionPolicyReport,
    PaperStrategySelectionPolicyRow,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
QUANTUM = Decimal("0.000001")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


@dataclass(frozen=True)
class NavRiskMetricsReport:
    latest_exit_nav: Decimal | None = Decimal("1000.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _selection_row(
    market_slug: str,
    *,
    decision: str = "selected",
    selected_position_notional: Decimal = Decimal("10.000000"),
    suggested_position_notional: Decimal | None = None,
) -> PaperStrategySelectionPolicyRow:
    selected_side = "yes" if decision == "selected" else "none"
    source_action = "recommend" if decision in ("selected", "skipped") else "watch"
    if suggested_position_notional is None:
        suggested_position_notional = (
            selected_position_notional if decision == "selected" else ZERO
        )
    return PaperStrategySelectionPolicyRow(
        market_slug=market_slug,
        question=f"{market_slug} question?",
        source_action=source_action,
        selected_side=selected_side,
        recommendation_score=Decimal("1.000000"),
        decision=decision,
        suggested_position_notional=suggested_position_notional,
        selected_position_notional=selected_position_notional,
        reason_codes=("selected_by_policy",)
        if decision == "selected"
        else ("source_action_watch",),
    )


def _selection_report(
    rows: tuple[PaperStrategySelectionPolicyRow, ...],
    *,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperStrategySelectionPolicyReport:
    total_selected = sum((row.selected_position_notional for row in rows), ZERO)
    max_total = Decimal("1000.000000")
    return PaperStrategySelectionPolicyReport(
        generated_at=GENERATED_AT,
        config_version="selection-policy-v1",
        row_count=len(rows),
        selected_count=sum(1 for row in rows if row.decision == "selected"),
        skipped_count=sum(1 for row in rows if row.decision == "skipped"),
        not_selected_count=sum(1 for row in rows if row.decision == "not_selected"),
        total_selected_notional=total_selected,
        total_suggested_notional=sum(
            (
                row.suggested_position_notional
                for row in rows
                if row.source_action == "recommend"
            ),
            ZERO,
        ),
        skipped_suggested_notional=sum(
            (row.suggested_position_notional for row in rows if row.decision == "skipped"),
            ZERO,
        ),
        remaining_total_notional=max_total - total_selected,
        total_notional_utilization=(total_selected / max_total).quantize(QUANTUM),
        selection_rows=rows,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _config(**overrides: object) -> PaperRecommendationRiskBudgetConfig:
    values = {
        "config_version": "risk-budget-v0",
        "max_total_utilization": Decimal("0.250000"),
        "max_single_recommendation_share": Decimal("0.100000"),
        "min_remaining_notional": Decimal("50.000000"),
        "max_selected_count": 3,
    }
    values.update(overrides)
    return PaperRecommendationRiskBudgetConfig(**values)


def _report(
    selection_report: object,
    *,
    config: PaperRecommendationRiskBudgetConfig | None = None,
    nav_report: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperRecommendationRiskBudgetReport:
    return build_paper_recommendation_risk_budget_report(
        selection_report,
        nav_risk_metrics_report=nav_report,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_risk_budget_passes_selected_rows_under_all_caps():
    selection_report = _selection_report(
        (
            _selection_row("alpha", selected_position_notional=Decimal("50.000000")),
            _selection_row("beta", selected_position_notional=Decimal("40.000000")),
        ),
    )

    report = _report(
        selection_report,
        nav_report=NavRiskMetricsReport(latest_exit_nav=Decimal("1000.000000")),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "risk-budget-v0"
    assert report.status == "pass"
    assert report.reason_codes == ("risk_budget_passed",)
    assert report.total_suggested_notional == Decimal("90.000000")
    assert report.remaining_total_notional == Decimal("160.000000")
    assert report.total_notional_utilization == Decimal("0.090000")
    assert report.utilization == Decimal("0.090000")
    assert report.largest_single_recommendation_share == Decimal("0.050000")
    assert report.selected_count == 2
    assert report.blocked_count == 0
    assert report.nav_notional == Decimal("1000.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_risk_budget_watches_when_near_but_not_over_total_cap():
    selection_report = _selection_report(
        (
            _selection_row("alpha", selected_position_notional=Decimal("240.000000")),
            _selection_row("beta", selected_position_notional=Decimal("5.000000")),
        ),
    )

    report = _report(
        selection_report,
        config=_config(
            max_single_recommendation_share=Decimal("0.500000"),
            min_remaining_notional=ZERO,
        ),
        nav_report=NavRiskMetricsReport(latest_exit_nav=Decimal("1000.000000")),
    )

    assert report.status == "watch"
    assert report.reason_codes == ("near_total_utilization_cap",)
    assert report.total_notional_utilization == Decimal("0.245000")
    assert report.remaining_total_notional == Decimal("5.000000")
    assert report.blocked_count == 0


def test_risk_budget_blocks_when_caps_are_breached():
    selection_report = _selection_report(
        (
            _selection_row("alpha", selected_position_notional=Decimal("120.000000")),
            _selection_row("beta", selected_position_notional=Decimal("110.000000")),
            _selection_row("gamma", selected_position_notional=Decimal("100.000000")),
            _selection_row("delta", selected_position_notional=Decimal("5.000000")),
        ),
    )

    report = _report(
        selection_report,
        nav_report=NavRiskMetricsReport(latest_exit_nav=Decimal("1000.000000")),
    )

    assert report.status == "blocked"
    assert report.reason_codes == (
        "total_utilization_cap_exceeded",
        "single_recommendation_share_exceeded",
        "min_remaining_notional_breached",
        "max_selected_count_exceeded",
    )
    assert report.total_suggested_notional == Decimal("335.000000")
    assert report.remaining_total_notional == ZERO
    assert report.total_notional_utilization == Decimal("0.335000")
    assert report.largest_single_recommendation_share == Decimal("0.120000")
    assert report.selected_count == 4
    assert report.blocked_count == 4


def test_risk_budget_uses_optional_nav_absence_without_division_metrics():
    selection_report = _selection_report(
        (_selection_row("alpha", selected_position_notional=Decimal("12.345678")),),
    )

    report = _report(selection_report, nav_report=None)

    assert report.status == "pass"
    assert report.reason_codes == ("risk_budget_passed",)
    assert report.nav_notional is None
    assert report.total_suggested_notional == Decimal("12.345678")
    assert report.remaining_total_notional is None
    assert report.total_notional_utilization is None
    assert report.largest_single_recommendation_share is None
    assert report.selected_count == 1
    assert report.blocked_count == 0


def test_risk_budget_blocks_empty_selection():
    report = _report(_selection_report(()))

    assert report.status == "blocked"
    assert report.reason_codes == ("empty_selection",)
    assert report.total_suggested_notional == ZERO
    assert report.remaining_total_notional is None
    assert report.total_notional_utilization is None
    assert report.largest_single_recommendation_share is None
    assert report.selected_count == 0
    assert report.blocked_count == 1


def test_risk_budget_config_validates_caps_and_types():
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=" risk-budget-v0")
    with pytest.raises(ValueError, match="max_total_utilization"):
        _config(max_total_utilization=Decimal("0.000000"))
    with pytest.raises(ValueError, match="max_total_utilization"):
        _config(max_total_utilization=Decimal("1.000001"))
    with pytest.raises(ValueError, match="max_single_recommendation_share"):
        _config(max_single_recommendation_share=Decimal("0.000000"))
    with pytest.raises(ValueError, match="max_single_recommendation_share"):
        _config(max_single_recommendation_share=Decimal("0.1000001"))
    with pytest.raises(ValueError, match="min_remaining_notional"):
        _config(min_remaining_notional=Decimal("-0.000001"))
    with pytest.raises(ValueError, match="max_selected_count"):
        _config(max_selected_count=0)
    with pytest.raises(ValueError, match="max_selected_count"):
        _config(max_selected_count=_IntSubclass(3))


def test_risk_budget_validates_hard_flags_when_inputs_expose_them():
    @dataclass(frozen=True)
    class SelectionShape:
        selection_rows: tuple[PaperStrategySelectionPolicyRow, ...]
        paper_only: object = True
        report_only: object = True
        readonly: object = True

    rows = (_selection_row("alpha"),)

    with pytest.raises(ValueError, match="selection_report must be paper_only"):
        _report(SelectionShape(rows, paper_only=False))
    with pytest.raises(ValueError, match="selection_report must be report_only"):
        _report(SelectionShape(rows, report_only=False))
    with pytest.raises(ValueError, match="selection_report must be readonly"):
        _report(SelectionShape(rows, readonly=False))
    with pytest.raises(ValueError, match="nav_risk_metrics_report must be paper_only"):
        _report(
            _selection_report(rows),
            nav_report=NavRiskMetricsReport(paper_only=False),
        )
    with pytest.raises(ValueError, match="nav_risk_metrics_report must be report_only"):
        _report(
            _selection_report(rows),
            nav_report=NavRiskMetricsReport(report_only=False),
        )
    with pytest.raises(ValueError, match="nav_risk_metrics_report must be readonly"):
        _report(
            _selection_report(rows),
            nav_report=NavRiskMetricsReport(readonly=False),
        )


def test_risk_budget_constructor_rejects_inconsistent_counts_status_and_reason_codes():
    valid = _report(
        _selection_report((_selection_row("alpha"),)),
        nav_report=NavRiskMetricsReport(latest_exit_nav=Decimal("1000.000000")),
    )

    with pytest.raises(ValueError, match="selected_count"):
        replace(valid, selected_count=2)
    with pytest.raises(ValueError, match="blocked_count"):
        replace(valid, blocked_count=1)
    with pytest.raises(ValueError, match="total_notional_utilization"):
        replace(valid, total_notional_utilization=Decimal("0.200000"))
    with pytest.raises(ValueError, match="remaining_total_notional"):
        replace(valid, remaining_total_notional=Decimal("800.000000"))
    with pytest.raises(ValueError, match="largest_single_recommendation_share"):
        replace(valid, largest_single_recommendation_share=Decimal("0.020000"))
    with pytest.raises(ValueError, match="status"):
        replace(valid, status="blocked")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(valid, reason_codes=("total_utilization_cap_exceeded",))


def test_risk_budget_decimal_quantization_utc_and_frozen_validations():
    report = _report(
        _selection_report((_selection_row("alpha"),)),
        generated_at=datetime(2026, 6, 19, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
        nav_report=NavRiskMetricsReport(latest_exit_nav=Decimal("1000.000000")),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    with pytest.raises(FrozenInstanceError):
        report.status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="generated_at"):
        _report(_selection_report((_selection_row("alpha"),)), generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        PaperRecommendationRiskBudgetReport(
            generated_at=_DatetimeSubclass(2026, 6, 19, 12, 0, tzinfo=UTC),
            config_version="risk-budget-v0",
            status="blocked",
            reason_codes=("empty_selection",),
            total_suggested_notional=ZERO,
            remaining_total_notional=None,
            total_notional_utilization=None,
            largest_single_recommendation_share=None,
            selected_count=0,
            blocked_count=1,
            max_total_utilization=Decimal("0.250000"),
            max_single_recommendation_share=Decimal("0.100000"),
            min_remaining_notional=Decimal("50.000000"),
            max_selected_count=3,
            selected_position_notional_values=(),
            nav_notional=None,
        )
    with pytest.raises(ValueError, match="max_total_utilization"):
        _config(max_total_utilization=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="total_suggested_notional"):
        replace(report, total_suggested_notional=Decimal("10.0000001"))
    with pytest.raises(ValueError, match="total_notional_utilization"):
        replace(report, total_notional_utilization=Decimal("0.0100001"))
    with pytest.raises(ValueError, match="selected_position_notional_values"):
        replace(report, selected_position_notional_values=(Decimal("10.0000001"),))


def test_risk_budget_accepts_selection_policy_shape_without_exact_type_cycle():
    @dataclass(frozen=True)
    class SelectionShape:
        selection_rows: tuple[PaperStrategySelectionPolicyRow, ...]
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    shape = SelectionShape(
        selection_rows=(
            _selection_row("alpha", selected_position_notional=Decimal("20.000000")),
        ),
    )

    report = _report(
        shape,
        nav_report=NavRiskMetricsReport(latest_exit_nav=Decimal("1000.000000")),
    )

    assert report.status == "pass"
    assert report.total_suggested_notional == Decimal("20.000000")
    assert report.selected_count == 1
