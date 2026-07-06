from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_packet_source_family_independence_gate_v2 as api
from polymarket_alpha_lab.research_packet_source_family_independence_gate_v2 import (
    ResearchPacketSourceFamilyEvidence,
    ResearchPacketSourceFamilyIndependenceGateConfig,
    ResearchPacketSourceFamilyIndependenceGateReport,
    ResearchPacketSourceFamilyIndependenceGateRow,
    ResearchPacketSourceFamilyPublicPayloadItem,
    build_research_packet_source_family_independence_gate_v2_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _evidence(
    *,
    packet_id: str = "packet_a",
    claim_id: str = "claim_a",
    source_id: str = "source_a",
    source_family: str = "official",
    confidence_score: Decimal = Decimal("0.700000"),
    corroborates_claim: bool = True,
) -> ResearchPacketSourceFamilyEvidence:
    return ResearchPacketSourceFamilyEvidence(
        packet_id=packet_id,
        claim_id=claim_id,
        source_id=source_id,
        source_family=source_family,
        observed_at=NOW,
        confidence_score=confidence_score,
        corroborates_claim=corroborates_claim,
    )


def _report(
    evidence: tuple[ResearchPacketSourceFamilyEvidence, ...],
    *,
    config: ResearchPacketSourceFamilyIndependenceGateConfig | None = None,
    public_payload: tuple[ResearchPacketSourceFamilyPublicPayloadItem, ...] = (),
) -> ResearchPacketSourceFamilyIndependenceGateReport:
    return build_research_packet_source_family_independence_gate_v2_report(
        evidence,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_source_family_independence_passes_with_distinct_families() -> None:
    report = _report(
        (
            _evidence(source_id="source_a", source_family="official"),
            _evidence(source_id="source_b", source_family="primary"),
        ),
    )

    row = report.rows[0]
    assert report.gate_status == "pass"
    assert report.packet_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert row.source_count == Decimal("2.000000")
    assert row.source_family_count == Decimal("2.000000")
    assert row.duplicate_source_family_count == Decimal("0.000000")
    assert row.independent_corroboration_count == Decimal("1.000000")
    assert row.gate_status == "pass"
    assert "source_family_independence_pass" in row.reason_codes
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_duplicate_family_penalties_are_reported() -> None:
    config = ResearchPacketSourceFamilyIndependenceGateConfig(
        duplicate_family_penalty_per_source=Decimal("0.200000"),
    )

    report = _report(
        (
            _evidence(source_id="source_a", source_family="official"),
            _evidence(source_id="source_b", source_family="official"),
        ),
        config=config,
    )

    row = report.rows[0]
    assert report.gate_status == "watch"
    assert row.source_family_count == Decimal("1.000000")
    assert row.duplicate_source_family_count == Decimal("1.000000")
    assert row.duplicate_family_penalty == Decimal("0.200000")
    assert row.independence_score == Decimal("0.500000")
    assert row.gate_status == "watch"
    assert "duplicate_source_family_penalty" in row.reason_codes
    assert "insufficient_source_family_independence" in row.reason_codes


def test_independent_corroboration_boosts_score() -> None:
    single_family = _report(
        (
            _evidence(
                source_id="source_a",
                source_family="official",
                confidence_score=Decimal("0.600000"),
            ),
        ),
    )
    distinct_families = _report(
        (
            _evidence(
                source_id="source_a",
                source_family="official",
                confidence_score=Decimal("0.600000"),
            ),
            _evidence(
                source_id="source_b",
                source_family="primary",
                confidence_score=Decimal("0.600000"),
            ),
        ),
    )

    single_row = single_family.rows[0]
    boosted_row = distinct_families.rows[0]
    assert single_row.independent_corroboration_boost == Decimal("0.000000")
    assert boosted_row.independent_corroboration_boost == Decimal("0.100000")
    assert boosted_row.independence_score > single_row.independence_score
    assert "independent_corroboration_boost" in boosted_row.reason_codes


def test_payload_serializes_decimals_as_strings_and_is_json_ready() -> None:
    report = _report(
        (
            _evidence(source_id="source_a", source_family="official"),
            _evidence(source_id="source_b", source_family="primary"),
        ),
        public_payload=(ResearchPacketSourceFamilyPublicPayloadItem("safe_key", "safe value"),),
    )

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["packet_count"] == "1.000000"
    assert payload["average_independence_score"] == "0.800000"
    assert payload["rows"][0]["source_count"] == "2.000000"
    assert payload["rows"][0]["independent_corroboration_boost"] == "0.100000"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = _report(
        (
            _evidence(source_id="source_a", source_family="official"),
            _evidence(source_id="source_b", source_family="primary"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.gate_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchPacketSourceFamilyIndependenceGateConfig):
            pass


def test_hard_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchPacketSourceFamilyIndependenceGateConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        ResearchPacketSourceFamilyEvidence(
            packet_id="packet_a",
            claim_id="claim_a",
            source_id="source_a",
            source_family="official",
            observed_at=NOW,
            confidence_score=Decimal("0.700000"),
            report_only=False,
        )

    report = _report(
        (
            _evidence(source_id="source_a", source_family="official"),
            _evidence(source_id="source_b", source_family="primary"),
        ),
    )
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = _report(
        (
            _evidence(source_id="source_a", source_family="official"),
            _evidence(source_id="source_b", source_family="primary"),
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchPacketSourceFamilyPublicPayloadItem("safe_key", "changed value"),
            ),
        )


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
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
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchPacketSourceFamilyPublicPayloadItem(key, "safe value")

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
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchPacketSourceFamilyPublicPayloadItem("safe_key", value)

    with pytest.raises(ValueError, match="unsafe public"):
        _evidence(source_id="buy_signal")


def test_no_unsafe_public_surfaces_are_exposed() -> None:
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
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ResearchPacketSourceFamilyIndependenceGateConfig,
        ResearchPacketSourceFamilyEvidence,
        ResearchPacketSourceFamilyPublicPayloadItem,
        ResearchPacketSourceFamilyIndependenceGateRow,
        ResearchPacketSourceFamilyIndependenceGateReport,
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
