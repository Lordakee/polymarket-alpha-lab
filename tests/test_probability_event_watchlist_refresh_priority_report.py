from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import inspect
from json import dumps

import pytest

import polymarket_alpha_lab.probability_event_watchlist_refresh_priority_report as report_module
from polymarket_alpha_lab.probability_event_watchlist_refresh_priority_report import (
    ProbabilityEventWatchlistRefreshPriorityConfig,
    ProbabilityEventWatchlistRefreshPriorityInput,
    ProbabilityEventWatchlistRefreshPriorityReport,
    ProbabilityEventWatchlistRefreshPriorityRow,
    build_probability_event_watchlist_refresh_priority_report,
    probability_event_watchlist_refresh_priority_report_payload,
)


GENERATED_AT = datetime(2026, 7, 12, 9, 30, tzinfo=UTC)


def _item(
    event_id: str,
    *,
    watch_status: str = "active",
    source_age_hours: Decimal = Decimal("1.000000"),
    market_close_hours: Decimal = Decimal("96.000000"),
    edge_to_threshold_probability: Decimal = Decimal("0.250000"),
    liquidity_status: str = "healthy",
    memory_policy_status: str = "current",
) -> ProbabilityEventWatchlistRefreshPriorityInput:
    return ProbabilityEventWatchlistRefreshPriorityInput(
        event_id=event_id,
        watch_status=watch_status,
        source_age_hours=source_age_hours,
        market_close_hours=market_close_hours,
        edge_to_threshold_probability=edge_to_threshold_probability,
        liquidity_status=liquidity_status,
        memory_policy_status=memory_policy_status,
    )


