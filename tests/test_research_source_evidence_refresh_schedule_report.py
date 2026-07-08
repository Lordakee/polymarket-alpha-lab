from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_source_evidence_refresh_schedule_report as api
from polymarket_alpha_lab.research_source_evidence_refresh_schedule_report import (
    ResearchSourceEvidenceRefreshScheduleConfig,
    ResearchSourceEvidenceRefreshScheduleInput,
    ResearchSourceEvidenceRefreshSchedulePublicPayloadItem,
    ResearchSourceEvidenceRefreshScheduleReport,
    ResearchSourceEvidenceRefreshScheduleRow,
    build_research_source_evidence_refresh_schedule_report,
    research_source_evidence_refresh_schedule_report_payload,
)


NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def schedule_input(
    source_key: str,
    *,
    hours_old: Decimal,
    authority_score: Decimal,
    contradiction_exposure_score: Decimal,
    independence_score: Decimal,
    category_volatility_score: Decimal,
) -> ResearchSourceEvidenceRefreshScheduleInput:
    return ResearchSourceEvidenceRefreshScheduleInput(
        source_key=source_key,
        last_verified_at=NOW - timedelta(seconds=float(hours_old * Decimal("3600"))),
        authority_score=authority_score,
        contradiction_exposure_score=contradiction_exposure_score,
        independence_score=independence_score,
        category_volatility_score=category_volatility_score,
    )


def report(
    items: tuple[ResearchSourceEvidenceRefreshScheduleInput, ...],
    *,
    config: ResearchSourceEvidenceRefreshScheduleConfig | None = None,
    public_payload: tuple[ResearchSourceEvidenceRefreshSchedulePublicPayloadItem, ...] = (),
) -> ResearchSourceEvidenceRefreshScheduleReport:
    return build_research_source_evidence_refresh_schedule_report(
        items,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_refresh_schedule_scores_and_sorts_rows_deterministically() -> None:
    schedule_report = report(
        (
            schedule_input(
                "source_c",
                hours_old=d("10"),
                authority_score=d("0.500000"),
                contradiction_exposure_score=d("0.400000"),
                independence_score=d("0.600000"),
                category_volatility_score=d("0.500000"),
            ),
            schedule_input(
                "source_a",
                hours_old=d("48"),
                authority_score=d("0.200000"),
                contradiction_exposure_score=d("0.900000"),
                independence_score=d("0.300000"),
                category_volatility_score=d("0.800000"),
            ),
            schedule_input(
                "source_b",
                hours_old=d("1"),
                authority_score=d("0.950000"),
                contradiction_exposure_score=d("0.000000"),
                independence_score=d("0.900000"),
                category_volatility_score=d("0.100000"),
            ),
        ),
    )

    assert schedule_report.status == "block"
    assert schedule_report.source_count == d("3.000000")
    assert schedule_report.pass_count == d("1.000000")
    assert schedule_report.watch_count == d("1.000000")
    assert schedule_report.block_count == d("1.000000")
    assert schedule_report.overdue_source_count == d("1.000000")
    assert schedule_report.average_refresh_pressure_score == d("0.451667")
    assert schedule_report.max_refresh_pressure_score == d("0.865000")

    assert tuple(row.source_key for row in schedule_report.rows) == (
        "source_a",
        "source_b",
        "source_c",
    )
    blocked_row = schedule_report.rows[0]
    pass_row = schedule_report.rows[1]
    watch_row = schedule_report.rows[2]

    assert blocked_row.status == "block"
    assert blocked_row.source_age_seconds == d("172800.000000")
    assert blocked_row.freshness_decay_score == d("1.000000")
    assert blocked_row.authority_gap_score == d("0.800000")
    assert blocked_row.independence_gap_score == d("0.700000")
    assert blocked_row.refresh_pressure_score == d("0.865000")
    assert blocked_row.refresh_interval_seconds == d("11664.000000")
    assert blocked_row.overdue_by_seconds == d("161136.000000")
    assert blocked_row.reason_codes == (
        "freshness_decay_pressure",
        "low_authority_pressure",
        "contradiction_exposure_pressure",
        "low_independence_pressure",
        "category_volatility_pressure",
        "refresh_overdue",
        "refresh_schedule_block",
    )

    assert pass_row.status == "pass"
    assert pass_row.refresh_pressure_score == d("0.050000")
    assert pass_row.refresh_interval_seconds == d("82080.000000")
    assert pass_row.overdue_by_seconds == d("0.000000")
    assert pass_row.reason_codes == ("refresh_schedule_pass",)

    assert watch_row.status == "watch"
    assert watch_row.freshness_decay_score == d("0.416667")
    assert watch_row.refresh_pressure_score == d("0.440000")
    assert watch_row.refresh_interval_seconds == d("48384.000000")
    assert watch_row.reason_codes == (
        "low_authority_pressure",
        "category_volatility_pressure",
        "refresh_schedule_watch",
    )


def test_payload_serialization_digest_and_no_non_decimal_public_numbers() -> None:
    schedule_report = report(
        (
            schedule_input(
                "source_a",
                hours_old=d("1"),
                authority_score=d("0.950000"),
                contradiction_exposure_score=d("0.000000"),
                independence_score=d("0.900000"),
                category_volatility_score=d("0.100000"),
            ),
        ),
        public_payload=(
            ResearchSourceEvidenceRefreshSchedulePublicPayloadItem(
                "schedule_basis",
                "sanitized cadence inputs only",
            ),
        ),
    )

    payload = research_source_evidence_refresh_schedule_report_payload(schedule_report)
    json.dumps(payload, sort_keys=True)

    assert payload == schedule_report.payload
    assert payload["source_count"] == "1.000000"
    assert payload["average_refresh_pressure_score"] == "0.050000"
    assert payload["rows"][0]["refresh_interval_seconds"] == "82080.000000"
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
                ResearchSourceEvidenceRefreshSchedulePublicPayloadItem(
                    "schedule_basis",
                    "changed cadence inputs",
                ),
            ),
        )


