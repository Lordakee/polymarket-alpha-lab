from __future__ import annotations

import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from typing import Any

import pytest


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_screen_stage_rollup_report",
    )


def stage_input(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "probability_screen": "pass",
        "team_route": "pass",
        "memory_policy": "pass",
        "source_quality": "pass",
        "cost_gate": "pass",
        "operator_packet": "pass",
        "supabase_readiness": "pass",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    for key, value in overrides.items():
        values[key] = value
    return module.StrategyScreenStageRollupInput(**values)


def rollup(**overrides: object) -> Any:
    module = api()
    return module.build_strategy_screen_stage_rollup_report(stage_input(**overrides))


def test_all_pass_stages_emit_pass_report_with_empty_manual_next_steps() -> None:
    module = api()

    report = rollup()
    payload = module.strategy_screen_stage_rollup_report_payload(report)

    assert module.__all__ == (
        "DEFAULT_STRATEGY_SCREEN_STAGE_ROLLUP_CONFIG_VERSION",
        "STRATEGY_SCREEN_STAGE_SEQUENCE",
        "STRATEGY_SCREEN_STAGE_STATUS_VALUES",
        "STRATEGY_SCREEN_OVERALL_STATUSES",
        "StrategyScreenStageRollupInput",
        "StrategyScreenStageRollupReport",
        "build_strategy_screen_stage_rollup_report",
        "strategy_screen_stage_rollup_report_payload",
        "strategy_screen_stage_rollup_report_digest",
        "validate_strategy_screen_stage_rollup_public_payload",
    )
    assert module.STRATEGY_SCREEN_STAGE_SEQUENCE == (
        "probability_screen",
        "team_route",
        "memory_policy",
        "source_quality",
        "cost_gate",
        "operator_packet",
        "supabase_readiness",
    )
    assert module.STRATEGY_SCREEN_STAGE_STATUS_VALUES == ("pass", "watch", "block")
    assert module.STRATEGY_SCREEN_OVERALL_STATUSES == ("pass", "watch", "block")
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert report.config_version == "strategy-screen-stage-rollup-v0"
    assert report.overall_status == "pass"
    assert report.blocking_stage is None
    assert report.manual_next_steps == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.public_payload == payload
    assert report.digest == module.strategy_screen_stage_rollup_report_digest(report)
    assert payload == {
        "config_version": "strategy-screen-stage-rollup-v0",
        "overall_status": "pass",
        "blocking_stage": None,
        "manual_next_steps": [],
        "stage_statuses": {
            "probability_screen": "pass",
            "team_route": "pass",
            "memory_policy": "pass",
            "source_quality": "pass",
            "cost_gate": "pass",
            "operator_packet": "pass",
            "supabase_readiness": "pass",
        },
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "digest": report.digest,
    }
    assert module.validate_strategy_screen_stage_rollup_public_payload(payload) == payload
    assert _runtime_numeric_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_watch_stages_emit_watch_without_blocking_stage() -> None:
    report = rollup(
        team_route="watch",
        operator_packet="watch",
    )

    assert report.overall_status == "watch"
    assert report.blocking_stage is None
    assert report.manual_next_steps == (
        "review_team_route_stage_before_continuing",
        "review_operator_packet_stage_before_continuing",
    )
    assert report.public_payload["manual_next_steps"] == [
        "review_team_route_stage_before_continuing",
        "review_operator_packet_stage_before_continuing",
    ]


def test_block_stages_emit_block_with_first_blocking_stage_and_blocker_steps() -> None:
    report = rollup(
        probability_screen="watch",
        memory_policy="block",
        source_quality="watch",
        cost_gate="block",
        supabase_readiness="block",
    )

    assert report.overall_status == "block"
    assert report.blocking_stage == "memory_policy"
    assert report.manual_next_steps == (
        "resolve_memory_policy_stage_blocker",
        "resolve_cost_gate_stage_blocker",
        "resolve_supabase_readiness_stage_blocker",
    )
    assert report.public_payload["blocking_stage"] == "memory_policy"


def test_input_and_report_contracts_are_frozen_strict_and_consistent() -> None:
    module = api()
    report = rollup()

    assert is_dataclass(module.StrategyScreenStageRollupInput)
    assert is_dataclass(module.StrategyScreenStageRollupReport)
    assert module.StrategyScreenStageRollupInput.__dataclass_params__.frozen is True
    assert module.StrategyScreenStageRollupReport.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.overall_status = "block"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadInput(module.StrategyScreenStageRollupInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(module.StrategyScreenStageRollupReport):
            pass

    with pytest.raises(ValueError, match="probability_screen"):
        stage_input(probability_screen="ready")
    with pytest.raises(ValueError, match="team_route"):
        stage_input(team_route=True)
    with pytest.raises(ValueError, match="readonly"):
        stage_input(readonly=False)
    with pytest.raises(ValueError, match="manual_next_steps"):
        replace(report, manual_next_steps=("review_team_route_stage_before_continuing",))
    with pytest.raises(ValueError, match="blocking_stage"):
        replace(report, blocking_stage="cost_gate")
    with pytest.raises(ValueError, match="digest"):
        replace(report, digest="0" * 64)

    for field in fields(report):
        assert type(getattr(report, field.name)) is not float


def test_public_payload_rejects_tampering_and_unsafe_stage_labels() -> None:
    module = api()
    report = rollup(team_route="watch")
    payload = dict(report.public_payload)

    with pytest.raises(ValueError, match="overall_status"):
        module.validate_strategy_screen_stage_rollup_public_payload(
            {
                **payload,
                "overall_status": "pass",
            },
        )
    with pytest.raises(ValueError, match="stage_statuses"):
        module.validate_strategy_screen_stage_rollup_public_payload(
            {
                **payload,
                "stage_statuses": {
                    **payload["stage_statuses"],
                    "cost_gate": "block",
                },
            },
        )
    with pytest.raises(ValueError, match="manual_next_steps"):
        module.validate_strategy_screen_stage_rollup_public_payload(
            {
                **payload,
                "manual_next_steps": [],
            },
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.validate_strategy_screen_stage_rollup_public_payload(
            {
                **payload,
                "paper_only": False,
            },
        )
    with pytest.raises(ValueError, match="public payload"):
        module.validate_strategy_screen_stage_rollup_public_payload(
            {
                **payload,
                "stage_statuses": {
                    **payload["stage_statuses"],
                    "wallet": "pass",
                },
            },
        )


def test_module_is_readonly_report_only_and_external_io_free() -> None:
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
        "live",
    ):
        assert forbidden not in source


def _runtime_numeric_paths(value: object, path: str = "") -> tuple[str, ...]:
    if type(value) in (int, float):
        return (path or "<root>",)
    if isinstance(value, dict):
        found: list[str] = []
        for key, item in value.items():
            found.extend(_runtime_numeric_paths(item, f"{path}.{key}" if path else str(key)))
        return tuple(found)
    if isinstance(value, list):
        found = []
        for index, item in enumerate(value):
            found.extend(_runtime_numeric_paths(item, f"{path}[{index}]"))
        return tuple(found)
    return ()
