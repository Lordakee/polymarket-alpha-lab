from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_probability_change_explanation_quality_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_strategy_probability_change_explanation_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _input(
    quality_key: str = "case_pass",
    *,
    probability_change_abs: Decimal = d("0.030000"),
    explanation_completeness_score: Decimal = d("0.900000"),
    evidence_linkage_score: Decimal = d("0.850000"),
    cost_context_coverage_score: Decimal = d("0.800000"),
    settlement_rule_clarity_score: Decimal = d("0.900000"),
    explanation_observed_at: datetime = GENERATED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchStrategyProbabilityChangeExplanationQualityInput(
        quality_key=quality_key,
        probability_change_abs=probability_change_abs,
        explanation_completeness_score=explanation_completeness_score,
        evidence_linkage_score=evidence_linkage_score,
        cost_context_coverage_score=cost_context_coverage_score,
        settlement_rule_clarity_score=settlement_rule_clarity_score,
        explanation_observed_at=explanation_observed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _config(**overrides: object):
    module = api()
    return module.ResearchStrategyProbabilityChangeExplanationQualityConfig(**overrides)


def _build_report(*rows, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_probability_change_explanation_quality_report(
        rows,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def test_probability_change_explanation_quality_rollup_flags_pass_watch_block() -> None:
    module = api()
    pass_input = _input(
        "case_pass",
        probability_change_abs=d("0.030000"),
        explanation_completeness_score=d("0.900000"),
        evidence_linkage_score=d("0.850000"),
        cost_context_coverage_score=d("0.800000"),
        settlement_rule_clarity_score=d("0.900000"),
    )
    watch_input = _input(
        "case_watch",
        probability_change_abs=d("0.070000"),
        explanation_completeness_score=d("0.720000"),
        evidence_linkage_score=d("0.650000"),
        cost_context_coverage_score=d("0.700000"),
        settlement_rule_clarity_score=d("0.820000"),
    )
    block_input = _input(
        "case_block",
        probability_change_abs=d("0.120000"),
        explanation_completeness_score=d("0.450000"),
        evidence_linkage_score=d("0.350000"),
        cost_context_coverage_score=d("0.500000"),
        settlement_rule_clarity_score=d("0.650000"),
    )

    report = _build_report(pass_input, watch_input, block_input)
    permuted = _build_report(block_input, pass_input, watch_input)
    payload = module.research_strategy_probability_change_explanation_quality_report_payload(
        report,
    )
    permuted_payload = (
        module.research_strategy_probability_change_explanation_quality_report_payload(
            permuted,
        )
    )

    assert is_dataclass(report)
    assert report.status == "block"
    assert report.quality_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.large_probability_change_count == d("2.000000")
    assert report.explanation_completeness_gap_count == d("2.000000")
    assert report.evidence_linkage_gap_count == d("2.000000")
    assert report.cost_context_gap_count == d("2.000000")
    assert report.settlement_rule_clarity_gap_count == d("1.000000")
    assert report.average_probability_change_abs == d("0.073333")
    assert report.average_quality_score == d("0.690833")
    assert report.max_deficiency_score == d("0.512500")
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.quality_key for row in report.rows) == (
        "case_block",
        "case_watch",
        "case_pass",
    )

    blocked = report.rows[0]
    assert blocked.rank == d("1.000000")
    assert blocked.quality_score == d("0.487500")
    assert blocked.deficiency_score == d("0.512500")
    assert blocked.reason_codes == (
        "probability_change_explanation_quality_block",
        "large_probability_change_quality_gap_block",
        "explanation_completeness_low_block",
        "evidence_linkage_low_block",
        "cost_context_missing_watch",
        "settlement_rule_clarity_low_watch",
    )

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.quality_score == d("0.722500")
    assert watched.reason_codes == (
        "probability_change_explanation_quality_watch",
        "large_probability_change_quality_gap_watch",
        "explanation_completeness_low_watch",
        "evidence_linkage_low_watch",
        "cost_context_missing_watch",
    )

    passing = report.rows[2]
    assert passing.status == "pass"
    assert passing.reason_codes == ("probability_change_explanation_quality_pass",)

    assert report.reason_codes == (
        "probability_change_explanation_quality_block",
        "probability_change_explanation_quality_watch",
        "probability_change_explanation_quality_pass",
        "large_probability_change_quality_gap_block",
        "large_probability_change_quality_gap_watch",
        "explanation_completeness_low_block",
        "explanation_completeness_low_watch",
        "evidence_linkage_low_block",
        "evidence_linkage_low_watch",
        "cost_context_missing_watch",
        "settlement_rule_clarity_low_watch",
    )
    assert payload == permuted_payload
    assert payload["public_payload_digest"] == report.public_payload_digest
    assert payload["rows"][0]["quality_score"] == "0.487500"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(report.public_payload_digest) == 64
    int(report.public_payload_digest, 16)
    assert report.public_payload_digest == (
        module.research_strategy_probability_change_explanation_quality_digest(report)
    )
    assert _number_paths(payload) == ()
    assert _forbidden_key_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_empty_report_blocks_as_missing_explanation_quality_inputs() -> None:
    module = api()
    local_generated_at = datetime(
        2026,
        7,
        8,
        14,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    report = _build_report(generated_at=local_generated_at)
    payload = module.research_strategy_probability_change_explanation_quality_report_payload(
        report,
    )

    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.quality_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "probability_change_explanation_quality_missing_inputs",
    )
    assert payload["status"] == "block"
    assert payload["generated_at"] == "2026-07-08T18:00:00+00:00"
    assert payload["rows"] == []
    assert payload["public_payload_digest"] == report.public_payload_digest


def test_decimal_frozen_flags_and_digest_tampering_are_validated() -> None:
    module = api()
    report = _build_report(_input())

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report, status="blocked")
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="probability_change_abs must be a Decimal"):
        _input(probability_change_abs=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_linkage_score must be a Decimal"):
        _input(evidence_linkage_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        _input(paper_only=False)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="report_only must be True"):
        _config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="public_payload_digest"):
        replace(report, public_payload_digest="0" * 64)
    with pytest.raises(ValueError, match="public_payload_digest"):
        replace(report, watch_count=d("2.000000"))

    assert module.research_strategy_probability_change_explanation_quality_digest_payload(
        report,
    ) == module.research_strategy_probability_change_explanation_quality_digest_payload(
        _build_report(_input()),
    )


def test_datetime_and_config_thresholds_are_strict() -> None:
    module = api()

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        module.build_research_strategy_probability_change_explanation_quality_report(
            (),
            generated_at=_DatetimeSubclass(2026, 7, 8, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="explanation_observed_at must be timezone-aware"):
        _input(explanation_observed_at=datetime(2026, 7, 8, 18, 0))

    class _NoneOffsetTz(tzinfo):
        def utcoffset(self, dt):
            return None

        def dst(self, dt):
            return None

    with pytest.raises(ValueError, match="explanation_observed_at must be timezone-aware"):
        _input(
            explanation_observed_at=datetime(2026, 7, 8, 18, 0, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="explanation_observed_at must not be after"):
        _build_report(
            _input(explanation_observed_at=GENERATED_AT + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="block_probability_change_threshold"):
        _config(
            watch_probability_change_threshold=d("0.200000"),
            block_probability_change_threshold=d("0.100000"),
        )
    with pytest.raises(ValueError, match="explanation_completeness"):
        _config(
            watch_explanation_completeness=d("0.400000"),
            block_explanation_completeness=d("0.500000"),
        )
    with pytest.raises(ValueError, match="settlement_rule_clarity"):
        _config(
            watch_settlement_rule_clarity=d("0.300000"),
            block_settlement_rule_clarity=d("0.400000"),
        )


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "candidate_case",
        "market_slug",
        "question_url",
        "raw_table_name",
        "wallet_order_trade",
        "buy_sell_recommendation",
    ),
)
def test_public_key_rejects_raw_identifiers_and_execution_surfaces(
    unsafe_value: str,
) -> None:
    with pytest.raises(ValueError, match="quality_key"):
        _input(quality_key=unsafe_value)


def test_public_report_rejects_nondeterministic_sequence_and_reason_codes() -> None:
    module = api()
    report = _build_report(
        _input(
            "case_block",
            probability_change_abs=d("0.120000"),
            explanation_completeness_score=d("0.450000"),
            evidence_linkage_score=d("0.350000"),
            cost_context_coverage_score=d("0.500000"),
            settlement_rule_clarity_score=d("0.650000"),
        ),
        _input("case_pass"),
    )

    with pytest.raises(ValueError, match="rows must use deterministic sequence"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="reason_codes must use deterministic sequence"):
        module.ResearchStrategyProbabilityChangeExplanationQualityRow(
            rank=d("1.000000"),
            quality_key="case_watch",
            explanation_observed_at=GENERATED_AT,
            probability_change_abs=d("0.070000"),
            explanation_completeness_score=d("0.720000"),
            evidence_linkage_score=d("0.650000"),
            cost_context_coverage_score=d("0.700000"),
            settlement_rule_clarity_score=d("0.820000"),
            quality_score=d("0.722500"),
            deficiency_score=d("0.277500"),
            status="watch",
            reason_codes=(
                "evidence_linkage_low_watch",
                "probability_change_explanation_quality_watch",
            ),
        )


def test_module_exposes_no_forbidden_surfaces_or_literal_float_constants() -> None:
    module = api()
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    public_forbidden = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "database",
        "network",
        "auth",
        "live",
        "raw",
    )
    runtime_forbidden = (
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
        "open",
    )
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )

    for forbidden in public_forbidden:
        assert forbidden not in lowered
    for public_name in module.__all__:
        lowered_name = public_name.lower()
        assert not any(term in lowered_name for term in public_forbidden)
    for cls in (
        module.ResearchStrategyProbabilityChangeExplanationQualityConfig,
        module.ResearchStrategyProbabilityChangeExplanationQualityInput,
        module.ResearchStrategyProbabilityChangeExplanationQualityRow,
        module.ResearchStrategyProbabilityChangeExplanationQualityReasonCodeCount,
        module.ResearchStrategyProbabilityChangeExplanationQualityReport,
    ):
        for field in fields(cls):
            lowered_name = field.name.lower()
            assert not any(term in lowered_name for term in public_forbidden)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"

    assert not calls.intersection(runtime_forbidden)
    assert not imports.intersection(runtime_forbidden)
    assert not any(hasattr(module, name) for name in runtime_forbidden)


def _number_paths(value: object, path: str = "") -> tuple[str, ...]:
    if type(value) in (float, int):
        return (path or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_number_paths(item, f"{path}.{key}" if path else str(key)))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_number_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _forbidden_key_paths(value: object, path: str = "") -> tuple[str, ...]:
    forbidden = ("candidate", "market", "slug", "question", "url", "dsn", "table")
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            current_path = f"{path}.{key}" if path else str(key)
            if any(fragment in str(key).lower() for fragment in forbidden):
                paths.append(current_path)
            paths.extend(_forbidden_key_paths(item, current_path))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_forbidden_key_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()
