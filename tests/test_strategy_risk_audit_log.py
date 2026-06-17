import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
)
from polymarket_alpha_lab.strategy_risk_audit_log import PaperStrategyRiskAuditLog


GENERATED_AT = datetime(2026, 6, 17, 14, 0, tzinfo=UTC)


def _report(status="audit_ready") -> PaperStrategyRiskAuditReport:
    statuses = {
        "audit_ready": ("pass", 6, 0, 0),
        "insufficient_evidence": ("incomplete", 0, 0, 6),
        "blocked_by_risk": ("fail", 0, 6, 0),
    }
    gate_status, pass_count, fail_count, incomplete_count = statuses[status]
    return PaperStrategyRiskAuditReport(
        generated_at=GENERATED_AT,
        config_version="strategy-risk-audit-v0",
        status=status,
        gate_count=6,
        pass_count=pass_count,
        fail_count=fail_count,
        incomplete_count=incomplete_count,
        gate_results=(
            PaperStrategyRiskAuditGateResult(
                "paper_history",
                gate_status,
                "mature",
                observed_value="cycle_count=25",
                threshold="min_cycle_count=20",
            ),
            PaperStrategyRiskAuditGateResult(
                "settlement_evidence",
                gate_status,
                "settled",
                observed_value=12,
                threshold=10,
            ),
            PaperStrategyRiskAuditGateResult(
                "forecast_quality",
                gate_status,
                "calibrated",
                observed_value="forecast_probability_quality_status=pass",
                threshold="forecast_probability_quality_status=pass",
            ),
            PaperStrategyRiskAuditGateResult(
                "cost_discipline",
                gate_status,
                "costs",
                observed_value="trade_count=25",
                threshold="min_cost_audit_trade_count=20",
            ),
            PaperStrategyRiskAuditGateResult(
                "nav_drawdown",
                gate_status,
                "drawdown",
                observed_value=Decimal("0.010000"),
                threshold=Decimal("0.050000"),
            ),
            PaperStrategyRiskAuditGateResult(
                "open_exposure",
                gate_status,
                "exposure",
                observed_value="open_position_count=1",
                threshold="max_no_exit_depth_count=0",
            ),
        ),
    )


def test_strategy_risk_audit_log_appends_jsonl_report(tmp_path):
    path = tmp_path / "nested" / "strategy-audits.jsonl"
    report = _report()

    PaperStrategyRiskAuditLog(path).append(report)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["generated_at"] == "2026-06-17T14:00:00+00:00"
    assert payload["config_version"] == "strategy-risk-audit-v0"
    assert payload["status"] == "audit_ready"
    assert payload["gate_count"] == 6
    assert payload["pass_count"] == 6
    assert payload["fail_count"] == 0
    assert payload["incomplete_count"] == 0
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert len(payload["gate_results"]) == 6
    assert payload["gate_results"][4]["gate_name"] == "nav_drawdown"
    assert payload["gate_results"][4]["observed_value"] == "0.010000"
    assert payload["gate_results"][4]["threshold"] == "0.050000"


def test_strategy_risk_audit_log_round_trips_reports_and_skips_blank_lines(tmp_path):
    path = tmp_path / "strategy-audits.jsonl"
    first = _report("audit_ready")
    second = _report("blocked_by_risk")

    log = PaperStrategyRiskAuditLog(path)
    log.append(first)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n")
    log.append(second)

    assert PaperStrategyRiskAuditLog.read(path) == (first, second)


def test_strategy_risk_audit_log_preserves_numeric_strings_on_string_gates(tmp_path):
    path = tmp_path / "strategy-audits.jsonl"
    report = _report()
    gates = list(report.gate_results)
    gates[0] = PaperStrategyRiskAuditGateResult(
        "paper_history",
        "pass",
        "mature",
        observed_value="1",
        threshold="2",
    )
    report = PaperStrategyRiskAuditReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        gate_count=report.gate_count,
        pass_count=report.pass_count,
        fail_count=report.fail_count,
        incomplete_count=report.incomplete_count,
        gate_results=tuple(gates),
    )

    PaperStrategyRiskAuditLog(path).append(report)

    recovered = PaperStrategyRiskAuditLog.read(path)[0]
    assert recovered == report
    assert isinstance(recovered.gate_results[0].observed_value, str)
    assert isinstance(recovered.gate_results[0].threshold, str)
    assert isinstance(recovered.gate_results[4].observed_value, Decimal)
    assert isinstance(recovered.gate_results[4].threshold, Decimal)


def test_strategy_risk_audit_log_empty_file_returns_empty_tuple(tmp_path):
    path = tmp_path / "strategy-audits.jsonl"
    path.touch()

    assert PaperStrategyRiskAuditLog.read(path) == ()


def test_strategy_risk_audit_log_invalid_json_reports_line_number(tmp_path):
    path = tmp_path / "strategy-audits.jsonl"
    path.write_text("\nnot json\n", encoding="utf-8")

    with pytest.raises(ValueError, match="strategy risk audit log line 2"):
        PaperStrategyRiskAuditLog.read(path)


def test_strategy_risk_audit_log_creates_parent_directories_from_string_path(tmp_path):
    path = tmp_path / "nested" / "strategy-audits.jsonl"

    PaperStrategyRiskAuditLog(str(path)).append(_report())

    assert path.exists()


@pytest.mark.parametrize("bad_path", (object(), "", " "))
def test_strategy_risk_audit_log_rejects_invalid_paths(tmp_path, bad_path):
    if isinstance(bad_path, str):
        value = bad_path
    else:
        value = bad_path

    with pytest.raises(ValueError):
        PaperStrategyRiskAuditLog(value)  # type: ignore[arg-type]

    directory_path = tmp_path / "directory"
    directory_path.mkdir()
    with pytest.raises(ValueError, match="file path"):
        PaperStrategyRiskAuditLog(directory_path)

    blocked_parent = tmp_path / "not-a-directory"
    blocked_parent.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="parent"):
        PaperStrategyRiskAuditLog(blocked_parent / "strategy-audits.jsonl")


def test_strategy_risk_audit_log_rejects_invalid_append_without_creating_file(tmp_path):
    path = tmp_path / "strategy-audits.jsonl"

    with pytest.raises(ValueError, match="report must be a PaperStrategyRiskAuditReport"):
        PaperStrategyRiskAuditLog(path).append(object())  # type: ignore[arg-type]

    assert not path.exists()


def test_strategy_risk_audit_log_preserves_existing_file_when_serialization_fails(
    tmp_path,
):
    path = tmp_path / "strategy-audits.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    report = _report()
    gates = list(report.gate_results)
    object.__setattr__(gates[4], "threshold", Decimal("NaN"))
    object.__setattr__(report, "gate_results", tuple(gates))

    with pytest.raises(ValueError, match="finite"):
        PaperStrategyRiskAuditLog(path).append(report)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'
