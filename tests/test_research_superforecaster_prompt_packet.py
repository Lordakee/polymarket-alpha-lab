from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


def api():
    return import_module("polymarket_alpha_lab.research_superforecaster_prompt_packet")


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence_summary(**overrides: object):
    values: dict[str, object] = {
        "assessment_label": "well_supported",
        "evidence_strength": d("0.860000"),
        "independent_evidence_count": d("3"),
        "missing_evidence_count": d("0"),
        "evidence_points": (
            "official_record_aligned",
            "independent_check_consistent",
        ),
    }
    values.update(overrides)
    return api().SuperforecasterEvidenceSummary(**values)


def base_rate_summary(**overrides: object):
    values: dict[str, object] = {
        "reference_class": "recent_policy_events",
        "base_rate_probability": d("0.420000"),
        "base_rate_sample_count": d("50"),
        "base_rate_quality": d("0.780000"),
        "base_rate_points": ("reference_class_relevant",),
    }
    values.update(overrides)
    return api().SuperforecasterBaseRateSummary(**values)


def rule_risk_summary(**overrides: object):
    values: dict[str, object] = {
        "rule_clarity": d("0.840000"),
        "resolution_rule_risk": d("0.100000"),
        "ambiguity_risk": d("0.050000"),
        "rule_risk_codes": ("rule_clear",),
        "rule_points": ("resolution_window_explicit",),
    }
    values.update(overrides)
    return api().SuperforecasterRuleRiskSummary(**values)


def cost_threshold(**overrides: object):
    values: dict[str, object] = {
        "maximum_research_cost_bps": d("30.000000"),
        "estimated_research_cost_bps": d("12.500000"),
        "minimum_evidence_strength": d("0.700000"),
        "minimum_base_rate_count": d("10"),
        "maximum_rule_risk": d("0.300000"),
    }
    values.update(overrides)
    return api().SuperforecasterCostThreshold(**values)


def build_packet(
    evidence: object | None = None,
    base_rate: object | None = None,
    rule_risk: object | None = None,
    cost: object | None = None,
):
    return api().build_research_superforecaster_prompt_packet(
        evidence_summary() if evidence is None else evidence,
        base_rate_summary() if base_rate is None else base_rate,
        rule_risk_summary() if rule_risk is None else rule_risk,
        cost_threshold() if cost is None else cost,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def assert_public_payload_is_sanitized(value: Any) -> None:
    encoded = json.dumps(value, sort_keys=True).lower()
    for term in (
        "raw-candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "https://",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    ):
        assert term not in encoded


def test_complete_pass_builds_human_and_llm_prompt_packet() -> None:
    module = api()

    packet = build_packet()

    assert packet == module.ResearchSuperforecasterPromptPacket(
        status="pass",
        evidence_summary=evidence_summary(),
        base_rate_summary=base_rate_summary(),
        rule_risk_summary=rule_risk_summary(),
        cost_threshold=cost_threshold(),
        prompt_sections=packet.prompt_sections,
        reason_codes=(
            "evidence_ready",
            "base_rate_ready",
            "rule_risk_within_threshold",
            "cost_within_threshold",
            "public_status_pass",
        ),
        derived_validation_digest=packet.derived_validation_digest,
    )
    assert tuple(section.audience for section in packet.prompt_sections) == (
        "human",
        "llm",
    )
    assert packet.paper_only is True
    assert packet.report_only is True
    assert packet.readonly is True

    payload = packet.payload
    assert payload["status"] == "pass"
    assert payload["evidence_summary"]["evidence_strength"] == "0.860000"
    assert payload["base_rate_summary"]["base_rate_probability"] == "0.420000"
    assert payload["cost_threshold"]["estimated_research_cost_bps"] == "12.500000"
    assert payload["prompt_sections"][0]["audience"] == "human"
    assert payload["prompt_sections"][1]["audience"] == "llm"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)
    assert_public_payload_is_sanitized(payload)


def test_missing_evidence_routes_prompt_packet_to_watch() -> None:
    packet = build_packet(
        evidence=evidence_summary(
            independent_evidence_count=d("1"),
            missing_evidence_count=d("2"),
            evidence_points=("official_record_aligned",),
        ),
    )

    assert packet.status == "watch"
    assert packet.reason_codes == (
        "evidence_missing",
        "base_rate_ready",
        "rule_risk_within_threshold",
        "cost_within_threshold",
        "public_status_watch",
    )
    assert packet.payload["status"] == "watch"
    assert packet.payload["evidence_summary"]["missing_evidence_count"] == "2"
    assert_public_payload_is_sanitized(packet.payload)


def test_public_leakage_blocks_and_redacts_prompt_packet() -> None:
    packet = build_packet(
        evidence=evidence_summary(
            evidence_points=(
                "raw-candidate-123 source_url https://example.invalid/path buy yes",
            ),
        ),
    )

    assert packet.status == "block"
    assert "unsafe_public_content_redacted" in packet.reason_codes
    assert packet.evidence_summary.evidence_points == ("<redacted>",)
    assert packet.payload["evidence_summary"]["evidence_points"] == ["<redacted>"]
    assert_public_payload_is_sanitized(packet.payload)


def test_rejects_non_decimal_and_non_tuple_input_types() -> None:
    with pytest.raises(ValueError, match="evidence_strength must be a Decimal"):
        evidence_summary(evidence_strength=0.86)
    with pytest.raises(ValueError, match="independent_evidence_count must be a Decimal"):
        evidence_summary(independent_evidence_count=3)
    with pytest.raises(ValueError, match="evidence_points must be a tuple"):
        evidence_summary(evidence_points=["official_record_aligned"])
    with pytest.raises(
        ValueError,
        match="evidence_summary must be a SuperforecasterEvidenceSummary",
    ):
        build_packet(evidence=object())


def test_hard_paper_only_report_only_readonly_flags_are_required() -> None:
    with pytest.raises(ValueError, match="paper_only must be True"):
        evidence_summary(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        base_rate_summary(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        cost_threshold(readonly=False)

    packet = build_packet()

    assert packet.paper_only is True
    assert packet.report_only is True
    assert packet.readonly is True
    assert packet.payload["paper_only"] is True
    assert packet.payload["report_only"] is True
    assert packet.payload["readonly"] is True


def test_packet_output_is_deterministic_and_dataclasses_are_frozen() -> None:
    module = api()
    left = build_packet()
    right = build_packet()

    assert left == right
    assert left.payload == right.payload
    assert left.derived_validation_digest == right.derived_validation_digest
    assert json.dumps(left.payload, sort_keys=True) == json.dumps(
        right.payload,
        sort_keys=True,
    )
    assert module.SuperforecasterEvidenceSummary.__dataclass_params__.frozen
    assert module.SuperforecasterBaseRateSummary.__dataclass_params__.frozen
    assert module.SuperforecasterRuleRiskSummary.__dataclass_params__.frozen
    assert module.SuperforecasterCostThreshold.__dataclass_params__.frozen
    assert module.SuperforecasterPromptSection.__dataclass_params__.frozen
    assert module.ResearchSuperforecasterPromptPacket.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        left.status = "watch"  # type: ignore[misc]
