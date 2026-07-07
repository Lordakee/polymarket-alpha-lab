from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_packet_resolution_evidence_sufficiency_score_v2 import (
    DEFAULT_RESEARCH_PACKET_RESOLUTION_EVIDENCE_SUFFICIENCY_SCORE_V2_CONFIG_VERSION,
    ResearchPacketResolutionEvidenceSufficiencyScoreV2Config,
    ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet,
    ResearchPacketResolutionEvidenceSufficiencyScoreV2Report,
    ResearchPacketResolutionEvidenceSufficiencyScoreV2Row,
    build_research_packet_resolution_evidence_sufficiency_score_v2_report,
    research_packet_resolution_evidence_sufficiency_score_v2_payload,
    validate_research_packet_resolution_evidence_sufficiency_score_v2_public_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _unsafe(*parts: str) -> str:
    return "".join(parts)


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("float found in public payload")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list | tuple):
        for item in value:
            assert_no_float(item)


def _packet(
    packet_id: str = "packet_alpha",
    **overrides: object,
) -> ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet:
    values: dict[str, object] = {
        "event_id": f"event_{packet_id}",
        "packet_id": packet_id,
        "event_category": "macro_cpi",
        "captured_at": GENERATED_AT - timedelta(minutes=30),
        "official_anchor_count": d("1"),
        "independent_source_family_count": d("2"),
        "freshest_evidence_observed_at": GENERATED_AT - timedelta(minutes=20),
        "contradiction_reviewed": True,
        "unresolved_contradiction_severity": d("0"),
        "resolution_rule_clarity_score": d("0.900000"),
        "settlement_evidence_count": d("1"),
        "source_attribution_coverage_ratio": d("1"),
    }
    values.update(overrides)
    return ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet(**values)


def _report() -> ResearchPacketResolutionEvidenceSufficiencyScoreV2Report:
    return build_research_packet_resolution_evidence_sufficiency_score_v2_report(
        (
            _packet(
                "gap_packet",
                official_anchor_count=d("0"),
                independent_source_family_count=d("1"),
                freshest_evidence_observed_at=GENERATED_AT - timedelta(hours=2),
                contradiction_reviewed=False,
                unresolved_contradiction_severity=d("0.600000"),
                resolution_rule_clarity_score=d("0.500000"),
                settlement_evidence_count=d("0"),
                source_attribution_coverage_ratio=d("0.250000"),
            ),
            _packet(
                "watch_packet",
                independent_source_family_count=d("1"),
                source_attribution_coverage_ratio=d("0.500000"),
            ),
            _packet("sufficient_packet"),
        ),
        config=ResearchPacketResolutionEvidenceSufficiencyScoreV2Config(),
        generated_at=GENERATED_AT,
    )


