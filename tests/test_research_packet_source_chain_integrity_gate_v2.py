from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_packet_source_chain_integrity_gate_v2 import (
    ResearchPacketSourceChainEvidence,
    ResearchPacketSourceChainIntegrityGateV2Config,
    ResearchPacketSourceChainIntegrityGateV2Report,
    ResearchPacketSourceChainIntegrityGateV2Row,
    build_research_packet_source_chain_integrity_gate_v2,
    research_packet_source_chain_integrity_gate_v2_public_payload,
    validate_research_packet_source_chain_integrity_gate_v2_public_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def source(
    evidence_id: str,
    source_family: str,
    source_kind: str,
    *,
    observed_delta_seconds: int = 600,
    probability_move_attribution: Decimal = d("0.000000"),
    rule_clarity_score: Decimal = d("0.000000"),
    resolution_evidence_score: Decimal = d("0.000000"),
    contradiction_review_complete: bool = False,
) -> ResearchPacketSourceChainEvidence:
    return ResearchPacketSourceChainEvidence(
        evidence_id=evidence_id,
        source_family=source_family,
        source_kind=source_kind,
        observed_at=GENERATED_AT - timedelta(seconds=observed_delta_seconds),
        probability_move_attribution=probability_move_attribution,
        rule_clarity_score=rule_clarity_score,
        resolution_evidence_score=resolution_evidence_score,
        contradiction_review_complete=contradiction_review_complete,
    )


def complete_sources() -> tuple[ResearchPacketSourceChainEvidence, ...]:
    return (
        source(
            "official-rules",
            "official_polymarket",
            "official_anchor",
            rule_clarity_score=d("0.950000"),
        ),
        source(
            "independent-alpha",
            "court_filings",
            "independent_source",
            probability_move_attribution=d("0.010000"),
        ),
        source(
            "move-alpha",
            "newswire",
            "probability_move_attribution",
            probability_move_attribution=d("0.020000"),
        ),
        source(
            "contradiction-alpha",
            "analyst_review",
            "contradiction_review",
            contradiction_review_complete=True,
        ),
        source(
            "resolution-alpha",
            "resolution_archive",
            "resolution_evidence",
            resolution_evidence_score=d("1.000000"),
        ),
        source(
            "rule-alpha",
            "rulebook",
            "rule_clarity",
            rule_clarity_score=d("0.900000"),
        ),
    )


def build_report(
    evidence_sources: tuple[ResearchPacketSourceChainEvidence, ...] = complete_sources(),
    *,
    config: ResearchPacketSourceChainIntegrityGateV2Config | None = None,
    probability_move_since_prior_packet: Decimal = d("0.025000"),
) -> ResearchPacketSourceChainIntegrityGateV2Report:
    return build_research_packet_source_chain_integrity_gate_v2(
        evidence_sources,
        config=config or ResearchPacketSourceChainIntegrityGateV2Config(),
        generated_at=GENERATED_AT,
        probability_move_since_prior_packet=probability_move_since_prior_packet,
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


def test_complete_source_chain_passes_with_decimal_only_payload() -> None:
    report = build_report()

    assert report.gate_status == "pass"
    assert report.reason_codes == ("source_chain_integrity_pass",)
    assert report.source_count == d("6")
    assert report.official_anchor_count == d("1")
    assert report.independent_source_family_count == d("5")
    assert report.probability_move_unattributed == d("0.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)

    payload = research_packet_source_chain_integrity_gate_v2_public_payload(report)

    assert payload["source_count"] == "6"
    assert payload["probability_move_since_prior_packet"] == "0.025000"
    assert payload["probability_move_attributed"] == "0.030000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_scalars(payload)
    assert validate_research_packet_source_chain_integrity_gate_v2_public_payload(payload)


def test_gate_blocks_each_required_source_chain_gap() -> None:
    sparse_sources = (
        source(
            "stale-independent",
            "single_family",
            "independent_source",
            observed_delta_seconds=90000,
            probability_move_attribution=d("0.000000"),
        ),
    )

    report = build_report(
        sparse_sources,
        probability_move_since_prior_packet=d("0.050000"),
    )

    assert report.gate_status == "blocked"
    assert report.reason_codes == (
        "missing_official_anchor",
        "insufficient_independent_source_family",
        "stale_source_evidence",
        "contradiction_review_incomplete",
        "probability_move_unattributed",
        "resolution_evidence_insufficient",
        "rule_clarity_below_floor",
    )
    assert report.recommended_next_step == "repair_source_chain_evidence"
    assert report.stale_source_count == d("1")


def test_contradiction_review_rows_must_be_complete() -> None:
    sources = tuple(
        source_item
        if source_item.source_kind != "contradiction_review"
        else replace(source_item, contradiction_review_complete=False)
        for source_item in complete_sources()
    )

    report = build_report(sources)

    assert report.gate_status == "blocked"
    assert "contradiction_review_incomplete" in report.reason_codes
    contradiction_rows = [
        row for row in report.evidence_rows if row.source_kind == "contradiction_review"
    ]
    assert contradiction_rows[0].evidence_status == "blocked"
    assert contradiction_rows[0].reason_codes == ("contradiction_review_incomplete",)


def test_derived_validation_digest_rejects_report_and_payload_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, derived_validation_digest="0" * 64)

    payload = research_packet_source_chain_integrity_gate_v2_public_payload(report)
    tampered = dict(payload)
    tampered["gate_status"] = "blocked"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        research_packet_source_chain_integrity_gate_v2_public_payload(tampered)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_packet_source_chain_integrity_gate_v2_public_payload(missing_digest)


def test_public_payload_rejects_unsafe_keys_and_values() -> None:
    payload = research_packet_source_chain_integrity_gate_v2_public_payload(build_report())

    unsafe_fragments = (
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
    for fragment in unsafe_fragments:
        unsafe_key_payload = dict(payload)
        unsafe_key_payload[f"{fragment}_field"] = "redacted"
        with pytest.raises(ValueError, match="unsafe public payload"):
            research_packet_source_chain_integrity_gate_v2_public_payload(
                unsafe_key_payload,
            )

        unsafe_value_payload = dict(payload)
        unsafe_value_payload["config_version"] = f"contains-{fragment}"
        with pytest.raises(ValueError, match="unsafe public payload"):
            research_packet_source_chain_integrity_gate_v2_public_payload(
                unsafe_value_payload,
            )


def test_public_payload_rejects_numeric_scalars_and_false_flags() -> None:
    payload = research_packet_source_chain_integrity_gate_v2_public_payload(build_report())

    numeric_payload = dict(payload)
    numeric_payload["source_count"] = 6
    with pytest.raises(ValueError, match="Decimal strings"):
        research_packet_source_chain_integrity_gate_v2_public_payload(numeric_payload)

    false_flag_payload = dict(payload)
    false_flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_packet_source_chain_integrity_gate_v2_public_payload(false_flag_payload)


def test_decimal_only_validation_rejects_float_and_integer_inputs() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        ResearchPacketSourceChainEvidence(
            evidence_id="bad-decimal",
            source_family="source_family",
            source_kind="independent_source",
            observed_at=GENERATED_AT,
            probability_move_attribution=0.1,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Decimal"):
        ResearchPacketSourceChainIntegrityGateV2Config(
            min_official_anchor_count=1,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Decimal"):
        build_research_packet_source_chain_integrity_gate_v2(
            complete_sources(),
            config=ResearchPacketSourceChainIntegrityGateV2Config(),
            generated_at=GENERATED_AT,
            probability_move_since_prior_packet=1,  # type: ignore[arg-type]
        )


def test_rejects_non_iterable_duplicates_future_sources_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="iterable"):
        build_research_packet_source_chain_integrity_gate_v2(
            "not rows",  # type: ignore[arg-type]
            config=ResearchPacketSourceChainIntegrityGateV2Config(),
            generated_at=GENERATED_AT,
            probability_move_since_prior_packet=d("0.000000"),
        )

    duplicate = complete_sources()[0]
    with pytest.raises(ValueError, match="unique"):
        build_report((duplicate, duplicate))

    future_source = replace(complete_sources()[0], observed_at=GENERATED_AT + timedelta(seconds=1))
    with pytest.raises(ValueError, match="observed_at"):
        build_report((future_source,))

    with pytest.raises(ValueError, match="paper_only"):
        replace(complete_sources()[0], paper_only=False)


def test_report_consistency_rejects_manual_mismatches() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="source_count"):
        replace(report, source_count=d("7"))
    with pytest.raises(ValueError, match="probability_move_unattributed"):
        replace(report, probability_move_unattributed=d("0.010000"))
    with pytest.raises(ValueError, match="gate_status"):
        replace(report, gate_status="blocked")


def test_dataclasses_are_frozen() -> None:
    config = ResearchPacketSourceChainIntegrityGateV2Config()
    evidence = complete_sources()[0]
    report = build_report()
    row = report.evidence_rows[0]

    frozen_values: tuple[Any, ...] = (config, evidence, row, report)
    for value in frozen_values:
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    assert isinstance(row, ResearchPacketSourceChainIntegrityGateV2Row)
