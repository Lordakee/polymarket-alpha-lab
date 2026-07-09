from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json

import pytest

import polymarket_alpha_lab.research_event_resolution_signal_timeliness_report as api
from polymarket_alpha_lab.research_event_resolution_signal_timeliness_report import (
    EventResolutionSignalTimelinessConfig,
    EventResolutionSignalTimelinessInput,
    EventResolutionSignalTimelinessReport,
    EventResolutionSignalTimelinessRow,
    build_research_event_resolution_signal_timeliness_report,
    research_event_resolution_signal_timeliness_report_json,
    research_event_resolution_signal_timeliness_report_payload,
)


NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _signal(
    *,
    resolution_key: str = "resolution_a",
    latest_signal_at: datetime | None = None,
    expected_update_cadence_seconds: Decimal = Decimal("3600.000000"),
    authority_tier: str = "official",
    contradiction_pressure: Decimal = Decimal("0.050000"),
    ambiguity_risk: Decimal = Decimal("0.050000"),
    verification_coverage: Decimal = Decimal("0.900000"),
    resolution_deadline_at: datetime | None = None,
) -> EventResolutionSignalTimelinessInput:
    return EventResolutionSignalTimelinessInput(
        resolution_key=resolution_key,
        latest_signal_at=latest_signal_at or NOW - timedelta(minutes=5),
        expected_update_cadence_seconds=expected_update_cadence_seconds,
        authority_tier=authority_tier,
        contradiction_pressure=contradiction_pressure,
        ambiguity_risk=ambiguity_risk,
        verification_coverage=verification_coverage,
        resolution_deadline_at=resolution_deadline_at or NOW + timedelta(days=7),
    )


def _report(
    signals: tuple[EventResolutionSignalTimelinessInput, ...],
    *,
    config: EventResolutionSignalTimelinessConfig | None = None,
) -> EventResolutionSignalTimelinessReport:
    return build_research_event_resolution_signal_timeliness_report(
        signals,
        generated_at=NOW,
        config=config,
    )


def test_triages_resolution_signal_timeliness_pass_watch_and_block() -> None:
    report = _report(
        (
            _signal(resolution_key="resolution_pass"),
            _signal(
                resolution_key="resolution_watch",
                latest_signal_at=NOW - timedelta(minutes=75),
                authority_tier="primary",
                verification_coverage=Decimal("0.700000"),
            ),
            _signal(
                resolution_key="resolution_block",
                latest_signal_at=NOW - timedelta(hours=3),
                contradiction_pressure=Decimal("0.750000"),
                ambiguity_risk=Decimal("0.800000"),
                verification_coverage=Decimal("0.200000"),
                resolution_deadline_at=NOW + timedelta(minutes=30),
            ),
        ),
    )

    statuses = {row.resolution_key: row.timeliness_status for row in report.rows}
    assert statuses == {
        "resolution_block": "block",
        "resolution_pass": "pass",
        "resolution_watch": "watch",
    }
    block_row = next(row for row in report.rows if row.resolution_key == "resolution_block")
    watch_row = next(row for row in report.rows if row.resolution_key == "resolution_watch")
    pass_row = next(row for row in report.rows if row.resolution_key == "resolution_pass")

    assert report.status == "block"
    assert report.signal_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert pass_row.latest_signal_age_seconds == Decimal("300.000000")
    assert pass_row.age_to_cadence_ratio == Decimal("0.083333")
    assert pass_row.timeliness_score == Decimal("0.920833")
    assert "fresh_authoritative_signal" in pass_row.reason_codes
    assert watch_row.age_to_cadence_ratio == Decimal("1.250000")
    assert "signal_age_watch" in watch_row.reason_codes
    assert block_row.deadline_proximity_seconds == Decimal("1800.000000")
    assert "signal_age_block" in block_row.reason_codes
    assert "deadline_critical" in block_row.reason_codes


def test_payload_serializes_decimals_deterministically_and_validates_digest() -> None:
    report = _report((_signal(),))

    payload = research_event_resolution_signal_timeliness_report_payload(report)
    encoded = research_event_resolution_signal_timeliness_report_json(report)
    assert encoded == json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    json.dumps(payload, sort_keys=True)
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["latest_signal_age_seconds"] == "300.000000"
    assert payload["generated_at"] == "2026-01-01T12:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(
            digest_payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert report.derived_validation_digest == expected_digest
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)


def test_dataclasses_are_frozen_and_digest_rejects_tampering() -> None:
    report = _report((_signal(),))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadRow(EventResolutionSignalTimelinessRow):
            pass

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="paper_only"):
        EventResolutionSignalTimelinessConfig(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(_signal(), readonly=False)


def test_public_payload_excludes_unsafe_surfaces_and_io_dependencies() -> None:
    unsafe_terms = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    report = _report((_signal(),))
    payload = research_event_resolution_signal_timeliness_report_payload(report)

    _assert_no_unsafe_public_terms(payload, unsafe_terms)
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        EventResolutionSignalTimelinessConfig,
        EventResolutionSignalTimelinessInput,
        EventResolutionSignalTimelinessRow,
        EventResolutionSignalTimelinessReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    with pytest.raises(ValueError, match="unsafe public"):
        _signal(resolution_key="candidate_123")

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


def _assert_no_unsafe_public_terms(value: object, unsafe_terms: tuple[str, ...]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(term in lowered for term in unsafe_terms)
            _assert_no_unsafe_public_terms(item, unsafe_terms)
        return
    if isinstance(value, list):
        for item in value:
            _assert_no_unsafe_public_terms(item, unsafe_terms)
        return
    if isinstance(value, str):
        lowered = value.lower()
        assert "://" not in lowered
        assert not any(term in lowered for term in unsafe_terms)
