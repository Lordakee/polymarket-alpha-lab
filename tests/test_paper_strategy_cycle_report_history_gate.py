from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_strategy_cycle_report_history import (
    PaperStrategyCycleReportHistoryConfig,
    PaperStrategyCycleReportHistoryReport,
    build_paper_strategy_cycle_report_history_report,
)
from polymarket_alpha_lab.paper_strategy_cycle_report_history_gate import (
    DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_CONFIG_VERSION,
    PaperStrategyCycleReportHistoryGateConfig,
    PaperStrategyCycleReportHistoryGateReasonCodeCount,
    PaperStrategyCycleReportHistoryGateReport,
    build_paper_strategy_cycle_report_history_gate_report,
)
from polymarket_alpha_lab.project_screening import (
    PaperProjectScreeningCandidate,
    PaperProjectScreeningGateResult,
    PaperProjectScreeningQueueItem,
    PaperProjectScreeningReport,
)
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleReport


GENERATED_AT = datetime(2026, 6, 29, 16, 0, tzinfo=UTC)


class PaperStrategyCycleReportHistoryGateConfigSubclass(
    PaperStrategyCycleReportHistoryGateConfig,
):
    pass


class PaperStrategyCycleReportHistoryGateReasonCodeCountSubclass(
    PaperStrategyCycleReportHistoryGateReasonCodeCount,
):
    pass


class PaperStrategyCycleReportHistoryGateReportSubclass(
    PaperStrategyCycleReportHistoryGateReport,
):
    pass


class PaperStrategyCycleReportHistoryReportSubclass(PaperStrategyCycleReportHistoryReport):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _screening_report(
    *,
    generated_at: datetime,
    ready_count: int,
) -> PaperProjectScreeningReport:
    candidates = tuple(
        PaperProjectScreeningCandidate(
            market_slug=f"market-{index}",
            question=f"Will market {index} resolve yes?",
            source_status="paper_review_ready",
            scoring_side="yes",
            valid_depth=True,
            net_edge_per_share=d("0.020000"),
            total_cost_per_share=d("0.001000"),
            ask_size=d("100.000000"),
            edge_component=d("0.020000"),
            confidence_component=d("0.000000"),
            depth_component=d("0.000000"),
            spread_penalty=d("0.000000"),
            resolution_risk_penalty=d("0.000000"),
            cost_penalty=d("0.000000"),
            screening_score=d("0.020000"),
            screening_status="screening_ready",
            reason_codes=("source_paper_review_ready", "yes_depth_ready"),
        )
        for index in range(ready_count)
    )
    queue_items = tuple(
        PaperProjectScreeningQueueItem(
            queue_position=index,
            market_slug=candidate.market_slug,
            question=candidate.question,
            research_bucket="research_ready",
            screening_score=candidate.screening_score,
            source_status=candidate.source_status,
            scoring_side=candidate.scoring_side,
            reason_codes=candidate.reason_codes,
        )
        for index, candidate in enumerate(candidates, start=1)
    )
    return PaperProjectScreeningReport(
        generated_at=generated_at,
        config_version="project-screening-v1",
        candidate_count=ready_count,
        ready_count=ready_count,
        watch_count=0,
        defer_count=0,
        blocked_count=0,
        gate_results=(
            PaperProjectScreeningGateResult(
                "input_count",
                "pass",
                "source_reports_supplied",
                "source reports supplied",
                ready_count,
                1,
            ),
            PaperProjectScreeningGateResult(
                "candidate_types",
                "pass",
                "source_report_types_ready",
                "candidate types ready",
                ready_count,
                ready_count,
            ),
            PaperProjectScreeningGateResult(
                "unique_slugs",
                "pass",
                "unique_market_slugs",
                "unique market slugs",
                ready_count,
                ready_count,
            ),
            PaperProjectScreeningGateResult(
                "screenable_candidates",
                "pass",
                "screenable_candidates_ready",
                "screenable candidates ready",
                ready_count,
                1,
            ),
        ),
        candidates=candidates,
        queue_items=queue_items,
    )


def _cycle_report(
    *,
    generated_at: datetime,
    scan_market_count: int,
    snapshot_ready_count: int,
    blocked_counts: tuple[tuple[str, int], ...],
) -> PaperStrategyCycleReport:
    blocked_market_count = sum(count for _reason_code, count in blocked_counts)
    screening_report = (
        _screening_report(
            generated_at=generated_at,
            ready_count=snapshot_ready_count,
        )
        if snapshot_ready_count > 0
        else None
    )
    return PaperStrategyCycleReport(
        generated_at=generated_at,
        config_version="strategy-cycle-v1",
        scan_market_count=scan_market_count,
        considered_count=snapshot_ready_count + blocked_market_count,
        snapshot_ready_count=snapshot_ready_count,
        cost_aware_report_count=snapshot_ready_count,
        blocked_counts=blocked_counts,
        screening_report=screening_report,
        cost_aware_reports=(),
    )


