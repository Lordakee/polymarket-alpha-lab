from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.team_memory_source_recheck_cadence_exception_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_EXCEPTION_REPORT_CONFIG_VERSION
        ),
        "overdue_recheck_after_seconds": d("86400.000000"),
        "stale_acknowledgement_after_seconds": d("43200.000000"),
        "repeated_overdue_threshold": d("2"),
        "required_source_families": (
            "news",
            "market",
            "resolution",
        ),
    }
    values.update(overrides)
    return module.TeamMemorySourceRecheckCadenceExceptionReportConfig(**values)


def source_row(
    source_id: str,
    team_id: str,
    category_id: str,
    source_family: str,
    *,
    source_checked_at: datetime = GENERATED_AT - timedelta(hours=1),
    source_rechecked_at: datetime | None = GENERATED_AT - timedelta(minutes=30),
    recheck_acknowledged_at: datetime | None = GENERATED_AT - timedelta(minutes=20),
):
    module = api()
    return module.TeamMemorySourceRecheckCadenceSourceRow(
        source_id=source_id,
        team_id=team_id,
        category_id=category_id,
        source_family=source_family,
        source_checked_at=source_checked_at,
        source_rechecked_at=source_rechecked_at,
        recheck_acknowledged_at=recheck_acknowledged_at,
    )


def report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_memory_source_recheck_cadence_exception_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_report_flags_overdue_missing_family_stale_ack_and_repeated_categories() -> None:
    module = api()
    exception_report = report(
        source_row(
            "politics_news_overdue",
            "politics",
            "politics",
            "news",
            source_checked_at=GENERATED_AT - timedelta(days=3),
            source_rechecked_at=None,
            recheck_acknowledged_at=None,
        ),
        source_row(
            "politics_market_stale_ack",
            "politics",
            "politics",
            "market",
            source_checked_at=GENERATED_AT - timedelta(hours=36),
            source_rechecked_at=GENERATED_AT - timedelta(hours=30),
            recheck_acknowledged_at=GENERATED_AT - timedelta(hours=24),
        ),
        source_row(
            "politics_resolution_overdue",
            "politics",
            "politics",
            "resolution",
            source_checked_at=GENERATED_AT - timedelta(hours=60),
            source_rechecked_at=None,
            recheck_acknowledged_at=None,
        ),
        source_row(
            "crypto_news_overdue",
            "crypto_btc",
            "finance.crypto.btc",
            "news",
            source_checked_at=GENERATED_AT - timedelta(days=2),
            source_rechecked_at=None,
            recheck_acknowledged_at=None,
        ),
        source_row(
            "soccer_resolution_current",
            "sports_soccer",
            "sports.soccer",
            "resolution",
        ),
    )

    assert type(exception_report) is module.TeamMemorySourceRecheckCadenceExceptionReport
    assert is_dataclass(exception_report)
    assert exception_report.generated_at == GENERATED_AT
    assert exception_report.config_version == (
        "team-memory-source-recheck-cadence-exception-report-v0"
    )
    assert exception_report.report_status == "blocked"
    assert exception_report.severity_bucket == "critical"
    assert exception_report.source_row_count == d("5")
    assert exception_report.exception_row_count == d("4")
    assert exception_report.overdue_recheck_count == d("3")
    assert exception_report.missing_source_family_evidence_count == d("4")
    assert exception_report.stale_acknowledgement_count == d("4")
    assert exception_report.repeated_overdue_team_count == d("1")
    assert exception_report.repeated_overdue_category_count == d("1")
    assert exception_report.team_rollup_count == d("3")
    assert exception_report.source_family_rollup_count == d("3")
    assert exception_report.exception_source_ratio == d("0.800000")
    assert exception_report.max_recheck_age_seconds == d("259200.000000")
    assert exception_report.max_acknowledgement_age_seconds == d("259200.000000")
    assert exception_report.reason_codes == (
        "source_recheck_overdue",
        "source_family_evidence_missing",
        "source_recheck_acknowledgement_stale",
        "repeated_overdue_team_present",
        "repeated_overdue_category_present",
    )
    assert exception_report.boundary_statement == (
        "Phase 1 pure in-memory report-only reducer for team-memory source recheck cadence exceptions."
    )
    assert exception_report.paper_only is True
    assert exception_report.report_only is True
    assert exception_report.readonly is True

    assert tuple(row.exception_status for row in exception_report.rows) == (
        "overdue_recheck",
        "overdue_recheck",
        "overdue_recheck",
        "stale_acknowledgement",
    )
    politics_overdue = exception_report.rows[0]
    assert politics_overdue == module.TeamMemorySourceRecheckCadenceExceptionRow(
        source_id="politics_news_overdue",
        team_id="politics",
        category_id="politics",
        source_family="news",
        exception_status="overdue_recheck",
        severity_bucket="critical",
        source_checked_at=GENERATED_AT - timedelta(days=3),
        source_rechecked_at=None,
        recheck_acknowledged_at=None,
        recheck_age_seconds=d("259200.000000"),
        acknowledgement_age_seconds=d("259200.000000"),
        overdue_recheck_delta_seconds=d("172800.000000"),
        stale_acknowledgement_delta_seconds=d("216000.000000"),
        missing_source_family_count=d("0"),
        repeated_overdue_team_count=d("2"),
        repeated_overdue_category_count=d("2"),
        reason_codes=(
            "source_recheck_overdue",
            "source_recheck_acknowledgement_stale",
            "repeated_overdue_team_present",
            "repeated_overdue_category_present",
        ),
    )

    assert tuple(row.team_id for row in exception_report.team_rollups) == (
        "politics",
        "crypto_btc",
        "sports_soccer",
    )
    politics_rollup = exception_report.team_rollups[0]
    assert politics_rollup.source_row_count == d("3")
    assert politics_rollup.exception_row_count == d("3")
    assert politics_rollup.overdue_recheck_count == d("2")
    assert politics_rollup.missing_source_family_evidence_count == d("0")
    assert politics_rollup.stale_acknowledgement_count == d("3")
    assert politics_rollup.severity_bucket == "critical"

    family_rollups = {
        row.source_family: row for row in exception_report.source_family_rollups
    }
    assert family_rollups["news"].overdue_recheck_count == d("2")
    assert family_rollups["news"].exception_row_count == d("2")
    assert family_rollups["resolution"].missing_source_family_evidence_count == d("1")
    assert family_rollups["market"].stale_acknowledgement_count == d("1")


