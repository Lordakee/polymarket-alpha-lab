from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_routing_drift_monitor_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_routing_drift_monitor_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def drift_input(**overrides: object) -> Any:
    values: dict[str, object] = {
        "previous_primary_team": "macro_team",
        "current_primary_team": "macro_team",
        "route_confidence_delta": d("0.000000"),
        "category_id": "finance.macro",
        "memory_policy_status": "pass",
        "source_quorum_status": "pass",
    }
    values.update(overrides)
    return api().SpecialistTeamRoutingDriftMonitorInput(**values)


def build_report(**overrides: object) -> Any:
    module = api()
    return module.build_specialist_team_routing_drift_monitor_report(
        drift_input(**overrides),
        config=module.SpecialistTeamRoutingDriftMonitorConfig(),
    )


def test_blocks_changed_team_with_large_confidence_drop_and_policy_gaps() -> None:
    module = api()

    report = build_report(
        previous_primary_team="macro_team",
        current_primary_team="crypto_team",
        route_confidence_delta=d("-0.420000"),
        category_id="finance.crypto",
        memory_policy_status="block",
        source_quorum_status="watch",
    )
    payload = module.specialist_team_routing_drift_monitor_report_payload(report)

    assert module.SPECIALIST_TEAM_ROUTING_DRIFT_MONITOR_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.config_version == (
        module.DEFAULT_SPECIALIST_TEAM_ROUTING_DRIFT_MONITOR_CONFIG_VERSION
    )
    assert report.routing_drift_status == "block"
    assert report.reason_codes == (
        "specialist_team_routing_drift_team_changed",
        "specialist_team_routing_drift_confidence_drop_block",
        "specialist_team_routing_drift_memory_policy_block",
        "specialist_team_routing_drift_source_quorum_watch",
    )
    assert report.manual_next_step == "manual_escalate_routing_drift_review"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert payload["route_confidence_delta"] == "-0.420000"
    assert payload["routing_drift_status"] == "block"
    assert payload["manual_next_step"] == "manual_escalate_routing_drift_review"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_passes_stable_route_and_watches_soft_drift_without_side_effects() -> None:
    clear = build_report()

    assert clear.routing_drift_status == "pass"
    assert clear.reason_codes == ("specialist_team_routing_drift_clear",)
    assert clear.manual_next_step == "manual_no_action"

    confidence_watch = build_report(route_confidence_delta=d("-0.160000"))
    assert confidence_watch.routing_drift_status == "watch"
    assert confidence_watch.reason_codes == (
        "specialist_team_routing_drift_confidence_drop_watch",
    )
    assert confidence_watch.manual_next_step == "manual_review_routing_drift_evidence"

    changed_team = build_report(
        previous_primary_team="macro_team",
        current_primary_team="rates_team",
        route_confidence_delta=d("0.010000"),
    )
    assert changed_team.routing_drift_status == "watch"
    assert changed_team.reason_codes == (
        "specialist_team_routing_drift_team_changed",
    )
    assert changed_team.manual_next_step == "manual_review_routing_drift_evidence"


def test_contract_is_frozen_decimal_only_report_only_and_strictly_validated() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_SPECIALIST_TEAM_ROUTING_DRIFT_MONITOR_CONFIG_VERSION",
        "SPECIALIST_TEAM_ROUTING_DRIFT_MONITOR_STATUSES",
        "SpecialistTeamRoutingDriftMonitorConfig",
        "SpecialistTeamRoutingDriftMonitorInput",
        "SpecialistTeamRoutingDriftMonitorReport",
        "build_specialist_team_routing_drift_monitor_report",
        "specialist_team_routing_drift_monitor_report_digest",
        "specialist_team_routing_drift_monitor_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    cfg = module.SpecialistTeamRoutingDriftMonitorConfig()
    item = drift_input()
    report = build_report(route_confidence_delta=d("-0.420000"))

    for value in (cfg, item, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            public_value = getattr(value, field.name)
            if field.name.endswith("_delta") or field.name.endswith("_threshold"):
                assert type(public_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.routing_drift_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(cfg, paper_only=False)
    with pytest.raises(ValueError, match="route_confidence_delta must be exactly Decimal"):
        drift_input(route_confidence_delta=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="route_confidence_delta must be exactly Decimal"):
        drift_input(route_confidence_delta=_DecimalSubclass("-0.100000"))
    with pytest.raises(ValueError, match="route_confidence_delta must be >= -1.000000"):
        drift_input(route_confidence_delta=d("-1.000001"))
    with pytest.raises(ValueError, match="category_id must be public"):
        drift_input(category_id="market_slug")
    with pytest.raises(ValueError, match="memory_policy_status"):
        drift_input(memory_policy_status="unknown")
    with pytest.raises(ValueError, match="routing_drift_status must match reason_codes"):
        replace(report, routing_drift_status="pass")


def test_payload_rejects_tampering_leaks_and_forbidden_capabilities() -> None:
    module = api()
    report = build_report(
        previous_primary_team="macro_team",
        current_primary_team="crypto_team",
        route_confidence_delta=d("-0.420000"),
        memory_policy_status="block",
    )
    payload = module.specialist_team_routing_drift_monitor_report_payload(report)

    tampered = dict(payload)
    tampered["routing_drift_status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.specialist_team_routing_drift_monitor_report_payload(tampered)

    for unsafe_key, unsafe_value in (
        ("market_slug", "opaque"),
        ("wallet", "opaque"),
        ("auth", "opaque"),
        ("order_ticket", "opaque"),
        ("live_flag", "opaque"),
    ):
        leaked = dict(payload)
        leaked[unsafe_key] = unsafe_value
        leaked["derived_validation_digest"] = canonical_digest(leaked)
        with pytest.raises(ValueError, match="unsafe"):
            module.specialist_team_routing_drift_monitor_report_payload(leaked)

    assert (
        module.specialist_team_routing_drift_monitor_report_digest(report)
        == payload["derived_validation_digest"]
    )

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "asyncio",
        "httpx",
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
    forbidden_call_names = {"__import__", "eval", "exec", "open", "print"}
    imports: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name is not None:
                calls.add(call_name)
    assert imports.isdisjoint(forbidden_import_roots)
    assert calls.isdisjoint(forbidden_call_names)

    text = MODULE_PATH.read_text(encoding="utf-8").casefold()
    for forbidden in ("live", "auth", "wallet", "order"):
        assert forbidden not in text


def _float_paths(value: object, path: str = "") -> tuple[str, ...]:
    if type(value) is float:
        return (path or "<root>",)
    if isinstance(value, dict):
        found: list[str] = []
        for key, item in value.items():
            found.extend(_float_paths(item, f"{path}.{key}" if path else str(key)))
        return tuple(found)
    if isinstance(value, list):
        found = []
        for index, item in enumerate(value):
            found.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(found)
    return ()


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
