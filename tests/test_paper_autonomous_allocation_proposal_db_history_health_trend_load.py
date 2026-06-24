from __future__ import annotations

import ast
import importlib
import sys
import types
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
    PaperAutonomousAllocationProposalDbHistoryConfig,
)


GENERATED_AT = datetime(2026, 6, 24, 12, 0, tzinfo=UTC)


@dataclass(frozen=True)
class HistoryReport:
    name: str
    generated_at: datetime


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryHealthConfig:
    config_version: str = "paper-autonomous-allocation-proposal-db-history-health-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryHealthReport:
    generated_at: datetime
    health_status: str
    source_history_reports: tuple[object, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig:
    config_version: str = "paper-autonomous-allocation-proposal-db-history-health-trend-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryHealthTrendReport:
    generated_at: datetime
    source_health_reports: tuple[object, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _make_health_module_stub() -> types.ModuleType:
    health_module = types.ModuleType(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health",
    )
    health_module.PaperAutonomousAllocationProposalDbHistoryHealthConfig = (
        PaperAutonomousAllocationProposalDbHistoryHealthConfig
    )
    health_module.PaperAutonomousAllocationProposalDbHistoryHealthReport = (
        PaperAutonomousAllocationProposalDbHistoryHealthReport
    )

    def build_paper_autonomous_allocation_proposal_db_history_health_report(
        source_history_reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryHealthConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryHealthReport:
        raise AssertionError("test should replace the health reducer")

    health_module.build_paper_autonomous_allocation_proposal_db_history_health_report = (
        build_paper_autonomous_allocation_proposal_db_history_health_report
    )
    return health_module


def _make_health_trend_module_stub() -> types.ModuleType:
    trend_module = types.ModuleType(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend",
    )
    trend_module.PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig = (
        PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig
    )
    trend_module.PaperAutonomousAllocationProposalDbHistoryHealthTrendReport = (
        PaperAutonomousAllocationProposalDbHistoryHealthTrendReport
    )

    def build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
        health_reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendReport:
        raise AssertionError("test should replace the trend reducer")

    trend_module.build_paper_autonomous_allocation_proposal_db_history_health_trend_report = (
        build_paper_autonomous_allocation_proposal_db_history_health_trend_report
    )
    return trend_module


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


def _load_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health",
        _make_health_module_stub(),
    )
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend",
        _make_health_trend_module_stub(),
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend_load",
        None,
    )
    try:
        return importlib.import_module(
            "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend_load",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"loader module is missing: {exc}", pytrace=False)


def test_loader_builds_prefix_window_health_reports_and_final_trend_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)
    connection = object()
    history_config = PaperAutonomousAllocationProposalDbHistoryConfig(
        min_report_count=3,
    )
    health_config = PaperAutonomousAllocationProposalDbHistoryHealthConfig()
    trend_config = PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig()
    history_report_3 = HistoryReport(
        "history-3",
        datetime(2026, 6, 24, 11, 0, tzinfo=UTC),
    )
    history_report_4 = HistoryReport(
        "history-4",
        datetime(2026, 6, 24, 12, 0, tzinfo=UTC),
    )
    health_report_1 = PaperAutonomousAllocationProposalDbHistoryHealthReport(
        generated_at=history_report_3.generated_at,
        health_status="pass",
        source_history_reports=(history_report_3,),
    )
    health_report_2 = PaperAutonomousAllocationProposalDbHistoryHealthReport(
        generated_at=history_report_4.generated_at,
        health_status="watch",
        source_history_reports=(history_report_3, history_report_4),
    )
    expected_trend_report = PaperAutonomousAllocationProposalDbHistoryHealthTrendReport(
        generated_at=GENERATED_AT,
        source_health_reports=(health_report_1, health_report_2),
    )
    prefix_calls: list[dict[str, object]] = []
    health_builder_calls: list[dict[str, object]] = []
    trend_builder_calls: list[dict[str, object]] = []

    def fake_prefix_loader(
        received_connection: object,
        *,
        limit: int | None,
        table_name: str,
        history_config: PaperAutonomousAllocationProposalDbHistoryConfig,
    ) -> tuple[HistoryReport, ...]:
        prefix_calls.append(
            {
                "connection": received_connection,
                "limit": limit,
                "table_name": table_name,
                "history_config": history_config,
            },
        )
        return (history_report_3, history_report_4)

    def fake_health_builder(
        source_history_reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryHealthConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryHealthReport:
        prefix_history = tuple(source_history_reports)  # type: ignore[arg-type]
        health_builder_calls.append(
            {
                "source_history_reports": prefix_history,
                "config": config,
                "generated_at": generated_at,
            },
        )
        if len(prefix_history) == 1:
            return health_report_1
        if len(prefix_history) == 2:
            return health_report_2
        raise AssertionError("unexpected prefix size")

    def fake_trend_builder(
        health_reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendReport:
        trend_builder_calls.append(
            {
                "health_reports": tuple(health_reports),  # type: ignore[arg-type]
                "config": config,
                "generated_at": generated_at,
            },
        )
        return expected_trend_report

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_db_history_prefix_reports",
        fake_prefix_loader,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_health_report",
        fake_health_builder,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_health_trend_report",
        fake_trend_builder,
    )

    result = (
        module_under_test
        .load_paper_autonomous_allocation_proposal_db_history_health_trend_report(
            connection,
            limit=None,
            table_name="paper_autonomous_allocation_proposal_reports_test",
            history_config=history_config,
            health_config=health_config,
            trend_config=trend_config,
            generated_at=GENERATED_AT,
        )
    )

    assert result is expected_trend_report
    assert prefix_calls == [
        {
            "connection": connection,
            "limit": None,
            "table_name": "paper_autonomous_allocation_proposal_reports_test",
            "history_config": history_config,
        },
    ]
    assert health_builder_calls == [
        {
            "source_history_reports": (history_report_3,),
            "config": health_config,
            "generated_at": history_report_3.generated_at,
        },
        {
            "source_history_reports": (history_report_3, history_report_4),
            "config": health_config,
            "generated_at": history_report_4.generated_at,
        },
    ]
    assert trend_builder_calls == [
        {
            "health_reports": (health_report_1, health_report_2),
            "config": trend_config,
            "generated_at": GENERATED_AT,
        },
    ]


def test_loader_builds_blocked_boundary_health_snapshot_when_prefix_loader_returns_no_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)
    history_config = PaperAutonomousAllocationProposalDbHistoryConfig(
        min_report_count=4,
    )
    health_config = PaperAutonomousAllocationProposalDbHistoryHealthConfig()
    trend_config = PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig()
    expected_trend_report = PaperAutonomousAllocationProposalDbHistoryHealthTrendReport(
        generated_at=GENERATED_AT,
        source_health_reports=("boundary-health-report",),
    )
    prefix_calls: list[object] = []
    health_builder_calls: list[dict[str, object]] = []
    trend_builder_calls: list[dict[str, object]] = []

    def fake_prefix_loader(
        received_connection: object,
        *,
        limit: int | None,
        table_name: str,
        history_config: PaperAutonomousAllocationProposalDbHistoryConfig,
    ) -> tuple[object, ...]:
        prefix_calls.append(received_connection)
        return ()

    def fake_health_builder(
        source_history_reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryHealthConfig,
        generated_at: datetime,
    ) -> object:
        health_builder_calls.append(
            {
                "source_history_reports": tuple(source_history_reports),  # type: ignore[arg-type]
                "config": config,
                "generated_at": generated_at,
            },
        )
        return "boundary-health-report"

    def fake_trend_builder(
        health_reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendReport:
        trend_builder_calls.append(
            {
                "health_reports": tuple(health_reports),  # type: ignore[arg-type]
                "config": config,
                "generated_at": generated_at,
            },
        )
        return expected_trend_report

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_db_history_prefix_reports",
        fake_prefix_loader,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_health_report",
        fake_health_builder,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_health_trend_report",
        fake_trend_builder,
    )

    result = (
        module_under_test
        .load_paper_autonomous_allocation_proposal_db_history_health_trend_report(
            object(),
            limit=3,
            table_name="paper_autonomous_allocation_proposal_reports_test",
            history_config=history_config,
            health_config=health_config,
            trend_config=trend_config,
            generated_at=GENERATED_AT,
        )
    )

    assert result is expected_trend_report
    assert len(prefix_calls) == 1
    assert health_builder_calls == [
        {
            "source_history_reports": (),
            "config": health_config,
            "generated_at": GENERATED_AT,
        },
    ]
    assert trend_builder_calls == [
        {
            "health_reports": ("boundary-health-report",),
            "config": trend_config,
            "generated_at": GENERATED_AT,
        },
    ]


