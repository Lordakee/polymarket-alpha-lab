from __future__ import annotations

import importlib
import sys
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.supabase_paper_research_packet_config import (
    PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR,
    PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR,
    PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_research_packet_quality_config import (
    PAPER_RESEARCH_PACKET_QUALITY_DB_DSN_ENV_VAR,
    PAPER_RESEARCH_PACKET_QUALITY_DB_ENABLED_ENV_VAR,
    PAPER_RESEARCH_PACKET_QUALITY_DB_TABLE_ENV_VAR,
)


CLI_DB_HELPERS = (
    {
        "helper": "_run_nav_snapshot_db_trend",
        "loader_module": "polymarket_alpha_lab.paper_nav_snapshot_db_trend_load",
        "loader": "load_paper_nav_snapshot_db_trend_report",
        "extra_kwargs": {},
    },
    {
        "helper": "_run_strategy_audit_db_history",
        "loader_module": "polymarket_alpha_lab.strategy_audit_db_history_load",
        "loader": "load_strategy_audit_db_history_report",
        "extra_kwargs": {},
    },
    {
        "helper": "_run_cost_audit_db_trend",
        "loader_module": "polymarket_alpha_lab.paper_trade_cost_audit_db_history_load",
        "loader": "load_paper_trade_cost_audit_db_history_report",
        "extra_kwargs": {},
    },
    {
        "helper": "_run_outcome_tracking_db_history",
        "loader_module": "polymarket_alpha_lab.outcome_tracking_db_history_load",
        "loader": "load_outcome_tracking_db_history_report",
        "extra_kwargs": {"stale_after_seconds": 7200},
    },
    {
        "helper": "_run_local_observability_trends_db_history",
        "loader_module": "polymarket_alpha_lab.local_observability_trends_db_history_load",
        "loader": "load_local_observability_trends_db_history_report",
        "extra_kwargs": {},
    },
    # `paper-research-packet-db-history` is intentionally excluded here.
    # It uses an autocommit-only read path with dedicated cleanup tests in
    # tests/test_cli_paper_research_packet_db_history.py, so it does not share
    # the commit/rollback contract exercised by the other DB history helpers.
)


class FakeConnection:
    def __init__(
        self,
        *,
        fail_commit: bool = False,
        fail_rollback: bool = False,
        fail_close: bool = False,
    ) -> None:
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0
        self.fail_commit = fail_commit
        self.fail_rollback = fail_rollback
        self.fail_close = fail_close

    def commit(self) -> None:
        self.commit_count += 1
        if self.fail_commit:
            raise RuntimeError("commit failed without dsn")

    def rollback(self) -> None:
        self.rollback_count += 1
        if self.fail_rollback:
            raise RuntimeError("rollback failed without dsn")

    def close(self) -> None:
        self.close_count += 1
        if self.fail_close:
            raise RuntimeError("close failed without dsn")


def _install_psycopg(
    monkeypatch: pytest.MonkeyPatch,
    connection: FakeConnection,
) -> list[str]:
    connect_calls: list[str] = []

    def fake_connect(dsn: str) -> FakeConnection:
        connect_calls.append(dsn)
        return connection

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    return connect_calls


def _install_psycopg_connection_map(
    monkeypatch: pytest.MonkeyPatch,
    connections_by_dsn: dict[str, FakeConnection],
) -> list[tuple[str, bool]]:
    connect_calls: list[tuple[str, bool]] = []

    def fake_connect(dsn: str, **kwargs: Any) -> FakeConnection:
        connect_calls.append((dsn, bool(kwargs.get("autocommit", False))))
        return connections_by_dsn[dsn]

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    return connect_calls


def _install_loader(
    monkeypatch: pytest.MonkeyPatch,
    case: dict[str, Any],
    loader: Any,
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    loader_module = importlib.import_module(case["loader_module"])

    def wrapped_loader(**kwargs: Any) -> Any:
        calls.append(dict(kwargs))
        return loader(**kwargs)

    monkeypatch.setattr(loader_module, case["loader"], wrapped_loader)
    return calls


def _run_case(case: dict[str, Any]) -> Any:
    kwargs = {
        "dsn": "postgresql://user:secret@example.invalid/db",
        "table_name": "paper_report_archive",
        "limit": 7,
        "runner": None,
    }
    kwargs.update(case["extra_kwargs"])
    return getattr(cli, case["helper"])(**kwargs)


def _set_packet_quality_operator_env(
    monkeypatch: pytest.MonkeyPatch,
    *,
    source_dsn: str,
    source_table: str,
    quality_dsn: str,
    quality_table: str,
) -> None:
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR, source_table)
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_QUALITY_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_QUALITY_DB_DSN_ENV_VAR, quality_dsn)
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_QUALITY_DB_TABLE_ENV_VAR, quality_table)


