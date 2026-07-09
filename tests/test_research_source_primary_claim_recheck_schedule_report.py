from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_source_primary_claim_recheck_schedule_report as api
from polymarket_alpha_lab.research_source_primary_claim_recheck_schedule_report import (
    ResearchSourcePrimaryClaimRecheckScheduleConfig,
    ResearchSourcePrimaryClaimRecheckScheduleInput,
    ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem,
    ResearchSourcePrimaryClaimRecheckScheduleReport,
    ResearchSourcePrimaryClaimRecheckScheduleRow,
    build_research_source_primary_claim_recheck_schedule_report,
    research_source_primary_claim_recheck_schedule_report_payload,
)


NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def recheck_input(
    claim_label: str,
    *,
    hours_old: Decimal,
    authority_score: Decimal,
    corroborating_source_count: Decimal,
    expected_corroborating_source_count: Decimal,
    contradiction_pressure_score: Decimal,
    extraction_confidence_score: Decimal,
    missing_critical_field_count: Decimal,
    critical_field_count: Decimal,
    hours_to_deadline: Decimal,
    authority_tier_label: str = "official_primary",
) -> ResearchSourcePrimaryClaimRecheckScheduleInput:
    return ResearchSourcePrimaryClaimRecheckScheduleInput(
        claim_label=claim_label,
        authority_tier_label=authority_tier_label,
        last_verified_at=NOW - timedelta(seconds=float(hours_old * d("3600"))),
        authority_score=authority_score,
        corroborating_source_count=corroborating_source_count,
        expected_corroborating_source_count=expected_corroborating_source_count,
        contradiction_pressure_score=contradiction_pressure_score,
        extraction_confidence_score=extraction_confidence_score,
        missing_critical_field_count=missing_critical_field_count,
        critical_field_count=critical_field_count,
        decision_deadline_at=NOW + timedelta(seconds=float(hours_to_deadline * d("3600"))),
    )