def test_repeated_overdue_reasons_are_not_global_cross_team_counts() -> None:
    exception_report = report(
        source_row(
            "politics_news_overdue",
            "politics",
            "politics",
            "news",
            source_checked_at=GENERATED_AT - timedelta(days=2),
            source_rechecked_at=None,
            recheck_acknowledged_at=None,
        ),
        source_row(
            "crypto_news_overdue",
            "crypto_btc",
            "finance.crypto.btc",
            "news",
            source_checked_at=GENERATED_AT - timedelta(days=2),
            source_rechecked_at=None,
            recheck_acknowledged_at=None,
        ),
        cfg=config(required_source_families=("news",)),
    )

    assert exception_report.overdue_recheck_count == d("2")
    assert exception_report.repeated_overdue_team_count == d("0")
    assert exception_report.repeated_overdue_category_count == d("0")
    assert "repeated_overdue_team_present" not in exception_report.reason_codes
    assert "repeated_overdue_category_present" not in exception_report.reason_codes
    assert all(row.repeated_overdue_team_count == d("1") for row in exception_report.rows)
    assert all(
        row.repeated_overdue_category_count == d("1")
        for row in exception_report.rows
    )


def test_report_empty_mapping_inputs_and_json_payload_are_float_free() -> None:
    module = api()
    empty = report()
    mapped = report(
        {
            "source_id": "mapped_source",
            "team_id": "macro_rates",
            "category_id": "finance.macro.rates",
            "source_family": "news",
            "source_checked_at": GENERATED_AT - timedelta(minutes=15),
            "source_rechecked_at": GENERATED_AT - timedelta(minutes=10),
            "recheck_acknowledged_at": GENERATED_AT - timedelta(minutes=5),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )

    assert empty.report_status == "pass"
    assert empty.severity_bucket == "none"
    assert empty.source_row_count == d("0")
    assert empty.rows == ()
    assert empty.team_rollups == ()
    assert empty.source_family_rollups == ()
    assert empty.reason_codes == (
        "no_team_memory_source_recheck_cadence_rows_supplied",
    )
    assert empty.max_recheck_age_seconds is None
    assert empty.max_acknowledgement_age_seconds is None

    assert mapped.report_status == "blocked"
    assert mapped.severity_bucket == "critical"
    assert mapped.source_row_count == d("1")
    assert mapped.exception_row_count == d("1")
    assert mapped.missing_source_family_evidence_count == d("2")
    assert mapped.reason_codes == ("source_family_evidence_missing",)
    assert mapped.rows[0].exception_status == "missing_source_family_evidence"
    assert mapped.rows[0].recheck_age_seconds == d("900.000000")
    assert mapped.rows[0].acknowledgement_age_seconds == d("300.000000")

    payload = module.team_memory_source_recheck_cadence_exception_report_payload(mapped)
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["source_row_count"] == "1.000000"
    assert payload["exception_source_ratio"] == "1.000000"
    assert payload["rows"][0]["recheck_age_seconds"] == "900.000000"
    assert payload["rows"][0]["source_checked_at"] == "2026-07-02T11:45:00+00:00"
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
    payload_text = repr(payload).lower()
    for forbidden in (
        "market_slug",
        "question",
        "payload_json",
        "raw_payload",
        "trading",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "sign",
        "advice",
        "auth",
        "private_key",
    ):
        assert forbidden not in payload_text


def test_dataclasses_are_frozen_decimal_only_and_utc_validated() -> None:
    module = api()
    exception_report = report(
        source_row("current_source", "politics", "politics", "news"),
    )

    assert module.__all__ == (
        "DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_EXCEPTION_REPORT_CONFIG_VERSION",
        "TeamMemorySourceRecheckCadenceExceptionReport",
        "TeamMemorySourceRecheckCadenceExceptionReportConfig",
        "TeamMemorySourceRecheckCadenceExceptionRow",
        "TeamMemorySourceRecheckCadenceSourceFamilyRollup",
        "TeamMemorySourceRecheckCadenceSourceRow",
        "TeamMemorySourceRecheckCadenceTeamRollup",
        "build_team_memory_source_recheck_cadence_exception_report",
        "team_memory_source_recheck_cadence_exception_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    numeric_values = [
        value
        for value in exception_report.__dict__.values()
        if isinstance(value, Decimal)
    ]
    numeric_values.extend(
        value
        for row in exception_report.rows
        for value in row.__dict__.values()
        if isinstance(value, Decimal)
    )
    numeric_values.extend(
        value
        for row in exception_report.team_rollups
        for value in row.__dict__.values()
        if isinstance(value, Decimal)
    )
    numeric_values.extend(
        value
        for row in exception_report.source_family_rollups
        for value in row.__dict__.values()
        if isinstance(value, Decimal)
    )
    assert numeric_values
    assert all(type(value) is Decimal for value in numeric_values)

    with pytest.raises(FrozenInstanceError):
        exception_report.report_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        config(overdue_recheck_after_seconds=_DecimalSubclass("86400.000000"))
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=" team-memory-source-recheck-cadence-exception-report-v0")
    with pytest.raises(ValueError, match="source_family"):
        source_row("bad_family", "politics", "politics", " social ")
    with pytest.raises(ValueError, match="generated_at"):
        module.build_team_memory_source_recheck_cadence_exception_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        report(
            source_row(
                "naive_checked",
                "politics",
                "politics",
                "news",
                source_checked_at=datetime(2026, 7, 2, 11, 0),
            ),
        )
    with pytest.raises(ValueError, match="future"):
        report(
            source_row(
                "future_checked",
                "politics",
                "politics",
                "news",
                source_checked_at=GENERATED_AT + timedelta(seconds=1),
                source_rechecked_at=None,
                recheck_acknowledged_at=None,
            ),
        )
    with pytest.raises(ValueError, match="recheck_acknowledged_at"):
        report(
            source_row(
                "bad_ack_sequence",
                "politics",
                "politics",
                "news",
                source_rechecked_at=GENERATED_AT - timedelta(minutes=10),
                recheck_acknowledged_at=GENERATED_AT - timedelta(minutes=20),
            ),
        )


