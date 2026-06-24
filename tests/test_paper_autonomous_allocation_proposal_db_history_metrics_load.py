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
class PaperAutonomousAllocationProposalDbHistoryMetricsConfig:
    config_version: str = "paper-autonomous-allocation-proposal-db-history-metrics-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsReport:
    generated_at: datetime
    source_reports: tuple[object, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow:
    pass


class PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow:
    pass


class PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary:
    pass


@dataclass(frozen=True)
class ProposalReport:
    name: str
    generated_at: datetime


class NoMutationConnection:
    def cursor(self) -> None:
        raise AssertionError("loader must not open cursors directly")

    def close(self) -> None:
        raise AssertionError("loader must not close")

    def commit(self) -> None:
        raise AssertionError("loader must not commit")

    def rollback(self) -> None:
        raise AssertionError("loader must not rollback")

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

    def create(self) -> None:
        raise AssertionError("loader must not write")

    def write(self) -> None:
        raise AssertionError("loader must not write")

    def upsert(self) -> None:
        raise AssertionError("loader must not write")

    def persist(self) -> None:
        raise AssertionError("loader must not persist")


def _make_metrics_module_stub() -> types.ModuleType:
    metrics_module = types.ModuleType(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics",
    )
    metrics_module.PaperAutonomousAllocationProposalDbHistoryMetricsConfig = (
        PaperAutonomousAllocationProposalDbHistoryMetricsConfig
    )
    metrics_module.PaperAutonomousAllocationProposalDbHistoryMetricsReport = (
        PaperAutonomousAllocationProposalDbHistoryMetricsReport
    )
    metrics_module.PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow = (
        PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow
    )
    metrics_module.PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow = (
        PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow
    )
    metrics_module.PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary = (
        PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary
    )

    def build_paper_autonomous_allocation_proposal_db_history_metrics_report(
        reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryMetricsConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryMetricsReport:
        raise AssertionError("test should replace the metrics reducer")

    metrics_module.build_paper_autonomous_allocation_proposal_db_history_metrics_report = (
        build_paper_autonomous_allocation_proposal_db_history_metrics_report
    )
    return metrics_module


def _make_store_module_stub() -> types.ModuleType:
    store_module = types.ModuleType(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_store",
    )

    def load_paper_autonomous_allocation_proposal_reports(
        connection: object,
        *,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[object, ...]:
        raise AssertionError("test should replace the proposal store loader")

    store_module.load_paper_autonomous_allocation_proposal_reports = (
        load_paper_autonomous_allocation_proposal_reports
    )
    return store_module


def _load_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics",
        _make_metrics_module_stub(),
    )
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_store",
        _make_store_module_stub(),
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_load",
        None,
    )
    try:
        return importlib.import_module(
            "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_load",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"loader module is missing: {exc}", pytrace=False)


def test_loader_loads_persisted_proposals_once_and_builds_chronological_metrics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)
    connection = object()
    config = PaperAutonomousAllocationProposalDbHistoryMetricsConfig()
    older_report = ProposalReport(
        name="older",
        generated_at=datetime(2026, 6, 24, 10, 0, tzinfo=UTC),
    )
    newer_report = ProposalReport(
        name="newer",
        generated_at=datetime(2026, 6, 24, 11, 0, tzinfo=UTC),
    )
    newest_report = ProposalReport(
        name="newest",
        generated_at=datetime(2026, 6, 24, 12, 0, tzinfo=UTC),
    )
    expected_metrics_report = PaperAutonomousAllocationProposalDbHistoryMetricsReport(
        generated_at=GENERATED_AT,
        source_reports=(older_report, newer_report, newest_report),
    )
    load_calls: list[dict[str, object]] = []
    reducer_calls: list[dict[str, object]] = []

    def fake_load_reports(
        received_connection: object,
        *,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[ProposalReport, ...]:
        load_calls.append(
            {
                "connection": received_connection,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return (newest_report, newer_report, older_report)

    def fake_metrics_reducer(
        reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryMetricsConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryMetricsReport:
        reducer_calls.append(
            {
                "reports": tuple(reports),  # type: ignore[arg-type]
                "config": config,
                "generated_at": generated_at,
            },
        )
        return expected_metrics_report

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_reports",
        fake_load_reports,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_metrics_report",
        fake_metrics_reducer,
    )

    result = (
        module_under_test
        .load_paper_autonomous_allocation_proposal_db_history_metrics_report(
            connection,
            limit=3,
            table_name="paper_autonomous_allocation_proposal_reports_test",
            config=config,
            generated_at=GENERATED_AT,
        )
    )

    assert result is expected_metrics_report
    assert load_calls == [
        {
            "connection": connection,
            "limit": 3,
            "table_name": "paper_autonomous_allocation_proposal_reports_test",
        },
    ]
    assert reducer_calls == [
        {
            "reports": (older_report, newer_report, newest_report),
            "config": config,
            "generated_at": GENERATED_AT,
        },
    ]


def test_loader_rejects_non_exact_config_before_store_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)

    class MetricsConfigSubclass(
        PaperAutonomousAllocationProposalDbHistoryMetricsConfig,
    ):
        pass

    load_calls: list[object] = []

    def fake_load_reports(*_args: object, **_kwargs: object) -> tuple[object, ...]:
        load_calls.append(object())
        return ()

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_reports",
        fake_load_reports,
    )

    invalid_cases = (
        (
            object(),
            "config must be a "
            "PaperAutonomousAllocationProposalDbHistoryMetricsConfig",
        ),
        (
            MetricsConfigSubclass(),
            "config must be a "
            "PaperAutonomousAllocationProposalDbHistoryMetricsConfig",
        ),
    )

    for config, message in invalid_cases:
        with pytest.raises(ValueError, match=message):
            (
                module_under_test
                .load_paper_autonomous_allocation_proposal_db_history_metrics_report(
                    object(),
                    limit=5,
                    table_name="paper_autonomous_allocation_proposal_reports_test",
                    config=config,
                    generated_at=GENERATED_AT,
                )
            )

    assert load_calls == []


def test_loader_does_not_call_cursor_or_manage_connection_lifecycle_or_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)
    connection = NoMutationConnection()
    metrics_config = PaperAutonomousAllocationProposalDbHistoryMetricsConfig()
    expected_metrics_report = PaperAutonomousAllocationProposalDbHistoryMetricsReport(
        generated_at=GENERATED_AT,
        source_reports=(),
    )
    load_calls: list[object] = []

    def fake_load_reports(
        received_connection: object,
        *,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[object, ...]:
        load_calls.append(received_connection)
        assert limit == 2
        assert table_name == "paper_autonomous_allocation_proposal_reports_test"
        return ()

    def fake_metrics_reducer(
        reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryMetricsConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryMetricsReport:
        assert tuple(reports) == ()  # type: ignore[arg-type]
        assert config is metrics_config
        assert generated_at is GENERATED_AT
        return expected_metrics_report

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_reports",
        fake_load_reports,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_metrics_report",
        fake_metrics_reducer,
    )

    result = (
        module_under_test
        .load_paper_autonomous_allocation_proposal_db_history_metrics_report(
            connection,
            limit=2,
            table_name="paper_autonomous_allocation_proposal_reports_test",
            config=metrics_config,
            generated_at=GENERATED_AT,
        )
    )

    assert result is expected_metrics_report
    assert load_calls == [connection]


def test_loader_module_imports_only_store_loader_and_metrics_reducer_symbols(
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
    keyword_names: list[str] = []
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
            keyword_names.extend(
                keyword.arg for keyword in node.keywords if keyword.arg is not None
            )
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    allowed_modules = {
        "__future__",
        "datetime",
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics",
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_store",
    }
    expected_imported_names = {
        "annotations",
        "datetime",
        "PaperAutonomousAllocationProposalDbHistoryMetricsConfig",
        "PaperAutonomousAllocationProposalDbHistoryMetricsReport",
        "build_paper_autonomous_allocation_proposal_db_history_metrics_report",
        "load_paper_autonomous_allocation_proposal_reports",
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
        "build_paper_autonomous_allocation_proposal_db_history_report",
        "load_paper_autonomous_allocation_proposal_db_history_prefix_reports",
        "build_paper_autonomous_allocation_proposal_db_history_health_report",
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
        "create",
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
        "write",
        "build_paper_autonomous_allocation_proposal_db_history_report",
        "load_paper_autonomous_allocation_proposal_db_history_prefix_reports",
        "build_paper_autonomous_allocation_proposal_db_history_health_report",
    }
    filter_keyword_names = {
        "allocation_config_version",
        "config_version",
        "proposal_status",
        "screening_gate_status",
    }

    assert set(imported_modules) <= allowed_modules
    assert set(imported_names) <= expected_imported_names
    assert all(
        fragment not in module_name
        for module_name in imported_modules
        for fragment in banned_module_fragments
    )
    assert not (set(imported_names) & banned_import_names)
    assert not (set(call_names) & banned_call_or_attribute_names)
    assert not (set(attribute_names) & banned_call_or_attribute_names)
    assert not (set(keyword_names) & filter_keyword_names)


def test_loader_module_documents_v0_unfiltered_aggregation_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)
    module_docs = " ".join((module_under_test.__doc__ or "").split())

    assert "v0 aggregates across all persisted proposal statuses" in module_docs
    assert "config versions selected by the table and limit" in module_docs
