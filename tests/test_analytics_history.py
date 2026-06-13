import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.analytics import PaperAnalyticsReport
from polymarket_alpha_lab.analytics_history import (
    PaperAnalyticsHistoryConfig,
    PaperAnalyticsHistoryGateResult,
    PaperAnalyticsHistoryLog,
    build_paper_analytics_history_report,
)
from tests.test_analytics import two_position_report


def shifted_report(
    report: PaperAnalyticsReport,
    *,
    days: int,
    exit_nav: Decimal | None = None,
) -> PaperAnalyticsReport:
    marked_at = report.marked_at + timedelta(days=days)
    performance = report.performance
    if exit_nav is not None:
        performance = replace(
            performance,
            exit_nav=exit_nav,
            exit_return_ratio=(
                (exit_nav - performance.starting_cash) / performance.starting_cash
            ).quantize(Decimal("0.0001")),
        )
    return replace(
        report,
        marked_at=marked_at,
        generated_at=report.generated_at + timedelta(days=days),
        performance=performance,
        drawdown_points=tuple(
            replace(point, marked_at=point.marked_at + timedelta(days=days))
            for point in report.drawdown_points
        ),
    )


def test_build_paper_analytics_history_report_summarizes_sorted_reports():
    _portfolio, _snapshot, first = two_position_report()
    second = shifted_report(first, days=7)
    third = shifted_report(first, days=35)

    report = build_paper_analytics_history_report(
        [third, first, second],
        config=PaperAnalyticsHistoryConfig(
            config_version="node4-test",
            max_exit_depth_shortfall_ratio=Decimal("0.5000"),
            max_breach_count=4,
        ),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        candidate_observation_count=250,
        simulated_trade_count=55,
        exited_trade_count=31,
    )

    assert report.generated_at == datetime(2026, 7, 20, tzinfo=UTC)
    assert report.config_version == "node4-test"
    assert report.first_marked_at == first.marked_at
    assert report.last_marked_at == third.marked_at
    assert report.report_count == 3
    assert report.candidate_observation_count == 250
    assert report.simulated_trade_count == 55
    assert report.exited_trade_count == 31
    assert report.forward_window_days == 35
    assert report.unique_market_count == 2
    assert report.unique_strategy_count == 2
    assert report.unique_risk_tag_count == 2
    assert report.latest_exit_nav == third.performance.exit_nav
    assert report.latest_total_exit_pnl == third.performance.total_exit_pnl
    assert report.max_drawdown == Decimal("0")
    assert report.max_drawdown_ratio == Decimal("0.0000")
    assert report.worst_exit_depth_shortfall_ratio == Decimal("0.2667")
    assert report.worst_no_exit_depth_cost_basis_ratio == Decimal("0.0000")
    assert report.worst_midpoint_nav_gap_ratio == Decimal("0.0008")
    assert report.largest_market_cost_basis_ratio == Decimal("0.0051")
    assert report.largest_risk_tag_cost_basis_ratio == Decimal("0.0061")
    assert report.max_breach_count == 4
    assert report.status == "paper_review_ready"
    assert [point.marked_at for point in report.trends] == [
        first.marked_at,
        second.marked_at,
        third.marked_at,
    ]


def test_build_paper_analytics_history_report_records_gate_results():
    _portfolio, _snapshot, source = two_position_report()

    report = build_paper_analytics_history_report(
        [source],
        config=PaperAnalyticsHistoryConfig(
            config_version="node4-test",
            max_exit_depth_shortfall_ratio=Decimal("0.1000"),
            max_breach_count=4,
        ),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        candidate_observation_count=10,
        simulated_trade_count=2,
        exited_trade_count=1,
    )

    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert list(gates) == [
        "data_integrity",
        "sample_size",
        "execution_cost_reality",
        "forecast_edge_quality",
        "risk_drawdown",
    ]
    assert gates["data_integrity"].status == "pass"
    assert gates["sample_size"].status == "fail"
    assert gates["execution_cost_reality"].status == "fail"
    assert gates["forecast_edge_quality"].status == "incomplete"
    assert gates["risk_drawdown"].status == "pass"
    assert "exit_depth_shortfall" in str(gates["execution_cost_reality"].observed_value)
    assert report.status == "blocked_by_risk"


