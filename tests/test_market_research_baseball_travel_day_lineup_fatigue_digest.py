import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 3, 20, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_baseball_travel_day_lineup_fatigue_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    game_key: str = "mlb-game-20260703-nyy-bos",
    team_key: str = "nyy",
    opponent_team_key: str = "bos",
    market_slug: str = "yankees-red-sox-moneyline",
    observed_at: datetime = datetime(2026, 7, 3, 19, 30, tzinfo=UTC),
    scheduled_start_at: datetime = datetime(2026, 7, 3, 23, 5, tzinfo=UTC),
    source_age_seconds: str | Decimal = "900.000000",
    travel_distance_miles: str | Decimal = "100.000000",
    timezone_shift_hours: str | Decimal = "0.000000",
    rest_hours_since_last_game: str | Decimal = "30.000000",
    lineup_regular_absences: str | Decimal = "0.000000",
):
    module = digest()
    return module.MarketResearchBaseballTravelDayLineupFatigueObservation(
        source_id=source_id,
        game_key=game_key,
        team_key=team_key,
        opponent_team_key=opponent_team_key,
        market_slug=market_slug,
        observed_at=observed_at,
        scheduled_start_at=scheduled_start_at,
        source_age_seconds=(
            source_age_seconds
            if isinstance(source_age_seconds, Decimal)
            else d(source_age_seconds)
        ),
        travel_distance_miles=(
            travel_distance_miles
            if isinstance(travel_distance_miles, Decimal)
            else d(travel_distance_miles)
        ),
        timezone_shift_hours=(
            timezone_shift_hours
            if isinstance(timezone_shift_hours, Decimal)
            else d(timezone_shift_hours)
        ),
        rest_hours_since_last_game=(
            rest_hours_since_last_game
            if isinstance(rest_hours_since_last_game, Decimal)
            else d(rest_hours_since_last_game)
        ),
        lineup_regular_absences=(
            lineup_regular_absences
            if isinstance(lineup_regular_absences, Decimal)
            else d(lineup_regular_absences)
        ),
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_baseball_travel_day_lineup_fatigue_digest(
        rows,
        config=cfg or module.MarketResearchBaseballTravelDayLineupFatigueDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(
        digest_report,
        module.MarketResearchBaseballTravelDayLineupFatigueDigestReport,
    )
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-baseball-travel-day-lineup-fatigue-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_baseball_travel_day_lineup_fatigue_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.long_travel_count == d("0.000000")
    assert digest_report.timezone_shift_count == d("0.000000")
    assert digest_report.short_rest_count == d("0.000000")
    assert digest_report.lineup_absence_count == d("0.000000")
    assert digest_report.max_fatigue_score == d("0.000000")
    assert digest_report.average_fatigue_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "baseball_travel_day_lineup_fatigue_digest_empty",
    )
    assert digest_report.reason_code_counts == (
        module.MarketResearchBaseballTravelDayLineupFatigueReasonCodeCount(
            reason_code="baseball_travel_day_lineup_fatigue_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_travel_day_lineup_fatigue_blocks_report_only_screening() -> None:
    digest_report = report(
        observation(
            "source-blocked",
            game_key="mlb-game-20260703-sea-nyy",
            team_key="sea",
            opponent_team_key="nyy",
            market_slug="mariners-yankees-moneyline",
            travel_distance_miles="1800.000000",
            timezone_shift_hours="3.000000",
            rest_hours_since_last_game="10.000000",
            lineup_regular_absences="4.000000",
        ),
        observation(
            "source-watch",
            game_key="mlb-game-20260703-lad-sfg",
            team_key="lad",
            opponent_team_key="sfg",
            market_slug="dodgers-giants-moneyline",
            observed_at=datetime(2026, 7, 3, 15, 30, tzinfo=timezone(timedelta(hours=-4))),
            travel_distance_miles="900.000000",
            timezone_shift_hours="1.500000",
            rest_hours_since_last_game="20.000000",
            lineup_regular_absences="2.000000",
        ),
        observation(
            "source-pass",
            game_key="mlb-game-20260703-bos-bal",
            team_key="bos",
            opponent_team_key="bal",
            market_slug="red-sox-orioles-moneyline",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_baseball_travel_day_lineup_fatigue_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.long_travel_count == d("2.000000")
    assert digest_report.timezone_shift_count == d("1.000000")
    assert digest_report.short_rest_count == d("1.000000")
    assert digest_report.lineup_absence_count == d("2.000000")
    assert digest_report.max_fatigue_score == d("0.895833")
    assert digest_report.average_fatigue_score == d("0.454167")
    assert digest_report.reason_codes == (
        "baseball_travel_day_lineup_fatigue_blocked_score_present",
        "baseball_travel_day_lineup_fatigue_watch_score_present",
        "baseball_travel_day_lineup_fatigue_long_travel_present",
        "baseball_travel_day_lineup_fatigue_timezone_shift_present",
        "baseball_travel_day_lineup_fatigue_short_rest_present",
        "baseball_travel_day_lineup_fatigue_lineup_absences_present",
    )
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "mariners-yankees-moneyline",
        "dodgers-giants-moneyline",
        "red-sox-orioles-moneyline",
    )

    blocked, watched, passed = digest_report.rows
    assert blocked.fatigue_status == "blocked"
    assert blocked.fatigue_score == d("0.895833")
    assert blocked.observed_at == datetime(2026, 7, 3, 19, 30, tzinfo=UTC)
    assert blocked.reason_codes == (
        "baseball_travel_day_lineup_fatigue_blocked_score",
        "baseball_travel_day_lineup_fatigue_lineup_absences",
        "baseball_travel_day_lineup_fatigue_long_travel",
        "baseball_travel_day_lineup_fatigue_short_rest",
        "baseball_travel_day_lineup_fatigue_source_fresh",
        "baseball_travel_day_lineup_fatigue_timezone_shift",
    )
    assert watched.fatigue_status == "watch"
    assert watched.fatigue_score == d("0.446667")
    assert watched.observed_at == datetime(2026, 7, 3, 19, 30, tzinfo=UTC)
    assert watched.reason_codes == (
        "baseball_travel_day_lineup_fatigue_lineup_absences",
        "baseball_travel_day_lineup_fatigue_long_travel",
        "baseball_travel_day_lineup_fatigue_source_fresh",
        "baseball_travel_day_lineup_fatigue_watch_score",
    )
    assert passed.fatigue_status == "pass"
    assert passed.fatigue_score == d("0.020000")
    assert passed.reason_codes == (
        "baseball_travel_day_lineup_fatigue_inline",
        "baseball_travel_day_lineup_fatigue_source_fresh",
    )


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        market_slug="beta-watch",
        travel_distance_miles="900.000000",
        timezone_shift_hours="1.500000",
        rest_hours_since_last_game="20.000000",
        lineup_regular_absences="2.000000",
    )
    second = observation(
        "source-blocked",
        market_slug="alpha-blocked",
        travel_distance_miles="1800.000000",
        timezone_shift_hours="3.000000",
        rest_hours_since_last_game="10.000000",
        lineup_regular_absences="4.000000",
    )
    third = observation(
        "source-watch-a",
        market_slug="alpha-watch",
        travel_distance_miles="900.000000",
        timezone_shift_hours="1.500000",
        rest_hours_since_last_game="20.000000",
        lineup_regular_absences="2.000000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "alpha-blocked",
        "alpha-watch",
        "beta-watch",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(sorted(row.reason_codes))
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        "baseball_travel_day_lineup_fatigue_blocked_score_present",
        "baseball_travel_day_lineup_fatigue_watch_score_present",
        "baseball_travel_day_lineup_fatigue_long_travel_present",
        "baseball_travel_day_lineup_fatigue_timezone_shift_present",
        "baseball_travel_day_lineup_fatigue_short_rest_present",
        "baseball_travel_day_lineup_fatigue_lineup_absences_present",
    )


def test_non_default_thresholds_can_downgrade_moderate_fatigue() -> None:
    module = digest()
    cfg = module.MarketResearchBaseballTravelDayLineupFatigueDigestConfig(
        watch_fatigue_score=d("0.600000"),
        blocked_fatigue_score=d("0.850000"),
    )

    digest_report = report(
        observation(
            "source-moderate",
            travel_distance_miles="900.000000",
            timezone_shift_hours="1.500000",
            rest_hours_since_last_game="20.000000",
            lineup_regular_absences="2.000000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_baseball_travel_day_lineup_fatigue_screening"
    )
    assert digest_report.rows[0].fatigue_status == "pass"
    assert digest_report.rows[0].reason_codes == (
        "baseball_travel_day_lineup_fatigue_inline",
        "baseball_travel_day_lineup_fatigue_lineup_absences",
        "baseball_travel_day_lineup_fatigue_long_travel",
        "baseball_travel_day_lineup_fatigue_source_fresh",
    )
    assert digest_report.reason_codes == (
        "baseball_travel_day_lineup_fatigue_long_travel_present",
        "baseball_travel_day_lineup_fatigue_lineup_absences_present",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="travel_distance_miles must be a Decimal"):
        observation(travel_distance_miles=_DecimalSubclass("42.000000"))
    with pytest.raises(ValueError, match="rest_hours_since_last_game must be nonnegative"):
        observation(rest_hours_since_last_game="-1.000000")
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 3, 19, 30))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_baseball_travel_day_lineup_fatigue_digest(
            (),
            config=module.MarketResearchBaseballTravelDayLineupFatigueDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 20, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="blocked_fatigue_score"):
        module.MarketResearchBaseballTravelDayLineupFatigueDigestConfig(
            watch_fatigue_score=d("0.900000"),
            blocked_fatigue_score=d("0.800000"),
        )

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(ValueError, match="fatigue_score must match"):
        replace(valid_row, fatigue_score=d("0.999999"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "baseball_travel_day_lineup_fatigue_inline",
                "baseball_travel_day_lineup_fatigue_watch_score",
            ),
        )

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_rows_and_report() -> None:
    module = digest()

    digest_report = report(observation("source-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.MarketResearchBaseballTravelDayLineupFatigueDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_payload_uses_string_numerics_and_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    digest_report = report(
        observation(
            "source-payload",
            travel_distance_miles="900.000000",
            timezone_shift_hours="1.500000",
            rest_hours_since_last_game="20.000000",
            lineup_regular_absences="2.000000",
        ),
    )

    payload = module.market_research_baseball_travel_day_lineup_fatigue_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["watch_count"] == "1.000000"
    assert payload["rows"][0]["travel_distance_miles"] == "900.000000"
    assert payload["rows"][0]["fatigue_score"] == "0.446667"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T19:30:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "order" not in lowered
                assert "auth" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.MarketResearchBaseballTravelDayLineupFatigueDigestConfig(),
        observation("source-dataclass"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if _is_public_numeric(field_value):
                assert type(field_value) is Decimal, field.name

    source = Path(
        "src/polymarket_alpha_lab/"
        "market_research_baseball_travel_day_lineup_fatigue_digest.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange",
        "fast mode",
    ):
        assert forbidden not in source.lower()


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
