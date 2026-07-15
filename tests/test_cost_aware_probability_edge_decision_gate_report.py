from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 12, 9, 30, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 12, 9, 15, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/cost_aware_probability_edge_decision_gate_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab.cost_aware_probability_edge_decision_gate_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def sample(reference: str, **overrides: object) -> Any:
    module = api()
    values = {
        "private_research_reference": reference,
        "observed_at": OBSERVED_AT,
        "gross_probability_edge": d("0.080000"),
        "total_cost": d("0.020000"),
        "spread": d("0.006000"),
        "depth": d("1.500000"),
        "capital_lockup": d("0.030000"),
        "resolution_risk": d("0.010000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.CostAwareProbabilityEdgeDecisionGateInput(**values)


def build_report(*inputs: object, config: object | None = None) -> Any:
    module = api()
    return module.build_cost_aware_probability_edge_decision_gate_report(
        inputs,
        generated_at=GENERATED_AT,
        config=config,
    )


def walk_json(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_json(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from walk_json(item)
        return
    yield value


def test_cost_aware_gate_scores_sorts_and_summarizes_manual_review_context() -> None:
    module = api()
    passed = sample("manual-review-pass")
    watched = sample(
        "manual-review-watch",
        gross_probability_edge=d("0.055000"),
        total_cost=d("0.030000"),
        spread=d("0.018000"),
        depth=d("0.850000"),
        capital_lockup=d("0.080000"),
        resolution_risk=d("0.030000"),
    )
    blocked = sample(
        "manual-review-block",
        gross_probability_edge=d("0.040000"),
        total_cost=d("0.070000"),
        spread=d("0.060000"),
        depth=d("0.250000"),
        capital_lockup=d("0.180000"),
        resolution_risk=d("0.090000"),
    )

    report = build_report(passed, watched, blocked)
    repeated_report = build_report(blocked, passed, watched)

    assert type(report) is module.CostAwareProbabilityEdgeDecisionGateReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "blocked"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.mean_gross_edge == d("0.058333")
    assert report.mean_total_cost == d("0.040000")
    assert report.mean_net_edge == d("0.018333")
    assert report.min_net_edge == d("-0.030000")
    assert report.max_spread == d("0.060000")
    assert report.min_depth == d("0.250000")
    assert report.max_capital_lockup == d("0.180000")
    assert report.max_resolution_risk == d("0.090000")
    assert report.reason_codes == (
        "cost_aware_probability_edge_decision_gate_report_blocked",
        "capital_lockup_review",
        "depth_review",
        "net_edge_review",
        "resolution_risk_review",
        "spread_review",
        "total_cost_review",
    )
    assert report.derived_validation_digest == repeated_report.derived_validation_digest

    block_row, watch_row, pass_row = report.rows
    assert [row.status for row in report.rows] == ["blocked", "watch", "pass"]
    assert set(row.status for row in report.rows) <= {"pass", "watch", "blocked"}

    assert block_row.gross_edge == d("0.040000")
    assert block_row.total_cost == d("0.070000")
    assert block_row.net_edge == d("-0.030000")
    assert block_row.reason_codes == (
        "cost_aware_probability_edge_decision_gate_blocked",
        "net_edge_blocked",
        "total_cost_blocked",
        "spread_blocked",
        "depth_blocked",
        "capital_lockup_blocked",
        "resolution_risk_blocked",
    )

    assert watch_row.gross_edge == d("0.055000")
    assert watch_row.total_cost == d("0.030000")
    assert watch_row.net_edge == d("0.025000")
    assert watch_row.reason_codes == (
        "cost_aware_probability_edge_decision_gate_watch",
        "net_edge_watch",
        "total_cost_watch",
        "spread_watch",
        "depth_watch",
        "capital_lockup_watch",
        "resolution_risk_watch",
    )

    assert pass_row.net_edge == d("0.060000")
    assert pass_row.reason_codes == (
        "cost_aware_probability_edge_decision_gate_pass",
    )
    assert len({row.signal_digest for row in report.rows}) == 3
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_input_blocks_with_manual_first_reason_code() -> None:
    report = build_report()

    assert report.status == "blocked"
    assert report.input_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.mean_gross_edge == d("0.000000")
    assert report.mean_total_cost == d("0.000000")
    assert report.mean_net_edge == d("0.000000")
    assert report.min_net_edge == d("0.000000")
    assert report.reason_codes == (
        "missing_cost_aware_probability_edge_decision_gate_inputs",
    )
    assert report.reason_code_counts == ()
    assert report.rows == ()


def test_public_payload_is_json_ready_safe_immutable_and_digest_bound() -> None:
    module = api()
    raw_reference = (
        "raw_candidate=alpha candidate_id=cid market_id=mid market_slug=slug "
        "question text source_url=https://example.invalid/a source_text dsn=postgres "
        "table_name=markets token=secret wallet order trade buy sell size submit sign"
    )
    report = build_report(
        sample(
            raw_reference,
            gross_probability_edge=d("0.040000"),
            total_cost=d("0.070000"),
            spread=d("0.060000"),
            depth=d("0.250000"),
            capital_lockup=d("0.180000"),
            resolution_risk=d("0.090000"),
        ),
    )
    same_instant_report = build_report(
        sample(
            raw_reference,
            observed_at=OBSERVED_AT.astimezone(timezone(timedelta(hours=-4))),
            gross_probability_edge=d("0.040000"),
            total_cost=d("0.070000"),
            spread=d("0.060000"),
            depth=d("0.250000"),
            capital_lockup=d("0.180000"),
            resolution_risk=d("0.090000"),
        ),
    )

    payload = module.cost_aware_probability_edge_decision_gate_report_payload(report)
    rendered_payload = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert report.derived_validation_digest == same_instant_report.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert set(report.derived_validation_digest) <= set("0123456789abcdef")
    assert payload["generated_at"] == "2026-07-12T09:30:00+00:00"
    assert payload["operator_review_context"] == "manual_first_cost_aware_probability_edge_review"
    assert payload["rows"][0]["operator_review_context"] == (
        "manual_first_cost_aware_probability_edge_review"
    )
    assert payload["rows"][0]["net_edge"] == "-0.030000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) in (int, float) for value in walk_json(payload))

    for forbidden in (
        raw_reference,
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question text",
        "source_url",
        "source_text",
        "https://example.invalid/a",
        "dsn=postgres",
        "table_name",
        "token=secret",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "size",
        "submit",
        "sign",
    ):
        assert forbidden.lower() not in rendered_payload.lower()

    with pytest.raises(TypeError, match="payload is immutable"):
        payload["status"] = "pass"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]

    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.cost_aware_probability_edge_decision_gate_report_payload(tampered)

    unsafe_payload = dict(payload)
    unsafe_payload["order_intent"] = "leaked"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.cost_aware_probability_edge_decision_gate_report_payload(unsafe_payload)


def test_contracts_are_frozen_decimal_only_strict_and_flag_locked() -> None:
    module = api()
    report = build_report(sample("strict-contracts"))

    for contract in (
        module.CostAwareProbabilityEdgeDecisionGateConfig,
        module.CostAwareProbabilityEdgeDecisionGateInput,
        module.CostAwareProbabilityEdgeDecisionGateRow,
        module.CostAwareProbabilityEdgeDecisionGateReasonCodeCount,
        module.CostAwareProbabilityEdgeDecisionGateReport,
    ):
        assert contract.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        assert all(field.type not in (int, float) for field in fields(contract))
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"{contract.__name__}Child", (contract,), {})

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        sample("decimal-subclass", total_cost=_DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="datetime"):
        sample("datetime-subclass", observed_at=_DateTimeSubclass(2026, 7, 12, tzinfo=UTC))


def test_owned_module_has_no_persistence_execution_or_order_intent_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    string_values: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
            if isinstance(node.value, str):
                string_values.append(node.value.lower())

    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "supabase",
        "web3",
    }
    assert not (forbidden_import_roots & {name.split(".", 1)[0] for name in imported_modules})

    forbidden_call_names = {
        "connect",
        "execute",
        "executemany",
        "post",
        "put",
        "patch",
        "delete",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "sign_transaction",
    }
    assert not (forbidden_call_names & set(call_names))
    assert not (
        {
            "wallet",
            "auth",
            "private_key",
            "order_execution",
            "live_trading",
            "order_intent",
            "order_size",
            "order_side",
            "submit_order",
            "sign_transaction",
        }
        & set(attribute_names)
    )
    assert not any("order_intent" in value for value in string_values)
    assert not any("order_size" in value for value in string_values)
    assert not any("order_side" in value for value in string_values)
