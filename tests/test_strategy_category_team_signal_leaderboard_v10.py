from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_category_team_signal_leaderboard_v10.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_category_team_signal_leaderboard_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-category-team-signal-leaderboard-test-v0",
        "min_sample_size": d("50"),
        "min_recent_resolved_count": d("5"),
        "min_signal_quality_score": d("0.650000"),
        "watch_signal_quality_score": d("0.550000"),
        "minimum_top_team_margin": d("0.050000"),
    }
    values.update(overrides)
    return module.StrategyCategoryTeamSignalLeaderboardConfig(**values)


def signal(**overrides: object):
    module = api()
    values = {
        "category": "sports",
        "team_id": "macro_team",
        "hit_rate": d("0.620000"),
        "calibration_error": d("0.080000"),
        "source_quality_score": d("0.900000"),
        "freshness_score": d("0.850000"),
        "sample_size": d("120"),
        "recent_resolved_count": d("18"),
        "reason_codes": ("team_signal_input",),
    }
    values.update(overrides)
    return module.StrategyCategoryTeamSignalInput(**values)


def report(*, signals=(), cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_category_team_signal_leaderboard(
        signals,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_builds_category_leaderboard_and_rotation_recommendation() -> None:
    leaderboard = report(
        signals=(
            signal(
                category="sports",
                team_id="alpha_team",
                hit_rate=d("0.700000"),
                calibration_error=d("0.040000"),
                source_quality_score=d("0.900000"),
                freshness_score=d("0.800000"),
                sample_size=d("100"),
                recent_resolved_count=d("12"),
            ),
            signal(
                category="sports",
                team_id="beta_team",
                hit_rate=d("0.640000"),
                calibration_error=d("0.060000"),
                source_quality_score=d("0.850000"),
                freshness_score=d("0.780000"),
                sample_size=d("140"),
                recent_resolved_count=d("20"),
            ),
            signal(
                category="crypto",
                team_id="gamma_team",
                hit_rate=d("0.580000"),
                calibration_error=d("0.120000"),
                source_quality_score=d("0.600000"),
                freshness_score=d("0.500000"),
                sample_size=d("40"),
                recent_resolved_count=d("3"),
            ),
        ),
    )

    assert is_dataclass(leaderboard)
    assert leaderboard.generated_at == GENERATED_AT
    assert leaderboard.generated_at.tzinfo is UTC
    assert leaderboard.config_version == "strategy-category-team-signal-leaderboard-test-v0"
    assert leaderboard.team_count == d("3")
    assert leaderboard.category_count == d("2")
    assert leaderboard.eligible_team_count == d("2")
    assert leaderboard.top_team_id == "alpha_team"
    assert leaderboard.top_category == "sports"
    assert leaderboard.rotation_recommendation == "rotate_to_top_team"
    assert leaderboard.reason_codes == (
        "category_team_signal_leader_identified",
        "category_team_signal_rotation_recommended",
        "category_team_signal_quality_pass",
        "category_team_signal_quality_watch",
        "category_team_signal_insufficient_sample",
        "category_team_signal_insufficient_recent_resolution",
    )
    assert leaderboard.paper_only is True
    assert leaderboard.report_only is True
    assert leaderboard.readonly is True

    assert tuple(row.team_id for row in leaderboard.leaderboard_rows) == (
        "alpha_team",
        "beta_team",
        "gamma_team",
    )
    leader, runner_up, insufficient = leaderboard.leaderboard_rows

    assert leader.rank == d("1")
    assert leader.category == "sports"
    assert leader.signal_quality_score == d("0.741000")
    assert leader.eligibility_status == "eligible"
    assert leader.rotation_signal == "leader"
    assert leader.reason_codes == (
        "team_signal_input",
        "category_team_signal_rank_1",
        "category_team_signal_quality_pass",
        "category_team_signal_sample_sufficient",
        "category_team_signal_recent_resolution_sufficient",
    )

    assert runner_up.rank == d("2")
    assert runner_up.signal_quality_score == d("0.686500")
    assert runner_up.eligibility_status == "eligible"
    assert runner_up.rotation_signal == "runner_up"
    assert runner_up.reason_codes == (
        "team_signal_input",
        "category_team_signal_runner_up",
        "category_team_signal_quality_pass",
        "category_team_signal_sample_sufficient",
        "category_team_signal_recent_resolution_sufficient",
    )

    assert insufficient.rank == d("3")
    assert insufficient.signal_quality_score == d("0.559000")
    assert insufficient.eligibility_status == "insufficient_sample"
    assert insufficient.rotation_signal == "watch"
    assert insufficient.reason_codes == (
        "team_signal_input",
        "category_team_signal_watch",
        "category_team_signal_quality_watch",
        "category_team_signal_insufficient_sample",
        "category_team_signal_insufficient_recent_resolution",
    )


def test_empty_report_is_watch_with_decimal_fields_and_flags() -> None:
    empty = report()

    assert empty.team_count == ZERO
    assert empty.category_count == ZERO
    assert empty.eligible_team_count == ZERO
    assert empty.top_team_id is None
    assert empty.top_category is None
    assert empty.rotation_recommendation == "watch"
    assert empty.reason_codes == ("category_team_signal_leaderboard_empty",)
    assert empty.leaderboard_rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(signals=(signal(),))
    for value in (empty, populated, *populated.leaderboard_rows):
        for item in fields(value):
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "rank",
                "leaderboard_rows",
            }:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_score",
                    "_rate",
                    "_error",
                    "_size",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_uses_decimal_strings_and_utc_datetimes() -> None:
    module = api()
    leaderboard = report(
        signals=(signal(category="macro", team_id="rates_team"),),
        generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_category_team_signal_leaderboard_payload(leaderboard)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["team_count"] == "1"
    assert payload["eligible_team_count"] == "1"
    assert payload["top_team_id"] == "rates_team"
    assert payload["leaderboard_rows"][0]["sample_size"] == "120"
    assert payload["leaderboard_rows"][0]["signal_quality_score"] == "0.688500"
    assert_no_float_values(payload)

    payload["signed_order_payload"] = "forbidden"
    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.strategy_category_team_signal_leaderboard_payload(payload)


def test_validation_rejects_bad_types_duplicates_timestamps_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_category_team_signal_leaderboard(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="hit_rate must be a Decimal"):
        signal(hit_rate=1)

    with pytest.raises(ValueError, match="hit_rate must be finite"):
        signal(hit_rate=Decimal("NaN"))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(generated_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(generated_at=_DatetimeSubclass(2026, 7, 6, tzinfo=UTC))

    with pytest.raises(ValueError, match="freshness_score must be a Decimal"):
        signal(freshness_score=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="sample_size must be an integer Decimal"):
        signal(sample_size=d("10.500000"))

    with pytest.raises(ValueError, match="duplicate category/team_id"):
        report(
            signals=(
                signal(category="sports", team_id="alpha_team"),
                signal(category="sports", team_id="alpha_team"),
            ),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyCategoryTeamSignalLeaderboardConfig(paper_only=False)

    row = report(signals=(signal(),)).leaderboard_rows[0]
    with pytest.raises(FrozenInstanceError):
        row.rotation_signal = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(row, readonly=False)


def test_payload_requires_report_type_and_hard_flags() -> None:
    module = api()
    leaderboard = report(signals=(signal(),))

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_category_team_signal_leaderboard_payload(object())

    with pytest.raises(ValueError, match="report_only must be True"):
        module.strategy_category_team_signal_leaderboard_payload(
            replace(leaderboard, report_only=False),
        )


def test_module_scope_has_no_live_trading_persistence_network_or_sensitive_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.level == 0
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "env",
        "http",
        "network",
        "order",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "rollback",
        "send",
        "sign",
        "submit",
        "trade",
        "write",
    }

    assert imports
    assert all(
        fragment not in module_name.lower()
        for module_name in imports
        for fragment in forbidden_import_fragments
    )
    assert not (set(call_names) & forbidden_call_or_attribute_names)
    assert not (set(attribute_names) & forbidden_call_or_attribute_names)


def test_public_api_exports_leaderboard_contract() -> None:
    module = api()

    assert module.__all__ == (
        "StrategyCategoryTeamSignalInput",
        "StrategyCategoryTeamSignalLeaderboardConfig",
        "StrategyCategoryTeamSignalLeaderboardReport",
        "StrategyCategoryTeamSignalLeaderboardRow",
        "build_strategy_category_team_signal_leaderboard",
        "strategy_category_team_signal_leaderboard_payload",
    )
