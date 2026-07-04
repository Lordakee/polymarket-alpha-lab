from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-basketball-referee-foul-rate-shift-digest-test-v0"


class _StringSubclass(str):
    pass


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_basketball_referee_foul_rate_shift_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides):
    digest = module()
    values = {
        "config_version": CONFIG_VERSION,
        "blocked_foul_rate_delta_threshold": d("6.000000"),
        "watch_foul_rate_delta_threshold": d("3.000000"),
        "blocked_technical_free_throw_delta_threshold": d("2.000000"),
        "watch_technical_free_throw_delta_threshold": d("1.000000"),
        "minimum_crew_games_sample_threshold": d("10.000000"),
        "stale_observation_seconds_threshold": d("7200.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchBasketballRefereeFoulRateShiftDigestConfig(**values)


def signal(
    fixture_id: str = "nba_bos_nyk_20260704",
    crew_key: str = "crew_alpha",
    *,
    league_key: str = "nba",
    home_team_key: str = "bos",
    away_team_key: str = "nyk",
    source_ref: str = "official_referee_box",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=30),
    crew_games_sample: Decimal = d("18.000000"),
    foul_rate_shift_per_game: Decimal = d("1.250000"),
    technical_free_throw_shift_per_game: Decimal = d("0.250000"),
    market_sensitivity_score: Decimal = d("0.500000"),
    signal_config_version: str = "basketball-referee-foul-rate-feed-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchBasketballRefereeFoulRateShiftDigestSignal(
        fixture_id=fixture_id,
        crew_key=crew_key,
        league_key=league_key,
        home_team_key=home_team_key,
        away_team_key=away_team_key,
        source_ref=source_ref,
        observed_at=observed_at,
        crew_games_sample=crew_games_sample,
        foul_rate_shift_per_game=foul_rate_shift_per_game,
        technical_free_throw_shift_per_game=technical_free_throw_shift_per_game,
        market_sensitivity_score=market_sensitivity_score,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals, **overrides):
    digest = module()
    values = {
        "signals": signals,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return digest.build_market_research_basketball_referee_foul_rate_shift_digest(
        **values,
    )


def assert_no_float_or_int(value: Any) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (float, int)):
        pytest.fail(f"numeric payload value is not a Decimal string: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int(item)


def test_referee_foul_rate_shift_digest_flags_blocked_watch_and_pass_rows() -> None:
    local_observed_at = datetime(
        2026,
        7,
        4,
        13,
        20,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    local_signal = signal(
        "nba_lal_den_20260704",
        "crew_high_whistle",
        home_team_key="lal",
        away_team_key="den",
        source_ref="official_box_local",
        observed_at=local_observed_at,
        crew_games_sample=d("14.000000"),
        foul_rate_shift_per_game=d("7.250000"),
        technical_free_throw_shift_per_game=d("1.500000"),
        market_sensitivity_score=d("0.850000"),
        signal_config_version="basketball-referee-foul-rate-feed-v1",
    )
    report = build_report(
        signal(
            "nba_lal_den_20260704",
            "crew_high_whistle",
            home_team_key="lal",
            away_team_key="den",
            source_ref="official_box_early",
            observed_at=GENERATED_AT - timedelta(minutes=50),
            crew_games_sample=d("12.000000"),
            foul_rate_shift_per_game=d("4.500000"),
            technical_free_throw_shift_per_game=d("1.000000"),
            market_sensitivity_score=d("0.700000"),
        ),
        local_signal,
        signal(
            "nba_mia_chi_20260704",
            "crew_old_sample",
            home_team_key="mia",
            away_team_key="chi",
            source_ref="archived_referee_note",
            observed_at=GENERATED_AT - timedelta(hours=3),
            crew_games_sample=d("12.000000"),
            foul_rate_shift_per_game=d("1.000000"),
            technical_free_throw_shift_per_game=d("0.250000"),
            market_sensitivity_score=d("0.300000"),
        ),
        signal(
            "nba_phx_dal_20260704",
            "crew_watch",
            home_team_key="phx",
            away_team_key="dal",
            source_ref="official_box_watch",
            observed_at=GENERATED_AT - timedelta(minutes=25),
            crew_games_sample=d("9.000000"),
            foul_rate_shift_per_game=d("3.500000"),
            technical_free_throw_shift_per_game=d("1.250000"),
            market_sensitivity_score=d("0.600000"),
        ),
        signal(
            "nba_bos_nyk_20260704",
            "crew_stable",
            source_ref="official_box_clear",
            observed_at=GENERATED_AT - timedelta(minutes=20),
        ),
    )

    assert is_dataclass(report)
    assert local_signal.observed_at == datetime(2026, 7, 4, 17, 20, tzinfo=UTC)
    assert local_signal.observed_at.tzinfo is UTC
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_basketball_referee_foul_rate_shift_review"
    )
    assert report.fixture_count == d("4.000000")
    assert report.signal_count == d("5.000000")
    assert report.blocked_fixture_count == d("2.000000")
    assert report.watch_fixture_count == d("1.000000")
    assert report.pass_fixture_count == d("1.000000")
    assert report.stale_observation_fixture_count == d("1.000000")
    assert report.foul_rate_shift_fixture_count == d("2.000000")
    assert report.technical_free_throw_shift_fixture_count == d("2.000000")
    assert report.thin_sample_fixture_count == d("1.000000")
    assert report.max_observation_age_seconds == d("10800.000000")
    assert report.max_foul_rate_shift_per_game == d("7.250000")
    assert report.max_technical_free_throw_shift_per_game == d("1.500000")
    assert report.max_market_sensitivity_score == d("0.850000")
    assert report.reason_codes == (
        "basketball_referee_foul_rate_shift_stale_observation",
        "basketball_referee_foul_rate_shift_foul_rate_blocked",
        "basketball_referee_foul_rate_shift_foul_rate_watch",
        "basketball_referee_foul_rate_shift_technical_free_throw_watch",
        "basketball_referee_foul_rate_shift_thin_sample",
    )
    assert report.reason_code_counts == (
        module().MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount(
            reason_code="basketball_referee_foul_rate_shift_stale_observation",
            fixture_count=d("1.000000"),
        ),
        module().MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount(
            reason_code="basketball_referee_foul_rate_shift_foul_rate_blocked",
            fixture_count=d("1.000000"),
        ),
        module().MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount(
            reason_code="basketball_referee_foul_rate_shift_foul_rate_watch",
            fixture_count=d("1.000000"),
        ),
        module().MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount(
            reason_code="basketball_referee_foul_rate_shift_technical_free_throw_watch",
            fixture_count=d("2.000000"),
        ),
        module().MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount(
            reason_code="basketball_referee_foul_rate_shift_thin_sample",
            fixture_count=d("1.000000"),
        ),
    )
    assert report.signal_config_versions == (
        ("archived_referee_note", "basketball-referee-foul-rate-feed-v0"),
        ("official_box_clear", "basketball-referee-foul-rate-feed-v0"),
        ("official_box_early", "basketball-referee-foul-rate-feed-v0"),
        ("official_box_local", "basketball-referee-foul-rate-feed-v1"),
        ("official_box_watch", "basketball-referee-foul-rate-feed-v0"),
    )

    assert tuple((row.fixture_id, row.crew_key, row.row_status) for row in report.rows) == (
        ("nba_lal_den_20260704", "crew_high_whistle", "blocked"),
        ("nba_mia_chi_20260704", "crew_old_sample", "blocked"),
        ("nba_phx_dal_20260704", "crew_watch", "watch"),
        ("nba_bos_nyk_20260704", "crew_stable", "pass"),
    )
    high_whistle = report.rows[0]
    assert high_whistle.signal_count == d("2.000000")
    assert high_whistle.observed_at_latest == datetime(2026, 7, 4, 17, 20, tzinfo=UTC)
    assert high_whistle.observation_age_seconds == d("2400.000000")
    assert high_whistle.crew_games_sample_max == d("14.000000")
    assert high_whistle.foul_rate_shift_per_game_max == d("7.250000")
    assert high_whistle.technical_free_throw_shift_per_game_max == d("1.500000")
    assert high_whistle.market_sensitivity_score_max == d("0.850000")
    assert high_whistle.reason_codes == (
        "basketball_referee_foul_rate_shift_foul_rate_blocked",
        "basketball_referee_foul_rate_shift_technical_free_throw_watch",
    )

    stale = report.rows[1]
    assert stale.reason_codes == ("basketball_referee_foul_rate_shift_stale_observation",)
    clear = report.rows[3]
    assert clear.reason_codes == ("basketball_referee_foul_rate_shift_pass",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_referee_foul_rate_shift_digest_passes_for_empty_and_stable_inputs() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.fixture_count == d("0.000000")
    assert empty_report.signal_count == d("0.000000")
    assert empty_report.reason_codes == ("basketball_referee_foul_rate_shift_empty",)
    assert empty_report.rows == ()
    assert empty_report.max_observation_age_seconds is None
    assert empty_report.max_market_sensitivity_score is None

    stable_report = build_report(
        signal(
            "nba_bos_nyk_20260704",
            "crew_stable",
            source_ref="official_current",
            observed_at=GENERATED_AT - timedelta(minutes=20),
        ),
        signal(
            "nba_mia_chi_20260704",
            "crew_beta",
            home_team_key="mia",
            away_team_key="chi",
            source_ref="official_second",
            observed_at=GENERATED_AT - timedelta(minutes=15),
            foul_rate_shift_per_game=d("2.000000"),
            technical_free_throw_shift_per_game=d("0.500000"),
        ),
    )

    assert stable_report.digest_status == "pass"
    assert stable_report.reason_codes == ("basketball_referee_foul_rate_shift_passed",)
    assert stable_report.reason_code_counts == ()
    assert tuple(row.row_status for row in stable_report.rows) == ("pass", "pass")


def test_referee_foul_rate_watch_and_technical_blocked_reasons_are_rank_sorted() -> None:
    report = build_report(
        signal(
            "nba_mem_sas_20260704",
            "crew_mixed_signal",
            home_team_key="mem",
            away_team_key="sas",
            source_ref="official_mixed_signal",
            observed_at=GENERATED_AT - timedelta(minutes=15),
            crew_games_sample=d("16.000000"),
            foul_rate_shift_per_game=d("4.000000"),
            technical_free_throw_shift_per_game=d("2.500000"),
            market_sensitivity_score=d("0.750000"),
        ),
    )

    assert report.digest_status == "blocked"
    assert report.blocked_fixture_count == d("1.000000")
    assert report.reason_codes == (
        "basketball_referee_foul_rate_shift_technical_free_throw_blocked",
        "basketball_referee_foul_rate_shift_foul_rate_watch",
    )
    assert report.rows[0].row_status == "blocked"
    assert report.rows[0].reason_codes == (
        "basketball_referee_foul_rate_shift_technical_free_throw_blocked",
        "basketball_referee_foul_rate_shift_foul_rate_watch",
    )


def test_referee_foul_rate_shift_payload_uses_six_decimal_strings() -> None:
    report = build_report(
        signal(
            observed_at=GENERATED_AT - timedelta(minutes=45),
            crew_games_sample=d("9.000000"),
            foul_rate_shift_per_game=d("4.250000"),
            technical_free_throw_shift_per_game=d("0.750000"),
            market_sensitivity_score=d("0.650000"),
        ),
    )

    payload = module().market_research_basketball_referee_foul_rate_shift_digest_payload(
        report,
    )

    json.dumps(payload, sort_keys=True)
    assert payload["fixture_count"] == "1.000000"
    assert payload["signal_count"] == "1.000000"
    assert payload["watch_fixture_count"] == "1.000000"
    assert payload["rows"][0]["observation_age_seconds"] == "2700.000000"
    assert payload["rows"][0]["foul_rate_shift_per_game_max"] == "4.250000"
    assert payload["rows"][0]["technical_free_throw_shift_per_game_max"] == "0.750000"
    assert payload["rows"][0]["observed_at_latest"] == "2026-07-04T17:15:00Z"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int(payload)


def test_public_dataclasses_are_frozen_and_public_numerics_are_decimal() -> None:
    digest = module()

    for name in (
        "MarketResearchBasketballRefereeFoulRateShiftDigestConfig",
        "MarketResearchBasketballRefereeFoulRateShiftDigestSignal",
        "MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount",
        "MarketResearchBasketballRefereeFoulRateShiftDigestRow",
        "MarketResearchBasketballRefereeFoulRateShiftDigestReport",
    ):
        cls = getattr(digest, name)
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    report = build_report(signal())
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].fixture_id = "changed"

    numeric_name_parts = (
        "_threshold",
        "_seconds",
        "_sample",
        "_rate_",
        "_score",
        "_delta",
    )
    for public_type in (
        digest.MarketResearchBasketballRefereeFoulRateShiftDigestConfig,
        digest.MarketResearchBasketballRefereeFoulRateShiftDigestSignal,
        digest.MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount,
        digest.MarketResearchBasketballRefereeFoulRateShiftDigestRow,
        digest.MarketResearchBasketballRefereeFoulRateShiftDigestReport,
    ):
        for field in fields(public_type):
            if field.name.endswith("_count") or any(
                part in field.name for part in numeric_name_parts
            ):
                assert "Decimal" in str(field.type)


def test_referee_foul_rate_shift_validation_rejects_unsafe_inputs_and_flags() -> None:
    digest = module()

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 15, 0))

    with pytest.raises(ValueError, match="fixture_id must be a string"):
        signal(fixture_id=_StringSubclass("fixture_subclass"))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(generated_at=_DatetimeSubclass(2026, 7, 4, 18, tzinfo=UTC))

    with pytest.raises(ValueError, match="foul_rate_shift_per_game must be a Decimal"):
        signal(foul_rate_shift_per_game=_DecimalSubclass("0.9"))

    with pytest.raises(ValueError, match="source_ref contains unsafe source detail"):
        signal(source_ref="source_wallet_hint")

    with pytest.raises(ValueError, match="signal readonly must be True"):
        signal(readonly=False)

    with pytest.raises(
        ValueError,
        match="blocked_foul_rate_delta_threshold must be at least watch threshold",
    ):
        config(
            blocked_foul_rate_delta_threshold=d("2.000000"),
            watch_foul_rate_delta_threshold=d("3.000000"),
        )

    row = build_report(signal()).rows[0]
    with pytest.raises(ValueError, match="row status must match reason codes"):
        replace(row, row_status="blocked")

    with pytest.raises(ValueError, match="reason_codes must be sorted by reason code rank"):
        replace(
            row,
            row_status="blocked",
            reason_codes=(
                "basketball_referee_foul_rate_shift_thin_sample",
                "basketball_referee_foul_rate_shift_stale_observation",
            ),
        )

    with pytest.raises(ValueError, match="report must be exactly"):
        digest.market_research_basketball_referee_foul_rate_shift_digest_payload(object())


