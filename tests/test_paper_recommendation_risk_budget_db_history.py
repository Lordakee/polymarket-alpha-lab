from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_recommendation_risk_budget import (
    PaperRecommendationRiskBudgetReport,
)
from polymarket_alpha_lab.paper_recommendation_risk_budget_db_history import (
    PaperRecommendationRiskBudgetDbHistoryConfig,
    PaperRecommendationRiskBudgetDbHistoryReport,
    build_paper_recommendation_risk_budget_db_history_report,
)


GENERATED_AT = datetime(2026, 6, 22, 10, 0, tzinfo=UTC)
BASE_REPORT_AT = datetime(2026, 6, 22, 8, 0, tzinfo=UTC)


def _config() -> PaperRecommendationRiskBudgetDbHistoryConfig:
    return PaperRecommendationRiskBudgetDbHistoryConfig(
        config_version="risk-budget-db-history-v0",
    )


def _history(
    reports: list[PaperRecommendationRiskBudgetReport]
    | tuple[PaperRecommendationRiskBudgetReport, ...],
) -> PaperRecommendationRiskBudgetDbHistoryReport:
    return build_paper_recommendation_risk_budget_db_history_report(
        reports,
        config=_config(),
        generated_at=GENERATED_AT,
    )


def _report(
    *,
    generated_at: datetime,
    status: str = "pass",
    reason_codes: tuple[str, ...] = ("risk_budget_passed",),
    total_notional_utilization: Decimal | None = Decimal("0.100000"),
    largest_single_recommendation_share: Decimal | None = Decimal("0.050000"),
    selected_count: int = 2,
    total_suggested_notional: Decimal = Decimal("100.000000"),
    nav_notional: Decimal | None = Decimal("1000.000000"),
    max_selected_count: int = 5,
) -> PaperRecommendationRiskBudgetReport:
    if nav_notional is not None and total_notional_utilization is not None:
        total_suggested_notional = (
            nav_notional * total_notional_utilization
        ).quantize(Decimal("0.000001"))
    selected_values = _selected_values(
        total_suggested_notional=total_suggested_notional,
        largest_single_recommendation_share=largest_single_recommendation_share,
        selected_count=selected_count,
        nav_notional=nav_notional,
    )
    return PaperRecommendationRiskBudgetReport(
        generated_at=generated_at,
        config_version="risk-budget-v0",
        status=status,
        reason_codes=reason_codes,
        total_suggested_notional=total_suggested_notional,
        remaining_total_notional=_remaining_total_notional(
            total_suggested_notional,
            nav_notional,
        ),
        total_notional_utilization=total_notional_utilization,
        largest_single_recommendation_share=largest_single_recommendation_share,
        selected_count=selected_count,
        blocked_count=_blocked_count(reason_codes),
        max_total_utilization=Decimal("0.250000"),
        max_single_recommendation_share=Decimal("0.100000"),
        min_remaining_notional=Decimal("0.000000"),
        max_selected_count=max_selected_count,
        selected_position_notional_values=selected_values,
        nav_notional=nav_notional,
    )


def _selected_values(
    *,
    total_suggested_notional: Decimal,
    largest_single_recommendation_share: Decimal | None,
    selected_count: int,
    nav_notional: Decimal | None,
) -> tuple[Decimal, ...]:
    if selected_count == 0:
        return ()
    if nav_notional is not None and largest_single_recommendation_share is not None:
        largest = (nav_notional * largest_single_recommendation_share).quantize(
            Decimal("0.000001"),
        )
    else:
        largest = (total_suggested_notional / Decimal(selected_count)).quantize(
            Decimal("0.000001"),
        )
    if selected_count == 1:
        return (total_suggested_notional,)
    remaining = total_suggested_notional - largest
    tail_count = selected_count - 1
    tail_value = (remaining / Decimal(tail_count)).quantize(Decimal("0.000001"))
    values = [largest, *(tail_value for _ in range(tail_count))]
    values[-1] = total_suggested_notional - sum(values[:-1], Decimal("0.000000"))
    return tuple(values)


def _remaining_total_notional(
    total_suggested_notional: Decimal,
    nav_notional: Decimal | None,
) -> Decimal | None:
    if nav_notional is None:
        return None
    remaining = nav_notional * Decimal("0.250000") - total_suggested_notional
    if remaining < Decimal("0.000000"):
        return Decimal("0.000000")
    return remaining.quantize(Decimal("0.000001"))


