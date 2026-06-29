from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.local_observability_trends import (
    LocalObservabilityTrendsReport,
)
from polymarket_alpha_lab.local_observability_trends_db_history import (
    LocalObservabilityTrendsDbHistoryConfig,
    LocalObservabilityTrendsDbHistoryReport,
    build_local_observability_trends_db_history_report,
)
from polymarket_alpha_lab.local_observability_trends_db_row import (
    local_observability_trends_report_to_db_row,
)
from polymarket_alpha_lab.nav_risk_trend import (
    NAV_RISK_TREND_STATUSES,
    PaperNavRiskTrendReport,
    PaperNavRiskTrendStatusRow,
)
from polymarket_alpha_lab.outcome_freshness import (
    OUTCOME_FRESHNESS_STATUSES,
    OutcomeFreshnessReport,
    OutcomeFreshnessStatusRow,
)
from polymarket_alpha_lab.paper_trade_cost_trend import (
    COST_TREND_STATUSES,
    PaperTradeCostTrendReport,
    PaperTradeCostTrendStatusRow,
)
from polymarket_alpha_lab.strategy_evidence import (
    EVIDENCE_GAP_NAMES,
    SNAPSHOT_STATUSES,
)
from polymarket_alpha_lab.strategy_evidence_trend import (
    PaperStrategyEvidenceTrendGapRow,
    PaperStrategyEvidenceTrendReport,
    PaperStrategyEvidenceTrendStatusRow,
)
from polymarket_alpha_lab.supabase_local_observability_trends_config import (
    LOCAL_OBSERVABILITY_TRENDS_DB_DSN_ENV_VAR,
    LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED_ENV_VAR,
    LOCAL_OBSERVABILITY_TRENDS_DB_TABLE_ENV_VAR,
)


GENERATED_AT = datetime(2026, 6, 21, 10, 0, tzinfo=UTC)
HISTORY_CONFIG_VERSION = "local-observability-trends-db-history-v0"
RATIO_ONE = Decimal("1.000000")
RATIO_ZERO = Decimal("0.000000")


def _config() -> LocalObservabilityTrendsDbHistoryConfig:
    return LocalObservabilityTrendsDbHistoryConfig(
        config_version=HISTORY_CONFIG_VERSION,
    )


def _history(
    reports: list[LocalObservabilityTrendsReport]
    | tuple[LocalObservabilityTrendsReport, ...],
) -> LocalObservabilityTrendsDbHistoryReport:
    return build_local_observability_trends_db_history_report(
        reports,
        config=_config(),
        generated_at=GENERATED_AT,
    )


def _ratio_row_count(total: int, count: int) -> Decimal | None:
    if total == 0:
        return None
    return (Decimal(count) / Decimal(total)).quantize(Decimal("0.000001"))


def _strategy_trend(
    status: str | None,
    *,
    generated_at: datetime,
) -> PaperStrategyEvidenceTrendReport:
    snapshot_count = 0 if status is None else 1
    latest_gap_names: tuple[str, ...] = ()
    local_risk_count = 0
    non_observed_count = 0
    if status == "local_evidence_gaps":
        latest_gap_names = ("missing_outcome_evidence",)
        non_observed_count = 1
    elif status == "local_risk_flags":
        latest_gap_names = ("negative_cost_adjusted_edges",)
        local_risk_count = 1
        non_observed_count = 1
    elif status == "no_local_evidence":
        non_observed_count = 1

    status_counts = {
        item: 1 if item == status else 0 for item in SNAPSHOT_STATUSES
    }
    gap_counts = {
        gap_name: 1 if gap_name in latest_gap_names else 0
        for gap_name in EVIDENCE_GAP_NAMES
    }
    return PaperStrategyEvidenceTrendReport(
        generated_at=generated_at,
        config_version="strategy-evidence-trend-v0",
        snapshot_report_count=snapshot_count,
        first_report_generated_at=generated_at if snapshot_count else None,
        latest_report_generated_at=generated_at if snapshot_count else None,
        latest_status=status,
        latest_evidence_gap_names=latest_gap_names,
        consecutive_local_risk_flags_count=local_risk_count,
        consecutive_non_observed_count=non_observed_count,
        status_rows=tuple(
            PaperStrategyEvidenceTrendStatusRow(
                snapshot_status=item,
                snapshot_count=status_counts[item],
                snapshot_ratio=_ratio_row_count(snapshot_count, status_counts[item]),
            )
            for item in SNAPSHOT_STATUSES
        ),
        gap_rows=tuple(
            PaperStrategyEvidenceTrendGapRow(
                evidence_gap_name=gap_name,
                gap_count=gap_counts[gap_name],
                gap_ratio=_ratio_row_count(snapshot_count, gap_counts[gap_name]),
            )
            for gap_name in EVIDENCE_GAP_NAMES
        ),
    )


