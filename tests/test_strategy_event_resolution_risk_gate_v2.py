from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_event_resolution_risk_gate_v2.py"
)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_event_resolution_risk_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def input_row(**overrides: object) -> Any:
    module = api()
    values = {
        "market_slug": "resolution-market",
        "condition_id": "condition-alpha",
        "outcome_name": "yes",
        "base_recommendation_probability": d("0.650000"),
        "ambiguous_resolution_criteria_score": ZERO,
        "official_source_weakness_score": ZERO,
        "rule_change_risk_score": ZERO,
        "dispute_history_score": ZERO,
        "settlement_lag_risk_score": ZERO,
        "reason_codes": (),
    }
    values.update(overrides)
    return module.StrategyEventResolutionRiskGateV2Input(**values)


def report(**overrides: object) -> Any:
    module = api()
    return module.build_strategy_event_resolution_risk_gate_v2_report(
        input_row(**overrides),
    )


def assert_no_public_numeric_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_numeric_values(item)


def test_resolution_risk_gate_scores_inputs_into_recommendation_penalty() -> None:
    result = report(
        base_recommendation_probability=d("0.720000"),
        ambiguous_resolution_criteria_score=d("0.600000"),
        official_source_weakness_score=d("0.400000"),
        rule_change_risk_score=d("0.300000"),
        dispute_history_score=d("0.200000"),
        settlement_lag_risk_score=d("0.500000"),
    )

    assert is_dataclass(result)
    assert result.config_version == "strategy-event-resolution-risk-gate-v2"
    assert result.resolution_risk_score == d("0.415000")
    assert result.recommendation_penalty == d("0.145250")
    assert result.penalty_adjusted_probability == d("0.574750")
    assert result.gate_status == "watch"
    assert result.required_followups == (
        "clarify_resolution_criteria",
        "refresh_official_sources",
        "monitor_rule_change",
        "review_dispute_history",
        "track_settlement_lag",
    )
    assert result.reason_codes == (
        "ambiguous_resolution_criteria_watch",
        "official_source_weakness_watch",
        "rule_change_risk_watch",
        "dispute_history_watch",
        "settlement_lag_risk_watch",
        "recommendation_penalty_watch",
    )
    assert len(result.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in result.derived_validation_digest)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    for item in fields(result):
        value = getattr(result, item.name)
        if item.name.endswith(("_probability", "_score", "_penalty", "_risk")):
            assert type(value) is Decimal


def test_resolution_risk_gate_passes_clean_surface_and_blocks_severe_surface() -> None:
    clean = report()

    assert clean.resolution_risk_score == ZERO
    assert clean.recommendation_penalty == ZERO
    assert clean.penalty_adjusted_probability == d("0.650000")
    assert clean.gate_status == "pass"
    assert clean.required_followups == ()
    assert clean.reason_codes == ("event_resolution_risk_clear",)

    severe = report(
        base_recommendation_probability=d("0.200000"),
        ambiguous_resolution_criteria_score=d("1.000000"),
        official_source_weakness_score=d("1.000000"),
        rule_change_risk_score=d("1.000000"),
        dispute_history_score=d("1.000000"),
        settlement_lag_risk_score=d("1.000000"),
    )

    assert severe.resolution_risk_score == d("1.000000")
    assert severe.recommendation_penalty == d("0.350000")
    assert severe.penalty_adjusted_probability == ZERO
    assert severe.gate_status == "blocked"
    assert severe.required_followups == (
        "resolve_resolution_criteria",
        "replace_official_sources",
        "escalate_rule_change_review",
        "escalate_dispute_review",
        "plan_settlement_lag",
    )
    assert severe.reason_codes == (
        "ambiguous_resolution_criteria_high",
        "official_source_weakness_high",
        "rule_change_risk_high",
        "dispute_history_high",
        "settlement_lag_risk_high",
        "recommendation_penalty_blocked",
    )


