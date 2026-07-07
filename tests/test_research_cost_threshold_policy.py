from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 7, 11, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    module_name = "polymarket_alpha_lab.research_cost_threshold_policy"
    assert importlib.util.find_spec(module_name) is not None
    return importlib.import_module(module_name)


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("utf-8")


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-cost-threshold-policy-test-v0",
        "watch_cost_to_edge_ratio": d("0.300000"),
        "block_cost_to_edge_ratio": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchCostThresholdConfig(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "candidate-alpha",
        "market_reference": "market-alpha",
        "observed_at": OBSERVED_AT,
        "probability_edge": d("0.100000"),
        "polymarket_taker_fee_probability": d("0.005000"),
        "spread_probability": d("0.010000"),
        "gas_cost": d("0.010000"),
        "deposit_cost": d("0.005000"),
        "settlement_cost": d("0.005000"),
        "expected_notional": d("10.000000"),
        "reason_codes": ("research_input",),
    }
    values.update(overrides)
    return module.ResearchCostThresholdCandidate(**values)


def report(*items: object, cfg=None):
    module = api()
    return module.build_research_cost_threshold_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_cost_ratio_below_watch_threshold_passes_research_filter() -> None:
    result = report(candidate())

    assert is_dataclass(result)
    assert result.status == "pass"
    assert result.candidate_count == d("1")
    assert result.pass_count == d("1")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.max_cost_to_edge_ratio == d("0.170000")
    assert result.reason_codes == ("research_cost_threshold_pass",)

    row = result.rows[0]
    assert row.status == "pass"
    assert row.total_cost_probability == d("0.017000")
    assert row.fixed_cost_probability == d("0.002000")
    assert row.cost_to_edge_ratio == d("0.170000")
    assert row.reason_codes == (
        "research_cost_threshold_pass",
        "research_input",
    )


def test_cost_ratio_at_watch_boundary_watches_research_filter() -> None:
    result = report(
        candidate(
            polymarket_taker_fee_probability=d("0.010000"),
            spread_probability=d("0.010000"),
            gas_cost=d("0.050000"),
            deposit_cost=d("0.050000"),
            settlement_cost=d("0.000000"),
        ),
    )

    assert result.status == "watch"
    row = result.rows[0]
    assert row.total_cost_probability == d("0.030000")
    assert row.cost_to_edge_ratio == d("0.300000")
    assert row.status == "watch"
    assert "cost_ratio_at_or_above_watch" in row.reason_codes


def test_cost_ratio_above_block_threshold_blocks_research_filter() -> None:
    result = report(
        candidate(
            polymarket_taker_fee_probability=d("0.020000"),
            spread_probability=d("0.020000"),
            gas_cost=d("0.100000"),
            deposit_cost=d("0.100000"),
            settlement_cost=d("0.000000"),
        ),
    )

    assert result.status == "block"
    row = result.rows[0]
    assert row.total_cost_probability == d("0.060000")
    assert row.cost_to_edge_ratio == d("0.600000")
    assert row.status == "block"
    assert "cost_ratio_at_or_above_block" in row.reason_codes


def test_rejects_non_exact_decimal_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="Decimal"):
        candidate(probability_edge=0.1)
    with pytest.raises(ValueError, match="Decimal"):
        candidate(expected_notional=10)
    with pytest.raises(ValueError, match="exact Decimal"):
        candidate(spread_probability=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="Decimal"):
        config(watch_cost_to_edge_ratio=0.3)
    with pytest.raises(ValueError, match="ResearchCostThresholdCandidate"):
        module.build_research_cost_threshold_report(
            [object()],
            config=config(),
            generated_at=GENERATED_AT,
        )


def test_public_payload_redacts_references_and_rejects_leaks() -> None:
    module = api()
    sensitive = "-".join(
        (
            hidden_word("77616c6c6574"),
            hidden_word("746f6b656e"),
            hidden_word("61757468"),
        ),
    )
    item = candidate(
        candidate_reference=f"raw-candidate-{sensitive}",
        market_reference="market-123-secret-question",
    )
    payload = module.research_cost_threshold_policy_payload(report(item))
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload["rows"][0]["research_reference"].startswith("research_ref_")
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    for fragment in (
        "raw-candidate",
        "market-123",
        "secret-question",
        hidden_word("77616c6c6574"),
        hidden_word("746f6b656e"),
        hidden_word("61757468"),
        hidden_word("6f72646572"),
        hidden_word("7472616465"),
        hidden_word("627579"),
        hidden_word("73656c6c"),
        hidden_word("7265636f6d6d656e646174696f6e"),
    ):
        assert fragment not in rendered
        assert fragment not in repr(payload).lower()

    tampered_payload = dict(payload)
    tampered_payload[hidden_word("6d61726b65745f6964")] = "redacted"
    with pytest.raises(ValueError, match="public payload"):
        module.research_cost_threshold_policy_payload(tampered_payload)

    tampered_payload = dict(payload)
    tampered_payload["note"] = f"contains-{hidden_word('7472616465')}"
    with pytest.raises(ValueError, match="public payload"):
        module.research_cost_threshold_policy_payload(tampered_payload)


def test_hard_flags_are_required_and_dataclasses_are_frozen() -> None:
    module = api()
    result = report(candidate())
    row = result.rows[0]

    for value in (
        config(),
        candidate(),
        row,
        result,
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True

    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(candidate(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        module.research_cost_threshold_policy_payload(replace(result, paper_only=False))

    for klass in (
        module.ResearchCostThresholdConfig,
        module.ResearchCostThresholdCandidate,
        module.ResearchCostThresholdRow,
        module.ResearchCostThresholdReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True


def test_output_is_deterministic_for_reordered_inputs() -> None:
    module = api()
    first = candidate(
        candidate_reference="alpha",
        market_reference="market-a",
        probability_edge=d("0.100000"),
        spread_probability=d("0.010000"),
    )
    second = candidate(
        candidate_reference="beta",
        market_reference="market-b",
        probability_edge=d("0.200000"),
        spread_probability=d("0.010000"),
    )

    report_a = report(second, first)
    report_b = report(first, second)
    payload_a = module.research_cost_threshold_policy_payload(report_a)
    payload_b = module.research_cost_threshold_policy_payload(report_b)

    assert report_a == report_b
    assert payload_a == payload_b
    assert json.dumps(payload_a, allow_nan=False, sort_keys=True) == json.dumps(
        payload_b,
        allow_nan=False,
        sort_keys=True,
    )
    assert module.research_cost_threshold_policy_payload(dict(payload_a)) == payload_a


def test_source_has_no_persistence_network_or_execution_surface() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    imports: list[str] = []
    call_names: list[str] = []
    attr_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".", maxsplit=1)[0])
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id.lower())
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr.lower())
        if isinstance(node, ast.Attribute):
            attr_names.append(node.attr.lower())

    assert not (
        set(imports)
        & {
            "asyncio",
            "csv",
            "http",
            "os",
            "pathlib",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "subprocess",
            "urllib",
        }
    )
    assert not (set(call_names) & {"open", "connect", "execute", "send", "post", "put"})
    assert not (set(attr_names) & {"connect", "execute", "send", "post", "put"})
