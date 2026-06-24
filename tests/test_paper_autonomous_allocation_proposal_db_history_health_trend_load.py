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
class PaperAutonomousAllocationProposalDbHistoryHealthConfig:
    config_version: str = "paper-autonomous-allocation-proposal-db-history-health-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryHealthReport:
    generated_at: datetime
    health_status: str
    history_report_count: int = 1
    pass_report_count: int = 1
    watch_report_count: int = 0
    blocked_report_count: int = 0
    latest_allocated_count: int | None = None
    latest_total_allocated_paper_notional: object | None = None
    latest_source_age_seconds: int | None = None
    max_source_age_seconds: int | None = None
    reason_codes: tuple[str, ...] = ("paper_health_passed",)
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


def _make_health_store_module_stub() -> types.ModuleType:
    health_store_module = types.ModuleType(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store",
    )

    def load_paper_autonomous_allocation_proposal_db_history_health_reports(
        connection: object,
        *,
        config_version: str | None = None,
        health_status: str | None = None,
        latest_history_status: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[object, ...]:
        raise AssertionError("test should replace the health report loader")

    health_store_module.load_paper_autonomous_allocation_proposal_db_history_health_reports = (
        load_paper_autonomous_allocation_proposal_db_history_health_reports
    )
    return health_store_module


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
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store",
        _make_health_store_module_stub(),
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


def test_loader_loads_persisted_health_reports_and_builds_final_trend_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)
    connection = object()
    health_config = PaperAutonomousAllocationProposalDbHistoryHealthConfig()
    trend_config = PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig()
    newer_health_report = PaperAutonomousAllocationProposalDbHistoryHealthReport(
        generated_at=datetime(2026, 6, 24, 12, 0, tzinfo=UTC),
        health_status="watch",
        history_report_count=2,
        pass_report_count=1,
        watch_report_count=1,
        reason_codes=("paper_health_watch",),
    )
    newest_health_report = PaperAutonomousAllocationProposalDbHistoryHealthReport(
        generated_at=datetime(2026, 6, 24, 13, 0, tzinfo=UTC),
        health_status="blocked",
        history_report_count=3,
        pass_report_count=1,
        watch_report_count=1,
        blocked_report_count=1,
        reason_codes=("paper_health_blocked",),
    )
    expected_trend_report = PaperAutonomousAllocationProposalDbHistoryHealthTrendReport(
        generated_at=GENERATED_AT,
        source_health_reports=(newer_health_report, newest_health_report),
    )
    load_calls: list[dict[str, object]] = []
    trend_builder_calls: list[dict[str, object]] = []

    def fake_load_health_reports(
        received_connection: object,
        *,
        config_version: str | None = None,
        health_status: str | None = None,
        latest_history_status: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[PaperAutonomousAllocationProposalDbHistoryHealthReport, ...]:
        load_calls.append(
            {
                "connection": received_connection,
                "config_version": config_version,
                "health_status": health_status,
                "latest_history_status": latest_history_status,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return (newest_health_report, newer_health_report)

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
        "load_paper_autonomous_allocation_proposal_db_history_health_reports",
        fake_load_health_reports,
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
            table_name="paper_autonomous_allocation_proposal_db_history_health_reports_test",
            health_config=health_config,
            trend_config=trend_config,
            generated_at=GENERATED_AT,
        )
    )

    assert result is expected_trend_report
    assert load_calls == [
        {
            "connection": connection,
            "config_version": health_config.config_version,
            "health_status": None,
            "latest_history_status": None,
            "limit": 2,
            "table_name": (
                "paper_autonomous_allocation_proposal_db_history_health_reports_test"
            ),
        },
    ]
    assert trend_builder_calls == [
        {
            "health_reports": (newer_health_report, newest_health_report),
            "config": trend_config,
            "generated_at": GENERATED_AT,
        },
    ]


def test_loader_preserves_duplicate_timestamp_input_position_from_persisted_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)
    health_config = PaperAutonomousAllocationProposalDbHistoryHealthConfig()
    trend_config = PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig()
    duplicate_generated_at = datetime(2026, 6, 24, 12, 0, tzinfo=UTC)
    first_loaded_report = PaperAutonomousAllocationProposalDbHistoryHealthReport(
        generated_at=duplicate_generated_at,
        health_status="watch",
        history_report_count=2,
        pass_report_count=1,
        watch_report_count=1,
        reason_codes=("paper_health_watch_newest",),
    )
    second_loaded_report = PaperAutonomousAllocationProposalDbHistoryHealthReport(
        generated_at=duplicate_generated_at,
        health_status="pass",
        reason_codes=("paper_health_pass_older",),
    )
    trend_builder_calls: list[tuple[object, ...]] = []
    expected_trend_report = PaperAutonomousAllocationProposalDbHistoryHealthTrendReport(
        generated_at=GENERATED_AT,
        source_health_reports=(second_loaded_report, first_loaded_report),
    )

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_db_history_health_reports",
        lambda *_args, **_kwargs: (first_loaded_report, second_loaded_report),
    )

    def fake_trend_builder(
        health_reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendReport:
        trend_builder_calls.append(tuple(health_reports))  # type: ignore[arg-type]
        assert config is trend_config
        assert generated_at is GENERATED_AT
        return expected_trend_report

    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_health_trend_report",
        fake_trend_builder,
    )

    result = (
        module_under_test
        .load_paper_autonomous_allocation_proposal_db_history_health_trend_report(
            object(),
            limit=None,
            table_name="paper_autonomous_allocation_proposal_db_history_health_reports_test",
            health_config=health_config,
            trend_config=trend_config,
            generated_at=GENERATED_AT,
        )
    )

    assert result is expected_trend_report
    assert trend_builder_calls == [(second_loaded_report, first_loaded_report)]


