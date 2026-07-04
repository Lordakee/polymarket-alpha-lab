from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 4, 23, 0, tzinfo=UTC)
BASE_OBSERVED_AT = datetime(2026, 7, 4, 20, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-basketball-altitude-travel-fatigue-digest-test-v0"


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_basketball_altitude_travel_fatigue_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    digest = module()
    values: dict[str, object] = {
        "config_version": CONFIG_VERSION,
        "fatigue_pressure_index_watch_threshold": d("0.650000"),
        "venue_altitude_feet_watch_threshold": d("4000.000000"),
        "altitude_change_feet_watch_threshold": d("2500.000000"),
        "rest_day_watch_threshold": d("1.000000"),
        "back_to_back_game_watch_threshold": d("1.000000"),
        "travel_mile_watch_threshold": d("750.000000"),
        "rotation_depth_watch_threshold": d("8.000000"),
        "min_signal_count": d("2.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchBasketballAltitudeTravelFatigueDigestConfig(**values)


def signal(
    team_event_key: str = "event.nba.den-lal.20260704.den",
    team_key: str = "den",
    *,
    event_key: str = "event.nba.den-lal.20260704",
    league_key: str = "nba",
    observed_at: datetime = BASE_OBSERVED_AT,
    venue_altitude_feet: Decimal = d("5280.000000"),
    altitude_change_feet: Decimal = d("0.000000"),
    rest_days: Decimal = d("2.000000"),
    back_to_back_game_count: Decimal = d("0.000000"),
    travel_miles: Decimal = d("120.000000"),
    available_rotation_players: Decimal = d("10.000000"),
    source_count: Decimal = d("2.000000"),
    signal_config_version: str = "basketball-altitude-travel-fatigue-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchBasketballAltitudeTravelFatigueDigestSignal(
        team_event_key=team_event_key,
        event_key=event_key,
        team_key=team_key,
        league_key=league_key,
        observed_at=observed_at,
        venue_altitude_feet=venue_altitude_feet,
        altitude_change_feet=altitude_change_feet,
        rest_days=rest_days,
        back_to_back_game_count=back_to_back_game_count,
        travel_miles=travel_miles,
        available_rotation_players=available_rotation_players,
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
    return digest.build_market_research_basketball_altitude_travel_fatigue_digest(
        **values,
    )


def test_digest_flags_altitude_rest_travel_back_to_back_and_rotation_pressure() -> None:
    report = build_report(
        signal(
            "event.nba.den-lal.20260704.den",
            "den",
            event_key="event.nba.den-lal.20260704",
            observed_at=GENERATED_AT - timedelta(hours=5),
            venue_altitude_feet=d("5280.000000"),
            altitude_change_feet=d("1600.000000"),
            rest_days=d("1.000000"),
            back_to_back_game_count=d("0.000000"),
            travel_miles=d("420.000000"),
            available_rotation_players=d("8.000000"),
            signal_config_version="basketball-fatigue-feed-v0",
        ),
        signal(
            "event.nba.den-lal.20260704.den",
            "den",
            event_key="event.nba.den-lal.20260704",
            observed_at=GENERATED_AT - timedelta(hours=1),
            venue_altitude_feet=d("5280.000000"),
            altitude_change_feet=d("4100.000000"),
            rest_days=d("0.000000"),
            back_to_back_game_count=d("1.000000"),
            travel_miles=d("900.000000"),
            available_rotation_players=d("6.000000"),
            signal_config_version="basketball-fatigue-feed-v1",
        ),
        signal(
            "event.nba.bos-mia.20260704.bos",
            "bos",
            event_key="event.nba.bos-mia.20260704",
            observed_at=GENERATED_AT - timedelta(minutes=45),
            venue_altitude_feet=d("43.000000"),
            altitude_change_feet=d("100.000000"),
            rest_days=d("2.000000"),
            back_to_back_game_count=d("0.000000"),
            travel_miles=d("80.000000"),
            available_rotation_players=d("10.000000"),
        ),
        signal(
            "event.nba.bos-mia.20260704.bos",
            "bos",
            event_key="event.nba.bos-mia.20260704",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            venue_altitude_feet=d("43.000000"),
            altitude_change_feet=d("160.000000"),
            rest_days=d("2.000000"),
            back_to_back_game_count=d("0.000000"),
            travel_miles=d("120.000000"),
            available_rotation_players=d("10.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.research_scope == (
        "basketball altitude travel fatigue phase 1 research digest only"
    )
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_basketball_altitude_travel_fatigue_digest"
    )
    assert report.team_event_count == d("2.000000")
    assert report.watch_team_event_count == d("1.000000")
    assert report.clear_team_event_count == d("1.000000")
    assert report.limited_history_team_event_count == d("0.000000")
    assert report.signal_count == d("4.000000")
    assert report.high_altitude_team_event_count == d("1.000000")
    assert report.altitude_change_team_event_count == d("1.000000")
    assert report.short_rest_team_event_count == d("1.000000")
    assert report.back_to_back_team_event_count == d("1.000000")
    assert report.travel_fatigue_team_event_count == d("1.000000")
    assert report.rotation_depth_team_event_count == d("1.000000")
    assert report.fatigue_pressure_index_team_event_count == d("1.000000")
    assert report.max_fatigue_pressure_index == d("0.944444")
    assert report.max_venue_altitude_feet == d("5280.000000")
    assert report.max_altitude_change_feet == d("4100.000000")
    assert report.min_rest_days == d("0.000000")
    assert report.max_travel_miles == d("900.000000")
    assert report.min_available_rotation_players == d("6.000000")
    assert report.reason_codes == (
        "basketball_altitude_travel_fatigue_pressure_index_high",
        "basketball_altitude_travel_fatigue_high_altitude",
        "basketball_altitude_travel_fatigue_altitude_change_high",
        "basketball_altitude_travel_fatigue_rest_days_short",
        "basketball_altitude_travel_fatigue_back_to_back_spot",
        "basketball_altitude_travel_fatigue_travel_high",
        "basketball_altitude_travel_fatigue_rotation_depth_short",
    )
    assert report.source_config_versions == (
        ("event.nba.bos-mia.20260704.bos", "basketball-altitude-travel-fatigue-source-v0"),
        ("event.nba.den-lal.20260704.den", "basketball-fatigue-feed-v0"),
        ("event.nba.den-lal.20260704.den", "basketball-fatigue-feed-v1"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.team_event_key for row in report.rows) == (
        "event.nba.den-lal.20260704.den",
        "event.nba.bos-mia.20260704.bos",
    )
    watch_row = report.rows[0]
    assert watch_row.digest_status == "watch"
    assert watch_row.latest_observed_at == GENERATED_AT - timedelta(hours=1)
    assert watch_row.fatigue_pressure_index == d("0.944444")
    assert watch_row.max_venue_altitude_feet == d("5280.000000")
    assert watch_row.max_altitude_change_feet == d("4100.000000")
    assert watch_row.min_rest_days == d("0.000000")
    assert watch_row.max_travel_miles == d("900.000000")
    assert watch_row.min_available_rotation_players == d("6.000000")
    assert watch_row.reason_codes == report.reason_codes
    assert report.rows[1].digest_status == "clear"
    assert report.rows[1].reason_codes == (
        "basketball_altitude_travel_fatigue_clear",
    )


def test_digest_passes_for_empty_clear_and_limited_history_inputs() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.team_event_count == d("0.000000")
    assert empty_report.signal_count == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.max_fatigue_pressure_index is None
    assert empty_report.reason_codes == ("basketball_altitude_travel_fatigue_empty",)

    stable_report = build_report(
        signal(
            "event.nba.atl-chi.20260704.atl",
            "atl",
            event_key="event.nba.atl-chi.20260704",
            venue_altitude_feet=d("1050.000000"),
        ),
        signal(
            "event.nba.atl-chi.20260704.atl",
            "atl",
            event_key="event.nba.atl-chi.20260704",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            venue_altitude_feet=d("1050.000000"),
            altitude_change_feet=d("200.000000"),
            rest_days=d("2.000000"),
            travel_miles=d("140.000000"),
            available_rotation_players=d("10.000000"),
        ),
        signal(
            "event.nba.mia-orl.20260704.mia",
            "mia",
            event_key="event.nba.mia-orl.20260704",
        ),
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.reason_codes == (
        "basketball_altitude_travel_fatigue_limited_history",
        "basketball_altitude_travel_fatigue_passed",
    )
    assert tuple((row.team_event_key, row.digest_status) for row in stable_report.rows) == (
        ("event.nba.mia-orl.20260704.mia", "limited_history"),
        ("event.nba.atl-chi.20260704.atl", "clear"),
    )


def test_payload_uses_six_decimal_strings_iso_datetimes_and_no_sensitive_surface() -> None:
    digest = module()
    report = build_report(
        signal(
            "event.nba.uta-phx.20260704.uta",
            "uta",
            event_key="event.nba.uta-phx.20260704",
            observed_at=datetime(2026, 7, 4, 15, 0, tzinfo=timezone(timedelta(hours=-4))),
            venue_altitude_feet=d("4226.000000"),
            altitude_change_feet=d("1800.000000"),
            rest_days=d("1.000000"),
            travel_miles=d("300.000000"),
            available_rotation_players=d("8.000000"),
        ),
        signal(
            "event.nba.uta-phx.20260704.uta",
            "uta",
            event_key="event.nba.uta-phx.20260704",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            venue_altitude_feet=d("4226.000000"),
            altitude_change_feet=d("3000.000000"),
            rest_days=d("0.000000"),
            back_to_back_game_count=d("1.000000"),
            travel_miles=d("760.000000"),
            available_rotation_players=d("7.000000"),
        ),
    )

    payload = digest.market_research_basketball_altitude_travel_fatigue_digest_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T23:00:00+00:00"
    assert payload["team_event_count"] == "1.000000"
    assert payload["rows"][0]["latest_observed_at"] == "2026-07-04T22:30:00+00:00"
    assert payload["rows"][0]["fatigue_pressure_index"] == "0.888888"
    assert payload["rows"][0]["max_venue_altitude_feet"] == "4226.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))

    for value in _walk_payload_values(payload):
        if isinstance(value, bool):
            continue
        assert not isinstance(value, int)

    payload_text = repr(payload).lower()
    for forbidden in (
        "wallet",
        "broker",
        "account",
        "advice",
        "auth",
        "signing",
        "submit",
        "cancel",
        "secret",
        "token",
        "exchange_mutation",
    ):
        assert forbidden not in payload_text


def test_dataclasses_validate_decimal_datetime_flags_duplicates_and_consistency() -> None:
    digest = module()

    row = signal()
    with pytest.raises(FrozenInstanceError):
        row.rest_days = d("1.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="rest_days must be a Decimal"):
        signal(rest_days=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 20, 0))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(
            signal(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 23, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="fatigue_pressure_index_watch_threshold"):
        config(fatigue_pressure_index_watch_threshold=_DecimalSubclass("0.650000"))

    with pytest.raises(ValueError, match="min_signal_count"):
        config(min_signal_count=d("1.500000"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="signals must not contain duplicate"):
        build_report(signal(signal_config_version="v0"), signal(signal_config_version="v1"))

    with pytest.raises(ValueError, match="team_key must match within team_event_key"):
        build_report(
            signal("event.nba.same.20260704.nyk", "nyk"),
            signal(
                "event.nba.same.20260704.nyk",
                "bkn",
                observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            ),
        )

    with pytest.raises(ValueError, match="event_key must match within team_event_key"):
        build_report(
            signal("event.nba.same.20260704.nyk", "nyk", event_key="event.nba.one"),
            signal(
                "event.nba.same.20260704.nyk",
                "nyk",
                event_key="event.nba.two",
                observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            ),
        )

    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))

    report = build_report(
        signal("event.nba.gamma.20260704.stl", "stl", event_key="event.nba.gamma"),
        signal(
            "event.nba.gamma.20260704.stl",
            "stl",
            event_key="event.nba.gamma",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
        ),
    )
    bad_report_values = {field.name: getattr(report, field.name) for field in fields(report)}
    bad_report_values["team_event_count"] = d("2.000000")
    with pytest.raises(ValueError, match="team_event_count"):
        digest.MarketResearchBasketballAltitudeTravelFatigueDigestReport(
            **bad_report_values,
        )


def test_public_dataclasses_are_frozen_and_public_numerics_are_decimal_only() -> None:
    digest = module()

    assert digest.__all__ == (
        "DEFAULT_MARKET_RESEARCH_BASKETBALL_ALTITUDE_TRAVEL_FATIGUE_DIGEST_CONFIG_VERSION",
        "BASKETBALL_ALTITUDE_TRAVEL_FATIGUE_RESEARCH_SCOPE",
        "MarketResearchBasketballAltitudeTravelFatigueDigestConfig",
        "MarketResearchBasketballAltitudeTravelFatigueDigestSignal",
        "MarketResearchBasketballAltitudeTravelFatigueDigestReasonCodeCount",
        "MarketResearchBasketballAltitudeTravelFatigueDigestRow",
        "MarketResearchBasketballAltitudeTravelFatigueDigestReport",
        "build_market_research_basketball_altitude_travel_fatigue_digest",
        "market_research_basketball_altitude_travel_fatigue_digest_payload",
    )
    for exported_name in digest.__all__:
        value = getattr(digest, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    report = build_report(signal("event.nba.delta.20260704.phi", "phi"))
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
                or field.name.endswith("_days")
                or field.name.endswith("_miles")
                or field.name.endswith("_feet")
                or field.name.endswith("_players")
                or field.name.endswith("_threshold")
            ):
                field_value = getattr(item, field.name)
                if field_value is not None:
                    assert type(field_value) is Decimal


def test_module_scope_has_no_io_live_trading_float_or_mutation_surface() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/"
        "market_research_basketball_altitude_travel_fatigue_digest.py",
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
        "supabase",
        "sqlite",
        "subprocess",
        "float(",
        "exchange_mutation",
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
        "supabase",
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
