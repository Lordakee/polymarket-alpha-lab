from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_packet_source_family_independence_score_v2 as api
from polymarket_alpha_lab.research_packet_source_family_independence_score_v2 import (
    ResearchPacketSourceFamilyIndependenceScoreConfig,
    ResearchPacketSourceFamilyIndependenceScoreReport,
    ResearchPacketSourceFamilyIndependenceScoreSource,
    build_research_packet_source_family_independence_score_v2_report,
)


def _source(
    *,
    packet_id: str = "packet_a",
    source_id: str = "source_a",
    source_family: str = "official",
    owner_family: str = "owner_a",
    derivation_family: str | None = None,
    claim_fingerprint: str = "claim_a",
    is_official_source: bool = False,
    source_age_seconds: Decimal = Decimal("3600.000000"),
    contradiction_severity: Decimal = Decimal("0.000000"),
) -> ResearchPacketSourceFamilyIndependenceScoreSource:
    return ResearchPacketSourceFamilyIndependenceScoreSource(
        packet_id=packet_id,
        source_id=source_id,
        source_family=source_family,
        owner_family=owner_family,
        derivation_family=derivation_family,
        claim_fingerprint=claim_fingerprint,
        is_official_source=is_official_source,
        source_age_seconds=source_age_seconds,
        contradiction_severity=contradiction_severity,
    )


def _report(
    sources: tuple[ResearchPacketSourceFamilyIndependenceScoreSource, ...],
    *,
    packet_id: str = "packet_a",
    config: ResearchPacketSourceFamilyIndependenceScoreConfig | None = None,
) -> ResearchPacketSourceFamilyIndependenceScoreReport:
    return build_research_packet_source_family_independence_score_v2_report(
        sources,
        packet_id=packet_id,
        config=config,
    )


def test_score_rewards_distinct_independent_families_and_is_reorder_stable() -> None:
    sources = (
        _source(
            source_id="source_a",
            source_family="official",
            owner_family="owner_a",
            claim_fingerprint="claim_a",
            is_official_source=True,
        ),
        _source(
            source_id="source_b",
            source_family="primary",
            owner_family="owner_b",
            claim_fingerprint="claim_b",
            is_official_source=True,
        ),
        _source(
            source_id="source_c",
            source_family="secondary",
            owner_family="owner_c",
            claim_fingerprint="claim_c",
        ),
        _source(
            source_id="source_d",
            source_family="analysis",
            owner_family="owner_d",
            claim_fingerprint="claim_d",
        ),
    )

    report = _report(sources)
    reordered_report = _report(tuple(reversed(sources)))

    assert report.source_count == Decimal("4.000000")
    assert report.distinct_source_family_count == Decimal("4.000000")
    assert report.family_count_score == Decimal("1.000000")
    assert report.shared_ownership_derivation_risk == Decimal("0.000000")
    assert report.official_source_coverage == Decimal("0.500000")
    assert report.duplicate_claim_ratio == Decimal("0.000000")
    assert report.stale_source_ratio == Decimal("0.000000")
    assert report.contradiction_severity == Decimal("0.000000")
    assert report.independence_score == Decimal("0.925000")
    assert report.score_status == "strong"
    assert report.reason_codes == (
        "family_count_met",
        "ownership_derivation_clear",
        "official_source_covered",
        "duplicate_claims_clear",
        "sources_current",
        "contradictions_clear",
        "independence_score_strong",
    )
    assert report.source_evidence_digest == reordered_report.source_evidence_digest
    assert report.derived_validation_digest == reordered_report.derived_validation_digest


