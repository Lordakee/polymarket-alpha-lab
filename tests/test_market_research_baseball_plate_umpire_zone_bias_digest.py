from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import importlib
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 13, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_baseball_plate_umpire_zone_bias_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str,
    *,
    market_slug: str = "dodgers-giants-total-over-8-5-july-2026",
    game_id: str = "mlb-2026-07-04-lad-sfg",
    plate_umpire_id: str = "umpire-rob-drake",
    called_strike_bias_rate: str = "0.045000",
    outside_zone_strike_rate_delta: str = "0.060000",
    inside_zone_ball_rate_delta: str = "-0.020000",
    run_environment_delta: str = "-0.030000",
    source_row_count: str = "1",
    observed_at: datetime = datetime(2026, 7, 4, 12, 30, tzinfo=UTC),
    reason_codes: tuple[str, ...] = ("baseball_plate_umpire_wide_zone_bias",),
):
    digest = api()
    return digest.BaseballPlateUmpireZoneBiasObservation(
        source_id=source_id,
        market_slug=market_slug,
        game_id=game_id,
        plate_umpire_id=plate_umpire_id,
        called_strike_bias_rate=d(called_strike_bias_rate),
        outside_zone_strike_rate_delta=d(outside_zone_strike_rate_delta),
        inside_zone_ball_rate_delta=d(inside_zone_ball_rate_delta),
        run_environment_delta=d(run_environment_delta),
        source_row_count=d(source_row_count),
        observed_at=observed_at,
        reason_codes=reason_codes,
    )


def report(*rows: object, config: object | None = None):
    digest = api()
    return digest.build_market_research_baseball_plate_umpire_zone_bias_digest(
        rows,
        config=config or digest.BaseballPlateUmpireZoneBiasDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )


