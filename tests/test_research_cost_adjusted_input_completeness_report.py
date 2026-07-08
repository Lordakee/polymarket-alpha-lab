from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_cost_adjusted_input_completeness_report import (
    DEFAULT_RESEARCH_COST_ADJUSTED_INPUT_COMPLETENESS_CONFIG_VERSION,
    CostAdjustedInputCompletenessConfig,
    CostAdjustedInputCompletenessInput,
    CostAdjustedInputCompletenessReasonCodeCount,
    CostAdjustedInputCompletenessReport,
    CostAdjustedInputCompletenessRow,
    build_research_cost_adjusted_input_completeness_report,
    research_cost_adjusted_input_completeness_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 14, 30, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 13, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> CostAdjustedInputCompletenessConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_COST_ADJUSTED_INPUT_COMPLETENESS_CONFIG_VERSION
        ),
        "pass_min_completeness_score": d("0.850000"),
        "watch_min_completeness_score": d("0.650000"),
        "max_pass_total_cost_rate": d("0.030000"),
        "max_watch_total_cost_rate": d("0.060000"),
        "max_pass_spread_rate": d("0.020000"),
        "max_watch_spread_rate": d("0.040000"),
        "min_pass_liquidity_quality": d("0.700000"),
        "min_watch_liquidity_quality": d("0.400000"),
        "min_pass_evidence_freshness": d("0.750000"),
        "min_watch_evidence_freshness": d("0.500000"),
        "min_pass_rule_clarity": d("0.800000"),
        "min_watch_rule_clarity": d("0.550000"),
    }
    values.update(overrides)
    return CostAdjustedInputCompletenessConfig(**values)