def test_report_prioritizes_watchlist_refresh_from_event_safety_fields() -> None:
    report = build_probability_event_watchlist_refresh_priority_report(
        (
            _item("fresh-event"),
            _item(
                "manual-blocker-event",
                source_age_hours=Decimal("2.000000"),
                market_close_hours=Decimal("2.000000"),
                edge_to_threshold_probability=Decimal("0.010000"),
                liquidity_status="blocked",
                memory_policy_status="blocked",
            ),
            _item(
                "stale-edge-event",
                source_age_hours=Decimal("30.000000"),
                market_close_hours=Decimal("12.000000"),
                edge_to_threshold_probability=Decimal("0.030000"),
                liquidity_status="thin",
            ),
            _item(
                "policy-review-event",
                source_age_hours=Decimal("8.000000"),
                market_close_hours=Decimal("36.000000"),
                edge_to_threshold_probability=Decimal("0.080000"),
                memory_policy_status="refresh_due",
            ),
        ),
        generated_at=GENERATED_AT,
        config=ProbabilityEventWatchlistRefreshPriorityConfig(
            source_stale_hours=Decimal("6.000000"),
            source_overdue_hours=Decimal("24.000000"),
            market_close_near_hours=Decimal("48.000000"),
            market_close_imminent_hours=Decimal("6.000000"),
            edge_watch_probability=Decimal("0.100000"),
            edge_urgent_probability=Decimal("0.020000"),
        ),
    )

    assert report.status == "block"
    assert report.event_count == Decimal("4.000000")
    assert report.critical_count == Decimal("1.000000")
    assert report.high_count == Decimal("1.000000")
    assert report.medium_count == Decimal("1.000000")
    assert report.low_count == Decimal("1.000000")
    assert tuple(row.event_id for row in report.rows) == (
        "manual-blocker-event",
        "stale-edge-event",
        "policy-review-event",
        "fresh-event",
    )
    assert tuple(row.refresh_priority for row in report.rows) == (
        "critical",
        "high",
        "medium",
        "low",
    )
    assert report.rows[0].reason_codes == (
        "liquidity_blocked",
        "memory_policy_blocked",
        "market_close_imminent",
        "edge_threshold_imminent",
    )
    assert report.rows[0].manual_next_step == "paper_review_resolve_refresh_blockers"
    assert report.rows[1].reason_codes == (
        "source_refresh_overdue",
        "market_close_near",
        "edge_threshold_near",
        "liquidity_thin",
    )
    assert report.rows[1].manual_next_step == "paper_review_refresh_sources_today"
    assert report.rows[2].reason_codes == (
        "source_refresh_stale",
        "market_close_near",
        "edge_threshold_near",
        "memory_policy_refresh_due",
    )
    assert report.rows[2].manual_next_step == "paper_review_schedule_watchlist_refresh"
    assert report.rows[3].reason_codes == ("watchlist_refresh_current",)
    assert report.rows[3].manual_next_step == "paper_review_continue_watchlist_monitoring"
    assert report.reason_codes == (
        "liquidity_blocked",
        "memory_policy_blocked",
        "source_refresh_overdue",
        "source_refresh_stale",
        "market_close_imminent",
        "market_close_near",
        "edge_threshold_imminent",
        "edge_threshold_near",
        "liquidity_thin",
        "memory_policy_refresh_due",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_json_ready_without_float_values() -> None:
    report = build_probability_event_watchlist_refresh_priority_report(
        (
            _item(
                "payload-event",
                source_age_hours=Decimal("7.500000"),
                market_close_hours=Decimal("18.000000"),
                edge_to_threshold_probability=Decimal("0.040000"),
                liquidity_status="thin",
            ),
        ),
        generated_at=GENERATED_AT,
        config=ProbabilityEventWatchlistRefreshPriorityConfig(),
    )

    payload = probability_event_watchlist_refresh_priority_report_payload(report)

    assert payload["generated_at"] == "2026-07-12T09:30:00+00:00"
    assert payload["event_count"] == "1.000000"
    assert payload["rows"][0]["source_age_hours"] == "7.500000"
    assert payload["rows"][0]["edge_to_threshold_probability"] == "0.040000"
    assert payload["rows"][0]["refresh_priority"] == "high"
    assert payload["rows"][0]["manual_next_step"] == "paper_review_refresh_sources_today"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_paths(payload) == ()
    dumps(payload, sort_keys=True)


def test_public_dataclasses_are_frozen_and_use_decimal_numeric_fields() -> None:
    for dataclass_type in (
        ProbabilityEventWatchlistRefreshPriorityConfig,
        ProbabilityEventWatchlistRefreshPriorityInput,
        ProbabilityEventWatchlistRefreshPriorityRow,
        ProbabilityEventWatchlistRefreshPriorityReport,
    ):
        assert is_dataclass(dataclass_type)
        assert dataclass_type.__dataclass_params__.frozen is True
        annotations = dataclass_type.__annotations__.values()
        assert all("float" not in str(annotation) for annotation in annotations)
        assert all("int" not in str(annotation) for annotation in annotations)

    item = _item("frozen-event")
    with pytest.raises(FrozenInstanceError):
        item.event_id = "changed"  # type: ignore[misc]


def test_validates_flags_statuses_decimal_inputs_and_safe_public_payloads() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        replace(ProbabilityEventWatchlistRefreshPriorityConfig(), paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(_item("readonly-event"), readonly=False)

    with pytest.raises(ValueError, match="Decimal"):
        _item("float-event", source_age_hours=1.0)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="nonnegative"):
        _item("negative-event", market_close_hours=Decimal("-1.000000"))

    with pytest.raises(ValueError, match="watch_status"):
        _item("bad-watch-event", watch_status="execute")

    with pytest.raises(ValueError, match="liquidity_status"):
        _item("bad-liquidity-event", liquidity_status="deep")

    with pytest.raises(ValueError, match="memory_policy_status"):
        _item("bad-memory-event", memory_policy_status="unknown")

    with pytest.raises(ValueError, match="duplicate event_id"):
        build_probability_event_watchlist_refresh_priority_report(
            (_item("duplicate-event"), _item("duplicate-event")),
            generated_at=GENERATED_AT,
            config=ProbabilityEventWatchlistRefreshPriorityConfig(),
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        build_probability_event_watchlist_refresh_priority_report(
            (_item("naive-generated-event"),),
            generated_at=datetime(2026, 7, 12, 9, 30),
            config=ProbabilityEventWatchlistRefreshPriorityConfig(),
        )

    with pytest.raises(ValueError, match="unsafe live surface"):
        probability_event_watchlist_refresh_priority_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet_address": "redacted",
            },
        )


def test_module_scope_has_no_network_storage_or_execution_imports() -> None:
    source = inspect.getsource(report_module)
    forbidden_terms = (
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "open(",
    )

    for term in forbidden_terms:
        assert term not in source


def _float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()
