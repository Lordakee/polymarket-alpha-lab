from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 4, 15, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab"
        ".market_research_baseball_starting_pitcher_late_swap_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str,
    *,
    game_id: str = "mlb-20260704-nyy-bos",
    market_slug: str = "yankees-red-sox-moneyline",
    team_id: str = "nyy",
    scheduled_starter_id: str = "pitcher-cole",
    current_listed_starter_id: str = "pitcher-cole",
    starter_status: str = "confirmed",
    minutes_until_first_pitch: str = "240.000000",
    lineup_confirmation_age_minutes: str = "30.000000",
    scratch_probability: str = "0.040000",
    market_probability: str = "0.520000",
    liquidity_usd: str = "1200.000000",
    source_row_count: str = "1",
    observed_at: datetime = datetime(2026, 7, 4, 12, 30, tzinfo=UTC),
    reason_codes: tuple[str, ...] = ("baseball_starting_pitcher_confirmed",),
):
    digest = api()
    return digest.BaseballStartingPitcherLateSwapObservation(
        source_id=source_id,
        game_id=game_id,
        market_slug=market_slug,
        team_id=team_id,
        scheduled_starter_id=scheduled_starter_id,
        current_listed_starter_id=current_listed_starter_id,
        starter_status=starter_status,
        minutes_until_first_pitch=d(minutes_until_first_pitch),
        lineup_confirmation_age_minutes=d(lineup_confirmation_age_minutes),
        scratch_probability=d(scratch_probability),
        market_probability=d(market_probability),
        liquidity_usd=d(liquidity_usd),
        source_row_count=d(source_row_count),
        observed_at=observed_at,
        reason_codes=reason_codes,
    )


