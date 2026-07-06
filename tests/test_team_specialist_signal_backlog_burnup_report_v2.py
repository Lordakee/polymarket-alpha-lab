from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_signal_backlog_burnup_report_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_signal_backlog_burnup_report_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def snapshot(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "team_id": "alpha_specialists",
        "snapshot_id": "alpha_backlog_20260706",
        "captured_at": GENERATED_AT,
        "completed_signal_count": d("10"),
        "carried_signal_count": d("0"),
        "escalated_signal_count": d("0"),
        "available_capacity_units": d("20"),
    }
    values.update(overrides)
    return module.TeamSpecialistSignalBacklogBurnupV2Input(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            snapshot(
                team_id="alpha_specialists",
                snapshot_id="alpha_backlog_20260706",
                completed_signal_count=d("10"),
                carried_signal_count=d("0"),
                escalated_signal_count=d("0"),
                available_capacity_units=d("20"),
            ),
            snapshot(
                team_id="beta_specialists",
                snapshot_id="beta_backlog_20260706",
                completed_signal_count=d("6"),
                carried_signal_count=d("3"),
                escalated_signal_count=d("1"),
                available_capacity_units=d("12"),
            ),
            snapshot(
                team_id="gamma_specialists",
                snapshot_id="gamma_backlog_20260706",
                completed_signal_count=d("2"),
                carried_signal_count=d("3"),
                escalated_signal_count=d("5"),
                available_capacity_units=d("8"),
            ),
        )
    return module.build_team_specialist_signal_backlog_burnup_report_v2(
        items,
        config=config,
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (float, int)):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_or_int_values(item)


def test_backlog_burnup_scoring_and_team_capacity_pressure() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.report_status == "blocked"
    assert report.team_count == d("3")
    assert report.pass_team_count == d("1")
    assert report.watch_team_count == d("1")
    assert report.blocked_team_count == d("1")
    assert report.average_backlog_burnup_score == d("0.526667")
    assert report.top_capacity_pressure_ratio == d("1.000000")
    assert report.top_escalation_priority_score == d("0.710000")
    assert report.reason_codes == (
        "signal_backlog_burnup_blocked_rows",
        "signal_backlog_burnup_watch_rows",
    )

    rows = report.rows
    assert tuple(row.team_id for row in rows) == (
        "gamma_specialists",
        "beta_specialists",
        "alpha_specialists",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.scope_signal_count for row in rows) == (d("10"), d("10"), d("10"))
    assert tuple(row.burnup_completion_ratio for row in rows) == (
        d("0.200000"),
        d("0.600000"),
        d("1.000000"),
    )
    assert tuple(row.capacity_pressure_ratio for row in rows) == (
        d("1.000000"),
        d("0.833333"),
        d("0.500000"),
    )
    assert tuple(row.escalation_ratio for row in rows) == (
        d("0.500000"),
        d("0.100000"),
        d("0.000000"),
    )
    assert tuple(row.backlog_burnup_score for row in rows) == (
        d("0.200000"),
        d("0.530000"),
        d("0.850000"),
    )
    assert tuple(row.escalation_priority_score for row in rows) == (
        d("0.710000"),
        d("0.380000"),
        d("0.150000"),
    )
    assert tuple(row.capacity_pressure_status for row in rows) == (
        "blocked",
        "watch",
        "pass",
    )
    assert tuple(row.report_status for row in rows) == ("blocked", "watch", "pass")


def test_escalation_priority_sorts_rows_and_handles_empty_scope() -> None:
    report = build_report(
        snapshot(
            team_id="empty_specialists",
            snapshot_id="empty_backlog_20260706",
            completed_signal_count=d("0"),
            carried_signal_count=d("0"),
            escalated_signal_count=d("0"),
            available_capacity_units=d("0"),
        ),
        snapshot(
            team_id="loaded_specialists",
            snapshot_id="loaded_backlog_20260706",
            completed_signal_count=d("1"),
            carried_signal_count=d("1"),
            escalated_signal_count=d("2"),
            available_capacity_units=d("2"),
        ),
    )

    assert tuple(row.team_id for row in report.rows) == (
        "loaded_specialists",
        "empty_specialists",
    )
    loaded, empty = report.rows
    assert loaded.escalation_priority_score == d("0.700000")
    assert loaded.report_status == "blocked"
    assert empty.scope_signal_count == d("0")
    assert empty.burnup_completion_ratio == d("1.000000")
    assert empty.capacity_pressure_ratio == d("0.000000")
    assert empty.escalation_priority_score == d("0.000000")
    assert empty.report_status == "pass"


