from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_decision_block_reason_catalog import (
    ResearchDecisionBlockReasonCatalogReport,
    ResearchDecisionBlockReasonCatalogRow,
    ResearchDecisionBlockReasonObservation,
    build_research_decision_block_reason_catalog_report,
    research_decision_block_reason_catalog_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedObservationShape:
    reason_family: str
    coverage_status: str
    severity_score: Decimal
    confidence_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    reason_family: str,
    coverage_status: str,
    severity_score: str = "0.600000",
    confidence_score: str = "0.800000",
    reason_codes: tuple[str, ...] = ("manual_reviewed",),
) -> ResearchDecisionBlockReasonObservation:
    return ResearchDecisionBlockReasonObservation(
        reason_family=reason_family,
        coverage_status=coverage_status,
        severity_score=d(severity_score),
        confidence_score=d(confidence_score),
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    generated_at: datetime = GENERATED_AT,
) -> ResearchDecisionBlockReasonCatalogReport:
    return build_research_decision_block_reason_catalog_report(
        rows,
        generated_at=generated_at,
    )


def test_empty_input_blocks_all_required_reason_families() -> None:
    catalog_report = report(())

    assert type(catalog_report) is ResearchDecisionBlockReasonCatalogReport
    assert catalog_report.generated_at == GENERATED_AT
    assert catalog_report.observation_count == d("0")
    assert catalog_report.reason_family_count == d("5")
    assert catalog_report.pass_count == d("0")
    assert catalog_report.watch_count == d("0")
    assert catalog_report.block_count == d("5")
    assert catalog_report.coverage_status == "block"
    assert catalog_report.reason_codes == (
        "missing_cost_too_high_reason_coverage",
        "missing_evidence_insufficient_reason_coverage",
        "missing_memory_gap_reason_coverage",
        "missing_settlement_ambiguity_reason_coverage",
        "missing_source_conflict_reason_coverage",
        "reason_catalog_block",
    )
    assert tuple(row.reason_family for row in catalog_report.rows) == (
        "cost_too_high",
        "evidence_insufficient",
        "memory_gap",
        "settlement_ambiguity",
        "source_conflict",
    )
    assert all(row.coverage_status == "block" for row in catalog_report.rows)
    assert catalog_report.paper_only is True
    assert catalog_report.report_only is True
    assert catalog_report.readonly is True


def test_all_required_families_with_pass_coverage_pass_report() -> None:
    catalog_report = report(
        (
            observation(reason_family="source_conflict", coverage_status="pass"),
            observation(reason_family="evidence_insufficient", coverage_status="pass"),
            observation(reason_family="settlement_ambiguity", coverage_status="pass"),
            observation(reason_family="memory_gap", coverage_status="pass"),
            observation(reason_family="cost_too_high", coverage_status="pass"),
        ),
    )

    assert catalog_report.coverage_status == "pass"
    assert catalog_report.observation_count == d("5")
    assert catalog_report.pass_count == d("5")
    assert catalog_report.watch_count == d("0")
    assert catalog_report.block_count == d("0")
    assert catalog_report.reason_codes == ("reason_catalog_pass",)
    assert all(type(row) is ResearchDecisionBlockReasonCatalogRow for row in catalog_report.rows)
    assert all(row.coverage_status == "pass" for row in catalog_report.rows)
    assert all(row.observation_count == d("1") for row in catalog_report.rows)
    assert all(row.average_confidence_score == d("0.800000") for row in catalog_report.rows)


def test_partial_watch_and_block_coverage_uses_worst_family_status() -> None:
    catalog_report = report(
        (
            observation(
                reason_family="evidence_insufficient",
                coverage_status="watch",
                confidence_score="0.500000",
                reason_codes=("needs_more_evidence",),
            ),
            observation(
                reason_family="cost_too_high",
                coverage_status="pass",
                severity_score="0.250000",
                confidence_score="0.900000",
            ),
            observation(
                reason_family="source_conflict",
                coverage_status="block",
                severity_score="0.950000",
                confidence_score="0.700000",
                reason_codes=("unresolved_conflict",),
            ),
        ),
    )

    source_conflict_row = catalog_report.rows[-1]
    assert source_conflict_row.reason_family == "source_conflict"
    assert source_conflict_row.coverage_status == "block"
    assert source_conflict_row.max_severity_score == d("0.950000")
    assert source_conflict_row.average_confidence_score == d("0.700000")
    assert catalog_report.coverage_status == "block"
    assert catalog_report.pass_count == d("1")
    assert catalog_report.watch_count == d("1")
    assert catalog_report.block_count == d("3")
    assert "reason_catalog_block" in catalog_report.reason_codes
    assert "source_conflict_block_coverage" in catalog_report.reason_codes
    assert "evidence_insufficient_watch_coverage" in catalog_report.reason_codes
    assert "missing_memory_gap_reason_coverage" in catalog_report.reason_codes


def test_payload_is_deterministic_decimal_only_and_public_safe() -> None:
    catalog_report = report(
        (
            SuppliedObservationShape(
                reason_family="memory_gap",
                coverage_status="watch",
                severity_score=d("0.400000"),
                confidence_score=d("0.600000"),
                reason_codes=("memory_review_needed",),
            ),
        ),
    )

    payload = research_decision_block_reason_catalog_payload(catalog_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["observation_count"] == "1"
    assert payload["rows"][2]["reason_family"] == "memory_gap"
    assert payload["rows"][2]["average_confidence_score"] == "0.600000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert "token" not in encoded.lower()
    assert "dsn" not in encoded.lower()
    assert "table" not in encoded.lower()
    assert "market-" not in encoded.lower()
    assert "source-id" not in encoded.lower()


def test_validation_rejects_bad_types_unknown_values_and_raw_sensitive_text() -> None:
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="reason_family"):
        observation(reason_family="unknown_reason", coverage_status="pass")
    with pytest.raises(ValueError, match="coverage_status"):
        observation(reason_family="memory_gap", coverage_status="ready")
    with pytest.raises(ValueError, match="severity_score"):
        ResearchDecisionBlockReasonObservation(
            reason_family="memory_gap",
            coverage_status="watch",
            severity_score=Decimal("0.1"),
            confidence_score=d("0.800000"),
            reason_codes=("manual_reviewed",),
        )
    with pytest.raises(ValueError, match="confidence_score"):
        ResearchDecisionBlockReasonObservation(
            reason_family="memory_gap",
            coverage_status="watch",
            severity_score=d("0.100000"),
            confidence_score=_DecimalSubclass("0.800000"),
            reason_codes=("manual_reviewed",),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        observation(
            reason_family="memory_gap",
            coverage_status="watch",
            reason_codes=("raw_market_slug:abc",),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            observation(reason_family="memory_gap", coverage_status="watch"),
            paper_only=False,
        )


def test_public_dataclasses_are_frozen_and_manual_report_consistency_is_checked() -> None:
    catalog_report = report(
        (
            observation(reason_family="memory_gap", coverage_status="watch"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        catalog_report.coverage_status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        catalog_report.rows[0].coverage_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="coverage_status"):
        replace(catalog_report, coverage_status="pass")
    with pytest.raises(ValueError, match="observation_count"):
        replace(catalog_report.rows[0], observation_count=d("2"))


def test_owned_module_has_no_network_filesystem_execution_or_advice_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_decision_block_reason_catalog.py"
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
        "buy",
        "sell",
        "trade",
        "order",
        "position",
        "investment advice",
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
