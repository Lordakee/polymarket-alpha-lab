from __future__ import annotations

import builtins
import dataclasses
import importlib
import inspect
import socket
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


EXPECTED_PHASE1_REPORT_MODULES = (
    "polymarket_alpha_lab.forecast_context_readiness_report",
    "polymarket_alpha_lab.information_freshness_refresh_sla_readiness_report",
    "polymarket_alpha_lab.input_failure_degradation_readiness_report",
    "polymarket_alpha_lab.portfolio_probability_event_readiness_report",
    "polymarket_alpha_lab.post_settlement_calibration_experience_feedback_report",
    "polymarket_alpha_lab.probability_event_cost_adjusted_position_recommendation_report",
    "polymarket_alpha_lab.probability_event_market_signal_risk_readiness_report",
    "polymarket_alpha_lab.strategy_phase1_readiness_aggregator",
)

PHASE1_REPORT_MODULES = EXPECTED_PHASE1_REPORT_MODULES

PHASE1_FLAG_FIELDS = ("paper_only", "report_only", "readonly")

PUBLIC_DATA_CLASSES_WITH_PHASE1_FLAGS = {
    "polymarket_alpha_lab.forecast_context_readiness_report": (
        "ForecastContextReadinessConfig",
        "ForecastContextReadinessInput",
        "ForecastContextReadinessReport",
        "ForecastContextReadinessRow",
        "ForecastContextSource",
    ),
    "polymarket_alpha_lab.information_freshness_refresh_sla_readiness_report": (
        "InformationFreshnessRefreshSlaReadinessConfig",
        "InformationFreshnessRefreshSlaReadinessItem",
        "InformationFreshnessRefreshSlaReadinessReport",
        "InformationFreshnessRefreshSlaReadinessRow",
    ),
    "polymarket_alpha_lab.input_failure_degradation_readiness_report": (
        "InputFailureDegradationReadinessReport",
        "InputFailureSignal",
    ),
    "polymarket_alpha_lab.portfolio_probability_event_readiness_report": (
        "PortfolioProbabilityEventReadinessConfig",
        "PortfolioProbabilityEventReadinessInput",
        "PortfolioProbabilityEventReadinessReport",
        "PortfolioProbabilityEventReadinessRow",
    ),
    "polymarket_alpha_lab.post_settlement_calibration_experience_feedback_report": (
        "PostSettlementCalibrationExperienceConfig",
        "PostSettlementCalibrationExperienceEvent",
        "PostSettlementCalibrationExperienceMemoryQueueItem",
        "PostSettlementCalibrationExperienceReasonCodeCount",
        "PostSettlementCalibrationExperienceReport",
        "PostSettlementCalibrationExperienceRow",
    ),
    "polymarket_alpha_lab.probability_event_cost_adjusted_position_recommendation_report": (
        "ProbabilityEventCostAdjustedPositionRecommendationInput",
        "ProbabilityEventCostAdjustedPositionRecommendationReport",
    ),
    "polymarket_alpha_lab.probability_event_market_signal_risk_readiness_report": (
        "ProbabilityEventMarketSignalRiskReadinessInput",
        "ProbabilityEventMarketSignalRiskReadinessReasonCodeCount",
        "ProbabilityEventMarketSignalRiskReadinessReport",
        "ProbabilityEventMarketSignalRiskReadinessRow",
    ),
    "polymarket_alpha_lab.strategy_phase1_readiness_aggregator": (
        "StrategyPhase1ReadinessReport",
        "StrategyPhase1ReadinessRow",
        "StrategyPhase1ReadinessSignal",
    ),
}


class _ImportIoBlocked(AssertionError):
    pass


def test_phase1_report_module_catalog_matches_current_node() -> None:
    assert PHASE1_REPORT_MODULES == EXPECTED_PHASE1_REPORT_MODULES


@pytest.mark.parametrize("module_name", PHASE1_REPORT_MODULES)
def test_phase1_report_module_imports_do_not_perform_file_network_or_db_io(
    module_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    importlib.import_module("polymarket_alpha_lab")
    _purge_module(module_name)
    _block_import_time_io(monkeypatch)

    imported = importlib.import_module(module_name)

    assert imported.__name__ == module_name


@pytest.mark.parametrize(
    ("module_name", "expected_class_names"),
    tuple(PUBLIC_DATA_CLASSES_WITH_PHASE1_FLAGS.items()),
)
def test_phase1_report_public_dataclass_flags_default_to_hard_readonly_boundary(
    module_name: str,
    expected_class_names: tuple[str, ...],
) -> None:
    module = importlib.import_module(module_name)
    actual_class_names = tuple(
        name
        for name, value in _public_module_dataclasses(module)
        if _has_phase1_flag_fields(value)
    )

    assert actual_class_names == expected_class_names
    for class_name, value in _public_module_dataclasses(module):
        if class_name not in expected_class_names:
            continue
        defaults = _field_defaults(value)
        for flag_name in PHASE1_FLAG_FIELDS:
            assert defaults[flag_name] is True, (module_name, class_name, flag_name)


def test_report_discovery_imports_as_readonly_registry_without_phase1_flag_dataclasses() -> None:
    module = importlib.import_module("polymarket_alpha_lab.report_discovery")

    assert tuple(name for name, _ in _public_module_dataclasses(module)) == (
        "ReportDiscoveryEntry",
        "ReportDiscoveryGroup",
    )
    assert module.report_discovery_groups() == module.REPORT_DISCOVERY_GROUPS


def _purge_module(module_name: str) -> None:
    for loaded_name in tuple(sys.modules):
        if loaded_name == module_name or loaded_name.startswith(f"{module_name}."):
            del sys.modules[loaded_name]


def _block_import_time_io(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def guarded_open(*args: object, **kwargs: object) -> Any:
        raise _ImportIoBlocked(f"import attempted file open: {args!r} {kwargs!r}")

    def guarded_connect(*args: object, **kwargs: object) -> Any:
        raise _ImportIoBlocked(f"import attempted socket connection: {args!r} {kwargs!r}")

    def guarded_create_connection(*args: object, **kwargs: object) -> Any:
        raise _ImportIoBlocked(
            f"import attempted network connection: {args!r} {kwargs!r}",
        )

    def guarded_import(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        if name == "psycopg" or name.startswith("psycopg."):
            raise _ImportIoBlocked(f"import attempted database adapter load: {name}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(Path, "read_text", guarded_open)
    monkeypatch.setattr(Path, "read_bytes", guarded_open)
    monkeypatch.setattr(socket.socket, "connect", guarded_connect, raising=False)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect, raising=False)
    monkeypatch.setattr(socket, "create_connection", guarded_create_connection)
    monkeypatch.setattr(builtins, "__import__", guarded_import)


def _public_module_dataclasses(module: ModuleType) -> tuple[tuple[str, type[object]], ...]:
    return tuple(
        (name, value)
        for name, value in sorted(vars(module).items())
        if not name.startswith("_")
        and inspect.isclass(value)
        and value.__module__ == module.__name__
        and dataclasses.is_dataclass(value)
    )


def _has_phase1_flag_fields(value: type[object]) -> bool:
    return set(PHASE1_FLAG_FIELDS).issubset(_field_defaults(value))


def _field_defaults(value: type[object]) -> dict[str, object]:
    return {field.name: field.default for field in dataclasses.fields(value)}
