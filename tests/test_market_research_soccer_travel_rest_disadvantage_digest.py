from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_soccer_travel_rest_disadvantage_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "short_rest_hours": d("72.000000"),
        "rest_disadvantage_hours": d("24.000000"),
        "long_travel_distance_km": d("2500.000000"),
        "timezone_shift_hours": d("3.000000"),
        "min_source_count": d("2.000000"),
        "watch_signal_count": d("2.000000"),
        "blocked_signal_count": d("4.000000"),
    }
    values.update(overrides)
    return module.MarketResearchSoccerTravelRestDisadvantageDigestConfig(**values)


def signal(
    signal_id: str = "signal-alpha",
    fixture_id: str = "fixture-alpha",
    team_id: str = "team-alpha",
    *,
    competition_id: str = "epl",
    opponent_id: str = "team-beta",
    venue_role: str = "home",
    observed_at: datetime = GENERATED_AT - timedelta(hours=2),
    team_rest_hours: Decimal = d("120.000000"),
    opponent_rest_hours: Decimal = d("110.000000"),
    travel_distance_km: Decimal = d("200.000000"),
    timezone_shift_hours: Decimal = d("0.000000"),
    source_count: Decimal = d("2.000000"),
    signal_config_version: str = "soccer-travel-rest-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketResearchSoccerTravelRestDisadvantageDigestSignal(
        signal_id=signal_id,
        fixture_id=fixture_id,
        competition_id=competition_id,
        team_id=team_id,
        opponent_id=opponent_id,
        venue_role=venue_role,
        observed_at=observed_at,
        team_rest_hours=team_rest_hours,
        opponent_rest_hours=opponent_rest_hours,
        travel_distance_km=travel_distance_km,
        timezone_shift_hours=timezone_shift_hours,
        source_count=source_count,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: object, **overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "signals": items,
        "config": config(),
        "generated_at": GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    }
    values.update(overrides)
    return module.build_market_research_soccer_travel_rest_disadvantage_digest(
        **values,
    )


def test_digest_flags_travel_rest_disadvantage_and_sorts_rows() -> None:
    module = api()

    report = build_report(
        signal(
            "signal-pass",
            "fixture-pass",
            "team-pass",
            opponent_id="team-rested",
            source_count=d("3.000000"),
        ),
        signal(
            "signal-blocked",
            "fixture-blocked",
            "team-tired",
            competition_id="ucl",
            opponent_id="team-fresh",
            venue_role="away",
            observed_at=datetime(
                2026,
                7,
                4,
                11,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            team_rest_hours=d("46.000000"),
            opponent_rest_hours=d("96.000000"),
            travel_distance_km=d("4200.000000"),
            timezone_shift_hours=d("4.000000"),
            source_count=d("1.000000"),
            signal_config_version="soccer-travel-rest-feed-v2",
        ),
        signal(
            "signal-watch",
            "fixture-watch",
            "team-watch",
            competition_id="cwc",
            opponent_id="team-home",
            venue_role="away",
            team_rest_hours=d("68.000000"),
            opponent_rest_hours=d("82.000000"),
            travel_distance_km=d("500.000000"),
            timezone_shift_hours=d("1.000000"),
            source_count=d("2.000000"),
            signal_config_version="soccer-travel-rest-feed-v1",
        ),
    )

    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-soccer-travel-rest-disadvantage-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_soccer_travel_rest_disadvantage_review"
    )
    assert report.signal_count == d("3.000000")
    assert report.blocked_signal_count == d("1.000000")
    assert report.watch_signal_count == d("1.000000")
    assert report.pass_signal_count == d("1.000000")
    assert report.short_rest_signal_count == d("2.000000")
    assert report.rest_gap_signal_count == d("1.000000")
    assert report.travel_load_signal_count == d("1.000000")
    assert report.timezone_shift_signal_count == d("1.000000")
    assert report.away_signal_count == d("2.000000")
    assert report.source_gap_signal_count == d("1.000000")
    assert report.max_disadvantage_pressure_score == d("1.000000")
    assert report.average_disadvantage_pressure_score == d("0.444444")
    assert report.min_team_rest_hours == d("46.000000")
    assert report.max_rest_disadvantage_hours == d("50.000000")
    assert report.max_travel_distance_km == d("4200.000000")
    assert report.reason_codes == (
        "soccer_travel_rest_disadvantage_blocked_present",
        "soccer_travel_rest_disadvantage_watch_present",
        "soccer_travel_rest_disadvantage_short_rest_present",
        "soccer_travel_rest_disadvantage_rest_gap_present",
        "soccer_travel_rest_disadvantage_travel_load_present",
        "soccer_travel_rest_disadvantage_timezone_shift_present",
        "soccer_travel_rest_disadvantage_away_present",
        "soccer_travel_rest_disadvantage_source_gap_present",
    )
    assert tuple(count.signal_count for count in report.reason_code_counts) == (
        d("1.000000"),
        d("1.000000"),
        d("2.000000"),
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
        d("2.000000"),
        d("1.000000"),
    )
    assert tuple(count.signal_ratio for count in report.reason_code_counts) == (
        d("0.333333"),
        d("0.333333"),
        d("0.666667"),
        d("0.333333"),
        d("0.333333"),
        d("0.333333"),
        d("0.666667"),
        d("0.333333"),
    )
    assert report.signal_config_versions == (
        ("fixture-blocked", "team-tired", "soccer-travel-rest-feed-v2"),
        ("fixture-pass", "team-pass", "soccer-travel-rest-source-v0"),
        ("fixture-watch", "team-watch", "soccer-travel-rest-feed-v1"),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.signal_id for row in report.rows) == (
        "signal-blocked",
        "signal-watch",
        "signal-pass",
    )
    blocked, watched, passed = report.rows
    assert blocked.digest_status == "blocked"
    assert blocked.observed_at == datetime(2026, 7, 4, 15, 30, tzinfo=UTC)
    assert blocked.rest_disadvantage_hours == d("50.000000")
    assert blocked.disadvantage_signal_count == d("6.000000")
    assert blocked.disadvantage_pressure_score == d("1.000000")
    assert blocked.reason_codes == (
        "soccer_travel_rest_disadvantage_short_rest",
        "soccer_travel_rest_disadvantage_rest_gap",
        "soccer_travel_rest_disadvantage_travel_load",
        "soccer_travel_rest_disadvantage_timezone_shift",
        "soccer_travel_rest_disadvantage_away",
        "soccer_travel_rest_disadvantage_source_gap",
        "soccer_travel_rest_disadvantage_blocked",
    )
    assert watched.digest_status == "watch"
    assert watched.reason_codes == (
        "soccer_travel_rest_disadvantage_short_rest",
        "soccer_travel_rest_disadvantage_away",
        "soccer_travel_rest_disadvantage_watch",
    )
    assert passed.digest_status == "pass"
    assert passed.reason_codes == ("soccer_travel_rest_disadvantage_clear",)


