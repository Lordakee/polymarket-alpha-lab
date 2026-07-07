from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_recommendation_price_limit_safety_band_v2"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_recommendation_price_limit_safety_band_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "phase1_price_limit_safety_band_v2"


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": CONFIG_VERSION,
        "fee_slippage_buffer": d("0.010000"),
        "spread_buffer": d("0.015000"),
        "stale_source_penalty": d("0.030000"),
        "max_fair_probability_age_seconds": d("600.000000"),
        "abstain_band": d("0.005000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationPriceLimitSafetyBandV2Config(**values)


def recommendation(**overrides: object) -> Any:
    module = api()
    values = {
        "recommendation_id": "rec-alpha",
        "market_slug": "market-alpha",
        "target_side": "yes",
        "fair_probability": d("0.650000"),
        "quoted_price": d("0.610000"),
        "fair_probability_observed_at": GENERATED_AT - timedelta(seconds=120),
    }
    values.update(overrides)
    return module.StrategyRecommendationPriceLimitSafetyBandV2Recommendation(**values)


def report(candidate: Any | None = None, cfg: Any | None = None, **overrides: object) -> Any:
    module = api()
    return module.build_strategy_recommendation_price_limit_safety_band_v2_report(
        candidate or recommendation(**overrides),
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def assert_no_native_numeric_or_decimal_values(value: Any) -> None:
    if type(value) in (int, float) or isinstance(value, Decimal):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_native_numeric_or_decimal_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_native_numeric_or_decimal_values(item)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def payload_digest(payload: dict[str, Any]) -> str:
    digest_source = {
        key: item
        for key, item in payload.items()
        if key != "derived_validation_digest"
    }
    return hashlib.sha256(
        json.dumps(
            digest_source,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def test_builds_decimal_only_report_with_price_limits_payload_and_digest() -> None:
    module = api()
    result = report()

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == CONFIG_VERSION
    assert result.recommendation_id == "rec-alpha"
    assert result.market_slug == "market-alpha"
    assert result.target_side == "yes"
    assert result.fair_probability == d("0.650000")
    assert result.side_fair_probability == d("0.650000")
    assert result.quoted_price == d("0.610000")
    assert result.source_age_seconds == d("120.000000")
    assert result.applied_stale_source_penalty == d("0.000000")
    assert result.total_safety_buffer == d("0.030000")
    assert result.max_acceptable_price == d("0.620000")
    assert result.min_acceptable_price == d("0.680000")
    assert result.price_edge_to_max == d("0.010000")
    assert result.price_distance_to_fair == d("0.040000")
    assert result.price_status == "price_limit_pass"
    assert result.source_status == "source_fresh"
    assert result.report_status == "paper_price_limit_pass"
    assert result.reason_codes == (
        "fee_slippage_buffer_applied",
        "spread_buffer_applied",
        "abstain_band_applied",
        "source_fresh",
        "price_at_or_below_max_acceptable",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.derived_validation_digest)

    payload = module.strategy_recommendation_price_limit_safety_band_v2_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-06T12:00:00Z"
    assert payload["fair_probability"] == "0.650000"
    assert payload["side_fair_probability"] == "0.650000"
    assert payload["total_safety_buffer"] == "0.030000"
    assert payload["max_acceptable_price"] == "0.620000"
    assert payload["min_acceptable_price"] == "0.680000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "wallet" not in encoded.lower()
    assert_no_native_numeric_or_decimal_values(payload)
    assert module.strategy_recommendation_price_limit_safety_band_v2_payload(payload) == payload


def test_no_side_uses_complement_probability_and_applies_stale_source_penalty() -> None:
    result = report(
        recommendation(
            target_side="no",
            fair_probability=d("0.350000"),
            quoted_price=d("0.580000"),
            fair_probability_observed_at=GENERATED_AT - timedelta(seconds=720),
        ),
    )

    assert result.target_side == "no"
    assert result.fair_probability == d("0.350000")
    assert result.side_fair_probability == d("0.650000")
    assert result.source_age_seconds == d("720.000000")
    assert result.applied_stale_source_penalty == d("0.030000")
    assert result.total_safety_buffer == d("0.060000")
    assert result.max_acceptable_price == d("0.590000")
    assert result.min_acceptable_price == d("0.710000")
    assert result.price_edge_to_max == d("0.010000")
    assert result.price_status == "price_limit_pass"
    assert result.source_status == "source_stale"
    assert result.report_status == "paper_price_limit_watch"
    assert result.reason_codes == (
        "fee_slippage_buffer_applied",
        "spread_buffer_applied",
        "stale_source_penalty_applied",
        "abstain_band_applied",
        "price_at_or_below_max_acceptable",
    )


def test_quote_inside_abstain_band_reports_abstain() -> None:
    result = report(quoted_price=d("0.650000"))

    assert result.max_acceptable_price == d("0.620000")
    assert result.min_acceptable_price == d("0.680000")
    assert result.price_edge_to_max == d("-0.030000")
    assert result.price_status == "price_limit_abstain"
    assert result.source_status == "source_fresh"
    assert result.report_status == "paper_price_limit_abstain"
    assert result.reason_codes == (
        "fee_slippage_buffer_applied",
        "spread_buffer_applied",
        "abstain_band_applied",
        "source_fresh",
        "price_inside_abstain_band",
    )


def test_quote_above_min_acceptable_reports_reject() -> None:
    result = report(quoted_price=d("0.700000"))

    assert result.max_acceptable_price == d("0.620000")
    assert result.min_acceptable_price == d("0.680000")
    assert result.price_edge_to_max == d("-0.080000")
    assert result.price_distance_to_fair == d("0.050000")
    assert result.price_status == "price_limit_reject"
    assert result.report_status == "paper_price_limit_reject"
    assert "price_above_min_acceptable" in result.reason_codes


def test_frozen_dataclasses_decimal_only_flags_and_validation() -> None:
    module = api()
    result = report()

    assert is_dataclass(module.StrategyRecommendationPriceLimitSafetyBandV2Config)
    assert is_dataclass(module.StrategyRecommendationPriceLimitSafetyBandV2Recommendation)
    assert is_dataclass(module.StrategyRecommendationPriceLimitSafetyBandV2Report)
    assert module.__all__ == (
        "StrategyRecommendationPriceLimitSafetyBandV2Config",
        "StrategyRecommendationPriceLimitSafetyBandV2Recommendation",
        "StrategyRecommendationPriceLimitSafetyBandV2Report",
        "build_strategy_recommendation_price_limit_safety_band_v2_report",
        "strategy_recommendation_price_limit_safety_band_v2_payload",
        "validate_strategy_recommendation_price_limit_safety_band_v2_public_payload",
    )

    with pytest.raises(FrozenInstanceError):
        result.max_acceptable_price = d("0.010000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        recommendation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="fair_probability"):
        recommendation(fair_probability=0.65)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="quoted_price"):
        recommendation(quoted_price=_DecimalSubclass("0.610000"))
    with pytest.raises(ValueError, match="fair_probability_observed_at"):
        recommendation(
            fair_probability_observed_at=_DatetimeSubclass(2026, 7, 6, 12, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_strategy_recommendation_price_limit_safety_band_v2_report(
            recommendation(),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )
    with pytest.raises(ValueError, match="future"):
        report(
            fair_probability_observed_at=GENERATED_AT + timedelta(seconds=1),
        )
    with pytest.raises(ValueError, match="max_acceptable_price"):
        replace(result, max_acceptable_price=result.max_acceptable_price + d("0.000001"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)

    for value in (result,):
        for field in fields(value):
            item_value = getattr(value, field.name)
            if field.name.endswith(
                (
                    "_band",
                    "_buffer",
                    "_penalty",
                    "_price",
                    "_probability",
                    "_seconds",
                    "_to_fair",
                    "_to_max",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_validation_rejects_tampering_and_native_numbers() -> None:
    module = api()
    payload = module.strategy_recommendation_price_limit_safety_band_v2_payload(report())

    tampered_price = {**payload, "max_acceptable_price": "0.999999"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_recommendation_price_limit_safety_band_v2_payload(tampered_price)

    with pytest.raises(ValueError, match="paper_only"):
        module.strategy_recommendation_price_limit_safety_band_v2_payload(
            {**payload, "paper_only": False},
        )
    with pytest.raises(ValueError, match="numeric"):
        module.strategy_recommendation_price_limit_safety_band_v2_payload(
            {**payload, "quoted_price": 0.61},
        )
    with pytest.raises(ValueError, match="numeric"):
        module.validate_strategy_recommendation_price_limit_safety_band_v2_public_payload(
            {**payload, "quoted_price": d("0.610000")},
        )
    with pytest.raises(ValueError, match="unsafe"):
        recommendation(market_slug="wallet-market")
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_recommendation_price_limit_safety_band_v2_payload(
            {**payload, "wallet_reference": "none"},
        )


def test_payload_validation_rejects_digest_valid_payload_with_missing_schema() -> None:
    module = api()
    payload = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload["derived_validation_digest"] = payload_digest(payload)

    with pytest.raises(ValueError, match="missing required fields"):
        module.validate_strategy_recommendation_price_limit_safety_band_v2_public_payload(
            payload,
        )


def test_payload_validation_rejects_digest_valid_non_decimal_strings() -> None:
    module = api()
    payload = module.strategy_recommendation_price_limit_safety_band_v2_payload(report())
    payload = {**payload, "quoted_price": "not-a-decimal"}
    payload["derived_validation_digest"] = payload_digest(payload)

    with pytest.raises(ValueError, match="quoted_price"):
        module.validate_strategy_recommendation_price_limit_safety_band_v2_public_payload(
            payload,
        )


def test_module_scope_has_no_io_network_auth_wallet_order_or_persistence_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_modules: list[str] = []
    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "db",
        "http",
        "network",
        "psycopg",
        "request",
        "socket",
        "sql",
        "sqlite",
        "subprocess",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "connect",
        "execute",
        "fetch",
        "request",
        "get",
        "post",
        "put",
        "delete",
        "submit",
        "cancel",
        "sign",
        "write",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "file",
        "network",
        "order",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imported_modules
    for module_name in imported_modules:
        lowered = module_name.lower()
        assert not module_name.startswith("polymarket_alpha_lab.")
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)
