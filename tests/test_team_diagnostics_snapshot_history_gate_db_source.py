from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import UTC, datetime
import importlib
import importlib.util
from pathlib import Path
import sys
import types
from typing import Any

import pytest

from polymarket_alpha_lab.team_diagnostics_snapshot_history import (
    TeamDiagnosticsSnapshotHistoryConfig,
)


MODULE_UNDER_TEST = (
    "polymarket_alpha_lab.team_diagnostics_snapshot_history_gate_db_source"
)
GATE_CONTRACT_MODULE = "polymarket_alpha_lab.team_diagnostics_snapshot_history_gate"
GENERATED_AT = datetime(2026, 6, 29, 18, 0, tzinfo=UTC)


@dataclass(frozen=True)
class _HistoryReport:
    status: str = "observed"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class _GateReport:
    gate_status: str = "pass"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _gate_config_type(monkeypatch: pytest.MonkeyPatch) -> type:
    existing = sys.modules.get(GATE_CONTRACT_MODULE)
    if existing is not None and hasattr(existing, "TeamDiagnosticsSnapshotHistoryGateConfig"):
        return existing.TeamDiagnosticsSnapshotHistoryGateConfig  # type: ignore[attr-defined]

    if importlib.util.find_spec(GATE_CONTRACT_MODULE) is not None:
        gate_contract = importlib.import_module(GATE_CONTRACT_MODULE)
        return gate_contract.TeamDiagnosticsSnapshotHistoryGateConfig  # type: ignore[attr-defined]

    gate_contract = types.ModuleType(GATE_CONTRACT_MODULE)

    @dataclass(frozen=True)
    class TeamDiagnosticsSnapshotHistoryGateConfig:
        config_version: str = "team-diagnostics-snapshot-history-gate-v0"
        max_latest_age_seconds: int = 86_400
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    gate_contract.TeamDiagnosticsSnapshotHistoryGateConfig = (
        TeamDiagnosticsSnapshotHistoryGateConfig
    )
    monkeypatch.setitem(sys.modules, GATE_CONTRACT_MODULE, gate_contract)
    return TeamDiagnosticsSnapshotHistoryGateConfig


