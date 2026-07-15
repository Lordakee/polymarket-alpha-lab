from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from polymarket_alpha_lab.source_family_diversity_gap_report import (
    SourceFamilyDiversityGapInput,
    SourceFamilyDiversityGapReport,
    build_source_family_diversity_gap_report,
    source_family_diversity_gap_payload,
    source_family_diversity_gap_payload_digest,
)


def test_builds_sufficient_diversity_report_payload_and_digest() -> None:
    report = build_source_family_diversity_gap_report(
        SourceFamilyDiversityGapInput(
            independent_source_count=Decimal("5"),
            source_family_count=Decimal("3"),
            official_source_count=Decimal("1"),
            single_family_dominance_probability=Decimal("0.250000"),
            required_family_count=Decimal("3"),
        ),
    )

    assert report.diversity_status == "sufficient"
    assert report.reason_codes == ("source_family_diversity_sufficient",)
    assert report.manual_next_step == "no_manual_review_required"
    assert report.independent_source_count == Decimal("5.000000")
    assert report.source_family_count == Decimal("3.000000")
    assert report.official_source_count == Decimal("1.000000")
    assert report.single_family_dominance_probability == Decimal("0.250000")
    assert report.required_family_count == Decimal("3.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    with pytest.raises(FrozenInstanceError):
        report.diversity_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="payload_digest"):
        SourceFamilyDiversityGapReport(
            config_version=report.config_version,
            diversity_status=report.diversity_status,
            reason_codes=report.reason_codes,
            manual_next_step=report.manual_next_step,
            independent_source_count=report.independent_source_count,
            source_family_count=report.source_family_count,
            official_source_count=report.official_source_count,
            single_family_dominance_probability=(
                report.single_family_dominance_probability
            ),
            required_family_count=report.required_family_count,
            payload_digest="0" * 64,
        )

    payload = source_family_diversity_gap_payload(report)

    assert payload["diversity_status"] == "sufficient"
    assert payload["reason_codes"] == ["source_family_diversity_sufficient"]
    assert payload["manual_next_step"] == "no_manual_review_required"
    assert payload["independent_source_count"] == "5.000000"
    assert payload["source_family_count"] == "3.000000"
    assert payload["official_source_count"] == "1.000000"
    assert payload["single_family_dominance_probability"] == "0.250000"
    assert payload["required_family_count"] == "3.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == report.payload_digest
    assert source_family_diversity_gap_payload_digest(report) == report.payload_digest

    payload_text = str(payload).lower()
    for forbidden_fragment in (
        "live",
        "auth",
        "wallet",
        "order",
        "key",
        "sign",
        "execute",
    ):
        assert forbidden_fragment not in payload_text


def test_blocks_when_family_count_is_below_requirement() -> None:
    report = build_source_family_diversity_gap_report(
        SourceFamilyDiversityGapInput(
            independent_source_count=Decimal("4"),
            source_family_count=Decimal("2"),
            official_source_count=Decimal("1"),
            single_family_dominance_probability=Decimal("0.300000"),
            required_family_count=Decimal("3"),
        ),
    )

    assert report.diversity_status == "blocked"
    assert report.reason_codes == ("source_family_count_below_required_blocker",)
    assert report.manual_next_step == "add_independent_source_family_review"


def test_warns_when_official_source_is_missing_or_single_family_dominates() -> None:
    report = build_source_family_diversity_gap_report(
        SourceFamilyDiversityGapInput(
            independent_source_count=Decimal("4"),
            source_family_count=Decimal("3"),
            official_source_count=Decimal("0"),
            single_family_dominance_probability=Decimal("0.800000"),
            required_family_count=Decimal("3"),
        ),
    )

    assert report.diversity_status == "watch"
    assert report.reason_codes == (
        "official_source_missing_attention",
        "single_family_dominance_probability_attention",
    )
    assert report.manual_next_step == "manual_source_family_diversity_review"


def test_rejects_non_decimal_inputs_invalid_ratios_and_non_readonly_flags() -> None:
    with pytest.raises(ValueError, match="independent_source_count must be a Decimal"):
        SourceFamilyDiversityGapInput(
            independent_source_count=5,  # type: ignore[arg-type]
            source_family_count=Decimal("3"),
            official_source_count=Decimal("1"),
            single_family_dominance_probability=Decimal("0.250000"),
            required_family_count=Decimal("3"),
        )

    with pytest.raises(
        ValueError,
        match="single_family_dominance_probability must be less than or equal to 1",
    ):
        SourceFamilyDiversityGapInput(
            independent_source_count=Decimal("5"),
            source_family_count=Decimal("3"),
            official_source_count=Decimal("1"),
            single_family_dominance_probability=Decimal("1.000001"),
            required_family_count=Decimal("3"),
        )

    with pytest.raises(ValueError, match="readonly must be True"):
        SourceFamilyDiversityGapInput(
            independent_source_count=Decimal("5"),
            source_family_count=Decimal("3"),
            official_source_count=Decimal("1"),
            single_family_dominance_probability=Decimal("0.250000"),
            required_family_count=Decimal("3"),
            readonly=False,
        )
