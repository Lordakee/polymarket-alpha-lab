from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 15, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_resolution_source_confidence_band_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    values: dict[str, object] = {
        "config_version": "resolution-source-confidence-band-v2-test",
        "freshness_window_hours": d("24.000000"),
        "min_official_anchor_count": d("2"),
        "min_independent_source_family_count": d("3"),
        "pass_lower_confidence_threshold": d("0.700000"),
        "blocked_upper_confidence_threshold": d("0.550000"),
        "severe_contradiction_threshold": d("0.700000"),
        "min_band_width": d("0.020000"),
    }
    values.update(overrides)
    return api().ResearchPacketResolutionSourceConfidenceBandV2Config(**values)


def evidence(
    evidence_id: str,
    *,
    source_id: str,
    source_family: str,
    hours_ago: int,
    is_official_anchor: bool,
    official_anchor_score: str,
    contradiction_severity_score: str,
    rule_clarity_score: str,
    settlement_evidence_score: str,
    probability_move_attribution_score: str,
):
    return api().ResearchPacketResolutionSourceConfidenceBandV2Evidence(
        packet_id="packet-final-result",
        event_id="event-final-result",
        outcome_key="yes",
        evidence_id=evidence_id,
        source_id=source_id,
        source_family=source_family,
        observed_at=GENERATED_AT - timedelta(hours=hours_ago),
        is_official_anchor=is_official_anchor,
        official_anchor_score=d(official_anchor_score),
        contradiction_severity_score=d(contradiction_severity_score),
        rule_clarity_score=d(rule_clarity_score),
        settlement_evidence_score=d(settlement_evidence_score),
        probability_move_attribution_score=d(probability_move_attribution_score),
    )


def clear_evidence():
    return (
        evidence(
            "evidence-official-a",
            source_id="official-a",
            source_family="official-family-a",
            hours_ago=2,
            is_official_anchor=True,
            official_anchor_score="1.000000",
            contradiction_severity_score="0.100000",
            rule_clarity_score="0.950000",
            settlement_evidence_score="1.000000",
            probability_move_attribution_score="0.900000",
        ),
        evidence(
            "evidence-official-b",
            source_id="official-b",
            source_family="official-family-b",
            hours_ago=4,
            is_official_anchor=True,
            official_anchor_score="0.900000",
            contradiction_severity_score="0.200000",
            rule_clarity_score="0.900000",
            settlement_evidence_score="1.000000",
            probability_move_attribution_score="0.800000",
        ),
        evidence(
            "evidence-independent-c",
            source_id="independent-c",
            source_family="independent-family-c",
            hours_ago=1,
            is_official_anchor=False,
            official_anchor_score="0.500000",
            contradiction_severity_score="0.100000",
            rule_clarity_score="0.850000",
            settlement_evidence_score="0.800000",
            probability_move_attribution_score="0.700000",
        ),
    )


