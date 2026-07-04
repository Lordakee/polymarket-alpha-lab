from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 13, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_gold_options_skew_shock_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str,
    *,
    market_slug: str = "gold-closes-above-2500-july-2026",
    expiry_bucket: str = "front_month",
    put_delta_25_iv: str = "0.320000",
    call_delta_25_iv: str = "0.240000",
    atm_iv: str = "0.280000",
    previous_skew_ratio: str = "0.210000",
    source_row_count: str = "1",
    observed_at: datetime = datetime(2026, 7, 4, 12, 30, tzinfo=UTC),
    reason_codes: tuple[str, ...] = ("gold_options_put_skew_widened",),
):
    digest = api()
    return digest.GoldOptionsSkewShockObservation(
        source_id=source_id,
        market_slug=market_slug,
        expiry_bucket=expiry_bucket,
        put_delta_25_iv=d(put_delta_25_iv),
        call_delta_25_iv=d(call_delta_25_iv),
        atm_iv=d(atm_iv),
        previous_skew_ratio=d(previous_skew_ratio),
        source_row_count=d(source_row_count),
        observed_at=observed_at,
        reason_codes=reason_codes,
    )


def report(*rows: object, config: object | None = None):
    digest = api()
    return digest.build_market_research_gold_options_skew_shock_digest(
        rows,
        config=config or digest.GoldOptionsSkewShockDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )


def test_empty_digest_is_decimal_zeroed_readonly_and_clear() -> None:
    digest_report = report()

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-gold-options-skew-shock-digest-v0"
    )
    assert digest_report.source_row_count == d("0")
    assert digest_report.observation_count == d("0")
    assert digest_report.pass_count == d("0")
    assert digest_report.watch_count == d("0")
    assert digest_report.blocked_count == d("0")
    assert digest_report.max_abs_skew_shock_ratio == d("0.000000")
    assert digest_report.average_skew_shock_ratio == d("0.000000")
    assert digest_report.top_screening_priority_score == d("0.000000")
    assert digest_report.digest_status == "pass"
    assert digest_report.reason_codes == ("gold_options_skew_shock_digest_clear",)
    assert digest_report.shock_rows == ()
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_risk_digest_reduces_gold_options_skew_shocks() -> None:
    digest_report = report(
        observation(
            "source-inline",
            market_slug="gold-rangebound-weekly",
            expiry_bucket="weekly",
            put_delta_25_iv="0.251000",
            call_delta_25_iv="0.250000",
            atm_iv="0.250000",
            previous_skew_ratio="0.003000",
            source_row_count="1",
            observed_at=datetime(2026, 7, 4, 9, 15, tzinfo=timezone(timedelta(hours=-4))),
            reason_codes=("gold_options_skew_inline",),
        ),
        observation(
            "source-blocked-put",
            market_slug="gold-breaks-lower-after-fed",
            expiry_bucket="front_month",
            put_delta_25_iv="0.320000",
            call_delta_25_iv="0.240000",
            atm_iv="0.280000",
            previous_skew_ratio="0.210000",
            source_row_count="3",
            observed_at=datetime(2026, 7, 4, 12, 45, tzinfo=UTC),
            reason_codes=("gold_options_put_skew_widened",),
        ),
        observation(
            "source-watch-call",
            market_slug="gold-rallies-above-record-high",
            expiry_bucket="two_week",
            put_delta_25_iv="0.220000",
            call_delta_25_iv="0.260000",
            atm_iv="0.250000",
            previous_skew_ratio="-0.120000",
            source_row_count="2",
            observed_at=datetime(2026, 7, 4, 11, 30, tzinfo=UTC),
            reason_codes=("gold_options_call_skew_widened",),
        ),
    )

    assert digest_report.source_row_count == d("6")
    assert digest_report.observation_count == d("3")
    assert digest_report.pass_count == d("1")
    assert digest_report.watch_count == d("1")
    assert digest_report.blocked_count == d("1")
    assert digest_report.max_abs_skew_shock_ratio == d("0.075714")
    assert digest_report.average_skew_shock_ratio == d("0.012238")
    assert digest_report.top_screening_priority_score == d("1.000000")
    assert digest_report.digest_status == "blocked"
    assert digest_report.reason_codes == (
        "gold_options_skew_shock_blocked_present",
        "gold_options_skew_shock_mixed_direction_present",
    )

    assert tuple(row.source_id for row in digest_report.shock_rows) == (
        "source-blocked-put",
        "source-watch-call",
        "source-inline",
    )
    blocked_row = digest_report.shock_rows[0]
    assert blocked_row.skew_ratio == d("0.285714")
    assert blocked_row.skew_shock_ratio == d("0.075714")
    assert blocked_row.abs_skew_shock_ratio == d("0.075714")
    assert blocked_row.skew_direction == "put_skew_widening"
    assert blocked_row.shock_status == "blocked"
    assert blocked_row.screening_priority_score == d("1.000000")
    assert blocked_row.reason_codes == ("gold_options_put_skew_shock_blocked",)
    assert blocked_row.observed_at == datetime(2026, 7, 4, 12, 45, tzinfo=UTC)

    watch_row = digest_report.shock_rows[1]
    assert watch_row.skew_ratio == d("-0.160000")
    assert watch_row.skew_shock_ratio == d("-0.040000")
    assert watch_row.skew_direction == "call_skew_widening"
    assert watch_row.shock_status == "watch"
    assert watch_row.screening_priority_score == d("0.800000")
    assert watch_row.reason_codes == ("gold_options_call_skew_shock_watch",)

    assert digest_report.shock_rows[2].skew_direction == "inline"
    assert digest_report.shock_rows[2].shock_status == "pass"


