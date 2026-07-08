from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_source_contradiction_memory_report import (
    ResearchEventSourceContradictionMemoryConfig,
    ResearchEventSourceContradictionMemoryRecord,
    ResearchEventSourceContradictionMemoryReport,
    ResearchEventSourceContradictionMemoryRow,
    build_research_event_source_contradiction_memory_report,
    research_event_source_contradiction_memory_report_payload,
    validate_research_event_source_contradiction_memory_public_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEventSourceContradictionMemoryConfig:
    values = {
        "config_version": "research-event-source-contradiction-memory-report-v0",
        "stale_evidence_seconds": d("86400"),
        "watch_recheck_urgency_score": d("0.350000"),
        "block_recheck_urgency_score": d("0.750000"),
        "unresolved_disagreement_weight": d("0.450000"),
        "stale_evidence_weight": d("0.300000"),
        "domain_escalation_fit_weight": d("0.250000"),
    }
    values.update(overrides)
    return ResearchEventSourceContradictionMemoryConfig(**values)


def memory_record(
    index: int,
    *,
    event_slug: str = "event-alpha",
    domain_label: str = "weather",
    source_label: str = "official-aggregate",
    position_label: str = "affirming",
    observed_at: datetime | None = None,
    resolved: bool = False,
    domain_escalation_fit: bool = False,
    reason_codes: tuple[str, ...] = (),
) -> ResearchEventSourceContradictionMemoryRecord:
    return ResearchEventSourceContradictionMemoryRecord(
        memory_id=f"memory-{index:03d}",
        event_slug=event_slug,
        domain_label=domain_label,
        source_label=source_label,
        position_label=position_label,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(hours=1)
        ),
        resolved=resolved,
        domain_escalation_fit=domain_escalation_fit,
        reason_codes=reason_codes,
    )