def report(
    items: tuple[ResearchSourcePrimaryClaimRecheckScheduleInput, ...],
    *,
    config: ResearchSourcePrimaryClaimRecheckScheduleConfig | None = None,
    public_payload: tuple[ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem, ...] = (),
) -> ResearchSourcePrimaryClaimRecheckScheduleReport:
    return build_research_source_primary_claim_recheck_schedule_report(
        items,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_primary_claim_recheck_schedule_scores_and_sorts_rows() -> None:
    schedule_report = report(
        (
            recheck_input(
                "claim_c",
                hours_old=d("10"),
                authority_score=d("0.600000"),
                corroborating_source_count=d("2.000000"),
                expected_corroborating_source_count=d("3.000000"),
                contradiction_pressure_score=d("0.400000"),
                extraction_confidence_score=d("0.700000"),
                missing_critical_field_count=d("0.000000"),
                critical_field_count=d("4.000000"),
                hours_to_deadline=d("12"),
            ),
            recheck_input(
                "claim_a",
                hours_old=d("48"),
                authority_score=d("0.200000"),
                corroborating_source_count=d("0.000000"),
                expected_corroborating_source_count=d("3.000000"),
                contradiction_pressure_score=d("0.900000"),
                extraction_confidence_score=d("0.300000"),
                missing_critical_field_count=d("2.000000"),
                critical_field_count=d("4.000000"),
                hours_to_deadline=d("2"),
            ),
            recheck_input(
                "claim_b",
                hours_old=d("1"),
                authority_score=d("0.950000"),
                corroborating_source_count=d("3.000000"),
                expected_corroborating_source_count=d("3.000000"),
                contradiction_pressure_score=d("0.000000"),
                extraction_confidence_score=d("0.950000"),
                missing_critical_field_count=d("0.000000"),
                critical_field_count=d("4.000000"),
                hours_to_deadline=d("48"),
            ),
        ),
    )

    assert schedule_report.status == "block"
    assert schedule_report.claim_count == d("3.000000")
    assert schedule_report.pass_count == d("1.000000")
    assert schedule_report.watch_count == d("1.000000")
    assert schedule_report.block_count == d("1.000000")
    assert schedule_report.overdue_claim_count == d("1.000000")
    assert schedule_report.average_recheck_pressure_score == d("0.414584")
    assert schedule_report.max_recheck_pressure_score == d("0.866667")

    assert tuple(row.claim_label for row in schedule_report.rows) == (
        "claim_a",
        "claim_b",
        "claim_c",
    )
    blocked_row = schedule_report.rows[0]
    pass_row = schedule_report.rows[1]
    watch_row = schedule_report.rows[2]

    assert blocked_row.status == "block"
    assert blocked_row.verification_age_score == d("1.000000")
    assert blocked_row.authority_gap_score == d("0.800000")
    assert blocked_row.corroboration_depth_score == d("0.000000")
    assert blocked_row.corroboration_gap_score == d("1.000000")
    assert blocked_row.extraction_confidence_gap_score == d("0.700000")
    assert blocked_row.missing_critical_field_score == d("0.500000")
    assert blocked_row.deadline_proximity_score == d("0.916667")
    assert blocked_row.recheck_pressure_score == d("0.866667")
    assert blocked_row.recheck_interval_seconds == d("11519.971200")
    assert blocked_row.overdue_by_seconds == d("161280.028800")
    assert blocked_row.reason_codes == (
        "verification_age_pressure",
        "low_source_authority_pressure",
        "low_corroboration_depth_pressure",
        "contradiction_pressure",
        "low_extraction_confidence_pressure",
        "missing_critical_fields_pressure",
        "deadline_proximity_pressure",
        "recheck_overdue",
        "primary_claim_recheck_block",
    )

    assert pass_row.status == "pass"
    assert pass_row.recheck_pressure_score == d("0.022917")
    assert pass_row.recheck_interval_seconds == d("84419.971200")
    assert pass_row.overdue_by_seconds == d("0.000000")
    assert pass_row.reason_codes == ("primary_claim_recheck_pass",)

    assert watch_row.status == "watch"
    assert watch_row.verification_age_score == d("0.416667")
    assert watch_row.corroboration_depth_score == d("0.666667")
    assert watch_row.recheck_pressure_score == d("0.354167")
    assert watch_row.reason_codes == ("primary_claim_recheck_watch",)


def test_payload_serialization_digest_and_no_non_decimal_public_numbers() -> None:
    schedule_report = report(
        (
            recheck_input(
                "claim_b",
                hours_old=d("1"),
                authority_score=d("0.950000"),
                corroborating_source_count=d("3.000000"),
                expected_corroborating_source_count=d("3.000000"),
                contradiction_pressure_score=d("0.000000"),
                extraction_confidence_score=d("0.950000"),
                missing_critical_field_count=d("0.000000"),
                critical_field_count=d("4.000000"),
                hours_to_deadline=d("48"),
            ),
        ),
        public_payload=(
            ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem(
                "schedule_basis",
                "sanitized primary claim cadence inputs only",
            ),
        ),
    )

    payload = research_source_primary_claim_recheck_schedule_report_payload(schedule_report)
    json.dumps(payload, sort_keys=True)

    assert payload == schedule_report.payload
    assert payload["claim_count"] == "1.000000"
    assert payload["average_recheck_pressure_score"] == "0.022917"
    assert payload["rows"][0]["recheck_interval_seconds"] == "84419.971200"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["derived_validation_digest"] == schedule_report.derived_validation_digest
    assert len(schedule_report.derived_validation_digest) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(schedule_report)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(schedule_report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            schedule_report,
            public_payload=(
                ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem(
                    "schedule_basis",
                    "changed sanitized cadence inputs",
                ),
            ),
        )


def test_validation_rejects_bad_types_bad_statuses_future_times_and_flags() -> None:
    with pytest.raises(ValueError, match="recheck pressure weights"):
        ResearchSourcePrimaryClaimRecheckScheduleConfig(
            authority_gap_weight=d("0.100000"),
        )
    with pytest.raises(ValueError, match="authority_score"):
        recheck_input(
            "claim_b",
            hours_old=d("1"),
            authority_score=_DecimalSubclass("0.950000"),
            corroborating_source_count=d("3.000000"),
            expected_corroborating_source_count=d("3.000000"),
            contradiction_pressure_score=d("0.000000"),
            extraction_confidence_score=d("0.950000"),
            missing_critical_field_count=d("0.000000"),
            critical_field_count=d("4.000000"),
            hours_to_deadline=d("48"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_source_primary_claim_recheck_schedule_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_source_primary_claim_recheck_schedule_report(
            (),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="last_verified_at"):
        report(
            (
                ResearchSourcePrimaryClaimRecheckScheduleInput(
                    claim_label="claim_b",
                    authority_tier_label="official_primary",
                    last_verified_at=NOW + timedelta(seconds=1),
                    authority_score=d("0.950000"),
                    corroborating_source_count=d("3.000000"),
                    expected_corroborating_source_count=d("3.000000"),
                    contradiction_pressure_score=d("0.000000"),
                    extraction_confidence_score=d("0.950000"),
                    missing_critical_field_count=d("0.000000"),
                    critical_field_count=d("4.000000"),
                    decision_deadline_at=NOW + timedelta(hours=48),
                ),
            ),
        )
    with pytest.raises(ValueError, match="decision_deadline_at"):
        report(
            (
                ResearchSourcePrimaryClaimRecheckScheduleInput(
                    claim_label="claim_b",
                    authority_tier_label="official_primary",
                    last_verified_at=NOW - timedelta(hours=1),
                    authority_score=d("0.950000"),
                    corroborating_source_count=d("3.000000"),
                    expected_corroborating_source_count=d("3.000000"),
                    contradiction_pressure_score=d("0.000000"),
                    extraction_confidence_score=d("0.950000"),
                    missing_critical_field_count=d("0.000000"),
                    critical_field_count=d("4.000000"),
                    decision_deadline_at=NOW - timedelta(seconds=1),
                ),
            ),
        )

    schedule_report = report(
        (
            recheck_input(
                "claim_b",
                hours_old=d("1"),
                authority_score=d("0.950000"),
                corroborating_source_count=d("3.000000"),
                expected_corroborating_source_count=d("3.000000"),
                contradiction_pressure_score=d("0.000000"),
                extraction_confidence_score=d("0.950000"),
                missing_critical_field_count=d("0.000000"),
                critical_field_count=d("4.000000"),
                hours_to_deadline=d("48"),
            ),
        ),
    )
    with pytest.raises(ValueError, match="status"):
        replace(schedule_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="paper_only"):
        replace(schedule_report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="rows"):
        replace(schedule_report, claim_count=d("2.000000"))


def test_public_dataclasses_are_frozen_and_reject_subclassing() -> None:
    schedule_report = report(
        (
            recheck_input(
                "claim_b",
                hours_old=d("1"),
                authority_score=d("0.950000"),
                corroborating_source_count=d("3.000000"),
                expected_corroborating_source_count=d("3.000000"),
                contradiction_pressure_score=d("0.000000"),
                extraction_confidence_score=d("0.950000"),
                missing_critical_field_count=d("0.000000"),
                critical_field_count=d("4.000000"),
                hours_to_deadline=d("48"),
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        schedule_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        schedule_report.rows[0].recheck_pressure_score = d("0")  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadRow(ResearchSourcePrimaryClaimRecheckScheduleRow):
            pass


def test_unsafe_public_payload_and_raw_identifier_surfaces_are_rejected() -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        ResearchSourcePrimaryClaimRecheckScheduleInput(
            claim_label="candidate_123",
            authority_tier_label="official_primary",
            last_verified_at=NOW,
            authority_score=d("0.950000"),
            corroborating_source_count=d("3.000000"),
            expected_corroborating_source_count=d("3.000000"),
            contradiction_pressure_score=d("0.000000"),
            extraction_confidence_score=d("0.950000"),
            missing_critical_field_count=d("0.000000"),
            critical_field_count=d("4.000000"),
            decision_deadline_at=NOW + timedelta(hours=48),
        )
    with pytest.raises(ValueError, match="unsafe public"):
        ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem(
            "source_url",
            "sanitized cadence inputs only",
        )
    with pytest.raises(ValueError, match="unsafe public"):
        ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem(
            "safe_label",
            "token credential",
        )
    for unsafe_key, unsafe_value in (
        ("execution_policy", "sanitized cadence inputs only"),
        ("safe_label", "recommendation summary"),
        ("sizing_note", "sanitized cadence inputs only"),
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem(
                unsafe_key,
                unsafe_value,
            )

    forbidden_public_terms = (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_public_terms)

    for cls in (
        ResearchSourcePrimaryClaimRecheckScheduleConfig,
        ResearchSourcePrimaryClaimRecheckScheduleInput,
        ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem,
        ResearchSourcePrimaryClaimRecheckScheduleReport,
        ResearchSourcePrimaryClaimRecheckScheduleRow,
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


def test_empty_input_returns_block_report_only_schedule() -> None:
    schedule_report = report(())

    assert schedule_report.status == "block"
    assert schedule_report.claim_count == d("0.000000")
    assert schedule_report.rows == ()
    assert schedule_report.reason_codes == ("empty_recheck_schedule",)
    assert tuple(
        (count.reason_code, count.count)
        for count in schedule_report.reason_code_counts
    ) == (("empty_recheck_schedule", d("1.000000")),)
    assert schedule_report.paper_only is True
    assert schedule_report.report_only is True
    assert schedule_report.readonly is True


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
