from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_resolution_source_mapping_report import (
    ResearchResolutionSourceMappingConfig,
    ResearchResolutionSourceMappingEvidence,
    ResearchResolutionSourceMappingReasonCodeCount,
    ResearchResolutionSourceMappingReport,
    ResearchResolutionSourceMappingRow,
    build_research_resolution_source_mapping_report,
    research_resolution_source_mapping_report_payload,
    validate_research_resolution_source_mapping_public_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchResolutionSourceMappingConfig:
    values = {
        "config_version": "research-resolution-source-mapping-report-v0",
        "min_official_source_count": d("1"),
        "min_reviewed_source_count": d("1"),
        "max_ambiguous_source_count": d("0"),
    }
    values.update(overrides)
    return ResearchResolutionSourceMappingConfig(**values)


def evidence(
    index: int,
    *,
    event_key: str = "event-alpha",
    source_key: str | None = None,
    source_family: str = "official",
    source_role: str = "official",
    observed_at: datetime | None = None,
    evidence_score: Decimal = d("0.900000"),
    review_status: str = "reviewed",
    evidence_gap: bool = False,
) -> ResearchResolutionSourceMappingEvidence:
    return ResearchResolutionSourceMappingEvidence(
        event_key=event_key,
        source_key=source_key or f"source-{index:03d}",
        source_family=source_family,
        source_role=source_role,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=index * 10),
        evidence_score=evidence_score,
        review_status=review_status,
        evidence_gap=evidence_gap,
    )


