from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.outcome_freshness import (
    OutcomeFreshnessConfig,
    OutcomeFreshnessReport,
    build_outcome_freshness_report,
)
from polymarket_alpha_lab.outcome_tracker import OutcomeTrackingReport
from polymarket_alpha_lab.outcome_tracking_db_row import (
    outcome_tracking_report_to_db_row,
)
from polymarket_alpha_lab.supabase_outcome_tracking_config import (
    OUTCOME_TRACKING_DB_DSN_ENV_VAR,
    OUTCOME_TRACKING_DB_ENABLED_ENV_VAR,
    OUTCOME_TRACKING_DB_TABLE_ENV_VAR,
)


GENERATED_AT = datetime(2026, 6, 21, 10, 0, tzinfo=UTC)
CONFIG_VERSION = "outcome-tracking-db-history-v0"


def _observation(
    generated_at: datetime,
    suffix: str,
) -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=generated_at,
        source_packet_id=f"packet-{suffix}",
        condition_id=f"condition-{suffix}",
        token_id=f"token-{suffix}",
        market_slug=f"market-{suffix}",
        strategy_type="market_quality",
        risk_tags=("liquidity",),
        predicted_probability=Decimal("1.000000"),
        actual_outcome_value=Decimal("1.000000"),
    )


def _tracking_report(
    *,
    generated_at: datetime,
    resolved_count: int,
    pending_count: int,
    suffix: str,
) -> OutcomeTrackingReport:
    observations = tuple(
        _observation(generated_at, f"{suffix}-{index}")
        for index in range(resolved_count)
    )
    evidence = (
        None
        if not observations
        else build_paper_forecast_evidence_report(
            observations,
            config=PaperForecastEvidenceConfig(config_version="outcome-tracker-v1"),
            generated_at=generated_at,
        )
    )
    return OutcomeTrackingReport(
        generated_at=generated_at,
        config_version="outcome-tracker-v1",
        total_markets_checked=resolved_count + pending_count,
        resolved_count=resolved_count,
        pending_count=pending_count,
        observations=observations,
        forecast_evidence_report=evidence,
    )


def _freshness_report() -> OutcomeFreshnessReport:
    reports = (
        _tracking_report(
            generated_at=datetime(2026, 6, 21, 8, 0, tzinfo=UTC),
            resolved_count=0,
            pending_count=1,
            suffix="early",
        ),
        _tracking_report(
            generated_at=datetime(2026, 6, 21, 9, 0, tzinfo=UTC),
            resolved_count=2,
            pending_count=0,
            suffix="latest",
        ),
    )
    return build_outcome_freshness_report(
        reports,
        config=OutcomeFreshnessConfig(
            config_version=CONFIG_VERSION,
            stale_after_seconds=3_601,
        ),
        generated_at=GENERATED_AT,
    )


def _source_record(report: OutcomeTrackingReport) -> tuple[object, ...]:
    row = outcome_tracking_report_to_db_row(report)
    return (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.total_markets_checked,
        row.resolved_count,
        row.pending_count,
        row.observation_count,
        row.forecast_evidence_status,
        row.payload_json,
        row.paper_only,
    )


