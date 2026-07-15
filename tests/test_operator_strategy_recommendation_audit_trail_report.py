from __future__ import annotations

import inspect
import json
from dataclasses import FrozenInstanceError, is_dataclass
from decimal import Decimal

import pytest

import polymarket_alpha_lab.operator_strategy_recommendation_audit_trail_report as audit_module
from polymarket_alpha_lab.operator_strategy_recommendation_audit_trail_report import (
    OperatorStrategyRecommendationAuditTrailReport,
    build_operator_strategy_recommendation_audit_trail_report,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def audit(**overrides: object) -> OperatorStrategyRecommendationAuditTrailReport:
    values = {
        "recommendation_count": d("3"),
        "ranked_candidate_count": d("3"),
        "missing_digest_count": d("0"),
        "manual_review_count": d("0"),
        "approved_candidate_count": d("3"),
    }
    values.update(overrides)
    return build_operator_strategy_recommendation_audit_trail_report(**values)


def test_complete_recommendation_chain_returns_pass_report_only_payload() -> None:
    report = audit()

    assert is_dataclass(report)
    assert report.recommendation_count == d("3")
    assert report.ranked_candidate_count == d("3")
    assert report.missing_digest_count == d("0")
    assert report.manual_review_count == d("0")
    assert report.approved_candidate_count == d("3")
    assert report.audit_trail_status == "pass"
    assert report.reason_codes == ("recommendation_audit_trail_complete",)
    assert report.manual_next_step == "archive_readonly_audit_trail"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload["recommendation_count"] == "3"
    assert payload["ranked_candidate_count"] == "3"
    assert payload["missing_digest_count"] == "0"
    assert payload["manual_review_count"] == "0"
    assert payload["approved_candidate_count"] == "3"
    assert payload["audit_trail_status"] == "pass"
    assert payload["reason_codes"] == ["recommendation_audit_trail_complete"]
    assert payload["manual_next_step"] == "archive_readonly_audit_trail"
    assert payload["payload_digest"] == report.payload_digest
    assert len(report.payload_digest) == 64
    int(report.payload_digest, 16)
    json.dumps(payload, sort_keys=True)
    assert not _contains_runtime_number(payload)


def test_watch_status_when_chain_requires_manual_review_but_no_digest_is_missing() -> None:
    report = audit(
        recommendation_count=d("4"),
        ranked_candidate_count=d("3"),
        missing_digest_count=d("0"),
        manual_review_count=d("1"),
        approved_candidate_count=d("2"),
    )

    assert report.audit_trail_status == "watch"
    assert report.reason_codes == (
        "manual_review_pending",
        "ranked_candidate_gap",
        "approval_gap",
    )
    assert report.manual_next_step == "complete_manual_review_before_operator_approval"


def test_blocked_status_when_digest_missing_or_approval_exceeds_recommendations() -> None:
    missing_digest = audit(
        recommendation_count=d("2"),
        ranked_candidate_count=d("2"),
        missing_digest_count=d("1"),
        manual_review_count=d("0"),
        approved_candidate_count=d("1"),
    )
    invalid_approval = audit(
        recommendation_count=d("1"),
        ranked_candidate_count=d("1"),
        missing_digest_count=d("0"),
        manual_review_count=d("0"),
        approved_candidate_count=d("2"),
    )

    assert missing_digest.audit_trail_status == "blocked"
    assert missing_digest.reason_codes == ("candidate_digest_missing", "approval_gap")
    assert missing_digest.manual_next_step == "rebuild_missing_digest_chain_before_approval"
    assert invalid_approval.audit_trail_status == "blocked"
    assert invalid_approval.reason_codes == ("approved_candidate_count_exceeds_recommendations",)
    assert invalid_approval.manual_next_step == "reconcile_approved_candidate_count"


def test_empty_readonly_audit_trail_is_watch_not_execution_advice() -> None:
    report = audit(
        recommendation_count=d("0"),
        ranked_candidate_count=d("0"),
        missing_digest_count=d("0"),
        manual_review_count=d("0"),
        approved_candidate_count=d("0"),
    )

    assert report.audit_trail_status == "watch"
    assert report.reason_codes == ("recommendation_audit_trail_empty",)
    assert report.manual_next_step == "wait_for_recommendation_chain"


def test_report_is_frozen_decimal_only_and_validates_inputs_and_flags() -> None:
    report = audit()

    with pytest.raises(FrozenInstanceError):
        report.audit_trail_status = "blocked"  # type: ignore[misc]

    for field_name in (
        "recommendation_count",
        "ranked_candidate_count",
        "missing_digest_count",
        "manual_review_count",
        "approved_candidate_count",
    ):
        assert type(getattr(report, field_name)) is Decimal

    with pytest.raises(ValueError, match="recommendation_count must be exactly Decimal"):
        audit(recommendation_count=3)
    with pytest.raises(ValueError, match="ranked_candidate_count must be an integer Decimal"):
        audit(ranked_candidate_count=d("1.5"))
    with pytest.raises(ValueError, match="missing_digest_count must be nonnegative"):
        audit(missing_digest_count=d("-1"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        OperatorStrategyRecommendationAuditTrailReport(
            recommendation_count=d("1"),
            ranked_candidate_count=d("1"),
            missing_digest_count=d("0"),
            manual_review_count=d("0"),
            approved_candidate_count=d("1"),
            audit_trail_status="pass",
            reason_codes=("recommendation_audit_trail_complete",),
            manual_next_step="archive_readonly_audit_trail",
            payload_digest="0" * 64,
            paper_only=False,
        )


def test_payload_digest_is_deterministic_and_rejects_mutation() -> None:
    first = audit()
    second = audit()

    assert first.public_payload == second.public_payload
    assert first.payload_digest == second.payload_digest
    with pytest.raises(TypeError, match="public_payload is immutable"):
        first.public_payload["audit_trail_status"] = "changed"


def test_module_has_no_live_auth_wallet_signature_execution_or_persistence_surface() -> None:
    source = inspect.getsource(audit_module).lower()

    forbidden_terms = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "jsonl",
        "open(",
        ".write",
        "wallet",
        "private_key",
        "api_key",
        "auth",
        "sign",
        "place_order",
        "submit_order",
        "execute",
        "trade",
    )
    assert all(term not in source for term in forbidden_terms)


def _contains_runtime_number(value: object) -> bool:
    if type(value) in {int, float}:
        return True
    if isinstance(value, dict):
        return any(_contains_runtime_number(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_runtime_number(item) for item in value)
    return False
