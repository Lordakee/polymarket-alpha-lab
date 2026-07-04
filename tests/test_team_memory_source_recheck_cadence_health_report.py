from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_memory_source_recheck_cadence_health_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def ts(seconds_before_generated_at: int) -> datetime:
    return GENERATED_AT - timedelta(seconds=seconds_before_generated_at)


def source(
    team_id: str = "politics",
    source_id: str = "source-alpha",
    *,
    last_rechecked_age_seconds: int = 300,
    due_seconds_before_generated_at: int = -300,
    acknowledged: bool = True,
):
    report = api()
    return report.TeamMemorySourceRecheckCadenceInput(
        team_id=team_id,
        source_id=source_id,
        last_rechecked_at=ts(last_rechecked_age_seconds),
        next_recheck_due_at=GENERATED_AT - timedelta(seconds=due_seconds_before_generated_at),
        acknowledged_at=ts(120) if acknowledged else None,
    )


def config(**overrides: object):
    report = api()
    values = {
        "watch_stale_age_seconds": d("3600.000000"),
        "blocked_stale_age_seconds": d("7200.000000"),
        "watch_overdue_source_count": d("1.000000"),
        "blocked_overdue_source_count": d("2.000000"),
        "min_acknowledged_source_coverage_ratio": d("0.750000"),
        "blocked_acknowledged_source_coverage_ratio": d("0.500000"),
    }
    values.update(overrides)
    return report.TeamMemorySourceRecheckCadenceHealthConfig(**values)


def health_report(*rows, cfg=None):
    report = api()
    return report.build_team_memory_source_recheck_cadence_health_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_empty_input_blocks_with_zero_decimal_counts_and_no_rows() -> None:
    cadence_report = health_report()

    assert is_dataclass(cadence_report)
    assert cadence_report.generated_at == GENERATED_AT
    assert cadence_report.generated_at.tzinfo is UTC
    assert cadence_report.status == "blocked"
    assert cadence_report.reason_codes == ("no_recheck_sources",)
    assert cadence_report.source_count == d("0.000000")
    assert cadence_report.overdue_source_count == d("0.000000")
    assert cadence_report.stale_source_count == d("0.000000")
    assert cadence_report.acknowledged_source_count == d("0.000000")
    assert cadence_report.acknowledged_source_coverage_ratio == d("0.000000")
    assert cadence_report.stale_cadence_age_seconds == d("0.000000")
    assert cadence_report.max_overdue_seconds == d("0.000000")
    assert cadence_report.source_rows == ()
    assert cadence_report.paper_only is True
    assert cadence_report.report_only is True
    assert cadence_report.readonly is True


def test_source_rows_sort_deterministically_by_status_age_and_identifier() -> None:
    cadence_report = health_report(
        source(
            "crypto_eth",
            "source-zulu",
            last_rechecked_age_seconds=1200,
            due_seconds_before_generated_at=-60,
        ),
        source(
            "politics",
            "source-alpha",
            last_rechecked_age_seconds=4200,
            due_seconds_before_generated_at=600,
        ),
        source(
            "crypto_btc",
            "source-bravo",
            last_rechecked_age_seconds=8000,
            due_seconds_before_generated_at=1200,
            acknowledged=False,
        ),
        source(
            "crypto_btc",
            "source-alpha",
            last_rechecked_age_seconds=8000,
            due_seconds_before_generated_at=30,
        ),
    )

    assert tuple((row.status, row.team_id, row.source_id) for row in cadence_report.source_rows) == (
        ("blocked", "crypto_btc", "source-bravo"),
        ("blocked", "crypto_btc", "source-alpha"),
        ("watch", "politics", "source-alpha"),
        ("pass", "crypto_eth", "source-zulu"),
    )
    assert cadence_report.source_rows[0].reason_codes == (
        "source_stale_cadence_blocked",
        "source_recheck_overdue",
        "source_not_acknowledged",
    )


def test_threshold_statuses_and_report_reason_codes_are_deterministic() -> None:
    watch_report = health_report(
        source("politics", "source-alpha", last_rechecked_age_seconds=3601),
        source("crypto_btc", "source-beta", acknowledged=False),
    )

    assert watch_report.status == "watch"
    assert watch_report.reason_codes == (
        "stale_cadence_age_watch",
        "low_acknowledged_source_coverage_watch",
    )
    assert watch_report.stale_source_count == d("1.000000")
    assert watch_report.overdue_source_count == d("0.000000")
    assert watch_report.acknowledged_source_coverage_ratio == d("0.500000")

    blocked_report = health_report(
        source(
            "politics",
            "source-alpha",
            last_rechecked_age_seconds=7201,
            due_seconds_before_generated_at=90,
            acknowledged=False,
        ),
        source(
            "crypto_btc",
            "source-beta",
            last_rechecked_age_seconds=7202,
            due_seconds_before_generated_at=30,
            acknowledged=False,
        ),
        source("crypto_eth", "source-charlie", acknowledged=True),
    )

    assert blocked_report.status == "blocked"
    assert blocked_report.reason_codes == (
        "stale_cadence_age_blocked",
        "overdue_sources_blocked",
        "low_acknowledged_source_coverage_blocked",
    )
    assert blocked_report.source_count == d("3.000000")
    assert blocked_report.overdue_source_count == d("2.000000")
    assert blocked_report.stale_source_count == d("2.000000")
    assert blocked_report.acknowledged_source_count == d("1.000000")
    assert blocked_report.acknowledged_source_coverage_ratio == d("0.333333")
    assert blocked_report.stale_cadence_age_seconds == d("7202.000000")
    assert blocked_report.max_overdue_seconds == d("90.000000")


