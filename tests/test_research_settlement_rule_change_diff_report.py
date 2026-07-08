from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_settlement_rule_change_diff_report as api
from polymarket_alpha_lab.research_settlement_rule_change_diff_report import (
    ResearchSettlementRuleChangeDiffReport,
    SettlementRuleChangeDiffConfig,
    SettlementRuleManualReview,
    SettlementRuleSummary,
    SettlementRuleSourceVerification,
    build_research_settlement_rule_change_diff_report,
)


NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def d(value: str) -> Decimal:
    return Decimal(value)


def old_rule_summary(**overrides: object) -> SettlementRuleSummary:
    values = {
        "event_id": "event_alpha",
        "rule_digest": DIGEST_A,
        "criteria_count": d("4.000000"),
        "ambiguous_criteria_count": d("1.000000"),
        "dispute_window_hours": d("24.000000"),
        "settlement_window_hours": d("48.000000"),
        "manual_resolution_allowed": False,
        "evidence_threshold_score": d("0.800000"),
        "settlement_risk_score": d("0.220000"),
    }
    values.update(overrides)
    return SettlementRuleSummary(**values)


def new_rule_summary(**overrides: object) -> SettlementRuleSummary:
    values = {
        "event_id": "event_alpha",
        "rule_digest": DIGEST_B,
        "criteria_count": d("5.000000"),
        "ambiguous_criteria_count": d("0.000000"),
        "dispute_window_hours": d("24.000000"),
        "settlement_window_hours": d("36.000000"),
        "manual_resolution_allowed": False,
        "evidence_threshold_score": d("0.850000"),
        "settlement_risk_score": d("0.180000"),
    }
    values.update(overrides)
    return SettlementRuleSummary(**values)


def source_verification(**overrides: object) -> SettlementRuleSourceVerification:
    values = {
        "verification_digest": DIGEST_C,
        "verified_source_count": d("3.000000"),
        "official_source_count": d("1.000000"),
        "independent_source_family_count": d("2.000000"),
        "conflicting_source_count": d("0.000000"),
        "source_confidence_score": d("0.920000"),
        "latest_source_age_hours": d("1.000000"),
    }
    values.update(overrides)
    return SettlementRuleSourceVerification(**values)


def manual_review(**overrides: object) -> SettlementRuleManualReview:
    values = {
        "review_digest": DIGEST_D,
        "review_status": "not_required",
        "required_issue_count": d("0.000000"),
        "completed_issue_count": d("0.000000"),
    }
    values.update(overrides)
    return SettlementRuleManualReview(**values)


def diff_report(
    *,
    old_summary: SettlementRuleSummary | None = None,
    new_summary: SettlementRuleSummary | None = None,
    verification: SettlementRuleSourceVerification | None = None,
    review: SettlementRuleManualReview | None = None,
    config: SettlementRuleChangeDiffConfig | None = None,
) -> ResearchSettlementRuleChangeDiffReport:
    return build_research_settlement_rule_change_diff_report(
        old_summary or old_rule_summary(),
        new_summary or new_rule_summary(),
        source_verification=verification or source_verification(),
        manual_review=review or manual_review(),
        generated_at=NOW,
        config=config,
    )


def test_pass_report_covers_rule_summaries_risk_sources_and_review() -> None:
    report = diff_report()

    assert report.verdict == "pass"
    assert report.old_rule_summary.rule_digest == DIGEST_A
    assert report.new_rule_summary.rule_digest == DIGEST_B
    assert report.risk_change.old_risk_score == d("0.220000")
    assert report.risk_change.new_risk_score == d("0.180000")
    assert report.risk_change.risk_delta == d("-0.040000")
    assert report.risk_change.risk_direction == "decreased"
    assert report.risk_change.risk_verdict == "pass"
    assert report.source_verification.verification_verdict == "pass"
    assert report.manual_review.review_verdict == "pass"
    assert report.manual_review.unresolved_issue_count == d("0.000000")
    assert "settlement_rule_change_diff_pass" in report.reason_codes
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_watch_report_flags_material_but_non_blocking_risk_increase() -> None:
    report = diff_report(
        new_summary=new_rule_summary(settlement_risk_score=d("0.280000")),
    )

    assert report.verdict == "watch"
    assert report.risk_change.risk_delta == d("0.060000")
    assert report.risk_change.risk_direction == "increased"
    assert report.risk_change.risk_verdict == "watch"
    assert "risk_increase_watch" in report.reason_codes
    assert report.source_verification.verification_verdict == "pass"
    assert report.manual_review.review_verdict == "pass"


