from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_sports_injury_signal_freshness_report import (
    DEFAULT_RESEARCH_SPORTS_INJURY_SIGNAL_FRESHNESS_REPORT_CONFIG_VERSION,
    RESEARCH_SPORTS_INJURY_SIGNAL_FRESHNESS_REPORT_SCOPE,
    ResearchSportsInjurySignalFreshnessConfig,
    ResearchSportsInjurySignalFreshnessLane,
    ResearchSportsInjurySignalFreshnessReasonCodeCount,
    ResearchSportsInjurySignalFreshnessReport,
    ResearchSportsInjurySignalFreshnessRow,
    build_research_sports_injury_signal_freshness_report,
    research_sports_injury_signal_freshness_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_sports_injury_signal_freshness_report.py"
)


class _StringSubclass(str):
    pass


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSportsInjurySignalFreshnessConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_SPORTS_INJURY_SIGNAL_FRESHNESS_REPORT_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("1800.000000"),
        "stale_source_watch_pressure": d("0.250000"),
        "stale_source_block_pressure": d("0.600000"),
        "contradiction_watch_pressure": d("0.200000"),
        "contradiction_block_pressure": d("0.500000"),
        "recheck_watch_urgency": d("0.300000"),
        "recheck_block_urgency": d("0.700000"),
    }
    values.update(overrides)
    return ResearchSportsInjurySignalFreshnessConfig(**values)


