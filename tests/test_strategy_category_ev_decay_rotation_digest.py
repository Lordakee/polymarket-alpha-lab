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
    / "strategy_category_ev_decay_rotation_digest.py"
)
GENERATED_AT = datetime(2026, 7, 3, 18, 30, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 3, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_category_ev_decay_rotation_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-category-ev-decay-rotation-digest-test-v0",
        "rotate_out_decay_ratio": d("0.400000"),
        "watch_decay_ratio": d("0.200000"),
        "min_rotation_ev_share_delta": d("0.100000"),
        "minimum_current_ev_ratio": d("0.005000"),
    }
    values.update(overrides)
    return module.StrategyCategoryEvDecayRotationDigestConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "category_id": "crypto",
        "observed_at": OBSERVED_AT,
        "peak_expected_value": d("0.100000"),
        "current_expected_value": d("0.060000"),
        "recommended_ev": d("60.000000"),
        "reason_codes": ("strategy_ev_decay_observed",),
    }
    values.update(overrides)
    return module.StrategyCategoryEvDecayRotationObservation(**values)


def report(*, observations=(), cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_category_ev_decay_rotation_digest(
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


def test_digest_summarizes_category_ev_decay_rotation_and_reason_codes() -> None:
    result = report(
        observations=(
            observation(
                category_id="macro",
                observed_at=OBSERVED_AT - timedelta(minutes=20),
                peak_expected_value=d("0.100000"),
                current_expected_value=d("0.090000"),
                recommended_ev=d("90.000000"),
            ),
            observation(
                category_id="macro",
                observed_at=OBSERVED_AT,
                peak_expected_value=d("0.100000"),
                current_expected_value=d("0.030000"),
                recommended_ev=d("30.000000"),
                reason_codes=("manual_ev_review",),
            ),
            observation(
                category_id="crypto",
                observed_at=OBSERVED_AT - timedelta(minutes=10),
                peak_expected_value=d("0.100000"),
                current_expected_value=d("0.060000"),
                recommended_ev=d("60.000000"),
            ),
            observation(
                category_id="crypto",
                observed_at=OBSERVED_AT,
                peak_expected_value=d("0.100000"),
                current_expected_value=d("0.080000"),
                recommended_ev=d("80.000000"),
            ),
            observation(
                category_id="sports",
                observed_at=OBSERVED_AT,
                peak_expected_value=d("0.100000"),
                current_expected_value=d("0.090000"),
                recommended_ev=d("10.000000"),
            ),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-category-ev-decay-rotation-digest-test-v0"
    assert result.observation_count == d("5")
    assert result.category_count == d("3")
    assert result.rotate_out_count == d("1")
    assert result.watch_count == d("1")
    assert result.hold_count == d("1")
    assert result.decayed_category_count == d("1")
    assert result.low_current_ev_count == d("0")
    assert result.max_ev_decay_ratio == d("0.700000")
    assert result.average_ev_decay_ratio == d("0.266667")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "category_ev_decay_rotate_out",
        "category_ev_decay_watch",
        "category_ev_decay_hold",
        "ev_decay_high",
        "ev_decay_moderate",
        "ev_decay_low",
        "category_rotation_detected",
        "manual_ev_review",
        "strategy_ev_decay_observed",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.category_id for row in result.category_rows) == (
        "macro",
        "crypto",
        "sports",
    )
    rotate_out, watched, held = result.category_rows

    assert rotate_out.rotation_status == "rotate_out"
    assert rotate_out.rotation_direction == "decrease"
    assert rotate_out.first_observed_at == OBSERVED_AT - timedelta(minutes=20)
    assert rotate_out.latest_observed_at == OBSERVED_AT
    assert rotate_out.starting_recommended_ev == d("90.000000")
    assert rotate_out.ending_recommended_ev == d("30.000000")
    assert rotate_out.recommended_ev_delta == d("-60.000000")
    assert rotate_out.starting_ev_share_ratio == d("0.600000")
    assert rotate_out.ending_ev_share_ratio == d("0.250000")
    assert rotate_out.ev_share_delta_ratio == d("-0.350000")
    assert rotate_out.peak_expected_value_ratio == d("0.100000")
    assert rotate_out.current_expected_value_ratio == d("0.030000")
    assert rotate_out.expected_value_delta_ratio == d("-0.070000")
    assert rotate_out.ev_decay_ratio == d("0.700000")
    assert rotate_out.ev_retention_ratio == d("0.300000")
    assert rotate_out.current_ev_buffer_ratio == d("0.025000")
    assert rotate_out.reason_codes == (
        "category_ev_decay_rotate_out",
        "category_rotation_decrease",
        "ev_decay_high",
        "current_ev_positive",
        "manual_ev_review",
        "strategy_ev_decay_observed",
    )

    assert watched.rotation_status == "watch"
    assert watched.rotation_direction == "increase"
    assert watched.starting_ev_share_ratio == d("0.400000")
    assert watched.ending_ev_share_ratio == d("0.666667")
    assert watched.ev_share_delta_ratio == d("0.266667")
    assert watched.ev_decay_ratio == d("0.200000")
    assert watched.ev_retention_ratio == d("0.800000")
    assert watched.reason_codes == (
        "category_ev_decay_watch",
        "category_rotation_increase",
        "ev_decay_moderate",
        "current_ev_positive",
        "strategy_ev_decay_observed",
    )

    assert held.rotation_status == "hold"
    assert held.starting_recommended_ev == ZERO
    assert held.ending_recommended_ev == d("10.000000")
    assert held.starting_ev_share_ratio == ZERO
    assert held.ending_ev_share_ratio == d("0.083333")
    assert held.ev_share_delta_ratio == d("0.083333")
    assert held.ev_decay_ratio == d("0.100000")
    assert held.reason_codes == (
        "category_ev_decay_hold",
        "category_rotation_stable",
        "ev_decay_low",
        "current_ev_positive",
        "strategy_ev_decay_observed",
    )


def test_new_category_share_increase_marks_rotation_detected() -> None:
    result = report(
        observations=(
            observation(
                category_id="new-category",
                current_expected_value=d("0.090000"),
                recommended_ev=d("25.000000"),
            ),
        ),
    )

    row = result.category_rows[0]
    assert row.rotation_direction == "increase"
    assert row.reason_codes == (
        "category_ev_decay_hold",
        "category_rotation_increase",
        "ev_decay_low",
        "current_ev_positive",
        "strategy_ev_decay_observed",
    )
    assert result.reason_codes == (
        "category_ev_decay_hold",
        "ev_decay_low",
        "category_rotation_detected",
        "strategy_ev_decay_observed",
    )


def test_empty_digest_is_watch_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.observation_count == d("0")
    assert empty.category_count == d("0")
    assert empty.rotate_out_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.hold_count == d("0")
    assert empty.decayed_category_count == d("0")
    assert empty.low_current_ev_count == d("0")
    assert empty.max_ev_decay_ratio == ZERO
    assert empty.average_ev_decay_ratio == ZERO
    assert empty.status == "watch"
    assert empty.reason_codes == ("strategy_category_ev_decay_rotation_empty",)
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
                    "_ev",
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
                observed_at=datetime(2026, 7, 3, 11, 0, tzinfo=timezone(timedelta(hours=-7))),
                peak_expected_value=d("0.100000"),
                current_expected_value=d("0.050000"),
                recommended_ev=d("40.000000"),
            ),
        ),
        generated_at=datetime(2026, 7, 3, 11, 30, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_category_ev_decay_rotation_digest_payload(result)
    assert payload["generated_at"] == "2026-07-03T18:30:00+00:00"
    assert payload["observation_count"] == "1"
    assert payload["max_ev_decay_ratio"] == "0.500000"
    assert payload["category_rows"][0]["latest_observed_at"] == "2026-07-03T18:00:00+00:00"
    assert payload["category_rows"][0]["ending_recommended_ev"] == "40.000000"
    assert_no_float_values(payload)


def test_validation_rejects_bad_types_thresholds_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_category_ev_decay_rotation_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="recommended_ev must be a Decimal"):
        observation(recommended_ev=100)

    with pytest.raises(ValueError, match="current_expected_value must be finite"):
        observation(current_expected_value=Decimal("NaN"))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(generated_at=datetime(2026, 7, 3, 18, 30))

    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))

    with pytest.raises(ValueError, match="peak_expected_value must be a Decimal"):
        observation(peak_expected_value=_DecimalSubclass("0.100000"))

    with pytest.raises(ValueError, match="peak_expected_value must be positive"):
        observation(peak_expected_value=d("0.000000"))

    with pytest.raises(ValueError, match="watch_decay_ratio must be below rotate_out_decay_ratio"):
        config(watch_decay_ratio=d("0.400000"))

    with pytest.raises(ValueError, match="duplicate category_id/observed_at"):
        report(
            observations=(
                observation(category_id="crypto", observed_at=OBSERVED_AT),
                observation(category_id="crypto", observed_at=OBSERVED_AT),
            ),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyCategoryEvDecayRotationDigestConfig(paper_only=False)

    row = report(observations=(observation(),)).category_rows[0]
    with pytest.raises(FrozenInstanceError):
        row.rotation_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(row, readonly=False)


def test_payload_requires_report_type_and_hard_flags() -> None:
    module = api()
    result = report(observations=(observation(),))

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_category_ev_decay_rotation_digest_payload(object())

    with pytest.raises(ValueError, match="report_only must be True"):
        module.strategy_category_ev_decay_rotation_digest_payload(
            replace(result, report_only=False),
        )


def test_payload_revalidates_tampered_derived_report_fields() -> None:
    module = api()
    result = report(observations=(observation(),))
    object.__setattr__(result, "category_count", d("2"))

    with pytest.raises(ValueError, match="category_count must match category_rows"):
        module.strategy_category_ev_decay_rotation_digest_payload(result)


def test_payload_revalidates_tampered_derived_category_row_fields() -> None:
    module = api()
    result = report(observations=(observation(),))
    row = result.category_rows[0]
    object.__setattr__(row, "ev_retention_ratio", d("0.999999"))

    with pytest.raises(ValueError, match="ev_retention_ratio must match ev_decay_ratio"):
        module.strategy_category_ev_decay_rotation_digest_payload(result)


def test_payload_rejects_injected_unsafe_public_surface_fields() -> None:
    module = api()
    result = report(observations=(observation(),))
    object.__setattr__(result, "wallet_address", "0xunsafe")

    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.strategy_category_ev_decay_rotation_digest_payload(result)


def test_module_scope_has_no_live_trading_persistence_network_or_sensitive_surfaces() -> None:
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
        "DEFAULT_STRATEGY_CATEGORY_EV_DECAY_ROTATION_DIGEST_CONFIG_VERSION",
        "StrategyCategoryEvDecayRotationDigestConfig",
        "StrategyCategoryEvDecayRotationObservation",
        "StrategyCategoryEvDecayRotationCategoryRow",
        "StrategyCategoryEvDecayRotationDigestReport",
        "build_strategy_category_ev_decay_rotation_digest",
        "strategy_category_ev_decay_rotation_digest_payload",
    )
