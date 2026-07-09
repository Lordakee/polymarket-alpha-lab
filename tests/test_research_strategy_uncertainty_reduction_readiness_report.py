from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_uncertainty_reduction_readiness_report import (
    DEFAULT_RESEARCH_STRATEGY_UNCERTAINTY_REDUCTION_READINESS_CONFIG_VERSION,
    ResearchStrategyUncertaintyReductionReadinessCandidate,
    ResearchStrategyUncertaintyReductionReadinessConfig,
    ResearchStrategyUncertaintyReductionReadinessReasonCodeCount,
    ResearchStrategyUncertaintyReductionReadinessReport,
    ResearchStrategyUncertaintyReductionReadinessRow,
    build_research_strategy_uncertainty_reduction_readiness_report,
    research_strategy_uncertainty_reduction_readiness_digest,
    research_strategy_uncertainty_reduction_readiness_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_uncertainty_reduction_readiness_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategyUncertaintyReductionReadinessConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_UNCERTAINTY_REDUCTION_READINESS_CONFIG_VERSION
        ),
        "pass_min_reduction_readiness_score": d("0.700000"),
        "watch_min_reduction_readiness_score": d("0.400000"),
        "current_uncertainty_weight": d("0.200000"),
        "source_freshness_weight": d("0.150000"),
        "evidence_quality_weight": d("0.150000"),
        "liquidity_reliability_weight": d("0.150000"),
        "cost_drag_weight": d("0.100000"),
        "resolution_clarity_weight": d("0.150000"),
        "specialist_memory_confidence_weight": d("0.100000"),
        "source_freshness_watch_age_seconds": d("3600.000000"),
        "source_freshness_block_age_seconds": d("14400.000000"),
        "cost_drag_watch_score": d("0.300000"),
        "cost_drag_block_score": d("0.700000"),
        "evidence_quality_watch_score": d("0.500000"),
        "evidence_quality_block_score": d("0.350000"),
        "liquidity_reliability_watch_score": d("0.450000"),
        "liquidity_reliability_block_score": d("0.200000"),
        "resolution_clarity_watch_score": d("0.500000"),
        "resolution_clarity_block_score": d("0.250000"),
        "memory_confidence_watch_score": d("0.450000"),
        "memory_confidence_block_score": d("0.200000"),
    }
    values.update(overrides)
    return ResearchStrategyUncertaintyReductionReadinessConfig(**values)