def report(
    records: tuple[ResearchEventSourceContradictionMemoryRecord, ...],
    *,
    cfg: ResearchEventSourceContradictionMemoryConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventSourceContradictionMemoryReport:
    return build_research_event_source_contradiction_memory_report(
        records,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_aggregate_unresolved_stale_domain_fit_blocks_with_deterministic_digest() -> None:
    records = (
        memory_record(
            3,
            event_slug="event-beta",
            domain_label="sports",
            source_label="official-aggregate",
            position_label="affirming",
        ),
        memory_record(
            2,
            source_label="analysis-aggregate",
            position_label="affirming",
            observed_at=GENERATED_AT - timedelta(days=2),
        ),
        memory_record(
            1,
            source_label="official-aggregate",
            position_label="negating",
            observed_at=GENERATED_AT - timedelta(minutes=90),
            domain_escalation_fit=True,
            reason_codes=("manual_review_needed",),
        ),
    )

    memory_report = report(records)
    payload = research_event_source_contradiction_memory_report_payload(memory_report)
    encoded = json.dumps(payload, sort_keys=True)
    rebuilt_payload = research_event_source_contradiction_memory_report_payload(
        report(tuple(reversed(records))),
    )

    assert type(memory_report) is ResearchEventSourceContradictionMemoryReport
    assert memory_report.generated_at == GENERATED_AT
    assert memory_report.event_count == d("2")
    assert memory_report.memory_record_count == d("3")
    assert memory_report.pass_count == d("1")
    assert memory_report.watch_count == d("0")
    assert memory_report.block_count == d("1")
    assert memory_report.unresolved_source_disagreement_count == d("1")
    assert memory_report.stale_contradiction_evidence_count == d("1")
    assert memory_report.domain_escalation_fit_count == d("1")
    assert memory_report.max_recheck_urgency_score == d("1.000000")
    assert memory_report.status == "block"
    assert memory_report.paper_only is True
    assert memory_report.report_only is True
    assert memory_report.readonly is True
    assert len(memory_report.derived_validation_digest) == 64

    alpha_row = memory_report.rows[0]
    assert type(alpha_row) is ResearchEventSourceContradictionMemoryRow
    assert alpha_row.event_slug == "event-alpha"
    assert alpha_row.domain_label == "weather"
    assert alpha_row.memory_record_count == d("2")
    assert alpha_row.source_label_count == d("2")
    assert alpha_row.position_label_count == d("2")
    assert alpha_row.contradiction_evidence_count == d("2")
    assert alpha_row.latest_observed_at == GENERATED_AT - timedelta(minutes=90)
    assert alpha_row.latest_evidence_age_seconds == d("5400")
    assert alpha_row.oldest_contradiction_evidence_age_seconds == d("172800")
    assert alpha_row.unresolved_source_disagreement is True
    assert alpha_row.stale_contradiction_evidence is True
    assert alpha_row.domain_escalation_fit is True
    assert alpha_row.recheck_urgency_score == d("1.000000")
    assert alpha_row.status == "block"
    assert alpha_row.source_labels == ("analysis-aggregate", "official-aggregate")
    assert alpha_row.position_labels == ("affirming", "negating")
    assert alpha_row.reason_codes == (
        "contradiction_memory_block",
        "domain_escalation_fit",
        "input_manual_review_needed",
        "recheck_urgency_block",
        "stale_contradiction_evidence",
        "unresolved_source_disagreement",
    )

    beta_row = memory_report.rows[1]
    assert beta_row.event_slug == "event-beta"
    assert beta_row.status == "pass"
    assert beta_row.recheck_urgency_score == d("0.000000")
    assert beta_row.reason_codes == (
        "contradiction_memory_pass",
        "domain_escalation_not_fit",
        "no_contradiction_evidence",
        "no_unresolved_source_disagreement",
        "recheck_urgency_pass",
    )

    assert payload["derived_validation_digest"] == memory_report.derived_validation_digest
    assert rebuilt_payload == payload
    assert payload["rows"][0]["recheck_urgency_score"] == "1.000000"
    assert payload["rows"][0]["latest_observed_at"] == "2026-07-08T10:30:00+00:00"
    assert not any(type(value) is int or isinstance(value, float) for value in _walk(payload))
    assert ": 1.0" not in encoded
    validate_research_event_source_contradiction_memory_public_payload(payload)


def test_validation_public_safety_flags_consistency_and_no_live_surfaces() -> None:
    memory_report = report(
        (
            memory_record(
                1,
                source_label="official-aggregate",
                position_label="affirming",
            ),
            memory_record(
                2,
                source_label="analysis-aggregate",
                position_label="negating",
                observed_at=GENERATED_AT - timedelta(days=2),
            ),
        ),
    )
    payload = research_event_source_contradiction_memory_report_payload(memory_report)

    with pytest.raises(FrozenInstanceError):
        memory_report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        memory_report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="stale_evidence_seconds"):
        config(stale_evidence_seconds=86400.0)
    with pytest.raises(ValueError, match="watch_recheck_urgency_score"):
        config(watch_recheck_urgency_score=_DecimalSubclass("0.350000"))
    with pytest.raises(ValueError, match="source_label"):
        memory_record(4, source_label="https://example.test/source")
    with pytest.raises(ValueError, match="event_slug"):
        memory_record(14, event_slug="market-alpha")
    with pytest.raises(ValueError, match="event_slug"):
        memory_record(17, event_slug="will-fed-cut-rates")
    with pytest.raises(ValueError, match="source_label"):
        memory_record(15, source_label="candidate-aggregate")
    with pytest.raises(ValueError, match="reason_codes"):
        memory_record(16, reason_codes=("market_slug",))
    with pytest.raises(ValueError, match="position_label"):
        memory_record(5, position_label="mixed")
    with pytest.raises(ValueError, match="resolved"):
        replace(memory_record(6), resolved=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        replace(memory_record(7), paper_only=False)
    with pytest.raises(ValueError, match="observed_at"):
        report((memory_record(8, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="status"):
        replace(memory_report.rows[0], status="pass")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_event_source_contradiction_memory_public_payload(
            {**payload, "derived_validation_digest": "0" * 64},
        )
    with pytest.raises(ValueError, match="paper_only"):
        validate_research_event_source_contradiction_memory_public_payload(
            {**payload, "paper_only": False},
        )
    with pytest.raises(ValueError, match="unsafe public value"):
        validate_research_event_source_contradiction_memory_public_payload(
            {
                **payload,
                "rows": [{**payload["rows"][0], "event_slug": "candidate-123"}],
            },
        )
    with pytest.raises(ValueError, match="event_slug"):
        validate_research_event_source_contradiction_memory_public_payload(
            {
                **payload,
                "rows": [{**payload["rows"][0], "event_slug": "will-fed-cut-rates"}],
            },
        )
    with pytest.raises(ValueError, match="unsafe public field"):
        validate_research_event_source_contradiction_memory_public_payload(
            {**payload, "wallet_address": "public-aggregate"},
        )

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_source_contradiction_memory_report.py"
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
        "wallet",
        "place_order",
        "live_trading",
        "database",
        "sqlalchemy",
    )
    assert all(term not in source for term in forbidden_terms)


def _walk(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk(item))
    else:
        values.append(value)
    return tuple(values)
