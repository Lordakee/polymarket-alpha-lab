from __future__ import annotations

import ast
import importlib
import sys
import types
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 6, 24, 9, 0, tzinfo=UTC)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryGateConfig:
    config_version: str = "paper-autonomous-allocation-proposal-db-history-gate-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryGateReport:
    generated_at: datetime
    gate_status: str
    source_history_report: object
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _make_gate_module_stub() -> types.ModuleType:
    gate_module = types.ModuleType(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate",
    )
    gate_module.PaperAutonomousAllocationProposalDbHistoryGateConfig = (
        PaperAutonomousAllocationProposalDbHistoryGateConfig
    )
    gate_module.PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount = (
        PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount
    )
    gate_module.PaperAutonomousAllocationProposalDbHistoryGateReport = (
        PaperAutonomousAllocationProposalDbHistoryGateReport
    )

    def build_paper_autonomous_allocation_proposal_db_history_gate_report(
        history_report: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryGateConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryGateReport:
        raise AssertionError("test should replace the gate reducer")

    gate_module.build_paper_autonomous_allocation_proposal_db_history_gate_report = (
        build_paper_autonomous_allocation_proposal_db_history_gate_report
    )
    return gate_module


from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (  # noqa: E402
    PaperAutonomousAllocationProposalDbHistoryConfig,
)


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

    def persist(self) -> None:
        raise AssertionError("loader must not persist")


@pytest.fixture()
def module_under_test(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate",
        _make_gate_module_stub(),
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate_load",
        None,
    )
    loaded_module = importlib.import_module(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate_load",
    )
    yield loaded_module
    sys.modules.pop(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate_load",
        None,
    )


def test_loader_delegates_history_load_and_builds_gate_report(
    module_under_test: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = object()
    history_config = PaperAutonomousAllocationProposalDbHistoryConfig()
    gate_config = PaperAutonomousAllocationProposalDbHistoryGateConfig()
    loaded_history_report = object()
    expected_gate_report = PaperAutonomousAllocationProposalDbHistoryGateReport(
        generated_at=GENERATED_AT,
        gate_status="pass",
        source_history_report=loaded_history_report,
    )
    history_loader_calls: list[
        tuple[
            object,
            int | None,
            str,
            PaperAutonomousAllocationProposalDbHistoryConfig,
            datetime,
        ]
    ] = []
    gate_builder_calls: list[
        tuple[
            object,
            PaperAutonomousAllocationProposalDbHistoryGateConfig,
            datetime,
        ]
    ] = []

    def fake_load(
        received_connection: object,
        *,
        limit: int | None,
        table_name: str,
        config: PaperAutonomousAllocationProposalDbHistoryConfig,
        generated_at: datetime,
    ) -> object:
        history_loader_calls.append(
            (
                received_connection,
                limit,
                table_name,
                config,
                generated_at,
            ),
        )
        return loaded_history_report

    def fake_build(
        history_report: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryGateConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryGateReport:
        gate_builder_calls.append((history_report, config, generated_at))
        return expected_gate_report

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_db_history_report",
        fake_load,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_gate_report",
        fake_build,
    )

    gate_report = (
        module_under_test
        .load_paper_autonomous_allocation_proposal_db_history_gate_report(
            connection,
            limit=7,
            table_name="paper_autonomous_allocation_proposal_reports",
            history_config=history_config,
            gate_config=gate_config,
            generated_at=GENERATED_AT,
        )
    )

    assert gate_report is expected_gate_report
    assert history_loader_calls == [
        (
            connection,
            7,
            "paper_autonomous_allocation_proposal_reports",
            history_config,
            GENERATED_AT,
        ),
    ]
    assert gate_builder_calls == [(loaded_history_report, gate_config, GENERATED_AT)]


def test_loader_rejects_non_exact_configs_before_history_load(
    module_under_test: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class HistoryConfigSubclass(PaperAutonomousAllocationProposalDbHistoryConfig):
        pass

    class GateConfigSubclass(PaperAutonomousAllocationProposalDbHistoryGateConfig):
        pass

    history_loader_calls: list[object] = []
    gate_builder_calls: list[object] = []

    def fake_load(
        received_connection: object,
        *,
        limit: int | None,
        table_name: str,
        config: PaperAutonomousAllocationProposalDbHistoryConfig,
        generated_at: datetime,
    ) -> object:
        history_loader_calls.append(received_connection)
        return object()

    def fake_build(
        history_report: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryGateConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryGateReport:
        gate_builder_calls.append(history_report)
        return PaperAutonomousAllocationProposalDbHistoryGateReport(
            generated_at=generated_at,
            gate_status="pass",
            source_history_report=history_report,
        )

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_db_history_report",
        fake_load,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_gate_report",
        fake_build,
    )

    with pytest.raises(
        ValueError,
        match=(
            "history_config must be a "
            "PaperAutonomousAllocationProposalDbHistoryConfig"
        ),
    ):
        (
            module_under_test
            .load_paper_autonomous_allocation_proposal_db_history_gate_report(
                object(),
                limit=5,
                table_name="paper_autonomous_allocation_proposal_reports",
                history_config=HistoryConfigSubclass(),
                gate_config=PaperAutonomousAllocationProposalDbHistoryGateConfig(),
                generated_at=GENERATED_AT,
            )
        )

    with pytest.raises(
        ValueError,
        match=(
            "gate_config must be a "
            "PaperAutonomousAllocationProposalDbHistoryGateConfig"
        ),
    ):
        (
            module_under_test
            .load_paper_autonomous_allocation_proposal_db_history_gate_report(
                object(),
                limit=5,
                table_name="paper_autonomous_allocation_proposal_reports",
                history_config=PaperAutonomousAllocationProposalDbHistoryConfig(),
                gate_config=GateConfigSubclass(),
                generated_at=GENERATED_AT,
            )
        )

    assert history_loader_calls == []
    assert gate_builder_calls == []


def test_loader_does_not_manage_connection_lifecycle_or_write(
    module_under_test: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = NoMutationConnection()
    history_config = PaperAutonomousAllocationProposalDbHistoryConfig()
    gate_config = PaperAutonomousAllocationProposalDbHistoryGateConfig()
    loaded_history_report = object()
    expected_gate_report = PaperAutonomousAllocationProposalDbHistoryGateReport(
        generated_at=GENERATED_AT,
        gate_status="pass",
        source_history_report=loaded_history_report,
    )
    history_loader_calls: list[object] = []

    def fake_load(
        received_connection: object,
        *,
        limit: int | None,
        table_name: str,
        config: PaperAutonomousAllocationProposalDbHistoryConfig,
        generated_at: datetime,
    ) -> object:
        history_loader_calls.append(received_connection)
        return loaded_history_report

    def fake_build(
        history_report: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryGateConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryGateReport:
        return expected_gate_report

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_db_history_report",
        fake_load,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_gate_report",
        fake_build,
    )

    gate_report = (
        module_under_test
        .load_paper_autonomous_allocation_proposal_db_history_gate_report(
            connection,
            limit=None,
            table_name="paper_autonomous_allocation_proposal_reports",
            history_config=history_config,
            gate_config=gate_config,
            generated_at=GENERATED_AT,
        )
    )

    assert gate_report is expected_gate_report
    assert history_loader_calls == [connection]


def test_loader_module_has_no_db_lifecycle_env_cli_write_or_upstream_surface(
    module_under_test: types.ModuleType,
) -> None:
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
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate",
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_load",
    }
    banned_module_fragments = (
        "psycopg",
        "cli",
        "_env",
        "env",
        "auth",
        "client",
        "exchange",
        "live_trading",
        "live-trading",
        "network",
        "order",
        "wallet",
        "screening",
        "queue",
        "store",
        "migration",
        "migrate",
    )
    banned_import_names = {
        "insert_paper_autonomous_allocation_proposal_report",
        "insert_paper_autonomous_allocation_proposal_report_with_result",
        "persist_paper_autonomous_allocation_proposal_report",
    }
    banned_call_or_attribute_names = {
        "api_key",
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