def candidate(
    raw_candidate_id: str,
    *,
    observed_at: datetime = GENERATED_AT,
    current_uncertainty: Decimal = d("0.800000"),
    source_age_seconds: Decimal = d("900.000000"),
    evidence_quality: Decimal = d("0.850000"),
    liquidity_reliability: Decimal = d("0.900000"),
    cost_drag: Decimal = d("0.100000"),
    resolution_clarity: Decimal = d("0.850000"),
    specialist_memory_confidence: Decimal = d("0.800000"),
    sensitive_context: str | None = (
        "candidate-id market-id market-slug question "
        "https://example.invalid/source source text postgres://host/db "
        "signals_table token abc wallet order trade buy sell recommend size"
    ),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyUncertaintyReductionReadinessCandidate:
    return ResearchStrategyUncertaintyReductionReadinessCandidate(
        raw_candidate_id=raw_candidate_id,
        observed_at=observed_at,
        current_uncertainty=current_uncertainty,
        source_age_seconds=source_age_seconds,
        evidence_quality=evidence_quality,
        liquidity_reliability=liquidity_reliability,
        cost_drag=cost_drag,
        resolution_clarity=resolution_clarity,
        specialist_memory_confidence=specialist_memory_confidence,
        sensitive_context=sensitive_context,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchStrategyUncertaintyReductionReadinessCandidate,
    cfg: ResearchStrategyUncertaintyReductionReadinessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyUncertaintyReductionReadinessReport:
    return build_research_strategy_uncertainty_reduction_readiness_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_scores_uncertainty_reduction_readiness_into_pass_watch_block() -> None:
    readiness_report = report(
        candidate("raw-pass"),
        candidate(
            "raw-watch",
            current_uncertainty=d("0.550000"),
            source_age_seconds=d("7200.000000"),
            evidence_quality=d("0.500000"),
            liquidity_reliability=d("0.400000"),
            cost_drag=d("0.350000"),
            resolution_clarity=d("0.450000"),
            specialist_memory_confidence=d("0.400000"),
        ),
        candidate(
            "raw-block",
            current_uncertainty=d("0.150000"),
            source_age_seconds=d("20000.000000"),
            evidence_quality=d("0.300000"),
            liquidity_reliability=d("0.100000"),
            cost_drag=d("0.850000"),
            resolution_clarity=d("0.200000"),
            specialist_memory_confidence=d("0.150000"),
        ),
    )

    assert type(readiness_report) is ResearchStrategyUncertaintyReductionReadinessReport
    assert readiness_report.generated_at == GENERATED_AT
    assert readiness_report.config_version == (
        DEFAULT_RESEARCH_STRATEGY_UNCERTAINTY_REDUCTION_READINESS_CONFIG_VERSION
    )
    assert readiness_report.candidate_count == d("3.000000")
    assert readiness_report.pass_count == ONE
    assert readiness_report.watch_count == ONE
    assert readiness_report.block_count == ONE
    assert readiness_report.mean_reduction_readiness_score == d("0.501042")
    assert readiness_report.mean_current_uncertainty == d("0.500000")
    assert readiness_report.max_cost_drag_score == d("0.850000")
    assert readiness_report.status == "block"
    assert readiness_report.reason_codes == (
        "current_uncertainty_gap_detected",
        "source_freshness_gap_detected",
        "evidence_quality_gap_detected",
        "liquidity_reliability_gap_detected",
        "cost_drag_gap_detected",
        "resolution_clarity_gap_detected",
        "specialist_memory_confidence_gap_detected",
        "composite_reduction_readiness_gap_detected",
    )
    assert readiness_report.paper_only is True
    assert readiness_report.report_only is True
    assert readiness_report.readonly is True

    first, second, third = readiness_report.rows
    assert type(first) is ResearchStrategyUncertaintyReductionReadinessRow
    assert tuple(row.status for row in readiness_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert first.row_number == ONE
    assert first.current_uncertainty_score == d("0.150000")
    assert first.source_freshness_score == ZERO
    assert first.cost_drag_score == d("0.850000")
    assert first.cost_efficiency_score == d("0.150000")
    assert first.reduction_readiness_score == d("0.150000")
    assert first.reason_codes == (
        "current_uncertainty_too_low_blocking",
        "source_freshness_blocking",
        "evidence_quality_blocking",
        "liquidity_reliability_blocking",
        "cost_drag_blocking",
        "resolution_clarity_blocking",
        "specialist_memory_confidence_blocking",
        "composite_reduction_readiness_blocking",
    )
    assert second.reduction_readiness_score == d("0.492500")
    assert second.source_freshness_score == d("0.500000")
    assert second.cost_efficiency_score == d("0.650000")
    assert second.reason_codes == (
        "source_freshness_watch",
        "evidence_quality_watch",
        "liquidity_reliability_watch",
        "cost_drag_watch",
        "resolution_clarity_watch",
        "specialist_memory_confidence_watch",
        "composite_reduction_readiness_watch",
    )
    assert third.reduction_readiness_score == d("0.860625")
    assert third.reason_codes == ("uncertainty_reduction_readiness_clear",)


def test_payload_digest_is_deterministic_public_safe_and_decimal_only() -> None:
    left = report(
        candidate("raw-z-pass"),
        candidate(
            "raw-a-block",
            current_uncertainty=d("0.150000"),
            source_age_seconds=d("20000.000000"),
            evidence_quality=d("0.300000"),
            liquidity_reliability=d("0.100000"),
            cost_drag=d("0.850000"),
            resolution_clarity=d("0.200000"),
            specialist_memory_confidence=d("0.150000"),
        ),
        candidate(
            "raw-m-watch",
            current_uncertainty=d("0.550000"),
            source_age_seconds=d("7200.000000"),
            evidence_quality=d("0.500000"),
            liquidity_reliability=d("0.400000"),
            cost_drag=d("0.350000"),
            resolution_clarity=d("0.450000"),
            specialist_memory_confidence=d("0.400000"),
        ),
    )
    right = report(
        candidate(
            "raw-m-watch",
            current_uncertainty=d("0.550000"),
            source_age_seconds=d("7200.000000"),
            evidence_quality=d("0.500000"),
            liquidity_reliability=d("0.400000"),
            cost_drag=d("0.350000"),
            resolution_clarity=d("0.450000"),
            specialist_memory_confidence=d("0.400000"),
        ),
        candidate("raw-z-pass"),
        candidate(
            "raw-a-block",
            current_uncertainty=d("0.150000"),
            source_age_seconds=d("20000.000000"),
            evidence_quality=d("0.300000"),
            liquidity_reliability=d("0.100000"),
            cost_drag=d("0.850000"),
            resolution_clarity=d("0.200000"),
            specialist_memory_confidence=d("0.150000"),
        ),
    )

    left_payload = research_strategy_uncertainty_reduction_readiness_report_payload(left)
    right_payload = research_strategy_uncertainty_reduction_readiness_report_payload(right)

    assert left_payload == right_payload
    assert research_strategy_uncertainty_reduction_readiness_digest(left) == (
        left.public_report_digest
    )
    assert left.public_report_digest == right.public_report_digest
    assert len(left.public_report_digest) == 64
    assert left_payload["candidate_count"] == "3.000000"
    assert left_payload["rows"][0]["reduction_readiness_score"] == "0.150000"
    assert_no_float(left_payload)
    json.dumps(left_payload, sort_keys=True)

    encoded = json.dumps(left_payload, sort_keys=True)
    for sensitive_value in (
        "raw-z-pass",
        "raw-a-block",
        "raw-m-watch",
        "candidate-id",
        "market-id",
        "market-slug",
        "question",
        "https://example.invalid/source",
        "source text",
        "postgres://host/db",
        "signals_table",
        "token abc",
        "wallet order trade",
        "buy sell recommend size",
    ):
        assert sensitive_value not in encoded
    for sensitive_key in (
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "question",
        "url",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "sizing",
    ):
        assert sensitive_key not in encoded

    object.__setattr__(left, "public_report_digest", "0" * 64)
    with pytest.raises(ValueError, match="public_report_digest"):
        research_strategy_uncertainty_reduction_readiness_report_payload(left)


def test_tied_public_rows_are_deterministic_without_private_identifiers() -> None:
    first = candidate(
        "raw-first",
        current_uncertainty=d("0.400000"),
        source_age_seconds=d("900.000000"),
        evidence_quality=d("0.400000"),
        liquidity_reliability=d("0.400000"),
        cost_drag=d("0.400000"),
        resolution_clarity=d("0.400000"),
        specialist_memory_confidence=d("0.700000"),
    )
    second = candidate(
        "raw-second",
        current_uncertainty=d("0.400000"),
        source_age_seconds=d("900.000000"),
        evidence_quality=d("0.400000"),
        liquidity_reliability=d("0.400000"),
        cost_drag=d("0.400000"),
        resolution_clarity=d("0.600000"),
        specialist_memory_confidence=d("0.400000"),
    )

    left_payload = research_strategy_uncertainty_reduction_readiness_report_payload(
        report(first, second),
    )
    right_payload = research_strategy_uncertainty_reduction_readiness_report_payload(
        report(second, first),
    )

    assert left_payload == right_payload
    assert left_payload["public_report_digest"] == right_payload["public_report_digest"]
    encoded = json.dumps(left_payload, sort_keys=True)
    assert "raw-first" not in encoded
    assert "raw-second" not in encoded


def test_empty_inputs_block_with_public_reason_count() -> None:
    readiness_report = report()

    assert readiness_report.status == "block"
    assert readiness_report.candidate_count == ZERO
    assert readiness_report.reason_codes == (
        "no_uncertainty_reduction_readiness_candidates",
    )
    assert readiness_report.reason_code_counts == (
        ResearchStrategyUncertaintyReductionReadinessReasonCodeCount(
            reason_code="no_uncertainty_reduction_readiness_candidates",
            count=ONE,
        ),
    )
    assert readiness_report.rows == ()


def test_validation_rejects_non_decimal_bad_time_bad_status_and_flags() -> None:
    with pytest.raises(ValueError, match="source_age_seconds"):
        candidate("bad-int", source_age_seconds=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_drag"):
        candidate("bad-float", cost_drag=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_quality"):
        candidate("bad-subclass", evidence_quality=_DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="observed_at"):
        candidate("bad-time", observed_at=datetime(2026, 7, 8, 14, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate("ok"), generated_at=datetime(2026, 7, 8, 14, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            candidate("subclass-time"),
            generated_at=_DatetimeSubclass(2026, 7, 8, 14, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        candidate("bad-flag", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report(candidate("flag-report")), readonly=False)
    with pytest.raises(ValueError, match="source_freshness_block_age_seconds must exceed"):
        config(source_freshness_block_age_seconds=d("3600.000000"))

    readiness_report = report(candidate("status-check"))
    with pytest.raises(ValueError, match="status"):
        replace(readiness_report.rows[0], status="blocked")


def test_public_dataclasses_are_frozen_and_module_has_no_live_surfaces() -> None:
    readiness_report = report(candidate("frozen"))

    with pytest.raises(FrozenInstanceError):
        readiness_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        readiness_report.rows[0].reduction_readiness_score = d("0.500000")  # type: ignore[misc]

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "connect(",
        "open(",
        "write_text",
        "write_bytes",
        "create_order",
        "cancel_order",
        "private_key",
        "api_key",
        "secret",
        "sizing",
        "position",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "urllib",
        "httpx",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "post",
        "request",
        "send",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)
