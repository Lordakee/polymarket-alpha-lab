from __future__ import annotations

import ast
import importlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
    PaperAutonomousAllocationProposalDbHistoryConfig,
)


@dataclass(frozen=True)
class ProposalReport:
    name: str
    generated_at: datetime


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


def _load_module():
    importlib.invalidate_caches()
    return importlib.import_module(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_prefix_load",
    )


def test_prefix_loader_loads_store_once_and_builds_reports_from_sufficient_prefixes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module()
    connection = object()
    history_config = PaperAutonomousAllocationProposalDbHistoryConfig(
        min_report_count=3,
    )
    reports_chronological = (
        ProposalReport("oldest", datetime(2026, 6, 24, 9, 0, tzinfo=UTC)),
        ProposalReport("middle", datetime(2026, 6, 24, 10, 0, tzinfo=UTC)),
        ProposalReport("newer", datetime(2026, 6, 24, 11, 0, tzinfo=UTC)),
        ProposalReport("newest", datetime(2026, 6, 24, 12, 0, tzinfo=UTC)),
    )
    db_descending_reports = tuple(reversed(reports_chronological))
    source_history_3 = object()
    source_history_4 = object()
    store_calls: list[dict[str, object]] = []
    history_builder_calls: list[dict[str, object]] = []

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

    result = (
        module_under_test
        .load_paper_autonomous_allocation_proposal_db_history_prefix_reports(
            connection,
            limit=None,
            table_name="paper_autonomous_allocation_proposal_reports_test",
            history_config=history_config,
        )
    )

    assert result == (source_history_3, source_history_4)
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


def test_prefix_loader_returns_empty_sequence_when_history_minimum_is_not_met(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module()
    connection = object()
    history_config = PaperAutonomousAllocationProposalDbHistoryConfig(
        min_report_count=4,
    )
    store_calls: list[dict[str, object]] = []

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
        return (
            ProposalReport("newest", datetime(2026, 6, 24, 11, 0, tzinfo=UTC)),
            ProposalReport("middle", datetime(2026, 6, 24, 10, 0, tzinfo=UTC)),
            ProposalReport("oldest", datetime(2026, 6, 24, 9, 0, tzinfo=UTC)),
        )

    def fail_history_builder(*args: object, **kwargs: object) -> object:
        raise AssertionError("history builder must not run without a sufficient prefix")

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_reports",
        fake_store,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_report",
        fail_history_builder,
    )

    result = (
        module_under_test
        .load_paper_autonomous_allocation_proposal_db_history_prefix_reports(
            connection,
            limit=3,
            table_name="paper_autonomous_allocation_proposal_reports_test",
            history_config=history_config,
        )
    )

    assert result == ()
    assert store_calls == [
        {
            "connection": connection,
            "limit": 3,
            "table_name": "paper_autonomous_allocation_proposal_reports_test",
        },
    ]


def test_prefix_loader_rejects_non_exact_history_config_before_store_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module()

    class HistoryConfigSubclass(PaperAutonomousAllocationProposalDbHistoryConfig):
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

    invalid_values = (
        object(),
        HistoryConfigSubclass(),
    )
    for invalid_config in invalid_values:
        with pytest.raises(
            ValueError,
            match=(
                "history_config must be a "
                "PaperAutonomousAllocationProposalDbHistoryConfig"
            ),
        ):
            (
                module_under_test
                .load_paper_autonomous_allocation_proposal_db_history_prefix_reports(
                    object(),
                    limit=5,
                    table_name="paper_autonomous_allocation_proposal_reports_test",
                    history_config=invalid_config,
                )
            )

    assert store_calls == []


def test_prefix_loader_does_not_manage_connection_lifecycle_or_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module()
    connection = NoMutationConnection()
    history_config = PaperAutonomousAllocationProposalDbHistoryConfig()
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

    result = (
        module_under_test
        .load_paper_autonomous_allocation_proposal_db_history_prefix_reports(
            connection,
            limit=2,
            table_name="paper_autonomous_allocation_proposal_reports_test",
            history_config=history_config,
        )
    )

    assert result == ()
    assert store_calls == [connection]


def test_prefix_loader_module_has_no_db_lifecycle_env_cli_or_live_trading_surface() -> None:
    module_under_test = _load_module()
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
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history",
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
