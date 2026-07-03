from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "market_outcome_freshness_recheck_coverage_report.py"
)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_outcome_freshness_recheck_coverage_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "market-outcome-freshness-recheck-coverage-test-v0",
        "stale_freshness_after_seconds": d("3600.000000"),
        "stale_close_time_after_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return module.MarketOutcomeFreshnessRecheckCoverageConfig(**values)


def item(
    market_id: str,
    *,
    market_slug: str | None = None,
    category_id: str = "politics",
    outcome_id: str = "yes",
    market_closes_at: datetime = datetime(2026, 7, 2, 14, 0, tzinfo=UTC),
    freshness_checked_at: datetime | None = datetime(2026, 7, 2, 11, 45, tzinfo=UTC),
    close_time_checked_at: datetime | None = datetime(2026, 7, 2, 11, 50, tzinfo=UTC),
    expected_outcome_count: Decimal = d("1.000000"),
    resolved_outcome_count: Decimal = d("1.000000"),
):
    module = api()
    return module.MarketOutcomeFreshnessRecheckCoverageInput(
        market_id=market_id,
        market_slug=market_slug or f"{market_id}-slug",
        category_id=category_id,
        outcome_id=outcome_id,
        market_closes_at=market_closes_at,
        freshness_checked_at=freshness_checked_at,
        close_time_checked_at=close_time_checked_at,
        expected_outcome_count=expected_outcome_count,
        resolved_outcome_count=resolved_outcome_count,
    )


