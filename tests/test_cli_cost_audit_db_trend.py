from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.paper_trade_cost_audit import PaperTradeCostAuditReport
from polymarket_alpha_lab.paper_trade_cost_audit_db_row import (
    paper_trade_cost_audit_report_to_db_row,
)
from polymarket_alpha_lab.paper_trade_cost_trend import (
    PaperTradeCostTrendReport,
    PaperTradeCostTrendStatusRow,
)
from polymarket_alpha_lab.supabase_paper_trade_cost_audit_config import (
    PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR,
    PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR,
    PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR,
)


def _cost_audit_report(
    *,
    generated_at: datetime,
    mean_cost_adjusted_edge: Decimal,
    mean_edge_cost_drag: Decimal,
    negative_cost_adjusted_edge_count: int,
) -> PaperTradeCostAuditReport:
    return PaperTradeCostAuditReport(
        generated_at=generated_at,
        config_version="paper-trade-cost-audit-v0",
        trade_count=1,
        total_filled_size=Decimal("100"),
        total_requested_size=Decimal("100"),
        fill_rate=Decimal("1.000000"),
        mean_theoretical_edge=Decimal("0.050000"),
        mean_cost_adjusted_edge=mean_cost_adjusted_edge,
        mean_edge_cost_drag=mean_edge_cost_drag,
        total_edge_cost_drag=Decimal("1.000000"),
        mean_research_slippage=Decimal("0.004000"),
        mean_fill_slippage=Decimal("0.006000"),
        partial_fill_count=0,
        negative_cost_adjusted_edge_count=negative_cost_adjusted_edge_count,
        largest_single_trade_cost_drag=Decimal("1.000000"),
    )


def _source_record(report: PaperTradeCostAuditReport) -> tuple[object, ...]:
    row = paper_trade_cost_audit_report_to_db_row(report)
    return (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.trade_count,
        row.total_filled_size,
        row.total_requested_size,
        row.fill_rate,
        row.mean_theoretical_edge,
        row.mean_cost_adjusted_edge,
        row.mean_edge_cost_drag,
        row.total_edge_cost_drag,
        row.mean_research_slippage,
        row.mean_fill_slippage,
        row.partial_fill_count,
        row.negative_cost_adjusted_edge_count,
        row.largest_single_trade_cost_drag,
        row.payload_json,
        row.paper_only,
        row.report_only,
        row.readonly,
    )


def _trend_report() -> PaperTradeCostTrendReport:
    early = _cost_audit_report(
        generated_at=datetime(2026, 6, 20, 8, 0, tzinfo=UTC),
        mean_cost_adjusted_edge=Decimal("0.040000"),
        mean_edge_cost_drag=Decimal("0.010000"),
        negative_cost_adjusted_edge_count=0,
    )
    latest = _cost_audit_report(
        generated_at=datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
        mean_cost_adjusted_edge=Decimal("-0.010000"),
        mean_edge_cost_drag=Decimal("0.020000"),
        negative_cost_adjusted_edge_count=1,
    )
    return PaperTradeCostTrendReport(
        generated_at=datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
        config_version="cost-audit-db-trend-v0",
        cost_audit_report_count=2,
        first_report_generated_at=early.generated_at,
        latest_report_generated_at=latest.generated_at,
        latest_trade_count=latest.trade_count,
        latest_fill_rate=latest.fill_rate,
        latest_mean_theoretical_edge=latest.mean_theoretical_edge,
        latest_mean_cost_adjusted_edge=latest.mean_cost_adjusted_edge,
        latest_mean_edge_cost_drag=latest.mean_edge_cost_drag,
        latest_total_edge_cost_drag=latest.total_edge_cost_drag,
        latest_partial_fill_count=latest.partial_fill_count,
        latest_negative_cost_adjusted_edge_count=(
            latest.negative_cost_adjusted_edge_count
        ),
        worst_observed_mean_edge_cost_drag=Decimal("0.020000"),
        worst_observed_negative_cost_adjusted_edge_count=1,
        consecutive_negative_cost_adjusted_edge_count=1,
        status="latest_negative_cost_adjusted_edges",
        status_rows=(
            PaperTradeCostTrendStatusRow(
                "empty_cost_audit_history",
                0,
                Decimal("0.000000"),
            ),
            PaperTradeCostTrendStatusRow(
                "latest_cost_observed",
                1,
                Decimal("0.500000"),
            ),
            PaperTradeCostTrendStatusRow(
                "latest_negative_cost_adjusted_edges",
                1,
                Decimal("0.500000"),
            ),
        ),
    )


