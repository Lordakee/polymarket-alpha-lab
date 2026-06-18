from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.cost_aware_event_strategy import (
    GATE_NAMES,
    PaperCostAwareEventSideResult,
    PaperCostAwareEventStrategyGateResult,
    PaperCostAwareEventStrategyReport,
)
from polymarket_alpha_lab.market_context_freshness import (
    PaperMarketContextFreshnessConfig,
    PaperMarketContextFreshnessReport,
    PaperMarketContextFreshnessRow,
    build_paper_market_context_freshness_report,
)


GENERATED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _IntSubclass(int):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def _config(**overrides) -> PaperMarketContextFreshnessConfig:
    values = {
        "config_version": "market-context-freshness-v0",
        "max_report_age_seconds": 120,
        "min_context_count": 1,
    }
    values.update(overrides)
    return PaperMarketContextFreshnessConfig(**values)


def _side_result(side: str) -> PaperCostAwareEventSideResult:
    return PaperCostAwareEventSideResult(
        side=side,
        fair_probability=Decimal("0.6000") if side == "yes" else Decimal("0.4000"),
        executable_price=Decimal("0.5000"),
        ask_size=Decimal("10.0000"),
        gross_edge_per_share=(
            Decimal("0.1000") if side == "yes" else Decimal("-0.1000")
        ),
        fee_cost_per_share=Decimal("0.000000"),
        non_fee_cost_per_share=Decimal("0.000000"),
        total_cost_per_share=Decimal("0.000000"),
        net_edge_per_share=(
            Decimal("0.100000") if side == "yes" else Decimal("-0.100000")
        ),
        reason_codes=("paper_edge_complete",),
    )


def _gate_results() -> tuple[PaperCostAwareEventStrategyGateResult, ...]:
    return tuple(
        PaperCostAwareEventStrategyGateResult(
            gate_name=gate_name,
            status="pass",
            reason_code=f"{gate_name}_ready",
            message="Gate observed.",
            observed_value=Decimal("1.0000"),
            threshold=Decimal("1.0000"),
        )
        for gate_name in GATE_NAMES
    )


def _source_report(
    market_slug: str = "alpha-market",
    *,
    generated_at: datetime | None = None,
) -> PaperCostAwareEventStrategyReport:
    return PaperCostAwareEventStrategyReport(
        generated_at=(
            generated_at
            if generated_at is not None
            else GENERATED_AT - timedelta(seconds=30)
        ),
        config_version="cost-aware-event-strategy-v0",
        market_slug=market_slug,
        question=f"{market_slug} context?",
        fair_probability_yes=Decimal("0.6000"),
        confidence=Decimal("0.9000"),
        yes_bid=Decimal("0.4900"),
        no_bid=Decimal("0.5000"),
        spread=Decimal("0.0200"),
        resolution_risk=Decimal("0.0500"),
        selected_side="yes",
        status="paper_review_ready",
        yes_result=_side_result("yes"),
        no_result=_side_result("no"),
        gate_results=_gate_results(),
    )


def test_market_context_freshness_reports_fresh_context_as_pass():
    report = build_paper_market_context_freshness_report(
        (
            _source_report(
                "beta-market",
                generated_at=GENERATED_AT - timedelta(seconds=30),
            ),
            _source_report(
                "alpha-market",
                generated_at=GENERATED_AT - timedelta(seconds=60),
            ),
        ),
        config=_config(max_report_age_seconds=120, min_context_count=2),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, PaperMarketContextFreshnessReport)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-context-freshness-v0"
    assert report.max_report_age_seconds == 120
    assert report.min_context_count == 2
    assert report.context_count == 2
    assert report.status == "pass"
    assert report.reason_codes == ("market_context_fresh",)
    assert report.rows == (
        PaperMarketContextFreshnessRow(
            market_slug="alpha-market",
            report_generated_at=GENERATED_AT - timedelta(seconds=60),
            report_age_seconds=Decimal("60"),
            status="pass",
            reason_codes=("fresh_market_context",),
        ),
        PaperMarketContextFreshnessRow(
            market_slug="beta-market",
            report_generated_at=GENERATED_AT - timedelta(seconds=30),
            report_age_seconds=Decimal("30"),
            status="pass",
            reason_codes=("fresh_market_context",),
        ),
    )
    assert tuple(row.paper_only for row in report.rows) == (True, True)
    assert tuple(row.report_only for row in report.rows) == (True, True)
    assert tuple(row.readonly for row in report.rows) == (True, True)


