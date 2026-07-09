from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_strategy_team_decision_queue_latency_report import (
    DEFAULT_RESEARCH_STRATEGY_TEAM_DECISION_QUEUE_LATENCY_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_TEAM_DECISION_QUEUE_LATENCY_STATUSES,
    ResearchStrategyTeamDecisionQueueLatencyConfig,
    ResearchStrategyTeamDecisionQueueLatencyInput,
    ResearchStrategyTeamDecisionQueueLatencyReport,
    ResearchStrategyTeamDecisionQueueLatencyRow,
    build_research_strategy_team_decision_queue_latency_report,
    research_strategy_team_decision_queue_latency_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyTeamDecisionQueueLatencyConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_TEAM_DECISION_QUEUE_LATENCY_REPORT_CONFIG_VERSION
        ),
        "watch_latency_score_threshold": d("0.350000"),
        "block_latency_score_threshold": d("0.700000"),
        "watch_queue_age_seconds": d("1800.000000"),
        "block_queue_age_seconds": d("7200.000000"),
        "watch_assignment_lag_seconds": d("900.000000"),
        "block_assignment_lag_seconds": d("3600.000000"),
        "watch_reviewer_gap_ratio": d("0.250000"),
        "block_reviewer_gap_ratio": d("0.500000"),
        "watch_decision_sla_breach_ratio": d("0.100000"),
        "block_decision_sla_breach_ratio": d("0.300000"),
        "watch_queue_load_ratio": d("0.750000"),
        "block_queue_load_ratio": d("1.250000"),
        "watch_rework_pressure": d("0.100000"),
        "block_rework_pressure": d("0.300000"),
        "watch_escalation_pressure": d("0.300000"),
        "block_escalation_pressure": d("0.700000"),
    }
    values.update(overrides)
    return ResearchStrategyTeamDecisionQueueLatencyConfig(**values)


def queue_input(**overrides: object) -> ResearchStrategyTeamDecisionQueueLatencyInput:
    values = {
        "queue_item_ref": "queue-alpha",
        "team_key": "strategy-team-a",
        "decision_lane_key": "macro",
        "queued_at": GENERATED_AT - timedelta(seconds=600),
        "first_review_started_at": GENERATED_AT - timedelta(seconds=300),
        "required_reviewer_count": d("4.000000"),
        "available_reviewer_count": d("4.000000"),
        "open_decision_count": d("3.000000"),
        "decision_capacity_count": d("10.000000"),
        "sla_breached_count": d("0.000000"),
        "rework_count": d("0.000000"),
        "escalation_pressure": d("0.050000"),
    }
    values.update(overrides)
    return ResearchStrategyTeamDecisionQueueLatencyInput(**values)


