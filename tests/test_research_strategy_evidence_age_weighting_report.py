from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_strategy_evidence_age_weighting_report import (
    ResearchStrategyEvidenceAgeWeightingConfig,
    ResearchStrategyEvidenceAgeWeightingInput,
    ResearchStrategyEvidenceAgeWeightingReasonCodeCount,
    ResearchStrategyEvidenceAgeWeightingReport,
    ResearchStrategyEvidenceAgeWeightingRow,
    build_research_strategy_evidence_age_weighting_report,
    research_strategy_evidence_age_weighting_report_digest,
    research_strategy_evidence_age_weighting_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_evidence_age_weighting_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyEvidenceAgeWeightingConfig:
    values = {
        "config_version": "research-strategy-evidence-age-weighting-report-v0",
        "fresh_age_seconds": d("3600"),
        "stale_age_seconds": d("86400"),
        "watch_pressure_threshold": d("0.350000"),
        "block_pressure_threshold": d("0.700000"),
        "aggregate_age_weight": d("0.350000"),
        "source_reliability_weight": d("0.200000"),
        "contradiction_pressure_weight": d("0.200000"),
        "catalyst_pressure_weight": d("0.150000"),
        "resolution_proximity_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchStrategyEvidenceAgeWeightingConfig(**values)


def evidence_item(
    research_case_label: str = "case-a",
    *,
    evidence_bucket_label: str = "bundle-alpha",
    aggregate_evidence_age_seconds: Decimal = d("1800"),
    source_reliability: Decimal = d("0.950000"),
    contradiction_pressure: Decimal = d("0.050000"),
    catalyst_pressure: Decimal = d("0.100000"),
    resolution_proximity: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchStrategyEvidenceAgeWeightingInput:
    return ResearchStrategyEvidenceAgeWeightingInput(
        research_case_label=research_case_label,
        evidence_bucket_label=evidence_bucket_label,
        aggregate_evidence_age_seconds=aggregate_evidence_age_seconds,
        source_reliability=source_reliability,
        contradiction_pressure=contradiction_pressure,
        catalyst_pressure=catalyst_pressure,
        resolution_proximity=resolution_proximity,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchStrategyEvidenceAgeWeightingConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyEvidenceAgeWeightingReport:
    return build_research_strategy_evidence_age_weighting_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_report_only_block_with_validation_digest() -> None:
    age_report = report(())

    assert type(age_report) is ResearchStrategyEvidenceAgeWeightingReport
    assert age_report.generated_at == GENERATED_AT
    assert age_report.config_version == "research-strategy-evidence-age-weighting-report-v0"
    assert age_report.case_count == d("0")
    assert age_report.pass_count == d("0")
    assert age_report.watch_count == d("0")
    assert age_report.block_count == d("0")
    assert age_report.average_weighted_age_pressure is None
    assert age_report.max_aggregate_evidence_age_seconds == d("0")
    assert age_report.status == "block"
    assert age_report.reason_codes == ("no_evidence_age_weighting_inputs",)
    assert age_report.reason_code_counts == (
        ResearchStrategyEvidenceAgeWeightingReasonCodeCount(
            reason_code="no_evidence_age_weighting_inputs",
            count=d("1"),
        ),
    )
    assert age_report.rows == ()
    assert len(age_report.derived_validation_digest) == 64
    assert age_report.paper_only is True
    assert age_report.report_only is True
    assert age_report.readonly is True


def test_report_weights_age_reliability_contradiction_catalyst_and_resolution() -> None:
    age_report = report(
        (
            evidence_item(
                "case-c",
                aggregate_evidence_age_seconds=d("172800"),
                source_reliability=d("0.400000"),
                contradiction_pressure=d("0.800000"),
                catalyst_pressure=d("0.900000"),
                resolution_proximity=d("0.900000"),
                reason_codes=("manual_freshness_review",),
            ),
            evidence_item("case-a"),
            evidence_item(
                "case-b",
                aggregate_evidence_age_seconds=d("43200"),
                source_reliability=d("0.700000"),
                contradiction_pressure=d("0.350000"),
                catalyst_pressure=d("0.450000"),
                resolution_proximity=d("0.400000"),
            ),
        ),
    )

    assert tuple(row.research_case_label for row in age_report.rows) == (
        "case-a",
        "case-b",
        "case-c",
    )
    assert age_report.status == "block"
    assert age_report.case_count == d("3")
    assert age_report.pass_count == d("1")
    assert age_report.watch_count == d("1")
    assert age_report.block_count == d("1")
    assert age_report.average_weighted_age_pressure == d("0.434964")
    assert age_report.max_aggregate_evidence_age_seconds == d("172800")

    pass_row, watch_row, block_row = age_report.rows
    assert type(pass_row) is ResearchStrategyEvidenceAgeWeightingRow
    assert pass_row.aggregate_age_pressure == d("0.000000")
    assert pass_row.source_reliability_gap == d("0.050000")
    assert pass_row.weighted_age_pressure == d("0.045000")
    assert pass_row.evidence_age_weight == d("0.955000")
    assert pass_row.status == "pass"
    assert watch_row.aggregate_age_pressure == d("0.478261")
    assert watch_row.weighted_age_pressure == d("0.404891")
    assert watch_row.evidence_age_weight == d("0.595109")
    assert watch_row.status == "watch"
    assert block_row.aggregate_age_pressure == d("1.000000")
    assert block_row.source_reliability_gap == d("0.600000")
    assert block_row.weighted_age_pressure == d("0.855000")
    assert block_row.evidence_age_weight == d("0.145000")
    assert block_row.status == "block"
    assert "input_manual_freshness_review" in block_row.reason_codes
    assert age_report.reason_code_counts == tuple(
        sorted(age_report.reason_code_counts, key=lambda item: item.reason_code),
    )


def test_payload_and_digest_are_deterministic_public_safe_and_decimal_strings() -> None:
    rows = (
        evidence_item("case-b", reason_codes=("manual_freshness_review",)),
        evidence_item("case-a", evidence_bucket_label="bundle-beta"),
    )

    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = research_strategy_evidence_age_weighting_report_payload(first_report)
    second_payload = research_strategy_evidence_age_weighting_report_payload(second_report)
    encoded = json.dumps(first_payload, sort_keys=True)
    first_digest = research_strategy_evidence_age_weighting_report_digest(first_report)

    assert first_payload == second_payload
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert first_digest == research_strategy_evidence_age_weighting_report_digest(second_report)
    assert len(first_digest) == 64
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["rows"][0]["weighted_age_pressure"] == "0.045000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 0.4" not in encoded
    assert all(
        fragment not in encoded.lower()
        for fragment in (
            "event_id",
            "market_id",
            "market_slug",
            "condition_id",
            "source_id",
            "source_ref",
            "source_url",
            "source_text",
            "raw_event",
            "raw_market",
            "raw_source",
            "b" + "uy",
            "se" + "ll",
            "reco" + "mmend",
            "position_size",
        )
    )


def test_validation_rejects_bad_types_thresholds_flags_and_raw_labels() -> None:
    with pytest.raises(ValueError, match="aggregate_age_weight"):
        config(aggregate_age_weight=d("0.100000"))
    with pytest.raises(ValueError, match="block_pressure_threshold"):
        config(block_pressure_threshold=d("0.300000"))
    with pytest.raises(ValueError, match="fresh_age_seconds"):
        config(fresh_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_reliability_weight"):
        config(source_reliability_weight=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence_item(),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (evidence_item(),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="research_case_label"):
        evidence_item(research_case_label="market-alpha")
    with pytest.raises(ValueError, match="evidence_bucket_label"):
        evidence_item(evidence_bucket_label="source-alpha")
    with pytest.raises(ValueError, match="aggregate_evidence_age_seconds"):
        evidence_item(aggregate_evidence_age_seconds=1800)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_pressure"):
        evidence_item(contradiction_pressure=d("1.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        evidence_item(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence_item(), paper_only=False)


def test_rows_and_reports_are_frozen_and_statuses_are_exact() -> None:
    age_report = report((evidence_item(),))
    row = age_report.rows[0]

    assert {row.status for row in age_report.rows} <= {"pass", "watch", "block"}
    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        age_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        ResearchStrategyEvidenceAgeWeightingRow(
            research_case_label="case-a",
            evidence_bucket_label="bundle-alpha",
            aggregate_evidence_age_seconds=d("1800"),
            aggregate_age_pressure=d("0.000000"),
            source_reliability=d("0.950000"),
            source_reliability_gap=d("0.050000"),
            contradiction_pressure=d("0.050000"),
            catalyst_pressure=d("0.100000"),
            resolution_proximity=d("0.100000"),
            weighted_age_pressure=d("0.045000"),
            evidence_age_weight=d("0.955000"),
            status="hold",
            reason_codes=("evidence_age_weighting_pass",),
        )


def test_module_stays_pure_report_only_without_persistence_or_execution_surfaces() -> None:
    source_text = MODULE_PATH.read_text()

    assert "open(" not in source_text
    assert "write(" not in source_text
    assert "requests" not in source_text
    assert "urllib" not in source_text
    assert "socket" not in source_text
    assert "psycopg" not in source_text
    assert "supabase" not in source_text
    assert "subprocess" not in source_text
    assert "websocket" not in source_text
    assert "private" + "_key" not in source_text
    assert "wal" + "let" not in source_text
    assert "au" + "th" not in source_text
    assert "or" + "der" not in source_text
    assert "tra" + "de" not in source_text


def _walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in _walk_payload_values(nested))
    if isinstance(value, list):
        return tuple(item for nested in value for item in _walk_payload_values(nested))
    return (value,)
