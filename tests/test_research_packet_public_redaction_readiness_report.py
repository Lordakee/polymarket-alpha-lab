from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_packet_public_redaction_readiness_report import (
    ResearchPacketPublicRedactionReadinessInput,
    build_research_packet_public_redaction_readiness_report,
    research_packet_public_redaction_readiness_digest,
    research_packet_public_redaction_readiness_payload,
)


def test_builds_ready_public_redaction_readiness_report_payload_and_digest() -> None:
    report = build_research_packet_public_redaction_readiness_report(
        ResearchPacketPublicRedactionReadinessInput(
            raw_identifier_field_count=Decimal("0"),
            unsafe_text_token_count=Decimal("0"),
            redacted_payload_ready=True,
            public_payload_audit_passed=True,
            source_reference_redacted=True,
            dsn_or_table_terms_absent=True,
            wallet_or_auth_terms_absent=True,
        ),
    )

    assert report.redaction_ready is True
    assert report.blocked_reason_codes == (
        "research_packet_public_redaction_ready",
    )
    assert report.attention_reason_codes == ()
    assert report.blocked_item_count == Decimal("0.000000")
    assert report.ready_ratio == Decimal("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    with pytest.raises(FrozenInstanceError):
        report.redaction_ready = False  # type: ignore[misc]

    payload = research_packet_public_redaction_readiness_payload(report)

    assert payload["redaction_ready"] is True
    assert payload["blocked_item_count"] == "0.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "wallet" not in str(payload).lower()
    assert "auth" not in str(payload).lower()
    assert "dsn" not in str(payload).lower()
    assert "table" not in str(payload).lower()
    assert research_packet_public_redaction_readiness_digest(report) == report.digest


def test_blocks_when_any_redaction_or_public_safety_gate_fails() -> None:
    report = build_research_packet_public_redaction_readiness_report(
        ResearchPacketPublicRedactionReadinessInput(
            raw_identifier_field_count=Decimal("2"),
            unsafe_text_token_count=Decimal("3"),
            redacted_payload_ready=False,
            public_payload_audit_passed=False,
            source_reference_redacted=False,
            dsn_or_table_terms_absent=False,
            wallet_or_auth_terms_absent=False,
        ),
    )

    assert report.redaction_ready is False
    assert report.blocked_item_count == Decimal("7.000000")
    assert report.ready_ratio == Decimal("0.000000")
    assert report.blocked_reason_codes == (
        "raw_identifier_fields_present_blocker",
        "unsafe_text_tokens_present_blocker",
        "redacted_payload_not_ready_blocker",
        "public_payload_audit_failed_blocker",
        "source_reference_not_redacted_blocker",
        "storage_terms_present_blocker",
        "credential_terms_present_blocker",
    )
    assert report.attention_reason_codes == (
        "operator_public_payload_requires_redaction_attention",
    )


def test_attention_only_when_payload_is_redacted_but_raw_counts_are_nonzero() -> None:
    report = build_research_packet_public_redaction_readiness_report(
        ResearchPacketPublicRedactionReadinessInput(
            raw_identifier_field_count=Decimal("1"),
            unsafe_text_token_count=Decimal("0"),
            redacted_payload_ready=True,
            public_payload_audit_passed=True,
            source_reference_redacted=True,
            dsn_or_table_terms_absent=True,
            wallet_or_auth_terms_absent=True,
        ),
    )

    assert report.redaction_ready is True
    assert report.blocked_item_count == Decimal("0.000000")
    assert report.ready_ratio == Decimal("0.857143")
    assert report.blocked_reason_codes == (
        "research_packet_public_redaction_ready",
    )
    assert report.attention_reason_codes == (
        "raw_identifier_fields_removed_attention",
    )


def test_rejects_non_decimal_counts_and_non_readonly_flags() -> None:
    with pytest.raises(ValueError, match="raw_identifier_field_count must be a Decimal"):
        ResearchPacketPublicRedactionReadinessInput(
            raw_identifier_field_count=1,  # type: ignore[arg-type]
            unsafe_text_token_count=Decimal("0"),
            redacted_payload_ready=True,
            public_payload_audit_passed=True,
            source_reference_redacted=True,
            dsn_or_table_terms_absent=True,
            wallet_or_auth_terms_absent=True,
        )

    with pytest.raises(ValueError, match="readonly must be True"):
        ResearchPacketPublicRedactionReadinessInput(
            raw_identifier_field_count=Decimal("0"),
            unsafe_text_token_count=Decimal("0"),
            redacted_payload_ready=True,
            public_payload_audit_passed=True,
            source_reference_redacted=True,
            dsn_or_table_terms_absent=True,
            wallet_or_auth_terms_absent=True,
            readonly=False,
        )
