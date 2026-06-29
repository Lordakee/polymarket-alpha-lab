from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_strategy_risk_audit_history_gate import (
    DEFAULT_PAPER_STRATEGY_RISK_AUDIT_HISTORY_GATE_CONFIG_VERSION,
    PaperStrategyRiskAuditHistoryGateConfig,
    PaperStrategyRiskAuditHistoryGateReasonCodeCount,
    PaperStrategyRiskAuditHistoryGateReport,
    build_paper_strategy_risk_audit_history_gate_report,
)
from polymarket_alpha_lab.strategy_audit_history import (
    PaperStrategyRiskAuditHistoryConfig,
    PaperStrategyRiskAuditHistoryReport,
    build_paper_strategy_risk_audit_history_report,
)
from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
)


GENERATED_AT = datetime(2026, 6, 29, 16, 0, tzinfo=UTC)
ALL_GATE_NAMES = (
    "paper_history",
    "settlement_evidence",
    "forecast_quality",
    "cost_discipline",
    "nav_drawdown",
    "open_exposure",
)
SETTLEMENT_GATE_NAMES = ALL_GATE_NAMES + ("settlement_nav_risk",)


class PaperStrategyRiskAuditHistoryGateConfigSubclass(
    PaperStrategyRiskAuditHistoryGateConfig,
):
    pass


class PaperStrategyRiskAuditHistoryGateReasonCodeCountSubclass(
    PaperStrategyRiskAuditHistoryGateReasonCodeCount,
):
    pass


class PaperStrategyRiskAuditHistoryGateReportSubclass(
    PaperStrategyRiskAuditHistoryGateReport,
):
    pass


class PaperStrategyRiskAuditHistoryReportSubclass(PaperStrategyRiskAuditHistoryReport):
    pass


def _audit_report(
    status: str,
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
            PaperStrategyRiskAuditGateResult(gate_name, gate_status, "message")
            for gate_name in ALL_GATE_NAMES
        ),
    )


def _settlement_audit_report(
    status: str,
    generated_at: datetime,
) -> PaperStrategyRiskAuditReport:
    status_map = {
        "audit_ready": ("pass", 7, 0, 0),
        "insufficient_evidence": ("incomplete", 0, 0, 7),
        "blocked_by_risk": ("fail", 0, 7, 0),
    }
    gate_status, pass_count, fail_count, incomplete_count = status_map[status]
    return PaperStrategyRiskAuditReport(
        generated_at=generated_at,
        config_version="strategy-risk-audit-v0",
        status=status,
        gate_count=7,
        pass_count=pass_count,
        fail_count=fail_count,
        incomplete_count=incomplete_count,
        gate_results=tuple(
            PaperStrategyRiskAuditGateResult(gate_name, gate_status, "message")
            for gate_name in SETTLEMENT_GATE_NAMES
        ),
    )


def _history_config() -> PaperStrategyRiskAuditHistoryConfig:
    return PaperStrategyRiskAuditHistoryConfig(
        config_version="strategy-risk-audit-history-v0",
    )


def _history_report(
    *statuses: str,
    latest_generated_at: datetime | None = None,
) -> PaperStrategyRiskAuditHistoryReport:
    latest_generated_at = latest_generated_at or (GENERATED_AT - timedelta(hours=1))
    reports = tuple(
        _audit_report(
            status,
            latest_generated_at - timedelta(hours=len(statuses) - index - 1),
        )
        for index, status in enumerate(statuses)
    )
    return build_paper_strategy_risk_audit_history_report(
        reports,
        config=_history_config(),
        generated_at=GENERATED_AT,
    )


