from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 5, 16, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NullOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_tennis_timezone_fatigue_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    match_id: str = "match-alpha",
    market_slug: str = "player-alpha-vs-player-beta",
    player_id: str = "player-alpha",
    tournament_key: str = "wimbledon-2026",
    origin_location_key: str = "new-york",
    destination_location_key: str = "london",
    travel_distance_km: str | Decimal = "5570.000000",
    timezone_shift_hours: str | Decimal = "5.000000",
    hours_since_arrival: str | Decimal = "30.000000",
    days_since_arrival: str | Decimal = "1.000000",
    recent_match_minutes_7d: str | Decimal = "260.000000",
    observed_at: datetime = datetime(2026, 7, 5, 9, 0, tzinfo=timezone(timedelta(hours=1))),
    scheduled_start_at: datetime = datetime(2026, 7, 6, 13, 30, tzinfo=timezone(timedelta(hours=1))),
    upstream_reason_codes: tuple[str, ...] = ("official_travel_context",),
):
    module = digest()
    return module.MarketResearchTennisTimezoneFatigueObservation(
        source_id=source_id,
        match_id=match_id,
        market_slug=market_slug,
        player_id=player_id,
        tournament_key=tournament_key,
        origin_location_key=origin_location_key,
        destination_location_key=destination_location_key,
        travel_distance_km=(
            travel_distance_km if isinstance(travel_distance_km, Decimal) else d(travel_distance_km)
        ),
        timezone_shift_hours=(
            timezone_shift_hours
            if isinstance(timezone_shift_hours, Decimal)
            else d(timezone_shift_hours)
        ),
        hours_since_arrival=(
            hours_since_arrival if isinstance(hours_since_arrival, Decimal) else d(hours_since_arrival)
        ),
        days_since_arrival=(
            days_since_arrival if isinstance(days_since_arrival, Decimal) else d(days_since_arrival)
        ),
        recent_match_minutes_7d=(
            recent_match_minutes_7d
            if isinstance(recent_match_minutes_7d, Decimal)
            else d(recent_match_minutes_7d)
        ),
        observed_at=observed_at,
        scheduled_start_at=scheduled_start_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*observations: object, cfg: object | None = None):
    module = digest()
    if cfg is None:
        cfg = module.MarketResearchTennisTimezoneFatigueDigestConfig()
    return module.build_market_research_tennis_timezone_fatigue_digest(
        observations,
        config=cfg,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(
        digest_report,
        module.MarketResearchTennisTimezoneFatigueDigestReport,
    )
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-tennis-timezone-fatigue-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_tennis_timezone_fatigue_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.timezone_shift_count == d("0.000000")
    assert digest_report.short_recovery_count == d("0.000000")
    assert digest_report.circadian_recovery_gap_count == d("0.000000")
    assert digest_report.long_travel_count == d("0.000000")
    assert digest_report.late_arrival_count == d("0.000000")
    assert digest_report.recent_match_load_count == d("0.000000")
    assert digest_report.max_timezone_fatigue_score == d("0.000000")
    assert digest_report.average_timezone_fatigue_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "tennis_timezone_fatigue_digest_empty",
    )
    assert digest_report.reason_code_counts == (
        module.MarketResearchTennisTimezoneFatigueReasonCodeCount(
            reason_code="tennis_timezone_fatigue_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_compounded_travel_timezone_and_load_pressure_blocks_market_screening() -> None:
    digest_report = report(
        observation(
            "source-blocked",
            match_id="match-blocked",
            market_slug="jetlagged-favorite-vs-local-player",
            player_id="player-jetlagged",
            travel_distance_km="7800.000000",
            timezone_shift_hours="8.000000",
            hours_since_arrival="18.000000",
            days_since_arrival="1.000000",
            recent_match_minutes_7d="410.000000",
        ),
        observation(
            "source-watch",
            match_id="match-watch",
            market_slug="quick-turnaround-timezone",
            player_id="player-watch",
            travel_distance_km="1800.000000",
            timezone_shift_hours="5.000000",
            hours_since_arrival="30.000000",
            days_since_arrival="3.000000",
            recent_match_minutes_7d="120.000000",
            observed_at=datetime(2026, 7, 5, 10, 0, tzinfo=timezone(timedelta(hours=2))),
        ),
        observation(
            "source-pass",
            match_id="match-pass",
            market_slug="rested-same-zone-baseline",
            player_id="player-rested",
            origin_location_key="paris",
            destination_location_key="london",
            travel_distance_km="340.000000",
            timezone_shift_hours="1.000000",
            hours_since_arrival="72.000000",
            days_since_arrival="6.000000",
            recent_match_minutes_7d="90.000000",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_tennis_timezone_fatigue_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.timezone_shift_count == d("2.000000")
    assert digest_report.short_recovery_count == d("2.000000")
    assert digest_report.circadian_recovery_gap_count == d("2.000000")
    assert digest_report.long_travel_count == d("1.000000")
    assert digest_report.late_arrival_count == d("1.000000")
    assert digest_report.recent_match_load_count == d("1.000000")
    assert digest_report.max_timezone_fatigue_score == d("1.000000")
    assert digest_report.average_timezone_fatigue_score == d("0.500000")
    assert digest_report.reason_codes == (
        "tennis_timezone_fatigue_blocked_present",
        "tennis_timezone_fatigue_timezone_shift_present",
        "tennis_timezone_fatigue_short_recovery_present",
        "tennis_timezone_fatigue_circadian_gap_present",
        "tennis_timezone_fatigue_long_travel_present",
        "tennis_timezone_fatigue_late_arrival_present",
        "tennis_timezone_fatigue_recent_match_load_present",
    )
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "jetlagged-favorite-vs-local-player",
        "quick-turnaround-timezone",
        "rested-same-zone-baseline",
    )

    blocked, watched, passed = digest_report.rows
    assert blocked.fatigue_status == "blocked"
    assert blocked.timezone_fatigue_score == d("1.000000")
    assert blocked.circadian_recovery_hours_required == d("96.000000")
    assert blocked.circadian_recovery_gap_hours == d("78.000000")
    assert blocked.observed_at == datetime(2026, 7, 5, 8, 0, tzinfo=UTC)
    assert blocked.reason_codes == (
        "tennis_timezone_fatigue_large_timezone_shift",
        "tennis_timezone_fatigue_short_recovery_window",
        "tennis_timezone_fatigue_circadian_recovery_gap",
        "tennis_timezone_fatigue_long_travel",
        "tennis_timezone_fatigue_late_arrival",
        "tennis_timezone_fatigue_recent_match_load",
        "tennis_timezone_fatigue_blocked",
    )
    assert watched.fatigue_status == "watch"
    assert watched.timezone_fatigue_score == d("0.500000")
    assert watched.observed_at == datetime(2026, 7, 5, 8, 0, tzinfo=UTC)
    assert watched.reason_codes == (
        "tennis_timezone_fatigue_large_timezone_shift",
        "tennis_timezone_fatigue_short_recovery_window",
        "tennis_timezone_fatigue_circadian_recovery_gap",
        "tennis_timezone_fatigue_watch",
    )
    assert passed.fatigue_status == "pass"
    assert passed.timezone_fatigue_score == d("0.000000")
    assert passed.reason_codes == ("tennis_timezone_fatigue_clear",)

    assert tuple(item.count for item in digest_report.reason_code_counts) == (
        d("1.000000"),
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
    )


def test_rows_reason_codes_and_counts_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        match_id="match-watch-b",
        market_slug="zeta-watch",
        timezone_shift_hours="5.000000",
        hours_since_arrival="30.000000",
        travel_distance_km="1500.000000",
        recent_match_minutes_7d="100.000000",
    )
    second = observation(
        "source-blocked",
        match_id="match-blocked",
        market_slug="alpha-blocked",
        timezone_shift_hours="8.000000",
        hours_since_arrival="18.000000",
        travel_distance_km="7800.000000",
        days_since_arrival="1.000000",
        recent_match_minutes_7d="410.000000",
    )
    third = observation(
        "source-watch-a",
        match_id="match-watch-a",
        market_slug="alpha-watch",
        timezone_shift_hours="5.000000",
        hours_since_arrival="30.000000",
        travel_distance_km="1500.000000",
        recent_match_minutes_7d="100.000000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "alpha-blocked",
        "alpha-watch",
        "zeta-watch",
    )
    assert forward.reason_codes == tuple(
        sorted(
            forward.reason_codes,
            key=module_reason_rank(forward.reason_codes, digest().REPORT_REASON_CODES),
        ),
    )

    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(forward, rows=tuple(reversed(forward.rows)))
    with pytest.raises(ValueError, match="reason_codes must be in canonical order"):
        replace(forward.rows[0], reason_codes=tuple(reversed(forward.rows[0].reason_codes)))
    with pytest.raises(ValueError, match="reason_codes must be in canonical order"):
        replace(forward, reason_codes=tuple(reversed(forward.reason_codes)))
    with pytest.raises(ValueError, match="reason_code_counts must be sorted"):
        replace(forward, reason_code_counts=tuple(reversed(forward.reason_code_counts)))
    with pytest.raises(ValueError, match="upstream_reason_codes must be sorted"):
        observation(upstream_reason_codes=("zeta_reason", "alpha_reason"))


def test_non_default_thresholds_can_downgrade_moderate_timezone_fatigue() -> None:
    module = digest()
    cfg = module.MarketResearchTennisTimezoneFatigueDigestConfig(
        watch_fatigue_signal_count=d("4.000000"),
        blocked_fatigue_signal_count=d("6.000000"),
        min_recovery_hours=d("48.000000"),
        recovery_hours_per_timezone=d("4.000000"),
    )

    digest_report = report(
        observation(
            "source-moderate",
            timezone_shift_hours="5.000000",
            hours_since_arrival="30.000000",
            travel_distance_km="1500.000000",
            days_since_arrival="3.000000",
            recent_match_minutes_7d="100.000000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_tennis_timezone_fatigue_screening"
    )
    assert digest_report.rows[0].fatigue_status == "pass"
    assert digest_report.rows[0].reason_codes == (
        "tennis_timezone_fatigue_large_timezone_shift",
        "tennis_timezone_fatigue_short_recovery_window",
        "tennis_timezone_fatigue_clear",
    )
    assert digest_report.max_timezone_fatigue_score == d("0.333333")
    assert digest_report.reason_codes == (
        "tennis_timezone_fatigue_timezone_shift_present",
        "tennis_timezone_fatigue_short_recovery_present",
    )


def test_validation_rejects_bad_inputs_subclasses_and_inconsistent_records() -> None:
    module = digest()

    with pytest.raises(TypeError, match="does not support subclassing"):
        class BadObservation(module.MarketResearchTennisTimezoneFatigueObservation):
            pass

    with pytest.raises(ValueError, match="timezone_shift_hours must be a Decimal"):
        observation(timezone_shift_hours=_DecimalSubclass("5.000000"))
    with pytest.raises(ValueError, match="timezone_shift_hours must be nonnegative"):
        observation(timezone_shift_hours="-1.000000")
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 5, 9, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 5, 9, 0, tzinfo=_NullOffsetTz()))
    with pytest.raises(ValueError, match="scheduled_start_at must be a datetime"):
        observation(
            scheduled_start_at=_DateTimeSubclass(2026, 7, 6, 13, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_tennis_timezone_fatigue_digest(
            (),
            config=module.MarketResearchTennisTimezoneFatigueDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 5, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="watch_fatigue_signal_count"):
        module.MarketResearchTennisTimezoneFatigueDigestConfig(
            watch_fatigue_signal_count=d("5.000000"),
            blocked_fatigue_signal_count=d("4.000000"),
        )

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(ValueError, match="circadian_recovery_gap_hours must match"):
        replace(valid_row, circadian_recovery_gap_hours=d("999.000000"))
    with pytest.raises(ValueError, match="reason_codes must match fatigue_status"):
        replace(
            valid_row,
            reason_codes=(
                "tennis_timezone_fatigue_blocked",
                "tennis_timezone_fatigue_clear",
            ),
        )
    with pytest.raises(ValueError, match="count must be positive"):
        module.MarketResearchTennisTimezoneFatigueReasonCodeCount(
            reason_code="tennis_timezone_fatigue_digest_empty",
            count=d("0.000000"),
            row_ratio=d("0.000000"),
        )

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_observations_rows_counts_and_report() -> None:
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
        module.MarketResearchTennisTimezoneFatigueDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason code count paper_only must be True"):
        replace(digest_report.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)
    with pytest.raises(ValueError, match="config must be exactly"):
        report(cfg=False)


def test_payload_uses_six_decimal_strings_and_module_has_no_mutation_or_io_surfaces() -> None:
    module = digest()
    digest_report = report(observation("source-payload"))

    payload = module.market_research_tennis_timezone_fatigue_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["timezone_shift_hours"] == "5.000000"
    assert payload["rows"][0]["circadian_recovery_gap_hours"] == "30.000000"
    assert payload["rows"][0]["timezone_fatigue_score"] == "0.833333"
    assert payload["rows"][0]["observed_at"] == "2026-07-05T08:00:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "auth" not in lowered
                assert "secret" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.MarketResearchTennisTimezoneFatigueDigestConfig(),
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


def test_payload_revalidates_nested_public_dataclasses_before_serialization() -> None:
    module = digest()

    false_flag_report = report(observation("source-tampered-flag"))
    object.__setattr__(false_flag_report.rows[0], "report_only", False)
    with pytest.raises(ValueError, match="row report_only must be True"):
        module.market_research_tennis_timezone_fatigue_digest_payload(
            false_flag_report,
        )

    non_six_decimal_report = report(observation("source-tampered-decimal"))
    object.__setattr__(
        non_six_decimal_report.rows[0],
        "timezone_shift_hours",
        d("5.1"),
    )
    with pytest.raises(ValueError, match="timezone_shift_hours must be six-decimal"):
        module.market_research_tennis_timezone_fatigue_digest_payload(
            non_six_decimal_report,
        )

    inconsistent_row_report = report(observation("source-tampered-row"))
    object.__setattr__(
        inconsistent_row_report.rows[0],
        "fatigue_signal_count",
        d("4.000000"),
    )
    with pytest.raises(ValueError, match="fatigue_signal_count must match reason_codes"):
        module.market_research_tennis_timezone_fatigue_digest_payload(
            inconsistent_row_report,
        )

    non_six_count_report = report(observation("source-tampered-count"))
    object.__setattr__(non_six_count_report.reason_code_counts[0], "count", d("1"))
    with pytest.raises(ValueError, match="count must be six-decimal"):
        module.market_research_tennis_timezone_fatigue_digest_payload(
            non_six_count_report,
        )


def test_module_does_not_import_or_call_dataclasses_asdict_for_payloads() -> None:
    source = Path(
        "src/polymarket_alpha_lab/"
        "market_research_tennis_timezone_fatigue_digest.py",
    ).read_text()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "dataclasses":
            assert all(alias.name != "asdict" for alias in node.names)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id != "asdict"
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr != "asdict"

    source = Path(
        "src/polymarket_alpha_lab/"
        "market_research_tennis_timezone_fatigue_digest.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    forbidden_calls = {
        "open",
        "connect",
        "execute",
        "urlopen",
        "request",
        "get",
        "post",
        "put",
        "delete",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "sqlite",
        "pathlib",
        "os",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "wallet",
        "credential",
        "secret",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange mutation",
    ):
        assert forbidden not in source.lower()


def module_reason_rank(
    _row_reasons: tuple[str, ...],
    allowed: tuple[str, ...],
):
    return allowed.index


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
