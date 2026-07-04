from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import ModuleType
from typing import Any, get_args, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 4, 15, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_tennis_medical_timeout_momentum_shift_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            "market-research-tennis-medical-timeout-momentum-shift-digest-v0"
        ),
        "watch_momentum_shift_score": d("0.450000"),
        "blocked_momentum_shift_score": d("0.700000"),
        "max_observation_age_seconds": d("1800.000000"),
        "stale_confidence_cap": d("0.350000"),
        "stable_confidence_cap": d("0.650000"),
        "serve_speed_drop_kph_threshold": d("3.000000"),
        "movement_decline_threshold": d("0.080000"),
    }
    values.update(overrides)
    return module.TennisMedicalTimeoutMomentumShiftDigestConfig(**values)


def observation(
    source_id: str = "source-alpha",
    *,
    event_id: str = "wimbledon-r3-alpha-beta",
    market_slug: str = "alpha-beta-match-probability",
    market_type: str = "match_probability",
    player_id: str = "player-alpha",
    opponent_id: str = "player-beta",
    tournament: str = "wimbledon",
    set_id: str = "match",
    medical_timeout_count: Decimal = d("1.000000"),
    trainer_visit_count: Decimal = d("1.000000"),
    serve_speed_drop_kph: Decimal = d("5.000000"),
    movement_score_change: Decimal = d("-0.100000"),
    momentum_pressure_score: Decimal = d("0.400000"),
    implied_probability_move: Decimal = d("0.030000"),
    observed_at: datetime = GENERATED_AT - timedelta(seconds=2400),
    base_confidence: Decimal = d("0.800000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.TennisMedicalTimeoutMomentumShiftObservation(
        source_id=source_id,
        event_id=event_id,
        market_slug=market_slug,
        market_type=market_type,
        player_id=player_id,
        opponent_id=opponent_id,
        tournament=tournament,
        set_id=set_id,
        medical_timeout_count=medical_timeout_count,
        trainer_visit_count=trainer_visit_count,
        serve_speed_drop_kph=serve_speed_drop_kph,
        movement_score_change=movement_score_change,
        momentum_pressure_score=momentum_pressure_score,
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
    return module.build_market_research_tennis_medical_timeout_momentum_shift_digest(
        inputs,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_medical_timeout_momentum_digest_scores_sorts_and_reasons_deterministically() -> None:
    report = digest(
        (
            observation(
                "beta-calm",
                event_id="roland-garros-r1-calm",
                market_slug="beta-calm-set-probability",
                market_type="set_probability",
                player_id="player-calm",
                opponent_id="player-steady",
                tournament="roland-garros",
                set_id="set-2",
                medical_timeout_count=d("0.000000"),
                trainer_visit_count=d("0.000000"),
                serve_speed_drop_kph=d("1.000000"),
                movement_score_change=d("0.050000"),
                momentum_pressure_score=d("0.100000"),
                implied_probability_move=d("-0.010000"),
                observed_at=GENERATED_AT - timedelta(seconds=60),
                base_confidence=d("0.720000"),
                upstream_reason_codes=("baseline-hold-pattern",),
            ),
            observation(
                "alpha-watch",
                observed_at=GENERATED_AT - timedelta(seconds=2400),
            ),
            observation(
                "zeta-blocked",
                event_id="wimbledon-r3-zeta-timeout",
                market_slug="zeta-timeout-match-probability",
                player_id="player-zeta",
                opponent_id="player-gamma",
                medical_timeout_count=d("1.000000"),
                trainer_visit_count=d("2.000000"),
                serve_speed_drop_kph=d("12.000000"),
                movement_score_change=d("-0.250000"),
                momentum_pressure_score=d("0.800000"),
                implied_probability_move=d("0.070000"),
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    10,
                    59,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                base_confidence=d("0.900000"),
                upstream_reason_codes=("knee-treatment-confirmed",),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-tennis-medical-timeout-momentum-shift-digest-v0"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_shift_count == d("1.000000")
    assert report.watch_shift_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.medical_timeout_signal_count == d("2.000000")
    assert report.trainer_visit_signal_count == d("2.000000")
    assert report.serve_speed_drop_signal_count == d("2.000000")
    assert report.movement_decline_signal_count == d("2.000000")
    assert report.max_momentum_shift_score == d("0.896667")
    assert report.average_momentum_shift_score == d("0.497778")
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_tennis_medical_timeout_momentum_shift_digest"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [
        (row.source_id, row.shift_status, row.momentum_shift_score)
        for row in report.rows
    ] == [
        ("zeta-blocked", "blocked", d("0.896667")),
        ("alpha-watch", "watch", d("0.568333")),
        ("beta-calm", "pass", d("0.028333")),
    ]

    blocked, watch, passed = report.rows
    assert blocked.observed_at == datetime(2026, 7, 4, 14, 59, tzinfo=UTC)
    assert blocked.source_age_seconds == d("60.000000")
    assert blocked.shift_direction == "medical_timeout_momentum_shift"
    assert blocked.confidence_cap == d("1.000000")
    assert blocked.capped_confidence == d("0.900000")
    assert blocked.reason_codes == (
        "medical_timeout_momentum_shift_blocked",
        "source_fresh",
        "medical_timeout_reported",
        "trainer_visit_cluster",
        "serve_speed_drop_detected",
        "movement_score_decline",
        "market_momentum_pressure_high",
        "market_probability_move_up",
        "knee-treatment-confirmed",
    )

    assert watch.shift_direction == "medical_timeout_momentum_shift"
    assert watch.source_age_seconds == d("2400.000000")
    assert watch.confidence_cap == d("0.350000")
    assert watch.capped_confidence == d("0.350000")
    assert watch.reason_codes == (
        "medical_timeout_momentum_shift_watch",
        "source_stale",
        "medical_timeout_reported",
        "trainer_visit_reported",
        "serve_speed_drop_detected",
        "movement_score_decline",
        "market_momentum_pressure_high",
    )

    assert passed.shift_direction == "medical_timeout_stable"
    assert passed.confidence_cap == d("0.650000")
    assert passed.capped_confidence == d("0.650000")
    assert passed.reason_codes == (
        "medical_timeout_momentum_shift_calm",
        "source_fresh",
        "baseline-hold-pattern",
    )

    assert report.reason_codes == (
        "medical_timeout_momentum_shift_blocked",
        "medical_timeout_momentum_shift_watch",
        "medical_timeout_momentum_shift_calm",
        "source_fresh",
        "source_stale",
        "medical_timeout_reported",
        "trainer_visit_cluster",
        "trainer_visit_reported",
        "serve_speed_drop_detected",
        "movement_score_decline",
        "market_momentum_pressure_high",
        "market_probability_move_up",
        "baseline-hold-pattern",
        "knee-treatment-confirmed",
    )
    assert report.reason_code_counts[0].reason_code == (
        "medical_timeout_momentum_shift_blocked"
    )
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
    assert report.blocked_shift_count == d("0.000000")
    assert report.watch_shift_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.max_momentum_shift_score == d("0.000000")
    assert report.average_momentum_shift_score == d("0.000000")
    assert report.digest_status == "empty"
    assert report.recommended_next_step == (
        "monitor_report_only_market_research_tennis_medical_timeout_momentum_shift_digest"
    )
    assert report.reason_codes == (
        "tennis_medical_timeout_momentum_shift_digest_empty",
    )
    assert report.reason_code_counts == (
        module.TennisMedicalTimeoutMomentumShiftReasonCodeCount(
            reason_code="tennis_medical_timeout_momentum_shift_digest_empty",
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
    payload = module.market_research_tennis_medical_timeout_momentum_shift_digest_payload(
        report,
    )
    json.dumps(payload, allow_nan=False, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T15:00:00+00:00"
    assert payload["row_count"] == "1.000000"
    assert payload["average_momentum_shift_score"] == "0.568333"
    assert payload["rows"][0]["momentum_shift_score"] == "0.568333"
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

    with pytest.raises(ValueError, match="medical_timeout_count"):
        observation(medical_timeout_count=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="momentum_pressure_score"):
        observation(momentum_pressure_score=d("1.100000"))

    with pytest.raises(ValueError, match="movement_score_change"):
        observation(movement_score_change=d("-1.100000"))

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(observed_at=datetime(2026, 7, 4, 15, 0))

    with pytest.raises(ValueError, match="datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest((observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        digest((observation("dupe"), observation("dupe")))

    with pytest.raises(ValueError, match="config must be exactly"):
        module.build_market_research_tennis_medical_timeout_momentum_shift_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="watch_momentum_shift_score"):
        config(
            watch_momentum_shift_score=d("0.800000"),
            blocked_momentum_shift_score=d("0.700000"),
        )

    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    report = digest((observation("frozen-row"),))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]
    with pytest.raises(ValueError, match="report"):
        module.market_research_tennis_medical_timeout_momentum_shift_digest_payload(
            object(),
        )
    with pytest.raises(ValueError, match="shift_status"):
        replace(report.rows[0], shift_status="blocked")


def test_non_default_thresholds_change_status_and_confidence_caps() -> None:
    cfg = config(
        watch_momentum_shift_score=d("0.300000"),
        blocked_momentum_shift_score=d("0.800000"),
        max_observation_age_seconds=d("1200.000000"),
        stale_confidence_cap=d("0.250000"),
        stable_confidence_cap=d("0.550000"),
        serve_speed_drop_kph_threshold=d("4.000000"),
        movement_decline_threshold=d("0.120000"),
    )
    report = digest(
        (
            observation(
                "threshold-row",
                medical_timeout_count=d("0.000000"),
                trainer_visit_count=d("1.000000"),
                serve_speed_drop_kph=d("5.000000"),
                movement_score_change=d("-0.120000"),
                momentum_pressure_score=d("0.550000"),
                observed_at=GENERATED_AT - timedelta(seconds=1300),
                base_confidence=d("0.820000"),
            ),
        ),
        cfg=cfg,
    )

    assert report.digest_status == "watch"
    assert report.max_momentum_shift_score == d("0.304167")
    assert report.watch_shift_count == d("1.000000")
    assert report.rows[0].shift_status == "watch"
    assert report.rows[0].confidence_cap == d("0.250000")
    assert report.rows[0].capped_confidence == d("0.250000")
    assert "serve_speed_drop_detected" in report.rows[0].reason_codes
    assert "movement_score_decline" in report.rows[0].reason_codes


def test_module_scope_is_pure_in_memory_report_only_surface() -> None:
    source = inspect.getsource(api()).lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "cursor(",
        "execute(",
        "web3",
        "wallet",
        "private_key",
        "api_key",
        "secret",
        "auth",
        "live_trading",
        "submit_order",
        "place_order",
        "cancel_order",
        "replace_order",
        "exchange",
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
        field_name.endswith("_count")
        or field_name.endswith("_rate")
        or field_name.endswith("_score")
        or field_name.endswith("_ratio")
        or field_name.endswith("_seconds")
        or field_name.endswith("_cap")
        or field_name.endswith("_confidence")
        or field_name.endswith("_move")
        or field_name.endswith("_kph")
        or field_name.endswith("_change")
    )


def _type_uses_float_or_int(hint: Any) -> bool:
    if hint in {float, int}:
        return True
    return any(_type_uses_float_or_int(arg) for arg in get_args(hint))
