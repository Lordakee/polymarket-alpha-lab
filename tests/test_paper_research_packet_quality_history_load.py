from __future__ import annotations

import ast
import importlib
import sys
import types
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest


GENERATED_AT = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
BASE_AT = datetime(2026, 6, 23, 8, 0, tzinfo=UTC)


@dataclass(frozen=True)
class FakeQualityReport:
    generated_at: datetime
    quality_status: str


@dataclass(frozen=True)
class PaperResearchPacketQualityHistoryConfig:
    config_version: str = "paper-research-packet-quality-history-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperResearchPacketQualityHistoryReport:
    generated_at: datetime
    config_version: str
    source_report_count: int
    first_source_generated_at: datetime | None
    latest_source_generated_at: datetime | None
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


@pytest.fixture()
def module_under_test(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    history_module = types.ModuleType(
        "polymarket_alpha_lab.paper_research_packet_quality_history",
    )
    history_module.PaperResearchPacketQualityHistoryConfig = (
        PaperResearchPacketQualityHistoryConfig
    )
    history_module.PaperResearchPacketQualityHistoryReport = (
        PaperResearchPacketQualityHistoryReport
    )

    def build_paper_research_packet_quality_history_report(
        reports: object,
        *,
        config: PaperResearchPacketQualityHistoryConfig,
        generated_at: datetime,
    ) -> PaperResearchPacketQualityHistoryReport:
        if type(config) is not PaperResearchPacketQualityHistoryConfig:
            raise ValueError(
                "config must be a PaperResearchPacketQualityHistoryConfig",
            )
        chronological_reports = tuple(reports)  # type: ignore[arg-type]
        return PaperResearchPacketQualityHistoryReport(
            generated_at=generated_at,
            config_version=config.config_version,
            source_report_count=len(chronological_reports),
            first_source_generated_at=(
                chronological_reports[0].generated_at
                if chronological_reports
                else None
            ),
            latest_source_generated_at=(
                chronological_reports[-1].generated_at
                if chronological_reports
                else None
            ),
        )

    history_module.build_paper_research_packet_quality_history_report = (
        build_paper_research_packet_quality_history_report
    )

    store_module = types.ModuleType(
        "polymarket_alpha_lab.paper_research_packet_quality_store",
    )

    def load_paper_research_packet_quality_reports(
        connection: object,
        *,
        config_version: str | None = None,
        quality_status: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[FakeQualityReport, ...]:
        raise AssertionError("test should replace the store loader")

    store_module.load_paper_research_packet_quality_reports = (
        load_paper_research_packet_quality_reports
    )

    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_research_packet_quality_history",
        history_module,
    )
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_research_packet_quality_store",
        store_module,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_research_packet_quality_history_load",
        None,
    )
    loaded_module = importlib.import_module(
        "polymarket_alpha_lab.paper_research_packet_quality_history_load",
    )
    yield loaded_module
    sys.modules.pop(
        "polymarket_alpha_lab.paper_research_packet_quality_history_load",
        None,
    )


