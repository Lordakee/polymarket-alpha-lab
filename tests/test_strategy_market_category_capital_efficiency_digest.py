from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_market_category_capital_efficiency_digest"
GENERATED_AT = datetime(2026, 7, 3, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_MARKET_CATEGORY_CAPITAL_EFFICIENCY_DIGEST_CONFIG_VERSION
        ),
        "target_liquidity_capacity": d("1000.000000"),
        "pass_efficiency_score": d("0.050000"),
        "watch_efficiency_score": d("0.010000"),
        "max_holding_period_days": d("30"),
        "low_forecast_confidence": d("0.500000"),
        "high_unresolved_exposure_ratio": d("0.750000"),
        "high_learning_value": d("0.700000"),
    }
    values.update(overrides)
    return module.StrategyMarketCategoryCapitalEfficiencyDigestConfig(**values)


def category(**overrides: object) -> Any:
    module = api()
    values = {
        "category": "macro",
        "expected_edge": d("0.050000"),
        "holding_period_days": d("20"),
        "fee_drag": d("0.005000"),
        "liquidity_capacity": d("1000.000000"),
        "forecast_confidence": d("0.800000"),
        "unresolved_exposure": d("100.000000"),
        "learning_value": d("0.300000"),
        "source_reference": "plain-ticket",
    }
    values.update(overrides)
    return module.StrategyMarketCategoryCapitalEfficiencyInput(**values)


def digest(*rows: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_strategy_market_category_capital_efficiency_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float
        assert type(value) is not int
        if isinstance(value, tuple):
            for item in value:
                if is_dataclass(item):
                    assert_public_numeric_fields_are_decimal(item)


def assert_no_float_values(value: object) -> None:
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_digest_ranks_categories_by_paper_capital_efficiency() -> None:
    result = digest(
        category(
            category="crypto",
            expected_edge=d("0.020000"),
            holding_period_days=d("7"),
            fee_drag=d("0.025000"),
            liquidity_capacity=d("1000.000000"),
            forecast_confidence=d("0.700000"),
            unresolved_exposure=d("1200.000000"),
            learning_value=d("0.800000"),
            source_reference="wallet://private-key",
        ),
        category(
            category="sports",
            expected_edge=d("0.090000"),
            holding_period_days=d("10"),
            fee_drag=d("0.010000"),
            liquidity_capacity=d("1000.000000"),
            forecast_confidence=d("0.800000"),
            unresolved_exposure=d("200.000000"),
            learning_value=d("0.800000"),
            source_reference="https://example.test/feed?token=secret",
        ),
        category(
            category="macro",
            expected_edge=d("0.050000"),
            holding_period_days=d("30"),
            fee_drag=d("0.005000"),
            liquidity_capacity=d("2000.000000"),
            forecast_confidence=d("0.900000"),
            unresolved_exposure=d("500.000000"),
            learning_value=d("0.100000"),
            source_reference="plain-ticket",
        ),
    )

    assert is_dataclass(result)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-market-category-capital-efficiency-digest-v0"
    assert result.category_count == d("3")
    assert result.pass_count == d("2")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("1")
    assert result.top_category == "sports"
    assert result.max_efficiency_score == d("3.363840")
    assert result.min_efficiency_score == ZERO
    assert result.average_efficiency_score == d("1.301955")
    assert result.digest_status == "watch"
    assert result.reason_codes == (
        "capital_efficiency_pass",
        "fee_drag_exceeds_edge",
        "learning_value_high",
        "liquidity_capacity_exhausted",
        "positive_net_edge",
        "unresolved_exposure_high",
    )
    assert_public_numeric_fields_are_decimal(result)

    assert tuple(row.category for row in result.rows) == ("sports", "macro", "crypto")
    top = result.rows[0]
    assert top.rank == d("1")
    assert top.net_expected_edge == d("0.080000")
    assert top.available_liquidity_capacity == d("800.000000")
    assert top.liquidity_capacity_score == d("0.800000")
    assert top.annualized_net_edge == d("2.920000")
    assert top.confidence_adjusted_edge == d("2.336000")
    assert top.learning_adjusted_edge == d("4.204800")
    assert top.efficiency_score == d("3.363840")
    assert top.capital_efficiency_status == "pass"
    assert top.redacted_source_reference == "<redacted>"
    assert top.reason_codes == (
        "capital_efficiency_pass",
        "learning_value_high",
        "positive_net_edge",
    )

    middle = result.rows[1]
    assert middle.rank == d("2")
    assert middle.category == "macro"
    assert middle.efficiency_score == d("0.542025")
    assert middle.redacted_source_reference == "plain-ticket"

    blocked = result.rows[2]
    assert blocked.rank == d("3")
    assert blocked.category == "crypto"
    assert blocked.net_expected_edge == d("-0.005000")
    assert blocked.available_liquidity_capacity == ZERO
    assert blocked.liquidity_capacity_score == ZERO
    assert blocked.efficiency_score == ZERO
    assert blocked.capital_efficiency_status == "blocked"
    assert blocked.reason_codes == (
        "fee_drag_exceeds_edge",
        "liquidity_capacity_exhausted",
        "unresolved_exposure_high",
    )


def test_empty_digest_is_report_only_readonly_and_decimal_zeroed() -> None:
    result = digest()

    assert result.category_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("0")
    assert result.top_category is None
    assert result.max_efficiency_score == ZERO
    assert result.min_efficiency_score == ZERO
    assert result.average_efficiency_score == ZERO
    assert result.digest_status == "blocked"
    assert result.reason_codes == (
        "strategy_market_category_capital_efficiency_digest_empty",
    )
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)


