from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.operator_decision_threshold_policy_readiness_report import (
    OperatorDecisionThresholdPolicyReadinessReport,
    build_operator_decision_threshold_policy_readiness_report,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(
    *,
    min_net_edge_probability: Decimal = d("0.060000"),
    min_confidence_probability: Decimal = d("0.700000"),
    max_cost_probability: Decimal = d("0.030000"),
    max_uncertainty_probability: Decimal = d("0.200000"),
    manual_override_required: bool = False,
) -> OperatorDecisionThresholdPolicyReadinessReport:
    return build_operator_decision_threshold_policy_readiness_report(
        min_net_edge_probability=min_net_edge_probability,
        min_confidence_probability=min_confidence_probability,
        max_cost_probability=max_cost_probability,
        max_uncertainty_probability=max_uncertainty_probability,
        manual_override_required=manual_override_required,
    )


def test_pass_report_is_public_readonly_and_digest_stable() -> None:
    readiness_report = build_report()

    assert type(readiness_report) is OperatorDecisionThresholdPolicyReadinessReport
    assert readiness_report.policy_status == "pass"
    assert readiness_report.reason_codes == (
        "net_edge_probability_ready",
        "confidence_probability_ready",
        "cost_probability_ready",
        "uncertainty_probability_ready",
        "manual_override_not_required",
        "operator_decision_threshold_policy_pass",
    )
    assert readiness_report.manual_next_step == "Proceed with paper-only operator review."
    assert readiness_report.paper_only is True
    assert readiness_report.report_only is True
    assert readiness_report.readonly is True

    payload = readiness_report.public_payload
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == {
        "manual_next_step": "Proceed with paper-only operator review.",
        "manual_override_required": False,
        "max_cost_probability": "0.030000",
        "max_uncertainty_probability": "0.200000",
        "min_confidence_probability": "0.700000",
        "min_net_edge_probability": "0.060000",
        "paper_only": True,
        "policy_status": "pass",
        "readonly": True,
        "reason_codes": [
            "net_edge_probability_ready",
            "confidence_probability_ready",
            "cost_probability_ready",
            "uncertainty_probability_ready",
            "manual_override_not_required",
            "operator_decision_threshold_policy_pass",
        ],
        "report_only": True,
    }
    assert readiness_report.payload_digest == (
        "dba3cbded05ea46364661b9ae7a9e000929dd8fb06080babf609afdc95d3e1f8"
    )
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.03" not in encoded
    assert "wallet" not in encoded
    assert "order" not in encoded


def test_watch_report_flags_soft_threshold_issues_without_manual_override() -> None:
    readiness_report = build_report(
        min_net_edge_probability=d("0.040000"),
        min_confidence_probability=d("0.650000"),
        max_cost_probability=d("0.070000"),
        max_uncertainty_probability=d("0.240000"),
    )

    assert readiness_report.policy_status == "watch"
    assert readiness_report.reason_codes == (
        "net_edge_probability_watch",
        "confidence_probability_watch",
        "cost_probability_watch",
        "uncertainty_probability_watch",
        "manual_override_not_required",
        "operator_decision_threshold_policy_watch",
    )
    assert readiness_report.manual_next_step == (
        "Review watch reason codes before any paper-only operator decision."
    )
    assert readiness_report.public_payload["policy_status"] == "watch"
    assert readiness_report.public_payload["max_cost_probability"] == "0.070000"


def test_block_report_requires_manual_review_for_hard_failures_or_override() -> None:
    readiness_report = build_report(
        min_net_edge_probability=d("0.010000"),
        min_confidence_probability=d("0.200000"),
        max_cost_probability=d("0.200000"),
        max_uncertainty_probability=d("0.900000"),
        manual_override_required=True,
    )

    assert readiness_report.policy_status == "block"
    assert readiness_report.reason_codes == (
        "net_edge_probability_below_minimum",
        "confidence_probability_below_minimum",
        "cost_probability_above_limit",
        "uncertainty_probability_above_limit",
        "manual_override_required",
        "operator_decision_threshold_policy_block",
    )
    assert readiness_report.manual_next_step == (
        "Manual override review required; keep the decision in paper-only mode."
    )
    assert readiness_report.public_payload["manual_override_required"] is True


def test_decimal_only_ratio_validation_and_readonly_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="min_net_edge_probability"):
        build_report(min_net_edge_probability=0.06)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_confidence_probability"):
        build_report(min_confidence_probability=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="max_cost_probability"):
        build_report(max_cost_probability=d("-0.000001"))
    with pytest.raises(ValueError, match="max_uncertainty_probability"):
        build_report(max_uncertainty_probability=d("1.000001"))
    with pytest.raises(ValueError, match="manual_override_required"):
        build_report(manual_override_required=1)  # type: ignore[arg-type]

    readiness_report = build_report()
    with pytest.raises(FrozenInstanceError):
        readiness_report.policy_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(readiness_report, paper_only=False)
    with pytest.raises(ValueError, match="payload_digest"):
        replace(readiness_report, payload_digest="bad")


def test_owned_module_has_no_live_auth_execution_or_persistence_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "operator_decision_threshold_policy_readiness_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        ".write",
        "jsonl",
        "persist",
        "connect(",
        "auth",
        "private_key",
        "api_key",
        "wallet",
        "sign",
        "signature",
        "place_order",
        "cancel_order",
        "execute",
        "execution",
        "position_size",
        "trade_recommendation",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