def test_validation_rejects_bad_types_bad_statuses_future_times_and_flags() -> None:
    with pytest.raises(ValueError, match="refresh pressure weights"):
        ResearchSourceEvidenceRefreshScheduleConfig(
            freshness_decay_weight=d("0.100000"),
        )
    with pytest.raises(ValueError, match="authority_score"):
        schedule_input(
            "source_a",
            hours_old=d("1"),
            authority_score=_DecimalSubclass("0.950000"),
            contradiction_exposure_score=d("0.000000"),
            independence_score=d("0.900000"),
            category_volatility_score=d("0.100000"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_source_evidence_refresh_schedule_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_source_evidence_refresh_schedule_report(
            (),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="last_verified_at"):
        report(
            (
                ResearchSourceEvidenceRefreshScheduleInput(
                    "source_a",
                    last_verified_at=NOW + timedelta(seconds=1),
                    authority_score=d("0.950000"),
                    contradiction_exposure_score=d("0.000000"),
                    independence_score=d("0.900000"),
                    category_volatility_score=d("0.100000"),
                ),
            ),
        )

    schedule_report = report(
        (
            schedule_input(
                "source_a",
                hours_old=d("1"),
                authority_score=d("0.950000"),
                contradiction_exposure_score=d("0.000000"),
                independence_score=d("0.900000"),
                category_volatility_score=d("0.100000"),
            ),
        ),
    )
    with pytest.raises(ValueError, match="status"):
        replace(schedule_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="paper_only"):
        replace(schedule_report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="rows"):
        replace(schedule_report, source_count=d("2.000000"))


def test_public_dataclasses_are_frozen_and_reject_subclassing() -> None:
    schedule_report = report(
        (
            schedule_input(
                "source_a",
                hours_old=d("1"),
                authority_score=d("0.950000"),
                contradiction_exposure_score=d("0.000000"),
                independence_score=d("0.900000"),
                category_volatility_score=d("0.100000"),
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        schedule_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        schedule_report.rows[0].refresh_pressure_score = d("0")  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadRow(ResearchSourceEvidenceRefreshScheduleRow):
            pass


def test_unsafe_public_payload_and_raw_identifier_surfaces_are_rejected() -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        ResearchSourceEvidenceRefreshScheduleInput(
            "candidate_123",
            last_verified_at=NOW,
            authority_score=d("0.950000"),
            contradiction_exposure_score=d("0.000000"),
            independence_score=d("0.900000"),
            category_volatility_score=d("0.100000"),
        )
    with pytest.raises(ValueError, match="unsafe public"):
        ResearchSourceEvidenceRefreshSchedulePublicPayloadItem(
            "source_url",
            "sanitized cadence inputs only",
        )
    with pytest.raises(ValueError, match="unsafe public"):
        ResearchSourceEvidenceRefreshSchedulePublicPayloadItem(
            "safe_label",
            "token credential",
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
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_public_terms)

    for cls in (
        ResearchSourceEvidenceRefreshScheduleConfig,
        ResearchSourceEvidenceRefreshScheduleInput,
        ResearchSourceEvidenceRefreshSchedulePublicPayloadItem,
        ResearchSourceEvidenceRefreshScheduleReport,
        ResearchSourceEvidenceRefreshScheduleRow,
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
    assert schedule_report.source_count == d("0.000000")
    assert schedule_report.rows == ()
    assert schedule_report.reason_codes == ("empty_source_schedule",)
    assert tuple(
        (count.reason_code, count.count)
        for count in schedule_report.reason_code_counts
    ) == (("empty_source_schedule", d("1.000000")),)
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
