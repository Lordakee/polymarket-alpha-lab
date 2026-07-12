import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_screening_pipeline_readiness_report import (
    StrategyScreeningPipelineReadinessReport,
    StrategyScreeningPipelineStageReadiness,
    build_strategy_screening_pipeline_readiness_report,
    strategy_screening_pipeline_readiness_digest,
    strategy_screening_pipeline_readiness_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_screening_pipeline_readiness_report.py"
)
GENERATED_AT = datetime(2026, 7, 11, 15, 30, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def stage(
    ready: bool,
    *,
    reason_codes: tuple[str, ...] = (),
    stage_label: str = "ready source",
) -> StrategyScreeningPipelineStageReadiness:
    return StrategyScreeningPipelineStageReadiness(
        ready=ready,
        reason_codes=reason_codes,
        stage_label=stage_label,
    )


def report(
    *,
    acquisition_ready: StrategyScreeningPipelineStageReadiness | bool = True,
    research_packet_ready: StrategyScreeningPipelineStageReadiness | bool = True,
    source_reliability_ready: StrategyScreeningPipelineStageReadiness | bool = True,
    probability_sanity_ready: StrategyScreeningPipelineStageReadiness | bool = True,
    cost_gate_ready: StrategyScreeningPipelineStageReadiness | bool = True,
    team_routing_ready: StrategyScreeningPipelineStageReadiness | bool = True,
    memory_context_ready: StrategyScreeningPipelineStageReadiness | bool = True,
    position_sizing_ready: StrategyScreeningPipelineStageReadiness | bool = True,
    manual_preflight_ready: StrategyScreeningPipelineStageReadiness | bool = True,
    operator_output_safety_ready: StrategyScreeningPipelineStageReadiness | bool = True,
    generated_at: datetime = GENERATED_AT,
) -> StrategyScreeningPipelineReadinessReport:
    return build_strategy_screening_pipeline_readiness_report(
        generated_at=generated_at,
        acquisition_ready=acquisition_ready,
        research_packet_ready=research_packet_ready,
        source_reliability_ready=source_reliability_ready,
        probability_sanity_ready=probability_sanity_ready,
        cost_gate_ready=cost_gate_ready,
        team_routing_ready=team_routing_ready,
        memory_context_ready=memory_context_ready,
        position_sizing_ready=position_sizing_ready,
        manual_preflight_ready=manual_preflight_ready,
        operator_output_safety_ready=operator_output_safety_ready,
    )


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in walk(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in walk(child))
    return (value,)


def float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if field.name.endswith("_count") or field.name.endswith("_ratio"):
            assert type(value) is Decimal, field.name


def test_builds_deterministic_strategy_screening_pipeline_readiness_report() -> None:
    readiness = report(
        acquisition_ready=stage(False, reason_codes=("acquisition_missing_market_snapshot",)),
        source_reliability_ready=stage(
            False,
            reason_codes=("source_reliability_thin_primary_sources",),
        ),
        cost_gate_ready=stage(
            True,
            reason_codes=("cost_gate_attention_wide_spread",),
        ),
        manual_preflight_ready=stage(
            False,
            reason_codes=("manual_preflight_missing_operator_ack",),
        ),
    )

    assert is_dataclass(readiness)
    assert readiness.pipeline_ready is False
    assert readiness.blocked_stage_count == d("3")
    assert readiness.attention_stage_count == d("1")
    assert readiness.ready_stage_count == d("7")
    assert readiness.total_stage_count == d("10")
    assert readiness.ready_stage_ratio == d("0.700000")
    assert readiness.next_blocked_stage == "acquisition_ready"
    assert readiness.reason_codes == (
        "acquisition_missing_market_snapshot",
        "cost_gate_attention_wide_spread",
        "manual_preflight_missing_operator_ack",
        "source_reliability_thin_primary_sources",
    )
    assert tuple(row.stage_name for row in readiness.stage_rows) == (
        "acquisition_ready",
        "research_packet_ready",
        "source_reliability_ready",
        "probability_sanity_ready",
        "cost_gate_ready",
        "team_routing_ready",
        "memory_context_ready",
        "position_sizing_ready",
        "manual_preflight_ready",
        "operator_output_safety_ready",
    )
    assert readiness.stage_rows[0].status == "blocked"
    assert readiness.stage_rows[0].reason_codes == ("acquisition_missing_market_snapshot",)
    assert readiness.stage_rows[4].status == "attention"
    assert readiness.stage_rows[4].reason_codes == ("cost_gate_attention_wide_spread",)
    assert readiness.stage_rows[-1].status == "ready"
    assert readiness.stage_rows[-1].reason_codes == ("operator_output_safety_ready",)
    assert readiness.paper_only is True
    assert readiness.report_only is True
    assert readiness.readonly is True


def test_all_ready_pipeline_has_no_blocked_stage_and_stable_digest() -> None:
    readiness = report()

    assert readiness == StrategyScreeningPipelineReadinessReport(
        generated_at=GENERATED_AT,
        pipeline_ready=True,
        total_stage_count=d("10"),
        ready_stage_count=d("10"),
        blocked_stage_count=d("0"),
        attention_stage_count=d("0"),
        ready_stage_ratio=d("1.000000"),
        next_blocked_stage=None,
        reason_codes=(
            "acquisition_ready",
            "cost_gate_ready",
            "manual_preflight_ready",
            "memory_context_ready",
            "operator_output_safety_ready",
            "position_sizing_ready",
            "probability_sanity_ready",
            "research_packet_ready",
            "source_reliability_ready",
            "team_routing_ready",
        ),
        stage_rows=readiness.stage_rows,
        public_digest=readiness.public_digest,
    )
    assert len(readiness.public_digest) == 64
    assert readiness.public_digest == strategy_screening_pipeline_readiness_digest(readiness)
    assert all(row.status == "ready" for row in readiness.stage_rows)
    assert all(row.ready is True for row in readiness.stage_rows)


def test_public_payload_uses_decimal_strings_digest_and_no_action_surface() -> None:
    readiness = report(
        probability_sanity_ready=stage(
            False,
            reason_codes=("probability_sanity_probability_out_of_bounds",),
        ),
    )

    payload = strategy_screening_pipeline_readiness_payload(readiness)

    assert payload == readiness.public_payload
    assert payload["generated_at"] == "2026-07-11T15:30:00+00:00"
    assert payload["pipeline_ready"] is False
    assert payload["blocked_stage_count"] == "1"
    assert payload["attention_stage_count"] == "0"
    assert payload["ready_stage_ratio"] == "0.900000"
    assert payload["next_blocked_stage"] == "probability_sanity_ready"
    assert payload["public_digest"] == readiness.public_digest
    assert payload["stage_rows"][3]["stage_name"] == "probability_sanity_ready"
    assert payload["stage_rows"][3]["status"] == "blocked"
    assert payload["stage_rows"][3]["reason_codes"] == [
        "probability_sanity_probability_out_of_bounds",
    ]
    assert float_paths(payload) == ()
    assert not any(isinstance(value, float) for value in walk(payload))
    json.dumps(payload, sort_keys=True)

    lowered = repr(payload).lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "sign",
        "trade",
        "live",
        "execution",
        "database",
    ):
        assert forbidden not in lowered


