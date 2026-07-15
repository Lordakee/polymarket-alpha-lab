from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_cost_adjusted_position_recommendation_report import (
    PROBABILITY_EVENT_COST_ADJUSTED_POSITION_RECOMMENDATION_REPORT_VERSION,
    ProbabilityEventCostAdjustedPositionRecommendationInput,
    ProbabilityEventCostAdjustedPositionRecommendationReport,
    build_probability_event_cost_adjusted_position_recommendation_report,
    probability_event_cost_adjusted_position_recommendation_report_digest,
    probability_event_cost_adjusted_position_recommendation_report_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_cost_adjusted_position_recommendation_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def recommendation_input(
    **overrides: object,
) -> ProbabilityEventCostAdjustedPositionRecommendationInput:
    values = {
        "event_id": "event-001",
        "market_slug": "fomc-july-2026",
        "outcome_side": "yes",
        "forecast_probability": d("0.620000"),
        "market_probability": d("0.540000"),
        "taker_fee_probability": d("0.010000"),
        "spread_probability": d("0.012000"),
        "slippage_probability": d("0.003000"),
        "settlement_delay_days": d("37.000000"),
        "annual_capital_charge_probability": d("0.100000"),
        "uncertainty_buffer_probability": d("0.020000"),
        "manual_fraction_cap_probability": d("0.050000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ProbabilityEventCostAdjustedPositionRecommendationInput(**values)


def report(
    **overrides: object,
) -> ProbabilityEventCostAdjustedPositionRecommendationReport:
    return build_probability_event_cost_adjusted_position_recommendation_report(
        recommendation_input(**overrides),
    )


def test_pass_report_calculates_cost_adjusted_break_even_ev_margin_kelly_and_lockup_hint() -> None:
    first = report(settlement_delay_days=d("7.000000"))
    second = report(settlement_delay_days=d("7.000000"))

    assert type(first) is ProbabilityEventCostAdjustedPositionRecommendationReport
    assert is_dataclass(first)
    assert first.__dataclass_params__.frozen is True
    assert (
        first.config_version
        == PROBABILITY_EVENT_COST_ADJUSTED_POSITION_RECOMMENDATION_REPORT_VERSION
    )
    assert first.readiness_status == "pass"
    assert first.capital_lockup_hint == "standard_capital_lockup_review"
    assert first.capital_lockup_cost_probability == d("0.001036")
    assert first.cost_adjusted_break_even_probability == d("0.566036")
    assert first.expected_value_probability == d("0.053964")
    assert first.margin_of_safety_probability == d("0.033964")
    assert first.kelly_upper_bound_probability == d("0.124351")
    assert first.recommended_position_fraction_probability == d("0.050000")
    assert first.reason_codes == (
        "cost_adjusted_expected_value_positive",
        "margin_of_safety_positive",
        "kelly_upper_bound_manual_cap_applied",
        "capital_lockup_cost_present",
    )
    assert first.manual_next_step == "document_phase1_readonly_position_boundary"
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second

    payload = probability_event_cost_adjusted_position_recommendation_report_payload(first)
    assert payload == first.public_payload
    assert payload == {
        "config_version": "probability-event-cost-adjusted-position-recommendation-v0",
        "event_id": "event-001",
        "market_slug": "fomc-july-2026",
        "outcome_side": "yes",
        "readiness_status": "pass",
        "forecast_probability": "0.620000",
        "market_probability": "0.540000",
        "taker_fee_probability": "0.010000",
        "spread_probability": "0.012000",
        "slippage_probability": "0.003000",
        "settlement_delay_days": "7.000000",
        "annual_capital_charge_probability": "0.100000",
        "capital_lockup_cost_probability": "0.001036",
        "cost_adjusted_break_even_probability": "0.566036",
        "expected_value_probability": "0.053964",
        "uncertainty_buffer_probability": "0.020000",
        "margin_of_safety_probability": "0.033964",
        "kelly_upper_bound_probability": "0.124351",
        "manual_fraction_cap_probability": "0.050000",
        "recommended_position_fraction_probability": "0.050000",
        "capital_lockup_hint": "standard_capital_lockup_review",
        "reason_codes": first.reason_codes,
        "manual_next_step": "document_phase1_readonly_position_boundary",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": first.payload_digest,
    }
    expected_digest = sha256(
        json.dumps(
            {**payload, "payload_digest": ""},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    assert first.payload_digest == expected_digest
    assert (
        probability_event_cost_adjusted_position_recommendation_report_digest(first)
        == expected_digest
    )
    assert _float_or_int_paths(payload) == ()
    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["readiness_status"] = "blocked"


def test_public_payload_property_revalidates_report_consistency_and_digest() -> None:
    inconsistent = report()
    object.__setattr__(
        inconsistent,
        "cost_adjusted_break_even_probability",
        d("0.560000"),
    )
    for export in (
        lambda: inconsistent.public_payload,
        lambda: probability_event_cost_adjusted_position_recommendation_report_payload(
            inconsistent,
        ),
    ):
        with pytest.raises(ValueError, match="cost_adjusted_break_even_probability"):
            export()

    digest_tampered = report()
    object.__setattr__(digest_tampered, "payload_digest", "0" * 64)
    for export in (
        lambda: digest_tampered.public_payload,
        lambda: probability_event_cost_adjusted_position_recommendation_report_payload(
            digest_tampered,
        ),
        lambda: probability_event_cost_adjusted_position_recommendation_report_digest(
            digest_tampered,
        ),
    ):
        with pytest.raises(ValueError, match="payload_digest"):
            export()


def test_public_exports_reject_noncanonical_decimal_and_string_subclasses() -> None:
    noncanonical_decimal = report()
    object.__setattr__(
        noncanonical_decimal,
        "forecast_probability",
        d("0.62"),
    )
    for export in (
        lambda: noncanonical_decimal.public_payload,
        lambda: probability_event_cost_adjusted_position_recommendation_report_payload(
            noncanonical_decimal,
        ),
    ):
        with pytest.raises(ValueError, match="forecast_probability.*six decimal"):
            export()

    string_subclass = report()
    object.__setattr__(string_subclass, "outcome_side", _StringSubclass("yes"))
    for export in (
        lambda: string_subclass.public_payload,
        lambda: probability_event_cost_adjusted_position_recommendation_report_payload(
            string_subclass,
        ),
    ):
        with pytest.raises(ValueError, match="outcome_side.*string"):
            export()


def test_public_payload_rejects_in_place_union_update() -> None:
    payload = report().public_payload

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload |= {"readiness_status": "blocked"}


def test_watch_report_keeps_positive_ev_but_flags_capital_lockup_and_small_margin() -> None:
    result = report(
        forecast_probability=d("0.595000"),
        settlement_delay_days=d("37.000000"),
    )

    assert result.readiness_status == "watch"
    assert result.capital_lockup_hint == "extended_settlement_delay_capital_locked"
    assert result.capital_lockup_cost_probability == d("0.005474")
    assert result.cost_adjusted_break_even_probability == d("0.570474")
    assert result.expected_value_probability == d("0.024526")
    assert result.margin_of_safety_probability == d("0.004526")
    assert result.kelly_upper_bound_probability == d("0.057100")
    assert result.recommended_position_fraction_probability == d("0.050000")
    assert result.reason_codes == (
        "cost_adjusted_expected_value_positive",
        "margin_of_safety_positive",
        "kelly_upper_bound_manual_cap_applied",
        "capital_lockup_cost_present",
        "extended_settlement_delay_capital_lockup_watch",
        "margin_of_safety_below_watch_threshold",
    )
    assert result.manual_next_step == "manual_review_costs_lockup_and_position_cap"


def test_blocked_report_zeroes_position_when_cost_adjusted_ev_is_not_positive() -> None:
    result = report(forecast_probability=d("0.560000"))

    assert result.readiness_status == "blocked"
    assert result.cost_adjusted_break_even_probability == d("0.570474")
    assert result.expected_value_probability == d("-0.010474")
    assert result.margin_of_safety_probability == d("-0.030474")
    assert result.kelly_upper_bound_probability == d("0.000000")
    assert result.recommended_position_fraction_probability == d("0.000000")
    assert result.reason_codes == (
        "cost_adjusted_expected_value_not_positive",
        "margin_of_safety_not_positive",
        "kelly_upper_bound_zero",
        "capital_lockup_cost_present",
        "extended_settlement_delay_capital_lockup_watch",
    )
    assert result.manual_next_step == "do_not_size_until_cost_adjusted_ev_improves"


def test_builder_revalidates_input_after_frozen_object_tampering() -> None:
    zero_cap = recommendation_input()
    object.__setattr__(zero_cap, "manual_fraction_cap_probability", d("0.000000"))
    with pytest.raises(ValueError, match="manual_fraction_cap_probability must be positive"):
        build_probability_event_cost_adjusted_position_recommendation_report(zero_cap)

    wrong_decimal_type = recommendation_input()
    object.__setattr__(wrong_decimal_type, "forecast_probability", 0.62)
    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        build_probability_event_cost_adjusted_position_recommendation_report(
            wrong_decimal_type,
        )


def test_high_legal_costs_block_and_zero_position_instead_of_failing_report_build() -> None:
    result = report(
        forecast_probability=d("0.900000"),
        market_probability=d("0.900000"),
        taker_fee_probability=d("0.100000"),
        spread_probability=d("0.100000"),
        slippage_probability=d("0.100000"),
        settlement_delay_days=d("365.000000"),
        annual_capital_charge_probability=d("1.000000"),
        uncertainty_buffer_probability=d("0.000000"),
        manual_fraction_cap_probability=d("0.100000"),
    )

    assert result.readiness_status == "blocked"
    assert result.capital_lockup_cost_probability == d("0.900000")
    assert result.cost_adjusted_break_even_probability == d("1.000000")
    assert result.expected_value_probability == d("-1.200000")
    assert result.margin_of_safety_probability == d("-1.200000")
    assert result.kelly_upper_bound_probability == d("0.000000")
    assert result.recommended_position_fraction_probability == d("0.000000")
    assert "cost_adjusted_break_even_exceeds_probability_ceiling" in result.reason_codes
    assert result.manual_next_step == "do_not_size_until_cost_adjusted_ev_improves"

    payload = probability_event_cost_adjusted_position_recommendation_report_payload(result)
    assert payload["cost_adjusted_break_even_probability"] == "1.000000"
    assert payload["recommended_position_fraction_probability"] == "0.000000"


def test_frozen_decimal_only_exact_types_flags_and_derived_invariants_are_enforced() -> None:
    input_value = recommendation_input()
    result = report()

    assert is_dataclass(input_value)
    assert input_value.__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        input_value.market_probability = d("0.550000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.readiness_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventCostAdjustedPositionRecommendationInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventCostAdjustedPositionRecommendationReport):
            pass

    with pytest.raises(ValueError, match="forecast_probability"):
        recommendation_input(forecast_probability=0.62)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_probability"):
        recommendation_input(market_probability=_DecimalSubclass("0.540000"))
    with pytest.raises(ValueError, match="settlement_delay_days"):
        recommendation_input(settlement_delay_days=d("-1.000000"))
    with pytest.raises(ValueError, match="manual_fraction_cap_probability"):
        recommendation_input(manual_fraction_cap_probability=d("0.000000"))
    with pytest.raises(ValueError, match="outcome_side"):
        recommendation_input(outcome_side="maybe")
    with pytest.raises(ValueError, match="paper_only"):
        recommendation_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="cost_adjusted_break_even_probability"):
        replace(result, cost_adjusted_break_even_probability=d("0.560000"))
    with pytest.raises(ValueError, match="payload_digest"):
        replace(result, payload_digest="0" * 64)

    hints = get_type_hints(ProbabilityEventCostAdjustedPositionRecommendationReport)
    for field in fields(result):
        value = getattr(result, field.name)
        if field.name.endswith("_probability") or field.name == "settlement_delay_days":
            assert type(value) is Decimal
            assert hints[field.name] is Decimal
        elif type(value) in (int, float):
            pytest.fail(f"runtime public numeric field is not Decimal: {field.name}")


def test_module_is_readonly_report_only_and_has_no_io_persistence_or_live_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "web3",
        "private_key",
        "wallet",
        "authentication",
        "live_trading",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "database",
        "network",
        "persist",
        "jsonl",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "web3",
    }
    forbidden_call_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "delete",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "open",
        "post",
        "put",
        "rollback",
        "sell",
        "send",
        "sign",
        "upsert",
        "write",
        "write_text",
        "write_bytes",
    }
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not imported_roots.intersection(forbidden_imports)
    assert not call_names.intersection(forbidden_call_names)
    assert float_constants == []


def _float_or_int_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if type(value) in (int, float, Decimal):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_or_int_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, (list, tuple)):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_or_int_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()
