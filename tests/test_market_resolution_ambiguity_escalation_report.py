from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_resolution_ambiguity_escalation_report import (
    MarketResolutionAmbiguityEscalationInput,
    build_market_resolution_ambiguity_escalation_report,
    market_resolution_ambiguity_escalation_payload,
    market_resolution_ambiguity_escalation_payload_digest,
)


def test_builds_clear_report_payload_and_digest() -> None:
    report = build_market_resolution_ambiguity_escalation_report(
        MarketResolutionAmbiguityEscalationInput(
            resolution_rule_clarity=Decimal("0.95"),
            oracle_dependency_count=Decimal("0"),
            ambiguous_terms_count=Decimal("0"),
            source_conflict_count=Decimal("0"),
            time_to_resolution_hours=Decimal("72"),
        ),
    )

    assert report.ambiguity_status == "clear"
    assert report.reason_codes == ("resolution_rules_clear",)
    assert report.manual_next_step == "continue_readonly_monitoring"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    with pytest.raises(FrozenInstanceError):
        report.ambiguity_status = "escalate"  # type: ignore[misc]

    payload = market_resolution_ambiguity_escalation_payload(report)

    assert payload["ambiguity_status"] == "clear"
    assert payload["resolution_rule_clarity"] == "0.950000"
    assert payload["oracle_dependency_count"] == "0.000000"
    assert payload["time_to_resolution_hours"] == "72.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == report.payload_digest
    assert "live" not in str(payload).lower()
    assert "auth" not in str(payload).lower()
    assert "wallet" not in str(payload).lower()
    assert "order" not in str(payload).lower()
    assert "key" not in str(payload).lower()
    assert "sign" not in str(payload).lower()
    assert "exec" not in str(payload).lower()
    assert report.public_payload == payload
    assert market_resolution_ambiguity_escalation_payload_digest(report) == (
        report.payload_digest
    )


def test_escalates_when_rules_are_unclear_and_conflicting_near_resolution() -> None:
    report = build_market_resolution_ambiguity_escalation_report(
        MarketResolutionAmbiguityEscalationInput(
            resolution_rule_clarity=Decimal("0.35"),
            oracle_dependency_count=Decimal("2"),
            ambiguous_terms_count=Decimal("3"),
            source_conflict_count=Decimal("1"),
            time_to_resolution_hours=Decimal("6"),
        ),
    )

    assert report.ambiguity_status == "escalate"
    assert report.reason_codes == (
        "resolution_rule_clarity_low",
        "oracle_dependency_present",
        "ambiguous_resolution_terms_present",
        "conflicting_resolution_sources_present",
        "resolution_window_imminent",
    )
    assert report.manual_next_step == "escalate_to_manual_resolution_review"

    payload = report.public_payload
    assert payload["ambiguity_status"] == "escalate"
    assert payload["reason_codes"] == [
        "resolution_rule_clarity_low",
        "oracle_dependency_present",
        "ambiguous_resolution_terms_present",
        "conflicting_resolution_sources_present",
        "resolution_window_imminent",
    ]
    assert payload["manual_next_step"] == "escalate_to_manual_resolution_review"


def test_marks_manual_review_for_medium_clarity_without_imminent_deadline() -> None:
    report = build_market_resolution_ambiguity_escalation_report(
        MarketResolutionAmbiguityEscalationInput(
            resolution_rule_clarity=Decimal("0.62"),
            oracle_dependency_count=Decimal("1"),
            ambiguous_terms_count=Decimal("1"),
            source_conflict_count=Decimal("0"),
            time_to_resolution_hours=Decimal("48"),
        ),
    )

    assert report.ambiguity_status == "manual_review"
    assert report.reason_codes == (
        "resolution_rule_clarity_partial",
        "oracle_dependency_present",
        "ambiguous_resolution_terms_present",
    )
    assert report.manual_next_step == "queue_manual_resolution_review"


def test_rejects_non_decimal_values_and_disabled_readonly_flags() -> None:
    with pytest.raises(ValueError, match="resolution_rule_clarity must be a Decimal"):
        MarketResolutionAmbiguityEscalationInput(
            resolution_rule_clarity=0.95,  # type: ignore[arg-type]
            oracle_dependency_count=Decimal("0"),
            ambiguous_terms_count=Decimal("0"),
            source_conflict_count=Decimal("0"),
            time_to_resolution_hours=Decimal("72"),
        )

    with pytest.raises(ValueError, match="readonly must be True"):
        MarketResolutionAmbiguityEscalationInput(
            resolution_rule_clarity=Decimal("0.95"),
            oracle_dependency_count=Decimal("0"),
            ambiguous_terms_count=Decimal("0"),
            source_conflict_count=Decimal("0"),
            time_to_resolution_hours=Decimal("72"),
            readonly=False,
        )
