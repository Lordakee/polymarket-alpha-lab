from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json

import pytest

import polymarket_alpha_lab.research_event_resolution_evidence_recency_quorum_report as api
from polymarket_alpha_lab.research_event_resolution_evidence_recency_quorum_report import (
    RESEARCH_EVENT_RESOLUTION_EVIDENCE_RECENCY_QUORUM_STATUSES,
    ResearchEventResolutionEvidenceRecencyQuorumConfig,
    ResearchEventResolutionEvidenceRecencyQuorumInput,
    ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem,
    ResearchEventResolutionEvidenceRecencyQuorumReport,
    ResearchEventResolutionEvidenceRecencyQuorumRow,
    build_research_event_resolution_evidence_recency_quorum_report,
    research_event_resolution_evidence_recency_quorum_public_payload,
    research_event_resolution_evidence_recency_quorum_report_digest,
    validate_research_event_resolution_evidence_recency_quorum_public_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def evidence_input(
    seed: str = "event-a",
    *,
    recent_evidence_count: Decimal = d("3.000000"),
    independent_evidence_count: Decimal = d("2.000000"),
    newest_evidence_age_seconds: Decimal = d("600.000000"),
    oldest_evidence_age_seconds: Decimal = d("1200.000000"),
    conflict_pressure: Decimal = d("0.100000"),
    resolution_update_latency_seconds: Decimal = d("600.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventResolutionEvidenceRecencyQuorumInput:
    return ResearchEventResolutionEvidenceRecencyQuorumInput(
        event_digest=digest(f"{seed}-event"),
        resolution_digest=digest(f"{seed}-resolution"),
        evidence_packet_digest=digest(f"{seed}-evidence"),
        recent_evidence_count=recent_evidence_count,
        independent_evidence_count=independent_evidence_count,
        newest_evidence_age_seconds=newest_evidence_age_seconds,
        oldest_evidence_age_seconds=oldest_evidence_age_seconds,
        conflict_pressure=conflict_pressure,
        resolution_update_latency_seconds=resolution_update_latency_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *inputs: ResearchEventResolutionEvidenceRecencyQuorumInput,
    config: ResearchEventResolutionEvidenceRecencyQuorumConfig | None = None,
    payload_items: tuple[ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem, ...] = (),
) -> ResearchEventResolutionEvidenceRecencyQuorumReport:
    return build_research_event_resolution_evidence_recency_quorum_report(
        inputs,
        generated_at=GENERATED_AT,
        config=config,
        public_payload=payload_items,
    )


def test_quorum_boundaries_classify_pass_watch_and_block_rows() -> None:
    readiness = report(
        evidence_input("pass"),
        evidence_input("recent-watch", recent_evidence_count=d("2.000000")),
        evidence_input(
            "block",
            recent_evidence_count=d("1.000000"),
            independent_evidence_count=ZERO,
        ),
    )

    rows = {row.event_digest: row for row in readiness.rows}
    assert readiness.status == "block"
    assert readiness.pass_count == d("1.000000")
    assert readiness.watch_count == d("1.000000")
    assert readiness.block_count == d("1.000000")
    assert rows[digest("pass-event")].status == "pass"
    assert rows[digest("pass-event")].reason_codes == ("evidence_recency_quorum_pass",)
    assert rows[digest("recent-watch-event")].status == "watch"
    assert rows[digest("recent-watch-event")].reason_codes == (
        "recent_evidence_quorum_watch",
    )
    assert rows[digest("block-event")].status == "block"
    assert rows[digest("block-event")].reason_codes == (
        "insufficient_recent_evidence_quorum_block",
        "insufficient_independent_evidence_quorum_block",
    )
    assert readiness.insufficient_quorum_count == d("2.000000")


def test_recency_conflict_and_latency_thresholds_apply_penalties() -> None:
    readiness = report(
        evidence_input(
            "recency-watch",
            oldest_evidence_age_seconds=d("90000.000000"),
        ),
        evidence_input(
            "recency-block",
            newest_evidence_age_seconds=d("259201.000000"),
            oldest_evidence_age_seconds=d("259201.000000"),
        ),
        evidence_input("conflict-watch", conflict_pressure=d("0.250000")),
        evidence_input("conflict-block", conflict_pressure=d("0.500000")),
        evidence_input(
            "latency-watch",
            resolution_update_latency_seconds=d("7200.000000"),
        ),
        evidence_input(
            "latency-block",
            resolution_update_latency_seconds=d("21600.000000"),
        ),
    )

    rows = {row.event_digest: row for row in readiness.rows}
    assert rows[digest("recency-watch-event")].status == "watch"
    assert "evidence_recency_watch" in rows[digest("recency-watch-event")].reason_codes
    assert rows[digest("recency-block-event")].status == "block"
    assert "evidence_recency_block" in rows[digest("recency-block-event")].reason_codes
    assert rows[digest("conflict-watch-event")].status == "watch"
    assert "conflict_pressure_watch" in rows[digest("conflict-watch-event")].reason_codes
    assert rows[digest("conflict-block-event")].status == "block"
    assert "conflict_pressure_block" in rows[digest("conflict-block-event")].reason_codes
    assert rows[digest("latency-watch-event")].status == "watch"
    assert "update_latency_watch" in rows[digest("latency-watch-event")].reason_codes
    assert rows[digest("latency-block-event")].status == "block"
    assert "update_latency_block" in rows[digest("latency-block-event")].reason_codes
    assert readiness.stale_evidence_count == d("2.000000")
    assert readiness.conflict_pressure_count == d("2.000000")
    assert readiness.update_latency_count == d("2.000000")


def test_public_payload_digest_validation_and_decimal_only_contract() -> None:
    payload_item = ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem(
        key="safe_context",
        value="sanitized digest evidence only",
    )
    first = report(
        evidence_input("zeta"),
        evidence_input("alpha", recent_evidence_count=d("2.000000")),
        payload_items=(payload_item,),
    )
    second = report(
        evidence_input("alpha", recent_evidence_count=d("2.000000")),
        evidence_input("zeta"),
        payload_items=(payload_item,),
    )

    first_payload = research_event_resolution_evidence_recency_quorum_public_payload(first)
    second_payload = second.payload
    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert research_event_resolution_evidence_recency_quorum_report_digest(first) == (
        first.derived_validation_digest
    )
    assert validate_research_event_resolution_evidence_recency_quorum_public_payload(
        first_payload,
    ) == first_payload
    assert first_payload["row_count"] == "2.000000"
    assert first_payload["rows"][0]["recency_quorum_score"] == "0.970000"
    assert first_payload["rows"][1]["conflict_pressure"] == "0.100000"
    json.dumps(first_payload, sort_keys=True)
    assert_no_float(first_payload)
    assert_no_non_decimal_public_numbers(first)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered = dict(first_payload)
    tampered["pass_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_event_resolution_evidence_recency_quorum_public_payload(
            tampered,
        )


def test_leak_prevention_rejects_raw_identifiers_and_unsafe_public_payloads() -> None:
    with pytest.raises(ValueError, match="sha256"):
        ResearchEventResolutionEvidenceRecencyQuorumInput(
            event_digest="raw-candidate-id",
            resolution_digest=digest("resolution"),
            evidence_packet_digest=digest("evidence"),
            recent_evidence_count=d("3.000000"),
            independent_evidence_count=d("2.000000"),
            newest_evidence_age_seconds=d("600.000000"),
            oldest_evidence_age_seconds=d("1200.000000"),
            conflict_pressure=d("0.100000"),
            resolution_update_latency_seconds=d("600.000000"),
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
        "wallet",
        "order",
        "trade",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem(
                key=key,
                value="safe value",
            )

    for value in (
        "https://example.test/private",
        "postgres://user:pass@example.test/db",
        "market-alpha raw locator",
        "wallet surface",
        "place order",
        "trade execution",
        "raw question text",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem(
                key="safe_key",
                value=value,
            )

    payload = report(evidence_input("safe")).payload
    encoded = json.dumps(payload, sort_keys=True).lower()
    for leaked in (
        "raw-candidate-id",
        "market-alpha",
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


def test_custom_threshold_validation_flags_and_frozen_types_are_enforced() -> None:
    custom = ResearchEventResolutionEvidenceRecencyQuorumConfig(
        pass_recent_evidence_count=d("4.000000"),
        watch_recent_evidence_count=d("3.000000"),
        pass_independent_evidence_count=d("3.000000"),
        watch_independent_evidence_count=d("2.000000"),
        min_recency_quorum_score=d("0.980000"),
    )
    readiness = report(
        evidence_input(
            "custom-watch",
            recent_evidence_count=d("4.000000"),
            independent_evidence_count=d("3.000000"),
        ),
        config=custom,
    )

    assert readiness.status == "watch"
    assert readiness.rows[0].reason_codes == ("recency_quorum_score_watch",)

    with pytest.raises(ValueError, match="watch_recent_evidence_count"):
        ResearchEventResolutionEvidenceRecencyQuorumConfig(
            pass_recent_evidence_count=d("2.000000"),
            watch_recent_evidence_count=d("3.000000"),
        )
    with pytest.raises(ValueError, match="update_latency_watch_seconds"):
        ResearchEventResolutionEvidenceRecencyQuorumConfig(
            update_latency_watch_seconds=d("21600.000000"),
            update_latency_block_seconds=d("7200.000000"),
        )
    with pytest.raises(ValueError, match="weights"):
        ResearchEventResolutionEvidenceRecencyQuorumConfig(
            quorum_weight=d("0.500000"),
            recency_weight=d("0.350000"),
            conflict_weight=d("0.150000"),
            latency_weight=d("0.100000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        ResearchEventResolutionEvidenceRecencyQuorumConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        evidence_input("flags", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        evidence_input("flags", readonly=False)

    frozen = report(evidence_input("frozen"))
    with pytest.raises(FrozenInstanceError):
        frozen.status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadReport(ResearchEventResolutionEvidenceRecencyQuorumReport):
            pass


def test_public_dataclasses_statuses_empty_report_and_exports_are_safe() -> None:
    empty = report()
    assert RESEARCH_EVENT_RESOLUTION_EVIDENCE_RECENCY_QUORUM_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert empty.status == "block"
    assert empty.row_count == ZERO
    assert empty.reason_codes == ("empty_evidence_recency_quorum_set",)
    validate_research_event_resolution_evidence_recency_quorum_public_payload(
        empty.payload,
    )

    for public_dataclass in (
        ResearchEventResolutionEvidenceRecencyQuorumConfig,
        ResearchEventResolutionEvidenceRecencyQuorumInput,
        ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem,
        ResearchEventResolutionEvidenceRecencyQuorumRow,
        ResearchEventResolutionEvidenceRecencyQuorumReport,
    ):
        assert is_dataclass(public_dataclass)
        assert public_dataclass.__dataclass_params__.frozen is True

    for value in (
        ResearchEventResolutionEvidenceRecencyQuorumConfig(),
        evidence_input("flags-ok"),
        report(evidence_input("row-ok")).rows[0],
        report(evidence_input("report-ok")),
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True

    assert api.__all__ == (
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_RECENCY_QUORUM_CONFIG_VERSION",
        "RESEARCH_EVENT_RESOLUTION_EVIDENCE_RECENCY_QUORUM_STATUSES",
        "ResearchEventResolutionEvidenceRecencyQuorumConfig",
        "ResearchEventResolutionEvidenceRecencyQuorumInput",
        "ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem",
        "ResearchEventResolutionEvidenceRecencyQuorumReport",
        "ResearchEventResolutionEvidenceRecencyQuorumRow",
        "build_research_event_resolution_evidence_recency_quorum_report",
        "research_event_resolution_evidence_recency_quorum_public_payload",
        "research_event_resolution_evidence_recency_quorum_report_digest",
        "validate_research_event_resolution_evidence_recency_quorum_public_payload",
    )
    for public_name in api.__all__:
        assert not contains_forbidden_public_surface(public_name)

    for public_type in (
        ResearchEventResolutionEvidenceRecencyQuorumConfig,
        ResearchEventResolutionEvidenceRecencyQuorumInput,
        ResearchEventResolutionEvidenceRecencyQuorumPublicPayloadItem,
        ResearchEventResolutionEvidenceRecencyQuorumRow,
        ResearchEventResolutionEvidenceRecencyQuorumReport,
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


def test_decimal_only_inputs_and_status_vocabulary_are_enforced() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        evidence_input(conflict_pressure=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="whole-number Decimal"):
        evidence_input(recent_evidence_count=d("1.500000"))
    with pytest.raises(ValueError, match="status"):
        replace(report(evidence_input("status")).rows[0], status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(report(evidence_input("status-report")), status="blocked")


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
