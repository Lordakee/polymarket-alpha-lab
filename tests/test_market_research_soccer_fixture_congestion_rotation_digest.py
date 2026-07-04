from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_soccer_fixture_congestion_rotation_digest.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_soccer_fixture_congestion_rotation_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    signal_id: str = "signal-alpha",
    *,
    match_id: str = "arsenal-chelsea",
    team_id: str = "arsenal",
    opponent_id: str = "chelsea",
    market_slug: str = "arsenal-chelsea-result",
    kickoff_at: datetime = datetime(2026, 7, 4, 19, 30, tzinfo=UTC),
    observed_at: datetime = datetime(2026, 7, 4, 11, 45, tzinfo=UTC),
    rest_hours: str | Decimal = "48.000000",
    travel_distance_km: str | Decimal = "350.000000",
    matches_last_14_days: str | Decimal = "3.000000",
    rotation_likelihood: str | Decimal = "0.560000",
    lineup_uncertainty: str | Decimal = "0.420000",
    reason_codes: tuple[str, ...] = ("soccer_fixture_congestion_pressure_watch",),
):
    module = api()
    return module.SoccerFixtureCongestionRotationSignal(
        signal_id=signal_id,
        match_id=match_id,
        team_id=team_id,
        opponent_id=opponent_id,
        market_slug=market_slug,
        kickoff_at=kickoff_at,
        observed_at=observed_at,
        rest_hours=rest_hours if isinstance(rest_hours, Decimal) else d(rest_hours),
        travel_distance_km=(
            travel_distance_km
            if isinstance(travel_distance_km, Decimal)
            else d(travel_distance_km)
        ),
        matches_last_14_days=(
            matches_last_14_days
            if isinstance(matches_last_14_days, Decimal)
            else d(matches_last_14_days)
        ),
        rotation_likelihood=(
            rotation_likelihood
            if isinstance(rotation_likelihood, Decimal)
            else d(rotation_likelihood)
        ),
        lineup_uncertainty=(
            lineup_uncertainty
            if isinstance(lineup_uncertainty, Decimal)
            else d(lineup_uncertainty)
        ),
        reason_codes=reason_codes,
    )


def build(*signals: object, generated_at: datetime = GENERATED_AT, cfg: object | None = None):
    module = api()
    return module.build_market_research_soccer_fixture_congestion_rotation_digest(
        signals,
        config=cfg or module.SoccerFixtureCongestionRotationDigestConfig(),
        generated_at=generated_at,
    )


def assert_payload_has_no_public_numbers(value: Any) -> None:
    if type(value) in {float, int}:
        pytest.fail(f"found public number in payload: {value!r}")
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = key.lower()
            assert "private_key" not in lowered
            assert "wallet" not in lowered
            assert "order" not in lowered
            assert "auth" not in lowered
            assert_payload_has_no_public_numbers(child)
    if isinstance(value, list):
        for child in value:
            assert_payload_has_no_public_numbers(child)


def test_digest_reduces_fixture_congestion_rotation_pressure_deterministically() -> None:
    module = api()

    report = build(
        signal(
            "signal-watch",
            match_id="bayern-dortmund",
            team_id="bayern",
            opponent_id="dortmund",
            market_slug="bayern-dortmund-winner",
            kickoff_at=datetime(2026, 7, 4, 21, 0, tzinfo=timezone(timedelta(hours=1))),
            observed_at=datetime(2026, 7, 4, 12, 30, tzinfo=timezone(timedelta(hours=1))),
            rest_hours="54.000000",
            travel_distance_km="780.000000",
            matches_last_14_days="3.000000",
            rotation_likelihood="0.540000",
            lineup_uncertainty="0.330000",
            reason_codes=("soccer_fixture_congestion_pressure_watch",),
        ),
        signal(
            "signal-blocked",
            match_id="madrid-atleti",
            team_id="madrid",
            opponent_id="atleti",
            market_slug="madrid-atleti-result",
            kickoff_at=datetime(2026, 7, 4, 18, 0, tzinfo=UTC),
            rest_hours="36.000000",
            travel_distance_km="1500.000000",
            matches_last_14_days="5.000000",
            rotation_likelihood="0.820000",
            lineup_uncertainty="0.660000",
            reason_codes=("soccer_fixture_congestion_pressure_high",),
        ),
        signal(
            "signal-inline",
            match_id="arsenal-chelsea",
            team_id="arsenal",
            opponent_id="chelsea",
            market_slug="arsenal-chelsea-result",
            rest_hours="96.000000",
            travel_distance_km="120.000000",
            matches_last_14_days="2.000000",
            rotation_likelihood="0.180000",
            lineup_uncertainty="0.120000",
            reason_codes=("soccer_fixture_congestion_pressure_inline",),
        ),
    )

    assert type(report) is module.SoccerFixtureCongestionRotationDigestReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-soccer-fixture-congestion-rotation-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_soccer_fixture_congestion_rotation_digest"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.high_pressure_count == d("1.000000")
    assert report.watch_pressure_count == d("1.000000")
    assert report.inline_pressure_count == d("1.000000")
    assert report.short_rest_count == d("2.000000")
    assert report.travel_burden_count == d("2.000000")
    assert report.rotation_pressure_count == d("2.000000")
    assert report.lineup_uncertainty_count == d("1.000000")
    assert report.max_congestion_score == d("1.000000")
    assert report.average_rest_hours == d("62.000000")
    assert report.reason_codes == (
        "soccer_fixture_congestion_high_pressure_present",
        "soccer_fixture_congestion_watch_pressure_present",
        "soccer_fixture_congestion_short_rest_present",
        "soccer_fixture_congestion_travel_burden_present",
        "soccer_fixture_congestion_rotation_likelihood_present",
        "soccer_fixture_congestion_lineup_uncertainty_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.market_slug for row in report.rows) == (
        "madrid-atleti-result",
        "bayern-dortmund-winner",
        "arsenal-chelsea-result",
    )
    blocked, watch, inline = report.rows
    assert blocked.pressure_bucket == "high_pressure"
    assert blocked.pressure_status == "blocked"
    assert blocked.congestion_score == d("1.000000")
    assert blocked.reason_codes == (
        "soccer_fixture_congestion_high_pressure",
        "soccer_fixture_congestion_short_rest",
        "soccer_fixture_congestion_travel_burden",
        "soccer_fixture_congestion_rotation_likely",
        "soccer_fixture_congestion_lineup_uncertain",
    )
    assert watch.kickoff_at == datetime(2026, 7, 4, 20, 0, tzinfo=UTC)
    assert watch.pressure_status == "watch"
    assert watch.congestion_score == d("0.650000")
    assert watch.reason_codes == (
        "soccer_fixture_congestion_watch_pressure",
        "soccer_fixture_congestion_short_rest",
        "soccer_fixture_congestion_travel_burden",
        "soccer_fixture_congestion_rotation_likely",
    )
    assert inline.pressure_status == "pass"
    assert inline.reason_codes == ("soccer_fixture_congestion_inline_pressure",)


