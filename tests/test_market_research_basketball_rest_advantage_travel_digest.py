from __future__ import annotations

import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 22, 0, tzinfo=UTC)
BASE_OBSERVED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-basketball-rest-advantage-travel-digest-test-v0"


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_basketball_rest_advantage_travel_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": CONFIG_VERSION,
        "short_rest_watch_threshold_hours": d("24.000000"),
        "rest_disadvantage_watch_threshold_hours": d("12.000000"),
        "travel_watch_threshold_miles": d("650.000000"),
        "travel_rest_pressure_index_watch_threshold": d("0.700000"),
        "min_signal_count": d("2.000000"),
    }
    values.update(overrides)
    return module.MarketResearchBasketballRestAdvantageTravelDigestConfig(**values)


def signal(
    team_game_key: str = "game.nba.bos.20260704",
    team_key: str = "bos",
    *,
    opponent_key: str = "nyk",
    league_key: str = "nba",
    market_slug: str = "bos-at-nyk-rest-travel",
    observed_at: datetime = BASE_OBSERVED_AT,
    game_start_at: datetime = GENERATED_AT + timedelta(days=1),
    team_rest_hours: Decimal = d("36.000000"),
    opponent_rest_hours: Decimal = d("36.000000"),
    travel_miles: Decimal = d("120.000000"),
    source_count: Decimal = d("1.000000"),
    signal_config_version: str = "basketball-rest-travel-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketResearchBasketballRestAdvantageTravelDigestSignal(
        team_game_key=team_game_key,
        team_key=team_key,
        opponent_key=opponent_key,
        league_key=league_key,
        market_slug=market_slug,
        observed_at=observed_at,
        game_start_at=game_start_at,
        team_rest_hours=team_rest_hours,
        opponent_rest_hours=opponent_rest_hours,
        travel_miles=travel_miles,
        source_count=source_count,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals: object, **overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "signals": signals,
        "config": config(),
        "generated_at": GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    }
    values.update(overrides)
    return module.build_market_research_basketball_rest_advantage_travel_digest(
        **values,
    )


def test_public_api_uses_digest_named_frozen_dataclasses() -> None:
    module = api()

    for type_name in (
        "MarketResearchBasketballRestAdvantageTravelDigestConfig",
        "MarketResearchBasketballRestAdvantageTravelDigestSignal",
        "MarketResearchBasketballRestAdvantageTravelDigestReasonCodeCount",
        "MarketResearchBasketballRestAdvantageTravelDigestRow",
        "MarketResearchBasketballRestAdvantageTravelDigestReport",
    ):
        type_ = getattr(module, type_name)
        assert is_dataclass(type_)
        assert type_.__dataclass_params__.frozen is True