def _history_report(
    *,
    history_status: str = "pass",
    generated_at: datetime = GENERATED_AT,
    latest_report_generated_at: datetime | None = None,
) -> PaperStrategyCycleReportHistoryReport:
    latest_report_generated_at = latest_report_generated_at or (
        generated_at - timedelta(hours=1)
    )
    reports = (
        _cycle_report(
            generated_at=latest_report_generated_at - timedelta(hours=2),
            scan_market_count=10,
            snapshot_ready_count=8,
            blocked_counts=(("blocked_fetch_error", 2),),
        ),
        _cycle_report(
            generated_at=latest_report_generated_at - timedelta(hours=1),
            scan_market_count=10,
            snapshot_ready_count=8,
            blocked_counts=(("blocked_fetch_error", 2),),
        ),
        _cycle_report(
            generated_at=latest_report_generated_at,
            scan_market_count=10,
            snapshot_ready_count=8,
            blocked_counts=(("blocked_fetch_error", 2),),
        ),
    )
    history_config = PaperStrategyCycleReportHistoryConfig()
    if history_status == "blocked":
        reports = reports[:1]
    elif history_status == "watch":
        history_config = PaperStrategyCycleReportHistoryConfig(
            max_blocked_market_share=d("0.100000"),
        )
    history = build_paper_strategy_cycle_report_history_report(
        reports,
        config=history_config,
        generated_at=generated_at,
    )
    assert history.history_status == history_status
    assert type(history) is PaperStrategyCycleReportHistoryReport
    return history