def report(
    *rows: ResearchStrategyTeamDecisionQueueLatencyInput,
    cfg: ResearchStrategyTeamDecisionQueueLatencyConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyTeamDecisionQueueLatencyReport:
    return build_research_strategy_team_decision_queue_latency_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_report_scores_decision_queue_latency_and_rolls_up_status() -> None:
    summary = report(
        queue_input(),
        queue_input(
            queue_item_ref="queue-beta",
            team_key="strategy-team-b",
            decision_lane_key="policy",
            queued_at=GENERATED_AT - timedelta(seconds=3000),
            first_review_started_at=GENERATED_AT - timedelta(seconds=1800),
            required_reviewer_count=d("10.000000"),
            available_reviewer_count=d("7.000000"),
            open_decision_count=d("8.000000"),
            decision_capacity_count=d("10.000000"),
            sla_breached_count=d("1.000000"),
            rework_count=d("1.000000"),
            escalation_pressure=d("0.400000"),
        ),
        queue_input(
            queue_item_ref="queue-gamma",
            team_key="strategy-team-c",
            decision_lane_key="macro",
            queued_at=GENERATED_AT - timedelta(seconds=9000),
            first_review_started_at=GENERATED_AT - timedelta(seconds=5000),
            required_reviewer_count=d("10.000000"),
            available_reviewer_count=d("4.000000"),
            open_decision_count=d("15.000000"),
            decision_capacity_count=d("10.000000"),
            sla_breached_count=d("6.000000"),
            rework_count=d("5.000000"),
            escalation_pressure=d("0.800000"),
        ),
    )

    assert summary.generated_at == GENERATED_AT
    assert (
        summary.config_version
        == DEFAULT_RESEARCH_STRATEGY_TEAM_DECISION_QUEUE_LATENCY_REPORT_CONFIG_VERSION
    )
    assert summary.queue_item_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.total_open_decisions == d("26.000000")
    assert summary.average_queue_age_seconds == d("4200.000000")
    assert summary.average_assignment_lag_seconds == d("1833.333333")
    assert summary.average_queue_load_ratio == d("0.866667")
    assert summary.average_latency_score == d("0.482011")
    assert summary.max_latency_score == d("0.936667")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "decision_queue_latency_report_block_rows",
        "decision_queue_latency_report_watch_rows",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyTeamDecisionQueueLatencyRow)
    assert len(blocked.queue_item_hash) == 64
    assert blocked.queue_age_seconds == d("9000.000000")
    assert blocked.assignment_lag_seconds == d("4000.000000")
    assert blocked.reviewer_gap_ratio == d("0.600000")
    assert blocked.queue_load_ratio == d("1.500000")
    assert blocked.queue_load_pressure == d("1.000000")
    assert blocked.sla_breach_ratio == d("0.400000")
    assert blocked.rework_pressure == d("0.333333")
    assert blocked.latency_score == d("0.936667")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "queue_age_block",
        "assignment_lag_block",
        "reviewer_gap_block",
        "decision_sla_breach_block",
        "queue_load_block",
        "rework_pressure_block",
        "escalation_pressure_block",
        "latency_score_block",
    )

    watched = summary.rows[1]
    assert watched.queue_age_pressure == d("0.416667")
    assert watched.assignment_lag_pressure == d("0.333333")
    assert watched.reviewer_gap_pressure == d("0.600000")
    assert watched.queue_load_pressure == d("0.640000")
    assert watched.latency_score == d("0.439933")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "queue_age_watch",
        "assignment_lag_watch",
        "reviewer_gap_watch",
        "decision_sla_breach_watch",
        "queue_load_watch",
        "rework_pressure_watch",
        "escalation_pressure_watch",
        "latency_score_watch",
    )

    passed = summary.rows[2]
    assert passed.queue_age_pressure == d("0.083333")
    assert passed.assignment_lag_pressure == d("0.083333")
    assert passed.reviewer_gap_ratio == d("0.000000")
    assert passed.latency_score == d("0.069433")
    assert passed.status == "pass"
    assert passed.reason_codes == ("decision_queue_latency_pass",)
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True
    assert len(passed.derived_validation_digest) == 64
    assert len(summary.derived_validation_digest) == 64


