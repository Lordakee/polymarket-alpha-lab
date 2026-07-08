from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_event_resolution_confidence_ladder_report as api
from polymarket_alpha_lab.research_event_resolution_confidence_ladder_report import (
    ResearchEventResolutionConfidenceLadderConfig,
    ResearchEventResolutionConfidenceLadderPublicPayloadItem,
    ResearchEventResolutionConfidenceLadderReport,
    ResearchEventResolutionConfidenceLadderRow,
    ResearchEventResolutionConfidenceSignal,
    build_research_event_resolution_confidence_ladder_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _signal(
    *,
    event_id: str = "event_a",
    official_evidence_score: Decimal = Decimal("0.900000"),
    alternative_evidence_score: Decimal = Decimal("0.700000"),
    dispute_risk_score: Decimal = Decimal("0.100000"),
    freshness_score: Decimal = Decimal("0.900000"),
    review_status: str = "reviewed",
    observed_at: datetime = NOW - timedelta(hours=1),
) -> ResearchEventResolutionConfidenceSignal:
    return ResearchEventResolutionConfidenceSignal(
        event_id=event_id,
        official_evidence_score=official_evidence_score,
        alternative_evidence_score=alternative_evidence_score,
        dispute_risk_score=dispute_risk_score,
        freshness_score=freshness_score,
        review_status=review_status,
        observed_at=observed_at,
    )


def _report(
    signals: tuple[ResearchEventResolutionConfidenceSignal, ...],
    *,
    config: ResearchEventResolutionConfidenceLadderConfig | None = None,
    public_payload: tuple[ResearchEventResolutionConfidenceLadderPublicPayloadItem, ...] = (),
) -> ResearchEventResolutionConfidenceLadderReport:
    return build_research_event_resolution_confidence_ladder_report(
        signals,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_resolution_confidence_ladder_passes_confirmed_events() -> None:
    report = _report((_signal(),))

    row = report.rows[0]
    assert report.ladder_status == "pass"
    assert report.event_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert report.average_resolution_confidence_score == Decimal("0.790000")
    assert row.event_id == "event_a"
    assert row.ladder_status == "pass"
    assert row.resolution_confidence_score == Decimal("0.790000")
    assert row.review_status == "reviewed"
    assert "resolution_confidence_pass" in row.reason_codes
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_ladder_watches_pending_review_and_weak_alternative_evidence() -> None:
    report = _report(
        (
            _signal(
                alternative_evidence_score=Decimal("0.300000"),
                review_status="pending",
            ),
        ),
    )

    row = report.rows[0]
    assert report.ladder_status == "watch"
    assert report.watch_count == Decimal("1.000000")
    assert row.ladder_status == "watch"
    assert "alternative_evidence_gap" in row.reason_codes
    assert "review_pending_watch" in row.reason_codes
    assert "resolution_confidence_pass" not in row.reason_codes


def test_ladder_blocks_high_dispute_risk_and_unreviewed_events() -> None:
    report = _report(
        (
            _signal(
                event_id="event_blocked",
                dispute_risk_score=Decimal("0.920000"),
                review_status="unreviewed",
            ),
        ),
    )

    row = report.rows[0]
    assert report.ladder_status == "block"
    assert report.block_count == Decimal("1.000000")
    assert row.ladder_status == "block"
    assert "dispute_risk_block" in row.reason_codes
    assert "review_unreviewed_block" in row.reason_codes


def test_empty_signal_set_blocks_with_empty_events_reason() -> None:
    report = _report(())

    assert report.ladder_status == "block"
    assert report.event_count == Decimal("0.000000")
    assert report.reason_codes == ("empty_events",)


def test_payload_serializes_decimal_strings_and_excludes_private_surfaces() -> None:
    report = _report(
        (_signal(),),
        public_payload=(
            ResearchEventResolutionConfidenceLadderPublicPayloadItem(
                "safe_key",
                "sanitized summary",
            ),
        ),
    )

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["event_count"] == "1.000000"
    assert payload["average_resolution_confidence_score"] == "0.790000"
    assert payload["rows"][0]["resolution_confidence_score"] == "0.790000"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_forbidden_public_surface(payload)


def test_strict_type_validation_rejects_floats_raw_payloads_and_bad_statuses() -> None:
    with pytest.raises(ValueError, match="official_evidence_score"):
        _signal(official_evidence_score=0.9)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="review_status"):
        _signal(review_status="approved")

    with pytest.raises(ValueError, match="timezone-aware"):
        build_research_event_resolution_confidence_ladder_report(
            (_signal(),),
            generated_at=datetime(2026, 1, 1),
        )

    with pytest.raises(ValueError, match="observed_at"):
        _report((_signal(observed_at=NOW + timedelta(seconds=1)),))

    for key in ("raw_note", "market_id", "question_id", "source_id", "url", "dsn", "table"):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventResolutionConfidenceLadderPublicPayloadItem(key, "safe value")

    for value in (
        "raw payload",
        "market question",
        "source item",
        "https://example.invalid/item",
        "dsn token",
        "buy this",
        "sell this",
        "trade recommendation",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventResolutionConfidenceLadderPublicPayloadItem("safe_key", value)


def test_dataclasses_are_frozen_reject_subclassing_and_validate_digest() -> None:
    report = _report((_signal(),))

    with pytest.raises(FrozenInstanceError):
        report.ladder_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchEventResolutionConfidenceLadderConfig):
            pass

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=Decimal("2.000000"))


def test_no_unsafe_public_names_or_external_write_surfaces_are_exposed() -> None:
    forbidden_terms = (
        "raw",
        "market",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "buy",
        "sell",
        "trade",
        "recommend",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_terms)

    for cls in (
        ResearchEventResolutionConfidenceLadderConfig,
        ResearchEventResolutionConfidenceSignal,
        ResearchEventResolutionConfidenceLadderPublicPayloadItem,
        ResearchEventResolutionConfidenceLadderRow,
        ResearchEventResolutionConfidenceLadderReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_terms)

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


def _assert_no_forbidden_public_surface(value: object) -> None:
    forbidden_terms = (
        "raw",
        "market",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "buy",
        "sell",
        "trade",
        "recommend",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(term in lowered_key for term in forbidden_terms)
            _assert_no_forbidden_public_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_no_forbidden_public_surface(item)
        return
    if isinstance(value, str):
        lowered = value.lower()
        assert not any(term in lowered for term in forbidden_terms)