def test_loader_rejects_non_exact_configs_before_prefix_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)

    class HistoryConfigSubclass(PaperAutonomousAllocationProposalDbHistoryConfig):
        pass

    class HealthConfigSubclass(PaperAutonomousAllocationProposalDbHistoryHealthConfig):
        pass

    class TrendConfigSubclass(PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig):
        pass

    prefix_calls: list[object] = []

    def fake_prefix_loader(
        received_connection: object,
        *,
        limit: int | None,
        table_name: str,
        history_config: PaperAutonomousAllocationProposalDbHistoryConfig,
    ) -> tuple[object, ...]:
        prefix_calls.append(received_connection)
        return ()

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_db_history_prefix_reports",
        fake_prefix_loader,
    )

    invalid_cases = (
        (
            object(),
            PaperAutonomousAllocationProposalDbHistoryHealthConfig(),
            PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig(),
            "history_config must be a PaperAutonomousAllocationProposalDbHistoryConfig",
        ),
        (
            HistoryConfigSubclass(),
            PaperAutonomousAllocationProposalDbHistoryHealthConfig(),
            PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig(),
            "history_config must be a PaperAutonomousAllocationProposalDbHistoryConfig",
        ),
        (
            PaperAutonomousAllocationProposalDbHistoryConfig(),
            object(),
            PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig(),
            "health_config must be a PaperAutonomousAllocationProposalDbHistoryHealthConfig",
        ),
        (
            PaperAutonomousAllocationProposalDbHistoryConfig(),
            HealthConfigSubclass(),
            PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig(),
            "health_config must be a PaperAutonomousAllocationProposalDbHistoryHealthConfig",
        ),
        (
            PaperAutonomousAllocationProposalDbHistoryConfig(),
            PaperAutonomousAllocationProposalDbHistoryHealthConfig(),
            object(),
            "trend_config must be a PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig",
        ),
        (
            PaperAutonomousAllocationProposalDbHistoryConfig(),
            PaperAutonomousAllocationProposalDbHistoryHealthConfig(),
            TrendConfigSubclass(),
            "trend_config must be a PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig",
        ),
    )

    for history_config, health_config, trend_config, message in invalid_cases:
        with pytest.raises(ValueError, match=message):
            (
                module_under_test
                .load_paper_autonomous_allocation_proposal_db_history_health_trend_report(
                    object(),
                    limit=5,
                    table_name="paper_autonomous_allocation_proposal_reports_test",
                    history_config=history_config,
                    health_config=health_config,
                    trend_config=trend_config,
                    generated_at=GENERATED_AT,
                )
            )

    assert prefix_calls == []