def build(rows=None, *, cfg=None):
    return api().build_research_packet_resolution_source_confidence_band_v2_report(
        clear_evidence() if rows is None else rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def assert_no_decimal_float_or_int(value: Any) -> None:
    assert type(value) is not Decimal
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_float_or_int(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_decimal_float_or_int(item)


def test_builds_decimal_confidence_bands_from_resolution_evidence_inputs() -> None:
    module = api()

    report = build()

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.evidence_count == d("3")
    assert report.official_anchor_count == d("2")
    assert report.independent_source_family_count == d("3")
    assert report.fresh_evidence_count == d("3")
    assert report.settlement_evidence_count == d("3")
    assert report.severe_contradiction_count == d("0")
    assert report.probability_move_attributed_count == d("3")
    assert report.average_lower_confidence == d("0.667194")
    assert report.average_midpoint_confidence == d("0.739583")
    assert report.average_upper_confidence == d("0.811972")
    assert report.confidence_band_status == "review"
    assert report.reason_codes == (
        "official_anchors_present",
        "independent_source_families_present",
        "fresh_evidence_present",
        "settlement_evidence_present",
        "probability_move_attributed",
        "confidence_band_review",
    )

    official_a = report.evidence_rows[0]
    assert official_a == module.ResearchPacketResolutionSourceConfidenceBandV2Row(
        packet_id="packet-final-result",
        event_id="event-final-result",
        outcome_key="yes",
        evidence_id="evidence-official-a",
        source_id="official-a",
        source_family="official-family-a",
        observed_at=GENERATED_AT - timedelta(hours=2),
        source_age_hours=d("2.000000"),
        is_official_anchor=True,
        official_anchor_score=d("1.000000"),
        independent_source_family_count=d("3"),
        source_family_independence_score=d("1.000000"),
        freshness_score=d("0.916667"),
        contradiction_severity_score=d("0.100000"),
        rule_clarity_score=d("0.950000"),
        settlement_evidence_score=d("1.000000"),
        probability_move_attribution_score=d("0.900000"),
        lower_confidence=d("0.778583"),
        midpoint_confidence=d("0.830833"),
        upper_confidence=d("0.883083"),
        band_width=d("0.052250"),
        confidence_band_status="pass",
        reason_codes=(
            "official_anchor_present",
            "fresh_evidence_present",
            "rule_clarity_high",
            "settlement_evidence_present",
            "probability_move_attributed",
            "confidence_band_pass",
        ),
    )


def test_blocked_report_reflects_stale_contradictory_unclear_unsettled_evidence() -> None:
    report = build(
        (
            evidence(
                "evidence-risk-a",
                source_id="risk-a",
                source_family="risk-family-a",
                hours_ago=48,
                is_official_anchor=False,
                official_anchor_score="0.100000",
                contradiction_severity_score="0.900000",
                rule_clarity_score="0.200000",
                settlement_evidence_score="0.000000",
                probability_move_attribution_score="0.000000",
            ),
        ),
    )

    assert report.evidence_count == d("1")
    assert report.official_anchor_count == d("0")
    assert report.independent_source_family_count == d("1")
    assert report.fresh_evidence_count == d("0")
    assert report.settlement_evidence_count == d("0")
    assert report.severe_contradiction_count == d("1")
    assert report.probability_move_attributed_count == d("0")
    assert report.average_lower_confidence == d("0.000000")
    assert report.average_midpoint_confidence == d("0.120000")
    assert report.average_upper_confidence == d("0.327000")
    assert report.confidence_band_status == "blocked"
    assert report.reason_codes == (
        "insufficient_official_anchors",
        "insufficient_source_family_independence",
        "stale_evidence_present",
        "severe_contradiction_present",
        "rule_clarity_low",
        "missing_settlement_evidence",
        "probability_move_unattributed",
        "confidence_band_blocked",
    )
    assert report.evidence_rows[0].confidence_band_status == "blocked"
    assert report.evidence_rows[0].reason_codes == (
        "official_anchor_missing",
        "stale_evidence_present",
        "severe_contradiction_present",
        "rule_clarity_low",
        "settlement_evidence_missing",
        "probability_move_unattributed",
        "confidence_band_blocked",
    )


def test_payload_serializes_decimal_strings_flags_digest_and_rejects_tampering() -> None:
    module = api()
    report = build()

    payload = module.research_packet_resolution_source_confidence_band_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T15:00:00+00:00"
    assert payload["evidence_count"] == "3"
    assert payload["average_midpoint_confidence"] == "0.739583"
    assert payload["evidence_rows"][0]["source_age_hours"] == "2.000000"
    assert payload["evidence_rows"][0]["midpoint_confidence"] == "0.830833"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert_no_decimal_float_or_int(payload)

    assert module.validate_research_packet_resolution_source_confidence_band_v2_payload(payload) == payload

    tampered = dict(payload)
    tampered["average_midpoint_confidence"] = "0.990000"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.validate_research_packet_resolution_source_confidence_band_v2_payload(
            tampered,
        )
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, confidence_band_status="pass")


def test_frozen_decimal_only_hard_flags_and_input_invariants() -> None:
    module = api()
    report = build()

    with pytest.raises(FrozenInstanceError):
        report.evidence_rows[0].source_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(clear_evidence()[0], readonly=False)

    class TaggedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="official_anchor_score must be a Decimal"):
        evidence(
            "evidence-tagged",
            source_id="tagged",
            source_family="tagged-family",
            hours_ago=1,
            is_official_anchor=True,
            official_anchor_score="1.000000",
            contradiction_severity_score="0.000000",
            rule_clarity_score="1.000000",
            settlement_evidence_score="1.000000",
            probability_move_attribution_score="1.000000",
        ).__class__(
            packet_id="packet-final-result",
            event_id="event-final-result",
            outcome_key="yes",
            evidence_id="evidence-tagged",
            source_id="tagged",
            source_family="tagged-family",
            observed_at=GENERATED_AT,
            is_official_anchor=True,
            official_anchor_score=TaggedDecimal("1.000000"),
            contradiction_severity_score=d("0.000000"),
            rule_clarity_score=d("1.000000"),
            settlement_evidence_score=d("1.000000"),
            probability_move_attribution_score=d("1.000000"),
        )

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        module.ResearchPacketResolutionSourceConfidenceBandV2Evidence(
            packet_id="packet-final-result",
            event_id="event-final-result",
            outcome_key="yes",
            evidence_id="evidence-naive",
            source_id="naive",
            source_family="naive-family",
            observed_at=datetime(2026, 7, 6, 15, 0),
            is_official_anchor=True,
            official_anchor_score=d("1.000000"),
            contradiction_severity_score=d("0.000000"),
            rule_clarity_score=d("1.000000"),
            settlement_evidence_score=d("1.000000"),
            probability_move_attribution_score=d("1.000000"),
        )

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build(
            (
                evidence(
                    "evidence-future",
                    source_id="future",
                    source_family="future-family",
                    hours_ago=-1,
                    is_official_anchor=True,
                    official_anchor_score="1.000000",
                    contradiction_severity_score="0.000000",
                    rule_clarity_score="1.000000",
                    settlement_evidence_score="1.000000",
                    probability_move_attribution_score="1.000000",
                ),
            ),
        )

    with pytest.raises(ValueError, match="evidence rows must share packet_id"):
        build(
            (
                clear_evidence()[0],
                replace(clear_evidence()[1], packet_id="packet-other"),
            ),
        )


