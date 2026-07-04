from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 4, 22, 0, tzinfo=UTC)
BASE_OBSERVED_AT = datetime(2026, 7, 4, 19, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-basketball-back-to-back-altitude-digest-test-v0"


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_basketball_back_to_back_altitude_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    digest = module()
    values: dict[str, object] = {
        "config_version": CONFIG_VERSION,
        "altitude_load_index_watch_threshold": d("0.650000"),
        "back_to_back_game_watch_threshold": d("1.000000"),
        "venue_altitude_feet_watch_threshold": d("4000.000000"),
        "altitude_change_feet_watch_threshold": d("2500.000000"),
        "rest_hour_watch_threshold": d("24.000000"),
        "min_signal_count": d("2.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchBasketballBackToBackAltitudeDigestConfig(**values)


def signal(
    team_schedule_key: str = "schedule.nba.den.20260704",
    team_key: str = "den",
    *,
    league_key: str = "nba",
    observed_at: datetime = BASE_OBSERVED_AT,
    back_to_back_game_count: Decimal = d("0.000000"),
    venue_altitude_feet: Decimal = d("5280.000000"),
    altitude_change_feet: Decimal = d("0.000000"),
    rest_hours: Decimal = d("36.000000"),
    travel_miles: Decimal = d("120.000000"),
    source_count: Decimal = d("2.000000"),
    signal_config_version: str = "basketball-back-to-back-altitude-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchBasketballBackToBackAltitudeDigestSignal(
        team_schedule_key=team_schedule_key,
        team_key=team_key,
        league_key=league_key,
        observed_at=observed_at,
        back_to_back_game_count=back_to_back_game_count,
        venue_altitude_feet=venue_altitude_feet,
        altitude_change_feet=altitude_change_feet,
        rest_hours=rest_hours,
        travel_miles=travel_miles,
        source_count=source_count,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals: object, **overrides: object):
    digest = module()
    values: dict[str, object] = {
        "signals": signals,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return digest.build_market_research_basketball_back_to_back_altitude_digest(
        **values,
    )


def test_digest_flags_back_to_back_altitude_change_rest_and_load() -> None:
    report = build_report(
        signal(
            "schedule.nba.den.20260704",
            "den",
            observed_at=GENERATED_AT - timedelta(hours=5),
            back_to_back_game_count=d("0.000000"),
            venue_altitude_feet=d("5280.000000"),
            altitude_change_feet=d("1200.000000"),
            rest_hours=d("30.000000"),
            travel_miles=d("420.000000"),
            signal_config_version="basketball-altitude-feed-v0",
        ),
        signal(
            "schedule.nba.den.20260704",
            "den",
            observed_at=GENERATED_AT - timedelta(hours=1),
            back_to_back_game_count=d("1.000000"),
            venue_altitude_feet=d("5280.000000"),
            altitude_change_feet=d("4100.000000"),
            rest_hours=d("18.000000"),
            travel_miles=d("900.000000"),
            signal_config_version="basketball-altitude-feed-v1",
        ),
        signal(
            "schedule.nba.bos.20260704",
            "bos",
            observed_at=GENERATED_AT - timedelta(minutes=45),
            back_to_back_game_count=d("0.000000"),
            venue_altitude_feet=d("43.000000"),
            altitude_change_feet=d("100.000000"),
            rest_hours=d("42.000000"),
            travel_miles=d("80.000000"),
        ),
        signal(
            "schedule.nba.bos.20260704",
            "bos",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            back_to_back_game_count=d("0.000000"),
            venue_altitude_feet=d("43.000000"),
            altitude_change_feet=d("160.000000"),
            rest_hours=d("40.000000"),
            travel_miles=d("120.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.research_scope == (
        "basketball back-to-back altitude research digest only"
    )
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_basketball_back_to_back_altitude_digest"
    )
    assert report.team_schedule_count == d("2")
    assert report.watch_team_schedule_count == d("1")
    assert report.clear_team_schedule_count == d("1")
    assert report.limited_history_team_schedule_count == d("0")
    assert report.signal_count == d("4")
    assert report.back_to_back_team_schedule_count == d("1")
    assert report.high_altitude_team_schedule_count == d("1")
    assert report.altitude_change_team_schedule_count == d("1")
    assert report.short_rest_team_schedule_count == d("1")
    assert report.altitude_load_index_team_schedule_count == d("1")
    assert report.max_altitude_load_index == d("0.916666")
    assert report.max_venue_altitude_feet == d("5280.000000")
    assert report.max_altitude_change_feet == d("4100.000000")
    assert report.min_rest_hours == d("18.000000")
    assert report.reason_codes == (
        "basketball_back_to_back_altitude_load_index_high",
        "basketball_back_to_back_altitude_back_to_back_spot",
        "basketball_back_to_back_altitude_high_altitude",
        "basketball_back_to_back_altitude_altitude_change_high",
        "basketball_back_to_back_altitude_rest_short",
    )
    assert report.source_config_versions == (
        ("schedule.nba.bos.20260704", "basketball-back-to-back-altitude-source-v0"),
        ("schedule.nba.den.20260704", "basketball-altitude-feed-v0"),
        ("schedule.nba.den.20260704", "basketball-altitude-feed-v1"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.team_schedule_key for row in report.rows) == (
        "schedule.nba.den.20260704",
        "schedule.nba.bos.20260704",
    )
    watch_row = report.rows[0]
    assert watch_row.digest_status == "watch"
    assert watch_row.latest_observed_at == GENERATED_AT - timedelta(hours=1)
    assert watch_row.altitude_load_index == d("0.916666")
    assert watch_row.max_venue_altitude_feet == d("5280.000000")
    assert watch_row.max_altitude_change_feet == d("4100.000000")
    assert watch_row.min_rest_hours == d("18.000000")
    assert watch_row.reason_codes == (
        "basketball_back_to_back_altitude_load_index_high",
        "basketball_back_to_back_altitude_back_to_back_spot",
        "basketball_back_to_back_altitude_high_altitude",
        "basketball_back_to_back_altitude_altitude_change_high",
        "basketball_back_to_back_altitude_rest_short",
    )
    assert report.rows[1].digest_status == "clear"
    assert report.rows[1].reason_codes == (
        "basketball_back_to_back_altitude_clear",
    )


def test_digest_passes_for_empty_clear_and_limited_history_inputs() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.team_schedule_count == d("0")
    assert empty_report.signal_count == d("0")
    assert empty_report.rows == ()
    assert empty_report.max_altitude_load_index is None
    assert empty_report.reason_codes == ("basketball_back_to_back_altitude_empty",)

    stable_report = build_report(
        signal(
            "schedule.nba.alpha.20260704",
            "atl",
            venue_altitude_feet=d("1050.000000"),
        ),
        signal(
            "schedule.nba.alpha.20260704",
            "atl",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            venue_altitude_feet=d("1050.000000"),
            altitude_change_feet=d("200.000000"),
            rest_hours=d("44.000000"),
            travel_miles=d("140.000000"),
        ),
        signal("schedule.nba.beta.20260704", "mia"),
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.reason_codes == (
        "basketball_back_to_back_altitude_limited_history",
        "basketball_back_to_back_altitude_passed",
    )
    assert tuple((row.team_schedule_key, row.digest_status) for row in stable_report.rows) == (
        ("schedule.nba.beta.20260704", "limited_history"),
        ("schedule.nba.alpha.20260704", "clear"),
    )


def test_payload_uses_decimal_strings_iso_datetimes_and_no_public_numeric_ints() -> None:
    digest = module()
    report = build_report(
        signal(
            "schedule.nba.payload.20260704",
            "uta",
            observed_at=datetime(2026, 7, 4, 14, 0, tzinfo=timezone(timedelta(hours=-4))),
            venue_altitude_feet=d("4226.000000"),
            altitude_change_feet=d("1800.000000"),
            rest_hours=d("28.000000"),
            travel_miles=d("300.000000"),
        ),
        signal(
            "schedule.nba.payload.20260704",
            "uta",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            back_to_back_game_count=d("1.000000"),
            venue_altitude_feet=d("4226.000000"),
            altitude_change_feet=d("3200.000000"),
            rest_hours=d("20.000000"),
            travel_miles=d("760.000000"),
        ),
    )

    payload = digest.market_research_basketball_back_to_back_altitude_digest_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T22:00:00+00:00"
    assert payload["team_schedule_count"] == "1"
    assert payload["rows"][0]["latest_observed_at"] == "2026-07-04T21:30:00+00:00"
    assert payload["rows"][0]["altitude_load_index"] == "0.861111"
    assert payload["rows"][0]["max_venue_altitude_feet"] == "4226"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))

    for value in _walk_payload_values(payload):
        if isinstance(value, bool):
            continue
        assert not isinstance(value, int)


def test_dataclasses_validate_decimal_datetime_flags_duplicates_and_consistency() -> None:
    digest = module()

    row = signal()
    with pytest.raises(FrozenInstanceError):
        row.rest_hours = d("30.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="rest_hours must be a Decimal"):
        signal(rest_hours=24)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 19, 0))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(
            signal(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 22, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="altitude_load_index_watch_threshold"):
        config(altitude_load_index_watch_threshold=_DecimalSubclass("0.650000"))

    with pytest.raises(ValueError, match="min_signal_count"):
        config(min_signal_count=d("1.500000"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="signals must not contain duplicate"):
        build_report(signal(signal_config_version="v0"), signal(signal_config_version="v1"))

    with pytest.raises(ValueError, match="team_key must match within team_schedule_key"):
        build_report(
            signal("schedule.nba.same.20260704", "nyk"),
            signal(
                "schedule.nba.same.20260704",
                "bkn",
                observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            ),
        )

    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))

    report = build_report(
        signal("schedule.nba.gamma.20260704", "stl"),
        signal(
            "schedule.nba.gamma.20260704",
            "stl",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
        ),
    )
    bad_report_values = {field.name: getattr(report, field.name) for field in fields(report)}
    bad_report_values["team_schedule_count"] = d("2")
    with pytest.raises(ValueError, match="team_schedule_count"):
        digest.MarketResearchBasketballBackToBackAltitudeDigestReport(
            **bad_report_values,
        )


def test_public_dataclasses_are_frozen_and_public_numerics_are_decimal_only() -> None:
    digest = module()

    assert digest.__all__ == (
        "DEFAULT_MARKET_RESEARCH_BASKETBALL_BACK_TO_BACK_ALTITUDE_DIGEST_CONFIG_VERSION",
        "BASKETBALL_BACK_TO_BACK_ALTITUDE_RESEARCH_SCOPE",
        "MarketResearchBasketballBackToBackAltitudeDigestConfig",
        "MarketResearchBasketballBackToBackAltitudeDigestSignal",
        "MarketResearchBasketballBackToBackAltitudeDigestReasonCodeCount",
        "MarketResearchBasketballBackToBackAltitudeDigestRow",
        "MarketResearchBasketballBackToBackAltitudeDigestReport",
        "build_market_research_basketball_back_to_back_altitude_digest",
        "market_research_basketball_back_to_back_altitude_digest_payload",
    )
    for exported_name in digest.__all__:
        value = getattr(digest, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    report = build_report(signal("schedule.nba.delta.20260704", "phi"))
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].digest_status = "watch"

    for item in (report, report.rows[0]):
        for field in fields(item):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_index")
                or field.name.endswith("_hours")
                or field.name.endswith("_miles")
                or field.name.endswith("_feet")
                or field.name.endswith("_threshold")
            ):
                field_value = getattr(item, field.name)
                if field_value is not None:
                    assert type(field_value) is Decimal


def test_module_scope_has_no_io_live_trading_float_or_sensitive_surface() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/"
        "market_research_basketball_back_to_back_altitude_digest.py",
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
