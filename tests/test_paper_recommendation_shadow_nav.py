from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_recommendation_shadow_nav import (
    PaperRecommendationShadowNavAllocationRow,
    PaperRecommendationShadowNavConfig,
    PaperRecommendationShadowNavReport,
    build_paper_recommendation_shadow_nav_report,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def _row(
    market_slug: str,
    *,
    side: str = "yes",
    allocated_paper_notional: Decimal = Decimal("25.000000"),
    max_loss_notional: Decimal = Decimal("25.000000"),
    expected_value_notional: Decimal = Decimal("2.000000"),
    reason_codes: tuple[str, ...] = ("selected_by_policy",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperRecommendationShadowNavAllocationRow:
    return PaperRecommendationShadowNavAllocationRow(
        market_slug=market_slug,
        side=side,
        allocated_paper_notional=allocated_paper_notional,
        max_loss_notional=max_loss_notional,
        expected_value_notional=expected_value_notional,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _config(**overrides: object) -> PaperRecommendationShadowNavConfig:
    values = {
        "nav_notional": Decimal("1000.000000"),
        "max_nav_at_risk_ratio": Decimal("0.150000"),
        "max_expected_drawdown_ratio": Decimal("0.020000"),
    }
    values.update(overrides)
    return PaperRecommendationShadowNavConfig(**values)


def _report(
    rows: tuple[object, ...],
    *,
    config: PaperRecommendationShadowNavConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperRecommendationShadowNavReport:
    return build_paper_recommendation_shadow_nav_report(
        rows,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_shadow_nav_passes_when_allocations_fit_nav_caps():
    rows = (
        _row(
            "alpha",
            allocated_paper_notional=Decimal("40.000000"),
            max_loss_notional=Decimal("30.000000"),
            expected_value_notional=Decimal("5.000000"),
        ),
        _row(
            "beta",
            side="no",
            allocated_paper_notional=Decimal("50.000000"),
            max_loss_notional=Decimal("45.000000"),
            expected_value_notional=Decimal("-3.000000"),
            reason_codes=("negative_edge_small",),
        ),
    )

    report = _report(rows)

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.status == "pass"
    assert report.reason_codes == ("shadow_nav_impact_passed",)
    assert report.total_allocated_notional == Decimal("90.000000")
    assert report.total_max_loss_notional == Decimal("75.000000")
    assert report.total_expected_value_notional == Decimal("2.000000")
    assert report.nav_at_risk_ratio == Decimal("0.075000")
    assert report.expected_drawdown_ratio == ZERO
    assert report.row_count == 2
    assert report.nav_notional == Decimal("1000.000000")
    assert report.max_nav_at_risk_ratio == Decimal("0.150000")
    assert report.max_expected_drawdown_ratio == Decimal("0.020000")
    assert report.allocation_rows == rows
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_shadow_nav_watches_near_limits_without_crossing_them():
    rows = (
        _row(
            "alpha",
            allocated_paper_notional=Decimal("140.000000"),
            max_loss_notional=Decimal("143.000000"),
            expected_value_notional=Decimal("-19.000000"),
        ),
    )

    report = _report(rows)

    assert report.status == "watch"
    assert report.reason_codes == (
        "near_nav_at_risk_limit",
        "near_expected_drawdown_limit",
    )
    assert report.total_allocated_notional == Decimal("140.000000")
    assert report.total_max_loss_notional == Decimal("143.000000")
    assert report.total_expected_value_notional == Decimal("-19.000000")
    assert report.nav_at_risk_ratio == Decimal("0.143000")
    assert report.expected_drawdown_ratio == Decimal("0.019000")


def test_shadow_nav_blocks_when_nav_risk_or_expected_drawdown_limits_are_exceeded():
    rows = (
        _row(
            "alpha",
            allocated_paper_notional=Decimal("80.000000"),
            max_loss_notional=Decimal("80.000000"),
            expected_value_notional=Decimal("-12.000000"),
        ),
        _row(
            "beta",
            allocated_paper_notional=Decimal("90.000000"),
            max_loss_notional=Decimal("90.000000"),
            expected_value_notional=Decimal("-11.000000"),
        ),
    )

    report = _report(rows)

    assert report.status == "blocked"
    assert report.reason_codes == (
        "nav_at_risk_limit_exceeded",
        "expected_drawdown_limit_exceeded",
    )
    assert report.total_allocated_notional == Decimal("170.000000")
    assert report.total_max_loss_notional == Decimal("170.000000")
    assert report.total_expected_value_notional == Decimal("-23.000000")
    assert report.nav_at_risk_ratio == Decimal("0.170000")
    assert report.expected_drawdown_ratio == Decimal("0.023000")


def test_shadow_nav_treats_empty_allocation_set_as_zero_impact_pass():
    report = _report(())

    assert report.status == "pass"
    assert report.reason_codes == ("shadow_nav_impact_passed",)
    assert report.total_allocated_notional == ZERO
    assert report.total_max_loss_notional == ZERO
    assert report.total_expected_value_notional == ZERO
    assert report.nav_at_risk_ratio == ZERO
    assert report.expected_drawdown_ratio == ZERO
    assert report.row_count == 0
    assert report.allocation_rows == ()


def test_shadow_nav_accepts_allocation_row_shape_without_exact_type_cycle():
    @dataclass(frozen=True)
    class AllocationShape:
        market_slug: str
        side: str
        allocated_paper_notional: Decimal
        max_loss_notional: Decimal
        expected_value_notional: Decimal
        reason_codes: tuple[str, ...]
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    row = AllocationShape(
        market_slug="shape-row",
        side="yes",
        allocated_paper_notional=Decimal("10.000000"),
        max_loss_notional=Decimal("9.000000"),
        expected_value_notional=Decimal("-1.000000"),
        reason_codes=("shape_input",),
    )

    report = _report((row,))

    assert report.status == "pass"
    assert report.total_allocated_notional == Decimal("10.000000")
    assert report.total_max_loss_notional == Decimal("9.000000")
    assert report.total_expected_value_notional == Decimal("-1.000000")
    assert report.nav_at_risk_ratio == Decimal("0.009000")
    assert report.expected_drawdown_ratio == Decimal("0.001000")
    assert report.allocation_rows == (
        _row(
            "shape-row",
            allocated_paper_notional=Decimal("10.000000"),
            max_loss_notional=Decimal("9.000000"),
            expected_value_notional=Decimal("-1.000000"),
            reason_codes=("shape_input",),
        ),
    )


def test_shadow_nav_validates_hard_safety_flags_on_inputs_and_config():
    with pytest.raises(ValueError, match="paper_only"):
        _row("unsafe-row", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _row("unsafe-row", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _row("unsafe-row", readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        PaperRecommendationShadowNavConfig(
            nav_notional=Decimal("1000.000000"),
            max_nav_at_risk_ratio=Decimal("0.150000"),
            max_expected_drawdown_ratio=Decimal("0.020000"),
            paper_only=False,
        )

    unsafe_row = _row("unsafe-shape")
    object.__setattr__(unsafe_row, "readonly", False)
    with pytest.raises(ValueError, match="allocation rows must be readonly"):
        _report((unsafe_row,))

    unsafe_config = _config()
    object.__setattr__(unsafe_config, "report_only", False)
    with pytest.raises(ValueError, match="config must be report_only"):
        _report((_row("alpha"),), config=unsafe_config)


def test_shadow_nav_decimal_quantization_utc_and_frozen_validations():
    report = _report(
        (_row("alpha"),),
        generated_at=datetime(2026, 6, 19, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    with pytest.raises(FrozenInstanceError):
        report.status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="generated_at"):
        _report((_row("alpha"),), generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        PaperRecommendationShadowNavReport(
            generated_at=_DatetimeSubclass(2026, 6, 19, 12, 0, tzinfo=UTC),
            status="pass",
            reason_codes=("shadow_nav_impact_passed",),
            total_allocated_notional=Decimal("0.000000"),
            total_max_loss_notional=Decimal("0.000000"),
            total_expected_value_notional=Decimal("0.000000"),
            nav_at_risk_ratio=Decimal("0.000000"),
            expected_drawdown_ratio=Decimal("0.000000"),
            row_count=0,
            nav_notional=Decimal("1000.000000"),
            max_nav_at_risk_ratio=Decimal("0.150000"),
            max_expected_drawdown_ratio=Decimal("0.020000"),
            allocation_rows=(),
        )
    with pytest.raises(ValueError, match="nav_notional"):
        _config(nav_notional=_DecimalSubclass("1000.000000"))
    with pytest.raises(ValueError, match="allocated_paper_notional"):
        _row("alpha", allocated_paper_notional=Decimal("10.0000001"))
    with pytest.raises(ValueError, match="expected_value_notional"):
        _row("alpha", expected_value_notional=Decimal("1.0000001"))
    with pytest.raises(ValueError, match="total_allocated_notional"):
        replace(report, total_allocated_notional=Decimal("25.0000001"))
    with pytest.raises(ValueError, match="nav_at_risk_ratio"):
        replace(report, nav_at_risk_ratio=Decimal("0.0250001"))
    with pytest.raises(ValueError, match="reason_codes"):
        _row("alpha", reason_codes=("duplicate", "duplicate"))


def test_shadow_nav_constructor_rejects_inconsistent_report_metrics():
    valid = _report((_row("alpha"),))

    with pytest.raises(ValueError, match="row_count"):
        replace(valid, row_count=2)
    with pytest.raises(ValueError, match="total_allocated_notional"):
        replace(valid, total_allocated_notional=Decimal("30.000000"))
    with pytest.raises(ValueError, match="total_max_loss_notional"):
        replace(valid, total_max_loss_notional=Decimal("30.000000"))
    with pytest.raises(ValueError, match="total_expected_value_notional"):
        replace(valid, total_expected_value_notional=Decimal("3.000000"))
    with pytest.raises(ValueError, match="nav_at_risk_ratio"):
        replace(valid, nav_at_risk_ratio=Decimal("0.030000"))
    with pytest.raises(ValueError, match="expected_drawdown_ratio"):
        replace(valid, expected_drawdown_ratio=Decimal("0.010000"))
    with pytest.raises(ValueError, match="status"):
        replace(valid, status="blocked")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(valid, reason_codes=("nav_at_risk_limit_exceeded",))
