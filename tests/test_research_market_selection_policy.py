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


MODULE_NAME = "polymarket_alpha_lab.research_market_selection_policy"
CONFIG_VERSION = "research-selection-policy-v0"
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


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
        "min_pass_evidence_quality_score": d("0.750000"),
        "min_watch_evidence_quality_score": d("0.500000"),
        "pass_research_cost_ratio": d("0.250000"),
        "block_research_cost_ratio": d("0.500000"),
        "min_pass_rule_clarity_score": d("0.700000"),
        "min_watch_rule_clarity_score": d("0.450000"),
        "min_pass_team_coverage_score": d("0.650000"),
        "min_watch_team_coverage_score": d("0.350000"),
        "supported_event_types": (
            "crypto_protocol",
            "macro_release",
            "policy_process",
            "sports_status",
            "weather_event",
        ),
    }
    values.update(overrides)
    return module.ResearchMarketSelectionPolicyConfig(**values)


def selection(**overrides: object):
    module = api()
    values = {
        "private_selection_key": "raw-selection-alpha",
        "event_type": "macro_release",
        "evidence_quality_score": d("0.900000"),
        "research_cost_ratio": d("0.100000"),
        "rule_clarity_score": d("0.850000"),
        "team_coverage_score": d("0.800000"),
    }
    values.update(overrides)
    return module.ResearchMarketSelectionPolicyInput(**values)


