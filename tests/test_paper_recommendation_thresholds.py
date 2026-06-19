from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_recommendation_thresholds import (
    PaperRecommendationThresholdsConfig,
    PaperRecommendationThresholdsInputRow,
    PaperRecommendationThresholdsReport,
    PaperRecommendationThresholdsRow,
    build_paper_recommendation_thresholds_report,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def input_row(
    *,
    market_slug: str = "event-alpha",
    side: str = "yes",
    action: str = "recommend",
    recommendation_score: Decimal = d("0.060000"),
    net_probability_edge: Decimal = d("0.060000"),
    executable_paper_shares: Decimal = d("50.000000"),
    total_cost_per_share: Decimal = d("0.020000"),
    reason_codes: tuple[str, ...] = ("seed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperRecommendationThresholdsInputRow:
    return PaperRecommendationThresholdsInputRow(
        market_slug=market_slug,
        side=side,
        action=action,
        recommendation_score=recommendation_score,
        net_probability_edge=net_probability_edge,
        executable_paper_shares=executable_paper_shares,
        total_cost_per_share=total_cost_per_share,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(
    *,
    min_net_probability_edge: Decimal = d("0.050000"),
    min_recommendation_score: Decimal = d("0.050000"),
    min_executable_paper_shares: Decimal = d("10.000000"),
    max_total_cost_per_share: Decimal = d("0.030000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperRecommendationThresholdsConfig:
    return PaperRecommendationThresholdsConfig(
        config_version="recommendation-thresholds-v0",
        min_net_probability_edge=min_net_probability_edge,
        min_recommendation_score=min_recommendation_score,
        min_executable_paper_shares=min_executable_paper_shares,
        max_total_cost_per_share=max_total_cost_per_share,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    *rows: PaperRecommendationThresholdsInputRow,
    cfg: PaperRecommendationThresholdsConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperRecommendationThresholdsReport:
    return build_paper_recommendation_thresholds_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def field_values(instance):
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_threshold_report_evaluates_pass_watch_and_blocked_rows_without_trades():
    report = build_report(
        input_row(
            market_slug="blocked-reject",
            action="reject",
            recommendation_score=ZERO,
            net_probability_edge=d("-0.010000"),
            executable_paper_shares=ZERO,
            total_cost_per_share=d("0.010000"),
            reason_codes=("source_reject",),
        ),
        input_row(
            market_slug="pass-alpha",
            side="yes",
            action="recommend",
            recommendation_score=d("0.0700004"),
            net_probability_edge=d("0.0600004"),
            executable_paper_shares=d("25.0000004"),
            total_cost_per_share=d("0.0200004"),
            reason_codes=("zeta", "alpha", "alpha"),
        ),
        input_row(
            market_slug="watch-score",
            side="no",
            action="recommend",
            recommendation_score=d("0.040000"),
            net_probability_edge=d("0.060000"),
            executable_paper_shares=d("25.000000"),
            total_cost_per_share=d("0.020000"),
            reason_codes=("source_watch",),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "recommendation-thresholds-v0"
    assert report.input_count == 3
    assert report.row_count == 3
    assert report.pass_count == 1
    assert report.watch_count == 1
    assert report.blocked_count == 1
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [row.market_slug for row in report.rows] == [
        "pass-alpha",
        "watch-score",
        "blocked-reject",
    ]

    passing = report.rows[0]
    assert passing.threshold_status == "pass"
    assert passing.failed_thresholds == ()
    assert passing.recommendation_score == d("0.070000")
    assert passing.net_probability_edge == d("0.060000")
    assert passing.executable_paper_shares == d("25.000000")
    assert passing.total_cost_per_share == d("0.020000")
    assert passing.reason_codes == ("alpha", "zeta")

    watch = report.rows[1]
    assert watch.threshold_status == "watch"
    assert watch.failed_thresholds == ("min_recommendation_score",)
    assert watch.reason_codes == (
        "below_min_recommendation_score",
        "source_watch",
    )

    blocked = report.rows[2]
    assert blocked.threshold_status == "blocked"
    assert blocked.failed_thresholds == (
        "min_net_probability_edge",
        "min_recommendation_score",
        "min_executable_paper_shares",
    )
    assert blocked.reason_codes == (
        "action_reject",
        "below_min_executable_paper_shares",
        "below_min_net_probability_edge",
        "below_min_recommendation_score",
        "source_reject",
    )


def test_threshold_report_records_all_configured_threshold_failures():
    report = build_report(
        input_row(
            market_slug="watch-all-thresholds",
            action="recommend",
            recommendation_score=d("0.010000"),
            net_probability_edge=d("0.020000"),
            executable_paper_shares=d("5.000000"),
            total_cost_per_share=d("0.040000"),
            reason_codes=("candidate",),
        ),
    )

    row = report.rows[0]
    assert row.threshold_status == "watch"
    assert row.failed_thresholds == (
        "min_net_probability_edge",
        "min_recommendation_score",
        "min_executable_paper_shares",
        "max_total_cost_per_share",
    )
    assert row.reason_codes == (
        "above_max_total_cost_per_share",
        "below_min_executable_paper_shares",
        "below_min_net_probability_edge",
        "below_min_recommendation_score",
        "candidate",
    )


def test_threshold_rows_sort_deterministically_by_status_score_edge_depth_cost_and_identity():
    report = build_report(
        input_row(
            market_slug="watch-b",
            side="yes",
            action="watch",
            recommendation_score=d("0.090000"),
            net_probability_edge=d("0.090000"),
            executable_paper_shares=d("50.000000"),
            total_cost_per_share=d("0.010000"),
        ),
        input_row(
            market_slug="pass-low-score",
            action="recommend",
            recommendation_score=d("0.060000"),
            net_probability_edge=d("0.060000"),
            executable_paper_shares=d("50.000000"),
            total_cost_per_share=d("0.010000"),
        ),
        input_row(
            market_slug="pass-high-score",
            action="recommend",
            recommendation_score=d("0.080000"),
            net_probability_edge=d("0.060000"),
            executable_paper_shares=d("50.000000"),
            total_cost_per_share=d("0.010000"),
        ),
        input_row(
            market_slug="blocked-a",
            action="reject",
            recommendation_score=ZERO,
            net_probability_edge=ZERO,
            executable_paper_shares=ZERO,
            total_cost_per_share=d("0.010000"),
        ),
        input_row(
            market_slug="pass-edge-high",
            action="recommend",
            recommendation_score=d("0.080000"),
            net_probability_edge=d("0.070000"),
            executable_paper_shares=d("20.000000"),
            total_cost_per_share=d("0.010000"),
        ),
        input_row(
            market_slug="pass-depth-high",
            action="recommend",
            recommendation_score=d("0.080000"),
            net_probability_edge=d("0.070000"),
            executable_paper_shares=d("40.000000"),
            total_cost_per_share=d("0.010000"),
        ),
    )

    assert [row.market_slug for row in report.rows] == [
        "pass-depth-high",
        "pass-edge-high",
        "pass-high-score",
        "pass-low-score",
        "watch-b",
        "blocked-a",
    ]


def test_threshold_dataclasses_are_frozen_normalize_utc_and_validate_consistency():
    eastern = timezone(timedelta(hours=-4))
    report = build_report(
        input_row(recommendation_score=d("0.0700004")),
        generated_at=datetime(2026, 6, 19, 8, 0, tzinfo=eastern),
    )
    assert report.generated_at == GENERATED_AT

    rebuilt_input = PaperRecommendationThresholdsInputRow(
        **field_values(input_row(recommendation_score=d("0.0700004")))
    )
    rebuilt_config = PaperRecommendationThresholdsConfig(**field_values(config()))
    rebuilt_row = PaperRecommendationThresholdsRow(**field_values(report.rows[0]))
    rebuilt_report = PaperRecommendationThresholdsReport(**field_values(report))
    assert rebuilt_input.recommendation_score == d("0.070000")
    assert rebuilt_config == config()
    assert rebuilt_row == report.rows[0]
    assert rebuilt_report == report

    with pytest.raises(FrozenInstanceError):
        rebuilt_input.side = "no"
    with pytest.raises(FrozenInstanceError):
        rebuilt_config.min_net_probability_edge = d("0.010000")
    with pytest.raises(FrozenInstanceError):
        rebuilt_row.threshold_status = "watch"
    with pytest.raises(FrozenInstanceError):
        rebuilt_report.rows = ()

    with pytest.raises(ValueError, match="failed_thresholds"):
        replace(report.rows[0], failed_thresholds=("min_recommendation_score",))
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=0)


@pytest.mark.parametrize(
    ("field_name", "bad_value", "match"),
    (
        ("recommendation_score", Decimal("-0.000001"), "recommendation_score"),
        ("recommendation_score", Decimal("1.000001"), "recommendation_score"),
        ("net_probability_edge", Decimal("NaN"), "net_probability_edge"),
        ("executable_paper_shares", Decimal("-0.000001"), "executable_paper_shares"),
        ("total_cost_per_share", Decimal("-0.000001"), "total_cost_per_share"),
    ),
)
def test_threshold_input_rejects_invalid_decimal_values(field_name, bad_value, match):
    with pytest.raises(ValueError, match=match):
        replace(input_row(), **{field_name: bad_value})


def test_threshold_config_requires_decimal_thresholds_and_safety_flags():
    with pytest.raises(ValueError, match="min_net_probability_edge"):
        replace(config(), min_net_probability_edge=0.05)
    with pytest.raises(ValueError, match="min_recommendation_score"):
        replace(config(), min_recommendation_score=0.05)
    with pytest.raises(ValueError, match="min_executable_paper_shares"):
        replace(config(), min_executable_paper_shares=10)
    with pytest.raises(ValueError, match="max_total_cost_per_share"):
        replace(config(), max_total_cost_per_share=0.03)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)

    safe_row = input_row()
    unsafe_row = object.__new__(PaperRecommendationThresholdsInputRow)
    for field_name, value in safe_row.__dict__.items():
        object.__setattr__(unsafe_row, field_name, value)
    object.__setattr__(unsafe_row, "paper_only", False)

    with pytest.raises(ValueError, match="paper_only"):
        build_report(unsafe_row)


def test_threshold_builder_rejects_non_exact_public_types_and_bad_iterables():
    with pytest.raises(ValueError, match="config"):
        build_paper_recommendation_thresholds_report(
            (input_row(),),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_recommendation_thresholds_report(
            (input_row(),),
            config=config(),
            generated_at="2026-06-19T12:00:00Z",
        )
    with pytest.raises(ValueError, match="rows"):
        build_paper_recommendation_thresholds_report(
            "not rows",
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="rows"):
        build_paper_recommendation_thresholds_report(
            (object(),),
            config=config(),
            generated_at=GENERATED_AT,
        )