def test_empty_digest_is_decimal_zeroed_readonly_and_clear() -> None:
    digest_report = report()

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-baseball-plate-umpire-zone-bias-digest-v0"
    )
    assert digest_report.source_row_count == d("0")
    assert digest_report.observation_count == d("0")
    assert digest_report.pass_count == d("0")
    assert digest_report.watch_count == d("0")
    assert digest_report.blocked_count == d("0")
    assert digest_report.max_abs_zone_bias_score == d("0.000000")
    assert digest_report.average_zone_bias_score == d("0.000000")
    assert digest_report.top_screening_priority_score == d("0.000000")
    assert digest_report.digest_status == "pass"
    assert digest_report.reason_codes == ("baseball_plate_umpire_zone_bias_digest_clear",)
    assert digest_report.bias_rows == ()
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_risk_digest_reduces_plate_umpire_zone_bias_rows() -> None:
    digest_report = report(
        observation(
            "source-inline",
            market_slug="yankees-red-sox-moneyline",
            game_id="mlb-2026-07-04-nyy-bos",
            plate_umpire_id="umpire-neutral",
            called_strike_bias_rate="0.006000",
            outside_zone_strike_rate_delta="0.004000",
            inside_zone_ball_rate_delta="-0.002000",
            run_environment_delta="-0.001000",
            source_row_count="1",
            observed_at=datetime(2026, 7, 4, 9, 15, tzinfo=timezone(timedelta(hours=-4))),
            reason_codes=("baseball_plate_umpire_zone_bias_inline",),
        ),
        observation(
            "source-blocked-wide",
            market_slug="dodgers-giants-total-under-8-5",
            game_id="mlb-2026-07-04-lad-sfg",
            plate_umpire_id="umpire-wide-zone",
            called_strike_bias_rate="0.050000",
            outside_zone_strike_rate_delta="0.070000",
            inside_zone_ball_rate_delta="-0.030000",
            run_environment_delta="-0.040000",
            source_row_count="3",
            observed_at=datetime(2026, 7, 4, 12, 45, tzinfo=UTC),
            reason_codes=("baseball_plate_umpire_wide_zone_bias",),
        ),
        observation(
            "source-watch-tight",
            market_slug="mets-phillies-total-over-9-5",
            game_id="mlb-2026-07-04-nym-phi",
            plate_umpire_id="umpire-tight-zone",
            called_strike_bias_rate="-0.020000",
            outside_zone_strike_rate_delta="-0.030000",
            inside_zone_ball_rate_delta="0.020000",
            run_environment_delta="0.015000",
            source_row_count="2",
            observed_at=datetime(2026, 7, 4, 11, 30, tzinfo=UTC),
            reason_codes=("baseball_plate_umpire_tight_zone_bias",),
        ),
    )

    assert digest_report.source_row_count == d("6")
    assert digest_report.observation_count == d("3")
    assert digest_report.pass_count == d("1")
    assert digest_report.watch_count == d("1")
    assert digest_report.blocked_count == d("1")
    assert digest_report.max_abs_zone_bias_score == d("0.052500")
    assert digest_report.average_zone_bias_score == d("0.011967")
    assert digest_report.top_screening_priority_score == d("1.000000")
    assert digest_report.digest_status == "blocked"
    assert digest_report.reason_codes == (
        "baseball_plate_umpire_zone_bias_blocked_present",
        "baseball_plate_umpire_mixed_zone_bias_present",
    )

    assert tuple(row.source_id for row in digest_report.bias_rows) == (
        "source-blocked-wide",
        "source-watch-tight",
        "source-inline",
    )
    blocked_row = digest_report.bias_rows[0]
    assert blocked_row.zone_bias_score == d("0.052500")
    assert blocked_row.abs_zone_bias_score == d("0.052500")
    assert blocked_row.zone_bias_direction == "wide_zone"
    assert blocked_row.risk_status == "blocked"
    assert blocked_row.screening_priority_score == d("1.000000")
    assert blocked_row.screening_note == "wide_zone_under_bias"
    assert blocked_row.reason_codes == ("baseball_plate_umpire_wide_zone_bias_blocked",)
    assert blocked_row.observed_at == datetime(2026, 7, 4, 12, 45, tzinfo=UTC)

    watch_row = digest_report.bias_rows[1]
    assert watch_row.zone_bias_score == d("-0.021750")
    assert watch_row.zone_bias_direction == "tight_zone"
    assert watch_row.risk_status == "watch"
    assert watch_row.screening_priority_score == d("0.435000")
    assert watch_row.screening_note == "tight_zone_over_bias"
    assert watch_row.reason_codes == ("baseball_plate_umpire_tight_zone_bias_watch",)

    assert digest_report.bias_rows[2].zone_bias_direction == "inline"
    assert digest_report.bias_rows[2].risk_status == "pass"
    assert digest_report.bias_rows[2].screening_note == "zone_bias_inline"


def test_digest_is_deterministic_for_input_order_and_reason_codes() -> None:
    left = observation(
        "source-a",
        market_slug="baseball-a-total",
        game_id="mlb-a",
        plate_umpire_id="umpire-a",
        called_strike_bias_rate="0.020000",
        outside_zone_strike_rate_delta="0.040000",
        inside_zone_ball_rate_delta="-0.010000",
        run_environment_delta="-0.010000",
        observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=UTC),
    )
    right = observation(
        "source-b",
        market_slug="baseball-b-total",
        game_id="mlb-b",
        plate_umpire_id="umpire-b",
        called_strike_bias_rate="0.020000",
        outside_zone_strike_rate_delta="0.040000",
        inside_zone_ball_rate_delta="-0.010000",
        run_environment_delta="-0.010000",
        observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=UTC),
    )

    first = report(right, left)
    second = report(left, right)

    assert tuple(row.source_id for row in first.bias_rows) == ("source-a", "source-b")
    assert asdict(first) == asdict(second)
    assert first.reason_codes == (
        "baseball_plate_umpire_zone_bias_watch_present",
        "baseball_plate_umpire_wide_zone_bias_present",
    )
    assert first.bias_rows[0].reason_codes == (
        "baseball_plate_umpire_wide_zone_bias_watch",
    )


