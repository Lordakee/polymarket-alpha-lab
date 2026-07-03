import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import get_args, get_origin

import pytest

from polymarket_alpha_lab.team_memory_source_recheck_cadence_status_report import (
    DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_STATUS_CONFIG_VERSION,
    TeamMemorySourceRecheckCadenceStatusConfig,
    TeamMemorySourceRecheckCadenceStatusReasonCodeCount,
    TeamMemorySourceRecheckCadenceStatusReport,
    TeamMemorySourceRecheckCadenceStatusRow,
    TeamMemorySourceRecheckCadenceSource,
    build_team_memory_source_recheck_cadence_status_report,
    team_memory_source_recheck_cadence_status_report_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/team_memory_source_recheck_cadence_status_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> TeamMemorySourceRecheckCadenceStatusConfig:
    values = {
        "config_version": DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_STATUS_CONFIG_VERSION,
        "due_soon_window_seconds": d("3600.000000"),
        "blocked_overdue_age_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return TeamMemorySourceRecheckCadenceStatusConfig(**values)


def _source(
    source_id: str,
    source_family: str,
    *,
    team_id: str = "politics",
    last_rechecked_at: datetime | None = GENERATED_AT - timedelta(hours=1),
    next_recheck_due_at: datetime = GENERATED_AT + timedelta(hours=1),
    source_config_version: str = "memory-source-v0",
) -> TeamMemorySourceRecheckCadenceSource:
    return TeamMemorySourceRecheckCadenceSource(
        team_id=team_id,
        source_id=source_id,
        source_family=source_family,
        last_rechecked_at=last_rechecked_at,
        next_recheck_due_at=next_recheck_due_at,
        source_config_version=source_config_version,
    )


def test_status_report_sorts_sources_and_summarizes_cadence_thresholds() -> None:
    report = build_team_memory_source_recheck_cadence_status_report(
        (
            _source(
                "btc_model",
                "model",
                team_id="crypto_btc",
                last_rechecked_at=GENERATED_AT - timedelta(hours=2),
                next_recheck_due_at=GENERATED_AT + timedelta(hours=2),
            ),
            _source(
                "polling_tracker",
                "polling",
                team_id="politics",
                last_rechecked_at=GENERATED_AT - timedelta(minutes=90),
                next_recheck_due_at=GENERATED_AT + timedelta(minutes=30),
            ),
            _source(
                "calendar_digest",
                "calendar",
                team_id="macro_rates",
                last_rechecked_at=GENERATED_AT - timedelta(hours=3),
                next_recheck_due_at=GENERATED_AT - timedelta(minutes=10),
            ),
            _source(
                "lineup_sheet",
                "lineups",
                team_id="sports_soccer",
                last_rechecked_at=None,
                next_recheck_due_at=GENERATED_AT + timedelta(hours=1),
            ),
            _source(
                "inventory_feed",
                "inventory",
                team_id="commodities_oil",
                last_rechecked_at=GENERATED_AT - timedelta(hours=5),
                next_recheck_due_at=GENERATED_AT - timedelta(seconds=9000),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, TeamMemorySourceRecheckCadenceStatusReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_STATUS_CONFIG_VERSION
    assert report.report_status == "blocked"
    assert report.source_count == d("5.000000")
    assert report.current_source_count == d("1.000000")
    assert report.due_soon_source_count == d("1.000000")
    assert report.overdue_source_count == d("2.000000")
    assert report.blocked_source_count == d("2.000000")
    assert report.missing_history_source_count == d("1.000000")
    assert report.watch_source_count == d("2.000000")
    assert report.overdue_source_ratio == d("0.400000")
    assert report.blocked_source_ratio == d("0.400000")
    assert report.max_overdue_age_seconds == d("9000.000000")
    assert report.max_last_recheck_age_seconds == d("18000.000000")
    assert report.reason_codes == (
        "team_memory_source_recheck_cadence_blocked_overdue",
        "team_memory_source_recheck_cadence_missing_history",
        "team_memory_source_recheck_cadence_overdue",
        "team_memory_source_recheck_cadence_due_soon",
        "team_memory_source_recheck_cadence_current",
    )
    assert report.reason_code_counts == (
        TeamMemorySourceRecheckCadenceStatusReasonCodeCount(
            reason_code="team_memory_source_recheck_cadence_blocked_overdue",
            source_count=d("1.000000"),
        ),
        TeamMemorySourceRecheckCadenceStatusReasonCodeCount(
            reason_code="team_memory_source_recheck_cadence_missing_history",
            source_count=d("1.000000"),
        ),
        TeamMemorySourceRecheckCadenceStatusReasonCodeCount(
            reason_code="team_memory_source_recheck_cadence_overdue",
            source_count=d("2.000000"),
        ),
        TeamMemorySourceRecheckCadenceStatusReasonCodeCount(
            reason_code="team_memory_source_recheck_cadence_due_soon",
            source_count=d("1.000000"),
        ),
        TeamMemorySourceRecheckCadenceStatusReasonCodeCount(
            reason_code="team_memory_source_recheck_cadence_current",
            source_count=d("1.000000"),
        ),
    )

    assert tuple(row.source_id for row in report.rows) == (
        "inventory_feed",
        "lineup_sheet",
        "calendar_digest",
        "polling_tracker",
        "btc_model",
    )
    assert tuple(row.cadence_status for row in report.rows) == (
        "blocked",
        "blocked",
        "overdue",
        "due_soon",
        "current",
    )
    assert report.rows[0] == TeamMemorySourceRecheckCadenceStatusRow(
        team_id="commodities_oil",
        source_id="inventory_feed",
        source_family="inventory",
        cadence_status="blocked",
        last_rechecked_at=GENERATED_AT - timedelta(hours=5),
        next_recheck_due_at=GENERATED_AT - timedelta(seconds=9000),
        due_delta_seconds=d("-9000.000000"),
        overdue_age_seconds=d("9000.000000"),
        last_recheck_age_seconds=d("18000.000000"),
        reason_codes=(
            "team_memory_source_recheck_cadence_blocked_overdue",
            "team_memory_source_recheck_cadence_overdue",
        ),
    )
    assert report.rows[1].last_recheck_age_seconds is None
    assert report.rows[1].reason_codes == (
        "team_memory_source_recheck_cadence_missing_history",
    )
    assert report.rows[2].due_delta_seconds == d("-600.000000")
    assert report.rows[3].due_delta_seconds == d("1800.000000")
    assert report.rows[4].reason_codes == (
        "team_memory_source_recheck_cadence_current",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_status_report_empty_input_returns_blocked_zero_report() -> None:
    report = build_team_memory_source_recheck_cadence_status_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.report_status == "blocked"
    assert report.source_count == d("0.000000")
    assert report.current_source_count == d("0.000000")
    assert report.due_soon_source_count == d("0.000000")
    assert report.overdue_source_count == d("0.000000")
    assert report.blocked_source_count == d("0.000000")
    assert report.missing_history_source_count == d("0.000000")
    assert report.watch_source_count == d("0.000000")
    assert report.overdue_source_ratio == d("0.000000")
    assert report.blocked_source_ratio == d("0.000000")
    assert report.max_overdue_age_seconds is None
    assert report.max_last_recheck_age_seconds is None
    assert report.rows == ()
    assert report.reason_code_counts == (
        TeamMemorySourceRecheckCadenceStatusReasonCodeCount(
            reason_code="team_memory_source_recheck_cadence_no_sources",
            source_count=d("0.000000"),
        ),
    )
    assert report.reason_codes == ("team_memory_source_recheck_cadence_no_sources",)


def test_status_report_normalizes_timezone_offsets_and_rejects_invalid_datetimes() -> None:
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    last_rechecked_at = datetime(2026, 7, 2, 7, 30, tzinfo=timezone(timedelta(hours=-4)))
    due_at = datetime(2026, 7, 2, 14, 15, tzinfo=timezone(timedelta(hours=2)))

    report = build_team_memory_source_recheck_cadence_status_report(
        (
            _source(
                "offset_source",
                "calendar",
                team_id="macro_rates",
                last_rechecked_at=last_rechecked_at,
                next_recheck_due_at=due_at,
            ),
        ),
        config=_config(),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].last_rechecked_at == datetime(2026, 7, 2, 11, 30, tzinfo=UTC)
    assert report.rows[0].next_recheck_due_at == datetime(2026, 7, 2, 12, 15, tzinfo=UTC)
    assert report.rows[0].last_recheck_age_seconds == d("1800.000000")
    assert report.rows[0].due_delta_seconds == d("900.000000")

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_team_memory_source_recheck_cadence_status_report(
            (_source("source_alpha", "polling"),),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="next_recheck_due_at must be timezone-aware"):
        _source(
            "source_alpha",
            "polling",
            next_recheck_due_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="last_rechecked_at must not be in the future"):
        build_team_memory_source_recheck_cadence_status_report(
            (
                _source(
                    "source_alpha",
                    "polling",
                    last_rechecked_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_status_report_payload_is_json_ready_decimal_string_only() -> None:
    report = build_team_memory_source_recheck_cadence_status_report(
        (
            _source(
                "source_alpha",
                "polling",
                last_rechecked_at=GENERATED_AT - timedelta(minutes=5),
                next_recheck_due_at=GENERATED_AT - timedelta(seconds=90),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    payload = team_memory_source_recheck_cadence_status_report_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["source_count"] == "1.000000"
    assert payload["overdue_source_ratio"] == "1.000000"
    assert payload["rows"][0]["last_rechecked_at"] == "2026-07-02T11:55:00+00:00"
    assert payload["rows"][0]["due_delta_seconds"] == "-90.000000"
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
    _assert_no_payload_numbers_or_datetimes(payload)

    with pytest.raises(ValueError, match="report must be"):
        team_memory_source_recheck_cadence_status_report_payload(object())  # type: ignore[arg-type]


def test_status_report_dataclasses_are_frozen_and_decimal_typed() -> None:
    report = build_team_memory_source_recheck_cadence_status_report(
        (_source("source_alpha", "polling"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    values = (
        _config(),
        _source("source_beta", "model"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )

    for value in values:
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False

    public_values = repr(asdict(report))
    assert "3600.000000" in public_values
    for dataclass_type in (
        TeamMemorySourceRecheckCadenceStatusConfig,
        TeamMemorySourceRecheckCadenceSource,
        TeamMemorySourceRecheckCadenceStatusRow,
        TeamMemorySourceRecheckCadenceStatusReasonCodeCount,
        TeamMemorySourceRecheckCadenceStatusReport,
    ):
        for field in fields(dataclass_type):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_age_seconds")
                or field.name.endswith("_delta_seconds")
                or field.name.endswith("_seconds")
            ):
                assert _field_allows_decimal(field.type), (
                    dataclass_type,
                    field.name,
                    field.type,
                )


def test_status_report_validates_types_flags_duplicates_and_consistency() -> None:
    report = build_team_memory_source_recheck_cadence_status_report(
        (_source("source_alpha", "polling"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="config_version"):
        TeamMemorySourceRecheckCadenceStatusConfig(
            config_version=_StringSubclass(
                DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_STATUS_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="due_soon_window_seconds"):
        TeamMemorySourceRecheckCadenceStatusConfig(due_soon_window_seconds=3600)
    with pytest.raises(ValueError, match="blocked_overdue_age_seconds"):
        TeamMemorySourceRecheckCadenceStatusConfig(
            blocked_overdue_age_seconds=_DecimalSubclass("7200.000000"),
        )
    with pytest.raises(ValueError, match="source_id"):
        _source("wallet_source", "polling")
    with pytest.raises(ValueError, match="paper_only"):
        replace(_source("source_alpha", "polling"), paper_only=False)
    with pytest.raises(ValueError, match="sources"):
        build_team_memory_source_recheck_cadence_status_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="unique"):
        build_team_memory_source_recheck_cadence_status_report(
            (
                _source("source_alpha", "polling"),
                _source("source_alpha", "model"),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="source_count"):
        replace(report, source_count=d("2.000000"))
    with pytest.raises(ValueError, match="report_status"):
        replace(report, report_status="blocked")
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            report,
            reason_code_counts=(
                TeamMemorySourceRecheckCadenceStatusReasonCodeCount(
                    reason_code="team_memory_source_recheck_cadence_due_soon",
                    source_count=d("2.000000"),
                ),
            ),
        )


def test_status_report_public_surface_stays_in_memory_report_only() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.team_memory_source_recheck_cadence_status_report",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_STATUS_CONFIG_VERSION",
        "TeamMemorySourceRecheckCadenceSource",
        "TeamMemorySourceRecheckCadenceStatusConfig",
        "TeamMemorySourceRecheckCadenceStatusReasonCodeCount",
        "TeamMemorySourceRecheckCadenceStatusReport",
        "TeamMemorySourceRecheckCadenceStatusRow",
        "build_team_memory_source_recheck_cadence_status_report",
        "team_memory_source_recheck_cadence_status_report_payload",
    )

    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {
        "__import__",
        "connect",
        "eval",
        "exec",
        "executemany",
        "open",
        "print",
    }

    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            violations.append("float constant")
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module] if node.module is not None else []
        else:
            names = []
        for name in names:
            root = name.split(".", maxsplit=1)[0]
            if root in forbidden_import_roots:
                violations.append(f"forbidden import {name}")
        if isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name in forbidden_call_names:
                violations.append(f"forbidden call {call_name}")

    assert sorted(set(violations)) == []


def _field_allows_decimal(annotation: object) -> bool:
    if annotation is Decimal:
        return True
    origin = get_origin(annotation)
    if origin in (tuple, list):
        return any(_field_allows_decimal(arg) for arg in get_args(annotation))
    if origin is None:
        return False
    return any(arg is type(None) or _field_allows_decimal(arg) for arg in get_args(annotation))


def _assert_no_payload_numbers_or_datetimes(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_payload_numbers_or_datetimes(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_no_payload_numbers_or_datetimes(item)
        return
    if isinstance(value, bool):
        return
    assert not isinstance(value, (Decimal, datetime, float, int))


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
