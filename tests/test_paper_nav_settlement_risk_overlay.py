import ast
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 6, 25, 9, 0, tzinfo=UTC)
MARKED_AT = datetime(2026, 6, 25, 8, 55, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 6, 25, 8, 0, tzinfo=UTC)
RESOLUTION_AT = datetime(2026, 6, 26, 8, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
STATUS_PRIORITY = {"acceptable": 0, "watch": 1, "blocked": 2}


def _imports():
    from polymarket_alpha_lab.nav_risk_metrics import (
        PaperNavRiskExposureRow,
        PaperNavRiskMetricsReport,
    )
    from polymarket_alpha_lab.paper_nav_settlement_risk_overlay import (
        PaperNavSettlementRiskOverlayConfig,
        PaperNavSettlementRiskOverlayReport,
        PaperNavSettlementRiskOverlayRow,
        build_paper_nav_settlement_risk_overlay_report,
    )
    from polymarket_alpha_lab.paper_settlement_timing import (
        PaperSettlementTimingReport,
        PaperSettlementTimingRow,
    )

    return {
        "PaperNavRiskExposureRow": PaperNavRiskExposureRow,
        "PaperNavRiskMetricsReport": PaperNavRiskMetricsReport,
        "PaperNavSettlementRiskOverlayConfig": PaperNavSettlementRiskOverlayConfig,
        "PaperNavSettlementRiskOverlayReport": PaperNavSettlementRiskOverlayReport,
        "PaperNavSettlementRiskOverlayRow": PaperNavSettlementRiskOverlayRow,
        "build_paper_nav_settlement_risk_overlay_report": (
            build_paper_nav_settlement_risk_overlay_report
        ),
        "PaperSettlementTimingReport": PaperSettlementTimingReport,
        "PaperSettlementTimingRow": PaperSettlementTimingRow,
    }


def _config(**overrides):
    values = {
        "config_version": "paper-nav-settlement-risk-overlay-v0",
        "max_blocked_settlement_exposure_share": Decimal("0.100000"),
    }
    values.update(overrides)
    return _imports()["PaperNavSettlementRiskOverlayConfig"](**values)


def _exposure(
    *,
    condition_id: str,
    market_slug: str,
    token_count: int = 1,
    open_size: Decimal,
    cost_basis: Decimal,
    exit_value: Decimal,
    share_of_exit_nav: Decimal,
):
    return _imports()["PaperNavRiskExposureRow"](
        condition_id=condition_id,
        market_slug=market_slug,
        token_count=token_count,
        open_size=open_size,
        cost_basis=cost_basis,
        exit_value=exit_value,
        share_of_exit_nav=share_of_exit_nav,
    )


def _nav_report(*exposure_rows):
    latest_exit_nav = Decimal("1000.0000")
    total_exit_value = sum((row.exit_value for row in exposure_rows), Decimal("0"))
    total_cost_basis = sum((row.cost_basis for row in exposure_rows), Decimal("0"))
    latest_cash_balance = latest_exit_nav - total_exit_value
    latest_unrealized_exit_pnl = total_exit_value - total_cost_basis
    largest = max(exposure_rows, key=lambda row: row.exit_value, default=None)
    open_position_count = sum(row.token_count for row in exposure_rows)

    return _imports()["PaperNavRiskMetricsReport"](
        generated_at=GENERATED_AT,
        config_version="nav-risk-metrics-v0",
        nav_snapshot_count=1,
        first_marked_at=MARKED_AT,
        last_marked_at=MARKED_AT,
        latest_exit_nav=latest_exit_nav,
        latest_starting_cash=latest_cash_balance + total_cost_basis,
        latest_cash_balance=latest_cash_balance,
        latest_total_cost_basis=total_cost_basis,
        latest_unrealized_exit_pnl=latest_unrealized_exit_pnl,
        peak_exit_nav=latest_exit_nav,
        trough_exit_nav=latest_exit_nav,
        cumulative_return=ZERO,
        max_drawdown=Decimal("0.0000"),
        max_drawdown_pct=ZERO,
        worst_nav_delta=None,
        nav_return_volatility=None,
        pending_notional=total_cost_basis,
        open_position_count=open_position_count,
        fully_executable_count=open_position_count,
        partially_executable_count=0,
        no_exit_depth_count=0,
        largest_market_exposure_value=None if largest is None else largest.exit_value,
        largest_market_exposure_share=None if largest is None else largest.share_of_exit_nav,
        exposure_rows=exposure_rows,
    )


def _timing_row(
    *,
    market_slug: str,
    timing_status: str = "acceptable",
    adjusted_net_probability_edge: Decimal = Decimal("0.080000"),
):
    if timing_status == "acceptable":
        settlement_context_fresh = True
        timing_cost_per_share = ZERO
        expected_resolution_at = RESOLUTION_AT
        reason_codes = ("source_edge",)
    elif timing_status == "watch":
        settlement_context_fresh = False
        timing_cost_per_share = Decimal("0.020000")
        expected_resolution_at = RESOLUTION_AT
        reason_codes = ("settlement_context_stale", "source_edge")
    else:
        settlement_context_fresh = True
        timing_cost_per_share = Decimal("0.050000")
        expected_resolution_at = None
        reason_codes = ("source_edge", "unknown_resolution")

    return _imports()["PaperSettlementTimingRow"](
        market_slug=market_slug,
        side="yes",
        action="recommend",
        net_probability_edge=adjusted_net_probability_edge + timing_cost_per_share,
        expected_resolution_at=expected_resolution_at,
        settlement_context_fresh=settlement_context_fresh,
        observed_at=OBSERVED_AT,
        days_to_resolution=(
            Decimal("1.000000") if expected_resolution_at is not None else None
        ),
        timing_status=timing_status,
        timing_cost_per_share=timing_cost_per_share,
        adjusted_net_probability_edge=adjusted_net_probability_edge,
        reason_codes=reason_codes,
    )


def _settlement_report(*rows):
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.adjusted_net_probability_edge,
                STATUS_PRIORITY[row.timing_status],
                row.market_slug,
                row.side,
            ),
        )
    )
    return _imports()["PaperSettlementTimingReport"](
        generated_at=GENERATED_AT,
        config_version="paper-settlement-timing-v0",
        input_count=len(rows),
        row_count=len(rows),
        acceptable_count=sum(1 for row in rows if row.timing_status == "acceptable"),
        watch_count=sum(1 for row in rows if row.timing_status == "watch"),
        blocked_count=sum(1 for row in rows if row.timing_status == "blocked"),
        rows=sorted_rows,
    )


