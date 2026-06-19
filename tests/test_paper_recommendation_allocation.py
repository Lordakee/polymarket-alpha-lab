from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_recommendation_allocation import (
    PaperRecommendationAllocationConfig,
    PaperRecommendationAllocationInput,
    PaperRecommendationAllocationReport,
    build_paper_recommendation_allocation_report,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


@dataclass(frozen=True)
class SideEdgeShape:
    market_slug: str = "shape-market"
    side: str = "yes"
    action: str = "recommend"
    net_probability_edge: Decimal = Decimal("0.200000")
    executable_paper_shares: Decimal = Decimal("3.000000")
    market_implied_probability: Decimal = Decimal("0.3333333")
    event_id: str | None = None
    theme_id: str | None = None
    correlation_group: str | None = None
    reason_codes: tuple[str, ...] = ("shape",)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _config(**overrides: object) -> PaperRecommendationAllocationConfig:
    values = {
        "config_version": "allocation-v0",
        "total_paper_budget": Decimal("1000.000000"),
        "max_paper_notional_per_market": Decimal("500.000000"),
        "max_paper_notional_per_event": Decimal("500.000000"),
        "max_paper_notional_per_theme": Decimal("500.000000"),
        "max_paper_notional_per_correlation_group": Decimal("500.000000"),
    }
    values.update(overrides)
    return PaperRecommendationAllocationConfig(**values)


def _input_row(
    market_slug: str = "alpha",
    *,
    side: str = "yes",
    action: str = "recommend",
    recommendation_score: Decimal | None = Decimal("0.100000"),
    net_probability_edge: Decimal | None = Decimal("0.100000"),
    executable_paper_shares: Decimal = Decimal("100.000000"),
    side_price: Decimal = Decimal("0.500000"),
    event_id: str | None = "event-alpha",
    theme_id: str | None = "theme-alpha",
    correlation_group: str | None = "corr-alpha",
    reason_codes: tuple[str, ...] = ("seed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperRecommendationAllocationInput:
    return PaperRecommendationAllocationInput(
        market_slug=market_slug,
        side=side,
        action=action,
        recommendation_score=recommendation_score,
        net_probability_edge=net_probability_edge,
        executable_paper_shares=executable_paper_shares,
        side_price=side_price,
        event_id=event_id,
        theme_id=theme_id,
        correlation_group=correlation_group,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    *rows: object,
    config: PaperRecommendationAllocationConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperRecommendationAllocationReport:
    return build_paper_recommendation_allocation_report(
        rows,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_allocates_recommendations_by_score_under_budget_and_caps():
    report = _report(
        _input_row(
            "beta",
            recommendation_score=Decimal("0.100000"),
            executable_paper_shares=Decimal("100.000000"),
            side_price=Decimal("0.400000"),
        ),
        _input_row(
            "alpha",
            recommendation_score=Decimal("0.200000"),
            executable_paper_shares=Decimal("60.000000"),
            side_price=Decimal("0.500000"),
        ),
        config=_config(total_paper_budget=Decimal("100.000000")),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "allocation-v0"
    assert [row.market_slug for row in report.rows] == ["alpha", "beta"]
    assert report.total_requested_paper_notional == Decimal("70.000000")
    assert report.total_allocated_paper_notional == Decimal("70.000000")
    assert report.remaining_paper_budget == Decimal("30.000000")
    assert report.allocated_count == 2
    assert report.capped_count == 0
    assert report.no_budget_count == 0
    assert report.skipped_count == 0

    alpha, beta = report.rows
    assert alpha.requested_paper_notional == Decimal("30.000000")
    assert alpha.allocated_paper_notional == Decimal("30.000000")
    assert alpha.allocated_paper_shares == Decimal("60.000000")
    assert alpha.cap_status == "allocated"
    assert alpha.reason_codes == ("seed",)

    assert beta.requested_paper_notional == Decimal("40.000000")
    assert beta.allocated_paper_notional == Decimal("40.000000")
    assert beta.allocated_paper_shares == Decimal("100.000000")
    assert beta.cap_status == "allocated"


def test_caps_reduce_allocations_at_market_event_theme_correlation_and_total_levels():
    report = _report(
        _input_row(
            "market-capped",
            recommendation_score=Decimal("0.600000"),
            executable_paper_shares=Decimal("100.000000"),
            side_price=Decimal("1.000000"),
            event_id="event-one",
            theme_id="theme-one",
            correlation_group="corr-one",
        ),
        _input_row(
            "event-capped",
            recommendation_score=Decimal("0.500000"),
            executable_paper_shares=Decimal("100.000000"),
            side_price=Decimal("1.000000"),
            event_id="event-one",
            theme_id="theme-two",
            correlation_group="corr-two",
        ),
        _input_row(
            "theme-capped",
            recommendation_score=Decimal("0.400000"),
            executable_paper_shares=Decimal("100.000000"),
            side_price=Decimal("1.000000"),
            event_id="event-two",
            theme_id="theme-one",
            correlation_group="corr-three",
        ),
        _input_row(
            "correlation-capped",
            recommendation_score=Decimal("0.300000"),
            executable_paper_shares=Decimal("100.000000"),
            side_price=Decimal("1.000000"),
            event_id="event-three",
            theme_id="theme-three",
            correlation_group="corr-one",
        ),
        _input_row(
            "total-capped",
            recommendation_score=Decimal("0.200000"),
            executable_paper_shares=Decimal("100.000000"),
            side_price=Decimal("1.000000"),
            event_id="event-four",
            theme_id="theme-four",
            correlation_group="corr-four",
        ),
        _input_row(
            "budget-exhausted",
            recommendation_score=Decimal("0.100000"),
            executable_paper_shares=Decimal("100.000000"),
            side_price=Decimal("1.000000"),
            event_id="event-five",
            theme_id="theme-five",
            correlation_group="corr-five",
        ),
        config=_config(
            total_paper_budget=Decimal("120.000000"),
            max_paper_notional_per_market=Decimal("50.000000"),
            max_paper_notional_per_event=Decimal("60.000000"),
            max_paper_notional_per_theme=Decimal("70.000000"),
            max_paper_notional_per_correlation_group=Decimal("80.000000"),
        ),
    )

    by_slug = {row.market_slug: row for row in report.rows}
    assert [row.market_slug for row in report.rows] == [
        "market-capped",
        "event-capped",
        "theme-capped",
        "correlation-capped",
        "total-capped",
        "budget-exhausted",
    ]
    assert report.total_allocated_paper_notional == Decimal("120.000000")
    assert report.remaining_paper_budget == ZERO
    assert report.capped_count == 5
    assert report.no_budget_count == 1

    assert by_slug["market-capped"].allocated_paper_notional == Decimal("50.000000")
    assert by_slug["event-capped"].allocated_paper_notional == Decimal("10.000000")
    assert by_slug["theme-capped"].allocated_paper_notional == Decimal("20.000000")
    assert by_slug["correlation-capped"].allocated_paper_notional == Decimal("30.000000")
    assert by_slug["total-capped"].allocated_paper_notional == Decimal("10.000000")
    assert by_slug["budget-exhausted"].allocated_paper_notional == ZERO

    assert "market_cap" in by_slug["market-capped"].reason_codes
    assert "event_cap" in by_slug["event-capped"].reason_codes
    assert "theme_cap" in by_slug["theme-capped"].reason_codes
    assert "correlation_cap" in by_slug["correlation-capped"].reason_codes
    assert "total_budget_cap" in by_slug["total-capped"].reason_codes
    assert "no_budget" in by_slug["budget-exhausted"].reason_codes
    assert {by_slug[name].cap_status for name in by_slug if name != "budget-exhausted"} == {
        "capped"
    }
    assert by_slug["budget-exhausted"].cap_status == "no_budget"


def test_skips_non_recommend_and_nonpositive_candidate_values_without_allocation():
    report = _report(
        _input_row("watch", action="watch", recommendation_score=Decimal("0.900000")),
        _input_row("zero-edge", recommendation_score=ZERO, net_probability_edge=ZERO),
        _input_row(
            "negative-edge",
            recommendation_score=None,
            net_probability_edge=Decimal("-0.010000"),
        ),
        _input_row("zero-shares", executable_paper_shares=ZERO),
        _input_row("zero-price", side_price=ZERO),
        _input_row(
            "fallback-edge",
            recommendation_score=None,
            net_probability_edge=Decimal("0.200000"),
            executable_paper_shares=Decimal("10.000000"),
            side_price=Decimal("1.000000"),
            event_id="event-fallback",
            theme_id="theme-fallback",
            correlation_group="corr-fallback",
        ),
        config=_config(total_paper_budget=Decimal("20.000000")),
    )

    by_slug = {row.market_slug: row for row in report.rows}
    assert report.total_allocated_paper_notional == Decimal("10.000000")
    assert by_slug["fallback-edge"].cap_status == "allocated"
    assert by_slug["fallback-edge"].allocated_paper_notional == Decimal("10.000000")
    assert by_slug["watch"].cap_status == "non_recommend"
    assert by_slug["watch"].allocated_paper_notional == ZERO
    assert "non_recommend" in by_slug["watch"].reason_codes

    for slug in ("zero-edge", "negative-edge", "zero-shares", "zero-price"):
        assert by_slug[slug].cap_status == "skipped"
        assert by_slug[slug].allocated_paper_notional == ZERO
        assert by_slug[slug].allocated_paper_shares == ZERO
        assert "skipped" in by_slug[slug].reason_codes


def test_cap_reason_codes_match_optional_scope_ids_when_some_scopes_are_absent():
    report = _report(
        _input_row(
            "theme-first",
            recommendation_score=Decimal("0.200000"),
            executable_paper_shares=Decimal("100.000000"),
            side_price=Decimal("1.000000"),
            event_id=None,
            theme_id="theme-sparse",
            correlation_group=None,
        ),
        _input_row(
            "theme-second",
            recommendation_score=Decimal("0.100000"),
            executable_paper_shares=Decimal("100.000000"),
            side_price=Decimal("1.000000"),
            event_id=None,
            theme_id="theme-sparse",
            correlation_group=None,
        ),
        config=_config(
            total_paper_budget=Decimal("500.000000"),
            max_paper_notional_per_theme=Decimal("120.000000"),
        ),
    )

    capped = next(row for row in report.rows if row.market_slug == "theme-second")
    assert capped.allocated_paper_notional == Decimal("20.000000")
    assert "theme_cap" in capped.reason_codes
    assert "event_cap" not in capped.reason_codes


def test_accepts_frozen_row_like_inputs_and_market_implied_probability_fallback():
    report = _report(
        SideEdgeShape(),
        generated_at=datetime(2026, 6, 19, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    row = report.rows[0]
    assert report.generated_at == GENERATED_AT
    assert row.market_slug == "shape-market"
    assert row.recommendation_score is None
    assert row.net_probability_edge == Decimal("0.200000")
    assert row.market_implied_probability == Decimal("0.333333")
    assert row.requested_paper_notional == Decimal("0.999999")
    assert row.allocated_paper_notional == Decimal("0.999999")
    assert row.allocated_paper_shares == Decimal("3.000000")
    assert row.event_id is None
    assert row.theme_id is None
    assert row.correlation_group is None
    assert row.reason_codes == ("shape",)


def test_decimal_only_micro_quantization_and_frozen_dataclasses():
    input_row = _input_row(
        executable_paper_shares=Decimal("3.0000004"),
        side_price=Decimal("0.3333333"),
    )
    cfg = _config(total_paper_budget=Decimal("1.2345678"))
    report = _report(input_row, config=cfg)
    row = report.rows[0]

    assert cfg.total_paper_budget == Decimal("1.234568")
    assert input_row.executable_paper_shares == Decimal("3.000000")
    assert input_row.side_price == Decimal("0.333333")
    assert row.requested_paper_notional == Decimal("0.999999")
    assert row.allocated_paper_notional == Decimal("0.999999")

    with pytest.raises(FrozenInstanceError):
        input_row.side = "no"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        cfg.total_paper_budget = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.cap_status = "skipped"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    with pytest.raises(ValueError, match="side_price"):
        _input_row(side_price=Decimal("NaN"))
    with pytest.raises(ValueError, match="recommendation_score"):
        _input_row(recommendation_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="total_paper_budget"):
        _config(total_paper_budget=1)  # type: ignore[arg-type]


def test_rejects_unsafe_inputs_config_and_mutable_row_like_inputs():
    @dataclass
    class MutableShape:
        market_slug: str = "mutable"
        side: str = "yes"
        action: str = "recommend"
        recommendation_score: Decimal = Decimal("0.100000")
        executable_paper_shares: Decimal = Decimal("1.000000")
        side_price: Decimal = Decimal("1.000000")
        reason_codes: tuple[str, ...] = ()
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    with pytest.raises(ValueError, match="paper_only"):
        _config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _config(readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        _report(_input_row(paper_only=False))
    with pytest.raises(ValueError, match="report_only"):
        _report(_input_row(report_only=False))
    with pytest.raises(ValueError, match="readonly"):
        _report(_input_row(readonly=False))
    with pytest.raises(ValueError, match="immutable"):
        _report(MutableShape())
    with pytest.raises(ValueError, match="generated_at"):
        _report(_input_row(), generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="event_id"):
        _input_row(event_id=" event")
    with pytest.raises(ValueError, match="edge"):
        _input_row(recommendation_score=None, net_probability_edge=None)


def test_report_and_row_constructors_reject_inconsistent_values():
    report = _report(_input_row())
    row = report.rows[0]

    with pytest.raises(ValueError, match="allocated_paper_notional"):
        replace(row, allocated_paper_notional=Decimal("0.000001"))
    with pytest.raises(ValueError, match="allocated_paper_shares"):
        replace(row, allocated_paper_shares=Decimal("0.000001"))
    with pytest.raises(ValueError, match="cap_status"):
        replace(row, cap_status="capped")
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=99)
    with pytest.raises(ValueError, match="total_allocated_paper_notional"):
        replace(report, total_allocated_paper_notional=ZERO)
    with pytest.raises(ValueError, match="remaining_paper_budget"):
        replace(report, remaining_paper_budget=Decimal("999.000000"))
