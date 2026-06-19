from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_outcome_uncertainty import (
    PaperOutcomeUncertaintyConfig,
    PaperOutcomeUncertaintyInput,
    PaperOutcomeUncertaintyReport,
    PaperOutcomeUncertaintyRow,
    build_paper_outcome_uncertainty_report,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def uncertainty_input(
    *,
    market_slug: str = "event-alpha",
    question: str = "Will alpha resolve yes?",
    side: str = "yes",
    action: str = "recommend",
    net_probability_edge: Decimal = d("0.080000"),
    ambiguity_score: Decimal = ZERO,
    has_clear_resolution_source: bool = True,
    reason_codes: tuple[str, ...] = ("edge_seed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperOutcomeUncertaintyInput:
    return PaperOutcomeUncertaintyInput(
        market_slug=market_slug,
        question=question,
        side=side,
        action=action,
        net_probability_edge=net_probability_edge,
        ambiguity_score=ambiguity_score,
        has_clear_resolution_source=has_clear_resolution_source,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(
    *,
    max_ambiguity_score: Decimal = d("0.700000"),
    ambiguity_penalty_multiplier: Decimal = d("0.100000"),
    missing_source_penalty_per_share: Decimal = d("0.020000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperOutcomeUncertaintyConfig:
    return PaperOutcomeUncertaintyConfig(
        config_version="outcome-uncertainty-v0",
        max_ambiguity_score=max_ambiguity_score,
        ambiguity_penalty_multiplier=ambiguity_penalty_multiplier,
        missing_source_penalty_per_share=missing_source_penalty_per_share,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*inputs: PaperOutcomeUncertaintyInput) -> PaperOutcomeUncertaintyReport:
    return build_paper_outcome_uncertainty_report(
        inputs,
        config=config(),
        generated_at=GENERATED_AT,
    )


def field_values(instance):
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_clear_sourced_outcome_definition_preserves_edge_without_cost():
    report = build_report(uncertainty_input())

    row = report.rows[0]
    assert row.market_slug == "event-alpha"
    assert row.question == "Will alpha resolve yes?"
    assert row.side == "yes"
    assert row.action == "recommend"
    assert row.net_probability_edge == d("0.080000")
    assert row.ambiguity_score == ZERO
    assert row.has_clear_resolution_source is True
    assert row.uncertainty_status == "clear"
    assert row.uncertainty_cost_per_share == ZERO
    assert row.adjusted_net_probability_edge == d("0.080000")
    assert row.reason_codes == ("edge_seed", "outcome_definition_clear")

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.input_count == 1
    assert report.row_count == 1
    assert report.clear_count == 1
    assert report.watch_count == 0
    assert report.blocked_count == 0


def test_ambiguous_outcome_definition_adds_decimal_penalty_and_watches():
    report = build_report(
        uncertainty_input(
            market_slug="ambiguous-market",
            net_probability_edge=d("0.080000"),
            ambiguity_score=d("0.300000"),
        ),
    )

    row = report.rows[0]
    assert row.uncertainty_status == "watch"
    assert row.uncertainty_cost_per_share == d("0.030000")
    assert row.adjusted_net_probability_edge == d("0.050000")
    assert row.reason_codes == ("ambiguous_outcome_definition", "edge_seed")


def test_missing_clear_resolution_source_adds_fixed_penalty_and_watches():
    report = build_report(
        uncertainty_input(
            market_slug="missing-source",
            net_probability_edge=d("0.080000"),
            ambiguity_score=d("0.100000"),
            has_clear_resolution_source=False,
        ),
    )

    row = report.rows[0]
    assert row.uncertainty_status == "watch"
    assert row.uncertainty_cost_per_share == d("0.030000")
    assert row.adjusted_net_probability_edge == d("0.050000")
    assert row.reason_codes == (
        "ambiguous_outcome_definition",
        "edge_seed",
        "missing_clear_resolution_source",
    )


def test_ambiguity_above_configured_cap_blocks_even_when_edge_remains_positive():
    report = build_paper_outcome_uncertainty_report(
        [
            uncertainty_input(
                market_slug="too-ambiguous",
                net_probability_edge=d("0.200000"),
                ambiguity_score=d("0.800000"),
            )
        ],
        config=config(max_ambiguity_score=d("0.700000")),
        generated_at=GENERATED_AT,
    )

    row = report.rows[0]
    assert row.uncertainty_status == "blocked"
    assert row.uncertainty_cost_per_share == d("0.080000")
    assert row.adjusted_net_probability_edge == d("0.120000")
    assert row.reason_codes == (
        "ambiguity_score_above_max",
        "ambiguous_outcome_definition",
        "edge_seed",
    )
    assert report.blocked_count == 1


def test_rows_sort_by_status_adjusted_edge_cost_and_identity():
    report = build_report(
        uncertainty_input(
            market_slug="watch-low",
            net_probability_edge=d("0.060000"),
            ambiguity_score=d("0.200000"),
        ),
        uncertainty_input(
            market_slug="clear-high",
            net_probability_edge=d("0.070000"),
            ambiguity_score=ZERO,
        ),
        uncertainty_input(
            market_slug="blocked-high",
            net_probability_edge=d("0.200000"),
            ambiguity_score=d("0.800000"),
        ),
        uncertainty_input(
            market_slug="watch-high",
            net_probability_edge=d("0.080000"),
            ambiguity_score=d("0.100000"),
        ),
        uncertainty_input(
            market_slug="clear-low",
            net_probability_edge=d("0.030000"),
            ambiguity_score=ZERO,
        ),
    )

    assert [row.market_slug for row in report.rows] == [
        "clear-high",
        "clear-low",
        "watch-high",
        "watch-low",
        "blocked-high",
    ]
    assert report.clear_count == 2
    assert report.watch_count == 2
    assert report.blocked_count == 1


def test_constructors_validate_consistency_utc_and_hard_safety_flags():
    eastern = timezone(timedelta(hours=-4))
    report = build_paper_outcome_uncertainty_report(
        [uncertainty_input()],
        config=config(),
        generated_at=datetime(2026, 6, 19, 8, 0, tzinfo=eastern),
    )
    assert report.generated_at == GENERATED_AT

    rebuilt_row = PaperOutcomeUncertaintyRow(**field_values(report.rows[0]))
    assert rebuilt_row == report.rows[0]

    with pytest.raises(ValueError, match="adjusted_net_probability_edge"):
        replace(report.rows[0], adjusted_net_probability_edge=d("0.010000"))
    with pytest.raises(ValueError, match="uncertainty_cost_per_share"):
        replace(report.rows[0], uncertainty_cost_per_share=d("0.000001"))
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=2)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(uncertainty_input(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)


def test_dataclasses_are_frozen():
    input_row = uncertainty_input()
    cfg = config()
    report = build_report(input_row)
    row = report.rows[0]

    with pytest.raises(FrozenInstanceError):
        input_row.action = "watch"
    with pytest.raises(FrozenInstanceError):
        cfg.max_ambiguity_score = d("0.500000")
    with pytest.raises(FrozenInstanceError):
        row.uncertainty_status = "blocked"
    with pytest.raises(FrozenInstanceError):
        report.rows = ()


@pytest.mark.parametrize(
    ("field_name", "bad_value", "match"),
    (
        ("ambiguity_score", Decimal("-0.000001"), "ambiguity_score"),
        ("ambiguity_score", Decimal("1.000001"), "ambiguity_score"),
        ("ambiguity_score", Decimal("NaN"), "ambiguity_score"),
        ("net_probability_edge", Decimal("NaN"), "net_probability_edge"),
    ),
)
def test_input_constructor_rejects_invalid_decimal_values(field_name, bad_value, match):
    with pytest.raises(ValueError, match=match):
        replace(uncertainty_input(), **{field_name: bad_value})


def test_config_constructor_rejects_invalid_decimal_values():
    with pytest.raises(ValueError, match="max_ambiguity_score"):
        config(max_ambiguity_score=d("-0.000001"))
    with pytest.raises(ValueError, match="max_ambiguity_score"):
        config(max_ambiguity_score=d("1.000001"))
    with pytest.raises(ValueError, match="ambiguity_penalty_multiplier"):
        config(ambiguity_penalty_multiplier=d("-0.000001"))
    with pytest.raises(ValueError, match="missing_source_penalty_per_share"):
        config(missing_source_penalty_per_share=d("-0.000001"))


def test_decimal_only_public_values_reject_float_int_and_subclass_values():
    with pytest.raises(ValueError, match="net_probability_edge"):
        replace(uncertainty_input(), net_probability_edge=0.08)
    with pytest.raises(ValueError, match="ambiguity_score"):
        replace(uncertainty_input(), ambiguity_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="max_ambiguity_score"):
        PaperOutcomeUncertaintyConfig(
            config_version="outcome-uncertainty-v0",
            max_ambiguity_score=1,
            ambiguity_penalty_multiplier=d("0.100000"),
            missing_source_penalty_per_share=d("0.020000"),
        )
    with pytest.raises(ValueError, match="uncertainty_cost_per_share"):
        PaperOutcomeUncertaintyRow(
            market_slug="float-row",
            question="Float row?",
            side="yes",
            action="recommend",
            net_probability_edge=d("0.080000"),
            ambiguity_score=d("0.300000"),
            has_clear_resolution_source=True,
            uncertainty_status="watch",
            uncertainty_cost_per_share=0.03,
            adjusted_net_probability_edge=d("0.050000"),
            reason_codes=("ambiguous_outcome_definition",),
        )


def test_decimal_fields_quantize_to_six_places():
    report = build_paper_outcome_uncertainty_report(
        [
            uncertainty_input(
                net_probability_edge=d("0.1234567"),
                ambiguity_score=d("0.3333333"),
            )
        ],
        config=config(ambiguity_penalty_multiplier=d("0.1000004")),
        generated_at=GENERATED_AT,
    )

    row = report.rows[0]
    assert row.net_probability_edge == d("0.123457")
    assert row.ambiguity_score == d("0.333333")
    assert row.uncertainty_cost_per_share == d("0.033333")
    assert row.adjusted_net_probability_edge == d("0.090124")


def test_builder_rejects_non_exact_public_types_and_non_utc_datetime_type():
    with pytest.raises(ValueError, match="config"):
        build_paper_outcome_uncertainty_report(
            [uncertainty_input()],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_outcome_uncertainty_report(
            [uncertainty_input()],
            config=config(),
            generated_at="2026-06-19T12:00:00Z",
        )
    with pytest.raises(ValueError, match="inputs"):
        build_paper_outcome_uncertainty_report(
            [object()],
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        PaperOutcomeUncertaintyReport(
            generated_at=_DatetimeSubclass(2026, 6, 19, 12, 0, tzinfo=UTC),
            config_version="outcome-uncertainty-v0",
            input_count=0,
            row_count=0,
            clear_count=0,
            watch_count=0,
            blocked_count=0,
            rows=(),
        )
