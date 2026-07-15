from __future__ import annotations

import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 11, 15, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 11, 14, 30, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_memory_supabase_readiness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    specialist_team_label: str,
    *,
    long_term_memory_table_ready: bool = True,
    memory_event_table_ready: bool = True,
    calibration_table_ready: bool = True,
    local_supabase_schema_contract_ready: bool = True,
    observed_at: datetime = OBSERVED_AT,
):
    return api().SpecialistTeamMemorySupabaseReadinessSignal(
        specialist_team_label=specialist_team_label,
        long_term_memory_table_ready=long_term_memory_table_ready,
        memory_event_table_ready=memory_event_table_ready,
        calibration_table_ready=calibration_table_ready,
        local_supabase_schema_contract_ready=local_supabase_schema_contract_ready,
        observed_at=observed_at,
    )


def build_report(*signals, generated_at: datetime = GENERATED_AT):
    return api().build_specialist_team_memory_supabase_readiness_report(
        signals,
        generated_at=generated_at,
    )


def test_memory_supabase_readiness_aggregates_ready_attention_and_blocker() -> None:
    module = api()

    report = build_report(
        signal("team_macro"),
        signal(
            "team_crypto",
            local_supabase_schema_contract_ready=False,
        ),
        signal(
            "team_politics",
            memory_event_table_ready=False,
            calibration_table_ready=False,
        ),
    )

    assert module.SPECIALIST_TEAM_MEMORY_SUPABASE_READINESS_STATUSES == (
        "ready",
        "attention",
        "blocker",
    )
    assert report.status == "blocker"
    assert report.specialist_team_count == d("3.000000")
    assert report.ready_count == d("1.000000")
    assert report.attention_count == d("1.000000")
    assert report.blocker_count == d("1.000000")
    assert report.ready_ratio == d("0.333333")
    assert report.attention_ratio == d("0.333333")
    assert report.blocker_ratio == d("0.333333")

    blocker, attention, ready = report.rows
    assert tuple(row.specialist_team_label for row in report.rows) == (
        "team_politics",
        "team_crypto",
        "team_macro",
    )
    assert tuple(row.status for row in report.rows) == (
        "blocker",
        "attention",
        "ready",
    )
    assert blocker.ready_signal_count == d("2.000000")
    assert blocker.required_signal_count == d("4.000000")
    assert blocker.readiness_ratio == d("0.500000")
    assert blocker.reason_codes == (
        "specialist_team_memory_event_table_blocker",
        "specialist_team_calibration_table_blocker",
    )
    assert attention.ready_signal_count == d("3.000000")
    assert attention.readiness_ratio == d("0.750000")
    assert attention.reason_codes == (
        "specialist_team_memory_supabase_schema_contract_attention",
    )
    assert ready.ready_signal_count == d("4.000000")
    assert ready.readiness_ratio == d("1.000000")
    assert ready.reason_codes == ("specialist_team_memory_supabase_ready",)

    reason_counts = {
        item.reason_code: (item.specialist_team_count, item.specialist_team_ratio)
        for item in report.reason_code_counts
    }
    assert reason_counts == {
        "specialist_team_memory_event_table_blocker": (
            d("1.000000"),
            d("0.333333"),
        ),
        "specialist_team_calibration_table_blocker": (
            d("1.000000"),
            d("0.333333"),
        ),
        "specialist_team_memory_supabase_schema_contract_attention": (
            d("1.000000"),
            d("0.333333"),
        ),
        "specialist_team_memory_supabase_ready": (d("1.000000"), d("0.333333")),
    }


def test_memory_supabase_readiness_rolls_up_ready_and_attention_states() -> None:
    attention_report = build_report(
        signal("team_macro"),
        signal("team_crypto", local_supabase_schema_contract_ready=False),
    )
    ready_report = build_report(signal("team_macro"), signal("team_crypto"))
    empty_report = build_report()

    assert attention_report.status == "attention"
    assert attention_report.ready_count == d("1.000000")
    assert attention_report.attention_count == d("1.000000")
    assert attention_report.blocker_count == d("0.000000")
    assert attention_report.reason_codes == (
        "specialist_team_memory_supabase_schema_contract_attention",
        "specialist_team_memory_supabase_ready",
    )

    assert ready_report.status == "ready"
    assert ready_report.ready_count == d("2.000000")
    assert ready_report.attention_count == d("0.000000")
    assert ready_report.blocker_count == d("0.000000")
    assert ready_report.ready_ratio == d("1.000000")
    assert ready_report.reason_codes == ("specialist_team_memory_supabase_ready",)

    assert empty_report.status == "ready"
    assert empty_report.specialist_team_count == d("0.000000")
    assert empty_report.ready_ratio == d("0.000000")
    assert empty_report.reason_codes == (
        "specialist_team_memory_supabase_no_specialist_teams",
    )
    assert empty_report.rows == ()
    assert empty_report.reason_code_counts == ()


def test_memory_supabase_readiness_is_frozen_decimal_only_and_paper_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_SPECIALIST_TEAM_MEMORY_SUPABASE_READINESS_CONFIG_VERSION",
        "SPECIALIST_TEAM_MEMORY_SUPABASE_READINESS_STATUSES",
        "SpecialistTeamMemorySupabaseReadinessReasonCodeCount",
        "SpecialistTeamMemorySupabaseReadinessReport",
        "SpecialistTeamMemorySupabaseReadinessRow",
        "SpecialistTeamMemorySupabaseReadinessSignal",
        "build_specialist_team_memory_supabase_readiness_report",
        "specialist_team_memory_supabase_readiness_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    report = build_report(signal("team_macro"))
    for value in (
        signal("team_energy"),
        report,
        *report.rows,
        *report.reason_code_counts,
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(("_count", "_ratio")):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "attention"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="ready_count must be a Decimal"):
        replace(report, ready_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="specialist_team_label"):
        signal("Team Macro")
    with pytest.raises(ValueError, match="long_term_memory_table_ready must be a bool"):
        module.SpecialistTeamMemorySupabaseReadinessSignal(
            specialist_team_label="team_macro",
            long_term_memory_table_ready=1,
            memory_event_table_ready=True,
            calibration_table_ready=True,
            local_supabase_schema_contract_ready=True,
            observed_at=OBSERVED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be UTC-aware"):
        build_report(signal("team_macro"), generated_at=datetime(2026, 7, 11, 15, 0))

    payload = module.specialist_team_memory_supabase_readiness_report_payload(report)
    assert payload["ready_count"] == "1.000000"
    assert payload["rows"][0]["readiness_ratio"] == "1.000000"
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)

    module_source = inspect.getsource(module).lower()
    for forbidden in (
        "create_client",
        "insert(",
        "upsert(",
        "delete(",
        "wallet",
        "live_trading",
    ):
        assert forbidden not in module_source


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
