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
        "polymarket_alpha_lab.strategy_candidate_expected_value_decay_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "candidate_id": "candidate-ev-decay-v2",
        "current_expected_value_bps": d("120.000000"),
        "previous_expected_value_bps": d("160.000000"),
        "peak_expected_value_bps": d("200.000000"),
        "edge_half_life_seconds": d("900"),
        "stale_quote_age_seconds": d("1200"),
        "liquidity_depth_usd": d("250.000000"),
        "minimum_liquidity_depth_usd": d("1000.000000"),
        "fee_bps": d("20.000000"),
        "spread_bps": d("30.000000"),
        "slippage_bps": d("40.000000"),
        "minimum_actionable_score": d("50.000000"),
        "reason_codes": ("research_signal_present",),
    }
    values.update(overrides)
    return module.StrategyCandidateExpectedValueDecayScoreV2Input(**values)


def score(subject: object | None = None):
    module = api()
    return module.estimate_strategy_candidate_expected_value_decay_score_v2(
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


def test_ev_decay_score_penalizes_decay_staleness_liquidity_and_costs() -> None:
    module = api()

    result = score()

    assert result == module.StrategyCandidateExpectedValueDecayScoreV2Result(
        candidate_id="candidate-ev-decay-v2",
        current_expected_value_bps=d("120.000000"),
        previous_expected_value_bps=d("160.000000"),
        peak_expected_value_bps=d("200.000000"),
        ev_delta_bps=d("-40.000000"),
        ev_decay_from_peak_bps=d("80.000000"),
        ev_decay_ratio=d("0.400000"),
        edge_half_life_seconds=d("900"),
        stale_quote_age_seconds=d("1200"),
        stale_edge_penalty_bps=d("35.000000"),
        liquidity_depth_usd=d("250.000000"),
        minimum_liquidity_depth_usd=d("1000.000000"),
        liquidity_damping_bps=d("75.000000"),
        fee_bps=d("20.000000"),
        spread_bps=d("30.000000"),
        slippage_bps=d("40.000000"),
        total_cost_bps=d("90.000000"),
        raw_decay_adjusted_edge_bps=d("40.000000"),
        paper_score_bps=d("-160.000000"),
        minimum_actionable_score=d("50.000000"),
        score_status="blocked",
        score_decision="reject",
        reason_codes=(
            "research_signal_present",
            "strategy_candidate_expected_value_decay_score_v2",
            "score_blocked",
            "edge_positive",
            "ev_decay_from_peak_detected",
            "stale_edge_penalty_applied",
            "liquidity_damping_applied",
            "cost_damping_applied",
            "score_below_zero",
        ),
        derived_validation_digest=(
            "2793c7e0f08c230f05e1758892470f3259ac5dc09c80789c48511073633871bd"
        ),
    )
    assert type(result.paper_score_bps) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_candidate_when_decay_adjusted_score_clears_threshold() -> None:
    result = score(
        score_input(
            current_expected_value_bps=d("240.000000"),
            previous_expected_value_bps=d("250.000000"),
            peak_expected_value_bps=d("260.000000"),
            edge_half_life_seconds=d("1200"),
            stale_quote_age_seconds=d("300"),
            liquidity_depth_usd=d("2000.000000"),
            minimum_liquidity_depth_usd=d("1000.000000"),
            fee_bps=d("5.000000"),
            spread_bps=d("10.000000"),
            slippage_bps=d("5.000000"),
            minimum_actionable_score=d("100.000000"),
            reason_codes=(),
        ),
    )

    assert result.ev_delta_bps == d("-10.000000")
    assert result.ev_decay_from_peak_bps == d("20.000000")
    assert result.ev_decay_ratio == d("0.076923")
    assert result.stale_edge_penalty_bps == d("0.000000")
    assert result.liquidity_damping_bps == d("0.000000")
    assert result.total_cost_bps == d("20.000000")
    assert result.raw_decay_adjusted_edge_bps == d("220.000000")
    assert result.paper_score_bps == d("200.000000")
    assert result.score_status == "candidate"
    assert result.score_decision == "paper_candidate"
    assert result.reason_codes == (
        "strategy_candidate_expected_value_decay_score_v2",
        "score_candidate",
        "edge_positive",
        "ev_decay_from_peak_detected",
        "cost_damping_applied",
        "minimum_actionable_score_met",
    )


def test_watch_when_score_is_positive_but_below_threshold() -> None:
    result = score(
        score_input(
            current_expected_value_bps=d("150.000000"),
            previous_expected_value_bps=d("150.000000"),
            peak_expected_value_bps=d("150.000000"),
            edge_half_life_seconds=d("600"),
            stale_quote_age_seconds=d("600"),
            liquidity_depth_usd=d("1000.000000"),
            minimum_liquidity_depth_usd=d("1000.000000"),
            fee_bps=d("20.000000"),
            spread_bps=d("15.000000"),
            slippage_bps=d("15.000000"),
            minimum_actionable_score=d("120.000000"),
            reason_codes=(),
        ),
    )

    assert result.ev_decay_from_peak_bps == d("0.000000")
    assert result.raw_decay_adjusted_edge_bps == d("150.000000")
    assert result.paper_score_bps == d("100.000000")
    assert result.score_status == "watch"
    assert result.score_decision == "manual_review"
    assert "score_positive_below_minimum" in result.reason_codes


def test_payload_serializes_decimals_as_strings_and_revalidates_digest() -> None:
    module = api()
    result = score()
    payload = result.payload

    assert payload == module.strategy_candidate_expected_value_decay_score_v2_payload(
        result,
    )
    assert payload["paper_score_bps"] == "-160.000000"
    assert payload["ev_decay_ratio"] == "0.400000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_candidate_expected_value_decay_score_v2_payload(result)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    subject = score_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.StrategyCandidateExpectedValueDecayScoreV2Input.__dataclass_params__.frozen
    assert module.StrategyCandidateExpectedValueDecayScoreV2Result.__dataclass_params__.frozen

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

    with pytest.raises(ValueError, match="current_expected_value_bps must be a Decimal"):
        score_input(current_expected_value_bps=120)
    with pytest.raises(ValueError, match="candidate_id must be a canonical"):
        score_input(candidate_id=" candidate-ev-decay-v2")
    with pytest.raises(ValueError, match="edge_half_life_seconds must be positive"):
        score_input(edge_half_life_seconds=d("0"))
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

    rebuilt = module.StrategyCandidateExpectedValueDecayScoreV2Result(
        **public_field_values(result),
    )
    assert rebuilt == result


def test_rejects_digest_tampering_and_unsafe_public_payload_keys_and_values() -> None:
    module = api()
    result = score()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.StrategyCandidateExpectedValueDecayScoreV2Result(
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
            module.reject_strategy_candidate_expected_value_decay_score_v2_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_strategy_candidate_expected_value_decay_score_v2_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/strategy_candidate_expected_value_decay_score_v2.py",
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
        "StrategyCandidateExpectedValueDecayScoreV2Input",
        "StrategyCandidateExpectedValueDecayScoreV2Result",
        "estimate_strategy_candidate_expected_value_decay_score_v2",
        "strategy_candidate_expected_value_decay_score_v2_payload",
        "reject_strategy_candidate_expected_value_decay_score_v2_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "strategy_candidate_expected_value_decay_score_v2" not in getattr(
        root,
        "__all__",
        (),
    )
