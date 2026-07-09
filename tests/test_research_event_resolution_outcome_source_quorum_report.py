from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json

import pytest

import polymarket_alpha_lab.research_event_resolution_outcome_source_quorum_report as api
from polymarket_alpha_lab.research_event_resolution_outcome_source_quorum_report import (
    ResearchEventResolutionOutcomeSourceQuorumConfig,
    ResearchEventResolutionOutcomeSourceQuorumInput,
    ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem,
    ResearchEventResolutionOutcomeSourceQuorumReport,
    build_research_event_resolution_outcome_source_quorum_report,
    research_event_resolution_outcome_source_quorum_public_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def source_input(
    seed: str = "event-a",
    *,
    authoritative_source_count: Decimal = d("3.000000"),
    newest_source_age_seconds: Decimal = d("600.000000"),
    oldest_source_age_seconds: Decimal = d("1200.000000"),
    contradiction_pressure: Decimal = d("0.100000"),
    seconds_until_deadline: Decimal = d("172800.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventResolutionOutcomeSourceQuorumInput:
    return ResearchEventResolutionOutcomeSourceQuorumInput(
        event_digest=digest(f"{seed}-event"),
        outcome_digest=digest(f"{seed}-outcome"),
        authoritative_source_count=authoritative_source_count,
        newest_source_age_seconds=newest_source_age_seconds,
        oldest_source_age_seconds=oldest_source_age_seconds,
        contradiction_pressure=contradiction_pressure,
        seconds_until_deadline=seconds_until_deadline,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *inputs: ResearchEventResolutionOutcomeSourceQuorumInput,
    config: ResearchEventResolutionOutcomeSourceQuorumConfig | None = None,
    payload_items: tuple[ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem, ...] = (),
) -> ResearchEventResolutionOutcomeSourceQuorumReport:
    return build_research_event_resolution_outcome_source_quorum_report(
        inputs,
        generated_at=GENERATED_AT,
        config=config,
        public_payload=payload_items,
    )


def test_quorum_boundaries_classify_pass_watch_and_block_rows() -> None:
    readiness = report(
        source_input("pass", authoritative_source_count=d("3.000000")),
        source_input("watch", authoritative_source_count=d("2.000000")),
        source_input("block", authoritative_source_count=d("1.000000")),
    )

    rows_by_count = {row.authoritative_source_count: row for row in readiness.rows}
    assert readiness.status == "block"
    assert readiness.pass_count == d("1.000000")
    assert readiness.watch_count == d("1.000000")
    assert readiness.block_count == d("1.000000")
    assert rows_by_count[d("3.000000")].status == "pass"
    assert rows_by_count[d("3.000000")].reason_codes == (
        "resolution_outcome_source_quorum_pass",
    )
    assert rows_by_count[d("2.000000")].status == "watch"
    assert rows_by_count[d("2.000000")].reason_codes == (
        "authoritative_quorum_watch",
    )
    assert rows_by_count[d("1.000000")].status == "block"
    assert rows_by_count[d("1.000000")].reason_codes == (
        "insufficient_authoritative_quorum_block",
    )


def test_stale_sources_contradictions_and_deadline_proximity_apply_penalties() -> None:
    readiness = report(
        source_input(
            "stale-watch",
            oldest_source_age_seconds=d("90000.000000"),
        ),
        source_input(
            "stale-block",
            newest_source_age_seconds=d("90001.000000"),
            oldest_source_age_seconds=d("90001.000000"),
        ),
        source_input(
            "contradiction-watch",
            contradiction_pressure=d("0.250000"),
        ),
        source_input(
            "contradiction-block",
            contradiction_pressure=d("0.500000"),
        ),
        source_input(
            "deadline-watch",
            seconds_until_deadline=d("3600.000000"),
        ),
        source_input(
            "deadline-block",
            seconds_until_deadline=ZERO,
        ),
    )

    rows = {row.event_digest: row for row in readiness.rows}
    assert rows[digest("stale-watch-event")].status == "watch"
    assert "source_freshness_watch" in rows[digest("stale-watch-event")].reason_codes
    assert rows[digest("stale-block-event")].status == "block"
    assert "source_freshness_block" in rows[digest("stale-block-event")].reason_codes
    assert rows[digest("contradiction-watch-event")].status == "watch"
    assert "contradiction_pressure_watch" in rows[digest("contradiction-watch-event")].reason_codes
    assert rows[digest("contradiction-block-event")].status == "block"
    assert "contradiction_pressure_block" in rows[digest("contradiction-block-event")].reason_codes
    assert rows[digest("deadline-watch-event")].status == "watch"
    assert "deadline_proximity_watch" in rows[digest("deadline-watch-event")].reason_codes
    assert rows[digest("deadline-block-event")].status == "block"
    assert "deadline_proximity_block" in rows[digest("deadline-block-event")].reason_codes
    assert readiness.source_freshness_penalty_count == d("2.000000")
    assert readiness.contradiction_pressure_count == d("2.000000")
    assert readiness.deadline_proximity_count == d("2.000000")


def test_public_payload_and_digest_are_deterministic_decimal_only_and_validated() -> None:
    payload_item = ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem(
        key="safe_context",
        value="sanitized digest inputs only",
    )
    first = report(
        source_input("zeta"),
        source_input("alpha", contradiction_pressure=d("0.250000")),
        payload_items=(payload_item,),
    )
    second = report(
        source_input("alpha", contradiction_pressure=d("0.250000")),
        source_input("zeta"),
        payload_items=(payload_item,),
    )

    first_payload = research_event_resolution_outcome_source_quorum_public_payload(first)
    second_payload = second.payload
    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["row_count"] == "2.000000"
    assert first_payload["rows"][0]["readiness_score"] == "0.849861"
    assert first_payload["rows"][1]["contradiction_pressure"] == "0.250000"
    json.dumps(first_payload, sort_keys=True)
    assert_no_float(first_payload)
    assert_no_non_decimal_public_numbers(first)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_leak_prevention_rejects_raw_identifiers_and_unsafe_public_payloads() -> None:
    with pytest.raises(ValueError, match="sha256"):
        ResearchEventResolutionOutcomeSourceQuorumInput(
            event_digest="raw-candidate-id",
            outcome_digest=digest("outcome"),
            authoritative_source_count=d("3.000000"),
            newest_source_age_seconds=d("600.000000"),
            oldest_source_age_seconds=d("1200.000000"),
            contradiction_pressure=d("0.100000"),
            seconds_until_deadline=d("172800.000000"),
        )

    for key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "auth",
        "wallet",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "candidate-id",
        "market.slug",
        "source url",
        "source.text",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem(
                key=key,
                value="safe value",
            )

    for value in (
        "https://example.test/source",
        "postgres://user:pass@example.test/db",
        "wallet surface",
        "place order",
        "trade execution",
        "raw question text",
        "authorization token",
        "live trading enabled",
        "buy outcome",
        "sell outcome",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem(
                key="safe_key",
                value=value,
            )

    payload = report(source_input("safe")).payload
    encoded = json.dumps(payload, sort_keys=True).lower()
    for leaked in (
        "raw-candidate-id",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
        "postgres://",
        "wallet surface",
        "place order",
        "trade execution",
    ):
        assert leaked not in encoded


def test_custom_threshold_validation_and_flags_are_enforced() -> None:
    custom = ResearchEventResolutionOutcomeSourceQuorumConfig(
        pass_authoritative_source_count=d("4.000000"),
        watch_authoritative_source_count=d("3.000000"),
        max_fresh_source_age_seconds=d("7200.000000"),
        deadline_watch_seconds=d("7200.000000"),
        deadline_block_seconds=d("600.000000"),
        min_readiness_score=d("0.750000"),
    )
    readiness = report(
        source_input(
            "custom-watch",
            authoritative_source_count=d("3.000000"),
            oldest_source_age_seconds=d("3600.000000"),
            seconds_until_deadline=d("8000.000000"),
        ),
        config=custom,
    )

    assert readiness.status == "watch"
    assert readiness.rows[0].status == "watch"
    assert readiness.rows[0].reason_codes == ("authoritative_quorum_watch",)

    with pytest.raises(ValueError, match="watch_authoritative_source_count"):
        ResearchEventResolutionOutcomeSourceQuorumConfig(
            pass_authoritative_source_count=d("2.000000"),
            watch_authoritative_source_count=d("3.000000"),
        )
    with pytest.raises(ValueError, match="deadline_block_seconds"):
        ResearchEventResolutionOutcomeSourceQuorumConfig(
            deadline_watch_seconds=d("600.000000"),
            deadline_block_seconds=d("7200.000000"),
        )
    with pytest.raises(ValueError, match="weights"):
        ResearchEventResolutionOutcomeSourceQuorumConfig(
            quorum_weight=d("0.500000"),
            freshness_weight=d("0.250000"),
            contradiction_weight=d("0.200000"),
            deadline_weight=d("0.200000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        ResearchEventResolutionOutcomeSourceQuorumConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        source_input("flags", report_only=False)

    frozen = report(source_input("frozen"))
    with pytest.raises(FrozenInstanceError):
        frozen.status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadReport(ResearchEventResolutionOutcomeSourceQuorumReport):
            pass


def test_public_exports_and_field_names_avoid_forbidden_surfaces() -> None:
    assert api.__all__ == (
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_OUTCOME_SOURCE_QUORUM_CONFIG_VERSION",
        "ResearchEventResolutionOutcomeSourceQuorumConfig",
        "ResearchEventResolutionOutcomeSourceQuorumInput",
        "ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem",
        "ResearchEventResolutionOutcomeSourceQuorumReport",
        "ResearchEventResolutionOutcomeSourceQuorumRow",
        "build_research_event_resolution_outcome_source_quorum_report",
        "research_event_resolution_outcome_source_quorum_public_payload",
    )
    for public_name in api.__all__:
        assert not contains_forbidden_public_surface(public_name)

    for public_type in (
        ResearchEventResolutionOutcomeSourceQuorumConfig,
        ResearchEventResolutionOutcomeSourceQuorumInput,
        ResearchEventResolutionOutcomeSourceQuorumPublicPayloadItem,
        api.ResearchEventResolutionOutcomeSourceQuorumRow,
        ResearchEventResolutionOutcomeSourceQuorumReport,
    ):
        for field in fields(public_type):
            assert not contains_forbidden_public_surface(field.name)

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


def assert_no_float(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"payload contains float: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            assert_no_non_decimal_public_numbers(getattr(value, field.name))


def contains_forbidden_public_surface(value: str) -> bool:
    lowered = value.lower()
    if any(
        phrase in lowered
        for phrase in (
            "candidate_id",
            "market_id",
            "market_slug",
            "source_url",
            "source_text",
            "table_name",
        )
    ):
        return True
    tokens = tuple(token for token in lowered.replace("_", " ").split() if token)
    forbidden_tokens = frozenset(
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
            "live",
            "buy",
            "sell",
            "recommendation",
            "sizing",
        ),
    )
    return any(token in forbidden_tokens for token in tokens)
