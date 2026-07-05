from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 5, 1, 0, tzinfo=UTC)
BASE_OBSERVED_AT = datetime(2026, 7, 4, 22, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_basketball_travel_fatigue_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    digest = module()
    values: dict[str, object] = {
        "fatigue_index_watch_threshold": d("0.650000"),
        "back_to_back_game_watch_threshold": d("1.000000"),
        "rest_hour_watch_threshold": d("24.000000"),
        "travel_mile_watch_threshold": d("750.000000"),
        "timezone_shift_hour_watch_threshold": d("2.000000"),
        "road_trip_game_watch_threshold": d("3.000000"),
        "min_signal_count": d("2.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchBasketballTravelFatigueDigestConfig(**values)


def signal(
    team_event_key: str = "event.nba.lal-den.20260704.lal",
    team_key: str = "lal",
    *,
    event_key: str = "event.nba.lal-den.20260704",
    league_key: str = "nba",
    observed_at: datetime = BASE_OBSERVED_AT,
    back_to_back_game_count: Decimal = d("0.000000"),
    rest_hours: Decimal = d("36.000000"),
    travel_miles: Decimal = d("120.000000"),
    timezone_shift_hours: Decimal = d("0.000000"),
    road_trip_game_count: Decimal = d("1.000000"),
    source_count: Decimal = d("2.000000"),
    signal_config_version: str = "basketball-travel-fatigue-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchBasketballTravelFatigueDigestSignal(
        team_event_key=team_event_key,
        event_key=event_key,
        team_key=team_key,
        league_key=league_key,
        observed_at=observed_at,
        back_to_back_game_count=back_to_back_game_count,
        rest_hours=rest_hours,
        travel_miles=travel_miles,
        timezone_shift_hours=timezone_shift_hours,
        road_trip_game_count=road_trip_game_count,
        source_count=source_count,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals: object, **overrides: object):
    digest = module()
    values: dict[str, object] = {
        "signals": signals,
        "config": config(),
        "generated_at": GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    }
    values.update(overrides)
    return digest.build_market_research_basketball_travel_fatigue_digest(**values)


def test_empty_input_is_blocked_with_one_empty_reason_count() -> None:
    digest = module()

    report = build_report()

    assert isinstance(report, digest.MarketResearchBasketballTravelFatigueDigestReport)
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-basketball-travel-fatigue-digest-v0"
    )
    assert report.research_scope == (
        "basketball back-to-back travel fatigue phase 1 research digest only"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_basketball_travel_fatigue_digest"
    )
    assert report.team_event_count == d("0.000000")
    assert report.watch_team_event_count == d("0.000000")
    assert report.clear_team_event_count == d("0.000000")
    assert report.limited_history_team_event_count == d("0.000000")
    assert report.signal_count == d("0.000000")
    assert report.max_fatigue_index is None
    assert report.max_travel_miles is None
    assert report.min_rest_hours is None
    assert report.max_timezone_shift_hours is None
    assert report.max_road_trip_game_count is None
    assert report.rows == ()
    assert report.source_config_versions == ()
    assert report.reason_codes == ("basketball_travel_fatigue_empty",)
    assert report.reason_code_counts == (
        digest.MarketResearchBasketballTravelFatigueDigestReasonCodeCount(
            reason_code="basketball_travel_fatigue_empty",
            team_event_count=d("1.000000"),
            team_event_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_digest_flags_back_to_back_travel_rest_timezone_and_road_trip() -> None:
    report = build_report(
        signal(
            "event.nba.lal-den.20260704.lal",
            "lal",
            observed_at=GENERATED_AT - timedelta(hours=5),
            back_to_back_game_count=d("0.000000"),
            rest_hours=d("30.000000"),
            travel_miles=d("420.000000"),
            timezone_shift_hours=d("1.000000"),
            road_trip_game_count=d("2.000000"),
            signal_config_version="basketball-schedule-feed-v0",
        ),
        signal(
            "event.nba.lal-den.20260704.lal",
            "lal",
            observed_at=GENERATED_AT - timedelta(hours=1),
            back_to_back_game_count=d("1.000000"),
            rest_hours=d("18.000000"),
            travel_miles=d("950.000000"),
            timezone_shift_hours=d("3.000000"),
            road_trip_game_count=d("4.000000"),
            signal_config_version="basketball-schedule-feed-v1",
        ),
        signal(
            "event.nba.bos-mia.20260704.bos",
            "bos",
            event_key="event.nba.bos-mia.20260704",
            observed_at=GENERATED_AT - timedelta(minutes=45),
            back_to_back_game_count=d("0.000000"),
            rest_hours=d("42.000000"),
            travel_miles=d("80.000000"),
            timezone_shift_hours=d("0.000000"),
            road_trip_game_count=d("1.000000"),
        ),
        signal(
            "event.nba.bos-mia.20260704.bos",
            "bos",
            event_key="event.nba.bos-mia.20260704",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            back_to_back_game_count=d("0.000000"),
            rest_hours=d("40.000000"),
            travel_miles=d("120.000000"),
            timezone_shift_hours=d("1.000000"),
            road_trip_game_count=d("1.000000"),
        ),
    )

    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_basketball_travel_fatigue_digest"
    )
    assert report.team_event_count == d("2.000000")
    assert report.watch_team_event_count == d("1.000000")
    assert report.clear_team_event_count == d("1.000000")
    assert report.limited_history_team_event_count == d("0.000000")
    assert report.signal_count == d("4.000000")
    assert report.fatigue_index_team_event_count == d("1.000000")
    assert report.back_to_back_team_event_count == d("1.000000")
    assert report.short_rest_team_event_count == d("1.000000")
    assert report.travel_fatigue_team_event_count == d("1.000000")
    assert report.timezone_shift_team_event_count == d("1.000000")
    assert report.road_trip_team_event_count == d("1.000000")
    assert report.max_fatigue_index == d("0.850000")
    assert report.max_travel_miles == d("950.000000")
    assert report.min_rest_hours == d("18.000000")
    assert report.max_timezone_shift_hours == d("3.000000")
    assert report.max_road_trip_game_count == d("4.000000")
    assert report.reason_codes == (
        "basketball_travel_fatigue_index_high",
        "basketball_travel_fatigue_back_to_back_spot",
        "basketball_travel_fatigue_rest_short",
        "basketball_travel_fatigue_travel_high",
        "basketball_travel_fatigue_timezone_shift_high",
        "basketball_travel_fatigue_road_trip_load_high",
    )
    assert report.source_config_versions == (
        ("event.nba.bos-mia.20260704.bos", "basketball-travel-fatigue-source-v0"),
        ("event.nba.lal-den.20260704.lal", "basketball-schedule-feed-v0"),
        ("event.nba.lal-den.20260704.lal", "basketball-schedule-feed-v1"),
    )

    assert tuple(row.team_event_key for row in report.rows) == (
        "event.nba.lal-den.20260704.lal",
        "event.nba.bos-mia.20260704.bos",
    )
    watch_row = report.rows[0]
    assert watch_row.digest_status == "watch"
    assert watch_row.latest_observed_at == GENERATED_AT - timedelta(hours=1)
    assert watch_row.fatigue_index == d("0.850000")
    assert watch_row.max_travel_miles == d("950.000000")
    assert watch_row.min_rest_hours == d("18.000000")
    assert watch_row.max_timezone_shift_hours == d("3.000000")
    assert watch_row.max_road_trip_game_count == d("4.000000")
    assert watch_row.reason_codes == (
        "basketball_travel_fatigue_index_high",
        "basketball_travel_fatigue_back_to_back_spot",
        "basketball_travel_fatigue_rest_short",
        "basketball_travel_fatigue_travel_high",
        "basketball_travel_fatigue_timezone_shift_high",
        "basketball_travel_fatigue_road_trip_load_high",
    )
    assert report.rows[1].digest_status == "clear"
    assert report.rows[1].reason_codes == ("basketball_travel_fatigue_clear",)


def test_digest_passes_for_clear_and_limited_history_inputs() -> None:
    report = build_report(
        signal(
            "event.nba.atl-chi.20260704.atl",
            "atl",
            event_key="event.nba.atl-chi.20260704",
        ),
        signal(
            "event.nba.atl-chi.20260704.atl",
            "atl",
            event_key="event.nba.atl-chi.20260704",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            rest_hours=d("44.000000"),
            travel_miles=d("140.000000"),
        ),
        signal(
            "event.nba.mia-orl.20260704.mia",
            "mia",
            event_key="event.nba.mia-orl.20260704",
        ),
    )

    assert report.digest_status == "pass"
    assert report.recommended_next_step == (
        "allow_report_only_basketball_travel_fatigue_digest"
    )
    assert report.reason_codes == (
        "basketball_travel_fatigue_limited_history",
        "basketball_travel_fatigue_passed",
    )
    assert report.reason_code_counts == (
        module().MarketResearchBasketballTravelFatigueDigestReasonCodeCount(
            reason_code="basketball_travel_fatigue_limited_history",
            team_event_count=d("1.000000"),
            team_event_ratio=d("0.500000"),
        ),
    )
    assert tuple((row.team_event_key, row.digest_status) for row in report.rows) == (
        ("event.nba.mia-orl.20260704.mia", "limited_history"),
        ("event.nba.atl-chi.20260704.atl", "clear"),
    )


def test_payload_uses_six_decimal_strings_iso_datetimes_and_no_sensitive_surface() -> None:
    digest = module()
    report = build_report(
        signal(
            "event.nba.payload.20260704.sea",
            "sea",
            event_key="event.nba.payload.20260704",
            observed_at=datetime(2026, 7, 4, 17, 0, tzinfo=timezone(timedelta(hours=-4))),
            rest_hours=d("24.000000"),
            travel_miles=d("300.000000"),
        ),
        signal(
            "event.nba.payload.20260704.sea",
            "sea",
            event_key="event.nba.payload.20260704",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            back_to_back_game_count=d("1.000000"),
            rest_hours=d("18.000000"),
            travel_miles=d("950.000000"),
            timezone_shift_hours=d("3.000000"),
            road_trip_game_count=d("4.000000"),
        ),
    )

    payload = digest.market_research_basketball_travel_fatigue_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-05T01:00:00+00:00"
    assert payload["team_event_count"] == "1.000000"
    assert payload["rows"][0]["latest_observed_at"] == "2026-07-05T00:30:00+00:00"
    assert payload["rows"][0]["fatigue_index"] == "0.850000"
    assert payload["rows"][0]["max_travel_miles"] == "950.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    for value in _walk_payload_values(payload):
        assert not isinstance(value, (Decimal, datetime, float))
        if not isinstance(value, bool):
            assert not isinstance(value, int)

    payload_text = repr(payload).lower()
    for forbidden in (
        "wallet",
        "broker",
        "account",
        "advice",
        "auth",
        "signing",
        "submit",
        "cancel",
        "secret",
        "token",
        "exchange_mutation",
    ):
        assert forbidden not in payload_text


def test_builder_uses_default_config_only_when_config_is_none() -> None:
    digest = module()

    omitted_config_report = (
        digest.build_market_research_basketball_travel_fatigue_digest(
            (),
            generated_at=GENERATED_AT,
        )
    )
    explicit_none_report = (
        digest.build_market_research_basketball_travel_fatigue_digest(
            (),
            config=None,
            generated_at=GENERATED_AT,
        )
    )

    assert omitted_config_report.config_version == (
        "market-research-basketball-travel-fatigue-digest-v0"
    )
    assert explicit_none_report.config_version == (
        "market-research-basketball-travel-fatigue-digest-v0"
    )

    unsafe_config = config()
    object.__setattr__(unsafe_config, "report_only", False)
    with pytest.raises(ValueError, match="config report_only must be True"):
        digest.build_market_research_basketball_travel_fatigue_digest(
            (),
            config=unsafe_config,
            generated_at=GENERATED_AT,
        )


def test_payload_rejects_tampered_nested_public_dataclass_flags() -> None:
    digest = module()
    report = build_report(signal())
    object.__setattr__(report.rows[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly must be True"):
        digest.market_research_basketball_travel_fatigue_digest_payload(report)


def test_payload_rejects_tampered_nested_non_six_decimal_values() -> None:
    digest = module()
    report = build_report(signal())
    object.__setattr__(report.reason_code_counts[0], "team_event_ratio", d("1.0000000"))

    with pytest.raises(ValueError, match="six-decimal Decimal"):
        digest.market_research_basketball_travel_fatigue_digest_payload(report)


def test_validation_rejects_bad_inputs_and_public_record_inconsistency() -> None:
    digest = module()

    frozen_signal = signal()
    with pytest.raises(FrozenInstanceError):
        frozen_signal.rest_hours = d("30.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="rest_hours must be a Decimal"):
        signal(rest_hours=24)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 22, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 22, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(
            signal(),
            generated_at=_DateTimeSubclass(2026, 7, 5, 1, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="fatigue_index_watch_threshold"):
        config(fatigue_index_watch_threshold=_DecimalSubclass("0.650000"))
    with pytest.raises(ValueError, match="min_signal_count"):
        config(min_signal_count=d("1.500000"))
    with pytest.raises(ValueError, match="config_version must be the supported"):
        config(config_version="market-research-basketball-travel-fatigue-test-v0")

    with pytest.raises(ValueError, match="signal report_only must be True"):
        replace(frozen_signal, report_only=False)
    report = build_report(
        signal(
            "event.nba.valid.20260704.nyk",
            "nyk",
            event_key="event.nba.valid.20260704",
        ),
        signal(
            "event.nba.valid.20260704.nyk",
            "nyk",
            event_key="event.nba.valid.20260704",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
        ),
    )
    with pytest.raises(ValueError, match="report readonly must be True"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="signals must not contain duplicate"):
        build_report(
            signal(signal_config_version="source-a"),
            signal(signal_config_version="source-b"),
        )
    with pytest.raises(ValueError, match="team_key must match within team_event_key"):
        build_report(
            signal("event.nba.same.20260704.nyk", "nyk"),
            signal(
                "event.nba.same.20260704.nyk",
                "bkn",
                observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            ),
        )
    with pytest.raises(ValueError, match="event_key must match within team_event_key"):
        build_report(
            signal("event.nba.same.20260704.nyk", "nyk", event_key="event.nba.one"),
            signal(
                "event.nba.same.20260704.nyk",
                "nyk",
                event_key="event.nba.two",
                observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            ),
        )
    with pytest.raises(ValueError, match="league_key must match within team_event_key"):
        build_report(
            signal("event.nba.same.20260704.nyk", "nyk", league_key="nba"),
            signal(
                "event.nba.same.20260704.nyk",
                "nyk",
                league_key="wnba",
                observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
            ),
        )
    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))

    bad_report_values = {field.name: getattr(report, field.name) for field in fields(report)}
    bad_report_values["team_event_count"] = d("2.000000")
    with pytest.raises(ValueError, match="team_event_count must match rows"):
        digest.MarketResearchBasketballTravelFatigueDigestReport(**bad_report_values)

    row = report.rows[0]
    with pytest.raises(ValueError, match="fatigue_index must match latest values"):
        replace(row, fatigue_index=d("0.500000"))
    with pytest.raises(ValueError, match="team_event_count must be positive"):
        digest.MarketResearchBasketballTravelFatigueDigestReasonCodeCount(
            reason_code="basketball_travel_fatigue_index_high",
            team_event_count=d("0.000000"),
            team_event_ratio=d("0.000000"),
        )


def test_public_constructors_reject_noncanonical_sequences() -> None:
    digest = module()
    report = build_report(
        signal(
            "event.nba.lal-den.20260704.lal",
            "lal",
            observed_at=GENERATED_AT - timedelta(hours=5),
        ),
        signal(
            "event.nba.lal-den.20260704.lal",
            "lal",
            observed_at=GENERATED_AT - timedelta(hours=1),
            back_to_back_game_count=d("1.000000"),
            rest_hours=d("18.000000"),
            travel_miles=d("950.000000"),
            timezone_shift_hours=d("3.000000"),
            road_trip_game_count=d("4.000000"),
        ),
        signal(
            "event.nba.bos-mia.20260704.bos",
            "bos",
            event_key="event.nba.bos-mia.20260704",
        ),
        signal(
            "event.nba.bos-mia.20260704.bos",
            "bos",
            event_key="event.nba.bos-mia.20260704",
            observed_at=BASE_OBSERVED_AT + timedelta(minutes=30),
        ),
    )

    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["rows"] = tuple(reversed(report.rows))
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        digest.MarketResearchBasketballTravelFatigueDigestReport(**values)

    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["source_config_versions"] = tuple(reversed(report.source_config_versions))
    with pytest.raises(ValueError, match="source_config_versions must be sorted"):
        digest.MarketResearchBasketballTravelFatigueDigestReport(**values)

    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["reason_code_counts"] = tuple(reversed(report.reason_code_counts))
    with pytest.raises(ValueError, match="reason_code_counts must be sorted"):
        digest.MarketResearchBasketballTravelFatigueDigestReport(**values)

    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["reason_codes"] = tuple(reversed(report.reason_codes))
    with pytest.raises(ValueError, match="reason_codes must be sorted"):
        digest.MarketResearchBasketballTravelFatigueDigestReport(**values)


def test_public_dataclasses_are_final_frozen_and_decimal_only() -> None:
    digest = module()

    assert digest.__all__ == (
        "DEFAULT_MARKET_RESEARCH_BASKETBALL_TRAVEL_FATIGUE_DIGEST_CONFIG_VERSION",
        "BASKETBALL_TRAVEL_FATIGUE_RESEARCH_SCOPE",
        "MarketResearchBasketballTravelFatigueDigestConfig",
        "MarketResearchBasketballTravelFatigueDigestSignal",
        "MarketResearchBasketballTravelFatigueDigestReasonCodeCount",
        "MarketResearchBasketballTravelFatigueDigestRow",
        "MarketResearchBasketballTravelFatigueDigestReport",
        "build_market_research_basketball_travel_fatigue_digest",
        "market_research_basketball_travel_fatigue_digest_payload",
    )

    public_types = (
        digest.MarketResearchBasketballTravelFatigueDigestConfig,
        digest.MarketResearchBasketballTravelFatigueDigestSignal,
        digest.MarketResearchBasketballTravelFatigueDigestReasonCodeCount,
        digest.MarketResearchBasketballTravelFatigueDigestRow,
        digest.MarketResearchBasketballTravelFatigueDigestReport,
    )
    for public_type in public_types:
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen is True
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})

    config_subclass = _make_subclass_bypassing_final_guard(
        digest.MarketResearchBasketballTravelFatigueDigestConfig,
    )
    with pytest.raises(ValueError, match="config must be exactly"):
        config_subclass()

    report = build_report(signal())
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].digest_status = "watch"  # type: ignore[misc]

    records = (
        config(),
        signal(),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )
    for record in records:
        for field in fields(record):
            field_value = getattr(record, field.name)
            if field_value is not None and _is_public_numeric_field(field.name):
                assert type(field_value) is Decimal, field.name


def test_module_scope_has_no_io_float_or_execution_surfaces() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/"
        "market_research_basketball_travel_fatigue_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()

    for forbidden in (
        "live trading",
        "wallet",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
        "auth",
        "private",
        "secret",
        "token",
        "order",
        "open(",
        "requests",
        "http",
        "urlopen",
        "socket",
        "psycopg",
        "supabase",
        "sqlite",
        "subprocess",
        "connect(",
        "execute(",
        "float(",
        "exchange_mutation",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
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
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _make_subclass_bypassing_final_guard(public_type: type[object]) -> type[object]:
    sentinel = object()
    original_init_subclass = public_type.__dict__.get("__init_subclass__", sentinel)
    public_type.__init_subclass__ = classmethod(lambda cls, **kwargs: None)  # type: ignore[attr-defined]
    try:
        return type(f"{public_type.__name__}BypassedSubclass", (public_type,), {})
    finally:
        if original_init_subclass is sentinel:
            delattr(public_type, "__init_subclass__")
        else:
            public_type.__init_subclass__ = original_init_subclass  # type: ignore[attr-defined]


def _is_public_numeric_field(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_ratio")
        or field_name.endswith("_index")
        or field_name.endswith("_hours")
        or field_name.endswith("_miles")
        or field_name.endswith("_threshold")
    )


def _walk_payload_values(value: object):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_payload_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_payload_values(item)
    else:
        yield value