def test_market_context_freshness_watches_context_older_than_max_age():
    report = build_paper_market_context_freshness_report(
        (
            _source_report(
                "stale-market",
                generated_at=GENERATED_AT - timedelta(seconds=61),
            ),
        ),
        config=_config(max_report_age_seconds=60, min_context_count=1),
        generated_at=GENERATED_AT,
    )

    assert report.status == "watch"
    assert report.reason_codes == ("stale_market_context",)
    assert report.rows == (
        PaperMarketContextFreshnessRow(
            market_slug="stale-market",
            report_generated_at=GENERATED_AT - timedelta(seconds=61),
            report_age_seconds=Decimal("61"),
            status="watch",
            reason_codes=("stale_market_context",),
        ),
    )


def test_market_context_freshness_marks_subsecond_old_report_as_stale():
    report = build_paper_market_context_freshness_report(
        (
            _source_report(
                "micro-stale-market",
                generated_at=GENERATED_AT - timedelta(seconds=60, microseconds=1),
            ),
        ),
        config=_config(max_report_age_seconds=60, min_context_count=1),
        generated_at=GENERATED_AT,
    )

    assert report.status == "watch"
    assert report.reason_codes == ("stale_market_context",)
    assert report.rows == (
        PaperMarketContextFreshnessRow(
            market_slug="micro-stale-market",
            report_generated_at=GENERATED_AT - timedelta(seconds=60, microseconds=1),
            report_age_seconds=Decimal("60.000001"),
            status="watch",
            reason_codes=("stale_market_context",),
        ),
    )


def test_market_context_freshness_blocks_after_double_max_age_and_sorts_by_severity():
    report = build_paper_market_context_freshness_report(
        (
            _source_report(
                "zeta-fresh-market",
                generated_at=GENERATED_AT - timedelta(seconds=60),
            ),
            _source_report(
                "middle-watch-market",
                generated_at=GENERATED_AT - timedelta(seconds=61),
            ),
            _source_report(
                "alpha-expired-market",
                generated_at=GENERATED_AT - timedelta(seconds=121),
            ),
        ),
        config=_config(max_report_age_seconds=60, min_context_count=3),
        generated_at=GENERATED_AT,
    )

    assert report.status == "blocked"
    assert report.reason_codes == ("blocked_market_context",)
    assert tuple(row.market_slug for row in report.rows) == (
        "alpha-expired-market",
        "middle-watch-market",
        "zeta-fresh-market",
    )
    assert tuple(row.status for row in report.rows) == ("blocked", "watch", "pass")
    assert report.rows[0].report_age_seconds == Decimal("121")
    assert report.rows[0].reason_codes == ("expired_market_context",)


