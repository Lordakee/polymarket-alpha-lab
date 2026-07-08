from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_source_evidence_chain_integrity_report as api
from polymarket_alpha_lab.research_source_evidence_chain_integrity_report import (
    ResearchSourceEvidenceChainIntegrityConfig,
    ResearchSourceEvidenceChainIntegrityLink,
    ResearchSourceEvidenceChainIntegrityPublicPayloadItem,
    ResearchSourceEvidenceChainIntegrityReport,
    ResearchSourceEvidenceChainIntegrityRow,
    build_research_source_evidence_chain_integrity_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _link(
    *,
    chain_id: str = "chain_a",
    claim_id: str = "claim_a",
    evidence_id: str = "evidence_a",
    source_class: str = "official",
    observed_at: datetime = NOW,
    linked_to_claim: bool = True,
    supports_claim: bool = True,
    contradicts_claim: bool = False,
    manual_review_flag: bool = False,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSourceEvidenceChainIntegrityLink:
    return ResearchSourceEvidenceChainIntegrityLink(
        chain_id=chain_id,
        claim_id=claim_id,
        evidence_id=evidence_id,
        source_class=source_class,
        observed_at=observed_at,
        linked_to_claim=linked_to_claim,
        supports_claim=supports_claim,
        contradicts_claim=contradicts_claim,
        manual_review_flag=manual_review_flag,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    links: tuple[ResearchSourceEvidenceChainIntegrityLink, ...],
    *,
    config: ResearchSourceEvidenceChainIntegrityConfig | None = None,
    public_payload: tuple[ResearchSourceEvidenceChainIntegrityPublicPayloadItem, ...] = (),
) -> ResearchSourceEvidenceChainIntegrityReport:
    return build_research_source_evidence_chain_integrity_report(
        links,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_integrity_report_passes_when_chain_has_quorum_complete_links_and_no_pressure() -> None:
    report = _report(
        (
            _link(evidence_id="evidence_a", source_class="official"),
            _link(evidence_id="evidence_b", source_class="primary"),
        ),
    )

    row = report.rows[0]
    assert report.integrity_status == "pass"
    assert report.chain_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert row.integrity_status == "pass"
    assert row.source_class_count == Decimal("2.000000")
    assert row.source_class_quorum_score == Decimal("1.000000")
    assert row.claim_linkage_completeness == Decimal("1.000000")
    assert row.stale_link_pressure == Decimal("0.000000")
    assert row.contradiction_exposure == Decimal("0.000000")
    assert row.manual_review_urgency == Decimal("0.000000")
    assert "evidence_chain_integrity_pass" in row.reason_codes
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_integrity_report_blocks_on_low_quorum_missing_links_stale_contradictions_and_review() -> None:
    config = ResearchSourceEvidenceChainIntegrityConfig(
        stale_after_seconds=Decimal("3600.000000"),
    )

    report = _report(
        (
            _link(
                evidence_id="evidence_a",
                source_class="official",
                observed_at=NOW - timedelta(hours=3),
                linked_to_claim=False,
                supports_claim=False,
                contradicts_claim=True,
            ),
            _link(
                evidence_id="evidence_b",
                source_class="official",
                observed_at=NOW - timedelta(hours=2),
                manual_review_flag=True,
            ),
        ),
        config=config,
    )

    row = report.rows[0]
    assert report.integrity_status == "block"
    assert report.block_count == Decimal("1.000000")
    assert row.integrity_status == "block"
    assert row.source_class_count == Decimal("1.000000")
    assert row.claim_count == Decimal("1.000000")
    assert row.evidence_link_count == Decimal("2.000000")
    assert row.linked_claim_count == Decimal("1.000000")
    assert row.unlinked_claim_count == Decimal("1.000000")
    assert row.stale_link_count == Decimal("2.000000")
    assert row.contradiction_count == Decimal("1.000000")
    assert row.manual_review_signal_count == Decimal("1.000000")
    assert row.claim_linkage_completeness == Decimal("0.500000")
    assert row.stale_link_pressure == Decimal("1.000000")
    assert row.contradiction_exposure == Decimal("0.500000")
    assert row.manual_review_urgency == Decimal("1.000000")
    assert row.reason_codes == (
        "source_class_quorum_gap",
        "claim_linkage_gap",
        "stale_link_pressure_block",
        "contradiction_exposure_block",
        "manual_review_urgency_block",
    )


def test_payload_serializes_decimal_values_as_strings_and_digest_is_deterministic() -> None:
    links = (
        _link(evidence_id="evidence_b", source_class="primary"),
        _link(evidence_id="evidence_a", source_class="official"),
    )
    public_payload = (
        ResearchSourceEvidenceChainIntegrityPublicPayloadItem(
            key="cohort",
            value="research_integrity",
        ),
    )

    first = _report(links, public_payload=public_payload)
    second = _report(tuple(reversed(links)), public_payload=public_payload)

    assert first.derived_validation_digest == second.derived_validation_digest
    payload = first.payload
    json.dumps(payload, sort_keys=True)
    assert payload["chain_count"] == "1.000000"
    assert payload["average_source_class_quorum_score"] == "1.000000"
    assert payload["average_claim_linkage_completeness"] == "1.000000"
    assert payload["rows"][0]["source_class_count"] == "2.000000"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_non_decimal_public_numbers(first)
    _assert_no_decimal_objects(payload)


def test_dataclasses_are_frozen_reject_subclassing_and_enforce_hard_flags() -> None:
    report = _report(
        (
            _link(evidence_id="evidence_a", source_class="official"),
            _link(evidence_id="evidence_b", source_class="primary"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.integrity_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchSourceEvidenceChainIntegrityConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ResearchSourceEvidenceChainIntegrityConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _link(report_only=False)  # type: ignore[call-arg]

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = _report(
        (
            _link(evidence_id="evidence_a", source_class="official"),
            _link(evidence_id="evidence_b", source_class="primary"),
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchSourceEvidenceChainIntegrityPublicPayloadItem(
                    "cohort",
                    "changed",
                ),
            ),
        )


def test_public_payload_rejects_raw_source_urls_text_market_identifiers_and_execution_surfaces() -> None:
    for key in (
        "market_slug",
        "source_url",
        "raw_source_text",
        "live_key",
        "auth_key",
        "wallet_key",
        "order_key",
        "network_key",
        "database_key",
        "sizing_key",
        "recommendation_key",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchSourceEvidenceChainIntegrityPublicPayloadItem(key, "safe value")

    for value in (
        "https://example.invalid/source",
        "raw source transcript",
        "market identifier",
        "live trading",
        "wallet item",
        "order item",
        "network item",
        "position sizing",
        "recommendation item",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchSourceEvidenceChainIntegrityPublicPayloadItem("safe_key", value)

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert "market" not in lowered
        assert "url" not in lowered
        assert "raw" not in lowered

    for cls in (
        ResearchSourceEvidenceChainIntegrityConfig,
        ResearchSourceEvidenceChainIntegrityLink,
        ResearchSourceEvidenceChainIntegrityPublicPayloadItem,
        ResearchSourceEvidenceChainIntegrityRow,
        ResearchSourceEvidenceChainIntegrityReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert "market" not in lowered
            assert "url" not in lowered
            assert "raw" not in lowered

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
