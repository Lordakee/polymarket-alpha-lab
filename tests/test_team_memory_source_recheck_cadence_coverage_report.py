from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_args, get_origin

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/team_memory_source_recheck_cadence_coverage_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_memory_source_recheck_cadence_coverage_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def target(
    team_id: str,
    category_id: str,
    expected_source_count: str,
) -> Any:
    module = api()
    return module.TeamMemorySourceRecheckCadenceCoverageTarget(
        team_id=team_id,
        category_id=category_id,
        expected_source_count=d(expected_source_count),
    )


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "team_category_targets": (
            target("politics", "politics", "3.000000"),
            target("crypto_btc", "finance.crypto.btc", "2.000000"),
            target("sports_soccer", "sports.soccer", "1.000000"),
        ),
        "min_source_coverage_ratio": d("0.750000"),
        "min_overdue_cadence_coverage_ratio": d("0.750000"),
        "min_acknowledged_source_coverage_ratio": d("0.750000"),
    }
    values.update(overrides)
    return module.TeamMemorySourceRecheckCadenceCoverageConfig(**values)


def source(
    team_id: str,
    category_id: str,
    source_id: str,
    source_family: str,
    *,
    last_rechecked_at: datetime | None = None,
    next_recheck_due_at: datetime | None = None,
    acknowledged_at: datetime | None = None,
) -> Any:
    module = api()
    return module.TeamMemorySourceRecheckCadenceCoverageSource(
        team_id=team_id,
        category_id=category_id,
        source_id=source_id,
        source_family=source_family,
        last_rechecked_at=(
            GENERATED_AT - timedelta(hours=2)
            if last_rechecked_at is None
            else last_rechecked_at
        ),
        next_recheck_due_at=(
            GENERATED_AT + timedelta(hours=2)
            if next_recheck_due_at is None
            else next_recheck_due_at
        ),
        acknowledged_at=acknowledged_at,
    )


def build_report(*sources: Any, config: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_team_memory_source_recheck_cadence_coverage_report(
        sources,
        config=cfg() if config is None else config,
        generated_at=generated_at,
    )


def test_coverage_report_groups_source_overdue_and_acknowledged_coverage() -> None:
    report = build_report(
        source(
            "politics",
            "politics",
            "politics-official",
            "official-results",
            acknowledged_at=GENERATED_AT - timedelta(minutes=10),
        ),
        source(
            "politics",
            "politics",
            "politics-polling",
            "polling",
            next_recheck_due_at=GENERATED_AT - timedelta(hours=2),
            acknowledged_at=None,
        ),
        source(
            "crypto_btc",
            "finance.crypto.btc",
            "btc-official",
            "exchange-filings",
            acknowledged_at=GENERATED_AT - timedelta(minutes=7),
        ),
        source(
            "crypto_btc",
            "finance.crypto.btc",
            "btc-flow",
            "etf-flow",
            acknowledged_at=GENERATED_AT - timedelta(minutes=5),
        ),
    )

    assert is_dataclass(report)
    assert type(report) is api().TeamMemorySourceRecheckCadenceCoverageReport
    assert report.generated_at == GENERATED_AT
    assert (
        report.config_version
        == api().DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_COVERAGE_CONFIG_VERSION
    )
    assert report.report_status == "blocked"
    assert report.team_category_count == d("3.000000")
    assert report.expected_source_count == d("6.000000")
    assert report.source_count == d("4.000000")
    assert report.missing_source_count == d("2.000000")
    assert report.current_cadence_source_count == d("3.000000")
    assert report.overdue_source_count == d("1.000000")
    assert report.acknowledged_source_count == d("3.000000")
    assert report.unacknowledged_source_count == d("1.000000")
    assert report.source_coverage_ratio == d("0.666667")
    assert report.overdue_cadence_coverage_ratio == d("0.750000")
    assert report.acknowledged_source_coverage_ratio == d("0.750000")
    assert report.max_overdue_age_seconds == d("7200.000000")
    assert report.reason_codes == (
        "team_memory_source_recheck_cadence_coverage_source_gap",
        "team_memory_source_recheck_cadence_coverage_overdue_gap",
        "team_memory_source_recheck_cadence_coverage_acknowledgement_gap",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.row_status, row.category_id, row.team_id) for row in report.team_category_rows) == (
        ("blocked", "politics", "politics"),
        ("blocked", "sports.soccer", "sports_soccer"),
        ("pass", "finance.crypto.btc", "crypto_btc"),
    )

    politics = report.team_category_rows[0]
    assert type(politics) is api().TeamMemorySourceRecheckCadenceCoverageTeamCategoryRow
    assert politics.expected_source_count == d("3.000000")
    assert politics.source_count == d("2.000000")
    assert politics.missing_source_count == d("1.000000")
    assert politics.current_cadence_source_count == d("1.000000")
    assert politics.overdue_source_count == d("1.000000")
    assert politics.acknowledged_source_count == d("1.000000")
    assert politics.unacknowledged_source_count == d("1.000000")
    assert politics.source_coverage_ratio == d("0.666667")
    assert politics.overdue_cadence_coverage_ratio == d("0.500000")
    assert politics.acknowledged_source_coverage_ratio == d("0.500000")
    assert politics.max_overdue_age_seconds == d("7200.000000")
    assert politics.latest_rechecked_at == GENERATED_AT - timedelta(hours=2)
    assert politics.latest_acknowledged_at == GENERATED_AT - timedelta(minutes=10)
    assert politics.reason_codes == (
        "team_memory_source_recheck_cadence_coverage_source_gap",
        "team_memory_source_recheck_cadence_coverage_overdue_gap",
        "team_memory_source_recheck_cadence_coverage_acknowledgement_gap",
    )

    soccer = report.team_category_rows[1]
    assert soccer.source_count == d("0.000000")
    assert soccer.source_coverage_ratio == d("0.000000")
    assert soccer.overdue_cadence_coverage_ratio == d("0.000000")
    assert soccer.acknowledged_source_coverage_ratio == d("0.000000")
    assert soccer.latest_rechecked_at is None
    assert soccer.latest_acknowledged_at is None

    btc = report.team_category_rows[2]
    assert btc.row_status == "pass"
    assert btc.reason_codes == (
        "team_memory_source_recheck_cadence_coverage_clear",
    )