def test_block_report_flags_source_failures_large_risk_and_unresolved_review() -> None:
    report = diff_report(
        new_summary=new_rule_summary(
            manual_resolution_allowed=True,
            settlement_risk_score=d("0.520000"),
        ),
        verification=source_verification(
            verified_source_count=d("1.000000"),
            official_source_count=d("0.000000"),
            independent_source_family_count=d("1.000000"),
            conflicting_source_count=d("1.000000"),
            source_confidence_score=d("0.400000"),
        ),
        review=manual_review(
            review_status="pending",
            required_issue_count=d("2.000000"),
            completed_issue_count=d("0.000000"),
        ),
    )

    assert report.verdict == "block"
    assert report.risk_change.risk_delta == d("0.300000")
    assert report.risk_change.risk_verdict == "block"
    assert report.source_verification.verification_verdict == "block"
    assert report.manual_review.review_verdict == "block"
    assert report.manual_review.unresolved_issue_count == d("2.000000")
    assert "risk_increase_block" in report.reason_codes
    assert "source_verification_block" in report.reason_codes
    assert "manual_review_unresolved_block" in report.reason_codes


def test_payload_serializes_decimals_and_excludes_raw_sensitive_public_surfaces() -> None:
    report = diff_report()

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["old_rule_summary"]["settlement_risk_score"] == "0.220000"
    assert payload["new_rule_summary"]["settlement_risk_score"] == "0.180000"
    assert payload["risk_change"]["risk_delta"] == "-0.040000"
    assert payload["source_verification"]["verified_source_count"] == "3.000000"
    assert payload["manual_review"]["unresolved_issue_count"] == "0.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_forbidden_public_payload_terms(payload)


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = diff_report()

    with pytest.raises(FrozenInstanceError):
        report.verdict = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(SettlementRuleChangeDiffConfig):
            pass

    with pytest.raises(TypeError):

        class BadSummary(SettlementRuleSummary):
            pass


def test_strict_decimal_types_and_hard_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="settlement_risk_score must be a Decimal"):
        new_rule_summary(settlement_risk_score=0.18)

    with pytest.raises(ValueError, match="source_confidence_score must be a Decimal"):
        source_verification(source_confidence_score=0.92)

    with pytest.raises(ValueError, match="paper_only"):
        SettlementRuleChangeDiffConfig(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        new_rule_summary(readonly=False)

    report = diff_report()
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)


def test_builder_rejects_wrong_types_and_mismatched_event_ids() -> None:
    with pytest.raises(ValueError, match="old_rule_summary"):
        build_research_settlement_rule_change_diff_report(
            object(),
            new_rule_summary(),
            source_verification=source_verification(),
            manual_review=manual_review(),
            generated_at=NOW,
        )

    report = diff_report(new_summary=new_rule_summary(event_id="event_beta"))
    assert report.verdict == "block"
    assert "event_id_mismatch_block" in report.reason_codes


def test_unsafe_public_inputs_and_api_surfaces_are_rejected() -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        old_rule_summary(event_id="event_raw_question")

    with pytest.raises(ValueError, match="unsafe public"):
        old_rule_summary(event_id="event_slug")

    with pytest.raises(ValueError, match="unsafe public"):
        old_rule_summary(event_id="event_url")

    forbidden_terms = (
        "raw",
        "question",
        "slug",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "auth",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_terms)

    for cls in (
        SettlementRuleChangeDiffConfig,
        SettlementRuleSummary,
        SettlementRuleSourceVerification,
        SettlementRuleManualReview,
        api.SettlementRuleRiskChange,
        api.SettlementRuleSourceVerificationResult,
        api.SettlementRuleManualReviewResult,
        ResearchSettlementRuleChangeDiffReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_terms)

    for forbidden_module in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_module)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))


def _assert_no_forbidden_public_payload_terms(value: object) -> None:
    forbidden_terms = (
        "raw",
        "question",
        "slug",
        "url",
        "text",
        "dsn",
        "table",
        "token",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(term in lowered for term in forbidden_terms)
            _assert_no_forbidden_public_payload_terms(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_forbidden_public_payload_terms(item)
    if isinstance(value, str):
        lowered = value.lower()
        assert not any(term in lowered for term in forbidden_terms)