def test_validation_rejects_bad_types_timestamps_reasons_and_duplicates() -> None:
    digest = api()

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="called_strike_bias_rate must be a Decimal"):
        digest.BaseballPlateUmpireZoneBiasObservation(
            source_id="source-float",
            market_slug="baseball-float",
            game_id="mlb-float",
            plate_umpire_id="umpire-float",
            called_strike_bias_rate=0.04,
            outside_zone_strike_rate_delta=d("0.060000"),
            inside_zone_ball_rate_delta=d("-0.020000"),
            run_environment_delta=d("-0.030000"),
            source_row_count=d("1"),
            observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=UTC),
            reason_codes=("baseball_plate_umpire_wide_zone_bias",),
        )

    with pytest.raises(ValueError, match="watch_abs_zone_bias_score must be a Decimal"):
        digest.BaseballPlateUmpireZoneBiasDigestConfig(
            watch_abs_zone_bias_score=DerivedDecimal("0.020000"),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest.build_market_research_baseball_plate_umpire_zone_bias_digest(
            (),
            generated_at=datetime(2026, 7, 4, 13, 0),
        )

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation("source-naive", observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="reason_codes must match zone bias direction"):
        observation(
            "source-bad-reason",
            reason_codes=("baseball_plate_umpire_tight_zone_bias",),
        )

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(observation("source-dupe"), observation("source-dupe"))

    with pytest.raises(ValueError, match="blocked_abs_zone_bias_score"):
        digest.BaseballPlateUmpireZoneBiasDigestConfig(
            watch_abs_zone_bias_score=d("0.050000"),
            blocked_abs_zone_bias_score=d("0.020000"),
        )


def test_frozen_dataclasses_and_hard_flags_are_enforced() -> None:
    digest = api()
    row = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        row.called_strike_bias_rate = d("0.030000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        digest.BaseballPlateUmpireZoneBiasDigestConfig(report_only=False)

    digest_report = report(row)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(digest_report.bias_rows[0], readonly=False)

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_non_default_thresholds_change_screening_status() -> None:
    digest = api()
    cfg = digest.BaseballPlateUmpireZoneBiasDigestConfig(
        watch_abs_zone_bias_score=d("0.003000"),
        blocked_abs_zone_bias_score=d("0.005000"),
    )
    strict_report = report(
        observation(
            "source-strict",
            called_strike_bias_rate="0.006000",
            outside_zone_strike_rate_delta="0.004000",
            inside_zone_ball_rate_delta="-0.002000",
            run_environment_delta="-0.001000",
            reason_codes=("baseball_plate_umpire_zone_bias_inline",),
        ),
        config=cfg,
    )

    assert strict_report.digest_status == "blocked"
    assert strict_report.blocked_count == d("1")
    assert strict_report.bias_rows[0].zone_bias_score == d("0.005150")
    assert strict_report.bias_rows[0].risk_status == "blocked"
    assert strict_report.bias_rows[0].screening_priority_score == d("1.000000")
    assert strict_report.reason_codes == (
        "baseball_plate_umpire_zone_bias_blocked_present",
        "baseball_plate_umpire_wide_zone_bias_present",
    )


def test_payload_public_numerics_and_source_surfaces_are_safe() -> None:
    digest = api()
    digest_report = report(observation("source-json"))
    payload = digest.market_research_baseball_plate_umpire_zone_bias_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["bias_rows"][0]["called_strike_bias_rate"] == "0.045000"
    assert payload["bias_rows"][0]["zone_bias_score"] == "0.046000"
    assert payload["bias_rows"][0]["observed_at"] == "2026-07-04T12:30:00+00:00"

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        else:
            assert not isinstance(value, float)

    walk(payload)

    for value in asdict(digest_report).values():
        if isinstance(value, Decimal):
            assert type(value) is Decimal
    for row in digest_report.bias_rows:
        for value in asdict(row).values():
            if isinstance(value, Decimal):
                assert type(value) is Decimal
                assert value.as_tuple().exponent in (0, -6)

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_baseball_plate_umpire_zone_bias_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "open(",
        "private_key",
        "place_order",
        "submit_order",
        "cancel_order",
        "live_trading",
        "wallet",
        "secret",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = {alias.name.split(".")[0] for alias in node.names}
            assert names.isdisjoint({"requests", "httpx", "aiohttp", "socket", "sqlite3"})
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in {
                "requests",
                "httpx",
                "aiohttp",
                "socket",
                "sqlite3",
            }
