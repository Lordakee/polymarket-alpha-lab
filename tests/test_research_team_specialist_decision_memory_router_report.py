from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    "src/polymarket_alpha_lab/"
    "research_team_specialist_decision_memory_router_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def _api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_decision_memory_router_report",
    )


def _input(
    api: Any,
    specialist_label: str,
    *,
    memory_match_score: Decimal,
    decision_context_score: Decimal,
    contradiction_pressure: Decimal,
    freshness_score: Decimal,
    pending_review_load: Decimal,
    review_capacity: Decimal,
) -> Any:
    return api.ResearchTeamSpecialistDecisionMemoryRouterInput(
        specialist_label=specialist_label,
        memory_match_score=memory_match_score,
        decision_context_score=decision_context_score,
        contradiction_pressure=contradiction_pressure,
        freshness_score=freshness_score,
        pending_review_load=pending_review_load,
        review_capacity=review_capacity,
    )


def test_builds_specialist_decision_memory_router_report() -> None:
    api = _api()

    report = api.build_research_team_specialist_decision_memory_router_report(
        (
            _input(
                api,
                "macro_rates",
                memory_match_score=Decimal("0.900000"),
                decision_context_score=Decimal("0.850000"),
                contradiction_pressure=Decimal("0.100000"),
                freshness_score=Decimal("0.900000"),
                pending_review_load=Decimal("1"),
                review_capacity=Decimal("4"),
            ),
            _input(
                api,
                "crypto_flow",
                memory_match_score=Decimal("0.450000"),
                decision_context_score=Decimal("0.400000"),
                contradiction_pressure=Decimal("0.650000"),
                freshness_score=Decimal("0.450000"),
                pending_review_load=Decimal("4"),
                review_capacity=Decimal("4"),
            ),
            _input(
                api,
                "sports_injuries",
                memory_match_score=Decimal("0.650000"),
                decision_context_score=Decimal("0.650000"),
                contradiction_pressure=Decimal("0.300000"),
                freshness_score=Decimal("0.700000"),
                pending_review_load=Decimal("3"),
                review_capacity=Decimal("4"),
            ),
        ),
        config=api.ResearchTeamSpecialistDecisionMemoryRouterConfig(),
        generated_at=GENERATED_AT,
    )

    assert type(report) is api.ResearchTeamSpecialistDecisionMemoryRouterReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        api.DEFAULT_RESEARCH_TEAM_SPECIALIST_DECISION_MEMORY_ROUTER_REPORT_CONFIG_VERSION
    )
    assert report.router_status == "block"
    assert report.specialist_count == Decimal("3.000000")
    assert report.pass_specialist_count == Decimal("1.000000")
    assert report.watch_specialist_count == Decimal("1.000000")
    assert report.block_specialist_count == Decimal("1.000000")
    assert report.average_router_score == Decimal("0.593333")
    assert report.lowest_router_score == Decimal("0.330000")
    assert report.lowest_memory_match_score == Decimal("0.450000")
    assert report.lowest_decision_context_score == Decimal("0.400000")
    assert report.max_contradiction_pressure == Decimal("0.650000")
    assert report.lowest_freshness_score == Decimal("0.450000")
    assert report.max_review_load_ratio == Decimal("1.000000")
    assert report.reason_codes == (
        "team_specialist_decision_memory_router_block_specialists_present",
        "team_specialist_decision_memory_router_watch_specialists_present",
    )
    assert report.reason_code_counts == (
        api.ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount(
            reason_code=(
                "team_specialist_decision_memory_router_memory_match_block"
            ),
            count=Decimal("1.000000"),
        ),
        api.ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount(
            reason_code=(
                "team_specialist_decision_memory_router_decision_context_block"
            ),
            count=Decimal("1.000000"),
        ),
        api.ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount(
            reason_code=(
                "team_specialist_decision_memory_router_contradiction_block"
            ),
            count=Decimal("1.000000"),
        ),
        api.ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount(
            reason_code="team_specialist_decision_memory_router_freshness_block",
            count=Decimal("1.000000"),
        ),
        api.ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount(
            reason_code="team_specialist_decision_memory_router_review_load_block",
            count=Decimal("1.000000"),
        ),
        api.ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount(
            reason_code="team_specialist_decision_memory_router_memory_match_watch",
            count=Decimal("1.000000"),
        ),
        api.ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount(
            reason_code=(
                "team_specialist_decision_memory_router_decision_context_watch"
            ),
            count=Decimal("1.000000"),
        ),
        api.ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount(
            reason_code="team_specialist_decision_memory_router_review_load_watch",
            count=Decimal("1.000000"),
        ),
        api.ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount(
            reason_code="team_specialist_decision_memory_router_ready",
            count=Decimal("1.000000"),
        ),
    )
    assert tuple((row.specialist_label, row.router_status) for row in report.rows) == (
        ("crypto_flow", "block"),
        ("macro_rates", "pass"),
        ("sports_injuries", "watch"),
    )

    block_row = report.rows[0]
    assert block_row.review_load_ratio == Decimal("1.000000")
    assert block_row.router_score == Decimal("0.330000")
    assert block_row.reason_codes == (
        "team_specialist_decision_memory_router_memory_match_block",
        "team_specialist_decision_memory_router_decision_context_block",
        "team_specialist_decision_memory_router_contradiction_block",
        "team_specialist_decision_memory_router_freshness_block",
        "team_specialist_decision_memory_router_review_load_block",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_deterministic_decimal_only_digest_bound_and_public_safe() -> None:
    api = _api()
    first_inputs = (
        _input(
            api,
            "sports_injuries",
            memory_match_score=Decimal("0.650000"),
            decision_context_score=Decimal("0.650000"),
            contradiction_pressure=Decimal("0.300000"),
            freshness_score=Decimal("0.700000"),
            pending_review_load=Decimal("3"),
            review_capacity=Decimal("4"),
        ),
        _input(
            api,
            "macro_rates",
            memory_match_score=Decimal("0.900000"),
            decision_context_score=Decimal("0.850000"),
            contradiction_pressure=Decimal("0.100000"),
            freshness_score=Decimal("0.900000"),
            pending_review_load=Decimal("1"),
            review_capacity=Decimal("4"),
        ),
    )

    report = api.build_research_team_specialist_decision_memory_router_report(
        first_inputs,
        config=api.ResearchTeamSpecialistDecisionMemoryRouterConfig(),
        generated_at=GENERATED_AT,
    )
    rebuilt = api.build_research_team_specialist_decision_memory_router_report(
        tuple(reversed(first_inputs)),
        config=api.ResearchTeamSpecialistDecisionMemoryRouterConfig(),
        generated_at=GENERATED_AT,
    )

    assert rebuilt.derived_validation_digest == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)

    payload = api.research_team_specialist_decision_memory_router_report_payload(report)
    assert api.research_team_specialist_decision_memory_router_report_payload(payload) == payload
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["specialist_count"] == "2.000000"
    assert payload["average_router_score"] == "0.725000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["specialist_label"] == "macro_rates"
    assert payload["rows"][0]["pending_review_load"] == "1.000000"
    assert payload["rows"][0]["paper_only"] is True
    encoded = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "candidate_id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "recommendation",
    ):
        assert forbidden not in encoded.lower()
    _assert_no_float_values(payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, average_router_score=Decimal("0.500000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.research_team_specialist_decision_memory_router_report_payload(
            {**payload, "average_router_score": "0.500000"},
        )
    with pytest.raises(ValueError, match="readonly"):
        api.research_team_specialist_decision_memory_router_report_payload(
            {**payload, "readonly": False},
        )


def test_validates_inputs_statuses_flags_and_safe_public_labels() -> None:
    api = _api()
    report = api.build_research_team_specialist_decision_memory_router_report(
        (
            _input(
                api,
                "macro_rates",
                memory_match_score=Decimal("1"),
                decision_context_score=Decimal("1"),
                contradiction_pressure=Decimal("0"),
                freshness_score=Decimal("1"),
                pending_review_load=Decimal("0"),
                review_capacity=Decimal("1"),
            ),
        ),
        config=api.ResearchTeamSpecialistDecisionMemoryRouterConfig(),
        generated_at=datetime(2026, 7, 9, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    assert {row.router_status for row in report.rows} <= {"pass", "watch", "block"}
    with pytest.raises(FrozenInstanceError):
        report.router_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="memory_match_score must be a Decimal"):
        replace(report.rows[0], memory_match_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="pending_review_load must not exceed"):
        replace(report.rows[0], pending_review_load=Decimal("2.000000"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_research_team_specialist_decision_memory_router_report(
            (),
            config=api.ResearchTeamSpecialistDecisionMemoryRouterConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="max_watch_review_load_ratio must be a Decimal"):
        api.ResearchTeamSpecialistDecisionMemoryRouterConfig(
            max_watch_review_load_ratio=_DecimalSubclass("0.750000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(api.ResearchTeamSpecialistDecisionMemoryRouterConfig(), paper_only=False)
    with pytest.raises(ValueError, match="specialist_label must be public"):
        _input(
            api,
            "market_slug_handler",
            memory_match_score=Decimal("1"),
            decision_context_score=Decimal("1"),
            contradiction_pressure=Decimal("0"),
            freshness_score=Decimal("1"),
            pending_review_load=Decimal("0"),
            review_capacity=Decimal("1"),
        )


def test_public_contract_is_frozen_decimal_only_report_only_and_in_memory() -> None:
    api = _api()
    public_types = {
        "ResearchTeamSpecialistDecisionMemoryRouterConfig",
        "ResearchTeamSpecialistDecisionMemoryRouterInput",
        "ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount",
        "ResearchTeamSpecialistDecisionMemoryRouterReport",
        "ResearchTeamSpecialistDecisionMemoryRouterRow",
    }
    for name in public_types:
        cls = getattr(api, name)
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    report = api.build_research_team_specialist_decision_memory_router_report(
        (
            _input(
                api,
                "macro_rates",
                memory_match_score=Decimal("1"),
                decision_context_score=Decimal("1"),
                contradiction_pressure=Decimal("0"),
                freshness_score=Decimal("1"),
                pending_review_load=Decimal("0"),
                review_capacity=Decimal("1"),
            ),
        ),
        config=api.ResearchTeamSpecialistDecisionMemoryRouterConfig(),
        generated_at=GENERATED_AT,
    )
    decimal_fields = {
        "specialist_count",
        "pass_specialist_count",
        "watch_specialist_count",
        "block_specialist_count",
        "average_router_score",
        "lowest_router_score",
        "lowest_memory_match_score",
        "lowest_decision_context_score",
        "max_contradiction_pressure",
        "lowest_freshness_score",
        "max_review_load_ratio",
    }
    for field_name in decimal_fields:
        assert type(getattr(report, field_name)) is Decimal
    for row in report.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if field.name.endswith("_score") or field.name.endswith("_ratio"):
                assert type(value) is Decimal
            if field.name in {"pending_review_load", "review_capacity"}:
                assert type(value) is Decimal

    tree = ast.parse(open(MODULE_PATH, encoding="utf-8").read())
    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {"__import__", "eval", "exec", "open", "print"}
    imports: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name is not None:
                calls.add(name)
    assert not (imports & forbidden_import_roots)
    assert not (calls & forbidden_call_names)

    text = open(MODULE_PATH, encoding="utf-8").read().lower()
    for forbidden in (
        "database",
        "network",
        "wallet",
        "credential",
        "private_key",
        "secret",
        "order",
        "live",
        "trade",
        "broker",
        "buy",
        "sell",
        "request",
        "submit",
        "supabase",
        "sqlite",
        "postgres",
        "insert",
        "update",
        "delete",
        "commit",
        "cursor",
    ):
        assert forbidden not in text
    assert api.__all__ == (
        "DEFAULT_RESEARCH_TEAM_SPECIALIST_DECISION_MEMORY_ROUTER_REPORT_CONFIG_VERSION",
        "ResearchTeamSpecialistDecisionMemoryRouterConfig",
        "ResearchTeamSpecialistDecisionMemoryRouterInput",
        "ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount",
        "ResearchTeamSpecialistDecisionMemoryRouterReport",
        "ResearchTeamSpecialistDecisionMemoryRouterRow",
        "build_research_team_specialist_decision_memory_router_report",
        "research_team_specialist_decision_memory_router_report_payload",
    )


def _assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for nested_value in value.values():
            _assert_no_float_values(nested_value)
    elif isinstance(value, (list, tuple)):
        for nested_value in value:
            _assert_no_float_values(nested_value)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
