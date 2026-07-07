from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_manual_review_checklist import (
    ResearchManualReviewChecklistConfig,
    ResearchManualReviewChecklistCost,
    ResearchManualReviewChecklistEvidence,
    ResearchManualReviewChecklistRule,
    ResearchManualReviewChecklistScore,
    ResearchManualReviewChecklistTeamStatus,
    build_research_manual_review_checklist,
    research_manual_review_checklist_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def safe_inputs() -> dict[str, tuple[object, ...]]:
    return {
        "scores": (
            ResearchManualReviewChecklistScore(
                score_code="score_quality",
                score_value=d("0.910000"),
                pass_floor=d("0.700000"),
                watch_floor=d("0.500000"),
            ),
        ),
        "rules": (
            ResearchManualReviewChecklistRule(
                rule_code="resolution_rule_clarity",
                rule_status="pass",
            ),
        ),
        "evidence": (
            ResearchManualReviewChecklistEvidence(
                evidence_code="evidence_bundle_coverage",
                evidence_status="pass",
                coverage_score=d("0.880000"),
            ),
        ),
        "costs": (
            ResearchManualReviewChecklistCost(
                cost_code="cost_friction",
                cost_ratio=d("0.030000"),
                watch_ceiling=d("0.100000"),
                block_ceiling=d("0.250000"),
            ),
        ),
        "team_statuses": (
            ResearchManualReviewChecklistTeamStatus(
                team_status_code="team_capacity",
                team_status="pass",
                coverage_score=d("0.920000"),
            ),
        ),
    }


def build_report(**overrides: tuple[object, ...]):
    values = safe_inputs()
    values.update(overrides)
    return build_research_manual_review_checklist(
        scores=values["scores"],
        rules=values["rules"],
        evidence=values["evidence"],
        costs=values["costs"],
        team_statuses=values["team_statuses"],
        generated_at=GENERATED_AT,
    )


def test_complete_inputs_build_pass_checklist_payload() -> None:
    report = build_report()

    assert report.checklist_status == "pass"
    assert report.item_count == d("5.000000")
    assert report.pass_count == d("5.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert [row.category for row in report.items] == [
        "score",
        "rule",
        "evidence",
        "cost",
        "team_status",
    ]
    assert all(row.status == "pass" for row in report.items)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = research_manual_review_checklist_payload(report)
    json.dumps(payload, sort_keys=True)
    assert payload["checklist_status"] == "pass"
    assert payload["item_count"] == "5.000000"
    assert payload["items"][0]["metric_value"] == "0.910000"
    assert payload["items"][3]["threshold_value"] == "0.100000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert not _contains_float(payload)
    _assert_no_forbidden_public_fragments(payload)


def test_missing_category_adds_watch_item_without_raw_context() -> None:
    report = build_report(evidence=())

    assert report.checklist_status == "watch"
    assert report.watch_count == d("1.000000")
    missing = [row for row in report.items if row.category == "evidence"]
    assert len(missing) == 1
    assert missing[0].status == "watch"
    assert missing[0].reason_codes == ("missing_required_evidence",)

    payload = research_manual_review_checklist_payload(report)
    assert payload["checklist_status"] == "watch"
    _assert_no_forbidden_public_fragments(payload)


def test_suspicious_redacted_inputs_block_without_leaking_raw_terms() -> None:
    report = build_report(
        evidence=(
            ResearchManualReviewChecklistEvidence(
                evidence_code="source_url_https_polymarket_buy_sell",
                evidence_status="pass",
                coverage_score=d("0.990000"),
                redaction_check_text="https://polymarket.example/market buy sell order",
            ),
        ),
    )

    assert report.checklist_status == "block"
    assert report.block_count == d("1.000000")
    assert report.items[2].category == "evidence"
    assert report.items[2].status == "block"
    assert report.items[2].reason_codes == ("unsafe_public_surface_block",)

    payload = research_manual_review_checklist_payload(report)
    payload_text = json.dumps(payload, sort_keys=True).lower()
    assert "polymarket" not in payload_text
    assert "source_url" not in payload_text
    assert "buy" not in payload_text
    assert "sell" not in payload_text
    assert "order" not in payload_text
    _assert_no_forbidden_public_fragments(payload)


def test_strict_type_validation_rejects_non_decimal_and_bad_status() -> None:
    with pytest.raises(ValueError, match="score_value"):
        ResearchManualReviewChecklistScore(
            score_code="score_quality",
            score_value=1,  # type: ignore[arg-type]
            pass_floor=d("0.700000"),
            watch_floor=d("0.500000"),
        )

    with pytest.raises(ValueError, match="cost_ratio"):
        ResearchManualReviewChecklistCost(
            cost_code="cost_friction",
            cost_ratio=0.03,  # type: ignore[arg-type]
            watch_ceiling=d("0.100000"),
            block_ceiling=d("0.250000"),
        )

    with pytest.raises(ValueError, match="rule_status"):
        ResearchManualReviewChecklistRule(
            rule_code="resolution_rule_clarity",
            rule_status="ready",
        )

    with pytest.raises(ValueError, match="generated_at"):
        build_research_manual_review_checklist(
            scores=(),
            rules=(),
            evidence=(),
            costs=(),
            team_statuses=(),
            generated_at="2026-07-07",  # type: ignore[arg-type]
        )


def test_hard_flags_are_required_and_dataclasses_are_frozen() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchManualReviewChecklistConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        ResearchManualReviewChecklistRule(
            rule_code="resolution_rule_clarity",
            rule_status="pass",
            report_only=False,
        )

    report = build_report()
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(FrozenInstanceError):
        report.items[0].status = "watch"  # type: ignore[misc]


def test_output_is_deterministic_for_unsorted_inputs() -> None:
    forward = build_research_manual_review_checklist(
        scores=(
            ResearchManualReviewChecklistScore(
                score_code="score_b",
                score_value=d("0.910000"),
                pass_floor=d("0.700000"),
                watch_floor=d("0.500000"),
            ),
            ResearchManualReviewChecklistScore(
                score_code="score_a",
                score_value=d("0.910000"),
                pass_floor=d("0.700000"),
                watch_floor=d("0.500000"),
            ),
        ),
        rules=(
            ResearchManualReviewChecklistRule("rule_b", "pass"),
            ResearchManualReviewChecklistRule("rule_a", "pass"),
        ),
        evidence=safe_inputs()["evidence"],
        costs=safe_inputs()["costs"],
        team_statuses=safe_inputs()["team_statuses"],
        generated_at=GENERATED_AT,
    )
    reverse = build_research_manual_review_checklist(
        scores=tuple(reversed(forward.source_scores)),
        rules=tuple(reversed(forward.source_rules)),
        evidence=safe_inputs()["evidence"],
        costs=safe_inputs()["costs"],
        team_statuses=safe_inputs()["team_statuses"],
        generated_at=GENERATED_AT,
    )

    assert forward.items == reverse.items
    assert forward.derived_validation_digest == reverse.derived_validation_digest
    assert research_manual_review_checklist_payload(forward) == (
        research_manual_review_checklist_payload(reverse)
    )


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False


def _assert_no_forbidden_public_fragments(payload: object) -> None:
    payload_text = json.dumps(payload, sort_keys=True).lower()
    for fragment in (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
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
        "buy",
        "sell",
        "recommendation",
    ):
        assert fragment not in payload_text
