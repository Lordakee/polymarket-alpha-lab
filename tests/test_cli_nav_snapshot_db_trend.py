from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.nav_risk_metrics import (
    PaperNavRiskMetricsConfig,
    build_paper_nav_risk_metrics_report,
)
from polymarket_alpha_lab.nav_risk_trend import (
    PaperNavRiskTrendConfig,
    PaperNavRiskTrendReport,
    build_paper_nav_risk_trend_report,
)
from polymarket_alpha_lab.paper_nav_snapshot_db_row import (
    paper_nav_snapshot_to_db_row,
)
from polymarket_alpha_lab.positions import PaperNavSnapshot
from polymarket_alpha_lab.supabase_paper_nav_snapshot_config import (
    PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR,
    PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR,
    PAPER_NAV_SNAPSHOT_DB_TABLE_ENV_VAR,
)


GENERATED_AT = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "nav-snapshot-db-trend-v0"


def _snapshot(marked_at: datetime, *, exit_nav: Decimal) -> PaperNavSnapshot:
    return PaperNavSnapshot(
        marked_at=marked_at,
        starting_cash=exit_nav,
        cash_balance=exit_nav,
        realized_pnl=Decimal("0.0000"),
        exit_nav=exit_nav,
        midpoint_nav=exit_nav,
        total_cost_basis=Decimal("0.0000"),
        unrealized_exit_pnl=Decimal("0.0000"),
        marks=(),
    )


def _trend_report() -> PaperNavRiskTrendReport:
    snapshots = (
        _snapshot(
            datetime(2026, 6, 21, 9, 0, tzinfo=UTC),
            exit_nav=Decimal("10000.0000"),
        ),
        _snapshot(
            datetime(2026, 6, 21, 10, 0, tzinfo=UTC),
            exit_nav=Decimal("9900.0000"),
        ),
        _snapshot(
            datetime(2026, 6, 21, 11, 0, tzinfo=UTC),
            exit_nav=Decimal("10100.0000"),
        ),
    )
    metric_reports = tuple(
        build_paper_nav_risk_metrics_report(
            snapshots[:prefix_size],
            config=PaperNavRiskMetricsConfig(
                config_version="nav-risk-metrics-v0",
                preserve_input_order=True,
            ),
            generated_at=GENERATED_AT,
        )
        for prefix_size in range(1, len(snapshots) + 1)
    )
    return build_paper_nav_risk_trend_report(
        metric_reports,
        config=PaperNavRiskTrendConfig(config_version=CONFIG_VERSION),
        generated_at=GENERATED_AT,
    )


def _source_record(snapshot: PaperNavSnapshot) -> tuple[object, ...]:
    row = paper_nav_snapshot_to_db_row(snapshot)
    return (
        row.snapshot_sha256,
        row.marked_at,
        row.starting_cash,
        row.cash_balance,
        row.exit_nav,
        row.midpoint_nav,
        row.total_cost_basis,
        row.unrealized_exit_pnl,
        row.mark_count,
        row.payload_json,
        row.paper_only,
    )


def test_nav_snapshot_db_trend_cli_requires_enabled_db_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(PAPER_NAV_SNAPSHOT_DB_TABLE_ENV_VAR, raising=False)
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("nav-snapshot-db-trend runner should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        ["nav-snapshot-db-trend"],
        nav_snapshot_db_trend_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert "nav-snapshot-db-trend failed:" in captured.err
    assert (
        "nav-snapshot-db-trend requires paper NAV snapshot DB to be enabled"
    ) in captured.err


def test_nav_snapshot_db_trend_cli_uses_injected_runner_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://nav-snapshot-db-trend@localhost/db"
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_TABLE_ENV_VAR, "paper_nav_archive")
    calls: list[dict[str, object]] = []

    def fake_runner(**kwargs: Any) -> PaperNavRiskTrendReport:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == "paper_nav_archive"
        assert kwargs["limit"] == 25
        assert kwargs["config_version"] == CONFIG_VERSION
        assert isinstance(kwargs["generated_at"], datetime)
        return _trend_report()

    exit_code = main(
        [
            "nav-snapshot-db-trend",
            "--limit",
            "25",
        ],
        nav_snapshot_db_trend_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert "nav-snapshot-db-trend:" in captured.out
    assert "status=latest_nav_risk_observed" in captured.out
    assert "report_count=3" in captured.out
    assert "latest_exit_nav=10100.0000" in captured.out
    assert "latest_cumulative_return=0.010000" in captured.out
    assert "latest_max_drawdown=100.0000" in captured.out
    assert "latest_max_drawdown_pct=0.010000" in captured.out
    assert "latest_open_position_count=0" in captured.out
    assert "consecutive_unexecutable_open_position_count=0" in captured.out
    assert "status_rows:" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "paper_nav_archive" not in captured.out


def test_nav_snapshot_db_trend_cli_default_load_path_no_network(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://nav-snapshot-db-trend@localhost/db"
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_TABLE_ENV_VAR, "paper_nav_archive")
    rows = (
        _source_record(
            _snapshot(
                datetime(2026, 6, 21, 11, 0, tzinfo=UTC),
                exit_nav=Decimal("10100.0000"),
            ),
        ),
        _source_record(
            _snapshot(
                datetime(2026, 6, 21, 10, 0, tzinfo=UTC),
                exit_nav=Decimal("9900.0000"),
            ),
        ),
    )

    class FakeCursor:
        def __init__(self, fetched_rows: tuple[tuple[object, ...], ...]) -> None:
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
        def __init__(self, fetched_rows: tuple[tuple[object, ...], ...]) -> None:
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
        return connection

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))

    exit_code = main(
        [
            "nav-snapshot-db-trend",
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
    assert "FROM paper_nav_archive" in sql
    assert "ORDER BY marked_at DESC, snapshot_sha256 DESC" in sql
    assert params == (2,)
    captured = capsys.readouterr()
    assert "nav-snapshot-db-trend:" in captured.out
    assert "report_count=2" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "paper_nav_archive" not in captured.out


def test_nav_snapshot_db_trend_cli_redacts_dsn_on_read_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://nav-snapshot-db-trend-secret@localhost/db"
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR, dsn)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(f"could not connect to {dsn}")

    exit_code = main(
        ["nav-snapshot-db-trend"],
        nav_snapshot_db_trend_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "nav-snapshot-db-trend failed: could not connect to <redacted-dsn>" in (
        captured.err
    )
    assert dsn not in captured.out
    assert dsn not in captured.err


@pytest.mark.parametrize("flag", ("--dsn", "--db-dsn", "--paper-nav-snapshot-db-dsn"))
def test_nav_snapshot_db_trend_cli_rejects_dsn_flags(
    capsys: pytest.CaptureFixture[str],
    flag: str,
) -> None:
    with pytest.raises(SystemExit):
        main(["nav-snapshot-db-trend", flag, "forbidden-value"])

    captured = capsys.readouterr()
    assert f"unrecognized arguments: {flag}" in captured.err


def test_nav_snapshot_db_trend_cli_rejects_non_positive_limit(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://nav-snapshot-db-trend@localhost/db"
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR, dsn)

    exit_code = main(
        [
            "nav-snapshot-db-trend",
            "--limit",
            "0",
        ],
        nav_snapshot_db_trend_runner=lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("runner should not run"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "nav-snapshot-db-trend failed: "
        "nav-snapshot-db-trend limit must be positive"
    ) in captured.err
    assert dsn not in captured.out
    assert dsn not in captured.err