def test_serialization_uses_decimal_strings_flags_and_digest() -> None:
    module = api()
    report = build_report()
    payload = module.team_specialist_signal_backlog_burnup_report_v2_payload(report)

    assert payload == report.payload
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["team_count"] == "3"
    assert payload["average_backlog_burnup_score"] == "0.526667"
    assert payload["top_capacity_pressure_ratio"] == "1.000000"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["escalation_priority_score"] == "0.710000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    dict_payload = dict(payload)
    assert module.team_specialist_signal_backlog_burnup_report_v2_payload(
        dict_payload,
    ) == payload


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistSignalBacklogBurnupReportV2Config()
    sample = snapshot()
    report = build_report(sample)
    row = report.rows[0]

    for item in (config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {
                "completion_weight",
                "capacity_pressure_weight",
                "escalation_weight",
                "capacity_pressure_watch_floor",
                "capacity_pressure_blocked_floor",
                "escalation_priority_watch_floor",
                "escalation_priority_blocked_floor",
                "completed_signal_count",
                "carried_signal_count",
                "escalated_signal_count",
                "available_capacity_units",
                "rank",
                "scope_signal_count",
                "burnup_completion_ratio",
                "capacity_pressure_ratio",
                "escalation_ratio",
                "backlog_burnup_score",
                "escalation_priority_score",
                "team_count",
                "pass_team_count",
                "watch_team_count",
                "blocked_team_count",
                "average_backlog_burnup_score",
                "top_capacity_pressure_ratio",
                "top_escalation_priority_score",
            }:
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistSignalBacklogBurnupReportV2Config(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        snapshot(readonly=False)


def test_digest_tampering_is_rejected_for_report_and_payload() -> None:
    module = api()
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, top_escalation_priority_score=d("0.700000"))

    payload = report.payload
    tampered_payload = dict(payload)
    tampered_payload["team_count"] = "4"
    with pytest.raises(ValueError, match="derived_validation_digest must match public payload"):
        module.team_specialist_signal_backlog_burnup_report_v2_payload(tampered_payload)


def test_unsafe_public_keys_and_values_are_rejected() -> None:
    module = api()

    for unsafe_value in (
        "live_team",
        "auth_team",
        "wallet_team",
        "order_team",
        "network_team",
        "database_team",
        "persist_team",
        "signing_team",
        "mutation_team",
        "buy_team",
        "sell_team",
        "trade_team",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            snapshot(team_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"order_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("trade",))


def test_validation_rejects_bad_values_duplicates_and_manual_drift() -> None:
    module = api()

    with pytest.raises(ValueError, match="completed_signal_count must be exactly Decimal"):
        snapshot(completed_signal_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="carried_signal_count must be >= 0.000000"):
        snapshot(carried_signal_count=d("-1"))
    with pytest.raises(ValueError, match="escalated_signal_count must be an integral Decimal"):
        snapshot(escalated_signal_count=d("1.5"))
    with pytest.raises(ValueError, match="captured_at must be timezone-aware"):
        snapshot(captured_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="captured_at values must be at or before generated_at"):
        build_report(snapshot(captured_at=datetime(2026, 7, 6, 13, 0, tzinfo=UTC)))
    with pytest.raises(ValueError, match="snapshots must not contain duplicate team_id values"):
        build_report(snapshot(), snapshot(snapshot_id="alpha_backlog_later"))
    with pytest.raises(ValueError, match="rows must be sorted by escalation priority and rank"):
        report = build_report()
        replace(report, rows=(report.rows[1], report.rows[0], report.rows[2]))
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(build_report(), pass_team_count=d("2"))
    with pytest.raises(ValueError, match="reason_codes must match report_status"):
        replace(
            build_report(),
            reason_codes=("signal_backlog_burnup_passed",),
        )

    with pytest.raises(ValueError, match="completion_weight must be exactly Decimal"):
        module.TeamSpecialistSignalBacklogBurnupReportV2Config(completion_weight=0)
    with pytest.raises(ValueError, match="score weights must sum to 1.000000"):
        module.TeamSpecialistSignalBacklogBurnupReportV2Config(
            escalation_weight=d("0.210000"),
        )


def test_module_scope_has_no_network_auth_wallet_order_db_or_trading_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_or_int_values([imports, call_names, attribute_names])
