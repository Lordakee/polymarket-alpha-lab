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


MODULE_NAME = "polymarket_alpha_lab.strategy_category_volatility_rotation_digest"
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ZERO_COUNT = Decimal("0")


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
            module.DEFAULT_STRATEGY_CATEGORY_VOLATILITY_ROTATION_DIGEST_CONFIG_VERSION
        ),
        "minimum_eligible_pressure_score": d("0.350000"),
        "watch_pressure_score": d("0.150000"),
        "maximum_stale_event_ratio": d("0.300000"),
        "watch_stale_event_ratio": d("0.500000"),
        "maximum_unresolved_event_ratio": d("0.400000"),
        "watch_unresolved_event_ratio": d("0.650000"),
        "maximum_sample_age_seconds": d("3600"),
        "watch_sample_age_seconds": d("7200"),
        "minimum_event_count": d("3"),
    }
    values.update(overrides)
    return module.StrategyCategoryVolatilityRotationDigestConfig(**values)


def category(category_name: str = "politics", **overrides: object) -> Any:
    module = api()
    values = {
        "category": category_name,
        "sample_observed_at": GENERATED_AT - timedelta(minutes=15),
        "event_count": d("8"),
        "probability_swing_abs": d("0.520000"),
        "intraday_probability_range": d("0.440000"),
        "probability_update_count": d("8"),
        "stale_event_ratio": d("0.100000"),
        "unresolved_event_ratio": d("0.200000"),
        "public_reference": "manual-note",
        "reason_codes": ("category_volatility_input_available",),
    }
    values.update(overrides)
    return module.StrategyCategoryVolatilityRotationInput(**values)


