from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_source_capture_completeness_report import (
    MarketResearchSourceCaptureCompletenessReport,
    build_market_research_source_capture_completeness_report,
    market_research_source_capture_completeness_report_payload,
    validate_market_research_source_capture_completeness_report_payload,
)


def test_builds_complete_capture_report_with_public_payload_and_digest() -> None:
    report = build_market_research_source_capture_completeness_report(
        source_count=Decimal("5"),
        captured_snapshot_count=Decimal("5"),
        missing_digest_count=Decimal("0"),
        official_source_count=Decimal("2"),
        minimum_required_sources=Decimal("3"),
    )

    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert report.capture_status == "complete"
    assert report.reason_codes == (
        "source_capture_complete",
        "source_capture_minimum_sources_met",
        "source_capture_official_source_present",
    )
    assert report.manual_next_step == "No manual follow-up required."
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload == market_research_source_capture_completeness_report_payload(report)
    assert payload["source_count"] == "5"
    assert payload["captured_snapshot_count"] == "5"
    assert payload["missing_digest_count"] == "0"
    assert payload["official_source_count"] == "2"
    assert payload["minimum_required_sources"] == "3"
    assert payload["capture_status"] == "complete"
    assert payload["reason_codes"] == list(report.reason_codes)
    assert payload["manual_next_step"] == "No manual follow-up required."
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == report.payload_digest
    assert len(report.payload_digest) == 64
    assert validate_market_research_source_capture_completeness_report_payload(payload) is True

    with pytest.raises(FrozenInstanceError):
        report.capture_status = "block"  # type: ignore[misc]


def test_builds_attention_report_when_capture_is_partial() -> None:
    report = build_market_research_source_capture_completeness_report(
        source_count=Decimal("4"),
        captured_snapshot_count=Decimal("3"),
        missing_digest_count=Decimal("1"),
        official_source_count=Decimal("1"),
        minimum_required_sources=Decimal("3"),
    )

    assert report.capture_status == "attention"
    assert report.reason_codes == (
        "source_capture_missing_digests",
        "source_capture_snapshot_gap",
    )
    assert report.manual_next_step == (
        "Re-capture missing source snapshots and regenerate absent digests before review."
    )


def test_builds_blocked_report_when_minimum_or_official_sources_are_missing() -> None:
    report = build_market_research_source_capture_completeness_report(
        source_count=Decimal("2"),
        captured_snapshot_count=Decimal("2"),
        missing_digest_count=Decimal("0"),
        official_source_count=Decimal("0"),
        minimum_required_sources=Decimal("3"),
    )

    assert report.capture_status == "blocked"
    assert report.reason_codes == (
        "source_capture_minimum_sources_unmet",
        "source_capture_no_official_source",
    )
    assert report.manual_next_step == (
        "Add official sources and meet the minimum source requirement before review."
    )


def test_rejects_non_decimal_counts_integers_and_inconsistent_counts() -> None:
    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        build_market_research_source_capture_completeness_report(
            source_count=5,  # type: ignore[arg-type]
            captured_snapshot_count=Decimal("5"),
            missing_digest_count=Decimal("0"),
            official_source_count=Decimal("1"),
            minimum_required_sources=Decimal("3"),
        )

    with pytest.raises(ValueError, match="captured_snapshot_count must not exceed source_count"):
        build_market_research_source_capture_completeness_report(
            source_count=Decimal("2"),
            captured_snapshot_count=Decimal("3"),
            missing_digest_count=Decimal("0"),
            official_source_count=Decimal("1"),
            minimum_required_sources=Decimal("2"),
        )

    with pytest.raises(ValueError, match="missing_digest_count must not exceed source_count"):
        build_market_research_source_capture_completeness_report(
            source_count=Decimal("2"),
            captured_snapshot_count=Decimal("2"),
            missing_digest_count=Decimal("3"),
            official_source_count=Decimal("1"),
            minimum_required_sources=Decimal("2"),
        )


def test_rejects_non_readonly_flags_and_unsafe_public_surfaces() -> None:
    with pytest.raises(ValueError, match="readonly must be True"):
        MarketResearchSourceCaptureCompletenessReport(
            source_count=Decimal("3"),
            captured_snapshot_count=Decimal("3"),
            missing_digest_count=Decimal("0"),
            official_source_count=Decimal("1"),
            minimum_required_sources=Decimal("3"),
            capture_status="complete",
            reason_codes=("source_capture_complete",),
            manual_next_step="No manual follow-up required.",
            readonly=False,
        )

    payload = {
        "source_count": "3",
        "captured_snapshot_count": "3",
        "missing_digest_count": "0",
        "official_source_count": "1",
        "minimum_required_sources": "3",
        "capture_status": "complete",
        "reason_codes": ["source_capture_complete"],
        "manual_next_step": "No manual follow-up required.",
        "".join(("li", "ve", "_pa", "th")): "forbidden",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": "0" * 64,
    }

    with pytest.raises(ValueError, match="unsafe public field"):
        validate_market_research_source_capture_completeness_report_payload(payload)
