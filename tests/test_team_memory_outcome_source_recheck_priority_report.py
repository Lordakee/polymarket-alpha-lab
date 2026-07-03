from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_memory_outcome_source_recheck_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def at_age(seconds: int) -> datetime:
    return GENERATED_AT - timedelta(seconds=seconds)


def input_row(
    team_id: str,
    category_id: str,
    outcome_id: str,
    *,
    source_age_seconds: int | None = 60,
    latest_source_rechecked_at: datetime | None = None,
    expected_source_count: str = "4.000000",
    verified_source_count: str = "4.000000",
    total_outcome_count: str = "5.000000",
    unresolved_outcome_count: str = "1.000000",
):
    priority = api()
    return priority.TeamMemoryOutcomeSourceRecheckPriorityInput(
        team_id=team_id,
        category_id=category_id,
        outcome_id=outcome_id,
        latest_source_rechecked_at=(
            latest_source_rechecked_at
            if latest_source_rechecked_at is not None
            else (None if source_age_seconds is None else at_age(source_age_seconds))
        ),
        expected_source_count=d(expected_source_count),
        verified_source_count=d(verified_source_count),
        total_outcome_count=d(total_outcome_count),
        unresolved_outcome_count=d(unresolved_outcome_count),
    )


def config(**overrides: object):
    priority = api()
    values = {
        "stale_source_recheck_watch_seconds": d("3600.000000"),
        "stale_source_recheck_blocked_seconds": d("7200.000000"),
        "source_coverage_watch_below_ratio": d("0.750000"),
        "source_coverage_blocked_below_ratio": d("0.500000"),
        "unresolved_outcome_pressure_watch_ratio": d("0.400000"),
        "unresolved_outcome_pressure_blocked_ratio": d("0.700000"),
    }
    values.update(overrides)
    return priority.TeamMemoryOutcomeSourceRecheckPriorityConfig(**values)


def report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    priority = api()
    return priority.build_team_memory_outcome_source_recheck_priority_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)
        return
    assert type(value) is not float


def joined(*parts: str) -> str:
    return "".join(parts)


def test_empty_input_returns_clear_decimal_report() -> None:
    priority_report = report()

    assert is_dataclass(priority_report)
    assert priority_report.generated_at == GENERATED_AT
    assert priority_report.config_version == (
        "team-memory-outcome-source-recheck-priority-v0"
    )
    assert priority_report.input_row_count == d("0.000000")
    assert priority_report.prioritized_row_count == d("0.000000")
    assert priority_report.blocked_row_count == d("0.000000")
    assert priority_report.watch_row_count == d("0.000000")
    assert priority_report.pass_row_count == d("0.000000")
    assert priority_report.stale_source_recheck_row_count == d("0.000000")
    assert priority_report.missing_source_recheck_row_count == d("0.000000")
    assert priority_report.low_source_coverage_row_count == d("0.000000")
    assert priority_report.high_unresolved_outcome_pressure_row_count == d("0.000000")
    assert priority_report.max_source_recheck_age_seconds == d("0.000000")
    assert priority_report.min_source_coverage_ratio == d("0.000000")
    assert priority_report.max_unresolved_outcome_pressure == d("0.000000")
    assert priority_report.priority_ratio == d("0.000000")
    assert priority_report.report_status == "pass"
    assert priority_report.reason_codes == (
        "team_memory_outcome_source_recheck_priority_clear",
    )
    assert priority_report.priority_rows == ()
    assert priority_report.paper_only is True
    assert priority_report.report_only is True
    assert priority_report.readonly is True


