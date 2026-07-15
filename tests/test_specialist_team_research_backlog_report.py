from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_research_backlog_report.py"
)
GENERATED_AT = datetime(2026, 7, 12, 10, 15, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_research_backlog_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def team(**overrides: object):
    module = api()
    values = {
        "team_code": "team_macro",
        "candidate_count": d("10.000000"),
        "blocked_count": d("1.000000"),
        "attention_count": d("2.000000"),
        "ready_count": d("7.000000"),
        "avg_source_age_seconds": d("1800.000000"),
        "avg_edge_to_threshold_probability": d("0.650000"),
        "memory_learning_priority_score": d("0.700000"),
    }
    values.update(overrides)
    return module.SpecialistTeamResearchBacklogInput(**values)


def report(*teams: object):
    module = api()
    return module.build_specialist_team_research_backlog_report(
        teams,
        config=module.SpecialistTeamResearchBacklogConfig(),
        generated_at=GENERATED_AT,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_int_values(child)
    if isinstance(value, list):
        for child in value:
            assert_no_float_or_int_values(child)


def reason_count(reason_code: str, count: Decimal):
    module = api()
    return module.SpecialistTeamResearchBacklogReasonCodeCount(
        reason_code=reason_code,
        count=count,
    )


def test_builds_sorted_readonly_backlog_report_with_reason_codes() -> None:
    module = api()
    rows = (
        team(
            team_code="team_ready",
            candidate_count=d("12.000000"),
            blocked_count=d("0.000000"),
            attention_count=d("1.000000"),
            ready_count=d("11.000000"),
            avg_source_age_seconds=d("900.000000"),
            avg_edge_to_threshold_probability=d("0.850000"),
            memory_learning_priority_score=d("0.800000"),
        ),
        team(
            team_code="team_attention",
            candidate_count=d("8.000000"),
            blocked_count=d("1.000000"),
            attention_count=d("4.000000"),
            ready_count=d("3.000000"),
            avg_source_age_seconds=d("10800.000000"),
            avg_edge_to_threshold_probability=d("0.450000"),
            memory_learning_priority_score=d("0.900000"),
        ),
        team(
            team_code="team_blocked",
            candidate_count=d("6.000000"),
            blocked_count=d("4.000000"),
            attention_count=d("1.000000"),
            ready_count=d("1.000000"),
            avg_source_age_seconds=d("90000.000000"),
            avg_edge_to_threshold_probability=d("0.250000"),
            memory_learning_priority_score=d("0.500000"),
        ),
    )

    result = report(*reversed(rows))

    assert is_dataclass(result)
    assert module.SPECIALIST_TEAM_RESEARCH_BACKLOG_PRIORITY_BANDS == (
        "critical",
        "high",
        "watch",
        "ready",
    )
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "specialist-team-research-backlog-report-v1"
    assert result.report_status == "block"
    assert result.team_count == d("3.000000")
    assert result.candidate_count == d("26.000000")
    assert result.blocked_count == d("5.000000")
    assert result.attention_count == d("6.000000")
    assert result.ready_count == d("15.000000")
    assert result.average_backlog_priority_score == d("0.456994")
    assert result.max_backlog_priority_score == d("0.790667")
    assert result.next_review_topic_count == d("16.000000")
    assert result.reason_codes == (
        "specialist_team_research_backlog_block",
        "critical_backlog_present",
        "high_backlog_present",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert [(row.priority_rank, row.team_code) for row in result.rows] == [
        (d("1.000000"), "team_blocked"),
        (d("2.000000"), "team_attention"),
        (d("3.000000"), "team_ready"),
    ]
    assert [row.backlog_priority_score for row in result.rows] == [
        d("0.790667"),
        d("0.447792"),
        d("0.132524"),
    ]
    assert [row.priority_band for row in result.rows] == [
        "critical",
        "high",
        "ready",
    ]
    assert [row.next_review_topic_count for row in result.rows] == [
        d("6.000000"),
        d("7.000000"),
        d("3.000000"),
    ]
    assert result.rows[0].top_reason_codes == (
        "blocked_ratio_critical",
        "source_age_critical",
        "edge_probability_low",
    )
    assert result.rows[1].top_reason_codes == (
        "attention_ratio_high",
        "source_age_high",
        "edge_probability_watch",
    )
    assert result.rows[2].top_reason_codes == ("backlog_ready",)
    assert result.reason_code_counts == (
        reason_count("blocked_ratio_critical", d("1.000000")),
        reason_count("source_age_critical", d("1.000000")),
        reason_count("edge_probability_low", d("1.000000")),
        reason_count("attention_ratio_high", d("1.000000")),
        reason_count("source_age_high", d("1.000000")),
        reason_count("edge_probability_watch", d("1.000000")),
        reason_count("backlog_ready", d("1.000000")),
    )


def test_payload_is_deterministic_decimal_stringed_and_report_only() -> None:
    module = api()
    first = report(
        team(team_code="team_ready"),
        team(
            team_code="team_attention",
            candidate_count=d("8.000000"),
            blocked_count=d("1.000000"),
            attention_count=d("4.000000"),
            ready_count=d("3.000000"),
            avg_source_age_seconds=d("10800.000000"),
            avg_edge_to_threshold_probability=d("0.450000"),
            memory_learning_priority_score=d("0.900000"),
        ),
    )
    second = report(*reversed(first.inputs))

    first_payload = module.specialist_team_research_backlog_report_payload(first)
    second_payload = module.specialist_team_research_backlog_report_payload(second)

    assert first_payload == first.payload
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True, separators=(",", ":")) == json.dumps(
        second_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert first_payload["team_count"] == "2.000000"
    assert first_payload["rows"][0]["backlog_priority_score"] == "0.447792"
    assert first_payload["rows"][0]["priority_band"] == "high"
    assert first_payload["validation_digest"] == first.validation_digest
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert_no_float_or_int_values(first_payload)
    assert module.validate_specialist_team_research_backlog_report_payload(first_payload)


def test_validation_requires_frozen_decimal_only_public_codes_and_hard_flags() -> None:
    module = api()
    result = report(team())

    with pytest.raises(FrozenInstanceError):
        result.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="candidate_count must be a Decimal"):
        team(candidate_count=10)

    with pytest.raises(ValueError, match="blocked_count must be a Decimal"):
        team(blocked_count=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="ready_count cannot exceed candidate_count"):
        team(candidate_count=d("2.000000"), ready_count=d("3.000000"))

    with pytest.raises(ValueError, match="candidate component counts cannot exceed candidate_count"):
        team(
            candidate_count=d("2.000000"),
            blocked_count=d("1.000000"),
            attention_count=d("1.000000"),
            ready_count=d("1.000000"),
        )

    with pytest.raises(ValueError, match="avg_edge_to_threshold_probability must be between 0 and 1"):
        team(avg_edge_to_threshold_probability=d("1.000001"))

    with pytest.raises(ValueError, match="team_code must be a public code"):
        team(team_code="Team Macro")

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(team(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="priority_band must be supported"):
        module.SpecialistTeamResearchBacklogRow(
            priority_rank=d("1.000000"),
            team_code="team_macro",
            candidate_count=d("10.000000"),
            blocked_count=d("1.000000"),
            attention_count=d("2.000000"),
            ready_count=d("7.000000"),
            avg_source_age_seconds=d("1800.000000"),
            avg_edge_to_threshold_probability=d("0.650000"),
            memory_learning_priority_score=d("0.700000"),
            blocked_ratio=d("0.100000"),
            attention_ratio=d("0.200000"),
            ready_ratio=d("0.700000"),
            source_age_pressure=d("0.020833"),
            backlog_priority_score=d("0.250000"),
            priority_band="trade",
            next_review_topic_count=d("3.000000"),
            top_reason_codes=("backlog_ready",),
        )


def test_public_numeric_fields_are_decimal_only_and_payload_rejects_tampering() -> None:
    module = api()
    decimal_fields = {
        "critical_priority_score",
        "high_priority_score",
        "watch_priority_score",
        "source_age_pressure_seconds",
        "source_age_high_seconds",
        "source_age_critical_seconds",
        "blocked_ratio_high",
        "blocked_ratio_critical",
        "attention_ratio_watch",
        "attention_ratio_high",
        "edge_probability_watch",
        "edge_probability_low",
        "candidate_count",
        "blocked_count",
        "attention_count",
        "ready_count",
        "avg_source_age_seconds",
        "avg_edge_to_threshold_probability",
        "memory_learning_priority_score",
        "priority_rank",
        "blocked_ratio",
        "attention_ratio",
        "ready_ratio",
        "source_age_pressure",
        "backlog_priority_score",
        "next_review_topic_count",
        "team_count",
        "average_backlog_priority_score",
        "max_backlog_priority_score",
        "count",
    }

    for cls in (
        module.SpecialistTeamResearchBacklogConfig,
        module.SpecialistTeamResearchBacklogInput,
        module.SpecialistTeamResearchBacklogRow,
        module.SpecialistTeamResearchBacklogReasonCodeCount,
        module.SpecialistTeamResearchBacklogReport,
    ):
        for item in fields(cls):
            if item.name in decimal_fields:
                assert get_type_hints(cls)[item.name] is Decimal

    payload = module.specialist_team_research_backlog_report_payload(report(team()))
    assert module.specialist_team_research_backlog_report_payload(payload) == payload

    tampered = dict(payload)
    tampered["team_count"] = "2.000000"
    with pytest.raises(ValueError, match="validation_digest|team_count"):
        module.specialist_team_research_backlog_report_payload(tampered)

    with pytest.raises(ValueError, match="Decimal"):
        numeric_payload = dict(payload)
        numeric_payload["team_count"] = 1
        module.specialist_team_research_backlog_report_payload(numeric_payload)

    with pytest.raises(ValueError, match="paper_only"):
        flag_payload = dict(payload)
        flag_payload["paper_only"] = False
        module.specialist_team_research_backlog_report_payload(flag_payload)


def test_empty_report_is_readonly_pass_with_decimal_zero_counts() -> None:
    empty = report()

    assert empty.team_count == d("0.000000")
    assert empty.candidate_count == d("0.000000")
    assert empty.blocked_count == d("0.000000")
    assert empty.attention_count == d("0.000000")
    assert empty.ready_count == d("0.000000")
    assert empty.average_backlog_priority_score == d("0.000000")
    assert empty.max_backlog_priority_score == d("0.000000")
    assert empty.next_review_topic_count == d("0.000000")
    assert empty.report_status == "pass"
    assert empty.reason_codes == ("specialist_team_research_backlog_clear",)
    assert empty.rows == ()
    assert empty.reason_code_counts == (
        reason_count("specialist_team_research_backlog_clear", d("1.000000")),
    )
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_module_surface_is_pure_readonly_report_without_io_or_trading_terms() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "requests",
        "urllib",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_client",
        "insert",
        "update",
        "delete",
        "execute",
    }
    forbidden_text = (
        "wallet",
        "auth",
        "private_key",
        "live trading",
        "place_order",
        "database",
        "network",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            if isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names

    lowered = source.lower()
    for token in forbidden_text:
        assert token not in lowered
