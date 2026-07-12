from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
from typing import Any

import pytest


MODULE_UNDER_TEST = (
    "polymarket_alpha_lab.market_event_resolution_criteria_change_monitor_report"
)


class _DecimalSubclass(Decimal):
    pass


def _module_under_test() -> Any:
    try:
        return importlib.import_module(MODULE_UNDER_TEST)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_UNDER_TEST:
            pytest.fail(f"{MODULE_UNDER_TEST} does not exist")
        raise


def _input(**overrides: object) -> Any:
    module = _module_under_test()
    values: dict[str, object] = {
        "criteria_snapshot_digest_present": True,
        "latest_criteria_digest_matches": True,
        "official_update_count": Decimal("0"),
        "ambiguous_update_count": Decimal("0"),
        "market_close_hours": Decimal("72.000000"),
    }
    values.update(overrides)
    return module.MarketEventResolutionCriteriaChangeMonitorInput(**values)


def _report(**overrides: object) -> Any:
    module = _module_under_test()
    return module.build_market_event_resolution_criteria_change_monitor_report(
        _input(**overrides),
    )


def _assert_no_public_numeric_scalars(value: Any) -> None:
    if type(value) in (Decimal, float, int):
        raise AssertionError(f"unexpected public numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_numeric_scalars(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_public_numeric_scalars(item)


def test_changed_criteria_blocks_with_manual_review_payload_and_digest() -> None:
    module = _module_under_test()

    report = _report(
        latest_criteria_digest_matches=False,
        official_update_count=Decimal("2"),
        ambiguous_update_count=Decimal("1"),
        market_close_hours=Decimal("5.500000"),
    )

    assert type(report) is module.MarketEventResolutionCriteriaChangeMonitorReport
    assert report.criteria_change_status == "changed"
    assert report.reason_codes == (
        "market_event_resolution_criteria_digest_changed",
        "market_event_resolution_criteria_official_updates_present",
        "market_event_resolution_criteria_ambiguous_updates_present",
        "market_event_resolution_criteria_close_window_attention",
    )
    assert report.manual_next_step == (
        "Manually compare official resolution criteria updates before relying on "
        "the market event resolution packet."
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload == module.market_event_resolution_criteria_change_monitor_report_payload(
        report,
    )
    assert payload["criteria_change_status"] == "changed"
    assert payload["official_update_count"] == "2"
    assert payload["ambiguous_update_count"] == "1"
    assert payload["market_close_hours"] == "5.500000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(report.payload_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.payload_digest)
    assert payload["payload_digest"] == report.payload_digest
    assert report.payload_digest == _report(
        latest_criteria_digest_matches=False,
        official_update_count=Decimal("2"),
        ambiguous_update_count=Decimal("1"),
        market_close_hours=Decimal("5.500000"),
    ).payload_digest
    _assert_no_public_numeric_scalars(payload)


def test_missing_snapshot_and_ambiguous_update_counts_drive_attention_status() -> None:
    report = _report(
        criteria_snapshot_digest_present=False,
        latest_criteria_digest_matches=True,
        official_update_count=Decimal("0"),
        ambiguous_update_count=Decimal("2"),
        market_close_hours=Decimal("30"),
    )

    assert report.criteria_change_status == "attention"
    assert report.reason_codes == (
        "market_event_resolution_criteria_snapshot_digest_missing",
        "market_event_resolution_criteria_ambiguous_updates_present",
    )
    assert report.manual_next_step == (
        "Manually capture the current public resolution criteria digest before "
        "closing the monitoring review."
    )


def test_unchanged_criteria_returns_ready_report_only_payload() -> None:
    report = _report()
    payload = report.public_payload

    assert report.criteria_change_status == "unchanged"
    assert report.reason_codes == (
        "market_event_resolution_criteria_unchanged",
    )
    assert report.manual_next_step == (
        "No manual criteria-change action required; keep monitoring in report-only mode."
    )
    assert payload["criteria_change_status"] == "unchanged"
    assert payload["reason_codes"] == [
        "market_event_resolution_criteria_unchanged",
    ]

    with pytest.raises(FrozenInstanceError):
        report.criteria_change_status = "changed"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)


def test_rejects_non_decimal_counts_flags_tampering_and_unsafe_payload() -> None:
    module = _module_under_test()

    with pytest.raises(ValueError, match="official_update_count"):
        _input(official_update_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ambiguous_update_count"):
        _input(ambiguous_update_count=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_close_hours"):
        _input(market_close_hours=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="official_update_count"):
        _input(official_update_count=Decimal("-1"))
    with pytest.raises(ValueError, match="criteria_snapshot_digest_present"):
        _input(criteria_snapshot_digest_present=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        _input(paper_only=False)

    payload = _report(official_update_count=Decimal("1")).public_payload
    assert module.market_event_resolution_criteria_change_monitor_report_payload(payload) == payload

    tampered = dict(payload)
    tampered["official_update_count"] = "0"
    with pytest.raises(ValueError, match="payload_digest must match"):
        module.market_event_resolution_criteria_change_monitor_report_payload(tampered)

    decimal_not_string = dict(payload)
    decimal_not_string["official_update_count"] = Decimal("1")
    with pytest.raises(ValueError, match="Decimal-derived string"):
        module.market_event_resolution_criteria_change_monitor_report_payload(
            decimal_not_string,
        )

    unsafe_key = dict(payload)
    unsafe_key["order_path"] = "blocked"
    with pytest.raises(ValueError, match="unsafe|schema"):
        module.market_event_resolution_criteria_change_monitor_report_payload(
            unsafe_key,
        )

    unsafe_value = dict(payload)
    unsafe_value["manual_next_step"] = "open wallet and sign order"
    with pytest.raises(ValueError, match="unsafe"):
        module.market_event_resolution_criteria_change_monitor_report_payload(
            unsafe_value,
        )

    for cls in (
        module.MarketEventResolutionCriteriaChangeMonitorInput,
        module.MarketEventResolutionCriteriaChangeMonitorReport,
    ):
        public_field_names = {field.name for field in fields(cls)}
        for forbidden in ("live", "auth", "wallet", "order", "key", "sign"):
            assert not any(forbidden in field_name.lower() for field_name in public_field_names)


def test_module_is_pure_readonly_report_scope_without_live_surfaces() -> None:
    module = _module_under_test()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "http",
        "io",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {
        "open",
        "print",
        "input",
        "compile",
        "eval",
        "exec",
        "connect",
        "fetch",
        "request",
        "submit",
        "cancel",
    }
    forbidden_attr_fragments = (
        "client",
        "connection",
        "cursor",
        "session",
    )
    forbidden_source_tokens = (
        "automatic",
        "execute",
        "crawler",
        "scrape",
        "wallet",
        "auth",
        "order",
        "signature",
    )

    for token in forbidden_source_tokens:
        assert token not in source.lower()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = node.names if isinstance(node, ast.Import) else [node]
            for alias in names:
                root = (
                    alias.name
                    if isinstance(node, ast.Import)
                    else (node.module or "")
                ).split(".")[0]
                assert root not in forbidden_import_roots
        if isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in forbidden_call_names
            if isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names
        if isinstance(node, ast.Attribute):
            assert not any(
                fragment in node.attr.lower()
                for fragment in forbidden_attr_fragments
            )
