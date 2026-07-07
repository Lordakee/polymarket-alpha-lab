from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_source_verification_coverage_report as api
from polymarket_alpha_lab.research_source_verification_coverage_report import (
    ResearchSourceVerificationCoverageConfig,
    ResearchSourceVerificationCoverageReport,
    ResearchSourceVerificationCoverageRow,
    ResearchSourceVerificationEvidence,
    ResearchSourceVerificationPublicPayloadItem,
    build_research_source_verification_coverage_report,
)


NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)


def _evidence(
    *,
    event_id: str = "event_alpha",
    evidence_id: str = "evidence_alpha",
    family_id: str = "official",
    observed_delta_minutes: Decimal = Decimal("30.000000"),
    confidence_score: Decimal = Decimal("0.800000"),
    supports_event: bool = True,
    is_official_confirmation: bool = False,
    is_counter_evidence: bool = False,
) -> ResearchSourceVerificationEvidence:
    return ResearchSourceVerificationEvidence(
        event_id=event_id,
        evidence_id=evidence_id,
        family_id=family_id,
        observed_at=NOW - timedelta(minutes=int(observed_delta_minutes)),
        confidence_score=confidence_score,
        supports_event=supports_event,
        is_official_confirmation=is_official_confirmation,
        is_counter_evidence=is_counter_evidence,
    )


