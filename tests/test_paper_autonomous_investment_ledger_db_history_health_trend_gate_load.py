from __future__ import annotations

import ast
import importlib
import sys
import types
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest

GENERATED_AT = datetime(2026, 6, 24, 12, 0, tzinfo=UTC)


@dataclass(frozen=True)
class PaperAutonomousInvestmentLedgerDbHistoryHealthConfig:
    config_version: str = "paper-autonomous-investment-ledger-db-history-health-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig:
    config_version: str = (
        "paper-autonomous-investment-ledger-db-history-health-trend-v0"
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig:
    config_version: str = (
        "paper-autonomous-investment-ledger-db-history-health-trend-gate-v0"
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport:
    generated_at: datetime
    source_trend_report: object
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class NoMutationConnection:
    def cursor(self) -> None:
        raise AssertionError("loader must not open cursors directly")

    def commit(self) -> None:
        raise AssertionError("loader must not commit")

    def rollback(self) -> None:
        raise AssertionError("loader must not rollback")

    def close(self) -> None:
        raise AssertionError("loader must not close")

    def execute(self) -> None:
        raise AssertionError("loader must not execute directly")

    def executemany(self) -> None:
        raise AssertionError("loader must not execute directly")

    def insert(self) -> None:
        raise AssertionError("loader must not write")

    def update(self) -> None:
        raise AssertionError("loader must not write")

    def delete(self) -> None:
        raise AssertionError("loader must not write")

    def upsert(self) -> None:
        raise AssertionError("loader must not write")

    def persist(self) -> None:
        raise AssertionError("loader must not persist")


def _make_health_module_stub() -> types.ModuleType:
    health_module = types.ModuleType(
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health",
    )
    health_module.PaperAutonomousInvestmentLedgerDbHistoryHealthConfig = (
        PaperAutonomousInvestmentLedgerDbHistoryHealthConfig
    )
    return health_module


def _make_health_trend_module_stub() -> types.ModuleType:
    trend_module = types.ModuleType(
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend",
    )
    trend_module.PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig = (
        PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig
    )
    return trend_module


def _make_health_trend_gate_module_stub() -> types.ModuleType:
    gate_module = types.ModuleType(
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend_gate",
    )
    gate_module.PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig = (
        PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig
    )
    gate_module.PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport = (
        PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport
    )

    def build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
        trend_report: object,
        *,
        config: PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig,
        generated_at: datetime,
    ) -> PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport:
        raise AssertionError("test should replace the gate reducer")

    gate_module.build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report = (
        build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report
    )
    return gate_module


def _make_health_trend_loader_module_stub() -> types.ModuleType:
    trend_loader_module = types.ModuleType(
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend_load",
    )

    def load_paper_autonomous_investment_ledger_db_history_health_trend_report(
        connection: object,
        *,
        limit: int | None,
        table_name: str,
        health_config: PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
        trend_config: PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig,
        generated_at: datetime,
    ) -> object:
        raise AssertionError("test should replace the trend loader")

    trend_loader_module.load_paper_autonomous_investment_ledger_db_history_health_trend_report = (
        load_paper_autonomous_investment_ledger_db_history_health_trend_report
    )
    return trend_loader_module


def _load_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    importlib.import_module("polymarket_alpha_lab")
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health",
        _make_health_module_stub(),
    )
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend",
        _make_health_trend_module_stub(),
    )
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend_gate",
        _make_health_trend_gate_module_stub(),
    )
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend_load",
        _make_health_trend_loader_module_stub(),
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend_gate_load",
        None,
    )
    try:
        return importlib.import_module(
            "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend_gate_load",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"loader module is missing: {exc}", pytrace=False)


def test_loader_composes_health_trend_loader_and_gate_reducer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)
    connection = object()
    health_config = PaperAutonomousInvestmentLedgerDbHistoryHealthConfig()
    trend_config = PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig()
    gate_config = PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig()
    trend_report = object()
    expected_gate_report = object()
    trend_loader_calls: list[dict[str, object]] = []
    gate_builder_calls: list[dict[str, object]] = []

    def fake_trend_loader(
        connection: object,
        *,
        limit: int | None,
        table_name: str,
        health_config: PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
        trend_config: PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig,
        generated_at: datetime,
    ) -> object:
        trend_loader_calls.append(
            {
                "connection": connection,
                "limit": limit,
                "table_name": table_name,
                "health_config": health_config,
                "trend_config": trend_config,
                "generated_at": generated_at,
            },
        )
        return trend_report

    def fake_gate_builder(
        received_trend_report: object,
        *,
        config: PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig,
        generated_at: datetime,
    ) -> object:
        gate_builder_calls.append(
            {
                "trend_report": received_trend_report,
                "config": config,
                "generated_at": generated_at,
            },
        )
        return expected_gate_report

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_investment_ledger_db_history_health_trend_report",
        fake_trend_loader,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report",
        fake_gate_builder,
    )

    result = (
        module_under_test
        .load_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
            connection,
            limit=25,
            table_name=(
                "paper_autonomous_investment_ledger_db_history_health_reports_test"
            ),
            health_config=health_config,
            trend_config=trend_config,
            gate_config=gate_config,
            generated_at=GENERATED_AT,
        )
    )

    assert result is expected_gate_report
    assert trend_loader_calls == [
        {
            "connection": connection,
            "limit": 25,
            "table_name": (
                "paper_autonomous_investment_ledger_db_history_health_reports_test"
            ),
            "health_config": health_config,
            "trend_config": trend_config,
            "generated_at": GENERATED_AT,
        },
    ]
    assert gate_builder_calls == [
        {
            "trend_report": trend_report,
            "config": gate_config,
            "generated_at": GENERATED_AT,
        },
    ]