def test_digest_flags_short_rest_rest_disadvantage_travel_and_pressure() -> None:
    report = build_report(
        signal(
            "game.nba.lal.20260705",
            "lal",
            opponent_key="den",
            market_slug="lal-at-den-rest-travel",
            observed_at=GENERATED_AT - timedelta(hours=3),
            game_start_at=datetime(2026, 7, 5, 20, 30, tzinfo=timezone(timedelta(hours=-6))),
            team_rest_hours=d("30.000000"),
            opponent_rest_hours=d("42.000000"),
            travel_miles=d("500.000000"),
            signal_config_version="basketball-rest-travel-feed-v0",
        ),
        signal(
            "game.nba.lal.20260705",
            "lal",
            opponent_key="den",
            market_slug="lal-at-den-rest-travel",
            observed_at=GENERATED_AT - timedelta(hours=1),
            game_start_at=datetime(2026, 7, 5, 20, 30, tzinfo=timezone(timedelta(hours=-6))),
            team_rest_hours=d("18.000000"),
            opponent_rest_hours=d("48.000000"),
            travel_miles=d("820.000000"),
            signal_config_version="basketball-rest-travel-feed-v1",
        ),
        signal(
            "game.nba.bos.20260705",
            "bos",
            opponent_key="nyk",
            market_slug="bos-at-nyk-rest-travel",
            observed_at=GENERATED_AT - timedelta(minutes=40),
            team_rest_hours=d("42.000000"),
            opponent_rest_hours=d("38.000000"),
            travel_miles=d("110.000000"),
        ),
        signal(
            "game.nba.bos.20260705",
            "bos",
            opponent_key="nyk",
            market_slug="bos-at-nyk-rest-travel",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            team_rest_hours=d("40.000000"),
            opponent_rest_hours=d("38.000000"),
            travel_miles=d("120.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.research_scope == "basketball rest advantage travel research digest only"
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_basketball_rest_advantage_travel_digest"
    )
    assert report.team_game_count == d("2.000000")
    assert report.watch_team_game_count == d("1.000000")
    assert report.clear_team_game_count == d("1.000000")
    assert report.limited_history_team_game_count == d("0.000000")
    assert report.signal_count == d("4.000000")
    assert report.short_rest_team_game_count == d("1.000000")
    assert report.rest_disadvantage_team_game_count == d("1.000000")
    assert report.travel_load_team_game_count == d("1.000000")
    assert report.travel_rest_pressure_index_team_game_count == d("1.000000")
    assert report.max_travel_rest_pressure_index == d("0.916666")
    assert report.min_team_rest_hours == d("18.000000")
    assert report.max_rest_disadvantage_hours == d("30.000000")
    assert report.max_travel_miles == d("820.000000")
    assert report.reason_codes == (
        "basketball_rest_advantage_travel_pressure_high",
        "basketball_rest_advantage_travel_short_rest",
        "basketball_rest_advantage_travel_rest_gap_high",
        "basketball_rest_advantage_travel_miles_high",
    )
    assert report.signal_config_versions == (
        ("game.nba.bos.20260705", "basketball-rest-travel-source-v0"),
        ("game.nba.lal.20260705", "basketball-rest-travel-feed-v0"),
        ("game.nba.lal.20260705", "basketball-rest-travel-feed-v1"),
    )
    assert report.reason_code_counts[0].team_game_ratio == d("0.500000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.team_game_key for row in report.rows) == (
        "game.nba.lal.20260705",
        "game.nba.bos.20260705",
    )
    watch_row = report.rows[0]
    assert watch_row.digest_status == "watch"
    assert watch_row.game_start_at == datetime(2026, 7, 6, 2, 30, tzinfo=UTC)
    assert watch_row.latest_observed_at == GENERATED_AT - timedelta(hours=1)
    assert watch_row.latest_team_rest_hours == d("18.000000")
    assert watch_row.latest_opponent_rest_hours == d("48.000000")
    assert watch_row.rest_disadvantage_hours == d("30.000000")
    assert watch_row.max_travel_miles == d("820.000000")
    assert watch_row.travel_rest_pressure_index == d("0.916666")
    assert watch_row.reason_codes == (
        "basketball_rest_advantage_travel_pressure_high",
        "basketball_rest_advantage_travel_short_rest",
        "basketball_rest_advantage_travel_rest_gap_high",
        "basketball_rest_advantage_travel_miles_high",
    )
    assert report.rows[1].digest_status == "clear"
    assert report.rows[1].reason_codes == ("basketball_rest_advantage_travel_clear",)


def test_validation_rejects_bad_inputs_flags_duplicates_and_inconsistent_records() -> None:
    module = api()

    with pytest.raises(ValueError, match="travel_miles must be a Decimal"):
        signal(travel_miles=_DecimalSubclass("120.000000"))

    with pytest.raises(ValueError, match="team_rest_hours must be a Decimal"):
        signal(team_rest_hours=24)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 18, 0))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(
            signal(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 22, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(minutes=1)))

    with pytest.raises(ValueError, match="game_start_at must not be before generated_at"):
        build_report(signal(game_start_at=GENERATED_AT - timedelta(minutes=1)))

    with pytest.raises(ValueError, match="duplicate team game observations"):
        build_report(
            signal(signal_config_version="feed-v0"),
            signal(signal_config_version="feed-v1"),
        )

    with pytest.raises(ValueError, match="opponent_key must match within team_game_key"):
        build_report(
            signal("game.nba.same.20260705", opponent_key="nyk"),
            signal(
                "game.nba.same.20260705",
                opponent_key="bkn",
                observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            ),
        )

    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    report = build_report(
        signal("game.nba.validation.20260705"),
        signal(
            "game.nba.validation.20260705",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
        ),
    )
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    with pytest.raises(ValueError, match="travel_rest_pressure_index must be at most 1"):
        replace(report.rows[0], travel_rest_pressure_index=d("1.100000"))

    bad_report_values = {
        field_name: getattr(report, field_name)
        for field_name in report.__dataclass_fields__
    }
    bad_report_values["team_game_count"] = d("3.000000")
    with pytest.raises(ValueError, match="team_game_count"):
        module.MarketResearchBasketballRestAdvantageTravelDigestReport(**bad_report_values)


