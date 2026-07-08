from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_team_resolution_feedback_backlog_report import (
    STATUSES,
    ResearchTeamResolutionFeedbackBacklogConfig,
    ResearchTeamResolutionFeedbackBacklogInput,
    ResearchTeamResolutionFeedbackBacklogReasonCodeCount,
    ResearchTeamResolutionFeedbackBacklogReport,
    ResearchTeamResolutionFeedbackBacklogRow,
    build_research_team_resolution_feedback_backlog_report,
    research_team_resolution_feedback_backlog_report_payload,
    validate_research_team_resolution_feedback_backlog_public_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_resolution_feedback_backlog_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchTeamResolutionFeedbackBacklogConfig:
    values: dict[str, object] = {
        "watch_calibration_writeback_age_seconds": d("3600.000000"),
        "block_calibration_writeback_age_seconds": d("86400.000000"),
        "stale_feedback_age_seconds": d("86400.000000"),
        "watch_stale_feedback_pressure": d("0.350000"),
        "block_stale_feedback_pressure": d("0.700000"),
        "watch_manual_escalation_urgency": d("0.500000"),
        "block_manual_escalation_urgency": d("0.900000"),
    }
    values.update(overrides)
    return ResearchTeamResolutionFeedbackBacklogConfig(**values)


def feedback_input(
    feedback_key: str = "feedback-a",
    *,
    team_key: str = "research-core",
    domain_key: str = "rates",
    unresolved_outcome_feedback: bool = False,
    calibration_writeback_age_seconds: Decimal = d("600.000000"),
    feedback_age_seconds: Decimal = d("1800.000000"),
    feedback_priority: Decimal = d("0.100000"),
    manual_escalation_requested: bool = False,
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamResolutionFeedbackBacklogInput:
    return ResearchTeamResolutionFeedbackBacklogInput(
        feedback_key=feedback_key,
        team_key=team_key,
        domain_key=domain_key,
        unresolved_outcome_feedback=unresolved_outcome_feedback,
        calibration_writeback_age_seconds=calibration_writeback_age_seconds,
        feedback_age_seconds=feedback_age_seconds,
        feedback_priority=feedback_priority,
        manual_escalation_requested=manual_escalation_requested,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    *items: ResearchTeamResolutionFeedbackBacklogInput,
    cfg: ResearchTeamResolutionFeedbackBacklogConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamResolutionFeedbackBacklogReport:
    return build_research_team_resolution_feedback_backlog_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def _walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for key, item in value.items():
            values.append(key)
            values.extend(_walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_payload_values(item))
        return tuple(values)
    return (value,)


def test_empty_input_returns_pass_report_with_hard_readonly_flags() -> None:
    report = build_report()

    assert type(report) is ResearchTeamResolutionFeedbackBacklogReport
    assert STATUSES == ("pass", "watch", "block")
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.feedback_count == d("0.000000")
    assert report.unresolved_outcome_feedback_count == d("0.000000")
    assert report.impacted_domain_count == d("0.000000")
    assert report.max_calibration_writeback_age_seconds == d("0.000000")
    assert report.stale_feedback_pressure == d("0.000000")
    assert report.manual_escalation_urgency == d("0.000000")
    assert report.reason_codes == ("resolution_feedback_backlog_empty",)
    assert report.reason_code_counts == (
        ResearchTeamResolutionFeedbackBacklogReasonCodeCount(
            reason_code="resolution_feedback_backlog_empty",
            count=d("1.000000"),
        ),
    )
    assert report.rows == ()
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_report_aggregates_resolution_feedback_backlog_pressure_and_urgency() -> None:
    report = build_report(
        feedback_input("feedback-a"),
        feedback_input(
            "feedback-b",
            domain_key="courts",
            unresolved_outcome_feedback=True,
            calibration_writeback_age_seconds=d("7200.000000"),
            feedback_age_seconds=d("43200.000000"),
            feedback_priority=d("0.400000"),
            reason_codes=("needs_team_writeback",),
        ),
        feedback_input(
            "feedback-c",
            domain_key="rates",
            unresolved_outcome_feedback=True,
            calibration_writeback_age_seconds=d("200000.000000"),
            feedback_age_seconds=d("172800.000000"),
            feedback_priority=d("0.900000"),
            manual_escalation_requested=True,
            reason_codes=("manual_review_requested",),
        ),
    )

    assert report.status == "block"
    assert report.feedback_count == d("3.000000")
    assert report.unresolved_outcome_feedback_count == d("2.000000")
    assert report.impacted_domain_count == d("2.000000")
    assert report.max_calibration_writeback_age_seconds == d("200000.000000")
    assert report.stale_feedback_pressure == d("0.950000")
    assert report.manual_escalation_urgency == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.reason_codes == (
        "resolution_feedback_backlog_block",
        "calibration_writeback_age_block",
        "manual_escalation_urgency_block",
        "stale_feedback_pressure_block",
        "calibration_writeback_age_watch",
        "stale_feedback_pressure_watch",
        "input_manual_review_requested",
        "input_needs_team_writeback",
    )

    pass_row, watch_row, block_row = report.rows
    assert tuple(row.feedback_key for row in report.rows) == (
        "feedback-a",
        "feedback-b",
        "feedback-c",
    )
    assert type(block_row) is ResearchTeamResolutionFeedbackBacklogRow
    assert pass_row.status == "pass"
    assert pass_row.stale_feedback_pressure == d("0.060417")
    assert pass_row.manual_escalation_urgency == d("0.100000")
    assert watch_row.status == "watch"
    assert watch_row.feedback_age_pressure == d("0.500000")
    assert watch_row.stale_feedback_pressure == d("0.450000")
    assert watch_row.manual_escalation_urgency == d("0.450000")
    assert block_row.status == "block"
    assert block_row.calibration_writeback_age_pressure == d("1.000000")
    assert block_row.feedback_age_pressure == d("1.000000")
    assert block_row.stale_feedback_pressure == d("0.950000")
    assert block_row.manual_escalation_urgency == d("1.000000")
    assert ResearchTeamResolutionFeedbackBacklogReasonCodeCount(
        reason_code="stale_feedback_pressure_block",
        count=d("1.000000"),
    ) in report.reason_code_counts


def test_payload_is_deterministic_digest_validated_and_public_safe() -> None:
    inputs = (
        feedback_input(
            "feedback-b",
            domain_key="courts",
            unresolved_outcome_feedback=True,
            calibration_writeback_age_seconds=d("7200.000000"),
            feedback_age_seconds=d("43200.000000"),
            feedback_priority=d("0.400000"),
            reason_codes=("needs_team_writeback",),
        ),
        feedback_input("feedback-a"),
    )

    first_report = build_report(*inputs)
    second_report = build_report(*tuple(reversed(inputs)))
    first_payload = research_team_resolution_feedback_backlog_report_payload(first_report)
    second_payload = research_team_resolution_feedback_backlog_report_payload(second_report)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["unresolved_outcome_feedback_count"] == "1.000000"
    assert first_payload["rows"][1]["stale_feedback_pressure"] == "0.450000"
    assert validate_research_team_resolution_feedback_backlog_public_payload(first_payload)
    assert not any(type(value) in (int, float, Decimal) for value in _walk_payload_values(first_payload))
    assert all(
        fragment not in encoded.lower()
        for fragment in (
            "candidate",
            "market_id",
            "market_slug",
            "slug",
            "question",
            "source_url",
            "source_text",
            "http",
            "dsn",
            "table",
            "private",
            "token",
        )
    )

    tampered_payload = dict(first_payload)
    tampered_payload["unresolved_outcome_feedback_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_team_resolution_feedback_backlog_public_payload(tampered_payload)


def test_validation_rejects_non_decimal_unsafe_values_mutation_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="watch_calibration_writeback_age_seconds"):
        config(watch_calibration_writeback_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_stale_feedback_pressure"):
        config(block_stale_feedback_pressure=d("0.300000"))
    with pytest.raises(ValueError, match="feedback_priority"):
        feedback_input(feedback_priority=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(feedback_input(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            feedback_input(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="feedback_key"):
        feedback_input(feedback_key="candidate-raw-123")
    with pytest.raises(ValueError, match="domain_key"):
        feedback_input(domain_key="market_slug")
    with pytest.raises(ValueError, match="team_key"):
        feedback_input(team_key="source-url")
    with pytest.raises(ValueError, match="readonly"):
        feedback_input(readonly=False)

    report = build_report(feedback_input())
    with pytest.raises(FrozenInstanceError):
        report.status = "block"  # type: ignore[misc]


def test_module_has_no_db_network_wallet_order_or_recommendation_surfaces() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    forbidden_imports = {
        "os",
        "socket",
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "web3",
    }
    function_names = {
        node.name.lower()
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    assert imports.isdisjoint(forbidden_imports)
    assert not any(
        fragment in function_name
        for function_name in function_names
        for fragment in ("wallet", "auth", "order", "trade", "sizing", "recommend")
    )
