from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_source_primary_evidence_staleness_alert_report as api
from polymarket_alpha_lab.research_source_primary_evidence_staleness_alert_report import (
    ResearchSourcePrimaryEvidenceStalenessAlertConfig,
    ResearchSourcePrimaryEvidenceStalenessAlertInput,
    ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem,
    ResearchSourcePrimaryEvidenceStalenessAlertReport,
    ResearchSourcePrimaryEvidenceStalenessAlertRow,
    build_research_source_primary_evidence_staleness_alert_report,
    research_source_primary_evidence_staleness_alert_report_payload,
)


NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def alert_input(
    evidence_key: str,
    *,
    hours_old: Decimal,
    authority_tier: str,
    corroboration_count: Decimal,
    contradiction_pressure: Decimal,
    extraction_confidence: Decimal,
    hours_until_deadline: Decimal,
) -> ResearchSourcePrimaryEvidenceStalenessAlertInput:
    return ResearchSourcePrimaryEvidenceStalenessAlertInput(
        evidence_key=evidence_key,
        authority_tier=authority_tier,
        last_verified_at=NOW - timedelta(seconds=float(hours_old * d("3600"))),
        corroboration_count=corroboration_count,
        contradiction_pressure=contradiction_pressure,
        extraction_confidence=extraction_confidence,
        deadline_at=NOW + timedelta(seconds=float(hours_until_deadline * d("3600"))),
    )