def test_empty_digest_is_blocked_report_only_and_zeroed() -> None:
    module = api()

    report = build()

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_soccer_fixture_congestion_rotation_digest"
    )
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.high_pressure_count == d("0.000000")
    assert report.watch_pressure_count == d("0.000000")
    assert report.inline_pressure_count == d("0.000000")
    assert report.short_rest_count == d("0.000000")
    assert report.travel_burden_count == d("0.000000")
    assert report.rotation_pressure_count == d("0.000000")
    assert report.lineup_uncertainty_count == d("0.000000")
    assert report.max_congestion_score == d("0.000000")
    assert report.average_rest_hours == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("soccer_fixture_congestion_digest_empty",)
    assert report.reason_code_counts == (
        module.SoccerFixtureCongestionRotationReasonCodeCount(
            reason_code="soccer_fixture_congestion_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_validation_enforces_public_decimal_datetime_flags_and_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="rotation_likelihood must be a Decimal"):
        signal(rotation_likelihood=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="lineup_uncertainty must be between zero and one"):
        signal(lineup_uncertainty="1.100000")
    with pytest.raises(ValueError, match="rest_hours must be nonnegative"):
        signal(rest_hours="-1.000000")
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 11, 45))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_soccer_fixture_congestion_rotation_digest(
            (),
            config=module.SoccerFixtureCongestionRotationDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build(signal(observed_at=datetime(2026, 7, 4, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="reason_codes must match congestion_score"):
        signal(
            rest_hours="96.000000",
            travel_distance_km="120.000000",
            matches_last_14_days="2.000000",
            rotation_likelihood="0.180000",
            lineup_uncertainty="0.120000",
            reason_codes=("soccer_fixture_congestion_pressure_high",),
        )
    with pytest.raises(ValueError, match="signals must contain"):
        build("not-a-signal")
    with pytest.raises(ValueError, match="duplicate signal_id"):
        build(signal("signal-dupe"), signal("signal-dupe"))
    with pytest.raises(ValueError, match="high_congestion_score must be at least watch"):
        module.SoccerFixtureCongestionRotationDigestConfig(
            watch_congestion_score=d("0.800000"),
            high_congestion_score=d("0.700000"),
        )
    with pytest.raises(ValueError, match="watch_congestion_score must use supported default"):
        module.SoccerFixtureCongestionRotationDigestConfig(
            watch_congestion_score=d("0.400000"),
        )
    with pytest.raises(ValueError, match="config report_only must be True"):
        module.SoccerFixtureCongestionRotationDigestConfig(report_only=False)
    with pytest.raises(ValueError, match="signal readonly must be True"):
        replace(signal("signal-hard-flags"), readonly=False)

    row = build(signal("signal-row")).rows[0]
    with pytest.raises(ValueError, match="congestion_score must match row pressure inputs"):
        replace(row, congestion_score=d("0.999999"))
    with pytest.raises(ValueError, match="reason_codes must match row pressure evidence"):
        replace(
            row,
            reason_codes=("soccer_fixture_congestion_inline_pressure",),
        )

    frozen = signal("signal-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen.rest_hours = d("1.000000")  # type: ignore[misc]


def test_payload_uses_six_decimal_strings_and_module_has_no_live_surfaces() -> None:
    module = api()
    report = build(signal("signal-payload"))

    payload = module.market_research_soccer_fixture_congestion_rotation_digest_payload(
        report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["rest_hours"] == "48.000000"
    assert payload["rows"][0]["rotation_likelihood"] == "0.560000"
    assert payload["rows"][0]["kickoff_at"] == "2026-07-04T19:30:00+00:00"
    assert_payload_has_no_public_numbers(payload)

    for public_record in (
        module.SoccerFixtureCongestionRotationDigestConfig(),
        signal("signal-dataclass"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if _public_numeric(field.name):
                assert type(value) is Decimal, field.name

    source = MODULE_PATH.read_text()
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
        "db",
        "env",
        "requests",
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
        "live trading",
        "wallet",
        "private_key",
        "secret",
        "database",
        "network",
        "submit_order",
        "cancel_order",
        "replace_order",
    ):
        assert forbidden not in source.lower()


def _public_numeric(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_ratio")
        or field_name.endswith("_score")
        or field_name.endswith("_hours")
        or field_name.endswith("_km")
        or field_name.endswith("_days")
        or field_name.endswith("_likelihood")
        or field_name.endswith("_uncertainty")
    )