def test_payload_is_json_ready_decimal_stringed_and_redacted() -> None:
    module = api()
    result = digest(
        category(
            category="macro",
            source_reference="https://example.test/private?api_key=secret",
        ),
        generated_at=datetime(2026, 7, 3, 11, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.strategy_market_category_capital_efficiency_digest_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-03T15:00:00+00:00"
    assert payload["category_count"] == "1"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["efficiency_score"] == "0.768690"
    assert payload["rows"][0]["redacted_source_reference"] == "<redacted>"
    assert "api_key=secret" not in encoded
    assert "source_reference" not in payload["rows"][0]
    assert not re.search(r":\s*-?\d+\.\d+", encoded)
    assert_no_float_values(payload)


def test_payload_accepts_safe_dict_and_rejects_flag_downgrades() -> None:
    module = api()

    payload = module.strategy_market_category_capital_efficiency_digest_payload(
        {
            "generated_at": GENERATED_AT,
            "category_count": d("1"),
            "rows": ({"rank": d("1"), "category": "macro"},),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )

    assert payload == {
        "generated_at": "2026-07-03T15:00:00+00:00",
        "category_count": "1",
        "rows": [{"rank": "1", "category": "macro"}],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.strategy_market_category_capital_efficiency_digest_payload(
            {
                "paper_only": False,
                "report_only": True,
                "readonly": True,
            },
        )


def test_payload_rejects_unsafe_surface_values_and_non_decimal_numbers() -> None:
    module = api()
    safe_flags = {"paper_only": True, "report_only": True, "readonly": True}

    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.strategy_market_category_capital_efficiency_digest_payload(
            {**safe_flags, "order_submission": "never"},
        )
    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.strategy_market_category_capital_efficiency_digest_payload(
            {**safe_flags, "network_endpoint": "paper"},
        )
    with pytest.raises(ValueError, match="unsafe value"):
        module.strategy_market_category_capital_efficiency_digest_payload(
            {**safe_flags, "redacted_source_reference": "api_key=secret"},
        )
    with pytest.raises(ValueError, match="unsafe value"):
        module.strategy_market_category_capital_efficiency_digest_payload(
            {**safe_flags, "redacted_source_reference": "wallet"},
        )
    with pytest.raises(ValueError, match="must use Decimal-derived string values"):
        module.strategy_market_category_capital_efficiency_digest_payload(
            {**safe_flags, "category_count": 1},
        )
    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.strategy_market_category_capital_efficiency_digest_payload(
            {**safe_flags, "efficiency_score": 0.1},
        )


def test_derived_validation_digest_is_report_and_row_bound() -> None:
    module = api()
    result = digest(
        category(
            category="macro",
            source_reference="https://example.test/private?api_key=secret",
        ),
    )

    assert len(result.derived_validation_digest) == 64
    assert len(result.rows[0].derived_validation_digest) == 64

    payload = module.strategy_market_category_capital_efficiency_digest_payload(result)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["rows"][0]["derived_validation_digest"] == (
        result.rows[0].derived_validation_digest
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result.rows[0], redacted_source_reference="plain-ticket")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)


def test_payload_revalidates_tampered_public_dataclass_derived_fields() -> None:
    module = api()
    result = digest(
        category(
            category="macro",
            source_reference="https://example.test/private?api_key=secret",
        ),
    )

    object.__setattr__(result.rows[0], "redacted_source_reference", "plain-ticket")

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_market_category_capital_efficiency_digest_payload(result)

    result = digest(category(category="macro"))
    object.__setattr__(result.rows[0], "liquidity_capacity_score", d("0.800000"))

    with pytest.raises(ValueError, match="efficiency_score|derived_validation_digest"):
        module.strategy_market_category_capital_efficiency_digest_payload(result)

    result = digest(category(category="macro"))
    object.__setattr__(result.rows[0], "liquidity_capacity_score", d("0.800000"))
    object.__setattr__(result.rows[0], "efficiency_score", d("0.683280"))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_market_category_capital_efficiency_digest_payload(result)


def test_public_payload_validator_rejects_unsafe_payloads() -> None:
    module = api()
    payload = module.strategy_market_category_capital_efficiency_digest_payload(
        digest(category()),
    )

    module.validate_strategy_market_category_capital_efficiency_digest_public_payload(
        payload,
    )
    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.validate_strategy_market_category_capital_efficiency_digest_public_payload(
            {**payload, "live_trading": "paper"},
        )
    with pytest.raises(ValueError, match="unsafe value"):
        module.validate_strategy_market_category_capital_efficiency_digest_public_payload(
            {**payload, "top_category": "wallet"},
        )
    with pytest.raises(ValueError, match="Decimal-derived"):
        module.validate_strategy_market_category_capital_efficiency_digest_public_payload(
            {**payload, "category_count": 1},
        )
    with pytest.raises(ValueError, match="readonly"):
        module.validate_strategy_market_category_capital_efficiency_digest_public_payload(
            {**payload, "readonly": False},
        )


def test_inputs_and_config_reject_non_decimal_subclasses_and_unsafe_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="expected_edge must be a Decimal"):
        category(expected_edge=0.1)
    with pytest.raises(ValueError, match="expected_edge must be exactly Decimal"):
        category(expected_edge=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="category must be a nonblank trimmed string"):
        category(category=_StringSubclass("macro"))
    with pytest.raises(ValueError, match="holding_period_days must be above zero"):
        category(holding_period_days=ZERO)
    with pytest.raises(ValueError, match="forecast_confidence must be between zero and one"):
        category(forecast_confidence=d("1.100000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        category(paper_only=False)
    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_market_category_capital_efficiency_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_report_dataclasses_are_frozen_and_datetimes_normalize_to_utc() -> None:
    result = digest(
        category(),
        generated_at=datetime(2026, 7, 3, 11, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.rows[0].paper_only is True
    assert result.rows[0].report_only is True
    assert result.rows[0].readonly is True

    with pytest.raises(FrozenInstanceError):
        result.rows[0].rank = d("99")

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        digest(category(), generated_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest(category(), generated_at=datetime(2026, 7, 3, 15, 0))

    with pytest.raises(ValueError, match="digest report must contain exact rows"):
        replace(result, rows=(object(),))


def test_public_dataclasses_are_frozen_phase1_records() -> None:
    module = api()

    for class_name in (
        "StrategyMarketCategoryCapitalEfficiencyDigestConfig",
        "StrategyMarketCategoryCapitalEfficiencyInput",
        "StrategyMarketCategoryCapitalEfficiencyDigestRow",
        "StrategyMarketCategoryCapitalEfficiencyDigestReport",
    ):
        cls = getattr(module, class_name)
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True


def test_module_is_pure_report_only_and_contains_no_io_or_trading_behavior() -> None:
    path = Path("src/polymarket_alpha_lab/strategy_market_category_capital_efficiency_digest.py")
    tree = ast.parse(path.read_text())

    banned_imports = {
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "psycopg",
    }
    banned_names = {
        "open",
        "connect",
        "cursor",
        "execute",
        "insert",
        "update",
        "delete",
        "create_order",
        "place_order",
        "submit_order",
        "trade",
        "auth",
        "login",
        "wallet",
        "order",
        "cancel",
        "replace",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_names
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_names