def _gate_report(
    history: PaperStrategyRiskAuditHistoryReport,
    *,
    config: PaperStrategyRiskAuditHistoryGateConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperStrategyRiskAuditHistoryGateReport:
    return build_paper_strategy_risk_audit_history_gate_report(
        history,
        config=config or PaperStrategyRiskAuditHistoryGateConfig(),
        generated_at=generated_at,
    )


def test_strategy_risk_audit_history_gate_preserves_settlement_nav_risk_gate_names() -> None:
    history = build_paper_strategy_risk_audit_history_report(
        (_settlement_audit_report("blocked_by_risk", GENERATED_AT - timedelta(hours=1)),),
        config=_history_config(),
        generated_at=GENERATED_AT,
    )

    gate = _gate_report(history)

    assert gate.gate_status == "blocked"
    assert gate.latest_fail_count == 7
    assert gate.latest_failed_gate_names == SETTLEMENT_GATE_NAMES
    assert "settlement_nav_risk" in gate.latest_failed_gate_names


def test_strategy_risk_audit_history_gate_passes_fresh_ready_history() -> None:
    history = _history_report("audit_ready")

    gate = _gate_report(history)

    assert gate.generated_at == GENERATED_AT
    assert (
        gate.config_version
        == DEFAULT_PAPER_STRATEGY_RISK_AUDIT_HISTORY_GATE_CONFIG_VERSION
    )
    assert gate.source_config_version == history.config_version
    assert gate.source_generated_at == history.generated_at
    assert gate.gate_status == "pass"
    assert gate.recommended_next_step == "allow_strategy_risk_audit_history_gate"
    assert gate.reason_codes == ("paper_strategy_risk_audit_history_gate_passed",)
    assert gate.reason_code_counts == (
        PaperStrategyRiskAuditHistoryGateReasonCodeCount(
            "paper_strategy_risk_audit_history_gate_passed",
            1,
        ),
    )
    assert gate.source_history_status == "latest_audit_ready"
    assert gate.source_report_count == history.audit_report_count
    assert gate.latest_source_generated_at == history.latest_audit_generated_at
    assert gate.latest_source_age_seconds == 3600
    assert gate.latest_audit_status == "audit_ready"
    assert gate.latest_pass_count == history.latest_pass_count
    assert gate.latest_fail_count == history.latest_fail_count
    assert gate.latest_incomplete_count == history.latest_incomplete_count
    assert gate.consecutive_non_ready_count == history.consecutive_non_ready_count
    assert (
        gate.consecutive_blocked_by_risk_count
        == history.consecutive_blocked_by_risk_count
    )
    assert (
        gate.consecutive_insufficient_evidence_count
        == history.consecutive_insufficient_evidence_count
    )
    assert gate.latest_failed_gate_names == history.latest_failed_gate_names
    assert gate.latest_incomplete_gate_names == history.latest_incomplete_gate_names
    assert history.paper_only is True
    assert history.report_only is True
    assert not hasattr(history, "readonly")
    assert gate.paper_only is True
    assert gate.report_only is True
    assert gate.readonly is True
    assert all(
        row.paper_only and row.report_only and row.readonly
        for row in gate.reason_code_counts
    )


def test_strategy_risk_audit_history_gate_blocks_latest_blocked_by_risk() -> None:
    gate = _gate_report(_history_report("blocked_by_risk"))

    assert gate.gate_status == "blocked"
    assert gate.recommended_next_step == "block_strategy_risk_audit_history_gate"
    assert gate.reason_codes == (
        "source_strategy_risk_audit_history_blocked_by_risk",
    )
    assert gate.reason_code_counts == (
        PaperStrategyRiskAuditHistoryGateReasonCodeCount(
            "source_strategy_risk_audit_history_blocked_by_risk",
            1,
        ),
    )
    assert gate.source_history_status == "latest_blocked_by_risk"
    assert gate.latest_audit_status == "blocked_by_risk"
    assert gate.latest_failed_gate_names == ALL_GATE_NAMES


def test_strategy_risk_audit_history_gate_watches_latest_insufficient_evidence() -> None:
    gate = _gate_report(_history_report("insufficient_evidence"))

    assert gate.gate_status == "watch"
    assert gate.recommended_next_step == "throttle_strategy_risk_audit_history_gate"
    assert gate.reason_codes == (
        "source_strategy_risk_audit_history_insufficient_evidence",
    )
    assert gate.source_history_status == "latest_insufficient_evidence"
    assert gate.latest_audit_status == "insufficient_evidence"
    assert gate.latest_incomplete_gate_names == ALL_GATE_NAMES


def test_strategy_risk_audit_history_gate_blocks_empty_audit_history() -> None:
    gate = _gate_report(_history_report())

    assert gate.gate_status == "blocked"
    assert gate.recommended_next_step == "block_strategy_risk_audit_history_gate"
    assert gate.reason_codes == (
        "missing_latest_strategy_risk_audit_history_timestamp",
    )
    assert gate.source_history_status == "empty_audit_history"
    assert gate.source_report_count == 0
    assert gate.latest_source_generated_at is None
    assert gate.latest_source_age_seconds is None
    assert gate.latest_audit_status is None
    assert gate.latest_pass_count == 0
    assert gate.latest_fail_count == 0
    assert gate.latest_incomplete_count == 0


def test_strategy_risk_audit_history_gate_blocks_missing_latest_timestamp() -> None:
    history = _history_report("audit_ready")
    object.__setattr__(history, "latest_audit_generated_at", None)

    gate = _gate_report(history)

    assert gate.gate_status == "blocked"
    assert gate.latest_source_generated_at is None
    assert gate.latest_source_age_seconds is None
    assert gate.reason_codes == (
        "missing_latest_strategy_risk_audit_history_timestamp",
    )


def test_strategy_risk_audit_history_gate_watches_stale_latest_timestamp() -> None:
    history = _history_report(
        "audit_ready",
        latest_generated_at=GENERATED_AT - timedelta(seconds=86_401),
    )

    gate = _gate_report(history)

    assert gate.gate_status == "watch"
    assert gate.recommended_next_step == "throttle_strategy_risk_audit_history_gate"
    assert gate.source_history_status == "latest_audit_ready"
    assert gate.latest_source_age_seconds == 86_401
    assert gate.reason_codes == ("stale_strategy_risk_audit_history",)


def test_strategy_risk_audit_history_gate_status_priority_blocks_over_stale() -> None:
    history = _history_report(
        "blocked_by_risk",
        latest_generated_at=GENERATED_AT - timedelta(seconds=86_401),
    )

    gate = _gate_report(history)

    assert gate.gate_status == "blocked"
    assert gate.reason_codes == (
        "source_strategy_risk_audit_history_blocked_by_risk",
        "stale_strategy_risk_audit_history",
    )
    assert tuple(row.report_count for row in gate.reason_code_counts) == (1, 1)


def test_strategy_risk_audit_history_gate_rejects_future_latest_timestamp() -> None:
    history = _history_report(
        "audit_ready",
        latest_generated_at=GENERATED_AT + timedelta(seconds=1),
    )

    with pytest.raises(ValueError, match="future"):
        _gate_report(history)


def test_strategy_risk_audit_history_gate_rejects_subclasses() -> None:
    history = _history_report("audit_ready")

    with pytest.raises(ValueError, match="config"):
        PaperStrategyRiskAuditHistoryGateConfigSubclass()
    with pytest.raises(ValueError, match="reason"):
        PaperStrategyRiskAuditHistoryGateReasonCodeCountSubclass(
            "paper_strategy_risk_audit_history_gate_passed",
            1,
        )
    with pytest.raises(ValueError, match="report"):
        PaperStrategyRiskAuditHistoryGateReportSubclass(**_gate_report(history).__dict__)

    source_subclass = PaperStrategyRiskAuditHistoryReportSubclass(**history.__dict__)
    with pytest.raises(ValueError, match="source history"):
        _gate_report(source_subclass)


def test_strategy_risk_audit_history_gate_outputs_are_frozen_and_validated() -> None:
    gate = _gate_report(_history_report("audit_ready"))

    with pytest.raises(FrozenInstanceError):
        gate.gate_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        gate.reason_code_counts[0].report_count = 2  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        replace(gate, config_version=" gate-v0 ")
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(gate, recommended_next_step="block_strategy_risk_audit_history_gate")
    with pytest.raises(ValueError, match="latest_source_age_seconds"):
        replace(gate, latest_source_generated_at=None)
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(gate, reason_code_counts=(object(),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(gate, reason_codes=("stale_strategy_risk_audit_history",))
    with pytest.raises(ValueError, match="readonly"):
        replace(gate, readonly=False)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("config_version", ""),
        ("config_version", " gate-v0 "),
        ("max_latest_age_seconds", 0),
        ("max_latest_age_seconds", True),
        ("paper_only", False),
        ("report_only", False),
        ("readonly", False),
    ),
)
def test_strategy_risk_audit_history_gate_config_validates_inputs(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        PaperStrategyRiskAuditHistoryGateConfig(**{field_name: bad_value})


def test_strategy_risk_audit_history_gate_revalidates_reason_rows() -> None:
    with pytest.raises(ValueError, match="reason_code"):
        PaperStrategyRiskAuditHistoryGateReasonCodeCount("unknown_reason", 1)
    with pytest.raises(ValueError, match="report_count"):
        PaperStrategyRiskAuditHistoryGateReasonCodeCount(
            "paper_strategy_risk_audit_history_gate_passed",
            0,
        )
    with pytest.raises(ValueError, match="paper_only"):
        PaperStrategyRiskAuditHistoryGateReasonCodeCount(
            "paper_strategy_risk_audit_history_gate_passed",
            1,
            paper_only=False,
        )


def test_strategy_risk_audit_history_gate_rejects_unsafe_source_flags() -> None:
    history = _history_report("audit_ready")
    object.__setattr__(history, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        _gate_report(history)

    history = _history_report("audit_ready")
    object.__setattr__(history, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        _gate_report(history)

    history = _history_report("audit_ready")
    object.__setattr__(history, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        _gate_report(history)

    history = _history_report("audit_ready")
    object.__setattr__(history, "readonly", True)
    assert _gate_report(history).readonly is True


def test_strategy_risk_audit_history_gate_module_scope_stays_pure_readonly() -> None:
    source = Path(
        "src/polymarket_alpha_lab/paper_strategy_risk_audit_history_gate.py",
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
        "order",
        "wallet",
        "auth",
    ):
        assert banned_term not in source.lower()
