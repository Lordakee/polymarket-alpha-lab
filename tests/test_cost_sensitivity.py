from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventSideResult,
    PaperCostAwareEventStrategyGateResult,
    PaperCostAwareEventStrategyReport,
)
from polymarket_alpha_lab.cost_sensitivity import (
    PaperCostSensitivityConfig,
    PaperCostSensitivityReport,
    PaperCostSensitivityRow,
    build_paper_cost_sensitivity_report,
)


GENERATED_AT = datetime(2026, 6, 18, 20, 0, tzinfo=UTC)
CONFIG_VERSION = "cost-sensitivity-v0"
GATE_NAMES = (
    "data_integrity",
    "confidence",
    "spread",
    "resolution_risk",
    "yes_depth",
    "no_depth",
    "edge_threshold",
)


def _config(**overrides):
    values = {
        "config_version": CONFIG_VERSION,
        "min_stressed_net_edge": Decimal("0.010000"),
        "cost_shock_per_share_values": (
            Decimal("0.000000"),
            Decimal("0.010000"),
        ),
    }
    values.update(overrides)
    return PaperCostSensitivityConfig(**values)


def _gate_results() -> tuple[PaperCostAwareEventStrategyGateResult, ...]:
    return tuple(
        PaperCostAwareEventStrategyGateResult(
            gate_name=gate_name,
            status="pass",
            reason_code=f"{gate_name}_ready",
            message=f"{gate_name} ready.",
            observed_value=Decimal("1"),
            threshold=Decimal("0"),
        )
        for gate_name in GATE_NAMES
    )


def _side_result(
    side: str,
    *,
    net_edge_per_share: Decimal | None,
) -> PaperCostAwareEventSideResult:
    has_edge = net_edge_per_share is not None
    return PaperCostAwareEventSideResult(
        side=side,
        fair_probability=Decimal("0.6200"),
        executable_price=Decimal("0.5000") if has_edge else None,
        ask_size=Decimal("10.0000"),
        gross_edge_per_share=net_edge_per_share,
        fee_cost_per_share=Decimal("0.000000") if has_edge else None,
        non_fee_cost_per_share=Decimal("0.000000") if has_edge else None,
        total_cost_per_share=Decimal("0.000000") if has_edge else None,
        net_edge_per_share=net_edge_per_share,
        reason_codes=("paper_edge_complete",) if has_edge else ("missing_ask",),
    )


def _source_report_kwargs(
    *,
    market_slug: str = "market-alpha",
    selected_side: str = "yes",
    yes_net_edge: Decimal | None = Decimal("0.030000"),
    no_net_edge: Decimal | None = Decimal("0.020000"),
):
    return {
        "generated_at": GENERATED_AT,
        "config_version": "cost-aware-event-v0",
        "market_slug": market_slug,
        "question": f"{market_slug}?",
        "fair_probability_yes": Decimal("0.6200"),
        "confidence": Decimal("0.8000"),
        "yes_bid": Decimal("0.4900"),
        "no_bid": Decimal("0.4800"),
        "spread": Decimal("0.0200"),
        "resolution_risk": Decimal("0.0500"),
        "selected_side": selected_side,
        "status": "paper_review_ready" if selected_side != "none" else "watch",
        "yes_result": _side_result("yes", net_edge_per_share=yes_net_edge),
        "no_result": _side_result("no", net_edge_per_share=no_net_edge),
        "gate_results": _gate_results(),
    }


def _source_report(**overrides) -> PaperCostAwareEventStrategyReport:
    return PaperCostAwareEventStrategyReport(**_source_report_kwargs(**overrides))