def test_rejects_unsafe_public_keys_and_values_for_execution_surfaces() -> None:
    module = api()
    payload = module.research_packet_resolution_source_confidence_band_v2_payload(build())

    unsafe_keys = (
        "li" "ve_mode",
        "au" "th_token",
        "wa" "llet_address",
        "or" "der_id",
        "net" "work_client",
        "data" "base_url",
        "per" "sist_path",
        "sign" "ing_key",
        "muta" "tion_endpoint",
        "bu" "y_flag",
        "se" "ll_flag",
        "tra" "de_path",
    )
    for unsafe_key in unsafe_keys:
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public field"):
            module.validate_research_packet_resolution_source_confidence_band_v2_payload(
                unsafe_payload,
            )

    unsafe_values = (
        "li" "ve mode",
        "au" "th token",
        "wa" "llet field",
        "or" "der detail",
        "net" "work call",
        "data" "base field",
        "per" "sist record",
        "sign" "ing request",
        "muta" "tion path",
        "bu" "y button",
        "se" "ll action",
        "tra" "de route",
    )
    for unsafe_value in unsafe_values:
        unsafe_payload = dict(payload)
        unsafe_rows = [dict(row) for row in payload["evidence_rows"]]
        unsafe_rows[0]["source_id"] = unsafe_value
        unsafe_payload["evidence_rows"] = unsafe_rows
        with pytest.raises(ValueError, match="unsafe public value"):
            module.validate_research_packet_resolution_source_confidence_band_v2_payload(
                unsafe_payload,
            )

    with pytest.raises(ValueError, match="unsafe public value"):
        evidence(
            "evidence-unsafe",
            source_id="wa" "llet-feed",
            source_family="unsafe-family",
            hours_ago=1,
            is_official_anchor=True,
            official_anchor_score="1.000000",
            contradiction_severity_score="0.000000",
            rule_clarity_score="1.000000",
            settlement_evidence_score="1.000000",
            probability_move_attribution_score="1.000000",
        )


def test_module_stays_isolated_report_only_and_without_side_effect_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "asyncio",
        "http",
        "requests",
        "socket",
        "sqlite3",
        "supabase",
        "web3",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".", 1)[0] for alias in node.names}
            assert imported.isdisjoint(forbidden_import_roots)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots

    forbidden_names = {
        "connect",
        "execute",
        "request",
        "session",
        "commit",
        "rollback",
    }
    names = {node.id.lower() for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert names.isdisjoint(forbidden_names)
    assert "Path" not in source
    assert "open(" not in source


def test_export_contract_is_limited_to_phase1_report_api() -> None:
    module = api()

    assert set(module.__all__) == {
        "DEFAULT_RESEARCH_PACKET_RESOLUTION_SOURCE_CONFIDENCE_BAND_V2_CONFIG_VERSION",
        "CONFIDENCE_BAND_REASON_CODES",
        "CONFIDENCE_BAND_STATUSES",
        "ResearchPacketResolutionSourceConfidenceBandV2Config",
        "ResearchPacketResolutionSourceConfidenceBandV2Evidence",
        "ResearchPacketResolutionSourceConfidenceBandV2Row",
        "ResearchPacketResolutionSourceConfidenceBandV2Report",
        "build_research_packet_resolution_source_confidence_band_v2_report",
        "research_packet_resolution_source_confidence_band_v2_payload",
        "validate_research_packet_resolution_source_confidence_band_v2_payload",
    }
