from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_evidence_chain_integrity_report as api
from polymarket_alpha_lab.research_evidence_chain_integrity_report import (
    ResearchEvidenceChainEvidence,
    ResearchEvidenceChainIntegrityConfig,
    ResearchEvidenceChainIntegrityReport,
    ResearchEvidenceChainIntegrityRow,
    ResearchEvidenceChainPublicPayloadItem,
    build_research_evidence_chain_integrity_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _evidence(
    *,
    packet_id: str = "packet_a",
    claim_id: str = "claim_a",
    evidence_id: str = "evidence_a",
    source_id: str = "source_a",
    source_family: str = "official",
    stance: str = "supporting",
    source_event_at: datetime = NOW - timedelta(days=2),
    captured_at: datetime = NOW - timedelta(days=1),
    confidence_score: Decimal = Decimal("0.800000"),
    citation_summary: str = "Official filing states the referenced condition was met.",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEvidenceChainEvidence:
    return ResearchEvidenceChainEvidence(
        packet_id=packet_id,
        claim_id=claim_id,
        evidence_id=evidence_id,
        source_id=source_id,
        source_family=source_family,
        stance=stance,
        source_event_at=source_event_at,
        captured_at=captured_at,
        confidence_score=confidence_score,
        citation_summary=citation_summary,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    evidence: tuple[ResearchEvidenceChainEvidence, ...],
    *,
    config: ResearchEvidenceChainIntegrityConfig | None = None,
    public_payload: tuple[ResearchEvidenceChainPublicPayloadItem, ...] = (),
) -> ResearchEvidenceChainIntegrityReport:
    return build_research_evidence_chain_integrity_report(
        evidence,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_complete_evidence_chain_passes_with_independence_counterevidence_and_timing() -> None:
    report = _report(
        (
            _evidence(evidence_id="evidence_a", source_id="source_a", source_family="official"),
            _evidence(
                evidence_id="evidence_b",
                source_id="source_b",
                source_family="primary",
                confidence_score=Decimal("0.700000"),
            ),
            _evidence(
                evidence_id="evidence_c",
                source_id="source_c",
                source_family="independent",
                stance="counterevidence",
                citation_summary="Independent archive records a conflicting public timestamp.",
            ),
        ),
    )

    row = report.rows[0]
    assert report.chain_status == "pass"
    assert report.claim_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert row.source_count == Decimal("3.000000")
    assert row.supporting_source_count == Decimal("2.000000")
    assert row.independent_support_family_count == Decimal("2.000000")
    assert row.counterevidence_count == Decimal("1.000000")
    assert row.chronology_issue_count == Decimal("0.000000")
    assert row.citation_summary_gap_count == Decimal("0.000000")
    assert row.gap_count == Decimal("0.000000")
    assert row.integrity_score == Decimal("1.000000")
    assert row.chain_status == "pass"
    assert row.reason_codes == ("complete_evidence_chain",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_missing_counterevidence_is_watch_gap() -> None:
    report = _report(
        (
            _evidence(evidence_id="evidence_a", source_id="source_a", source_family="official"),
            _evidence(evidence_id="evidence_b", source_id="source_b", source_family="primary"),
        ),
    )

    row = report.rows[0]
    assert report.chain_status == "watch"
    assert report.watch_count == Decimal("1.000000")
    assert row.counterevidence_count == Decimal("0.000000")
    assert row.gap_count == Decimal("1.000000")
    assert row.integrity_score == Decimal("0.750000")
    assert row.chain_status == "watch"
    assert "missing_counterevidence" in row.reason_codes


def test_chronology_issue_blocks_chain() -> None:
    report = _report(
        (
            _evidence(evidence_id="evidence_a", source_id="source_a", source_family="official"),
            _evidence(
                evidence_id="evidence_b",
                source_id="source_b",
                source_family="primary",
                source_event_at=NOW,
                captured_at=NOW - timedelta(days=1),
            ),
            _evidence(
                evidence_id="evidence_c",
                source_id="source_c",
                source_family="independent",
                stance="counterevidence",
                citation_summary="Independent archive records a conflicting public timestamp.",
            ),
        ),
    )

    row = report.rows[0]
    assert report.chain_status == "block"
    assert report.block_count == Decimal("1.000000")
    assert row.chronology_issue_count == Decimal("1.000000")
    assert row.chain_status == "block"
    assert "chronology_issue" in row.reason_codes


def test_short_citation_summary_is_reported_as_watch_gap() -> None:
    config = ResearchEvidenceChainIntegrityConfig(
        min_citation_summary_characters=Decimal("24.000000"),
    )

    report = _report(
        (
            _evidence(
                evidence_id="evidence_a",
                source_id="source_a",
                source_family="official",
                citation_summary="Too short.",
            ),
            _evidence(evidence_id="evidence_b", source_id="source_b", source_family="primary"),
            _evidence(
                evidence_id="evidence_c",
                source_id="source_c",
                source_family="independent",
                stance="counterevidence",
                citation_summary="Independent archive records a conflicting public timestamp.",
            ),
        ),
        config=config,
    )

    row = report.rows[0]
    assert report.chain_status == "watch"
    assert row.citation_summary_gap_count == Decimal("1.000000")
    assert row.gap_count == Decimal("1.000000")
    assert row.integrity_score == Decimal("0.750000")
    assert "citation_summary_gap" in row.reason_codes


def test_payload_serializes_decimal_values_as_strings_and_is_json_ready() -> None:
    report = _report(
        (
            _evidence(evidence_id="evidence_a", source_id="source_a", source_family="official"),
            _evidence(evidence_id="evidence_b", source_id="source_b", source_family="primary"),
            _evidence(
                evidence_id="evidence_c",
                source_id="source_c",
                source_family="independent",
                stance="counterevidence",
                citation_summary="Independent archive records a conflicting public timestamp.",
            ),
        ),
        public_payload=(ResearchEvidenceChainPublicPayloadItem("safe_key", "safe value"),),
    )

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["claim_count"] == "1.000000"
    assert payload["average_integrity_score"] == "1.000000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["rows"][0]["integrity_score"] == "1.000000"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = _report(
        (
            _evidence(evidence_id="evidence_a", source_id="source_a", source_family="official"),
            _evidence(evidence_id="evidence_b", source_id="source_b", source_family="primary"),
            _evidence(
                evidence_id="evidence_c",
                source_id="source_c",
                source_family="independent",
                stance="counterevidence",
                citation_summary="Independent archive records a conflicting public timestamp.",
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.chain_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadEvidence(ResearchEvidenceChainEvidence):
            pass


def test_strict_type_validation_rejects_float_naive_datetime_and_bad_sequences() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        _evidence(confidence_score=0.8)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="timezone-aware"):
        _evidence(source_event_at=datetime(2026, 1, 1))

    with pytest.raises(ValueError, match="known stance"):
        _evidence(stance="neutral")

    with pytest.raises(ValueError, match="sequence"):
        build_research_evidence_chain_integrity_report(
            "not evidence",  # type: ignore[arg-type]
            generated_at=NOW,
        )

    with pytest.raises(ValueError, match="Decimal"):
        ResearchEvidenceChainIntegrityConfig(
            min_independent_support_family_count=2,  # type: ignore[arg-type]
        )


def test_hard_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchEvidenceChainIntegrityConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _evidence(report_only=False)  # type: ignore[call-arg]

    report = _report(
        (
            _evidence(evidence_id="evidence_a", source_id="source_a", source_family="official"),
            _evidence(evidence_id="evidence_b", source_id="source_b", source_family="primary"),
            _evidence(
                evidence_id="evidence_c",
                source_id="source_c",
                source_family="independent",
                stance="counterevidence",
                citation_summary="Independent archive records a conflicting public timestamp.",
            ),
        ),
    )
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = _report(
        (
            _evidence(evidence_id="evidence_a", source_id="source_a", source_family="official"),
            _evidence(evidence_id="evidence_b", source_id="source_b", source_family="primary"),
            _evidence(
                evidence_id="evidence_c",
                source_id="source_c",
                source_family="independent",
                stance="counterevidence",
                citation_summary="Independent archive records a conflicting public timestamp.",
            ),
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(ResearchEvidenceChainPublicPayloadItem("safe_key", "changed"),),
        )


def test_unsafe_public_payload_keys_values_and_citation_summaries_are_rejected() -> None:
    unsafe_terms = (
        "auth",
        "wallet",
        "order",
        "database",
        "network",
        "persist",
        "buy",
        "sell",
        "trade",
        "recommend",
        "advice",
    )
    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEvidenceChainPublicPayloadItem(f"{term}_key", "safe value")
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEvidenceChainPublicPayloadItem("safe_key", f"{term} value")

    with pytest.raises(ValueError, match="unsafe public"):
        _evidence(citation_summary="Visit https://example.invalid for the source.")

    with pytest.raises(ValueError, match="unsafe public"):
        _evidence(source_id="wallet_source")


def test_no_unsafe_public_surfaces_or_external_io_modules_are_exposed() -> None:
    unsafe_terms = (
        "auth",
        "wallet",
        "order",
        "database",
        "network",
        "persist",
        "buy",
        "sell",
        "trade",
        "recommend",
        "advice",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ResearchEvidenceChainIntegrityConfig,
        ResearchEvidenceChainEvidence,
        ResearchEvidenceChainPublicPayloadItem,
        ResearchEvidenceChainIntegrityRow,
        ResearchEvidenceChainIntegrityReport,
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
