from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 5, 2, 10, tzinfo=UTC)
START_AT = datetime(2026, 7, 4, 23, 5, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_baseball_late_inning_wind_carry_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "watch_wind_carry_shift_mph": d("6.000000"),
        "blocked_wind_carry_shift_mph": d("16.000000"),
        "watch_gust_carry_shift_mph": d("10.000000"),
        "blocked_gust_carry_shift_mph": d("24.000000"),
        "min_temperature_increase_f": d("7.000000"),
        "min_humidity_change_pct": d("12.000000"),
        "min_late_inning": d("7.000000"),
        "max_input_age_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return module.MarketResearchBaseballLateInningWindCarryDigestConfig(**values)


def observation(
    source_id: str = "source-alpha",
    *,
    market_slug: str = "mlb-yankees-red-sox-total",
    event_slug: str = "mlb-yankees-red-sox-20260704",
    market_type: str = "game_total",
    current_inning: Decimal = d("8.000000"),
    scheduled_start_at: datetime = START_AT,
    observed_at: datetime | None = None,
    prior_observed_at: datetime | None = None,
    prior_wind_direction: str = "neutral",
    current_wind_direction: str = "neutral",
    prior_sustained_wind_mph: Decimal = d("6.000000"),
    current_sustained_wind_mph: Decimal = d("8.000000"),
    prior_gust_wind_mph: Decimal = d("10.000000"),
    current_gust_wind_mph: Decimal = d("12.000000"),
    prior_temperature_f: Decimal = d("72.000000"),
    current_temperature_f: Decimal = d("73.000000"),
    prior_humidity_pct: Decimal = d("58.000000"),
    current_humidity_pct: Decimal = d("57.000000"),
    roof_status: str = "closed",
    roof_status_confirmed: bool = True,
    source_refs: tuple[str, ...] = ("public-carry-note",),
):
    module = api()
    resolved_observed_at = observed_at or GENERATED_AT - timedelta(seconds=900)
    return module.MarketResearchBaseballLateInningWindCarryObservation(
        source_id=source_id,
        market_slug=market_slug,
        event_slug=event_slug,
        market_type=market_type,
        current_inning=current_inning,
        scheduled_start_at=scheduled_start_at,
        observed_at=resolved_observed_at,
        prior_observed_at=prior_observed_at
        or resolved_observed_at - timedelta(seconds=900),
        prior_wind_direction=prior_wind_direction,
        current_wind_direction=current_wind_direction,
        prior_sustained_wind_mph=prior_sustained_wind_mph,
        current_sustained_wind_mph=current_sustained_wind_mph,
        prior_gust_wind_mph=prior_gust_wind_mph,
        current_gust_wind_mph=current_gust_wind_mph,
        prior_temperature_f=prior_temperature_f,
        current_temperature_f=current_temperature_f,
        prior_humidity_pct=prior_humidity_pct,
        current_humidity_pct=current_humidity_pct,
        roof_status=roof_status,
        roof_status_confirmed=roof_status_confirmed,
        source_refs=source_refs,
    )


def digest_report(*rows: object, cfg: object | None = None):
    module = api()
    return module.build_market_research_baseball_late_inning_wind_carry_digest(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = api()

    report = digest_report()

    assert isinstance(report, module.MarketResearchBaseballLateInningWindCarryDigestReport)
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-baseball-late-inning-wind-carry-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_baseball_late_inning_wind_carry_screening"
    )
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.stale_input_count == d("0.000000")
    assert report.late_inning_risk_count == d("0.000000")
    assert report.wind_carry_shift_count == d("0.000000")
    assert report.gust_carry_shift_count == d("0.000000")
    assert report.temperature_shift_count == d("0.000000")
    assert report.humidity_shift_count == d("0.000000")
    assert report.open_roof_count == d("0.000000")
    assert report.totals_market_count == d("0.000000")
    assert report.home_run_market_count == d("0.000000")
    assert report.max_input_age_seconds == d("0.000000")
    assert report.max_wind_carry_shift_mph == d("0.000000")
    assert report.max_gust_carry_shift_mph == d("0.000000")
    assert report.max_temperature_increase_f == d("0.000000")
    assert report.max_humidity_change_pct == d("0.000000")
    assert report.carry_risk_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "baseball_late_inning_wind_carry_digest_empty",
    )
    assert report.reason_code_counts == (
        module.MarketResearchBaseballLateInningWindCarryReasonCodeCount(
            reason_code="baseball_late_inning_wind_carry_digest_empty",
            market_count=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_late_inning_wind_carry_flags_totals_and_home_run_markets() -> None:
    module = api()

    report = digest_report(
        observation(
            "source-watch",
            market_slug="mlb-wrigley-total",
            market_type="game_total",
            prior_wind_direction="neutral",
            current_wind_direction="outbound",
            prior_sustained_wind_mph=d("5.000000"),
            current_sustained_wind_mph=d("12.000000"),
            prior_gust_wind_mph=d("10.000000"),
            current_gust_wind_mph=d("22.000000"),
            prior_temperature_f=d("71.000000"),
            current_temperature_f=d("79.000000"),
            prior_humidity_pct=d("60.000000"),
            current_humidity_pct=d("47.000000"),
            roof_status="open",
        ),
        observation("source-pass", market_slug="mlb-clear-total"),
        observation(
            "source-blocked",
            market_slug="mlb-coors-home-run-yes",
            market_type="home_run",
            current_inning=d("9.000000"),
            observed_at=datetime(
                2026,
                7,
                4,
                21,
                55,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            prior_wind_direction="inbound",
            current_wind_direction="outbound",
            prior_sustained_wind_mph=d("5.000000"),
            current_sustained_wind_mph=d("22.000000"),
            prior_gust_wind_mph=d("12.000000"),
            current_gust_wind_mph=d("38.000000"),
            prior_temperature_f=d("74.000000"),
            current_temperature_f=d("84.000000"),
            prior_humidity_pct=d("62.000000"),
            current_humidity_pct=d("46.000000"),
            roof_status="open",
        ),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_baseball_late_inning_wind_carry_screening"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.stale_input_count == d("0.000000")
    assert report.late_inning_risk_count == d("2.000000")
    assert report.wind_carry_shift_count == d("2.000000")
    assert report.gust_carry_shift_count == d("2.000000")
    assert report.temperature_shift_count == d("2.000000")
    assert report.humidity_shift_count == d("2.000000")
    assert report.open_roof_count == d("2.000000")
    assert report.totals_market_count == d("1.000000")
    assert report.home_run_market_count == d("1.000000")
    assert report.max_input_age_seconds == d("900.000000")
    assert report.max_wind_carry_shift_mph == d("27.000000")
    assert report.max_gust_carry_shift_mph == d("50.000000")
    assert report.max_temperature_increase_f == d("10.000000")
    assert report.max_humidity_change_pct == d("16.000000")
    assert report.carry_risk_score == d("1.000000")
    assert tuple(row.market_slug for row in report.rows) == (
        "mlb-coors-home-run-yes",
        "mlb-wrigley-total",
        "mlb-clear-total",
    )
    assert report.reason_codes == (
        "baseball_late_inning_wind_carry_wind_carry_shift",
        "baseball_late_inning_wind_carry_gust_carry_shift",
        "baseball_late_inning_wind_carry_temperature_boost",
        "baseball_late_inning_wind_carry_humidity_change",
        "baseball_late_inning_wind_carry_open_roof",
        "baseball_late_inning_wind_carry_totals_market",
        "baseball_late_inning_wind_carry_home_run_market",
    )
    assert tuple(item.market_count for item in report.reason_code_counts) == (
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
        d("1.000000"),
        d("1.000000"),
    )

    blocked, watch, passed = report.rows
    assert blocked.row_status == "blocked"
    assert blocked.observed_at == datetime(2026, 7, 5, 1, 55, tzinfo=UTC)
    assert blocked.input_age_seconds == d("900.000000")
    assert blocked.wind_carry_shift_mph == d("27.000000")
    assert blocked.gust_carry_shift_mph == d("50.000000")
    assert blocked.temperature_increase_f == d("10.000000")
    assert blocked.humidity_change_pct == d("16.000000")
    assert blocked.reason_codes == (
        "baseball_late_inning_wind_carry_wind_carry_shift",
        "baseball_late_inning_wind_carry_gust_carry_shift",
        "baseball_late_inning_wind_carry_temperature_boost",
        "baseball_late_inning_wind_carry_humidity_change",
        "baseball_late_inning_wind_carry_open_roof",
        "baseball_late_inning_wind_carry_home_run_market",
    )
    assert watch.row_status == "watch"
    assert watch.wind_carry_shift_mph == d("12.000000")
    assert watch.gust_carry_shift_mph == d("22.000000")
    assert watch.reason_codes == (
        "baseball_late_inning_wind_carry_wind_carry_shift",
        "baseball_late_inning_wind_carry_gust_carry_shift",
        "baseball_late_inning_wind_carry_temperature_boost",
        "baseball_late_inning_wind_carry_humidity_change",
        "baseball_late_inning_wind_carry_open_roof",
        "baseball_late_inning_wind_carry_totals_market",
    )
    assert passed.row_status == "pass"
    assert passed.reason_codes == ("baseball_late_inning_wind_carry_clear",)


def test_rows_reason_codes_and_counts_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        market_slug="zeta-watch",
        prior_wind_direction="neutral",
        current_wind_direction="outbound",
        current_sustained_wind_mph=d("12.000000"),
        current_gust_wind_mph=d("22.000000"),
    )
    second = observation(
        "source-blocked",
        market_slug="alpha-blocked",
        prior_wind_direction="inbound",
        current_wind_direction="outbound",
        prior_sustained_wind_mph=d("4.000000"),
        current_sustained_wind_mph=d("22.000000"),
        prior_gust_wind_mph=d("8.000000"),
        current_gust_wind_mph=d("38.000000"),
    )
    third = observation(
        "source-watch-a",
        market_slug="alpha-watch",
        prior_wind_direction="neutral",
        current_wind_direction="outbound",
        current_sustained_wind_mph=d("12.000000"),
        current_gust_wind_mph=d("22.000000"),
    )

    forward = digest_report(first, second, third)
    reverse = digest_report(third, second, first)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "alpha-blocked",
        "alpha-watch",
        "zeta-watch",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(
            code for code in module_row_reason_order() if code in row.reason_codes
        )
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        "baseball_late_inning_wind_carry_wind_carry_shift",
        "baseball_late_inning_wind_carry_gust_carry_shift",
        "baseball_late_inning_wind_carry_totals_market",
    )


def test_pre_late_inning_rows_do_not_trigger_carry_reasons() -> None:
    report = digest_report(
        observation(
            "source-early",
            current_inning=d("6.000000"),
            prior_wind_direction="inbound",
            current_wind_direction="outbound",
            prior_sustained_wind_mph=d("10.000000"),
            current_sustained_wind_mph=d("25.000000"),
            prior_gust_wind_mph=d("15.000000"),
            current_gust_wind_mph=d("40.000000"),
            prior_temperature_f=d("70.000000"),
            current_temperature_f=d("90.000000"),
            prior_humidity_pct=d("70.000000"),
            current_humidity_pct=d("35.000000"),
            roof_status="open",
        ),
    )

    assert report.digest_status == "pass"
    assert report.rows[0].row_status == "pass"
    assert report.rows[0].reason_codes == ("baseball_late_inning_wind_carry_clear",)
    assert report.reason_codes == ("baseball_late_inning_wind_carry_digest_clear",)


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = api()

    with pytest.raises(ValueError, match="current_sustained_wind_mph must be a Decimal"):
        observation(current_sustained_wind_mph=_DecimalSubclass("8.000000"))
    with pytest.raises(ValueError, match="prior_humidity_pct must be between zero and one hundred"):
        observation(prior_humidity_pct=d("101.000000"))
    with pytest.raises(ValueError, match="scheduled_start_at must be timezone-aware"):
        observation(scheduled_start_at=datetime(2026, 7, 4, 23, 5))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_baseball_late_inning_wind_carry_digest(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 5, 2, 10, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        digest_report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        digest_report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="watch_wind_carry_shift_mph"):
        module.MarketResearchBaseballLateInningWindCarryDigestConfig(
            watch_wind_carry_shift_mph=d("20.000000"),
            blocked_wind_carry_shift_mph=d("10.000000"),
        )
    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        digest_report(
            observation(
                "source-future",
                observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="prior_observed_at must not exceed observed_at"):
        observation(
            "source-prior-future",
            prior_observed_at=GENERATED_AT - timedelta(seconds=100),
            observed_at=GENERATED_AT - timedelta(seconds=200),
        )
    with pytest.raises(ValueError, match="current_gust_wind_mph"):
        observation(
            "source-bad-gust",
            current_sustained_wind_mph=d("20.000000"),
            current_gust_wind_mph=d("19.000000"),
        )

    valid_row = digest_report(observation("source-valid")).rows[0]
    with pytest.raises(ValueError, match="wind_carry_shift_mph must match"):
        replace(valid_row, wind_carry_shift_mph=d("999.000000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "baseball_late_inning_wind_carry_clear",
                "baseball_late_inning_wind_carry_wind_carry_shift",
            ),
        )

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_rows_counts_and_report() -> None:
    module = api()

    report = digest_report(observation("source-hard-flags"))
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)
    assert all(
        count.paper_only and count.report_only and count.readonly
        for count in report.reason_code_counts
    )

    with pytest.raises(ValueError, match="paper_only"):
        module.MarketResearchBaseballLateInningWindCarryDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)


def test_payload_uses_six_decimal_strings_and_redacts_sensitive_refs() -> None:
    module = api()
    report = digest_report(
        observation(
            "source-payload",
            prior_wind_direction="neutral",
            current_wind_direction="outbound",
            current_sustained_wind_mph=d("12.000000"),
            current_gust_wind_mph=d("22.000000"),
            source_refs=("public-carry-note", "https://example.test/path?token=abcd"),
        ),
    )

    payload = module.market_research_baseball_late_inning_wind_carry_digest_payload(
        report,
    )
    payload_text = repr(payload).lower()

    assert payload["generated_at"] == "2026-07-05T02:10:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["wind_carry_shift_mph"] == "12.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-05T01:55:00+00:00"
    assert payload["rows"][0]["redacted_source_refs"] == [
        "[redacted-ref]",
        "public-carry-note",
    ]
    assert json.loads(json.dumps(payload, allow_nan=False, sort_keys=True)) == payload
    assert "token" not in payload_text
    assert "abcd" not in payload_text
    walk_payload(payload)

    for public_record in (
        config(),
        observation("source-dataclass"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        assert_public_numbers_are_decimal(public_record)


def test_module_scope_excludes_io_mutation_sensitive_surfaces_and_float_literals() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    lowered_source = source.lower()

    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )
    for forbidden in (
        "private_key",
        "wallet",
        "auth",
        "token",
        "trading",
        "order",
        "cancel",
        "replace",
        "exchange",
        "secret",
        "api_key",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
    ):
        assert forbidden not in lowered_source

    imported_modules: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "http",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    )
    forbidden_call_names = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "delete",
        "send",
        "write",
    }
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not (called_names & forbidden_call_names)


