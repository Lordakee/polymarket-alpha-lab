from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_category_rotation_composite_gate_digest"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_category_rotation_composite_gate_digest.py"
)
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_CATEGORY_ROTATION_COMPOSITE_GATE_DIGEST_CONFIG_VERSION
        ),
        "max_pass_cost_drag_score": d("0.030000"),
        "max_watch_cost_drag_score": d("0.060000"),
        "max_pass_volatility_pressure_score": d("0.300000"),
        "max_watch_volatility_pressure_score": d("0.550000"),
        "max_pass_resolution_timeline_pressure_score": d("0.250000"),
        "max_watch_resolution_timeline_pressure_score": d("0.500000"),
        "min_pass_liquidity_capacity_score": d("0.700000"),
        "min_watch_liquidity_capacity_score": d("0.450000"),
        "min_pass_research_capacity_score": d("0.700000"),
        "min_watch_research_capacity_score": d("0.450000"),
        "max_pass_signal_age_seconds": d("1800.000000"),
        "max_watch_signal_age_seconds": d("3600.000000"),
        "min_pass_learning_value_score": d("0.500000"),
        "min_watch_learning_value_score": d("0.250000"),
        "minimum_pass_categories": d("1.000000"),
    }
    values.update(overrides)
    return module.StrategyCategoryRotationCompositeGateDigestConfig(**values)


def signal(category_id: str = "politics", **overrides: object) -> Any:
    module = api()
    values = {
        "category_id": category_id,
        "team_id": "alpha_team",
        "signal_observed_at": GENERATED_AT - timedelta(minutes=15),
        "cost_drag_score": d("0.020000"),
        "volatility_pressure_score": d("0.200000"),
        "resolution_timeline_pressure_score": d("0.200000"),
        "liquidity_capacity_score": d("0.800000"),
        "research_capacity_score": d("0.750000"),
        "learning_value_score": d("0.700000"),
        "public_reference": "manual-note",
        "reason_codes": ("category_rotation_signal_available",),
    }
    values.update(overrides)
    return module.StrategyCategoryRotationCompositeGateSignal(**values)