def test_empty_coverage_report_blocks_with_decimal_zeroes() -> None:
    report = build_report(config=cfg(team_category_targets=()))

    assert report.report_status == "blocked"
    assert report.reason_codes == (
        "team_memory_source_recheck_cadence_coverage_no_team_categories",
    )
    assert report.team_category_count == d("0.000000")
    assert report.expected_source_count == d("0.000000")
    assert report.source_count == d("0.000000")
    assert report.missing_source_count == d("0.000000")
    assert report.current_cadence_source_count == d("0.000000")
    assert report.overdue_source_count == d("0.000000")
    assert report.acknowledged_source_count == d("0.000000")
    assert report.unacknowledged_source_count == d("0.000000")
    assert report.source_coverage_ratio == d("0.000000")
    assert report.overdue_cadence_coverage_ratio == d("0.000000")
    assert report.acknowledged_source_coverage_ratio == d("0.000000")
    assert report.max_overdue_age_seconds == d("0.000000")
    assert report.team_category_rows == ()


def test_timezone_offsets_normalize_to_utc_and_future_inputs_are_rejected() -> None:
    module = api()
    eastern = timezone(timedelta(hours=-4))
    berlin = timezone(timedelta(hours=2))
    report = module.build_team_memory_source_recheck_cadence_coverage_report(
        (
            source(
                "politics",
                "politics",
                "politics-official",
                "official-results",
                last_rechecked_at=datetime(2026, 7, 2, 7, 30, tzinfo=eastern),
                next_recheck_due_at=datetime(2026, 7, 2, 14, 15, tzinfo=berlin),
                acknowledged_at=datetime(2026, 7, 2, 7, 45, tzinfo=eastern),
            ),
        ),
        config=module.TeamMemorySourceRecheckCadenceCoverageConfig(
            team_category_targets=(target("politics", "politics", "1.000000"),),
        ),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=eastern),
    )

    row = report.team_category_rows[0]
    assert report.generated_at == GENERATED_AT
    assert row.latest_rechecked_at == datetime(2026, 7, 2, 11, 30, tzinfo=UTC)
    assert row.latest_acknowledged_at == datetime(2026, 7, 2, 11, 45, tzinfo=UTC)
    assert row.overdue_source_count == d("0.000000")

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_team_memory_source_recheck_cadence_coverage_report(
            (),
            config=cfg(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="last_rechecked_at must be timezone-aware"):
        source(
            "politics",
            "politics",
            "naive-last",
            "official-results",
            last_rechecked_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="acknowledged_at must not be in the future"):
        build_report(
            source(
                "politics",
                "politics",
                "future-ack",
                "official-results",
                acknowledged_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="last_rechecked_at must not be in the future"):
        build_report(
            source(
                "politics",
                "politics",
                "future-last",
                "official-results",
                last_rechecked_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )


def test_payload_is_json_ready_with_decimal_strings_and_no_floats() -> None:
    payload = api().team_memory_source_recheck_cadence_coverage_report_payload(
        build_report(
            source(
                "politics",
                "politics",
                "politics-official",
                "official-results",
                next_recheck_due_at=GENERATED_AT - timedelta(seconds=90),
                acknowledged_at=GENERATED_AT - timedelta(minutes=2),
            ),
            config=api().TeamMemorySourceRecheckCadenceCoverageConfig(
                team_category_targets=(target("politics", "politics", "1.000000"),),
            ),
        ),
    )

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["source_count"] == "1.000000"
    assert payload["source_coverage_ratio"] == "1.000000"
    assert payload["overdue_cadence_coverage_ratio"] == "0.000000"
    assert payload["acknowledged_source_coverage_ratio"] == "1.000000"
    assert payload["team_category_rows"][0]["max_overdue_age_seconds"] == "90.000000"
    assert payload["team_category_rows"][0]["latest_rechecked_at"] == (
        "2026-07-02T10:00:00+00:00"
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
    assert_no_float_or_decimal_values(payload)

    with pytest.raises(ValueError, match="report must be"):
        api().team_memory_source_recheck_cadence_coverage_report_payload(object())


def test_dataclasses_are_frozen_decimal_typed_and_validate_consistency() -> None:
    module = api()
    report = build_report(
        source(
            "politics",
            "politics",
            "politics-official",
            "official-results",
            acknowledged_at=GENERATED_AT - timedelta(minutes=2),
        ),
        config=module.TeamMemorySourceRecheckCadenceCoverageConfig(
            team_category_targets=(target("politics", "politics", "1.000000"),),
        ),
    )

    assert module.__all__ == (
        "DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_COVERAGE_CONFIG_VERSION",
        "TeamMemorySourceRecheckCadenceCoverageConfig",
        "TeamMemorySourceRecheckCadenceCoverageReport",
        "TeamMemorySourceRecheckCadenceCoverageSource",
        "TeamMemorySourceRecheckCadenceCoverageTarget",
        "TeamMemorySourceRecheckCadenceCoverageTeamCategoryRow",
        "build_team_memory_source_recheck_cadence_coverage_report",
        "team_memory_source_recheck_cadence_coverage_report_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    for value in (
        report,
        report.team_category_rows[0],
        source("politics", "politics", "politics-fresh", "official-results"),
        target("politics", "politics", "1.000000"),
        cfg(),
    ):
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    for dataclass_type in (
        module.TeamMemorySourceRecheckCadenceCoverageConfig,
        module.TeamMemorySourceRecheckCadenceCoverageReport,
        module.TeamMemorySourceRecheckCadenceCoverageTarget,
        module.TeamMemorySourceRecheckCadenceCoverageTeamCategoryRow,
    ):
        for field in fields(dataclass_type):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
            ):
                assert field_allows_decimal(field.type), (
                    dataclass_type,
                    field.name,
                    field.type,
                )

    with pytest.raises(ValueError, match="min_source_coverage_ratio"):
        module.TeamMemorySourceRecheckCadenceCoverageConfig(
            min_source_coverage_ratio=1,
        )
    with pytest.raises(ValueError, match="min_acknowledged_source_coverage_ratio"):
        module.TeamMemorySourceRecheckCadenceCoverageConfig(
            min_acknowledged_source_coverage_ratio=_DecimalSubclass("0.750000"),
        )
    with pytest.raises(ValueError, match="category_id"):
        source(
            "crypto_btc",
            "politics",
            "mismatched-category",
            "official-results",
        )
    with pytest.raises(ValueError, match="source_id"):
        source(
            "politics",
            "politics",
            "wallet-source",
            "official-results",
        )
    for blocked_source_id in (
        "live-source",
        "trading-source",
        "cancel-source",
        "replace-source",
    ):
        with pytest.raises(ValueError, match="source_id"):
            source(
                "politics",
                "politics",
                blocked_source_id,
                "official-results",
            )
    for blocked_source_family in (
        "live-feed",
        "trading-feed",
        "cancel-feed",
        "replace-feed",
    ):
        with pytest.raises(ValueError, match="source_family"):
            source(
                "politics",
                "politics",
                f"family-boundary-{blocked_source_family.split('-', maxsplit=1)[1]}",
                blocked_source_family,
            )
    with pytest.raises(ValueError, match="unique"):
        build_report(
            source("politics", "politics", "duplicate", "official-results"),
            source("politics", "politics", "duplicate", "polling"),
        )
    with pytest.raises(ValueError, match="source_count"):
        replace(report, source_count=d("2.000000"))
    with pytest.raises(ValueError, match="report_status"):
        replace(report, report_status="blocked")


def test_module_scope_is_pure_in_memory_report_only() -> None:
    module_source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = module_source.lower()
    for blocked_text in (
        "db",
        "network",
        "live",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "advice",
    ):
        assert blocked_text not in lowered

    tree = ast.parse(module_source)
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
                "delete",
            }

    assert not any(
        imported_module.split(".", maxsplit=1)[0]
        in {"httpx", "psycopg", "requests", "socket", "subprocess", "urllib"}
        for imported_module in imported_modules
    )


def field_allows_decimal(annotation: object) -> bool:
    if annotation is Decimal:
        return True
    origin = get_origin(annotation)
    if origin in (tuple, list):
        return any(field_allows_decimal(arg) for arg in get_args(annotation))
    if origin is None:
        return False
    return any(arg is type(None) or field_allows_decimal(arg) for arg in get_args(annotation))


def assert_no_float_or_decimal_values(value: object) -> None:
    if isinstance(value, (Decimal, float)):
        raise AssertionError(f"numeric payload leak: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_decimal_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_decimal_values(item)
