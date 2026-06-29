from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from importlib import import_module
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend_gate import (
    PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReasonCodeCount,
    PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport,
)
from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend_gate import (
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReasonCodeCount,
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_history_health import (
    PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount,
    PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport,
)
from polymarket_alpha_lab.paper_strategy_cycle_report_history_gate import (
    PaperStrategyCycleReportHistoryGateReasonCodeCount,
    PaperStrategyCycleReportHistoryGateReport,
)


GENERATED_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
SOURCE_TZ = timezone(timedelta(hours=-4))


def _api():
    return import_module("polymarket_alpha_lab.paper_autonomous_readiness_gate")


def _screening_report(
    *,
    health_status: str = "pass",
    recommended_next_step: str | None = None,
    generated_at: datetime = GENERATED_AT,
    config_version: str = "screening-health-v0",
    reason_codes: tuple[str, ...] = (
        "paper_autonomous_screening_decision_support_gate_db_history_health_passed",
    ),
    reason_code_counts: tuple[
        PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount,
        ...,
    ]
    | None = None,
) -> PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport:
    if recommended_next_step is None:
        recommended_next_step = {
            "pass": "allow_paper_autonomous_screening_decision_support_gate_history_review",
            "watch": (
                "throttle_paper_autonomous_screening_decision_support_gate_history_review"
            ),
            "blocked": (
                "block_paper_autonomous_screening_decision_support_gate_history_review"
            ),
        }[health_status]
    if reason_code_counts is None:
        reason_code_counts = tuple(
            PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReasonCodeCount(
                reason_code=reason_code,
                report_count=1,
            )
            for reason_code in reason_codes
        )
    return PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport(
        generated_at=generated_at,
        config_version=config_version,
        health_status=health_status,
        recommended_next_step=recommended_next_step,
        source_report_count=3,
        pass_gate_report_count=3 if health_status == "pass" else 2,
        watch_gate_report_count=1 if health_status == "watch" else 0,
        blocked_gate_report_count=1 if health_status == "blocked" else 0,
        latest_gate_status=health_status,
        latest_gate_generated_at=generated_at - timedelta(minutes=5),
        latest_gate_age_seconds=300,
        consecutive_latest_watch_count=1 if health_status == "watch" else 0,
        consecutive_latest_blocked_count=1 if health_status == "blocked" else 0,
        distinct_gate_config_versions=("screening-gate-v0",),
        distinct_operator_flow_gate_config_versions=("operator-flow-v0",),
        distinct_queue_risk_config_versions=("queue-risk-v0",),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def _allocation_report(
    *,
    gate_status: str = "pass",
    recommended_next_step: str | None = None,
    generated_at: datetime = GENERATED_AT,
    config_version: str = "allocation-trend-gate-v0",
    source_config_version: str = "allocation-trend-v0",
    reason_codes: tuple[str, ...] = (
        "paper_autonomous_allocation_proposal_db_history_health_trend_gate_passed",
    ),
    reason_code_counts: tuple[
        PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReasonCodeCount,
        ...,
    ]
    | None = None,
) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport:
    if recommended_next_step is None:
        recommended_next_step = {
            "pass": (
                "allow_paper_autonomous_allocation_proposal_db_history_health_trend_review"
            ),
            "watch": (
                "throttle_paper_autonomous_allocation_proposal_db_history_health_trend_review"
            ),
            "blocked": (
                "block_paper_autonomous_allocation_proposal_db_history_health_trend_review"
            ),
        }[gate_status]
    if reason_code_counts is None:
        reason_code_counts = tuple(
            PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReasonCodeCount(
                reason_code=reason_code,
                report_count=1,
            )
            for reason_code in reason_codes
        )
    return PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport(
        generated_at=generated_at,
        config_version=config_version,
        source_config_version=source_config_version,
        source_generated_at=generated_at - timedelta(minutes=10),
        gate_status=gate_status,
        recommended_next_step=recommended_next_step,
        reason_code_counts=reason_code_counts,
        source_health_report_count=3,
        trend_report_age_seconds=600,
        latest_health_status=gate_status,
        latest_health_generated_at=generated_at - timedelta(minutes=10),
        latest_source_age_seconds=600,
        duplicate_generated_at_count=0,
        consecutive_latest_watch_count=1 if gate_status == "watch" else 0,
        consecutive_latest_blocked_count=1 if gate_status == "blocked" else 0,
        watch_report_count_delta=0,
        blocked_report_count_delta=0,
        latest_allocated_count_delta=0,
        latest_total_allocated_paper_notional_delta=None,
        latest_reason_code_counts=(("source_allocation_reason", 1),),
        repeated_reason_code_counts=(),
        reason_codes=reason_codes,
    )


def _ledger_report(
    *,
    gate_status: str = "pass",
    recommended_next_step: str | None = None,
    generated_at: datetime = GENERATED_AT,
    config_version: str = "ledger-trend-gate-v0",
    source_config_version: str = "ledger-trend-v0",
    reason_codes: tuple[str, ...] = (
        "paper_autonomous_investment_ledger_db_history_health_trend_gate_passed",
    ),
    reason_code_counts: tuple[
        PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReasonCodeCount,
        ...,
    ]
    | None = None,
) -> PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport:
    if recommended_next_step is None:
        recommended_next_step = {
            "pass": (
                "allow_paper_autonomous_investment_ledger_db_history_health_trend_review"
            ),
            "watch": (
                "throttle_paper_autonomous_investment_ledger_db_history_health_trend_review"
            ),
            "blocked": (
                "block_paper_autonomous_investment_ledger_db_history_health_trend_review"
            ),
        }[gate_status]
    if reason_code_counts is None:
        reason_code_counts = tuple(
            PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReasonCodeCount(
                reason_code=reason_code,
                report_count=1,
            )
            for reason_code in reason_codes
        )
    return PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport(
        generated_at=generated_at,
        config_version=config_version,
        source_config_version=source_config_version,
        source_generated_at=generated_at - timedelta(minutes=15),
        gate_status=gate_status,
        recommended_next_step=recommended_next_step,
        reason_code_counts=reason_code_counts,
        source_health_report_count=3,
        trend_report_age_seconds=900,
        latest_health_status=gate_status,
        latest_health_generated_at=generated_at - timedelta(minutes=15),
        latest_source_age_seconds=900,
        duplicate_generated_at_count=0,
        consecutive_latest_watch_count=1 if gate_status == "watch" else 0,
        consecutive_latest_blocked_count=1 if gate_status == "blocked" else 0,
        watch_ledger_report_count_delta=0,
        blocked_ledger_report_count_delta=0,
        latest_source_record_count_delta=0,
        latest_submitted_count_delta=0,
        latest_held_count_delta=0,
        latest_blocked_count_delta=0,
        latest_total_submitted_notional_delta=None,
        latest_source_generated_at_delta_seconds=0,
        latest_source_age_seconds_delta=0,
        max_source_age_seconds_delta=0,
        duplicate_latest_generated_at_count_delta=0,
        latest_reason_code_counts=(("source_ledger_reason", 1),),
        repeated_reason_code_counts=(),
        reason_codes=reason_codes,
    )


def _strategy_cycle_history_gate_report(
    *,
    gate_status: str = "pass",
    recommended_next_step: str | None = None,
    generated_at: datetime = GENERATED_AT,
    config_version: str = "paper-strategy-cycle-report-history-gate-v0",
    source_config_version: str = "paper-strategy-cycle-report-history-v0",
    reason_codes: tuple[str, ...] | None = None,
    reason_code_counts: tuple[
        PaperStrategyCycleReportHistoryGateReasonCodeCount,
        ...,
    ]
    | None = None,
) -> PaperStrategyCycleReportHistoryGateReport:
    if recommended_next_step is None:
        recommended_next_step = {
            "pass": "allow_strategy_cycle_history_gate",
            "watch": "throttle_strategy_cycle_history_gate",
            "blocked": "block_strategy_cycle_history_gate",
        }[gate_status]
    if reason_codes is None:
        reason_codes = {
            "pass": ("paper_strategy_cycle_report_history_gate_passed",),
            "watch": ("source_strategy_cycle_report_history_watch",),
            "blocked": ("source_strategy_cycle_report_history_blocked",),
        }[gate_status]
    if reason_code_counts is None:
        reason_code_counts = tuple(
            PaperStrategyCycleReportHistoryGateReasonCodeCount(
                reason_code=reason_code,
                report_count=1,
            )
            for reason_code in reason_codes
        )
    return PaperStrategyCycleReportHistoryGateReport(
        generated_at=generated_at,
        config_version=config_version,
        source_config_version=source_config_version,
        source_generated_at=generated_at - timedelta(minutes=20),
        gate_status=gate_status,
        recommended_next_step=recommended_next_step,
        reason_code_counts=reason_code_counts,
        source_history_status=gate_status,
        source_report_count=3,
        latest_source_generated_at=generated_at - timedelta(minutes=20),
        latest_source_age_seconds=1_200,
        latest_snapshot_ready_share=Decimal("1"),
        blocked_market_share=Decimal("0"),
        latest_snapshot_ready_count=3,
        latest_considered_count=3,
        total_blocked_market_count=0,
        reason_codes=reason_codes,
    )


def _readiness_report(
    *,
    screening_report: (
        PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport | None
    ) = None,
    allocation_report: (
        PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport | None
    ) = None,
    investment_ledger_report: (
        PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport | None
    ) = None,
    strategy_cycle_history_gate_report: (
        PaperStrategyCycleReportHistoryGateReport | None
    ) = None,
    generated_at: datetime = GENERATED_AT,
):
    api = _api()
    return api.build_paper_autonomous_readiness_gate_report(
        screening_report or _screening_report(),
        allocation_report or _allocation_report(),
        investment_ledger_report or _ledger_report(),
        config=api.PaperAutonomousReadinessGateConfig(),
        generated_at=generated_at,
        strategy_cycle_history_gate_report=strategy_cycle_history_gate_report,
    )


def test_readiness_gate_default_config_and_all_exports():
    api = _api()

    config = api.PaperAutonomousReadinessGateConfig()

    assert config.config_version == "paper-autonomous-readiness-gate-v0"
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True
    assert api.__all__ == (
        "DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_CONFIG_VERSION",
        "PaperAutonomousReadinessGateConfig",
        "PaperAutonomousReadinessGateReasonCodeCount",
        "PaperAutonomousReadinessGateSourceStatus",
        "PaperAutonomousReadinessGateReport",
        "build_paper_autonomous_readiness_gate_report",
    )


def test_readiness_gate_passes_when_all_sources_pass_and_normalizes_time():
    generated_at = datetime(2026, 6, 25, 8, 0, tzinfo=SOURCE_TZ)

    report = _readiness_report(generated_at=generated_at)

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "paper-autonomous-readiness-gate-v0"
    assert report.readiness_status == "pass"
    assert report.recommended_next_step == "allow_paper_autonomous_readiness_review"
    assert report.reason_codes == (
        "allocation_proposal_db_history_health_trend_gate_pass",
        "investment_ledger_db_history_health_trend_gate_pass",
        "paper_autonomous_readiness_gate_passed",
        "screening_decision_support_gate_db_history_health_pass",
    )
    assert report.reason_code_counts == (
        _api().PaperAutonomousReadinessGateReasonCodeCount(
            "allocation_proposal_db_history_health_trend_gate_pass",
            1,
        ),
        _api().PaperAutonomousReadinessGateReasonCodeCount(
            "investment_ledger_db_history_health_trend_gate_pass",
            1,
        ),
        _api().PaperAutonomousReadinessGateReasonCodeCount(
            "paper_autonomous_readiness_gate_passed",
            1,
        ),
        _api().PaperAutonomousReadinessGateReasonCodeCount(
            "screening_decision_support_gate_db_history_health_pass",
            1,
        ),
    )
    assert tuple(row.source_name for row in report.source_statuses) == (
        "screening_decision_support_gate_db_history_health",
        "allocation_proposal_db_history_health_trend_gate",
        "investment_ledger_db_history_health_trend_gate",
    )
    assert tuple(row.status for row in report.source_statuses) == (
        "pass",
        "pass",
        "pass",
    )
    assert tuple(row.generated_at for row in report.source_statuses) == (
        GENERATED_AT,
        GENERATED_AT,
        GENERATED_AT,
    )
    assert tuple(row.config_version for row in report.source_statuses) == (
        "screening-health-v0",
        "allocation-trend-gate-v0",
        "ledger-trend-gate-v0",
    )
    assert tuple(row.recommended_next_step for row in report.source_statuses) == (
        "allow_paper_autonomous_screening_decision_support_gate_history_review",
        "allow_paper_autonomous_allocation_proposal_db_history_health_trend_review",
        "allow_paper_autonomous_investment_ledger_db_history_health_trend_review",
    )
    assert report.source_config_versions == (
        ("screening_decision_support_gate_db_history_health", "screening-health-v0"),
        ("allocation_proposal_db_history_health_trend_gate", "allocation-trend-gate-v0"),
        ("investment_ledger_db_history_health_trend_gate", "ledger-trend-gate-v0"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_readiness_gate_keeps_legacy_three_source_behavior_without_strategy_cycle_gate():
    report = _readiness_report()
    assert tuple(row.source_name for row in report.source_statuses) == (
        "screening_decision_support_gate_db_history_health",
        "allocation_proposal_db_history_health_trend_gate",
        "investment_ledger_db_history_health_trend_gate",
    )
    assert "strategy_cycle_report_history_gate_pass" not in report.reason_codes


def test_readiness_gate_includes_strategy_cycle_history_gate_as_fourth_source():
    report = _readiness_report(
        strategy_cycle_history_gate_report=_strategy_cycle_history_gate_report(),
    )
    assert tuple(row.source_name for row in report.source_statuses) == (
        "screening_decision_support_gate_db_history_health",
        "strategy_cycle_report_history_gate",
        "allocation_proposal_db_history_health_trend_gate",
        "investment_ledger_db_history_health_trend_gate",
    )
    assert report.reason_codes == (
        "allocation_proposal_db_history_health_trend_gate_pass",
        "investment_ledger_db_history_health_trend_gate_pass",
        "paper_autonomous_readiness_gate_passed",
        "screening_decision_support_gate_db_history_health_pass",
        "strategy_cycle_report_history_gate_pass",
    )


def test_readiness_gate_strategy_cycle_watch_throttles_and_blocked_blocks():
    watch_report = _readiness_report(
        strategy_cycle_history_gate_report=_strategy_cycle_history_gate_report(
            gate_status="watch",
        ),
    )
    assert watch_report.readiness_status == "watch"
    assert "strategy_cycle_report_history_gate_watch" in watch_report.reason_codes

    blocked_report = _readiness_report(
        strategy_cycle_history_gate_report=_strategy_cycle_history_gate_report(
            gate_status="blocked",
        ),
    )
    assert blocked_report.readiness_status == "blocked"
    assert "strategy_cycle_report_history_gate_blocked" in blocked_report.reason_codes


def test_readiness_gate_rejects_noncanonical_four_source_constructor_sequence():
    report = _readiness_report(
        strategy_cycle_history_gate_report=_strategy_cycle_history_gate_report(),
    )
    source_statuses = (
        report.source_statuses[1],
        report.source_statuses[0],
        report.source_statuses[2],
        report.source_statuses[3],
    )

    with pytest.raises(ValueError, match="canonical source sequence"):
        replace(
            report,
            source_statuses=source_statuses,
            source_config_versions=tuple(
                (row.source_name, row.config_version) for row in source_statuses
            ),
        )


def test_readiness_gate_watches_when_any_source_watches_without_blockers():
    report = _readiness_report(
        allocation_report=_allocation_report(
            gate_status="watch",
            reason_codes=("latest_allocation_proposal_db_history_health_trend_watch",),
        ),
    )

    assert report.readiness_status == "watch"
    assert report.recommended_next_step == "throttle_paper_autonomous_readiness_review"
    assert report.reason_codes == (
        "allocation_proposal_db_history_health_trend_gate_watch",
        "investment_ledger_db_history_health_trend_gate_pass",
        "screening_decision_support_gate_db_history_health_pass",
    )
    assert report.reason_code_counts == (
        _api().PaperAutonomousReadinessGateReasonCodeCount(
        "allocation_proposal_db_history_health_trend_gate_watch",
            1,
        ),
        _api().PaperAutonomousReadinessGateReasonCodeCount(
            "investment_ledger_db_history_health_trend_gate_pass",
            1,
        ),
        _api().PaperAutonomousReadinessGateReasonCodeCount(
            "screening_decision_support_gate_db_history_health_pass",
            1,
        ),
    )


def test_readiness_gate_blocks_when_any_source_blocks_and_blocked_takes_precedence():
    report = _readiness_report(
        screening_report=_screening_report(
            health_status="watch",
            reason_codes=(
                "latest_paper_autonomous_screening_decision_support_gate_watch",
            ),
        ),
        investment_ledger_report=_ledger_report(
            gate_status="blocked",
            reason_codes=(
                "latest_paper_autonomous_investment_ledger_db_history_health_trend_blocked",
            ),
        ),
    )

    assert report.readiness_status == "blocked"
    assert report.recommended_next_step == "block_paper_autonomous_readiness_review"
    assert report.reason_codes == (
        "allocation_proposal_db_history_health_trend_gate_pass",
        "investment_ledger_db_history_health_trend_gate_blocked",
        "screening_decision_support_gate_db_history_health_watch",
    )
    assert report.reason_code_counts == (
        _api().PaperAutonomousReadinessGateReasonCodeCount(
            "allocation_proposal_db_history_health_trend_gate_pass",
            1,
        ),
        _api().PaperAutonomousReadinessGateReasonCodeCount(
            "investment_ledger_db_history_health_trend_gate_blocked",
            1,
        ),
        _api().PaperAutonomousReadinessGateReasonCodeCount(
            "screening_decision_support_gate_db_history_health_watch",
            1,
        ),
    )


def test_readiness_gate_reason_code_counts_are_deterministic_and_positive():
    report = _readiness_report(
        screening_report=_screening_report(
            health_status="watch",
            reason_codes=(
                "latest_paper_autonomous_screening_decision_support_gate_watch",
            ),
        ),
        allocation_report=_allocation_report(
            gate_status="watch",
            reason_codes=("latest_allocation_proposal_db_history_health_trend_watch",),
        ),
        investment_ledger_report=_ledger_report(
            gate_status="blocked",
            reason_codes=(
                "latest_paper_autonomous_investment_ledger_db_history_health_trend_blocked",
            ),
        ),
    )

    assert report.reason_code_counts == (
        _api().PaperAutonomousReadinessGateReasonCodeCount(
            "allocation_proposal_db_history_health_trend_gate_watch",
            1,
        ),
        _api().PaperAutonomousReadinessGateReasonCodeCount(
            "investment_ledger_db_history_health_trend_gate_blocked",
            1,
        ),
        _api().PaperAutonomousReadinessGateReasonCodeCount(
            "screening_decision_support_gate_db_history_health_watch",
            1,
        ),
    )
    assert report.reason_codes == tuple(row.reason_code for row in report.reason_code_counts)
    assert all(row.report_count > 0 for row in report.reason_code_counts)


def test_readiness_gate_dataclasses_are_frozen_and_validate_hard_flags():
    api = _api()
    config = api.PaperAutonomousReadinessGateConfig()
    source_status = api.PaperAutonomousReadinessGateSourceStatus(
        source_name="screening_decision_support_gate_db_history_health",
        status="pass",
        recommended_next_step=(
            "allow_paper_autonomous_screening_decision_support_gate_history_review"
        ),
        generated_at=GENERATED_AT,
        config_version="screening-health-v0",
    )
    reason_count = api.PaperAutonomousReadinessGateReasonCodeCount(
        "paper_autonomous_readiness_gate_passed",
        1,
    )
    report = _readiness_report()

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_status.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason_count.report_count = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.readiness_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config .*paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="source status .*report_only"):
        replace(source_status, report_only=False)
    with pytest.raises(ValueError, match="reason code count .*readonly"):
        replace(reason_count, readonly=False)
    with pytest.raises(ValueError, match="readiness report .*paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="source_config_versions must match source_statuses"):
        replace(
            report,
            source_config_versions=(
                ("screening_decision_support_gate_db_history_health", "other-v0"),
                (
                    "allocation_proposal_db_history_health_trend_gate",
                    "allocation-trend-gate-v0",
                ),
                (
                    "investment_ledger_db_history_health_trend_gate",
                    "ledger-trend-gate-v0",
                ),
            ),
        )


def test_readiness_gate_rejects_subclassed_and_wrong_source_types():
    api = _api()

    with pytest.raises(TypeError, match="does not support subclassing"):

        class ConfigSubclass(api.PaperAutonomousReadinessGateConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class ReportSubclass(api.PaperAutonomousReadinessGateReport):
            pass

    with pytest.raises(ValueError, match="screening_report must be a"):
        api.build_paper_autonomous_readiness_gate_report(
            object(),
            _allocation_report(),
            _ledger_report(),
            config=api.PaperAutonomousReadinessGateConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="allocation_report must be a"):
        api.build_paper_autonomous_readiness_gate_report(
            _screening_report(),
            object(),
            _ledger_report(),
            config=api.PaperAutonomousReadinessGateConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="investment_ledger_report must be a"):
        api.build_paper_autonomous_readiness_gate_report(
            _screening_report(),
            _allocation_report(),
            object(),
            config=api.PaperAutonomousReadinessGateConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="strategy_cycle_history_gate_report must be a"):
        api.build_paper_autonomous_readiness_gate_report(
            _screening_report(),
            _allocation_report(),
            _ledger_report(),
            config=api.PaperAutonomousReadinessGateConfig(),
            generated_at=GENERATED_AT,
            strategy_cycle_history_gate_report=object(),
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_readiness_gate_rejects_source_reports_without_hard_flags(flag_name: str):
    source_report = _allocation_report()
    object.__setattr__(source_report, flag_name, False)

    with pytest.raises(ValueError, match=f"allocation_report must be {flag_name}"):
        _readiness_report(allocation_report=source_report)


def test_readiness_gate_source_code_has_no_unsafe_surface():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_autonomous_readiness_gate.py"
    )
    source = module_path.read_text()
    tree = ast.parse(source)
    forbidden = {
        "auth",
        "account",
        "cancel",
        "environ",
        "live",
        "order",
        "psycopg",
        "sign",
        "submit",
        "supabase",
        "trade",
        "wallet",
    }
    module_docstring = ast.get_docstring(tree)

    imports: list[str] = []
    names: list[str] = []
    calls: list[str] = []
    attrs: list[str] = []
    constants: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attrs.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value != module_docstring:
                constants.append(node.value)

    haystacks = {
        "import": imports,
        "name": names,
        "call": calls,
        "attribute": attrs,
        "constant": constants,
    }
    for label, values in haystacks.items():
        for value in values:
            lowered = value.lower()
            for word in forbidden:
                assert word not in lowered, f"{label} {value!r} contains {word!r}"
