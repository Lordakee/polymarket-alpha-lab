from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.team_memory_outcome_source_recheck_health_report import (
    TeamMemoryOutcomeSourceRecheckHealthConfig,
    TeamMemoryOutcomeSourceRecheckMemoryRow,
    build_team_memory_outcome_source_recheck_health_report,
    team_memory_outcome_source_recheck_health_report_to_json,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def memory_row(**overrides: object) -> TeamMemoryOutcomeSourceRecheckMemoryRow:
    values = {
        "team_id": "macro",
        "category_id": "rates",
        "latest_source_rechecked_at": GENERATED_AT - timedelta(hours=1),
        "expected_source_count": d("4"),
        "verified_source_count": d("4"),
        "total_outcome_count": d("5"),
        "unresolved_outcome_count": d("1"),
    }
    values.update(overrides)
    return TeamMemoryOutcomeSourceRecheckMemoryRow(**values)


def config(**overrides: object) -> TeamMemoryOutcomeSourceRecheckHealthConfig:
    values = {
        "watch_source_recheck_age_seconds": d("3600.000000"),
        "blocked_source_recheck_age_seconds": d("7200.000000"),
        "watch_min_source_coverage_ratio": d("0.750000"),
        "blocked_min_source_coverage_ratio": d("0.500000"),
        "watch_unresolved_outcome_pressure": d("0.400000"),
        "blocked_unresolved_outcome_pressure": d("0.700000"),
    }
    values.update(overrides)
    return TeamMemoryOutcomeSourceRecheckHealthConfig(**values)


def report(
    rows: tuple[TeamMemoryOutcomeSourceRecheckMemoryRow, ...],
    *,
    cfg: TeamMemoryOutcomeSourceRecheckHealthConfig | None = None,
    generated_at: datetime = GENERATED_AT,
):
    return build_team_memory_outcome_source_recheck_health_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_builds_blocked_readonly_report() -> None:
    result = report(())

    assert result.generated_at == GENERATED_AT
    assert result.config_version == "team-memory-outcome-source-recheck-health-v0"
    assert result.health_status == "blocked"
    assert result.row_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("0")
    assert result.stale_source_recheck_count == d("0")
    assert result.low_source_coverage_count == d("0")
    assert result.high_unresolved_outcome_pressure_count == d("0")
    assert result.oldest_source_recheck_age_seconds is None
    assert result.average_source_coverage_ratio == d("0.000000")
    assert result.highest_unresolved_outcome_pressure == d("0.000000")
    assert result.rows == ()
    assert result.reason_codes == ("memory_rows_empty",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_report_sorts_rows_and_reason_codes_deterministically() -> None:
    result = report(
        (
            memory_row(
                team_id="zeta",
                category_id="weather",
                expected_source_count=d("4"),
                verified_source_count=d("2"),
                total_outcome_count=d("5"),
                unresolved_outcome_count=d("3"),
            ),
            memory_row(
                team_id="alpha",
                category_id="rates",
                latest_source_rechecked_at=GENERATED_AT - timedelta(seconds=7201),
            ),
            memory_row(
                team_id="alpha",
                category_id="credit",
                expected_source_count=d("4"),
                verified_source_count=d("4"),
                total_outcome_count=d("5"),
                unresolved_outcome_count=d("1"),
            ),
        ),
    )

    assert tuple((row.team_id, row.category_id) for row in result.rows) == (
        ("alpha", "credit"),
        ("alpha", "rates"),
        ("zeta", "weather"),
    )
    assert result.health_status == "blocked"
    assert result.reason_codes == (
        "stale_source_recheck_rows_present",
        "low_source_coverage_rows_present",
        "high_unresolved_outcome_pressure_rows_present",
    )
    assert result.stale_source_recheck_count == d("1")
    assert result.low_source_coverage_count == d("1")
    assert result.high_unresolved_outcome_pressure_count == d("1")

    stale = result.rows[1]
    assert stale.source_recheck_age_seconds == d("7201.000000")
    assert stale.health_status == "blocked"
    assert stale.reason_codes == ("source_recheck_stale_blocked",)

    pressured = result.rows[2]
    assert pressured.source_coverage_ratio == d("0.500000")
    assert pressured.unresolved_outcome_pressure == d("0.600000")
    assert pressured.health_status == "watch"
    assert pressured.reason_codes == (
        "source_coverage_low_watch",
        "unresolved_outcome_pressure_high_watch",
    )


def test_threshold_statuses_are_stable_at_pass_watch_and_blocked_boundaries() -> None:
    result = report(
        (
            memory_row(team_id="pass-row", category_id="thresholds"),
            memory_row(
                team_id="watch-row",
                category_id="thresholds",
                latest_source_rechecked_at=GENERATED_AT - timedelta(seconds=3601),
                expected_source_count=d("4"),
                verified_source_count=d("2"),
                total_outcome_count=d("5"),
                unresolved_outcome_count=d("3"),
            ),
            memory_row(
                team_id="blocked-row",
                category_id="thresholds",
                latest_source_rechecked_at=GENERATED_AT - timedelta(seconds=7201),
                expected_source_count=d("4"),
                verified_source_count=d("1"),
                total_outcome_count=d("5"),
                unresolved_outcome_count=d("4"),
            ),
        ),
    )

    rows_by_team = {row.team_id: row for row in result.rows}

    assert rows_by_team["pass-row"].health_status == "pass"
    assert rows_by_team["pass-row"].reason_codes == ("outcome_source_recheck_ready",)

    assert rows_by_team["watch-row"].health_status == "watch"
    assert rows_by_team["watch-row"].source_recheck_status == "watch"
    assert rows_by_team["watch-row"].source_coverage_status == "watch"
    assert rows_by_team["watch-row"].outcome_pressure_status == "watch"
    assert rows_by_team["watch-row"].reason_codes == (
        "source_recheck_stale_watch",
        "source_coverage_low_watch",
        "unresolved_outcome_pressure_high_watch",
    )

    assert rows_by_team["blocked-row"].health_status == "blocked"
    assert rows_by_team["blocked-row"].source_recheck_status == "blocked"
    assert rows_by_team["blocked-row"].source_coverage_status == "blocked"
    assert rows_by_team["blocked-row"].outcome_pressure_status == "blocked"
    assert rows_by_team["blocked-row"].reason_codes == (
        "source_recheck_stale_blocked",
        "source_coverage_low_blocked",
        "unresolved_outcome_pressure_high_blocked",
    )

    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.health_status == "blocked"


def test_health_row_rejects_reason_codes_that_do_not_match_dimension_statuses() -> None:
    watch = report(
        (
            memory_row(
                latest_source_rechecked_at=GENERATED_AT - timedelta(seconds=3601),
            ),
        ),
    ).rows[0]
    assert watch.source_recheck_status == "watch"
    assert watch.source_coverage_status == "pass"
    assert watch.outcome_pressure_status == "pass"

    with pytest.raises(ValueError, match="reason_codes must match dimension statuses"):
        replace(watch, reason_codes=())

    with pytest.raises(ValueError, match="reason_codes must match dimension statuses"):
        replace(watch, reason_codes=("custom_reason",))

    with pytest.raises(ValueError, match="reason_codes must match dimension statuses"):
        replace(watch, reason_codes=("source_coverage_low_watch",))

    with pytest.raises(ValueError, match="non-pass rows must not use ready reason code"):
        replace(watch, reason_codes=("outcome_source_recheck_ready",))


def test_rejects_non_utc_datetimes_and_future_rechecks() -> None:
    with pytest.raises(ValueError, match="generated_at must be UTC-aware"):
        report((memory_row(),), generated_at=datetime(2026, 7, 2, 12, 0))

    with pytest.raises(ValueError, match="generated_at must be UTC-aware"):
        report(
            (memory_row(),),
            generated_at=datetime(
                2026,
                7,
                2,
                5,
                0,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        )

    with pytest.raises(ValueError, match="latest_source_rechecked_at must be UTC-aware"):
        memory_row(latest_source_rechecked_at=datetime(2026, 7, 2, 11, 0))

    with pytest.raises(ValueError, match="latest_source_rechecked_at must be UTC-aware"):
        memory_row(
            latest_source_rechecked_at=datetime(
                2026,
                7,
                2,
                4,
                0,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        )

    with pytest.raises(ValueError, match="latest_source_rechecked_at must not be after generated_at"):
        report(
            (
                memory_row(
                    latest_source_rechecked_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )


def test_public_dataclasses_are_frozen_and_validate_decimal_inputs() -> None:
    result = report((memory_row(),))

    with pytest.raises(FrozenInstanceError):
        result.rows[0].health_status = "blocked"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        result.health_status = "pass"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        config().blocked_source_recheck_age_seconds = d("1")  # type: ignore[misc]

    with pytest.raises(ValueError, match="expected_source_count"):
        memory_row(expected_source_count=4)

    with pytest.raises(ValueError, match="watch_source_recheck_age_seconds"):
        config(watch_source_recheck_age_seconds=3600)


def test_json_payload_uses_decimal_strings_and_iso_datetimes() -> None:
    result = report(
        (
            memory_row(
                team_id="json",
                category_id="payload",
                latest_source_rechecked_at=GENERATED_AT - timedelta(seconds=3661),
                expected_source_count=d("3"),
                verified_source_count=d("2"),
                total_outcome_count=d("4"),
                unresolved_outcome_count=d("2"),
            ),
        ),
    )

    payload = team_memory_outcome_source_recheck_health_report_to_json(result)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["config_version"] == "team-memory-outcome-source-recheck-health-v0"
    assert payload["row_count"] == "1"
    assert payload["average_source_coverage_ratio"] == "0.666667"
    assert payload["oldest_source_recheck_age_seconds"] == "3661.000000"
    assert payload["reason_codes"] == [
        "stale_source_recheck_rows_present",
        "low_source_coverage_rows_present",
        "high_unresolved_outcome_pressure_rows_present",
    ]

    row_payload = payload["rows"][0]
    assert row_payload["latest_source_rechecked_at"] == "2026-07-02T10:58:59+00:00"
    assert row_payload["expected_source_count"] == "3"
    assert row_payload["source_recheck_age_seconds"] == "3661.000000"
    assert row_payload["source_coverage_ratio"] == "0.666667"
    assert row_payload["unresolved_outcome_pressure"] == "0.500000"

    def assert_no_decimal(value: object) -> None:
        if isinstance(value, Decimal):
            raise AssertionError(f"payload contains Decimal {value}")
        if isinstance(value, dict):
            for item in value.values():
                assert_no_decimal(item)
        if isinstance(value, list):
            for item in value:
                assert_no_decimal(item)

    assert_no_decimal(payload)


def test_json_payload_uses_shared_paper_report_surface_guards() -> None:
    source = inspect.getsource(team_memory_outcome_source_recheck_health_report_to_json)

    assert "json_ready_no_floats" in source
    assert "reject_unsafe_surface_fields" in source
    assert "require_paper_only_flags" in source


def test_json_payload_rejects_unsafe_public_surface_string_values() -> None:
    result = report(
        (
            memory_row(
                team_id="wallet_auth_order",
                category_id="private_key_trade",
            ),
        ),
    )

    assert result.rows[0].team_id == "wallet_auth_order"
    assert result.rows[0].category_id == "private_key_trade"

    with pytest.raises(ValueError, match="unsafe live surface value"):
        team_memory_outcome_source_recheck_health_report_to_json(result)


def test_json_payload_rejects_nested_flag_and_payload_tampering(monkeypatch: pytest.MonkeyPatch) -> None:
    module = __import__(
        "polymarket_alpha_lab.team_memory_outcome_source_recheck_health_report",
        fromlist=[""],
    )
    result = report((memory_row(),))

    object.__setattr__(result.rows[0], "report_only", False)
    with pytest.raises(ValueError, match="report_only must be True"):
        team_memory_outcome_source_recheck_health_report_to_json(result)
    object.__setattr__(result.rows[0], "report_only", True)

    original_row_to_json = module._health_row_to_json
    monkeypatch.setattr(
        module,
        "_health_row_to_json",
        lambda row: {**original_row_to_json(row), "live_execution_id": "exec-1"},
    )
    with pytest.raises(ValueError, match="unsafe live surface field"):
        team_memory_outcome_source_recheck_health_report_to_json(result)

    monkeypatch.setattr(
        module,
        "_health_row_to_json",
        lambda row: {**original_row_to_json(row), "source_coverage_ratio": 1.0},
    )
    with pytest.raises(ValueError, match="must not be a float"):
        team_memory_outcome_source_recheck_health_report_to_json(result)
