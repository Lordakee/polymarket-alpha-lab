from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_resolution_evidence_staleness_backlog_report import (
    ResearchResolutionEvidenceStalenessBacklogConfig,
    ResearchResolutionEvidenceStalenessBacklogInput,
    ResearchResolutionEvidenceStalenessBacklogReasonCodeCount,
    ResearchResolutionEvidenceStalenessBacklogReport,
    ResearchResolutionEvidenceStalenessBacklogRow,
    build_research_resolution_evidence_staleness_backlog_report,
    research_resolution_evidence_staleness_backlog_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedBacklogShape:
    public_case_id: str
    evidence_bundle_count: Decimal
    aggregate_evidence_age_seconds: Decimal
    source_class_reliability: Decimal
    contradiction_pressure: Decimal
    deadline_proximity: Decimal
    rule_clarity: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchResolutionEvidenceStalenessBacklogConfig:
    values = {
        "fresh_age_seconds": d("3600"),
        "stale_age_seconds": d("86400"),
        "watch_pressure_threshold": d("0.350000"),
        "block_pressure_threshold": d("0.700000"),
        "aggregate_age_weight": d("0.300000"),
        "source_class_reliability_weight": d("0.200000"),
        "contradiction_pressure_weight": d("0.200000"),
        "deadline_proximity_weight": d("0.150000"),
        "rule_clarity_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchResolutionEvidenceStalenessBacklogConfig(**values)


def backlog_item(
    public_case_id: str = "case-a",
    *,
    evidence_bundle_count: Decimal = d("3"),
    aggregate_evidence_age_seconds: Decimal = d("1800"),
    source_class_reliability: Decimal = d("0.950000"),
    contradiction_pressure: Decimal = d("0.050000"),
    deadline_proximity: Decimal = d("0.100000"),
    rule_clarity: Decimal = d("0.900000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchResolutionEvidenceStalenessBacklogInput:
    return ResearchResolutionEvidenceStalenessBacklogInput(
        public_case_id=public_case_id,
        evidence_bundle_count=evidence_bundle_count,
        aggregate_evidence_age_seconds=aggregate_evidence_age_seconds,
        source_class_reliability=source_class_reliability,
        contradiction_pressure=contradiction_pressure,
        deadline_proximity=deadline_proximity,
        rule_clarity=rule_clarity,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchResolutionEvidenceStalenessBacklogConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchResolutionEvidenceStalenessBacklogReport:
    return build_research_resolution_evidence_staleness_backlog_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_public_safe_pass_report_with_digest() -> None:
    backlog_report = report(())

    assert type(backlog_report) is ResearchResolutionEvidenceStalenessBacklogReport
    assert backlog_report.generated_at == GENERATED_AT
    assert backlog_report.case_count == d("0")
    assert backlog_report.pass_count == d("0")
    assert backlog_report.watch_count == d("0")
    assert backlog_report.block_count == d("0")
    assert backlog_report.average_backlog_pressure is None
    assert backlog_report.max_aggregate_evidence_age_seconds == d("0")
    assert backlog_report.status == "pass"
    assert backlog_report.reason_codes == ("no_staleness_backlog_items",)
    assert backlog_report.reason_code_counts == (
        ResearchResolutionEvidenceStalenessBacklogReasonCodeCount(
            reason_code="no_staleness_backlog_items",
            count=d("1"),
        ),
    )
    assert backlog_report.rows == ()
    assert len(backlog_report.derived_validation_digest) == 64
    assert backlog_report.paper_only is True
    assert backlog_report.report_only is True
    assert backlog_report.readonly is True


def test_backlog_uses_age_reliability_contradiction_deadline_and_rule_clarity() -> None:
    backlog_report = report(
        (
            backlog_item(
                "case-c",
                aggregate_evidence_age_seconds=d("172800"),
                source_class_reliability=d("0.400000"),
                contradiction_pressure=d("0.800000"),
                deadline_proximity=d("0.900000"),
                rule_clarity=d("0.300000"),
                reason_codes=("requires_fresh_public_evidence",),
            ),
            backlog_item(
                "case-a",
                aggregate_evidence_age_seconds=d("1800"),
                source_class_reliability=d("0.950000"),
                contradiction_pressure=d("0.050000"),
                deadline_proximity=d("0.100000"),
                rule_clarity=d("0.900000"),
            ),
            backlog_item(
                "case-b",
                aggregate_evidence_age_seconds=d("43200"),
                source_class_reliability=d("0.700000"),
                contradiction_pressure=d("0.350000"),
                deadline_proximity=d("0.400000"),
                rule_clarity=d("0.700000"),
            ),
        ),
    )

    assert tuple(row.public_case_id for row in backlog_report.rows) == (
        "case-a",
        "case-b",
        "case-c",
    )
    assert backlog_report.status == "block"
    assert backlog_report.case_count == d("3")
    assert backlog_report.pass_count == d("1")
    assert backlog_report.watch_count == d("1")
    assert backlog_report.block_count == d("1")
    assert backlog_report.average_backlog_pressure == d("0.418333")
    assert backlog_report.max_aggregate_evidence_age_seconds == d("172800")

    pass_row, watch_row, block_row = backlog_report.rows
    assert type(pass_row) is ResearchResolutionEvidenceStalenessBacklogRow
    assert pass_row.aggregate_age_pressure == d("0.000000")
    assert pass_row.source_class_reliability_gap == d("0.050000")
    assert pass_row.rule_clarity_gap == d("0.100000")
    assert pass_row.backlog_pressure == d("0.050000")
    assert pass_row.status == "pass"
    assert watch_row.aggregate_age_pressure == d("0.500000")
    assert watch_row.backlog_pressure == d("0.385000")
    assert watch_row.status == "watch"
    assert block_row.aggregate_age_pressure == d("1.000000")
    assert block_row.source_class_reliability_gap == d("0.600000")
    assert block_row.rule_clarity_gap == d("0.700000")
    assert block_row.backlog_pressure == d("0.820000")
    assert block_row.status == "block"
    assert "input_requires_fresh_public_evidence" in block_row.reason_codes
    assert backlog_report.reason_code_counts == tuple(
        sorted(backlog_report.reason_code_counts, key=lambda item: item.reason_code),
    )


def test_payload_and_digest_are_deterministic_public_safe_and_decimal_strings() -> None:
    rows = (
        SuppliedBacklogShape(
            public_case_id="case-b",
            evidence_bundle_count=d("2"),
            aggregate_evidence_age_seconds=d("43200"),
            source_class_reliability=d("0.700000"),
            contradiction_pressure=d("0.350000"),
            deadline_proximity=d("0.400000"),
            rule_clarity=d("0.700000"),
            reason_codes=("manual_backlog_review",),
        ),
        backlog_item("case-a"),
    )

    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = research_resolution_evidence_staleness_backlog_report_payload(
        first_report,
    )
    second_payload = research_resolution_evidence_staleness_backlog_report_payload(
        second_report,
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["rows"][0]["backlog_pressure"] == "0.050000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 0.5" not in encoded
    assert all(
        fragment not in encoded.lower()
        for fragment in (
            "http",
            "source_url",
            "source_text",
            "source_ref",
            "market_slug",
            "market_id",
            "condition_id",
        )
    )


def test_validation_rejects_bad_types_thresholds_flags_and_unsafe_public_values() -> None:
    with pytest.raises(ValueError, match="aggregate_age_weight"):
        config(aggregate_age_weight=d("0.100000"))
    with pytest.raises(ValueError, match="block_pressure_threshold"):
        config(block_pressure_threshold=d("0.300000"))
    with pytest.raises(ValueError, match="fresh_age_seconds"):
        config(fresh_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_class_reliability_weight"):
        config(source_class_reliability_weight=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((backlog_item(),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (backlog_item(),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="public_case_id"):
        backlog_item(public_case_id="case url")
    with pytest.raises(ValueError, match="public_case_id"):
        backlog_item(public_case_id="market-alpha")
    with pytest.raises(ValueError, match="evidence_bundle_count"):
        backlog_item(evidence_bundle_count=d("1.5"))
    with pytest.raises(ValueError, match="aggregate_evidence_age_seconds"):
        backlog_item(aggregate_evidence_age_seconds=1800)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_pressure"):
        backlog_item(contradiction_pressure=d("1.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        backlog_item(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(backlog_item(), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    backlog_report = report((backlog_item(),))

    with pytest.raises(FrozenInstanceError):
        backlog_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        backlog_report.rows[0].backlog_pressure = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(backlog_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(backlog_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="count"):
        replace(backlog_report, case_count=d("2"))


def test_owned_module_has_no_filesystem_network_execution_or_advice_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_resolution_evidence_staleness_backlog_report.py"
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
        "auth",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
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
