from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_settlement_friction_edge_decay_report import (
    DEFAULT_RESEARCH_MARKET_SETTLEMENT_FRICTION_EDGE_DECAY_CONFIG_VERSION,
    ResearchMarketSettlementFrictionEdgeDecayCandidate,
    ResearchMarketSettlementFrictionEdgeDecayConfig,
    ResearchMarketSettlementFrictionEdgeDecayReasonCodeCount,
    ResearchMarketSettlementFrictionEdgeDecayReport,
    ResearchMarketSettlementFrictionEdgeDecayRow,
    build_research_market_settlement_friction_edge_decay_report,
    research_market_settlement_friction_edge_decay_digest,
    research_market_settlement_friction_edge_decay_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_market_settlement_friction_edge_decay_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketSettlementFrictionEdgeDecayConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_MARKET_SETTLEMENT_FRICTION_EDGE_DECAY_CONFIG_VERSION
        ),
        "pass_min_decayed_edge_ratio": d("0.030000"),
        "watch_min_decayed_edge_ratio": d("0.005000"),
        "direct_cost_drag_watch_ratio": d("0.020000"),
        "direct_cost_drag_block_ratio": d("0.060000"),
        "liquidity_depth_target_ratio": d("1.000000"),
        "liquidity_depth_shortfall_watch_score": d("0.200000"),
        "liquidity_depth_shortfall_block_score": d("0.600000"),
        "liquidity_depth_max_drag_ratio": d("0.020000"),
        "settlement_friction_watch_score": d("0.350000"),
        "settlement_friction_block_score": d("0.750000"),
        "settlement_friction_max_decay_ratio": d("0.030000"),
        "time_to_resolution_watch_hours": d("48.000000"),
        "time_to_resolution_block_hours": d("168.000000"),
        "time_to_resolution_max_decay_ratio": d("0.020000"),
        "edge_decay_watch_ratio": d("0.025000"),
        "edge_decay_block_ratio": d("0.050000"),
    }
    values.update(overrides)
    return ResearchMarketSettlementFrictionEdgeDecayConfig(**values)