def _gate_report(
    history: PaperStrategyCycleReportHistoryReport,
    *,
    config: PaperStrategyCycleReportHistoryGateConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperStrategyCycleReportHistoryGateReport:
    return build_paper_strategy_cycle_report_history_gate_report(
        history,
        config=config or PaperStrategyCycleReportHistoryGateConfig(),
        generated_at=generated_at,
    )


def test_strategy_cycle_report_history_gate_passes_fresh_pass_history() -> None:
    history = _history_report(history_status="pass")

    gate = _gate_report(history)

    assert gate.generated_at == GENERATED_AT
    assert (
        gate.config_version
        == DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_CONFIG_VERSION
    )
    assert gate.source_config_version == history.config_version
    assert gate.source_generated_at == history.generated_at
    assert gate.gate_status == "pass"
    assert gate.recommended_next_step == "allow_strategy_cycle_history_gate"
    assert gate.reason_codes == ("paper_strategy_cycle_report_history_gate_passed",)
    assert gate.reason_code_counts == (
        PaperStrategyCycleReportHistoryGateReasonCodeCount(
            "paper_strategy_cycle_report_history_gate_passed",
            1,
        ),
    )
    assert gate.source_history_status == "pass"
    assert gate.source_report_count == history.report_count
    assert gate.latest_source_generated_at == history.latest_report_generated_at
    assert gate.latest_source_age_seconds == 3600
    assert gate.latest_snapshot_ready_share == history.latest_snapshot_ready_share
    assert gate.latest_snapshot_ready_share is history.latest_snapshot_ready_share
    assert gate.blocked_market_share == history.blocked_market_share
    assert gate.blocked_market_share is history.blocked_market_share
    assert gate.latest_snapshot_ready_count == history.latest_snapshot_ready_count
    assert gate.latest_considered_count == history.latest_considered_count
    assert gate.total_blocked_market_count == history.total_blocked_market_count
    assert history.paper_only is True
    assert history.report_only is True
    assert history.readonly is True
    assert gate.paper_only is True
    assert gate.report_only is True
    assert gate.readonly is True
    assert all(
        row.paper_only and row.report_only and row.readonly
        for row in gate.reason_code_counts
    )


def test_strategy_cycle_report_history_gate_blocks_source_blocked_history() -> None:
    gate = _gate_report(_history_report(history_status="blocked"))

    assert gate.gate_status == "blocked"
    assert gate.recommended_next_step == "block_strategy_cycle_history_gate"
    assert gate.reason_codes == ("source_strategy_cycle_report_history_blocked",)
    assert gate.reason_code_counts == (
        PaperStrategyCycleReportHistoryGateReasonCodeCount(
            "source_strategy_cycle_report_history_blocked",
            1,
        ),
    )


def test_strategy_cycle_report_history_gate_watches_source_watch_history() -> None:
    gate = _gate_report(_history_report(history_status="watch"))

    assert gate.gate_status == "watch"
    assert gate.recommended_next_step == "throttle_strategy_cycle_history_gate"
    assert gate.reason_codes == ("source_strategy_cycle_report_history_watch",)
    assert gate.reason_code_counts == (
        PaperStrategyCycleReportHistoryGateReasonCodeCount(
            "source_strategy_cycle_report_history_watch",
            1,
        ),
    )


def test_strategy_cycle_report_history_gate_watches_stale_latest_timestamp() -> None:
    history = _history_report(
        history_status="pass",
        latest_report_generated_at=GENERATED_AT - timedelta(seconds=86_401),
    )

    gate = _gate_report(history)

    assert gate.gate_status == "watch"
    assert gate.latest_source_age_seconds == 86_401
    assert gate.reason_codes == ("stale_strategy_cycle_report_history",)


def test_strategy_cycle_report_history_gate_blocks_missing_latest_timestamp() -> None:
    history = _history_report(history_status="pass")
    object.__setattr__(history, "latest_report_generated_at", None)

    gate = _gate_report(history)

    assert gate.gate_status == "blocked"
    assert gate.latest_source_generated_at is None
    assert gate.latest_source_age_seconds is None
    assert gate.reason_codes == (
        "missing_latest_strategy_cycle_report_history_timestamp",
    )


def test_strategy_cycle_report_history_gate_status_priority_blocks_over_watch() -> None:
    history = _history_report(
        history_status="blocked",
        latest_report_generated_at=GENERATED_AT - timedelta(seconds=86_401),
    )

    gate = _gate_report(history)

    assert gate.gate_status == "blocked"
    assert gate.reason_codes == (
        "source_strategy_cycle_report_history_blocked",
        "stale_strategy_cycle_report_history",
    )
    assert tuple(row.report_count for row in gate.reason_code_counts) == (1, 1)


def test_strategy_cycle_report_history_gate_rejects_future_latest_timestamp() -> None:
    history = _history_report(
        history_status="pass",
        latest_report_generated_at=GENERATED_AT + timedelta(seconds=1),
    )

    with pytest.raises(ValueError, match="future"):
        _gate_report(history)


def test_strategy_cycle_report_history_gate_rejects_subclasses() -> None:
    history = _history_report(history_status="pass")

    with pytest.raises(ValueError, match="config"):
        PaperStrategyCycleReportHistoryGateConfigSubclass()
    with pytest.raises(ValueError, match="reason"):
        PaperStrategyCycleReportHistoryGateReasonCodeCountSubclass(
            "paper_strategy_cycle_report_history_gate_passed",
            1,
        )
    with pytest.raises(ValueError, match="report"):
        PaperStrategyCycleReportHistoryGateReportSubclass(
            **_gate_report(history).__dict__,
        )

    source_subclass = PaperStrategyCycleReportHistoryReportSubclass(**history.__dict__)
    with pytest.raises(ValueError, match="source history"):
        _gate_report(source_subclass)


def test_strategy_cycle_report_history_gate_outputs_are_frozen_and_validated() -> None:
    history = _history_report(history_status="pass")
    gate = _gate_report(history)

    with pytest.raises(FrozenInstanceError):
        gate.gate_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        gate.reason_code_counts[0].report_count = 2  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        replace(gate, config_version=" gate-v0 ")
    with pytest.raises(ValueError, match="latest_snapshot_ready_share"):
        replace(gate, latest_snapshot_ready_share=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(gate, reason_code_counts=(object(),))  # type: ignore[arg-type]
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
def test_strategy_cycle_report_history_gate_config_validates_inputs(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        PaperStrategyCycleReportHistoryGateConfig(**{field_name: bad_value})


def test_strategy_cycle_report_history_gate_rejects_unsafe_source_flags() -> None:
    history = _history_report(history_status="pass")
    object.__setattr__(history, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        _gate_report(history)

    history = _history_report(history_status="pass")
    object.__setattr__(history, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        _gate_report(history)

    history = _history_report(history_status="pass")
    object.__setattr__(history, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        _gate_report(history)


def test_strategy_cycle_report_history_gate_rejects_float_rates() -> None:
    history = _history_report(history_status="pass")
    object.__setattr__(history, "latest_snapshot_ready_share", 0.8)

    with pytest.raises(ValueError, match="latest_snapshot_ready_share"):
        _gate_report(history)


def test_strategy_cycle_report_history_gate_module_scope_stays_pure_readonly() -> None:
    source = Path(
        "src/polymarket_alpha_lab/paper_strategy_cycle_report_history_gate.py",
    ).read_text(encoding="utf-8")

    for banned_import in (
        "psycopg",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib",
        "websocket",
        "websockets",
        "eth_account",
    ):
        assert banned_import not in source.lower()