def digest(
    *rows: Any,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_strategy_category_rotation_composite_gate_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_public_numeric_fields_are_decimal(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for item in fields(value):
            nested = getattr(value, item.name)
            if type(nested) is bool:
                continue
            assert type(nested) is not int
            assert type(nested) is not float
            if isinstance(nested, Decimal):
                assert type(nested) is Decimal
            if isinstance(nested, tuple):
                for child in nested:
                    assert_public_numeric_fields_are_decimal(child)


def assert_no_float_or_decimal_payload_values(value: Any) -> None:
    if isinstance(value, (float, Decimal)):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_decimal_payload_values(child)
    if isinstance(value, list):
        for child in value:
            assert_no_float_or_decimal_payload_values(child)


def test_digest_reduces_category_signals_to_pass_watch_and_blocked_readiness_rows() -> None:
    result = digest(
        signal(
            "sports",
            team_id="sports_team",
            signal_observed_at=GENERATED_AT - timedelta(hours=2),
            cost_drag_score=d("0.080000"),
            volatility_pressure_score=d("0.700000"),
            resolution_timeline_pressure_score=d("0.600000"),
            liquidity_capacity_score=d("0.200000"),
            research_capacity_score=d("0.200000"),
            learning_value_score=d("0.100000"),
            public_reference="https://example.test/feed?token=secret",
        ),
        signal(
            "crypto",
            team_id="crypto_team",
            signal_observed_at=GENERATED_AT - timedelta(minutes=15),
        ),
        signal(
            "politics",
            team_id="politics_team",
            signal_observed_at=GENERATED_AT - timedelta(minutes=40),
            cost_drag_score=d("0.040000"),
            volatility_pressure_score=d("0.350000"),
            resolution_timeline_pressure_score=d("0.300000"),
            liquidity_capacity_score=d("0.600000"),
            research_capacity_score=d("0.500000"),
            learning_value_score=d("0.300000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.config_version == "strategy-category-rotation-composite-gate-digest-v0"
    assert result.category_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.blocked_count == d("1.000000")
    assert result.status == "blocked"
    assert result.passed_category_ids == ("crypto",)
    assert result.reason_codes == tuple(sorted(set(result.reason_codes)))
    assert "category_rotation_composite_gate_blocked" in result.reason_codes
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)

    assert tuple(row.category_id for row in result.rows) == (
        "crypto",
        "politics",
        "sports",
    )
    assert tuple(row.readiness_status for row in result.rows) == (
        "pass",
        "watch",
        "blocked",
    )
    assert tuple(row.rank for row in result.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )

    passed = result.rows[0]
    assert passed.team_id == "crypto_team"
    assert passed.signal_age_seconds == d("900.000000")
    assert passed.readiness_score == d("0.797143")
    assert passed.redacted_public_reference == "manual-note"
    assert passed.reason_codes == (
        "category_rotation_composite_gate_pass",
        "category_rotation_signal_available",
        "cost_drag_clear",
        "learning_value_clear",
        "liquidity_capacity_clear",
        "research_capacity_clear",
        "resolution_timeline_clear",
        "signal_staleness_clear",
        "volatility_pressure_clear",
    )

    watched = result.rows[1]
    assert watched.readiness_score == d("0.577619")
    assert watched.reason_codes == (
        "category_rotation_composite_gate_watch",
        "category_rotation_signal_available",
        "cost_drag_watch",
        "learning_value_watch",
        "liquidity_capacity_watch",
        "research_capacity_watch",
        "resolution_timeline_watch",
        "signal_staleness_watch",
        "volatility_pressure_watch",
    )

    blocked = result.rows[2]
    assert blocked.readiness_score == ZERO
    assert blocked.redacted_public_reference.startswith("public_ref_")
    assert blocked.reason_codes == (
        "category_rotation_composite_gate_blocked",
        "category_rotation_signal_available",
        "cost_drag_blocked",
        "learning_value_blocked",
        "liquidity_capacity_blocked",
        "research_capacity_blocked",
        "resolution_timeline_blocked",
        "signal_staleness_blocked",
        "volatility_pressure_blocked",
    )

    counts_by_reason_code = {
        row.reason_code: row.count for row in result.reason_code_counts
    }
    assert counts_by_reason_code["category_rotation_signal_available"] == d("3.000000")
    assert result.reason_code_counts == tuple(
        sorted(result.reason_code_counts, key=lambda row: (-row.count, row.reason_code)),
    )


def test_empty_digest_is_watch_report_only_readonly_and_decimal_zeroed() -> None:
    result = digest()

    assert result.category_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.blocked_count == ZERO
    assert result.status == "watch"
    assert result.passed_category_ids == ()
    assert result.max_readiness_score == ZERO
    assert result.min_readiness_score == ZERO
    assert result.average_readiness_score == ZERO
    assert result.reason_codes == ("category_rotation_composite_gate_digest_empty",)
    assert result.reason_code_counts == ()
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)


def test_payload_redacts_public_references_and_serializes_decimal_counts_as_strings() -> None:
    module = api()
    source = signal(
        public_reference="https://example.test/feed?token=secret&wallet=0xabc123",
        reason_codes=(
            "category_rotation_signal_available",
            "api_key_sk_live_secret_token",
            "wallet_0xabc123_private_key",
            "order_cancel_replace_auth",
        ),
    )
    result = digest(
        source,
        generated_at=datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.strategy_category_rotation_composite_gate_digest_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
    payload_repr = repr(payload).lower()
    result_repr = repr(result).lower()
    source_repr = repr(source).lower()

    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["category_count"] == "1.000000"
    assert payload["rows"][0]["rank"] == "1.000000"
    assert payload["rows"][0]["readiness_score"] == "0.797143"
    assert payload["rows"][0]["redacted_public_reference"].startswith("public_ref_")
    assert payload["rows"][0]["reason_codes"] == [
        "category_rotation_composite_gate_pass",
        "category_rotation_signal_available",
        "cost_drag_clear",
        "credential_redacted",
        "learning_value_clear",
        "liquidity_capacity_clear",
        "reference_redacted",
        "research_capacity_clear",
        "resolution_timeline_clear",
        "signal_staleness_clear",
        "surface_redacted",
        "volatility_pressure_clear",
    ]
    assert not re.search(r":\s*-?\d+\.\d+", encoded)
    assert_no_float_or_decimal_payload_values(payload)
    for forbidden in (
        "api_key",
        "sk_live",
        "secret",
        "token",
        "private_key",
        "0xabc123",
        "wallet",
        "order_cancel",
        "cancel",
        "replace",
        "auth",
    ):
        assert forbidden not in payload_repr
        assert forbidden not in result_repr
        assert forbidden not in source_repr


def test_payload_dict_path_rejects_numeric_and_phase1_boundary_drift() -> None:
    module = api()
    payload = module.strategy_category_rotation_composite_gate_digest_payload(
        digest(signal()),
    )

    assert module.strategy_category_rotation_composite_gate_digest_payload(payload) == payload

    with pytest.raises(ValueError, match="readonly.*True"):
        module.strategy_category_rotation_composite_gate_digest_payload(
            {**payload, "readonly": False},
        )

    nested_flag_payload = dict(payload)
    nested_flag_payload["rows"] = [{**payload["rows"][0], "paper_only": False}]
    with pytest.raises(ValueError, match="paper_only.*True"):
        module.strategy_category_rotation_composite_gate_digest_payload(
            nested_flag_payload,
        )

    with pytest.raises(ValueError, match="category_count.*Decimal|numeric"):
        module.strategy_category_rotation_composite_gate_digest_payload(
            {**payload, "category_count": 1},
        )

    with pytest.raises(ValueError, match="float"):
        module.strategy_category_rotation_composite_gate_digest_payload(
            {**payload, "average_readiness_score": 0.42},
        )

    with pytest.raises(ValueError, match="generated_at.*timezone-aware"):
        module.strategy_category_rotation_composite_gate_digest_payload(
            {**payload, "generated_at": datetime(2026, 7, 4, 12, 0)},
        )

    with pytest.raises(ValueError, match="generated_at.*datetime"):
        module.strategy_category_rotation_composite_gate_digest_payload(
            {**payload, "generated_at": _DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC)},
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_category_rotation_composite_gate_digest_payload(
            {**payload, "public_reference": "https://example.test/feed?token=secret"},
        )

    with pytest.raises(ValueError, match="JSON object keys"):
        module.strategy_category_rotation_composite_gate_digest_payload({1: "x", **payload})


def test_validation_rejects_non_decimal_datetime_subclasses_and_unsafe_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="cost_drag_score must be a Decimal"):
        signal(cost_drag_score=1)
    with pytest.raises(ValueError, match="cost_drag_score must be exactly Decimal"):
        signal(cost_drag_score=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="volatility_pressure_score must be a Decimal"):
        signal(volatility_pressure_score=0.2)
    with pytest.raises(ValueError, match="category_id must be a nonblank trimmed string"):
        signal(category_id=_StringSubclass("politics"))
    with pytest.raises(ValueError, match="signal_observed_at must be timezone-aware"):
        signal(signal_observed_at=datetime(2026, 7, 4, 11, 45))
    with pytest.raises(ValueError, match="signal_observed_at must be timezone-aware"):
        signal(
            signal_observed_at=datetime(
                2026,
                7,
                4,
                11,
                45,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="signal_observed_at must be a datetime"):
        signal(signal_observed_at=_DatetimeSubclass(2026, 7, 4, 11, 45, tzinfo=UTC))
    with pytest.raises(ValueError, match="signal_observed_at must not be after generated_at"):
        digest(signal(signal_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only must be True"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_category_rotation_composite_gate_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="max_pass_cost_drag_score"):
        config(max_pass_cost_drag_score=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        digest(signal(), generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="categories must be unique"):
        digest(signal("crypto"), signal("crypto"))


def test_report_dataclasses_are_frozen_and_revalidate_invariants() -> None:
    result = digest(
        signal(
            signal_observed_at=datetime(
                2026,
                7,
                4,
                7,
                45,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert result.generated_at == GENERATED_AT
    assert result.rows[0].signal_observed_at == datetime(2026, 7, 4, 11, 45, tzinfo=UTC)
    assert result.rows[0].signal_observed_at.tzinfo is UTC

    with pytest.raises(FrozenInstanceError):
        result.rows[0].readiness_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.reason_code_counts[0].count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result.rows[0], readonly=False)
    with pytest.raises(ValueError, match="digest report must contain exact rows"):
        replace(result, rows=(object(),))
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(result, reason_code_counts=())


def test_module_is_pure_report_only_and_avoids_io_db_or_live_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    tree = ast.parse(source)

    forbidden_calls = {"open", "print", "float"}
    forbidden_import_roots = {
        "http",
        "json",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_literals = (
        "api_key",
        "private_key",
        "wallet",
        "secret",
        "token",
        "order",
        "cancel",
        "replace",
        "auth",
        "trade",
        "network",
        "socket",
        "sqlite",
        "subprocess",
        "requests",
        "urllib",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots

    for forbidden in forbidden_literals:
        assert forbidden not in source