def test_empty_input_returns_blocked_report_only_digest() -> None:
    module = api()

    report = build_report()

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_soccer_travel_rest_disadvantage_review"
    )
    assert report.signal_count == d("0.000000")
    assert report.rows == ()
    assert report.max_disadvantage_pressure_score == d("0.000000")
    assert report.average_disadvantage_pressure_score == d("0.000000")
    assert report.min_team_rest_hours == d("0.000000")
    assert report.max_rest_disadvantage_hours == d("0.000000")
    assert report.max_travel_distance_km == d("0.000000")
    assert report.reason_codes == (
        "soccer_travel_rest_disadvantage_digest_empty",
    )
    assert report.reason_code_counts == (
        module.MarketResearchSoccerTravelRestDisadvantageDigestReasonCodeCount(
            reason_code="soccer_travel_rest_disadvantage_digest_empty",
            signal_count=d("1.000000"),
            signal_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_contract_rejects_subclasses_lists_noncanonical_decimals_and_future_times() -> None:
    module = api()

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "BadConfig",
            (module.MarketResearchSoccerTravelRestDisadvantageDigestConfig,),
            {},
        )
    with pytest.raises(ValueError, match="signal_id must be a string"):
        signal(signal_id=_StringSubclass("signal-alpha"))
    with pytest.raises(ValueError, match="team_rest_hours must be a Decimal"):
        signal(team_rest_hours=_DecimalSubclass("72.000000"))
    with pytest.raises(ValueError, match="team_rest_hours must use exactly six decimal places"):
        signal(team_rest_hours=d("72"))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(
            signal(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(signal(), generated_at=datetime(2026, 7, 4, 18, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 16, 0))
    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="signals must be a tuple"):
        module.build_market_research_soccer_travel_rest_disadvantage_digest(
            signals=[signal()],
            config=config(),
            generated_at=GENERATED_AT,
        )

    report = build_report(
        signal(
            "signal-blocked",
            venue_role="away",
            team_rest_hours=d("46.000000"),
            opponent_rest_hours=d("96.000000"),
            travel_distance_km=d("4200.000000"),
            timezone_shift_hours=d("4.000000"),
            source_count=d("1.000000"),
        ),
    )
    with pytest.raises(FrozenInstanceError):
        report.signal_count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="rows must be a tuple"):
        replace(report, rows=list(report.rows))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(report.rows[0], reason_codes=list(report.rows[0].reason_codes))
    with pytest.raises(ValueError, match="signal_count must be positive"):
        module.MarketResearchSoccerTravelRestDisadvantageDigestReasonCodeCount(
            reason_code="soccer_travel_rest_disadvantage_blocked_present",
            signal_count=d("0.000000"),
            signal_ratio=d("0.000000"),
        )
    with pytest.raises(ValueError, match="signal_count must be a whole Decimal"):
        module.MarketResearchSoccerTravelRestDisadvantageDigestReasonCodeCount(
            reason_code="soccer_travel_rest_disadvantage_blocked_present",
            signal_count=d("0.500000"),
            signal_ratio=d("0.500000"),
        )
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(report, reason_code_counts=report.reason_code_counts[1:])
    with pytest.raises(ValueError, match="signal paper_only must be True"):
        signal(paper_only=False)


def test_payload_serializes_recursively_and_rejects_mutated_nested_dataclasses() -> None:
    module = api()
    report = build_report(
        signal(
            "signal-payload",
            "fixture-payload",
            "team-payload",
            venue_role="away",
            team_rest_hours=d("46.000000"),
            opponent_rest_hours=d("96.000000"),
            travel_distance_km=d("4200.000000"),
            timezone_shift_hours=d("4.000000"),
            source_count=d("1.000000"),
        ),
    )

    payload = module.market_research_soccer_travel_rest_disadvantage_digest_payload(
        report,
    )

    assert payload["generated_at"] == "2026-07-04T18:00:00+00:00"
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T16:00:00+00:00"
    assert payload["rows"][0]["disadvantage_pressure_score"] == "1.000000"
    assert payload["reason_code_counts"][0]["signal_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_plain_payload(payload)

    object.__setattr__(
        report.rows[0],
        "observed_at",
        datetime(2026, 7, 4, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="observed_at must be UTC"):
        module.market_research_soccer_travel_rest_disadvantage_digest_payload(
            report,
        )

    fresh_report = build_report(
        signal(
            "signal-zero-count",
            "fixture-zero-count",
            "team-zero-count",
            venue_role="away",
            team_rest_hours=d("46.000000"),
            opponent_rest_hours=d("96.000000"),
            travel_distance_km=d("4200.000000"),
            timezone_shift_hours=d("4.000000"),
            source_count=d("1.000000"),
        ),
    )
    object.__setattr__(
        fresh_report.reason_code_counts[0],
        "signal_count",
        d("0.000000"),
    )
    with pytest.raises(ValueError, match="signal_count must be positive"):
        module.market_research_soccer_travel_rest_disadvantage_digest_payload(
            fresh_report,
        )


def test_builder_recursively_revalidates_tampered_signals() -> None:
    tampered = signal("signal-tampered-time", "fixture-tampered-time", "team-tampered")
    object.__setattr__(
        tampered,
        "observed_at",
        datetime(2026, 7, 4, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="observed_at must be UTC"):
        build_report(tampered)

    tampered = signal("signal-tampered-decimal", "fixture-tampered-decimal", "team-tampered")
    object.__setattr__(tampered, "team_rest_hours", d("72"))
    with pytest.raises(ValueError, match="team_rest_hours must use exactly six decimal places"):
        build_report(tampered)


def test_public_numeric_fields_are_exact_decimal_and_module_surface_is_pure() -> None:
    module = api()
    report = build_report(
        signal(
            "signal-public",
            "fixture-public",
            "team-public",
            venue_role="away",
            team_rest_hours=d("46.000000"),
            opponent_rest_hours=d("96.000000"),
            travel_distance_km=d("4200.000000"),
            timezone_shift_hours=d("4.000000"),
            source_count=d("1.000000"),
        ),
    )

    for item in (
        config(),
        signal(),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(item)
        assert item.__dataclass_params__.frozen is True
        for field in fields(item):
            value = getattr(item, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal
                assert value.as_tuple().exponent == -6

    exported = set(module.__all__)
    assert {
        "DEFAULT_MARKET_RESEARCH_SOCCER_TRAVEL_REST_DISADVANTAGE_DIGEST_CONFIG_VERSION",
        "MarketResearchSoccerTravelRestDisadvantageDigestConfig",
        "MarketResearchSoccerTravelRestDisadvantageDigestSignal",
        "MarketResearchSoccerTravelRestDisadvantageDigestReasonCodeCount",
        "MarketResearchSoccerTravelRestDisadvantageDigestRow",
        "MarketResearchSoccerTravelRestDisadvantageDigestReport",
        "build_market_research_soccer_travel_rest_disadvantage_digest",
        "market_research_soccer_travel_rest_disadvantage_digest_payload",
    } <= exported

    source = inspect.getsource(module)
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    forbidden_calls = {
        "open",
        "connect",
        "request",
        "post",
        "put",
        "delete",
        "patch",
        "commit",
        "execute",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
            assert all(alias.name != ("as" + "dict") for alias in node.names)
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
                assert func.id != ("as" + "dict")
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
                assert func.attr != ("as" + "dict")

    forbidden_import_fragments = (
        "db",
        "env",
        "req" + "uests",
        "url" + "lib",
        "sock" + "et",
        "sub" + "process",
        "psy" + "copg",
        "supa" + "base",
        "web3",
        "http",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for token in ("market_" + "slug", "ques" + "tion", "payload_" + "json"):
        assert token not in source


def _assert_plain_payload(value: object) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _assert_plain_payload(child)
        return
    if isinstance(value, list):
        for child in value:
            _assert_plain_payload(child)
        return
    assert not isinstance(value, (Decimal, datetime, float))