def test_digest_passes_for_empty_clear_and_limited_history_inputs() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.team_game_count == d("0.000000")
    assert empty_report.signal_count == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.max_travel_rest_pressure_index is None
    assert empty_report.min_team_rest_hours is None
    assert empty_report.reason_codes == ("basketball_rest_advantage_travel_empty",)
    assert empty_report.reason_code_counts == (
        api().MarketResearchBasketballRestAdvantageTravelDigestReasonCodeCount(
            reason_code="basketball_rest_advantage_travel_empty",
            team_game_count=d("1.000000"),
            team_game_ratio=d("0.000000"),
        ),
    )

    stable_report = build_report(
        signal("game.nba.alpha.20260705", "atl"),
        signal(
            "game.nba.alpha.20260705",
            "atl",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            team_rest_hours=d("42.000000"),
            opponent_rest_hours=d("40.000000"),
            travel_miles=d("140.000000"),
        ),
        signal("game.nba.beta.20260705", "mia"),
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.reason_codes == (
        "basketball_rest_advantage_travel_limited_history",
        "basketball_rest_advantage_travel_passed",
    )
    assert tuple((row.team_game_key, row.digest_status) for row in stable_report.rows) == (
        ("game.nba.beta.20260705", "limited_history"),
        ("game.nba.alpha.20260705", "clear"),
    )


def test_payload_uses_six_decimal_strings_and_exposes_no_live_mutation_surface() -> None:
    module = api()
    report = build_report(
        signal(
            "game.nba.payload.20260705",
            "sea",
            observed_at=datetime(2026, 7, 4, 15, 30, tzinfo=timezone(timedelta(hours=-4))),
            team_rest_hours=d("28.000000"),
            opponent_rest_hours=d("38.000000"),
            travel_miles=d("250.000000"),
        ),
        signal(
            "game.nba.payload.20260705",
            "sea",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            team_rest_hours=d("18.000000"),
            opponent_rest_hours=d("48.000000"),
            travel_miles=d("820.000000"),
        ),
    )

    payload = module.market_research_basketball_rest_advantage_travel_digest_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T22:00:00+00:00"
    assert payload["team_game_count"] == "1.000000"
    assert payload["signal_count"] == "2.000000"
    assert payload["reason_code_counts"][0]["team_game_ratio"] == "1.000000"
    assert payload["rows"][0]["latest_observed_at"] == "2026-07-04T21:30:00+00:00"
    assert payload["rows"][0]["source_count"] == "2.000000"
    assert payload["rows"][0]["travel_rest_pressure_index"] == "0.916666"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, (Decimal, datetime, float)) for value in _walk_values(payload))

    rendered_payload = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "private_key",
        "wallet",
        "account",
        "balance",
        "order",
        "cancel",
        "replace",
        "signing_key",
        "exchange_mutation",
    ):
        assert forbidden not in rendered_payload

    for public_record in (
        module.MarketResearchBasketballRestAdvantageTravelDigestConfig(),
        signal("game.nba.dataclass.20260705"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal, field.name
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type

    source = inspect.getsource(module).lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "open(",
        "path(",
        "connect(",
        "cursor(",
        "execute(",
        "web3",
        "wallet",
        "private_key",
        "place_order",
        "cancel_order",
        "replace_order",
        "exchange_mutation",
        "secret",
        "token",
        "api_key",
        "os.environ",
        "float(",
    ):
        assert forbidden not in source


def _walk_values(value: object):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_values(item)
    else:
        yield value
