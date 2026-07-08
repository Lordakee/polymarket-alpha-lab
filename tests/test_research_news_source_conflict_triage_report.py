from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_news_source_conflict_triage_report import (
    ResearchNewsSourceConflictTriageConfig,
    ResearchNewsSourceConflictTriageInput,
    ResearchNewsSourceConflictTriageReport,
    ResearchNewsSourceConflictTriageRow,
    build_research_news_source_conflict_triage_report,
    research_news_source_conflict_triage_report_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchNewsSourceConflictTriageConfig:
    values = {
        "config_version": "research-news-source-conflict-triage-report-v0",
        "min_independent_source_family_count": d("3.000000"),
        "fresh_publication_age_seconds": d("1800.000000"),
        "stale_publication_age_seconds": d("86400.000000"),
        "publication_timing_attention_score": d("0.600000"),
        "high_counter_evidence_strength": d("0.750000"),
        "high_impact_domain_score": d("0.750000"),
        "high_impact_severity": d("0.700000"),
        "blocked_triage_risk_score": d("0.700000"),
        "watch_triage_risk_score": d("0.300000"),
        "source_independence_gap_weight": d("0.200000"),
        "publication_timing_weight": d("0.150000"),
        "counter_evidence_weight": d("0.250000"),
        "impact_domain_weight": d("0.150000"),
        "impact_severity_weight": d("0.150000"),
        "escalation_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchNewsSourceConflictTriageConfig(**values)


def conflict(
    conflict_id: str,
    *,
    supporting_source_family_count: Decimal = d("2.000000"),
    opposing_source_family_count: Decimal = d("2.000000"),
    shared_source_family_count: Decimal = d("0.000000"),
    newest_publication_age_seconds: Decimal = d("7200.000000"),
    oldest_publication_age_seconds: Decimal = d("9000.000000"),
    counter_evidence_strength: Decimal = d("0.050000"),
    impact_domain: str = "metadata",
    impact_severity: Decimal = d("0.100000"),
    operator_escalation_requested: bool = False,
) -> ResearchNewsSourceConflictTriageInput:
    return ResearchNewsSourceConflictTriageInput(
        conflict_id=conflict_id,
        supporting_source_family_count=supporting_source_family_count,
        opposing_source_family_count=opposing_source_family_count,
        shared_source_family_count=shared_source_family_count,
        newest_publication_age_seconds=newest_publication_age_seconds,
        oldest_publication_age_seconds=oldest_publication_age_seconds,
        counter_evidence_strength=counter_evidence_strength,
        impact_domain=impact_domain,
        impact_severity=impact_severity,
        operator_escalation_requested=operator_escalation_requested,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchNewsSourceConflictTriageConfig | None = None,
) -> ResearchNewsSourceConflictTriageReport:
    return build_research_news_source_conflict_triage_report(
        rows,
        config=cfg or config(),
    )


def test_empty_input_returns_blocked_report_only_triage() -> None:
    triage_report = report(())

    assert type(triage_report) is ResearchNewsSourceConflictTriageReport
    assert triage_report.config_version == "research-news-source-conflict-triage-report-v0"
    assert triage_report.report_status == "blocked"
    assert triage_report.recommended_escalation == "immediate"
    assert triage_report.input_count == d("0.000000")
    assert triage_report.blocked_count == d("0.000000")
    assert triage_report.watch_count == d("0.000000")
    assert triage_report.pass_count == d("0.000000")
    assert triage_report.highest_triage_risk_score == d("0.000000")
    assert triage_report.rows == ()
    assert triage_report.reason_codes == ("news_conflict_triage_no_inputs",)
    assert triage_report.paper_only is True
    assert triage_report.report_only is True
    assert triage_report.readonly is True


def test_low_risk_independent_minor_conflict_passes_with_decimal_scores() -> None:
    triage_report = report((conflict("case-pass"),))

    assert triage_report.report_status == "pass"
    assert triage_report.pass_count == d("1.000000")
    assert triage_report.watch_count == d("0.000000")
    assert triage_report.blocked_count == d("0.000000")
    assert triage_report.highest_triage_risk_score == d("0.094606")
    assert triage_report.reason_codes == (
        "news_conflict_triage_status_pass",
        "news_conflict_counter_evidence_present",
    )

    row = triage_report.rows[0]
    assert type(row) is ResearchNewsSourceConflictTriageRow
    assert row.conflict_id == "case-pass"
    assert row.priority_rank == d("1.000000")
    assert row.source_independence_score == d("1.000000")
    assert row.source_independence_gap_score == d("0.000000")
    assert row.publication_timing_score == d("0.347370")
    assert row.counter_evidence_strength == d("0.050000")
    assert row.impact_domain == "metadata"
    assert row.impact_domain_score == d("0.100000")
    assert row.impact_severity == d("0.100000")
    assert row.escalation_need_score == d("0.000000")
    assert row.triage_risk_score == d("0.094606")
    assert row.triage_status == "pass"
    assert row.recommended_escalation == "routine"
    assert row.publication_span_seconds == d("1800.000000")
    assert row.reason_codes == (
        "news_conflict_triage_status_pass",
        "news_conflict_counter_evidence_present",
    )


def test_mixed_conflicts_rank_block_watch_and_pass_rows_deterministically() -> None:
    triage_report = report(
        (
            conflict("case-pass"),
            conflict(
                "case-watch",
                supporting_source_family_count=d("1.000000"),
                opposing_source_family_count=d("1.000000"),
                shared_source_family_count=d("1.000000"),
                newest_publication_age_seconds=d("1200.000000"),
                oldest_publication_age_seconds=d("7200.000000"),
                counter_evidence_strength=d("0.450000"),
                impact_domain="resolution",
                impact_severity=d("0.400000"),
            ),
            conflict(
                "case-block",
                supporting_source_family_count=d("1.000000"),
                opposing_source_family_count=d("1.000000"),
                shared_source_family_count=d("1.000000"),
                newest_publication_age_seconds=d("300.000000"),
                oldest_publication_age_seconds=d("100000.000000"),
                counter_evidence_strength=d("0.900000"),
                impact_domain="settlement",
                impact_severity=d("0.900000"),
            ),
        ),
    )

    assert triage_report.report_status == "blocked"
    assert triage_report.recommended_escalation == "immediate"
    assert triage_report.input_count == d("3.000000")
    assert triage_report.blocked_count == d("1.000000")
    assert triage_report.watch_count == d("1.000000")
    assert triage_report.pass_count == d("1.000000")
    assert triage_report.low_source_independence_count == d("2.000000")
    assert triage_report.publication_time_attention_count == d("1.000000")
    assert triage_report.high_counter_evidence_count == d("1.000000")
    assert triage_report.high_impact_domain_count == d("2.000000")
    assert triage_report.high_impact_severity_count == d("1.000000")
    assert triage_report.escalation_needed_count == d("1.000000")
    assert triage_report.highest_triage_risk_score == d("0.893333")
    assert tuple(row.conflict_id for row in triage_report.rows) == (
        "case-block",
        "case-watch",
        "case-pass",
    )
    assert tuple(row.triage_status for row in triage_report.rows) == (
        "blocked",
        "watch",
        "pass",
    )
    assert tuple(row.priority_rank for row in triage_report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert triage_report.rows[0].reason_codes == (
        "news_conflict_triage_status_blocked",
        "news_conflict_source_independence_low",
        "news_conflict_publication_time_attention",
        "news_conflict_counter_evidence_high",
        "news_conflict_impact_domain_high",
        "news_conflict_impact_severity_high",
        "news_conflict_escalation_needed",
    )
    assert triage_report.rows[1].triage_risk_score == d("0.497497")
    assert triage_report.reason_codes == (
        "news_conflict_triage_status_blocked",
        "news_conflict_source_independence_low",
        "news_conflict_publication_time_attention",
        "news_conflict_counter_evidence_present",
        "news_conflict_counter_evidence_high",
        "news_conflict_impact_domain_high",
        "news_conflict_impact_severity_high",
        "news_conflict_escalation_needed",
    )


def test_public_payload_uses_decimal_strings_and_excludes_sensitive_fields() -> None:
    triage_report = report(
        (
            conflict("case-pass"),
            conflict(
                "case-block",
                supporting_source_family_count=d("1.000000"),
                opposing_source_family_count=d("1.000000"),
                shared_source_family_count=d("1.000000"),
                newest_publication_age_seconds=d("300.000000"),
                oldest_publication_age_seconds=d("100000.000000"),
                counter_evidence_strength=d("0.900000"),
                impact_domain="settlement",
                impact_severity=d("0.900000"),
            ),
        ),
    )

    payload = research_news_source_conflict_triage_report_payload(triage_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["input_count"] == "2.000000"
    assert payload["rows"][0]["triage_risk_score"] == "0.893333"
    assert payload["rows"][0]["derived_validation_digest"] == (
        triage_report.rows[0].derived_validation_digest
    )
    assert not any(type(value) in (int, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    assert _unsafe_payload_matches(payload) == ()


def test_validation_rejects_bad_types_unsafe_identifiers_bad_ordering_and_flags() -> None:
    with pytest.raises(ValueError, match="triage risk score weights"):
        config(counter_evidence_weight=d("0.200000"))
    with pytest.raises(ValueError, match="blocked_triage_risk_score"):
        config(blocked_triage_risk_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="counter_evidence_strength"):
        conflict("case-bad", counter_evidence_strength=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="conflict_id"):
        conflict("raw-market-0xabc")
    with pytest.raises(ValueError, match="conflict_id"):
        conflict("case url")
    with pytest.raises(ValueError, match="oldest_publication_age_seconds"):
        conflict(
            "case-time",
            newest_publication_age_seconds=d("100.000000"),
            oldest_publication_age_seconds=d("99.000000"),
        )
    with pytest.raises(ValueError, match="shared_source_family_count"):
        conflict(
            "case-shared",
            supporting_source_family_count=d("1.000000"),
            opposing_source_family_count=d("2.000000"),
            shared_source_family_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="impact_domain"):
        conflict("case-domain", impact_domain="rumor")
    with pytest.raises(ValueError, match="operator_escalation_requested"):
        conflict("case-bool", operator_escalation_requested=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="readonly"):
        replace(conflict("case-flag"), readonly=False)
    with pytest.raises(ValueError, match="rows must be unique"):
        report((conflict("case-dup"), conflict("case-dup")))


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    triage_report = report((conflict("case-pass"),))

    with pytest.raises(FrozenInstanceError):
        triage_report.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        triage_report.rows[0].triage_risk_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="recommended_escalation"):
        replace(triage_report.rows[0], recommended_escalation="immediate")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(triage_report, report_status="watch")


def test_owned_module_has_no_io_trading_database_or_sensitive_public_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_news_source_conflict_triage_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "insert ",
        "update ",
        "delete ",
        "commit(",
        "execute(",
        "source_url",
        "source_text",
        "source_ref",
        "raw_market",
        "market_id",
        "dsn",
        "token",
        "trade",
        "order",
        "buy",
        "sell",
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


def _unsafe_payload_matches(value: object) -> tuple[str, ...]:
    unsafe_terms = (
        "url",
        "text",
        "ref",
        "dsn",
        "table",
        "token",
        "raw",
        "market",
        "condition",
        "clob",
        "http",
        "https",
    )
    matches: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            matches.extend(_unsafe_string_matches(str(key), unsafe_terms))
            matches.extend(_unsafe_payload_matches(item))
    elif isinstance(value, list):
        for item in value:
            matches.extend(_unsafe_payload_matches(item))
    elif isinstance(value, str):
        matches.extend(_unsafe_string_matches(value, unsafe_terms))
    return tuple(matches)


def _unsafe_string_matches(value: str, unsafe_terms: tuple[str, ...]) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in value.lower():
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(token for token in tokens if token in unsafe_terms)
