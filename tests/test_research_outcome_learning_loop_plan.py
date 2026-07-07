from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_outcome_learning_loop_plan import (
    ResearchOutcomeLearningLoopConfig,
    ResearchOutcomeLearningLoopEvent,
    ResearchOutcomeLearningLoopPlanRow,
    ResearchOutcomeLearningLoopReasonCodeCount,
    ResearchOutcomeLearningLoopReport,
    build_research_outcome_learning_loop_plan,
    research_outcome_learning_loop_plan_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 10, 30, tzinfo=UTC)
RESOLVED_AT = datetime(2026, 7, 6, 18, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedOutcomeShape:
    event_ref: str
    team_ref: str
    forecast_probability: Decimal
    resolved_probability: Decimal
    evidence_gap_score: Decimal
    memory_update_score: Decimal
    write_plan_score: Decimal
    resolved_at: datetime
    evidence_gap_count: Decimal = Decimal("0")
    memory_item_count: Decimal = Decimal("0")
    write_plan_item_count: Decimal = Decimal("0")
    has_resolution_evidence: bool = True
    has_team_memory_update: bool = True
    has_local_write_plan: bool = True
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchOutcomeLearningLoopConfig:
    values = {
        "config_version": "research-outcome-learning-loop-plan-v0",
        "pass_learning_score": d("0.700000"),
        "watch_learning_score": d("0.400000"),
        "forecast_bias_weight": d("0.350000"),
        "evidence_gap_weight": d("0.250000"),
        "memory_update_weight": d("0.200000"),
        "write_plan_weight": d("0.200000"),
        "forecast_bias_watch_threshold": d("0.150000"),
        "forecast_bias_block_threshold": d("0.350000"),
        "minimum_write_plan_items": d("2"),
    }
    values.update(overrides)
    return ResearchOutcomeLearningLoopConfig(**values)


def event(index: int, **overrides: object) -> ResearchOutcomeLearningLoopEvent:
    values = {
        "event_ref": f"event-{index:03d}",
        "team_ref": "research-team-alpha",
        "forecast_probability": d("0.620000"),
        "resolved_probability": d("1.000000"),
        "evidence_gap_score": d("0.200000"),
        "memory_update_score": d("1.000000"),
        "write_plan_score": d("1.000000"),
        "resolved_at": RESOLVED_AT,
        "evidence_gap_count": d("1"),
        "memory_item_count": d("2"),
        "write_plan_item_count": d("3"),
        "has_resolution_evidence": True,
        "has_team_memory_update": True,
        "has_local_write_plan": True,
        "reason_codes": (),
    }
    values.update(overrides)
    return ResearchOutcomeLearningLoopEvent(**values)


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchOutcomeLearningLoopConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchOutcomeLearningLoopReport:
    return build_research_outcome_learning_loop_plan(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_with_no_database_connection() -> None:
    learning_report = report(())

    assert type(learning_report) is ResearchOutcomeLearningLoopReport
    assert learning_report.generated_at == GENERATED_AT
    assert learning_report.config_version == "research-outcome-learning-loop-plan-v0"
    assert learning_report.event_count == d("0")
    assert learning_report.pass_count == d("0")
    assert learning_report.watch_count == d("0")
    assert learning_report.blocked_count == d("0")
    assert learning_report.average_learning_score is None
    assert learning_report.status == "blocked"
    assert learning_report.reason_codes == ("no_settled_prediction_events",)
    assert learning_report.reason_code_counts == (
        ResearchOutcomeLearningLoopReasonCodeCount(
            reason_code="no_settled_prediction_events",
            count=d("1"),
        ),
    )
    assert learning_report.rows == ()
    assert learning_report.public_payload == ()
    assert learning_report.paper_only is True
    assert learning_report.report_only is True
    assert learning_report.readonly is True


def test_closed_loop_event_passes_with_prediction_bias_and_write_plan_coverage() -> None:
    learning_report = report(
        (
            event(
                1,
                forecast_probability=d("0.880000"),
                resolved_probability=d("1.000000"),
                evidence_gap_score=d("0.000000"),
                memory_update_score=d("1.000000"),
                write_plan_score=d("1.000000"),
                evidence_gap_count=d("0"),
                memory_item_count=d("3"),
                write_plan_item_count=d("3"),
                reason_codes=("manual_postmortem_completed",),
            ),
        ),
    )

    assert learning_report.status == "pass"
    assert learning_report.event_count == d("1")
    assert learning_report.pass_count == d("1")
    assert learning_report.watch_count == d("0")
    assert learning_report.blocked_count == d("0")
    assert learning_report.average_learning_score == d("0.958000")
    assert learning_report.reason_codes == ("research_outcome_learning_loop_pass",)

    row = learning_report.rows[0]
    assert type(row) is ResearchOutcomeLearningLoopPlanRow
    assert row.event_ref == "event-001"
    assert row.team_ref == "research-team-alpha"
    assert row.forecast_bias == d("0.120000")
    assert row.bias_score == d("0.880000")
    assert row.evidence_gap_score == d("0.000000")
    assert row.evidence_coverage_score == d("1.000000")
    assert row.memory_update_score == d("1.000000")
    assert row.write_plan_score == d("1.000000")
    assert row.learning_score == d("0.958000")
    assert row.status == "pass"
    assert row.local_write_plan == (
        "stage_redacted_outcome_delta",
        "upsert_team_memory_rollup",
        "append_evidence_gap_backlog",
    )
    assert row.reason_codes == (
        "input_manual_postmortem_completed",
        "local_postgres_write_plan_ready",
        "memory_update_ready",
        "prediction_bias_within_watch_threshold",
        "research_outcome_learning_loop_pass",
        "resolution_evidence_present",
    )


def test_evidence_gaps_and_missing_memory_update_watch() -> None:
    learning_report = report(
        (
            event(
                1,
                forecast_probability=d("0.620000"),
                resolved_probability=d("1.000000"),
                evidence_gap_score=d("0.500000"),
                memory_update_score=d("0.300000"),
                write_plan_score=d("0.500000"),
                evidence_gap_count=d("2"),
                memory_item_count=d("0"),
                write_plan_item_count=d("1"),
                has_team_memory_update=False,
            ),
        ),
    )

    row = learning_report.rows[0]
    assert learning_report.status == "watch"
    assert learning_report.watch_count == d("1")
    assert learning_report.average_learning_score == d("0.442000")
    assert row.forecast_bias == d("0.380000")
    assert row.learning_score == d("0.442000")
    assert row.status == "watch"
    assert row.reason_codes == (
        "evidence_gap_backlog_needed",
        "local_postgres_write_plan_incomplete",
        "memory_update_missing",
        "prediction_bias_block_threshold_exceeded",
        "research_outcome_learning_loop_watch",
        "resolution_evidence_present",
    )


def test_high_bias_missing_resolution_and_missing_write_plan_block() -> None:
    learning_report = report(
        (
            event(
                1,
                forecast_probability=d("0.930000"),
                resolved_probability=d("0.000000"),
                evidence_gap_score=d("1.000000"),
                memory_update_score=d("0.000000"),
                write_plan_score=d("0.000000"),
                evidence_gap_count=d("3"),
                memory_item_count=d("0"),
                write_plan_item_count=d("0"),
                has_resolution_evidence=False,
                has_team_memory_update=False,
                has_local_write_plan=False,
            ),
        ),
    )

    row = learning_report.rows[0]
    assert learning_report.status == "blocked"
    assert learning_report.blocked_count == d("1")
    assert learning_report.average_learning_score == d("0.024500")
    assert row.forecast_bias == d("0.930000")
    assert row.bias_score == d("0.070000")
    assert row.learning_score == d("0.024500")
    assert row.status == "blocked"
    assert row.reason_codes == (
        "evidence_gap_backlog_needed",
        "local_postgres_write_plan_missing",
        "memory_update_missing",
        "prediction_bias_block_threshold_exceeded",
        "research_outcome_learning_loop_blocked",
        "resolution_evidence_missing",
    )


def test_rows_reason_counts_and_public_payload_are_sanitized_and_decimal_only() -> None:
    learning_report = report(
        (
            SuppliedOutcomeShape(
                event_ref="event-002",
                team_ref="research-team-beta",
                forecast_probability=d("0.500000"),
                resolved_probability=d("1.000000"),
                evidence_gap_score=d("0.250000"),
                memory_update_score=d("0.750000"),
                write_plan_score=d("0.500000"),
                resolved_at=RESOLVED_AT,
                evidence_gap_count=d("1"),
                memory_item_count=d("2"),
                write_plan_item_count=d("2"),
                reason_codes=("analyst_reviewed",),
            ),
            event(
                1,
                forecast_probability=d("0.880000"),
                resolved_probability=d("1.000000"),
                evidence_gap_score=d("0.000000"),
                memory_update_score=d("1.000000"),
                write_plan_score=d("1.000000"),
                evidence_gap_count=d("0"),
                memory_item_count=d("3"),
                write_plan_item_count=d("3"),
            ),
        ),
    )

    payload = research_outcome_learning_loop_plan_payload(learning_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.event_ref for row in learning_report.rows) == (
        "event-001",
        "event-002",
    )
    assert learning_report.public_payload == ()
    assert payload["rows"][0]["learning_score"] == "0.958000"
    assert payload["rows"][0]["forecast_bias"] == "0.120000"
    assert payload["rows"][0]["local_write_plan"] == [
        "stage_redacted_outcome_delta",
        "upsert_team_memory_rollup",
        "append_evidence_gap_backlog",
    ]
    assert "dsn" not in encoded.lower()
    assert "table" not in encoded.lower()
    assert "source_url" not in encoded.lower()
    assert "source_text" not in encoded.lower()
    assert "raw_market" not in encoded.lower()
    assert "buy" not in encoded.lower()
    assert "sell" not in encoded.lower()
    assert "trade" not in encoded.lower()
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_validation_rejects_bad_types_unsafe_public_values_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="forecast_bias_weight"):
        config(forecast_bias_weight=d("0.500000"))
    with pytest.raises(ValueError, match="pass_learning_score"):
        config(pass_learning_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_learning_score"):
        config(watch_learning_score=_DecimalSubclass("0.400000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((event(1),), generated_at=datetime(2026, 7, 7, 10, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (event(1),),
            generated_at=_DatetimeSubclass(2026, 7, 7, 10, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="event_ref"):
        event(1, event_ref="market-raw-123")
    with pytest.raises(ValueError, match="team_ref"):
        event(1, team_ref="research team")
    with pytest.raises(ValueError, match="forecast_probability"):
        event(1, forecast_probability=d("1.100000"))
    with pytest.raises(ValueError, match="resolved_at"):
        event(1, resolved_at=datetime(2026, 7, 6, 18, 0))
    with pytest.raises(ValueError, match="resolved_at"):
        report((event(1, resolved_at=GENERATED_AT),))
    with pytest.raises(ValueError, match="has_local_write_plan"):
        replace(event(1), has_local_write_plan=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        event(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(event(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    learning_report = report((event(1),))

    with pytest.raises(FrozenInstanceError):
        learning_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        learning_report.rows[0].learning_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="learning_score"):
        replace(learning_report.rows[0], learning_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(learning_report, status="pass")


def test_owned_module_has_no_database_network_trading_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_outcome_learning_loop_plan.py"
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
        "create_engine",
        "supabase.create_client",
        "wallet",
        "private_key",
        "place_order",
        "cancel_order",
        "submit_order",
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