def report(
    items: tuple[ResearchSourcePrimaryEvidenceStalenessAlertInput, ...],
    *,
    config: ResearchSourcePrimaryEvidenceStalenessAlertConfig | None = None,
    public_payload: tuple[ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem, ...] = (),
) -> ResearchSourcePrimaryEvidenceStalenessAlertReport:
    return build_research_source_primary_evidence_staleness_alert_report(
        items,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_alert_scores_and_sorts_rows_deterministically() -> None:
    alert_report = report(
        (
            alert_input(
                "evidence_c",
                hours_old=d("12"),
                authority_tier="secondary_primary",
                corroboration_count=d("2"),
                contradiction_pressure=d("0.250000"),
                extraction_confidence=d("0.700000"),
                hours_until_deadline=d("36"),
            ),
            alert_input(
                "evidence_a",
                hours_old=d("1"),
                authority_tier="official_primary",
                corroboration_count=d("3"),
                contradiction_pressure=d("0.000000"),
                extraction_confidence=d("0.950000"),
                hours_until_deadline=d("96"),
            ),
            alert_input(
                "evidence_b",
                hours_old=d("72"),
                authority_tier="unknown",
                corroboration_count=d("0"),
                contradiction_pressure=d("0.900000"),
                extraction_confidence=d("0.300000"),
                hours_until_deadline=d("6"),
            ),
        ),
    )

    assert alert_report.status == "block"
    assert alert_report.evidence_count == d("3.000000")
    assert alert_report.pass_count == d("1.000000")
    assert alert_report.watch_count == d("1.000000")
    assert alert_report.block_count == d("1.000000")
    assert alert_report.overdue_count == d("1.000000")
    assert alert_report.average_alert_score == d("0.428333")
    assert alert_report.max_alert_score == d("0.890000")
    assert tuple(row.evidence_key for row in alert_report.rows) == (
        "evidence_a",
        "evidence_b",
        "evidence_c",
    )

    pass_row, block_row, watch_row = alert_report.rows
    assert pass_row.status == "pass"
    assert pass_row.verification_age_seconds == d("3600.000000")
    assert pass_row.verification_age_pressure == d("0.041667")
    assert pass_row.authority_tier_gap_score == d("0.000000")
    assert pass_row.corroboration_gap_score == d("0.000000")
    assert pass_row.extraction_confidence_gap_score == d("0.050000")
    assert pass_row.deadline_proximity_score == d("0.000000")
    assert pass_row.alert_score == d("0.020000")
    assert pass_row.reason_codes == ("primary_evidence_alert_pass",)

    assert block_row.status == "block"
    assert block_row.verification_age_pressure == d("1.000000")
    assert block_row.authority_tier_gap_score == d("0.750000")
    assert block_row.corroboration_gap_score == d("1.000000")
    assert block_row.deadline_proximity_score == d("0.875000")
    assert block_row.alert_score == d("0.890000")
    assert block_row.verification_overdue_by_seconds == d("172800.000000")
    assert block_row.reason_codes == (
        "verification_age_pressure",
        "low_authority_tier_pressure",
        "low_corroboration_pressure",
        "contradiction_pressure",
        "low_extraction_confidence_pressure",
        "deadline_proximity_pressure",
        "verification_overdue",
        "primary_evidence_alert_block",
    )

    assert watch_row.status == "watch"
    assert watch_row.verification_age_pressure == d("0.500000")
    assert watch_row.corroboration_gap_score == d("0.333333")
    assert watch_row.deadline_proximity_score == d("0.250000")
    assert watch_row.alert_score == d("0.375000")
    assert watch_row.reason_codes == (
        "verification_age_pressure",
        "low_authority_tier_pressure",
        "primary_evidence_alert_watch",
    )


def test_payload_digest_validation_and_decimal_string_serialization() -> None:
    alert_report = report(
        (
            alert_input(
                "evidence_a",
                hours_old=d("1"),
                authority_tier="official_primary",
                corroboration_count=d("3"),
                contradiction_pressure=d("0.000000"),
                extraction_confidence=d("0.950000"),
                hours_until_deadline=d("96"),
            ),
        ),
        public_payload=(
            ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem(
                "basis",
                "sanitized primary evidence freshness metrics",
            ),
        ),
    )
    repeated_report = report(
        (
            alert_input(
                "evidence_a",
                hours_old=d("1"),
                authority_tier="official_primary",
                corroboration_count=d("3"),
                contradiction_pressure=d("0.000000"),
                extraction_confidence=d("0.950000"),
                hours_until_deadline=d("96"),
            ),
        ),
        public_payload=(
            ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem(
                "basis",
                "sanitized primary evidence freshness metrics",
            ),
        ),
    )

    payload = research_source_primary_evidence_staleness_alert_report_payload(alert_report)
    json.dumps(payload, sort_keys=True)

    assert payload == alert_report.payload
    assert alert_report.derived_validation_digest == repeated_report.derived_validation_digest
    assert len(alert_report.derived_validation_digest) == 64
    assert payload["evidence_count"] == "1.000000"
    assert payload["average_alert_score"] == "0.020000"
    assert payload["rows"][0]["verification_age_seconds"] == "3600.000000"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["derived_validation_digest"] == alert_report.derived_validation_digest
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(alert_report)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(alert_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            alert_report,
            public_payload=(
                ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem(
                    "basis",
                    "changed sanitized freshness metrics",
                ),
            ),
        )


def test_validation_rejects_bad_types_future_times_statuses_and_flags() -> None:
    with pytest.raises(ValueError, match="weights"):
        ResearchSourcePrimaryEvidenceStalenessAlertConfig(
            verification_age_weight=d("0.100000"),
        )
    with pytest.raises(ValueError, match="corroboration_count"):
        alert_input(
            "evidence_a",
            hours_old=d("1"),
            authority_tier="official_primary",
            corroboration_count=_DecimalSubclass("3"),
            contradiction_pressure=d("0.000000"),
            extraction_confidence=d("0.950000"),
            hours_until_deadline=d("96"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_source_primary_evidence_staleness_alert_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_source_primary_evidence_staleness_alert_report(
            (),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="last_verified_at"):
        report(
            (
                ResearchSourcePrimaryEvidenceStalenessAlertInput(
                    evidence_key="evidence_a",
                    authority_tier="official_primary",
                    last_verified_at=NOW + timedelta(seconds=1),
                    corroboration_count=d("3"),
                    contradiction_pressure=d("0.000000"),
                    extraction_confidence=d("0.950000"),
                    deadline_at=NOW + timedelta(hours=96),
                ),
            ),
        )

    alert_report = report(
        (
            alert_input(
                "evidence_a",
                hours_old=d("1"),
                authority_tier="official_primary",
                corroboration_count=d("3"),
                contradiction_pressure=d("0.000000"),
                extraction_confidence=d("0.950000"),
                hours_until_deadline=d("96"),
            ),
        ),
    )
    with pytest.raises(ValueError, match="status"):
        replace(alert_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="paper_only"):
        replace(alert_report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="rows"):
        replace(alert_report, evidence_count=d("2.000000"))


def test_public_dataclasses_are_frozen_and_reject_subclassing() -> None:
    alert_report = report(
        (
            alert_input(
                "evidence_a",
                hours_old=d("1"),
                authority_tier="official_primary",
                corroboration_count=d("3"),
                contradiction_pressure=d("0.000000"),
                extraction_confidence=d("0.950000"),
                hours_until_deadline=d("96"),
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        alert_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        alert_report.rows[0].alert_score = d("0")  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadRow(ResearchSourcePrimaryEvidenceStalenessAlertRow):
            pass


def test_unsafe_public_surfaces_are_rejected_and_module_has_no_io_imports() -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        ResearchSourcePrimaryEvidenceStalenessAlertInput(
            evidence_key="candidate_123",
            authority_tier="official_primary",
            last_verified_at=NOW,
            corroboration_count=d("3"),
            contradiction_pressure=d("0.000000"),
            extraction_confidence=d("0.950000"),
            deadline_at=NOW + timedelta(hours=96),
        )
    with pytest.raises(ValueError, match="evidence_key"):
        ResearchSourcePrimaryEvidenceStalenessAlertInput(
            evidence_key="a1b2c3d4e5f6",
            authority_tier="official_primary",
            last_verified_at=NOW,
            corroboration_count=d("3"),
            contradiction_pressure=d("0.000000"),
            extraction_confidence=d("0.950000"),
            deadline_at=NOW + timedelta(hours=96),
        )
    with pytest.raises(ValueError, match="unsafe public"):
        ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem(
            "source_url",
            "sanitized freshness metrics only",
        )
    with pytest.raises(ValueError, match="unsafe public"):
        ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem(
            "basis",
            "wallet credential",
        )
    for compact_leak in (
        "candidate123",
        "marketSlug",
        "sourceText",
        "sizingSignal",
        "executionSurface",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem(
                "basis",
                compact_leak,
            )

    forbidden_public_terms = (
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "execution",
        "live",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_public_terms)

    for cls in (
        ResearchSourcePrimaryEvidenceStalenessAlertConfig,
        ResearchSourcePrimaryEvidenceStalenessAlertInput,
        ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem,
        ResearchSourcePrimaryEvidenceStalenessAlertReport,
        ResearchSourcePrimaryEvidenceStalenessAlertRow,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_public_terms)

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


def test_empty_input_returns_pass_report_only_alert() -> None:
    alert_report = report(())

    assert alert_report.status == "pass"
    assert alert_report.evidence_count == d("0.000000")
    assert alert_report.pass_count == d("0.000000")
    assert alert_report.watch_count == d("0.000000")
    assert alert_report.block_count == d("0.000000")
    assert alert_report.overdue_count == d("0.000000")
    assert alert_report.average_alert_score == d("0.000000")
    assert alert_report.max_alert_score == d("0.000000")
    assert alert_report.rows == ()
    assert alert_report.reason_codes == ("empty_primary_evidence_alert",)
    assert tuple(
        (count.reason_code, count.count)
        for count in alert_report.reason_code_counts
    ) == (("empty_primary_evidence_alert", d("1.000000")),)
    assert alert_report.paper_only is True
    assert alert_report.report_only is True
    assert alert_report.readonly is True


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
