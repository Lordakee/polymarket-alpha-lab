from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 12, 9, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.probability_event_resolution_rule_evidence_gap_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence(
    event_id: str = "event-clear",
    *,
    resolution_rule_text_present: bool = True,
    official_resolution_source_present: bool = True,
    rule_hash_present: bool = True,
    rule_ambiguity_count: str = "0",
    source_refresh_age_hours: str = "1.000000",
):
    report = api()
    return report.ProbabilityEventResolutionRuleEvidenceGapInput(
        event_id=event_id,
        resolution_rule_text_present=resolution_rule_text_present,
        official_resolution_source_present=official_resolution_source_present,
        rule_hash_present=rule_hash_present,
        rule_ambiguity_count=d(rule_ambiguity_count),
        source_refresh_age_hours=d(source_refresh_age_hours),
    )


def gap_report(*items, generated_at: datetime = GENERATED_AT):
    report = api()
    return report.build_probability_event_resolution_rule_evidence_gap_report(
        items,
        config=report.ProbabilityEventResolutionRuleEvidenceGapConfig(),
        generated_at=generated_at,
    )


def test_clear_resolution_rule_evidence_passes_readonly_report() -> None:
    readiness_report = gap_report(
        evidence("event-z", source_refresh_age_hours="2.000000"),
        evidence("event-a", source_refresh_age_hours="0.500000"),
    )

    assert is_dataclass(readiness_report)
    assert readiness_report.generated_at == GENERATED_AT
    assert readiness_report.config_version == (
        "probability-event-resolution-rule-evidence-gap-report-v0"
    )
    assert readiness_report.event_count == d("2")
    assert readiness_report.pass_event_count == d("2")
    assert readiness_report.watch_event_count == d("0")
    assert readiness_report.blocked_event_count == d("0")
    assert readiness_report.readiness_status == "pass"
    assert readiness_report.reason_codes == ("resolution_rule_evidence_ready",)
    assert readiness_report.manual_next_step == "no_manual_resolution_rule_action_required"
    assert readiness_report.paper_only is True
    assert readiness_report.report_only is True
    assert readiness_report.readonly is True

    assert tuple(row.event_id for row in readiness_report.rows) == (
        "event-a",
        "event-z",
    )
    assert all(row.readiness_status == "pass" for row in readiness_report.rows)
    assert readiness_report.rows[0].reason_codes == (
        "resolution_rule_text_present",
        "official_resolution_source_present",
        "rule_hash_present",
        "resolution_rule_unambiguous",
        "resolution_source_fresh",
    )
    assert readiness_report.rows[0].manual_next_step == (
        "no_manual_resolution_rule_action_required"
    )


def test_unclear_resolution_rule_or_missing_evidence_cannot_pass() -> None:
    readiness_report = gap_report(
        evidence(
            "event-ambiguous",
            rule_ambiguity_count="1",
            source_refresh_age_hours="1.000000",
        ),
        evidence(
            "event-missing-source",
            official_resolution_source_present=False,
            source_refresh_age_hours="1.000000",
        ),
        evidence(
            "event-stale",
            source_refresh_age_hours="49.000000",
        ),
    )

    assert readiness_report.readiness_status == "blocked"
    assert readiness_report.pass_event_count == d("0")
    assert readiness_report.watch_event_count == d("1")
    assert readiness_report.blocked_event_count == d("2")
    assert readiness_report.reason_codes == (
        "resolution_rule_ambiguity_present",
        "official_resolution_source_missing",
        "resolution_source_refresh_stale",
        "manual_resolution_rule_review_required",
    )
    assert readiness_report.manual_next_step == (
        "escalate_unclear_resolution_rule_before_probability_use"
    )

    ambiguous = readiness_report.rows[0]
    assert ambiguous.event_id == "event-ambiguous"
    assert ambiguous.readiness_status == "blocked"
    assert ambiguous.reason_codes == (
        "resolution_rule_text_present",
        "official_resolution_source_present",
        "rule_hash_present",
        "resolution_rule_ambiguity_present",
        "resolution_source_fresh",
    )
    assert ambiguous.manual_next_step == (
        "escalate_unclear_resolution_rule_before_probability_use"
    )

    missing_source = readiness_report.rows[1]
    assert missing_source.readiness_status == "blocked"
    assert "official_resolution_source_missing" in missing_source.reason_codes
    assert missing_source.manual_next_step == (
        "attach_official_resolution_source_before_probability_use"
    )

    stale = readiness_report.rows[2]
    assert stale.readiness_status == "watch"
    assert stale.reason_codes == (
        "resolution_rule_text_present",
        "official_resolution_source_present",
        "rule_hash_present",
        "resolution_rule_unambiguous",
        "resolution_source_refresh_stale",
    )
    assert stale.manual_next_step == "refresh_official_resolution_source_evidence"