def test_market_context_freshness_rejects_future_report_timestamps():
    with pytest.raises(ValueError, match="future"):
        build_paper_market_context_freshness_report(
            (
                _source_report(
                    "future-market",
                    generated_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_market_context_freshness_blocks_empty_or_insufficient_context():
    empty_report = build_paper_market_context_freshness_report(
        (),
        config=_config(max_report_age_seconds=60, min_context_count=1),
        generated_at=GENERATED_AT,
    )
    short_report = build_paper_market_context_freshness_report(
        (
            _source_report(
                "fresh-market",
                generated_at=GENERATED_AT - timedelta(seconds=1),
            ),
        ),
        config=_config(max_report_age_seconds=60, min_context_count=2),
        generated_at=GENERATED_AT,
    )

    assert empty_report.status == "blocked"
    assert empty_report.context_count == 0
    assert empty_report.reason_codes == (
        "no_market_context",
        "insufficient_market_context",
    )
    assert empty_report.rows == ()
    assert short_report.status == "blocked"
    assert short_report.context_count == 1
    assert short_report.reason_codes == ("insufficient_market_context",)
    assert tuple(row.status for row in short_report.rows) == ("pass",)


def test_market_context_freshness_rejects_direct_row_status_inconsistent_with_age():
    stale_row_claiming_pass = PaperMarketContextFreshnessRow(
        market_slug="stale-market",
        report_generated_at=GENERATED_AT - timedelta(seconds=999),
        report_age_seconds=Decimal("999.000000"),
        status="pass",
        reason_codes=("fresh_market_context",),
    )

    with pytest.raises(ValueError, match="row status"):
        PaperMarketContextFreshnessReport(
            generated_at=GENERATED_AT,
            config_version="market-context-freshness-v0",
            max_report_age_seconds=1,
            min_context_count=1,
            context_count=1,
            status="pass",
            reason_codes=("market_context_fresh",),
            rows=(stale_row_claiming_pass,),
        )


def test_market_context_freshness_accepts_direct_report_matching_row_age_statuses():
    direct_report = PaperMarketContextFreshnessReport(
        generated_at=GENERATED_AT,
        config_version="market-context-freshness-v0",
        max_report_age_seconds=60,
        min_context_count=1,
        context_count=2,
        status="watch",
        reason_codes=("stale_market_context",),
        rows=(
            PaperMarketContextFreshnessRow(
                market_slug="stale-market",
                report_generated_at=GENERATED_AT - timedelta(seconds=61),
                report_age_seconds=Decimal("61.000000"),
                status="watch",
                reason_codes=("stale_market_context",),
            ),
            PaperMarketContextFreshnessRow(
                market_slug="fresh-market",
                report_generated_at=GENERATED_AT - timedelta(seconds=60),
                report_age_seconds=Decimal("60.000000"),
                status="pass",
                reason_codes=("fresh_market_context",),
            ),
        ),
    )
    built_report = build_paper_market_context_freshness_report(
        (
            _source_report(
                "stale-market",
                generated_at=GENERATED_AT - timedelta(seconds=61),
            ),
            _source_report(
                "fresh-market",
                generated_at=GENERATED_AT - timedelta(seconds=60),
            ),
        ),
        config=_config(max_report_age_seconds=60, min_context_count=1),
        generated_at=GENERATED_AT,
    )

    assert direct_report.status == "watch"
    assert direct_report.reason_codes == ("stale_market_context",)
    assert tuple(row.status for row in direct_report.rows) == ("watch", "pass")
    assert built_report.status == "watch"
    assert built_report.reason_codes == ("stale_market_context",)
    assert tuple(row.status for row in built_report.rows) == ("watch", "pass")


def test_market_context_freshness_normalizes_datetimes_to_utc():
    generated_at = datetime(
        2026,
        6,
        18,
        8,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    source_generated_at = datetime(
        2026,
        6,
        18,
        13,
        30,
        tzinfo=timezone(timedelta(hours=2)),
    )

    report = build_paper_market_context_freshness_report(
        (_source_report("offset-market", generated_at=source_generated_at),),
        config=_config(max_report_age_seconds=3600, min_context_count=1),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].report_generated_at == datetime(2026, 6, 18, 11, 30, tzinfo=UTC)
    assert report.rows[0].report_age_seconds == Decimal("1800")


def test_market_context_freshness_validates_exact_scalar_types():
    with pytest.raises(ValueError, match="config_version"):
        PaperMarketContextFreshnessConfig(
            config_version=_StringSubclass("market-context-freshness-v0"),
            max_report_age_seconds=60,
            min_context_count=1,
        )
    with pytest.raises(ValueError, match="max_report_age_seconds"):
        PaperMarketContextFreshnessConfig(
            config_version="market-context-freshness-v0",
            max_report_age_seconds=True,
            min_context_count=1,
        )
    with pytest.raises(ValueError, match="min_context_count"):
        PaperMarketContextFreshnessConfig(
            config_version="market-context-freshness-v0",
            max_report_age_seconds=60,
            min_context_count=_IntSubclass(1),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_market_context_freshness_report(
            (_source_report(),),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 6, 18, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="reports"):
        build_paper_market_context_freshness_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="market_slug"):
        PaperMarketContextFreshnessRow(
            market_slug=_StringSubclass("market"),
            report_generated_at=GENERATED_AT,
            report_age_seconds=Decimal("1"),
            status="pass",
            reason_codes=("fresh_market_context",),
        )
    with pytest.raises(ValueError, match="report_age_seconds"):
        PaperMarketContextFreshnessRow(
            market_slug="market",
            report_generated_at=GENERATED_AT,
            report_age_seconds=_DecimalSubclass("1"),
            status="pass",
            reason_codes=("fresh_market_context",),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        PaperMarketContextFreshnessRow(
            market_slug="market",
            report_generated_at=GENERATED_AT,
            report_age_seconds=Decimal("1"),
            status="pass",
            reason_codes=(_StringSubclass("fresh_market_context"),),
        )


def test_market_context_freshness_rejects_non_paper_or_report_source_flags():
    non_paper_report = _source_report("non-paper-market")
    object.__setattr__(non_paper_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        build_paper_market_context_freshness_report(
            (non_paper_report,),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    non_report_report = _source_report("non-report-market")
    object.__setattr__(non_report_report, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        build_paper_market_context_freshness_report(
            (non_report_report,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_market_context_freshness_dataclasses_are_frozen_and_hard_flags_are_true():
    report = build_paper_market_context_freshness_report(
        (_source_report("fresh-market"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