def test_report_scores_resolution_evidence_dimensions_with_decimal_only_counts() -> None:
    report = _report()

    assert isinstance(report, ResearchPacketResolutionEvidenceSufficiencyScoreV2Report)
    assert (
        report.config_version
        == DEFAULT_RESEARCH_PACKET_RESOLUTION_EVIDENCE_SUFFICIENCY_SCORE_V2_CONFIG_VERSION
    )
    assert report.report_status == "insufficient"
    assert report.packet_count == d("3.000000")
    assert report.sufficient_packet_count == d("1.000000")
    assert report.watch_packet_count == d("1.000000")
    assert report.insufficient_packet_count == d("1.000000")
    assert report.attention_packet_count == d("2.000000")
    assert report.official_anchor_gap_packet_count == d("1.000000")
    assert report.source_family_gap_packet_count == d("2.000000")
    assert report.stale_evidence_packet_count == d("1.000000")
    assert report.contradiction_review_gap_packet_count == d("1.000000")
    assert report.rule_clarity_gap_packet_count == d("1.000000")
    assert report.settlement_evidence_gap_packet_count == d("1.000000")
    assert report.source_attribution_gap_packet_count == d("2.000000")
    assert report.average_sufficiency_score == d("0.686508")
    assert report.min_sufficiency_score_observed == d("0.202381")
    assert tuple((row.packet_id, row.sufficiency_status) for row in report.rows) == (
        ("gap_packet", "insufficient"),
        ("watch_packet", "watch"),
        ("sufficient_packet", "sufficient"),
    )
    assert report.rows[0] == ResearchPacketResolutionEvidenceSufficiencyScoreV2Row(
        event_id="event_gap_packet",
        packet_id="gap_packet",
        event_category="macro_cpi",
        captured_at=GENERATED_AT - timedelta(minutes=30),
        official_anchor_count=d("0.000000"),
        independent_source_family_count=d("1.000000"),
        freshest_evidence_observed_at=GENERATED_AT - timedelta(hours=2),
        evidence_age_seconds=d("7200.000000"),
        contradiction_reviewed=False,
        unresolved_contradiction_severity=d("0.600000"),
        resolution_rule_clarity_score=d("0.500000"),
        settlement_evidence_count=d("0.000000"),
        source_attribution_coverage_ratio=d("0.250000"),
        official_anchor_score=d("0.000000"),
        source_family_score=d("0.500000"),
        freshness_score=d("0.000000"),
        contradiction_review_score=d("0.000000"),
        rule_clarity_component_score=d("0.666667"),
        settlement_evidence_score=d("0.000000"),
        source_attribution_score=d("0.250000"),
        sufficiency_score=d("0.202381"),
        sufficiency_status="insufficient",
        reason_codes=(
            "research_packet_resolution_evidence_sufficiency_score_v2_missing_official_anchor",
            "research_packet_resolution_evidence_sufficiency_score_v2_insufficient_source_families",
            "research_packet_resolution_evidence_sufficiency_score_v2_stale_evidence",
            "research_packet_resolution_evidence_sufficiency_score_v2_contradiction_review_missing",
            "research_packet_resolution_evidence_sufficiency_score_v2_rule_clarity_weak",
            "research_packet_resolution_evidence_sufficiency_score_v2_settlement_evidence_missing",
            "research_packet_resolution_evidence_sufficiency_score_v2_source_attribution_weak",
        ),
        derived_validation_digest=report.rows[0].derived_validation_digest,
    )
    assert report.reason_code_counts[1].reason_code.endswith(
        "insufficient_source_families",
    )
    assert report.reason_code_counts[1].packet_count == d("2.000000")
    assert report.reason_code_counts[1].packet_ratio == d("0.666667")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)


