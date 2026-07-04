from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 4, 21, 0, tzinfo=UTC)
BASE_OBSERVED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-basketball-clutch-rest-digest-test-v0"


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_basketball_clutch_rest_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    digest = module()
    values: dict[str, object] = {
        "config_version": CONFIG_VERSION,
        "clutch_minutes_watch_threshold": d("5.000000"),
        "rest_hours_watch_threshold": d("24.000000"),
        "travel_miles_watch_threshold": d("650.000000"),
        "clutch_load_index_watch_threshold": d("0.650000"),
        "min_signal_count": d("2"),
    }
    values.update(overrides)
    return digest.MarketResearchBasketballClutchRestDigestConfig(**values)


def signal(
    team_game_key: str = "game.nba.bos.20260704",
    team_key: str = "bos",
    *,
    league_key: str = "nba",
    observed_at: datetime = BASE_OBSERVED_AT,
    clutch_minutes_last_game: Decimal = d("3.000000"),
    rest_hours: Decimal = d("36.000000"),
    travel_miles: Decimal = d("120.000000"),
    projected_rotation_minutes: Decimal = d("34.000000"),
    source_count: Decimal = d("2"),
    signal_config_version: str = "basketball-clutch-rest-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchBasketballClutchRestDigestSignal(
        team_game_key=team_game_key,
        team_key=team_key,
        league_key=league_key,
        observed_at=observed_at,
        clutch_minutes_last_game=clutch_minutes_last_game,
        rest_hours=rest_hours,
        travel_miles=travel_miles,
        projected_rotation_minutes=projected_rotation_minutes,
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
    return digest.build_market_research_basketball_clutch_rest_digest(**values)


def test_digest_flags_clutch_minutes_short_rest_travel_and_load() -> None:
    report = build_report(
        signal(
            "game.nba.lal.20260704",
            "lal",
            observed_at=GENERATED_AT - timedelta(hours=4),
            clutch_minutes_last_game=d("4.000000"),
            rest_hours=d("30.000000"),
            travel_miles=d("500.000000"),
            projected_rotation_minutes=d("33.000000"),
            signal_config_version="basketball-clutch-feed-v0",
        ),
        signal(
            "game.nba.lal.20260704",
            "lal",
            observed_at=GENERATED_AT - timedelta(hours=1),
            clutch_minutes_last_game=d("7.000000"),
            rest_hours=d("18.000000"),
            travel_miles=d("820.000000"),
            projected_rotation_minutes=d("39.000000"),
            signal_config_version="basketball-clutch-feed-v1",
        ),
        signal(
            "game.nba.bos.20260704",
            "bos",
            observed_at=GENERATED_AT - timedelta(minutes=50),
            clutch_minutes_last_game=d("2.000000"),
            rest_hours=d("40.000000"),
            travel_miles=d("80.000000"),
            projected_rotation_minutes=d("31.000000"),
        ),
        signal(
            "game.nba.bos.20260704",
            "bos",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            clutch_minutes_last_game=d("3.000000"),
            rest_hours=d("38.000000"),
            travel_miles=d("110.000000"),
            projected_rotation_minutes=d("33.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.research_scope == "basketball clutch rest research digest only"
    assert report.digest_status == "watch"
    assert report.recommended_next_step == "review_report_only_basketball_clutch_rest_digest"
    assert report.team_game_count == d("2")
    assert report.watch_team_game_count == d("1")
    assert report.clear_team_game_count == d("1")
    assert report.limited_history_team_game_count == d("0")
    assert report.signal_count == d("4")
    assert report.clutch_minutes_team_game_count == d("1")
    assert report.short_rest_team_game_count == d("1")
    assert report.travel_load_team_game_count == d("1")
    assert report.clutch_load_index_team_game_count == d("1")
    assert report.max_clutch_load_index == d("0.916666")
    assert report.max_clutch_minutes_last_game == d("7.000000")
    assert report.min_rest_hours == d("18.000000")
    assert report.max_travel_miles == d("820.000000")
    assert report.reason_codes == (
        "basketball_clutch_rest_clutch_load_index_high",
        "basketball_clutch_rest_clutch_minutes_high",
        "basketball_clutch_rest_rest_short",
        "basketball_clutch_rest_travel_high",
    )
    assert report.signal_config_versions == (
        ("game.nba.bos.20260704", "basketball-clutch-rest-source-v0"),
        ("game.nba.lal.20260704", "basketball-clutch-feed-v0"),
        ("game.nba.lal.20260704", "basketball-clutch-feed-v1"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.team_game_key for row in report.rows) == (
        "game.nba.lal.20260704",
        "game.nba.bos.20260704",
    )
    watch_row = report.rows[0]
    assert watch_row.digest_status == "watch"
    assert watch_row.latest_observed_at == GENERATED_AT - timedelta(hours=1)
    assert watch_row.clutch_load_index == d("0.916666")
    assert watch_row.max_clutch_minutes_last_game == d("7.000000")
    assert watch_row.min_rest_hours == d("18.000000")
    assert watch_row.max_travel_miles == d("820.000000")
    assert watch_row.reason_codes == (
        "basketball_clutch_rest_clutch_load_index_high",
        "basketball_clutch_rest_clutch_minutes_high",
        "basketball_clutch_rest_rest_short",
        "basketball_clutch_rest_travel_high",
    )
    assert report.rows[1].digest_status == "clear"
    assert report.rows[1].reason_codes == ("basketball_clutch_rest_clear",)


def test_digest_passes_for_empty_clear_and_limited_history_inputs() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.team_game_count == d("0")
    assert empty_report.signal_count == d("0")
    assert empty_report.rows == ()
    assert empty_report.max_clutch_load_index is None
    assert empty_report.reason_codes == ("basketball_clutch_rest_empty",)

    stable_report = build_report(
        signal("game.nba.alpha.20260704", "atl"),
        signal(
            "game.nba.alpha.20260704",
            "atl",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            rest_hours=d("42.000000"),
            travel_miles=d("150.000000"),
        ),
        signal("game.nba.beta.20260704", "mia"),
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.reason_codes == (
        "basketball_clutch_rest_limited_history",
        "basketball_clutch_rest_passed",
    )
    assert tuple((row.team_game_key, row.digest_status) for row in stable_report.rows) == (
        ("game.nba.beta.20260704", "limited_history"),
        ("game.nba.alpha.20260704", "clear"),
    )


def test_payload_helper_uses_json_ready_scalars_without_sensitive_surface() -> None:
    digest = module()
    report = build_report(
        signal(
            "game.nba.payload.20260704",
            "sea",
            observed_at=datetime(2026, 7, 4, 13, 0, tzinfo=timezone(timedelta(hours=-4))),
            rest_hours=d("28.000000"),
            travel_miles=d("250.000000"),
        ),
        signal(
            "game.nba.payload.20260704",
            "sea",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            clutch_minutes_last_game=d("6.000000"),
            rest_hours=d("20.000000"),
            travel_miles=d("700.000000"),
            projected_rotation_minutes=d("38.000000"),
        ),
    )

    payload = digest.market_research_basketball_clutch_rest_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T21:00:00+00:00"
    assert payload["team_game_count"] == "1"
    assert payload["rows"][0]["latest_observed_at"] == "2026-07-04T20:30:00+00:00"
    assert payload["rows"][0]["clutch_load_index"] == "0.916666"
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

    row = signal()
    with pytest.raises(FrozenInstanceError):
        row.rest_hours = d("30.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="rest_hours must be a Decimal"):
        signal(rest_hours=24)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 18, 0))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(
            signal(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 21, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="clutch_load_index_watch_threshold"):
        config(clutch_load_index_watch_threshold=_DecimalSubclass("0.650000"))

    with pytest.raises(ValueError, match="min_signal_count"):
        config(min_signal_count=d("1.500000"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="signals must not contain duplicate"):
        build_report(signal(signal_config_version="v0"), signal(signal_config_version="v1"))

    with pytest.raises(ValueError, match="team_key must match within team_game_key"):
        build_report(
            signal("game.nba.same.20260704", "nyk"),
            signal(
                "game.nba.same.20260704",
                "bkn",
                observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            ),
        )

    report = build_report(
        signal("game.nba.gamma.20260704", "stl"),
        signal(
            "game.nba.gamma.20260704",
            "stl",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
        ),
    )
    bad_report_values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
    }
    bad_report_values["team_game_count"] = d("2")
    with pytest.raises(ValueError, match="team_game_count"):
        digest.MarketResearchBasketballClutchRestDigestReport(**bad_report_values)


def test_public_numeric_count_and_ratio_fields_are_decimal_only() -> None:
    report = build_report(signal("game.nba.delta.20260704", "phi"))
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
        "src/polymarket_alpha_lab/market_research_basketball_clutch_rest_digest.py",
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