def test_loader_builds_empty_trend_when_persisted_health_db_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)
    health_config = PaperAutonomousAllocationProposalDbHistoryHealthConfig()
    trend_config = PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig()
    expected_trend_report = PaperAutonomousAllocationProposalDbHistoryHealthTrendReport(
        generated_at=GENERATED_AT,
        source_health_reports=(),
    )
    trend_builder_calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_db_history_health_reports",
        lambda *_args, **_kwargs: (),
    )

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
        "build_paper_autonomous_allocation_proposal_db_history_health_trend_report",
        fake_trend_builder,
    )

    result = (
        module_under_test
        .load_paper_autonomous_allocation_proposal_db_history_health_trend_report(
            object(),
            limit=3,
            table_name="paper_autonomous_allocation_proposal_db_history_health_reports_test",
            health_config=health_config,
            trend_config=trend_config,
            generated_at=GENERATED_AT,
        )
    )

    assert result is expected_trend_report
    assert trend_builder_calls == [
        {
            "health_reports": (),
            "config": trend_config,
            "generated_at": GENERATED_AT,
        },
    ]


def test_loader_does_not_call_proposal_history_prefix_or_health_reducer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)
    health_config = PaperAutonomousAllocationProposalDbHistoryHealthConfig()
    trend_config = PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig()
    expected_trend_report = PaperAutonomousAllocationProposalDbHistoryHealthTrendReport(
        generated_at=GENERATED_AT,
        source_health_reports=(),
    )

    for forbidden_name in (
        "load_paper_autonomous_allocation_proposal_db_history_prefix_reports",
        "build_paper_autonomous_allocation_proposal_db_history_health_report",
    ):
        assert not hasattr(module_under_test, forbidden_name)

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_db_history_health_reports",
        lambda *_args, **_kwargs: (),
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_autonomous_allocation_proposal_db_history_health_trend_report",
        lambda *_args, **_kwargs: expected_trend_report,
    )

    result = (
        module_under_test
        .load_paper_autonomous_allocation_proposal_db_history_health_trend_report(
            object(),
            limit=3,
            table_name="paper_autonomous_allocation_proposal_db_history_health_reports_test",
            health_config=health_config,
            trend_config=trend_config,
            generated_at=GENERATED_AT,
        )
    )

    assert result is expected_trend_report


def test_loader_rejects_non_exact_configs_before_health_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)

    class HealthConfigSubclass(PaperAutonomousAllocationProposalDbHistoryHealthConfig):
        pass

    class TrendConfigSubclass(PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig):
        pass

    load_calls: list[object] = []

    def fake_load_health_reports(*_args: object, **_kwargs: object) -> tuple[object, ...]:
        load_calls.append(object())
        return ()

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_db_history_health_reports",
        fake_load_health_reports,
    )

    invalid_cases = (
        (
            object(),
            PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig(),
            "health_config must be a PaperAutonomousAllocationProposalDbHistoryHealthConfig",
        ),
        (
            HealthConfigSubclass(),
            PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig(),
            "health_config must be a PaperAutonomousAllocationProposalDbHistoryHealthConfig",
        ),
        (
            PaperAutonomousAllocationProposalDbHistoryHealthConfig(),
            object(),
            "trend_config must be a PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig",
        ),
        (
            PaperAutonomousAllocationProposalDbHistoryHealthConfig(),
            TrendConfigSubclass(),
            "trend_config must be a PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig",
        ),
    )

    for health_config, trend_config, message in invalid_cases:
        with pytest.raises(ValueError, match=message):
            (
                module_under_test
                .load_paper_autonomous_allocation_proposal_db_history_health_trend_report(
                    object(),
                    limit=5,
                    table_name=(
                        "paper_autonomous_allocation_proposal_db_history_health_reports_test"
                    ),
                    health_config=health_config,
                    trend_config=trend_config,
                    generated_at=GENERATED_AT,
                )
            )

    assert load_calls == []


def test_loader_does_not_manage_connection_lifecycle_or_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_under_test = _load_module(monkeypatch)
    connection = NoMutationConnection()
    health_config = PaperAutonomousAllocationProposalDbHistoryHealthConfig()
    trend_config = PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig()
    expected_trend_report = PaperAutonomousAllocationProposalDbHistoryHealthTrendReport(
        generated_at=GENERATED_AT,
        source_health_reports=(),
    )
    load_calls: list[object] = []

    def fake_load_health_reports(
        received_connection: object,
        **_kwargs: object,
    ) -> tuple[object, ...]:
        load_calls.append(received_connection)
        return ()

    def fake_trend_builder(
        health_reports: object,
        *,
        config: PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
        generated_at: datetime,
    ) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendReport:
        assert tuple(health_reports) == ()  # type: ignore[arg-type]
        assert config is trend_config
        assert generated_at is GENERATED_AT
        return expected_trend_report

    monkeypatch.setattr(
        module_under_test,
        "load_paper_autonomous_allocation_proposal_db_history_health_reports",
        fake_load_health_reports,
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
            table_name="paper_autonomous_allocation_proposal_db_history_health_reports_test",
            health_config=health_config,
            trend_config=trend_config,
            generated_at=GENERATED_AT,
        )
    )

    assert result is expected_trend_report
    assert load_calls == [connection]


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
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health",
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend",
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store",
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
        "load_paper_autonomous_allocation_proposal_db_history_prefix_reports",
        "build_paper_autonomous_allocation_proposal_db_history_health_report",
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