def _outcome_freshness(
    status: str,
    *,
    generated_at: datetime,
) -> OutcomeFreshnessReport:
    report_count = 0 if status == "empty_outcome_history" else 1
    latest_total = 1 if status == "latest_outcomes_pending" else 0
    latest_pending = 1 if status == "latest_outcomes_pending" else 0
    latest_age = 7_200 if status == "latest_outcomes_stale" else 60
    status_counts = {
        item: 1 if item == status and report_count else 0
        for item in OUTCOME_FRESHNESS_STATUSES
    }
    return OutcomeFreshnessReport(
        generated_at=generated_at,
        config_version="outcome-freshness-v0",
        outcome_report_count=report_count,
        first_report_generated_at=generated_at if report_count else None,
        latest_report_generated_at=generated_at if report_count else None,
        latest_total_markets_checked=latest_total,
        latest_resolved_count=0,
        latest_pending_count=latest_pending,
        latest_resolved_ratio=RATIO_ZERO if latest_total else None,
        latest_pending_ratio=RATIO_ONE if latest_total else None,
        latest_report_age_seconds=latest_age if report_count else None,
        consecutive_pending_count=1 if latest_pending else 0,
        status=status,
        status_rows=tuple(
            OutcomeFreshnessStatusRow(
                status=item,
                outcome_report_count=status_counts[item],
                outcome_report_ratio=_ratio_row_count(
                    report_count,
                    status_counts[item],
                ),
            )
            for item in OUTCOME_FRESHNESS_STATUSES
        ),
    )


def _nav_trend(
    status: str,
    *,
    generated_at: datetime,
) -> PaperNavRiskTrendReport:
    report_count = 0 if status == "empty_nav_risk_history" else 1
    status_counts = {
        item: 1 if item == status and report_count else 0
        for item in NAV_RISK_TREND_STATUSES
    }
    has_unexecutable_positions = status == "latest_nav_has_unexecutable_positions"
    open_positions = 1 if has_unexecutable_positions else 0
    return PaperNavRiskTrendReport(
        generated_at=generated_at,
        config_version="nav-risk-trend-v0",
        nav_risk_report_count=report_count,
        first_report_generated_at=generated_at if report_count else None,
        latest_report_generated_at=generated_at if report_count else None,
        latest_exit_nav=Decimal("100.0000") if report_count else None,
        latest_cumulative_return=Decimal("0.000000") if report_count else None,
        latest_max_drawdown=Decimal("0.0000") if report_count else None,
        latest_max_drawdown_pct=Decimal("0.000000") if report_count else None,
        latest_nav_return_volatility=None,
        latest_open_position_count=open_positions,
        latest_fully_executable_count=0,
        latest_partially_executable_count=0,
        latest_no_exit_depth_count=open_positions,
        latest_largest_market_exposure_value=(
            Decimal("25.0000") if open_positions else None
        ),
        latest_largest_market_exposure_share=(
            Decimal("0.250000") if open_positions else None
        ),
        worst_observed_max_drawdown_pct=(
            Decimal("0.000000") if report_count else None
        ),
        consecutive_unexecutable_open_position_count=(
            1 if has_unexecutable_positions else 0
        ),
        status=status,
        status_rows=tuple(
            PaperNavRiskTrendStatusRow(
                status=item,
                report_count=status_counts[item],
                report_ratio=_ratio_row_count(report_count, status_counts[item]),
            )
            for item in NAV_RISK_TREND_STATUSES
        ),
    )


