from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_strategy_risk_register"
SOURCE = Path("src/polymarket_alpha_lab/research_strategy_risk_register.py")
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"missing research strategy risk register module: {MODULE_NAME}")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": module.DEFAULT_RESEARCH_STRATEGY_RISK_REGISTER_CONFIG_VERSION,
        "watch_rule_risk_score": d("0.300000"),
        "block_rule_risk_score": d("0.700000"),
        "watch_evidence_source_risk_score": d("0.300000"),
        "block_evidence_source_risk_score": d("0.700000"),
        "watch_cost_risk_score": d("0.300000"),
        "block_cost_risk_score": d("0.700000"),
        "watch_team_capacity_risk_score": d("0.300000"),
        "block_team_capacity_risk_score": d("0.700000"),
        "watch_composite_risk_score": d("0.250000"),
        "block_composite_risk_score": d("0.650000"),
    }
    values.update(overrides)
    return module.ResearchStrategyRiskRegisterConfig(**values)


def observation(
    *,
    rule_risk_score: Decimal = d("0.100000"),
    evidence_source_risk_score: Decimal = d("0.100000"),
    cost_risk_score: Decimal = d("0.100000"),
    team_capacity_risk_score: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchStrategyRiskRegisterObservation(
        rule_risk_score=rule_risk_score,
        evidence_source_risk_score=evidence_source_risk_score,
        cost_risk_score=cost_risk_score,
        team_capacity_risk_score=team_capacity_risk_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_register(*rows: object, **overrides: object) -> Any:
    module = api()
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    selected_config = overrides.pop("config", None)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    return module.build_research_strategy_risk_register(
        rows,
        config=selected_config or config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_register_rolls_up_rule_source_cost_and_team_capacity_risks() -> None:
    report = build_register(
        observation(),
        observation(
            rule_risk_score=d("0.400000"),
            evidence_source_risk_score=d("0.200000"),
            cost_risk_score=d("0.150000"),
            team_capacity_risk_score=d("0.200000"),
        ),
        observation(
            rule_risk_score=d("0.800000"),
            evidence_source_risk_score=d("0.750000"),
            cost_risk_score=d("0.900000"),
            team_capacity_risk_score=d("0.700000"),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-strategy-risk-register-v0"
    assert report.register_status == "block"
    assert report.entry_count == d("3")
    assert report.pass_entry_count == d("1")
    assert report.watch_entry_count == d("1")
    assert report.block_entry_count == d("1")
    assert report.average_composite_risk_score == d("0.375000")
    assert report.max_composite_risk_score == d("0.787500")
    assert report.max_rule_risk_score == d("0.800000")
    assert report.max_evidence_source_risk_score == d("0.750000")
    assert report.max_cost_risk_score == d("0.900000")
    assert report.max_team_capacity_risk_score == d("0.700000")
    assert report.reason_codes == (
        "strategy_risk_register_entries_block",
        "rule_risk_block",
        "evidence_source_risk_block",
        "cost_risk_block",
        "team_capacity_risk_block",
        "rule_risk_watch",
    )
    assert report.risk_summary == (
        "register_status=block",
        "entry_count=3",
        "block_entry_count=1",
        "watch_entry_count=1",
        "pass_entry_count=1",
        "average_composite_risk_score=0.375000",
        "max_composite_risk_score=0.787500",
        "reason=strategy_risk_register_entries_block count=1",
        "reason=rule_risk_block count=1",
        "reason=evidence_source_risk_block count=1",
        "reason=cost_risk_block count=1",
        "reason=team_capacity_risk_block count=1",
        "reason=rule_risk_watch count=1",
    )

    assert tuple(row.risk_status for row in report.rows) == ("block", "watch", "pass")
    assert report.rows[0].composite_risk_score == d("0.787500")
    assert report.rows[0].reason_codes == (
        "rule_risk_block",
        "evidence_source_risk_block",
        "cost_risk_block",
        "team_capacity_risk_block",
        "composite_risk_block",
    )
    assert report.rows[1].composite_risk_score == d("0.237500")
    assert report.rows[1].reason_codes == ("rule_risk_watch",)
    assert report.rows[2].reason_codes == ("strategy_risk_register_entry_pass",)


def test_empty_register_is_report_only_block_with_zero_decimals() -> None:
    report = build_register()

    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.register_status == "block"
    assert report.entry_count == d("0")
    assert report.pass_entry_count == d("0")
    assert report.watch_entry_count == d("0")
    assert report.block_entry_count == d("0")
    assert report.average_composite_risk_score == d("0.000000")
    assert report.max_composite_risk_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("strategy_risk_register_no_entries_block",)
    assert report.risk_summary == (
        "register_status=block",
        "entry_count=0",
        "block_entry_count=0",
        "watch_entry_count=0",
        "pass_entry_count=0",
        "average_composite_risk_score=0.000000",
        "max_composite_risk_score=0.000000",
        "reason=strategy_risk_register_no_entries_block count=1",
    )


def test_public_payload_is_sanitized_decimal_stringed_and_digest_backed() -> None:
    module = api()
    report = build_register(
        observation(
            rule_risk_score=d("0.800000"),
            evidence_source_risk_score=d("0.750000"),
            cost_risk_score=d("0.900000"),
            team_capacity_risk_score=d("0.700000"),
        ),
    )

    payload = module.research_strategy_risk_register_payload(report)
    json.dumps(payload)
    payload_text = repr(payload).lower()

    assert payload == report.payload
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["entry_count"] == "1"
    assert payload["max_cost_risk_score"] == "0.900000"
    assert payload["risk_summary_digest"] == report.risk_summary_digest
    assert len(report.risk_summary_digest) == 64
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)

    forbidden_public_fragments = (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "http://",
        "https://",
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
    )
    for fragment in forbidden_public_fragments:
        assert fragment not in payload_text


def test_dataclasses_are_frozen_decimal_only_exact_and_hard_flagged() -> None:
    module = api()
    sample_config = config()
    sample_observation = observation()
    report = build_register(sample_observation)
    row = report.rows[0]
    reason_count = report.reason_code_counts[0]

    decimal_fields = {
        "watch_rule_risk_score",
        "block_rule_risk_score",
        "watch_evidence_source_risk_score",
        "block_evidence_source_risk_score",
        "watch_cost_risk_score",
        "block_cost_risk_score",
        "watch_team_capacity_risk_score",
        "block_team_capacity_risk_score",
        "watch_composite_risk_score",
        "block_composite_risk_score",
        "rule_risk_score",
        "evidence_source_risk_score",
        "cost_risk_score",
        "team_capacity_risk_score",
        "composite_risk_score",
        "count",
        "entry_count",
        "pass_entry_count",
        "watch_entry_count",
        "block_entry_count",
        "average_rule_risk_score",
        "average_evidence_source_risk_score",
        "average_cost_risk_score",
        "average_team_capacity_risk_score",
        "average_composite_risk_score",
        "max_rule_risk_score",
        "max_evidence_source_risk_score",
        "max_cost_risk_score",
        "max_team_capacity_risk_score",
        "max_composite_risk_score",
    }

    for item in (sample_config, sample_observation, row, reason_count, report):
        assert is_dataclass(item)
        assert getattr(item.__dataclass_params__, "frozen") is True
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            if field.name in decimal_fields:
                assert type(getattr(item, field.name)) is Decimal

    for cls_name in (
        "ResearchStrategyRiskRegisterConfig",
        "ResearchStrategyRiskRegisterObservation",
        "ResearchStrategyRiskRegisterRow",
        "ResearchStrategyRiskRegisterReasonCodeCount",
        "ResearchStrategyRiskRegisterReport",
    ):
        hints = get_type_hints(getattr(module, cls_name))
        for field in fields(getattr(module, cls_name)):
            if field.name in decimal_fields:
                assert hints[field.name] is Decimal

    with pytest.raises(ValueError, match="rule_risk_score must be exactly Decimal"):
        observation(rule_risk_score=Decimal("0.100000"))  # sanity check base path first
        observation(rule_risk_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="rule_risk_score must be exactly Decimal"):
        observation(rule_risk_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="cost_risk_score must be exactly Decimal"):
        observation(cost_risk_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(sample_config, paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(sample_observation, readonly=False)

    class ConfigSubclass(module.ResearchStrategyRiskRegisterConfig):
        pass

    with pytest.raises(ValueError, match="config must be exactly ResearchStrategyRiskRegisterConfig"):
        ConfigSubclass()


def test_report_digest_rejects_tampering() -> None:
    report = build_register(observation())

    with pytest.raises(ValueError, match="risk_summary_digest mismatch"):
        replace(report, average_composite_risk_score=d("0.900000"))


def test_public_payload_rejects_unsafe_keys_and_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public key"):
        module._reject_unsafe_public_payload("payload", {"raw_candidate_id": "x"})
    with pytest.raises(ValueError, match="unsafe public value"):
        module._reject_unsafe_public_payload("payload", {"safe": "https://example.test/x"})
    with pytest.raises(ValueError, match="unsafe public value"):
        module._reject_unsafe_public_payload("payload", {"safe": "wallet token"})


def test_module_stays_pure_manual_research_without_network_persistence_or_execution_surface() -> None:
    module = api()
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    banned_import_roots = {
        "boto3",
        "http",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    banned_call_names = {
        "Request",
        "commit",
        "connect",
        "execute",
        "executemany",
        "open",
        "rollback",
        "urlopen",
    }
    unsafe_public_name_fragments = {
        "auth",
        "buy",
        "candidate_id",
        "dsn",
        "market_id",
        "market_slug",
        "order",
        "position",
        "recommendation",
        "sell",
        "source_ref",
        "source_text",
        "source_url",
        "table",
        "token",
        "trade",
        "wallet",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in banned_import_roots
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in banned_call_names
            if isinstance(func, ast.Attribute):
                assert func.attr not in banned_call_names

    for name in dir(module):
        if name.startswith("_"):
            continue
        folded = name.lower()
        for fragment in unsafe_public_name_fragments:
            assert fragment not in folded
