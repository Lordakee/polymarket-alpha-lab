from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module("polymarket_alpha_lab.research_review_packet_builder")


def score_summary(**overrides: Any):
    values: dict[str, Any] = {
        "score_band": "high_confidence",
        "review_confidence": d("0.910000"),
        "evidence_strength": d("0.880000"),
        "explanation_coverage": d("0.840000"),
        "leakage_risk": d("0.000000"),
        "missing_evidence_count": d("0"),
        "summary_codes": ("well_supported", "explanation_complete"),
    }
    values.update(overrides)
    return api().RedactedReviewScoreSummary(**values)


def team_route(**overrides: Any):
    values: dict[str, Any] = {
        "team_id": "politics",
        "route_label": "senior_manual_review",
        "route_reason_codes": ("team_domain_match",),
    }
    values.update(overrides)
    return api().ReviewTeamRoute(**values)


def cost_threshold(**overrides: Any):
    values: dict[str, Any] = {
        "maximum_review_cost_bps": d("25.000000"),
        "estimated_review_cost_bps": d("12.500000"),
        "minimum_pass_score": d("0.700000"),
    }
    values.update(overrides)
    return api().ReviewCostThreshold(**values)


def explanation_layer(**overrides: Any):
    values: dict[str, Any] = {
        "explanation_codes": ("official_quorum_present", "timeliness_checked"),
        "public_rationale_points": (
            "resolution_rule_confirmed",
            "independent_public_evidence_aligned",
        ),
    }
    values.update(overrides)
    return api().ReviewExplanationLayer(**values)


def build_packet(
    score: object | None = None,
    route: object | None = None,
    cost: object | None = None,
    layer: object | None = None,
):
    return api().build_research_review_packet(
        score_summary() if score is None else score,
        team_route() if route is None else route,
        cost_threshold() if cost is None else cost,
        explanation_layer() if layer is None else layer,
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
    forbidden = (
        "raw-candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
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
    )
    encoded = json.dumps(value, sort_keys=True).lower()
    for term in forbidden:
        assert term not in encoded


def test_complete_packet_pass_combines_review_inputs_into_public_payload() -> None:
    module = api()

    packet = build_packet()

    assert packet == module.ResearchReviewPacket(
        review_status="pass",
        score_summary=score_summary(),
        team_route=team_route(),
        cost_threshold=cost_threshold(),
        explanation_layer=explanation_layer(),
        reason_codes=(
            "score_meets_pass_threshold",
            "evidence_complete",
            "cost_within_threshold",
            "explanation_layer_complete",
            "team_route_ready",
            "public_status_pass",
        ),
        derived_validation_digest=packet.derived_validation_digest,
    )
    assert packet.paper_only is True
    assert packet.report_only is True
    assert packet.readonly is True
    assert type(packet.score_summary.review_confidence) is Decimal
    assert type(packet.cost_threshold.maximum_review_cost_bps) is Decimal

    payload = packet.payload
    assert payload["review_status"] == "pass"
    assert payload["score_summary"]["review_confidence"] == "0.910000"
    assert payload["cost_threshold"]["estimated_review_cost_bps"] == "12.500000"
    assert payload["team_route"]["team_id"] == "politics"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)
    assert_public_payload_is_sanitized(payload)


def test_missing_evidence_routes_packet_to_watch_without_leaking_inputs() -> None:
    packet = build_packet(
        score_summary(
            review_confidence=d("0.720000"),
            evidence_strength=d("0.610000"),
            missing_evidence_count=d("2"),
            summary_codes=("thin_evidence",),
        ),
    )

    assert packet.review_status == "watch"
    assert packet.reason_codes == (
        "score_meets_pass_threshold",
        "evidence_missing",
        "cost_within_threshold",
        "explanation_layer_complete",
        "team_route_ready",
        "public_status_watch",
    )
    assert packet.payload["review_status"] == "watch"
    assert packet.payload["score_summary"]["missing_evidence_count"] == "2"
    assert_public_payload_is_sanitized(packet.payload)


def test_public_leakage_blocks_packet_and_redacts_payload() -> None:
    packet = build_packet(
        layer=explanation_layer(
            public_rationale_points=(
                "buy yes on raw-candidate-123 at https://example.invalid/market_slug",
            ),
        ),
    )

    assert packet.review_status == "block"
    assert "unsafe_public_content_redacted" in packet.reason_codes
    assert packet.explanation_layer.public_rationale_points == ("<redacted>",)
    assert packet.payload["explanation_layer"]["public_rationale_points"] == [
        "<redacted>",
    ]
    assert_public_payload_is_sanitized(packet.payload)


def test_rejects_non_decimal_and_non_tuple_input_types() -> None:
    with pytest.raises(ValueError, match="review_confidence must be a Decimal"):
        score_summary(review_confidence=0.91)
    with pytest.raises(ValueError, match="missing_evidence_count must be a Decimal"):
        score_summary(missing_evidence_count=0)
    with pytest.raises(ValueError, match="summary_codes must be a tuple"):
        score_summary(summary_codes=["well_supported"])
    with pytest.raises(ValueError, match="score_summary must be a RedactedReviewScoreSummary"):
        build_packet(score=object())


def test_hard_paper_only_report_only_readonly_flags_are_required() -> None:
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_summary(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        team_route(report_only=False)
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
    assert module.RedactedReviewScoreSummary.__dataclass_params__.frozen
    assert module.ReviewTeamRoute.__dataclass_params__.frozen
    assert module.ReviewCostThreshold.__dataclass_params__.frozen
    assert module.ReviewExplanationLayer.__dataclass_params__.frozen
    assert module.ResearchReviewPacket.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        left.review_status = "watch"  # type: ignore[misc]
