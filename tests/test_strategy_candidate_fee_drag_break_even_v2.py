from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_fee_drag_break_even_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "candidate_id": "candidate-fee-drag-break-even-v2",
        "expected_probability": d("0.640000"),
        "market_probability": d("0.600000"),
        "taker_fee_probability_delta": d("0.010000"),
        "spread_probability_delta": d("0.006000"),
        "slippage_probability_delta": d("0.004000"),
        "settlement_lag_days": d("14"),
        "annualized_capital_drag_rate": d("0.120000"),
        "liquidity_depth_usd": d("250.000000"),
        "minimum_liquidity_depth_usd": d("1000.000000"),
        "liquidity_haircut_probability_delta": d("0.020000"),
        "minimum_actionable_edge_probability_delta": d("0.005000"),
        "reason_codes": ("research_signal_present",),
    }
    values.update(overrides)
    return module.StrategyCandidateFeeDragBreakEvenV2Input(**values)


def score(subject: object | None = None):
    module = api()
    return module.estimate_strategy_candidate_fee_drag_break_even_v2(
        score_input() if subject is None else subject,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_fee_drag_break_even_score_accounts_for_all_phase1_drags() -> None:
    module = api()

    result = score()

    assert result == module.StrategyCandidateFeeDragBreakEvenV2Result(
        candidate_id="candidate-fee-drag-break-even-v2",
        expected_probability=d("0.640000"),
        market_probability=d("0.600000"),
        gross_edge_probability_delta=d("0.040000"),
        taker_fee_probability_delta=d("0.010000"),
        spread_probability_delta=d("0.006000"),
        slippage_probability_delta=d("0.004000"),
        direct_cost_probability_delta=d("0.020000"),
        settlement_lag_days=d("14"),
        annualized_capital_drag_rate=d("0.120000"),
        settlement_lag_capital_drag_probability_delta=d("0.002762"),
        liquidity_depth_usd=d("250.000000"),
        minimum_liquidity_depth_usd=d("1000.000000"),
        liquidity_shortfall_ratio=d("0.750000"),
        liquidity_haircut_probability_delta=d("0.020000"),
        liquidity_haircut_applied_probability_delta=d("0.015000"),
        total_drag_probability_delta=d("0.037762"),
        break_even_probability=d("0.637762"),
        net_break_even_edge_probability_delta=d("0.002238"),
        minimum_actionable_edge_probability_delta=d("0.005000"),
        score_status="watch",
        score_decision="manual_review",
        reason_codes=(
            "research_signal_present",
            "strategy_candidate_fee_drag_break_even_v2",
            "score_watch",
            "edge_positive",
            "taker_fee_drag_applied",
            "spread_drag_applied",
            "slippage_drag_applied",
            "settlement_lag_capital_drag_applied",
            "liquidity_haircut_applied",
            "net_edge_positive_below_minimum",
        ),
        derived_validation_digest=(
            "bbcb0bbfe35fd58f5467be5da10dc4552fa8b354dc89d7c5bfe10c4806a60ad9"
        ),
    )
    assert type(result.net_break_even_edge_probability_delta) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_candidate_when_net_break_even_edge_clears_action_band() -> None:
    result = score(
        score_input(
            expected_probability=d("0.680000"),
            market_probability=d("0.600000"),
            taker_fee_probability_delta=d("0.005000"),
            spread_probability_delta=d("0.005000"),
            slippage_probability_delta=d("0.002000"),
            settlement_lag_days=d("7"),
            annualized_capital_drag_rate=d("0.050000"),
            liquidity_depth_usd=d("2000.000000"),
            minimum_liquidity_depth_usd=d("1000.000000"),
            liquidity_haircut_probability_delta=d("0.010000"),
            minimum_actionable_edge_probability_delta=d("0.050000"),
            reason_codes=(),
        ),
    )

    assert result.gross_edge_probability_delta == d("0.080000")
    assert result.direct_cost_probability_delta == d("0.012000")
    assert result.settlement_lag_capital_drag_probability_delta == d("0.000575")
    assert result.liquidity_shortfall_ratio == d("0.000000")
    assert result.liquidity_haircut_applied_probability_delta == d("0.000000")
    assert result.total_drag_probability_delta == d("0.012575")
    assert result.break_even_probability == d("0.612575")
    assert result.net_break_even_edge_probability_delta == d("0.067425")
    assert result.score_status == "candidate"
    assert result.score_decision == "paper_candidate"
    assert result.reason_codes == (
        "strategy_candidate_fee_drag_break_even_v2",
        "score_candidate",
        "edge_positive",
        "taker_fee_drag_applied",
        "spread_drag_applied",
        "slippage_drag_applied",
        "settlement_lag_capital_drag_applied",
        "minimum_actionable_edge_met",
    )


def test_blocked_when_phase1_drags_exceed_gross_edge() -> None:
    result = score(
        score_input(
            expected_probability=d("0.610000"),
            market_probability=d("0.600000"),
            taker_fee_probability_delta=d("0.005000"),
            spread_probability_delta=d("0.004000"),
            slippage_probability_delta=d("0.003000"),
            settlement_lag_days=d("0"),
            annualized_capital_drag_rate=d("0.000000"),
            liquidity_depth_usd=d("1000.000000"),
            minimum_liquidity_depth_usd=d("1000.000000"),
            liquidity_haircut_probability_delta=d("0.010000"),
            minimum_actionable_edge_probability_delta=d("0.005000"),
            reason_codes=(),
        ),
    )

    assert result.gross_edge_probability_delta == d("0.010000")
    assert result.total_drag_probability_delta == d("0.012000")
    assert result.net_break_even_edge_probability_delta == d("-0.002000")
    assert result.score_status == "blocked"
    assert result.score_decision == "reject"
    assert "net_edge_below_zero" in result.reason_codes


def test_result_rejects_reason_codes_that_do_not_match_derived_fields() -> None:
    module = api()
    result = score()
    mismatched_reason_codes = tuple(
        "score_candidate" if reason_code == "score_watch" else reason_code
        for reason_code in result.reason_codes
    )

    with pytest.raises(ValueError, match="reason_codes must match"):
        module.StrategyCandidateFeeDragBreakEvenV2Result(
            **{
                **public_field_values(result),
                "reason_codes": mismatched_reason_codes,
                "derived_validation_digest": "",
            },
        )


def test_payload_serializes_decimals_as_strings_and_revalidates_digest() -> None:
    module = api()
    result = score()
    payload = result.payload

    assert payload == module.strategy_candidate_fee_drag_break_even_v2_payload(result)
    assert payload["net_break_even_edge_probability_delta"] == "0.002238"
    assert payload["settlement_lag_days"] == "14"
    assert payload["liquidity_shortfall_ratio"] == "0.750000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_candidate_fee_drag_break_even_v2_payload(result)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    subject = score_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.StrategyCandidateFeeDragBreakEvenV2Input.__dataclass_params__.frozen
    assert module.StrategyCandidateFeeDragBreakEvenV2Result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.candidate_id = "other-candidate"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.score_status = "candidate"  # type: ignore[misc]

    for instance in (subject, result):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="expected_probability must be a Decimal"):
        score_input(expected_probability=120)
    with pytest.raises(ValueError, match="candidate_id must be a canonical"):
        score_input(candidate_id=" candidate-fee-drag-break-even-v2")
    with pytest.raises(ValueError, match="market_probability must be between"):
        score_input(market_probability=d("1.000001"))
    with pytest.raises(ValueError, match="settlement_lag_days must be integral"):
        score_input(settlement_lag_days=d("1.500000"))
    with pytest.raises(ValueError, match="minimum_liquidity_depth_usd must be positive"):
        score_input(minimum_liquidity_depth_usd=d("0.000000"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["research_signal_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="score_input"):
        score(object())

    rebuilt = module.StrategyCandidateFeeDragBreakEvenV2Result(
        **public_field_values(result),
    )
    assert rebuilt == result


def test_rejects_digest_tampering_and_unsafe_public_payload_keys_and_values() -> None:
    module = api()
    result = score()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.StrategyCandidateFeeDragBreakEvenV2Result(
            **{
                **public_field_values(result),
                "derived_validation_digest": "0" * 64,
            },
        )

    unsafe_terms = (
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
    )
    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            score_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_strategy_candidate_fee_drag_break_even_v2_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_strategy_candidate_fee_drag_break_even_v2_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/strategy_candidate_fee_drag_break_even_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    unsafe_surface_terms = (
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "wallet",
        " auth",
        "buy",
        "sell",
        "trade",
        "live",
    )
    for term in unsafe_surface_terms:
        assert term not in lowered

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }
    assert module.__all__ == (
        "SCORE_STATUSES",
        "SCORE_DECISIONS",
        "StrategyCandidateFeeDragBreakEvenV2Input",
        "StrategyCandidateFeeDragBreakEvenV2Result",
        "estimate_strategy_candidate_fee_drag_break_even_v2",
        "strategy_candidate_fee_drag_break_even_v2_payload",
        "reject_strategy_candidate_fee_drag_break_even_v2_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "strategy_candidate_fee_drag_break_even_v2" not in getattr(
        root,
        "__all__",
        (),
    )
