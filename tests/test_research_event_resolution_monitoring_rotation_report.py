from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_resolution_monitoring_rotation_report import (
    ResearchEventResolutionMonitoringRotationConfig,
    ResearchEventResolutionMonitoringRotationInput,
    ResearchEventResolutionMonitoringRotationReport,
    ResearchEventResolutionMonitoringRotationRow,
    build_research_event_resolution_monitoring_rotation_report,
    research_event_resolution_monitoring_rotation_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEventResolutionMonitoringRotationConfig:
    values = {
        "config_version": "resolution-monitoring-rotation-report-v0",
        "fresh_evidence_age_seconds": d("1800"),
        "stale_evidence_age_seconds": d("21600"),
        "deadline_window_seconds": d("86400"),
        "oracle_lag_limit_seconds": d("3600"),
        "watch_rotation_pressure": d("0.450000"),
        "block_rotation_pressure": d("0.700000"),
        "evidence_age_weight": d("0.250000"),
        "deadline_weight": d("0.250000"),
        "source_reliability_weight": d("0.200000"),
        "oracle_lag_weight": d("0.150000"),
        "capacity_weight": d("0.150000"),
        "pass_monitoring_interval_seconds": d("3600"),
        "watch_monitoring_interval_seconds": d("900"),
        "block_monitoring_interval_seconds": d("300"),
    }
    values.update(overrides)
    return ResearchEventResolutionMonitoringRotationConfig(**values)


def rotation_input(
    rotation_bucket: str,
    *,
    aggregate_evidence_age_seconds: Decimal,
    deadline_proximity_seconds: Decimal,
    source_reliability_score: Decimal,
    oracle_lag_seconds: Decimal,
    open_resolution_items: Decimal,
    monitoring_capacity_units: Decimal,
    reason_codes: tuple[str, ...] = (),
) -> ResearchEventResolutionMonitoringRotationInput:
    return ResearchEventResolutionMonitoringRotationInput(
        rotation_bucket=rotation_bucket,
        aggregate_evidence_age_seconds=aggregate_evidence_age_seconds,
        deadline_proximity_seconds=deadline_proximity_seconds,
        source_reliability_score=source_reliability_score,
        oracle_lag_seconds=oracle_lag_seconds,
        open_resolution_items=open_resolution_items,
        monitoring_capacity_units=monitoring_capacity_units,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[ResearchEventResolutionMonitoringRotationInput, ...],
    *,
    cfg: ResearchEventResolutionMonitoringRotationConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventResolutionMonitoringRotationReport:
    return build_research_event_resolution_monitoring_rotation_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_public_safe_block_report() -> None:
    rotation_report = report(())

    assert type(rotation_report) is ResearchEventResolutionMonitoringRotationReport
    assert rotation_report.generated_at == GENERATED_AT
    assert rotation_report.config_version == "resolution-monitoring-rotation-report-v0"
    assert rotation_report.input_count == d("0")
    assert rotation_report.row_count == d("0")
    assert rotation_report.pass_count == d("0")
    assert rotation_report.watch_count == d("0")
    assert rotation_report.block_count == d("0")
    assert rotation_report.average_rotation_pressure is None
    assert rotation_report.max_rotation_pressure is None
    assert rotation_report.status == "block"
    assert rotation_report.reason_codes == ("no_resolution_monitoring_aggregates",)
    assert rotation_report.rows == ()
    assert rotation_report.paper_only is True
    assert rotation_report.report_only is True
    assert rotation_report.readonly is True
    assert len(rotation_report.derived_validation_digest) == 64


def test_rotation_plan_uses_age_deadline_reliability_oracle_lag_and_capacity() -> None:
    rotation_report = report(
        (
            rotation_input(
                "late-oracle-capacity",
                aggregate_evidence_age_seconds=d("21600"),
                deadline_proximity_seconds=d("0"),
                source_reliability_score=d("0.100000"),
                oracle_lag_seconds=d("7200"),
                open_resolution_items=d("10"),
                monitoring_capacity_units=d("5"),
                reason_codes=("manual_review",),
            ),
            rotation_input(
                "near-deadline-watch",
                aggregate_evidence_age_seconds=d("10800"),
                deadline_proximity_seconds=d("43200"),
                source_reliability_score=d("0.500000"),
                oracle_lag_seconds=d("1800"),
                open_resolution_items=d("3"),
                monitoring_capacity_units=d("4"),
            ),
            rotation_input(
                "fresh-covered-pass",
                aggregate_evidence_age_seconds=d("900"),
                deadline_proximity_seconds=d("86400"),
                source_reliability_score=d("0.950000"),
                oracle_lag_seconds=d("0"),
                open_resolution_items=d("1"),
                monitoring_capacity_units=d("10"),
            ),
        ),
    )

    assert rotation_report.status == "block"
    assert rotation_report.input_count == d("3")
    assert rotation_report.row_count == d("3")
    assert rotation_report.block_count == d("1")
    assert rotation_report.watch_count == d("1")
    assert rotation_report.pass_count == d("1")
    assert rotation_report.average_rotation_pressure == d("0.514167")
    assert rotation_report.max_rotation_pressure == d("0.980000")
    assert rotation_report.near_deadline_count == d("2")
    assert rotation_report.stale_evidence_count == d("1")
    assert rotation_report.oracle_lag_count == d("2")
    assert rotation_report.constrained_capacity_count == d("2")

    rows = {row.rotation_bucket: row for row in rotation_report.rows}
    assert tuple(rows) == (
        "late-oracle-capacity",
        "near-deadline-watch",
        "fresh-covered-pass",
    )

    block_row = rows["late-oracle-capacity"]
    assert type(block_row) is ResearchEventResolutionMonitoringRotationRow
    assert block_row.rotation_priority == d("1")
    assert block_row.evidence_age_pressure == d("1.000000")
    assert block_row.deadline_pressure == d("1.000000")
    assert block_row.source_reliability_pressure == d("0.900000")
    assert block_row.oracle_lag_pressure == d("1.000000")
    assert block_row.capacity_pressure == d("1.000000")
    assert block_row.rotation_pressure == d("0.980000")
    assert block_row.monitoring_interval_seconds == d("300")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "capacity_constrained",
        "evidence_stale",
        "input_manual_review",
        "oracle_lag_elevated",
        "resolution_deadline_near",
        "rotation_block",
        "source_reliability_low",
    )

    watch_row = rows["near-deadline-watch"]
    assert watch_row.rotation_priority == d("2")
    assert watch_row.rotation_pressure == d("0.537500")
    assert watch_row.monitoring_interval_seconds == d("900")
    assert watch_row.status == "watch"

    pass_row = rows["fresh-covered-pass"]
    assert pass_row.rotation_priority == d("3")
    assert pass_row.rotation_pressure == d("0.025000")
    assert pass_row.monitoring_interval_seconds == d("3600")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == (
        "capacity_available",
        "evidence_fresh",
        "oracle_lag_clear",
        "resolution_deadline_not_near",
        "rotation_pass",
        "source_reliability_high",
    )


def test_payload_and_digest_are_deterministic_decimal_only_and_public_safe() -> None:
    row_a = rotation_input(
        "near-deadline-watch",
        aggregate_evidence_age_seconds=d("10800"),
        deadline_proximity_seconds=d("43200"),
        source_reliability_score=d("0.500000"),
        oracle_lag_seconds=d("1800"),
        open_resolution_items=d("3"),
        monitoring_capacity_units=d("4"),
    )
    row_b = rotation_input(
        "fresh-covered-pass",
        aggregate_evidence_age_seconds=d("900"),
        deadline_proximity_seconds=d("86400"),
        source_reliability_score=d("0.950000"),
        oracle_lag_seconds=d("0"),
        open_resolution_items=d("1"),
        monitoring_capacity_units=d("10"),
    )
    first_report = report((row_b, row_a))
    second_report = report((row_a, row_b))

    first_payload = research_event_resolution_monitoring_rotation_report_payload(first_report)
    second_payload = research_event_resolution_monitoring_rotation_report_payload(second_report)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["rows"][0]["rotation_bucket"] == "near-deadline-watch"
    assert first_payload["rows"][0]["rotation_pressure"] == "0.537500"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 0.5" not in encoded
    assert "raw-event-123" not in encoded
    assert "market-" not in encoded
    assert "source-" not in encoded


def test_validation_rejects_non_decimal_inputs_bad_status_flags_and_identifiers() -> None:
    with pytest.raises(ValueError, match="fresh_evidence_age_seconds"):
        config(fresh_evidence_age_seconds=1800)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="deadline_weight"):
        config(deadline_weight=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="weights"):
        config(capacity_weight=d("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="aggregate_evidence_age_seconds"):
        rotation_input(
            "bad-decimal",
            aggregate_evidence_age_seconds=1,  # type: ignore[arg-type]
            deadline_proximity_seconds=d("1"),
            source_reliability_score=d("1"),
            oracle_lag_seconds=d("0"),
            open_resolution_items=d("1"),
            monitoring_capacity_units=d("1"),
        )
    with pytest.raises(ValueError, match="source_reliability_score"):
        rotation_input(
            "bad-reliability",
            aggregate_evidence_age_seconds=d("1"),
            deadline_proximity_seconds=d("1"),
            source_reliability_score=d("1.100000"),
            oracle_lag_seconds=d("0"),
            open_resolution_items=d("1"),
            monitoring_capacity_units=d("1"),
        )
    with pytest.raises(ValueError, match="rotation_bucket"):
        rotation_input(
            "raw-event-123",
            aggregate_evidence_age_seconds=d("1"),
            deadline_proximity_seconds=d("1"),
            source_reliability_score=d("1"),
            oracle_lag_seconds=d("0"),
            open_resolution_items=d("1"),
            monitoring_capacity_units=d("1"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            rotation_input(
                "safe-bucket",
                aggregate_evidence_age_seconds=d("1"),
                deadline_proximity_seconds=d("1"),
                source_reliability_score=d("1"),
                oracle_lag_seconds=d("0"),
                open_resolution_items=d("1"),
                monitoring_capacity_units=d("1"),
            ),
            paper_only=False,
        )


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    rotation_report = report(
        (
            rotation_input(
                "fresh-covered-pass",
                aggregate_evidence_age_seconds=d("900"),
                deadline_proximity_seconds=d("86400"),
                source_reliability_score=d("0.950000"),
                oracle_lag_seconds=d("0"),
                open_resolution_items=d("1"),
                monitoring_capacity_units=d("10"),
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        rotation_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        rotation_report.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(rotation_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(rotation_report, status="blocked")
    with pytest.raises(ValueError, match="rotation_pressure"):
        replace(rotation_report.rows[0], rotation_pressure=d("0.900000"))


def test_owned_module_has_no_io_execution_or_unsafe_language_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_resolution_monitoring_rotation_report.py"
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
        "postgres",
        "mysql",
        "wallet",
        "auth",
        "order",
        "trade",
        "live execution",
        "recommend",
        "sizing",
        "event_id",
        "market_id",
        "source_id",
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
