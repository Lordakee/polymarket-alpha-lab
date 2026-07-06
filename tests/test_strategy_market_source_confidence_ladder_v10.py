import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_market_source_confidence_ladder_v10"


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(**overrides: object) -> Any:
    module = api()
    values = {
        "market_id": "market-alpha",
        "official_source_score": d("0.920000"),
        "primary_source_score": d("0.800000"),
        "secondary_source_score": d("0.630000"),
        "market_data_score": d("0.550000"),
        "source_dependency_penalty": d("0.030000"),
        "freshness_penalty": d("0.050000"),
    }
    values.update(overrides)
    return module.StrategyMarketSourceConfidenceLadderV10Input(**values)


def evaluate(item: Any | None = None) -> Any:
    module = api()
    return module.evaluate_strategy_market_source_confidence_ladder_v10(
        item or signal(),
    )


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float, field.name
        assert type(value) is not int, field.name


def assert_no_runtime_numeric(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    assert not isinstance(value, Decimal)
    if isinstance(value, dict):
        for child in value.values():
            assert_no_runtime_numeric(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_runtime_numeric(child)


def test_official_source_scores_trusted_confidence_ladder_payload() -> None:
    module = api()

    result = evaluate()

    assert isinstance(result, module.StrategyMarketSourceConfidenceLadderV10Report)
    assert is_dataclass(result)
    assert result.__dataclass_params__.frozen
    assert result.market_id == "market-alpha"
    assert result.official_source_score == d("0.920000")
    assert result.primary_source_score == d("0.800000")
    assert result.secondary_source_score == d("0.630000")
    assert result.market_data_score == d("0.550000")
    assert result.source_dependency_penalty == d("0.030000")
    assert result.freshness_penalty == d("0.050000")
    assert result.adjusted_confidence_score == d("0.840000")
    assert result.confidence_ladder_status == "trusted"
    assert result.confidence_level == "official"
    assert result.required_source_upgrade == "none"
    assert result.reason_codes == (
        "confidence_ladder_trusted",
        "freshness_penalty_clear",
        "official_source_verified",
        "source_dependency_penalty_clear",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)

    payload = module.strategy_market_source_confidence_ladder_v10_payload(result)
    json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload == result.payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["official_source_score"] == "0.920000"
    assert payload["adjusted_confidence_score"] == "0.840000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert_no_runtime_numeric(payload)
    assert module.strategy_market_source_confidence_ladder_v10_payload(payload) == payload


def test_secondary_and_market_data_only_inputs_require_source_upgrade() -> None:
    secondary = evaluate(
        signal(
            official_source_score=d("0.200000"),
            primary_source_score=d("0.300000"),
            secondary_source_score=d("0.680000"),
            market_data_score=d("0.610000"),
            source_dependency_penalty=d("0.100000"),
            freshness_penalty=d("0.050000"),
        ),
    )

    assert secondary.adjusted_confidence_score == d("0.530000")
    assert secondary.confidence_ladder_status == "upgrade_required"
    assert secondary.confidence_level == "secondary"
    assert secondary.required_source_upgrade == "official_or_primary_source"
    assert secondary.reason_codes == (
        "freshness_penalty_clear",
        "secondary_source_supported",
        "source_dependency_penalty_clear",
        "source_upgrade_required",
    )

    market_data_only = evaluate(
        signal(
            official_source_score=d("0.200000"),
            primary_source_score=d("0.300000"),
            secondary_source_score=d("0.400000"),
            market_data_score=d("0.620000"),
            source_dependency_penalty=d("0.040000"),
            freshness_penalty=d("0.030000"),
        ),
    )

    assert market_data_only.adjusted_confidence_score == d("0.550000")
    assert market_data_only.confidence_ladder_status == "upgrade_required"
    assert market_data_only.confidence_level == "market_data"
    assert market_data_only.required_source_upgrade == "primary_or_official_source"
    assert market_data_only.reason_codes == (
        "freshness_penalty_clear",
        "market_data_only_supported",
        "source_dependency_penalty_clear",
        "source_upgrade_required",
    )


def test_penalties_and_thin_sources_block_confidence_ladder() -> None:
    penalized = evaluate(
        signal(
            official_source_score=d("0.900000"),
            primary_source_score=d("0.850000"),
            secondary_source_score=d("0.800000"),
            market_data_score=d("0.750000"),
            source_dependency_penalty=d("0.300000"),
            freshness_penalty=d("0.250000"),
        ),
    )

    assert penalized.adjusted_confidence_score == d("0.350000")
    assert penalized.confidence_ladder_status == "blocked"
    assert penalized.confidence_level == "official"
    assert penalized.required_source_upgrade == "independent_fresh_source"
    assert penalized.reason_codes == (
        "freshness_penalty_high",
        "official_source_verified",
        "source_confidence_blocked",
        "source_dependency_penalty_high",
    )

    thin = evaluate(
        signal(
            official_source_score=d("0.200000"),
            primary_source_score=d("0.300000"),
            secondary_source_score=d("0.400000"),
            market_data_score=d("0.420000"),
        ),
    )

    assert thin.adjusted_confidence_score == d("0.340000")
    assert thin.confidence_ladder_status == "blocked"
    assert thin.confidence_level == "insufficient"
    assert thin.required_source_upgrade == "primary_or_official_source"
    assert thin.reason_codes == (
        "freshness_penalty_clear",
        "source_confidence_blocked",
        "source_confidence_insufficient",
        "source_dependency_penalty_clear",
    )


def test_inputs_report_payload_and_flags_validate_strict_decimal_surfaces() -> None:
    module = api()

    with pytest.raises(ValueError, match="official_source_score must be a Decimal"):
        signal(official_source_score=1)
    with pytest.raises(ValueError, match="official_source_score must be exactly Decimal"):
        signal(official_source_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="official_source_score must be between zero and one"):
        signal(official_source_score=d("1.100000"))
    with pytest.raises(ValueError, match="source_dependency_penalty must be between zero and one"):
        signal(source_dependency_penalty=d("-0.100000"))
    with pytest.raises(ValueError, match="market_id must be a nonblank trimmed string"):
        signal(market_id=" market-alpha")
    with pytest.raises(ValueError, match="input paper_only must be True"):
        signal(paper_only=False)

    result = evaluate()
    with pytest.raises(FrozenInstanceError):
        result.confidence_level = "secondary"  # type: ignore[misc]
    with pytest.raises(ValueError, match="confidence_ladder_status must match"):
        module.StrategyMarketSourceConfidenceLadderV10Report(
            **{**result.__dict__, "confidence_ladder_status": "blocked"},
        )
    with pytest.raises(ValueError, match="reason_codes must match"):
        module.StrategyMarketSourceConfidenceLadderV10Report(
            **{**result.__dict__, "reason_codes": ("source_confidence_blocked",)},
        )
    with pytest.raises(ValueError, match="report readonly must be True"):
        module.StrategyMarketSourceConfidenceLadderV10Report(
            **{**result.__dict__, "readonly": False},
        )

    payload = result.payload
    with pytest.raises(ValueError, match="readonly"):
        module.strategy_market_source_confidence_ladder_v10_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="float"):
        module.strategy_market_source_confidence_ladder_v10_payload(
            {**payload, "adjusted_confidence_score": 0.5},
        )
    with pytest.raises(ValueError, match="Decimal"):
        module.strategy_market_source_confidence_ladder_v10_payload(
            {**payload, "adjusted_confidence_score": 1},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_market_source_confidence_ladder_v10_payload(
            {**payload, "market_id": "https://example.test/source?token=secret"},
        )


def test_module_is_paper_report_readonly_with_no_external_side_effect_surface() -> None:
    path = Path("src/polymarket_alpha_lab/strategy_market_source_confidence_ladder_v10.py")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    banned_imports = {
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    banned_call_names = {
        "auth",
        "cancel",
        "connect",
        "create_order",
        "login",
        "open",
        "place_order",
        "replace",
        "submit_order",
        "trade",
        "wallet",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_call_names
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_call_names

    forbidden_terms = (
        "live trading",
        "authentication",
        "wallet",
        "durable file",
        "database",
        "supabase",
        "requests",
        "httpx",
        "socket",
        "subprocess",
    )
    lowered = source.lower()
    assert [term for term in forbidden_terms if term in lowered] == []
