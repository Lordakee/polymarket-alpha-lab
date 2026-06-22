from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.paper_recommendation_reason_trend import (
    PaperRecommendationReasonTrendReport,
    PaperRecommendationReasonTrendRow,
    PaperRecommendationTransitionTrendRow,
)


GENERATED_AT = datetime(2026, 6, 22, 18, 0, tzinfo=UTC)
T1 = datetime(2026, 6, 22, 15, 0, tzinfo=UTC)
T2 = datetime(2026, 6, 22, 16, 0, tzinfo=UTC)
T3 = datetime(2026, 6, 22, 17, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_recommendation_reason_trend_health",
    )


def _config(
    *,
    max_blocked_status_share: Decimal = d("0.500000"),
    max_reject_status_share: Decimal = d("0.500000"),
    max_new_reason_code_count: int = 0,
    max_transition_count: int = 0,
):
    module = _api()
    return module.PaperRecommendationReasonTrendHealthConfig(
        config_version="paper-recommendation-reason-trend-health-v0",
        max_blocked_status_share=max_blocked_status_share,
        max_reject_status_share=max_reject_status_share,
        max_new_reason_code_count=max_new_reason_code_count,
        max_transition_count=max_transition_count,
    )


def _reason_row(
    reason_code: str,
    *,
    source_status: str = "recommend",
    count: int = 1,
    first_seen_at: datetime = T1,
    latest_seen_at: datetime = T3,
) -> PaperRecommendationReasonTrendRow:
    return PaperRecommendationReasonTrendRow(
        reason_code=reason_code,
        source_status=source_status,
        count=count,
        first_seen_at=first_seen_at,
        latest_seen_at=latest_seen_at,
    )


def _transition_row(
    *,
    market_slug: str = "alpha-market",
    side: str = "yes",
    from_status: str = "watch",
    to_status: str = "recommend",
    transition_count: int = 1,
    latest_transition_at: datetime = T3,
    reason_codes: tuple[str, ...] = ("alpha",),
) -> PaperRecommendationTransitionTrendRow:
    return PaperRecommendationTransitionTrendRow(
        market_slug=market_slug,
        side=side,
        from_status=from_status,
        to_status=to_status,
        transition_count=transition_count,
        latest_transition_at=latest_transition_at,
        reason_codes=reason_codes,
    )


def _source_report(
    *,
    source_report_count: int = 3,
    reason_trend_rows: tuple[PaperRecommendationReasonTrendRow, ...] = (),
    transition_trend_rows: tuple[PaperRecommendationTransitionTrendRow, ...] = (),
) -> PaperRecommendationReasonTrendReport:
    ordered_reason_rows = tuple(
        sorted(
            reason_trend_rows,
            key=lambda row: (-row.count, row.reason_code, row.source_status),
        ),
    )
    ordered_transition_rows = tuple(
        sorted(
            transition_trend_rows,
            key=lambda row: (
                -row.transition_count,
                row.market_slug,
                row.side,
                row.from_status,
                row.to_status,
            ),
        ),
    )
    return PaperRecommendationReasonTrendReport(
        generated_at=T3,
        config_version="paper-recommendation-reason-trend-v0",
        source_report_count=source_report_count,
        reason_trend_rows=ordered_reason_rows,
        transition_trend_rows=ordered_transition_rows,
    )


