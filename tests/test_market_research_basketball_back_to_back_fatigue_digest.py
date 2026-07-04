from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 4, 20, 0, tzinfo=UTC)
BASE_OBSERVED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-basketball-back-to-back-fatigue-digest-test-v0"


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_basketball_back_to_back_fatigue_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides):
    digest = module()
    values = {
        "config_version": CONFIG_VERSION,
        "fatigue_index_watch_threshold": d("0.650000"),
        "back_to_back_game_watch_threshold": d("1.000000"),
        "travel_mile_watch_threshold": d("700.000000"),
        "rest_hour_watch_threshold": d("22.000000"),
        "minutes_load_watch_threshold": d("38.000000"),
        "min_snapshot_count": d("2.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchBasketballBackToBackFatigueDigestConfig(**values)


def snapshot(
    team_schedule_key: str = "schedule.nba.bos",
    team_key: str = "bos",
    *,
    league_key: str = "nba",
    observed_at: datetime = BASE_OBSERVED_AT,
    back_to_back_game_count: Decimal = d("0.000000"),
    rest_hours: Decimal = d("36.000000"),
    travel_miles: Decimal = d("120.000000"),
    projected_starter_minutes: Decimal = d("34.000000"),
    source_count: Decimal = d("2.000000"),
    source_config_version: str = "basketball-back-to-back-fatigue-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchBasketballBackToBackFatigueDigestSnapshot(
        team_schedule_key=team_schedule_key,
        team_key=team_key,
        league_key=league_key,
        observed_at=observed_at,
        back_to_back_game_count=back_to_back_game_count,
        rest_hours=rest_hours,
        travel_miles=travel_miles,
        projected_starter_minutes=projected_starter_minutes,
        source_count=source_count,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*snapshots, **overrides):
    digest = module()
    values = {
        "snapshots": snapshots,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return digest.build_market_research_basketball_back_to_back_fatigue_digest(**values)


def test_digest_flags_back_to_back_travel_rest_and_minutes_fatigue() -> None:
    report = build_report(
        snapshot(
            "schedule.nba.lal",
            "lal",
            observed_at=GENERATED_AT - timedelta(hours=5),
            back_to_back_game_count=d("0.000000"),
            rest_hours=d("30.000000"),
            travel_miles=d("420.000000"),
            projected_starter_minutes=d("35.000000"),
            source_config_version="basketball-schedule-feed-v0",
        ),
        snapshot(
            "schedule.nba.lal",
            "lal",
            observed_at=GENERATED_AT - timedelta(hours=1),
            back_to_back_game_count=d("1.000000"),
            rest_hours=d("18.000000"),
            travel_miles=d("900.000000"),
            projected_starter_minutes=d("40.000000"),
            source_config_version="basketball-schedule-feed-v1",
        ),
        snapshot(
            "schedule.nba.bos",
            "bos",
            observed_at=GENERATED_AT - timedelta(minutes=45),
            back_to_back_game_count=d("0.000000"),
            rest_hours=d("42.000000"),
            travel_miles=d("80.000000"),
            projected_starter_minutes=d("32.000000"),
        ),
        snapshot(
            "schedule.nba.bos",
            "bos",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            back_to_back_game_count=d("0.000000"),
            rest_hours=d("40.000000"),
            travel_miles=d("120.000000"),
            projected_starter_minutes=d("34.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_basketball_back_to_back_fatigue_digest"
    )
    assert report.team_schedule_count == d("2")
    assert report.fatigued_team_schedule_count == d("1")
    assert report.clear_team_schedule_count == d("1")
    assert report.snapshot_count == d("4")
    assert report.back_to_back_team_schedule_count == d("1")
    assert report.travel_fatigue_team_schedule_count == d("1")
    assert report.short_rest_team_schedule_count == d("1")
    assert report.minutes_load_team_schedule_count == d("1")
    assert report.max_fatigue_index == d("0.892857")
    assert report.max_travel_miles == d("900.000000")
    assert report.min_rest_hours == d("18.000000")
    assert report.max_projected_starter_minutes == d("40.000000")
    assert report.reason_codes == (
        "basketball_back_to_back_fatigue_back_to_back_spot",
        "basketball_back_to_back_fatigue_minutes_load_high",
        "basketball_back_to_back_fatigue_rest_short",
        "basketball_back_to_back_fatigue_travel_high",
    )
    assert report.source_config_versions == (
        ("schedule.nba.bos", "basketball-back-to-back-fatigue-source-v0"),
        ("schedule.nba.lal", "basketball-schedule-feed-v0"),
        ("schedule.nba.lal", "basketball-schedule-feed-v1"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.team_schedule_key for row in report.rows) == (
        "schedule.nba.lal",
        "schedule.nba.bos",
    )
    fatigued = report.rows[0]
    assert fatigued.digest_status == "fatigued"
    assert fatigued.latest_observed_at == GENERATED_AT - timedelta(hours=1)
    assert fatigued.fatigue_index == d("0.892857")
    assert fatigued.max_travel_miles == d("900.000000")
    assert fatigued.min_rest_hours == d("18.000000")
    assert fatigued.reason_codes == (
        "basketball_back_to_back_fatigue_back_to_back_spot",
        "basketball_back_to_back_fatigue_minutes_load_high",
        "basketball_back_to_back_fatigue_rest_short",
        "basketball_back_to_back_fatigue_travel_high",
    )
    assert report.rows[1].digest_status == "clear"
    assert report.rows[1].reason_codes == ("basketball_back_to_back_fatigue_clear",)


def test_digest_passes_for_empty_clear_and_limited_history_inputs() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.team_schedule_count == d("0")
    assert empty_report.snapshot_count == d("0")
    assert empty_report.rows == ()
    assert empty_report.max_fatigue_index is None
    assert empty_report.reason_codes == ("basketball_back_to_back_fatigue_empty",)

    stable_report = build_report(
        snapshot("schedule.nba.alpha", "atl"),
        snapshot(
            "schedule.nba.alpha",
            "atl",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            rest_hours=d("44.000000"),
            travel_miles=d("140.000000"),
        ),
        snapshot("schedule.nba.beta", "mia"),
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.reason_codes == (
        "basketball_back_to_back_fatigue_limited_history",
        "basketball_back_to_back_fatigue_passed",
    )
    assert tuple((row.team_schedule_key, row.digest_status) for row in stable_report.rows) == (
        ("schedule.nba.beta", "limited_history"),
        ("schedule.nba.alpha", "clear"),
    )


def test_payload_helper_uses_json_ready_scalars_without_sensitive_surface() -> None:
    digest = module()
    report = build_report(
        snapshot(
            "schedule.nba.payload",
            "sea",
            observed_at=datetime(2026, 7, 4, 13, 0, tzinfo=timezone(timedelta(hours=-4))),
            rest_hours=d("24.000000"),
            travel_miles=d("300.000000"),
        ),
        snapshot(
            "schedule.nba.payload",
            "sea",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            back_to_back_game_count=d("1.000000"),
            rest_hours=d("20.000000"),
            travel_miles=d("760.000000"),
            projected_starter_minutes=d("39.000000"),
        ),
    )

    payload = digest.market_research_basketball_back_to_back_fatigue_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T20:00:00+00:00"
    assert payload["team_schedule_count"] == "1"
    assert payload["rows"][0]["latest_observed_at"] == "2026-07-04T19:30:00+00:00"
    assert payload["rows"][0]["fatigue_index"] == "0.821428"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))

    payload_text = repr(payload).lower()
    for forbidden in (
        "wallet",
        "broker",
        "order",
        "account",
        "advice",
        "auth",
        "signing",
        "submit",
        "cancel",
        "secret",
        "token",
    ):
        assert forbidden not in payload_text


def test_dataclasses_validate_decimal_datetime_flags_consistency_and_types() -> None:
    digest = module()

    row = snapshot()
    with pytest.raises(FrozenInstanceError):
        row.rest_hours = d("30.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="rest_hours must be a Decimal"):
        snapshot(rest_hours=24)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        snapshot(observed_at=datetime(2026, 7, 4, 18, 0))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(
            snapshot(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 20, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="fatigue_index_watch_threshold"):
        config(fatigue_index_watch_threshold=_DecimalSubclass("0.650000"))

    with pytest.raises(ValueError, match="min_snapshot_count"):
        config(min_snapshot_count=d("1.500000"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="snapshots must not contain duplicate"):
        build_report(snapshot(source_config_version="v0"), snapshot(source_config_version="v1"))

    with pytest.raises(ValueError, match="team_key must match within team_schedule_key"):
        build_report(
            snapshot("schedule.nba.same", "nyk"),
            snapshot(
                "schedule.nba.same",
                "bkn",
                observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            ),
        )

    report = build_report(
        snapshot("schedule.nba.gamma", "stl"),
        snapshot(
            "schedule.nba.gamma",
            "stl",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
        ),
    )
    bad_report_values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
    }
    bad_report_values["team_schedule_count"] = d("2")
    with pytest.raises(ValueError, match="team_schedule_count"):
        digest.MarketResearchBasketballBackToBackFatigueDigestReport(**bad_report_values)


def test_public_numeric_count_and_ratio_fields_are_decimal_only() -> None:
    report = build_report(snapshot("schedule.nba.delta", "phi"))
    row = report.rows[0]

    for value in (report, row):
        for field in fields(value):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_index")
                or field.name.endswith("_hours")
                or field.name.endswith("_miles")
                or field.name.endswith("_minutes")
            ):
                field_value = getattr(value, field.name)
                if field_value is not None:
                    assert type(field_value) is Decimal


def test_module_scope_has_no_io_live_trading_float_or_durable_store_surface() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/"
        "market_research_basketball_back_to_back_fatigue_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()

    for forbidden in (
        "live trading",
        "wallet",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
        "auth",
        "private",
        "secret",
        "token",
        "open(",
        "requests",
        "http",
        "socket",
        "psycopg",
        "sqlite",
        "sql",
        "float(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _walk_payload_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_payload_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_payload_values(item)
    else:
        yield value
