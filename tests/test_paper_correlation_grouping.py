from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_correlation_grouping import (
    PaperCorrelationGroupRow,
    PaperCorrelationGroupingConfig,
    PaperCorrelationGroupingReport,
    PaperCorrelationInputRow,
    build_paper_correlation_grouping_report,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


def _input_row(
    market_slug: str,
    *,
    side: str = "yes",
    action: str = "recommend",
    recommendation_score: Decimal = Decimal("0.800000"),
    requested_paper_notional: Decimal = Decimal("10.000000"),
    event_id: str = "event-alpha",
    theme_id: str = "theme-macro",
    correlation_group: str = "rates",
    reason_codes: tuple[str, ...] = ("edge_positive",),
    paper_only: object = True,
    report_only: object = True,
    readonly: object = True,
) -> PaperCorrelationInputRow:
    return PaperCorrelationInputRow(
        market_slug=market_slug,
        side=side,
        action=action,
        recommendation_score=recommendation_score,
        requested_paper_notional=requested_paper_notional,
        event_id=event_id,
        theme_id=theme_id,
        correlation_group=correlation_group,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _config(**overrides: object) -> PaperCorrelationGroupingConfig:
    values = {
        "config_version": "correlation-groups-v0",
        "max_group_notional": Decimal("100.000000"),
        "max_group_count": 3,
    }
    values.update(overrides)
    return PaperCorrelationGroupingConfig(**values)


def _report(
    rows: object,
    *,
    config: PaperCorrelationGroupingConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperCorrelationGroupingReport:
    return build_paper_correlation_grouping_report(
        rows,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_correlation_grouping_summarizes_event_theme_and_correlation_groups():
    rows = (
        _input_row(
            "gamma-market",
            requested_paper_notional=Decimal("25.000000"),
            event_id="event-b",
            theme_id="theme-b",
            correlation_group="macro",
            reason_codes=("zeta",),
        ),
        _input_row(
            "alpha-market",
            requested_paper_notional=Decimal("40.000000"),
            event_id="event-a",
            theme_id="theme-a",
            correlation_group="macro",
            reason_codes=("alpha",),
        ),
        _input_row(
            "beta-market",
            action="watch",
            side="none",
            recommendation_score=Decimal("0.250000"),
            requested_paper_notional=ZERO,
            event_id="event-a",
            theme_id="theme-a",
            correlation_group="single-beta",
            reason_codes=("watch_only",),
        ),
        _input_row(
            "delta-market",
            requested_paper_notional=Decimal("12.345678"),
            event_id="event-a",
            theme_id="theme-b",
            correlation_group="macro",
            reason_codes=("alpha", "depth_ok"),
        ),
    )

    report = _report(
        rows,
        generated_at=datetime(2026, 6, 19, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "correlation-groups-v0"
    assert report.input_row_count == 4
    assert report.group_count == 6
    assert report.blocked_group_count == 0
    assert report.watch_group_count == 1
    assert report.group_rows == (
        PaperCorrelationGroupRow(
            group_key="event-a",
            group_type="event",
            row_count=3,
            recommended_count=2,
            requested_notional=Decimal("52.345678"),
            group_status="pass",
            reason_codes=(
                "correlation_group_passed",
                "alpha",
                "depth_ok",
                "watch_only",
            ),
        ),
        PaperCorrelationGroupRow(
            group_key="event-b",
            group_type="event",
            row_count=1,
            recommended_count=1,
            requested_notional=Decimal("25.000000"),
            group_status="pass",
            reason_codes=("correlation_group_passed", "zeta"),
        ),
        PaperCorrelationGroupRow(
            group_key="macro",
            group_type="correlation",
            row_count=3,
            recommended_count=3,
            requested_notional=Decimal("77.345678"),
            group_status="watch",
            reason_codes=("near_group_count_cap", "alpha", "depth_ok", "zeta"),
        ),
        PaperCorrelationGroupRow(
            group_key="single-beta",
            group_type="correlation",
            row_count=1,
            recommended_count=0,
            requested_notional=ZERO,
            group_status="pass",
            reason_codes=("correlation_group_passed", "watch_only"),
        ),
        PaperCorrelationGroupRow(
            group_key="theme-a",
            group_type="theme",
            row_count=2,
            recommended_count=1,
            requested_notional=Decimal("40.000000"),
            group_status="pass",
            reason_codes=("correlation_group_passed", "alpha", "watch_only"),
        ),
        PaperCorrelationGroupRow(
            group_key="theme-b",
            group_type="theme",
            row_count=2,
            recommended_count=2,
            requested_notional=Decimal("37.345678"),
            group_status="pass",
            reason_codes=("correlation_group_passed", "alpha", "depth_ok", "zeta"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_correlation_grouping_blocks_over_caps_and_uses_per_type_overrides():
    rows = (
        _input_row(
            "alpha",
            requested_paper_notional=Decimal("70.000000"),
            event_id="event-a",
            theme_id="theme-risk",
            correlation_group="macro",
        ),
        _input_row(
            "beta",
            requested_paper_notional=Decimal("60.000000"),
            event_id="event-a",
            theme_id="theme-risk",
            correlation_group="macro",
            reason_codes=("crowded",),
        ),
        _input_row(
            "gamma",
            requested_paper_notional=Decimal("5.000000"),
            event_id="event-b",
            theme_id="theme-risk",
            correlation_group="macro",
        ),
    )

    report = _report(
        rows,
        config=_config(
            event_max_group_notional=Decimal("120.000000"),
            event_max_group_count=5,
            theme_max_group_notional=Decimal("200.000000"),
            theme_max_group_count=2,
            correlation_max_group_notional=Decimal("80.000000"),
            correlation_max_group_count=5,
        ),
    )

    event_a = report.group_row("event", "event-a")
    theme_risk = report.group_row("theme", "theme-risk")
    macro = report.group_row("correlation", "macro")

    assert event_a.group_status == "blocked"
    assert event_a.requested_notional == Decimal("130.000000")
    assert event_a.reason_codes == (
        "group_notional_cap_exceeded",
        "crowded",
        "edge_positive",
    )
    assert theme_risk.group_status == "blocked"
    assert theme_risk.recommended_count == 3
    assert theme_risk.reason_codes == (
        "group_count_cap_exceeded",
        "crowded",
        "edge_positive",
    )
    assert macro.group_status == "blocked"
    assert macro.reason_codes == (
        "group_notional_cap_exceeded",
        "crowded",
        "edge_positive",
    )
    assert report.blocked_group_count == 3
    assert report.watch_group_count == 0


def test_correlation_grouping_watches_near_notional_cap():
    rows = (
        _input_row(
            "alpha",
            requested_paper_notional=Decimal("95.000000"),
            event_id="event-a",
            theme_id="theme-a",
            correlation_group="macro",
        ),
    )

    report = _report(rows)

    assert report.group_row("event", "event-a").group_status == "watch"
    assert report.group_row("event", "event-a").reason_codes == (
        "near_group_notional_cap",
        "edge_positive",
    )


def test_correlation_grouping_accepts_report_shape_and_rejects_hard_flags():
    @dataclass(frozen=True)
    class RecommendationShape:
        recommendation_rows: tuple[PaperCorrelationInputRow, ...]
        paper_only: object = True
        report_only: object = True
        readonly: object = True

    rows = (_input_row("alpha"),)

    assert _report(RecommendationShape(rows)).group_count == 3
    with pytest.raises(ValueError, match="recommendation_rows must be an iterable"):
        _report("not rows")
    with pytest.raises(ValueError, match="recommendation source must be paper_only"):
        _report(RecommendationShape(rows, paper_only=False))
    with pytest.raises(ValueError, match="recommendation source must be report_only"):
        _report(RecommendationShape(rows, report_only=False))
    with pytest.raises(ValueError, match="recommendation source must be readonly"):
        _report(RecommendationShape(rows, readonly=False))
    with pytest.raises(ValueError, match="paper_only"):
        _input_row("bad-paper", paper_only=1)
    with pytest.raises(ValueError, match="report_only"):
        _input_row("bad-report", report_only=1)
    with pytest.raises(ValueError, match="readonly"):
        _input_row("bad-readonly", readonly=1)


def test_correlation_grouping_validates_config_decimal_precision_and_types():
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=" correlation-groups-v0")
    with pytest.raises(ValueError, match="max_group_notional"):
        _config(max_group_notional=Decimal("100.0000001"))
    with pytest.raises(ValueError, match="max_group_notional"):
        _config(max_group_notional=Decimal("0.000000"))
    with pytest.raises(ValueError, match="max_group_notional"):
        _config(max_group_notional=_DecimalSubclass("100.000000"))
    with pytest.raises(ValueError, match="max_group_count"):
        _config(max_group_count=0)
    with pytest.raises(ValueError, match="max_group_count"):
        _config(max_group_count=_IntSubclass(3))
    with pytest.raises(ValueError, match="event_max_group_count"):
        _config(event_max_group_count=0)
    with pytest.raises(ValueError, match="theme_max_group_notional"):
        _config(theme_max_group_notional=Decimal("10.0000001"))
    with pytest.raises(ValueError, match="correlation_max_group_notional"):
        _config(correlation_max_group_notional=Decimal("-0.000001"))


def test_correlation_grouping_validates_input_rows_and_report_consistency():
    with pytest.raises(ValueError, match="side"):
        _input_row("alpha", side="maybe")
    with pytest.raises(ValueError, match="action"):
        _input_row("alpha", action="buy")
    with pytest.raises(ValueError, match="recommendation_score"):
        _input_row("alpha", recommendation_score=Decimal("0.1000001"))
    with pytest.raises(ValueError, match="recommendation_score"):
        _input_row("alpha", recommendation_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="requested_paper_notional"):
        _input_row("alpha", requested_paper_notional=Decimal("1.0000001"))
    with pytest.raises(ValueError, match="reason_codes"):
        _input_row("alpha", reason_codes=("edge_positive", "edge_positive"))
    with pytest.raises(ValueError, match="recommended rows"):
        _input_row("alpha", action="recommend", side="none")
    with pytest.raises(ValueError, match="unrecommended rows"):
        _input_row("alpha", action="watch", requested_paper_notional=Decimal("1.000000"))

    report = _report((_input_row("alpha"),))

    with pytest.raises(ValueError, match="group_count"):
        replace(report, group_count=2)
    with pytest.raises(ValueError, match="blocked_group_count"):
        replace(report, blocked_group_count=1)
    with pytest.raises(ValueError, match="watch_group_count"):
        replace(report, watch_group_count=1)
    with pytest.raises(ValueError, match="input_row_count"):
        replace(report, input_row_count=2)
    with pytest.raises(ValueError, match="group_rows"):
        replace(report, group_rows=tuple(reversed(report.group_rows)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_correlation_grouping_frozen_and_generated_at_type_validation():
    report = _report((_input_row("alpha"),))

    with pytest.raises(FrozenInstanceError):
        report.group_count = 99  # type: ignore[misc]
    with pytest.raises(ValueError, match="generated_at"):
        _report((_input_row("alpha"),), generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        PaperCorrelationGroupingReport(
            generated_at=_DatetimeSubclass(2026, 6, 19, 12, 0, tzinfo=UTC),
            config_version="correlation-groups-v0",
            input_row_count=0,
            group_count=0,
            blocked_group_count=0,
            watch_group_count=0,
            group_rows=(),
        )