def test_cost_audit_db_trend_cli_requires_enabled_db_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR, raising=False)
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("cost-audit-db-trend runner should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        ["cost-audit-db-trend"],
        cost_audit_db_trend_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert "cost-audit-db-trend failed:" in captured.err
    assert (
        "cost-audit-db-trend requires paper trade cost audit DB to be enabled"
    ) in captured.err


def test_cost_audit_db_trend_cli_uses_injected_runner_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://cost-audit-db-trend.example.invalid/db"
    monkeypatch.setenv(PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR,
        "paper_trade_cost_audit_archive",
    )
    calls: list[dict[str, object]] = []
    trend_report = _trend_report()

    def fake_runner(**kwargs: Any) -> PaperTradeCostTrendReport:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == "paper_trade_cost_audit_archive"
        assert kwargs["limit"] == 25
        assert kwargs["config_version"] == "cost-audit-db-trend-v0"
        assert isinstance(kwargs["generated_at"], datetime)
        return trend_report

    exit_code = main(
        [
            "cost-audit-db-trend",
            "--limit",
            "25",
        ],
        cost_audit_db_trend_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert "cost-audit-db-trend:" in captured.out
    assert "status=latest_negative_cost_adjusted_edges" in captured.out
    assert "report_count=2" in captured.out
    assert "first_report_generated_at=2026-06-20T08:00:00+00:00" in captured.out
    assert "latest_report_generated_at=2026-06-20T09:00:00+00:00" in captured.out
    assert "latest_trade_count=1" in captured.out
    assert "latest_fill_rate=1.000000" in captured.out
    assert "latest_mean_cost_adjusted_edge=-0.010000" in captured.out
    assert "latest_mean_edge_cost_drag=0.020000" in captured.out
    assert "latest_negative_cost_adjusted_edge_count=1" in captured.out
    assert "worst_observed_mean_edge_cost_drag=0.020000" in captured.out
    assert "consecutive_negative_cost_adjusted_edge_count=1" in captured.out
    assert (
        "status_rows: empty_cost_audit_history:0,"
        "latest_cost_observed:1,"
        "latest_negative_cost_adjusted_edges:1"
    ) in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "paper_trade_cost_audit_archive" not in captured.out


def test_cost_audit_db_trend_cli_default_load_path_no_network(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://cost-audit-db-trend.example.invalid/db"
    monkeypatch.setenv(PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR,
        "paper_trade_cost_audit_archive",
    )
    rows = (
        _source_record(
            _cost_audit_report(
                generated_at=datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
                mean_cost_adjusted_edge=Decimal("-0.010000"),
                mean_edge_cost_drag=Decimal("0.020000"),
                negative_cost_adjusted_edge_count=1,
            ),
        ),
        _source_record(
            _cost_audit_report(
                generated_at=datetime(2026, 6, 20, 8, 0, tzinfo=UTC),
                mean_cost_adjusted_edge=Decimal("0.040000"),
                mean_edge_cost_drag=Decimal("0.010000"),
                negative_cost_adjusted_edge_count=0,
            ),
        ),
    )

    class FakeCursor:
        def __init__(
            self,
            fetched_rows: tuple[tuple[object, ...], ...],
        ) -> None:
            self.rows = fetched_rows
            self.calls: list[tuple[str, tuple[object, ...]]] = []
            self.closed = False

        def execute(self, sql: str, params: tuple[object, ...] = ()) -> None:
            self.calls.append((" ".join(sql.split()), params))

        def fetchall(self) -> tuple[tuple[object, ...], ...]:
            return self.rows

        def close(self) -> None:
            self.closed = True

    class FakeConnection:
        def __init__(
            self,
            fetched_rows: tuple[tuple[object, ...], ...],
        ) -> None:
            self.cursor_instance = FakeCursor(fetched_rows)
            self.cursor_count = 0
            self.commit_count = 0
            self.rollback_count = 0
            self.close_count = 0

        def cursor(self) -> FakeCursor:
            self.cursor_count += 1
            return self.cursor_instance

        def commit(self) -> None:
            self.commit_count += 1

        def rollback(self) -> None:
            self.rollback_count += 1

        def close(self) -> None:
            self.close_count += 1

    connection = FakeConnection(rows)
    connect_calls: list[str] = []

    def fake_connect(connect_dsn: str) -> FakeConnection:
        connect_calls.append(connect_dsn)
        if connect_dsn != dsn:
            raise AssertionError(f"unexpected dsn: {connect_dsn}")
        return connection

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))

    exit_code = main(
        [
            "cost-audit-db-trend",
            "--limit",
            "2",
        ],
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert connect_calls == [dsn]
    assert connection.cursor_count == 1
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert "FROM paper_trade_cost_audit_archive" in sql
    assert "ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC" in sql
    assert params == (2,)

    captured = capsys.readouterr()
    assert "cost-audit-db-trend:" in captured.out
    assert "status=latest_negative_cost_adjusted_edges" in captured.out
    assert "report_count=2" in captured.out
    assert "first_report_generated_at=2026-06-20T08:00:00+00:00" in captured.out
    assert "latest_report_generated_at=2026-06-20T09:00:00+00:00" in captured.out
    assert "latest_trade_count=1" in captured.out
    assert "latest_fill_rate=1.000000" in captured.out
    assert "latest_mean_cost_adjusted_edge=-0.010000" in captured.out
    assert "latest_mean_edge_cost_drag=0.020000" in captured.out
    assert "latest_negative_cost_adjusted_edge_count=1" in captured.out
    assert "worst_observed_mean_edge_cost_drag=0.020000" in captured.out
    assert "consecutive_negative_cost_adjusted_edge_count=1" in captured.out
    assert (
        "status_rows: empty_cost_audit_history:0,"
        "latest_cost_observed:1,"
        "latest_negative_cost_adjusted_edges:1"
    ) in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "paper_trade_cost_audit_archive" not in captured.out


def test_cost_audit_db_trend_cli_redacts_dsn_on_read_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://cost-audit-db-trend-secret.example.invalid/db"
    monkeypatch.setenv(PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR, dsn)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(f"could not connect to {dsn}")

    exit_code = main(
        ["cost-audit-db-trend"],
        cost_audit_db_trend_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "cost-audit-db-trend failed: could not connect to <redacted-dsn>"
    ) in captured.err
    assert dsn not in captured.out
    assert dsn not in captured.err


@pytest.mark.parametrize(
    "flag",
    (
        "--dsn",
        "--db-dsn",
        "--paper-trade-cost-audit-db-dsn",
    ),
)
def test_cost_audit_db_trend_cli_rejects_dsn_flags(
    capsys: pytest.CaptureFixture[str],
    flag: str,
) -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "cost-audit-db-trend",
                flag,
                "forbidden-value",
            ],
            client_factory=lambda: "fake-client",
        )

    captured = capsys.readouterr()
    assert f"unrecognized arguments: {flag}" in captured.err


def test_cost_audit_db_trend_cli_rejects_non_positive_limit(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://cost-audit-db-trend.example.invalid/db"
    monkeypatch.setenv(PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR, dsn)

    def forbidden_runner(**kwargs: Any) -> object:
        raise AssertionError("cost-audit-db-trend runner should not run")

    exit_code = main(
        [
            "cost-audit-db-trend",
            "--limit",
            "0",
        ],
        cost_audit_db_trend_runner=forbidden_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "cost-audit-db-trend failed: "
        "cost-audit-db-trend limit must be positive"
    ) in captured.err
    assert dsn not in captured.out
    assert dsn not in captured.err