def test_loader_does_not_manage_connection_lifecycle_or_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)
    connection = NoMutationConnection()
    history_config = PaperAutonomousAllocationProposalDbHistoryConfig()
    health_config = PaperAutonomousAllocationProposalDbHistoryHealthConfig()
    trend_config = PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig()
    expected_trend_report = PaperAutonomousAllocationProposalDbHistoryHealthTrendReport(
        generated_at=GENERATED_AT,
        source_health_reports=("boundary-health-report",),
    )
    prefix_calls: list[object] = []
    health_builder_calls: list[dict[str, object]] = []

    def fake_prefix_loader(
        received_connection: object,
        *,
        limit: int | None,
        table_name: str,
        history_config: PaperAutonomousAllocationProposalDbHistoryConfig,
    ) -> tuple[object, ...]:
        prefix_calls.append(received_connection)
        return ()

    def fake_health_builder(
        source_history_reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryHealthConfig,
        generated_at: datetime,
    ) -> object:
        health_builder_calls.append(
            {
                "source_history_reports": tuple(source_history_reports),  # type: ignore[arg-type]
                "config": config,
                "generated_at": generated_at,
            },
        )
        return "boundary-health-report"

    def fake_trend_builder(
        health_reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendReport:
        assert tuple(health_reports) == ("boundary-health-report",)  # type: ignore[arg-type]
        assert config is trend_config
        assert generated_at is GENERATED_AT
        return expected_trend_report

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_db_history_prefix_reports",
        fake_prefix_loader,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_health_report",
        fake_health_builder,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_health_trend_report",
        fake_trend_builder,
    )

    result = (
        module_under_test
        .load_paper_autonomous_allocation_proposal_db_history_health_trend_report(
            connection,
            limit=2,
            table_name="paper_autonomous_allocation_proposal_reports_test",
            history_config=history_config,
            health_config=health_config,
            trend_config=trend_config,
            generated_at=GENERATED_AT,
        )
    )

    assert result is expected_trend_report
    assert prefix_calls == [connection]
    assert health_builder_calls == [
        {
            "source_history_reports": (),
            "config": health_config,
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

    imported_modules: list[str] = []
    imported_names: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imported_modules.append(node.module)
            imported_names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    allowed_modules = {
        "__future__",
        "datetime",
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history",
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health",
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend",
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_prefix_load",
    }
    banned_module_fragments = (
        "psycopg",
        "cli",
        "_env",
        "env",
        "auth",
        "client",
        "supabase",
        "exchange",
        "live_trading",
        "live-trading",
        "network",
        "order",
        "wallet",
        "account",
        "execution",
        "approval",
        "advice",
        "migration",
        "migrate",
    )
    banned_import_names = {
        "insert_paper_autonomous_allocation_proposal_report",
        "insert_paper_autonomous_allocation_proposal_report_with_result",
        "persist_paper_autonomous_allocation_proposal_report",
        "load_paper_autonomous_allocation_proposal_reports",
        "build_paper_autonomous_allocation_proposal_db_history_report",
    }
    banned_call_or_attribute_names = {
        "account",
        "api_key",
        "approval",
        "approve",
        "cancel",
        "close",
        "commit",
        "connect",
        "create_order",
        "cursor",
        "delete",
        "environ",
        "execute",
        "executemany",
        "execution",
        "getenv",
        "insert",
        "migrate",
        "persist",
        "print",
        "private_key",
        "replace_order",
        "rollback",
        "sign",
        "submit",
        "trade",
        "update",
        "upsert",
        "wallet",
        "load_paper_autonomous_allocation_proposal_reports",
        "build_paper_autonomous_allocation_proposal_db_history_report",
    }

    assert set(imported_modules) <= allowed_modules
    assert all(
        fragment not in module_name
        for module_name in imported_modules
        for fragment in banned_module_fragments
    )
    assert not (set(imported_names) & banned_import_names)
    assert not (set(call_names) & banned_call_or_attribute_names)
    assert not (set(attribute_names) & banned_call_or_attribute_names)