def test_ranking_is_deterministic_with_dimension_tie_breakers() -> None:
    priority_report = report(
        input_row("team_zeta", "rates", "outcome_low_age", source_age_seconds=4000),
        input_row(
            "team_beta",
            "rates",
            "outcome_low_coverage",
            source_age_seconds=8000,
            expected_source_count="4.000000",
            verified_source_count="1.000000",
            total_outcome_count="10.000000",
            unresolved_outcome_count="3.000000",
        ),
        input_row(
            "team_alpha",
            "rates",
            "outcome_alpha",
            source_age_seconds=8000,
            expected_source_count="4.000000",
            verified_source_count="2.000000",
            total_outcome_count="10.000000",
            unresolved_outcome_count="9.000000",
        ),
        input_row(
            "team_alpha",
            "rates",
            "outcome_beta",
            source_age_seconds=8000,
            expected_source_count="4.000000",
            verified_source_count="2.000000",
            total_outcome_count="10.000000",
            unresolved_outcome_count="7.000000",
        ),
        input_row("team_clear", "rates", "outcome_clear"),
    )

    assert priority_report.input_row_count == d("5.000000")
    assert priority_report.prioritized_row_count == d("4.000000")
    assert priority_report.blocked_row_count == d("3.000000")
    assert priority_report.watch_row_count == d("1.000000")
    assert priority_report.pass_row_count == d("1.000000")
    assert priority_report.report_status == "blocked"

    assert tuple(row.outcome_id for row in priority_report.priority_rows) == (
        "outcome_low_coverage",
        "outcome_alpha",
        "outcome_beta",
        "outcome_low_age",
    )
    assert tuple(row.priority_rank for row in priority_report.priority_rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
        d("4.000000"),
    )

    first = priority_report.priority_rows[0]
    assert first.priority_status == "blocked"
    assert first.source_recheck_age_seconds == d("8000.000000")
    assert first.source_coverage_ratio == d("0.250000")
    assert first.source_coverage_shortfall_ratio == d("0.750000")
    assert first.unresolved_outcome_pressure == d("0.300000")
    assert first.priority_reason_count == d("2.000000")
    assert first.reason_codes == (
        "source_recheck_stale_blocked",
        "source_coverage_low_blocked",
    )

    assert priority_report.reason_codes == (
        "team_memory_outcome_source_recheck_priority_blocked",
        "source_recheck_stale_blocked_present",
        "source_recheck_stale_watch_present",
        "source_coverage_low_blocked_present",
        "source_coverage_low_watch_present",
        "unresolved_outcome_pressure_high_blocked_present",
    )


def test_threshold_statuses_reason_codes_and_missing_recheck() -> None:
    priority_report = report(
        input_row("team_missing", "rates", "outcome_missing", source_age_seconds=None),
        input_row("team_age_watch", "rates", "outcome_age", source_age_seconds=3600),
        input_row(
            "team_coverage_watch",
            "rates",
            "outcome_coverage",
            expected_source_count="2.000000",
            verified_source_count="1.000000",
        ),
        input_row(
            "team_pressure_watch",
            "rates",
            "outcome_pressure",
            total_outcome_count="5.000000",
            unresolved_outcome_count="2.000000",
        ),
    )

    rows = {row.team_id: row for row in priority_report.priority_rows}

    assert rows["team_missing"].priority_status == "blocked"
    assert rows["team_missing"].source_recheck_age_seconds is None
    assert rows["team_missing"].reason_codes == ("source_recheck_missing",)

    assert rows["team_age_watch"].priority_status == "watch"
    assert rows["team_age_watch"].reason_codes == ("source_recheck_stale_watch",)

    assert rows["team_coverage_watch"].priority_status == "watch"
    assert rows["team_coverage_watch"].source_coverage_ratio == d("0.500000")
    assert rows["team_coverage_watch"].reason_codes == ("source_coverage_low_watch",)

    assert rows["team_pressure_watch"].priority_status == "watch"
    assert rows["team_pressure_watch"].unresolved_outcome_pressure == d("0.400000")
    assert rows["team_pressure_watch"].reason_codes == (
        "unresolved_outcome_pressure_high_watch",
    )

    assert priority_report.missing_source_recheck_row_count == d("1.000000")
    assert priority_report.stale_source_recheck_row_count == d("2.000000")
    assert priority_report.low_source_coverage_row_count == d("1.000000")
    assert priority_report.high_unresolved_outcome_pressure_row_count == d("1.000000")