def test_missing_rule_text_and_hash_are_blocking_manual_next_steps() -> None:
    readiness_report = gap_report(
        evidence(
            "event-missing-rule",
            resolution_rule_text_present=False,
            rule_hash_present=False,
        ),
    )

    assert readiness_report.readiness_status == "blocked"
    row = readiness_report.rows[0]
    assert row.readiness_status == "blocked"
    assert row.reason_codes == (
        "resolution_rule_text_missing",
        "official_resolution_source_present",
        "rule_hash_missing",
        "resolution_rule_unambiguous",
        "resolution_source_fresh",
    )
    assert row.manual_next_step == (
        "attach_resolution_rule_text_before_probability_use"
    )


def test_payload_is_decimal_string_readonly_and_tamper_evident() -> None:
    report = api()
    readiness_report = gap_report(
        evidence(
            "event-json",
            rule_ambiguity_count="2",
            source_refresh_age_hours="72.500000",
        ),
    )

    payload = report.probability_event_resolution_rule_evidence_gap_report_payload(
        readiness_report,
    )

    assert payload["event_count"] == "1"
    assert payload["rows"][0]["rule_ambiguity_count"] == "2"
    assert payload["rows"][0]["source_refresh_age_hours"] == "72.500000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64
    assert not any(type(value) in (float, int) for value in _walk(payload))

    assert (
        report.probability_event_resolution_rule_evidence_gap_report_payload(payload)
        == payload
    )

    tampered = dict(payload)
    tampered["event_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report.probability_event_resolution_rule_evidence_gap_report_payload(tampered)


def test_validation_rejects_non_decimal_counts_flags_and_unsafe_surfaces() -> None:
    report = api()

    with pytest.raises(ValueError, match="rule_ambiguity_count must be a Decimal"):
        report.ProbabilityEventResolutionRuleEvidenceGapInput(
            event_id="event-bad-decimal",
            resolution_rule_text_present=True,
            official_resolution_source_present=True,
            rule_hash_present=True,
            rule_ambiguity_count=1,
            source_refresh_age_hours=d("1.000000"),
        )

    with pytest.raises(ValueError, match="source_refresh_age_hours must be finite"):
        evidence(source_refresh_age_hours="NaN")

    with pytest.raises(ValueError, match="rule_ambiguity_count must be integral"):
        evidence(rule_ambiguity_count="0.5")

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(evidence(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        report.ProbabilityEventResolutionRuleEvidenceGapConfig(readonly=False)

    with pytest.raises(ValueError, match="duplicate event_id"):
        gap_report(evidence("event-dupe"), evidence("event-dupe"))

    for unsafe_value in (
        "live-mode",
        "auth-token",
        "wallet-check",
        "order-review",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            evidence(event_id=unsafe_value)


def test_public_dataclasses_are_frozen_and_module_has_no_side_effect_surface() -> None:
    item = evidence("event-frozen")
    with pytest.raises(FrozenInstanceError):
        item.event_id = "event-other"  # type: ignore[misc]

    source = Path(
        "src/polymarket_alpha_lab/probability_event_resolution_rule_evidence_gap_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "authentication",
        "private_key",
        "wallet",
        "account",
        "order",
        "network",
        "request",
        "http",
        "urllib",
        "open(",
        "read(",
        "write(",
        "database",
        "persist",
        "live",
        "buy",
        "sell",
    ):
        assert forbidden not in lowered


def _walk(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk(item)
        return
    if isinstance(value, list):
        for item in value:
            yield from _walk(item)
        return
    yield value
