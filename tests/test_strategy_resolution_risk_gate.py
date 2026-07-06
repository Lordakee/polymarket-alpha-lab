from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_resolution_risk_gate import (
    DEFAULT_STRATEGY_RESOLUTION_RISK_GATE_CONFIG_VERSION,
    StrategyResolutionRiskGateConfig,
    StrategyResolutionRiskGateMetrics,
    StrategyResolutionRiskGateReasonCodeCount,
    StrategyResolutionRiskGateReport,
    build_strategy_resolution_risk_gate_report,
    strategy_resolution_risk_gate_payload,
)


class StrategyResolutionRiskGateConfigSubclass(StrategyResolutionRiskGateConfig):
    pass


class StrategyResolutionRiskGateMetricsSubclass(StrategyResolutionRiskGateMetrics):
    pass


class StrategyResolutionRiskGateReasonCodeCountSubclass(
    StrategyResolutionRiskGateReasonCodeCount,
):
    pass


class StrategyResolutionRiskGateReportSubclass(StrategyResolutionRiskGateReport):
    pass


def _metrics(
    *,
    rule_clarity_score: Decimal = Decimal("0.900000"),
    official_source_count: Decimal = Decimal("3"),
    dispute_history_score: Decimal = Decimal("0.100000"),
    time_to_resolution_hours: Decimal = Decimal("48.000000"),
    resolution_dependency_count: Decimal = Decimal("0"),
) -> StrategyResolutionRiskGateMetrics:
    return StrategyResolutionRiskGateMetrics(
        rule_clarity_score=rule_clarity_score,
        official_source_count=official_source_count,
        dispute_history_score=dispute_history_score,
        time_to_resolution_hours=time_to_resolution_hours,
        resolution_dependency_count=resolution_dependency_count,
    )


def _report(
    metrics: StrategyResolutionRiskGateMetrics,
    *,
    config: StrategyResolutionRiskGateConfig | None = None,
) -> StrategyResolutionRiskGateReport:
    return build_strategy_resolution_risk_gate_report(
        metrics,
        config=config or StrategyResolutionRiskGateConfig(),
    )


