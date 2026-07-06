from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab import research_packet_official_source_anchor_score_v2 as module


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def _anchor(
    *,
    anchor_id: str = "anchor-election-board",
    packet_id: str = "packet-election-001",
    event_id: str = "event-election-001",
    source_family: str = "election-board",
    source_title: str = "Official election board bulletin",
    observed_delta: timedelta = timedelta(hours=1),
    official_strength_score: Decimal = Decimal("0.950000"),
    resolution_relevance: Decimal = Decimal("1.000000"),
    ambiguity_coverage: Decimal = Decimal("0.900000"),
    contradiction_handling: Decimal = Decimal("1.000000"),
) -> module.ResearchPacketOfficialSourceAnchorInput:
    return module.ResearchPacketOfficialSourceAnchorInput(
        packet_id=packet_id,
        event_id=event_id,
        anchor_id=anchor_id,
        source_family=source_family,
        source_title=source_title,
        observed_at=GENERATED_AT - observed_delta,
        official_strength_score=official_strength_score,
        resolution_relevance=resolution_relevance,
        ambiguity_coverage=ambiguity_coverage,
        contradiction_handling=contradiction_handling,
    )


def _report() -> module.ResearchPacketOfficialSourceAnchorScoreReport:
    return module.build_research_packet_official_source_anchor_score_v2_report(
        (
            _anchor(anchor_id="anchor-election-board"),
            _anchor(
                anchor_id="anchor-court-docket",
                source_family="court-docket",
                source_title="Official court docket notice",
                official_strength_score=Decimal("0.900000"),
                resolution_relevance=Decimal("0.950000"),
            ),
            _anchor(
                anchor_id="anchor-duplicate-family",
                source_family="election-board",
                source_title="Official election board certification",
                official_strength_score=Decimal("0.880000"),
                resolution_relevance=Decimal("0.900000"),
            ),
        ),
        config=module.ResearchPacketOfficialSourceAnchorScoreConfig(),
        generated_at=GENERATED_AT,
    )


def test_builds_decimal_only_report_and_public_payload() -> None:
    report = _report()

    assert report.status == "pass"
    assert report.anchor_count == Decimal("3")
    assert report.packet_count == Decimal("1")
    assert report.source_family_count == Decimal("2")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)

    first_row = report.rows[0]
    assert first_row.source_family_independence == Decimal("0.500000")
    assert first_row.anchor_score == Decimal("0.901250")

    payload = module.research_packet_official_source_anchor_score_v2_payload(report)
    assert payload["anchor_count"] == "3"
    assert payload["average_anchor_score"] == "0.903750"
    assert payload["rows"][0]["anchor_score"] == "0.901250"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_low_scores_staleness_and_repeated_family_drive_blocked_status() -> None:
    config = module.ResearchPacketOfficialSourceAnchorScoreConfig(
        max_source_age_seconds=Decimal("100.000000"),
        min_source_family_independence=Decimal("0.750000"),
    )

    report = module.build_research_packet_official_source_anchor_score_v2_report(
        (
            _anchor(
                anchor_id="anchor-low-one",
                source_family="thin-family",
                observed_delta=timedelta(seconds=200),
                official_strength_score=Decimal("0.300000"),
                resolution_relevance=Decimal("0.400000"),
                ambiguity_coverage=Decimal("0.200000"),
                contradiction_handling=Decimal("0.300000"),
            ),
            _anchor(
                anchor_id="anchor-low-two",
                source_family="thin-family",
                observed_delta=timedelta(seconds=150),
                official_strength_score=Decimal("0.400000"),
                resolution_relevance=Decimal("0.450000"),
                ambiguity_coverage=Decimal("0.300000"),
                contradiction_handling=Decimal("0.200000"),
            ),
        ),
        config=config,
        generated_at=GENERATED_AT,
    )

    assert report.status == "blocked"
    assert report.blocked_count == Decimal("2")
    assert report.stale_anchor_count == Decimal("2")
    assert report.low_official_strength_count == Decimal("2")
    assert report.low_resolution_relevance_count == Decimal("2")
    assert report.thin_source_family_independence_count == Decimal("2")
    assert report.ambiguity_gap_count == Decimal("2")
    assert report.contradiction_handling_gap_count == Decimal("2")
    assert report.reason_codes == (
        "official_source_anchor_score_blocked",
        "low_official_strength",
        "low_resolution_relevance",
        "stale_source_anchor",
        "thin_source_family_independence",
        "thin_ambiguity_coverage",
        "weak_contradiction_handling",
    )


def test_frozen_dataclass_and_digest_reject_report_tampering() -> None:
    report = _report()

    with pytest.raises(FrozenInstanceError):
        report.status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = module.research_packet_official_source_anchor_score_v2_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["average_anchor_score"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_official_source_anchor_score_v2_payload(tampered_payload)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_official_source_anchor_score_v2_payload(missing_digest)


def test_public_payload_rejects_unsafe_keys_and_values() -> None:
    payload = module.research_packet_official_source_anchor_score_v2_payload(_report())

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["wallet_reference"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public key"):
        module.research_packet_official_source_anchor_score_v2_payload(unsafe_key_payload)

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [dict(payload["rows"][0], source_title="live order page")]
    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_packet_official_source_anchor_score_v2_payload(unsafe_value_payload)

    with pytest.raises(ValueError, match="unsafe public value"):
        _anchor(source_title="Official wallet resolution page")


def test_inputs_require_decimals_hard_flags_and_safe_time_ordering() -> None:
    with pytest.raises(ValueError, match="official_strength_score must be a Decimal"):
        _anchor(official_strength_score=0.9)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchPacketOfficialSourceAnchorScoreConfig(paper_only=False)

    future_anchor = _anchor(observed_delta=timedelta(seconds=-1))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        module.build_research_packet_official_source_anchor_score_v2_report(
            (future_anchor,),
            config=module.ResearchPacketOfficialSourceAnchorScoreConfig(),
            generated_at=GENERATED_AT,
        )


def test_rejects_duplicate_anchor_identity_and_unsupported_payload_type() -> None:
    anchor = _anchor()

    with pytest.raises(ValueError, match="unique by packet_id and anchor_id"):
        module.build_research_packet_official_source_anchor_score_v2_report(
            (anchor, anchor),
            config=module.ResearchPacketOfficialSourceAnchorScoreConfig(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="report must be"):
        module.research_packet_official_source_anchor_score_v2_payload(object())
