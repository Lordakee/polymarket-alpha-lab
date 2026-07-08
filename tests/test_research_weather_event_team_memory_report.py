from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, get_args, get_origin, get_type_hints

import pytest

from polymarket_alpha_lab.research_weather_event_team_memory_report import (
    DEFAULT_RESEARCH_WEATHER_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION,
    ResearchWeatherEventTeamMemoryObservation,
    ResearchWeatherEventTeamMemoryReport,
    ResearchWeatherEventTeamMemoryReportConfig,
    ResearchWeatherEventTeamMemoryReportReasonCodeCount,
    build_research_weather_event_team_memory_report,
    research_weather_event_team_memory_report_digest,
    research_weather_event_team_memory_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_weather_event_team_memory_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    team_id: str = "weather",
    *,
    specialist_role: str = "weather_event_memory",
    event_family: str = "tropical_cyclone",
    region_bucket: str = "us_gulf_coast",
    memory_last_refreshed_at: datetime = GENERATED_AT - timedelta(hours=6),
    forecast_source_last_seen_at: datetime = GENERATED_AT - timedelta(minutes=20),
    evidence_reuse_count: Decimal = d("4.000000"),
    evidence_reuse_ratio: Decimal = d("0.800000"),
    calibration_sample_count: Decimal = d("6.000000"),
    recent_brier_score: Decimal = d("0.120000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchWeatherEventTeamMemoryObservation:
    return ResearchWeatherEventTeamMemoryObservation(
        team_id=team_id,
        specialist_role=specialist_role,
        event_family=event_family,
        region_bucket=region_bucket,
        memory_last_refreshed_at=memory_last_refreshed_at,
        forecast_source_last_seen_at=forecast_source_last_seen_at,
        evidence_reuse_count=evidence_reuse_count,
        evidence_reuse_ratio=evidence_reuse_ratio,
        calibration_sample_count=calibration_sample_count,
        recent_brier_score=recent_brier_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[ResearchWeatherEventTeamMemoryObservation, ...],
    *,
    cfg: ResearchWeatherEventTeamMemoryReportConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchWeatherEventTeamMemoryReport:
    return build_research_weather_event_team_memory_report(
        rows,
        config=cfg or ResearchWeatherEventTeamMemoryReportConfig(),
        generated_at=generated_at,
    )


def assert_no_float_or_int(value: object) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (float, int)):
        pytest.fail(f"payload numeric values must be Decimal strings: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
    elif isinstance(value, list | tuple):
        for item in value:
            assert_no_float_or_int(item)


def test_builds_weather_memory_report_with_readiness_rollups() -> None:
    summary = report(
        (
            observation(
                team_id="climate",
                specialist_role="climate_event_memory",
                event_family="heat_extreme",
                region_bucket="us_southwest",
                memory_last_refreshed_at=GENERATED_AT - timedelta(days=18),
                forecast_source_last_seen_at=GENERATED_AT - timedelta(hours=8),
                evidence_reuse_count=d("2.000000"),
                evidence_reuse_ratio=d("0.500000"),
                calibration_sample_count=d("4.000000"),
                recent_brier_score=d("0.240000"),
            ),
            observation(
                team_id="weather",
                event_family="flash_flood",
                region_bucket="us_mid_atlantic",
                memory_last_refreshed_at=GENERATED_AT - timedelta(days=45),
                forecast_source_last_seen_at=GENERATED_AT - timedelta(days=3),
                evidence_reuse_count=d("0.000000"),
                evidence_reuse_ratio=d("0.100000"),
                calibration_sample_count=d("1.000000"),
                recent_brier_score=d("0.420000"),
            ),
            observation(
                team_id="weather",
                event_family="tropical_cyclone",
                region_bucket="us_gulf_coast",
            ),
        ),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert (
        summary.config_version
        == DEFAULT_RESEARCH_WEATHER_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
    )
    assert summary.digest_status == "block"
    assert summary.next_review_step == "pause_weather_event_memory_reuse"
    assert summary.observation_count == d("3.000000")
    assert summary.team_count == d("2.000000")
    assert summary.specialist_count == d("2.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.stale_memory_count == d("2.000000")
    assert summary.stale_forecast_source_count == d("2.000000")
    assert summary.evidence_reuse_gap_count == d("2.000000")
    assert summary.calibration_gap_count == d("2.000000")
    assert summary.mean_evidence_reuse_ratio == d("0.466667")
    assert summary.mean_recent_brier_score == d("0.260000")
    assert summary.max_memory_age_seconds == d("3888000.000000")
    assert summary.max_forecast_source_age_seconds == d("259200.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.readiness_status for row in summary.rows) == (
        "block",
        "watch",
        "pass",
    )

    blocked = summary.rows[0]
    assert blocked.team_id == "weather"
    assert blocked.event_family == "flash_flood"
    assert blocked.region_bucket == "us_mid_atlantic"
    assert blocked.memory_age_seconds == d("3888000.000000")
    assert blocked.forecast_source_age_seconds == d("259200.000000")
    assert blocked.readiness_score == d("0.000000")
    assert blocked.reason_codes == (
        "weather_event_memory_calibration_brier_block",
        "weather_event_memory_calibration_sample_block",
        "weather_event_memory_evidence_reuse_block",
        "weather_event_memory_forecast_source_stale_block",
        "weather_event_memory_stale_block",
    )

    watched = summary.rows[1]
    assert watched.readiness_status == "watch"
    assert watched.reason_codes == (
        "weather_event_memory_calibration_brier_watch",
        "weather_event_memory_calibration_sample_watch",
        "weather_event_memory_evidence_reuse_watch",
        "weather_event_memory_forecast_source_stale_watch",
        "weather_event_memory_stale_watch",
    )

    passed = summary.rows[2]
    assert passed.readiness_status == "pass"
    assert passed.readiness_score == d("0.936000")
    assert passed.reason_codes == ("weather_event_memory_ready",)

    assert summary.reason_code_counts == (
        ResearchWeatherEventTeamMemoryReportReasonCodeCount(
            reason_code="weather_event_memory_calibration_brier_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchWeatherEventTeamMemoryReportReasonCodeCount(
            reason_code="weather_event_memory_calibration_sample_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchWeatherEventTeamMemoryReportReasonCodeCount(
            reason_code="weather_event_memory_evidence_reuse_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchWeatherEventTeamMemoryReportReasonCodeCount(
            reason_code="weather_event_memory_forecast_source_stale_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchWeatherEventTeamMemoryReportReasonCodeCount(
            reason_code="weather_event_memory_stale_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchWeatherEventTeamMemoryReportReasonCodeCount(
            reason_code="weather_event_memory_calibration_brier_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchWeatherEventTeamMemoryReportReasonCodeCount(
            reason_code="weather_event_memory_calibration_sample_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchWeatherEventTeamMemoryReportReasonCodeCount(
            reason_code="weather_event_memory_evidence_reuse_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchWeatherEventTeamMemoryReportReasonCodeCount(
            reason_code="weather_event_memory_forecast_source_stale_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchWeatherEventTeamMemoryReportReasonCodeCount(
            reason_code="weather_event_memory_stale_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchWeatherEventTeamMemoryReportReasonCodeCount(
            reason_code="weather_event_memory_ready",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
    )


def test_empty_and_payload_digest_are_report_only_readonly_and_deterministic() -> None:
    summary = report(())
    payload = research_weather_event_team_memory_report_payload(summary)
    digest = research_weather_event_team_memory_report_digest(summary)

    assert summary.digest_status == "block"
    assert summary.next_review_step == "pause_weather_event_memory_reuse"
    assert summary.observation_count == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == ("weather_event_memory_report_empty",)
    assert digest.startswith("sha256:")
    assert digest == research_weather_event_team_memory_report_digest(payload)
    assert digest == research_weather_event_team_memory_report_digest(summary)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["observation_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True)
    assert_no_float_or_int(payload)


def test_rejects_unsafe_inputs_and_public_payload_surfaces() -> None:
    with pytest.raises(ValueError, match="memory_last_refreshed_at"):
        observation(memory_last_refreshed_at=datetime(2026, 7, 8, 12, 0))

    with pytest.raises(ValueError, match="forecast_source_last_seen_at"):
        observation(
            forecast_source_last_seen_at=_DatetimeSubclass(2026, 7, 8, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="recent_brier_score"):
        observation(recent_brier_score=0.2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="evidence_reuse_count"):
        observation(evidence_reuse_count=_DecimalSubclass("4.000000"))

    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)

    with pytest.raises(ValueError, match="must not be after generated_at"):
        report(
            (
                observation(
                    forecast_source_last_seen_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )

    with pytest.raises(ValueError, match="aggregate-safe"):
        observation(region_bucket="https://example.invalid/private")

    with pytest.raises(ValueError, match="unsafe surface"):
        research_weather_event_team_memory_report_payload(
            {
                "team_id": "weather",
                "market_slug": "hidden-slug",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_report_dataclasses_are_frozen_and_decimal_only() -> None:
    summary = report((observation(),))
    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "watch"  # type: ignore[misc]

    dataclass_types = (
        ResearchWeatherEventTeamMemoryReportConfig,
        ResearchWeatherEventTeamMemoryObservation,
        type(summary.rows[0]),
        ResearchWeatherEventTeamMemoryReportReasonCodeCount,
        ResearchWeatherEventTeamMemoryReport,
    )
    for dataclass_type in dataclass_types:
        assert is_dataclass(dataclass_type)
        assert getattr(dataclass_type, "__dataclass_params__").frozen is True
        hints = get_type_hints(dataclass_type)
        for item in fields(dataclass_type):
            hint = hints[item.name]
            origin = get_origin(hint)
            args = get_args(hint)
            if item.name.endswith("_count") or item.name.endswith("_seconds"):
                assert hint is Decimal
            if item.name.endswith("_ratio") or item.name.endswith("_score"):
                assert hint is Decimal or (origin is type(None) and Decimal in args)


def test_source_contains_no_live_db_network_wallet_or_order_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlalchemy",
        "psycopg",
        "psycopg2",
        "web3",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", maxsplit=1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", maxsplit=1)[0] not in forbidden_import_roots

    forbidden_tokens = (
        "wallet",
        "private_key",
        "place_order",
        "cancel_order",
        "live_trading",
        "network_client",
        "db_session",
    )
    lowered = source.lower()
    for token in forbidden_tokens:
        assert token not in lowered
