from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import json
import re

import pytest

from polymarket_alpha_lab.research_market_resolution_evidence_freshness_exception_report import (
    RESEARCH_MARKET_RESOLUTION_EVIDENCE_FRESHNESS_EXCEPTION_STATUSES,
    ResearchMarketResolutionEvidenceFreshnessExceptionConfig,
    ResearchMarketResolutionEvidenceFreshnessExceptionInput,
    ResearchMarketResolutionEvidenceFreshnessExceptionReport,
    ResearchMarketResolutionEvidenceFreshnessExceptionRow,
    build_research_market_resolution_evidence_freshness_exception_report,
    research_market_resolution_evidence_freshness_exception_report_digest,
    research_market_resolution_evidence_freshness_exception_report_payload,
    validate_research_market_resolution_evidence_freshness_exception_public_payload,
)


d = Decimal
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
CONFIG = ResearchMarketResolutionEvidenceFreshnessExceptionConfig(
    config_version="research-market-resolution-evidence-freshness-exception-report-v1",
    watch_official_evidence_age_seconds=d("600.000000"),
    block_official_evidence_age_seconds=d("1800.000000"),
    watch_independent_corroboration_age_seconds=d("900.000000"),
    block_independent_corroboration_age_seconds=d("2700.000000"),
    watch_rule_ambiguity_pressure=d("0.250000"),
    block_rule_ambiguity_pressure=d("0.650000"),
    watch_unresolved_contradiction_count=d("1.000000"),
    block_unresolved_contradiction_count=d("3.000000"),
    watch_manual_escalation_urgency=d("0.400000"),
    block_manual_escalation_urgency=d("0.750000"),
)


def observation(
    *,
    resolution_case_key: str = (
        "candidate-raw-alpha|market-id-alpha|will-event-resolve-yes|"
        "https://sources.example/private?token=secret|postgres://private/table"
    ),
    official_evidence_observed_at: datetime | None = GENERATED_AT
    - timedelta(minutes=5),
    independent_corroboration_observed_at: datetime | None = GENERATED_AT
    - timedelta(minutes=6),
    rule_ambiguity_pressure: Decimal = d("0.050000"),
    unresolved_contradiction_count: Decimal = d("0.000000"),
    manual_escalation_urgency: Decimal = d("0.100000"),
) -> ResearchMarketResolutionEvidenceFreshnessExceptionInput:
    return ResearchMarketResolutionEvidenceFreshnessExceptionInput(
        resolution_case_key=resolution_case_key,
        official_evidence_observed_at=official_evidence_observed_at,
        independent_corroboration_observed_at=independent_corroboration_observed_at,
        rule_ambiguity_pressure=rule_ambiguity_pressure,
        unresolved_contradiction_count=unresolved_contradiction_count,
        manual_escalation_urgency=manual_escalation_urgency,
    )


def walk_values(value: object) -> list[object]:
    if isinstance(value, dict):
        values: list[object] = list(value.keys())
        for child in value.values():
            values.extend(walk_values(child))
        return values
    if isinstance(value, list):
        values = []
        for child in value:
            values.extend(walk_values(child))
        return values
    return [value]


