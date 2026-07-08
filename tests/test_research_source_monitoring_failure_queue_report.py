from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_monitoring_failure_queue_report import (
    ResearchSourceMonitoringFailureEvent,
    ResearchSourceMonitoringFailureQueueConfig,
    ResearchSourceMonitoringFailureQueueItem,
    ResearchSourceMonitoringFailureQueueReport,
    build_research_source_monitoring_failure_queue_report,
    research_source_monitoring_failure_queue_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
_DEFAULT_LAST_SUCCESS_AT = object()


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceMonitoringFailureQueueConfig:
    values = {
        "config_version": "research-source-monitoring-failure-queue-v0",
        "watch_refresh_age_seconds": d("7200.000000"),
        "block_refresh_age_seconds": d("86400.000000"),
        "min_alternative_source_count": d("1.000000"),
        "block_affected_market_count": d("5.000000"),
        "block_affected_candidate_count": d("20.000000"),
        "watch_escalation_priority_score": d("0.500000"),
        "block_escalation_priority_score": d("0.850000"),
    }
    values.update(overrides)
    return ResearchSourceMonitoringFailureQueueConfig(**values)


def event(
    index: int,
    *,
    failure_id: str | None = None,
    source_alias: str = "official-feed",
    team_id: str = "politics",
    category_id: str = "politics",
    failure_type: str = "timeout",
    impact_domain: str = "resolution",
    detected_at: datetime | None = None,
    last_success_at: datetime | None | object = _DEFAULT_LAST_SUCCESS_AT,
    affected_market_count: Decimal = d("1.000000"),
    affected_candidate_count: Decimal = d("0.000000"),
    refresh_attempt_count: Decimal = d("1.000000"),
    alternative_sources: tuple[str, ...] = ("venue-backup",),
    escalation_priority_score: Decimal = d("0.400000"),
) -> ResearchSourceMonitoringFailureEvent:
    return ResearchSourceMonitoringFailureEvent(
        failure_id=failure_id or f"failure-{index:03d}",
        source_alias=source_alias,
        team_id=team_id,
        category_id=category_id,
        failure_type=failure_type,
        impact_domain=impact_domain,
        detected_at=detected_at or GENERATED_AT - timedelta(minutes=index),
        last_success_at=(
            GENERATED_AT - timedelta(hours=1)
            if last_success_at is _DEFAULT_LAST_SUCCESS_AT
            else last_success_at
        ),
        affected_market_count=affected_market_count,
        affected_candidate_count=affected_candidate_count,
        refresh_attempt_count=refresh_attempt_count,
        alternative_sources=alternative_sources,
        escalation_priority_score=escalation_priority_score,
    )


def report(
    events: tuple[ResearchSourceMonitoringFailureEvent, ...],
    *,
    cfg: ResearchSourceMonitoringFailureQueueConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceMonitoringFailureQueueReport:
    return build_research_source_monitoring_failure_queue_report(
        events,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_pass_report_without_queue_items() -> None:
    failure_report = report(())

    assert type(failure_report) is ResearchSourceMonitoringFailureQueueReport
    assert failure_report.generated_at == GENERATED_AT
    assert failure_report.config_version == "research-source-monitoring-failure-queue-v0"
    assert failure_report.status == "pass"
    assert failure_report.failure_count == d("0.000000")
    assert failure_report.queue_item_count == d("0.000000")
    assert failure_report.pass_count == d("0.000000")
    assert failure_report.watch_count == d("0.000000")
    assert failure_report.blocked_count == d("0.000000")
    assert failure_report.high_refresh_risk_count == d("0.000000")
    assert failure_report.missing_alternative_source_count == d("0.000000")
    assert failure_report.total_affected_market_count == d("0.000000")
    assert failure_report.total_affected_candidate_count == d("0.000000")
    assert failure_report.max_escalation_priority_score == d("0.000000")
    assert failure_report.reason_codes == ("no_source_monitoring_failures",)
    assert failure_report.queue_items == ()
    assert failure_report.paper_only is True
    assert failure_report.report_only is True
    assert failure_report.readonly is True


def test_mitigated_low_risk_failure_passes_but_remains_auditable() -> None:
    failure_report = report(
        (
            event(
                1,
                failure_type="parse_error",
                impact_domain="news_context",
                affected_market_count=d("0.000000"),
                affected_candidate_count=d("0.000000"),
                refresh_attempt_count=d("2.000000"),
                alternative_sources=("wire-backup", "venue-backup"),
                escalation_priority_score=d("0.200000"),
            ),
        ),
    )

    assert failure_report.status == "pass"
    assert failure_report.failure_count == d("1.000000")
    assert failure_report.queue_item_count == d("1.000000")
    assert failure_report.pass_count == d("1.000000")
    assert failure_report.watch_count == d("0.000000")
    assert failure_report.blocked_count == d("0.000000")
    assert failure_report.reason_codes == ("source_monitoring_failure_pass",)

    item = failure_report.queue_items[0]
    assert type(item) is ResearchSourceMonitoringFailureQueueItem
    assert item.failure_id == "failure-001"
    assert item.source_alias == "official-feed"
    assert item.failure_type == "parse_error"
    assert item.impact_domain == "news_context"
    assert item.refresh_risk == "low"
    assert item.alternative_source_count == d("2.000000")
    assert item.queue_status == "pass"
    assert item.priority_rank == d("1.000000")
    assert item.reason_codes == (
        "alternative_sources_available",
        "failure_type_parse_error",
        "impact_domain_news_context",
        "low_refresh_risk",
        "source_monitoring_failure_pass",
    )


def test_high_risk_missing_alternative_failure_blocks_and_sorts_first() -> None:
    failure_report = report(
        (
            event(
                1,
                failure_type="timeout",
                impact_domain="probability",
                last_success_at=GENERATED_AT - timedelta(hours=3),
                affected_market_count=d("2.000000"),
                affected_candidate_count=d("2.000000"),
                alternative_sources=("venue-backup",),
                escalation_priority_score=d("0.600000"),
            ),
            event(
                2,
                failure_type="auth_error",
                impact_domain="resolution",
                last_success_at=None,
                affected_market_count=d("6.000000"),
                affected_candidate_count=d("22.000000"),
                refresh_attempt_count=d("4.000000"),
                alternative_sources=(),
                escalation_priority_score=d("0.950000"),
            ),
        ),
    )

    assert failure_report.status == "block"
    assert failure_report.failure_count == d("2.000000")
    assert failure_report.queue_item_count == d("2.000000")
    assert failure_report.pass_count == d("0.000000")
    assert failure_report.watch_count == d("1.000000")
    assert failure_report.blocked_count == d("1.000000")
    assert failure_report.high_refresh_risk_count == d("1.000000")
    assert failure_report.missing_alternative_source_count == d("1.000000")
    assert failure_report.total_affected_market_count == d("8.000000")
    assert failure_report.total_affected_candidate_count == d("24.000000")
    assert failure_report.max_escalation_priority_score == d("0.950000")
    assert failure_report.reason_codes == (
        "affected_candidate_threshold_hit",
        "affected_market_threshold_hit",
        "failure_type_auth_error",
        "failure_type_timeout",
        "high_escalation_priority",
        "high_refresh_risk",
        "impact_domain_probability",
        "impact_domain_resolution",
        "missing_alternative_source",
        "source_monitoring_failure_block",
        "source_monitoring_failure_watch",
        "watch_refresh_risk",
    )

    blocking_item, watch_item = failure_report.queue_items
    assert blocking_item.failure_id == "failure-002"
    assert blocking_item.queue_status == "block"
    assert blocking_item.priority_rank == d("1.000000")
    assert blocking_item.refresh_risk == "high"
    assert blocking_item.alternative_sources == ()
    assert blocking_item.reason_codes == (
        "affected_candidate_threshold_hit",
        "affected_market_threshold_hit",
        "failure_type_auth_error",
        "high_escalation_priority",
        "high_refresh_risk",
        "impact_domain_resolution",
        "missing_alternative_source",
        "source_monitoring_failure_block",
    )
    assert watch_item.failure_id == "failure-001"
    assert watch_item.queue_status == "watch"
    assert watch_item.priority_rank == d("2.000000")
    assert watch_item.refresh_risk == "watch"


def test_payload_serializes_decimals_as_strings_and_excludes_sensitive_identifiers() -> None:
    failure_report = report(
        (
            event(
                1,
                source_alias="court-feed",
                impact_domain="resolution",
                last_success_at=None,
                alternative_sources=(),
                escalation_priority_score=d("0.900000"),
            ),
        ),
    )

    payload = research_source_monitoring_failure_queue_report_payload(failure_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["queue_items"][0]["escalation_priority_score"] == "0.900000"
    assert payload["queue_items"][0]["alternative_sources"] == []
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert all(
        fragment not in encoded.lower()
        for fragment in (
            "source_url",
            "source_text",
            "source_ref",
            "dsn",
            "table_name",
            "api_token",
            "market_id",
            "candidate_id",
            "http://",
            "https://",
            "postgresql://",
            "token=",
        )
    )


def test_validation_rejects_bad_types_enums_times_flags_and_unsafe_public_values() -> None:
    with pytest.raises(ValueError, match="watch_refresh_age_seconds"):
        config(watch_refresh_age_seconds=7200)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_escalation_priority_score"):
        config(block_escalation_priority_score=_DecimalSubclass("0.850000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((event(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((event(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="team_id"):
        event(1, team_id="unknown")
    with pytest.raises(ValueError, match="category_id"):
        event(1, team_id="politics", category_id="finance.crypto.btc")
    with pytest.raises(ValueError, match="failure_type"):
        event(1, failure_type="network")
    with pytest.raises(ValueError, match="impact_domain"):
        event(1, impact_domain="secret_table")
    with pytest.raises(ValueError, match="detected_at"):
        event(1, detected_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="detected_at"):
        report((event(1, detected_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="last_success_at"):
        event(1, last_success_at=GENERATED_AT + timedelta(seconds=1))
    with pytest.raises(ValueError, match="affected_market_count"):
        event(1, affected_market_count=d("1.5"))
    with pytest.raises(ValueError, match="escalation_priority_score"):
        event(1, escalation_priority_score=Decimal("0.5"))  # not quantized
    with pytest.raises(ValueError, match="alternative_sources"):
        event(1, alternative_sources=("https://private.example/source",))
    with pytest.raises(ValueError, match="source_alias"):
        event(1, source_alias="official token=abc123")
    with pytest.raises(ValueError, match="paper_only"):
        replace(event(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_reports_validate_consistency() -> None:
    failure_report = report((event(1),))

    with pytest.raises(FrozenInstanceError):
        failure_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        failure_report.queue_items[0].queue_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="queue_status"):
        replace(failure_report.queue_items[0], queue_status="block")
    with pytest.raises(ValueError, match="blocked_count"):
        replace(failure_report, blocked_count=d("1.000000"))


def test_owned_module_has_no_network_db_trading_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_monitoring_failure_queue_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "web3",
        "clob",
        "order",
        "trade",
        "submit",
        "cancel",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
