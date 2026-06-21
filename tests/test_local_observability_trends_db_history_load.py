from __future__ import annotations

import ast
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.local_observability_trends_db_history_load as db_history_load
from polymarket_alpha_lab.local_observability_trends import (
    LocalObservabilityTrendsReport,
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


GENERATED_AT = datetime(2026, 6, 21, 10, 0, tzinfo=UTC)
HISTORY_CONFIG_VERSION = "local-observability-trends-db-history-load-v0"
RATIO_ONE = Decimal("1.000000")
RATIO_ZERO = Decimal("0.000000")


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


def test_load_local_observability_trends_db_history_builds_from_store_desc_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = object()
    calls: list[tuple[Any, int | None, str]] = []

    def load_reports(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "local_observability_trends_reports",
    ) -> tuple[LocalObservabilityTrendsReport, ...]:
        calls.append((connection_arg, limit, table_name))
        return (
            _report(
                generated_at=datetime(2026, 6, 21, 9, 0, tzinfo=UTC),
                strategy_status="local_risk_flags",
                outcome_status="latest_outcomes_stale",
                nav_status="latest_nav_has_unexecutable_positions",
                cost_status="latest_negative_cost_adjusted_edges",
            ),
            _report(
                generated_at=datetime(2026, 6, 21, 8, 0, tzinfo=UTC),
                strategy_status="local_evidence_gaps",
            ),
            _report(
                generated_at=datetime(2026, 6, 21, 7, 0, tzinfo=UTC),
            ),
        )

    monkeypatch.setattr(
        db_history_load.local_observability_trends_store,
        "load_local_observability_trends_reports",
        load_reports,
    )

    history = db_history_load.load_local_observability_trends_db_history_report(
        generated_at=GENERATED_AT,
        config_version=HISTORY_CONFIG_VERSION,
        connection=connection,
        limit=25,
        table_name="local_observability_archive",
    )

    assert calls == [(connection, 25, "local_observability_archive")]
    assert history.generated_at == GENERATED_AT
    assert history.config_version == HISTORY_CONFIG_VERSION
    assert history.status == "latest_local_observability_trends_warning"
    assert history.report_count == 3
    assert history.first_report_generated_at == datetime(2026, 6, 21, 7, 0, tzinfo=UTC)
    assert history.latest_report_generated_at == datetime(2026, 6, 21, 9, 0, tzinfo=UTC)
    assert history.latest_strategy_evidence_status == "local_risk_flags"
    assert history.latest_outcome_status == "latest_outcomes_stale"
    assert history.latest_nav_status == "latest_nav_has_unexecutable_positions"
    assert history.latest_cost_status == "latest_negative_cost_adjusted_edges"
    assert history.consecutive_outcome_stale_count == 1
    assert history.consecutive_nav_warning_or_high_risk_count == 1
    assert history.consecutive_cost_warning_or_critical_count == 1


def test_load_local_observability_trends_db_history_reverses_store_desc_ties(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    same_generated_at = datetime(2026, 6, 21, 9, 0, tzinfo=UTC)

    def load_reports(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "local_observability_trends_reports",
    ) -> tuple[LocalObservabilityTrendsReport, ...]:
        return (
            _report(
                generated_at=same_generated_at,
                strategy_status="local_risk_flags",
            ),
            _report(
                generated_at=same_generated_at,
                strategy_status="local_evidence_observed",
            ),
        )

    monkeypatch.setattr(
        db_history_load.local_observability_trends_store,
        "load_local_observability_trends_reports",
        load_reports,
    )

    history = db_history_load.load_local_observability_trends_db_history_report(
        generated_at=GENERATED_AT,
        config_version=HISTORY_CONFIG_VERSION,
        connection=object(),
    )

    assert history.report_count == 2
    assert history.first_report_generated_at == same_generated_at
    assert history.latest_report_generated_at == same_generated_at
    assert history.latest_strategy_evidence_status == "local_risk_flags"
    assert history.status == "latest_local_observability_trends_warning"


def test_load_local_observability_trends_db_history_keeps_empty_history_readonly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def load_reports(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "local_observability_trends_reports",
    ) -> tuple[LocalObservabilityTrendsReport, ...]:
        return ()

    monkeypatch.setattr(
        db_history_load.local_observability_trends_store,
        "load_local_observability_trends_reports",
        load_reports,
    )

    history = db_history_load.load_local_observability_trends_db_history_report(
        generated_at=GENERATED_AT,
        config_version=HISTORY_CONFIG_VERSION,
        connection=object(),
    )

    assert history.status == "empty_local_observability_trends_db_history"
    assert history.report_count == 0
    assert history.first_report_generated_at is None
    assert history.latest_report_generated_at is None
    assert history.paper_only is True
    assert history.report_only is True
    assert history.readonly is True


@pytest.mark.parametrize(
    ("flag_name", "message"),
    (
        ("paper_only", "paper_only"),
        ("report_only", "report_only"),
        ("readonly", "readonly"),
    ),
)
def test_load_local_observability_trends_db_history_rejects_unsafe_loaded_flags(
    monkeypatch: pytest.MonkeyPatch,
    flag_name: str,
    message: str,
) -> None:
    def load_reports(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "local_observability_trends_reports",
    ) -> tuple[LocalObservabilityTrendsReport, ...]:
        report = replace(
            _report(generated_at=datetime(2026, 6, 21, 7, 0, tzinfo=UTC)),
        )
        object.__setattr__(report, flag_name, False)
        return (report,)

    monkeypatch.setattr(
        db_history_load.local_observability_trends_store,
        "load_local_observability_trends_reports",
        load_reports,
    )

    with pytest.raises(ValueError, match=message):
        db_history_load.load_local_observability_trends_db_history_report(
            generated_at=GENERATED_AT,
            config_version=HISTORY_CONFIG_VERSION,
            connection=object(),
        )


def test_local_observability_trends_db_history_load_module_has_no_live_driver_or_cli_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "local_observability_trends_db_history_load.py"
    )
    module = ast.parse(module_path.read_text())
    imported_roots: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "aiohttp",
        "argparse",
        "click",
        "eth_account",
        "httpx",
        "os",
        "psycopg",
        "requests",
        "socket",
        "sys",
        "urllib",
        "websocket",
        "websockets",
    }
