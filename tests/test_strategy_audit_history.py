from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_audit_history import (
    PaperStrategyRiskAuditHistoryConfig,
    PaperStrategyRiskAuditHistoryGateStatusSummary,
    PaperStrategyRiskAuditHistoryReport,
    PaperStrategyRiskAuditHistoryStatusRow,
    build_paper_strategy_risk_audit_history_report,
)
from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
)


GENERATED_AT = datetime(2026, 6, 17, 15, 0, tzinfo=UTC)
ALL_GATE_NAMES = (
    "paper_history",
    "settlement_evidence",
    "forecast_quality",
    "cost_discipline",
    "nav_drawdown",
    "open_exposure",
)
ALL_GATE_NAMES_WITH_SETTLEMENT_NAV_RISK = ALL_GATE_NAMES + ("settlement_nav_risk",)


def _audit_report(status: str, generated_at: datetime) -> PaperStrategyRiskAuditReport:
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
        gate_results=(
            PaperStrategyRiskAuditGateResult("paper_history", gate_status, "m"),
            PaperStrategyRiskAuditGateResult(
                "settlement_evidence",
                gate_status,
                "m",
            ),
            PaperStrategyRiskAuditGateResult("forecast_quality", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("cost_discipline", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("nav_drawdown", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("open_exposure", gate_status, "m"),
        ),
    )


def _seven_gate_blocked_audit_report(
    generated_at: datetime,
) -> PaperStrategyRiskAuditReport:
    return PaperStrategyRiskAuditReport(
        generated_at=generated_at,
        config_version="strategy-risk-audit-v0",
        status="blocked_by_risk",
        gate_count=7,
        pass_count=0,
        fail_count=7,
        incomplete_count=0,
        gate_results=tuple(
            PaperStrategyRiskAuditGateResult(gate_name, "fail", "m")
            for gate_name in ALL_GATE_NAMES_WITH_SETTLEMENT_NAV_RISK
        ),
    )


def _seven_gate_ready_audit_report(
    generated_at: datetime,
) -> PaperStrategyRiskAuditReport:
    return PaperStrategyRiskAuditReport(
        generated_at=generated_at,
        config_version="strategy-risk-audit-v0",
        status="audit_ready",
        gate_count=7,
        pass_count=7,
        fail_count=0,
        incomplete_count=0,
        gate_results=tuple(
            PaperStrategyRiskAuditGateResult(gate_name, "pass", "m")
            for gate_name in ALL_GATE_NAMES_WITH_SETTLEMENT_NAV_RISK
        ),
    )


def _config() -> PaperStrategyRiskAuditHistoryConfig:
    return PaperStrategyRiskAuditHistoryConfig(
        config_version="strategy-audit-history-v0",
    )


def _history_report(
    *reports: PaperStrategyRiskAuditReport,
) -> PaperStrategyRiskAuditHistoryReport:
    return build_paper_strategy_risk_audit_history_report(
        reports,
        config=_config(),
        generated_at=GENERATED_AT,
    )


def _replace_status_row(
    history: PaperStrategyRiskAuditHistoryReport,
    audit_status: str,
    **changes: object,
) -> tuple[PaperStrategyRiskAuditHistoryStatusRow, ...]:
    return tuple(
        replace(row, **changes) if row.audit_status == audit_status else row
        for row in history.status_rows
    )


def _replace_gate_status_summary(
    history: PaperStrategyRiskAuditHistoryReport,
    gate_name: str,
    gate_status: str,
    **changes: object,
) -> tuple[PaperStrategyRiskAuditHistoryGateStatusSummary, ...]:
    return tuple(
        replace(row, **changes)
        if row.gate_name == gate_name and row.gate_status == gate_status
        else row
        for row in history.gate_status_summaries
    )


def test_strategy_audit_history_summarizes_statuses_and_latest_gates():
    reports = (
        _audit_report("audit_ready", datetime(2026, 6, 17, 12, 0, tzinfo=UTC)),
        _audit_report(
            "insufficient_evidence",
            datetime(2026, 6, 17, 13, 0, tzinfo=UTC),
        ),
        _audit_report(
            "blocked_by_risk",
            datetime(2026, 6, 17, 14, 0, tzinfo=UTC),
        ),
    )

    history = build_paper_strategy_risk_audit_history_report(
        reports,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert history.status == "latest_blocked_by_risk"
    assert history.audit_report_count == 3
    assert history.audit_ready_count == 1
    assert history.insufficient_evidence_count == 1
    assert history.blocked_by_risk_count == 1
    assert history.latest_audit_status == "blocked_by_risk"
    assert history.first_audit_generated_at == reports[0].generated_at
    assert history.latest_audit_generated_at == reports[-1].generated_at
    assert history.consecutive_non_ready_count == 2
    assert history.consecutive_blocked_by_risk_count == 1
    assert history.consecutive_insufficient_evidence_count == 0
    assert history.latest_failed_gate_names == (
        "paper_history",
        "settlement_evidence",
        "forecast_quality",
        "cost_discipline",
        "nav_drawdown",
        "open_exposure",
    )
    assert history.latest_incomplete_gate_names == ()
    rows = {row.audit_status: row for row in history.status_rows}
    assert rows["audit_ready"].audit_count == 1
    assert rows["audit_ready"].audit_ratio == Decimal("0.3333")
    assert rows["insufficient_evidence"].audit_count == 1
    assert rows["blocked_by_risk"].audit_count == 1
    gate_rows = {
        (row.gate_name, row.gate_status): row
        for row in history.gate_status_summaries
    }
    assert gate_rows[("nav_drawdown", "pass")].audit_count == 1
    assert gate_rows[("nav_drawdown", "incomplete")].audit_count == 1
    assert gate_rows[("nav_drawdown", "fail")].audit_count == 1
    assert gate_rows[("settlement_nav_risk", "pass")].audit_count == 0
    assert gate_rows[("settlement_nav_risk", "fail")].audit_count == 0
    assert gate_rows[("settlement_nav_risk", "incomplete")].audit_count == 0
    assert history.paper_only is True
    assert history.report_only is True


def test_strategy_audit_history_empty_input_is_report_only():
    history = build_paper_strategy_risk_audit_history_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert history.status == "empty_audit_history"
    assert history.audit_report_count == 0
    assert history.audit_ready_count == 0
    assert history.insufficient_evidence_count == 0
    assert history.blocked_by_risk_count == 0
    assert history.latest_audit_status is None
    assert history.first_audit_generated_at is None
    assert history.latest_audit_generated_at is None
    assert history.latest_failed_gate_names == ()
    assert history.latest_incomplete_gate_names == ()
    assert all(row.audit_count == 0 for row in history.status_rows)
    assert all(row.audit_ratio is None for row in history.status_rows)
    assert all(row.audit_count == 0 for row in history.gate_status_summaries)
    assert all(row.audit_ratio is None for row in history.gate_status_summaries)
    assert history.paper_only is True
    assert history.report_only is True


def test_strategy_audit_history_latest_ready_resets_non_ready_streaks():
    reports = (
        _audit_report(
            "blocked_by_risk",
            datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
        ),
        _audit_report("audit_ready", datetime(2026, 6, 17, 13, 0, tzinfo=UTC)),
    )

    history = build_paper_strategy_risk_audit_history_report(
        reports,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert history.status == "latest_audit_ready"
    assert history.latest_audit_status == "audit_ready"
    assert history.consecutive_non_ready_count == 0
    assert history.consecutive_blocked_by_risk_count == 0
    assert history.consecutive_insufficient_evidence_count == 0
    assert history.latest_failed_gate_names == ()
    assert history.latest_incomplete_gate_names == ()


def test_strategy_audit_history_latest_insufficient_evidence_tracks_incomplete_gates_and_streak():
    reports = (
        _audit_report("audit_ready", datetime(2026, 6, 17, 12, 0, tzinfo=UTC)),
        _audit_report(
            "insufficient_evidence",
            datetime(2026, 6, 17, 13, 0, tzinfo=UTC),
        ),
        _audit_report(
            "insufficient_evidence",
            datetime(2026, 6, 17, 14, 0, tzinfo=UTC),
        ),
    )

    history = _history_report(*reports)

    assert history.status == "latest_insufficient_evidence"
    assert history.latest_audit_status == "insufficient_evidence"
    assert history.consecutive_non_ready_count == 2
    assert history.consecutive_blocked_by_risk_count == 0
    assert history.consecutive_insufficient_evidence_count == 2
    assert history.latest_failed_gate_names == ()
    assert history.latest_incomplete_gate_names == ALL_GATE_NAMES


def test_strategy_audit_history_accepts_optional_settlement_nav_risk_gate() -> None:
    history = _history_report(
        _seven_gate_blocked_audit_report(
            datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
        ),
    )

    gate_rows = {
        (row.gate_name, row.gate_status): row
        for row in history.gate_status_summaries
    }
    assert history.latest_fail_count == 7
    assert "settlement_nav_risk" in history.latest_failed_gate_names
    assert gate_rows[("settlement_nav_risk", "fail")].audit_count == 1
    assert gate_rows[("settlement_nav_risk", "pass")].audit_count == 0
    assert gate_rows[("settlement_nav_risk", "incomplete")].audit_count == 0


def test_strategy_audit_history_validates_latest_counts_against_latest_report_gate_count() -> None:
    history = _history_report(
        _seven_gate_blocked_audit_report(
            datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
        ),
    )

    with pytest.raises(ValueError):
        replace(history, latest_fail_count=6)


def test_strategy_audit_history_validates_all_pass_optional_latest_gate_count() -> None:
    history = _history_report(
        _seven_gate_ready_audit_report(
            datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
        ),
    )

    assert history.latest_pass_count == 7
    with pytest.raises(ValueError):
        replace(history, latest_pass_count=6)


def test_strategy_audit_history_rejects_invalid_inputs():
    with pytest.raises(ValueError, match="audit_reports must be a list or tuple"):
        build_paper_strategy_risk_audit_history_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="audit_reports must be a list or tuple"):
        build_paper_strategy_risk_audit_history_report(
            "not reports",
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="audit_reports must contain"):
        build_paper_strategy_risk_audit_history_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_strategy_audit_history_rejects_invalid_config_and_generated_at():
    with pytest.raises(ValueError, match="config must be"):
        build_paper_strategy_risk_audit_history_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_paper_strategy_risk_audit_history_report(
            (),
            config=_config(),
            generated_at=object(),  # type: ignore[arg-type]
        )


def test_strategy_audit_history_report_rejects_status_inconsistent_with_latest_audit_status():
    history = _history_report(
        _audit_report("blocked_by_risk", datetime(2026, 6, 17, 12, 0, tzinfo=UTC)),
    )

    with pytest.raises(ValueError):
        replace(
            history,
            status="latest_audit_ready",
            latest_audit_status="blocked_by_risk",
        )


def test_strategy_audit_history_report_empty_history_rejects_latest_values():
    history = _history_report()
    invalid_cases = (
        ("latest_pass_count", 1),
        ("latest_fail_count", 1),
        ("latest_incomplete_count", 1),
        ("consecutive_non_ready_count", 1),
        ("consecutive_blocked_by_risk_count", 1),
        ("consecutive_insufficient_evidence_count", 1),
        ("latest_failed_gate_names", ("paper_history",)),
        ("latest_incomplete_gate_names", ("paper_history",)),
    )

    for field_name, value in invalid_cases:
        with pytest.raises(ValueError):
            replace(history, **{field_name: value})


def test_strategy_audit_history_report_rejects_status_row_ratio_mismatch():
    history = _history_report(
        _audit_report("audit_ready", datetime(2026, 6, 17, 12, 0, tzinfo=UTC)),
    )
    rows = _replace_status_row(
        history,
        "audit_ready",
        audit_ratio=Decimal("0.5000"),
    )

    with pytest.raises(ValueError):
        replace(history, status_rows=rows)


def test_strategy_audit_history_report_empty_history_rejects_status_row_ratios():
    history = _history_report()
    rows = _replace_status_row(
        history,
        "audit_ready",
        audit_ratio=Decimal("0.0000"),
    )

    with pytest.raises(ValueError):
        replace(history, status_rows=rows)


def test_strategy_audit_history_report_rejects_gate_status_counts_that_do_not_sum_to_total():
    history = _history_report(
        _audit_report("audit_ready", datetime(2026, 6, 17, 12, 0, tzinfo=UTC)),
    )
    rows = _replace_gate_status_summary(
        history,
        "paper_history",
        "fail",
        audit_count=1,
        audit_ratio=Decimal("1.0000"),
    )

    with pytest.raises(ValueError):
        replace(history, gate_status_summaries=rows)


def test_strategy_audit_history_report_rejects_gate_status_ratio_mismatch():
    history = _history_report(
        _audit_report("audit_ready", datetime(2026, 6, 17, 12, 0, tzinfo=UTC)),
    )
    rows = _replace_gate_status_summary(
        history,
        "paper_history",
        "pass",
        audit_ratio=Decimal("0.5000"),
    )

    with pytest.raises(ValueError):
        replace(history, gate_status_summaries=rows)