def _module_under_test(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    _gate_config_type(monkeypatch)
    sys.modules.pop(MODULE_UNDER_TEST, None)
    try:
        return importlib.import_module(MODULE_UNDER_TEST)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_UNDER_TEST:
            pytest.fail(f"{MODULE_UNDER_TEST} does not exist")
        raise


def test_forwards_filters_and_history_options_to_loader_then_builds_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module_under_test(monkeypatch)
    gate_config_type = _gate_config_type(monkeypatch)
    history_config = TeamDiagnosticsSnapshotHistoryConfig()
    gate_config = gate_config_type()
    history_report = _HistoryReport()
    gate_report = _GateReport()
    loader_calls: list[dict[str, object]] = []
    builder_calls: list[tuple[object, object, datetime]] = []

    def history_loader(**kwargs: object) -> _HistoryReport:
        loader_calls.append(kwargs)
        return history_report

    def gate_builder(
        source_report: object,
        *,
        config: object,
        generated_at: datetime,
    ) -> _GateReport:
        builder_calls.append((source_report, config, generated_at))
        return gate_report

    result = module.load_team_diagnostics_snapshot_history_gate_report(
        history_loader=history_loader,
        gate_builder=gate_builder,
        history_config=history_config,
        gate_config=gate_config,
        generated_at=GENERATED_AT,
        team_id="team-alpha",
        market_slug="market-alpha",
        forecast_id="forecast-alpha",
        config_version="snapshot-v1",
        limit=25,
    )

    assert result is gate_report
    assert loader_calls == [
        {
            "config": history_config,
            "generated_at": GENERATED_AT,
            "team_id": "team-alpha",
            "market_slug": "market-alpha",
            "forecast_id": "forecast-alpha",
            "config_version": "snapshot-v1",
            "limit": 25,
        },
    ]
    assert builder_calls == [(history_report, gate_config, GENERATED_AT)]
    assert (
        "load_team_diagnostics_snapshot_history_gate_report"
        in module.__all__
    )


def test_rejects_non_callable_loader_builder_and_non_exact_configs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module_under_test(monkeypatch)
    gate_config_type = _gate_config_type(monkeypatch)
    history_config = TeamDiagnosticsSnapshotHistoryConfig()
    gate_config = gate_config_type()
    calls: list[str] = []

    class HistoryConfigSubclass(TeamDiagnosticsSnapshotHistoryConfig):
        pass

    class GateConfigSubclass(gate_config_type):
        pass

    def history_loader(**_: object) -> _HistoryReport:
        calls.append("history_loader")
        return _HistoryReport()

    def gate_builder(
        source_report: object,
        *,
        config: object,
        generated_at: datetime,
    ) -> _GateReport:
        calls.append("gate_builder")
        return _GateReport()

    with pytest.raises(ValueError, match="history_loader"):
        module.load_team_diagnostics_snapshot_history_gate_report(
            history_loader=object(),
            gate_builder=gate_builder,
            history_config=history_config,
            gate_config=gate_config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="gate_builder"):
        module.load_team_diagnostics_snapshot_history_gate_report(
            history_loader=history_loader,
            gate_builder=object(),
            history_config=history_config,
            gate_config=gate_config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="TeamDiagnosticsSnapshotHistoryConfig"):
        module.load_team_diagnostics_snapshot_history_gate_report(
            history_loader=history_loader,
            gate_builder=gate_builder,
            history_config=object.__new__(HistoryConfigSubclass),
            gate_config=gate_config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="TeamDiagnosticsSnapshotHistoryGateConfig"):
        module.load_team_diagnostics_snapshot_history_gate_report(
            history_loader=history_loader,
            gate_builder=gate_builder,
            history_config=history_config,
            gate_config=object.__new__(GateConfigSubclass),
            generated_at=GENERATED_AT,
        )

    assert calls == []


@pytest.mark.parametrize("flag_name", ["paper_only", "report_only", "readonly"])
def test_requires_returned_gate_report_hard_flags(
    monkeypatch: pytest.MonkeyPatch,
    flag_name: str,
) -> None:
    module = _module_under_test(monkeypatch)
    gate_config_type = _gate_config_type(monkeypatch)

    def history_loader(**_: object) -> _HistoryReport:
        return _HistoryReport()

    def gate_builder(
        source_report: object,
        *,
        config: object,
        generated_at: datetime,
    ) -> Any:
        return _GateReport(**{flag_name: False})

    with pytest.raises(ValueError, match=flag_name):
        module.load_team_diagnostics_snapshot_history_gate_report(
            history_loader=history_loader,
            gate_builder=gate_builder,
            history_config=TeamDiagnosticsSnapshotHistoryConfig(),
            gate_config=gate_config_type(),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize("flag_name", ["paper_only", "report_only", "readonly"])
def test_rejects_returned_gate_report_missing_hard_flags(
    monkeypatch: pytest.MonkeyPatch,
    flag_name: str,
) -> None:
    module = _module_under_test(monkeypatch)
    gate_config_type = _gate_config_type(monkeypatch)

    def history_loader(**_: object) -> _HistoryReport:
        return _HistoryReport()

    def gate_builder(
        source_report: object,
        *,
        config: object,
        generated_at: datetime,
    ) -> Any:
        values = {
            "gate_status": "pass",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
        del values[flag_name]
        return types.SimpleNamespace(**values)

    with pytest.raises(ValueError, match=flag_name):
        module.load_team_diagnostics_snapshot_history_gate_report(
            history_loader=history_loader,
            gate_builder=gate_builder,
            history_config=TeamDiagnosticsSnapshotHistoryConfig(),
            gate_config=gate_config_type(),
            generated_at=GENERATED_AT,
        )


def test_module_has_no_db_env_cli_store_lifecycle_or_write_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module_under_test(monkeypatch)
    module_path = Path(module.__file__)
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    banned_module_fragments = (
        "psycopg",
        "_env",
        "cli",
        "store",
    )
    banned_call_or_attribute_names = {
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "getenv",
        "insert",
        "open",
        "persist",
        "rollback",
        "write",
    }

    assert all(
        fragment not in module_name
        for module_name in imported_modules
        for fragment in banned_module_fragments
    )
    assert not (set(call_names) & banned_call_or_attribute_names)
    assert not (set(attribute_names) & banned_call_or_attribute_names)