def report(*rows, config=None):
    digest = api()
    return digest.build_market_research_baseball_starting_pitcher_late_swap_digest(
        rows,
        config=config or digest.BaseballStartingPitcherLateSwapDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_digest_reduces_late_swap_signals_with_deterministic_rows() -> None:
    digest_report = report(
        observation(
            "source-pass",
            game_id="mlb-20260704-lad-sf",
            market_slug="dodgers-giants-moneyline",
            team_id="lad",
            scheduled_starter_id="pitcher-yamamoto",
            current_listed_starter_id="pitcher-yamamoto",
            starter_status="confirmed",
            minutes_until_first_pitch="360.000000",
            scratch_probability="0.030000",
            market_probability="0.610000",
            liquidity_usd="950.000000",
            observed_at=datetime(2026, 7, 4, 9, 0, tzinfo=UTC),
            reason_codes=("baseball_starting_pitcher_confirmed",),
        ),
        observation(
            "source-watch",
            game_id="mlb-20260704-sea-hou",
            market_slug="mariners-astros-moneyline",
            team_id="sea",
            scheduled_starter_id="pitcher-kirby",
            current_listed_starter_id="pitcher-kirby",
            starter_status="questionable",
            minutes_until_first_pitch="90.000000",
            lineup_confirmation_age_minutes="155.000000",
            scratch_probability="0.180000",
            market_probability="0.480000",
            liquidity_usd="840.000000",
            observed_at=datetime(2026, 7, 4, 11, 30, tzinfo=UTC),
            reason_codes=(
                "baseball_starting_pitcher_questionable",
                "baseball_starting_pitcher_confirmation_stale",
            ),
        ),
        observation(
            "source-blocked",
            game_id="mlb-20260704-nyy-bos",
            market_slug="yankees-red-sox-moneyline",
            team_id="nyy",
            scheduled_starter_id="pitcher-cole",
            current_listed_starter_id="pitcher-schmidt",
            starter_status="changed",
            minutes_until_first_pitch="45.000000",
            scratch_probability="0.380000",
            market_probability="0.520000",
            liquidity_usd="1800.000000",
            source_row_count="2",
            observed_at=datetime(2026, 7, 4, 12, 45, tzinfo=UTC),
            reason_codes=("baseball_starting_pitcher_changed",),
        ),
    )

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-baseball-starting-pitcher-late-swap-digest-v0"
    )
    assert digest_report.source_row_count == d("4")
    assert digest_report.observation_count == d("3")
    assert digest_report.blocked_swap_risk_count == d("1")
    assert digest_report.watch_swap_risk_count == d("1")
    assert digest_report.pass_swap_risk_count == d("1")
    assert digest_report.changed_starter_count == d("1")
    assert digest_report.max_scratch_probability == d("0.380000")
    assert digest_report.average_scratch_probability == d("0.196667")
    assert digest_report.min_minutes_until_first_pitch == d("45.000000")
    assert digest_report.digest_status == "blocked"
    assert digest_report.reason_codes == (
        "baseball_starting_pitcher_late_swap_blocked_risk_present",
        "baseball_starting_pitcher_late_swap_changed_starter_present",
        "baseball_starting_pitcher_late_swap_watch_risk_present",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    assert tuple(row.market_slug for row in digest_report.risk_rows) == (
        "yankees-red-sox-moneyline",
        "mariners-astros-moneyline",
        "dodgers-giants-moneyline",
    )
    assert digest_report.risk_rows[0].swap_risk_status == "blocked"
    assert digest_report.risk_rows[0].reason_codes == (
        "baseball_starting_pitcher_late_swap_changed_starter",
        "baseball_starting_pitcher_late_swap_high_scratch_probability",
    )
    assert digest_report.risk_rows[1].swap_risk_status == "watch"
    assert digest_report.risk_rows[1].reason_codes == (
        "baseball_starting_pitcher_late_swap_watch_scratch_probability",
        "baseball_starting_pitcher_late_swap_questionable_near_first_pitch",
        "baseball_starting_pitcher_late_swap_stale_confirmation_near_first_pitch",
    )
    assert digest_report.risk_rows[2].swap_risk_status == "pass"
    assert digest_report.risk_rows[2].reason_codes == (
        "baseball_starting_pitcher_late_swap_clear",
    )


def test_empty_digest_is_readonly_report_only_and_decimal_zeroed() -> None:
    digest_report = report()

    assert digest_report.source_row_count == d("0")
    assert digest_report.observation_count == d("0")
    assert digest_report.blocked_swap_risk_count == d("0")
    assert digest_report.watch_swap_risk_count == d("0")
    assert digest_report.pass_swap_risk_count == d("0")
    assert digest_report.changed_starter_count == d("0")
    assert digest_report.max_scratch_probability == d("0.000000")
    assert digest_report.average_scratch_probability == d("0.000000")
    assert digest_report.min_minutes_until_first_pitch == d("0.000000")
    assert digest_report.digest_status == "pass"
    assert digest_report.reason_codes == (
        "baseball_starting_pitcher_late_swap_digest_clear",
    )
    assert digest_report.risk_rows == ()
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_sorting_is_deterministic_for_equal_risk_scores() -> None:
    row_b = observation(
        "source-b",
        game_id="mlb-20260704-bbb-ccc",
        market_slug="beta-market",
        team_id="bbb",
        scratch_probability="0.280000",
        observed_at=datetime(2026, 7, 4, 10, 0, tzinfo=UTC),
    )
    row_a = observation(
        "source-a",
        game_id="mlb-20260704-aaa-ccc",
        market_slug="alpha-market",
        team_id="aaa",
        scratch_probability="0.280000",
        observed_at=datetime(2026, 7, 4, 10, 0, tzinfo=UTC),
    )
    digest_report = report(row_b, row_a)

    assert tuple(row.source_id for row in digest_report.risk_rows) == (
        "source-a",
        "source-b",
    )
    assert report(row_a, row_b).risk_rows == digest_report.risk_rows


def test_non_default_thresholds_can_keep_high_probability_on_watch() -> None:
    digest = api()
    custom_config = digest.BaseballStartingPitcherLateSwapDigestConfig(
        watch_scratch_probability=d("0.100000"),
        blocked_scratch_probability=d("0.400000"),
    )

    digest_report = report(
        observation("source-threshold", scratch_probability="0.260000"),
        config=custom_config,
    )

    assert digest_report.digest_status == "watch"
    assert digest_report.blocked_swap_risk_count == d("0")
    assert digest_report.watch_swap_risk_count == d("1")
    assert digest_report.risk_rows[0].reason_codes == (
        "baseball_starting_pitcher_late_swap_watch_scratch_probability",
    )


def test_digest_rejects_float_inputs_false_flags_duplicates_and_mutation() -> None:
    digest = api()

    with pytest.raises(ValueError, match="scratch_probability must be a Decimal"):
        digest.BaseballStartingPitcherLateSwapObservation(
            source_id="source-float",
            game_id="mlb-20260704-nyy-bos",
            market_slug="yankees-red-sox-moneyline",
            team_id="nyy",
            scheduled_starter_id="pitcher-cole",
            current_listed_starter_id="pitcher-cole",
            starter_status="confirmed",
            minutes_until_first_pitch=d("120.000000"),
            lineup_confirmation_age_minutes=d("30.000000"),
            scratch_probability=0.12,
            market_probability=d("0.520000"),
            liquidity_usd=d("1200.000000"),
            source_row_count=d("1"),
            observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=UTC),
            reason_codes=("baseball_starting_pitcher_confirmed",),
        )

    row = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        row.scratch_probability = d("0.900000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        digest.BaseballStartingPitcherLateSwapDigestConfig(report_only=False)

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(observation("source-dupe"), observation("source-dupe"))


def test_digest_validates_timestamps_reason_codes_and_starter_consistency() -> None:
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation("source-naive", observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="reason_codes must match starter_status"):
        observation(
            "source-bad-reason",
            starter_status="questionable",
            reason_codes=("baseball_starting_pitcher_confirmed",),
        )

    with pytest.raises(ValueError, match="changed starters must change pitcher ids"):
        observation(
            "source-bad-changed",
            starter_status="changed",
            current_listed_starter_id="pitcher-cole",
            reason_codes=("baseball_starting_pitcher_changed",),
        )

    with pytest.raises(ValueError, match="unchanged statuses must keep pitcher ids aligned"):
        observation(
            "source-bad-confirmed",
            starter_status="confirmed",
            current_listed_starter_id="pitcher-schmidt",
            reason_codes=("baseball_starting_pitcher_confirmed",),
        )

    with pytest.raises(ValueError, match="blocked_scratch_probability"):
        api().BaseballStartingPitcherLateSwapDigestConfig(
            watch_scratch_probability=d("0.300000"),
            blocked_scratch_probability=d("0.200000"),
        )


def test_payload_is_json_ready_and_omits_live_or_durable_surfaces() -> None:
    payload = api().market_research_baseball_starting_pitcher_late_swap_digest_payload(
        report(
            observation(
                "source-json",
                scratch_probability="0.280000",
                minutes_until_first_pitch="30.000000",
            ),
        ),
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["risk_rows"][0]["scratch_probability"] == "0.280000"
    assert payload["risk_rows"][0]["minutes_until_first_pitch"] == "30.000000"

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                assert "wallet" not in key
                assert "auth" not in key
                assert "private_key" not in key
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        else:
            assert not isinstance(value, float)

    walk(payload)


def test_public_records_are_frozen_and_public_numerics_are_decimal_only() -> None:
    digest = api()
    digest_report = report(observation("source-decimal", scratch_probability="0.280000"))

    for name in digest.__all__:
        value = getattr(digest, name)
        if isinstance(value, type) and is_dataclass(value):
            assert value.__dataclass_params__.frozen is True

    for record in (
        digest.BaseballStartingPitcherLateSwapDigestConfig(),
        digest_report,
        *digest_report.risk_rows,
    ):
        for field_name, value in asdict(record).items():
            if (
                field_name.endswith("_count")
                or field_name.endswith("_probability")
                or field_name.endswith("_minutes")
                or field_name.endswith("_usd")
            ):
                assert type(value) is Decimal
                assert value.as_tuple().exponent in (0, -6)


def test_module_has_no_live_durable_or_mutating_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_baseball_starting_pitcher_late_swap_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "requests",
        "httpx",
        "urlopen",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "connect(",
        "execute(",
        "open(",
        "wallet",
        "private_key",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "live_trading",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = {alias.name.split(".")[0] for alias in node.names}
            assert names.isdisjoint(
                {
                    "requests",
                    "httpx",
                    "socket",
                    "subprocess",
                    "psycopg",
                    "supabase",
                },
            )
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in {
                "requests",
                "httpx",
                "socket",
                "subprocess",
                "psycopg",
                "supabase",
            }