def test_referee_foul_rate_shift_rejects_duplicate_sources_and_future_observations() -> None:
    with pytest.raises(ValueError, match="duplicate fixture/source pairs"):
        build_report(signal(), signal())

    with pytest.raises(ValueError, match="observed_at values must be at or before generated_at"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))


def test_referee_foul_rate_shift_module_stays_pure_and_unwired() -> None:
    module_path = Path(__file__).resolve().parents[1] / (
        "src/polymarket_alpha_lab/"
        "market_research_basketball_referee_foul_rate_shift_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "live trading",
        "payload_json",
        "wallet",
        "broker",
        "order",
        "auth",
        "secret",
        "private",
        "cancel",
        "replace",
        "exchange",
        "trade",
        "execute",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "supabase",
        "open(",
        "path(",
        "subprocess",
        "sqlite3",
    )
    assert all(term not in lowered for term in forbidden_terms)

    parsed = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(parsed)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "supabase",
        "sqlite3",
        "subprocess",
        "pathlib",
    } & imports

    exported = set(getattr(module(), "__all__"))
    assert exported == {
        "DEFAULT_MARKET_RESEARCH_BASKETBALL_REFEREE_FOUL_RATE_SHIFT_DIGEST_CONFIG_VERSION",
        "MarketResearchBasketballRefereeFoulRateShiftDigestConfig",
        "MarketResearchBasketballRefereeFoulRateShiftDigestSignal",
        "MarketResearchBasketballRefereeFoulRateShiftDigestReasonCodeCount",
        "MarketResearchBasketballRefereeFoulRateShiftDigestRow",
        "MarketResearchBasketballRefereeFoulRateShiftDigestReport",
        "build_market_research_basketball_referee_foul_rate_shift_digest",
        "market_research_basketball_referee_foul_rate_shift_digest_payload",
    }
