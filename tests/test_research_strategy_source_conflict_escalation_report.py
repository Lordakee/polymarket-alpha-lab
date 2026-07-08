from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_strategy_source_conflict_escalation_report as api
from polymarket_alpha_lab.research_strategy_source_conflict_escalation_report import (
    ResearchStrategySourceConflictEscalationConfig,
    ResearchStrategySourceConflictEscalationObservation,
    ResearchStrategySourceConflictEscalationReport,
    ResearchStrategySourceConflictEscalationRow,
    build_research_strategy_source_conflict_escalation_report,
)


NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _observation(
    *,
    conflict_group_hash: str = HASH_A,
    input_row_number: Decimal = Decimal("1.000000"),
    source_class: str = "official",
    observed_at: datetime | None = None,
    contradiction_score: Decimal = Decimal("0.300000"),
    specialist_dissent_score: Decimal = Decimal("0.000000"),
    manual_escalation_urgency: Decimal = Decimal("0.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategySourceConflictEscalationObservation:
    return ResearchStrategySourceConflictEscalationObservation(
        conflict_group_hash=conflict_group_hash,
        input_row_number=input_row_number,
        source_class=source_class,
        observed_at=observed_at or NOW,
        contradiction_score=contradiction_score,
        specialist_dissent_score=specialist_dissent_score,
        manual_escalation_urgency=manual_escalation_urgency,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    observations: tuple[ResearchStrategySourceConflictEscalationObservation, ...],
    *,
    config: ResearchStrategySourceConflictEscalationConfig | None = None,
) -> ResearchStrategySourceConflictEscalationReport:
    return build_research_strategy_source_conflict_escalation_report(
        observations,
        generated_at=NOW,
        config=config,
    )


def test_escalation_report_aggregates_pass_watch_and_block_readiness() -> None:
    report = _report(
        (
            _observation(
                conflict_group_hash=HASH_B,
                input_row_number=Decimal("5.000000"),
                source_class="specialist",
                observed_at=NOW - timedelta(hours=8),
                contradiction_score=Decimal("0.900000"),
                specialist_dissent_score=Decimal("0.800000"),
                manual_escalation_urgency=Decimal("0.900000"),
            ),
            _observation(
                conflict_group_hash=HASH_A,
                input_row_number=Decimal("1.000000"),
                source_class="official",
                contradiction_score=Decimal("0.300000"),
            ),
            _observation(
                conflict_group_hash=HASH_A,
                input_row_number=Decimal("2.000000"),
                source_class="primary",
                contradiction_score=Decimal("0.200000"),
            ),
            _observation(
                conflict_group_hash=HASH_A,
                input_row_number=Decimal("3.000000"),
                source_class="specialist",
                contradiction_score=Decimal("0.100000"),
            ),
            _observation(
                conflict_group_hash=HASH_C,
                input_row_number=Decimal("6.000000"),
                source_class="official",
                observed_at=NOW - timedelta(hours=3),
                contradiction_score=Decimal("0.550000"),
            ),
            _observation(
                conflict_group_hash=HASH_C,
                input_row_number=Decimal("7.000000"),
                source_class="primary",
                observed_at=NOW - timedelta(hours=2),
                contradiction_score=Decimal("0.450000"),
            ),
        ),
    )

    pass_row, block_row, watch_row = report.rows
    assert report.escalation_status == "block"
    assert report.conflict_group_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert report.max_stale_conflict_age_seconds == Decimal("28800.000000")
    assert report.max_manual_escalation_urgency == Decimal("0.900000")
    assert pass_row.aggregate_row_number == Decimal("1.000000")
    assert pass_row.conflict_group_hash == HASH_A
    assert pass_row.source_class_count == Decimal("3.000000")
    assert pass_row.source_class_quorum_score == Decimal("1.000000")
    assert pass_row.contradiction_pressure == Decimal("0.200000")
    assert pass_row.escalation_status == "pass"
    assert block_row.aggregate_row_number == Decimal("2.000000")
    assert block_row.conflict_group_hash == HASH_B
    assert block_row.stale_conflict_age_seconds == Decimal("28800.000000")
    assert block_row.escalation_status == "block"
    assert "manual_escalation_block" in block_row.reason_codes
    assert watch_row.aggregate_row_number == Decimal("3.000000")
    assert watch_row.conflict_group_hash == HASH_C
    assert watch_row.source_class_quorum_score == Decimal("0.666667")
    assert watch_row.escalation_status == "watch"
    assert "source_class_quorum_watch" in watch_row.reason_codes
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_deterministic_json_ready_and_digest_validated() -> None:
    observations = (
        _observation(
            conflict_group_hash=HASH_C,
            input_row_number=Decimal("3.000000"),
            source_class="primary",
            contradiction_score=Decimal("0.450000"),
        ),
        _observation(
            conflict_group_hash=HASH_A,
            input_row_number=Decimal("1.000000"),
            source_class="official",
            contradiction_score=Decimal("0.200000"),
        ),
    )

    report = _report(observations)
    reordered = _report(tuple(reversed(observations)))
    payload = report.payload

    assert payload == reordered.payload
    assert report.derived_validation_digest == reordered.derived_validation_digest
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-01-01T12:00:00+00:00"
    assert payload["conflict_group_count"] == "2.000000"
    assert payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert payload["rows"][0]["conflict_group_hash"] == HASH_A
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_public_payload_exposes_only_aggregate_row_numbers_or_hashes() -> None:
    report = _report(
        (
            _observation(
                conflict_group_hash=HASH_A,
                input_row_number=Decimal("99.000000"),
                source_class="official",
                contradiction_score=Decimal("0.800000"),
            ),
        ),
    )
    payload_text = json.dumps(report.payload, sort_keys=True)

    for forbidden in (
        "candidate",
        "market",
        "slug",
        "question",
        "source_url",
        "source_text",
        "postgres",
        "table",
        "token",
        "dsn",
        "secret",
    ):
        assert forbidden not in payload_text.lower()
    assert "99.000000" not in payload_text
    assert HASH_A in payload_text
    assert "aggregate_row_number" in payload_text


def test_rejects_non_decimal_naive_future_and_unsafe_inputs() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        _observation(input_row_number=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="timezone-aware"):
        _observation(observed_at=datetime(2026, 1, 1))

    with pytest.raises(ValueError, match="after generated_at"):
        _report((_observation(observed_at=NOW + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="conflict_group_hash"):
        _observation(conflict_group_hash="raw_candidate_123")

    with pytest.raises(ValueError, match="source_class"):
        _observation(source_class="https://example.test/source")


def test_dataclasses_are_frozen_and_hard_flags_are_enforced() -> None:
    report = _report((_observation(),))

    with pytest.raises(FrozenInstanceError):
        report.escalation_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadRow(ResearchStrategySourceConflictEscalationRow):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ResearchStrategySourceConflictEscalationConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _observation(report_only=False)  # type: ignore[call-arg]

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_no_forbidden_surfaces_are_exported() -> None:
    forbidden_terms = (
        "db",
        "database",
        "dsn",
        "network",
        "wallet",
        "auth",
        "order",
        "live",
        "trading",
        "sizing",
        "recommendation",
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "token",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_terms)

    for cls in (
        ResearchStrategySourceConflictEscalationConfig,
        ResearchStrategySourceConflictEscalationObservation,
        ResearchStrategySourceConflictEscalationRow,
        ResearchStrategySourceConflictEscalationReport,
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