def test_payload_serializes_decimal_strings_and_rejects_public_tampering() -> None:
    report = build_research_packet_resolution_evidence_sufficiency_score_v2_report(
        (
            _packet(
                "offset_packet",
                captured_at=datetime(2026, 7, 6, 7, 30, tzinfo=timezone(timedelta(hours=-4))),
                freshest_evidence_observed_at=datetime(
                    2026,
                    7,
                    6,
                    7,
                    45,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
            ),
        ),
        config=ResearchPacketResolutionEvidenceSufficiencyScoreV2Config(),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = research_packet_resolution_evidence_sufficiency_score_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["packet_count"] == "1.000000"
    assert payload["average_sufficiency_score"] == "1.000000"
    assert payload["rows"][0]["captured_at"] == "2026-07-06T11:30:00+00:00"
    assert payload["rows"][0]["evidence_age_seconds"] == "900.000000"
    assert payload["rows"][0]["source_family_score"] == "1.000000"
    assert payload["rows"][0]["derived_validation_digest"] == report.rows[0].derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float(payload)
    assert validate_research_packet_resolution_evidence_sufficiency_score_v2_public_payload(
        payload,
    )

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_packet_resolution_evidence_sufficiency_score_v2_public_payload(
            missing_digest,
        )

    tampered_payload = dict(payload)
    tampered_payload["packet_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_packet_resolution_evidence_sufficiency_score_v2_payload(tampered_payload)

    tampered_row_payload = dict(payload)
    tampered_row_payload["rows"] = [dict(payload["rows"][0])]
    tampered_row_payload["rows"][0]["sufficiency_score"] = "0.500000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_packet_resolution_evidence_sufficiency_score_v2_payload(tampered_row_payload)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload[_unsafe("wal", "let", "_id")] = "redacted"
    with pytest.raises(ValueError, match="public"):
        research_packet_resolution_evidence_sufficiency_score_v2_payload(unsafe_key_payload)

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["operator_note"] = _unsafe("needs_", "tra", "de", "_desk")
    with pytest.raises(ValueError, match="public"):
        research_packet_resolution_evidence_sufficiency_score_v2_payload(unsafe_value_payload)


def test_frozen_decimal_only_inputs_flags_and_dataclass_tamper_revalidation() -> None:
    with pytest.raises(ValueError, match="config_version"):
        ResearchPacketResolutionEvidenceSufficiencyScoreV2Config(
            config_version=_StringSubclass(
                DEFAULT_RESEARCH_PACKET_RESOLUTION_EVIDENCE_SUFFICIENCY_SCORE_V2_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="min_official_anchor_count"):
        ResearchPacketResolutionEvidenceSufficiencyScoreV2Config(min_official_anchor_count=1)
    with pytest.raises(ValueError, match="min_independent_source_family_count"):
        ResearchPacketResolutionEvidenceSufficiencyScoreV2Config(
            min_independent_source_family_count=_DecimalSubclass("2"),
        )
    with pytest.raises(ValueError, match="max_unresolved_contradiction_severity"):
        ResearchPacketResolutionEvidenceSufficiencyScoreV2Config(
            max_unresolved_contradiction_severity=0.25,
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(ResearchPacketResolutionEvidenceSufficiencyScoreV2Config(), paper_only=False)
    with pytest.raises(ValueError, match="event_id"):
        _packet("unsafe_packet", event_id=_unsafe("au", "th", "_reference"))
    with pytest.raises(ValueError, match="official_anchor_count"):
        _packet("numeric_packet", official_anchor_count=1)
    with pytest.raises(ValueError, match="source_attribution_coverage_ratio"):
        _packet("float_packet", source_attribution_coverage_ratio=0.5)
    with pytest.raises(ValueError, match="captured_at"):
        _packet("naive_packet", captured_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_packet_resolution_evidence_sufficiency_score_v2_report(
            (_packet("packet"),),
            config=ResearchPacketResolutionEvidenceSufficiencyScoreV2Config(),
            generated_at=_DateTimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )

    report = _report()
    with pytest.raises(FrozenInstanceError):
        report.report_status = "sufficient"
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_report = _report()
    object.__setattr__(tampered_report.rows[0], "sufficiency_score", d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest|sufficiency_score"):
        research_packet_resolution_evidence_sufficiency_score_v2_payload(tampered_report)

    tampered_count_report = _report()
    object.__setattr__(tampered_count_report, "packet_count", d("4.000000"))
    with pytest.raises(ValueError, match="packet_count|derived_validation_digest"):
        research_packet_resolution_evidence_sufficiency_score_v2_payload(
            tampered_count_report,
        )

    for public_type in (
        ResearchPacketResolutionEvidenceSufficiencyScoreV2Config,
        ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet,
        ResearchPacketResolutionEvidenceSufficiencyScoreV2Row,
        ResearchPacketResolutionEvidenceSufficiencyScoreV2Report,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):

            class _Subclass(public_type):  # type: ignore[misc, valid-type]
                pass


def test_module_scope_is_readonly_report_only_and_has_no_external_surface() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_packet_resolution_evidence_sufficiency_score_v2",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    lowered_source = source.lower()

    forbidden_surface_tokens = (
        _unsafe("li", "ve"),
        _unsafe("au", "th"),
        _unsafe("wal", "let"),
        _unsafe("ord", "er"),
        _unsafe("net", "work"),
        _unsafe("data", "base"),
        _unsafe("per", "sist"),
        _unsafe("sign", "ing"),
        _unsafe("muta", "tion"),
        _unsafe("bu", "y"),
        _unsafe("se", "ll"),
        _unsafe("tra", "de"),
    )
    assert not any(token in lowered_source for token in forbidden_surface_tokens)
    assert not hasattr(module, "client")
    assert not hasattr(module, "session")

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "asyncio",
        "http",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