def _blocked_count(reason_codes: tuple[str, ...]) -> int:
    blocking_reason_codes = {
        "empty_selection",
        "total_utilization_cap_exceeded",
        "single_recommendation_share_exceeded",
        "min_remaining_notional_breached",
        "max_selected_count_exceeded",
    }
    return sum(1 for reason_code in reason_codes if reason_code in blocking_reason_codes)


def test_risk_budget_db_history_empty_history_is_readonly_report() -> None:
    history = _history(())

    assert history.generated_at == GENERATED_AT
    assert history.config_version == "risk-budget-db-history-v0"
    assert history.status == "empty_paper_recommendation_risk_budget_db_history"
    assert history.report_count == 0
    assert history.first_report_generated_at is None
    assert history.latest_report_generated_at is None
    assert history.latest_status is None
    assert history.status_counts == (("pass", 0), ("watch", 0), ("blocked", 0))
    assert history.latest_total_notional_utilization is None
    assert history.worst_total_notional_utilization is None
    assert history.latest_largest_single_recommendation_share is None
    assert history.worst_largest_single_recommendation_share is None
    assert history.latest_selected_count is None
    assert history.latest_blocked_count is None
    assert history.reason_code_counts == ()
    assert history.duplicate_generated_at_count == 0
    assert history.paper_only is True
    assert history.report_only is True
    assert history.readonly is True


def test_risk_budget_db_history_counts_statuses_and_latest_status() -> None:
    history = _history(
        (
            _report(
                generated_at=BASE_REPORT_AT,
                status="pass",
                reason_codes=("risk_budget_passed",),
            ),
            _report(
                generated_at=BASE_REPORT_AT + timedelta(minutes=1),
                status="watch",
                reason_codes=("near_total_utilization_cap",),
                total_notional_utilization=Decimal("0.240000"),
                largest_single_recommendation_share=Decimal("0.080000"),
                selected_count=3,
            ),
            _report(
                generated_at=BASE_REPORT_AT + timedelta(minutes=2),
                status="blocked",
                reason_codes=("max_selected_count_exceeded",),
                largest_single_recommendation_share=Decimal("0.040000"),
                selected_count=4,
                max_selected_count=3,
            ),
        ),
    )

    assert history.status == "latest_paper_recommendation_risk_budget_blocked"
    assert history.report_count == 3
    assert history.first_report_generated_at == BASE_REPORT_AT
    assert history.latest_report_generated_at == BASE_REPORT_AT + timedelta(minutes=2)
    assert history.latest_status == "blocked"
    assert history.status_counts == (("pass", 1), ("watch", 1), ("blocked", 1))
    assert history.latest_selected_count == 4
    assert history.latest_blocked_count == 1


def test_risk_budget_db_history_sorts_out_of_order_history_and_counts_duplicate_ties() -> None:
    duplicate_time = BASE_REPORT_AT + timedelta(minutes=2)
    loaded_history = (
        _report(
            generated_at=duplicate_time,
            status="watch",
            reason_codes=("near_total_utilization_cap",),
            total_notional_utilization=Decimal("0.240000"),
            largest_single_recommendation_share=Decimal("0.080000"),
            selected_count=3,
        ),
        _report(
            generated_at=BASE_REPORT_AT,
            status="pass",
            reason_codes=("risk_budget_passed",),
            total_notional_utilization=Decimal("0.050000"),
            largest_single_recommendation_share=Decimal("0.050000"),
            selected_count=1,
        ),
        _report(
            generated_at=duplicate_time,
            status="blocked",
            reason_codes=("max_selected_count_exceeded",),
            largest_single_recommendation_share=Decimal("0.040000"),
            selected_count=4,
            max_selected_count=3,
        ),
    )

    history = _history(loaded_history)

    assert history.first_report_generated_at == BASE_REPORT_AT
    assert history.latest_report_generated_at == duplicate_time
    assert history.latest_status == "blocked"
    assert history.status == "latest_paper_recommendation_risk_budget_blocked"
    assert history.latest_total_notional_utilization == Decimal("0.100000")
    assert history.latest_largest_single_recommendation_share == Decimal("0.040000")
    assert history.latest_selected_count == 4
    assert history.latest_blocked_count == 1
    assert history.duplicate_generated_at_count == 1