def build_report(*items: object, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_market_outcome_freshness_recheck_coverage_report(
        items,
        config=config(),
        generated_at=generated_at,
    )


def assert_json_ready_without_floats(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError("payload must not contain floats")
    if isinstance(value, dict):
        for nested_value in value.values():
            assert_json_ready_without_floats(nested_value)
        return
    if isinstance(value, (list, tuple)):
        for nested_value in value:
            assert_json_ready_without_floats(nested_value)
        return
    assert value is None or isinstance(value, (str, bool))


def test_empty_coverage_report_is_json_ready_with_decimal_zeroes() -> None:
    module = api()
    report = build_report()

    assert report.report_status == "empty"
    assert report.reason_codes == ("no_market_outcome_freshness_recheck_coverage_rows",)
    assert report.market_count == d("0.000000")
    assert report.category_count == d("0.000000")
    assert report.freshness_covered_count == d("0.000000")
    assert report.freshness_gap_count == d("0.000000")
    assert report.unresolved_outcome_count == d("0.000000")
    assert report.stale_close_time_count == d("0.000000")
    assert report.freshness_coverage_ratio == d("0.000000")
    assert report.unresolved_outcome_ratio == d("0.000000")
    assert report.stale_close_time_ratio == d("0.000000")
    assert report.category_rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.market_outcome_freshness_recheck_coverage_report_payload(report)
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["market_count"] == "0.000000"
    assert payload["freshness_coverage_ratio"] == "0.000000"
    assert payload["category_rows"] == []
    assert_json_ready_without_floats(payload)
    json.dumps(payload, sort_keys=True)


def test_report_status_weight_covers_all_report_statuses() -> None:
    module = api()

    assert set(module.REPORT_STATUS_WEIGHT) == set(module.REPORT_STATUSES)
    assert module.REPORT_STATUS_WEIGHT["empty"] < module.REPORT_STATUS_WEIGHT["blocked"]


def test_coverage_report_groups_categories_and_status_reasons_deterministically() -> None:
    report = build_report(
        item(
            "market-ready",
            category_id="politics",
            expected_outcome_count=d("2.000000"),
            resolved_outcome_count=d("2.000000"),
        ),
        item(
            "market-stale-freshness",
            category_id="crypto",
            freshness_checked_at=datetime(2026, 7, 2, 10, 30, tzinfo=UTC),
        ),
        item(
            "market-unresolved",
            category_id="sports",
            expected_outcome_count=d("3.000000"),
            resolved_outcome_count=d("2.000000"),
        ),
        item(
            "market-stale-close",
            category_id="crypto",
            freshness_checked_at=datetime(2026, 7, 2, 11, 30, tzinfo=UTC),
            close_time_checked_at=datetime(2026, 7, 2, 9, 30, tzinfo=UTC),
        ),
        item(
            "market-missing",
            category_id="politics",
            freshness_checked_at=None,
            close_time_checked_at=None,
        ),
    )

    assert report.report_status == "blocked"
    assert report.reason_codes == (
        "unresolved_outcome_coverage_gap",
        "freshness_recheck_coverage_gap",
        "stale_close_time_coverage_gap",
    )
    assert report.market_count == d("5.000000")
    assert report.category_count == d("3.000000")
    assert report.freshness_covered_count == d("3.000000")
    assert report.freshness_gap_count == d("2.000000")
    assert report.unresolved_outcome_count == d("1.000000")
    assert report.stale_close_time_count == d("2.000000")
    assert report.freshness_coverage_ratio == d("0.600000")
    assert report.unresolved_outcome_ratio == d("0.200000")
    assert report.stale_close_time_ratio == d("0.400000")

    assert tuple(row.category_id for row in report.category_rows) == (
        "sports",
        "crypto",
        "politics",
    )
    sports, crypto, politics = report.category_rows
    assert sports.category_status == "blocked"
    assert sports.market_count == d("1.000000")
    assert sports.unresolved_outcome_count == d("1.000000")
    assert sports.reason_codes == ("unresolved_outcome_coverage_gap",)
    assert crypto.category_status == "watch"
    assert crypto.market_count == d("2.000000")
    assert crypto.freshness_covered_count == d("1.000000")
    assert crypto.freshness_gap_count == d("1.000000")
    assert crypto.stale_close_time_count == d("1.000000")
    assert crypto.reason_codes == (
        "freshness_recheck_coverage_gap",
        "stale_close_time_coverage_gap",
    )
    assert politics.category_status == "watch"
    assert politics.market_count == d("2.000000")
    assert politics.freshness_coverage_ratio == d("0.500000")
    assert politics.stale_close_time_ratio == d("0.500000")


def test_ready_report_and_category_sorting_are_input_order_independent() -> None:
    rows = (
        item("market-z", category_id="zeta"),
        item("market-a", category_id="alpha"),
    )
    report = build_report(*reversed(rows))

    assert report.report_status == "ready"
    assert report.reason_codes == ("market_outcome_freshness_recheck_coverage_ready",)
    assert report.freshness_coverage_ratio == d("1.000000")
    assert report.unresolved_outcome_ratio == d("0.000000")
    assert report.stale_close_time_ratio == d("0.000000")
    assert tuple(row.category_id for row in report.category_rows) == ("alpha", "zeta")
    assert tuple(row.category_status for row in report.category_rows) == (
        "ready",
        "ready",
    )


def test_dataclasses_are_frozen_decimal_public_metrics_and_utc_normalized() -> None:
    module = api()
    eastern = timezone(timedelta(hours=-4))
    report = module.build_market_outcome_freshness_recheck_coverage_report(
        (
            item(
                "market-timezone",
                market_closes_at=datetime(2026, 7, 2, 10, 0, tzinfo=eastern),
                freshness_checked_at=datetime(2026, 7, 2, 7, 30, tzinfo=eastern),
                close_time_checked_at=datetime(2026, 7, 2, 7, 40, tzinfo=eastern),
            ),
        ),
        config=config(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=eastern),
    )

    assert module.__all__ == (
        "DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_COVERAGE_CONFIG_VERSION",
        "MarketOutcomeFreshnessRecheckCoverageCategoryRow",
        "MarketOutcomeFreshnessRecheckCoverageConfig",
        "MarketOutcomeFreshnessRecheckCoverageInput",
        "MarketOutcomeFreshnessRecheckCoverageReport",
        "build_market_outcome_freshness_recheck_coverage_report",
        "market_outcome_freshness_recheck_coverage_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    assert report.generated_at == GENERATED_AT
    normalized_input = item(
        "market-offset",
        market_closes_at=datetime(2026, 7, 2, 10, 0, tzinfo=eastern),
        freshness_checked_at=datetime(2026, 7, 2, 7, 30, tzinfo=eastern),
        close_time_checked_at=datetime(2026, 7, 2, 7, 40, tzinfo=eastern),
    )
    assert normalized_input.market_closes_at == datetime(2026, 7, 2, 14, 0, tzinfo=UTC)
    assert normalized_input.freshness_checked_at == datetime(
        2026,
        7,
        2,
        11,
        30,
        tzinfo=UTC,
    )
    assert normalized_input.close_time_checked_at == datetime(
        2026,
        7,
        2,
        11,
        40,
        tzinfo=UTC,
    )

    with pytest.raises(FrozenInstanceError):
        report.report_status = "ready"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.category_rows[0].category_status = "blocked"  # type: ignore[misc]

    public_decimal_suffixes = ("count", "ratio", "seconds")
    for value in (config(), normalized_input, report, *report.category_rows):
        for field in fields(value):
            if field.name.endswith(public_decimal_suffixes):
                assert type(getattr(value, field.name)) is Decimal


def test_rejects_invalid_inputs_flags_and_future_timestamps() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_market_outcome_freshness_recheck_coverage_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="stale_freshness_after_seconds"):
        config(stale_freshness_after_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="stale_close_time_after_seconds"):
        config(stale_close_time_after_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="expected_outcome_count"):
        item("market-float", expected_outcome_count=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="resolved_outcome_count"):
        item(
            "market-over-resolved",
            expected_outcome_count=d("1.000000"),
            resolved_outcome_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="market_id and outcome_id pairs must be unique"):
        build_report(item("market-dup"), item("market-dup"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(item("market-flag"), paper_only=False)
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_market_outcome_freshness_recheck_coverage_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="freshness_checked_at must be <= generated_at"):
        build_report(
            item(
                "market-future-freshness",
                freshness_checked_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="close_time_checked_at must be <= generated_at"):
        build_report(
            item(
                "market-future-close",
                close_time_checked_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )


def test_payload_helper_and_module_surface_avoid_runtime_side_effects() -> None:
    module = api()
    report = build_report(item("market-json"))
    payload = module.market_outcome_freshness_recheck_coverage_report_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["stale_freshness_after_seconds"] == "3600.000000"
    assert payload["category_rows"][0]["market_count"] == "1.000000"
    assert payload["category_rows"][0]["freshness_coverage_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert_json_ready_without_floats(payload)
    json.dumps(payload, sort_keys=True)

    rebuilt_category = module.MarketOutcomeFreshnessRecheckCoverageCategoryRow(
        **{field.name: getattr(report.category_rows[0], field.name) for field in fields(report.category_rows[0])},
    )
    rebuilt_report = module.MarketOutcomeFreshnessRecheckCoverageReport(
        **{field.name: getattr(report, field.name) for field in fields(report)},
    )
    assert rebuilt_category == report.category_rows[0]
    assert rebuilt_report == report

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    assert set(_imported_modules(tree)) <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
    }
    normalized_names = {
        _normalize_identifier(name)
        for name in _collected_names(tree)
        if _normalize_identifier(name) != "readonly"
    }
    for fragment in (
        "db",
        "network",
        "file",
        "live",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "exchange",
        "mutation",
        "signing",
        "advice",
        "secret",
        "password",
        "credential",
        "apikey",
        "privatekey",
        "supabase",
        "postgres",
        "sql",
        "http",
        "request",
        "session",
        "env",
    ):
        assert not any(fragment in name for name in normalized_names), fragment
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "__import__",
                "compile",
                "eval",
                "exec",
                "input",
                "open",
                "print",
            }


def _imported_modules(tree: ast.Module) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return tuple(modules)


def _collected_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            names.add(node.arg)
        elif isinstance(node, ast.alias):
            names.add(node.name)
            if node.asname is not None:
                names.add(node.asname)
    return names


def _normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())
