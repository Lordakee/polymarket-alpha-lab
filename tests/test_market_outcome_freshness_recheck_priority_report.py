from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_outcome_freshness_recheck_priority_report import (
    MarketOutcomeFreshnessRecheckCandidate,
    MarketOutcomeFreshnessRecheckPriorityConfig,
    MarketOutcomeFreshnessRecheckPriorityReport,
    build_market_outcome_freshness_recheck_priority_report,
    market_outcome_freshness_recheck_priority_report_to_json,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
CONFIG = MarketOutcomeFreshnessRecheckPriorityConfig(
    config_version="market-outcome-freshness-recheck-priority-v0",
    stale_after_seconds=Decimal("3600"),
    urgent_after_seconds=Decimal("21600"),
    close_pressure_window_seconds=Decimal("7200"),
)


def _candidate(
    index: int,
    *,
    market_slug: str | None = None,
    condition_id: str | None = None,
    question: str | None = None,
    expected_outcome_count: Decimal = Decimal("2"),
    resolved_outcome_count: Decimal = Decimal("2"),
    last_outcome_checked_at: datetime | None = GENERATED_AT - timedelta(minutes=5),
    market_close_time: datetime | None = GENERATED_AT + timedelta(days=1),
) -> MarketOutcomeFreshnessRecheckCandidate:
    return MarketOutcomeFreshnessRecheckCandidate(
        market_slug=market_slug or f"market-{index}",
        condition_id=condition_id or f"condition-{index}",
        question=question or f"Will market {index} resolve?",
        expected_outcome_count=expected_outcome_count,
        resolved_outcome_count=resolved_outcome_count,
        last_outcome_checked_at=last_outcome_checked_at,
        market_close_time=market_close_time,
    )


def _report(
    *candidates: MarketOutcomeFreshnessRecheckCandidate,
    config: MarketOutcomeFreshnessRecheckPriorityConfig = CONFIG,
    generated_at: datetime = GENERATED_AT,
) -> MarketOutcomeFreshnessRecheckPriorityReport:
    return build_market_outcome_freshness_recheck_priority_report(
        candidates,
        config=config,
        generated_at=generated_at,
    )


def test_recheck_priority_empty_input_returns_readonly_empty_report():
    report = _report()

    assert isinstance(report, MarketOutcomeFreshnessRecheckPriorityReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-outcome-freshness-recheck-priority-v0"
    assert report.candidate_count == Decimal("0")
    assert report.row_count == Decimal("0")
    assert report.fresh_count == Decimal("0")
    assert report.watch_count == Decimal("0")
    assert report.urgent_count == Decimal("0")
    assert report.recheck_count == Decimal("0")
    assert report.total_unresolved_outcome_gap == Decimal("0")
    assert report.max_outcome_freshness_age_seconds is None
    assert report.min_close_time_delta_seconds is None
    assert report.status == "empty"
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_recheck_priority_ranking_is_deterministic_across_factors_and_ties():
    stale_checked_at = GENERATED_AT - timedelta(hours=5)
    close_soon = GENERATED_AT + timedelta(minutes=30)
    close_later = GENERATED_AT + timedelta(hours=10)
    alpha_tie = _candidate(
        4,
        market_slug="alpha-tie",
        condition_id="condition-alpha",
        expected_outcome_count=Decimal("3"),
        resolved_outcome_count=Decimal("1"),
        last_outcome_checked_at=stale_checked_at,
        market_close_time=close_soon,
    )
    beta_tie = _candidate(
        5,
        market_slug="beta-tie",
        condition_id="condition-beta",
        expected_outcome_count=Decimal("3"),
        resolved_outcome_count=Decimal("1"),
        last_outcome_checked_at=stale_checked_at,
        market_close_time=close_soon,
    )
    same_gap_less_close_pressure = _candidate(
        2,
        market_slug="same-gap-less-close-pressure",
        expected_outcome_count=Decimal("3"),
        resolved_outcome_count=Decimal("1"),
        last_outcome_checked_at=stale_checked_at,
        market_close_time=close_later,
    )
    smaller_gap = _candidate(
        1,
        market_slug="smaller-gap",
        expected_outcome_count=Decimal("2"),
        resolved_outcome_count=Decimal("1"),
        last_outcome_checked_at=stale_checked_at,
        market_close_time=close_later,
    )

    report = _report(
        smaller_gap,
        beta_tie,
        same_gap_less_close_pressure,
        alpha_tie,
    )

    assert [row.market_slug for row in report.rows] == [
        "alpha-tie",
        "beta-tie",
        "same-gap-less-close-pressure",
        "smaller-gap",
    ]
    assert [row.priority_rank for row in report.rows] == [
        Decimal("1"),
        Decimal("2"),
        Decimal("3"),
        Decimal("4"),
    ]
    assert [row.staleness_priority_seconds for row in report.rows] == [
        Decimal("18000"),
        Decimal("18000"),
        Decimal("18000"),
        Decimal("18000"),
    ]
    assert [row.unresolved_outcome_gap for row in report.rows] == [
        Decimal("2"),
        Decimal("2"),
        Decimal("2"),
        Decimal("1"),
    ]
    assert [row.close_time_pressure_seconds for row in report.rows] == [
        Decimal("5400"),
        Decimal("5400"),
        Decimal("0"),
        Decimal("0"),
    ]


def test_recheck_priority_never_checked_ranks_before_very_stale_checked_market():
    never_checked = _candidate(
        1,
        market_slug="never-checked",
        expected_outcome_count=Decimal("2"),
        resolved_outcome_count=Decimal("1"),
        last_outcome_checked_at=None,
        market_close_time=GENERATED_AT + timedelta(hours=1),
    )
    very_stale_checked = _candidate(
        2,
        market_slug="very-stale-checked",
        expected_outcome_count=Decimal("2"),
        resolved_outcome_count=Decimal("1"),
        last_outcome_checked_at=GENERATED_AT - timedelta(days=2),
        market_close_time=GENERATED_AT + timedelta(hours=1),
    )

    report = _report(very_stale_checked, never_checked)

    assert [row.market_slug for row in report.rows] == [
        "never-checked",
        "very-stale-checked",
    ]
    assert report.rows[0].reason_codes[0] == "outcome_never_checked"


def test_recheck_priority_threshold_statuses_and_reason_codes_are_deterministic():
    never_checked = _candidate(
        1,
        market_slug="never-checked",
        expected_outcome_count=Decimal("2"),
        resolved_outcome_count=Decimal("0"),
        last_outcome_checked_at=None,
        market_close_time=GENERATED_AT - timedelta(minutes=1),
    )
    urgent_stale = _candidate(
        2,
        market_slug="urgent-stale",
        last_outcome_checked_at=GENERATED_AT - timedelta(hours=6),
    )
    watch = _candidate(
        3,
        market_slug="watch",
        expected_outcome_count=Decimal("2"),
        resolved_outcome_count=Decimal("1"),
        last_outcome_checked_at=GENERATED_AT - timedelta(hours=1),
        market_close_time=GENERATED_AT + timedelta(hours=1),
    )
    fresh = _candidate(
        4,
        market_slug="fresh",
        last_outcome_checked_at=GENERATED_AT - timedelta(seconds=3599),
        market_close_time=GENERATED_AT + timedelta(seconds=7201),
    )

    report = _report(fresh, watch, urgent_stale, never_checked)
    rows = {row.market_slug: row for row in report.rows}

    assert report.status == "urgent"
    assert report.urgent_count == Decimal("2")
    assert report.watch_count == Decimal("1")
    assert report.fresh_count == Decimal("1")
    assert report.recheck_count == Decimal("3")
    assert rows["never-checked"].priority_status == "urgent"
    assert rows["never-checked"].outcome_freshness_age_seconds is None
    assert rows["never-checked"].staleness_priority_seconds == Decimal("43200")
    assert rows["never-checked"].close_time_delta_seconds == Decimal("-60")
    assert rows["never-checked"].reason_codes == (
        "outcome_never_checked",
        "unresolved_outcome_gap",
        "market_close_time_passed",
    )
    assert rows["urgent-stale"].priority_status == "urgent"
    assert rows["urgent-stale"].outcome_freshness_age_seconds == Decimal("21600")
    assert rows["urgent-stale"].reason_codes == ("outcome_freshness_urgent",)
    assert rows["watch"].priority_status == "watch"
    assert rows["watch"].reason_codes == (
        "outcome_freshness_stale",
        "unresolved_outcome_gap",
        "market_close_time_soon",
    )
    assert rows["fresh"].priority_status == "fresh"
    assert rows["fresh"].reason_codes == ("outcome_freshness_fresh",)


def test_recheck_priority_rejects_non_utc_datetimes():
    eastern = timezone(timedelta(hours=-4))

    with pytest.raises(ValueError, match="generated_at.*UTC-aware"):
        _report(generated_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="last_outcome_checked_at.*UTC-aware"):
        _candidate(
            1,
            last_outcome_checked_at=datetime(2026, 7, 2, 8, 0, tzinfo=eastern),
        )
    with pytest.raises(ValueError, match="market_close_time.*UTC-aware"):
        _candidate(2, market_close_time=datetime(2026, 7, 2, 12, 30))


def test_recheck_priority_rejects_future_last_outcome_check():
    with pytest.raises(ValueError, match="last_outcome_checked_at"):
        _report(
            _candidate(
                1,
                last_outcome_checked_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )


def test_recheck_priority_dataclasses_are_frozen_and_revalidate_hard_flags():
    report = _report(_candidate(1))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].priority_rank = Decimal("2")
    with pytest.raises(ValueError, match="paper_only"):
        replace(CONFIG, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(_candidate(2), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)


def test_recheck_priority_public_entry_points_reject_wrong_types():
    with pytest.raises(ValueError, match="config"):
        build_market_outcome_freshness_recheck_priority_report(
            (_candidate(1),),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="report"):
        market_outcome_freshness_recheck_priority_report_to_json(object())


def test_recheck_priority_report_rejects_rows_out_of_priority_sort_order():
    report = _report(
        _candidate(
            1,
            market_slug="never-checked",
            last_outcome_checked_at=None,
        ),
        _candidate(
            2,
            market_slug="fresh-checked",
            last_outcome_checked_at=GENERATED_AT - timedelta(minutes=5),
        ),
    )
    misordered_rows = (
        replace(report.rows[1], priority_rank=Decimal("1")),
        replace(report.rows[0], priority_rank=Decimal("2")),
    )

    with pytest.raises(ValueError, match="deterministic priority sort"):
        MarketOutcomeFreshnessRecheckPriorityReport(
            generated_at=report.generated_at,
            config_version=report.config_version,
            candidate_count=report.candidate_count,
            row_count=report.row_count,
            fresh_count=report.fresh_count,
            watch_count=report.watch_count,
            urgent_count=report.urgent_count,
            recheck_count=report.recheck_count,
            total_unresolved_outcome_gap=report.total_unresolved_outcome_gap,
            max_outcome_freshness_age_seconds=report.max_outcome_freshness_age_seconds,
            min_close_time_delta_seconds=report.min_close_time_delta_seconds,
            status=report.status,
            rows=misordered_rows,
        )


def test_recheck_priority_json_payload_uses_decimal_strings_and_iso_datetimes():
    candidate = _candidate(
        1,
        expected_outcome_count=Decimal("2"),
        resolved_outcome_count=Decimal("1"),
        last_outcome_checked_at=GENERATED_AT - timedelta(hours=2),
        market_close_time=GENERATED_AT + timedelta(minutes=20),
    )
    report = _report(candidate)

    payload = market_outcome_freshness_recheck_priority_report_to_json(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["total_unresolved_outcome_gap"] == "1"
    assert payload["max_outcome_freshness_age_seconds"] == "7200"
    assert payload["min_close_time_delta_seconds"] == "1200"
    assert payload["rows"][0]["priority_rank"] == "1"
    assert payload["rows"][0]["expected_outcome_count"] == "2"
    assert payload["rows"][0]["outcome_freshness_age_seconds"] == "7200"
    assert payload["rows"][0]["close_time_pressure_seconds"] == "6000"
    assert payload["rows"][0]["last_outcome_checked_at"] == (
        "2026-07-02T10:00:00+00:00"
    )
    json.dumps(payload)
    _assert_json_safe(payload)


def test_recheck_priority_module_source_has_no_float_type_surface():
    source = Path(
        "src/polymarket_alpha_lab/market_outcome_freshness_recheck_priority_report.py",
    ).read_text()

    assert "float" not in source


def _assert_json_safe(value):
    if isinstance(value, dict):
        for nested in value.values():
            _assert_json_safe(nested)
        return
    if isinstance(value, list):
        for nested in value:
            _assert_json_safe(nested)
        return
    assert type(value) is not Decimal
    assert type(value) is not datetime
    assert type(value) is not float