def digest(
    *rows: Any,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_strategy_category_volatility_rotation_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_public_numeric_fields_are_decimal(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            nested = getattr(value, field.name)
            if type(nested) is bool:
                continue
            assert type(nested) is not int
            assert type(nested) is not float
            if isinstance(nested, Decimal):
                assert type(nested) is Decimal
            if isinstance(nested, tuple):
                for item in nested:
                    assert_public_numeric_fields_are_decimal(item)


def assert_no_float_values(value: object) -> None:
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_digest_ranks_categories_by_volatility_pressure_and_rotation_state() -> None:
    module = api()

    result = digest(
        category(
            "sports",
            event_count=d("10"),
            probability_swing_abs=d("0.060000"),
            intraday_probability_range=d("0.050000"),
            probability_update_count=d("1"),
        ),
        category(
            "crypto",
            event_count=d("4"),
            probability_swing_abs=d("0.330000"),
            intraday_probability_range=d("0.280000"),
            probability_update_count=d("2"),
        ),
        category("politics"),
    )

    assert is_dataclass(result)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-category-volatility-rotation-digest-v0"
    assert result.category_count == d("3")
    assert result.eligible_count == d("1")
    assert result.watch_count == d("1")
    assert result.deprioritize_count == d("1")
    assert result.top_category == "politics"
    assert result.max_volatility_pressure_score == d("0.588000")
    assert result.min_volatility_pressure_score == d("0.064500")
    assert result.average_volatility_pressure_score == d("0.333000")
    assert result.digest_status == "watch"
    assert result.reason_codes == (
        "category_volatility_input_available",
        "event_count_sufficient",
        "sample_recent",
        "stale_event_ratio_clear",
        "unresolved_event_ratio_clear",
        "volatility_pressure_deprioritize",
        "volatility_pressure_eligible",
        "volatility_pressure_high",
        "volatility_pressure_low",
        "volatility_pressure_watch",
    )
    assert_public_numeric_fields_are_decimal(result)

    assert tuple(row.category for row in result.rows) == ("politics", "crypto", "sports")
    top = result.rows[0]
    assert top.rank == d("1")
    assert top.update_density_score == d("1.000000")
    assert top.sample_age_seconds == d("900.000000")
    assert top.volatility_pressure_score == d("0.588000")
    assert top.rotation_state == "eligible"
    assert top.redacted_public_reference == "manual-note"
    assert top.reason_codes == (
        "category_volatility_input_available",
        "event_count_sufficient",
        "sample_recent",
        "stale_event_ratio_clear",
        "unresolved_event_ratio_clear",
        "volatility_pressure_eligible",
        "volatility_pressure_high",
    )

    watch_row = result.rows[1]
    assert watch_row.category == "crypto"
    assert watch_row.update_density_score == d("0.500000")
    assert watch_row.volatility_pressure_score == d("0.346500")
    assert watch_row.rotation_state == "watch"
    assert watch_row.reason_codes == (
        "category_volatility_input_available",
        "event_count_sufficient",
        "sample_recent",
        "stale_event_ratio_clear",
        "unresolved_event_ratio_clear",
        "volatility_pressure_watch",
    )

    low_row = result.rows[2]
    assert low_row.category == "sports"
    assert low_row.update_density_score == d("0.100000")
    assert low_row.volatility_pressure_score == d("0.064500")
    assert low_row.rotation_state == "deprioritize"
    assert low_row.reason_codes == (
        "category_volatility_input_available",
        "event_count_sufficient",
        "sample_recent",
        "stale_event_ratio_clear",
        "unresolved_event_ratio_clear",
        "volatility_pressure_deprioritize",
        "volatility_pressure_low",
    )

    assert result.reason_code_counts == tuple(
        sorted(result.reason_code_counts, key=lambda row: (-row.count, row.reason_code)),
    )
    counts_by_reason_code = {
        row.reason_code: row.count for row in result.reason_code_counts
    }
    assert counts_by_reason_code["category_volatility_input_available"] == d("3")
    assert result.reason_code_counts[0] == module.StrategyCategoryVolatilityRotationDigestReasonCodeCount(
        reason_code="category_volatility_input_available",
        count=d("3"),
    )


def test_empty_digest_is_report_only_readonly_and_decimal_zeroed() -> None:
    result = digest()

    assert result.category_count == ZERO_COUNT
    assert result.eligible_count == ZERO_COUNT
    assert result.watch_count == ZERO_COUNT
    assert result.deprioritize_count == ZERO_COUNT
    assert result.top_category is None
    assert result.max_volatility_pressure_score == ZERO
    assert result.min_volatility_pressure_score == ZERO
    assert result.average_volatility_pressure_score == ZERO
    assert result.digest_status == "deprioritize"
    assert result.reason_codes == ("strategy_category_volatility_rotation_digest_empty",)
    assert result.reason_code_counts == ()
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)


def test_payload_is_json_ready_decimal_stringed_and_redacted() -> None:
    module = api()
    result = digest(
        category(
            reason_codes=(
                "category_volatility_input_available",
                "api_key_sk_live_secret_token",
                "wallet_0xabc123_private_key",
                "order_cancel_replace_auth",
            ),
            public_reference="https://example.test/feed?token=secret",
        ),
        generated_at=datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.strategy_category_volatility_rotation_digest_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
    payload_repr = repr(payload).lower()
    report_repr = repr(result).lower()

    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["category_count"] == "1"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["volatility_pressure_score"] == "0.588000"
    assert payload["rows"][0]["redacted_public_reference"] == "<redacted>"
    assert payload["rows"][0]["reason_codes"] == [
        "category_volatility_input_available",
        "credential_redacted",
        "event_count_sufficient",
        "reference_redacted",
        "sample_recent",
        "stale_event_ratio_clear",
        "surface_redacted",
        "unresolved_event_ratio_clear",
        "volatility_pressure_eligible",
        "volatility_pressure_high",
    ]
    assert not re.search(r":\s*-?\d+\.\d+", encoded)
    assert_no_float_values(payload)
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
        assert forbidden not in report_repr


def test_payload_dict_path_enforces_strict_phase1_boundaries() -> None:
    module = api()
    payload = module.strategy_category_volatility_rotation_digest_payload(
        digest(category()),
    )

    assert module.strategy_category_volatility_rotation_digest_payload(payload) == payload

    with pytest.raises(ValueError, match="readonly.*True"):
        module.strategy_category_volatility_rotation_digest_payload(
            {**payload, "readonly": False},
        )

    nested_flag_payload = dict(payload)
    nested_flag_payload["rows"] = [{**payload["rows"][0], "paper_only": False}]
    with pytest.raises(ValueError, match="paper_only.*True"):
        module.strategy_category_volatility_rotation_digest_payload(nested_flag_payload)

    with pytest.raises(ValueError, match="category_count.*Decimal|numeric"):
        module.strategy_category_volatility_rotation_digest_payload(
            {**payload, "category_count": 1},
        )

    with pytest.raises(ValueError, match="float"):
        module.strategy_category_volatility_rotation_digest_payload(
            {**payload, "average_volatility_pressure_score": 0.42},
        )

    with pytest.raises(ValueError, match="generated_at.*timezone-aware"):
        module.strategy_category_volatility_rotation_digest_payload(
            {**payload, "generated_at": datetime(2026, 7, 4, 12, 0)},
        )

    with pytest.raises(ValueError, match="generated_at.*datetime"):
        module.strategy_category_volatility_rotation_digest_payload(
            {**payload, "generated_at": _DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC)},
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_category_volatility_rotation_digest_payload(
            {**payload, "wallet": {"address": "0x0"}},
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_category_volatility_rotation_digest_payload(
            {**payload, "public_reference": "https://example.test/feed?token=secret"},
        )

    with pytest.raises(ValueError, match="JSON object keys"):
        module.strategy_category_volatility_rotation_digest_payload({1: "x", **payload})


def test_validation_rejects_non_decimal_datetime_subclasses_and_unsafe_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="event_count must be a Decimal"):
        category(event_count=8)
    with pytest.raises(ValueError, match="event_count must be exactly Decimal"):
        category(event_count=_DecimalSubclass("8"))
    with pytest.raises(ValueError, match="probability_swing_abs must be a Decimal"):
        category(probability_swing_abs=0.52)
    with pytest.raises(ValueError, match="category must be a nonblank trimmed string"):
        category(category_name=_StringSubclass("politics"))
    with pytest.raises(ValueError, match="event_count must be above zero"):
        category(event_count=ZERO_COUNT)
    with pytest.raises(ValueError, match="probability_swing_abs must be between zero and one"):
        category(probability_swing_abs=d("1.100000"))
    with pytest.raises(ValueError, match="sample_observed_at must be timezone-aware"):
        category(sample_observed_at=datetime(2026, 7, 4, 11, 45))
    with pytest.raises(ValueError, match="sample_observed_at must be timezone-aware"):
        category(
            sample_observed_at=datetime(
                2026,
                7,
                4,
                11,
                45,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="sample_observed_at must be a datetime"):
        category(sample_observed_at=_DatetimeSubclass(2026, 7, 4, 11, 45, tzinfo=UTC))
    with pytest.raises(ValueError, match="sample_observed_at must not be after generated_at"):
        digest(category(sample_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only must be True"):
        category(paper_only=False)
    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_category_volatility_rotation_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="watch_pressure_score"):
        config(watch_pressure_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        digest(category(), generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="categories must be unique"):
        digest(category("crypto"), category("crypto"))


def test_report_dataclasses_are_frozen_and_validate_invariants() -> None:
    result = digest(
        category(
            sample_observed_at=datetime(
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
    assert result.generated_at.tzinfo is UTC
    assert result.rows[0].sample_observed_at == datetime(2026, 7, 4, 11, 45, tzinfo=UTC)
    assert result.rows[0].sample_observed_at.tzinfo is UTC

    with pytest.raises(FrozenInstanceError):
        result.rows[0].rotation_state = "watch"
    with pytest.raises(FrozenInstanceError):
        result.reason_code_counts[0].count = d("2")
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result.rows[0], readonly=False)
    with pytest.raises(ValueError, match="digest report must contain exact rows"):
        replace(result, rows=(object(),))
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(result, reason_code_counts=())


def test_module_is_pure_report_only_and_avoids_io_network_or_live_terms() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "strategy_category_volatility_rotation_digest.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
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
