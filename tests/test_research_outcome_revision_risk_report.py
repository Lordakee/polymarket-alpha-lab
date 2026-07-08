from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import ast
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_outcome_revision_risk_report import (
    ResearchOutcomeRevisionRiskConfig,
    ResearchOutcomeRevisionRiskObservation,
    ResearchOutcomeRevisionRiskReasonCodeCount,
    ResearchOutcomeRevisionRiskReport,
    ResearchOutcomeRevisionRiskRow,
    build_research_outcome_revision_risk_report,
    research_outcome_revision_risk_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_outcome_revision_risk_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedObservationShape:
    event_id: str
    outcome_id: str
    observation_id: str
    lifecycle_stage: str
    observed_at: datetime
    settlement_at: datetime | None
    expected_settlement_at: datetime | None
    dispute_window_ends_at: datetime | None
    evidence_update_count: Decimal = Decimal("0")
    contradicting_evidence_update_count: Decimal = Decimal("0")
    evidence_reliability_score: Decimal = Decimal("0.800000")
    postmortem_impact_score: Decimal = Decimal("0.000000")
    memory_update_needed: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchOutcomeRevisionRiskConfig:
    values = {
        "config_version": "research-outcome-revision-risk-report-v0",
        "near_settlement_seconds": d("86400"),
        "watch_evidence_update_count": d("1"),
        "block_contradicting_update_count": d("1"),
        "min_reliability_score": d("0.700000"),
        "block_reliability_score": d("0.400000"),
        "watch_postmortem_impact_score": d("0.400000"),
        "high_postmortem_impact_score": d("0.700000"),
        "watch_revision_risk_score": d("0.300000"),
        "block_revision_risk_score": d("0.700000"),
    }
    values.update(overrides)
    return ResearchOutcomeRevisionRiskConfig(**values)


def observation(
    index: int,
    *,
    event_id: str = "event-alpha",
    outcome_id: str = "outcome-yes",
    lifecycle_stage: str = "settled",
    observed_at: datetime | None = None,
    settlement_at: datetime | None = None,
    expected_settlement_at: datetime | None = None,
    dispute_window_ends_at: datetime | None = None,
    evidence_update_count: Decimal = d("0"),
    contradicting_evidence_update_count: Decimal = d("0"),
    evidence_reliability_score: Decimal = d("0.900000"),
    postmortem_impact_score: Decimal = d("0.100000"),
    memory_update_needed: bool = False,
    reason_codes: tuple[str, ...] = (),
) -> ResearchOutcomeRevisionRiskObservation:
    default_observed_at = GENERATED_AT - timedelta(hours=1)
    actual_observed_at = observed_at if observed_at is not None else default_observed_at
    if lifecycle_stage == "settled":
        actual_settlement_at = (
            settlement_at if settlement_at is not None else GENERATED_AT - timedelta(days=3)
        )
        actual_expected_settlement_at = expected_settlement_at
        actual_dispute_window_ends_at = (
            dispute_window_ends_at
            if dispute_window_ends_at is not None
            else GENERATED_AT - timedelta(days=1)
        )
    else:
        actual_settlement_at = settlement_at
        actual_expected_settlement_at = (
            expected_settlement_at
            if expected_settlement_at is not None
            else GENERATED_AT + timedelta(hours=12)
        )
        actual_dispute_window_ends_at = dispute_window_ends_at
    return ResearchOutcomeRevisionRiskObservation(
        event_id=event_id,
        outcome_id=outcome_id,
        observation_id=f"observation-{index:03d}",
        lifecycle_stage=lifecycle_stage,
        observed_at=actual_observed_at,
        settlement_at=actual_settlement_at,
        expected_settlement_at=actual_expected_settlement_at,
        dispute_window_ends_at=actual_dispute_window_ends_at,
        evidence_update_count=evidence_update_count,
        contradicting_evidence_update_count=contradicting_evidence_update_count,
        evidence_reliability_score=evidence_reliability_score,
        postmortem_impact_score=postmortem_impact_score,
        memory_update_needed=memory_update_needed,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchOutcomeRevisionRiskConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchOutcomeRevisionRiskReport:
    return build_research_outcome_revision_risk_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_stable_settled_outcome_passes_revision_risk_report() -> None:
    risk_report = report(
        (
            observation(2, postmortem_impact_score=d("0.200000"), reason_codes=("audited",)),
            observation(1, evidence_reliability_score=d("0.800000")),
        ),
    )

    assert type(risk_report) is ResearchOutcomeRevisionRiskReport
    assert risk_report.generated_at == GENERATED_AT
    assert risk_report.config_version == "research-outcome-revision-risk-report-v0"
    assert risk_report.event_outcome_count == d("1")
    assert risk_report.observation_count == d("2")
    assert risk_report.pass_count == d("1")
    assert risk_report.watch_count == d("0")
    assert risk_report.block_count == d("0")
    assert risk_report.memory_update_needed_count == d("0")
    assert risk_report.status == "pass"
    assert risk_report.reason_codes == ("outcome_revision_risk_pass",)
    assert risk_report.paper_only is True
    assert risk_report.report_only is True
    assert risk_report.readonly is True

    row = risk_report.rows[0]
    assert type(row) is ResearchOutcomeRevisionRiskRow
    assert row.event_id == "event-alpha"
    assert row.outcome_id == "outcome-yes"
    assert row.observation_count == d("2")
    assert row.settled_observation_count == d("2")
    assert row.near_settlement_observation_count == d("0")
    assert row.active_dispute_window_count == d("0")
    assert row.evidence_update_count == d("0")
    assert row.contradicting_evidence_update_count == d("0")
    assert row.memory_update_needed_count == d("0")
    assert row.evidence_reliability_score == d("0.850000")
    assert row.postmortem_impact_score == d("0.200000")
    assert row.revision_risk_score == d("0.060000")
    assert row.status == "pass"
    assert row.reason_codes == (
        "dispute_window_clear",
        "evidence_reliability_pass",
        "evidence_update_clear",
        "input_audited",
        "memory_update_not_needed",
        "outcome_revision_risk_pass",
        "postmortem_impact_low",
        "revision_risk_score_low",
        "settled_event",
    )


def test_watch_and_block_rows_roll_up_to_block_report() -> None:
    risk_report = report(
        (
            observation(
                1,
                event_id="event-watch",
                outcome_id="outcome-a",
                lifecycle_stage="near_settlement",
                settlement_at=None,
                expected_settlement_at=GENERATED_AT + timedelta(hours=8),
                evidence_update_count=d("1"),
                evidence_reliability_score=d("0.650000"),
                postmortem_impact_score=d("0.300000"),
                memory_update_needed=True,
            ),
            observation(
                2,
                event_id="event-block",
                outcome_id="outcome-b",
                settlement_at=GENERATED_AT - timedelta(hours=2),
                dispute_window_ends_at=GENERATED_AT + timedelta(hours=10),
                evidence_update_count=d("2"),
                contradicting_evidence_update_count=d("1"),
                evidence_reliability_score=d("0.350000"),
                postmortem_impact_score=d("0.800000"),
                memory_update_needed=True,
            ),
        ),
    )

    assert risk_report.status == "block"
    assert risk_report.event_outcome_count == d("2")
    assert risk_report.pass_count == d("0")
    assert risk_report.watch_count == d("1")
    assert risk_report.block_count == d("1")
    assert risk_report.memory_update_needed_count == d("2")
    assert tuple(row.status for row in risk_report.rows) == ("block", "watch")

    blocked_row = risk_report.rows[0]
    assert blocked_row.event_id == "event-block"
    assert blocked_row.active_dispute_window_count == d("1")
    assert blocked_row.evidence_update_count == d("2")
    assert blocked_row.contradicting_evidence_update_count == d("1")
    assert blocked_row.evidence_reliability_score == d("0.350000")
    assert blocked_row.postmortem_impact_score == d("0.800000")
    assert blocked_row.revision_risk_score == d("0.900000")
    assert blocked_row.reason_codes == (
        "contradicting_evidence_update",
        "dispute_window_active",
        "evidence_reliability_block",
        "evidence_update_present",
        "memory_update_needed",
        "outcome_revision_risk_block",
        "postmortem_impact_block",
        "revision_risk_score_block",
        "settled_event",
    )

    watch_row = risk_report.rows[1]
    assert watch_row.event_id == "event-watch"
    assert watch_row.revision_risk_score == d("0.315000")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "dispute_window_clear",
        "evidence_reliability_watch",
        "evidence_update_present",
        "memory_update_needed",
        "near_settlement_event",
        "outcome_revision_risk_watch",
        "postmortem_impact_low",
        "revision_risk_score_watch",
    )


def test_payload_is_public_decimal_only_and_excludes_raw_surfaces() -> None:
    risk_report = report((observation(2), observation(1)))

    payload = research_outcome_revision_risk_report_payload(risk_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["observation_count"] == "2"
    assert payload["rows"][0]["evidence_reliability_score"] == "0.900000"
    assert payload["rows"][0]["revision_risk_score"] == "0.035000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    for unsafe_fragment in ("raw", "market", "source", "url", "text", "dsn", "table", "token"):
        assert unsafe_fragment not in encoded.lower()


def test_supplied_shapes_are_normalized_and_reason_counts_are_deterministic() -> None:
    risk_report = report(
        (
            SuppliedObservationShape(
                event_id="z-event",
                outcome_id="outcome-b",
                observation_id="obs-z",
                lifecycle_stage="settled",
                observed_at=GENERATED_AT - timedelta(minutes=20),
                settlement_at=GENERATED_AT - timedelta(days=2),
                expected_settlement_at=None,
                dispute_window_ends_at=GENERATED_AT - timedelta(days=1),
                reason_codes=("zeta", "alpha"),
            ),
            observation(1, event_id="a-event", outcome_id="outcome-a"),
            observation(2, event_id="a-event", outcome_id="outcome-a"),
        ),
    )

    assert tuple((row.event_id, row.outcome_id) for row in risk_report.rows) == (
        ("a-event", "outcome-a"),
        ("z-event", "outcome-b"),
    )
    assert tuple(
        (count.reason_code, count.count)
        for count in risk_report.reason_code_counts
        if count.reason_code.startswith("input_")
    ) == (("input_alpha", d("1")), ("input_zeta", d("1")))
    assert type(risk_report.reason_code_counts[0]) is ResearchOutcomeRevisionRiskReasonCodeCount


def test_validation_rejects_bad_types_unknown_enums_future_times_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="near_settlement_seconds"):
        config(near_settlement_seconds=d("0"))
    with pytest.raises(ValueError, match="min_reliability_score"):
        config(min_reliability_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_revision_risk_score"):
        config(watch_revision_risk_score=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (observation(1),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="event_id"):
        observation(1, event_id=" event-alpha")
    with pytest.raises(ValueError, match="event_id"):
        observation(1, event_id="raw-event")
    with pytest.raises(ValueError, match="lifecycle_stage"):
        observation(1, lifecycle_stage="prelaunch")
    with pytest.raises(ValueError, match="observed_at"):
        observation(1, observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((observation(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="settlement_at"):
        observation(1, settlement_at=GENERATED_AT + timedelta(seconds=1))
    with pytest.raises(ValueError, match="expected_settlement_at"):
        ResearchOutcomeRevisionRiskObservation(
            event_id="event-alpha",
            outcome_id="outcome-yes",
            observation_id="observation-missing-expected",
            lifecycle_stage="near_settlement",
            observed_at=GENERATED_AT - timedelta(hours=1),
            settlement_at=None,
            expected_settlement_at=None,
            dispute_window_ends_at=None,
        )
    with pytest.raises(ValueError, match="contradicting_evidence_update_count"):
        observation(
            1,
            evidence_update_count=d("0"),
            contradicting_evidence_update_count=d("1"),
        )
    with pytest.raises(ValueError, match="evidence_reliability_score"):
        observation(1, evidence_reliability_score=d("1.1"))
    with pytest.raises(ValueError, match="memory_update_needed"):
        replace(observation(1), memory_update_needed=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        observation(1, reason_codes=("NeedsReview",))
    with pytest.raises(ValueError, match="unsafe public value"):
        observation(1, reason_codes=("source_token",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    risk_report = report((observation(1), observation(2)))

    with pytest.raises(FrozenInstanceError):
        risk_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        risk_report.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(risk_report.rows[0], status="watch")
    with pytest.raises(ValueError, match="memory_update_needed_count"):
        replace(risk_report, memory_update_needed_count=d("1"))


def test_empty_report_blocks_without_side_effect_plan() -> None:
    risk_report = report(())

    assert risk_report.status == "block"
    assert risk_report.event_outcome_count == d("0")
    assert risk_report.observation_count == d("0")
    assert risk_report.reason_codes == ("no_outcome_revision_observations",)
    assert tuple(
        (count.reason_code, count.count) for count in risk_report.reason_code_counts
    ) == (("no_outcome_revision_observations", d("1")),)


def test_owned_module_has_no_network_database_filesystem_execution_or_advice_surface() -> None:
    module_tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(module_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(module_tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    forbidden_imports = {
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "psycopg",
        "sqlalchemy",
        "asyncpg",
    }
    forbidden_calls = {"open", "connect", "cursor", "execute", "write_text", "write_bytes"}
    forbidden_advice_terms = ("buy", "sell", "trade", "recommend", "advice")

    assert imported_roots.isdisjoint(forbidden_imports)
    for node in ast.walk(module_tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_calls
            if isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_calls

    lowered = MODULE_PATH.read_text(encoding="utf-8").lower()
    for term in forbidden_advice_terms:
        assert term not in lowered


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
