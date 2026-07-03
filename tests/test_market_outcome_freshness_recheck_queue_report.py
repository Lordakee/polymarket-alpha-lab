from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from json import dumps
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_outcome_freshness_recheck_queue_report import (
    MarketOutcomeFreshnessObservation,
    MarketOutcomeFreshnessRecheckQueueConfig,
    MarketOutcomeFreshnessRecheckQueueReport,
    MarketOutcomeFreshnessRecheckQueueRow,
    MarketOutcomeFreshnessRecheckReasonCodeCount,
    build_market_outcome_freshness_recheck_queue_report,
    market_outcome_freshness_recheck_queue_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 18, 0, tzinfo=UTC)
BASE_CLOSED_AT = datetime(2026, 7, 2, 16, 0, tzinfo=UTC)


class _FloatSubclass(float):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def test_empty_input_is_deterministic_report_only_clear_summary() -> None:
    report = build_market_outcome_freshness_recheck_queue_report(
        (),
        config=MarketOutcomeFreshnessRecheckQueueConfig(),
        generated_at=GENERATED_AT,
    )

    assert report == MarketOutcomeFreshnessRecheckQueueReport(
        generated_at=GENERATED_AT,
        config_version="market-outcome-freshness-recheck-queue-v0",
        queue_status="clear",
        market_count=Decimal("0"),
        queued_count=Decimal("0"),
        clear_count=Decimal("0"),
        queued_ratio=Decimal("0.000000"),
        stale_official_source_after_seconds=Decimal("900"),
        priority_close_age_seconds=Decimal("3600"),
        rows=(),
        reason_code_counts=(),
        reason_codes=(),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_queues_outcome_freshness_rechecks_with_deterministic_priority_and_reasons() -> None:
    report = build_market_outcome_freshness_recheck_queue_report(
        (
            _observation(
                "market-stale",
                "gamma",
                outcome="yes",
                official_source_checked_at=GENERATED_AT - timedelta(minutes=45),
                proxy_outcome="yes",
                acknowledged_at=GENERATED_AT - timedelta(minutes=5),
                closed_at=GENERATED_AT - timedelta(minutes=50),
            ),
            _observation(
                "market-clear",
                "alpha",
                outcome="yes",
                official_source_checked_at=GENERATED_AT - timedelta(minutes=3),
                proxy_outcome="yes",
                acknowledged_at=GENERATED_AT - timedelta(minutes=2),
                closed_at=GENERATED_AT - timedelta(minutes=10),
            ),
            _observation(
                "market-urgent",
                "beta",
                outcome=None,
                official_source_checked_at=GENERATED_AT - timedelta(minutes=20),
                proxy_outcome="no",
                acknowledged_at=None,
                closed_at=GENERATED_AT - timedelta(hours=3),
            ),
            _observation(
                "market-contradiction",
                "delta",
                outcome="yes",
                official_source_checked_at=GENERATED_AT - timedelta(minutes=1),
                proxy_outcome="no",
                acknowledged_at=GENERATED_AT - timedelta(minutes=1),
                closed_at=GENERATED_AT - timedelta(hours=2),
            ),
        ),
        config=MarketOutcomeFreshnessRecheckQueueConfig(
            stale_official_source_after_seconds=Decimal("900"),
            priority_close_age_seconds=Decimal("3600"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.queue_status == "queued"
    assert report.market_count == Decimal("4")
    assert report.queued_count == Decimal("3")
    assert report.clear_count == Decimal("1")
    assert report.queued_ratio == Decimal("0.750000")
    assert report.reason_codes == (
        "missing_outcome",
        "stale_official_source",
        "proxy_contradiction",
        "missing_acknowledgement",
        "close_age_priority",
    )
    assert report.reason_code_counts == (
        MarketOutcomeFreshnessRecheckReasonCodeCount(
            reason_code="missing_outcome",
            count=Decimal("1"),
        ),
        MarketOutcomeFreshnessRecheckReasonCodeCount(
            reason_code="stale_official_source",
            count=Decimal("2"),
        ),
        MarketOutcomeFreshnessRecheckReasonCodeCount(
            reason_code="proxy_contradiction",
            count=Decimal("1"),
        ),
        MarketOutcomeFreshnessRecheckReasonCodeCount(
            reason_code="missing_acknowledgement",
            count=Decimal("1"),
        ),
        MarketOutcomeFreshnessRecheckReasonCodeCount(
            reason_code="close_age_priority",
            count=Decimal("2"),
        ),
    )
    assert report.rows == (
        MarketOutcomeFreshnessRecheckQueueRow(
            market_id="market-urgent",
            market_slug="beta",
            closed_at=GENERATED_AT - timedelta(hours=3),
            close_age_seconds=Decimal("10800"),
            official_source_checked_at=GENERATED_AT - timedelta(minutes=20),
            official_source_age_seconds=Decimal("1200"),
            queue_status="queued",
            priority_status="urgent",
            priority_rank=Decimal("1"),
            reason_codes=(
                "missing_outcome",
                "stale_official_source",
                "missing_acknowledgement",
                "close_age_priority",
            ),
        ),
        MarketOutcomeFreshnessRecheckQueueRow(
            market_id="market-contradiction",
            market_slug="delta",
            closed_at=GENERATED_AT - timedelta(hours=2),
            close_age_seconds=Decimal("7200"),
            official_source_checked_at=GENERATED_AT - timedelta(minutes=1),
            official_source_age_seconds=Decimal("60"),
            queue_status="queued",
            priority_status="urgent",
            priority_rank=Decimal("1"),
            reason_codes=("proxy_contradiction", "close_age_priority"),
        ),
        MarketOutcomeFreshnessRecheckQueueRow(
            market_id="market-stale",
            market_slug="gamma",
            closed_at=GENERATED_AT - timedelta(minutes=50),
            close_age_seconds=Decimal("3000"),
            official_source_checked_at=GENERATED_AT - timedelta(minutes=45),
            official_source_age_seconds=Decimal("2700"),
            queue_status="queued",
            priority_status="standard",
            priority_rank=Decimal("3"),
            reason_codes=("stale_official_source",),
        ),
    )


def test_aware_datetimes_are_normalized_to_utc_for_age_seconds() -> None:
    closed_at = datetime(2026, 7, 2, 10, 30, tzinfo=timezone(timedelta(hours=-4)))
    checked_at = datetime(2026, 7, 2, 13, 45, tzinfo=timezone(timedelta(hours=-4)))

    report = build_market_outcome_freshness_recheck_queue_report(
        (
            MarketOutcomeFreshnessObservation(
                market_id="market-timezone",
                market_slug="timezone-market",
                closed_at=closed_at,
                outcome="yes",
                official_source_checked_at=checked_at,
                proxy_outcome="yes",
                acknowledged_at=None,
            ),
        ),
        config=MarketOutcomeFreshnessRecheckQueueConfig(
            stale_official_source_after_seconds=Decimal("120"),
            priority_close_age_seconds=Decimal("10000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.rows[0].closed_at == datetime(2026, 7, 2, 14, 30, tzinfo=UTC)
    assert report.rows[0].official_source_checked_at == datetime(
        2026,
        7,
        2,
        17,
        45,
        tzinfo=UTC,
    )
    assert report.rows[0].close_age_seconds == Decimal("12600")
    assert report.rows[0].official_source_age_seconds == Decimal("900")


def test_payload_helper_is_json_ready_decimal_stringified_and_has_no_live_surface() -> None:
    report = build_market_outcome_freshness_recheck_queue_report(
        (
            _observation(
                "market-payload",
                "payload-market",
                outcome=None,
                official_source_checked_at=None,
                proxy_outcome=None,
                acknowledged_at=None,
                closed_at=GENERATED_AT - timedelta(hours=2),
            ),
        ),
        config=MarketOutcomeFreshnessRecheckQueueConfig(),
        generated_at=GENERATED_AT,
    )

    payload = market_outcome_freshness_recheck_queue_payload(report)

    assert payload["generated_at"] == "2026-07-02T18:00:00+00:00"
    assert payload["market_count"] == "1"
    assert payload["queued_ratio"] == "1.000000"
    assert payload["rows"][0]["close_age_seconds"] == "7200"
    assert payload["rows"][0]["official_source_age_seconds"] is None
    assert payload["reason_code_counts"][0]["count"] == "1"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_paths(payload) == ()
    dumps(payload)

    payload_text = repr(payload).lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "advice",
    ):
        assert forbidden not in payload_text


def test_inputs_are_frozen_and_reject_false_flags_naive_datetimes_and_floats() -> None:
    observation = _observation(
        "market-frozen",
        "frozen-market",
        outcome="yes",
        official_source_checked_at=GENERATED_AT,
        proxy_outcome="yes",
        acknowledged_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        observation.market_id = "other-market"  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly"):
        replace(observation, readonly=False)

    with pytest.raises(ValueError, match="report_only"):
        MarketOutcomeFreshnessRecheckQueueConfig(report_only=False)

    with pytest.raises(ValueError, match="timezone-aware"):
        MarketOutcomeFreshnessObservation(
            market_id="market-naive",
            market_slug="naive-market",
            closed_at=datetime(2026, 7, 2, 16, 0),
            outcome=None,
            official_source_checked_at=None,
            proxy_outcome=None,
            acknowledged_at=None,
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        MarketOutcomeFreshnessObservation(
            market_id="market-none-offset-tz",
            market_slug="none-offset-tz-market",
            closed_at=datetime(2026, 7, 2, 16, 0, tzinfo=_NoneOffsetTz()),
            outcome=None,
            official_source_checked_at=None,
            proxy_outcome=None,
            acknowledged_at=None,
        )

    with pytest.raises(ValueError, match="Decimal"):
        MarketOutcomeFreshnessRecheckQueueConfig(
            stale_official_source_after_seconds=_FloatSubclass(1.5),
        )


def test_module_source_has_no_float_type_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_outcome_freshness_recheck_queue_report.py",
    ).read_text()

    assert "float" not in source


def _observation(
    market_id: str,
    market_slug: str,
    *,
    outcome: str | None,
    official_source_checked_at: datetime | None,
    proxy_outcome: str | None,
    acknowledged_at: datetime | None,
    closed_at: datetime | None = None,
) -> MarketOutcomeFreshnessObservation:
    return MarketOutcomeFreshnessObservation(
        market_id=market_id,
        market_slug=market_slug,
        closed_at=BASE_CLOSED_AT if closed_at is None else closed_at,
        outcome=outcome,
        official_source_checked_at=official_source_checked_at,
        proxy_outcome=proxy_outcome,
        acknowledged_at=acknowledged_at,
    )


def _float_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if isinstance(value, float):
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            item_prefix = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_float_paths(item, item_prefix))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, item in enumerate(value):
            item_prefix = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_float_paths(item, item_prefix))
        return tuple(paths)
    return ()
