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
        "polymarket_alpha_lab.market_research_baseball_umpire_zone_tendency_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str,
    *,
    market_slug: str = "dodgers-giants-total-under-8-5-july-2026",
    game_id: str = "mlb-2026-07-04-lad-sfg",
    plate_umpire_id: str = "umpire-wide-zone",
    called_strike_rate_delta: str = "0.070000",
    shadow_zone_strike_rate_delta: str = "0.060000",
    outside_zone_strike_rate_delta: str = "0.040000",
    walk_rate_delta: str = "-0.030000",
    source_pitch_count: str = "300",
    observed_at: datetime = datetime(2026, 7, 4, 12, 30, tzinfo=UTC),
    reason_codes: tuple[str, ...] = (
        "baseball_umpire_zone_tendency_wide_zone_reported",
    ),
):
    digest = api()
    return digest.BaseballUmpireZoneTendencyObservation(
        source_id=source_id,
        market_slug=market_slug,
        game_id=game_id,
        plate_umpire_id=plate_umpire_id,
        called_strike_rate_delta=d(called_strike_rate_delta),
        shadow_zone_strike_rate_delta=d(shadow_zone_strike_rate_delta),
        outside_zone_strike_rate_delta=d(outside_zone_strike_rate_delta),
        walk_rate_delta=d(walk_rate_delta),
        source_pitch_count=d(source_pitch_count),
        observed_at=observed_at,
        reason_codes=reason_codes,
    )


def report(*rows: object, config: object | None = None):
    digest = api()
    return digest.build_market_research_baseball_umpire_zone_tendency_digest(
        rows,
        config=config or digest.BaseballUmpireZoneTendencyDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )


def test_empty_digest_is_decimal_zeroed_readonly_and_clear() -> None:
    digest_report = report()

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-baseball-umpire-zone-tendency-digest-v0"
    )
    assert digest_report.source_pitch_count == d("0.000000")
    assert digest_report.observation_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.max_abs_zone_tendency_score == d("0.000000")
    assert digest_report.average_zone_tendency_score == d("0.000000")
    assert digest_report.top_screening_priority_score == d("0.000000")
    assert digest_report.digest_status == "pass"
    assert digest_report.reason_codes == (
        "baseball_umpire_zone_tendency_digest_clear",
    )
    assert digest_report.tendency_rows == ()
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_risk_digest_reduces_umpire_zone_tendency_rows() -> None:
    digest_report = report(
        observation(
            "source-inline",
            market_slug="yankees-red-sox-total",
            game_id="mlb-2026-07-04-nyy-bos",
            plate_umpire_id="umpire-neutral",
            called_strike_rate_delta="0.006000",
            shadow_zone_strike_rate_delta="0.004000",
            outside_zone_strike_rate_delta="0.002000",
            walk_rate_delta="-0.001000",
            source_pitch_count="90",
            observed_at=datetime(2026, 7, 4, 9, 15, tzinfo=timezone(timedelta(hours=-4))),
            reason_codes=("baseball_umpire_zone_tendency_inline_reported",),
        ),
        observation(
            "source-blocked-wide",
            market_slug="dodgers-giants-total-under-8-5",
            game_id="mlb-2026-07-04-lad-sfg",
            plate_umpire_id="umpire-wide-zone",
            called_strike_rate_delta="0.070000",
            shadow_zone_strike_rate_delta="0.060000",
            outside_zone_strike_rate_delta="0.040000",
            walk_rate_delta="-0.030000",
            source_pitch_count="300",
            observed_at=datetime(2026, 7, 4, 12, 45, tzinfo=UTC),
            reason_codes=("baseball_umpire_zone_tendency_wide_zone_reported",),
        ),
        observation(
            "source-watch-tight",
            market_slug="mets-phillies-total-over-9-5",
            game_id="mlb-2026-07-04-nym-phi",
            plate_umpire_id="umpire-tight-zone",
            called_strike_rate_delta="-0.030000",
            shadow_zone_strike_rate_delta="-0.026000",
            outside_zone_strike_rate_delta="-0.016000",
            walk_rate_delta="0.020000",
            source_pitch_count="180",
            observed_at=datetime(2026, 7, 4, 11, 30, tzinfo=UTC),
            reason_codes=("baseball_umpire_zone_tendency_tight_zone_reported",),
        ),
    )

    assert digest_report.source_pitch_count == d("570.000000")
    assert digest_report.observation_count == d("3.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.max_abs_zone_tendency_score == d("0.061000")
    assert digest_report.average_zone_tendency_score == d("0.013083")
    assert digest_report.top_screening_priority_score == d("1.000000")
    assert digest_report.digest_status == "blocked"
    assert digest_report.reason_codes == (
        "baseball_umpire_zone_tendency_blocked_present",
        "baseball_umpire_zone_tendency_mixed_tendency_present",
    )

    assert tuple(row.source_id for row in digest_report.tendency_rows) == (
        "source-blocked-wide",
        "source-watch-tight",
        "source-inline",
    )
    blocked_row = digest_report.tendency_rows[0]
    assert blocked_row.zone_tendency_score == d("0.061000")
    assert blocked_row.abs_zone_tendency_score == d("0.061000")
    assert blocked_row.zone_tendency_direction == "wide_zone"
    assert blocked_row.risk_status == "blocked"
    assert blocked_row.screening_priority_score == d("1.000000")
    assert blocked_row.screening_note == "wide_zone_run_suppression"
    assert blocked_row.reason_codes == (
        "baseball_umpire_zone_tendency_wide_zone_blocked",
    )
    assert blocked_row.observed_at == datetime(2026, 7, 4, 12, 45, tzinfo=UTC)

    watch_row = digest_report.tendency_rows[1]
    assert watch_row.zone_tendency_score == d("-0.026400")
    assert watch_row.zone_tendency_direction == "tight_zone"
    assert watch_row.risk_status == "watch"
    assert watch_row.screening_priority_score == d("0.440000")
    assert watch_row.screening_note == "tight_zone_run_inflation"
    assert watch_row.reason_codes == (
        "baseball_umpire_zone_tendency_tight_zone_watch",
    )

    assert digest_report.tendency_rows[2].zone_tendency_direction == "inline"
    assert digest_report.tendency_rows[2].risk_status == "pass"
    assert digest_report.tendency_rows[2].screening_note == "zone_tendency_inline"


def test_digest_is_deterministic_for_input_order_and_reason_codes() -> None:
    left = observation(
        "source-a",
        market_slug="baseball-a-total",
        game_id="mlb-a",
        plate_umpire_id="umpire-a",
        called_strike_rate_delta="0.033000",
        shadow_zone_strike_rate_delta="0.025000",
        outside_zone_strike_rate_delta="0.013000",
        walk_rate_delta="-0.010000",
        source_pitch_count="100",
        observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=UTC),
    )
    right = observation(
        "source-b",
        market_slug="baseball-b-total",
        game_id="mlb-b",
        plate_umpire_id="umpire-b",
        called_strike_rate_delta="0.033000",
        shadow_zone_strike_rate_delta="0.025000",
        outside_zone_strike_rate_delta="0.013000",
        walk_rate_delta="-0.010000",
        source_pitch_count="100",
        observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=UTC),
    )

    first = report(right, left)
    second = report(left, right)

    assert tuple(row.source_id for row in first.tendency_rows) == (
        "source-a",
        "source-b",
    )
    assert asdict(first) == asdict(second)
    assert first.reason_codes == (
        "baseball_umpire_zone_tendency_watch_present",
        "baseball_umpire_zone_tendency_wide_zone_present",
    )
    assert first.tendency_rows[0].reason_codes == (
        "baseball_umpire_zone_tendency_wide_zone_watch",
    )


