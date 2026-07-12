from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_source_refresh_sla_readiness_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_source_refresh_sla_readiness_report.py"
)


class DecimalSubclass(Decimal):
    pass


def module() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def item(
    candidate_id: str,
    *,
    official_anchor_age_hours: Decimal = d("1.000000"),
    independent_source_age_hours: Decimal = d("2.000000"),
    refresh_due_hours: Decimal = d("12.000000"),
    contradiction_status: str = "none",
    market_close_hours: Decimal = d("48.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    report_module = module()
    return report_module.MarketSourceRefreshSlaReadinessItem(
        candidate_id=candidate_id,
        official_anchor_age_hours=official_anchor_age_hours,
        independent_source_age_hours=independent_source_age_hours,
        refresh_due_hours=refresh_due_hours,
        contradiction_status=contradiction_status,
        market_close_hours=market_close_hours,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any) -> Any:
    report_module = module()
    return report_module.build_market_source_refresh_sla_readiness_report(
        items,
        config=report_module.MarketSourceRefreshSlaReadinessConfig(
            config_version="market-source-refresh-sla-readiness-test-v0",
            official_anchor_stale_after_hours=d("6.000000"),
            independent_source_stale_after_hours=d("12.000000"),
            refresh_due_soon_hours=d("2.000000"),
            market_close_urgent_hours=d("24.000000"),
        ),
    )


def assert_json_safe_without_public_numbers(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_json_safe_without_public_numbers(item_value)
    elif isinstance(value, list):
        for item_value in value:
            assert_json_safe_without_public_numbers(item_value)
    else:
        assert value is None or isinstance(value, (str, bool))


def test_builds_refresh_sla_readiness_rows_and_rollup() -> None:
    report = build_report(
        item("candidate-pass"),
        item(
            "candidate-due-soon",
            refresh_due_hours=d("1.000000"),
        ),
        item(
            "candidate-official-stale",
            official_anchor_age_hours=d("7.000000"),
        ),
        item(
            "candidate-independent-stale",
            independent_source_age_hours=d("13.000000"),
        ),
        item(
            "candidate-contradiction",
            contradiction_status="confirmed",
        ),
        item(
            "candidate-close-stale",
            official_anchor_age_hours=d("6.000001"),
            market_close_hours=d("2.000000"),
        ),
    )

    assert report.refresh_sla_status == "blocked"
    assert report.candidate_count == d("6.000000")
    assert report.pass_candidate_count == d("1.000000")
    assert report.watch_candidate_count == d("3.000000")
    assert report.blocked_candidate_count == d("2.000000")
    assert report.stale_candidate_count == d("3.000000")
    assert report.contradiction_candidate_count == d("1.000000")
    assert report.due_candidate_count == d("1.000000")
    assert report.urgent_close_candidate_count == d("1.000000")
    assert report.pass_candidate_ratio == d("0.166667")
    assert report.reason_codes == (
        "confirmed_source_contradiction",
        "market_close_refresh_stale_block",
        "refresh_due_within_sla_window",
        "official_anchor_stale",
        "independent_source_stale",
    )
    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-contradiction",
        "candidate-close-stale",
        "candidate-due-soon",
        "candidate-official-stale",
        "candidate-independent-stale",
        "candidate-pass",
    )
    assert tuple(row.refresh_sla_status for row in report.rows) == (
        "blocked",
        "blocked",
        "watch",
        "watch",
        "watch",
        "pass",
    )
    assert report.rows[0].manual_next_step == "block_report_only_source_refresh_review"
    assert report.rows[1].reason_codes == (
        "market_close_refresh_stale_block",
        "official_anchor_stale",
    )
    assert report.rows[2].manual_next_step == "watch_report_only_source_refresh_queue"
    assert report.rows[3].reason_codes == ("official_anchor_stale",)
    assert report.rows[4].reason_codes == ("independent_source_stale",)
    assert report.rows[5].reason_codes == ("source_refresh_sla_ready",)
    assert report.rows[5].manual_next_step == "allow_report_only_source_refresh_readiness"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_stale_information_candidates_can_only_watch_or_block() -> None:
    report = build_report(
        item(
            "candidate-stale-watch",
            official_anchor_age_hours=d("6.000001"),
        ),
        item(
            "candidate-stale-block",
            independent_source_age_hours=d("12.000001"),
            market_close_hours=d("1.000000"),
        ),
    )

    stale_rows = [
        row
        for row in report.rows
        if "official_anchor_stale" in row.reason_codes
        or "independent_source_stale" in row.reason_codes
    ]
    assert stale_rows
    assert {row.refresh_sla_status for row in stale_rows} <= {"watch", "blocked"}
    assert all(not row.manual_next_step.startswith("allow_") for row in stale_rows)
    assert report.rows[0].refresh_sla_status == "blocked"
    assert report.rows[1].refresh_sla_status == "watch"


def test_empty_report_is_report_only_readonly_and_decimal_safe() -> None:
    report_module = module()
    report = build_report()

    assert type(report) is report_module.MarketSourceRefreshSlaReadinessReport
    assert report.refresh_sla_status == "blocked"
    assert report.candidate_count == d("0.000000")
    assert report.pass_candidate_ratio == d("0.000000")
    assert report.reason_codes == ("no_market_source_refresh_candidates",)
    assert report.rows == ()

    payload = report_module.market_source_refresh_sla_readiness_report_payload(report)
    assert payload["candidate_count"] == "0.000000"
    assert payload["pass_candidate_ratio"] == "0.000000"
    assert payload["rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_json_safe_without_public_numbers(payload)
    json.dumps(payload, sort_keys=True)


def test_public_dataclasses_are_frozen_exact_and_decimal_only() -> None:
    report_module = module()
    report = build_report(item("candidate-decimal"))

    assert tuple(report_module.__all__) == (
        "DEFAULT_MARKET_SOURCE_REFRESH_SLA_READINESS_CONFIG_VERSION",
        "MarketSourceRefreshSlaReadinessConfig",
        "MarketSourceRefreshSlaReadinessItem",
        "MarketSourceRefreshSlaReadinessReport",
        "MarketSourceRefreshSlaReadinessRow",
        "build_market_source_refresh_sla_readiness_report",
        "market_source_refresh_sla_readiness_report_payload",
    )
    for exported_name in report_module.__all__:
        value = getattr(report_module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.rows[0].refresh_sla_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        item("candidate-flag", market_close_hours=d("1.000000"), paper_only=False)  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="subclassing"):
        type("DerivedConfig", (report_module.MarketSourceRefreshSlaReadinessConfig,), {})
    with pytest.raises(ValueError, match="official_anchor_stale_after_hours"):
        report_module.MarketSourceRefreshSlaReadinessConfig(
            official_anchor_stale_after_hours=DecimalSubclass("6.000000"),
        )
    with pytest.raises(ValueError, match="official_anchor_age_hours"):
        item("candidate-float", official_anchor_age_hours=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="independent_source_age_hours"):
        item(
            "candidate-unquantized",
            independent_source_age_hours=d("1.0000001"),
        )

    for value in (
        report_module.MarketSourceRefreshSlaReadinessConfig(),
        item("candidate-fields"),
        *report.rows,
        report,
    ):
        for field in fields(value):
            if field.name.endswith(("_count", "_ratio", "_hours")):
                assert type(getattr(value, field.name)) is Decimal


def test_rejects_unknown_contradiction_and_tampered_consistency() -> None:
    report = build_report(item("candidate-valid"))

    with pytest.raises(ValueError, match="contradiction_status"):
        item("candidate-bad-contradiction", contradiction_status="maybe")
    with pytest.raises(ValueError, match="candidate_id"):
        item(" candidate-space ")
    with pytest.raises(ValueError, match="candidate_count"):
        replace(report, candidate_count=d("2.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report.rows[0], reason_codes=("official_anchor_stale",))
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(report.rows[0], manual_next_step="watch_report_only_source_refresh_queue")
    with pytest.raises(ValueError, match="deterministic"):
        replace(
            build_report(item("candidate-b"), item("candidate-a")),
            rows=tuple(reversed(build_report(item("candidate-b"), item("candidate-a")).rows)),
        )


def test_module_is_readonly_report_only_and_external_surface_free() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))

    assert set(_imported_modules(tree)) <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "decimal",
        "typing",
    }
    normalized_names = {
        _normalize_identifier(name)
        for name in _collected_names(tree)
        if _normalize_identifier(name) != "readonly"
    }
    for fragment in (
        "persist",
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "account",
        "broker",
        "submit",
        "cancel",
        "signing",
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
                "read",
                "write",
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