def _build(
    source_report: PaperRecommendationReasonTrendReport,
    *,
    config=None,
    generated_at: datetime = GENERATED_AT,
):
    return _api().build_paper_recommendation_reason_trend_health_report(
        source_report,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_reason_trend_health_blocks_when_source_history_is_empty():
    report = _build(_source_report(source_report_count=0))
    api = _api()

    assert isinstance(report, api.PaperRecommendationReasonTrendHealthReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-recommendation-reason-trend-health-v0"
    assert report.health_status == "blocked"
    assert report.source_report_count == 0
    assert report.reason_code_count == 0
    assert report.blocked_status_count == 0
    assert report.blocked_status_share is None
    assert report.reject_status_count == 0
    assert report.reject_status_share is None
    assert report.new_reason_code_count == 0
    assert report.transition_count == 0
    assert report.persistent_reason_codes == ()
    assert report.reason_codes == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_reason_trend_health_passes_when_trend_is_clean_and_stable():
    report = _build(
        _source_report(
            reason_trend_rows=(
                _reason_row(
                    "beta",
                    source_status="watch",
                    count=1,
                    first_seen_at=T1,
                    latest_seen_at=T2,
                ),
                _reason_row(
                    "alpha",
                    source_status="recommend",
                    count=3,
                    first_seen_at=T1,
                    latest_seen_at=T3,
                ),
            ),
        ),
    )

    assert report.health_status == "pass"
    assert report.source_report_count == 3
    assert report.reason_code_count == 2
    assert report.blocked_status_count == 0
    assert type(report.blocked_status_share) is Decimal
    assert report.blocked_status_share == d("0.000000")
    assert report.reject_status_count == 0
    assert type(report.reject_status_share) is Decimal
    assert report.reject_status_share == d("0.000000")
    assert report.new_reason_code_count == 0
    assert report.transition_count == 0
    assert report.persistent_reason_codes == ("alpha",)
    assert report.reason_codes == ("alpha", "beta")
    assert report.max_blocked_status_share == d("0.500000")
    assert report.max_reject_status_share == d("0.500000")
    assert report.max_new_reason_code_count == 0
    assert report.max_transition_count == 0


def test_reason_trend_health_blocks_when_blocked_status_share_exceeds_threshold():
    report = _build(
        _source_report(
            reason_trend_rows=(
                _reason_row(
                    "gamma",
                    source_status="blocked",
                    count=3,
                    first_seen_at=T1,
                    latest_seen_at=T3,
                ),
                _reason_row(
                    "alpha",
                    source_status="recommend",
                    count=2,
                    first_seen_at=T1,
                    latest_seen_at=T3,
                ),
            ),
        ),
        config=_config(max_blocked_status_share=d("0.500000")),
    )

    assert report.health_status == "blocked"
    assert report.blocked_status_count == 3
    assert report.blocked_status_share == d("0.600000")
    assert report.reject_status_count == 0
    assert report.reject_status_share == d("0.000000")


def test_reason_trend_health_blocks_when_reject_status_share_exceeds_threshold():
    report = _build(
        _source_report(
            reason_trend_rows=(
                _reason_row(
                    "reject_a",
                    source_status="reject",
                    count=1,
                    first_seen_at=T1,
                    latest_seen_at=T3,
                ),
                _reason_row(
                    "reject_b",
                    source_status="reject",
                    count=1,
                    first_seen_at=T1,
                    latest_seen_at=T3,
                ),
                _reason_row(
                    "alpha",
                    source_status="recommend",
                    count=1,
                    first_seen_at=T1,
                    latest_seen_at=T3,
                ),
            ),
        ),
        config=_config(max_reject_status_share=d("0.500000")),
    )

    assert report.health_status == "blocked"
    assert report.blocked_status_count == 0
    assert report.blocked_status_share == d("0.000000")
    assert report.reject_status_count == 2
    assert report.reject_status_share == d("0.666667")


def test_reason_trend_health_watches_when_new_reason_code_count_exceeds_threshold():
    report = _build(
        _source_report(
            reason_trend_rows=(
                _reason_row(
                    "zeta",
                    source_status="watch",
                    count=1,
                    first_seen_at=T3,
                    latest_seen_at=T3,
                ),
                _reason_row(
                    "alpha",
                    source_status="recommend",
                    count=2,
                    first_seen_at=T1,
                    latest_seen_at=T3,
                ),
                _reason_row(
                    "beta",
                    source_status="queued",
                    count=1,
                    first_seen_at=T3,
                    latest_seen_at=T3,
                ),
            ),
        ),
        config=_config(max_new_reason_code_count=1),
    )

    assert report.health_status == "watch"
    assert report.new_reason_code_count == 2
    assert report.transition_count == 0
    assert report.persistent_reason_codes == ("alpha",)
    assert report.reason_codes == ("alpha", "beta", "zeta")


def test_reason_trend_health_watches_when_transition_count_exceeds_threshold():
    report = _build(
        _source_report(
            reason_trend_rows=(
                _reason_row(
                    "beta",
                    source_status="watch",
                    count=1,
                    first_seen_at=T1,
                    latest_seen_at=T2,
                ),
                _reason_row(
                    "alpha",
                    source_status="recommend",
                    count=2,
                    first_seen_at=T1,
                    latest_seen_at=T3,
                ),
            ),
            transition_trend_rows=(
                _transition_row(
                    transition_count=2,
                    latest_transition_at=T3,
                    reason_codes=("alpha",),
                ),
            ),
        ),
        config=_config(max_transition_count=1),
    )

    assert report.health_status == "watch"
    assert report.new_reason_code_count == 0
    assert report.transition_count == 2
    assert report.persistent_reason_codes == ("alpha",)
    assert report.reason_codes == ("alpha", "beta")


def test_reason_trend_health_orders_reason_codes_and_persistent_codes_deterministically():
    report = _build(
        _source_report(
            reason_trend_rows=(
                _reason_row(
                    "zeta",
                    source_status="recommend",
                    count=2,
                    first_seen_at=T1,
                    latest_seen_at=T3,
                ),
                _reason_row(
                    "beta",
                    source_status="queued",
                    count=1,
                    first_seen_at=T1,
                    latest_seen_at=T2,
                ),
                _reason_row(
                    "alpha",
                    source_status="watch",
                    count=3,
                    first_seen_at=T1,
                    latest_seen_at=T3,
                ),
            ),
        ),
    )

    assert report.health_status == "pass"
    assert report.reason_codes == ("alpha", "beta", "zeta")
    assert report.persistent_reason_codes == ("alpha", "zeta")


def test_reason_trend_health_config_and_report_are_frozen():
    config = _config()
    report = _build(
        _source_report(
            reason_trend_rows=(
                _reason_row(
                    "alpha",
                    source_status="recommend",
                    count=2,
                    first_seen_at=T1,
                    latest_seen_at=T3,
                ),
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        config.max_transition_count = 2
    with pytest.raises(FrozenInstanceError):
        report.health_status = "blocked"


def test_reason_trend_health_enforces_hard_flags():
    api = _api()
    with pytest.raises(ValueError, match="paper_only"):
        api.PaperRecommendationReasonTrendHealthConfig(
            config_version="paper-recommendation-reason-trend-health-v0",
            max_blocked_status_share=d("0.500000"),
            max_reject_status_share=d("0.500000"),
            max_new_reason_code_count=0,
            max_transition_count=0,
            paper_only=False,
        )

    report = _build(
        _source_report(
            reason_trend_rows=(
                _reason_row(
                    "alpha",
                    source_status="recommend",
                    count=2,
                    first_seen_at=T1,
                    latest_seen_at=T3,
                ),
            ),
        ),
    )

    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