def _build_overlay(nav_report, settlement_report, **config_overrides):
    return _imports()["build_paper_nav_settlement_risk_overlay_report"](
        nav_risk_report=nav_report,
        settlement_timing_report=settlement_report,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def test_overlay_projects_settlement_status_onto_nav_exposure_without_side_effects():
    nav_report = _nav_report(
        _exposure(
            condition_id="condition-a",
            market_slug="market-a",
            open_size=Decimal("120.0000"),
            cost_basis=Decimal("80.0000"),
            exit_value=Decimal("100.0000"),
            share_of_exit_nav=Decimal("0.100000"),
        ),
        _exposure(
            condition_id="condition-b",
            market_slug="market-b",
            open_size=Decimal("70.0000"),
            cost_basis=Decimal("40.0000"),
            exit_value=Decimal("50.0000"),
            share_of_exit_nav=Decimal("0.050000"),
        ),
        _exposure(
            condition_id="condition-c",
            market_slug="market-c",
            open_size=Decimal("40.0000"),
            cost_basis=Decimal("30.0000"),
            exit_value=Decimal("25.0000"),
            share_of_exit_nav=Decimal("0.025000"),
        ),
    )
    settlement_report = _settlement_report(
        _timing_row(market_slug="market-a", timing_status="acceptable"),
        _timing_row(market_slug="market-b", timing_status="watch"),
        _timing_row(market_slug="market-c", timing_status="blocked"),
    )

    report = _build_overlay(nav_report, settlement_report)

    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-nav-settlement-risk-overlay-v0"
    assert report.nav_risk_config_version == "nav-risk-metrics-v0"
    assert report.settlement_timing_config_version == "paper-settlement-timing-v0"
    assert report.nav_snapshot_count == 1
    assert report.settlement_row_count == 3
    assert report.exposure_row_count == 3
    assert report.acceptable_count == 1
    assert report.watch_count == 1
    assert report.blocked_count == 1
    assert report.missing_settlement_count == 0
    assert report.acceptable_exit_value == Decimal("100.0000")
    assert report.watch_exit_value == Decimal("50.0000")
    assert report.blocked_exit_value == Decimal("25.0000")
    assert report.missing_settlement_exit_value == Decimal("0")
    assert report.blocked_or_missing_exit_value == Decimal("25.0000")
    assert report.blocked_or_missing_exit_nav_share == Decimal("0.025000")
    assert report.max_blocked_settlement_exposure_share == Decimal("0.100000")
    assert report.status == "settlement_nav_risk_watch"

    assert tuple(row.market_slug for row in report.rows) == (
        "market-c",
        "market-b",
        "market-a",
    )
    blocked, watched, acceptable = report.rows
    assert blocked.overlay_status == "blocked"
    assert blocked.settlement_timing_status == "blocked"
    assert blocked.reason_codes == ("source_edge", "unknown_resolution")
    assert watched.overlay_status == "watch"
    assert watched.timing_cost_per_share == Decimal("0.020000")
    assert watched.adjusted_net_probability_edge == Decimal("0.080000")
    assert acceptable.overlay_status == "acceptable"


def test_overlay_blocks_missing_settlement_timing_for_open_nav_exposure():
    nav_report = _nav_report(
        _exposure(
            condition_id="condition-known",
            market_slug="known-market",
            open_size=Decimal("100.0000"),
            cost_basis=Decimal("70.0000"),
            exit_value=Decimal("80.0000"),
            share_of_exit_nav=Decimal("0.080000"),
        ),
        _exposure(
            condition_id="condition-missing",
            market_slug="missing-market",
            open_size=Decimal("50.0000"),
            cost_basis=Decimal("30.0000"),
            exit_value=Decimal("40.0000"),
            share_of_exit_nav=Decimal("0.040000"),
        ),
    )

    report = _build_overlay(
        nav_report,
        _settlement_report(_timing_row(market_slug="known-market")),
    )

    assert report.status == "settlement_nav_risk_blocked"
    assert report.missing_settlement_count == 1
    assert report.missing_settlement_exit_value == Decimal("40.0000")
    assert report.blocked_or_missing_exit_nav_share == Decimal("0.040000")
    missing_row = next(row for row in report.rows if row.market_slug == "missing-market")
    assert missing_row.overlay_status == "blocked"
    assert missing_row.settlement_timing_status is None
    assert missing_row.timing_cost_per_share is None
    assert missing_row.adjusted_net_probability_edge is None
    assert missing_row.reason_codes == ("missing_settlement_timing",)


def test_overlay_characterizes_missing_timing_row_as_blocked_with_missing_totals():
    nav_report = _nav_report(
        _exposure(
            condition_id="condition-known",
            market_slug="known-market",
            open_size=Decimal("100.0000"),
            cost_basis=Decimal("70.0000"),
            exit_value=Decimal("80.0000"),
            share_of_exit_nav=Decimal("0.080000"),
        ),
        _exposure(
            condition_id="condition-missing-a",
            market_slug="missing-a",
            open_size=Decimal("75.0000"),
            cost_basis=Decimal("55.0000"),
            exit_value=Decimal("60.0000"),
            share_of_exit_nav=Decimal("0.060000"),
        ),
        _exposure(
            condition_id="condition-missing-b",
            market_slug="missing-b",
            open_size=Decimal("45.0000"),
            cost_basis=Decimal("30.0000"),
            exit_value=Decimal("35.0000"),
            share_of_exit_nav=Decimal("0.035000"),
        ),
    )

    report = _build_overlay(
        nav_report,
        _settlement_report(_timing_row(market_slug="known-market")),
    )

    assert report.status == "settlement_nav_risk_blocked"
    assert report.acceptable_count == 1
    assert report.watch_count == 0
    assert report.blocked_count == 2
    assert report.missing_settlement_count == 2
    assert report.blocked_exit_value == Decimal("0")
    assert report.missing_settlement_exit_value == Decimal("95.0000")
    assert report.blocked_or_missing_exit_value == Decimal("95.0000")
    assert report.blocked_or_missing_exit_nav_share == Decimal("0.095000")
    missing_rows = tuple(
        row for row in report.rows if row.settlement_timing_status is None
    )
    assert tuple(row.market_slug for row in missing_rows) == ("missing-a", "missing-b")
    assert all(row.overlay_status == "blocked" for row in missing_rows)
    assert all(row.reason_codes == ("missing_settlement_timing",) for row in missing_rows)


def test_overlay_blocks_when_blocked_settlement_exposure_exceeds_configured_share():
    nav_report = _nav_report(
        _exposure(
            condition_id="condition-blocked",
            market_slug="blocked-market",
            open_size=Decimal("200.0000"),
            cost_basis=Decimal("160.0000"),
            exit_value=Decimal("150.0000"),
            share_of_exit_nav=Decimal("0.150000"),
        ),
        _exposure(
            condition_id="condition-ok",
            market_slug="ok-market",
            open_size=Decimal("60.0000"),
            cost_basis=Decimal("40.0000"),
            exit_value=Decimal("30.0000"),
            share_of_exit_nav=Decimal("0.030000"),
        ),
    )
    settlement_report = _settlement_report(
        _timing_row(market_slug="blocked-market", timing_status="blocked"),
        _timing_row(market_slug="ok-market", timing_status="acceptable"),
    )

    report = _build_overlay(nav_report, settlement_report)

    assert report.blocked_or_missing_exit_value == Decimal("150.0000")
    assert report.blocked_or_missing_exit_nav_share == Decimal("0.150000")
    assert report.max_blocked_settlement_exposure_share == Decimal("0.100000")
    assert report.status == "settlement_nav_risk_blocked"


def test_overlay_empty_nav_exposure_returns_empty_report():
    report = _build_overlay(_nav_report(), _settlement_report())

    assert report.status == "empty_nav_settlement_risk_overlay"
    assert report.exposure_row_count == 0
    assert report.acceptable_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.blocked_or_missing_exit_value == Decimal("0")
    assert report.blocked_or_missing_exit_nav_share == Decimal("0.000000")
    assert report.rows == ()


def test_overlay_direct_constructors_revalidate_consistency_and_flags():
    report = _build_overlay(
        _nav_report(
            _exposure(
                condition_id="condition-a",
                market_slug="market-a",
                open_size=Decimal("100.0000"),
                cost_basis=Decimal("70.0000"),
                exit_value=Decimal("80.0000"),
                share_of_exit_nav=Decimal("0.080000"),
            ),
        ),
        _settlement_report(_timing_row(market_slug="market-a")),
    )
    rebuilt_row = _imports()["PaperNavSettlementRiskOverlayRow"](
        **{field.name: getattr(report.rows[0], field.name) for field in fields(report.rows[0])}
    )
    assert rebuilt_row == report.rows[0]

    with pytest.raises(ValueError, match="blocked_or_missing_exit_value"):
        replace(report, blocked_or_missing_exit_value=Decimal("1.0000"))
    with pytest.raises(ValueError, match="exposure_row_count"):
        replace(report, exposure_row_count=2)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(FrozenInstanceError):
        report.status = "settlement_nav_risk_blocked"


def test_overlay_rejects_invalid_public_inputs_and_keeps_decimal_boundary():
    nav_report = _nav_report()
    settlement_report = _settlement_report()

    with pytest.raises(ValueError, match="max_blocked_settlement_exposure_share"):
        _config(max_blocked_settlement_exposure_share=0.1)
    with pytest.raises(ValueError, match="max_blocked_settlement_exposure_share"):
        _config(max_blocked_settlement_exposure_share=Decimal("1.000001"))
    with pytest.raises(ValueError, match="nav_risk_report"):
        _build_overlay(object(), settlement_report)
    with pytest.raises(ValueError, match="settlement_timing_report"):
        _build_overlay(nav_report, object())
    with pytest.raises(ValueError, match="config"):
        _imports()["build_paper_nav_settlement_risk_overlay_report"](
            nav_risk_report=nav_report,
            settlement_timing_report=settlement_report,
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        _imports()["build_paper_nav_settlement_risk_overlay_report"](
            nav_risk_report=nav_report,
            settlement_timing_report=settlement_report,
            config=_config(),
            generated_at="now",
        )
    with pytest.raises(ValueError, match="report_only"):
        _build_overlay(replace(nav_report, report_only=False), settlement_report)


def test_overlay_module_stays_report_only_leaf_computation():
    import polymarket_alpha_lab.paper_nav_settlement_risk_overlay as overlay

    source = inspect.getsource(overlay)
    tree = ast.parse(source)
    project_imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith("polymarket_alpha_lab."):
                project_imports.add(module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("polymarket_alpha_lab."):
                    project_imports.add(alias.name)

    assert project_imports == {
        "polymarket_alpha_lab.nav_risk_metrics",
        "polymarket_alpha_lab.paper_settlement_timing",
    }
    lowered = source.lower()
    for forbidden in (
        ".read(",
        "open(",
        "path",
        "logging",
        "logger",
        "client",
        "network",
        "auth",
        "wallet",
        "private_key",
        "trade",
    ):
        assert forbidden not in lowered