def test_strategy_resolution_risk_gate_passes_clear_resolution_profile() -> None:
    report = _report(_metrics())

    assert report.config_version == DEFAULT_STRATEGY_RESOLUTION_RISK_GATE_CONFIG_VERSION
    assert report.gate_status == "pass"
    assert report.recommended_next_step == "allow_strategy_resolution_risk_gate"
    assert report.rule_clarity_score == Decimal("0.900000")
    assert report.official_source_count == Decimal("3")
    assert report.dispute_history_score == Decimal("0.100000")
    assert report.time_to_resolution_hours == Decimal("48.000000")
    assert report.resolution_dependency_count == Decimal("0")
    assert report.reason_codes == ("strategy_resolution_risk_gate_passed",)
    assert report.reason_code_counts == (
        StrategyResolutionRiskGateReasonCodeCount(
            reason_code="strategy_resolution_risk_gate_passed",
            count=Decimal("1"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(
        row.paper_only and row.report_only and row.readonly
        for row in report.reason_code_counts
    )


def test_strategy_resolution_risk_gate_watches_soft_resolution_risks() -> None:
    report = _report(
        _metrics(
            rule_clarity_score=Decimal("0.700000"),
            official_source_count=Decimal("1"),
            dispute_history_score=Decimal("0.400000"),
            time_to_resolution_hours=Decimal("12.000000"),
            resolution_dependency_count=Decimal("2"),
        ),
    )

    assert report.gate_status == "watch"
    assert report.recommended_next_step == "refresh_strategy_resolution_risk_evidence"
    assert report.reason_codes == (
        "weak_rule_clarity",
        "limited_official_sources",
        "elevated_dispute_history",
        "near_resolution_time_pressure",
        "resolution_dependency_load",
    )
    assert tuple(row.count for row in report.reason_code_counts) == (
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    )


def test_strategy_resolution_risk_gate_blocks_hard_resolution_risks() -> None:
    report = _report(
        _metrics(
            rule_clarity_score=Decimal("0.400000"),
            official_source_count=Decimal("0"),
            dispute_history_score=Decimal("0.700000"),
            time_to_resolution_hours=Decimal("4.000000"),
            resolution_dependency_count=Decimal("3"),
        ),
    )

    assert report.gate_status == "blocked"
    assert report.recommended_next_step == "block_strategy_resolution_risk_gate"
    assert report.reason_codes == (
        "ambiguous_resolution_rules",
        "missing_official_sources",
        "severe_dispute_history",
        "imminent_resolution_window",
        "excessive_resolution_dependencies",
    )


def test_strategy_resolution_risk_gate_blocking_reasons_dominate_watch_reasons() -> None:
    report = _report(
        _metrics(
            rule_clarity_score=Decimal("0.400000"),
            official_source_count=Decimal("1"),
            dispute_history_score=Decimal("0.400000"),
            time_to_resolution_hours=Decimal("12.000000"),
            resolution_dependency_count=Decimal("2"),
        ),
    )

    assert report.gate_status == "blocked"
    assert report.reason_codes == (
        "ambiguous_resolution_rules",
        "limited_official_sources",
        "elevated_dispute_history",
        "near_resolution_time_pressure",
        "resolution_dependency_load",
    )


def test_strategy_resolution_risk_gate_payload_is_report_only_decimal_text() -> None:
    payload = strategy_resolution_risk_gate_payload(_report(_metrics()))

    assert payload == {
        "config_version": DEFAULT_STRATEGY_RESOLUTION_RISK_GATE_CONFIG_VERSION,
        "gate_status": "pass",
        "recommended_next_step": "allow_strategy_resolution_risk_gate",
        "rule_clarity_score": "0.900000",
        "official_source_count": "3",
        "dispute_history_score": "0.100000",
        "time_to_resolution_hours": "48.000000",
        "resolution_dependency_count": "0",
        "reason_codes": ["strategy_resolution_risk_gate_passed"],
        "reason_code_counts": [
            {
                "reason_code": "strategy_resolution_risk_gate_passed",
                "count": "1",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("rule_clarity_score", 1),
        ("official_source_count", 1),
        ("dispute_history_score", 0.1),
        ("time_to_resolution_hours", "24"),
        ("resolution_dependency_count", True),
        ("paper_only", False),
        ("report_only", False),
        ("readonly", False),
    ),
)
def test_strategy_resolution_risk_gate_metrics_require_decimal_only_and_hard_flags(
    field_name: str,
    bad_value: object,
) -> None:
    kwargs = {
        "rule_clarity_score": Decimal("0.900000"),
        "official_source_count": Decimal("3"),
        "dispute_history_score": Decimal("0.100000"),
        "time_to_resolution_hours": Decimal("48.000000"),
        "resolution_dependency_count": Decimal("0"),
        field_name: bad_value,
    }

    with pytest.raises(ValueError, match=field_name):
        StrategyResolutionRiskGateMetrics(**kwargs)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("config_version", ""),
        ("pass_rule_clarity_score", Decimal("0.400000")),
        ("block_rule_clarity_score", Decimal("0.800000")),
        ("pass_official_source_count", Decimal("0")),
        ("block_official_source_count", Decimal("2")),
        ("pass_dispute_history_score", Decimal("0.700000")),
        ("block_dispute_history_score", Decimal("0.100000")),
        ("pass_time_to_resolution_hours", Decimal("4.000000")),
        ("block_time_to_resolution_hours", Decimal("48.000000")),
        ("pass_resolution_dependency_count", Decimal("3")),
        ("block_resolution_dependency_count", Decimal("1")),
        ("paper_only", False),
        ("report_only", False),
        ("readonly", False),
    ),
)
def test_strategy_resolution_risk_gate_config_validates_thresholds(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        StrategyResolutionRiskGateConfig(**{field_name: bad_value})


def test_strategy_resolution_risk_gate_outputs_are_frozen_and_tuple_only() -> None:
    report = _report(_metrics())

    with pytest.raises(FrozenInstanceError):
        report.gate_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.reason_code_counts[0].count = Decimal("2")  # type: ignore[misc]
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(report, recommended_next_step="block_strategy_resolution_risk_gate")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=["strategy_resolution_risk_gate_passed"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=list(report.reason_code_counts))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_strategy_resolution_risk_gate_rejects_subclasses() -> None:
    metrics = _metrics()
    report = _report(metrics)

    with pytest.raises(ValueError, match="config"):
        StrategyResolutionRiskGateConfigSubclass()
    with pytest.raises(ValueError, match="metrics"):
        StrategyResolutionRiskGateMetricsSubclass(**metrics.__dict__)
    with pytest.raises(ValueError, match="reason"):
        StrategyResolutionRiskGateReasonCodeCountSubclass(
            "strategy_resolution_risk_gate_passed",
            Decimal("1"),
        )
    with pytest.raises(ValueError, match="report"):
        StrategyResolutionRiskGateReportSubclass(**report.__dict__)


def test_strategy_resolution_risk_gate_revalidates_reason_rows() -> None:
    with pytest.raises(ValueError, match="reason_code"):
        StrategyResolutionRiskGateReasonCodeCount("unknown_reason", Decimal("1"))
    with pytest.raises(ValueError, match="count"):
        StrategyResolutionRiskGateReasonCodeCount(
            "strategy_resolution_risk_gate_passed",
            Decimal("0"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        StrategyResolutionRiskGateReasonCodeCount(
            "strategy_resolution_risk_gate_passed",
            Decimal("1"),
            paper_only=False,
        )


def test_strategy_resolution_risk_gate_rejects_unsafe_source_flags() -> None:
    metrics = _metrics()
    object.__setattr__(metrics, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        _report(metrics)

    metrics = _metrics()
    object.__setattr__(metrics, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        _report(metrics)

    metrics = _metrics()
    object.__setattr__(metrics, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        _report(metrics)


def test_strategy_resolution_risk_gate_module_scope_stays_pure_readonly() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_resolution_risk_gate.py",
    ).read_text(encoding="utf-8")

    for banned_term in (
        "psycopg",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib",
        "websocket",
        "websockets",
        "eth_account",
        "cli",
        "env",
        "wallet",
        "auth",
    ):
        assert banned_term not in source.lower()
