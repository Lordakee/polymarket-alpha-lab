from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.probability_event_expected_utility_rank_readiness_report as api
from polymarket_alpha_lab.probability_event_expected_utility_rank_readiness_report import (
    ProbabilityEventExpectedUtilityRankReadinessInput,
    ProbabilityEventExpectedUtilityRankReadinessReport,
    build_probability_event_expected_utility_rank_readiness_report,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_expected_utility_rank_readiness_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def readiness_input(
    *,
    net_edge_probability: Decimal = ONE,
    confidence_probability: Decimal = ONE,
    liquidity_probability: Decimal = ONE,
    cost_probability: Decimal = ONE,
    capital_lockup_probability: Decimal = ONE,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventExpectedUtilityRankReadinessInput:
    return ProbabilityEventExpectedUtilityRankReadinessInput(
        net_edge_probability=net_edge_probability,
        confidence_probability=confidence_probability,
        liquidity_probability=liquidity_probability,
        cost_probability=cost_probability,
        capital_lockup_probability=capital_lockup_probability,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    readiness: ProbabilityEventExpectedUtilityRankReadinessInput,
) -> ProbabilityEventExpectedUtilityRankReadinessReport:
    return build_probability_event_expected_utility_rank_readiness_report(readiness)


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_ready_candidate_ranks_for_manual_review_only() -> None:
    readiness = report(readiness_input())

    assert is_dataclass(readiness)
    assert readiness.rank_status == "ready_for_manual_rank"
    assert readiness.expected_utility_score == ONE
    assert readiness.reason_codes == ("probability_event_expected_utility_rank_ready",)
    assert readiness.manual_next_step == (
        "Manually compare this report-only candidate against other readonly "
        "probability events before any operator-authorized action."
    )
    assert readiness.paper_only is True
    assert readiness.report_only is True
    assert readiness.readonly is True

    assert readiness.public_payload == {
        "rank_status": "ready_for_manual_rank",
        "expected_utility_score": "1.000000",
        "reason_codes": ["probability_event_expected_utility_rank_ready"],
        "manual_next_step": (
            "Manually compare this report-only candidate against other readonly "
            "probability events before any operator-authorized action."
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert readiness.payload_digest == api.probability_event_expected_utility_rank_payload_digest(
        readiness.public_payload,
    )
    assert_no_float_or_int_values(readiness.public_payload)


def test_expected_utility_score_is_decimal_product_and_reason_codes_explain_drag() -> None:
    readiness = report(
        readiness_input(
            net_edge_probability=d("0.800000"),
            confidence_probability=d("0.750000"),
            liquidity_probability=d("0.500000"),
            cost_probability=d("0.900000"),
            capital_lockup_probability=d("0.600000"),
        ),
    )

    assert readiness.rank_status == "manual_rank_attention"
    assert readiness.expected_utility_score == d("0.162000")
    assert readiness.reason_codes == (
        "probability_event_expected_utility_net_edge_attention",
        "probability_event_expected_utility_confidence_attention",
        "probability_event_expected_utility_liquidity_attention",
        "probability_event_expected_utility_cost_attention",
        "probability_event_expected_utility_capital_lockup_attention",
    )
    assert readiness.public_payload["expected_utility_score"] == "0.162000"
    assert readiness.payload_digest == api.probability_event_expected_utility_rank_payload_digest(
        readiness.public_payload,
    )


def test_zero_component_blocks_manual_rank_until_research_resolves_gap() -> None:
    readiness = report(
        readiness_input(
            net_edge_probability=d("0.700000"),
            confidence_probability=ZERO,
            liquidity_probability=d("0.800000"),
        ),
    )

    assert readiness.rank_status == "manual_rank_blocked"
    assert readiness.expected_utility_score == ZERO
    assert readiness.reason_codes == (
        "probability_event_expected_utility_confidence_blocked",
        "probability_event_expected_utility_net_edge_attention",
        "probability_event_expected_utility_liquidity_attention",
    )
    assert readiness.manual_next_step == (
        "Resolve blocked probability inputs before manually ranking this "
        "paper-only candidate."
    )


def test_dataclasses_are_frozen_decimal_only_and_flags_are_enforced() -> None:
    readiness = report(readiness_input())

    with pytest.raises(FrozenInstanceError):
        readiness.rank_status = "manual_rank_blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventExpectedUtilityRankReadinessInput):
            pass

    with pytest.raises(ValueError, match="net_edge_probability must be a Decimal"):
        readiness_input(net_edge_probability=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="net_edge_probability must be between"):
        readiness_input(net_edge_probability=d("1.100000"))

    with pytest.raises(ValueError, match="paper_only"):
        readiness_input(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        readiness_input(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(readiness, readonly=False)

    with pytest.raises(ValueError, match="payload_digest"):
        replace(readiness, payload_digest="bad-digest")


def test_public_api_excludes_execution_auth_wallet_persistence_and_side_effect_surfaces() -> None:
    forbidden_fragments = (
        "live",
        "auth",
        "wallet",
        "key",
        "sign",
        "execute",
        "order",
        "trade",
        "database",
        "jsonl",
        "persist",
        "file",
        "network",
        "request",
        "http",
        "broker",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (
        ProbabilityEventExpectedUtilityRankReadinessInput,
        ProbabilityEventExpectedUtilityRankReadinessReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
        "open",
        "Path",
    ):
        assert not hasattr(api, forbidden_name)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    forbidden_calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                forbidden_calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                forbidden_calls.add(node.func.attr)

    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "psycopg",
            "web3",
            "ccxt",
            "subprocess",
            "pathlib",
        },
    )
    assert forbidden_calls.isdisjoint({"open", "write", "dump", "dumps"})
    assert json.dumps(readiness_input().__dict__, default=str)
