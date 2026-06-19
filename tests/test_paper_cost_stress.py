from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_cost_stress import (
    PaperCostStressConfig,
    PaperCostStressInput,
    PaperCostStressReport,
    PaperCostStressScenarioRow,
    build_paper_cost_stress_report,
)


GENERATED_AT = datetime(2026, 6, 19, 14, 30, tzinfo=UTC)
CONFIG_VERSION = "paper-cost-stress-v0"


def d(value: str) -> Decimal:
    return Decimal(value)


def stress_input(
    *,
    market_slug: str = "event-alpha",
    side: str = "yes",
    action: str = "recommend",
    net_probability_edge: Decimal = d("0.0300004"),
    total_cost_per_share: Decimal = d("0.0120004"),
    recommendation_score: Decimal = d("0.0300004"),
    reason_codes: tuple[str, ...] = ("seed_edge",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperCostStressInput:
    return PaperCostStressInput(
        market_slug=market_slug,
        side=side,
        action=action,
        net_probability_edge=net_probability_edge,
        total_cost_per_share=total_cost_per_share,
        recommendation_score=recommendation_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(
    *,
    scenarios: tuple[tuple[str, Decimal], ...] = (
        ("base", d("0.000000")),
        ("small", d("0.010000")),
    ),
) -> PaperCostStressConfig:
    return PaperCostStressConfig(
        config_version=CONFIG_VERSION,
        cost_shock_per_share_scenarios=scenarios,
    )


def build_report(
    *inputs: PaperCostStressInput,
    cfg: PaperCostStressConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperCostStressReport:
    return build_paper_cost_stress_report(
        inputs,
        config=cfg or config(),
        generated_at=generated_at,
    )


def field_values(instance):
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_cost_stress_marks_recommendation_survival_under_extra_cost_shocks():
    report = build_report(
        stress_input(
            market_slug="event-alpha",
            side="yes",
            action="recommend",
            net_probability_edge=d("0.0300004"),
            total_cost_per_share=d("0.0120004"),
            recommendation_score=d("0.0300004"),
        ),
        cfg=config(
            scenarios=(
                ("base", d("0.000000")),
                ("heavy", d("0.0400004")),
            ),
        ),
    )

    assert isinstance(report, PaperCostStressReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.input_count == 1
    assert report.scenario_count == 2
    assert report.row_count == 2
    assert report.pass_count == 1
    assert report.watch_count == 0
    assert report.fail_count == 1
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert [
        (
            row.market_slug,
            row.side,
            row.action,
            row.scenario_name,
            row.net_probability_edge,
            row.cost_shock_per_share,
            row.total_cost_per_share,
            row.recommendation_score,
            row.stressed_net_probability_edge,
            row.survival_status,
            row.reason_codes,
            row.paper_only,
            row.report_only,
            row.readonly,
        )
        for row in report.rows
    ] == [
        (
            "event-alpha",
            "yes",
            "recommend",
            "base",
            d("0.030000"),
            d("0.000000"),
            d("0.012000"),
            d("0.030000"),
            d("0.030000"),
            "pass",
            ("seed_edge", "cost_stress_pass"),
            True,
            True,
            True,
        ),
        (
            "event-alpha",
            "yes",
            "recommend",
            "heavy",
            d("0.030000"),
            d("0.040000"),
            d("0.012000"),
            d("0.030000"),
            d("-0.010000"),
            "fail",
            ("seed_edge", "nonpositive_stressed_net_probability_edge"),
            True,
            True,
            True,
        ),
    ]


def test_cost_stress_marks_source_watch_rows_as_watch_when_edge_remains_positive():
    report = build_report(
        stress_input(
            market_slug="event-watch",
            side="no",
            action="watch",
            net_probability_edge=d("0.012000"),
            recommendation_score=d("0.012000"),
            reason_codes=("market_context_stale",),
        ),
        cfg=config(scenarios=(("small", d("0.002000")),)),
    )

    assert report.pass_count == 0
    assert report.watch_count == 1
    assert report.fail_count == 0
    assert report.rows[0].stressed_net_probability_edge == d("0.010000")
    assert report.rows[0].survival_status == "watch"
    assert report.rows[0].reason_codes == (
        "market_context_stale",
        "source_action_not_recommend",
    )


def test_cost_stress_orders_rows_by_market_side_and_scenario_order():
    report = build_report(
        stress_input(market_slug="market-b", side="yes"),
        stress_input(market_slug="market-a", side="yes"),
        stress_input(market_slug="market-a", side="no"),
        cfg=config(
            scenarios=(
                ("medium", d("0.010000")),
                ("base", d("0.000000")),
            ),
        ),
    )

    assert [
        (row.market_slug, row.side, row.scenario_name)
        for row in report.rows
    ] == [
        ("market-a", "no", "medium"),
        ("market-a", "no", "base"),
        ("market-a", "yes", "medium"),
        ("market-a", "yes", "base"),
        ("market-b", "yes", "medium"),
        ("market-b", "yes", "base"),
    ]


def test_cost_stress_config_validates_canonical_unique_nonnegative_scenarios():
    cfg = config(
        scenarios=(
            ("base", d("0.0000004")),
            ("heavy", d("0.0250004")),
        ),
    )

    assert cfg.cost_shock_per_share_scenarios == (
        ("base", d("0.000000")),
        ("heavy", d("0.025000")),
    )

    bad_values = [
        [],
        (),
        (("base", d("0.000000")), ("base", d("0.010000"))),
        ((" base", d("0.000000")),),
        (("", d("0.000000")),),
        (("base", d("-0.000001")),),
        (("base", d("NaN")),),
        (("base", 0),),
        (("base", 0.0),),
        (("base", True),),
        ((1, d("0.000000")),),
        ("base", d("0.000000")),
    ]
    for value in bad_values:
        with pytest.raises(ValueError, match="cost_shock_per_share_scenarios"):
            PaperCostStressConfig(
                config_version=CONFIG_VERSION,
                cost_shock_per_share_scenarios=value,
            )


def test_cost_stress_normalizes_generated_at_to_utc_and_dataclasses_are_frozen():
    report = build_report(
        stress_input(),
        generated_at=datetime(
            2026,
            6,
            19,
            10,
            30,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert report.generated_at == GENERATED_AT

    with pytest.raises(FrozenInstanceError):
        report.rows = ()
    with pytest.raises(FrozenInstanceError):
        report.rows[0].survival_status = "fail"


def test_cost_stress_rejects_non_decimal_scalars_and_non_exact_public_types():
    class ConfigSubclass(PaperCostStressConfig):
        pass

    class InputSubclass(PaperCostStressInput):
        pass

    class DateTimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="net_probability_edge"):
        replace(stress_input(), net_probability_edge=0.03)
    with pytest.raises(ValueError, match="total_cost_per_share"):
        replace(stress_input(), total_cost_per_share=0)
    with pytest.raises(ValueError, match="recommendation_score"):
        replace(stress_input(), recommendation_score=True)
    with pytest.raises(ValueError, match="config"):
        build_paper_cost_stress_report(
            [stress_input()],
            config=ConfigSubclass(
                config_version=CONFIG_VERSION,
                cost_shock_per_share_scenarios=(("base", d("0.000000")),),
            ),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="inputs"):
        build_paper_cost_stress_report(
            [InputSubclass(**field_values(stress_input()))],
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_cost_stress_report(
            [stress_input()],
            config=config(),
            generated_at=DateTimeSubclass(2026, 6, 19, 14, 30, tzinfo=UTC),
        )


def test_cost_stress_validates_consistency_and_hard_safety_flags():
    report = build_report(stress_input())
    row = report.rows[0]

    rebuilt_row = PaperCostStressScenarioRow(**field_values(row))
    assert rebuilt_row == row

    with pytest.raises(ValueError, match="stressed_net_probability_edge"):
        replace(row, stressed_net_probability_edge=d("0.000001"))
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=99)
    with pytest.raises(ValueError, match="paper_only"):
        replace(stress_input(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