def input_row(
    *,
    spread_rate: Decimal = d("0.010000"),
    taker_fee_rate: Decimal = d("0.004000"),
    deposit_friction_rate: Decimal = d("0.002000"),
    settlement_friction_rate: Decimal = d("0.003000"),
    gas_friction_rate: Decimal = d("0.001000"),
    liquidity_quality: Decimal = d("0.900000"),
    evidence_freshness: Decimal = d("0.950000"),
    rule_clarity: Decimal = d("0.900000"),
    observed_at: datetime = OBSERVED_AT,
    reason_codes: tuple[str, ...] = ("manual_inputs_collected",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> CostAdjustedInputCompletenessInput:
    return CostAdjustedInputCompletenessInput(
        spread_rate=spread_rate,
        taker_fee_rate=taker_fee_rate,
        deposit_friction_rate=deposit_friction_rate,
        settlement_friction_rate=settlement_friction_rate,
        gas_friction_rate=gas_friction_rate,
        liquidity_quality=liquidity_quality,
        evidence_freshness=evidence_freshness,
        rule_clarity=rule_clarity,
        observed_at=observed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: CostAdjustedInputCompletenessInput,
    cfg: CostAdjustedInputCompletenessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> CostAdjustedInputCompletenessReport:
    return build_research_cost_adjusted_input_completeness_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload_values(item))
        return tuple(values)
    return (value,)


def test_builds_pass_watch_and_block_report_only_completeness_rows() -> None:
    completeness_report = report(
        input_row(
            spread_rate=d("0.050000"),
            taker_fee_rate=d("0.010000"),
            deposit_friction_rate=d("0.010000"),
            settlement_friction_rate=d("0.010000"),
            gas_friction_rate=d("0.005000"),
            liquidity_quality=d("0.250000"),
            evidence_freshness=d("0.350000"),
            rule_clarity=d("0.400000"),
            reason_codes=("manual_inputs_collected", "desk_escalation"),
        ),
        input_row(
            spread_rate=d("0.025000"),
            taker_fee_rate=d("0.006000"),
            deposit_friction_rate=d("0.004000"),
            settlement_friction_rate=d("0.004000"),
            gas_friction_rate=d("0.001000"),
            liquidity_quality=d("0.550000"),
            evidence_freshness=d("0.650000"),
            rule_clarity=d("0.650000"),
        ),
        input_row(reason_codes=("all_inputs_ready",)),
    )

    assert is_dataclass(completeness_report)
    assert type(completeness_report) is CostAdjustedInputCompletenessReport
    assert completeness_report.generated_at == GENERATED_AT
    assert completeness_report.config_version == (
        "research-cost-adjusted-input-completeness-report-v0"
    )
    assert completeness_report.input_count == d("3.000000")
    assert completeness_report.pass_count == d("1.000000")
    assert completeness_report.watch_count == d("1.000000")
    assert completeness_report.block_count == d("1.000000")
    assert completeness_report.max_total_cost_rate == d("0.085000")
    assert completeness_report.min_completeness_score == d("0.337500")
    assert completeness_report.status == "block"
    assert completeness_report.summary_explanation == (
        "block: cost-adjusted inputs are incomplete for manual or paper review"
    )
    assert completeness_report.reason_codes == (
        "cost_adjusted_inputs_report_block",
        "cost_adjusted_total_cost_block",
        "cost_adjusted_spread_block",
        "cost_adjusted_liquidity_block",
        "cost_adjusted_evidence_freshness_block",
        "cost_adjusted_rule_clarity_block",
        "cost_adjusted_completeness_block",
        "cost_adjusted_total_cost_watch",
        "cost_adjusted_spread_watch",
        "cost_adjusted_liquidity_watch",
        "cost_adjusted_evidence_freshness_watch",
        "cost_adjusted_rule_clarity_watch",
        "cost_adjusted_completeness_watch",
    )
    assert completeness_report.paper_only is True
    assert completeness_report.report_only is True
    assert completeness_report.readonly is True
    assert len(completeness_report.derived_validation_digest) == 64

    block_row, watch_row, pass_row = completeness_report.rows
    assert tuple(row.status for row in completeness_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert block_row.row_index == d("1.000000")
    assert block_row.total_cost_rate == d("0.085000")
    assert block_row.completeness_score == d("0.337500")
    assert block_row.status_explanation == (
        "block: cost-adjusted inputs are incomplete for manual or paper review"
    )
    assert block_row.reason_codes == (
        "desk_escalation",
        "manual_inputs_collected",
        "cost_adjusted_total_cost_block",
        "cost_adjusted_spread_block",
        "cost_adjusted_liquidity_block",
        "cost_adjusted_evidence_freshness_block",
        "cost_adjusted_rule_clarity_block",
        "cost_adjusted_completeness_block",
    )
    assert watch_row.row_index == d("2.000000")
    assert watch_row.total_cost_rate == d("0.040000")
    assert watch_row.completeness_score == d("0.625000")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "manual_inputs_collected",
        "cost_adjusted_total_cost_watch",
        "cost_adjusted_spread_watch",
        "cost_adjusted_liquidity_watch",
        "cost_adjusted_evidence_freshness_watch",
        "cost_adjusted_rule_clarity_watch",
        "cost_adjusted_completeness_watch",
    )
    assert pass_row.row_index == d("3.000000")
    assert pass_row.total_cost_rate == d("0.020000")
    assert pass_row.completeness_score == d("0.912500")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == (
        "all_inputs_ready",
        "cost_adjusted_inputs_complete",
    )

    assert completeness_report.reason_code_counts[0] == (
        CostAdjustedInputCompletenessReasonCodeCount(
            reason_code="manual_inputs_collected",
            count=d("2.000000"),
            input_ratio=d("0.666667"),
        )
    )


def test_empty_report_blocks_without_review_inputs_and_keeps_hard_flags() -> None:
    completeness_report = report()

    assert completeness_report.input_count == ZERO
    assert completeness_report.pass_count == ZERO
    assert completeness_report.watch_count == ZERO
    assert completeness_report.block_count == ZERO
    assert completeness_report.max_total_cost_rate == ZERO
    assert completeness_report.min_completeness_score == ZERO
    assert completeness_report.status == "block"
    assert completeness_report.summary_explanation == (
        "block: no cost-adjusted inputs supplied for manual or paper review"
    )
    assert completeness_report.reason_codes == ("cost_adjusted_inputs_report_empty",)
    assert completeness_report.reason_code_counts == ()
    assert completeness_report.rows == ()

    populated = report(input_row())
    for value in (
        completeness_report,
        populated,
        *populated.rows,
        *populated.reason_code_counts,
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(
                ("_count", "_rate", "_quality", "_freshness", "_clarity", "_score", "_ratio"),
            ) or item.name == "row_index":
                assert type(item_value) is Decimal

    frozen = input_row()
    with pytest.raises(FrozenInstanceError):
        frozen.spread_rate = d("0.100000")  # type: ignore[misc]


def test_payload_is_deterministic_json_safe_and_has_no_raw_market_or_source_ids() -> None:
    completeness_report = report(
        input_row(
            observed_at=datetime(
                2026,
                7,
                8,
                6,
                45,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            8,
            7,
            30,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )

    payload = research_cost_adjusted_input_completeness_report_payload(
        completeness_report,
    )
    repeated_payload = research_cost_adjusted_input_completeness_report_payload(
        completeness_report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == repeated_payload
    assert payload["generated_at"] == "2026-07-08T14:30:00+00:00"
    assert payload["rows"][0]["observed_at"] == "2026-07-08T13:45:00+00:00"
    assert payload["rows"][0]["total_cost_rate"] == "0.020000"
    assert payload["rows"][0]["completeness_score"] == "0.912500"
    assert "market" not in encoded.lower()
    assert "source" not in encoded.lower()
    assert "identifier" not in encoded.lower()
    assert not any(
        type(value) in (int, float, Decimal) for value in walk_payload_values(payload)
    )
    assert completeness_report.derived_validation_digest == (
        research_cost_adjusted_input_completeness_report_payload(
            completeness_report,
        )["derived_validation_digest"]
    )


def test_validation_rejects_non_decimal_types_bad_thresholds_terms_and_flags() -> None:
    with pytest.raises(ValueError, match="spread_rate"):
        input_row(spread_rate=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="taker_fee_rate"):
        input_row(taker_fee_rate=_DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="liquidity_quality"):
        input_row(liquidity_quality=d("1.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 8, 14, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            input_row(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 14, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("source_api_seen",))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="pass_min_completeness_score"):
        config(pass_min_completeness_score=d("0.600000"))
    with pytest.raises(ValueError, match="max_watch_total_cost_rate"):
        config(max_watch_total_cost_rate=d("0.020000"))
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="custom")


def test_report_rejects_impure_inputs_and_does_not_expose_execution_surfaces() -> None:
    impure_input = input_row()
    object.__setattr__(impure_input, "readonly", False)
    with pytest.raises(ValueError, match="inputs"):
        build_research_cost_adjusted_input_completeness_report(
            (impure_input,),
            config=config(),
            generated_at=GENERATED_AT,
        )

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_cost_adjusted_input_completeness_report.py"
    )
    tree = ast.parse(module_path.read_text())
    banned_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "post",
        "put",
        "delete",
        "wallet",
        "auth",
        "order",
        "trade",
        "sign",
    }
    banned_import_roots = {
        "os",
        "socket",
        "sqlite3",
        "subprocess",
        "requests",
        "urllib",
        "httpx",
        "web3",
        "psycopg",
        "supabase",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = ""
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            assert name.lower() not in banned_calls
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned_import_roots