def lane(
    lane_id: str = "basketball.injury-news.aggregate",
    *,
    sport_lane: str = "basketball",
    aggregate_label: str | None = None,
    latest_signal_observed_at: datetime = GENERATED_AT - timedelta(minutes=10),
    signal_count: Decimal = d("10.000000"),
    stale_source_count: Decimal = d("1.000000"),
    contradiction_count: Decimal = d("0.000000"),
    recheck_due_count: Decimal = d("1.000000"),
    lane_config_version: str = "sports-injury-signal-lane-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSportsInjurySignalFreshnessLane:
    return ResearchSportsInjurySignalFreshnessLane(
        lane_id=lane_id,
        sport_lane=sport_lane,
        aggregate_label=aggregate_label or f"{sport_lane}-injury-news",
        latest_signal_observed_at=latest_signal_observed_at,
        signal_count=signal_count,
        stale_source_count=stale_source_count,
        contradiction_count=contradiction_count,
        recheck_due_count=recheck_due_count,
        lane_config_version=lane_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *lanes: ResearchSportsInjurySignalFreshnessLane,
    cfg: ResearchSportsInjurySignalFreshnessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSportsInjurySignalFreshnessReport:
    return build_research_sports_injury_signal_freshness_report(
        lanes,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk(value: object) -> list[object]:
    items = [value]
    if isinstance(value, dict):
        for item in value.values():
            items.extend(walk(item))
    elif isinstance(value, list):
        for item in value:
            items.extend(walk(item))
    return items


def test_reduces_aggregate_sports_injury_signal_freshness_pressures() -> None:
    summary = report(
        lane(
            "football.injury-news.aggregate",
            sport_lane="football",
            aggregate_label="football-injury-news",
            latest_signal_observed_at=GENERATED_AT - timedelta(minutes=40),
            stale_source_count=d("3.000000"),
            contradiction_count=d("1.000000"),
            recheck_due_count=d("3.000000"),
        ),
        lane(
            "tennis.injury-news.aggregate",
            sport_lane="tennis",
            aggregate_label="tennis-injury-news",
            latest_signal_observed_at=GENERATED_AT - timedelta(hours=2),
            stale_source_count=d("7.000000"),
            contradiction_count=d("6.000000"),
            recheck_due_count=d("8.000000"),
        ),
        lane(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_SPORTS_INJURY_SIGNAL_FRESHNESS_REPORT_CONFIG_VERSION
    )
    assert summary.research_scope == RESEARCH_SPORTS_INJURY_SIGNAL_FRESHNESS_REPORT_SCOPE
    assert summary.status == "block"
    assert summary.recheck_urgency == d("0.800000")
    assert summary.lane_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.stale_source_pressure_lane_count == d("2.000000")
    assert summary.contradiction_pressure_lane_count == d("1.000000")
    assert summary.recheck_urgency_lane_count == d("2.000000")
    assert summary.max_signal_age_seconds_observed == d("7200.000000")
    assert summary.average_stale_source_pressure == d("0.366667")
    assert summary.average_contradiction_pressure == d("0.233333")
    assert tuple(row.lane_id for row in summary.rows) == (
        "tennis.injury-news.aggregate",
        "football.injury-news.aggregate",
        "basketball.injury-news.aggregate",
    )

    blocked = summary.rows[0]
    assert blocked.status == "block"
    assert blocked.signal_age_seconds == d("7200.000000")
    assert blocked.stale_source_pressure == d("0.700000")
    assert blocked.contradiction_pressure == d("0.600000")
    assert blocked.recheck_urgency == d("0.800000")
    assert blocked.reason_codes == (
        "sports_injury_signal_freshness_stale_source_block",
        "sports_injury_signal_freshness_contradiction_block",
        "sports_injury_signal_freshness_recheck_block",
        "sports_injury_signal_freshness_signal_age_watch",
    )

    watched = summary.rows[1]
    assert watched.status == "watch"
    assert watched.stale_source_pressure == d("0.300000")
    assert watched.reason_codes == (
        "sports_injury_signal_freshness_stale_source_watch",
        "sports_injury_signal_freshness_recheck_watch",
        "sports_injury_signal_freshness_signal_age_watch",
    )

    passed = summary.rows[2]
    assert passed.status == "pass"
    assert passed.reason_codes == ("sports_injury_signal_freshness_pass",)

    assert summary.reason_code_counts == (
        ResearchSportsInjurySignalFreshnessReasonCodeCount(
            reason_code="sports_injury_signal_freshness_stale_source_watch",
            count=d("1.000000"),
            lane_ratio=d("0.333333"),
        ),
        ResearchSportsInjurySignalFreshnessReasonCodeCount(
            reason_code="sports_injury_signal_freshness_stale_source_block",
            count=d("1.000000"),
            lane_ratio=d("0.333333"),
        ),
        ResearchSportsInjurySignalFreshnessReasonCodeCount(
            reason_code="sports_injury_signal_freshness_contradiction_block",
            count=d("1.000000"),
            lane_ratio=d("0.333333"),
        ),
        ResearchSportsInjurySignalFreshnessReasonCodeCount(
            reason_code="sports_injury_signal_freshness_recheck_watch",
            count=d("1.000000"),
            lane_ratio=d("0.333333"),
        ),
        ResearchSportsInjurySignalFreshnessReasonCodeCount(
            reason_code="sports_injury_signal_freshness_recheck_block",
            count=d("1.000000"),
            lane_ratio=d("0.333333"),
        ),
        ResearchSportsInjurySignalFreshnessReasonCodeCount(
            reason_code="sports_injury_signal_freshness_signal_age_watch",
            count=d("2.000000"),
            lane_ratio=d("0.666667"),
        ),
        ResearchSportsInjurySignalFreshnessReasonCodeCount(
            reason_code="sports_injury_signal_freshness_pass",
            count=d("1.000000"),
            lane_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(item.reason_code for item in summary.reason_code_counts)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_payload_digest_is_deterministic_decimal_only_and_report_only() -> None:
    first = report(
        lane("football.injury-news.aggregate", sport_lane="football"),
        lane("basketball.injury-news.aggregate", sport_lane="basketball"),
    )
    second = report(
        lane("basketball.injury-news.aggregate", sport_lane="basketball"),
        lane("football.injury-news.aggregate", sport_lane="football"),
    )

    first_payload = research_sports_injury_signal_freshness_report_payload(first)
    second_payload = research_sports_injury_signal_freshness_report_payload(second)

    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload == second_payload
    json.dumps(first_payload, sort_keys=True)
    assert first_payload["generated_at"] == "2026-07-08T12:00:00Z"
    assert first_payload["lane_count"] == "2.000000"
    assert first_payload["rows"][0]["signal_count"] == "10.000000"
    assert first_payload["rows"][0]["latest_signal_observed_at"] == (
        "2026-07-08T11:50:00Z"
    )
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(item, float) for item in walk(first_payload))
    for item in walk(first_payload):
        if isinstance(item, bool):
            continue
        assert not isinstance(item, int)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, lane_count=d("3.000000"))


def test_validation_blocks_non_aggregate_labels_status_drift_flags_and_bad_types() -> None:
    for exported_type in (
        ResearchSportsInjurySignalFreshnessConfig,
        ResearchSportsInjurySignalFreshnessLane,
        ResearchSportsInjurySignalFreshnessReasonCodeCount,
        ResearchSportsInjurySignalFreshnessRow,
        ResearchSportsInjurySignalFreshnessReport,
    ):
        assert is_dataclass(exported_type)
        assert exported_type.__dataclass_params__.frozen is True

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("research-sports-injury-signal-v0"))
    with pytest.raises(ValueError, match="max_signal_age_seconds"):
        config(max_signal_age_seconds=_DecimalSubclass("1800.000000"))
    with pytest.raises(ValueError, match="stale_source_watch_pressure"):
        config(stale_source_watch_pressure=d("0.700000"))
    with pytest.raises(ValueError, match="lane_id"):
        lane(lane_id=_StringSubclass("basketball.injury-news.aggregate"))
    with pytest.raises(ValueError, match="aggregate"):
        lane(aggregate_label="player-specific-injury-note")
    with pytest.raises(ValueError, match="signal_count"):
        lane(signal_count=10.0)
    with pytest.raises(ValueError, match="stale_source_count"):
        lane(stale_source_count=d("11.000000"))
    with pytest.raises(ValueError, match="future"):
        report(lane(latest_signal_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="generated_at"):
        report(lane(), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        lane(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        lane(readonly=False)
    with pytest.raises(ValueError, match="unique"):
        report(lane(), lane(aggregate_label="basketball-injury-news-alt"))
    with pytest.raises(ValueError, match="lanes"):
        build_research_sports_injury_signal_freshness_report(
            [object()],
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(FrozenInstanceError):
        summary = report(lane())
        summary.status = "watch"  # type: ignore[misc]

    summary = report(lane())
    with pytest.raises(ValueError, match="status"):
        replace(summary.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(summary.rows[0], status="ready")
    with pytest.raises(ValueError, match="report"):
        research_sports_injury_signal_freshness_report_payload(object())


def test_public_dataclasses_are_decimal_only_and_module_has_no_io_surface() -> None:
    public_numeric_markers = (
        "_count",
        "_ratio",
        "_seconds",
        "_pressure",
        "_urgency",
    )
    for dataclass_type in (
        ResearchSportsInjurySignalFreshnessConfig,
        ResearchSportsInjurySignalFreshnessLane,
        ResearchSportsInjurySignalFreshnessReasonCodeCount,
        ResearchSportsInjurySignalFreshnessRow,
        ResearchSportsInjurySignalFreshnessReport,
    ):
        for field in fields(dataclass_type):
            if any(field.name.endswith(marker) for marker in public_numeric_markers):
                assert field.type in (Decimal, "Decimal")

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    attribute_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)
        if isinstance(node, ast.Attribute):
            attribute_names.add(node.attr)

    forbidden_imports = {
        "os",
        "pathlib",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "supabase",
        "subprocess",
    }
    forbidden_calls_or_attributes = {
        "open",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "write",
        "read_text",
        "getenv",
        "environ",
        "trade",
    }
    assert imported_modules.isdisjoint(forbidden_imports)
    assert not (call_names & forbidden_calls_or_attributes)
    assert not (attribute_names & forbidden_calls_or_attributes)
    for forbidden in (
        "live trading",
        "wallet",
        "broker",
        "signing",
        "submit_order",
        "cancel_order",
        "auth",
        "secret",
        "private",
        "network",
        "database",
    ):
        assert forbidden not in lowered
