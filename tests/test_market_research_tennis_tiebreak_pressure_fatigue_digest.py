from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import ModuleType
from typing import Any, get_args, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_tennis_tiebreak_pressure_fatigue_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "market-research-tennis-tiebreak-pressure-fatigue-digest-v0",
        "watch_pressure_fatigue_score": d("0.450000"),
        "blocked_pressure_fatigue_score": d("0.700000"),
        "max_source_age_seconds": d("1800.000000"),
        "stale_confidence_cap": d("0.300000"),
        "calm_confidence_cap": d("0.650000"),
        "high_recent_tiebreak_count": d("2.000000"),
        "high_tiebreak_point_count": d("40.000000"),
        "high_recent_minutes_played": d("180.000000"),
        "min_recovery_hours": d("36.000000"),
        "high_pressure_point_loss_rate": d("0.500000"),
        "high_first_serve_drop_rate": d("0.080000"),
    }
    values.update(overrides)
    return module.TennisTiebreakPressureFatigueDigestConfig(**values)


def observation(
    source_id: str = "source-alpha",
    *,
    match_id: str = "wimbledon-r3-alpha-beta",
    condition_id: str = "alpha-beta-tiebreak-pressure-fatigue",
    player_id: str = "player-alpha",
    opponent_id: str = "player-beta",
    tournament: str = "wimbledon",
    surface: str = "grass",
    recent_tiebreak_count: Decimal = d("2.000000"),
    tiebreak_point_count: Decimal = d("32.000000"),
    deciding_set_tiebreak_count: Decimal = d("0.000000"),
    pressure_point_loss_rate: Decimal = d("0.550000"),
    first_serve_drop_rate: Decimal = d("0.080000"),
    recovery_hours: Decimal = d("40.000000"),
    recent_minutes_played: Decimal = d("150.000000"),
    implied_probability_move: Decimal = d("0.000000"),
    observed_at: datetime = GENERATED_AT - timedelta(seconds=2400),
    base_confidence: Decimal = d("0.800000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.TennisTiebreakPressureFatigueObservation(
        source_id=source_id,
        match_id=match_id,
        condition_id=condition_id,
        player_id=player_id,
        opponent_id=opponent_id,
        tournament=tournament,
        surface=surface,
        recent_tiebreak_count=recent_tiebreak_count,
        tiebreak_point_count=tiebreak_point_count,
        deciding_set_tiebreak_count=deciding_set_tiebreak_count,
        pressure_point_loss_rate=pressure_point_loss_rate,
        first_serve_drop_rate=first_serve_drop_rate,
        recovery_hours=recovery_hours,
        recent_minutes_played=recent_minutes_played,
        implied_probability_move=implied_probability_move,
        observed_at=observed_at,
        base_confidence=base_confidence,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    inputs: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_market_research_tennis_tiebreak_pressure_fatigue_digest(
        inputs,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_high_risk_digest_scores_sorts_and_reasons_deterministically() -> None:
    report = digest(
        (
            observation(
                "beta-calm",
                match_id="roland-garros-qf-calm",
                condition_id="beta-calm-tiebreak-under",
                player_id="player-calm",
                opponent_id="player-steady",
                tournament="roland-garros",
                surface="clay",
                recent_tiebreak_count=d("0.000000"),
                tiebreak_point_count=d("8.000000"),
                pressure_point_loss_rate=d("0.250000"),
                first_serve_drop_rate=d("0.020000"),
                recovery_hours=d("50.000000"),
                recent_minutes_played=d("90.000000"),
                observed_at=GENERATED_AT - timedelta(seconds=60),
                base_confidence=d("0.720000"),
                upstream_reason_codes=("clay_hold_stable",),
            ),
            observation("alpha-watch"),
            observation(
                "zeta-blocked",
                match_id="wimbledon-r3-zeta-pressure",
                condition_id="zeta-pressure-tiebreak-over",
                player_id="player-zeta",
                opponent_id="player-gamma",
                recent_tiebreak_count=d("3.000000"),
                tiebreak_point_count=d("55.000000"),
                deciding_set_tiebreak_count=d("1.000000"),
                pressure_point_loss_rate=d("0.780000"),
                first_serve_drop_rate=d("0.140000"),
                recovery_hours=d("20.000000"),
                recent_minutes_played=d("220.000000"),
                implied_probability_move=d("0.070000"),
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    59,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                base_confidence=d("0.900000"),
                upstream_reason_codes=("medical_timeout_reported",),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-tennis-tiebreak-pressure-fatigue-digest-v0"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_pressure_fatigue_count == d("1.000000")
    assert report.watch_pressure_fatigue_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.pressure_fatigue_signal_count == d("2.000000")
    assert report.max_pressure_fatigue_score == d("0.829956")
    assert report.average_pressure_fatigue_score == d("0.503541")
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_tennis_tiebreak_pressure_fatigue_digest"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [
        (row.source_id, row.pressure_fatigue_status, row.pressure_fatigue_score)
        for row in report.rows
    ] == [
        ("zeta-blocked", "blocked", d("0.829956")),
        ("alpha-watch", "watch", d("0.531667")),
        ("beta-calm", "pass", d("0.149000")),
    ]

    blocked, watch, passed = report.rows
    assert blocked.observed_at == datetime(2026, 7, 4, 11, 59, tzinfo=UTC)
    assert blocked.source_age_seconds == d("60.000000")
    assert blocked.pressure_fatigue_direction == "tiebreak_pressure_fatigue"
    assert blocked.confidence_cap == d("1.000000")
    assert blocked.capped_confidence == d("0.900000")
    assert blocked.reason_codes == (
        "tiebreak_pressure_fatigue_blocked",
        "source_fresh",
        "recent_tiebreak_load_high",
        "tiebreak_point_load_high",
        "deciding_set_tiebreak_load",
        "pressure_point_loss_high",
        "first_serve_drop_high",
        "short_recovery_window",
        "recent_minutes_load_high",
        "market_probability_move_up",
        "medical_timeout_reported",
    )

    assert watch.pressure_fatigue_direction == "tiebreak_pressure_fatigue"
    assert watch.source_age_seconds == d("2400.000000")
    assert watch.confidence_cap == d("0.300000")
    assert watch.capped_confidence == d("0.300000")
    assert watch.reason_codes == (
        "tiebreak_pressure_fatigue_watch",
        "source_stale",
        "recent_tiebreak_load_high",
        "pressure_point_loss_high",
        "first_serve_drop_high",
    )

    assert passed.pressure_fatigue_direction == "tiebreak_pressure_resilient"
    assert passed.confidence_cap == d("0.650000")
    assert passed.capped_confidence == d("0.650000")
    assert passed.reason_codes == (
        "tiebreak_pressure_fatigue_calm",
        "source_fresh",
        "clay_hold_stable",
    )

    assert report.reason_codes == (
        "tiebreak_pressure_fatigue_blocked",
        "tiebreak_pressure_fatigue_watch",
        "tiebreak_pressure_fatigue_calm",
        "source_fresh",
        "source_stale",
        "recent_tiebreak_load_high",
        "tiebreak_point_load_high",
        "deciding_set_tiebreak_load",
        "pressure_point_loss_high",
        "first_serve_drop_high",
        "short_recovery_window",
        "recent_minutes_load_high",
        "market_probability_move_up",
        "clay_hold_stable",
        "medical_timeout_reported",
    )
    assert report.reason_code_counts[0].reason_code == "tiebreak_pressure_fatigue_blocked"
    assert report.reason_code_counts[0].count == d("1.000000")
    assert report.reason_code_counts[0].row_ratio == d("0.333333")
    source_fresh_count = next(
        item for item in report.reason_code_counts if item.reason_code == "source_fresh"
    )
    assert source_fresh_count.count == d("2.000000")
    assert source_fresh_count.row_ratio == d("0.666667")


def test_empty_input_returns_report_only_readonly_digest() -> None:
    module = api()
    report = digest(())

    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.blocked_pressure_fatigue_count == d("0.000000")
    assert report.watch_pressure_fatigue_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.max_pressure_fatigue_score == d("0.000000")
    assert report.average_pressure_fatigue_score == d("0.000000")
    assert report.digest_status == "empty"
    assert report.recommended_next_step == (
        "monitor_report_only_market_research_tennis_tiebreak_pressure_fatigue_digest"
    )
    assert report.reason_codes == ("tennis_tiebreak_pressure_fatigue_digest_empty",)
    assert report.reason_code_counts == (
        module.TennisTiebreakPressureFatigueReasonCodeCount(
            reason_code="tennis_tiebreak_pressure_fatigue_digest_empty",
            count=d("0.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_decimal_strings_frozen_dataclasses_and_no_public_floats() -> None:
    module = api()
    report = digest((observation("payload-row"),))
    payload = module.market_research_tennis_tiebreak_pressure_fatigue_digest_payload(
        report,
    )
    json.dumps(payload, allow_nan=False, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["row_count"] == "1.000000"
    assert payload["average_pressure_fatigue_score"] == "0.531667"
    assert payload["rows"][0]["pressure_fatigue_score"] == "0.531667"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_floats(payload)

    for value in _walk_dataclasses(report):
        assert value.__dataclass_params__.frozen is True
        for hint in get_type_hints(type(value)).values():
            assert not _type_uses_float_or_int(hint)
        for field in fields(value):
            if _is_public_numeric(field.name):
                field_value = getattr(value, field.name)
                assert field_value is None or type(field_value) is Decimal


def test_validation_rejects_bad_types_datetimes_future_rows_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="recent_tiebreak_count"):
        observation(recent_tiebreak_count=_DecimalSubclass("2.000000"))

    with pytest.raises(ValueError, match="pressure_point_loss_rate"):
        observation(pressure_point_loss_rate=d("1.100000"))

    with pytest.raises(ValueError, match="implied_probability_move"):
        observation(implied_probability_move=d("1.100000"))

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest((observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        digest((observation("dupe"), observation("dupe")))

    with pytest.raises(ValueError, match="config must be exactly"):
        module.build_market_research_tennis_tiebreak_pressure_fatigue_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="watch_pressure_fatigue_score"):
        config(
            watch_pressure_fatigue_score=d("0.800000"),
            blocked_pressure_fatigue_score=d("0.700000"),
        )

    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    report = digest((observation("frozen-row"),))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]


def test_non_default_thresholds_change_status_and_source_caps() -> None:
    cfg = config(
        watch_pressure_fatigue_score=d("0.300000"),
        blocked_pressure_fatigue_score=d("0.800000"),
        max_source_age_seconds=d("1200.000000"),
        stale_confidence_cap=d("0.250000"),
        calm_confidence_cap=d("0.550000"),
        min_recovery_hours=d("48.000000"),
    )
    report = digest(
        (
            observation(
                "threshold-row",
                recent_tiebreak_count=d("1.000000"),
                tiebreak_point_count=d("20.000000"),
                pressure_point_loss_rate=d("0.400000"),
                first_serve_drop_rate=d("0.040000"),
                recovery_hours=d("30.000000"),
                recent_minutes_played=d("60.000000"),
                observed_at=GENERATED_AT - timedelta(seconds=1300),
                base_confidence=d("0.820000"),
            ),
        ),
        cfg=cfg,
    )

    assert report.digest_status == "watch"
    assert report.max_pressure_fatigue_score == d("0.322667")
    assert report.watch_pressure_fatigue_count == d("1.000000")
    assert report.rows[0].pressure_fatigue_status == "watch"
    assert report.rows[0].confidence_cap == d("0.250000")
    assert report.rows[0].capped_confidence == d("0.250000")
    assert "short_recovery_window" in report.rows[0].reason_codes


def test_module_scope_is_pure_in_memory_report_only_surface() -> None:
    source = inspect.getsource(api()).lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "open(",
        "pathlib",
        "connect(",
        "cursor(",
        "execute(",
        "web3",
        "wallet",
        "private_key",
        "api_key",
        "secret",
        "live_trading",
        "submit_order",
        "place_order",
        "cancel_order",
        "replace_order",
    ):
        assert forbidden not in source

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "cursor",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail(f"public payload must not contain floats: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    elif isinstance(value, list | tuple):
        for item in value:
            assert_no_floats(item)


def _walk_dataclasses(value: object) -> tuple[object, ...]:
    found: list[object] = []
    if is_dataclass(value) and not isinstance(value, type):
        found.append(value)
        for field in fields(value):
            found.extend(_walk_dataclasses(getattr(value, field.name)))
    elif isinstance(value, tuple):
        for item in value:
            found.extend(_walk_dataclasses(item))
    return tuple(found)


def _is_public_numeric(field_name: str) -> bool:
    return (
        field_name.endswith("_cap")
        or field_name.endswith("_confidence")
        or field_name.endswith("_count")
        or field_name.endswith("_hours")
        or field_name.endswith("_minutes")
        or field_name.endswith("_move")
        or field_name.endswith("_rate")
        or field_name.endswith("_ratio")
        or field_name.endswith("_score")
        or field_name.endswith("_seconds")
    )


def _type_uses_float_or_int(hint: Any) -> bool:
    if hint in {float, int}:
        return True
    return any(_type_uses_float_or_int(arg) for arg in get_args(hint))
