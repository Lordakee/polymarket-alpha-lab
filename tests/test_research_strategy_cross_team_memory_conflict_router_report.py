from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
DETECTED_AT = GENERATED_AT - timedelta(hours=2)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_cross_team_memory_conflict_router_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_strategy_cross_team_memory_conflict_router_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_CONFLICT_ROUTER_REPORT_CONFIG_VERSION
        ),
        "watch_disagreement_severity_score": d("0.250000"),
        "block_disagreement_severity_score": d("0.700000"),
        "watch_memory_freshness_lag_hours": d("24.000000"),
        "block_memory_freshness_lag_hours": d("72.000000"),
        "watch_unresolved_disagreement_count": d("1"),
        "block_unresolved_disagreement_count": d("3"),
        "watch_domain_overlap_score": d("0.500000"),
        "block_domain_overlap_score": d("0.850000"),
        "watch_route_priority_score": d("0.350000"),
        "block_route_priority_score": d("0.750000"),
    }
    values.update(overrides)
    return module.ResearchStrategyCrossTeamMemoryConflictRouterConfig(**values)


def conflict(**overrides: object):
    module = api()
    values = {
        "conflict_group_label": "baseline_memory",
        "primary_team_label": "macro_rates",
        "secondary_team_label": "policy_research",
        "disagreement_severity_score": d("0.100000"),
        "memory_freshness_lag_hours": d("6.000000"),
        "unresolved_disagreement_count": d("0"),
        "domain_overlap_score": d("0.100000"),
        "detected_at": DETECTED_AT,
    }
    values.update(overrides)
    return module.ResearchStrategyCrossTeamMemoryConflictInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_cross_team_memory_conflict_router_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_int_float_or_decimal_payload_values(value: Any) -> None:
    if type(value) in (int, float) or type(value) is Decimal:
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_float_or_decimal_payload_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_float_or_decimal_payload_values(item)


def payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def test_router_prioritizes_severity_freshness_and_manual_queue_status() -> None:
    result = build_report(
        conflict(
            conflict_group_label="policy_memory",
            primary_team_label="macro_rates",
            secondary_team_label="policy_research",
            disagreement_severity_score=d("0.850000"),
            memory_freshness_lag_hours=d("80.000000"),
            unresolved_disagreement_count=d("3"),
            domain_overlap_score=d("0.900000"),
        ),
        conflict(
            conflict_group_label="turnout_memory",
            primary_team_label="sports_models",
            secondary_team_label="event_research",
            disagreement_severity_score=d("0.400000"),
            memory_freshness_lag_hours=d("30.000000"),
            unresolved_disagreement_count=d("1"),
            domain_overlap_score=d("0.550000"),
        ),
        conflict(
            conflict_group_label="stable_memory",
            primary_team_label="crypto_research",
            secondary_team_label="risk_review",
        ),
    )

    assert type(result) is api().ResearchStrategyCrossTeamMemoryConflictRouterReport
    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "research-strategy-cross-team-memory-conflict-router-report-v0"
    )
    assert result.routed_conflict_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.unresolved_disagreement_total == d("4")
    assert result.freshness_stale_count == d("2")
    assert result.max_route_priority_score == d("1.000000")
    assert result.oldest_memory_freshness_lag_hours == d("80.000000")
    assert result.status == "block"
    assert result.paper_route_action == "paper_cross_team_memory_conflict_route_block"
    assert result.reason_codes == (
        "cross_team_memory_conflict_route_block",
        "disagreement_severity_block",
        "memory_freshness_block",
        "unresolved_disagreement_block",
        "domain_overlap_block",
        "route_priority_block",
        "disagreement_severity_watch",
        "memory_freshness_watch",
        "unresolved_disagreement_watch",
        "domain_overlap_watch",
        "route_priority_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64

    blocked, watched, passed = result.rows
    assert tuple(row.route_status for row in result.rows) == ("block", "watch", "pass")
    assert tuple(row.manual_queue_label for row in result.rows) == (
        "manual_research_queue_block",
        "manual_research_queue_watch",
        "manual_research_queue_monitor",
    )

    assert blocked.conflict_group_label == "policy_memory"
    assert blocked.primary_team_label == "macro_rates"
    assert blocked.secondary_team_label == "policy_research"
    assert blocked.freshness_pressure_score == d("1.000000")
    assert blocked.route_priority_score == d("1.000000")
    assert blocked.reason_codes == (
        "disagreement_severity_block",
        "memory_freshness_block",
        "unresolved_disagreement_block",
        "domain_overlap_block",
        "route_priority_block",
    )

    assert watched.route_priority_score == d("0.550000")
    assert watched.reason_codes == (
        "disagreement_severity_watch",
        "memory_freshness_watch",
        "unresolved_disagreement_watch",
        "domain_overlap_watch",
        "route_priority_watch",
    )

    assert passed.route_priority_score == d("0.100000")
    assert passed.reason_codes == ("cross_team_memory_conflict_route_clear",)

    assert result.reason_code_counts[0].reason_code == (
        "cross_team_memory_conflict_route_clear"
    )
    assert result.reason_code_counts[0].count == d("1")
    assert result.reason_code_counts[0].routed_conflict_ratio == d("0.333333")


def test_empty_router_report_is_pass_with_decimal_fields_and_hard_flags() -> None:
    result = build_report()

    assert result.routed_conflict_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.unresolved_disagreement_total == d("0")
    assert result.freshness_stale_count == d("0")
    assert result.max_route_priority_score == d("0.000000")
    assert result.oldest_memory_freshness_lag_hours == d("0.000000")
    assert result.status == "pass"
    assert result.paper_route_action == "paper_cross_team_memory_conflict_route_monitor"
    assert result.reason_codes == ("cross_team_memory_conflict_router_empty",)
    assert result.reason_code_counts == ()
    assert result.rows == ()

    populated = build_report(conflict())
    for value in (result, populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(("_count", "_total", "_score", "_hours", "_ratio")):
                assert type(item_value) is Decimal


def test_payload_is_deterministic_public_safe_decimal_only_and_digest_checked() -> None:
    module = api()
    first = build_report(
        conflict(
            conflict_group_label="policy_memory",
            primary_team_label="macro_rates",
            secondary_team_label="policy_research",
            disagreement_severity_score=d("0.850000"),
            memory_freshness_lag_hours=d("80.000000"),
            unresolved_disagreement_count=d("3"),
            domain_overlap_score=d("0.900000"),
            detected_at=datetime(
                2026,
                7,
                8,
                4,
                30,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        conflict(
            conflict_group_label="turnout_memory",
            primary_team_label="sports_models",
            secondary_team_label="event_research",
            disagreement_severity_score=d("0.400000"),
            memory_freshness_lag_hours=d("30.000000"),
            unresolved_disagreement_count=d("1"),
            domain_overlap_score=d("0.550000"),
        ),
        generated_at=datetime(2026, 7, 8, 5, tzinfo=timezone(timedelta(hours=-7))),
    )
    second = build_report(
        conflict(
            conflict_group_label="turnout_memory",
            primary_team_label="sports_models",
            secondary_team_label="event_research",
            disagreement_severity_score=d("0.400000"),
            memory_freshness_lag_hours=d("30.000000"),
            unresolved_disagreement_count=d("1"),
            domain_overlap_score=d("0.550000"),
        ),
        conflict(
            conflict_group_label="policy_memory",
            primary_team_label="macro_rates",
            secondary_team_label="policy_research",
            disagreement_severity_score=d("0.850000"),
            memory_freshness_lag_hours=d("80.000000"),
            unresolved_disagreement_count=d("3"),
            domain_overlap_score=d("0.900000"),
            detected_at=datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
        ),
    )
    changed = build_report(
        conflict(
            conflict_group_label="policy_memory",
            primary_team_label="macro_rates",
            secondary_team_label="policy_research",
            disagreement_severity_score=d("0.800000"),
            memory_freshness_lag_hours=d("80.000000"),
            unresolved_disagreement_count=d("3"),
            domain_overlap_score=d("0.900000"),
            detected_at=datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
        ),
    )

    payload = module.research_strategy_cross_team_memory_conflict_router_report_payload(
        first,
    )
    repeat_payload = (
        module.research_strategy_cross_team_memory_conflict_router_report_payload(second)
    )

    assert first.generated_at == GENERATED_AT
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.derived_validation_digest != changed.derived_validation_digest
    assert payload == repeat_payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["routed_conflict_count"] == "2"
    assert payload["rows"][0]["route_priority_score"] == "1.000000"
    assert payload["rows"][0]["detected_at"] == "2026-07-08T11:30:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_int_float_or_decimal_payload_values(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    unsafe_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "database",
        "network",
        "live",
    )
    assert not any(
        fragment in key.lower()
        for key in payload_keys(payload)
        for fragment in unsafe_fragments
    )
    payload_text = repr(payload).lower()
    assert not any(fragment in payload_text for fragment in unsafe_fragments)

    tampered = dict(payload)
    tampered["pass_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_cross_team_memory_conflict_router_report_payload(
            tampered,
        )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, pass_count=d("2"))


def test_rejects_unsafe_labels_bad_types_flags_times_and_manual_tampering() -> None:
    module = api()
    result = build_report(
        conflict(
            conflict_group_label="policy_memory",
            disagreement_severity_score=d("0.850000"),
        ),
        conflict(conflict_group_label="stable_memory", primary_team_label="risk_review"),
    )
    row = result.rows[0]
    payload = (
        module.research_strategy_cross_team_memory_conflict_router_report_payload(result)
    )

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.route_status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError):
        type("BadConfig", (module.ResearchStrategyCrossTeamMemoryConflictRouterConfig,), {})
    with pytest.raises(ValueError, match="Decimal"):
        conflict(disagreement_severity_score=0.5)
    with pytest.raises(ValueError, match="Decimal"):
        conflict(memory_freshness_lag_hours=_DecimalSubclass("30.000000"))
    with pytest.raises(ValueError, match="integral"):
        conflict(unresolved_disagreement_count=d("1.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(conflict(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="detected_at"):
        conflict(detected_at=datetime(2026, 7, 8, 11, 45))
    with pytest.raises(ValueError, match="detected_at"):
        conflict(detected_at=_DatetimeSubclass(2026, 7, 8, 11, 45, tzinfo=UTC))
    with pytest.raises(ValueError, match="future"):
        build_report(conflict(detected_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        build_report(conflict(), conflict())
    with pytest.raises(ValueError, match="conflict_group_label"):
        conflict(conflict_group_label="market_note")
    with pytest.raises(ValueError, match="primary_team_label"):
        conflict(primary_team_label="wallet_team")
    with pytest.raises(ValueError, match="paper_only"):
        conflict(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_report(conflict(), cfg=object())
    with pytest.raises(ValueError, match="route_status"):
        replace(row, route_status="pass")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, pass_count=d("2"))
    with pytest.raises(ValueError, match="rows"):
        replace(result, rows=tuple(reversed(result.rows)))

    unsafe = dict(payload)
    unsafe["source_reference"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_strategy_cross_team_memory_conflict_router_report_payload(
            unsafe,
        )

    numeric = dict(payload)
    numeric["routed_conflict_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        module.research_strategy_cross_team_memory_conflict_router_report_payload(
            numeric,
        )

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_cross_team_memory_conflict_router_report_payload(
            downgraded,
        )


def test_module_is_report_only_without_external_or_decision_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "network",
        "wallet",
        "account",
        "auth",
        "private_key",
        "api_key",
        "secret",
        "clob",
        "submit",
        "cancel",
        "signing",
        "trade",
        "trading",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "buy",
        "sell",
        "recommendation",
        "sizing",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Constant) and type(node.value) is float
        for node in ast.walk(tree)
    )
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"__import__", "float", "open", "request", "write"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in {"connect", "execute", "write", "write_text"}
