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
class ProposalReport:
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
    sys.modules.pop(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_load",
        None,
    )
    try:
        return importlib.import_module(
            "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_load",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"loader module is missing: {exc}", pytrace=False)


def test_loader_loads_store_once_and_builds_prefix_history_health_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)
    connection = object()
    history_config = PaperAutonomousAllocationProposalDbHistoryConfig(
        min_report_count=3,
    )
    health_config = PaperAutonomousAllocationProposalDbHistoryHealthConfig()
    reports_chronological = (
        ProposalReport("oldest", datetime(2026, 6, 24, 9, 0, tzinfo=UTC)),
        ProposalReport("middle", datetime(2026, 6, 24, 10, 0, tzinfo=UTC)),
        ProposalReport("newer", datetime(2026, 6, 24, 11, 0, tzinfo=UTC)),
        ProposalReport("newest", datetime(2026, 6, 24, 12, 0, tzinfo=UTC)),
    )
    db_descending_reports = tuple(reversed(reports_chronological))
    source_history_3 = object()
    source_history_4 = object()
    expected_health_report = PaperAutonomousAllocationProposalDbHistoryHealthReport(
        generated_at=GENERATED_AT,
        health_status="pass",
        source_history_reports=(source_history_3, source_history_4),
    )
    store_calls: list[dict[str, object]] = []
    history_builder_calls: list[dict[str, object]] = []
    health_builder_calls: list[dict[str, object]] = []

    def fake_store(
        received_connection: object,
        *,
        limit: int | None,
        table_name: str,
    ) -> tuple[ProposalReport, ...]:
        store_calls.append(
            {
                "connection": received_connection,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return db_descending_reports

    def fake_history_builder(
        proposal_reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryConfig,
        generated_at: datetime,
    ) -> object:
        prefix_reports = tuple(proposal_reports)  # type: ignore[arg-type]
        history_builder_calls.append(
            {
                "proposal_reports": prefix_reports,
                "config": config,
                "generated_at": generated_at,
            },
        )
        return {
            3: source_history_3,
            4: source_history_4,
        }[len(prefix_reports)]

    def fake_health_builder(
        source_history_reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryHealthConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryHealthReport:
        health_builder_calls.append(
            {
                "source_history_reports": tuple(source_history_reports),  # type: ignore[arg-type]
                "config": config,
                "generated_at": generated_at,
            },
        )
        return expected_health_report

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_reports",
        fake_store,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_report",
        fake_history_builder,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_health_report",
        fake_health_builder,
    )

    result = (
        module_under_test
        .load_paper_autonomous_allocation_proposal_db_history_health_report(
            connection,
            limit=None,
            table_name="paper_autonomous_allocation_proposal_reports_test",
            history_config=history_config,
            health_config=health_config,
            generated_at=GENERATED_AT,
        )
    )

    assert result is expected_health_report
    assert store_calls == [
        {
            "connection": connection,
            "limit": None,
            "table_name": "paper_autonomous_allocation_proposal_reports_test",
        },
    ]
    assert history_builder_calls == [
        {
            "proposal_reports": reports_chronological[:3],
            "config": history_config,
            "generated_at": reports_chronological[2].generated_at,
        },
        {
            "proposal_reports": reports_chronological[:4],
            "config": history_config,
            "generated_at": reports_chronological[3].generated_at,
        },
    ]
    assert health_builder_calls == [
        {
            "source_history_reports": (source_history_3, source_history_4),
            "config": health_config,
            "generated_at": GENERATED_AT,
        },
    ]


def test_loader_rejects_non_exact_configs_before_store_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)

    class HistoryConfigSubclass(PaperAutonomousAllocationProposalDbHistoryConfig):
        pass

    class HealthConfigSubclass(PaperAutonomousAllocationProposalDbHistoryHealthConfig):
        pass

    store_calls: list[object] = []

    def fake_store(
        received_connection: object,
        *,
        limit: int | None,
        table_name: str,
    ) -> tuple[object, ...]:
        store_calls.append(received_connection)
        return ()

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_reports",
        fake_store,
    )

    invalid_cases = (
        (
            object(),
            PaperAutonomousAllocationProposalDbHistoryHealthConfig(),
            "history_config must be a PaperAutonomousAllocationProposalDbHistoryConfig",
        ),
        (
            HistoryConfigSubclass(),
            PaperAutonomousAllocationProposalDbHistoryHealthConfig(),
            "history_config must be a PaperAutonomousAllocationProposalDbHistoryConfig",
        ),
        (
            PaperAutonomousAllocationProposalDbHistoryConfig(),
            object(),
            "health_config must be a PaperAutonomousAllocationProposalDbHistoryHealthConfig",
        ),
        (
            PaperAutonomousAllocationProposalDbHistoryConfig(),
            HealthConfigSubclass(),
            "health_config must be a PaperAutonomousAllocationProposalDbHistoryHealthConfig",
        ),
    )

    for history_config, health_config, message in invalid_cases:
        with pytest.raises(ValueError, match=message):
            (
                module_under_test
                .load_paper_autonomous_allocation_proposal_db_history_health_report(
                    object(),
                    limit=5,
                    table_name="paper_autonomous_allocation_proposal_reports_test",
                    history_config=history_config,
                    health_config=health_config,
                    generated_at=GENERATED_AT,
                )
            )

    assert store_calls == []


def test_loader_does_not_manage_connection_lifecycle_or_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)
    connection = NoMutationConnection()
    history_config = PaperAutonomousAllocationProposalDbHistoryConfig()
    health_config = PaperAutonomousAllocationProposalDbHistoryHealthConfig()
    expected_health_report = PaperAutonomousAllocationProposalDbHistoryHealthReport(
        generated_at=GENERATED_AT,
        health_status="blocked",
        source_history_reports=(),
    )
    store_calls: list[object] = []

    def fake_store(
        received_connection: object,
        *,
        limit: int | None,
        table_name: str,
    ) -> tuple[object, ...]:
        store_calls.append(received_connection)
        return ()

    def fake_health_builder(
        source_history_reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryHealthConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryHealthReport:
        assert tuple(source_history_reports) == ()  # type: ignore[arg-type]
        assert config is health_config
        assert generated_at is GENERATED_AT
        return expected_health_report

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_reports",
        fake_store,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_health_report",
        fake_health_builder,
    )

    result = (
        module_under_test
        .load_paper_autonomous_allocation_proposal_db_history_health_report(
            connection,
            limit=2,
            table_name="paper_autonomous_allocation_proposal_reports_test",
            history_config=history_config,
            health_config=health_config,
            generated_at=GENERATED_AT,
        )
    )

    assert result is expected_health_report
    assert store_calls == [connection]


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
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_store",
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