def test_build_paper_analytics_history_report_marks_insufficient_evidence_when_only_sample_fails():
    _portfolio, _snapshot, source = two_position_report()

    report = build_paper_analytics_history_report(
        [source],
        config=PaperAnalyticsHistoryConfig(
            config_version="node4-test",
            max_exit_depth_shortfall_ratio=Decimal("0.5000"),
            max_breach_count=4,
        ),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        candidate_observation_count=10,
        simulated_trade_count=2,
        exited_trade_count=1,
    )

    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["sample_size"].status == "fail"
    assert gates["execution_cost_reality"].status == "pass"
    assert gates["risk_drawdown"].status == "pass"
    assert report.status == "insufficient_evidence"


def test_build_paper_analytics_history_report_computes_sequence_drawdown_from_exit_nav():
    _portfolio, _snapshot, source = two_position_report()
    first = shifted_report(source, days=0, exit_nav=Decimal("10000"))
    second = shifted_report(source, days=7, exit_nav=Decimal("9500"))
    third = shifted_report(source, days=14, exit_nav=Decimal("9900"))

    report = build_paper_analytics_history_report(
        [third, first, second],
        config=PaperAnalyticsHistoryConfig(
            config_version="node4-test",
            max_drawdown_ratio=Decimal("0.0100"),
            max_exit_depth_shortfall_ratio=Decimal("0.5000"),
            max_breach_count=4,
        ),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        candidate_observation_count=250,
        simulated_trade_count=55,
        exited_trade_count=31,
    )

    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert report.trends[0].drawdown == Decimal("0")
    assert report.trends[1].drawdown == Decimal("500")
    assert report.trends[1].drawdown_ratio == Decimal("0.0500")
    assert report.trends[2].drawdown == Decimal("100")
    assert report.max_drawdown == Decimal("500")
    assert report.max_drawdown_ratio == Decimal("0.0500")
    assert gates["risk_drawdown"].status == "fail"
    assert report.status == "blocked_by_risk"


def test_build_paper_analytics_history_report_handles_empty_input():
    report = build_paper_analytics_history_report(
        [],
        config=PaperAnalyticsHistoryConfig(config_version="node4-test"),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
    )

    assert report.report_count == 0
    assert report.first_marked_at is None
    assert report.last_marked_at is None
    assert report.forward_window_days == 0
    assert report.latest_exit_nav is None
    assert report.max_breach_count == 0
    assert report.trends == ()
    assert report.status == "incomplete_data"
    assert {gate.status for gate in report.gate_results} == {"incomplete"}


def test_build_paper_analytics_history_report_rejects_duplicate_marked_at():
    _portfolio, _snapshot, source = two_position_report()

    with pytest.raises(ValueError, match="duplicate.*marked_at"):
        build_paper_analytics_history_report(
            [source, source],
            config=PaperAnalyticsHistoryConfig(config_version="node4-test"),
            generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        )