def test_datetime_inputs_must_be_utc_aware_and_not_future() -> None:
    report = api()

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report.build_team_memory_source_recheck_cadence_health_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )

    with pytest.raises(ValueError, match="last_rechecked_at must be timezone-aware"):
        report.TeamMemorySourceRecheckCadenceInput(
            team_id="politics",
            source_id="source-alpha",
            last_rechecked_at=datetime(2026, 7, 2, 11, 0),
            next_recheck_due_at=GENERATED_AT,
            acknowledged_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="last_rechecked_at must not be after generated_at"):
        health_report(
            report.TeamMemorySourceRecheckCadenceInput(
                team_id="politics",
                source_id="source-alpha",
                last_rechecked_at=GENERATED_AT + timedelta(seconds=1),
                next_recheck_due_at=GENERATED_AT,
                acknowledged_at=GENERATED_AT,
            ),
        )


def test_dataclasses_are_frozen_and_reject_non_decimal_public_numbers() -> None:
    report = api()
    cfg = config()
    row = source()
    cadence_report = health_report(row, cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        row.source_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        cadence_report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(cfg, paper_only=False)
    with pytest.raises(ValueError, match="watch_stale_age_seconds must be a Decimal"):
        report.TeamMemorySourceRecheckCadenceHealthConfig(
            watch_stale_age_seconds=3600,
        )


def test_report_dataclass_rejects_inconsistent_reason_code_surface() -> None:
    cadence_report = health_report(source())

    with pytest.raises(ValueError, match="status must match reason_codes"):
        replace(cadence_report, status="watch")
    with pytest.raises(ValueError, match="source_recheck_cadence_clear must stand alone"):
        replace(
            cadence_report,
            status="watch",
            reason_codes=("overdue_sources_watch", "source_recheck_cadence_clear"),
        )
    with pytest.raises(ValueError, match="no_recheck_sources requires no source_rows"):
        replace(cadence_report, status="blocked", reason_codes=("no_recheck_sources",))
    with pytest.raises(ValueError, match="stale_source_count must match source_rows"):
        replace(cadence_report, stale_source_count=d("1.000000"))


def test_nonnegative_decimal_inputs_normalize_negative_zero() -> None:
    report = api()

    row = report.TeamMemorySourceRecheckCadenceSourceRow(
        team_id="politics",
        source_id="source-alpha",
        last_rechecked_at=GENERATED_AT,
        next_recheck_due_at=GENERATED_AT,
        acknowledged_at=GENERATED_AT,
        acknowledged=True,
        source_age_seconds=d("-0.000000"),
        overdue_seconds=d("-0.000000"),
        status="pass",
        reason_codes=("source_recheck_current",),
    )

    assert str(row.source_age_seconds) == "0.000000"
    assert str(row.overdue_seconds) == "0.000000"


def test_payload_is_json_ready_with_decimal_strings_and_iso_datetimes() -> None:
    payload = api().team_memory_source_recheck_cadence_health_payload(
        health_report(
            source(
                "politics",
                "source-alpha",
                last_rechecked_age_seconds=7201,
                due_seconds_before_generated_at=90,
                acknowledged=False,
            ),
        ),
    )

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["source_count"] == "1.000000"
    assert payload["acknowledged_source_coverage_ratio"] == "0.000000"
    assert payload["source_rows"][0]["source_age_seconds"] == "7201.000000"
    assert payload["source_rows"][0]["overdue_seconds"] == "90.000000"
    assert payload["source_rows"][0]["last_rechecked_at"] == "2026-07-02T09:59:59+00:00"

    def assert_no_float(value: object) -> None:
        assert type(value) is not float
        if isinstance(value, dict):
            for item in value.values():
                assert_no_float(item)
        elif isinstance(value, list):
            for item in value:
                assert_no_float(item)

    assert_no_float(payload)


def test_module_scope_has_no_live_trading_io_or_advice_surface() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/team_memory_source_recheck_cadence_health_report.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "submit",
        "cancel",
        "sign",
        "advice",
        "recommend",
        "market_slug",
        "question",
        "payload_json",
        "open(",
        "read_text",
        "write_text",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
