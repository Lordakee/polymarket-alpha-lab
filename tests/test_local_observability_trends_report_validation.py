from __future__ import annotations

from dataclasses import fields, replace
from datetime import UTC, datetime
from typing import Any

import pytest

from polymarket_alpha_lab.local_observability_trends import (
    LocalObservabilityTrendsReport,
)
from polymarket_alpha_lab.nav_risk_trend import (
    PaperNavRiskTrendConfig,
    build_paper_nav_risk_trend_report,
)
from polymarket_alpha_lab.outcome_freshness import (
    OutcomeFreshnessConfig,
    build_outcome_freshness_report,
)
from polymarket_alpha_lab.paper_trade_cost_trend import (
    PaperTradeCostTrendConfig,
    build_paper_trade_cost_trend_report,
)
from polymarket_alpha_lab.strategy_evidence_trend import (
    PaperStrategyEvidenceTrendConfig,
    PaperStrategyEvidenceTrendReport,
    build_paper_strategy_evidence_trend_report,
)


GENERATED_AT = datetime(2026, 6, 17, 18, 0, tzinfo=UTC)


class _PaperStrategyEvidenceTrendReportSubclass(PaperStrategyEvidenceTrendReport):
    pass


class _DuckReport:
    def __init__(self, source: Any) -> None:
        for field in fields(source):
            setattr(self, field.name, getattr(source, field.name))


def _strategy_evidence_trend():
    return build_paper_strategy_evidence_trend_report(
        (),
        config=PaperStrategyEvidenceTrendConfig(
            config_version="strategy-evidence-trend-v0",
        ),
        generated_at=GENERATED_AT,
    )


def _outcome_freshness():
    return build_outcome_freshness_report(
        (),
        config=OutcomeFreshnessConfig(
            config_version="outcome-freshness-v0",
            stale_after_seconds=60,
        ),
        generated_at=GENERATED_AT,
    )


def _nav_risk_trend():
    return build_paper_nav_risk_trend_report(
        (),
        config=PaperNavRiskTrendConfig(config_version="nav-risk-trend-v0"),
        generated_at=GENERATED_AT,
    )


def _paper_trade_cost_trend():
    return build_paper_trade_cost_trend_report(
        (),
        config=PaperTradeCostTrendConfig(
            config_version="paper-trade-cost-trend-v0",
        ),
        generated_at=GENERATED_AT,
    )


def _report() -> LocalObservabilityTrendsReport:
    return LocalObservabilityTrendsReport(
        generated_at=GENERATED_AT,
        config_version="local-observability-trends-v0",
        strategy_evidence_trend=_strategy_evidence_trend(),
        outcome_freshness=_outcome_freshness(),
        nav_risk_trend=_nav_risk_trend(),
        paper_trade_cost_trend=_paper_trade_cost_trend(),
    )


def _field_values(instance: Any) -> dict[str, Any]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


@pytest.mark.parametrize(
    ("field_name", "wrong_field_name", "expected_type_name"),
    (
        (
            "strategy_evidence_trend",
            "outcome_freshness",
            "PaperStrategyEvidenceTrendReport",
        ),
        (
            "outcome_freshness",
            "strategy_evidence_trend",
            "OutcomeFreshnessReport",
        ),
        (
            "nav_risk_trend",
            "paper_trade_cost_trend",
            "PaperNavRiskTrendReport",
        ),
        (
            "paper_trade_cost_trend",
            "nav_risk_trend",
            "PaperTradeCostTrendReport",
        ),
    ),
)
def test_local_observability_report_rejects_wrong_child_report_type(
    field_name,
    wrong_field_name,
    expected_type_name,
):
    report = _report()

    with pytest.raises(
        ValueError,
        match=f"{field_name} must be a {expected_type_name}",
    ):
        replace(report, **{field_name: getattr(report, wrong_field_name)})


def test_local_observability_report_rejects_child_report_subclass():
    report = _report()
    subclassed_child = _PaperStrategyEvidenceTrendReportSubclass(
        **_field_values(report.strategy_evidence_trend),
    )

    assert isinstance(subclassed_child, PaperStrategyEvidenceTrendReport)
    assert type(subclassed_child) is not PaperStrategyEvidenceTrendReport
    with pytest.raises(
        ValueError,
        match="strategy_evidence_trend must be a PaperStrategyEvidenceTrendReport",
    ):
        replace(report, strategy_evidence_trend=subclassed_child)


def test_local_observability_report_rejects_duck_typed_child_report():
    report = _report()
    duck_child = _DuckReport(report.outcome_freshness)

    assert duck_child.paper_only is True
    assert duck_child.report_only is True
    assert duck_child.readonly is True
    with pytest.raises(
        ValueError,
        match="outcome_freshness must be a OutcomeFreshnessReport",
    ):
        replace(report, outcome_freshness=duck_child)


@pytest.mark.parametrize(
    ("field_name", "flag_name"),
    (
        ("strategy_evidence_trend", "paper_only"),
        ("strategy_evidence_trend", "report_only"),
        ("strategy_evidence_trend", "readonly"),
        ("outcome_freshness", "paper_only"),
        ("outcome_freshness", "report_only"),
        ("outcome_freshness", "readonly"),
        ("nav_risk_trend", "paper_only"),
        ("nav_risk_trend", "report_only"),
        ("nav_risk_trend", "readonly"),
        ("paper_trade_cost_trend", "paper_only"),
        ("paper_trade_cost_trend", "report_only"),
        ("paper_trade_cost_trend", "readonly"),
    ),
)
def test_local_observability_report_rejects_child_report_false_safety_flags(
    field_name,
    flag_name,
):
    report = _report()
    child = replace(getattr(report, field_name))
    object.__setattr__(child, flag_name, False)

    with pytest.raises(
        ValueError,
        match=f"{field_name} {flag_name} must be True",
    ):
        replace(report, **{field_name: child})