def test_build_paper_analytics_history_report_rejects_bad_public_inputs():
    _portfolio, _snapshot, source = two_position_report()
    config = PaperAnalyticsHistoryConfig(config_version="node4-test")

    with pytest.raises(ValueError, match="reports"):
        build_paper_analytics_history_report(
            "not-reports",
            config=config,
            generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="candidate_observation_count"):
        build_paper_analytics_history_report(
            [source],
            config=config,
            generated_at=datetime(2026, 7, 20, tzinfo=UTC),
            candidate_observation_count=True,
        )
    with pytest.raises(ValueError, match="PaperAnalyticsReport"):
        build_paper_analytics_history_report(
            [object()],
            config=config,
            generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_analytics_history_report(
            [source],
            config=object(),
            generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_analytics_history_report(
            [source],
            config=config,
            generated_at=None,
        )


def test_analytics_history_config_rejects_non_decimal_thresholds():
    with pytest.raises(ValueError, match="max_drawdown_ratio"):
        PaperAnalyticsHistoryConfig(
            config_version="node4-test",
            max_drawdown_ratio=1,
        )


def test_analytics_history_gate_result_rejects_float_values():
    with pytest.raises(ValueError, match="observed_value"):
        PaperAnalyticsHistoryGateResult(
            gate_name="sample_size",
            status="fail",
            message="bad",
            observed_value=1.0,
        )
    with pytest.raises(ValueError, match="threshold"):
        PaperAnalyticsHistoryGateResult(
            gate_name="sample_size",
            status="fail",
            message="bad",
            threshold=1.0,
        )


def test_analytics_history_gate_result_rejects_unknown_status_and_gate_name():
    with pytest.raises(ValueError, match="gate_name"):
        PaperAnalyticsHistoryGateResult(
            gate_name="unknown",
            status="fail",
            message="bad",
        )
    with pytest.raises(ValueError, match="status"):
        PaperAnalyticsHistoryGateResult(
            gate_name="sample_size",
            status="unknown",
            message="bad",
        )


def test_analytics_history_report_rejects_unknown_status():
    _portfolio, _snapshot, source = two_position_report()
    report = build_paper_analytics_history_report(
        [source],
        config=PaperAnalyticsHistoryConfig(config_version="node4-test"),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="status"):
        replace(report, status="unknown")


def test_analytics_history_dataclasses_are_frozen():
    _portfolio, _snapshot, source = two_position_report()
    report = build_paper_analytics_history_report(
        [source],
        config=PaperAnalyticsHistoryConfig(config_version="node4-test"),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
    )

    with pytest.raises(FrozenInstanceError):
        report.report_count = 0
    with pytest.raises(FrozenInstanceError):
        report.trends[0].breach_count = 0


def test_paper_analytics_history_log_appends_jsonl_report(tmp_path):
    _portfolio, _snapshot, source = two_position_report()
    report = build_paper_analytics_history_report(
        [source],
        config=PaperAnalyticsHistoryConfig(config_version="node4-test"),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
    )
    log = PaperAnalyticsHistoryLog(path=tmp_path / "history.jsonl")

    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].startswith('{"candidate_observation_count"')
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["generated_at"] == "2026-07-20T00:00:00+00:00"
    assert stored["config_version"] == "node4-test"
    assert stored["latest_exit_nav"] == "9989.600"
    assert stored["gate_results"][0]["gate_name"] == "data_integrity"


def test_paper_analytics_history_log_appends_without_overwriting_and_creates_parent_dirs(
    tmp_path,
):
    _portfolio, _snapshot, source = two_position_report()
    report = build_paper_analytics_history_report(
        [source],
        config=PaperAnalyticsHistoryConfig(config_version="node4-test"),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
    )
    log = PaperAnalyticsHistoryLog(path=str(tmp_path / "nested" / "history.jsonl"))

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["generated_at"] == "2026-07-20T00:00:00+00:00"
    assert json.loads(lines[1])["generated_at"] == "2026-07-20T00:00:00+00:00"


def test_paper_analytics_history_log_rejects_invalid_public_input_before_file_creation(
    tmp_path,
):
    path = tmp_path / "history.jsonl"
    log = PaperAnalyticsHistoryLog(path=path)

    with pytest.raises(ValueError, match="PaperAnalyticsHistoryReport"):
        log.append(object())

    assert not path.exists()


def test_paper_analytics_history_log_preserves_existing_file_when_serialization_fails(
    tmp_path,
):
    _portfolio, _snapshot, source = two_position_report()
    report = build_paper_analytics_history_report(
        [source],
        config=PaperAnalyticsHistoryConfig(config_version="node4-test"),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
    )
    object.__setattr__(report.trends[0], "exit_nav", Decimal("NaN"))
    path = tmp_path / "history.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = PaperAnalyticsHistoryLog(path=path)

    with pytest.raises(ValueError, match="finite|JSON|serializable"):
        log.append(report)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'