def test_public_payload_is_deterministic_hashed_decimal_and_digest_guarded() -> None:
    sensitive_ref = (
        "candidate-alpha market-alpha will resolve "
        "https://private.example/path?api_key=hidden-token table=db.events"
    )
    first_payload = research_strategy_team_decision_queue_latency_report_payload(
        report(queue_input(queue_item_ref=sensitive_ref)),
    )
    second_payload = research_strategy_team_decision_queue_latency_report_payload(
        report(queue_input(queue_item_ref=sensitive_ref)),
    )
    encoded = json.dumps(first_payload, sort_keys=True).lower()

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["queue_item_count"] == "1.000000"
    assert first_payload["rows"][0]["queue_item_hash"] == hashlib.sha256(
        sensitive_ref.encode("utf-8"),
    ).hexdigest()
    assert first_payload["rows"][0]["latency_score"] == "0.069433"
    assert "queue_item_ref" not in first_payload["rows"][0]
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert first_payload["derived_validation_digest"] == _payload_digest(first_payload)
    assert_no_decimal_or_raw_numeric_values(first_payload)

    forbidden_payload_fragments = (
        "candidate-alpha",
        "market-alpha",
        "will resolve",
        "https://",
        "private.example",
        "api_key",
        "hidden-token",
        "table=",
        "db.events",
        "queue_item_ref",
    )
    assert all(fragment not in encoded for fragment in forbidden_payload_fragments)

    tampered_payload = json.loads(json.dumps(first_payload))
    tampered_payload["rows"][0]["latency_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_team_decision_queue_latency_report_payload(tampered_payload)

    numeric_payload = json.loads(json.dumps(first_payload))
    numeric_payload["queue_item_count"] = 1
    with pytest.raises(ValueError, match="queue_item_count"):
        research_strategy_team_decision_queue_latency_report_payload(numeric_payload)

    unsafe_payload = json.loads(json.dumps(first_payload))
    unsafe_payload["candidate_id"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_team_decision_queue_latency_report_payload(unsafe_payload)

    unsafe_nested_payload = json.loads(json.dumps(first_payload))
    unsafe_nested_payload["rows"][0]["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_strategy_team_decision_queue_latency_report_payload(unsafe_nested_payload)


def test_public_payload_rejects_signed_schema_downgrades() -> None:
    public_payload = research_strategy_team_decision_queue_latency_report_payload(
        report(queue_input()),
    )

    minimal_payload: dict[str, object] = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    minimal_payload["derived_validation_digest"] = _payload_digest(minimal_payload)
    with pytest.raises(ValueError, match="payload"):
        research_strategy_team_decision_queue_latency_report_payload(minimal_payload)

    unknown_payload = json.loads(json.dumps(public_payload))
    unknown_payload["id"] = "opaque-private-ref"
    unknown_payload["derived_validation_digest"] = _payload_digest(unknown_payload)
    with pytest.raises(ValueError, match="payload"):
        research_strategy_team_decision_queue_latency_report_payload(unknown_payload)

    bad_report_status_payload = json.loads(json.dumps(public_payload))
    bad_report_status_payload["status"] = "pending"
    bad_report_status_payload["derived_validation_digest"] = _payload_digest(
        bad_report_status_payload,
    )
    with pytest.raises(ValueError, match="status"):
        research_strategy_team_decision_queue_latency_report_payload(
            bad_report_status_payload,
        )

    bad_row_status_payload = json.loads(json.dumps(public_payload))
    bad_row_status_payload["rows"][0]["status"] = "pending"
    bad_row_status_payload["rows"][0]["derived_validation_digest"] = _payload_digest(
        bad_row_status_payload["rows"][0],
    )
    bad_row_status_payload["derived_validation_digest"] = _payload_digest(
        bad_row_status_payload,
    )
    with pytest.raises(ValueError, match="status"):
        research_strategy_team_decision_queue_latency_report_payload(
            bad_row_status_payload,
        )

    bad_reason_payload = json.loads(json.dumps(public_payload))
    bad_reason_payload["reason_codes"] = ["unknown_reason"]
    bad_reason_payload["derived_validation_digest"] = _payload_digest(bad_reason_payload)
    with pytest.raises(ValueError, match="reason_codes"):
        research_strategy_team_decision_queue_latency_report_payload(bad_reason_payload)


def test_validation_rejects_non_decimal_times_duplicates_flags_and_tampering() -> None:
    with pytest.raises(ValueError, match="required_reviewer_count"):
        queue_input(required_reviewer_count=4)
    with pytest.raises(ValueError, match="escalation_pressure"):
        queue_input(escalation_pressure=d("1.1"))
    with pytest.raises(ValueError, match="queued_at"):
        queue_input(queued_at=datetime(2026, 7, 8, 11, 50))
    with pytest.raises(ValueError, match="generated_at"):
        report(queue_input(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="queued_at"):
        report(queue_input(queued_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate"):
        report(queue_input(queue_item_ref="same"), queue_input(queue_item_ref="same"))
    with pytest.raises(ValueError, match="watch_latency_score_threshold"):
        config(watch_latency_score_threshold=d("0.800000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="block_queue_age_seconds"):
        config(block_queue_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            queue_input(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="team_key"):
        queue_input(team_key="execution")

    summary = report(queue_input())
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary.rows[0],
            latency_score=d("0.500000"),
            derived_validation_digest=summary.rows[0].derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            queue_item_count=d("0.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )


def test_public_dataclasses_are_frozen_and_module_has_no_forbidden_surfaces() -> None:
    summary = report(queue_input())
    row = summary.rows[0]

    assert is_dataclass(ResearchStrategyTeamDecisionQueueLatencyConfig)
    assert is_dataclass(ResearchStrategyTeamDecisionQueueLatencyInput)
    assert is_dataclass(ResearchStrategyTeamDecisionQueueLatencyRow)
    assert is_dataclass(ResearchStrategyTeamDecisionQueueLatencyReport)
    assert RESEARCH_STRATEGY_TEAM_DECISION_QUEUE_LATENCY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary, report_only=False)

    source = Path(
        "src/polymarket_alpha_lab/research_strategy_team_decision_queue_latency_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "wallet",
        "broker",
        "private_key",
        "investment_advice",
        "execution",
        "live_trading",
        "buy",
        "sell",
        "sizing",
        "recommendation",
        "requests.",
        "urllib",
        "sqlite",
        "sqlalchemy",
        "open(",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "api_key",
    ):
        assert forbidden not in lowered
    assert not re.search(
        r"\b(auth|wallet|broker|order|trade|live|buy|sell|sizing|execution)\b",
        lowered,
    )

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"

    assert summary.__class__.__module__.endswith(
        "research_strategy_team_decision_queue_latency_report",
    )


def _payload_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def assert_no_decimal_or_raw_numeric_values(value: object) -> None:
    if type(value) is bool or value is None:
        return
    assert not isinstance(value, Decimal)
    assert type(value) is not int
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_or_raw_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_decimal_or_raw_numeric_values(item)