def test_loader_rejects_non_exact_configs_before_trend_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)

    class HealthConfigSubclass(PaperAutonomousInvestmentLedgerDbHistoryHealthConfig):
        pass

    class TrendConfigSubclass(
        PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig,
    ):
        pass

    class GateConfigSubclass(
        PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig,
    ):
        pass

    trend_loader_calls: list[object] = []

    def fake_trend_loader(
        connection: object,
        *,
        limit: int | None,
        table_name: str,
        health_config: PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
        trend_config: PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig,
        generated_at: datetime,
    ) -> object:
        trend_loader_calls.append(connection)
        return object()

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_investment_ledger_db_history_health_trend_report",
        fake_trend_loader,
    )

    invalid_cases = (
        (
            object(),
            PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig(),
            PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig(),
            "health_config must be a PaperAutonomousInvestmentLedgerDbHistoryHealthConfig",
        ),
        (
            HealthConfigSubclass(),
            PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig(),
            PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig(),
            "health_config must be a PaperAutonomousInvestmentLedgerDbHistoryHealthConfig",
        ),
        (
            PaperAutonomousInvestmentLedgerDbHistoryHealthConfig(),
            object(),
            PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig(),
            "trend_config must be a PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig",
        ),
        (
            PaperAutonomousInvestmentLedgerDbHistoryHealthConfig(),
            TrendConfigSubclass(),
            PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig(),
            "trend_config must be a PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig",
        ),
        (
            PaperAutonomousInvestmentLedgerDbHistoryHealthConfig(),
            PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig(),
            object(),
            "gate_config must be a "
            "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig",
        ),
        (
            PaperAutonomousInvestmentLedgerDbHistoryHealthConfig(),
            PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig(),
            GateConfigSubclass(),
            "gate_config must be a "
            "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig",
        ),
    )

    for (
        health_config,
        trend_config,
        gate_config,
        message,
    ) in invalid_cases:
        with pytest.raises(ValueError, match=message):
            (
                module_under_test
                .load_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
                    object(),
                    limit=5,
                    table_name=(
                        "paper_autonomous_investment_ledger_db_history_health_reports_test"
                    ),
                    health_config=health_config,
                    trend_config=trend_config,
                    gate_config=gate_config,
                    generated_at=GENERATED_AT,
                )
            )

    assert trend_loader_calls == []


def test_loader_does_not_manage_connection_lifecycle_or_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)
    connection = NoMutationConnection()
    health_config = PaperAutonomousInvestmentLedgerDbHistoryHealthConfig()
    trend_config = PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig()
    gate_config = PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig()
    trend_report = object()
    expected_gate_report = object()
    trend_loader_calls: list[object] = []
    gate_builder_calls: list[dict[str, object]] = []

    def fake_trend_loader(
        received_connection: object,
        *,
        limit: int | None,
        table_name: str,
        health_config: PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
        trend_config: PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig,
        generated_at: datetime,
    ) -> object:
        trend_loader_calls.append(received_connection)
        return trend_report

    def fake_gate_builder(
        received_trend_report: object,
        *,
        config: PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig,
        generated_at: datetime,
    ) -> object:
        gate_builder_calls.append(
            {
                "trend_report": received_trend_report,
                "config": config,
                "generated_at": generated_at,
            },
        )
        return expected_gate_report

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_investment_ledger_db_history_health_trend_report",
        fake_trend_loader,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report",
        fake_gate_builder,
    )

    result = (
        module_under_test
        .load_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
            connection,
            limit=2,
            table_name=(
                "paper_autonomous_investment_ledger_db_history_health_reports_test"
            ),
            health_config=health_config,
            trend_config=trend_config,
            gate_config=gate_config,
            generated_at=GENERATED_AT,
        )
    )

    assert result is expected_gate_report
    assert trend_loader_calls == [connection]
    assert gate_builder_calls == [
        {
            "trend_report": trend_report,
            "config": gate_config,
            "generated_at": GENERATED_AT,
        },
    ]


def test_loader_module_has_no_db_lifecycle_env_cli_or_live_trading_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)
    module_path = module_under_test.__file__
    assert module_path is not None
    source = Path(module_path).read_text(encoding="utf-8")
    tree = ast.parse(source)

    banned_names = {
        "psycopg",
        "supabase",
        "environ",
        "migration",
        "commit",
        "rollback",
        "cursor",
        "execute",
        "executemany",
        "insert",
        "update",
        "delete",
        "upsert",
        "persist",
        "auth",
        "client",
        "exchange",
        "network",
        "wallet",
        "account",
        "order",
        "execution",
        "approval",
        "trade",
        "sign",
        "submit",
        "cancel",
        "replace",
    }
    observed_names: set[str] = set()
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
                observed_names.add(alias.name.split(".", maxsplit=1)[0])
                if alias.asname is not None:
                    observed_names.add(alias.asname)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imported_modules.add(node.module)
                observed_names.update(node.module.split("."))
            for alias in node.names:
                observed_names.add(alias.name)
                if alias.asname is not None:
                    observed_names.add(alias.asname)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                observed_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                observed_names.add(function.attr)
        elif isinstance(node, ast.Attribute):
            observed_names.add(node.attr)
        elif isinstance(node, ast.Name):
            observed_names.add(node.id)

    allowed_modules = {
        "__future__",
        "datetime",
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history",
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health",
        (
            "polymarket_alpha_lab."
            "paper_autonomous_investment_ledger_db_history_health_trend"
        ),
        (
            "polymarket_alpha_lab."
            "paper_autonomous_investment_ledger_db_history_health_trend_gate"
        ),
        (
            "polymarket_alpha_lab."
            "paper_autonomous_investment_ledger_db_history_health_trend_load"
        ),
    }

    assert imported_modules <= allowed_modules
    assert not (observed_names & banned_names)
