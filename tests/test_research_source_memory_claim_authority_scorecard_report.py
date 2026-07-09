from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_source_memory_claim_authority_scorecard_report import (
    ResearchSourceMemoryClaimAuthorityEvidence,
    ResearchSourceMemoryClaimAuthorityScorecardConfig,
    ResearchSourceMemoryClaimAuthorityScorecardReport,
    ResearchSourceMemoryClaimAuthorityScorecardRow,
    build_research_source_memory_claim_authority_scorecard_report,
    research_source_memory_claim_authority_scorecard_report_public_payload,
    validate_research_source_memory_claim_authority_scorecard_report_public_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_memory_claim_authority_scorecard_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence(
    evidence_id: str,
    claim_memory_id: str,
    authority_tier: str,
    *,
    source_family: str = "official_rules_archive",
    observed_delta_seconds: int = 600,
    authority_weight: Decimal = d("1.000000"),
    corroboration_weight: Decimal = d("1.000000"),
    contradiction_weight: Decimal = d("0.000000"),
    extraction_confidence: Decimal = d("1.000000"),
) -> ResearchSourceMemoryClaimAuthorityEvidence:
    return ResearchSourceMemoryClaimAuthorityEvidence(
        evidence_id=evidence_id,
        claim_memory_id=claim_memory_id,
        authority_tier=authority_tier,
        source_family=source_family,
        observed_at=GENERATED_AT - timedelta(seconds=observed_delta_seconds),
        authority_weight=authority_weight,
        corroboration_weight=corroboration_weight,
        contradiction_weight=contradiction_weight,
        extraction_confidence=extraction_confidence,
    )


def complete_evidence() -> tuple[ResearchSourceMemoryClaimAuthorityEvidence, ...]:
    return (
        evidence(
            "memory-evidence-alpha",
            "claim-memory-alpha",
            "official",
            source_family="official_rules_archive",
            authority_weight=d("1.000000"),
        ),
        evidence(
            "memory-evidence-beta",
            "claim-memory-alpha",
            "primary",
            source_family="court_record_archive",
            authority_weight=d("0.900000"),
            corroboration_weight=d("0.950000"),
        ),
    )


def build_report(
    rows: tuple[ResearchSourceMemoryClaimAuthorityEvidence, ...] = complete_evidence(),
    *,
    config: ResearchSourceMemoryClaimAuthorityScorecardConfig | None = None,
) -> ResearchSourceMemoryClaimAuthorityScorecardReport:
    return build_research_source_memory_claim_authority_scorecard_report(
        rows,
        config=config or ResearchSourceMemoryClaimAuthorityScorecardConfig(),
        generated_at=GENERATED_AT,
    )


def assert_no_public_numeric_scalars(value: object) -> None:
    if value is None or type(value) is bool or type(value) is str:
        return
    if isinstance(value, (int, float, Decimal)):
        raise AssertionError(f"public payload contains numeric scalar: {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_public_numeric_scalars(item)
        return
    if type(value) is list:
        for item in value:
            assert_no_public_numeric_scalars(item)
        return
    raise AssertionError(f"unexpected public payload value: {value!r}")


def test_authority_scorecard_passes_with_decimal_only_public_payload() -> None:
    report = build_report()

    assert report.status == "pass"
    assert report.claim_count == d("1")
    assert report.evidence_count == d("2")
    assert report.pass_count == d("1")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.average_authority_score == d("0.962500")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)

    payload = research_source_memory_claim_authority_scorecard_report_public_payload(report)

    assert payload["status"] == "pass"
    assert payload["claim_count"] == "1"
    assert payload["evidence_count"] == "2"
    assert payload["average_authority_score"] == "0.962500"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_scalars(payload)
    assert validate_research_source_memory_claim_authority_scorecard_report_public_payload(
        payload,
    )


def test_statuses_are_limited_to_pass_watch_and_block() -> None:
    watch_report = build_report(
        (
            evidence(
                "watch-evidence",
                "watch-memory",
                "secondary",
                authority_weight=d("0.600000"),
                corroboration_weight=d("0.600000"),
                extraction_confidence=d("0.600000"),
            ),
        ),
    )
    block_report = build_report(
        (
            evidence(
                "block-evidence",
                "block-memory",
                "unverified",
                authority_weight=d("0.250000"),
                corroboration_weight=d("0.100000"),
                contradiction_weight=d("0.900000"),
                extraction_confidence=d("0.400000"),
            ),
        ),
    )

    assert watch_report.status == "watch"
    assert watch_report.rows[0].status == "watch"
    assert block_report.status == "block"
    assert block_report.rows[0].status == "block"

    with pytest.raises(ValueError, match="status"):
        replace(watch_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(watch_report, status="blocked")


def test_public_payload_is_deterministic_and_digest_validated() -> None:
    report = build_report(tuple(reversed(complete_evidence())))
    same_report = build_report(complete_evidence())

    payload = research_source_memory_claim_authority_scorecard_report_public_payload(report)
    same_payload = research_source_memory_claim_authority_scorecard_report_public_payload(
        same_report,
    )

    assert payload == same_payload
    assert validate_research_source_memory_claim_authority_scorecard_report_public_payload(
        payload,
    )

    tampered = dict(payload)
    tampered["status"] = "block"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_source_memory_claim_authority_scorecard_report_public_payload(tampered)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_source_memory_claim_authority_scorecard_report_public_payload(
            missing_digest,
        )


def test_public_payload_does_not_expose_raw_inputs_or_sensitive_values() -> None:
    payload = research_source_memory_claim_authority_scorecard_report_public_payload(
        build_report(),
    )
    encoded = json.dumps(payload, sort_keys=True)

    for raw_value in (
        "claim-memory-alpha",
        "memory-evidence-alpha",
        "memory-evidence-beta",
        "official_rules_archive",
        "court_record_archive",
    ):
        assert raw_value not in encoded

    unsafe_values = (
        "https://example.invalid/private",
        "raw_" + "text",
        "post" + "gres://opaque",
        "cand" + "idate",
        "mar" + "ket",
        "source_" + "url",
        "source_" + "text",
        "d" + "sn",
        "ta" + "ble",
        "tok" + "en",
    )
    for unsafe_value in unsafe_values:
        unsafe_payload = dict(payload)
        unsafe_payload["review_note"] = unsafe_value
        with pytest.raises(ValueError, match="unsafe public payload"):
            research_source_memory_claim_authority_scorecard_report_public_payload(
                unsafe_payload,
            )


def test_decimal_only_validation_rejects_integer_and_float_inputs() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        ResearchSourceMemoryClaimAuthorityEvidence(
            evidence_id="bad-decimal",
            claim_memory_id="claim-memory-alpha",
            authority_tier="official",
            source_family="official_rules_archive",
            observed_at=GENERATED_AT,
            authority_weight=1,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Decimal"):
        ResearchSourceMemoryClaimAuthorityScorecardConfig(
            pass_authority_score=0.8,  # type: ignore[arg-type]
        )


def test_rejects_bad_inputs_duplicates_future_dates_and_flags() -> None:
    with pytest.raises(ValueError, match="iterable"):
        build_research_source_memory_claim_authority_scorecard_report(
            "not rows",  # type: ignore[arg-type]
            config=ResearchSourceMemoryClaimAuthorityScorecardConfig(),
            generated_at=GENERATED_AT,
        )

    duplicate = complete_evidence()[0]
    with pytest.raises(ValueError, match="unique"):
        build_report((duplicate, duplicate))

    future_row = replace(complete_evidence()[0], observed_at=GENERATED_AT + timedelta(seconds=1))
    with pytest.raises(ValueError, match="observed_at"):
        build_report((future_row,))

    with pytest.raises(ValueError, match="paper_only"):
        replace(complete_evidence()[0], paper_only=False)


def test_report_consistency_rejects_manual_mismatches() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="claim_count"):
        replace(report, claim_count=d("2"))
    with pytest.raises(ValueError, match="average_authority_score"):
        replace(report, average_authority_score=d("0.500000"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="block")


def test_dataclasses_are_frozen() -> None:
    config = ResearchSourceMemoryClaimAuthorityScorecardConfig()
    evidence_row = complete_evidence()[0]
    report = build_report()
    row = report.rows[0]

    frozen_values: tuple[Any, ...] = (config, evidence_row, row, report)
    for value in frozen_values:
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    assert isinstance(row, ResearchSourceMemoryClaimAuthorityScorecardRow)


def test_module_has_no_external_action_terms() -> None:
    module_text = MODULE_PATH.read_text(encoding="utf-8").lower()

    forbidden_terms = (
        "data" + "base",
        "net" + "work",
        "wall" + "et",
        "ord" + "er",
        "li" + "ve",
        "trad" + "ing",
        "siz" + "ing",
        "recomm" + "endation",
    )
    for forbidden_term in forbidden_terms:
        assert forbidden_term not in module_text