def _summary_quality_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
        quality_status="pass",
        source_generated_at=datetime(2026, 6, 23, 11, 0, tzinfo=UTC),
        source_age_seconds=3600,
        included_share=None,
        skipped_share=None,
        check_count=0,
        pass_count=0,
        watch_count=0,
        blocked_count=0,
        check_rows=(),
        reason_code_counts=(),
    )


def _install_packet_quality_default_build(
    monkeypatch: pytest.MonkeyPatch,
    *,
    source_report: object,
    quality_report: object,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    loader_calls: list[dict[str, Any]] = []
    builder_calls: list[dict[str, Any]] = []

    def fake_load(
        connection: object,
        *,
        limit: int,
        table_name: str,
    ) -> tuple[object, ...]:
        loader_calls.append(
            {
                "connection": connection,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return (source_report,)

    def fake_build(
        packet_report: object,
        *,
        config: object,
        generated_at: datetime,
    ) -> object:
        builder_calls.append(
            {
                "packet_report": packet_report,
                "config": config,
                "generated_at": generated_at,
            },
        )
        return quality_report

    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_research_packet_store."
        "load_paper_research_packet_reports",
        fake_load,
    )
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_research_packet_quality."
        "build_paper_research_packet_quality_report",
        fake_build,
    )
    return loader_calls, builder_calls


@pytest.mark.parametrize("case", CLI_DB_HELPERS, ids=lambda case: case["helper"])
def test_cli_inline_db_cleanup_does_not_mask_loader_exception(
    monkeypatch: pytest.MonkeyPatch,
    case: dict[str, Any],
) -> None:
    connection = FakeConnection(fail_rollback=True, fail_close=True)
    connect_calls = _install_psycopg(monkeypatch, connection)

    def fail_loader(**kwargs: Any) -> None:
        raise ValueError("read failed without dsn")

    loader_calls = _install_loader(monkeypatch, case, fail_loader)

    with pytest.raises(ValueError) as exc_info:
        _run_case(case)

    assert str(exc_info.value) == "read failed without dsn"
    assert connect_calls == ["postgresql://user:secret@example.invalid/db"]
    assert len(loader_calls) == 1
    assert loader_calls[0]["connection"] is connection
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


@pytest.mark.parametrize("case", CLI_DB_HELPERS, ids=lambda case: case["helper"])
def test_cli_inline_db_cleanup_does_not_mask_commit_exception(
    monkeypatch: pytest.MonkeyPatch,
    case: dict[str, Any],
) -> None:
    connection = FakeConnection(
        fail_commit=True,
        fail_rollback=True,
        fail_close=True,
    )
    _install_psycopg(monkeypatch, connection)
    _install_loader(monkeypatch, case, lambda **kwargs: "ok")

    with pytest.raises(RuntimeError) as exc_info:
        _run_case(case)

    assert str(exc_info.value) == "commit failed without dsn"
    assert connection.commit_count == 1
    assert connection.rollback_count == 1
    assert connection.close_count == 1


@pytest.mark.parametrize("case", CLI_DB_HELPERS, ids=lambda case: case["helper"])
def test_cli_inline_db_close_failure_does_not_replace_success(
    monkeypatch: pytest.MonkeyPatch,
    case: dict[str, Any],
) -> None:
    connection = FakeConnection(fail_close=True)
    _install_psycopg(monkeypatch, connection)
    _install_loader(monkeypatch, case, lambda **kwargs: "ok")

    result = _run_case(case)

    assert result == "ok"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_packet_quality_cli_persist_commits_quality_connection_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_dsn = "postgresql://packet-source.example.invalid/db"
    source_table = "paper_research_packet_archive"
    quality_dsn = "postgresql://packet-quality.example.invalid/db"
    quality_table = "paper_research_packet_quality_reports"
    _set_packet_quality_operator_env(
        monkeypatch,
        source_dsn=source_dsn,
        source_table=source_table,
        quality_dsn=quality_dsn,
        quality_table=quality_table,
    )
    source_connection = FakeConnection()
    quality_connection = FakeConnection()
    connect_calls = _install_psycopg_connection_map(
        monkeypatch,
        {
            source_dsn: source_connection,
            quality_dsn: quality_connection,
        },
    )
    source_report = SimpleNamespace(kind="source-packet")
    quality_report = _summary_quality_report()
    loader_calls, builder_calls = _install_packet_quality_default_build(
        monkeypatch,
        source_report=source_report,
        quality_report=quality_report,
    )
    insert_calls: list[dict[str, object]] = []

    def fake_insert(
        connection: object,
        report: object,
        *,
        table_name: str,
    ) -> object:
        insert_calls.append(
            {
                "connection": connection,
                "report": report,
                "table_name": table_name,
            },
        )
        return SimpleNamespace(report_sha256="a" * 64)

    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_research_packet_quality_store."
        "insert_paper_research_packet_quality_report",
        fake_insert,
    )

    exit_code = cli.main(
        ["paper-research-packet-quality", "--persist"],
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert connect_calls == [(source_dsn, True), (quality_dsn, False)]
    assert loader_calls == [
        {
            "connection": source_connection,
            "limit": 1,
            "table_name": source_table,
        },
    ]
    assert len(builder_calls) == 1
    assert builder_calls[0]["packet_report"] is source_report
    assert isinstance(builder_calls[0]["generated_at"], datetime)
    assert builder_calls[0]["generated_at"].tzinfo is UTC
    assert insert_calls == [
        {
            "connection": quality_connection,
            "report": quality_report,
            "table_name": quality_table,
        },
    ]
    assert source_connection.commit_count == 0
    assert source_connection.rollback_count == 0
    assert source_connection.close_count == 1
    assert quality_connection.commit_count == 1
    assert quality_connection.rollback_count == 0
    assert quality_connection.close_count == 1


def test_packet_quality_cli_persist_rolls_back_and_closes_on_insert_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_dsn = "postgresql://packet-source.example.invalid/db"
    source_table = "paper_research_packet_archive"
    quality_dsn = "postgresql://packet-quality.example.invalid/db"
    quality_table = "paper_research_packet_quality_reports"
    _set_packet_quality_operator_env(
        monkeypatch,
        source_dsn=source_dsn,
        source_table=source_table,
        quality_dsn=quality_dsn,
        quality_table=quality_table,
    )
    source_connection = FakeConnection()
    quality_connection = FakeConnection()
    connect_calls = _install_psycopg_connection_map(
        monkeypatch,
        {
            source_dsn: source_connection,
            quality_dsn: quality_connection,
        },
    )
    quality_report = _summary_quality_report()
    _install_packet_quality_default_build(
        monkeypatch,
        source_report=SimpleNamespace(kind="source-packet"),
        quality_report=quality_report,
    )
    insert_calls: list[dict[str, object]] = []

    def broken_insert(
        connection: object,
        report: object,
        *,
        table_name: str,
    ) -> object:
        insert_calls.append(
            {
                "connection": connection,
                "report": report,
                "table_name": table_name,
            },
        )
        raise ValueError("insert failed without dsn")

    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_research_packet_quality_store."
        "insert_paper_research_packet_quality_report",
        broken_insert,
    )

    exit_code = cli.main(
        ["paper-research-packet-quality", "--persist"],
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    assert connect_calls == [(source_dsn, True), (quality_dsn, False)]
    assert insert_calls == [
        {
            "connection": quality_connection,
            "report": quality_report,
            "table_name": quality_table,
        },
    ]
    assert source_connection.commit_count == 0
    assert source_connection.rollback_count == 0
    assert source_connection.close_count == 1
    assert quality_connection.commit_count == 0
    assert quality_connection.rollback_count == 1
    assert quality_connection.close_count == 1


def test_packet_quality_db_history_read_path_uses_autocommit_and_closes_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from polymarket_alpha_lab.paper_research_packet_quality_history import (
        PaperResearchPacketQualityHistoryConfig,
    )

    dsn = "postgresql://packet-quality-history.example.invalid/db"
    table_name = "paper_research_packet_quality_reports"
    connection = FakeConnection()
    connect_calls = _install_psycopg_connection_map(
        monkeypatch,
        {dsn: connection},
    )
    report = SimpleNamespace(history_status="pass")
    loader_calls: list[dict[str, object]] = []

    def fake_load(
        received_connection: object,
        *,
        config_version: str | None = None,
        quality_status: str | None = None,
        limit: int | None,
        table_name: str,
        config: PaperResearchPacketQualityHistoryConfig,
        generated_at: datetime,
    ) -> object:
        loader_calls.append(
            {
                "connection": received_connection,
                "config_version": config_version,
                "quality_status": quality_status,
                "limit": limit,
                "table_name": table_name,
                "config": config,
                "generated_at": generated_at,
            },
        )
        return report

    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_research_packet_quality_history_load."
        "load_paper_research_packet_quality_history_report",
        fake_load,
    )

    result = getattr(cli, "_run_paper_research_packet_quality_db_history")(
        dsn=dsn,
        table_name=table_name,
        limit=7,
        runner=None,
    )

    assert result is report
    assert connect_calls == [(dsn, True)]
    assert len(loader_calls) == 1
    assert loader_calls[0]["connection"] is connection
    assert loader_calls[0]["config_version"] is None
    assert loader_calls[0]["quality_status"] is None
    assert loader_calls[0]["limit"] == 7
    assert loader_calls[0]["table_name"] == table_name
    assert type(loader_calls[0]["config"]) is PaperResearchPacketQualityHistoryConfig
    assert isinstance(loader_calls[0]["generated_at"], datetime)
    assert loader_calls[0]["generated_at"].tzinfo is UTC
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1