def report(*items: object, cfg=None):
    module = api()
    return module.build_research_market_selection_policy_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def assert_no_public_numerics(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numerics(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numerics(item)


def test_pass_watch_and_block_research_priorities_are_combined() -> None:
    module = api()

    result = report(
        selection(private_selection_key="raw-pass"),
        selection(
            private_selection_key="raw-watch",
            event_type="sports_status",
            evidence_quality_score=d("0.650000"),
            research_cost_ratio=d("0.350000"),
            rule_clarity_score=d("0.600000"),
            team_coverage_score=d("0.500000"),
        ),
        selection(
            private_selection_key="raw-block",
            event_type="uncovered_event",
            evidence_quality_score=d("0.400000"),
            research_cost_ratio=d("0.600000"),
            rule_clarity_score=d("0.300000"),
            team_coverage_score=d("0.200000"),
        ),
    )

    assert is_dataclass(result)
    assert result.overall_research_priority == "block"
    assert result.item_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.reason_codes == (
        "selection_policy_block_present",
        "selection_policy_watch_present",
    )

    assert tuple(row.research_priority for row in result.rows) == ("block", "watch", "pass")
    block_row, watch_row, pass_row = result.rows
    assert block_row.event_type == "uncovered_event"
    assert block_row.event_type_support_score == d("0.000000")
    assert "unsupported_event_type_block" in block_row.reason_codes
    assert "cost_ratio_at_or_above_block" in block_row.reason_codes
    assert "evidence_quality_below_watch" in block_row.reason_codes
    assert watch_row.event_type == "sports_status"
    assert watch_row.event_type_support_score == d("1.000000")
    assert "cost_ratio_above_pass" in watch_row.reason_codes
    assert "rule_clarity_below_pass" in watch_row.reason_codes
    assert pass_row.reason_codes == ("selection_policy_pass",)

    payload = module.research_market_selection_policy_payload(result)
    assert payload["config_version"] == CONFIG_VERSION
    assert payload["item_count"] == "3.000000"
    assert payload["rows"][0]["research_cost_ratio"] == "0.600000"
    assert payload["rows"][0]["selection_reference"].startswith("selection_ref_")
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numerics(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_decimal_only_rejects_non_exact_types_and_noncanonical_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="evidence_quality_score"):
        selection(evidence_quality_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="research_cost_ratio"):
        selection(research_cost_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="rule_clarity_score"):
        selection(rule_clarity_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="team_coverage_score"):
        selection(team_coverage_score=d("0.80"))
    with pytest.raises(ValueError, match="min_pass_evidence_quality_score"):
        config(min_pass_evidence_quality_score=d("0.75"))
    with pytest.raises(ValueError, match="ResearchMarketSelectionPolicyInput"):
        module.build_research_market_selection_policy_report(
            [object()],
            config=config(),
            generated_at=GENERATED_AT,
        )


def test_public_payload_redacts_private_identifiers_and_rejects_leaks() -> None:
    module = api()
    sensitive = "-".join(
        (
            hidden_word("63616e646964617465"),
            hidden_word("6d61726b6574"),
            hidden_word("77616c6c6574"),
            hidden_word("746f6b656e"),
            hidden_word("61757468"),
        ),
    )
    result = report(
        selection(
            private_selection_key=f"raw-secret-{sensitive}",
            event_type="policy_process",
        ),
    )
    payload = module.research_market_selection_policy_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload["rows"][0]["selection_reference"].startswith("selection_ref_")
    for fragment in (
        "raw-secret",
        hidden_word("63616e646964617465"),
        hidden_word("6d61726b6574"),
        hidden_word("736c7567"),
        hidden_word("7175657374696f6e"),
        hidden_word("736f757263655f726566"),
        hidden_word("736f757263655f75726c"),
        hidden_word("736f757263655f74657874"),
        hidden_word("64736e"),
        hidden_word("7461626c65"),
        hidden_word("77616c6c6574"),
        hidden_word("746f6b656e"),
        hidden_word("61757468"),
        hidden_word("6f72646572"),
        hidden_word("7472616465"),
        hidden_word("706f736974696f6e"),
        hidden_word("627579"),
        hidden_word("73656c6c"),
        hidden_word("7265636f6d6d656e646174696f6e"),
    ):
        assert fragment not in rendered

    with pytest.raises(ValueError, match="unsafe public value"):
        selection(event_type=hidden_word("736f757263655f75726c"))

    for unsafe_key in (
        hidden_word("63616e6469646174655f6964"),
        hidden_word("6d61726b65745f736c7567"),
        hidden_word("7175657374696f6e"),
        hidden_word("736f757263655f726566"),
        hidden_word("64736e"),
        hidden_word("7461626c65"),
    ):
        with pytest.raises(ValueError, match="unsafe public field"):
            module.research_market_selection_policy_payload(
                {**payload, unsafe_key: "redacted"},
            )

    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_market_selection_policy_payload(
            {**payload, "reason_codes": [hidden_word("627579") + "_signal"]},
        )


def test_hard_flags_and_frozen_dataclasses_are_enforced() -> None:
    module = api()
    result = report(selection())
    row = result.rows[0]

    for value in (config(), selection(), row, result):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True

    with pytest.raises(FrozenInstanceError):
        row.research_priority = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(selection(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        module.research_market_selection_policy_payload(
            replace(result, paper_only=False),
        )

    for klass in (
        module.ResearchMarketSelectionPolicyConfig,
        module.ResearchMarketSelectionPolicyInput,
        module.ResearchMarketSelectionPolicyRow,
        module.ResearchMarketSelectionPolicyReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True


def test_report_and_payload_are_deterministic_for_reordered_inputs() -> None:
    module = api()
    first = selection(
        private_selection_key="raw-first",
        event_type="weather_event",
        evidence_quality_score=d("0.800000"),
        research_cost_ratio=d("0.200000"),
        rule_clarity_score=d("0.750000"),
        team_coverage_score=d("0.700000"),
    )
    second = selection(
        private_selection_key="raw-second",
        event_type="crypto_protocol",
        evidence_quality_score=d("0.650000"),
        research_cost_ratio=d("0.300000"),
        rule_clarity_score=d("0.600000"),
        team_coverage_score=d("0.500000"),
    )

    report_a = report(second, first)
    report_b = report(first, second)
    payload_a = module.research_market_selection_policy_payload(report_a)
    payload_b = module.research_market_selection_policy_payload(report_b)

    assert report_a == report_b
    assert payload_a == payload_b
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert module.research_market_selection_policy_payload(dict(payload_a)) == payload_a


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
