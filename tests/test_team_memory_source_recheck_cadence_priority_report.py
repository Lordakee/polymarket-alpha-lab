from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_memory_source_recheck_cadence_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "default_recheck_cadence_seconds": d("3600.000000"),
        "low_acknowledged_source_coverage_ratio": d("0.750000"),
        "overdue_source_count_block_threshold": d("2.000000"),
    }
    values.update(overrides)
    return module.TeamMemorySourceRecheckCadencePriorityConfig(**values)


def source_row(
    source_id: str,
    *,
    team_id: str = "politics",
    category_id: str = "politics",
    last_rechecked_seconds_ago: int = 600,
    source_acknowledged_at: datetime | None = GENERATED_AT - timedelta(minutes=5),
    recheck_cadence_seconds: Decimal | None = d("3600.000000"),
) -> Any:
    module = api()
    return module.TeamMemorySourceRecheckCadencePriorityInput(
        team_id=team_id,
        category_id=category_id,
        source_id=source_id,
        source_last_rechecked_at=GENERATED_AT
        - timedelta(seconds=last_rechecked_seconds_ago),
        source_acknowledged_at=source_acknowledged_at,
        recheck_cadence_seconds=recheck_cadence_seconds,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_team_memory_source_recheck_cadence_priority_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_priority_report_returns_empty_readonly_decimal_report() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.TeamMemorySourceRecheckCadencePriorityReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "empty"
    assert report.team_count == d("0.000000")
    assert report.source_count == d("0.000000")
    assert report.acknowledged_source_count == d("0.000000")
    assert report.overdue_source_count == d("0.000000")
    assert report.low_acknowledged_source_coverage_count == d("0.000000")
    assert report.highest_stale_cadence_age_seconds == d("0.000000")
    assert report.acknowledged_source_coverage_ratio == d("0.000000")
    assert report.reason_codes == ("team_memory_source_recheck_cadence_empty",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_priority_report_ranks_by_stale_age_overdue_count_low_coverage_and_ties() -> None:
    report = build_report(
        source_row(
            "politics_old",
            last_rechecked_seconds_ago=7200,
            source_acknowledged_at=None,
        ),
        source_row("politics_fresh"),
        source_row(
            "macro_old",
            team_id="macro_rates",
            category_id="finance.macro.rates",
            last_rechecked_seconds_ago=7200,
            source_acknowledged_at=None,
        ),
        source_row(
            "btc_old_one",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            last_rechecked_seconds_ago=5400,
        ),
        source_row(
            "btc_old_two",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            last_rechecked_seconds_ago=5400,
        ),
        source_row(
            "soccer_fresh",
            team_id="sports_soccer",
            category_id="sports.soccer",
        ),
    )

    assert tuple(row.team_id for row in report.rows) == (
        "macro_rates",
        "politics",
        "crypto_btc",
        "sports_soccer",
    )
    assert tuple(row.stale_cadence_age_seconds for row in report.rows) == (
        d("3600.000000"),
        d("3600.000000"),
        d("1800.000000"),
        d("0.000000"),
    )
    assert tuple(row.overdue_source_count for row in report.rows) == (
        d("1.000000"),
        d("1.000000"),
        d("2.000000"),
        d("0.000000"),
    )
    assert tuple(row.acknowledged_source_coverage_ratio for row in report.rows) == (
        d("0.000000"),
        d("0.500000"),
        d("1.000000"),
        d("1.000000"),
    )
    assert report.team_count == d("4.000000")
    assert report.source_count == d("6.000000")
    assert report.overdue_source_count == d("4.000000")
    assert report.highest_stale_cadence_age_seconds == d("3600.000000")
    assert report.acknowledged_source_coverage_ratio == d("0.666667")


def test_priority_report_thresholds_statuses_and_reason_codes_are_deterministic() -> None:
    report = build_report(
        source_row(
            "backlog_one",
            last_rechecked_seconds_ago=9000,
            source_acknowledged_at=None,
        ),
        source_row(
            "backlog_two",
            last_rechecked_seconds_ago=7200,
        ),
        source_row(
            "coverage_gap",
            team_id="sports_other",
            category_id="sports.other",
            source_acknowledged_at=None,
        ),
    )

    assert report.status == "blocked"
    assert report.reason_codes == (
        "team_memory_source_recheck_cadence_stale",
        "team_memory_source_recheck_cadence_overdue_sources",
        "team_memory_source_recheck_cadence_overdue_backlog",
        "team_memory_source_recheck_cadence_low_acknowledged_source_coverage",
    )

    backlog = report.rows[0]
    assert backlog.team_id == "politics"
    assert backlog.status == "blocked"
    assert backlog.source_count == d("2.000000")
    assert backlog.acknowledged_source_count == d("1.000000")
    assert backlog.overdue_source_count == d("2.000000")
    assert backlog.stale_cadence_age_seconds == d("5400.000000")
    assert backlog.acknowledged_source_coverage_ratio == d("0.500000")
    assert backlog.reason_codes == (
        "team_memory_source_recheck_cadence_stale",
        "team_memory_source_recheck_cadence_overdue_sources",
        "team_memory_source_recheck_cadence_overdue_backlog",
        "team_memory_source_recheck_cadence_low_acknowledged_source_coverage",
    )

    coverage_gap = report.rows[1]
    assert coverage_gap.team_id == "sports_other"
    assert coverage_gap.status == "watch"
    assert coverage_gap.overdue_source_count == d("0.000000")
    assert coverage_gap.stale_cadence_age_seconds == d("0.000000")
    assert coverage_gap.reason_codes == (
        "team_memory_source_recheck_cadence_low_acknowledged_source_coverage",
    )


def test_priority_report_rejects_non_utc_and_future_datetimes() -> None:
    module = api()
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_memory_source_recheck_cadence_priority_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="source_last_rechecked_at must be timezone-aware"):
        module.TeamMemorySourceRecheckCadencePriorityInput(
            team_id="politics",
            category_id="politics",
            source_id="naive_recheck",
            source_last_rechecked_at=datetime(2026, 7, 2, 11, 0),
            source_acknowledged_at=GENERATED_AT,
            recheck_cadence_seconds=d("3600.000000"),
        )
    with pytest.raises(ValueError, match="source_acknowledged_at must be timezone-aware"):
        module.TeamMemorySourceRecheckCadencePriorityInput(
            team_id="politics",
            category_id="politics",
            source_id="naive_ack",
            source_last_rechecked_at=GENERATED_AT,
            source_acknowledged_at=datetime(2026, 7, 2, 11, 0),
            recheck_cadence_seconds=d("3600.000000"),
        )
    with pytest.raises(ValueError, match="source_last_rechecked_at must not be in the future"):
        module.build_team_memory_source_recheck_cadence_priority_report(
            (
                module.TeamMemorySourceRecheckCadencePriorityInput(
                    team_id="politics",
                    category_id="politics",
                    source_id="future_recheck",
                    source_last_rechecked_at=GENERATED_AT + timedelta(seconds=1),
                    source_acknowledged_at=GENERATED_AT,
                    recheck_cadence_seconds=d("3600.000000"),
                ),
            ),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="default_recheck_cadence_seconds must be a Decimal"):
        config(default_recheck_cadence_seconds=_DecimalSubclass("3600.000000"))
    with pytest.raises(ValueError, match="recheck_cadence_seconds must be a Decimal"):
        module.TeamMemorySourceRecheckCadencePriorityInput(
            team_id="politics",
            category_id="politics",
            source_id="int_cadence",
            source_last_rechecked_at=GENERATED_AT,
            source_acknowledged_at=GENERATED_AT,
            recheck_cadence_seconds=3600,
        )


def test_priority_report_exports_frozen_public_dataclasses() -> None:
    module = api()
    report = build_report(source_row("frozen_source"))

    assert module.__all__ == (
        "DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_PRIORITY_CONFIG_VERSION",
        "TeamMemorySourceRecheckCadencePriorityConfig",
        "TeamMemorySourceRecheckCadencePriorityInput",
        "TeamMemorySourceRecheckCadencePriorityReport",
        "TeamMemorySourceRecheckCadencePriorityRow",
        "build_team_memory_source_recheck_cadence_priority_report",
        "team_memory_source_recheck_cadence_priority_report_payload",
    )
    assert is_dataclass(config())
    assert is_dataclass(source_row("frozen_input"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "ready"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"
    with pytest.raises(FrozenInstanceError):
        config().low_acknowledged_source_coverage_ratio = d("0.500000")


def test_priority_report_payload_is_json_ready_with_decimal_strings() -> None:
    module = api()
    report = build_report(
        source_row(
            "json_source",
            last_rechecked_seconds_ago=9000,
            source_acknowledged_at=None,
        ),
    )
    payload = module.team_memory_source_recheck_cadence_priority_report_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["team_count"] == "1.000000"
    assert payload["source_count"] == "1.000000"
    assert payload["acknowledged_source_coverage_ratio"] == "0.000000"
    assert payload["highest_stale_cadence_age_seconds"] == "5400.000000"
    assert payload["rows"][0]["stale_cadence_age_seconds"] == "5400.000000"
    assert payload["rows"][0]["source_age_seconds"] == "9000.000000"
    json.dumps(payload)

    def assert_no_float_values(value: object) -> None:
        if isinstance(value, dict):
            for item in value.values():
                assert_no_float_values(item)
        elif isinstance(value, list):
            for item in value:
                assert_no_float_values(item)
        else:
            assert type(value) is not float

    assert_no_float_values(payload)


def test_priority_report_scope_is_pure_in_memory_report_only() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "market_slug",
        "question",
        "live",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "advice",
        "private_key",
        "credential",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