def test_risk_budget_db_history_tracks_latest_and_worst_values() -> None:
    history = _history(
        (
            _report(
                generated_at=BASE_REPORT_AT,
                status="pass",
                reason_codes=("risk_budget_passed",),
                total_notional_utilization=Decimal("0.090000"),
                largest_single_recommendation_share=Decimal("0.030000"),
                selected_count=3,
            ),
            _report(
                generated_at=BASE_REPORT_AT + timedelta(minutes=1),
                status="watch",
                reason_codes=("near_total_utilization_cap",),
                total_notional_utilization=Decimal("0.240000"),
                largest_single_recommendation_share=Decimal("0.080000"),
                selected_count=3,
            ),
            _report(
                generated_at=BASE_REPORT_AT + timedelta(minutes=2),
                status="pass",
                reason_codes=("risk_budget_passed",),
                total_notional_utilization=Decimal("0.100000"),
                largest_single_recommendation_share=Decimal("0.040000"),
                selected_count=3,
            ),
        ),
    )

    assert history.latest_status == "pass"
    assert history.status == "latest_paper_recommendation_risk_budget_passed"
    assert history.latest_total_notional_utilization == Decimal("0.100000")
    assert history.worst_total_notional_utilization == Decimal("0.240000")
    assert history.latest_largest_single_recommendation_share == Decimal("0.040000")
    assert history.worst_largest_single_recommendation_share == Decimal("0.080000")


def test_risk_budget_db_history_ignores_absent_ratio_metrics_for_worst_values() -> None:
    history = _history(
        (
            _report(
                generated_at=BASE_REPORT_AT,
                status="blocked",
                reason_codes=("empty_selection",),
                total_notional_utilization=None,
                largest_single_recommendation_share=None,
                selected_count=0,
                total_suggested_notional=Decimal("0.000000"),
                nav_notional=None,
            ),
            _report(
                generated_at=BASE_REPORT_AT + timedelta(minutes=1),
                status="pass",
                reason_codes=("risk_budget_passed",),
                total_notional_utilization=Decimal("0.010000"),
                largest_single_recommendation_share=Decimal("0.010000"),
            ),
        ),
    )

    assert history.latest_total_notional_utilization == Decimal("0.010000")
    assert history.worst_total_notional_utilization == Decimal("0.010000")
    assert history.latest_largest_single_recommendation_share == Decimal("0.010000")
    assert history.worst_largest_single_recommendation_share == Decimal("0.010000")


def test_risk_budget_db_history_aggregates_reason_codes_sorted_by_code() -> None:
    history = _history(
        (
            _report(
                generated_at=BASE_REPORT_AT,
                status="watch",
                reason_codes=(
                    "near_total_utilization_cap",
                    "near_single_recommendation_share_cap",
                ),
                total_notional_utilization=Decimal("0.240000"),
                largest_single_recommendation_share=Decimal("0.095000"),
                selected_count=3,
            ),
            _report(
                generated_at=BASE_REPORT_AT + timedelta(minutes=1),
                status="blocked",
                reason_codes=("max_selected_count_exceeded",),
                largest_single_recommendation_share=Decimal("0.040000"),
                selected_count=4,
                max_selected_count=3,
            ),
        ),
    )

    assert history.reason_code_counts == (
        ("max_selected_count_exceeded", 1),
        ("near_single_recommendation_share_cap", 1),
        ("near_total_utilization_cap", 1),
    )


@pytest.mark.parametrize(
    ("flag_name", "message"),
    (
        ("paper_only", "paper_only"),
        ("report_only", "report_only"),
        ("readonly", "readonly"),
    ),
)
def test_risk_budget_db_history_rejects_unsafe_source_flags(
    flag_name: str,
    message: str,
) -> None:
    report = replace(_report(generated_at=BASE_REPORT_AT))
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=message):
        _history((report,))


def test_risk_budget_db_history_report_is_frozen() -> None:
    history = _history((_report(generated_at=BASE_REPORT_AT),))

    with pytest.raises(FrozenInstanceError):
        history.readonly = False  # type: ignore[misc]