def test_public_numeric_fields_are_decimal_only() -> None:
    module = api()
    public_classes = (
        module.MarketResearchBaseballLateInningWindCarryDigestConfig,
        module.MarketResearchBaseballLateInningWindCarryObservation,
        module.MarketResearchBaseballLateInningWindCarryDigestRow,
        module.MarketResearchBaseballLateInningWindCarryReasonCodeCount,
        module.MarketResearchBaseballLateInningWindCarryDigestReport,
    )
    numeric_name_fragments = (
        "count",
        "mph",
        "seconds",
        "score",
        "ratio",
        "inning",
        "temperature",
        "humidity",
    )

    for cls in public_classes:
        for field in fields(cls):
            if field.name in ("rows", "reason_code_counts"):
                continue
            if any(fragment in field.name for fragment in numeric_name_fragments):
                assert field.type in (Decimal, "Decimal")


def module_row_reason_order() -> tuple[str, ...]:
    return (
        "baseball_late_inning_wind_carry_clear",
        "baseball_late_inning_wind_carry_stale_input",
        "baseball_late_inning_wind_carry_wind_carry_shift",
        "baseball_late_inning_wind_carry_gust_carry_shift",
        "baseball_late_inning_wind_carry_temperature_boost",
        "baseball_late_inning_wind_carry_humidity_change",
        "baseball_late_inning_wind_carry_open_roof",
        "baseball_late_inning_wind_carry_totals_market",
        "baseball_late_inning_wind_carry_home_run_market",
    )


def walk_payload(value: Any) -> None:
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


def assert_public_numbers_are_decimal(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numbers_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, tuple):
        for item in value:
            assert_public_numbers_are_decimal(item)
        return
    if isinstance(value, Decimal):
        assert type(value) is Decimal
