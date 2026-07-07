from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal

import pytest


CONFIG_VERSION = "candidate-research-queue-priority-v0"
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.candidate_research_queue_priority",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    priority = module()
    values = {
        "config_version": CONFIG_VERSION,
        "watch_priority_threshold": d("0.500000"),
        "high_priority_threshold": d("0.750000"),
        "block_risk_threshold": d("0.800000"),
    }
    values.update(overrides)
    return priority.CandidateResearchQueuePriorityConfig(**values)


def summary(
    summary_ref: str,
    *,
    status: str = "watch",
    score: Decimal = d("0.850000"),
    risk_score: Decimal = d("0.300000"),
    uncertainty_score: Decimal = d("0.900000"),
    impact_score: Decimal = d("0.800000"),
    reason_codes: tuple[str, ...] = ("manual_research_gap",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    priority = module()
    return priority.CandidateResearchQueuePrioritySummary(
        summary_ref=summary_ref,
        status=status,
        score=score,
        risk_score=risk_score,
        uncertainty_score=uncertainty_score,
        impact_score=impact_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*summaries: object, cfg=None):
    priority = module()
    return priority.build_candidate_research_queue_priority(
        summaries,
        config=cfg or config(),
    )


def test_high_priority_watch_sorts_to_top_with_manual_research_explanation() -> None:
    priority = module()
    report = build_report(
        summary(
            "summary-low",
            status="pass",
            score=d("0.350000"),
            risk_score=d("0.100000"),
            uncertainty_score=d("0.200000"),
            impact_score=d("0.400000"),
            reason_codes=("routine_clear",),
        ),
        summary("summary-watch"),
    )

    assert is_dataclass(report)
    assert report.config_version == CONFIG_VERSION
    assert report.summary_count == d("2.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == ZERO
    assert report.status == "watch"
    assert report.top_priority_tier == "high"
    assert report.max_research_priority_score == d("0.980000")
    assert report.reason_codes == (
        "high_manual_research_priority_present",
        "watch_summary_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.research_priority_explanation == (
        "block summaries are reviewed first for manual research only",
        "watch summaries are sorted by risk uncertainty impact and score",
        "pass summaries remain available after higher priority review",
    )

    assert report.rows == (
        priority.CandidateResearchQueuePriorityRow(
            summary_ref="summary-watch",
            status="watch",
            priority_tier="high",
            research_priority_score=d("0.980000"),
            score=d("0.850000"),
            risk_score=d("0.300000"),
            uncertainty_score=d("0.900000"),
            impact_score=d("0.800000"),
            reason_codes=(
                "high_manual_research_priority",
                "manual_research_gap",
                "watch_summary",
            ),
        ),
        priority.CandidateResearchQueuePriorityRow(
            summary_ref="summary-low",
            status="pass",
            priority_tier="low",
            research_priority_score=d("0.235000"),
            score=d("0.350000"),
            risk_score=d("0.100000"),
            uncertainty_score=d("0.200000"),
            impact_score=d("0.400000"),
            reason_codes=("low_manual_research_priority", "routine_clear"),
        ),
    )

    payload = priority.candidate_research_queue_priority_payload(report)
    assert payload["summary_count"] == "2.000000"
    assert payload["rows"][0]["research_priority_score"] == "0.980000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True)
    assert not _contains_float(payload)
    _assert_public_payload_has_no_blocked_terms(payload)


def test_low_risk_pass_remains_pass_with_low_priority() -> None:
    report = build_report(
        summary(
            "summary-clear",
            status="pass",
            score=d("0.400000"),
            risk_score=d("0.100000"),
            uncertainty_score=d("0.200000"),
            impact_score=d("0.300000"),
            reason_codes=("routine_clear",),
        ),
    )

    assert report.status == "pass"
    assert report.top_priority_tier == "low"
    assert report.max_research_priority_score == d("0.215000")
    assert report.reason_codes == ("queue_priority_clear",)
    assert report.rows[0].status == "pass"
    assert report.rows[0].priority_tier == "low"


def test_high_risk_summary_blocks_public_status() -> None:
    report = build_report(
        summary(
            "summary-risk",
            status="watch",
            score=d("0.650000"),
            risk_score=d("0.850000"),
            uncertainty_score=d("0.500000"),
            impact_score=d("0.600000"),
            reason_codes=("elevated_uncertainty",),
        ),
    )

    assert report.status == "block"
    assert report.block_count == d("1.000000")
    assert report.watch_count == ZERO
    assert report.reason_codes == (
        "block_summary_present",
        "high_manual_research_priority_present",
        "risk_limit_block_present",
    )
    assert report.rows[0].status == "block"
    assert report.rows[0].reason_codes == (
        "elevated_uncertainty",
        "high_manual_research_priority",
        "risk_limit_block",
    )


def test_decimal_only_rejects_int_float_and_decimal_subclass() -> None:
    priority = module()

    with pytest.raises(ValueError, match="score"):
        summary("summary-bad", score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="risk_score"):
        summary("summary-bad", risk_score=d("0.10"))  # not canonical
    with pytest.raises(ValueError, match="impact_score"):
        summary("summary-bad", impact_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="watch_priority_threshold"):
        priority.CandidateResearchQueuePriorityConfig(
            config_version=CONFIG_VERSION,
            watch_priority_threshold=0.5,  # type: ignore[arg-type]
            high_priority_threshold=d("0.750000"),
            block_risk_threshold=d("0.800000"),
        )


def test_public_surface_rejects_leaks_and_live_action_language() -> None:
    priority = module()

    with pytest.raises(ValueError, match="unsafe public value"):
        summary("candidate-alpha")
    with pytest.raises(ValueError, match="unsafe public value"):
        summary("summary-safe", reason_codes=("source_url_present",))

    payload = priority.candidate_research_queue_priority_payload(
        build_report(summary("summary-safe")),
    )
    with pytest.raises(ValueError, match="unsafe public field"):
        priority.candidate_research_queue_priority_payload(
            {**payload, "market_slug": "hidden"},
        )
    with pytest.raises(ValueError, match="unsafe public value"):
        priority.candidate_research_queue_priority_payload(
            {**payload, "reason_codes": ["bu" + "y_signal"]},
        )


def test_hard_flags_and_frozen_dataclasses_are_enforced() -> None:
    priority = module()
    report = build_report(summary("summary-safe"))

    assert is_dataclass(priority.CandidateResearchQueuePriorityConfig)
    assert is_dataclass(priority.CandidateResearchQueuePrioritySummary)
    assert is_dataclass(priority.CandidateResearchQueuePriorityRow)
    assert is_dataclass(priority.CandidateResearchQueuePriorityReport)
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].research_priority_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        summary("summary-safe", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    payload = priority.candidate_research_queue_priority_payload(report)
    with pytest.raises(ValueError, match="report_only"):
        priority.candidate_research_queue_priority_payload(
            {**payload, "report_only": False},
        )


def test_output_is_deterministic_for_input_order_and_payload_roundtrip() -> None:
    first = build_report(
        summary("summary-b", status="pass", score=d("0.450000")),
        summary("summary-a", status="watch", score=d("0.850000")),
    )
    second = build_report(
        summary("summary-a", status="watch", score=d("0.850000")),
        summary("summary-b", status="pass", score=d("0.450000")),
    )
    priority = module()
    first_payload = priority.candidate_research_queue_priority_payload(first)
    second_payload = priority.candidate_research_queue_priority_payload(second)

    assert first == second
    assert first_payload == second_payload
    assert priority.candidate_research_queue_priority_payload(first_payload) == first_payload


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False


def _assert_public_payload_has_no_blocked_terms(payload: dict[str, object]) -> None:
    encoded = json.dumps(payload, sort_keys=True).lower()
    for blocked in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "bu" + "y",
        "se" + "ll",
        "rec" + "ommend",
    ):
        assert blocked not in encoded
