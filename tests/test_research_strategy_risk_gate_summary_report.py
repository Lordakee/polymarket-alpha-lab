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


MODULE_NAME = "polymarket_alpha_lab.research_strategy_risk_gate_summary_report"
SOURCE = Path("src/polymarket_alpha_lab/research_strategy_risk_gate_summary_report.py")
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"missing research strategy risk gate summary module: {MODULE_NAME}")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": module.DEFAULT_RESEARCH_STRATEGY_RISK_GATE_SUMMARY_CONFIG_VERSION,
        "watch_aggregate_uncertainty_score": d("0.300000"),
        "block_aggregate_uncertainty_score": d("0.700000"),
        "watch_cost_pressure_score": d("0.300000"),
        "block_cost_pressure_score": d("0.700000"),
        "watch_liquidity_quality_floor": d("0.600000"),
        "block_liquidity_quality_floor": d("0.300000"),
        "watch_settlement_risk_score": d("0.300000"),
        "block_settlement_risk_score": d("0.700000"),
        "watch_information_freshness_floor": d("0.700000"),
        "block_information_freshness_floor": d("0.400000"),
        "watch_team_disagreement_score": d("0.300000"),
        "block_team_disagreement_score": d("0.700000"),
        "watch_composite_risk_score": d("0.250000"),
        "block_composite_risk_score": d("0.650000"),
    }
    values.update(overrides)
    return module.ResearchStrategyRiskGateSummaryConfig(**values)


