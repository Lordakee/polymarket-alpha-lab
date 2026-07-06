from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import inspect
import json

import pytest

import polymarket_alpha_lab.research_packet_source_timeliness_exception_queue_v2 as api
from polymarket_alpha_lab.research_packet_source_timeliness_exception_queue_v2 import (
    ResearchPacketSourceTimelinessExceptionQueueConfig,
    ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem,
    ResearchPacketSourceTimelinessExceptionQueueReport,
    ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot,
    build_research_packet_source_timeliness_exception_queue_v2_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)
UNSAFE_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)


def _source(
    *,
    source_id: str = "source_a",
    age_seconds: int = 600,
    expected_refresh_seconds: Decimal = Decimal("3600.000000"),
    urgent_refresh_requested: bool = False,
) -> ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot:
    return ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot(
        packet_id="packet_a",
        source_id=source_id,
        observed_at=NOW - timedelta(seconds=age_seconds),
        expected_refresh_seconds=expected_refresh_seconds,
        urgent_refresh_requested=urgent_refresh_requested,
    )


def _report(
    *sources: ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot,
    config: ResearchPacketSourceTimelinessExceptionQueueConfig | None = None,
    public_payload: tuple[
        ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem,
        ...,
    ] = (),
) -> ResearchPacketSourceTimelinessExceptionQueueReport:
    return build_research_packet_source_timeliness_exception_queue_v2_report(
        sources,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_timeliness_exception_queue_scores_and_ranks_refresh_need() -> None:
    report = _report(
        _source(source_id="source_fresh", age_seconds=600),
        _source(source_id="source_stale", age_seconds=7200),
        _source(
            source_id="source_urgent",
            age_seconds=7200,
            urgent_refresh_requested=True,
        ),
    )

    assert report.queue_status == "urgent"
    assert report.source_count == Decimal("3.000000")
    assert report.current_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.urgent_count == Decimal("1.000000")
    assert report.max_timeliness_exception_score == Decimal("0.850000")
    assert report.average_timeliness_exception_score == Decimal("0.483333")
    assert tuple(row.source_id for row in report.rows) == (
        "source_urgent",
        "source_stale",
        "source_fresh",
    )

    urgent = report.rows[0]
    assert urgent.rank == Decimal("1.000000")
    assert urgent.age_seconds == Decimal("7200.000000")
    assert urgent.overdue_seconds == Decimal("3600.000000")
    assert urgent.stale_age_ratio == Decimal("1.000000")
    assert urgent.stale_source_penalty == Decimal("0.600000")
    assert urgent.urgent_refresh_boost == Decimal("0.250000")
    assert urgent.timeliness_exception_score == Decimal("0.850000")
    assert urgent.queue_state == "urgent"
    assert urgent.reason_codes == (
        "source_stale_penalty",
        "urgent_refresh_requested",
        "urgent_refresh_boost",
        "timeliness_exception_urgent",
    )

    stale = report.rows[1]
    assert stale.rank == Decimal("2.000000")
    assert stale.stale_source_penalty == Decimal("0.600000")
    assert stale.urgent_refresh_boost == Decimal("0.000000")
    assert stale.timeliness_exception_score == Decimal("0.600000")
    assert stale.queue_state == "watch"
    assert stale.reason_codes == (
        "source_stale_penalty",
        "timeliness_exception_watch",
    )

    fresh = report.rows[2]
    assert fresh.rank == Decimal("3.000000")
    assert fresh.age_seconds == Decimal("600.000000")
    assert fresh.overdue_seconds == Decimal("0.000000")
    assert fresh.timeliness_exception_score == Decimal("0.000000")
    assert fresh.queue_state == "current"
    assert fresh.reason_codes == (
        "source_timely",
        "timeliness_exception_current",
    )


def test_payload_serializes_decimal_strings_and_rejects_non_decimal_numbers() -> None:
    report = _report(
        _source(
            source_id="source_urgent",
            age_seconds=7200,
            urgent_refresh_requested=True,
        ),
        public_payload=(
            ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem(
                "safe_key",
                "safe value",
            ),
        ),
    )

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["source_count"] == "1.000000"
    assert payload["urgent_count"] == "1.000000"
    assert payload["max_timeliness_exception_score"] == "0.850000"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["rows"][0]["age_seconds"] == "7200.000000"
    assert payload["rows"][0]["stale_source_penalty"] == "0.600000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)

    with pytest.raises(ValueError, match="Decimal"):
        ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot(
            packet_id="packet_a",
            source_id="source_a",
            observed_at=NOW,
            expected_refresh_seconds=3600,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Decimal"):
        ResearchPacketSourceTimelinessExceptionQueueConfig(
            watch_exception_score=0.4,  # type: ignore[arg-type]
        )


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = _report(_source())

    with pytest.raises(FrozenInstanceError):
        report.queue_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchPacketSourceTimelinessExceptionQueueConfig):
            pass


def test_hard_paper_report_readonly_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchPacketSourceTimelinessExceptionQueueConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot(
            packet_id="packet_a",
            source_id="source_a",
            observed_at=NOW,
            expected_refresh_seconds=Decimal("3600.000000"),
            report_only=False,
        )

    report = _report(_source())
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = _report(_source())

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem(
                    "safe_key",
                    "changed value",
                ),
            ),
        )


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
    for term in UNSAFE_TERMS:
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem(
                f"{term}_key",
                "safe value",
            )

        with pytest.raises(ValueError, match="unsafe public"):
            ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem(
                "safe_key",
                f"{term} value",
            )

    with pytest.raises(ValueError, match="unsafe public"):
        _source(source_id="trade_signal")


def test_no_unsafe_surfaces_are_exposed() -> None:
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in UNSAFE_TERMS)

    for cls in (
        ResearchPacketSourceTimelinessExceptionQueueConfig,
        ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot,
        ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem,
        api.ResearchPacketSourceTimelinessExceptionQueueRow,
        ResearchPacketSourceTimelinessExceptionQueueReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in UNSAFE_TERMS)

    for parameter in inspect.signature(
        build_research_packet_source_timeliness_exception_queue_v2_report,
    ).parameters:
        lowered = parameter.lower()
        assert not any(term in lowered for term in UNSAFE_TERMS)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
