from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_settlement_evidence_packet_report as api
from polymarket_alpha_lab.research_settlement_evidence_packet_report import (
    ResearchSettlementAmbiguityPoint,
    ResearchSettlementEvidenceItem,
    ResearchSettlementEvidencePacketConfig,
    ResearchSettlementEvidencePacketPublicPayloadItem,
    ResearchSettlementEvidencePacketReport,
    ResearchSettlementEvidencePacketRow,
    ResearchSettlementReviewState,
    ResearchSettlementRuleMapping,
    build_research_settlement_evidence_packet_report,
)


NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)
SETTLES_AT = NOW + timedelta(hours=6)


def _evidence(
    *,
    packet_id: str = "packet_a",
    event_id: str = "event_a",
    evidence_id: str = "evidence_result",
    evidence_type: str = "official_result",
    source_id: str = "official_source",
    source_family: str = "official",
    supports_resolution: bool = True,
    relevance_score: Decimal = Decimal("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSettlementEvidenceItem:
    return ResearchSettlementEvidenceItem(
        packet_id=packet_id,
        event_id=event_id,
        evidence_id=evidence_id,
        evidence_type=evidence_type,
        source_id=source_id,
        source_family=source_family,
        observed_at=NOW - timedelta(minutes=10),
        relevance_score=relevance_score,
        supports_resolution=supports_resolution,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _rule_mapping(
    *,
    packet_id: str = "packet_a",
    event_id: str = "event_a",
    rule_id: str = "rule_result",
    evidence_id: str = "evidence_result",
    mapping_status: str = "mapped",
) -> ResearchSettlementRuleMapping:
    return ResearchSettlementRuleMapping(
        packet_id=packet_id,
        event_id=event_id,
        rule_id=rule_id,
        evidence_id=evidence_id,
        mapping_status=mapping_status,
    )


def _review(
    *,
    packet_id: str = "packet_a",
    event_id: str = "event_a",
    review_status: str = "approved",
    reviewer_count: Decimal = Decimal("2.000000"),
) -> ResearchSettlementReviewState:
    return ResearchSettlementReviewState(
        packet_id=packet_id,
        event_id=event_id,
        review_status=review_status,
        reviewer_count=reviewer_count,
        reviewed_at=NOW - timedelta(minutes=5),
    )


def _report(
    evidence: tuple[ResearchSettlementEvidenceItem, ...],
    *,
    rule_mappings: tuple[ResearchSettlementRuleMapping, ...] | None = None,
    ambiguity_points: tuple[ResearchSettlementAmbiguityPoint, ...] = (),
    review_states: tuple[ResearchSettlementReviewState, ...] | None = None,
    config: ResearchSettlementEvidencePacketConfig | None = None,
    settlement_due_at: datetime = SETTLES_AT,
    public_payload: tuple[ResearchSettlementEvidencePacketPublicPayloadItem, ...] = (),
) -> ResearchSettlementEvidencePacketReport:
    return build_research_settlement_evidence_packet_report(
        evidence,
        rule_mappings=(
            rule_mappings
            if rule_mappings is not None
            else (
                _rule_mapping(rule_id="rule_result", evidence_id="evidence_result"),
                _rule_mapping(rule_id="rule_source", evidence_id="evidence_source"),
            )
        ),
        ambiguity_points=ambiguity_points,
        review_states=review_states if review_states is not None else (_review(),),
        generated_at=NOW,
        settlement_due_at=settlement_due_at,
        config=config,
        public_payload=public_payload,
    )


def test_settlement_evidence_packet_passes_when_complete_independent_mapped_and_reviewed() -> None:
    report = _report(
        (
            _evidence(
                evidence_id="evidence_result",
                evidence_type="official_result",
                source_id="official_source",
                source_family="official",
            ),
            _evidence(
                evidence_id="evidence_source",
                evidence_type="resolution_rule",
                source_id="venue_source",
                source_family="venue",
            ),
            _evidence(
                evidence_id="evidence_time",
                evidence_type="settlement_time",
                source_id="calendar_source",
                source_family="calendar",
            ),
        ),
    )

    row = report.rows[0]
    assert report.packet_status == "pass"
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert row.packet_status == "pass"
    assert row.evidence_completeness_score == Decimal("1.000000")
    assert row.source_independence_score == Decimal("1.000000")
    assert row.rule_mapping_score == Decimal("1.000000")
    assert row.open_ambiguity_count == Decimal("0.000000")
    assert row.review_status == "approved"
    assert row.settlement_hours_remaining == Decimal("6.000000")
    assert "settlement_evidence_packet_pass" in row.reason_codes
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_missing_evidence_and_incomplete_rule_mapping_produce_watch() -> None:
    report = _report(
        (
            _evidence(
                evidence_id="evidence_result",
                evidence_type="official_result",
                source_id="official_source",
                source_family="official",
            ),
        ),
        rule_mappings=(
            _rule_mapping(
                rule_id="rule_result",
                evidence_id="evidence_result",
                mapping_status="mapped",
            ),
            _rule_mapping(
                rule_id="rule_source",
                evidence_id="evidence_missing",
                mapping_status="partial",
            ),
        ),
        review_states=(_review(review_status="needs_review", reviewer_count=Decimal("1.000000")),),
    )

    row = report.rows[0]
    assert report.packet_status == "watch"
    assert report.watch_count == Decimal("1.000000")
    assert row.packet_status == "watch"
    assert row.evidence_completeness_score == Decimal("0.333333")
    assert row.source_family_count == Decimal("1.000000")
    assert row.rule_mapping_score == Decimal("0.500000")
    assert row.reviewer_count == Decimal("1.000000")
    assert "evidence_incomplete" in row.reason_codes
    assert "source_independence_watch" in row.reason_codes
    assert "rule_mapping_partial" in row.reason_codes
    assert "review_pending" in row.reason_codes


def test_unresolved_high_severity_ambiguity_blocks_packet() -> None:
    report = _report(
        (
            _evidence(
                evidence_id="evidence_result",
                evidence_type="official_result",
                source_id="official_source",
                source_family="official",
            ),
            _evidence(
                evidence_id="evidence_source",
                evidence_type="resolution_rule",
                source_id="venue_source",
                source_family="venue",
            ),
            _evidence(
                evidence_id="evidence_time",
                evidence_type="settlement_time",
                source_id="calendar_source",
                source_family="calendar",
            ),
        ),
        ambiguity_points=(
            ResearchSettlementAmbiguityPoint(
                packet_id="packet_a",
                event_id="event_a",
                ambiguity_id="ambiguous_overtime_rule",
                severity_score=Decimal("0.900000"),
                resolved=False,
            ),
        ),
    )

    row = report.rows[0]
    assert report.packet_status == "block"
    assert report.block_count == Decimal("1.000000")
    assert row.packet_status == "block"
    assert row.open_ambiguity_count == Decimal("1.000000")
    assert row.max_open_ambiguity_severity == Decimal("0.900000")
    assert "unresolved_ambiguity_block" in row.reason_codes


def test_payload_serializes_decimal_values_as_strings_and_digest_detects_tampering() -> None:
    report = _report(
        (
            _evidence(
                evidence_id="evidence_result",
                evidence_type="official_result",
                source_id="official_source",
                source_family="official",
            ),
            _evidence(
                evidence_id="evidence_source",
                evidence_type="resolution_rule",
                source_id="venue_source",
                source_family="venue",
            ),
            _evidence(
                evidence_id="evidence_time",
                evidence_type="settlement_time",
                source_id="calendar_source",
                source_family="calendar",
            ),
        ),
        public_payload=(
            ResearchSettlementEvidencePacketPublicPayloadItem("safe_context", "settlement packet"),
        ),
    )

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["packet_count"] == "1.000000"
    assert payload["settlement_hours_remaining_min"] == "6.000000"
    assert payload["rows"][0]["source_independence_score"] == "1.000000"
    assert payload["generated_at"] == "2026-01-01T12:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_dataclasses_are_frozen_reject_subclassing_and_enforce_decimal_only() -> None:
    report = _report(
        (
            _evidence(
                evidence_id="evidence_result",
                evidence_type="official_result",
                source_id="official_source",
                source_family="official",
            ),
            _evidence(
                evidence_id="evidence_source",
                evidence_type="resolution_rule",
                source_id="venue_source",
                source_family="venue",
            ),
            _evidence(
                evidence_id="evidence_time",
                evidence_type="settlement_time",
                source_id="calendar_source",
                source_family="calendar",
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.packet_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchSettlementEvidencePacketConfig):
            pass

    with pytest.raises(ValueError, match="Decimal"):
        ResearchSettlementEvidenceItem(
            packet_id="packet_a",
            event_id="event_a",
            evidence_id="evidence_result",
            evidence_type="official_result",
            source_id="official_source",
            source_family="official",
            observed_at=NOW,
            relevance_score=0.9,  # type: ignore[arg-type]
        )


def test_hard_flags_and_public_payload_safety_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchSettlementEvidencePacketConfig(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        _evidence(readonly=False)  # type: ignore[call-arg]

    for key in (
        "live_key",
        "auth_key",
        "wallet_key",
        "order_key",
        "network_key",
        "database_key",
        "persist_key",
        "signing_key",
        "mutation_key",
        "buy_key",
        "sell_key",
        "trade_key",
        "advice_key",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchSettlementEvidencePacketPublicPayloadItem(key, "safe value")

    for value in (
        "live item",
        "auth item",
        "wallet item",
        "order item",
        "network item",
        "database item",
        "persist item",
        "signing item",
        "mutation item",
        "buy item",
        "sell item",
        "trade item",
        "investment advice",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchSettlementEvidencePacketPublicPayloadItem("safe_key", value)


def test_no_unsafe_public_surfaces_or_external_write_clients_are_exposed() -> None:
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
        "advice",
        "recommendation",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ResearchSettlementEvidencePacketConfig,
        ResearchSettlementEvidenceItem,
        ResearchSettlementRuleMapping,
        ResearchSettlementAmbiguityPoint,
        ResearchSettlementReviewState,
        ResearchSettlementEvidencePacketPublicPayloadItem,
        ResearchSettlementEvidencePacketRow,
        ResearchSettlementEvidencePacketReport,
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