def test_public_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    readiness = report(research_packet_ready=False)

    with pytest.raises(FrozenInstanceError):
        readiness.pipeline_ready = True  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        readiness.stage_rows[0].status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(generated_at=datetime(2026, 7, 11, 15, 30))
    with pytest.raises(ValueError, match="readiness input must be a bool or StrategyScreeningPipelineStageReadiness"):
        report(acquisition_ready=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ready must be a bool"):
        StrategyScreeningPipelineStageReadiness(ready=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason code must be a non-empty canonical string"):
        stage(False, reason_codes=("bad reason",))
    with pytest.raises(ValueError, match="blocked stages must provide at least one blocker reason"):
        stage(False)
    with pytest.raises(ValueError, match="attention reason codes must contain '_attention'"):
        stage(True, reason_codes=("source_reliability_thin_primary_sources",))
    with pytest.raises(ValueError, match="stage_rows must match canonical stage order"):
        replace(readiness, stage_rows=tuple(reversed(readiness.stage_rows)))
    with pytest.raises(ValueError, match="public_digest must match public payload"):
        replace(readiness, public_digest="0" * 64)
    with pytest.raises(ValueError, match="readonly"):
        replace(readiness, readonly=False)

    assert_public_numeric_fields_are_decimal(readiness)
    for row in readiness.stage_rows:
        assert_public_numeric_fields_are_decimal(row)


def test_module_does_not_import_io_network_db_or_execution_surfaces() -> None:
    tree = compile(
        MODULE_PATH.read_text(encoding="utf-8"),
        str(MODULE_PATH),
        "exec",
        ast.PyCF_ONLY_AST,
    )
    imported_names: set[str] = set()
    call_names: set[str] = set()
    attr_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_names.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                attr_names.add(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attr_names.add(node.attr)

    forbidden_imports = {
        "asyncio",
        "http",
        "jsonlines",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "execute",
        "executemany",
        "submit",
        "cancel",
        "sign",
        "place_order",
        "create_order",
    }
    forbidden_attrs = forbidden_calls

    assert imported_names.isdisjoint(forbidden_imports)
    assert call_names.isdisjoint(forbidden_calls)
    assert attr_names.isdisjoint(forbidden_attrs)