def test_validation_rejects_bad_types_timestamps_reasons_and_duplicates() -> None:
    digest = api()

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="called_strike_rate_delta must be a Decimal"):
        digest.BaseballUmpireZoneTendencyObservation(
            source_id="source-float",
            market_slug="baseball-float",
            game_id="mlb-float",
            plate_umpire_id="umpire-float",
            called_strike_rate_delta=0.04,
            shadow_zone_strike_rate_delta=d("0.060000"),
            outside_zone_strike_rate_delta=d("0.040000"),
            walk_rate_delta=d("-0.030000"),
            source_pitch_count=d("300"),
            observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=UTC),
            reason_codes=("baseball_umpire_zone_tendency_wide_zone_reported",),
        )

    with pytest.raises(
        ValueError,
        match="watch_abs_zone_tendency_score must be a Decimal",
    ):
        digest.BaseballUmpireZoneTendencyDigestConfig(
            watch_abs_zone_tendency_score=DerivedDecimal("0.025000"),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest.build_market_research_baseball_umpire_zone_tendency_digest(
            (),
            generated_at=datetime(2026, 7, 4, 13, 0),
        )

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation("source-naive", observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="reason_codes must match zone tendency"):
        observation(
            "source-bad-reason",
            reason_codes=("baseball_umpire_zone_tendency_tight_zone_reported",),
        )

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(observation("source-dupe"), observation("source-dupe"))

    with pytest.raises(ValueError, match="blocked_abs_zone_tendency_score"):
        digest.BaseballUmpireZoneTendencyDigestConfig(
            watch_abs_zone_tendency_score=d("0.060000"),
            blocked_abs_zone_tendency_score=d("0.025000"),
        )


def test_frozen_dataclasses_and_hard_flags_are_enforced() -> None:
    digest = api()
    row = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        row.called_strike_rate_delta = d("0.030000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        digest.BaseballUmpireZoneTendencyDigestConfig(report_only=False)

    digest_report = report(row)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(digest_report.tendency_rows[0], readonly=False)

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_non_default_thresholds_change_screening_status() -> None:
    digest = api()
    cfg = digest.BaseballUmpireZoneTendencyDigestConfig(
        watch_abs_zone_tendency_score=d("0.003000"),
        blocked_abs_zone_tendency_score=d("0.004000"),
    )
    strict_report = report(
        observation(
            "source-strict",
            called_strike_rate_delta="0.006000",
            shadow_zone_strike_rate_delta="0.004000",
            outside_zone_strike_rate_delta="0.002000",
            walk_rate_delta="-0.001000",
            source_pitch_count="75",
            reason_codes=("baseball_umpire_zone_tendency_inline_reported",),
        ),
        config=cfg,
    )

    assert strict_report.digest_status == "blocked"
    assert strict_report.blocked_count == d("1.000000")
    assert strict_report.tendency_rows[0].zone_tendency_score == d("0.004650")
    assert strict_report.tendency_rows[0].risk_status == "blocked"
    assert strict_report.tendency_rows[0].screening_priority_score == d("1.000000")
    assert strict_report.reason_codes == (
        "baseball_umpire_zone_tendency_blocked_present",
        "baseball_umpire_zone_tendency_wide_zone_present",
    )


def test_payload_public_numerics_and_source_surfaces_are_safe() -> None:
    digest = api()
    digest_report = report(observation("source-json"))
    payload = digest.market_research_baseball_umpire_zone_tendency_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["source_pitch_count"] == "300.000000"
    assert payload["observation_count"] == "1.000000"
    assert payload["tendency_rows"][0]["called_strike_rate_delta"] == "0.070000"
    assert payload["tendency_rows"][0]["zone_tendency_score"] == "0.061000"
    assert payload["tendency_rows"][0]["observed_at"] == "2026-07-04T12:30:00+00:00"

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
            assert value.as_tuple().exponent == -6
    for row in digest_report.tendency_rows:
        for value in asdict(row).values():
            if isinstance(value, Decimal):
                assert type(value) is Decimal
                assert value.as_tuple().exponent == -6

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_baseball_umpire_zone_tendency_digest.py"
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
