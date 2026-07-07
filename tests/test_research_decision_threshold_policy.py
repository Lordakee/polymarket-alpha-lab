from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_decision_threshold_policy import (
    ResearchDecisionThresholdPolicyConfig,
    ResearchDecisionThresholdPolicyInput,
    ResearchDecisionThresholdPolicyReasonCodeCount,
    ResearchDecisionThresholdPolicyReport,
    ResearchDecisionThresholdPolicyRow,
    build_research_decision_threshold_policy_report,
    research_decision_threshold_policy_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchDecisionThresholdPolicyConfig:
    values = {
        "config_version": "research-decision-threshold-policy-v0",
        "pass_net_score": d("0.550000"),
        "watch_net_score": d("0.300000"),
        "min_edge_score": d("0.250000"),
        "min_confidence_score": d("0.400000"),
        "max_cost_score": d("0.500000"),
        "max_risk_score": d("0.500000"),
        "edge_weight": d("0.400000"),
        "confidence_weight": d("0.300000"),
        "cost_weight": d("0.150000"),
        "risk_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchDecisionThresholdPolicyConfig(**values)


def candidate(
    candidate_id: str,
    *,
    edge_score: Decimal = d("0.900000"),
    confidence_score: Decimal = d("0.850000"),
    cost_score: Decimal = d("0.100000"),
    risk_score: Decimal = d("0.100000"),
) -> ResearchDecisionThresholdPolicyInput:
    return ResearchDecisionThresholdPolicyInput(
        candidate_id=candidate_id,
        edge_score=edge_score,
        confidence_score=confidence_score,
        cost_score=cost_score,
        risk_score=risk_score,
    )


def report(
    rows: tuple[ResearchDecisionThresholdPolicyInput, ...],
    *,
    cfg: ResearchDecisionThresholdPolicyConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchDecisionThresholdPolicyReport:
    return build_research_decision_threshold_policy_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_without_candidate_rows() -> None:
    threshold_report = report(())

    assert type(threshold_report) is ResearchDecisionThresholdPolicyReport
    assert threshold_report.generated_at == GENERATED_AT
    assert threshold_report.config_version == "research-decision-threshold-policy-v0"
    assert threshold_report.status == "block"
    assert threshold_report.candidate_count == d("0")
    assert threshold_report.pass_count == d("0")
    assert threshold_report.watch_count == d("0")
    assert threshold_report.block_count == d("0")
    assert threshold_report.average_edge_score == d("0.000000")
    assert threshold_report.average_confidence_score == d("0.000000")
    assert threshold_report.average_cost_score == d("0.000000")
    assert threshold_report.average_risk_score == d("0.000000")
    assert threshold_report.average_net_score == d("0.000000")
    assert threshold_report.rows == ()
    assert threshold_report.reason_code_counts == (
        ResearchDecisionThresholdPolicyReasonCodeCount(
            reason_code="no_research_candidates",
            count=d("1"),
            candidate_ratio=d("1.000000"),
        ),
    )
    assert threshold_report.reason_codes == ("no_research_candidates",)
    assert "Research threshold report" in threshold_report.explanation
    assert threshold_report.paper_only is True
    assert threshold_report.report_only is True
    assert threshold_report.readonly is True


def test_pass_watch_and_block_rows_aggregate_decimal_thresholds() -> None:
    threshold_report = report(
        (
            candidate(
                "gamma",
                edge_score=d("0.800000"),
                confidence_score=d("0.900000"),
                risk_score=d("0.900000"),
            ),
            candidate(
                "beta",
                edge_score=d("0.650000"),
                confidence_score=d("0.650000"),
                cost_score=d("0.200000"),
                risk_score=d("0.250000"),
            ),
            candidate("alpha"),
        ),
    )

    assert threshold_report.status == "block"
    assert threshold_report.candidate_count == d("3")
    assert threshold_report.pass_count == d("1")
    assert threshold_report.watch_count == d("1")
    assert threshold_report.block_count == d("1")
    assert threshold_report.average_edge_score == d("0.783333")
    assert threshold_report.average_confidence_score == d("0.800000")
    assert threshold_report.average_cost_score == d("0.133333")
    assert threshold_report.average_risk_score == d("0.416667")
    assert threshold_report.average_net_score == d("0.470833")
    assert tuple(row.candidate_id for row in threshold_report.rows) == (
        "alpha",
        "beta",
        "gamma",
    )

    alpha, beta, gamma = threshold_report.rows
    assert type(alpha) is ResearchDecisionThresholdPolicyRow
    assert alpha.status == "pass"
    assert alpha.net_score == d("0.585000")
    assert alpha.weighted_edge_score == d("0.360000")
    assert alpha.weighted_confidence_score == d("0.255000")
    assert alpha.cost_drag_score == d("0.015000")
    assert alpha.risk_drag_score == d("0.015000")
    assert alpha.reason_codes == (
        "edge_threshold_met",
        "confidence_threshold_met",
        "cost_threshold_met",
        "risk_threshold_met",
        "net_score_pass_threshold_met",
        "research_decision_threshold_pass",
    )
    assert "candidate=alpha" in alpha.explanation
    assert "net_score=0.585000" in alpha.explanation

    assert beta.status == "watch"
    assert beta.net_score == d("0.387500")
    assert "research_decision_threshold_watch" in beta.reason_codes

    assert gamma.status == "block"
    assert gamma.net_score == d("0.440000")
    assert "risk_above_limit" in gamma.reason_codes
    assert "research_decision_threshold_block" in gamma.reason_codes


def test_payload_is_public_json_ready_and_contains_no_float_values() -> None:
    threshold_report = report((candidate("alpha"),))

    payload = research_decision_threshold_policy_report_payload(threshold_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["average_net_score"] == "0.585000"
    assert payload["rows"][0]["edge_score"] == "0.900000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    assert "trade_recommendation" not in encoded
    assert "position_size" not in encoded
    assert "wallet" not in encoded
    assert "order" not in encoded


def test_validation_rejects_bad_types_bad_ranges_times_and_flags() -> None:
    with pytest.raises(ValueError, match="edge_weight"):
        config(edge_weight=d("0.500000"))
    with pytest.raises(ValueError, match="pass_net_score"):
        config(pass_net_score=0.55)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_net_score"):
        config(watch_net_score=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((candidate("alpha"),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (candidate("alpha"),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="candidate_id"):
        candidate(" alpha")
    with pytest.raises(ValueError, match="edge_score"):
        candidate("alpha", edge_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="confidence_score"):
        candidate("alpha", confidence_score=d("1.000001"))
    with pytest.raises(ValueError, match="cost_score"):
        candidate("alpha", cost_score=d("-0.000001"))
    with pytest.raises(ValueError, match="risk_score"):
        candidate("alpha", risk_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate("alpha"), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_reports_validate_consistency() -> None:
    threshold_report = report((candidate("alpha"),))

    with pytest.raises(FrozenInstanceError):
        threshold_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        threshold_report.rows[0].net_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(threshold_report.rows[0], status="block")
    with pytest.raises(ValueError, match="pass_count"):
        replace(threshold_report, pass_count=d("0"))
    with pytest.raises(ValueError, match="average_net_score"):
        replace(threshold_report, average_net_score=d("0.100000"))


def test_owned_module_has_no_live_or_persistence_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_decision_threshold_policy.py"
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
        "connect(",
        "private_key",
        "wallet",
        "place_order",
        "cancel_order",
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
