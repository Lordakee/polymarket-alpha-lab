from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_risk_evidence_gap_escalation_report as api
from polymarket_alpha_lab.research_risk_evidence_gap_escalation_report import (
    ResearchRiskEvidenceGapEscalationConfig,
    ResearchRiskEvidenceGapEscalationObservation,
    build_research_risk_evidence_gap_escalation_report,
    research_risk_evidence_gap_escalation_report_payload,
)


NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)


def _observation(
    *,
    research_slug: str = "research-alpha",
    source_class: str = "official",
    observed_at: datetime = NOW,
    contradiction_open: bool = False,
) -> ResearchRiskEvidenceGapEscalationObservation:
    return ResearchRiskEvidenceGapEscalationObservation(
        research_slug=research_slug,
        source_class=source_class,
        observed_at=observed_at,
        contradiction_open=contradiction_open,
    )


def test_aggregate_evidence_gaps_escalate_manual_review_urgency() -> None:
    config = ResearchRiskEvidenceGapEscalationConfig(
        required_source_classes=("official", "primary", "context"),
        stale_observation_seconds=Decimal("3600.000000"),
        watch_manual_review_urgency=Decimal("0.333333"),
        block_manual_review_urgency=Decimal("0.666667"),
    )

    report = build_research_risk_evidence_gap_escalation_report(
        (
            _observation(source_class="official"),
            _observation(
                source_class="primary",
                observed_at=NOW - timedelta(seconds=7200),
                contradiction_open=True,
            ),
        ),
        config=config,
        generated_at=NOW,
    )

    row = report.rows[0]
    assert report.status == "block"
    assert report.reason_codes == (
        "missing_source_class_gap",
        "stale_research_observation",
        "unresolved_evidence_contradiction",
        "manual_review_urgency_block",
    )
    assert report.research_item_count == Decimal("1.000000")
    assert report.missing_source_class_count == Decimal("1.000000")
    assert report.stale_observation_count == Decimal("1.000000")
    assert report.unresolved_contradiction_count == Decimal("1.000000")
    assert report.manual_review_urgency_score == Decimal("1.000000")

    assert row.research_slug == "research-alpha"
    assert row.observed_source_class_count == Decimal("2.000000")
    assert row.required_source_class_count == Decimal("3.000000")
    assert row.missing_source_class_count == Decimal("1.000000")
    assert row.missing_source_classes == ("context",)
    assert row.stale_observation_count == Decimal("1.000000")
    assert row.unresolved_contradiction_count == Decimal("1.000000")
    assert row.manual_review_urgency_score == Decimal("1.000000")
    assert row.status == "block"
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_complete_fresh_resolved_evidence_passes() -> None:
    report = build_research_risk_evidence_gap_escalation_report(
        (
            _observation(source_class="official"),
            _observation(source_class="primary"),
            _observation(source_class="context"),
        ),
        config=ResearchRiskEvidenceGapEscalationConfig(
            required_source_classes=("official", "primary", "context"),
        ),
        generated_at=NOW,
    )

    assert report.status == "pass"
    assert report.reason_codes == ("evidence_gap_escalation_pass",)
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert report.manual_review_urgency_score == Decimal("0.000000")
    assert report.rows[0].status == "pass"
    assert report.rows[0].reason_codes == ("evidence_gap_escalation_pass",)


def test_payload_is_deterministic_json_ready_and_tamper_evident() -> None:
    config = ResearchRiskEvidenceGapEscalationConfig(
        required_source_classes=("official", "primary", "context"),
        stale_observation_seconds=Decimal("3600.000000"),
    )
    observations = (
        _observation(source_class="primary", observed_at=NOW - timedelta(seconds=7200)),
        _observation(source_class="official"),
    )
    report = build_research_risk_evidence_gap_escalation_report(
        observations,
        config=config,
        generated_at=NOW,
    )
    reversed_report = build_research_risk_evidence_gap_escalation_report(
        tuple(reversed(observations)),
        config=config,
        generated_at=NOW,
    )

    payload = research_risk_evidence_gap_escalation_report_payload(report)
    reversed_payload = research_risk_evidence_gap_escalation_report_payload(
        reversed_report,
    )
    json.dumps(payload, sort_keys=True)
    assert payload == reversed_payload
    assert payload["counts"]["missing_source_class_count"] == "1.000000"
    assert payload["counts"]["stale_observation_count"] == "1.000000"
    assert payload["rows"][0]["manual_review_urgency_score"] == "0.666667"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_decimal_objects(payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_risk_evidence_gap_escalation_report_payload(tampered_payload)


def test_report_only_guardrails_reject_mutation_unsafe_surfaces_and_non_decimals() -> None:
    report = build_research_risk_evidence_gap_escalation_report(
        (_observation(source_class="official"),),
        config=ResearchRiskEvidenceGapEscalationConfig(
            required_source_classes=("official",),
        ),
        generated_at=NOW,
    )

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchRiskEvidenceGapEscalationConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ResearchRiskEvidenceGapEscalationConfig(paper_only=False)

    with pytest.raises(ValueError, match="Decimal"):
        ResearchRiskEvidenceGapEscalationConfig(
            stale_observation_seconds=3600,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="unsafe"):
        _observation(research_slug="raw-id-research")

    with pytest.raises(ValueError, match="future"):
        build_research_risk_evidence_gap_escalation_report(
            (_observation(observed_at=NOW + timedelta(seconds=1)),),
            config=ResearchRiskEvidenceGapEscalationConfig(
                required_source_classes=("official",),
            ),
            generated_at=NOW,
        )


def test_public_surface_excludes_execution_and_source_text_terms() -> None:
    unsafe_terms = (
        "recommendation",
        "sizing",
        "buy",
        "sell",
        "raw_id",
        "rawid",
        "url",
        "source_text",
        "db",
        "network",
        "wallet",
        "order",
        "live",
        "trading",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ResearchRiskEvidenceGapEscalationConfig,
        ResearchRiskEvidenceGapEscalationObservation,
        api.ResearchRiskEvidenceGapEscalationRow,
        api.ResearchRiskEvidenceGapEscalationReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    for forbidden_name in (
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
        assert not hasattr(api, forbidden_name)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)
