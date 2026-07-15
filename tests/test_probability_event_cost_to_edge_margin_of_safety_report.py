from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

import polymarket_alpha_lab.probability_event_cost_to_edge_margin_of_safety_report as api
from polymarket_alpha_lab.probability_event_cost_to_edge_margin_of_safety_report import (
    ProbabilityEventCostToEdgeMarginOfSafetyInput,
    ProbabilityEventCostToEdgeMarginOfSafetyReport,
    build_probability_event_cost_to_edge_margin_of_safety_report,
    probability_event_cost_to_edge_margin_of_safety_report_digest,
    probability_event_cost_to_edge_margin_of_safety_report_to_payload,
    validate_probability_event_cost_to_edge_margin_of_safety_public_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_cost_to_edge_margin_of_safety_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def input_row(
    **overrides: object,
) -> ProbabilityEventCostToEdgeMarginOfSafetyInput:
    values = {
        "raw_edge_probability": d("0.120000"),
        "taker_fee_probability": d("0.015000"),
        "estimated_slippage_probability": d("0.020000"),
        "settlement_cost_probability": d("0.010000"),
        "uncertainty_buffer_probability": d("0.025000"),
    }
    values.update(overrides)
    return ProbabilityEventCostToEdgeMarginOfSafetyInput(**values)


def report(
    **overrides: object,
) -> ProbabilityEventCostToEdgeMarginOfSafetyReport:
    return build_probability_event_cost_to_edge_margin_of_safety_report(
        input_row(**overrides),
    )


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_runtime_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_positive_raw_edge_above_all_costs_emits_pass_payload_and_digest() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventCostToEdgeMarginOfSafetyReport
    assert is_dataclass(first)
    assert first.net_edge_probability == d("0.075000")
    assert first.margin_of_safety_probability == d("0.050000")
    assert first.margin_status == "pass"
    assert first.reason_codes == (
        "probability_event_cost_to_edge_margin_of_safety_pass",
    )
    assert first.manual_next_step == (
        "document_cost_adjusted_edge_for_manual_phase1_review"
    )
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second

    payload = probability_event_cost_to_edge_margin_of_safety_report_to_payload(first)
    assert first.public_payload == payload
    assert payload == {
        "raw_edge_probability": "0.120000",
        "taker_fee_probability": "0.015000",
        "estimated_slippage_probability": "0.020000",
        "settlement_cost_probability": "0.010000",
        "uncertainty_buffer_probability": "0.025000",
        "net_edge_probability": "0.075000",
        "margin_of_safety_probability": "0.050000",
        "margin_status": "pass",
        "reason_codes": [
            "probability_event_cost_to_edge_margin_of_safety_pass",
        ],
        "manual_next_step": "document_cost_adjusted_edge_for_manual_phase1_review",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    expected_digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert first.payload_digest == expected_digest
    assert first.payload_digest == second.payload_digest
    assert (
        probability_event_cost_to_edge_margin_of_safety_report_digest(first)
        == expected_digest
    )
    assert (
        validate_probability_event_cost_to_edge_margin_of_safety_public_payload(
            payload,
        )
        == payload
    )
    assert_no_runtime_numbers(payload)


def test_cost_drag_and_uncertainty_buffer_determine_watch_and_block_status() -> None:
    watched = report(
        raw_edge_probability=d("0.070000"),
        taker_fee_probability=d("0.015000"),
        estimated_slippage_probability=d("0.020000"),
        settlement_cost_probability=d("0.010000"),
        uncertainty_buffer_probability=d("0.025000"),
    )
    blocked = report(
        raw_edge_probability=d("0.040000"),
        taker_fee_probability=d("0.015000"),
        estimated_slippage_probability=d("0.020000"),
        settlement_cost_probability=d("0.010000"),
        uncertainty_buffer_probability=d("0.025000"),
    )

    assert watched.net_edge_probability == d("0.025000")
    assert watched.margin_of_safety_probability == d("0.000000")
    assert watched.margin_status == "watch"
    assert watched.reason_codes == (
        "probability_event_cost_to_edge_margin_of_safety_no_positive_margin",
    )
    assert watched.manual_next_step == "tighten_cost_inputs_before_manual_review"

    assert blocked.net_edge_probability == d("-0.005000")
    assert blocked.margin_of_safety_probability == d("-0.030000")
    assert blocked.margin_status == "blocked"
    assert blocked.reason_codes == (
        "probability_event_cost_to_edge_margin_of_safety_costs_exceed_raw_edge",
        "probability_event_cost_to_edge_margin_of_safety_no_positive_margin",
    )
    assert blocked.manual_next_step == "block_manual_review_until_edge_exceeds_costs"


def test_dataclasses_are_frozen_decimal_only_and_flags_are_hard_true() -> None:
    source = input_row()
    result = report()

    assert is_dataclass(ProbabilityEventCostToEdgeMarginOfSafetyInput)
    assert is_dataclass(ProbabilityEventCostToEdgeMarginOfSafetyReport)
    assert source.__dataclass_params__.frozen
    assert result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        result.margin_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventCostToEdgeMarginOfSafetyInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventCostToEdgeMarginOfSafetyReport):
            pass

    with pytest.raises(ValueError, match="raw_edge_probability"):
        input_row(raw_edge_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="taker_fee_probability"):
        input_row(taker_fee_probability=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="net_edge_probability"):
        replace(result, net_edge_probability=1)  # type: ignore[arg-type]

    hints = get_type_hints(ProbabilityEventCostToEdgeMarginOfSafetyReport)
    for field_name in (
        "raw_edge_probability",
        "taker_fee_probability",
        "estimated_slippage_probability",
        "settlement_cost_probability",
        "uncertainty_buffer_probability",
        "net_edge_probability",
        "margin_of_safety_probability",
    ):
        assert hints[field_name] is Decimal
    for field in fields(result):
        value = getattr(result, field.name)
        if field.name.endswith("_probability"):
            assert type(value) is Decimal


def test_manual_report_and_payload_tampering_must_match_derived_values() -> None:
    result = report()

    with pytest.raises(ValueError, match="net_edge_probability"):
        ProbabilityEventCostToEdgeMarginOfSafetyReport(
            raw_edge_probability=d("0.120000"),
            taker_fee_probability=d("0.015000"),
            estimated_slippage_probability=d("0.020000"),
            settlement_cost_probability=d("0.010000"),
            uncertainty_buffer_probability=d("0.025000"),
            net_edge_probability=d("0.074000"),
            margin_of_safety_probability=d("0.050000"),
            margin_status="pass",
            reason_codes=(
                "probability_event_cost_to_edge_margin_of_safety_pass",
            ),
            manual_next_step="document_cost_adjusted_edge_for_manual_phase1_review",
            payload_digest=result.payload_digest,
        )

    payload = dict(result.public_payload)
    with pytest.raises(ValueError, match="net_edge_probability"):
        validate_probability_event_cost_to_edge_margin_of_safety_public_payload(
            {**payload, "net_edge_probability": "0.074000"},
        )
    with pytest.raises(ValueError, match="margin_status"):
        validate_probability_event_cost_to_edge_margin_of_safety_public_payload(
            {**payload, "margin_status": "blocked"},
        )
    with pytest.raises(ValueError, match="paper_only"):
        validate_probability_event_cost_to_edge_margin_of_safety_public_payload(
            {**payload, "paper_only": False},
        )


def test_module_has_no_live_io_execution_or_file_persistence_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "web3",
        "live",
        "auth",
        "wallet",
        "order",
        "private_key",
        "api_key",
        "sign",
        "execute",
        "submit",
        "jsonl",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)
        elif isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id.lower())
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr.lower())

    assert not float_constants
    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "psycopg",
            "supabase",
            "web3",
        },
    )
    assert call_names.isdisjoint(
        {
            "connect",
            "cursor",
            "delete",
            "executemany",
            "fetch",
            "insert",
            "open",
            "post",
            "put",
            "rollback",
            "send",
            "submit",
            "upsert",
            "write",
            "write_text",
            "write_bytes",
        },
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert "live" not in lowered
        assert "auth" not in lowered
        assert "wallet" not in lowered
        assert "order" not in lowered
        assert "key" not in lowered
        assert "sign" not in lowered
        assert "execute" not in lowered
