from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any, get_args, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 4, 16, 0, tzinfo=timezone(timedelta(hours=-4)))
GENERATED_AT_UTC = datetime(2026, 7, 4, 20, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_research_tennis_seed_draw_path_pressure_digest.py"
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    try:
        return importlib.import_module(
            "polymarket_alpha_lab.market_research_tennis_seed_draw_path_pressure_digest",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"module missing: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": module.DEFAULT_TENNIS_SEED_DRAW_PATH_PRESSURE_DIGEST_CONFIG_VERSION,
        "watch_path_pressure_score": d("0.300000"),
        "blocked_path_pressure_score": d("0.500000"),
        "min_projected_match_count": d("3.000000"),
    }
    values.update(overrides)
    return module.TennisSeedDrawPathPressureDigestConfig(**values)


def input_row(
    source_id: str,
    *,
    tournament_id: str = "wimbledon-2026",
    draw_id: str = "main-draw",
    player_id: str = "player-alpha",
    seed_rank: str | Decimal = "4.000000",
    projected_match_count: str | Decimal = "4.000000",
    seeded_opponent_count: str | Decimal = "1.000000",
    top_eight_opponent_count: str | Decimal = "0.000000",
    short_rest_match_count: str | Decimal = "0.000000",
    observed_at: datetime = GENERATED_AT_UTC - timedelta(hours=1),
    reason_codes: tuple[str, ...] = (
        "tennis_seed_draw_path_pressure_input_observed",
    ),
) -> Any:
    module = api()
    return module.TennisSeedDrawPathPressureInput(
        source_id=source_id,
        tournament_id=tournament_id,
        draw_id=draw_id,
        player_id=player_id,
        seed_rank=seed_rank if isinstance(seed_rank, Decimal) else d(seed_rank),
        projected_match_count=(
            projected_match_count
            if isinstance(projected_match_count, Decimal)
            else d(projected_match_count)
        ),
        seeded_opponent_count=(
            seeded_opponent_count
            if isinstance(seeded_opponent_count, Decimal)
            else d(seeded_opponent_count)
        ),
        top_eight_opponent_count=(
            top_eight_opponent_count
            if isinstance(top_eight_opponent_count, Decimal)
            else d(top_eight_opponent_count)
        ),
        short_rest_match_count=(
            short_rest_match_count
            if isinstance(short_rest_match_count, Decimal)
            else d(short_rest_match_count)
        ),
        observed_at=observed_at,
        reason_codes=reason_codes,
    )


def digest_report(*rows: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_market_research_tennis_seed_draw_path_pressure_digest(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_path_pressure_digest_reduces_rows_deterministically() -> None:
    module = api()

    report = digest_report(
        input_row(
            "source-clear",
            player_id="player-clear",
            seed_rank="8.000000",
            projected_match_count="6.000000",
            seeded_opponent_count="0.000000",
            top_eight_opponent_count="0.000000",
            short_rest_match_count="0.000000",
        ),
        input_row(
            "source-watch",
            player_id="player-watch",
            seed_rank="4.000000",
            projected_match_count="3.000000",
            seeded_opponent_count="2.000000",
            top_eight_opponent_count="1.000000",
            short_rest_match_count="0.000000",
            observed_at=datetime(2026, 7, 4, 8, 30, tzinfo=timezone(timedelta(hours=-4))),
            reason_codes=(
                "tennis_seed_draw_path_pressure_input_observed",
                "tennis_seed_draw_path_pressure_seeded_opponent_cluster",
            ),
        ),
        input_row(
            "source-blocked",
            tournament_id="us-open-2026",
            player_id="player-blocked",
            seed_rank="2.000000",
            projected_match_count="4.000000",
            seeded_opponent_count="4.000000",
            top_eight_opponent_count="2.000000",
            short_rest_match_count="2.000000",
            reason_codes=(
                "tennis_seed_draw_path_pressure_input_observed",
                "tennis_seed_draw_path_pressure_seeded_opponent_cluster",
                "tennis_seed_draw_path_pressure_short_rest_path",
            ),
        ),
    )

    assert type(report) is module.TennisSeedDrawPathPressureDigest
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert report.generated_at == GENERATED_AT_UTC
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "market-research-tennis-seed-draw-path-pressure-digest-v0"
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_tennis_seed_draw_path_pressure_digest"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.source_count == d("3.000000")
    assert report.watch_row_count == d("1.000000")
    assert report.blocked_row_count == d("1.000000")
    assert report.total_projected_match_count == d("13.000000")
    assert report.total_seeded_opponent_count == d("6.000000")
    assert report.total_top_eight_opponent_count == d("3.000000")
    assert report.total_short_rest_match_count == d("2.000000")
    assert report.max_path_pressure_score == d("0.666667")
    assert report.weighted_path_pressure_score == d("0.282051")
    assert report.reason_codes == (
        "tennis_seed_draw_path_pressure_blocked_present",
        "tennis_seed_draw_path_pressure_watch_present",
        "tennis_seed_draw_path_pressure_seeded_cluster_present",
        "tennis_seed_draw_path_pressure_rest_cluster_present",
    )
    assert tuple(row.player_id for row in report.rows) == (
        "player-blocked",
        "player-watch",
        "player-clear",
    )

    blocked, watch, clear = report.rows
    assert type(blocked) is module.TennisSeedDrawPathPressureRow
    assert blocked.observed_at == GENERATED_AT_UTC - timedelta(hours=1)
    assert blocked.pressure_status == "blocked"
    assert blocked.seeded_opponent_ratio == d("1.000000")
    assert blocked.top_eight_opponent_ratio == d("0.500000")
    assert blocked.rest_pressure_ratio == d("0.500000")
    assert blocked.path_pressure_score == d("0.666667")
    assert blocked.reason_codes == (
        "tennis_seed_draw_path_pressure_seeded_cluster",
        "tennis_seed_draw_path_pressure_top_seed_cluster",
        "tennis_seed_draw_path_pressure_rest_cluster",
        "tennis_seed_draw_path_pressure_blocked",
    )
    assert watch.pressure_status == "watch"
    assert watch.observed_at == datetime(2026, 7, 4, 12, 30, tzinfo=UTC)
    assert watch.path_pressure_score == d("0.333333")
    assert clear.pressure_status == "clear"
    assert clear.reason_codes == ("tennis_seed_draw_path_pressure_clear",)


def test_empty_input_is_blocked_with_positive_reason_count() -> None:
    module = api()

    report = digest_report()

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_tennis_seed_draw_path_pressure_digest"
    )
    assert report.reason_codes == ("tennis_seed_draw_path_pressure_digest_empty",)
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.source_count == d("0.000000")
    assert report.max_path_pressure_score == d("0.000000")
    assert report.weighted_path_pressure_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_code_counts == (
        module.TennisSeedDrawPathPressureReasonCodeCount(
            reason_code="tennis_seed_draw_path_pressure_digest_empty",
            row_count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_reason_counts_payload_and_public_numerics_are_strict() -> None:
    module = api()
    report = digest_report(
        input_row(
            "source-blocked",
            player_id="player-blocked",
            projected_match_count="4.000000",
            seeded_opponent_count="4.000000",
            top_eight_opponent_count="2.000000",
            short_rest_match_count="2.000000",
        ),
        input_row(
            "source-watch",
            player_id="player-watch",
            projected_match_count="3.000000",
            seeded_opponent_count="2.000000",
            top_eight_opponent_count="1.000000",
        ),
    )

    assert report.reason_code_counts == (
        module.TennisSeedDrawPathPressureReasonCodeCount(
            reason_code="tennis_seed_draw_path_pressure_blocked_present",
            row_count=d("1.000000"),
            row_ratio=d("0.500000"),
        ),
        module.TennisSeedDrawPathPressureReasonCodeCount(
            reason_code="tennis_seed_draw_path_pressure_watch_present",
            row_count=d("1.000000"),
            row_ratio=d("0.500000"),
        ),
        module.TennisSeedDrawPathPressureReasonCodeCount(
            reason_code="tennis_seed_draw_path_pressure_seeded_cluster_present",
            row_count=d("2.000000"),
            row_ratio=d("1.000000"),
        ),
        module.TennisSeedDrawPathPressureReasonCodeCount(
            reason_code="tennis_seed_draw_path_pressure_rest_cluster_present",
            row_count=d("1.000000"),
            row_ratio=d("0.500000"),
        ),
    )

    payload = module.market_research_tennis_seed_draw_path_pressure_digest_payload(report)
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["generated_at"] == "2026-07-04T20:00:00+00:00"
    assert payload["input_count"] == "2.000000"
    assert payload["rows"][0]["path_pressure_score"] == "0.666667"
    assert payload["reason_code_counts"][0]["row_ratio"] == "0.500000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_paths(payload) == ()
    _assert_no_raw_decimal_or_datetime(payload)

    for public_record in _walk_dataclasses(report):
        assert public_record.__dataclass_params__.frozen is True
        for hint in get_type_hints(type(public_record)).values():
            assert not _type_uses_float(hint)
        for field in fields(public_record):
            if _is_public_numeric(field.name):
                assert type(getattr(public_record, field.name)) is Decimal


def test_rejects_lists_subclasses_noncanonical_numerics_and_bad_ordering() -> None:
    module = api()

    with pytest.raises(ValueError, match="inputs must be a tuple"):
        module.build_market_research_tennis_seed_draw_path_pressure_digest(
            [input_row("source-list")],
            config=config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        module.TennisSeedDrawPathPressureInput(
            source_id="source-reason-list",
            tournament_id="wimbledon-2026",
            draw_id="main-draw",
            player_id="player-list",
            seed_rank=d("4.000000"),
            projected_match_count=d("4.000000"),
            seeded_opponent_count=d("1.000000"),
            top_eight_opponent_count=d("0.000000"),
            short_rest_match_count=d("0.000000"),
            observed_at=GENERATED_AT_UTC,
            reason_codes=["tennis_seed_draw_path_pressure_input_observed"],
        )

    for public_dataclass in (
        module.TennisSeedDrawPathPressureDigestConfig,
        module.TennisSeedDrawPathPressureInput,
        module.TennisSeedDrawPathPressureReasonCodeCount,
        module.TennisSeedDrawPathPressureRow,
        module.TennisSeedDrawPathPressureDigest,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"{public_dataclass.__name__}Child", (public_dataclass,), {})

    with pytest.raises(ValueError, match="seed_rank must use six decimal places"):
        input_row("source-noncanonical-seed", seed_rank=d("4"))

    with pytest.raises(ValueError, match="seed_rank must be a Decimal"):
        input_row("source-decimal-subclass", seed_rank=_DecimalSubclass("4.000000"))

    with pytest.raises(ValueError, match="watch_path_pressure_score must use six decimal"):
        config(watch_path_pressure_score=d("0.3"))

    with pytest.raises(ValueError, match="row_count must be positive"):
        module.TennisSeedDrawPathPressureReasonCodeCount(
            reason_code="tennis_seed_draw_path_pressure_watch_present",
            row_count=d("0.000000"),
            row_ratio=d("0.000000"),
        )
    with pytest.raises(ValueError, match="row_count must be a whole Decimal"):
        module.TennisSeedDrawPathPressureReasonCodeCount(
            reason_code="tennis_seed_draw_path_pressure_watch_present",
            row_count=d("0.500000"),
            row_ratio=d("0.500000"),
        )

    row = input_row("source-frozen")
    with pytest.raises(FrozenInstanceError):
        row.source_id = "changed"  # type: ignore[misc]

    report = digest_report(
        input_row("source-alpha", player_id="player-alpha"),
        input_row(
            "source-beta",
            player_id="player-beta",
            projected_match_count="4.000000",
            seeded_opponent_count="4.000000",
            top_eight_opponent_count="2.000000",
            short_rest_match_count="2.000000",
        ),
    )
    assert tuple(row.player_id for row in report.rows) == ("player-beta", "player-alpha")
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(report, rows=tuple(reversed(report.rows)))

    with pytest.raises(ValueError, match="reason_code_counts must match"):
        replace(
            report,
            reason_code_counts=(
                module.TennisSeedDrawPathPressureReasonCodeCount(
                    reason_code="tennis_seed_draw_path_pressure_blocked_present",
                    row_count=d("1.000000"),
                    row_ratio=d("1.000000"),
                ),
            ),
        )


def test_timestamps_normalize_to_utc_and_future_rows_are_rejected() -> None:
    module = api()

    row = input_row(
        "source-timezone",
        observed_at=datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    assert row.observed_at == datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
    assert row.observed_at.tzinfo is UTC

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        input_row("source-naive-time", observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="observed_at must have a UTC offset"):
        input_row(
            "source-none-offset",
            observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        input_row(
            "source-datetime-subclass",
            observed_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        module.build_market_research_tennis_seed_draw_path_pressure_digest(
            (
                input_row(
                    "source-future",
                    observed_at=GENERATED_AT_UTC + timedelta(seconds=1),
                ),
            ),
            config=config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_tennis_seed_draw_path_pressure_digest(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 20, 0, tzinfo=UTC),
        )


def test_payload_recursively_revalidates_tampered_nested_dataclasses() -> None:
    module = api()
    report = digest_report(input_row("source-payload"))

    object.__setattr__(report.rows[0], "path_pressure_score", d("0.5"))
    with pytest.raises(ValueError, match="six decimal"):
        module.market_research_tennis_seed_draw_path_pressure_digest_payload(report)

    report = digest_report(input_row("source-nested-flag"))
    object.__setattr__(report.rows[0], "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        module.market_research_tennis_seed_draw_path_pressure_digest_payload(report)

    report = digest_report(input_row("source-count"))
    object.__setattr__(report.reason_code_counts[0], "row_count", d("0.000000"))
    with pytest.raises(ValueError, match="row_count must be positive"):
        module.market_research_tennis_seed_draw_path_pressure_digest_payload(report)

    report = digest_report(input_row("source-fractional-count"))
    object.__setattr__(report.reason_code_counts[0], "row_count", d("0.500000"))
    with pytest.raises(ValueError, match="row_count must be a whole Decimal"):
        module.market_research_tennis_seed_draw_path_pressure_digest_payload(report)

    report = digest_report(input_row("source-nonutc-payload"))
    object.__setattr__(
        report.rows[0],
        "observed_at",
        datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="observed_at must be UTC"):
        module.market_research_tennis_seed_draw_path_pressure_digest_payload(report)

    report = digest_report(input_row("source-list-payload"))
    object.__setattr__(report, "rows", list(report.rows))
    with pytest.raises(ValueError, match="rows must be a tuple"):
        module.market_research_tennis_seed_draw_path_pressure_digest_payload(report)


def test_static_module_scope_stays_pure_report_only() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "shelve",
        "pickle",
        "open(",
        "pathlib",
        "auth",
        "wallet",
        "account",
        "private_key",
        "api_key",
        "secret",
        "market_slug",
        "question",
        "payload_json",
        "asdict",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange_mutation",
        "trade",
        "client",
        "subprocess",
    ):
        assert forbidden not in lowered

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
        "asdict",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "__import__",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


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
    return field_name.endswith(("_count", "_ratio", "_rank", "_score"))


def _type_uses_float(hint: Any) -> bool:
    if hint is float:
        return True
    return any(_type_uses_float(arg) for arg in get_args(hint))


def _float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _assert_no_raw_decimal_or_datetime(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_raw_decimal_or_datetime(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_raw_decimal_or_datetime(item)
    else:
        assert not isinstance(value, (Decimal, datetime))