def test_rejects_naive_offset_future_and_inconsistent_values() -> None:
    priority = api()

    with pytest.raises(ValueError, match="generated_at must be UTC-aware"):
        report(input_row("team_alpha", "rates", "outcome_alpha"), generated_at=datetime(2026, 7, 2, 12, 0))

    with pytest.raises(ValueError, match="latest_source_rechecked_at must be UTC-aware"):
        priority.TeamMemoryOutcomeSourceRecheckPriorityInput(
            team_id="team_alpha",
            category_id="rates",
            outcome_id="outcome_alpha",
            latest_source_rechecked_at=datetime(2026, 7, 2, 11, 0),
            expected_source_count=d("1.000000"),
            verified_source_count=d("1.000000"),
            total_outcome_count=d("1.000000"),
            unresolved_outcome_count=d("0.000000"),
        )

    with pytest.raises(ValueError, match="latest_source_rechecked_at must be UTC-aware"):
        priority.TeamMemoryOutcomeSourceRecheckPriorityInput(
            team_id="team_alpha",
            category_id="rates",
            outcome_id="outcome_alpha",
            latest_source_rechecked_at=datetime(
                2026,
                7,
                2,
                7,
                0,
                tzinfo=timezone(timedelta(hours=-5)),
            ),
            expected_source_count=d("1.000000"),
            verified_source_count=d("1.000000"),
            total_outcome_count=d("1.000000"),
            unresolved_outcome_count=d("0.000000"),
        )

    with pytest.raises(
        ValueError,
        match="latest_source_rechecked_at must not be after generated_at",
    ):
        report(
            input_row(
                "team_future",
                "rates",
                "outcome_future",
                latest_source_rechecked_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )

    with pytest.raises(ValueError, match="verified_source_count"):
        input_row(
            "team_bad",
            "rates",
            "outcome_bad",
            expected_source_count="1.000000",
            verified_source_count="2.000000",
        )

    duplicate = input_row("team_dupe", "rates", "outcome_dupe")
    with pytest.raises(ValueError, match="unique"):
        report(duplicate, duplicate)


def test_dataclasses_are_frozen_and_public_numeric_fields_are_decimal() -> None:
    priority = api()
    input_value = input_row("team_alpha", "rates", "outcome_alpha", source_age_seconds=8000)
    priority_report = report(input_value)

    with pytest.raises(FrozenInstanceError):
        input_value.team_id = "team_beta"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        priority_report.report_status = "pass"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        priority_report.priority_rows[0].priority_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        priority.TeamMemoryOutcomeSourceRecheckPriorityConfig(paper_only=False)

    checked_values: list[object] = []
    for item in (
        config(),
        input_value,
        priority_report,
        priority_report.priority_rows[0],
    ):
        assert is_dataclass(item)
        for field in fields(item):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
                or field.name.endswith("_pressure")
                or field.name.endswith("_rank")
            ):
                value = getattr(item, field.name)
                if value is not None:
                    checked_values.append(value)

    assert checked_values
    assert all(type(value) is Decimal for value in checked_values)


def test_json_payload_uses_decimal_strings_iso_datetimes_and_no_floats() -> None:
    payload = api().team_memory_outcome_source_recheck_priority_report_to_jsonable(
        report(
            input_row(
                "team_json",
                "rates",
                "outcome_json",
                source_age_seconds=3661,
                expected_source_count="3.000000",
                verified_source_count="2.000000",
                total_outcome_count="4.000000",
                unresolved_outcome_count="2.000000",
            ),
        ),
    )

    assert_no_float_values(payload)
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["input_row_count"] == "1.000000"
    assert payload["priority_ratio"] == "1.000000"
    assert payload["priority_rows"][0]["priority_rank"] == "1.000000"
    assert payload["priority_rows"][0]["latest_source_rechecked_at"] == (
        "2026-07-02T10:58:59+00:00"
    )
    assert payload["priority_rows"][0]["source_recheck_age_seconds"] == "3661.000000"
    assert payload["priority_rows"][0]["source_coverage_ratio"] == "0.666667"
    assert payload["priority_rows"][0]["unresolved_outcome_pressure"] == "0.500000"
    json.dumps(payload, sort_keys=True)


def test_jsonable_uses_shared_paper_report_surface_guards() -> None:
    source = inspect.getsource(
        api().team_memory_outcome_source_recheck_priority_report_to_jsonable,
    )

    assert "json_ready_no_floats" in source
    assert "reject_unsafe_surface_fields" in source
    assert "require_paper_only_flags" in source


