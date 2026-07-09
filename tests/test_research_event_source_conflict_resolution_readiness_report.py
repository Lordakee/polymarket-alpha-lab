from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json

import pytest

import polymarket_alpha_lab.research_event_source_conflict_resolution_readiness_report as api
from polymarket_alpha_lab.research_event_source_conflict_resolution_readiness_report import (
    ResearchEventSourceConflictResolutionReadinessConfig,
    ResearchEventSourceConflictResolutionReadinessInput,
    ResearchEventSourceConflictResolutionReadinessPublicPayloadItem,
    ResearchEventSourceConflictResolutionReadinessReport,
    build_research_event_source_conflict_resolution_readiness_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _input(
    *,
    conflict_digest: str | None = None,
    rule_source_mapping_digest: str | None = None,
    source_claim_count: Decimal = Decimal("3.000000"),
    independent_source_count: Decimal = Decimal("2.000000"),
    authority_score: Decimal = Decimal("0.800000"),
    newest_source_age_seconds: Decimal = Decimal("600.000000"),
    oldest_source_age_seconds: Decimal = Decimal("1200.000000"),
    contradiction_severity: Decimal = Decimal("0.600000"),
    rule_source_mapping_score: Decimal = Decimal("0.900000"),
) -> ResearchEventSourceConflictResolutionReadinessInput:
    return ResearchEventSourceConflictResolutionReadinessInput(
        conflict_digest=conflict_digest or _digest("conflict-a"),
        rule_source_mapping_digest=rule_source_mapping_digest or _digest("rule-a"),
        source_claim_count=source_claim_count,
        independent_source_count=independent_source_count,
        authority_score=authority_score,
        newest_source_age_seconds=newest_source_age_seconds,
        oldest_source_age_seconds=oldest_source_age_seconds,
        contradiction_severity=contradiction_severity,
        rule_source_mapping_score=rule_source_mapping_score,
    )


def _report(
    inputs: tuple[ResearchEventSourceConflictResolutionReadinessInput, ...],
    *,
    config: ResearchEventSourceConflictResolutionReadinessConfig | None = None,
    public_payload: tuple[
        ResearchEventSourceConflictResolutionReadinessPublicPayloadItem,
        ...,
    ] = (),
) -> ResearchEventSourceConflictResolutionReadinessReport:
    return build_research_event_source_conflict_resolution_readiness_report(
        inputs,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_resolution_readiness_passes_with_authoritative_fresh_independent_mapping() -> None:
    report = _report((_input(),))

    row = report.rows[0]
    assert report.status == "pass"
    assert report.conflict_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert row.status == "pass"
    assert row.freshness_score == Decimal("0.993056")
    assert row.independence_score == Decimal("1.000000")
    assert row.readiness_score == Decimal("0.868611")
    assert "conflict_resolution_readiness_pass" in row.reason_codes
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_resolution_readiness_blocks_when_core_resolution_inputs_are_not_ready() -> None:
    report = _report(
        (
            _input(
                authority_score=Decimal("0.400000"),
                newest_source_age_seconds=Decimal("90000.000000"),
                oldest_source_age_seconds=Decimal("90000.000000"),
                independent_source_count=Decimal("1.000000"),
                contradiction_severity=Decimal("0.700000"),
                rule_source_mapping_score=Decimal("0.300000"),
            ),
        ),
    )

    row = report.rows[0]
    assert report.status == "block"
    assert report.block_count == Decimal("1.000000")
    assert row.status == "block"
    assert "authority_below_threshold" in row.reason_codes
    assert "source_freshness_block" in row.reason_codes
    assert "insufficient_independence" in row.reason_codes
    assert "rule_source_mapping_gap" in row.reason_codes


def test_low_contradiction_severity_stays_watch_even_with_strong_sources() -> None:
    report = _report((_input(contradiction_severity=Decimal("0.100000")),))

    row = report.rows[0]
    assert report.status == "watch"
    assert report.watch_count == Decimal("1.000000")
    assert row.status == "watch"
    assert "low_contradiction_severity_watch" in row.reason_codes


def test_payload_serializes_decimals_and_digest_is_deterministic() -> None:
    report = _report(
        (_input(),),
        public_payload=(
            ResearchEventSourceConflictResolutionReadinessPublicPayloadItem(
                "safe_context",
                "redacted digest inputs only",
            ),
        ),
    )

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["conflict_count"] == "1.000000"
    assert payload["average_readiness_score"] == "0.868611"
    assert payload["rows"][0]["source_claim_count"] == "3.000000"
    assert payload["rows"][0]["readiness_score"] == "0.868611"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert "conflict-a" not in json.dumps(payload, sort_keys=True)
    assert "rule-a" not in json.dumps(payload, sort_keys=True)
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = _report((_input(),))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchEventSourceConflictResolutionReadinessConfig):
            pass


def test_hard_flags_and_digest_validation_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchEventSourceConflictResolutionReadinessConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _input().__class__(
            conflict_digest=_digest("conflict-a"),
            rule_source_mapping_digest=_digest("rule-a"),
            source_claim_count=Decimal("3.000000"),
            independent_source_count=Decimal("2.000000"),
            authority_score=Decimal("0.800000"),
            newest_source_age_seconds=Decimal("600.000000"),
            oldest_source_age_seconds=Decimal("1200.000000"),
            contradiction_severity=Decimal("0.600000"),
            rule_source_mapping_score=Decimal("0.900000"),
            report_only=False,
        )

    report = _report((_input(),))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_public_payload_rejects_raw_or_unsafe_surfaces() -> None:
    with pytest.raises(ValueError, match="sha256"):
        _input(conflict_digest="raw-candidate-id")

    for key in (
        "candidate_id",
        "market_slug",
        "question_text",
        "source_url",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventSourceConflictResolutionReadinessPublicPayloadItem(
                key,
                "safe value",
            )

    for value in (
        "https://example.com/raw-source",
        "postgres://user:pass@example/db",
        "auth header",
        "authorization header",
        "secret material",
        "live trading route",
        "position sizing output",
        "analyst recommendation",
        "execution instruction",
        "wallet surface",
        "place order",
        "trade execution",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventSourceConflictResolutionReadinessPublicPayloadItem(
                "safe_key",
                value,
            )


def test_no_unsafe_public_names_or_execution_modules_are_exposed() -> None:
    for public_name in api.__all__:
        assert not _contains_unsafe_public_name(public_name)

    for cls in (
        ResearchEventSourceConflictResolutionReadinessConfig,
        ResearchEventSourceConflictResolutionReadinessInput,
        ResearchEventSourceConflictResolutionReadinessPublicPayloadItem,
        api.ResearchEventSourceConflictResolutionReadinessRow,
        ResearchEventSourceConflictResolutionReadinessReport,
    ):
        for field in fields(cls):
            assert not _contains_unsafe_public_name(field.name)

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


def _contains_unsafe_public_name(value: str) -> bool:
    lowered = value.lower()
    if any(
        phrase in lowered
        for phrase in (
            "market_id",
            "market_slug",
            "source_url",
            "question_text",
            "table_name",
        )
    ):
        return True
    tokens = tuple(token for token in lowered.replace("_", " ").split() if token)
    unsafe_tokens = frozenset(
        (
            "candidate",
            "question",
            "url",
            "text",
            "dsn",
            "table",
            "token",
            "wallet",
            "order",
            "trade",
            "auth",
            "database",
            "network",
            "scrap",
            "scraping",
            "live",
            "buy",
            "sell",
        ),
    )
    return any(token in unsafe_tokens for token in tokens)