def report(
    rows: tuple[ResearchResolutionSourceMappingEvidence, ...],
    *,
    cfg: ResearchResolutionSourceMappingConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchResolutionSourceMappingReport:
    return build_research_resolution_source_mapping_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_official_and_alternate_reviewed_sources_pass() -> None:
    mapping_report = report(
        (
            evidence(2, source_role="alternate", source_family="press"),
            evidence(1, source_role="official", source_family="exchange"),
        ),
    )

    assert type(mapping_report) is ResearchResolutionSourceMappingReport
    assert mapping_report.status == "pass"
    assert mapping_report.event_count == d("1")
    assert mapping_report.source_count == d("2")
    assert mapping_report.official_source_count == d("1")
    assert mapping_report.alternate_source_count == d("1")
    assert mapping_report.ambiguous_source_count == d("0")
    assert mapping_report.evidence_gap_count == d("0")
    assert mapping_report.reviewed_source_count == d("2")
    assert mapping_report.pass_count == d("1")
    assert mapping_report.watch_count == d("0")
    assert mapping_report.block_count == d("0")
    assert mapping_report.reason_codes == ("resolution_source_mapping_pass",)

    row = mapping_report.rows[0]
    assert type(row) is ResearchResolutionSourceMappingRow
    assert row.event_key == "event-alpha"
    assert row.source_count == d("2")
    assert row.official_source_count == d("1")
    assert row.alternate_source_count == d("1")
    assert row.ambiguous_source_count == d("0")
    assert row.evidence_gap_count == d("0")
    assert row.reviewed_source_count == d("2")
    assert row.pending_review_count == d("0")
    assert row.escalated_review_count == d("0")
    assert row.average_evidence_score == d("0.900000")
    assert row.latest_observed_at == GENERATED_AT - timedelta(minutes=10)
    assert row.latest_source_age_seconds == d("600.000000")
    assert row.review_status == "reviewed"
    assert row.status == "pass"
    assert row.reason_codes == ("resolution_source_mapping_pass",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_ambiguous_source_and_pending_review_create_watch_status() -> None:
    mapping_report = report(
        (
            evidence(1, source_role="official", source_family="exchange"),
            evidence(
                2,
                source_role="ambiguous",
                source_family="social",
                review_status="pending_review",
                evidence_score=d("0.500000"),
            ),
        ),
    )

    row = mapping_report.rows[0]
    assert mapping_report.status == "watch"
    assert mapping_report.watch_count == d("1")
    assert mapping_report.reason_codes == (
        "ambiguous_sources_present",
        "review_pending",
    )
    assert row.status == "watch"
    assert row.review_status == "pending_review"
    assert row.ambiguous_source_count == d("1")
    assert row.pending_review_count == d("1")
    assert row.reason_codes == (
        "ambiguous_sources_present",
        "review_pending",
    )


def test_missing_official_evidence_gap_and_escalated_review_block_status() -> None:
    mapping_report = report(
        (
            evidence(
                1,
                source_role="alternate",
                source_family="analysis",
                review_status="escalated_review",
                evidence_gap=True,
                evidence_score=d("0.300000"),
            ),
        ),
    )

    row = mapping_report.rows[0]
    assert mapping_report.status == "block"
    assert mapping_report.block_count == d("1")
    assert mapping_report.official_source_count == d("0")
    assert mapping_report.evidence_gap_count == d("1")
    assert mapping_report.escalated_review_count == d("1")
    assert mapping_report.reason_codes == (
        "evidence_gap_present",
        "missing_official_source",
        "review_escalated",
    )
    assert row.status == "block"
    assert row.review_status == "escalated_review"
    assert row.reason_codes == (
        "evidence_gap_present",
        "missing_official_source",
        "review_escalated",
    )


def test_empty_input_blocks_with_zero_counts() -> None:
    mapping_report = report(())

    assert mapping_report.status == "block"
    assert mapping_report.event_count == d("0")
    assert mapping_report.source_count == d("0")
    assert mapping_report.average_evidence_score is None
    assert mapping_report.reason_codes == ("no_resolution_sources",)
    assert mapping_report.reason_code_counts == (
        ResearchResolutionSourceMappingReasonCodeCount(
            reason_code="no_resolution_sources",
            count=d("1"),
        ),
    )
    assert mapping_report.rows == ()


def test_rows_reason_counts_and_payload_are_public_safe_and_decimal_strings() -> None:
    mapping_report = report(
        (
            evidence(3, event_key="event-z", source_role="alternate"),
            evidence(1, event_key="event-a", source_role="official"),
            evidence(
                2,
                event_key="event-z",
                source_role="ambiguous",
                review_status="pending_review",
                evidence_score=d("0.500000"),
            ),
        ),
    )

    payload = research_resolution_source_mapping_report_payload(mapping_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.event_key for row in mapping_report.rows) == ("event-a", "event-z")
    assert tuple(
        (count.reason_code, count.count)
        for count in mapping_report.reason_code_counts
    ) == (
        ("ambiguous_sources_present", d("1")),
        ("missing_official_source", d("1")),
        ("review_pending", d("1")),
    )
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["event_count"] == "2"
    assert payload["source_count"] == "3"
    assert payload["average_evidence_score"] == "0.766667"
    assert payload["rows"][1]["average_evidence_score"] == "0.700000"
    assert not any(
        isinstance(value, float | int) and type(value) is not bool
        for value in _walk_payload_values(payload)
    )
    assert all(
        forbidden not in encoded.lower()
        for forbidden in ("http://", "https://", "url", "raw_market", "market_id")
    )
    assert validate_research_resolution_source_mapping_public_payload(payload) is True


def test_validation_rejects_bad_types_unknown_enums_future_times_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="min_official_source_count"):
        config(min_official_source_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_reviewed_source_count"):
        config(min_reviewed_source_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="event_key"):
        evidence(1, event_key=" event-alpha")
    with pytest.raises(ValueError, match="source_key"):
        evidence(1, source_key="https://example.test/resolution")
    with pytest.raises(ValueError, match="source_key"):
        evidence(1, source_key="raw_market_123")
    with pytest.raises(ValueError, match="source_role"):
        evidence(1, source_role="primary")
    with pytest.raises(ValueError, match="review_status"):
        evidence(1, review_status="done")
    with pytest.raises(ValueError, match="evidence_score"):
        evidence(1, evidence_score=d("1.000001"))
    with pytest.raises(ValueError, match="evidence_score"):
        evidence(1, evidence_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        evidence(1, observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((evidence(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="evidence_gap"):
        replace(evidence(1), evidence_gap=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_reports_validate_consistency() -> None:
    mapping_report = report((evidence(1),))

    with pytest.raises(FrozenInstanceError):
        mapping_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        mapping_report.rows[0].source_count = d("9")  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_count"):
        replace(mapping_report.rows[0], source_count=d("9"))
    with pytest.raises(ValueError, match="status"):
        replace(mapping_report, status="watch")


def test_owned_module_has_no_network_filesystem_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_resolution_source_mapping_report.py"
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
        "sqlite",
        "sqlalchemy",
        "insert ",
        "update ",
        "delete ",
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