def test_digest_is_deterministic_for_input_order_and_reason_codes() -> None:
    left = observation(
        "source-a",
        market_slug="gold-a",
        expiry_bucket="front_month",
        put_delta_25_iv="0.270000",
        call_delta_25_iv="0.250000",
        atm_iv="0.250000",
        previous_skew_ratio="0.040000",
        observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=UTC),
    )
    right = observation(
        "source-b",
        market_slug="gold-b",
        expiry_bucket="front_month",
        put_delta_25_iv="0.270000",
        call_delta_25_iv="0.250000",
        atm_iv="0.250000",
        previous_skew_ratio="0.040000",
        observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=UTC),
    )

    first = report(right, left)
    second = report(left, right)

    assert tuple(row.source_id for row in first.shock_rows) == ("source-a", "source-b")
    assert asdict(first) == asdict(second)
    assert first.reason_codes == (
        "gold_options_skew_shock_watch_present",
        "gold_options_put_skew_shock_present",
    )
    assert first.shock_rows[0].reason_codes == ("gold_options_put_skew_shock_watch",)


def test_validation_rejects_bad_types_timestamps_reasons_and_duplicates() -> None:
    digest = api()

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="put_delta_25_iv must be a Decimal"):
        digest.GoldOptionsSkewShockObservation(
            source_id="source-float",
            market_slug="gold-float",
            expiry_bucket="front_month",
            put_delta_25_iv=0.32,
            call_delta_25_iv=d("0.240000"),
            atm_iv=d("0.280000"),
            previous_skew_ratio=d("0.210000"),
            source_row_count=d("1"),
            observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=UTC),
            reason_codes=("gold_options_put_skew_widened",),
        )

    with pytest.raises(ValueError, match="watch_abs_skew_shock_ratio must be a Decimal"):
        digest.GoldOptionsSkewShockDigestConfig(
            watch_abs_skew_shock_ratio=DerivedDecimal("0.020000"),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest.build_market_research_gold_options_skew_shock_digest(
            (),
            generated_at=datetime(2026, 7, 4, 13, 0),
        )

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation("source-naive", observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="reason_codes must match skew shock direction"):
        observation(
            "source-bad-reason",
            reason_codes=("gold_options_call_skew_widened",),
        )

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(observation("source-dupe"), observation("source-dupe"))

    with pytest.raises(ValueError, match="blocked_abs_skew_shock_ratio"):
        digest.GoldOptionsSkewShockDigestConfig(
            watch_abs_skew_shock_ratio=d("0.050000"),
            blocked_abs_skew_shock_ratio=d("0.020000"),
        )


def test_frozen_dataclasses_and_hard_flags_are_enforced() -> None:
    digest = api()
    row = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        row.atm_iv = d("0.300000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        digest.GoldOptionsSkewShockDigestConfig(report_only=False)

    digest_report = report(row)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(digest_report.shock_rows[0], readonly=False)

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_non_default_thresholds_change_screening_status() -> None:
    digest = api()
    cfg = digest.GoldOptionsSkewShockDigestConfig(
        watch_abs_skew_shock_ratio=d("0.005000"),
        blocked_abs_skew_shock_ratio=d("0.010000"),
    )
    strict_report = report(
        observation(
            "source-strict",
            put_delta_25_iv="0.260000",
            call_delta_25_iv="0.250000",
            atm_iv="0.250000",
            previous_skew_ratio="0.030000",
        ),
        config=cfg,
    )

    assert strict_report.digest_status == "blocked"
    assert strict_report.blocked_count == d("1")
    assert strict_report.shock_rows[0].skew_shock_ratio == d("0.010000")
    assert strict_report.shock_rows[0].shock_status == "blocked"
    assert strict_report.shock_rows[0].screening_priority_score == d("1.000000")
    assert strict_report.reason_codes == (
        "gold_options_skew_shock_blocked_present",
        "gold_options_put_skew_shock_present",
    )


def test_payload_public_numerics_and_source_surfaces_are_safe() -> None:
    digest = api()
    digest_report = report(observation("source-json"))
    payload = digest.market_research_gold_options_skew_shock_digest_payload(digest_report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["shock_rows"][0]["put_delta_25_iv"] == "0.320000"
    assert payload["shock_rows"][0]["skew_shock_ratio"] == "0.075714"
    assert payload["shock_rows"][0]["observed_at"] == "2026-07-04T12:30:00+00:00"

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
    for row in digest_report.shock_rows:
        for value in asdict(row).values():
            if isinstance(value, Decimal):
                assert type(value) is Decimal
                assert value.as_tuple().exponent in (0, -6)

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_gold_options_skew_shock_digest.py"
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
