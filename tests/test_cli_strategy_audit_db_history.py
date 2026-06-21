from __future__ import annotations

import sys
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.strategy_audit_history import (
    PaperStrategyRiskAuditHistoryConfig,
    PaperStrategyRiskAuditHistoryReport,
    build_paper_strategy_risk_audit_history_report,
)
from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
)
from polymarket_alpha_lab.strategy_risk_audit_db_row import (
    strategy_risk_audit_report_to_db_row,
)
from polymarket_alpha_lab.supabase_strategy_risk_audit_config import (
    STRATEGY_RISK_AUDIT_DB_DSN_ENV_VAR,
    STRATEGY_RISK_AUDIT_DB_ENABLED_ENV_VAR,
    STRATEGY_RISK_AUDIT_DB_TABLE_ENV_VAR,
)


GENERATED_AT = datetime(2026, 6, 21, 10, 0, tzinfo=UTC)
HISTORY_CONFIG_VERSION = "strategy-audit-db-history-v0"
ALL_GATE_NAMES = (
    "paper_history",
    "settlement_evidence",
    "forecast_quality",
    "cost_discipline",
    "nav_drawdown",
    "open_exposure",
)


def _audit_report(
    status: str,
    *,
    generated_at: datetime,
) -> PaperStrategyRiskAuditReport:
    status_map = {
        "audit_ready": ("pass", 6, 0, 0),
        "insufficient_evidence": ("incomplete", 0, 0, 6),
        "blocked_by_risk": ("fail", 0, 6, 0),
    }
    gate_status, pass_count, fail_count, incomplete_count = status_map[status]
    return PaperStrategyRiskAuditReport(
        generated_at=generated_at,
        config_version="strategy-risk-audit-v0",
        status=status,
        gate_count=6,
        pass_count=pass_count,
        fail_count=fail_count,
        incomplete_count=incomplete_count,
        gate_results=tuple(
            PaperStrategyRiskAuditGateResult(
                gate_name=gate_name,
                status=gate_status,
                message="gate-message",
            )
            for gate_name in ALL_GATE_NAMES
        ),
    )


def _config() -> PaperStrategyRiskAuditHistoryConfig:
    return PaperStrategyRiskAuditHistoryConfig(
        config_version=HISTORY_CONFIG_VERSION,
    )