def candidate(
    anonymized_candidate_key: str,
    *,
    aggregate_uncertainty_score: Decimal = d("0.100000"),
    cost_pressure_score: Decimal = d("0.100000"),
    liquidity_quality_score: Decimal = d("0.900000"),
    settlement_risk_score: Decimal = d("0.100000"),
    information_freshness_score: Decimal = d("0.900000"),
    team_disagreement_score: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchStrategyRiskGateCandidate(
        anonymized_candidate_key=anonymized_candidate_key,
        aggregate_uncertainty_score=aggregate_uncertainty_score,
        cost_pressure_score=cost_pressure_score,
        liquidity_quality_score=liquidity_quality_score,
        settlement_risk_score=settlement_risk_score,
        information_freshness_score=information_freshness_score,
        team_disagreement_score=team_disagreement_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*candidates: object, **overrides: object) -> Any:
    module = api()
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    selected_config = overrides.pop("config", None)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    return module.build_research_strategy_risk_gate_summary_report(
        candidates,
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


def test_summary_rolls_up_risk_gate_state_without_decision_language() -> None:
    report = build_report(
        candidate("bucket-pass"),
        candidate(
            "bucket-watch",
            aggregate_uncertainty_score=d("0.400000"),
            cost_pressure_score=d("0.200000"),
            liquidity_quality_score=d("0.550000"),
            settlement_risk_score=d("0.200000"),
            information_freshness_score=d("0.600000"),
            team_disagreement_score=d("0.350000"),
        ),
        candidate(
            "bucket-block",
            aggregate_uncertainty_score=d("0.800000"),
            cost_pressure_score=d("0.750000"),
            liquidity_quality_score=d("0.200000"),
            settlement_risk_score=d("0.700000"),
            information_freshness_score=d("0.300000"),
            team_disagreement_score=d("0.800000"),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-strategy-risk-gate-summary-v0"
    assert report.gate_status == "block"
    assert report.candidate_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_aggregate_uncertainty_score == d("0.433333")
    assert report.average_cost_pressure_score == d("0.350000")
    assert report.average_liquidity_quality_score == d("0.550000")
    assert report.average_settlement_risk_score == d("0.333333")
    assert report.average_information_freshness_score == d("0.600000")
    assert report.average_team_disagreement_score == d("0.416667")
    assert report.average_composite_risk_score == d("0.397222")
    assert report.min_liquidity_quality_score == d("0.200000")
    assert report.min_information_freshness_score == d("0.300000")
    assert report.max_composite_risk_score == d("0.758333")
    assert report.reason_codes == (
        "aggregate_uncertainty_block",
        "cost_pressure_block",
        "liquidity_quality_block",
        "settlement_risk_block",
        "information_freshness_block",
        "team_disagreement_block",
        "composite_risk_block",
        "aggregate_uncertainty_watch",
        "liquidity_quality_watch",
        "information_freshness_watch",
        "team_disagreement_watch",
        "composite_risk_watch",
        "risk_gate_pass",
    )

    assert tuple(row.anonymized_candidate_key for row in report.rows) == (
        "bucket-block",
        "bucket-watch",
        "bucket-pass",
    )
    assert tuple(row.gate_status for row in report.rows) == ("block", "watch", "pass")
    assert report.rows[0].composite_risk_score == d("0.758333")
    assert report.rows[0].reason_codes == (
        "aggregate_uncertainty_block",
        "cost_pressure_block",
        "liquidity_quality_block",
        "settlement_risk_block",
        "information_freshness_block",
        "team_disagreement_block",
        "composite_risk_block",
    )
    assert report.rows[1].composite_risk_score == d("0.333333")
    assert report.rows[1].reason_codes == (
        "aggregate_uncertainty_watch",
        "liquidity_quality_watch",
        "information_freshness_watch",
        "team_disagreement_watch",
        "composite_risk_watch",
    )
    assert report.rows[2].reason_codes == ("risk_gate_pass",)

    payload_text = repr(report.payload).lower()
    for blocked_fragment in ("buy", "sell", "recommend", "position", "sizing"):
        assert blocked_fragment not in payload_text


def test_empty_candidate_set_is_report_only_block() -> None:
    report = build_report()

    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.gate_status == "block"
    assert report.candidate_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.average_composite_risk_score == d("0.000000")
    assert report.max_composite_risk_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("empty_candidate_set_block",)


def test_payload_and_digest_are_deterministic_public_and_decimal_stringed() -> None:
    module = api()
    first = build_report(
        candidate("bucket-b"),
        candidate(
            "bucket-a",
            aggregate_uncertainty_score=d("0.400000"),
            liquidity_quality_score=d("0.550000"),
            information_freshness_score=d("0.600000"),
        ),
    )
    second = build_report(
        candidate(
            "bucket-a",
            aggregate_uncertainty_score=d("0.400000"),
            liquidity_quality_score=d("0.550000"),
            information_freshness_score=d("0.600000"),
        ),
        candidate("bucket-b"),
    )

    payload = module.research_strategy_risk_gate_summary_report_payload(first)
    json.dumps(payload)

    assert payload == first.payload
    assert first.payload == second.payload
    assert first.risk_gate_summary_digest == second.risk_gate_summary_digest
    assert len(first.risk_gate_summary_digest) == 64
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["candidate_count"] == "2"
    assert payload["rows"][0]["composite_risk_score"] == "0.258333"
    assert payload["risk_gate_summary_digest"] == first.risk_gate_summary_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)

    payload_text = repr(payload).lower()
    for blocked_fragment in (
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "source_ref",
        "source_url",
        "http://",
        "https://",
        "wallet",
        "auth",
        "order",
        "trade",
        "live execution",
    ):
        assert blocked_fragment not in payload_text


def test_dataclasses_are_frozen_exact_decimal_only_and_hard_flagged() -> None:
    module = api()
    sample_report = build_report(candidate("bucket-a"))
    sample_row = sample_report.rows[0]

    assert is_dataclass(module.ResearchStrategyRiskGateSummaryConfig)
    assert is_dataclass(module.ResearchStrategyRiskGateCandidate)
    assert is_dataclass(module.ResearchStrategyRiskGateSummaryRow)
    assert is_dataclass(module.ResearchStrategyRiskGateSummaryReport)

    type_hints = get_type_hints(module.ResearchStrategyRiskGateCandidate)
    numeric_field_names = (
        "aggregate_uncertainty_score",
        "cost_pressure_score",
        "liquidity_quality_score",
        "settlement_risk_score",
        "information_freshness_score",
        "team_disagreement_score",
    )
    for field_name in numeric_field_names:
        assert type_hints[field_name] is Decimal

    for dataclass_type in (
        module.ResearchStrategyRiskGateSummaryConfig,
        module.ResearchStrategyRiskGateCandidate,
        module.ResearchStrategyRiskGateSummaryRow,
        module.ResearchStrategyRiskGateSummaryReport,
    ):
        for flag_name in ("paper_only", "report_only", "readonly"):
            flag_field = next(field for field in fields(dataclass_type) if field.name == flag_name)
            assert flag_field.default is True

    with pytest.raises(ValueError, match="config_version"):
        config(config_version="custom")
    with pytest.raises(ValueError, match="watch_cost_pressure_score"):
        config(watch_cost_pressure_score=1)
    with pytest.raises(ValueError, match="watch_cost_pressure_score"):
        config(watch_cost_pressure_score=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="block_liquidity_quality_floor"):
        config(block_liquidity_quality_floor=d("0.800000"))
    with pytest.raises(ValueError, match="aggregate_uncertainty_score"):
        candidate("bucket-a", aggregate_uncertainty_score=0.1)
    with pytest.raises(ValueError, match="cost_pressure_score"):
        candidate("bucket-a", cost_pressure_score=d("0.10"))
    with pytest.raises(ValueError, match="liquidity_quality_score"):
        candidate("bucket-a", liquidity_quality_score=d("NaN"))
    with pytest.raises(ValueError, match="gate_status"):
        module.ResearchStrategyRiskGateSummaryRow(
            anonymized_candidate_key="bucket-a",
            aggregate_uncertainty_score=d("0.100000"),
            cost_pressure_score=d("0.100000"),
            liquidity_quality_score=d("0.900000"),
            settlement_risk_score=d("0.100000"),
            information_freshness_score=d("0.900000"),
            team_disagreement_score=d("0.100000"),
            composite_risk_score=d("0.100000"),
            gate_status="blocked",
            reason_codes=("risk_gate_pass",),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate("bucket-a"), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    with pytest.raises(FrozenInstanceError):
        sample_report.paper_only = False
    with pytest.raises(FrozenInstanceError):
        sample_row.gate_status = "block"


@pytest.mark.parametrize(
    "unsafe_key",
    (
        "event_id:abc",
        "market_id:abc",
        "market_slug:abc",
        "source_ref:abc",
        "https://example.test/source",
        "wallet-token",
        "auth-token",
        "order-ticket",
        "trade-ticket",
        "live execution",
        "buy sell recommendation",
        "position sizing",
    ),
)
def test_rejects_raw_identifiers_and_live_decision_surfaces(unsafe_key: str) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        candidate(unsafe_key)


def test_module_has_no_db_network_wallet_or_execution_surfaces() -> None:
    tree = ast.parse(SOURCE.read_text())
    imported_roots: set[str] = set()
    call_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "socket",
            "sqlite3",
            "psycopg",
            "supabase",
            "web3",
            "subprocess",
        },
    )
    assert call_names.isdisjoint(
        {
            "connect",
            "request",
            "post",
            "put",
            "patch",
            "delete",
            "send",
            "order",
            "trade",
            "execute",
        },
    )
