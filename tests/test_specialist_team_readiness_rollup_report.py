from __future__ import annotations

import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_readiness_rollup_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "operating_cycle_ready": True,
        "learning_dashboard_ready": True,
        "knowledge_base_index_ready": True,
        "assignment_load_balance_ready": True,
        "research_queue_ready": True,
        "memory_update_queue_ready": True,
        "domain_risk_register_ready": True,
        "supabase_memory_ready": True,
    }
    values.update(overrides)
    return module.build_specialist_team_readiness_rollup_report(**values)


def test_rollup_ready_report_exports_public_payload_and_digest() -> None:
    module = api()

    report = build_report()

    assert module.__all__ == (
        "DEFAULT_SPECIALIST_TEAM_READINESS_ROLLUP_CONFIG_VERSION",
        "SPECIALIST_TEAM_READINESS_ROLLUP_BANDS",
        "SpecialistTeamReadinessRollupReport",
        "build_specialist_team_readiness_rollup_report",
        "specialist_team_readiness_rollup_report_payload",
        "specialist_team_readiness_rollup_report_digest",
    )
    assert module.SPECIALIST_TEAM_READINESS_ROLLUP_BANDS == (
        "ready",
        "attention",
        "blocked",
    )
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert report.config_version == "specialist-team-readiness-rollup-v0"
    assert report.specialist_rollup_ready is True
    assert report.rollup_band == "ready"
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == ()
    assert report.ready_ratio == d("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload == module.specialist_team_readiness_rollup_report_payload(report)
    assert payload["ready_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["digest"] == report.digest
    assert report.digest == module.specialist_team_readiness_rollup_report_digest(report)
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_rollup_blocks_when_core_readiness_inputs_are_missing() -> None:
    report = build_report(
        operating_cycle_ready=False,
        research_queue_ready=False,
        domain_risk_register_ready=False,
        supabase_memory_ready=False,
    )

    assert report.specialist_rollup_ready is False
    assert report.rollup_band == "blocked"
    assert report.ready_ratio == d("0.500000")
    assert report.blocked_reason_codes == (
        "operating_cycle_not_ready",
        "research_queue_not_ready",
        "domain_risk_register_not_ready",
        "supabase_memory_not_ready",
    )
    assert report.attention_reason_codes == ()
    assert report.public_payload["blocked_reason_codes"] == [
        "operating_cycle_not_ready",
        "research_queue_not_ready",
        "domain_risk_register_not_ready",
        "supabase_memory_not_ready",
    ]


def test_rollup_uses_attention_band_for_learning_knowledge_and_load_gaps() -> None:
    report = build_report(
        learning_dashboard_ready=False,
        knowledge_base_index_ready=False,
        assignment_load_balance_ready=False,
        memory_update_queue_ready=False,
    )

    assert report.specialist_rollup_ready is False
    assert report.rollup_band == "attention"
    assert report.ready_ratio == d("0.500000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "learning_dashboard_not_ready",
        "knowledge_base_index_not_ready",
        "assignment_load_balance_not_ready",
        "memory_update_queue_not_ready",
    )


def test_rollup_validates_frozen_decimal_only_and_hard_flags() -> None:
    report = build_report(operating_cycle_ready=False)

    for exported_name in api().__all__:
        value = getattr(api(), exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    for field in fields(report):
        item = getattr(report, field.name)
        if field.name == "ready_ratio":
            assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rollup_band = "ready"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="operating_cycle_ready must be a bool"):
        build_report(operating_cycle_ready=1)
    with pytest.raises(ValueError, match="ready_ratio must match readiness flags"):
        replace(report, ready_ratio=d("0.900000"))
    with pytest.raises(ValueError, match="digest must match public payload"):
        replace(report, digest="0" * 64)


def test_module_is_read_only_report_only_and_side_effect_free() -> None:
    source = inspect.getsource(api()).lower()
    for forbidden in (
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "subprocess",
        "open(",
        "read_text",
        "write_text",
        "connect(",
        "execute(",
        "insert",
        "update ",
        "delete(",
        "post(",
        "put(",
        "wallet",
        "trade",
        "auth",
        "order",
        "private_key",
        "live_trading",
    ):
        assert forbidden not in source


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