def _cost_trend(
    status: str,
    *,
    generated_at: datetime,
) -> PaperTradeCostTrendReport:
    report_count = 0 if status == "empty_cost_audit_history" else 1
    has_negative_edge = status == "latest_negative_cost_adjusted_edges"
    status_counts = {
        item: 1 if item == status and report_count else 0
        for item in COST_TREND_STATUSES
    }
    return PaperTradeCostTrendReport(
        generated_at=generated_at,
        config_version="paper-trade-cost-trend-v0",
        cost_audit_report_count=report_count,
        first_report_generated_at=generated_at if report_count else None,
        latest_report_generated_at=generated_at if report_count else None,
        latest_trade_count=1 if report_count else 0,
        latest_fill_rate=RATIO_ONE if report_count else None,
        latest_mean_theoretical_edge=Decimal("0.050000") if report_count else None,
        latest_mean_cost_adjusted_edge=(
            Decimal("-0.010000") if has_negative_edge else Decimal("0.040000")
        )
        if report_count
        else None,
        latest_mean_edge_cost_drag=Decimal("0.010000") if report_count else None,
        latest_total_edge_cost_drag=Decimal("0.010000") if report_count else None,
        latest_partial_fill_count=0,
        latest_negative_cost_adjusted_edge_count=1 if has_negative_edge else 0,
        worst_observed_mean_edge_cost_drag=(
            Decimal("0.010000") if report_count else None
        ),
        worst_observed_negative_cost_adjusted_edge_count=(
            1 if has_negative_edge else 0
        ),
        consecutive_negative_cost_adjusted_edge_count=(
            1 if has_negative_edge else 0
        ),
        status=status,
        status_rows=tuple(
            PaperTradeCostTrendStatusRow(
                status=item,
                status_count=status_counts[item],
                status_ratio=_ratio_row_count(report_count, status_counts[item]),
            )
            for item in COST_TREND_STATUSES
        ),
    )


def _report(
    *,
    generated_at: datetime,
    strategy_status: str | None = "local_evidence_observed",
    outcome_status: str = "latest_outcomes_fresh",
    nav_status: str = "latest_nav_risk_observed",
    cost_status: str = "latest_cost_observed",
) -> LocalObservabilityTrendsReport:
    return LocalObservabilityTrendsReport(
        generated_at=generated_at,
        config_version="local-observability-trends-v0",
        strategy_evidence_trend=_strategy_trend(
            strategy_status,
            generated_at=generated_at,
        ),
        outcome_freshness=_outcome_freshness(
            outcome_status,
            generated_at=generated_at,
        ),
        nav_risk_trend=_nav_trend(nav_status, generated_at=generated_at),
        paper_trade_cost_trend=_cost_trend(cost_status, generated_at=generated_at),
    )


def _history_report() -> LocalObservabilityTrendsDbHistoryReport:
    return _history(
        (
            _report(generated_at=datetime(2026, 6, 21, 7, 0, tzinfo=UTC)),
            _report(
                generated_at=datetime(2026, 6, 21, 8, 0, tzinfo=UTC),
                strategy_status="local_evidence_gaps",
            ),
            _report(
                generated_at=datetime(2026, 6, 21, 9, 0, tzinfo=UTC),
                strategy_status="local_risk_flags",
                outcome_status="latest_outcomes_stale",
                nav_status="latest_nav_has_unexecutable_positions",
                cost_status="latest_negative_cost_adjusted_edges",
            ),
        ),
    )


def _source_record(report: LocalObservabilityTrendsReport) -> tuple[object, ...]:
    row = local_observability_trends_report_to_db_row(report)
    return (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.strategy_evidence_snapshot_count,
        row.strategy_evidence_latest_status,
        row.outcome_freshness_status,
        row.outcome_report_count,
        row.nav_risk_status,
        row.nav_risk_report_count,
        row.paper_trade_cost_status,
        row.paper_trade_cost_report_count,
        row.payload_json,
        row.paper_only,
        row.report_only,
        row.readonly,
    )