def _report(
    evidence: tuple[ResearchSourceVerificationEvidence, ...],
    *,
    config: ResearchSourceVerificationCoverageConfig | None = None,
    public_payload: tuple[ResearchSourceVerificationPublicPayloadItem, ...] = (),
) -> ResearchSourceVerificationCoverageReport:
    return build_research_source_verification_coverage_report(
        evidence,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_passes_when_independent_official_counter_and_fresh_coverage_exist() -> None:
    report = _report(
        (
            _evidence(
                evidence_id="evidence_official",
                family_id="official",
                confidence_score=Decimal("0.900000"),
                is_official_confirmation=True,
            ),
            _evidence(
                evidence_id="evidence_primary",
                family_id="primary",
                confidence_score=Decimal("0.800000"),
            ),
            _evidence(
                evidence_id="evidence_counter",
                family_id="archive",
                observed_delta_minutes=Decimal("45.000000"),
                confidence_score=Decimal("0.600000"),
                supports_event=False,
                is_counter_evidence=True,
            ),
        ),
    )

    row = report.rows[0]
    assert report.coverage_status == "pass"
    assert report.event_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert row.evidence_count == Decimal("3.000000")
    assert row.confirming_evidence_count == Decimal("2.000000")
    assert row.counter_evidence_count == Decimal("1.000000")
    assert row.independent_family_count == Decimal("3.000000")
    assert row.official_confirmation_count == Decimal("1.000000")
    assert row.stale_evidence_count == Decimal("0.000000")
    assert row.max_observed_age_minutes == Decimal("45.000000")
    assert row.verification_score == Decimal("1.000000")
    assert row.coverage_status == "pass"
    assert row.reason_codes == (
        "official_confirmation_present",
        "counter_evidence_present",
        "refresh_current",
        "verification_coverage_pass",
    )
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_watch_reports_missing_official_and_counter_coverage() -> None:
    report = _report(
        (
            _evidence(evidence_id="evidence_alpha", family_id="primary"),
            _evidence(evidence_id="evidence_beta", family_id="secondary"),
        ),
    )

    row = report.rows[0]
    assert report.coverage_status == "watch"
    assert report.watch_count == Decimal("1.000000")
    assert row.coverage_status == "watch"
    assert row.verification_score == Decimal("0.500000")
    assert "missing_official_confirmation" in row.reason_codes
    assert "missing_counter_evidence" in row.reason_codes
    assert "verification_coverage_watch" in row.reason_codes


def test_block_reports_stale_refresh_or_missing_confirming_evidence() -> None:
    stale = _report(
        (
            _evidence(
                evidence_id="evidence_stale",
                family_id="official",
                observed_delta_minutes=Decimal("181.000000"),
                is_official_confirmation=True,
            ),
            _evidence(
                evidence_id="evidence_counter",
                family_id="archive",
                observed_delta_minutes=Decimal("181.000000"),
                supports_event=False,
                is_counter_evidence=True,
            ),
        ),
    )
    no_confirming = _report(
        (
            _evidence(
                evidence_id="evidence_counter",
                family_id="archive",
                supports_event=False,
                is_counter_evidence=True,
            ),
        ),
    )

    assert stale.coverage_status == "block"
    assert stale.rows[0].coverage_status == "block"
    assert stale.rows[0].stale_evidence_count == Decimal("2.000000")
    assert "refresh_stale" in stale.rows[0].reason_codes
    assert "verification_coverage_block" in stale.rows[0].reason_codes
    assert no_confirming.coverage_status == "block"
    assert "missing_confirming_evidence" in no_confirming.rows[0].reason_codes


def test_payload_is_decimal_string_json_ready_sanitized_and_deterministic() -> None:
    ordered = (
        _evidence(
            evidence_id="evidence_official",
            family_id="official",
            is_official_confirmation=True,
        ),
        _evidence(evidence_id="evidence_primary", family_id="primary"),
        _evidence(
            evidence_id="evidence_counter",
            family_id="archive",
            supports_event=False,
            is_counter_evidence=True,
        ),
    )
    report = _report(
        ordered,
        public_payload=(
            ResearchSourceVerificationPublicPayloadItem("review_batch", "jan_2026"),
        ),
    )
    reordered = _report(
        tuple(reversed(ordered)),
        public_payload=(
            ResearchSourceVerificationPublicPayloadItem("review_batch", "jan_2026"),
        ),
    )

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["event_count"] == "1.000000"
    assert payload["average_verification_score"] == "1.000000"
    assert payload["rows"][0]["evidence_count"] == "3.000000"
    assert payload["rows"][0]["max_observed_age_minutes"] == "30.000000"
    assert payload["generated_at"] == "2026-01-01T12:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert report.derived_validation_digest == reordered.derived_validation_digest
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_forbidden_public_surface(payload)


def test_dataclasses_are_frozen_and_reject_subclassing_and_bad_flags() -> None:
    report = _report(
        (
            _evidence(
                evidence_id="evidence_official",
                family_id="official",
                is_official_confirmation=True,
            ),
            _evidence(evidence_id="evidence_primary", family_id="primary"),
            _evidence(
                evidence_id="evidence_counter",
                family_id="archive",
                supports_event=False,
                is_counter_evidence=True,
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.coverage_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchSourceVerificationCoverageConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ResearchSourceVerificationCoverageConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(report.rows[0], report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_strict_types_and_unsafe_inputs_are_rejected() -> None:
    with pytest.raises(ValueError, match="confidence_score must be a Decimal"):
        _evidence(confidence_score=0.8)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="supports_event must be a bool"):
        _evidence(supports_event=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="timezone-aware"):
        ResearchSourceVerificationEvidence(
            event_id="event_alpha",
            evidence_id="evidence_alpha",
            family_id="official",
            observed_at=datetime(2026, 1, 1, 12),
            confidence_score=Decimal("0.800000"),
        )

    with pytest.raises(ValueError, match="counter evidence must not support event"):
        _evidence(is_counter_evidence=True, supports_event=True)

    with pytest.raises(ValueError, match="official confirmation must support event"):
        _evidence(is_official_confirmation=True, supports_event=False)

    for unsafe_value in (
        "raw_candidate_alpha",
        "market_alpha",
        "source_alpha",
        "https://example.test/item",
        "dsn_value",
        "table_name",
        "token_value",
        "wallet_value",
        "auth_value",
        "order_value",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchSourceVerificationPublicPayloadItem("safe_key", unsafe_value)


def test_digest_rejects_tampering_and_public_surface_has_no_forbidden_fields() -> None:
    report = _report(
        (
            _evidence(
                evidence_id="evidence_official",
                family_id="official",
                is_official_confirmation=True,
            ),
            _evidence(evidence_id="evidence_primary", family_id="primary"),
            _evidence(
                evidence_id="evidence_counter",
                family_id="archive",
                supports_event=False,
                is_counter_evidence=True,
            ),
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    for cls in (
        ResearchSourceVerificationCoverageConfig,
        ResearchSourceVerificationEvidence,
        ResearchSourceVerificationPublicPayloadItem,
        ResearchSourceVerificationCoverageRow,
        ResearchSourceVerificationCoverageReport,
    ):
        for field in fields(cls):
            assert field.name not in {"candidate", "market", "url", "dsn", "table", "token"}
            assert not field.name.startswith("raw_")
            assert "wallet" not in field.name
            assert "auth" not in field.name
            assert "order" not in field.name

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
    forbidden = (
        "raw_candidate",
        "market",
        "source",
        "http://",
        "https://",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "buy",
        "sell",
        "trading",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(term in lowered_key for term in forbidden)
            _assert_no_forbidden_public_surface(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_forbidden_public_surface(item)
    elif isinstance(value, str):
        lowered_value = value.lower()
        assert not any(term in lowered_value for term in forbidden)
