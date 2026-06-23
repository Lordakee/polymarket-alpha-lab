from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab import paper_research_packet_db_history_load as module_under_test
from polymarket_alpha_lab.paper_research_packet import (
    PaperResearchPacketReport,
    PaperResearchPacketRow,
)
from polymarket_alpha_lab.paper_research_packet_db_history import (
    PaperResearchPacketDbHistoryConfig,
    build_paper_research_packet_db_history_report as real_build_history,
)
from polymarket_alpha_lab.paper_research_packet_db_history_load import (
    load_paper_research_packet_db_history_report,
)


GENERATED_AT = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
BASE_AT = datetime(2026, 6, 23, 8, 0, tzinfo=UTC)


class NoMutationConnection:
    def cursor(self) -> None:
        raise AssertionError("loader must not open cursors directly")

    def commit(self) -> None:
        raise AssertionError("loader must not commit")

    def rollback(self) -> None:
        raise AssertionError("loader must not rollback")

    def close(self) -> None:
        raise AssertionError("loader must not close")


def d(value: str) -> Decimal:
    return Decimal(value)


def _packet_row(
    *,
    market_slug: str,
    recommendation_score: Decimal = d("0.900000"),
    net_edge: Decimal = d("0.080000"),
) -> PaperResearchPacketRow:
    return PaperResearchPacketRow(
        packet_rank=1,
        market_slug=market_slug,
        question=f"Will {market_slug} resolve yes?",
        side="yes",
        research_priority="high",
        required_checks=(
            "outcome_definition",
            "liquidity_depth",
            "cost_sensitivity",
            "settlement_timing",
        ),
        reason_codes=("side_edge_recommend",),
        recommendation_score=recommendation_score,
        net_edge=net_edge,
        allocated_notional=d("25.000000"),
        requested_notional=d("40.000000"),
    )


def _packet_report(
    *,
    generated_at: datetime,
    market_slug: str = "event-alpha",
) -> PaperResearchPacketReport:
    row = _packet_row(market_slug=market_slug)
    return PaperResearchPacketReport(
        generated_at=generated_at,
        config_version="paper-research-packet-v0",
        input_row_count=1,
        packet_row_count=1,
        included_count=1,
        skipped_count=0,
        high_priority_count=1,
        medium_priority_count=0,
        low_priority_count=0,
        packet_rows=(row,),
    )


def test_loader_passes_query_options_and_reverses_store_descending_reports(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = object()
    config = PaperResearchPacketDbHistoryConfig()
    older = _packet_report(generated_at=BASE_AT, market_slug="older-event")
    latest = _packet_report(
        generated_at=BASE_AT + timedelta(hours=2),
        market_slug="latest-event",
    )
    store_calls: list[tuple[object, int | None, str]] = []
    reducer_calls: list[
        tuple[
            tuple[PaperResearchPacketReport, ...],
            PaperResearchPacketDbHistoryConfig,
            datetime,
        ]
    ] = []

    def fake_load(
        received_connection: object,
        *,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[PaperResearchPacketReport, ...]:
        store_calls.append((received_connection, limit, table_name))
        return (latest, older)

    def fake_build(
        reports: object,
        *,
        config: PaperResearchPacketDbHistoryConfig,
        generated_at: datetime,
    ):
        reducer_reports = tuple(reports)  # type: ignore[arg-type]
        reducer_calls.append((reducer_reports, config, generated_at))
        return real_build_history(
            list(reducer_reports),
            config=config,
            generated_at=generated_at,
        )

    monkeypatch.setattr(
        module_under_test,
        "load_paper_research_packet_reports",
        fake_load,
    )
    monkeypatch.setattr(
        module_under_test,
        "build_paper_research_packet_db_history_report",
        fake_build,
    )

    history = load_paper_research_packet_db_history_report(
        connection,
        limit=2,
        table_name="custom_packet_reports",
        config=config,
        generated_at=GENERATED_AT,
    )

    assert store_calls == [(connection, 2, "custom_packet_reports")]
    assert reducer_calls == [((older, latest), config, GENERATED_AT)]
    assert history.report_count == 2
    assert history.first_report_generated_at == older.generated_at
    assert history.latest_report_generated_at == latest.generated_at
    assert history.latest_top_packet_market_slug == "latest-event"


def test_loader_empty_loaded_reports_produce_empty_history_without_connection_mutation(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = NoMutationConnection()
    config = PaperResearchPacketDbHistoryConfig()
    store_calls: list[tuple[object, int | None, str]] = []

    def fake_load(
        received_connection: object,
        *,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[PaperResearchPacketReport, ...]:
        store_calls.append((received_connection, limit, table_name))
        return ()

    monkeypatch.setattr(
        module_under_test,
        "load_paper_research_packet_reports",
        fake_load,
    )

    history = load_paper_research_packet_db_history_report(
        connection,
        limit=None,
        table_name="paper_research_packet_reports",
        config=config,
        generated_at=GENERATED_AT,
    )

    assert store_calls == [(connection, None, "paper_research_packet_reports")]
    assert history.report_count == 0
    assert history.first_report_generated_at is None
    assert history.latest_report_generated_at is None
    assert history.latest_top_packet_market_slug is None


def test_loader_module_has_no_direct_connection_env_or_live_client_surface():
    module_path = Path(module_under_test.__file__)
    source = module_path.read_text(encoding="utf-8")
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
        "psycopg",
        "cli",
        "_env",
        "auth",
        "client",
        "exchange",
        "live_trading",
        "network",
        "order",
        "wallet",
    )
    banned_import_names = {
        "insert_paper_research_packet_report",
        "insert_paper_research_packet_report_with_result",
        "persist_paper_research_packet_report",
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