def test_jsonable_rejects_nested_flag_and_payload_tampering() -> None:
    priority = api()
    priority_report = report(
        input_row("team_json", "rates", "outcome_json", source_age_seconds=8000),
    )

    object.__setattr__(priority_report.priority_rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        priority.team_memory_outcome_source_recheck_priority_report_to_jsonable(
            priority_report,
        )
    object.__setattr__(priority_report.priority_rows[0], "paper_only", True)

    original_asdict = priority.asdict
    try:
        priority.asdict = lambda value: {  # type: ignore[method-assign]
            **original_asdict(value),
            "live_execution_id": "exec-1",
        }
        with pytest.raises(ValueError, match="unsafe live surface field"):
            priority.team_memory_outcome_source_recheck_priority_report_to_jsonable(
                priority_report,
            )

        priority.asdict = lambda value: {  # type: ignore[method-assign]
            **original_asdict(value),
            "priority_ratio": 1.0,
        }
        with pytest.raises(ValueError, match="must not be a float"):
            priority.team_memory_outcome_source_recheck_priority_report_to_jsonable(
                priority_report,
            )
    finally:
        priority.asdict = original_asdict  # type: ignore[method-assign]


def test_priority_row_rejects_reason_codes_that_conflict_with_metrics() -> None:
    priority = api()

    with pytest.raises(ValueError, match="reason_codes must match row metrics"):
        priority.TeamMemoryOutcomeSourceRecheckPriorityRow(
            priority_rank=d("1.000000"),
            team_id="team_fresh",
            category_id="rates",
            outcome_id="outcome_fresh",
            latest_source_rechecked_at=at_age(60),
            source_recheck_age_seconds=d("60.000000"),
            expected_source_count=d("4.000000"),
            verified_source_count=d("4.000000"),
            source_coverage_ratio=d("1.000000"),
            source_coverage_shortfall_ratio=d("0.000000"),
            total_outcome_count=d("5.000000"),
            unresolved_outcome_count=d("1.000000"),
            unresolved_outcome_pressure=d("0.200000"),
            priority_reason_count=d("1.000000"),
            priority_status="blocked",
            reason_codes=("source_recheck_missing",),
        )


def test_priority_row_rejects_noncanonical_reason_code_sequence() -> None:
    priority = api()

    with pytest.raises(ValueError, match="canonical reason code sequence"):
        priority.TeamMemoryOutcomeSourceRecheckPriorityRow(
            priority_rank=d("1.000000"),
            team_id="team_sequence",
            category_id="rates",
            outcome_id="outcome_sequence",
            latest_source_rechecked_at=at_age(8000),
            source_recheck_age_seconds=d("8000.000000"),
            expected_source_count=d("4.000000"),
            verified_source_count=d("1.000000"),
            source_coverage_ratio=d("0.250000"),
            source_coverage_shortfall_ratio=d("0.750000"),
            total_outcome_count=d("10.000000"),
            unresolved_outcome_count=d("3.000000"),
            unresolved_outcome_pressure=d("0.300000"),
            priority_reason_count=d("2.000000"),
            priority_status="blocked",
            reason_codes=(
                "source_coverage_low_blocked",
                "source_recheck_stale_blocked",
            ),
        )


def test_builder_still_emits_canonical_priority_row_reason_codes() -> None:
    priority_report = report(
        input_row(
            "team_builder",
            "rates",
            "outcome_builder",
            source_age_seconds=8000,
            expected_source_count="4.000000",
            verified_source_count="1.000000",
            total_outcome_count="10.000000",
            unresolved_outcome_count="8.000000",
        ),
    )

    assert priority_report.priority_rows[0].reason_codes == (
        "source_recheck_stale_blocked",
        "source_coverage_low_blocked",
        "unresolved_outcome_pressure_high_blocked",
    )


def test_jsonable_rejects_unsafe_surface_string_values() -> None:
    priority = api()
    priority_report = report(
        input_row(
            "wallet_auth_order",
            "private_key_trade",
            "submit_cancel_order",
            source_age_seconds=8000,
        ),
    )

    with pytest.raises(ValueError, match="unsafe live surface value"):
        priority.team_memory_outcome_source_recheck_priority_report_to_jsonable(
            priority_report,
        )


def test_module_has_no_io_or_disallowed_execution_surface() -> None:
    source = inspect.getsource(api()).lower()

    assert "float(" not in source
    assert ".total_seconds(" not in source
    assert "open(" not in source
    assert "path(" not in source
    assert "psycopg" not in source
    assert "sqlalchemy" not in source
    for fragment in (
        joined("net", "work"),
        joined("au", "th"),
        joined("wal", "let"),
        joined("bro", "ker"),
        joined("ord", "er"),
        joined("sub", "mit"),
        joined("can", "cel"),
        joined("sig", "ning"),
        joined("ad", "vice"),
        "socket",
        "requests",
        "http",
    ):
        assert fragment not in source

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