def test_aggregates_freshness_exceptions_without_raw_resolution_identifiers() -> None:
    passed = observation(
        resolution_case_key=(
            "candidate-pass|market-pass|will-pass-question|"
            "https://official.example/pass?token=hidden"
        ),
    )
    watched = observation(
        resolution_case_key=(
            "candidate-watch|market-watch|will-watch-question|source text"
        ),
        official_evidence_observed_at=GENERATED_AT - timedelta(minutes=20),
        independent_corroboration_observed_at=GENERATED_AT - timedelta(minutes=22),
        rule_ambiguity_pressure=d("0.300000"),
        unresolved_contradiction_count=d("1.000000"),
        manual_escalation_urgency=d("0.500000"),
    )
    blocked = observation(
        resolution_case_key=(
            "candidate-block|market-block|will-block-question|"
            "postgres://private:secret@db.internal/schema.table"
        ),
        official_evidence_observed_at=None,
        independent_corroboration_observed_at=GENERATED_AT - timedelta(hours=1),
        rule_ambiguity_pressure=d("0.700000"),
        unresolved_contradiction_count=d("4.000000"),
        manual_escalation_urgency=d("0.800000"),
    )

    report = build_research_market_resolution_evidence_freshness_exception_report(
        (watched, blocked, passed),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.max_official_evidence_age_seconds == d("1200.000000")
    assert report.max_independent_corroboration_age_seconds == d("3600.000000")
    assert report.max_rule_ambiguity_pressure == d("0.700000")
    assert report.total_unresolved_contradiction_count == d("5.000000")
    assert report.max_manual_escalation_urgency == d("0.800000")
    assert report.reason_codes == (
        "official_evidence_missing_block",
        "official_evidence_age_watch",
        "independent_corroboration_age_watch",
        "independent_corroboration_age_block",
        "rule_ambiguity_pressure_watch",
        "rule_ambiguity_pressure_block",
        "unresolved_contradiction_count_watch",
        "unresolved_contradiction_count_block",
        "manual_escalation_urgency_watch",
        "manual_escalation_urgency_block",
        "resolution_evidence_freshness_exception_watch",
        "resolution_evidence_freshness_exception_block",
    )

    assert tuple(row.aggregate_row_number for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in report.rows) == ("watch", "pass", "block")
    assert all(re.fullmatch(r"[0-9a-f]{64}", row.evidence_exception_hash) for row in report.rows)

    blocked_row = next(row for row in report.rows if row.status == "block")
    assert blocked_row.official_evidence_age_seconds is None
    assert blocked_row.independent_corroboration_age_seconds == d("3600.000000")
    assert blocked_row.reason_codes == (
        "official_evidence_missing_block",
        "independent_corroboration_age_block",
        "rule_ambiguity_pressure_block",
        "unresolved_contradiction_count_block",
        "manual_escalation_urgency_block",
        "resolution_evidence_freshness_exception_block",
    )

    payload = research_market_resolution_evidence_freshness_exception_report_payload(report)
    json.dumps(payload, sort_keys=True)
    public_text = json.dumps(payload, sort_keys=True)
    for private_fragment in (
        "candidate-",
        "market-",
        "will-",
        "question",
        "https://",
        "postgres://",
        "source text",
        "token",
        "schema.table",
    ):
        assert private_fragment not in public_text


def test_report_payload_and_digest_are_deterministic_and_validated() -> None:
    observations = (
        observation(
            resolution_case_key="private-candidate-a|private-market-a",
            official_evidence_observed_at=GENERATED_AT - timedelta(minutes=20),
        ),
        observation(
            resolution_case_key="private-candidate-b|private-market-b",
            manual_escalation_urgency=d("0.800000"),
        ),
    )

    first = build_research_market_resolution_evidence_freshness_exception_report(
        observations,
        config=CONFIG,
        generated_at=GENERATED_AT,
    )
    second = build_research_market_resolution_evidence_freshness_exception_report(
        tuple(reversed(observations)),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    first_payload = research_market_resolution_evidence_freshness_exception_report_payload(first)
    second_payload = research_market_resolution_evidence_freshness_exception_report_payload(second)
    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert (
        research_market_resolution_evidence_freshness_exception_report_digest(first)
        == first.derived_validation_digest
    )
    assert (
        first_payload["derived_validation_digest"]
        == first.derived_validation_digest
    )
    assert (
        validate_research_market_resolution_evidence_freshness_exception_public_payload(
            first_payload,
        )
        == first_payload
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered = dict(first_payload)
    tampered["pass_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_market_resolution_evidence_freshness_exception_public_payload(
            tampered,
        )

    unsafe = dict(first_payload)
    unsafe["source_url"] = "https://secret.example/private"
    with pytest.raises(ValueError, match="unsafe public"):
        validate_research_market_resolution_evidence_freshness_exception_public_payload(
            unsafe,
        )


def test_public_dataclasses_are_frozen_and_hard_flagged() -> None:
    report = build_research_market_resolution_evidence_freshness_exception_report(
        (observation(),),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    for public_dataclass in (
        ResearchMarketResolutionEvidenceFreshnessExceptionConfig,
        ResearchMarketResolutionEvidenceFreshnessExceptionInput,
        ResearchMarketResolutionEvidenceFreshnessExceptionRow,
        ResearchMarketResolutionEvidenceFreshnessExceptionReport,
    ):
        assert is_dataclass(public_dataclass)
        assert public_dataclass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    for value in (CONFIG, observation(), report.rows[0], report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(ValueError, match="paper_only"):
            replace(value, paper_only=False)
        with pytest.raises(ValueError, match="report_only"):
            replace(value, report_only=False)
        with pytest.raises(ValueError, match="readonly"):
            replace(value, readonly=False)


def test_public_numerics_are_decimal_only_and_payload_has_decimal_strings() -> None:
    report = build_research_market_resolution_evidence_freshness_exception_report(
        (
            observation(
                official_evidence_observed_at=GENERATED_AT - timedelta(minutes=20),
                unresolved_contradiction_count=d("2.000000"),
            ),
        ),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    numeric_values = [
        report.row_count,
        report.watch_count,
        report.max_official_evidence_age_seconds,
        report.total_unresolved_contradiction_count,
        report.rows[0].aggregate_row_number,
        report.rows[0].rule_ambiguity_pressure,
        report.rows[0].unresolved_contradiction_count,
    ]
    assert all(type(value) is Decimal for value in numeric_values)

    with pytest.raises(ValueError, match="Decimal"):
        observation(rule_ambiguity_pressure=0.5)  # type: ignore[arg-type]

    payload = research_market_resolution_evidence_freshness_exception_report_payload(report)
    assert payload["row_count"] == "1.000000"
    assert payload["max_official_evidence_age_seconds"] == "1200.000000"
    assert payload["rows"][0]["unresolved_contradiction_count"] == "2.000000"

    for value in walk_values(payload):
        assert not isinstance(value, float)
        assert type(value) is not int


def test_status_vocabulary_and_validation_are_exact() -> None:
    report = build_research_market_resolution_evidence_freshness_exception_report(
        (observation(),),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert RESEARCH_MARKET_RESOLUTION_EVIDENCE_FRESHNESS_EXCEPTION_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.status == "pass"

    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(report, status="blocked")


def test_datetimes_are_normalized_to_utc_and_future_evidence_is_rejected() -> None:
    eastern = timezone(timedelta(hours=-4))
    report = build_research_market_resolution_evidence_freshness_exception_report(
        (
            observation(
                official_evidence_observed_at=datetime(2026, 7, 8, 7, 55, tzinfo=eastern),
                independent_corroboration_observed_at=datetime(
                    2026,
                    7,
                    8,
                    7,
                    54,
                    tzinfo=eastern,
                ),
            ),
        ),
        config=CONFIG,
        generated_at=datetime(2026, 7, 8, 8, 0, tzinfo=eastern),
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].official_evidence_observed_at == datetime(
        2026,
        7,
        8,
        11,
        55,
        tzinfo=UTC,
    )
    assert report.rows[0].official_evidence_age_seconds == d("300.000000")

    with pytest.raises(ValueError, match="timezone-aware"):
        observation(official_evidence_observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="official_evidence_age_seconds"):
        build_research_market_resolution_evidence_freshness_exception_report(
            (
                observation(
                    official_evidence_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )


def test_empty_report_is_pass_report_only_and_digest_validated() -> None:
    report = build_research_market_resolution_evidence_freshness_exception_report(
        (),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.status == "pass"
    assert report.row_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.max_official_evidence_age_seconds is None
    assert report.max_independent_corroboration_age_seconds is None
    assert report.reason_codes == ("resolution_evidence_freshness_exception_pass",)
    validate_research_market_resolution_evidence_freshness_exception_public_payload(
        research_market_resolution_evidence_freshness_exception_report_payload(report),
    )


def test_input_surface_excludes_io_trading_sizing_and_public_raw_locator_terms() -> None:
    forbidden_terms = (
        "db",
        "database",
        "network",
        "wallet",
        "order",
        "submit",
        "cancel",
        "sign",
        "trade",
        "advice",
        "auth",
        "sizing",
        "notional",
        "recommendation",
        "candidate_id",
        "market_id",
        "slug",
        "question",
        "source_url",
        "url",
        "dsn",
        "table",
        "token",
    )
    public_names = {
        name
        for obj in (
            ResearchMarketResolutionEvidenceFreshnessExceptionConfig,
            ResearchMarketResolutionEvidenceFreshnessExceptionInput,
            ResearchMarketResolutionEvidenceFreshnessExceptionRow,
            ResearchMarketResolutionEvidenceFreshnessExceptionReport,
        )
        for name in obj.__dataclass_fields__
    } | {
        build_research_market_resolution_evidence_freshness_exception_report.__name__,
        research_market_resolution_evidence_freshness_exception_report_digest.__name__,
        research_market_resolution_evidence_freshness_exception_report_payload.__name__,
        validate_research_market_resolution_evidence_freshness_exception_public_payload.__name__,
    }

    assert not {
        name
        for name in public_names
        for forbidden_term in forbidden_terms
        if forbidden_term in name.lower()
    }
