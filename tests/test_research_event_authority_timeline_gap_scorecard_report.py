from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_event_authority_timeline_gap_scorecard_report as api
from polymarket_alpha_lab.research_event_authority_timeline_gap_scorecard_report import (
    ResearchEventAuthorityTimelineGapObservation,
    ResearchEventAuthorityTimelineGapScorecardConfig,
    ResearchEventAuthorityTimelineGapScorecardReport,
    build_research_event_authority_timeline_gap_scorecard_report,
)


NOW = datetime(2026, 2, 3, tzinfo=UTC)


def _observation(
    *,
    event_family: str = "macro_resolution",
    authority_family: str = "official_calendar",
    timeline_gap_minutes: Decimal = Decimal("30.000000"),
    authority_confidence_score: Decimal = Decimal("0.900000"),
    authority_coverage_score: Decimal = Decimal("0.800000"),
    conflicting_authority_count: Decimal = Decimal("0.000000"),
) -> ResearchEventAuthorityTimelineGapObservation:
    return ResearchEventAuthorityTimelineGapObservation(
        event_family=event_family,
        authority_family=authority_family,
        observed_at=NOW,
        timeline_gap_minutes=timeline_gap_minutes,
        authority_confidence_score=authority_confidence_score,
        authority_coverage_score=authority_coverage_score,
        conflicting_authority_count=conflicting_authority_count,
    )


def _report(
    observations: tuple[ResearchEventAuthorityTimelineGapObservation, ...],
    *,
    config: ResearchEventAuthorityTimelineGapScorecardConfig | None = None,
) -> ResearchEventAuthorityTimelineGapScorecardReport:
    return build_research_event_authority_timeline_gap_scorecard_report(
        observations,
        generated_at=NOW,
        config=config,
    )


def test_scorecard_aggregates_pass_watch_and_block_rows() -> None:
    report = _report(
        (
            _observation(
                event_family="gamma_resolution",
                authority_family="official_notice",
                timeline_gap_minutes=Decimal("300.000000"),
                authority_confidence_score=Decimal("0.400000"),
                authority_coverage_score=Decimal("0.500000"),
                conflicting_authority_count=Decimal("1.000000"),
            ),
            _observation(
                event_family="alpha_resolution",
                authority_family="official_calendar",
            ),
            _observation(
                event_family="beta_resolution",
                authority_family="official_calendar",
                timeline_gap_minutes=Decimal("180.000000"),
                authority_confidence_score=Decimal("0.800000"),
                authority_coverage_score=Decimal("0.750000"),
            ),
        ),
    )

    assert report.status == "block"
    assert report.row_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert report.event_family_count == Decimal("3.000000")
    assert report.authority_family_count == Decimal("2.000000")
    assert report.average_gap_score == Decimal("0.502778")
    assert report.max_timeline_gap_minutes == Decimal("300.000000")
    assert tuple(row.event_family for row in report.rows) == (
        "alpha_resolution",
        "beta_resolution",
        "gamma_resolution",
    )
    assert tuple(row.status for row in report.rows) == ("pass", "watch", "block")
    assert report.rows[0].gap_score == Decimal("0.858333")
    assert report.rows[1].gap_score == Decimal("0.600000")
    assert report.rows[2].gap_score == Decimal("0.050000")
    assert report.reason_codes == (
        "authority_timeline_pass",
        "timeline_gap_watch",
        "timeline_gap_block",
        "low_authority_confidence",
        "low_authority_coverage",
        "conflicting_authority_block",
    )


def test_payload_is_deterministic_json_safe_and_decimal_string_only() -> None:
    report = _report(
        (
            _observation(event_family="beta_resolution"),
            _observation(event_family="alpha_resolution"),
        ),
    )

    payload = report.payload
    assert json.dumps(payload, ensure_ascii=True, sort_keys=True)
    assert payload["generated_at"] == "2026-02-03T00:00:00+00:00"
    assert payload["row_count"] == "2.000000"
    assert payload["rows"][0]["timeline_gap_minutes"] == "30.000000"
    assert payload["rows"][0]["gap_score"] == "0.858333"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    assert payload == report.payload
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)


def test_dataclasses_are_frozen_and_hard_flags_are_enforced() -> None:
    report = _report((_observation(),))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchEventAuthorityTimelineGapScorecardConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ResearchEventAuthorityTimelineGapScorecardConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        ResearchEventAuthorityTimelineGapObservation(
            event_family="macro_resolution",
            authority_family="official_calendar",
            observed_at=NOW,
            timeline_gap_minutes=Decimal("30.000000"),
            authority_confidence_score=Decimal("0.900000"),
            authority_coverage_score=Decimal("0.800000"),
            conflicting_authority_count=Decimal("0.000000"),
            report_only=False,
        )

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = _report((_observation(),))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, generated_at=datetime(2026, 2, 3, 1, tzinfo=UTC))

    payload_tampered_report = _report((_observation(),))
    object.__setattr__(
        payload_tampered_report,
        "row_count",
        Decimal("2.000000"),
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        payload_tampered_report.payload

    nested_payload_tampered_report = _report((_observation(),))
    object.__setattr__(
        nested_payload_tampered_report.rows[0],
        "gap_score",
        Decimal("0.123456"),
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        nested_payload_tampered_report.payload


def test_rejects_unsafe_public_values_and_surfaces() -> None:
    for unsafe_value in (
        "candidate_alpha",
        "market_alpha",
        "alpha_slug",
        "question_alpha",
        "https://example.invalid/item",
        "source_url",
        "raw_text",
        "dsn_value",
        "table_name",
        "token_value",
        "wallet_value",
        "order_value",
        "trade_value",
        "recommendation_value",
        "sizing_value",
        "live_value",
        "auth_value",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            _observation(event_family=unsafe_value)

    unsafe_terms = (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "recommendation",
        "sizing",
        "live",
        "network",
        "database",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ResearchEventAuthorityTimelineGapScorecardConfig,
        ResearchEventAuthorityTimelineGapObservation,
        api.ResearchEventAuthorityTimelineGapScorecardRow,
        ResearchEventAuthorityTimelineGapScorecardReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

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
