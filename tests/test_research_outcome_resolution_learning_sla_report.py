from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.research_outcome_resolution_learning_sla_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def aggregate(
    aggregate_label: str,
    *,
    resolved_outcome_count: Decimal = d("10.000000"),
    settlement_evidence_checked_at: datetime = datetime(
        2026,
        7,
        8,
        11,
        30,
        tzinfo=UTC,
    ),
    calibration_feedback_complete_count: Decimal = d("9.000000"),
    error_taxonomy_mapped_count: Decimal = d("10.000000"),
    memory_writeback_pending_count: Decimal = d("0.000000"),
    oldest_memory_writeback_pending_at: datetime | None = None,
):
    report_module = module()
    return report_module.ResearchOutcomeResolutionLearningSlaAggregate(
        aggregate_label=aggregate_label,
        resolved_outcome_count=resolved_outcome_count,
        settlement_evidence_checked_at=settlement_evidence_checked_at,
        calibration_feedback_complete_count=calibration_feedback_complete_count,
        error_taxonomy_mapped_count=error_taxonomy_mapped_count,
        memory_writeback_pending_count=memory_writeback_pending_count,
        oldest_memory_writeback_pending_at=oldest_memory_writeback_pending_at,
    )


def build_report(*aggregates):
    report_module = module()
    return report_module.build_research_outcome_resolution_learning_sla_report(
        aggregates,
        config=report_module.ResearchOutcomeResolutionLearningSlaConfig(
            config_version="research-outcome-resolution-learning-sla-test-v0",
            settlement_evidence_stale_after_seconds=d("3600.000000"),
            calibration_feedback_min_ratio=d("0.800000"),
            error_taxonomy_min_ratio=d("0.900000"),
            memory_writeback_due_after_seconds=d("1800.000000"),
        ),
        generated_at=GENERATED_AT,
    )