def candidate(
    raw_candidate_id: str,
    *,
    observed_at: datetime = GENERATED_AT,
    gross_edge_ratio: Decimal = d("0.080000"),
    fee_drag_ratio: Decimal = d("0.003000"),
    spread_drag_ratio: Decimal = d("0.004000"),
    slippage_drag_ratio: Decimal = d("0.002000"),
    liquidity_depth_coverage_ratio: Decimal = d("1.200000"),
    settlement_friction_score: Decimal = d("0.100000"),
    time_to_resolution_hours: Decimal = d("24.000000"),
    sensitive_context: str | None = (
        "candidate-id market-id market-slug question "
        "https://example.invalid/source source text postgres://host/db "
        "settlement_table token abc wallet order trade buy sell sizing recommend"
    ),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketSettlementFrictionEdgeDecayCandidate:
    return ResearchMarketSettlementFrictionEdgeDecayCandidate(
        raw_candidate_id=raw_candidate_id,
        observed_at=observed_at,
        gross_edge_ratio=gross_edge_ratio,
        fee_drag_ratio=fee_drag_ratio,
        spread_drag_ratio=spread_drag_ratio,
        slippage_drag_ratio=slippage_drag_ratio,
        liquidity_depth_coverage_ratio=liquidity_depth_coverage_ratio,
        settlement_friction_score=settlement_friction_score,
        time_to_resolution_hours=time_to_resolution_hours,
        sensitive_context=sensitive_context,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchMarketSettlementFrictionEdgeDecayCandidate,
    cfg: ResearchMarketSettlementFrictionEdgeDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketSettlementFrictionEdgeDecayReport:
    return build_research_market_settlement_friction_edge_decay_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_edge_decay_math_classifies_pass_watch_and_block() -> None:
    decay_report = report(
        candidate("raw-pass"),
        candidate(
            "raw-watch",
            fee_drag_ratio=d("0.006000"),
            spread_drag_ratio=d("0.008000"),
            slippage_drag_ratio=d("0.004000"),
            liquidity_depth_coverage_ratio=d("0.700000"),
            settlement_friction_score=d("0.400000"),
            time_to_resolution_hours=d("72.000000"),
        ),
        candidate(
            "raw-block",
            fee_drag_ratio=d("0.020000"),
            spread_drag_ratio=d("0.015000"),
            slippage_drag_ratio=d("0.010000"),
            liquidity_depth_coverage_ratio=d("0.200000"),
            settlement_friction_score=d("0.800000"),
            time_to_resolution_hours=d("200.000000"),
        ),
    )

    assert type(decay_report) is ResearchMarketSettlementFrictionEdgeDecayReport
    assert decay_report.generated_at == GENERATED_AT
    assert decay_report.config_version == (
        DEFAULT_RESEARCH_MARKET_SETTLEMENT_FRICTION_EDGE_DECAY_CONFIG_VERSION
    )
    assert decay_report.candidate_count == d("3.000000")
    assert decay_report.pass_count == ONE
    assert decay_report.watch_count == ONE
    assert decay_report.block_count == ONE
    assert decay_report.direct_cost_drag_count == d("2.000000")
    assert decay_report.liquidity_depth_shortfall_count == d("2.000000")
    assert decay_report.settlement_friction_count == d("2.000000")
    assert decay_report.time_to_resolution_decay_count == d("2.000000")
    assert decay_report.edge_decay_count == ONE
    assert decay_report.net_edge_count == ONE
    assert decay_report.mean_direct_cost_drag_ratio == d("0.031333")
    assert decay_report.mean_total_edge_decay_ratio == d("0.023476")
    assert decay_report.mean_decayed_edge_ratio == d("0.025191")
    assert decay_report.min_decayed_edge_ratio == d("-0.025000")
    assert decay_report.max_total_edge_decay_ratio == d("0.044000")
    assert decay_report.status == "block"
    assert decay_report.reason_codes == (
        "direct_cost_drag_detected",
        "liquidity_depth_shortfall_detected",
        "settlement_friction_detected",
        "time_to_resolution_decay_detected",
        "edge_decay_detected",
        "net_edge_detected",
    )
    assert decay_report.paper_only is True
    assert decay_report.report_only is True
    assert decay_report.readonly is True

    first, second, third = decay_report.rows
    assert type(first) is ResearchMarketSettlementFrictionEdgeDecayRow
    assert tuple(row.status for row in decay_report.rows) == ("block", "watch", "pass")
    assert first.row_number == ONE
    assert first.liquidity_depth_shortfall_score == d("0.800000")
    assert first.liquidity_depth_drag_ratio == d("0.016000")
    assert first.direct_cost_drag_ratio == d("0.061000")
    assert first.cost_adjusted_edge_ratio == d("0.019000")
    assert first.settlement_friction_decay_ratio == d("0.024000")
    assert first.time_decay_score == ONE
    assert first.time_decay_ratio == d("0.020000")
    assert first.total_edge_decay_ratio == d("0.044000")
    assert first.decayed_edge_ratio == d("-0.025000")
    assert first.reason_codes == (
        "direct_cost_drag_blocking",
        "liquidity_depth_shortfall_blocking",
        "settlement_friction_blocking",
        "time_to_resolution_decay_blocking",
        "edge_decay_watch",
        "net_edge_blocking",
    )
    assert second.direct_cost_drag_ratio == d("0.024000")
    assert second.decayed_edge_ratio == d("0.035429")
    assert second.reason_codes == (
        "direct_cost_drag_watch",
        "liquidity_depth_shortfall_watch",
        "settlement_friction_watch",
        "time_to_resolution_decay_watch",
    )
    assert third.decayed_edge_ratio == d("0.065143")
    assert third.reason_codes == ("settlement_friction_edge_decay_clear",)


def test_settlement_friction_thresholds_and_custom_config_validation() -> None:
    strict_config = config(
        pass_min_decayed_edge_ratio=d("0.020000"),
        watch_min_decayed_edge_ratio=d("0.001000"),
        settlement_friction_watch_score=d("0.250000"),
        settlement_friction_block_score=d("0.500000"),
    )

    watch_report = report(
        candidate(
            "custom-watch",
            settlement_friction_score=d("0.300000"),
            time_to_resolution_hours=d("12.000000"),
        ),
        cfg=strict_config,
    )
    block_report = report(
        candidate(
            "custom-block",
            settlement_friction_score=d("0.500000"),
            time_to_resolution_hours=d("12.000000"),
        ),
        cfg=strict_config,
    )

    assert watch_report.status == "watch"
    assert watch_report.rows[0].reason_codes == ("settlement_friction_watch",)
    assert block_report.status == "block"
    assert block_report.rows[0].reason_codes == ("settlement_friction_blocking",)

    with pytest.raises(ValueError, match="pass_min_decayed_edge_ratio"):
        config(pass_min_decayed_edge_ratio=d("0.005000"))
    with pytest.raises(ValueError, match="liquidity_depth_target_ratio"):
        config(liquidity_depth_target_ratio=ZERO)
    with pytest.raises(ValueError, match="time_to_resolution_block_hours must exceed"):
        config(time_to_resolution_block_hours=d("48.000000"))
    with pytest.raises(ValueError, match="settlement_friction_block_score must exceed"):
        config(settlement_friction_block_score=d("0.350000"))


def test_payload_digest_is_deterministic_public_safe_and_decimal_only() -> None:
    left = report(
        candidate("raw-z-pass"),
        candidate(
            "raw-a-block",
            fee_drag_ratio=d("0.020000"),
            spread_drag_ratio=d("0.015000"),
            slippage_drag_ratio=d("0.010000"),
            liquidity_depth_coverage_ratio=d("0.200000"),
            settlement_friction_score=d("0.800000"),
            time_to_resolution_hours=d("200.000000"),
        ),
        candidate(
            "raw-m-watch",
            fee_drag_ratio=d("0.006000"),
            spread_drag_ratio=d("0.008000"),
            slippage_drag_ratio=d("0.004000"),
            liquidity_depth_coverage_ratio=d("0.700000"),
            settlement_friction_score=d("0.400000"),
            time_to_resolution_hours=d("72.000000"),
        ),
    )
    right = report(
        candidate(
            "raw-m-watch",
            fee_drag_ratio=d("0.006000"),
            spread_drag_ratio=d("0.008000"),
            slippage_drag_ratio=d("0.004000"),
            liquidity_depth_coverage_ratio=d("0.700000"),
            settlement_friction_score=d("0.400000"),
            time_to_resolution_hours=d("72.000000"),
        ),
        candidate("raw-z-pass"),
        candidate(
            "raw-a-block",
            fee_drag_ratio=d("0.020000"),
            spread_drag_ratio=d("0.015000"),
            slippage_drag_ratio=d("0.010000"),
            liquidity_depth_coverage_ratio=d("0.200000"),
            settlement_friction_score=d("0.800000"),
            time_to_resolution_hours=d("200.000000"),
        ),
    )

    left_payload = research_market_settlement_friction_edge_decay_report_payload(left)
    right_payload = research_market_settlement_friction_edge_decay_report_payload(right)

    assert left_payload == right_payload
    assert research_market_settlement_friction_edge_decay_digest(left) == (
        left.public_report_digest
    )
    assert left.public_report_digest == right.public_report_digest
    assert len(left.public_report_digest) == 64
    assert left_payload["candidate_count"] == "3.000000"
    assert left_payload["rows"][0]["decayed_edge_ratio"] == "-0.025000"
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
        "settlement_table",
        "token abc",
        "wallet order trade",
        "buy sell sizing recommend",
    ):
        assert sensitive_value not in encoded
    for sensitive_key in (
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "size",
        "recommendation",
    ):
        assert sensitive_key not in encoded

    object.__setattr__(left, "public_report_digest", "0" * 64)
    with pytest.raises(ValueError, match="public_report_digest"):
        research_market_settlement_friction_edge_decay_report_payload(left)


def test_empty_inputs_block_with_public_reason_count() -> None:
    decay_report = report()

    assert decay_report.status == "block"
    assert decay_report.candidate_count == ZERO
    assert decay_report.reason_codes == (
        "no_settlement_friction_edge_decay_candidates",
    )
    assert decay_report.reason_code_counts == (
        ResearchMarketSettlementFrictionEdgeDecayReasonCodeCount(
            reason_code="no_settlement_friction_edge_decay_candidates",
            count=ONE,
        ),
    )
    assert decay_report.rows == ()


def test_validation_rejects_non_decimal_bad_time_bad_status_and_flags() -> None:
    with pytest.raises(ValueError, match="gross_edge_ratio"):
        candidate("bad-int", gross_edge_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fee_drag_ratio"):
        candidate("bad-float", fee_drag_ratio=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="settlement_friction_score"):
        candidate("bad-subclass", settlement_friction_score=_DecimalSubclass("0.1"))
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

    decay_report = report(candidate("status-check"))
    with pytest.raises(ValueError, match="status"):
        replace(decay_report.rows[0], status="blocked")


def test_public_dataclasses_are_frozen_and_module_has_no_live_surfaces() -> None:
    decay_report = report(candidate("frozen"))

    with pytest.raises(FrozenInstanceError):
        decay_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        decay_report.rows[0].decayed_edge_ratio = d("0.500000")  # type: ignore[misc]

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
        "recommend",
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
