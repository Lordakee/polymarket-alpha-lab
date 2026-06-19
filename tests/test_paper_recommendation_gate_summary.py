from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_recommendation_gate_summary import (
    GateReasonCodeCount,
    PaperRecommendationGateInputRow,
    PaperRecommendationGateSummaryReport,
    PaperRecommendationGateSummaryRow,
    build_paper_recommendation_gate_summary_report,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


@dataclass(frozen=True)
class InputGateShape:
    market_slug: str
    side: str
    gate_name: str
    gate_status: str
    gate_cost_per_share: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _gate_row(
    market_slug: str,
    *,
    side: str = "yes",
    gate_name: str = "risk_budget",
    gate_status: str = "pass",
    gate_cost_per_share: Decimal = Decimal("0.010000"),
    reason_codes: tuple[str, ...] = ("risk_budget_passed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperRecommendationGateInputRow:
    return PaperRecommendationGateInputRow(
        market_slug=market_slug,
        side=side,
        gate_name=gate_name,
        gate_status=gate_status,
        gate_cost_per_share=gate_cost_per_share,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    rows: tuple[object, ...],
    *,
    generated_at: datetime = GENERATED_AT,
) -> PaperRecommendationGateSummaryReport:
    return build_paper_recommendation_gate_summary_report(
        rows,
        generated_at=generated_at,
    )


def test_gate_summary_groups_rows_by_gate_name_with_status_counts_costs_and_reasons():
    report = _report(
        (
            _gate_row(
                "market-beta",
                gate_name="liquidity",
                gate_status="watch",
                gate_cost_per_share=Decimal("0.020000"),
                reason_codes=("wide_spread", "thin_book"),
            ),
            _gate_row(
                "market-alpha",
                side="no",
                gate_name="risk_budget",
                gate_status="blocked",
                gate_cost_per_share=Decimal("0.050000"),
                reason_codes=("cap_exceeded",),
            ),
            _gate_row(
                "market-gamma",
                gate_name="liquidity",
                gate_status="pass",
                gate_cost_per_share=Decimal("0.010000"),
                reason_codes=("liquidity_passed",),
            ),
            _gate_row(
                "market-delta",
                gate_name="risk_budget",
                gate_status="watch",
                gate_cost_per_share=Decimal("0.015000"),
                reason_codes=("cap_exceeded", "near_limit"),
            ),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.gate_input_count == 4
    assert report.gate_name_count == 2
    assert report.pass_count == 1
    assert report.watch_count == 2
    assert report.blocked_count == 1
    assert report.total_gate_cost_per_share == Decimal("0.095000")
    assert report.primary_status == "blocked"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.rows == (
        PaperRecommendationGateSummaryRow(
            gate_name="risk_budget",
            gate_input_count=2,
            pass_count=0,
            watch_count=1,
            blocked_count=1,
            total_gate_cost_per_share=Decimal("0.065000"),
            primary_status="blocked",
            reason_code_counts=(
                GateReasonCodeCount(reason_code="cap_exceeded", count=2),
                GateReasonCodeCount(reason_code="near_limit", count=1),
            ),
        ),
        PaperRecommendationGateSummaryRow(
            gate_name="liquidity",
            gate_input_count=2,
            pass_count=1,
            watch_count=1,
            blocked_count=0,
            total_gate_cost_per_share=Decimal("0.030000"),
            primary_status="watch",
            reason_code_counts=(
                GateReasonCodeCount(reason_code="liquidity_passed", count=1),
                GateReasonCodeCount(reason_code="thin_book", count=1),
                GateReasonCodeCount(reason_code="wide_spread", count=1),
            ),
        ),
    )


def test_gate_summary_accepts_supplied_input_shapes_without_exact_type_coupling():
    report = _report(
        (
            InputGateShape(
                market_slug="market-alpha",
                side="yes",
                gate_name="calibration",
                gate_status="pass",
                gate_cost_per_share=Decimal("0.001000"),
                reason_codes=("calibration_passed",),
            ),
        ),
    )

    assert report.rows == (
        PaperRecommendationGateSummaryRow(
            gate_name="calibration",
            gate_input_count=1,
            pass_count=1,
            watch_count=0,
            blocked_count=0,
            total_gate_cost_per_share=Decimal("0.001000"),
            primary_status="pass",
            reason_code_counts=(
                GateReasonCodeCount(reason_code="calibration_passed", count=1),
            ),
        ),
    )


def test_gate_summary_empty_input_is_pass_with_zero_totals():
    report = _report(())

    assert report.gate_input_count == 0
    assert report.gate_name_count == 0
    assert report.pass_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.total_gate_cost_per_share == ZERO
    assert report.primary_status == "pass"
    assert report.rows == ()


def test_gate_summary_validates_hard_safety_flags_on_supplied_rows():
    valid = _gate_row("market-alpha")

    with pytest.raises(ValueError, match="gate row must be paper_only"):
        _report((replace(valid, paper_only=False),))
    with pytest.raises(ValueError, match="gate row must be report_only"):
        _report((replace(valid, report_only=False),))
    with pytest.raises(ValueError, match="gate row must be readonly"):
        _report((replace(valid, readonly=False),))


def test_gate_summary_validates_statuses_decimal_quantization_and_utc():
    report = _report(
        (_gate_row("market-alpha"),),
        generated_at=datetime(2026, 6, 19, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    with pytest.raises(FrozenInstanceError):
        report.primary_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="generated_at"):
        _report((_gate_row("market-alpha"),), generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        PaperRecommendationGateSummaryReport(
            generated_at=_DatetimeSubclass(2026, 6, 19, 12, 0, tzinfo=UTC),
            gate_input_count=0,
            gate_name_count=0,
            pass_count=0,
            watch_count=0,
            blocked_count=0,
            total_gate_cost_per_share=ZERO,
            primary_status="pass",
            rows=(),
        )
    with pytest.raises(ValueError, match="gate_status"):
        _gate_row("market-alpha", gate_status="skip")
    with pytest.raises(ValueError, match="gate_cost_per_share"):
        _gate_row("market-alpha", gate_cost_per_share=Decimal("0.0100001"))
    with pytest.raises(ValueError, match="gate_cost_per_share"):
        _gate_row("market-alpha", gate_cost_per_share=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="count"):
        GateReasonCodeCount(reason_code="risk_budget_passed", count=_IntSubclass(1))


def test_gate_summary_constructor_rejects_inconsistent_report_and_group_rows():
    valid = _report(
        (
            _gate_row("market-alpha", gate_status="pass"),
            _gate_row("market-beta", gate_status="watch", reason_codes=("near_limit",)),
        ),
    )

    with pytest.raises(ValueError, match="gate_input_count"):
        replace(valid, gate_input_count=3)
    with pytest.raises(ValueError, match="gate_name_count"):
        replace(valid, gate_name_count=2)
    with pytest.raises(ValueError, match="watch_count"):
        replace(valid, watch_count=0)
    with pytest.raises(ValueError, match="total_gate_cost_per_share"):
        replace(valid, total_gate_cost_per_share=Decimal("0.999999"))
    with pytest.raises(ValueError, match="primary_status"):
        replace(valid, primary_status="blocked")
    with pytest.raises(ValueError, match="gate_input_count"):
        replace(
            valid.rows[0],
            gate_input_count=3,
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            valid.rows[0],
            reason_code_counts=(),
        )