def test_loader_passes_query_options_and_reverses_store_descending_reports(
    module_under_test: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = object()
    config = PaperResearchPacketQualityHistoryConfig()
    older = FakeQualityReport(generated_at=BASE_AT, quality_status="pass")
    latest = FakeQualityReport(
        generated_at=BASE_AT + timedelta(hours=2),
        quality_status="watch",
    )
    store_calls: list[tuple[object, str | None, str | None, int | None, str]] = []
    reducer_calls: list[
        tuple[
            tuple[FakeQualityReport, ...],
            PaperResearchPacketQualityHistoryConfig,
            datetime,
        ]
    ] = []

    def fake_load(
        received_connection: object,
        *,
        config_version: str | None = None,
        quality_status: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[FakeQualityReport, ...]:
        store_calls.append(
            (
                received_connection,
                config_version,
                quality_status,
                limit,
                table_name,
            ),
        )
        return (latest, older)

    def fake_build(
        reports: object,
        *,
        config: PaperResearchPacketQualityHistoryConfig,
        generated_at: datetime,
    ) -> PaperResearchPacketQualityHistoryReport:
        reducer_reports = tuple(reports)  # type: ignore[arg-type]
        reducer_calls.append((reducer_reports, config, generated_at))
        return PaperResearchPacketQualityHistoryReport(
            generated_at=generated_at,
            config_version=config.config_version,
            source_report_count=len(reducer_reports),
            first_source_generated_at=reducer_reports[0].generated_at,
            latest_source_generated_at=reducer_reports[-1].generated_at,
        )

    monkeypatch.setattr(
        module_under_test,
        "load_paper_research_packet_quality_reports",
        fake_load,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_research_packet_quality_history_report",
        fake_build,
    )

    history = module_under_test.load_paper_research_packet_quality_history_report(
        connection,
        config_version="paper-research-packet-quality-v0",
        quality_status="watch",
        limit=2,
        table_name="custom_packet_quality_reports",
        config=config,
        generated_at=GENERATED_AT,
    )

    assert store_calls == [
        (
            connection,
            "paper-research-packet-quality-v0",
            "watch",
            2,
            "custom_packet_quality_reports",
        ),
    ]
    assert reducer_calls == [((older, latest), config, GENERATED_AT)]
    assert history.source_report_count == 2
    assert history.first_source_generated_at == older.generated_at
    assert history.latest_source_generated_at == latest.generated_at


def test_loader_empty_loaded_reports_produce_empty_history_without_connection_mutation(
    module_under_test: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = NoMutationConnection()
    config = PaperResearchPacketQualityHistoryConfig()
    store_calls: list[tuple[object, str | None, str | None, int | None, str]] = []

    def fake_load(
        received_connection: object,
        *,
        config_version: str | None = None,
        quality_status: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[FakeQualityReport, ...]:
        store_calls.append(
            (
                received_connection,
                config_version,
                quality_status,
                limit,
                table_name,
            ),
        )
        return ()

    monkeypatch.setattr(
        module_under_test,
        "load_paper_research_packet_quality_reports",
        fake_load,
    )

    history = module_under_test.load_paper_research_packet_quality_history_report(
        connection,
        config_version=None,
        quality_status=None,
        limit=None,
        table_name="paper_research_packet_quality_reports",
        config=config,
        generated_at=GENERATED_AT,
    )

    assert store_calls == [
        (
            connection,
            None,
            None,
            None,
            "paper_research_packet_quality_reports",
        ),
    ]
    assert history.source_report_count == 0
    assert history.first_source_generated_at is None
    assert history.latest_source_generated_at is None


def test_loader_rejects_bad_config_exact_type_before_store_load(
    module_under_test: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ConfigSubclass(PaperResearchPacketQualityHistoryConfig):
        pass

    store_calls: list[object] = []

    def fake_load(
        received_connection: object,
        *,
        config_version: str | None = None,
        quality_status: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[FakeQualityReport, ...]:
        store_calls.append(received_connection)
        return ()

    monkeypatch.setattr(
        module_under_test,
        "load_paper_research_packet_quality_reports",
        fake_load,
    )

    with pytest.raises(
        ValueError,
        match="config must be a PaperResearchPacketQualityHistoryConfig",
    ):
        module_under_test.load_paper_research_packet_quality_history_report(
            object(),
            config_version=None,
            quality_status=None,
            limit=5,
            table_name="paper_research_packet_quality_reports",
            config=ConfigSubclass(),
            generated_at=GENERATED_AT,
        )

    assert store_calls == []


def test_loader_module_has_no_direct_storage_env_or_live_client_surface(
    module_under_test: types.ModuleType,
) -> None:
    module_path = module_under_test.__file__
    assert module_path is not None
    source = open(module_path, encoding="utf-8").read()
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

    banned_module_fragments = (
        "db",
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
    )
    banned_import_names = {
        "insert_paper_research_packet_quality_report",
        "insert_paper_research_packet_quality_report_with_result",
        "persist_paper_research_packet_quality_report",
    }
    banned_call_or_attribute_names = {
        "api_key",
        "cancel",
        "close",
        "commit",
        "connect",
        "create_order",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "getenv",
        "insert",
        "persist",
        "print",
        "private_key",
        "replace_order",
        "rollback",
        "sign",
        "submit",
        "wallet",
    }

    assert all(
        fragment not in module_name
        for module_name in imported_modules
        for fragment in banned_module_fragments
    )
    assert not (set(imported_names) & banned_import_names)
    assert not (set(call_names) & banned_call_or_attribute_names)
    assert not (set(attribute_names) & banned_call_or_attribute_names)
