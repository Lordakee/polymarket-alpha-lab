from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.probability_event_source_contradiction_aging_report"
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_source_contradiction_aging_report.py",
)
GENERATED_AT = datetime(2026, 7, 11, 15, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api() -> Any:
    return importlib.import_module(MODULE_NAME)


def _input(**overrides: object) -> object:
    api = _api()
    values = {
        "unresolved_contradiction_count": d("2.000000"),
        "oldest_contradiction_age_hours": d("30.000000"),
        "official_anchor_age_hours": d("6.000000"),
        "manual_owner_present": True,
        "market_close_hours": d("96.000000"),
    }
    values.update(overrides)
    return api.ProbabilityEventSourceContradictionAgingInput(**values)


def _config(**overrides: object) -> object:
    api = _api()
    values = {
        "config_version": api.DEFAULT_PROBABILITY_EVENT_SOURCE_CONTRADICTION_AGING_CONFIG_VERSION,
        "watch_contradiction_age_hours": d("24.000000"),
        "block_contradiction_age_hours": d("72.000000"),
        "official_anchor_stale_hours": d("48.000000"),
        "market_close_urgent_hours": d("12.000000"),
    }
    values.update(overrides)
    return api.ProbabilityEventSourceContradictionAgingConfig(**values)


def _report(
    source: object | None = None,
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> object:
    return _api().build_probability_event_source_contradiction_aging_report(
        source or _input(),
        config=cfg or _config(),
        generated_at=generated_at,
    )


def _walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(_walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(_walk_values(item))
        return tuple(nested)
    return (value,)


def test_reports_pass_watch_and_block_contradiction_aging_statuses() -> None:
    api = _api()

    passing = _report(
        _input(
            unresolved_contradiction_count=d("0.000000"),
            oldest_contradiction_age_hours=d("0.000000"),
            official_anchor_age_hours=d("4.000000"),
            manual_owner_present=False,
            market_close_hours=d("120.000000"),
        ),
    )
    watched = _report(
        _input(
            unresolved_contradiction_count=d("1.000000"),
            oldest_contradiction_age_hours=d("30.000000"),
            official_anchor_age_hours=d("8.000000"),
            manual_owner_present=False,
            market_close_hours=d("96.000000"),
        ),
    )
    blocked = _report(
        _input(
            unresolved_contradiction_count=d("3.000000"),
            oldest_contradiction_age_hours=d("80.000000"),
            official_anchor_age_hours=d("60.000000"),
            manual_owner_present=False,
            market_close_hours=d("8.000000"),
        ),
    )

    assert type(blocked) is api.ProbabilityEventSourceContradictionAgingReport
    assert is_dataclass(blocked)
    assert passing.contradiction_aging_status == "pass"
    assert passing.reason_codes == ("no_unresolved_contradictions",)
    assert passing.manual_next_step == "continue_probability_event_source_monitoring"
    assert watched.contradiction_aging_status == "watch"
    assert watched.reason_codes == (
        "unresolved_contradictions_present",
        "contradiction_age_watch",
        "manual_owner_missing",
    )
    assert watched.manual_next_step == "assign_manual_owner_and_recheck_sources"
    assert blocked.contradiction_aging_status == "block"
    assert blocked.reason_codes == (
        "unresolved_contradictions_present",
        "contradiction_age_block",
        "official_anchor_stale",
        "manual_owner_missing",
        "market_close_urgent",
    )
    assert blocked.manual_next_step == "escalate_stale_contradiction_before_market_close"
    assert blocked.generated_at == GENERATED_AT
    assert blocked.paper_only is True
    assert blocked.report_only is True
    assert blocked.readonly is True


def test_payload_is_decimal_string_report_only_readonly_and_digest_checked() -> None:
    api = _api()
    report = _report()

    payload = api.probability_event_source_contradiction_aging_report_payload(report)
    payload_again = api.probability_event_source_contradiction_aging_report_payload(report)

    assert payload == payload_again
    assert payload == report.payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["unresolved_contradiction_count"] == "2.000000"
    assert payload["oldest_contradiction_age_hours"] == "30.000000"
    assert payload["contradiction_aging_status"] == "watch"
    assert payload["manual_next_step"] == "continue_owner_review_of_aging_contradictions"
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))

    tampered = dict(payload)
    tampered["contradiction_aging_status"] = "block"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.probability_event_source_contradiction_aging_report_payload(tampered)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        api.probability_event_source_contradiction_aging_report_payload(downgraded)

    rendered = json.dumps(payload, sort_keys=True).casefold()
    forbidden_terms = (
        "wallet",
        "auth",
        "order",
        "trade",
        "private_key",
        "live",
        "position",
        "sizing",
        "buy",
        "sell",
    )
    assert not any(term in rendered for term in forbidden_terms)


def test_frozen_dataclasses_decimal_only_and_validation_guards() -> None:
    api = _api()
    report = _report()

    for cls_name in (
        "ProbabilityEventSourceContradictionAgingConfig",
        "ProbabilityEventSourceContradictionAgingInput",
        "ProbabilityEventSourceContradictionAgingReport",
    ):
        assert is_dataclass(getattr(api, cls_name))

    with pytest.raises(FrozenInstanceError):
        report.contradiction_aging_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="generated_at"):
        _report(generated_at=_DateTimeSubclass(2026, 7, 11, 15, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="unresolved_contradiction_count"):
        _input(unresolved_contradiction_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="oldest_contradiction_age_hours"):
        _input(oldest_contradiction_age_hours=_DecimalSubclass("30.000000"))
    with pytest.raises(ValueError, match="manual_owner_present"):
        _input(manual_owner_present="true")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_close_hours"):
        _input(market_close_hours=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        _input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    for value in (report,):
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name.endswith(("_count", "_hours")):
                assert type(item) is Decimal


def test_source_has_no_persistence_live_auth_wallet_or_order_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    imports: list[str] = []
    calls: list[str] = []
    string_values: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_values.append(node.value.casefold())

    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "supabase",
    }
    forbidden_calls = {"open", "connect", "execute", "post", "put", "patch", "delete"}
    forbidden_strings = {
        "wallet",
        "auth",
        "order",
        "trade",
        "private_key",
        "live",
        "database",
        "network",
        "position",
        "sizing",
    }
    assert forbidden_imports.isdisjoint(imports)
    assert forbidden_calls.isdisjoint(calls)
    assert not any(term in value for term in forbidden_strings for value in string_values)
