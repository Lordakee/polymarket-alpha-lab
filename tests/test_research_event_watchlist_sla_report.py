from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_event_watchlist_sla_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_watchlist_sla_report.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} is not implemented")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def item(**overrides: object) -> object:
    module = api()
    values: dict[str, object] = {
        "watchlist_id": "watch_fed_01",
        "event_id": "event_fed_cut",
        "market_slug": "fed-cut-by-september",
        "team_owner_id": "rates_team_lead",
        "last_refreshed_at": GENERATED_AT - timedelta(seconds=600),
        "evidence_checked_at": GENERATED_AT - timedelta(seconds=1800),
        "settlement_at": GENERATED_AT + timedelta(seconds=172800),
        "settlement_checked_at": None,
        "review_requested_at": GENERATED_AT - timedelta(seconds=3600),
        "reviewed_at": GENERATED_AT - timedelta(seconds=1200),
    }
    values.update(overrides)
    return module.ResearchEventWatchlistSlaItem(**values)


def build_report(*items: object, generated_at: datetime = GENERATED_AT) -> object:
    module = api()
    return module.build_research_event_watchlist_sla_report(
        items,
        generated_at=generated_at,
    )


def test_builds_watchlist_sla_report_with_pass_watch_and_block_rows() -> None:
    pass_item = item(
        watchlist_id="watch_pass",
        event_id="event_pass",
        market_slug="fed-cut-by-september",
    )
    watch_item = item(
        watchlist_id="watch_refresh",
        event_id="event_watch",
        market_slug="jobs-print-above-consensus",
        last_refreshed_at=GENERATED_AT - timedelta(seconds=3600),
        evidence_checked_at=GENERATED_AT - timedelta(seconds=900),
        settlement_at=GENERATED_AT + timedelta(seconds=43200),
        settlement_checked_at=GENERATED_AT - timedelta(seconds=600),
        review_requested_at=GENERATED_AT - timedelta(seconds=7200),
        reviewed_at=None,
    )
    block_item = item(
        watchlist_id="watch_block",
        event_id="event_block",
        market_slug="cpi-above-forecast",
        team_owner_id=None,
        last_refreshed_at=GENERATED_AT - timedelta(seconds=1200),
        evidence_checked_at=GENERATED_AT - timedelta(seconds=10800),
        settlement_at=GENERATED_AT + timedelta(seconds=1800),
        settlement_checked_at=None,
        review_requested_at=GENERATED_AT - timedelta(seconds=691200),
        reviewed_at=None,
    )

    report = build_report(watch_item, block_item, pass_item)
    rows = {row.event_id: row for row in report.rows}

    assert tuple(row.event_id for row in report.rows) == (
        "event_block",
        "event_pass",
        "event_watch",
    )
    assert report.report_status == "block"
    assert report.event_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.refresh_frequency_breach_count == d("1.000000")
    assert report.evidence_stale_count == d("1.000000")
    assert report.missing_team_owner_count == d("1.000000")
    assert report.near_settlement_check_due_count == d("2.000000")
    assert report.review_overdue_count == d("1.000000")
    assert report.oldest_refresh_age_seconds == d("3600.000000")
    assert report.oldest_evidence_age_seconds == d("10800.000000")
    assert report.nearest_seconds_to_settlement == d("1800.000000")
    assert report.reason_codes == (
        "watchlist_sla_clear",
        "refresh_frequency_breach",
        "evidence_stale",
        "team_owner_missing",
        "near_settlement_check_missing",
        "review_overdue",
        "watchlist_sla_watch",
        "watchlist_sla_block",
    )

    assert rows["event_pass"].row_status == "pass"
    assert rows["event_pass"].reason_codes == ("watchlist_sla_clear",)
    assert rows["event_pass"].refresh_age_seconds == d("600.000000")
    assert rows["event_pass"].evidence_age_seconds == d("1800.000000")
    assert rows["event_pass"].seconds_to_settlement == d("172800.000000")
    assert rows["event_pass"].near_settlement_check_required is False

    assert rows["event_watch"].row_status == "watch"
    assert rows["event_watch"].refresh_frequency_breach is True
    assert rows["event_watch"].near_settlement_check_required is True
    assert rows["event_watch"].settlement_check_age_seconds == d("600.000000")
    assert rows["event_watch"].reason_codes == (
        "refresh_frequency_breach",
        "watchlist_sla_watch",
    )

    assert rows["event_block"].row_status == "block"
    assert rows["event_block"].team_owner_missing is True
    assert rows["event_block"].evidence_stale is True
    assert rows["event_block"].near_settlement_check_missing is True
    assert rows["event_block"].review_overdue is True
    assert rows["event_block"].reason_codes == (
        "evidence_stale",
        "team_owner_missing",
        "near_settlement_check_missing",
        "review_overdue",
        "watchlist_sla_block",
    )


