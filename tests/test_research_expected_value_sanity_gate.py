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


MODULE_NAME = "polymarket_alpha_lab.research_expected_value_sanity_gate"
CONFIG_VERSION = "research-expected-value-sanity-gate-v0"
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 7, 11, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def api():
    assert importlib.util.find_spec(MODULE_NAME) is not None
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("utf-8")


def config(**overrides: object):
    module = api()
    values = {
        "config_version": CONFIG_VERSION,
        "min_pass_probability_delta": d("0.050000"),
        "min_watch_probability_delta": d("0.020000"),
        "watch_cost_to_delta_ratio": d("0.300000"),
        "block_cost_to_delta_ratio": d("0.500000"),
        "min_pass_evidence_quality": d("0.750000"),
        "min_watch_evidence_quality": d("0.500000"),
        "min_pass_liquidity_summary": d("0.650000"),
        "min_watch_liquidity_summary": d("0.400000"),
    }
    values.update(overrides)
    return module.ResearchExpectedValueSanityGateConfig(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "candidate-alpha",
        "market_reference": "market-alpha",
        "observed_at": OBSERVED_AT,
        "sanitized_probability_delta": d("0.080000"),
        "total_cost_probability": d("0.010000"),
        "evidence_quality_score": d("0.900000"),
        "liquidity_summary_score": d("0.800000"),
        "reason_codes": ("operator_review_ready",),
    }
    values.update(overrides)
    return module.ResearchExpectedValueSanityGateCandidate(**values)


def report(*items: object, cfg=None):
    module = api()
    return module.build_research_expected_value_sanity_gate_report(
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


def test_pass_watch_and_block_statuses_combine_sanity_inputs() -> None:
    module = api()

    result = report(
        candidate(candidate_reference="candidate-pass", market_reference="market-pass"),
        candidate(
            candidate_reference="candidate-watch",
            market_reference="market-watch",
            sanitized_probability_delta=d("0.040000"),
            evidence_quality_score=d("0.600000"),
        ),
        candidate(
            candidate_reference="candidate-block",
            market_reference="market-block",
            sanitized_probability_delta=d("0.050000"),
            total_cost_probability=d("0.030000"),
            evidence_quality_score=d("0.450000"),
            liquidity_summary_score=d("0.300000"),
        ),
    )

    assert is_dataclass(result)
    assert result.status == "block"
    assert result.candidate_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.reason_codes == (
        "expected_value_sanity_block_present",
        "expected_value_sanity_watch_present",
    )

    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    block_row, watch_row, pass_row = result.rows
    assert block_row.cost_to_delta_ratio == d("0.600000")
    assert "cost_ratio_at_or_above_block" in block_row.reason_codes
    assert "evidence_quality_below_watch" in block_row.reason_codes
    assert "liquidity_summary_below_watch" in block_row.reason_codes
    assert watch_row.sanitized_probability_delta == d("0.040000")
    assert "probability_delta_below_pass" in watch_row.reason_codes
    assert "evidence_quality_below_pass" in watch_row.reason_codes
    assert pass_row.cost_to_delta_ratio == d("0.125000")
    assert pass_row.reason_codes == (
        "expected_value_sanity_pass",
        "operator_review_ready",
    )

    payload = module.research_expected_value_sanity_gate_payload(result)
    assert payload["candidate_count"] == "3.000000"
    assert payload["rows"][0]["cost_to_delta_ratio"] == "0.600000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)
    json.dumps(payload, sort_keys=True)


def test_decimal_only_rejects_non_exact_and_noncanonical_decimal_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="sanitized_probability_delta"):
        candidate(sanitized_probability_delta=0.08)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="total_cost_probability"):
        candidate(total_cost_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_quality_score"):
        candidate(evidence_quality_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="min_pass_probability_delta"):
        config(min_pass_probability_delta=d("0.05"))
    with pytest.raises(ValueError, match="ResearchExpectedValueSanityGateCandidate"):
        module.build_research_expected_value_sanity_gate_report(
            [object()],
            config=config(),
            generated_at=GENERATED_AT,
        )


def test_public_payload_redacts_identifiers_and_rejects_leaks() -> None:
    module = api()
    sensitive = "-".join(
        (
            hidden_word("77616c6c6574"),
            hidden_word("746f6b656e"),
            hidden_word("61757468"),
        ),
    )
    result = report(
        candidate(
            candidate_reference=f"raw-candidate-secret-{sensitive}",
            market_reference="market-secret-slug-question",
        ),
    )
    payload = module.research_expected_value_sanity_gate_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload["rows"][0]["research_reference"].startswith("research_ref_")
    for fragment in (
        "raw-candidate-secret",
        "market-secret-slug-question",
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

    for unsafe_key in (
        hidden_word("63616e6469646174655f6964"),
        hidden_word("6d61726b65745f736c7567"),
        hidden_word("736f757263655f75726c"),
        hidden_word("64736e"),
        hidden_word("7461626c65"),
    ):
        with pytest.raises(ValueError, match="unsafe public field"):
            module.research_expected_value_sanity_gate_payload(
                {**payload, unsafe_key: "redacted"},
            )

    with pytest.raises(ValueError, match="unsafe public value"):
        candidate(reason_codes=(f"contains_{hidden_word('736f757263655f74657874')}",))
    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_expected_value_sanity_gate_payload(
            {**payload, "reason_codes": [hidden_word("627579") + "_signal"]},
        )


def test_hard_flags_and_frozen_dataclasses_are_enforced() -> None:
    module = api()
    result = report(candidate())
    row = result.rows[0]

    for value in (config(), candidate(), row, result):
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
        module.research_expected_value_sanity_gate_payload(
            replace(result, paper_only=False),
        )

    for klass in (
        module.ResearchExpectedValueSanityGateConfig,
        module.ResearchExpectedValueSanityGateCandidate,
        module.ResearchExpectedValueSanityGateRow,
        module.ResearchExpectedValueSanityGateReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True


def test_report_and_digest_are_deterministic_for_reordered_inputs() -> None:
    module = api()
    first = candidate(
        candidate_reference="candidate-first",
        market_reference="market-first",
        sanitized_probability_delta=d("0.060000"),
        total_cost_probability=d("0.010000"),
    )
    second = candidate(
        candidate_reference="candidate-second",
        market_reference="market-second",
        sanitized_probability_delta=d("0.030000"),
        total_cost_probability=d("0.012000"),
    )

    report_a = report(second, first)
    report_b = report(first, second)
    payload_a = module.research_expected_value_sanity_gate_payload(report_a)
    payload_b = module.research_expected_value_sanity_gate_payload(report_b)

    assert report_a == report_b
    assert payload_a == payload_b
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert module.research_expected_value_sanity_gate_payload(dict(payload_a)) == payload_a


def test_source_has_no_persistence_network_or_transaction_surface() -> None:
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
