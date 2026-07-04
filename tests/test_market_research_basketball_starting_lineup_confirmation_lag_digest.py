from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 4, 18, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_basketball_starting_lineup_confirmation_lag_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    event_id: str = "nba-20260704-lal-bos",
    team: str = "lal",
    opponent: str = "bos",
    market_slug: str = "lal-bos-moneyline",
    minutes_to_tip: str | Decimal = "30.000000",
    lineup_confirmed_flag: str | Decimal = "0.000000",
    projected_starter_uncertainty_count: str | Decimal = "2.000000",
    injury_report_freshness_age_minutes: str | Decimal = "90.000000",
    beat_source_disagreement_count: str | Decimal = "0.000000",
    implied_minute_volatility: str | Decimal = "0.120000",
    observed_at: datetime = datetime(2026, 7, 4, 17, 0, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("beat_lineup_watch",),
):
    module = digest()
    return module.BasketballStartingLineupConfirmationLagObservation(
        source_id=source_id,
        event_id=event_id,
        team=team,
        opponent=opponent,
        market_slug=market_slug,
        minutes_to_tip=(
            minutes_to_tip if isinstance(minutes_to_tip, Decimal) else d(minutes_to_tip)
        ),
        lineup_confirmed_flag=(
            lineup_confirmed_flag
            if isinstance(lineup_confirmed_flag, Decimal)
            else d(lineup_confirmed_flag)
        ),
        projected_starter_uncertainty_count=(
            projected_starter_uncertainty_count
            if isinstance(projected_starter_uncertainty_count, Decimal)
            else d(projected_starter_uncertainty_count)
        ),
        injury_report_freshness_age_minutes=(
            injury_report_freshness_age_minutes
            if isinstance(injury_report_freshness_age_minutes, Decimal)
            else d(injury_report_freshness_age_minutes)
        ),
        beat_source_disagreement_count=(
            beat_source_disagreement_count
            if isinstance(beat_source_disagreement_count, Decimal)
            else d(beat_source_disagreement_count)
        ),
        implied_minute_volatility=(
            implied_minute_volatility
            if isinstance(implied_minute_volatility, Decimal)
            else d(implied_minute_volatility)
        ),
        observed_at=observed_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_basketball_starting_lineup_confirmation_lag_digest(
        rows,
        config=cfg or module.BasketballStartingLineupConfirmationLagDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(
        digest_report,
        module.BasketballStartingLineupConfirmationLagDigestReport,
    )
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-basketball-starting-lineup-confirmation-lag-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_basketball_starting_lineup_confirmation_lag_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.unconfirmed_lineup_count == d("0.000000")
    assert digest_report.close_to_tip_count == d("0.000000")
    assert digest_report.starter_uncertainty_count == d("0.000000")
    assert digest_report.stale_injury_report_count == d("0.000000")
    assert digest_report.beat_disagreement_count == d("0.000000")
    assert digest_report.implied_minute_volatility_count == d("0.000000")
    assert digest_report.max_lineup_lag_risk_score == d("0.000000")
    assert digest_report.average_lineup_lag_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "basketball_starting_lineup_confirmation_lag_digest_empty",
    )
    assert digest_report.reason_code_counts == (
        module.BasketballStartingLineupConfirmationLagReasonCodeCount(
            reason_code="basketball_starting_lineup_confirmation_lag_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_compounded_unconfirmed_lineup_lag_blocks_event_market_screening() -> None:
    module = digest()

    digest_report = report(
        observation(
            "source-blocked",
            event_id="nba-blocked",
            team="lal",
            opponent="bos",
            market_slug="alpha-blocked-lag",
            minutes_to_tip="12.000000",
            lineup_confirmed_flag="0.000000",
            projected_starter_uncertainty_count="3.000000",
            injury_report_freshness_age_minutes="260.000000",
            beat_source_disagreement_count="2.000000",
            implied_minute_volatility="0.180000",
            upstream_reason_codes=("injury_questionable", "beat_report_late"),
        ),
        observation(
            "source-watch",
            event_id="nba-watch",
            team="nyk",
            opponent="mia",
            market_slug="beta-watch-lag",
            minutes_to_tip="50.000000",
            lineup_confirmed_flag="0.000000",
            projected_starter_uncertainty_count="2.000000",
            injury_report_freshness_age_minutes="60.000000",
            beat_source_disagreement_count="0.000000",
            implied_minute_volatility="0.120000",
            observed_at=datetime(2026, 7, 4, 12, 30, tzinfo=timezone(timedelta(hours=2))),
        ),
        observation(
            "source-pass",
            event_id="nba-pass",
            team="den",
            opponent="phx",
            market_slug="gamma-confirmed-lineup",
            minutes_to_tip="70.000000",
            lineup_confirmed_flag="1.000000",
            projected_starter_uncertainty_count="0.000000",
            injury_report_freshness_age_minutes="30.000000",
            beat_source_disagreement_count="0.000000",
            implied_minute_volatility="0.020000",
            upstream_reason_codes=("official_lineup_confirmed",),
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_basketball_starting_lineup_confirmation_lag_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.unconfirmed_lineup_count == d("2.000000")
    assert digest_report.close_to_tip_count == d("1.000000")
    assert digest_report.starter_uncertainty_count == d("2.000000")
    assert digest_report.stale_injury_report_count == d("1.000000")
    assert digest_report.beat_disagreement_count == d("1.000000")
    assert digest_report.implied_minute_volatility_count == d("2.000000")
    assert digest_report.max_lineup_lag_risk_score == d("1.000000")
    assert digest_report.average_lineup_lag_risk_score == d("0.500000")
    assert digest_report.reason_codes == (
        "basketball_starting_lineup_confirmation_lag_blocked_present",
        "basketball_starting_lineup_confirmation_lag_unconfirmed_lineup_present",
        "basketball_starting_lineup_confirmation_lag_close_to_tip_present",
        "basketball_starting_lineup_confirmation_lag_starter_uncertainty_present",
        "basketball_starting_lineup_confirmation_lag_stale_injury_report_present",
        "basketball_starting_lineup_confirmation_lag_beat_disagreement_present",
        "basketball_starting_lineup_confirmation_lag_implied_minute_volatility_present",
    )
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "alpha-blocked-lag",
        "beta-watch-lag",
        "gamma-confirmed-lineup",
    )

    blocked, watched, passed = digest_report.rows
    assert blocked.lineup_lag_status == "blocked"
    assert blocked.lineup_lag_signal_count == d("6.000000")
    assert blocked.lineup_lag_risk_score == d("1.000000")
    assert blocked.upstream_reason_codes == ("beat_report_late", "injury_questionable")
    assert blocked.reason_codes == (
        "basketball_starting_lineup_confirmation_lag_unconfirmed_lineup",
        "basketball_starting_lineup_confirmation_lag_close_to_tip",
        "basketball_starting_lineup_confirmation_lag_projected_starter_uncertainty",
        "basketball_starting_lineup_confirmation_lag_stale_injury_report",
        "basketball_starting_lineup_confirmation_lag_beat_source_disagreement",
        "basketball_starting_lineup_confirmation_lag_implied_minute_volatility",
        "basketball_starting_lineup_confirmation_lag_blocked",
    )
    assert watched.lineup_lag_status == "watch"
    assert watched.observed_at == datetime(2026, 7, 4, 10, 30, tzinfo=UTC)
    assert watched.lineup_lag_risk_score == d("0.500000")
    assert watched.reason_codes == (
        "basketball_starting_lineup_confirmation_lag_unconfirmed_lineup",
        "basketball_starting_lineup_confirmation_lag_projected_starter_uncertainty",
        "basketball_starting_lineup_confirmation_lag_implied_minute_volatility",
        "basketball_starting_lineup_confirmation_lag_watch",
    )
    assert passed.lineup_lag_status == "pass"
    assert passed.lineup_lag_risk_score == d("0.000000")
    assert passed.reason_codes == (
        "basketball_starting_lineup_confirmation_lag_clear",
    )

    assert tuple(item.reason_code for item in digest_report.reason_code_counts) == (
        "basketball_starting_lineup_confirmation_lag_blocked_present",
        "basketball_starting_lineup_confirmation_lag_unconfirmed_lineup_present",
        "basketball_starting_lineup_confirmation_lag_close_to_tip_present",
        "basketball_starting_lineup_confirmation_lag_starter_uncertainty_present",
        "basketball_starting_lineup_confirmation_lag_stale_injury_report_present",
        "basketball_starting_lineup_confirmation_lag_beat_disagreement_present",
        "basketball_starting_lineup_confirmation_lag_implied_minute_volatility_present",
    )
    assert tuple(item.count for item in digest_report.reason_code_counts) == (
        d("1.000000"),
        d("2.000000"),
        d("1.000000"),
        d("2.000000"),
        d("1.000000"),
        d("1.000000"),
        d("2.000000"),
    )


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        event_id="nba-watch-b",
        market_slug="zeta-watch-lag",
        lineup_confirmed_flag="0.000000",
        minutes_to_tip="50.000000",
        projected_starter_uncertainty_count="2.000000",
        implied_minute_volatility="0.120000",
    )
    second = observation(
        "source-blocked",
        event_id="nba-blocked",
        market_slug="alpha-blocked-lag",
        lineup_confirmed_flag="0.000000",
        minutes_to_tip="8.000000",
        projected_starter_uncertainty_count="4.000000",
        injury_report_freshness_age_minutes="300.000000",
        beat_source_disagreement_count="1.000000",
        implied_minute_volatility="0.200000",
    )
    third = observation(
        "source-watch-a",
        event_id="nba-watch-a",
        market_slug="alpha-watch-lag",
        lineup_confirmed_flag="0.000000",
        minutes_to_tip="55.000000",
        projected_starter_uncertainty_count="2.000000",
        implied_minute_volatility="0.120000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "alpha-blocked-lag",
        "alpha-watch-lag",
        "zeta-watch-lag",
    )
    assert forward.reason_codes == (
        "basketball_starting_lineup_confirmation_lag_blocked_present",
        "basketball_starting_lineup_confirmation_lag_unconfirmed_lineup_present",
        "basketball_starting_lineup_confirmation_lag_close_to_tip_present",
        "basketball_starting_lineup_confirmation_lag_starter_uncertainty_present",
        "basketball_starting_lineup_confirmation_lag_stale_injury_report_present",
        "basketball_starting_lineup_confirmation_lag_beat_disagreement_present",
        "basketball_starting_lineup_confirmation_lag_implied_minute_volatility_present",
    )


def test_non_default_thresholds_can_downgrade_moderate_lineup_lag() -> None:
    module = digest()
    cfg = module.BasketballStartingLineupConfirmationLagDigestConfig(
        projected_starter_uncertainty_count=d("4.000000"),
        implied_minute_volatility=d("0.200000"),
        watch_lag_signal_count=d("4.000000"),
        blocked_lag_signal_count=d("6.000000"),
    )

    digest_report = report(
        observation(
            "source-moderate",
            minutes_to_tip="50.000000",
            lineup_confirmed_flag="0.000000",
            projected_starter_uncertainty_count="2.000000",
            implied_minute_volatility="0.120000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_basketball_starting_lineup_confirmation_lag_screening"
    )
    assert digest_report.rows[0].lineup_lag_status == "pass"
    assert digest_report.rows[0].lineup_lag_risk_score == d("0.166667")
    assert digest_report.rows[0].reason_codes == (
        "basketball_starting_lineup_confirmation_lag_unconfirmed_lineup",
        "basketball_starting_lineup_confirmation_lag_clear",
    )
    assert digest_report.reason_codes == (
        "basketball_starting_lineup_confirmation_lag_unconfirmed_lineup_present",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="minutes_to_tip must be a Decimal"):
        observation(minutes_to_tip=_DecimalSubclass("30.000000"))
    with pytest.raises(ValueError, match="minutes_to_tip must be nonnegative"):
        observation(minutes_to_tip="-1.000000")
    with pytest.raises(ValueError, match="lineup_confirmed_flag must be zero or one"):
        observation(lineup_confirmed_flag="0.500000")
    with pytest.raises(ValueError, match="implied_minute_volatility must be no greater than one"):
        observation(implied_minute_volatility="1.500000")
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 4, 17, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_basketball_starting_lineup_confirmation_lag_digest(
            (),
            config=module.BasketballStartingLineupConfirmationLagDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 18, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="watch_lag_signal_count"):
        module.BasketballStartingLineupConfirmationLagDigestConfig(
            watch_lag_signal_count=d("5.000000"),
            blocked_lag_signal_count=d("4.000000"),
        )

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(ValueError, match="lineup_lag_risk_score must match"):
        replace(valid_row, lineup_lag_risk_score=d("0.999999"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "basketball_starting_lineup_confirmation_lag_clear",
                "basketball_starting_lineup_confirmation_lag_blocked",
            ),
        )

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_rows_counts_and_report() -> None:
    module = digest()

    digest_report = report(observation("source-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)
    assert all(
        count.paper_only and count.report_only and count.readonly
        for count in digest_report.reason_code_counts
    )

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.BasketballStartingLineupConfirmationLagDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_payload_uses_six_decimal_strings_and_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    digest_report = report(observation("source-payload"))

    payload = module.market_research_basketball_starting_lineup_confirmation_lag_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["minutes_to_tip"] == "30.000000"
    assert payload["rows"][0]["lineup_confirmed_flag"] == "0.000000"
    assert payload["rows"][0]["lineup_lag_risk_score"] == "0.666667"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T17:00:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "auth" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.BasketballStartingLineupConfirmationLagDigestConfig(),
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
        "market_research_basketball_starting_lineup_confirmation_lag_digest.py",
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
        "submit_order",
        "cancel_order",
        "replace_order",
        "cancel(",
    ):
        assert forbidden not in source


def _is_public_numeric(value: object) -> bool:
    return type(value) is Decimal or type(value) is int or type(value) is float