def test_risk_dimensions_reduce_score_with_deterministic_reasons() -> None:
    report = _report(
        (
            _source(
                source_id="source_a",
                source_family="official",
                owner_family="owner_a",
                derivation_family="base_a",
                claim_fingerprint="claim_a",
                is_official_source=True,
            ),
            _source(
                source_id="source_b",
                source_family="primary",
                owner_family="owner_a",
                derivation_family="base_a",
                claim_fingerprint="claim_a",
                source_age_seconds=Decimal("172801.000000"),
                contradiction_severity=Decimal("0.400000"),
            ),
            _source(
                source_id="source_c",
                source_family="secondary",
                owner_family="owner_b",
                claim_fingerprint="claim_b",
                contradiction_severity=Decimal("0.800000"),
            ),
            _source(
                source_id="source_d",
                source_family="analysis",
                owner_family="owner_c",
                derivation_family="base_d",
                claim_fingerprint="claim_c",
                source_age_seconds=Decimal("200000.000000"),
            ),
        ),
    )

    assert report.distinct_source_family_count == Decimal("4.000000")
    assert report.shared_ownership_derivation_source_count == Decimal("2.000000")
    assert report.shared_ownership_derivation_risk == Decimal("0.500000")
    assert report.official_source_coverage == Decimal("0.250000")
    assert report.duplicate_claim_count == Decimal("1.000000")
    assert report.duplicate_claim_ratio == Decimal("0.250000")
    assert report.stale_source_count == Decimal("2.000000")
    assert report.stale_source_ratio == Decimal("0.500000")
    assert report.contradiction_severity == Decimal("0.800000")
    assert report.independence_score == Decimal("0.620000")
    assert report.score_status == "watch"
    assert report.reason_codes == (
        "family_count_met",
        "shared_ownership_or_derivation_risk",
        "official_source_covered",
        "duplicate_claims_present",
        "stale_sources_present",
        "contradiction_severity_present",
        "independence_score_watch",
    )


def test_empty_source_set_returns_blocked_zero_score() -> None:
    report = _report(())

    assert report.source_count == Decimal("0.000000")
    assert report.distinct_source_family_count == Decimal("0.000000")
    assert report.independence_score == Decimal("0.000000")
    assert report.score_status == "blocked"
    assert report.reason_codes == ("empty_sources", "independence_score_blocked")
    assert len(report.source_evidence_digest) == 64
    assert len(report.derived_validation_digest) == 64


def test_payload_serializes_decimals_as_strings_and_is_json_ready() -> None:
    report = _report(
        (
            _source(
                source_id="source_a",
                source_family="official",
                owner_family="owner_a",
                claim_fingerprint="claim_a",
                is_official_source=True,
            ),
            _source(
                source_id="source_b",
                source_family="primary",
                owner_family="owner_b",
                claim_fingerprint="claim_b",
            ),
        ),
    )

    payload = report.payload

    json.dumps(payload, sort_keys=True)
    assert payload["source_count"] == "2.000000"
    assert payload["official_source_coverage"] == "0.500000"
    assert payload["independence_score"] == "0.775000"
    assert payload["source_evidence_digest"] == report.source_evidence_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = _report((_source(),))

    with pytest.raises(FrozenInstanceError):
        report.score_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadSource(ResearchPacketSourceFamilyIndependenceScoreSource):
            pass

    with pytest.raises(TypeError):

        class BadConfig(ResearchPacketSourceFamilyIndependenceScoreConfig):
            pass


def test_decimal_only_inputs_and_hard_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        _source(source_age_seconds=3600)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Decimal"):
        _source(contradiction_severity=0.1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="paper_only"):
        ResearchPacketSourceFamilyIndependenceScoreConfig(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        ResearchPacketSourceFamilyIndependenceScoreSource(
            packet_id="packet_a",
            source_id="source_a",
            source_family="official",
            owner_family="owner_a",
            derivation_family=None,
            claim_fingerprint="claim_a",
            is_official_source=True,
            source_age_seconds=Decimal("3600.000000"),
            contradiction_severity=Decimal("0.000000"),
            readonly=False,
        )

    report = _report((_source(),))
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)


def test_validation_rejects_inconsistent_or_tampered_reports() -> None:
    source = _source()
    report = _report((source,))

    with pytest.raises(ValueError, match="packet_id"):
        _report((replace(source, packet_id="packet_b"),))

    with pytest.raises(ValueError, match="source_id"):
        _report((source, source))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, source_evidence_digest="1" * 64)


def test_no_unsafe_public_surfaces_or_runtime_integrations_are_exposed() -> None:
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
        ResearchPacketSourceFamilyIndependenceScoreConfig,
        ResearchPacketSourceFamilyIndependenceScoreSource,
        ResearchPacketSourceFamilyIndependenceScoreReport,
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

    with pytest.raises(ValueError, match="unsafe public"):
        _source(source_id="trade_signal")


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
    if type(value) is bool or value is None or isinstance(value, str):
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
