from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_cost_adjusted_kelly_bound_readiness_report import (
    PROBABILITY_EVENT_COST_ADJUSTED_KELLY_BOUND_READINESS_REPORT_VERSION,
    ProbabilityEventCostAdjustedKellyBoundReadinessInput,
    ProbabilityEventCostAdjustedKellyBoundReadinessReport,
    build_probability_event_cost_adjusted_kelly_bound_readiness_report,
    probability_event_cost_adjusted_kelly_bound_readiness_report_payload,
    probability_event_cost_adjusted_kelly_bound_readiness_report_digest,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_cost_adjusted_kelly_bound_readiness_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def readiness_input(
    **overrides: object,
) -> ProbabilityEventCostAdjustedKellyBoundReadinessInput:
    values = {
        "win_probability": d("0.620000"),
        "market_probability": d("0.500000"),
        "net_edge_probability": d("0.120000"),
        "cost_probability": d("0.020000"),
        "uncertainty_probability": d("0.030000"),
        "manual_fraction_cap_probability": d("0.050000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ProbabilityEventCostAdjustedKellyBoundReadinessInput(**values)


def report(
    **overrides: object,
) -> ProbabilityEventCostAdjustedKellyBoundReadinessReport:
    return build_probability_event_cost_adjusted_kelly_bound_readiness_report(
        readiness_input(**overrides),
    )


def test_ready_report_caps_cost_adjusted_kelly_fraction_and_digest() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventCostAdjustedKellyBoundReadinessReport
    assert is_dataclass(first)
    assert first.__dataclass_params__.frozen is True
    assert (
        first.config_version
        == PROBABILITY_EVENT_COST_ADJUSTED_KELLY_BOUND_READINESS_REPORT_VERSION
    )
    assert first.kelly_bound_status == "ready"
    assert first.cost_adjusted_fraction_probability == d("0.050000")
    assert first.reason_codes == (
        "kelly_bound_positive_cost_adjusted_edge",
        "kelly_bound_manual_cap_applied",
        "kelly_bound_manual_review_required",
    )
    assert first.manual_next_step == "review_manual_position_boundary"
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second
    assert first.payload_digest == second.payload_digest
    assert (
        probability_event_cost_adjusted_kelly_bound_readiness_report_digest(first)
        == first.payload_digest
    )

    payload = probability_event_cost_adjusted_kelly_bound_readiness_report_payload(first)
    assert payload == first.public_payload
    assert payload == {
        "config_version": "probability-event-cost-adjusted-kelly-bound-readiness-v0",
        "kelly_bound_status": "ready",
        "win_probability": "0.620000",
        "market_probability": "0.500000",
        "net_edge_probability": "0.120000",
        "cost_probability": "0.020000",
        "uncertainty_probability": "0.030000",
        "manual_fraction_cap_probability": "0.050000",
        "cost_adjusted_fraction_probability": "0.050000",
        "reason_codes": first.reason_codes,
        "manual_next_step": "review_manual_position_boundary",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": first.payload_digest,
    }
    json.dumps(payload, sort_keys=True)
    expected_digest = sha256(
        json.dumps(
            {**payload, "payload_digest": ""},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    assert first.payload_digest == expected_digest
    assert _float_or_int_paths(payload) == ()

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["kelly_bound_status"] = "blocked"


def test_blocked_report_zeroes_fraction_when_cost_and_uncertainty_exhaust_edge() -> None:
    result = report(
        win_probability=d("0.540000"),
        market_probability=d("0.500000"),
        net_edge_probability=d("0.040000"),
        cost_probability=d("0.030000"),
        uncertainty_probability=d("0.020000"),
        manual_fraction_cap_probability=d("0.050000"),
    )

    assert result.kelly_bound_status == "blocked"
    assert result.cost_adjusted_fraction_probability == d("0.000000")
    assert result.reason_codes == (
        "kelly_bound_cost_uncertainty_exhaust_edge",
        "kelly_bound_zero_fraction_boundary",
        "kelly_bound_manual_review_required",
    )
    assert result.manual_next_step == "do_not_size_position_manually_until_edge_improves"


def test_watch_report_flags_uncapped_fraction_below_manual_cap() -> None:
    result = report(
        win_probability=d("0.590000"),
        market_probability=d("0.500000"),
        net_edge_probability=d("0.090000"),
        cost_probability=d("0.020000"),
        uncertainty_probability=d("0.020000"),
        manual_fraction_cap_probability=d("0.200000"),
    )

    assert result.kelly_bound_status == "watch"
    assert result.cost_adjusted_fraction_probability == d("0.050000")
    assert result.reason_codes == (
        "kelly_bound_positive_cost_adjusted_edge",
        "kelly_bound_below_manual_cap",
        "kelly_bound_watch_small_boundary",
        "kelly_bound_manual_review_required",
    )
    assert result.manual_next_step == "review_small_manual_boundary_before_any_paper_entry"


def test_frozen_decimal_only_exact_types_and_hard_flags() -> None:
    input_value = readiness_input()
    result = report()

    assert is_dataclass(input_value)
    assert input_value.__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        input_value.win_probability = d("0.600000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.kelly_bound_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventCostAdjustedKellyBoundReadinessInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventCostAdjustedKellyBoundReadinessReport):
            pass

    with pytest.raises(ValueError, match="win_probability"):
        readiness_input(win_probability="0.620000")
    with pytest.raises(ValueError, match="market_probability"):
        readiness_input(market_probability=d("1.100000"))
    with pytest.raises(ValueError, match="net_edge_probability"):
        readiness_input(net_edge_probability=d("0.130000"))
    with pytest.raises(ValueError, match="manual_fraction_cap_probability"):
        readiness_input(manual_fraction_cap_probability=d("0.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        readiness_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="cost_adjusted_fraction_probability"):
        replace(result, cost_adjusted_fraction_probability=d("0.060000"))
    with pytest.raises(ValueError, match="payload_digest"):
        probability_event_cost_adjusted_kelly_bound_readiness_report_payload(
            replace(result, payload_digest="0" * 64),
        )

    hints = get_type_hints(ProbabilityEventCostAdjustedKellyBoundReadinessReport)
    for field in fields(ProbabilityEventCostAdjustedKellyBoundReadinessReport):
        value = getattr(result, field.name)
        if field.name.endswith("_probability"):
            assert type(value) is Decimal
            assert hints[field.name] is Decimal
        elif type(value) in (int, float):
            pytest.fail(f"runtime public numeric field is not Decimal: {field.name}")


def test_module_is_readonly_report_only_and_has_no_live_execution_or_io_surface() -> None:
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
        "web3",
        "private_key",
        "wallet",
        "authentication",
        "live_trading",
        "order execution",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "database",
        "network",
        "jsonl",
        "persistence",
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