def test_local_observability_trends_db_history_cli_requires_enabled_db_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(LOCAL_OBSERVABILITY_TRENDS_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(LOCAL_OBSERVABILITY_TRENDS_DB_TABLE_ENV_VAR, raising=False)
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("db history runner should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        ["local-observability-trends-db-history"],
        local_observability_trends_db_history_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert "local-observability-trends-db-history failed:" in captured.err
    assert (
        "local-observability-trends-db-history requires local observability "
        "trends DB to be enabled"
    ) in captured.err


def test_local_observability_trends_db_history_cli_uses_injected_runner_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://local-observability-history@localhost/db"
    monkeypatch.setenv(LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(LOCAL_OBSERVABILITY_TRENDS_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        LOCAL_OBSERVABILITY_TRENDS_DB_TABLE_ENV_VAR,
        "local_observability_trends_archive",
    )
    calls: list[dict[str, object]] = []
    history_report = _history_report()

    def fake_runner(**kwargs: Any) -> LocalObservabilityTrendsDbHistoryReport:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == "local_observability_trends_archive"
        assert kwargs["limit"] == 25
        assert isinstance(kwargs["generated_at"], datetime)
        if "config" in kwargs:
            assert kwargs["config"] == _config()
        else:
            assert kwargs["config_version"] == HISTORY_CONFIG_VERSION
        return history_report

    exit_code = main(
        [
            "local-observability-trends-db-history",
            "--limit",
            "25",
        ],
        local_observability_trends_db_history_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert "local-observability-trends-db-history:" in captured.out
    assert "status=latest_local_observability_trends_warning" in captured.out
    assert "report_count=3" in captured.out
    assert "first_report_generated_at=2026-06-21T07:00:00+00:00" in captured.out
    assert "latest_report_generated_at=2026-06-21T09:00:00+00:00" in captured.out
    assert "latest_strategy_evidence_status=local_risk_flags" in captured.out
    assert "latest_outcome_status=latest_outcomes_stale" in captured.out
    assert "latest_nav_status=latest_nav_has_unexecutable_positions" in captured.out
    assert "latest_cost_status=latest_negative_cost_adjusted_edges" in captured.out
    assert "duplicate_generated_at_count=0" in captured.out
    assert "consecutive_outcome_stale_count=1" in captured.out
    assert "consecutive_nav_warning_or_high_risk_count=1" in captured.out
    assert "consecutive_cost_warning_or_critical_count=1" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "local_observability_trends_archive" not in captured.out


def test_local_observability_trends_db_history_cli_default_load_path_no_network(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://local-observability-history@localhost/db"
    monkeypatch.setenv(LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(LOCAL_OBSERVABILITY_TRENDS_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        LOCAL_OBSERVABILITY_TRENDS_DB_TABLE_ENV_VAR,
        "local_observability_trends_archive",
    )
    rows = (
        _source_record(
            _report(
                generated_at=datetime(2026, 6, 21, 9, 0, tzinfo=UTC),
                strategy_status="local_risk_flags",
                outcome_status="latest_outcomes_stale",
                nav_status="latest_nav_has_unexecutable_positions",
                cost_status="latest_negative_cost_adjusted_edges",
            ),
        ),
        _source_record(
            _report(generated_at=datetime(2026, 6, 21, 8, 0, tzinfo=UTC)),
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
        if connect_dsn != dsn:
            raise AssertionError(f"unexpected dsn: {connect_dsn}")
        return connection

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    sys.modules.pop("polymarket_alpha_lab.local_observability_trends_psycopg", None)

    exit_code = main(
        [
            "local-observability-trends-db-history",
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
    assert "FROM local_observability_trends_archive" in sql
    assert "ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC" in sql
    assert params == (2,)

    captured = capsys.readouterr()
    assert "local-observability-trends-db-history:" in captured.out
    assert "status=latest_local_observability_trends_warning" in captured.out
    assert "report_count=2" in captured.out
    assert "latest_strategy_evidence_status=local_risk_flags" in captured.out
    assert "latest_outcome_status=latest_outcomes_stale" in captured.out
    assert "latest_nav_status=latest_nav_has_unexecutable_positions" in captured.out
    assert "latest_cost_status=latest_negative_cost_adjusted_edges" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "local_observability_trends_archive" not in captured.out


def test_local_observability_trends_db_history_cli_redacts_dsn_on_read_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://local-observability-history@localhost/db"
    monkeypatch.setenv(LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(LOCAL_OBSERVABILITY_TRENDS_DB_DSN_ENV_VAR, dsn)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(f"could not connect to {dsn}")

    exit_code = main(
        ["local-observability-trends-db-history"],
        local_observability_trends_db_history_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "local-observability-trends-db-history failed: "
        "could not connect to <redacted-dsn>"
    ) in captured.err
    assert dsn not in captured.out
    assert dsn not in captured.err


@pytest.mark.parametrize(
    "flag",
    (
        "--dsn",
        "--db-dsn",
        "--local-observability-trends-db-dsn",
    ),
)
def test_local_observability_trends_db_history_cli_rejects_dsn_flags(
    capsys: pytest.CaptureFixture[str],
    flag: str,
) -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "local-observability-trends-db-history",
                flag,
                "forbidden-value",
            ],
            client_factory=lambda: "fake-client",
        )

    captured = capsys.readouterr()
    assert f"unrecognized arguments: {flag}" in captured.err


def test_local_observability_trends_db_history_cli_rejects_non_positive_limit(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://local-observability-history@localhost/db"
    monkeypatch.setenv(LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(LOCAL_OBSERVABILITY_TRENDS_DB_DSN_ENV_VAR, dsn)

    def forbidden_runner(**kwargs: Any) -> object:
        raise AssertionError("db history runner should not run")

    exit_code = main(
        [
            "local-observability-trends-db-history",
            "--limit",
            "0",
        ],
        local_observability_trends_db_history_runner=forbidden_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "local-observability-trends-db-history failed: "
        "local-observability-trends-db-history limit must be positive"
    ) in captured.err
    assert dsn not in captured.out
    assert dsn not in captured.err