def _history_report() -> PaperStrategyRiskAuditHistoryReport:
    return build_paper_strategy_risk_audit_history_report(
        (
            _audit_report(
                "audit_ready",
                generated_at=datetime(2026, 6, 21, 7, 0, tzinfo=UTC),
            ),
            _audit_report(
                "blocked_by_risk",
                generated_at=datetime(2026, 6, 21, 9, 0, tzinfo=UTC),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )


def _source_record(report: PaperStrategyRiskAuditReport) -> tuple[object, ...]:
    row = strategy_risk_audit_report_to_db_row(report)
    return (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.status,
        row.gate_count,
        row.pass_count,
        row.fail_count,
        row.incomplete_count,
        row.gate_results_json,
        row.payload_json,
        row.paper_only,
        row.report_only,
        row.readonly,
    )


def test_strategy_audit_db_history_cli_requires_enabled_db_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(STRATEGY_RISK_AUDIT_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(STRATEGY_RISK_AUDIT_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(STRATEGY_RISK_AUDIT_DB_TABLE_ENV_VAR, raising=False)
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("strategy-audit-db-history runner should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        ["strategy-audit-db-history"],
        strategy_audit_db_history_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert "strategy-audit-db-history failed:" in captured.err
    assert (
        "strategy-audit-db-history requires strategy risk audit DB to be enabled"
    ) in captured.err


def test_strategy_audit_db_history_cli_uses_injected_runner_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://strategy-audit-db-history.example.invalid/db"
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        STRATEGY_RISK_AUDIT_DB_TABLE_ENV_VAR,
        "strategy_risk_audit_archive",
    )
    calls: list[dict[str, object]] = []
    history_report = _history_report()

    def fake_runner(**kwargs: Any) -> PaperStrategyRiskAuditHistoryReport:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == "strategy_risk_audit_archive"
        assert kwargs["limit"] == 25
        assert kwargs["config"] == _config()
        assert isinstance(kwargs["generated_at"], datetime)
        return history_report

    exit_code = main(
        [
            "strategy-audit-db-history",
            "--limit",
            "25",
        ],
        strategy_audit_db_history_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert "strategy-audit-db-history:" in captured.out
    assert "reports=2" in captured.out
    assert "status=latest_blocked_by_risk" in captured.out
    assert "latest_status=blocked_by_risk" in captured.out
    assert "audit_ready=1" in captured.out
    assert "insufficient_evidence=0" in captured.out
    assert "blocked_by_risk=1" in captured.out
    assert "first=2026-06-21T07:00:00+00:00" in captured.out
    assert "latest=2026-06-21T09:00:00+00:00" in captured.out
    assert "consecutive_non_ready=1" in captured.out
    assert "latest_failed_gates=paper_history,settlement_evidence" in captured.out
    assert "paper_history: pass=1 fail=1 incomplete=0" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "strategy_risk_audit_archive" not in captured.out


def test_strategy_audit_db_history_cli_default_load_path_no_network(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://strategy-audit-db-history.example.invalid/db"
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        STRATEGY_RISK_AUDIT_DB_TABLE_ENV_VAR,
        "strategy_risk_audit_archive",
    )
    rows = (
        _source_record(
            _audit_report(
                "blocked_by_risk",
                generated_at=datetime(2026, 6, 21, 9, 0, tzinfo=UTC),
            ),
        ),
        _source_record(
            _audit_report(
                "audit_ready",
                generated_at=datetime(2026, 6, 21, 7, 0, tzinfo=UTC),
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
            "strategy-audit-db-history",
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
    assert "FROM strategy_risk_audit_archive" in sql
    assert "ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC" in sql
    assert params == (2,)

    captured = capsys.readouterr()
    assert "strategy-audit-db-history:" in captured.out
    assert "reports=2" in captured.out
    assert "status=latest_blocked_by_risk" in captured.out
    assert "latest_status=blocked_by_risk" in captured.out
    assert "audit_ready=1" in captured.out
    assert "insufficient_evidence=0" in captured.out
    assert "blocked_by_risk=1" in captured.out
    assert "first=2026-06-21T07:00:00+00:00" in captured.out
    assert "latest=2026-06-21T09:00:00+00:00" in captured.out
    assert "consecutive_non_ready=1" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "strategy_risk_audit_archive" not in captured.out


def test_strategy_audit_db_history_cli_redacts_dsn_on_read_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://strategy-audit-db-history-secret.example.invalid/db"
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_DSN_ENV_VAR, dsn)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(f"could not connect to {dsn}")

    exit_code = main(
        ["strategy-audit-db-history"],
        strategy_audit_db_history_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "strategy-audit-db-history failed: could not connect to <redacted-dsn>"
    ) in captured.err
    assert dsn not in captured.out
    assert dsn not in captured.err


@pytest.mark.parametrize(
    "flag",
    (
        "--dsn",
        "--db-dsn",
        "--strategy-risk-audit-db-dsn",
    ),
)
def test_strategy_audit_db_history_cli_rejects_dsn_flags(
    capsys: pytest.CaptureFixture[str],
    flag: str,
) -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "strategy-audit-db-history",
                flag,
                "forbidden-value",
            ],
            client_factory=lambda: "fake-client",
        )

    captured = capsys.readouterr()
    assert f"unrecognized arguments: {flag}" in captured.err


def test_strategy_audit_db_history_cli_rejects_non_positive_limit(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://strategy-audit-db-history.example.invalid/db"
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_DSN_ENV_VAR, dsn)

    def forbidden_runner(**kwargs: Any) -> object:
        raise AssertionError("strategy-audit-db-history runner should not run")

    exit_code = main(
        [
            "strategy-audit-db-history",
            "--limit",
            "0",
        ],
        strategy_audit_db_history_runner=forbidden_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "strategy-audit-db-history failed: "
        "strategy-audit-db-history limit must be positive"
    ) in captured.err
    assert dsn not in captured.out
    assert dsn not in captured.err