def test_outcome_tracking_db_history_cli_requires_enabled_db_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(OUTCOME_TRACKING_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(OUTCOME_TRACKING_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(OUTCOME_TRACKING_DB_TABLE_ENV_VAR, raising=False)
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("outcome-tracking-db-history runner should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        ["outcome-tracking-db-history"],
        outcome_tracking_db_history_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert "outcome-tracking-db-history failed:" in captured.err
    assert (
        "outcome-tracking-db-history requires outcome tracking DB to be enabled"
    ) in captured.err


def test_outcome_tracking_db_history_cli_uses_injected_runner_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://outcome-tracking-db-history.example.invalid/db"
    monkeypatch.setenv(OUTCOME_TRACKING_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(OUTCOME_TRACKING_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(OUTCOME_TRACKING_DB_TABLE_ENV_VAR, "outcome_tracking_archive")
    calls: list[dict[str, object]] = []

    def fake_runner(**kwargs: Any) -> OutcomeFreshnessReport:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == "outcome_tracking_archive"
        assert kwargs["limit"] == 25
        assert kwargs["stale_after_seconds"] == 3_601
        assert kwargs["config_version"] == CONFIG_VERSION
        assert isinstance(kwargs["generated_at"], datetime)
        return _freshness_report()

    exit_code = main(
        [
            "outcome-tracking-db-history",
            "--limit",
            "25",
            "--stale-after-seconds",
            "3601",
        ],
        outcome_tracking_db_history_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert "outcome-tracking-db-history:" in captured.out
    assert "status=latest_outcomes_fresh" in captured.out
    assert "report_count=2" in captured.out
    assert "first_report_generated_at=2026-06-21T08:00:00+00:00" in captured.out
    assert "latest_report_generated_at=2026-06-21T09:00:00+00:00" in captured.out
    assert "latest_total_markets_checked=2" in captured.out
    assert "latest_resolved_count=2" in captured.out
    assert "latest_pending_count=0" in captured.out
    assert "latest_report_age_seconds=3600" in captured.out
    assert "consecutive_pending_count=0" in captured.out
    assert "status_rows:" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "outcome_tracking_archive" not in captured.out


def test_outcome_tracking_db_history_cli_default_load_path_no_network(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://outcome-tracking-db-history.example.invalid/db"
    monkeypatch.setenv(OUTCOME_TRACKING_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(OUTCOME_TRACKING_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(OUTCOME_TRACKING_DB_TABLE_ENV_VAR, "outcome_tracking_archive")
    rows = (
        _source_record(
            _tracking_report(
                generated_at=datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
                resolved_count=2,
                pending_count=0,
                suffix="latest",
            ),
        ),
        _source_record(
            _tracking_report(
                generated_at=datetime(2026, 6, 20, 8, 0, tzinfo=UTC),
                resolved_count=0,
                pending_count=1,
                suffix="early",
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
            "outcome-tracking-db-history",
            "--limit",
            "2",
            "--stale-after-seconds",
            "7200",
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
    assert "FROM outcome_tracking_archive" in sql
    assert "ORDER BY generated_at DESC, report_sha256 DESC" in sql
    assert params == (2,)
    captured = capsys.readouterr()
    assert "outcome-tracking-db-history:" in captured.out
    assert "report_count=2" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "outcome_tracking_archive" not in captured.out


def test_outcome_tracking_db_history_cli_redacts_dsn_on_read_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://outcome-tracking-db-history-secret.example.invalid/db"
    monkeypatch.setenv(OUTCOME_TRACKING_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(OUTCOME_TRACKING_DB_DSN_ENV_VAR, dsn)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(f"could not connect to {dsn}")

    exit_code = main(
        ["outcome-tracking-db-history"],
        outcome_tracking_db_history_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "outcome-tracking-db-history failed: could not connect to <redacted-dsn>"
    ) in captured.err
    assert dsn not in captured.out
    assert dsn not in captured.err


@pytest.mark.parametrize("flag", ("--dsn", "--db-dsn", "--outcome-tracking-db-dsn"))
def test_outcome_tracking_db_history_cli_rejects_dsn_flags(
    capsys: pytest.CaptureFixture[str],
    flag: str,
) -> None:
    with pytest.raises(SystemExit):
        main(["outcome-tracking-db-history", flag, "forbidden-value"])

    captured = capsys.readouterr()
    assert f"unrecognized arguments: {flag}" in captured.err


def test_outcome_tracking_db_history_cli_rejects_non_positive_limit(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://outcome-tracking-db-history.example.invalid/db"
    monkeypatch.setenv(OUTCOME_TRACKING_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(OUTCOME_TRACKING_DB_DSN_ENV_VAR, dsn)

    exit_code = main(
        [
            "outcome-tracking-db-history",
            "--limit",
            "0",
        ],
        outcome_tracking_db_history_runner=lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("runner should not run"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "outcome-tracking-db-history failed: "
        "outcome-tracking-db-history limit must be positive"
    ) in captured.err
    assert dsn not in captured.out
    assert dsn not in captured.err