def test_payload_serializes_decimals_and_exposes_safe_local_field_plan() -> None:
    report = build_report(item(event_id="event_b"), item(event_id="event_a"))
    payload = report.payload

    assert tuple(row.event_id for row in report.rows) == ("event_a", "event_b")
    assert json.dumps(payload, sort_keys=True)
    assert payload["event_count"] == "2.000000"
    assert payload["rows"][0]["refresh_age_seconds"] == "600.000000"
    assert payload["rows"][0]["evidence_age_seconds"] == "1800.000000"
    assert payload["local_field_names"] == list(report.local_field_names)
    assert "table" not in json.dumps(payload).lower()
    assert "dsn" not in json.dumps(payload).lower()
    assert "token" not in json.dumps(payload).lower()
    _assert_no_decimal_objects(payload)
    _assert_public_numeric_values_are_decimal(report)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.ResearchEventWatchlistSlaConfig()
    source = item()
    report = build_report(source)
    row = report.rows[0]

    for value in (config, source, row, report):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        _assert_public_numeric_values_are_decimal(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchEventWatchlistSlaConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        item(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_validation_rejects_non_decimal_future_times_unsafe_text_and_bad_counts() -> None:
    module = api()

    with pytest.raises(ValueError, match="Decimal"):
        module.ResearchEventWatchlistSlaConfig(refresh_max_age_seconds=1800)
    with pytest.raises(ValueError, match="after generated_at"):
        build_report(item(last_refreshed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="reviewed_at must be on or after"):
        item(
            review_requested_at=GENERATED_AT - timedelta(seconds=100),
            reviewed_at=GENERATED_AT - timedelta(seconds=200),
        )
    with pytest.raises(ValueError, match="unsafe public"):
        item(market_slug="wallet-context")

    report = build_report(item())
    with pytest.raises(ValueError, match="event_count"):
        replace(report, event_count=d("2.000000"))
    with pytest.raises(ValueError, match="nonnegative"):
        replace(report.rows[0], refresh_age_seconds=d("-1.000000"))


def test_module_scope_has_no_io_database_credentials_trading_or_order_surface() -> None:
    module = api()
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
        "auth",
        "client",
        "clob",
        "database",
        "db",
        "http",
        "network",
        "persist",
        "psycopg",
        "request",
        "socket",
        "sql",
        "supabase",
        "urllib",
        "wallet",
        "web3",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "open",
        "order",
        "persist",
        "rollback",
        "sell",
        "send",
        "sign",
        "trade",
        "write",
    }
    unsafe_public_terms = (
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_public_terms)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item_value in value.values():
            _assert_no_decimal_objects(item_value)
    if isinstance(value, list):
        for item_value in value:
            _assert_no_decimal_objects(item_value)


def _assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if isinstance(value, (str, datetime)):
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal: {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item_value in value.values():
            _assert_public_numeric_values_are_decimal(item_value)
        return
    if isinstance(value, (list, tuple)):
        for item_value in value:
            _assert_public_numeric_values_are_decimal(item_value)
