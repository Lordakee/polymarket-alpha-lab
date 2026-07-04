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
    / "strategy_category_cost_drag_rotation_digest.py"
)
GENERATED_AT = datetime(2026, 7, 3, 15, 30, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 3, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_category_cost_drag_rotation_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(**overrides: object):
    module = api()
    values = {
        "category_id": "crypto",
        "observed_at": OBSERVED_AT,
        "recommended_notional": d("100.000000"),
        "realized_cost_drag": d("0.020000"),
        "baseline_cost_drag": d("0.010000"),
        "reason_codes": ("strategy_cost_drag_observed",),
    }
    values.update(overrides)
    return module.StrategyCategoryCostDragRotationObservation(**values)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-category-cost-drag-rotation-digest-v0",
        "max_cost_drag_ratio": d("0.050000"),
        "min_rotation_notional_share_delta": d("0.100000"),
    }
    values.update(overrides)
    return module.StrategyCategoryCostDragRotationDigestConfig(**values)


def report(*, observations=(), cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_category_cost_drag_rotation_digest(
        observations,
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


def test_digest_summarizes_category_rotation_cost_drag_and_reason_codes() -> None:
    result = report(
        observations=(
            observation(
                category_id="macro",
                observed_at=OBSERVED_AT - timedelta(minutes=20),
                recommended_notional=d("80.000000"),
                realized_cost_drag=d("0.020000"),
                baseline_cost_drag=d("0.010000"),
            ),
            observation(
                category_id="macro",
                observed_at=OBSERVED_AT,
                recommended_notional=d("120.000000"),
                realized_cost_drag=d("0.070000"),
                baseline_cost_drag=d("0.020000"),
                reason_codes=("manual_cost_review",),
            ),
            observation(
                category_id="crypto",
                observed_at=OBSERVED_AT - timedelta(minutes=10),
                recommended_notional=d("120.000000"),
                realized_cost_drag=d("0.020000"),
                baseline_cost_drag=d("0.010000"),
            ),
            observation(
                category_id="crypto",
                observed_at=OBSERVED_AT,
                recommended_notional=d("60.000000"),
                realized_cost_drag=d("0.030000"),
                baseline_cost_drag=d("0.010000"),
            ),
            observation(
                category_id="sports",
                observed_at=OBSERVED_AT,
                recommended_notional=d("20.000000"),
                realized_cost_drag=d("0.010000"),
                baseline_cost_drag=d("0.010000"),
            ),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-category-cost-drag-rotation-digest-v0"
    assert result.observation_count == d("5")
    assert result.category_count == d("3")
    assert result.rotation_in_count == d("1")
    assert result.rotation_out_count == d("1")
    assert result.stable_count == d("1")
    assert result.high_cost_drag_count == d("1")
    assert result.max_cost_drag_ratio == d("0.070000")
    assert result.max_cost_drag_excess_ratio == d("0.020000")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "category_cost_drag_high",
        "category_rotation_detected",
        "manual_cost_review",
        "strategy_cost_drag_observed",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.category_id for row in result.category_rows) == (
        "macro",
        "crypto",
        "sports",
    )
    assert tuple(row.rotation_status for row in result.category_rows) == (
        "rotating_in",
        "rotating_out",
        "stable",
    )
    macro, crypto, sports = result.category_rows

    assert macro.starting_notional_share_ratio == d("0.400000")
    assert macro.ending_notional_share_ratio == d("0.600000")
    assert macro.notional_share_delta_ratio == d("0.200000")
    assert macro.cost_drag_ratio == d("0.070000")
    assert macro.cost_drag_excess_ratio == d("0.020000")
    assert macro.reason_codes == (
        "category_cost_drag_high",
        "category_rotating_in",
        "manual_cost_review",
        "strategy_cost_drag_observed",
    )

    assert crypto.starting_notional_share_ratio == d("0.600000")
    assert crypto.ending_notional_share_ratio == d("0.300000")
    assert crypto.notional_share_delta_ratio == d("-0.300000")
    assert crypto.cost_drag_ratio == d("0.030000")
    assert crypto.cost_drag_excess_ratio == ZERO
    assert crypto.reason_codes == (
        "category_rotating_out",
        "strategy_cost_drag_observed",
    )

    assert sports.starting_notional_share_ratio == ZERO
    assert sports.ending_notional_share_ratio == d("0.100000")
    assert sports.notional_share_delta_ratio == d("0.100000")
    assert sports.rotation_status == "stable"
    assert sports.reason_codes == (
        "category_rotation_stable",
        "strategy_cost_drag_observed",
    )


def test_empty_digest_is_watch_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.observation_count == d("0")
    assert empty.category_count == d("0")
    assert empty.rotation_in_count == d("0")
    assert empty.rotation_out_count == d("0")
    assert empty.stable_count == d("0")
    assert empty.high_cost_drag_count == d("0")
    assert empty.max_cost_drag_ratio == ZERO
    assert empty.max_cost_drag_excess_ratio == ZERO
    assert empty.status == "watch"
    assert empty.reason_codes == ("strategy_category_cost_drag_rotation_empty",)
    assert empty.category_rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(observations=(observation(),))
    for value in (empty, *populated.category_rows, populated):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_notional",
                    "_drag",
                    "_ratio",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_uses_decimal_strings_utc_datetimes_and_no_floats() -> None:
    module = api()
    result = report(
        observations=(
            observation(
                category_id="macro",
                observed_at=datetime(2026, 7, 3, 8, 0, tzinfo=timezone(timedelta(hours=-7))),
                recommended_notional=d("75.000000"),
                realized_cost_drag=d("0.060000"),
                baseline_cost_drag=d("0.020000"),
            ),
        ),
        generated_at=datetime(2026, 7, 3, 8, 30, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_category_cost_drag_rotation_digest_payload(result)
    assert payload["generated_at"] == "2026-07-03T15:30:00+00:00"
    assert payload["observation_count"] == "1"
    assert payload["max_cost_drag_ratio"] == "0.060000"
    assert payload["category_rows"][0]["latest_observed_at"] == "2026-07-03T15:00:00+00:00"
    assert payload["category_rows"][0]["ending_recommended_notional"] == "75.000000"
    assert_no_float_values(payload)


def test_public_strings_reject_sensitive_reference_fragments_before_payload() -> None:
    with pytest.raises(ValueError, match="unsafe public text"):
        observation(category_id="crypto?token=secret")

    with pytest.raises(ValueError, match="unsafe public text"):
        observation(reason_codes=("manual_secret_review",))

    with pytest.raises(ValueError, match="unsafe public text"):
        config(config_version="digest-token-secret")


def test_validation_rejects_bad_types_thresholds_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_category_cost_drag_rotation_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="recommended_notional must be a Decimal"):
        observation(recommended_notional=100)

    with pytest.raises(ValueError, match="realized_cost_drag must be finite"):
        observation(realized_cost_drag=Decimal("NaN"))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(generated_at=datetime(2026, 7, 3, 15, 30))

    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))

    with pytest.raises(ValueError, match="baseline_cost_drag must be a Decimal"):
        observation(baseline_cost_drag=_DecimalSubclass("0.010000"))

    with pytest.raises(ValueError, match="baseline_cost_drag must be nonnegative"):
        observation(baseline_cost_drag=d("-0.000001"))

    with pytest.raises(ValueError, match="duplicate category_id/observed_at"):
        report(
            observations=(
                observation(category_id="crypto", observed_at=OBSERVED_AT),
                observation(category_id="crypto", observed_at=OBSERVED_AT),
            ),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyCategoryCostDragRotationDigestConfig(paper_only=False)

    row = report(observations=(observation(),)).category_rows[0]
    with pytest.raises(FrozenInstanceError):
        row.rotation_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(row, readonly=False)


def test_payload_requires_report_type_and_hard_flags() -> None:
    module = api()
    result = report(observations=(observation(),))

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_category_cost_drag_rotation_digest_payload(object())

    with pytest.raises(ValueError, match="report_only must be True"):
        module.strategy_category_cost_drag_rotation_digest_payload(
            replace(result, report_only=False),
        )


def test_module_scope_has_no_live_trading_persistence_network_or_sensitive_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_source_fragments = (
        "live trading",
        "auth",
        "wallet",
        "order",
        "cancel",
        "replace",
        "private_key",
        "api_key",
        "secret",
        "broker",
        "trade",
        "requests",
        "http",
        "psycopg",
        "sqlite",
        "open(",
        "write(",
    )
    assert [term for term in forbidden_source_fragments if term in source] == []

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
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
        "clob",
        "env",
        "http",
        "psycopg",
        "requests",
        "sqlite",
        "store",
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
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "rollback",
        "send",
        "sign",
        "trade",
        "write",
    }

    assert all(
        fragment not in module_name
        for module_name in imports
        for fragment in forbidden_import_fragments
    )
    assert not (set(call_names) & forbidden_call_or_attribute_names)
    assert not (set(attribute_names) & forbidden_call_or_attribute_names)


def test_public_api_exports_digest_contract() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_STRATEGY_CATEGORY_COST_DRAG_ROTATION_DIGEST_CONFIG_VERSION",
        "StrategyCategoryCostDragRotationDigestConfig",
        "StrategyCategoryCostDragRotationObservation",
        "StrategyCategoryCostDragRotationCategoryRow",
        "StrategyCategoryCostDragRotationDigestReport",
        "build_strategy_category_cost_drag_rotation_digest",
        "strategy_category_cost_drag_rotation_digest_payload",
    )