def test_timezone_aware_inputs_normalize_to_utc_age_seconds() -> None:
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    row = source_row(
        "offset_source",
        "macro_rates",
        "finance.macro.rates",
        "news",
        source_checked_at=datetime(
            2026,
            7,
            2,
            10,
            0,
            tzinfo=timezone(timedelta(hours=2)),
        ),
        source_rechecked_at=datetime(
            2026,
            7,
            2,
            7,
            30,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
        recheck_acknowledged_at=datetime(
            2026,
            7,
            2,
            11,
            45,
            tzinfo=timezone(timedelta(hours=0)),
        ),
    )

    exception_report = report(row, generated_at=generated_at)

    assert exception_report.generated_at == GENERATED_AT
    assert exception_report.rows[0].source_checked_at == datetime(
        2026,
        7,
        2,
        8,
        0,
        tzinfo=UTC,
    )
    assert exception_report.rows[0].source_rechecked_at == datetime(
        2026,
        7,
        2,
        11,
        30,
        tzinfo=UTC,
    )
    assert exception_report.rows[0].recheck_acknowledged_at == datetime(
        2026,
        7,
        2,
        11,
        45,
        tzinfo=UTC,
    )
    assert exception_report.rows[0].recheck_age_seconds == d("14400.000000")
    assert exception_report.rows[0].acknowledgement_age_seconds == d("900.000000")