def assert_json_ready_without_public_numerics(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise AssertionError("payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for nested_value in value.values():
            assert_json_ready_without_public_numerics(nested_value)
        return
    if isinstance(value, (list, tuple)):
        for nested_value in value:
            assert_json_ready_without_public_numerics(nested_value)
        return
    assert value is None or isinstance(value, (str, bool))


def test_builds_aggregate_learning_sla_report_across_readiness_dimensions() -> None:
    report = build_report(
        aggregate("aggregate:domain:ready"),
        aggregate(
            "aggregate:cohort:settlement-stale",
            settlement_evidence_checked_at=datetime(2026, 7, 8, 10, 0, tzinfo=UTC),
        ),
        aggregate(
            "aggregate:domain:calibration-gap",
            calibration_feedback_complete_count=d("7.000000"),
        ),
        aggregate(
            "aggregate:source_family:taxonomy-gap",
            error_taxonomy_mapped_count=d("8.000000"),
        ),
        aggregate(
            "aggregate:team:memory-urgent",
            memory_writeback_pending_count=d("2.000000"),
            oldest_memory_writeback_pending_at=datetime(2026, 7, 8, 11, 0, tzinfo=UTC),
        ),
        aggregate(
            "aggregate:team:memory-missing-age",
            memory_writeback_pending_count=d("1.000000"),
        ),
        aggregate(
            "aggregate:resolution_window:no-resolved",
            resolved_outcome_count=d("0.000000"),
            calibration_feedback_complete_count=d("0.000000"),
            error_taxonomy_mapped_count=d("0.000000"),
        ),
    )

    assert report.status == "block"
    assert report.aggregate_count == d("7.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("3.000000")
    assert report.block_count == d("3.000000")
    assert report.resolved_outcome_count == d("60.000000")
    assert report.stale_settlement_evidence_count == d("1.000000")
    assert report.incomplete_calibration_feedback_count == d("1.000000")
    assert report.insufficient_error_taxonomy_coverage_count == d("1.000000")
    assert report.urgent_memory_writeback_count == d("1.000000")
    assert report.missing_memory_writeback_age_count == d("1.000000")
    assert report.min_calibration_feedback_completion_ratio == d("0.000000")
    assert report.min_error_taxonomy_coverage_ratio == d("0.000000")
    assert report.max_settlement_evidence_age_seconds == d("7200.000000")
    assert report.max_memory_writeback_urgency_seconds == d("3600.000000")
    assert report.reason_codes == (
        "missing_memory_writeback_age",
        "no_resolved_outcomes",
        "memory_writeback_urgent",
        "settlement_evidence_stale",
        "calibration_feedback_incomplete",
        "error_taxonomy_coverage_gap",
    )
    assert tuple(row.aggregate_label for row in report.rows) == (
        "aggregate:resolution_window:no-resolved",
        "aggregate:team:memory-missing-age",
        "aggregate:team:memory-urgent",
        "aggregate:cohort:settlement-stale",
        "aggregate:domain:calibration-gap",
        "aggregate:source_family:taxonomy-gap",
        "aggregate:domain:ready",
    )
    assert report.rows[0].status == "block"
    assert report.rows[0].reason_codes == ("no_resolved_outcomes",)
    assert report.rows[2].memory_writeback_urgency_seconds == d("3600.000000")
    assert report.rows[3].settlement_evidence_age_seconds == d("7200.000000")
    assert report.rows[4].calibration_feedback_completion_ratio == d("0.700000")
    assert report.rows[5].error_taxonomy_coverage_ratio == d("0.800000")
    assert report.rows[6].status == "pass"
    assert report.rows[6].reason_codes == ("learning_sla_clear",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_aggregate_set_blocks_without_dividing_by_zero() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.aggregate_count == d("0.000000")
    assert report.resolved_outcome_count == d("0.000000")
    assert report.min_calibration_feedback_completion_ratio == d("0.000000")
    assert report.min_error_taxonomy_coverage_ratio == d("0.000000")
    assert report.reason_codes == ("no_learning_aggregates",)
    assert report.rows == ()


def test_payload_is_deterministic_digest_checked_and_json_ready() -> None:
    report_module = module()
    report = build_report(aggregate("aggregate:all"))

    payload = report_module.research_outcome_resolution_learning_sla_report_payload(report)
    repeated_payload = report_module.research_outcome_resolution_learning_sla_report_payload(
        report,
    )

    assert payload == repeated_payload
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["aggregate_count"] == "1.000000"
    assert payload["rows"][0]["calibration_feedback_completion_ratio"] == "0.900000"
    assert payload["rows"][0]["paper_only"] is True
    assert_json_ready_without_public_numerics(payload)
    json.dumps(payload, sort_keys=True)

    assert (
        report_module.research_outcome_resolution_learning_sla_report_payload(payload)
        == payload
    )
    tampered = dict(payload)
    tampered["status"] = "block"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_module.research_outcome_resolution_learning_sla_report_payload(tampered)
    tampered_numeric = dict(payload)
    tampered_numeric["aggregate_count"] = 1
    with pytest.raises(ValueError, match="Decimal-derived strings"):
        report_module.research_outcome_resolution_learning_sla_report_payload(
            tampered_numeric,
        )


def test_dataclasses_are_frozen_and_public_numeric_fields_use_decimal() -> None:
    report_module = module()

    assert report_module.__all__ == (
        "DEFAULT_RESEARCH_OUTCOME_RESOLUTION_LEARNING_SLA_CONFIG_VERSION",
        "ResearchOutcomeResolutionLearningSlaAggregate",
        "ResearchOutcomeResolutionLearningSlaConfig",
        "ResearchOutcomeResolutionLearningSlaReport",
        "ResearchOutcomeResolutionLearningSlaRow",
        "build_research_outcome_resolution_learning_sla_report",
        "research_outcome_resolution_learning_sla_report_payload",
        "validate_research_outcome_resolution_learning_sla_public_payload",
    )
    for exported_name in report_module.__all__:
        value = getattr(report_module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(aggregate("aggregate:domain:frozen"))
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"  # type: ignore[misc]

    for value in (report, *report.rows):
        for field in fields(value):
            if field.name.endswith(("count", "ratio", "seconds")):
                assert type(getattr(value, field.name)) is Decimal


def test_aggregate_safe_labels_hard_flags_and_aware_datetimes_are_required() -> None:
    report_module = module()

    with pytest.raises(ValueError, match="aggregate_label"):
        aggregate("domain:missing-prefix")
    with pytest.raises(ValueError, match="aggregate_label"):
        aggregate("aggregate:unknown:too-specific")
    with pytest.raises(ValueError, match="paper_only"):
        report_module.ResearchOutcomeResolutionLearningSlaAggregate(
            aggregate_label="aggregate:all",
            resolved_outcome_count=d("1.000000"),
            settlement_evidence_checked_at=GENERATED_AT,
            calibration_feedback_complete_count=d("1.000000"),
            error_taxonomy_mapped_count=d("1.000000"),
            memory_writeback_pending_count=d("0.000000"),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report_module.build_research_outcome_resolution_learning_sla_report(
            (),
            config=report_module.ResearchOutcomeResolutionLearningSlaConfig(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )

    report = report_module.build_research_outcome_resolution_learning_sla_report(
        (
            aggregate(
                "aggregate:team:utc-normalized",
                settlement_evidence_checked_at=datetime(
                    2026,
                    7,
                    8,
                    11,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
        ),
        config=report_module.ResearchOutcomeResolutionLearningSlaConfig(),
        generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc),
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].settlement_evidence_checked_at == datetime(
        2026,
        7,
        8,
        11,
        0,
        tzinfo=UTC,
    )


def test_rejects_float_decimal_subclass_and_inconsistent_counts() -> None:
    report_module = module()

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="calibration_feedback_min_ratio"):
        report_module.ResearchOutcomeResolutionLearningSlaConfig(
            calibration_feedback_min_ratio=1.0,
        )
    with pytest.raises(ValueError, match="resolved_outcome_count"):
        report_module.ResearchOutcomeResolutionLearningSlaAggregate(
            aggregate_label="aggregate:all",
            resolved_outcome_count=DerivedDecimal("1.000000"),
            settlement_evidence_checked_at=GENERATED_AT,
            calibration_feedback_complete_count=d("1.000000"),
            error_taxonomy_mapped_count=d("1.000000"),
            memory_writeback_pending_count=d("0.000000"),
        )
    with pytest.raises(ValueError, match="must not exceed resolved_outcome_count"):
        aggregate(
            "aggregate:domain:bad-counts",
            resolved_outcome_count=d("1.000000"),
            calibration_feedback_complete_count=d("2.000000"),
        )


def test_module_omits_forbidden_runtime_surfaces() -> None:
    source = module().__loader__.get_source(module().__name__)
    assert source is not None
    lowered = source.lower()

    for forbidden in (
        "database",
        "network",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "trade",
        "position",
    ):
        assert forbidden not in lowered
