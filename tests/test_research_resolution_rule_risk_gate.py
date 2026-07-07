from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_resolution_rule_risk_gate"
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_RESEARCH_RESOLUTION_RULE_RISK_GATE_CONFIG_VERSION,
        "max_pass_risk_score": d("0.250000"),
        "max_watch_risk_score": d("0.550000"),
        "min_pass_rule_completeness_score": d("0.900000"),
        "min_watch_rule_completeness_score": d("0.650000"),
        "max_pass_resolution_path_ambiguity_score": d("0.250000"),
        "max_watch_resolution_path_ambiguity_score": d("0.550000"),
        "max_pass_dispute_risk_score": d("0.250000"),
        "max_watch_dispute_risk_score": d("0.550000"),
        "max_pass_resolution_timing_pressure_score": d("0.250000"),
        "max_watch_resolution_timing_pressure_score": d("0.550000"),
        "rule_incompleteness_weight": d("0.350000"),
        "resolution_path_ambiguity_weight": d("0.250000"),
        "dispute_risk_weight": d("0.250000"),
        "resolution_timing_pressure_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchResolutionRuleRiskGateConfig(**values)


def item(**overrides: object):
    module = api()
    values = {
        "research_item_reference": "research_ref_alpha",
        "rule_completeness_score": d("0.950000"),
        "resolution_path_ambiguity_score": d("0.100000"),
        "dispute_risk_score": d("0.100000"),
        "resolution_timing_pressure_score": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchResolutionRuleRiskGateInput(**values)


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_resolution_rule_risk_gate(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_no_numeric_payload_values(value: Any) -> None:
    if type(value) in (Decimal, float, int):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_numeric_payload_values(item_value)
    if isinstance(value, list):
        for item_value in value:
            assert_no_numeric_payload_values(item_value)


def test_pass_watch_block_prioritizes_resolution_rule_risk_for_human_research() -> None:
    result = report(
        item(
            research_item_reference="research_ref_pass",
            rule_completeness_score=d("0.950000"),
            resolution_path_ambiguity_score=d("0.100000"),
            dispute_risk_score=d("0.100000"),
            resolution_timing_pressure_score=d("0.100000"),
        ),
        item(
            research_item_reference="research_ref_watch",
            rule_completeness_score=d("0.780000"),
            resolution_path_ambiguity_score=d("0.300000"),
            dispute_risk_score=d("0.300000"),
            resolution_timing_pressure_score=d("0.300000"),
        ),
        item(
            research_item_reference="research_ref_block",
            rule_completeness_score=d("0.400000"),
            resolution_path_ambiguity_score=d("0.900000"),
            dispute_risk_score=d("0.700000"),
            resolution_timing_pressure_score=d("0.800000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.item_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.max_resolution_rule_risk_score == d("0.730000")
    assert result.average_resolution_rule_risk_score == d("0.361500")
    assert result.status == "block"
    assert result.human_research_priority == "urgent"
    assert result.reason_codes == (
        "resolution_rule_risk_block_present",
        "resolution_rule_risk_watch_present",
        "rule_completeness_block_present",
        "resolution_path_ambiguity_block_present",
        "dispute_risk_block_present",
        "resolution_timing_pressure_block_present",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_sha256(result.report_sha256)
    assert_sha256(result.derived_validation_digest)

    assert tuple(row.status for row in result.results) == ("block", "watch", "pass")
    blocked, watched, passed = result.results

    assert blocked.research_item_reference == "research_ref_block"
    assert blocked.rule_incompleteness_pressure == d("0.600000")
    assert blocked.resolution_rule_risk_score == d("0.730000")
    assert blocked.human_research_priority == "urgent"
    assert blocked.reason_codes == (
        "resolution_rule_risk_block",
        "rule_completeness_block",
        "resolution_path_ambiguity_block",
        "dispute_risk_block",
        "resolution_timing_pressure_block",
    )
    assert_sha256(blocked.result_sha256)
    assert_sha256(blocked.derived_validation_digest)

    assert watched.resolution_rule_risk_score == d("0.272000")
    assert watched.status == "watch"
    assert watched.human_research_priority == "elevated"
    assert watched.reason_codes == (
        "resolution_rule_risk_watch",
        "rule_completeness_watch",
        "resolution_path_ambiguity_watch",
        "dispute_risk_watch",
        "resolution_timing_pressure_watch",
    )

    assert passed.resolution_rule_risk_score == d("0.082500")
    assert passed.status == "pass"
    assert passed.human_research_priority == "routine"
    assert passed.reason_codes == ("resolution_rule_risk_pass",)


def test_decimal_exact_type_rejection_and_frozen_public_dataclasses() -> None:
    module = api()
    result = report(item()).results[0]

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="rule_completeness_score must be a Decimal"):
        item(rule_completeness_score=1)
    with pytest.raises(ValueError, match="resolution_path_ambiguity_score must be a Decimal"):
        item(resolution_path_ambiguity_score=0.1)
    with pytest.raises(ValueError, match="dispute_risk_score must be a Decimal"):
        item(dispute_risk_score=DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="resolution_timing_pressure_score must be a Decimal"):
        item(resolution_timing_pressure_score=DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="max_pass_risk_score must be a Decimal"):
        config(max_pass_risk_score=0.25)
    with pytest.raises(ValueError, match="weights must sum"):
        config(resolution_timing_pressure_weight=d("0.100000"))
    with pytest.raises(ValueError, match="inputs items must be"):
        report(object())
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_resolution_rule_risk_gate(
            (item(),),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_public_payload_rejects_sensitive_keys_values_and_trading_language() -> None:
    module = api()

    for forbidden_reference in (
        "raw_candidate_id_123",
        "market_id_123",
        "market_slug_alpha",
        "market question text",
        "source_ref_alpha",
        "source_url_alpha",
        "source_text_alpha",
        "postgres_dsn",
        "table_name",
        "token_value",
        "wallet_auth",
        "order_trade",
        "position_size",
        "buy_sell_recommendation",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            item(research_item_reference=forbidden_reference)

    result = report(item())
    payload = module.research_resolution_rule_risk_gate_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    for forbidden in (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "http",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    ):
        assert forbidden not in rendered

    with pytest.raises(ValueError, match="unsafe public"):
        module.validate_research_resolution_rule_risk_gate_public_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "market_id": "leak"},
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.validate_research_resolution_rule_risk_gate_public_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "safe": "buy now"},
        )


def test_hard_paper_report_readonly_flags_are_enforced() -> None:
    result = report(item())

    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.results[0].paper_only is True
    assert result.results[0].report_only is True
    assert result.results[0].readonly is True

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        item(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result.results[0], readonly=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)


def test_report_and_digest_are_deterministic_decimal_string_public_payloads() -> None:
    module = api()
    first = report(
        item(
            research_item_reference="research_ref_watch",
            rule_completeness_score=d("0.780000"),
            resolution_path_ambiguity_score=d("0.300000"),
            dispute_risk_score=d("0.300000"),
            resolution_timing_pressure_score=d("0.300000"),
        ),
        generated_at=datetime(2026, 7, 7, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    second = report(
        item(
            research_item_reference="research_ref_watch",
            rule_completeness_score=d("0.780000"),
            resolution_path_ambiguity_score=d("0.300000"),
            dispute_risk_score=d("0.300000"),
            resolution_timing_pressure_score=d("0.300000"),
        ),
        generated_at=GENERATED_AT,
    )

    first_payload = module.research_resolution_rule_risk_gate_payload(first)
    second_payload = module.research_resolution_rule_risk_gate_payload(second)

    assert first == second
    assert first_payload == second_payload
    assert first.report_sha256 == second.report_sha256
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert first_payload["item_count"] == "1.000000"
    assert first_payload["average_resolution_rule_risk_score"] == "0.272000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert first_payload["results"][0]["resolution_rule_risk_score"] == "0.272000"
    assert first_payload["results"][0]["status"] == "watch"
    assert first_payload["results"][0]["human_research_priority"] == "elevated"
    assert_no_numeric_payload_values(first_payload)
    assert json.dumps(first_payload, allow_nan=False, sort_keys=True)


def test_module_is_pure_research_only_decimal_only_and_not_wired_to_live_surfaces() -> None:
    module = api()
    source = inspect_source = __import__("inspect").getsource(module)

    assert module.ResearchResolutionRuleRiskGateConfig.__dataclass_params__.frozen
    assert module.ResearchResolutionRuleRiskGateInput.__dataclass_params__.frozen
    assert module.ResearchResolutionRuleRiskGateResult.__dataclass_params__.frozen
    assert module.ResearchResolutionRuleRiskGateReport.__dataclass_params__.frozen
    assert module.__all__ == (
        "DEFAULT_RESEARCH_RESOLUTION_RULE_RISK_GATE_CONFIG_VERSION",
        "ResearchResolutionRuleRiskGateConfig",
        "ResearchResolutionRuleRiskGateInput",
        "ResearchResolutionRuleRiskGateResult",
        "ResearchResolutionRuleRiskGateReport",
        "build_research_resolution_rule_risk_gate",
        "validate_research_resolution_rule_risk_gate_report",
        "validate_research_resolution_rule_risk_gate_public_payload",
        "research_resolution_rule_risk_gate_payload",
    )
    assert "paper_only" in source
    assert "report_only" in source
    assert "readonly" in source

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
    tree = ast.parse(inspect_source)
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
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