def test_payload_uses_decimal_strings_safe_text_flags_and_validation_digest() -> None:
    module = api()
    result = report(
        market_slug="payload-market",
        condition_id="condition-payload",
        outcome_name="yes",
        base_recommendation_probability=d("0.720000"),
        ambiguous_resolution_criteria_score=d("0.600000"),
        official_source_weakness_score=d("0.400000"),
        rule_change_risk_score=d("0.300000"),
        dispute_history_score=d("0.200000"),
        settlement_lag_risk_score=d("0.500000"),
    )

    payload = module.strategy_event_resolution_risk_gate_v2_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert payload == result.payload
    assert payload["base_recommendation_probability"] == "0.720000"
    assert payload["resolution_risk_score"] == "0.415000"
    assert payload["recommendation_penalty"] == "0.145250"
    assert payload["penalty_adjusted_probability"] == "0.574750"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_values(payload)
    for unsafe in (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ):
        assert unsafe not in rendered.lower()


def test_validation_rejects_bad_inputs_flags_subclasses_and_tampering() -> None:
    module = api()

    with pytest.raises(ValueError, match="input"):
        module.build_strategy_event_resolution_risk_gate_v2_report(object())
    with pytest.raises(ValueError, match="market_slug"):
        input_row(market_slug="")
    with pytest.raises(ValueError, match="unsafe public text"):
        input_row(market_slug="live-market")
    with pytest.raises(ValueError, match="outcome_name"):
        input_row(outcome_name=" yes ")
    with pytest.raises(ValueError, match="base_recommendation_probability"):
        input_row(base_recommendation_probability=1)
    with pytest.raises(ValueError, match="base_recommendation_probability"):
        input_row(base_recommendation_probability=_DecimalSubclass("0.650000"))
    with pytest.raises(ValueError, match="ambiguous_resolution_criteria_score"):
        input_row(ambiguous_resolution_criteria_score=d("1.000001"))
    with pytest.raises(ValueError, match="official_source_weakness_score"):
        input_row(official_source_weakness_score=d("-0.000001"))
    with pytest.raises(ValueError, match="rule_change_risk_score"):
        input_row(rule_change_risk_score=d("0.1234567"))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=["manual_review"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unsafe public text"):
        input_row(reason_codes=("buy_signal",))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)

    result = report()
    with pytest.raises(FrozenInstanceError):
        result.gate_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, ambiguous_resolution_criteria_score=d("0.500000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)


def test_payload_rejects_tampered_digest_unsafe_public_keys_values_and_numbers() -> None:
    module = api()
    result = report()

    tampered_score = replace(result)
    object.__setattr__(tampered_score, "resolution_risk_score", d("0.999999"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_event_resolution_risk_gate_v2_payload(tampered_score)

    unsafe_key = replace(result)
    object.__setattr__(unsafe_key, "network_marker", "safe")
    with pytest.raises(ValueError, match="unsafe public text"):
        module.strategy_event_resolution_risk_gate_v2_payload(unsafe_key)

    unsafe_value = replace(result)
    object.__setattr__(unsafe_value, "safe_extra", "wallet-marker")
    with pytest.raises(ValueError, match="unsafe public text"):
        module.strategy_event_resolution_risk_gate_v2_payload(unsafe_value)

    unsafe_number = replace(result)
    object.__setattr__(unsafe_number, "safe_extra", 1)
    with pytest.raises(ValueError, match="public payload numeric"):
        module.strategy_event_resolution_risk_gate_v2_payload(unsafe_number)


def test_module_scope_has_no_live_surfaces_or_non_decimal_numeric_literals() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "float",
                "open",
                "connect",
                "execute",
                "fetch",
                "request",
                "submit",
            }

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }

    lowered = source.lower()
    for banned in (
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib",
        "websocket",
        "psycopg",
        "sqlite",
        "supabase",
        "private_key",
        "clob",
        "open(",
        "connect(",
        "execute(",
        "fetch(",
        "submit(",
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ):
        assert banned not in lowered
