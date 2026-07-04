from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any, get_args, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 4, 23, 30, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_research_baseball_catcher_framing_edge_digest.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_baseball_catcher_framing_edge_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "market-research-baseball-catcher-framing-edge-digest-v0",
        "max_update_age_seconds": d("900.000000"),
        "max_lineup_confirmation_age_seconds": d("1200.000000"),
        "elite_framing_runs": d("12.000000"),
        "watch_edge_score_threshold": d("0.400000"),
        "blocked_edge_score_threshold": d("0.750000"),
        "min_catcher_availability_score": d("0.600000"),
        "max_source_disagreement": d("0.250000"),
    }
    values.update(overrides)
    return module.BaseballCatcherFramingEdgeDigestConfig(**values)


def observation(
    source_id: str,
    *,
    team: str = "mets",
    opponent: str = "braves",
    market_slug: str = "mets-braves-total",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=5),
    catcher_framing_runs: object = "8.000000",
    umpire_called_strike_sensitivity: object = "0.900000",
    pitcher_zone_edge_rate: object = "0.900000",
    catcher_availability_score: object = "0.900000",
    lineup_confirmation_age_seconds: object = "600.000000",
    source_disagreement: object = "0.050000",
    reason_codes: tuple[str, ...] = (
        "baseball_catcher_framing_edge_input_reported",
    ),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.BaseballCatcherFramingEdgeObservation(
        source_id=source_id,
        team=team,
        opponent=opponent,
        market_slug=market_slug,
        observed_at=observed_at,
        catcher_framing_runs=(
            d(catcher_framing_runs)
            if type(catcher_framing_runs) is str
            else catcher_framing_runs
        ),
        umpire_called_strike_sensitivity=(
            d(umpire_called_strike_sensitivity)
            if type(umpire_called_strike_sensitivity) is str
            else umpire_called_strike_sensitivity
        ),
        pitcher_zone_edge_rate=(
            d(pitcher_zone_edge_rate)
            if type(pitcher_zone_edge_rate) is str
            else pitcher_zone_edge_rate
        ),
        catcher_availability_score=(
            d(catcher_availability_score)
            if type(catcher_availability_score) is str
            else catcher_availability_score
        ),
        lineup_confirmation_age_seconds=(
            d(lineup_confirmation_age_seconds)
            if type(lineup_confirmation_age_seconds) is str
            else lineup_confirmation_age_seconds
        ),
        source_disagreement=(
            d(source_disagreement)
            if type(source_disagreement) is str
            else source_disagreement
        ),
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    *rows: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_market_research_baseball_catcher_framing_edge_digest(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def test_catcher_framing_edge_digest_reduces_markets_deterministically() -> None:
    report = digest(
        observation(
            "source-pass",
            team="cubs",
            opponent="cardinals",
            market_slug="cubs-cardinals-player-strikeouts",
            catcher_framing_runs="3.000000",
            umpire_called_strike_sensitivity="0.700000",
            pitcher_zone_edge_rate="0.600000",
            catcher_availability_score="0.900000",
            reason_codes=(
                "baseball_catcher_framing_edge_input_reported",
                "baseball_catcher_framing_edge_pitcher_profile",
            ),
        ),
        observation(
            "source-blocked",
            team="mariners",
            opponent="rangers",
            market_slug="mariners-rangers-run-line",
            observed_at=datetime(2026, 7, 4, 18, 20, tzinfo=timezone(timedelta(hours=-5))),
            catcher_framing_runs="14.500000",
            umpire_called_strike_sensitivity="0.920000",
            pitcher_zone_edge_rate="0.870000",
            catcher_availability_score="0.970000",
            source_disagreement="0.260000",
            reason_codes=(
                "baseball_catcher_framing_edge_input_reported",
                "baseball_catcher_framing_edge_manual_chart",
            ),
        ),
        observation(
            "source-watch",
            team="mets",
            opponent="braves",
            market_slug="mets-braves-total",
            catcher_framing_runs="-8.000000",
            umpire_called_strike_sensitivity="0.900000",
            pitcher_zone_edge_rate="0.900000",
            catcher_availability_score="0.900000",
            reason_codes=(
                "baseball_catcher_framing_edge_input_reported",
                "baseball_catcher_framing_edge_lineup_confirmed",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.next_step == (
        "block_report_only_market_research_baseball_catcher_framing_edge_digest"
    )
    assert report.market_count == d("3.000000")
    assert report.source_count == d("3.000000")
    assert report.pass_market_count == d("1.000000")
    assert report.watch_market_count == d("1.000000")
    assert report.blocked_market_count == d("1.000000")
    assert report.stale_source_count == d("0.000000")
    assert report.lineup_stale_count == d("0.000000")
    assert report.disagreement_risk_count == d("1.000000")
    assert report.availability_risk_count == d("0.000000")
    assert report.max_edge_score == d("0.776388")
    assert report.risk_score == d("0.776388")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.market_slug for row in report.rows) == (
        "mariners-rangers-run-line",
        "mets-braves-total",
        "cubs-cardinals-player-strikeouts",
    )
    blocked, watch, passing = report.rows

    assert blocked.edge_status == "blocked"
    assert blocked.latest_observed_at == datetime(2026, 7, 4, 23, 20, tzinfo=UTC)
    assert blocked.source_age_seconds == d("600.000000")
    assert blocked.catcher_framing_runs == d("14.500000")
    assert blocked.edge_score == d("0.776388")
    assert blocked.risk_score == d("0.776388")
    assert blocked.reason_codes == (
        "baseball_catcher_framing_edge_blocked_threshold",
        "baseball_catcher_framing_edge_catcher_available",
        "baseball_catcher_framing_edge_input_reported",
        "baseball_catcher_framing_edge_lineup_fresh",
        "baseball_catcher_framing_edge_manual_chart",
        "baseball_catcher_framing_edge_source_disagreement_high",
        "baseball_catcher_framing_edge_source_fresh",
    )

    assert watch.edge_status == "watch"
    assert watch.catcher_framing_runs == d("-8.000000")
    assert watch.edge_score == d("0.486000")
    assert watch.reason_codes == (
        "baseball_catcher_framing_edge_catcher_available",
        "baseball_catcher_framing_edge_input_reported",
        "baseball_catcher_framing_edge_lineup_confirmed",
        "baseball_catcher_framing_edge_lineup_fresh",
        "baseball_catcher_framing_edge_source_fresh",
        "baseball_catcher_framing_edge_watch_threshold",
    )

    assert passing.edge_status == "pass"
    assert passing.edge_score == d("0.094500")
    assert passing.reason_codes == (
        "baseball_catcher_framing_edge_catcher_available",
        "baseball_catcher_framing_edge_input_reported",
        "baseball_catcher_framing_edge_pass_threshold",
        "baseball_catcher_framing_edge_pitcher_profile",
        "baseball_catcher_framing_edge_lineup_fresh",
        "baseball_catcher_framing_edge_source_fresh",
    )
    assert report.reason_codes == (
        "baseball_catcher_framing_edge_blocked_present",
        "baseball_catcher_framing_edge_watch_present",
        "baseball_catcher_framing_edge_pass_present",
        "baseball_catcher_framing_edge_source_disagreement_present",
    )


def test_empty_input_returns_pure_report_only_zero_digest_and_payload_strings() -> None:
    module = api()
    report = digest()
    payload = module.market_research_baseball_catcher_framing_edge_digest_payload(
        report,
    )
    json.dumps(payload, allow_nan=False, sort_keys=True)

    assert report.digest_status == "pass"
    assert report.reason_codes == (
        "baseball_catcher_framing_edge_digest_empty",
    )
    assert report.market_count == d("0.000000")
    assert report.source_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_code_counts == ()
    assert payload["generated_at"] == "2026-07-04T23:30:00+00:00"
    assert payload["market_count"] == "0.000000"
    assert payload["risk_score"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_or_int_paths(payload) == ()


def test_reason_code_counts_are_decimal_and_sorted_by_report_reason_order() -> None:
    module = api()
    report = digest(
        observation(
            "source-blocked",
            team="alpha",
            opponent="beta",
            market_slug="alpha-beta-run-line",
            catcher_framing_runs="14.000000",
            umpire_called_strike_sensitivity="0.920000",
            pitcher_zone_edge_rate="0.870000",
            catcher_availability_score="0.970000",
            source_disagreement="0.260000",
        ),
        observation(
            "source-watch",
            team="gamma",
            opponent="delta",
            market_slug="gamma-delta-total",
            catcher_framing_runs="8.000000",
            umpire_called_strike_sensitivity="0.900000",
            pitcher_zone_edge_rate="0.900000",
            catcher_availability_score="0.900000",
        ),
    )

    assert report.reason_code_counts == (
        module.BaseballCatcherFramingEdgeReasonCodeCount(
            reason_code="baseball_catcher_framing_edge_blocked_present",
            market_count=d("1.000000"),
            market_ratio=d("0.500000"),
        ),
        module.BaseballCatcherFramingEdgeReasonCodeCount(
            reason_code="baseball_catcher_framing_edge_watch_present",
            market_count=d("1.000000"),
            market_ratio=d("0.500000"),
        ),
        module.BaseballCatcherFramingEdgeReasonCodeCount(
            reason_code="baseball_catcher_framing_edge_source_disagreement_present",
            market_count=d("1.000000"),
            market_ratio=d("0.500000"),
        ),
    )

    for value in _walk_dataclasses(report):
        assert value.__dataclass_params__.frozen is True
        for hint in get_type_hints(type(value)).values():
            assert not _type_uses_float_or_int(hint)
        for field in fields(value):
            if _is_public_numeric(field.name):
                assert type(getattr(value, field.name)) is Decimal


def test_validates_decimals_utc_datetimes_flags_duplicates_and_frozen_instances() -> None:
    module = api()

    with pytest.raises(ValueError, match="pitcher_zone_edge_rate must be a Decimal"):
        module.BaseballCatcherFramingEdgeObservation(
            source_id="bad-decimal",
            team="mets",
            opponent="braves",
            market_slug="mets-braves-total",
            observed_at=GENERATED_AT,
            catcher_framing_runs=d("8.000000"),
            umpire_called_strike_sensitivity=d("0.900000"),
            pitcher_zone_edge_rate=1,  # type: ignore[arg-type]
            catcher_availability_score=d("0.900000"),
            lineup_confirmation_age_seconds=d("600.000000"),
            source_disagreement=d("0.050000"),
            reason_codes=("baseball_catcher_framing_edge_input_reported",),
        )

    with pytest.raises(ValueError, match="catcher_framing_runs must be a Decimal"):
        observation("bad-decimal-subclass", catcher_framing_runs=_DecimalSubclass("1.000000"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        observation("bad-naive-time", observed_at=datetime(2026, 7, 4, 23, 30))

    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        observation(
            "bad-time-subclass",
            observed_at=_DatetimeSubclass(2026, 7, 4, 23, 30, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest(observation("future-row", observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="duplicate source_id"):
        digest(observation("dupe"), observation("dupe", market_slug="other-market"))

    with pytest.raises(ValueError, match="config must be a BaseballCatcherFramingEdgeDigestConfig"):
        digest(cfg=object())

    with pytest.raises(ValueError, match="source_disagreement must be no greater than one"):
        observation("bad-ratio", source_disagreement=d("1.100000"))

    with pytest.raises(ValueError, match="paper_only"):
        observation("bad-flag", paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)

    row = observation("frozen")
    with pytest.raises(FrozenInstanceError):
        row.source_id = "changed"  # type: ignore[misc]


def test_static_module_scope_is_pure_report_only_and_readonly() -> None:
    module = api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "live_trading",
        "auth",
        "wallet",
        "broker",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange",
        "private_key",
        "api_key",
        "secret",
        "requests",
        "http",
        "httpx",
        "socket",
        "urlopen",
        "psycopg",
        "supabase",
        "subprocess",
        "open(",
        "pathlib",
        "environ",
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
        "connect",
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

    for name in module.__all__:
        value = getattr(module, name)
        if is_dataclass(value):
            assert value.__dataclass_params__.frozen is True


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
        field_name.endswith("_age_seconds")
        or field_name.endswith("_count")
        or field_name.endswith("_disagreement")
        or field_name.endswith("_rate")
        or field_name.endswith("_ratio")
        or field_name.endswith("_runs")
        or field_name.endswith("_score")
        or field_name.endswith("_threshold")
    )


def _type_uses_float_or_int(hint: Any) -> bool:
    if hint in {float, int}:
        return True
    return any(_type_uses_float_or_int(arg) for arg in get_args(hint))


def _float_or_int_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, bool):
        return ()
    if isinstance(value, (float, int)):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_or_int_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_or_int_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()
