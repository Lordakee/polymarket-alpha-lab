from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.probability_event_resolution_timeline_compression_report as api
from polymarket_alpha_lab.probability_event_resolution_timeline_compression_report import (
    ProbabilityEventResolutionTimelineCompressionInput,
    ProbabilityEventResolutionTimelineCompressionReport,
    build_probability_event_resolution_timeline_compression_report,
)


def _input(
    *,
    market_close_hours: Decimal = Decimal("12.000000"),
    next_catalyst_hours: Decimal = Decimal("4.000000"),
    review_sla_hours: Decimal = Decimal("2.000000"),
    source_refresh_sla_hours: Decimal = Decimal("1.000000"),
    manual_decision_sla_hours: Decimal = Decimal("3.000000"),
) -> ProbabilityEventResolutionTimelineCompressionInput:
    return ProbabilityEventResolutionTimelineCompressionInput(
        market_close_hours=market_close_hours,
        next_catalyst_hours=next_catalyst_hours,
        review_sla_hours=review_sla_hours,
        source_refresh_sla_hours=source_refresh_sla_hours,
        manual_decision_sla_hours=manual_decision_sla_hours,
    )


def _report(
    item: ProbabilityEventResolutionTimelineCompressionInput,
) -> ProbabilityEventResolutionTimelineCompressionReport:
    return build_probability_event_resolution_timeline_compression_report(item)


def test_builds_open_compression_report_from_catalyst_critical_path() -> None:
    report = _report(_input())

    assert report.compression_status == "open"
    assert report.critical_path_hours == Decimal("1.000000")
    assert report.reason_codes == ("catalyst_before_close", "source_refresh_path")
    assert report.manual_next_step == "refresh_public_sources_before_next_review"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert report.public_payload["compression_status"] == "open"
    assert report.public_payload["critical_path_hours"] == "1.000000"
    assert report.public_payload["reason_codes"] == [
        "catalyst_before_close",
        "source_refresh_path",
    ]
    assert report.public_payload["paper_only"] is True
    assert report.public_payload["report_only"] is True
    assert report.public_payload["readonly"] is True
    assert report.public_payload["payload_digest"] == report.payload_digest
    assert len(report.payload_digest) == 64
    json.dumps(report.public_payload, sort_keys=True)
    _assert_no_decimal_objects(report.public_payload)
    _assert_no_non_decimal_public_numbers(report)


def test_statuses_follow_close_catalyst_and_manual_decision_windows() -> None:
    already_closed = _report(
        _input(
            market_close_hours=Decimal("0.000000"),
            next_catalyst_hours=Decimal("2.000000"),
        ),
    )
    assert already_closed.compression_status == "closed"
    assert already_closed.critical_path_hours == Decimal("0.000000")
    assert already_closed.reason_codes == ("market_close_elapsed",)
    assert already_closed.manual_next_step == "archive_report_only_resolution_timeline"

    decision_due = _report(
        _input(
            market_close_hours=Decimal("8.000000"),
            next_catalyst_hours=Decimal("3.000000"),
            review_sla_hours=Decimal("5.000000"),
            source_refresh_sla_hours=Decimal("4.000000"),
            manual_decision_sla_hours=Decimal("1.500000"),
        ),
    )
    assert decision_due.compression_status == "compressed"
    assert decision_due.critical_path_hours == Decimal("1.500000")
    assert decision_due.reason_codes == (
        "catalyst_before_close",
        "manual_decision_path",
    )
    assert decision_due.manual_next_step == "prepare_manual_resolution_decision_packet"

    close_watch = _report(
        _input(
            market_close_hours=Decimal("2.000000"),
            next_catalyst_hours=Decimal("6.000000"),
            review_sla_hours=Decimal("5.000000"),
            source_refresh_sla_hours=Decimal("4.000000"),
            manual_decision_sla_hours=Decimal("3.000000"),
        ),
    )
    assert close_watch.compression_status == "compressed"
    assert close_watch.critical_path_hours == Decimal("2.000000")
    assert close_watch.reason_codes == ("close_before_catalyst", "market_close_path")
    assert close_watch.manual_next_step == "escalate_manual_review_before_market_close"


def test_public_payload_and_digest_are_deterministic_and_tamper_evident() -> None:
    report = _report(_input())
    same_report = _report(_input())

    assert report.public_payload == same_report.public_payload
    assert report.payload_digest == same_report.payload_digest

    with pytest.raises(ValueError, match="payload_digest"):
        replace(report, payload_digest="0" * 64)

    with pytest.raises(ValueError, match="critical_path_hours"):
        replace(report, critical_path_hours=Decimal("2.000000"))


def test_frozen_dataclasses_and_hard_readonly_flags_are_enforced() -> None:
    report = _report(_input())

    with pytest.raises(FrozenInstanceError):
        report.compression_status = "closed"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventResolutionTimelineCompressionInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventResolutionTimelineCompressionReport):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ProbabilityEventResolutionTimelineCompressionInput(
            market_close_hours=Decimal("1.000000"),
            next_catalyst_hours=Decimal("1.000000"),
            review_sla_hours=Decimal("1.000000"),
            source_refresh_sla_hours=Decimal("1.000000"),
            manual_decision_sla_hours=Decimal("1.000000"),
            paper_only=False,
        )

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_decimal_only_inputs_and_nonnegative_hours_are_enforced() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        _input(market_close_hours=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="finite"):
        _input(next_catalyst_hours=Decimal("NaN"))

    with pytest.raises(ValueError, match="nonnegative"):
        _input(review_sla_hours=Decimal("-0.000001"))


def test_no_unsafe_public_surfaces_or_capability_imports_are_exposed() -> None:
    forbidden_public_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "key",
        "sign",
        "signature",
        "execute",
        "execution",
        "jsonl",
        "persist",
        "file",
    )
    allowed_public_names = {
        "ProbabilityEventResolutionTimelineCompressionInput",
        "ProbabilityEventResolutionTimelineCompressionReport",
        "build_probability_event_resolution_timeline_compression_report",
    }

    assert set(api.__all__) == allowed_public_names
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_public_terms)

    for cls in (
        ProbabilityEventResolutionTimelineCompressionInput,
        ProbabilityEventResolutionTimelineCompressionReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_public_terms)

    for forbidden_name in (
        "open",
        "Path",
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
    if type(value) is bool or value is None or isinstance(value, str):
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