def test_cost_sensitivity_marks_pass_and_watch_under_shocks():
    source = _source_report(
        market_slug="market-alpha",
        selected_side="yes",
        yes_net_edge=Decimal("0.030000"),
    )
    config = _config(
        cost_shock_per_share_values=(
            Decimal("0.000000"),
            Decimal("0.025000"),
        ),
    )

    report = build_paper_cost_sensitivity_report(
        [source],
        config=config,
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, PaperCostSensitivityReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.source_report_count == 1
    assert report.row_count == 2
    assert report.pass_count == 1
    assert report.watch_count == 1
    assert report.blocked_count == 0
    assert report.status == "watch"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert [
        (
            row.market_slug,
            row.selected_side,
            row.base_net_edge_per_share,
            row.cost_shock_per_share,
            row.stressed_net_edge_per_share,
            row.status,
            row.reason_codes,
        )
        for row in report.rows
    ] == [
        (
            "market-alpha",
            "yes",
            Decimal("0.030000"),
            Decimal("0.000000"),
            Decimal("0.030000"),
            "pass",
            ("stressed_net_edge_ready",),
        ),
        (
            "market-alpha",
            "yes",
            Decimal("0.030000"),
            Decimal("0.025000"),
            Decimal("0.005000"),
            "watch",
            ("stressed_net_edge_below_minimum",),
        ),
    ]


def test_cost_sensitivity_blocks_missing_selected_side_or_base_edge():
    missing_side = _source_report(
        market_slug="market-beta",
        selected_side="none",
        yes_net_edge=Decimal("0.040000"),
        no_net_edge=Decimal("0.030000"),
    )
    missing_edge = _source_report(
        market_slug="market-gamma",
        selected_side="no",
        no_net_edge=None,
    )
    config = _config(cost_shock_per_share_values=(Decimal("0.010000"),))

    report = build_paper_cost_sensitivity_report(
        (missing_edge, missing_side),
        config=config,
        generated_at=GENERATED_AT,
    )

    assert report.status == "blocked"
    assert report.pass_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 2
    assert [
        (
            row.market_slug,
            row.selected_side,
            row.base_net_edge_per_share,
            row.cost_shock_per_share,
            row.stressed_net_edge_per_share,
            row.status,
            row.reason_codes,
        )
        for row in report.rows
    ] == [
        (
            "market-beta",
            "none",
            None,
            Decimal("0.010000"),
            None,
            "blocked",
            ("missing_selected_side",),
        ),
        (
            "market-gamma",
            "no",
            None,
            Decimal("0.010000"),
            None,
            "blocked",
            ("missing_base_net_edge",),
        ),
    ]


def test_cost_sensitivity_orders_rows_by_market_side_and_shock():
    sources = [
        _source_report(
            market_slug="market-b",
            selected_side="yes",
            yes_net_edge=Decimal("0.040000"),
        ),
        _source_report(
            market_slug="market-a",
            selected_side="yes",
            yes_net_edge=Decimal("0.040000"),
        ),
        _source_report(
            market_slug="market-a",
            selected_side="no",
            no_net_edge=Decimal("0.040000"),
        ),
    ]
    config = _config(
        cost_shock_per_share_values=(
            Decimal("0.020000"),
            Decimal("0.000000"),
        ),
    )

    report = build_paper_cost_sensitivity_report(
        sources,
        config=config,
        generated_at=GENERATED_AT,
    )

    assert [
        (row.market_slug, row.selected_side, row.cost_shock_per_share)
        for row in report.rows
    ] == [
        ("market-a", "no", Decimal("0.000000")),
        ("market-a", "no", Decimal("0.020000")),
        ("market-a", "yes", Decimal("0.000000")),
        ("market-a", "yes", Decimal("0.020000")),
        ("market-b", "yes", Decimal("0.000000")),
        ("market-b", "yes", Decimal("0.020000")),
    ]


def test_cost_sensitivity_config_validates_and_normalizes_shocks():
    config = _config(
        cost_shock_per_share_values=(
            Decimal("0.020000"),
            Decimal("0.000000"),
            Decimal("0.010000"),
        ),
    )

    assert config.cost_shock_per_share_values == (
        Decimal("0.000000"),
        Decimal("0.010000"),
        Decimal("0.020000"),
    )

    bad_values = [
        [],
        (),
        (Decimal("-0.010000"),),
        (Decimal("NaN"),),
        (Decimal("Infinity"),),
        (0,),
        (0.0,),
        (True,),
        (Decimal("0.010000"), Decimal("0.010000")),
    ]
    for value in bad_values:
        with pytest.raises(ValueError, match="cost_shock_per_share_values"):
            _config(cost_shock_per_share_values=value)


def test_cost_sensitivity_uses_exact_type_validation():
    class ConfigSubclass(PaperCostSensitivityConfig):
        pass

    class ReportSubclass(PaperCostAwareEventStrategyReport):
        pass

    class DateTimeSubclass(datetime):
        pass

    class StrSubclass(str):
        pass

    with pytest.raises(ValueError, match="config_version"):
        PaperCostSensitivityConfig(
            config_version=StrSubclass(CONFIG_VERSION),
            min_stressed_net_edge=Decimal("0.010000"),
            cost_shock_per_share_values=(Decimal("0.000000"),),
        )
    with pytest.raises(ValueError, match="min_stressed_net_edge"):
        PaperCostSensitivityConfig(
            config_version=CONFIG_VERSION,
            min_stressed_net_edge=0,
            cost_shock_per_share_values=(Decimal("0.000000"),),
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_cost_sensitivity_report(
            [_source_report()],
            config=ConfigSubclass(
                config_version=CONFIG_VERSION,
                min_stressed_net_edge=Decimal("0.010000"),
                cost_shock_per_share_values=(Decimal("0.000000"),),
            ),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_cost_sensitivity_report(
            [_source_report()],
            config=_config(),
            generated_at=DateTimeSubclass(2026, 6, 18, 20, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source reports"):
        build_paper_cost_sensitivity_report(
            [object()],
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="source reports"):
        build_paper_cost_sensitivity_report(
            [ReportSubclass(**_source_report_kwargs())],
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="pass_count"):
        PaperCostSensitivityReport(
            generated_at=GENERATED_AT,
            config_version=CONFIG_VERSION,
            source_report_count=0,
            row_count=0,
            pass_count=True,
            watch_count=0,
            blocked_count=0,
            status="pass",
            rows=(),
        )


def test_cost_sensitivity_normalizes_generated_at_to_utc():
    generated_at = datetime(
        2026,
        6,
        18,
        16,
        30,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    report = build_paper_cost_sensitivity_report(
        [_source_report()],
        config=_config(),
        generated_at=generated_at,
    )

    assert report.generated_at == datetime(2026, 6, 18, 20, 30, tzinfo=UTC)


def test_cost_sensitivity_dataclasses_are_frozen():
    config = _config()
    report = build_paper_cost_sensitivity_report(
        [_source_report()],
        config=config,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        config.min_stressed_net_edge = Decimal("0")
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "pass"


def test_cost_sensitivity_requires_hard_flags():
    report = build_paper_cost_sensitivity_report(
        [_source_report()],
        config=_config(),
        generated_at=GENERATED_AT,
    )

    for flag_name in ("paper_only", "report_only", "readonly"):
        values = {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "source_report_count": report.source_report_count,
            "row_count": report.row_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "blocked_count": report.blocked_count,
            "status": report.status,
            "rows": report.rows,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
        values[flag_name] = False
        with pytest.raises(ValueError, match=flag_name):
            PaperCostSensitivityReport(**values)

    source = _source_report()
    object.__setattr__(source, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        build_paper_cost_sensitivity_report(
            [source],
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_cost_sensitivity_row_validates_scalars_and_reason_codes():
    with pytest.raises(ValueError, match="market_slug"):
        PaperCostSensitivityRow(
            market_slug=" market",
            selected_side="yes",
            base_net_edge_per_share=Decimal("0.020000"),
            cost_shock_per_share=Decimal("0.000000"),
            stressed_net_edge_per_share=Decimal("0.020000"),
            status="pass",
            reason_codes=("stressed_net_edge_ready",),
        )
    with pytest.raises(ValueError, match="cost_shock_per_share"):
        PaperCostSensitivityRow(
            market_slug="market",
            selected_side="yes",
            base_net_edge_per_share=Decimal("0.020000"),
            cost_shock_per_share=0,
            stressed_net_edge_per_share=Decimal("0.020000"),
            status="pass",
            reason_codes=("stressed_net_edge_ready",),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        PaperCostSensitivityRow(
            market_slug="market",
            selected_side="yes",
            base_net_edge_per_share=Decimal("0.020000"),
            cost_shock_per_share=Decimal("0.000000"),
            stressed_net_edge_per_share=Decimal("0.020000"),
            status="pass",
            reason_codes=(),
        )
