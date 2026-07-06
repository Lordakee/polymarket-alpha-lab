from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.strategy_information_edge_decay_gate_v2",
    )


def gate_input(**overrides: Any):
    values: dict[str, Any] = {
        "signal_id": "signal-alpha",
        "market_slug": "market-alpha",
        "forecast_edge": d("0.080000"),
        "information_age_hours": d("0.000000"),
        "source_quality_score": d("1.000000"),
        "contradiction_severity_score": d("0.000000"),
        "official_source_lag_hours": d("0.000000"),
        "market_probability_move_without_evidence": d("0.000000"),
        "specialist_confidence_score": d("1.000000"),
    }
    values.update(overrides)
    return api().StrategyInformationEdgeDecayGateV2Input(**values)


def build(subject: object | None = None):
    return api().build_strategy_information_edge_decay_gate_v2(
        gate_input() if subject is None else subject,
    )


def assert_no_decimal_int_or_float_payload_values(value: Any) -> None:
    if type(value) in (Decimal, int, float):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_int_or_float_payload_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_decimal_int_or_float_payload_values(item)


def test_fresh_high_quality_signal_passes_with_full_edge_retained() -> None:
    module = api()

    result = build()

    assert result == module.StrategyInformationEdgeDecayGateV2Result(
        signal_id="signal-alpha",
        market_slug="market-alpha",
        forecast_edge=d("0.080000"),
        information_age_hours=d("0.000000"),
        source_quality_score=d("1.000000"),
        contradiction_severity_score=d("0.000000"),
        official_source_lag_hours=d("0.000000"),
        market_probability_move_without_evidence=d("0.000000"),
        specialist_confidence_score=d("1.000000"),
        freshness_factor=d("1.000000"),
        contradiction_factor=d("1.000000"),
        official_source_lag_factor=d("1.000000"),
        unsupported_move_factor=d("1.000000"),
        edge_decay_factor=d("1.000000"),
        decayed_forecast_edge=d("0.080000"),
        gate_status="pass",
        recommended_action="include_in_paper_report",
        required_followups=(),
        reason_codes=(
            "gate_status_pass",
            "freshness_clear",
            "source_quality_strong",
            "contradiction_clear",
            "official_lag_clear",
            "unsupported_move_clear",
            "specialist_confidence_strong",
            "edge_decay_factor_pass",
            "forecast_edge_retained",
        ),
        derived_validation_digest=result.derived_validation_digest,
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    for value in (
        result.forecast_edge,
        result.freshness_factor,
        result.contradiction_factor,
        result.official_source_lag_factor,
        result.unsupported_move_factor,
        result.edge_decay_factor,
        result.decayed_forecast_edge,
    ):
        assert type(value) is Decimal


def test_stale_lower_quality_conflicted_signal_decays_to_review() -> None:
    result = build(
        gate_input(
            signal_id="signal-review",
            information_age_hours=d("39.000000"),
            source_quality_score=d("0.750000"),
            contradiction_severity_score=d("0.250000"),
            official_source_lag_hours=d("38.000000"),
            market_probability_move_without_evidence=d("0.200000"),
            specialist_confidence_score=d("0.800000"),
        ),
    )

    assert result.freshness_factor == d("0.500000")
    assert result.contradiction_factor == d("0.750000")
    assert result.official_source_lag_factor == d("0.500000")
    assert result.unsupported_move_factor == d("0.800000")
    assert result.edge_decay_factor == d("0.090000")
    assert result.decayed_forecast_edge == d("0.007200")
    assert result.gate_status == "review"
    assert result.recommended_action == "review_before_paper_report"
    assert result.required_followups == (
        "refresh_information_timestamp",
        "improve_source_quality",
        "resolve_evidence_contradictions",
        "wait_for_official_source_update",
        "explain_probability_move_with_evidence",
        "raise_specialist_confidence",
    )
    assert result.reason_codes == (
        "gate_status_review",
        "freshness_watch",
        "source_quality_watch",
        "contradiction_watch",
        "official_lag_watch",
        "unsupported_move_watch",
        "specialist_confidence_watch",
        "edge_decay_factor_watch",
        "forecast_edge_reduced",
    )


def test_extreme_information_risks_block_and_clamp_decayed_edge() -> None:
    result = build(
        gate_input(
            signal_id="signal-blocked",
            information_age_hours=d("90.000000"),
            source_quality_score=d("0.200000"),
            contradiction_severity_score=d("1.000000"),
            official_source_lag_hours=d("90.000000"),
            market_probability_move_without_evidence=d("1.000000"),
            specialist_confidence_score=d("0.100000"),
        ),
    )

    assert result.freshness_factor == d("0.000000")
    assert result.contradiction_factor == d("0.000000")
    assert result.official_source_lag_factor == d("0.000000")
    assert result.unsupported_move_factor == d("0.000000")
    assert result.edge_decay_factor == d("0.000000")
    assert result.decayed_forecast_edge == d("0.000000")
    assert result.gate_status == "blocked"
    assert result.recommended_action == "exclude_from_paper_report"
    assert result.reason_codes == (
        "gate_status_blocked",
        "freshness_blocked",
        "source_quality_weak",
        "contradiction_severe",
        "official_lag_blocked",
        "unsupported_move_high",
        "specialist_confidence_weak",
        "edge_decay_factor_blocked",
        "forecast_edge_exhausted",
    )


def test_public_payload_serializes_decimal_as_strings_and_rejects_tampering() -> None:
    module = api()
    result = build(
        gate_input(
            signal_id="signal-payload",
            information_age_hours=d("39.000000"),
            source_quality_score=d("0.750000"),
            contradiction_severity_score=d("0.250000"),
            official_source_lag_hours=d("38.000000"),
            market_probability_move_without_evidence=d("0.200000"),
            specialist_confidence_score=d("0.800000"),
        ),
    )

    payload = module.strategy_information_edge_decay_gate_v2_payload(result)

    assert payload == result.payload
    assert payload["forecast_edge"] == "0.080000"
    assert payload["edge_decay_factor"] == "0.090000"
    assert payload["decayed_forecast_edge"] == "0.007200"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert type(payload["derived_validation_digest"]) is str
    assert len(payload["derived_validation_digest"]) == 64
    assert all(character in "0123456789abcdef" for character in payload["derived_validation_digest"])
    assert_no_decimal_int_or_float_payload_values(payload)

    restored = module.StrategyInformationEdgeDecayGateV2Result.from_payload(payload)
    assert restored == result

    tampered = dict(payload)
    tampered["decayed_forecast_edge"] = "0.070000"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.StrategyInformationEdgeDecayGateV2Result.from_payload(tampered)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(result, signal_id="signal-tampered")


def test_unsafe_public_keys_and_values_are_rejected() -> None:
    module = api()

    for forbidden_value in (
        "live surface",
        "auth callback",
        "wallet field",
        "order detail",
        "network call",
        "database row",
        "persist record",
        "signing request",
        "mutation path",
        "buy button",
        "sell action",
        "trade route",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            gate_input(market_slug=forbidden_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("payload", {"safe": {"wallet": "blocked"}})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("payload", {"safe": "database field"})


def test_validation_rejects_wrong_types_subclasses_bad_flags_and_mismatched_results() -> None:
    module = api()
    subject = gate_input()
    result = build(subject)

    class InputSubclass(module.StrategyInformationEdgeDecayGateV2Input):
        pass

    class ResultSubclass(module.StrategyInformationEdgeDecayGateV2Result):
        pass

    with pytest.raises(FrozenInstanceError):
        subject.signal_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.gate_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="signal_id must"):
        gate_input(signal_id=" signal-alpha ")
    with pytest.raises(ValueError, match="forecast_edge must be a Decimal"):
        gate_input(forecast_edge="0.080000")
    with pytest.raises(ValueError, match="forecast_edge must be nonnegative"):
        gate_input(forecast_edge=d("-0.010000"))
    with pytest.raises(ValueError, match="source_quality_score must be between"):
        gate_input(source_quality_score=d("1.000001"))
    with pytest.raises(ValueError, match="source_quality_score must not exceed six"):
        gate_input(source_quality_score=d("0.1234567"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        gate_input(paper_only=False)
    with pytest.raises(ValueError, match="subject must be"):
        build(object())
    with pytest.raises(ValueError, match="subject must be"):
        build(InputSubclass(**subject.__dict__))
    with pytest.raises(ValueError, match="result must be"):
        module.strategy_information_edge_decay_gate_v2_payload(object())
    with pytest.raises(ValueError, match="result must be"):
        ResultSubclass(**result.__dict__)
    with pytest.raises(ValueError, match="edge_decay_factor must match"):
        replace(result, edge_decay_factor=d("0.500000"))
    with pytest.raises(ValueError, match="decayed_forecast_edge must match"):
        replace(result, decayed_forecast_edge=d("0.010000"))
    with pytest.raises(ValueError, match="recommended_action must match"):
        replace(result, recommended_action="review_before_paper_report")
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(result, reason_codes=("gate_status_pass",))
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_module_is_decimal_only_report_only_and_unwired_from_unsafe_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)

    assert module.StrategyInformationEdgeDecayGateV2Input.__dataclass_params__.frozen
    assert module.StrategyInformationEdgeDecayGateV2Result.__dataclass_params__.frozen
    assert module.__all__ == (
        "GATE_STATUSES",
        "RECOMMENDED_ACTIONS",
        "REQUIRED_FOLLOWUPS",
        "REASON_CODES",
        "StrategyInformationEdgeDecayGateV2Input",
        "StrategyInformationEdgeDecayGateV2Result",
        "build_strategy_information_edge_decay_gate_v2",
        "strategy_information_edge_decay_gate_v2_payload",
    )

    forbidden_import_roots = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "supabase",
    )
    forbidden_call_names = {
        "authenticate",
        "cancel_order",
        "create_order",
        "open",
        "place_order",
        "read_text",
        "submit_order",
        "write_text",
    }

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", *forbidden_call_names}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_call_names

    assert {name.split(".", 1)[0] for name in imported_modules}.isdisjoint(
        forbidden_import_roots,
    )
    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }
