from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_strategy_cycle_report_history import (
    DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_CONFIG_VERSION,
    PaperStrategyCycleReportHistoryConfig,
    PaperStrategyCycleReportHistoryReport,
    build_paper_strategy_cycle_report_history_report,
)
from polymarket_alpha_lab.project_screening import (
    PaperProjectScreeningCandidate,
    PaperProjectScreeningGateResult,
    PaperProjectScreeningQueueItem,
    PaperProjectScreeningReport,
)
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleReport


GENERATED_AT = datetime(2026, 6, 29, 16, 0, tzinfo=UTC)


class PaperStrategyCycleReportSubclass(PaperStrategyCycleReport):
    pass


class PaperStrategyCycleReportHistoryConfigSubclass(PaperStrategyCycleReportHistoryConfig):
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
    paper_only: bool = True,
    report_only: bool = True,
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
        paper_only=paper_only,
        report_only=report_only,
    )


def _history_report(
    *reports: PaperStrategyCycleReport,
    config: PaperStrategyCycleReportHistoryConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperStrategyCycleReportHistoryReport:
    return build_paper_strategy_cycle_report_history_report(
        reports,
        config=config or PaperStrategyCycleReportHistoryConfig(),
        generated_at=generated_at,
    )


def test_strategy_cycle_report_history_passes_and_aggregates_blocked_reasons() -> None:
    reports = (
        _cycle_report(
            generated_at=datetime(2026, 6, 29, 9, 0, tzinfo=UTC),
            scan_market_count=10,
            snapshot_ready_count=3,
            blocked_counts=(("blocked_fetch_error", 1),),
        ),
        _cycle_report(
            generated_at=datetime(
                2026,
                6,
                29,
                6,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            scan_market_count=12,
            snapshot_ready_count=5,
            blocked_counts=(("blocked_non_binary_market", 1),),
        ),
        _cycle_report(
            generated_at=datetime(2026, 6, 29, 11, 0, tzinfo=UTC),
            scan_market_count=8,
            snapshot_ready_count=4,
            blocked_counts=(("blocked_fetch_error", 1),),
        ),
    )

    history = _history_report(
        *reports,
        generated_at=datetime(2026, 6, 29, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert history.generated_at == GENERATED_AT
    assert history.config_version == DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_CONFIG_VERSION
    assert history.history_status == "pass"
    assert history.report_count == 3
    assert history.first_report_generated_at == datetime(2026, 6, 29, 9, 0, tzinfo=UTC)
    assert history.latest_report_generated_at == datetime(2026, 6, 29, 11, 0, tzinfo=UTC)
    assert history.total_scan_market_count == 30
    assert history.total_considered_count == 15
    assert history.total_snapshot_ready_count == 12
    assert history.total_cost_aware_report_count == 12
    assert history.total_blocked_market_count == 3
    assert history.latest_scan_market_count == 8
    assert history.latest_considered_count == 5
    assert history.latest_snapshot_ready_count == 4
    assert history.latest_cost_aware_report_count == 4
    assert history.latest_blocked_market_count == 1
    assert history.overall_snapshot_ready_share == d("0.800000")
    assert history.latest_snapshot_ready_share == d("0.800000")
    assert history.blocked_market_share == d("0.200000")
    assert tuple(row.reason_code for row in history.blocked_reason_rows) == (
        "blocked_fetch_error",
        "blocked_non_binary_market",
    )
    assert history.blocked_reason_rows[0].blocked_market_count == 2
    assert history.blocked_reason_rows[0].report_count == 2
    assert history.blocked_reason_rows[1].blocked_market_count == 1
    assert history.blocked_reason_rows[1].report_count == 1
    assert history.reason_codes == ()
    assert history.paper_only is True
    assert history.report_only is True
    assert history.readonly is True


def test_strategy_cycle_report_history_status_priority_blocks_insufficient_history() -> None:
    history = _history_report(
        _cycle_report(
            generated_at=datetime(2026, 6, 29, 9, 0, tzinfo=UTC),
            scan_market_count=2,
            snapshot_ready_count=1,
            blocked_counts=(("blocked_fetch_error", 1),),
        ),
    )

    assert history.history_status == "blocked"
    assert history.reason_codes == ("insufficient_strategy_cycle_report_history",)


def test_strategy_cycle_report_history_blocks_when_latest_snapshot_share_is_low() -> None:
    reports = (
        _cycle_report(
            generated_at=datetime(2026, 6, 29, 9, 0, tzinfo=UTC),
            scan_market_count=4,
            snapshot_ready_count=4,
            blocked_counts=(),
        ),
        _cycle_report(
            generated_at=datetime(2026, 6, 29, 10, 0, tzinfo=UTC),
            scan_market_count=4,
            snapshot_ready_count=4,
            blocked_counts=(),
        ),
        _cycle_report(
            generated_at=datetime(2026, 6, 29, 11, 0, tzinfo=UTC),
            scan_market_count=4,
            snapshot_ready_count=0,
            blocked_counts=(("blocked_fetch_error", 4),),
        ),
    )

    history = _history_report(
        *reports,
        config=PaperStrategyCycleReportHistoryConfig(
            max_blocked_market_share=d("1.000000"),
        ),
    )

    assert history.history_status == "blocked"
    assert history.latest_snapshot_ready_share == d("0.000000")
    assert history.reason_codes == ("latest_snapshot_ready_share_below_minimum",)


def test_strategy_cycle_report_history_watches_when_blocked_share_is_high() -> None:
    reports = (
        _cycle_report(
            generated_at=datetime(2026, 6, 29, 9, 0, tzinfo=UTC),
            scan_market_count=4,
            snapshot_ready_count=3,
            blocked_counts=(("blocked_fetch_error", 1),),
        ),
        _cycle_report(
            generated_at=datetime(2026, 6, 29, 10, 0, tzinfo=UTC),
            scan_market_count=4,
            snapshot_ready_count=3,
            blocked_counts=(("blocked_fetch_error", 1),),
        ),
        _cycle_report(
            generated_at=datetime(2026, 6, 29, 11, 0, tzinfo=UTC),
            scan_market_count=4,
            snapshot_ready_count=3,
            blocked_counts=(("blocked_non_binary_market", 1),),
        ),
    )

    history = _history_report(
        *reports,
        config=PaperStrategyCycleReportHistoryConfig(
            max_blocked_market_share=d("0.200000"),
        ),
    )

    assert history.history_status == "watch"
    assert history.blocked_market_share == d("0.250000")
    assert history.reason_codes == ("blocked_market_share_above_limit",)


def test_strategy_cycle_report_history_rejects_empty_input_and_wrong_types() -> None:
    with pytest.raises(ValueError, match="reports"):
        _history_report()
    with pytest.raises(ValueError, match="reports"):
        build_paper_strategy_cycle_report_history_report(
            "not reports",
            config=PaperStrategyCycleReportHistoryConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="PaperStrategyCycleReport"):
        build_paper_strategy_cycle_report_history_report(
            (object(),),
            config=PaperStrategyCycleReportHistoryConfig(),
            generated_at=GENERATED_AT,
        )


def test_strategy_cycle_report_history_rejects_subclasses() -> None:
    report = _cycle_report(
        generated_at=datetime(2026, 6, 29, 9, 0, tzinfo=UTC),
        scan_market_count=1,
        snapshot_ready_count=1,
        blocked_counts=(),
    )

    with pytest.raises(ValueError, match="PaperStrategyCycleReport"):
        _history_report(PaperStrategyCycleReportSubclass(**report.__dict__))
    with pytest.raises(ValueError, match="config"):
        build_paper_strategy_cycle_report_history_report(
            (report,),
            config=PaperStrategyCycleReportHistoryConfigSubclass(),
            generated_at=GENERATED_AT,
        )


def test_strategy_cycle_report_history_rejects_unsafe_source_report_flags() -> None:
    report = _cycle_report(
        generated_at=datetime(2026, 6, 29, 9, 0, tzinfo=UTC),
        scan_market_count=1,
        snapshot_ready_count=1,
        blocked_counts=(),
    )
    object.__setattr__(report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        _history_report(report)

    report = _cycle_report(
        generated_at=datetime(2026, 6, 29, 9, 0, tzinfo=UTC),
        scan_market_count=1,
        snapshot_ready_count=1,
        blocked_counts=(),
    )
    object.__setattr__(report, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        _history_report(report)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("config_version", ""),
        ("config_version", " history-v0 "),
        ("min_report_count", 0),
        ("min_report_count", True),
        ("min_latest_snapshot_ready_share", 0.1),
        ("min_latest_snapshot_ready_share", d("NaN")),
        ("max_blocked_market_share", d("Infinity")),
        ("paper_only", False),
        ("report_only", False),
        ("readonly", False),
    ),
)
def test_strategy_cycle_report_history_config_validates_inputs(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        PaperStrategyCycleReportHistoryConfig(**{field_name: bad_value})


def test_strategy_cycle_report_history_outputs_are_frozen_and_validated() -> None:
    history = _history_report(
        _cycle_report(
            generated_at=datetime(2026, 6, 29, 9, 0, tzinfo=UTC),
            scan_market_count=1,
            snapshot_ready_count=1,
            blocked_counts=(),
        ),
        _cycle_report(
            generated_at=datetime(2026, 6, 29, 10, 0, tzinfo=UTC),
            scan_market_count=1,
            snapshot_ready_count=1,
            blocked_counts=(),
        ),
        _cycle_report(
            generated_at=datetime(2026, 6, 29, 11, 0, tzinfo=UTC),
            scan_market_count=1,
            snapshot_ready_count=1,
            blocked_counts=(),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        history.history_status = "watch"  # type: ignore[misc]

    blocked_history = _history_report(
        _cycle_report(
            generated_at=datetime(2026, 6, 29, 9, 0, tzinfo=UTC),
            scan_market_count=2,
            snapshot_ready_count=1,
            blocked_counts=(("blocked_fetch_error", 1),),
        ),
    )
    with pytest.raises(FrozenInstanceError):
        blocked_history.blocked_reason_rows[0].blocked_market_count = 9  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        replace(history, config_version=" strategy-cycle-history-v0 ")
    with pytest.raises(ValueError, match="overall_snapshot_ready_share"):
        replace(history, overall_snapshot_ready_share=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="blocked_market_share"):
        replace(history, blocked_market_share=d("NaN"))
    with pytest.raises(ValueError, match="readonly"):
        replace(history, readonly=False)


def test_strategy_cycle_report_history_module_scope_stays_pure_readonly() -> None:
    source = Path(
        "src/polymarket_alpha_lab/paper_strategy_cycle_report_history.py",
    ).read_text(encoding="utf-8")

    for banned in (
        "psycopg",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib",
        "websocket",
        "websockets",
        "eth_account",
        "private_key",
        "wallet",
        "api_key",
        "submit_order",
        "cancel_order",
        "replace_order",
        "live_trading",
        "exchange",
    ):
        assert banned not in source.lower()
