from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_settlement_resolution_friction_report import (
    DEFAULT_RESEARCH_MARKET_SETTLEMENT_RESOLUTION_FRICTION_CONFIG_VERSION,
    ResearchMarketSettlementResolutionFrictionCandidate,
    ResearchMarketSettlementResolutionFrictionConfig,
    ResearchMarketSettlementResolutionFrictionReasonCodeCount,
    ResearchMarketSettlementResolutionFrictionReport,
    ResearchMarketSettlementResolutionFrictionRow,
    build_research_market_settlement_resolution_friction_report,
    research_market_settlement_resolution_friction_digest,
    research_market_settlement_resolution_friction_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_market_settlement_resolution_friction_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketSettlementResolutionFrictionConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_MARKET_SETTLEMENT_RESOLUTION_FRICTION_CONFIG_VERSION
        ),
        "pass_max_friction_score": d("0.300000"),
        "watch_max_friction_score": d("0.650000"),
        "settlement_lag_watch_hours": d("24.000000"),
        "settlement_lag_block_hours": d("72.000000"),
        "resolution_ambiguity_watch_score": d("0.350000"),
        "resolution_ambiguity_block_score": d("0.800000"),
        "source_rule_alignment_watch_score": d("0.650000"),
        "source_rule_alignment_block_score": d("0.300000"),
        "fee_spread_drag_watch_ratio": d("0.020000"),
        "fee_spread_drag_block_ratio": d("0.060000"),
        "liquidity_constraint_watch_score": d("0.300000"),
        "liquidity_constraint_block_score": d("0.750000"),
        "settlement_lag_weight": d("0.200000"),
        "resolution_ambiguity_weight": d("0.250000"),
        "source_rule_alignment_weight": d("0.200000"),
        "fee_spread_drag_weight": d("0.150000"),
        "liquidity_constraint_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchMarketSettlementResolutionFrictionConfig(**values)


def candidate(
    raw_candidate_id: str,
    *,
    observed_at: datetime = GENERATED_AT,
    settlement_lag_hours: Decimal = d("6.000000"),
    resolution_ambiguity_score: Decimal = d("0.100000"),
    source_rule_alignment_score: Decimal = d("0.900000"),
    fee_spread_drag_ratio: Decimal = d("0.006000"),
    liquidity_constraint_score: Decimal = d("0.100000"),
    sensitive_context: str | None = (
        "candidate-id market-id market-slug question "
        "https://example.invalid/source source text postgres://host/db "
        "settlement_table token abc wallet order trade buy sell sizing"
    ),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketSettlementResolutionFrictionCandidate:
    return ResearchMarketSettlementResolutionFrictionCandidate(
        raw_candidate_id=raw_candidate_id,
        observed_at=observed_at,
        settlement_lag_hours=settlement_lag_hours,
        resolution_ambiguity_score=resolution_ambiguity_score,
        source_rule_alignment_score=source_rule_alignment_score,
        fee_spread_drag_ratio=fee_spread_drag_ratio,
        liquidity_constraint_score=liquidity_constraint_score,
        sensitive_context=sensitive_context,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchMarketSettlementResolutionFrictionCandidate,
    cfg: ResearchMarketSettlementResolutionFrictionConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketSettlementResolutionFrictionReport:
    return build_research_market_settlement_resolution_friction_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_combines_settlement_resolution_alignment_drag_and_liquidity() -> None:
    friction_report = report(
        candidate("raw-pass"),
        candidate(
            "raw-watch",
            settlement_lag_hours=d("30.000000"),
            resolution_ambiguity_score=d("0.400000"),
            source_rule_alignment_score=d("0.600000"),
            fee_spread_drag_ratio=d("0.025000"),
            liquidity_constraint_score=d("0.350000"),
        ),
        candidate(
            "raw-block",
            settlement_lag_hours=d("96.000000"),
            resolution_ambiguity_score=d("0.850000"),
            source_rule_alignment_score=d("0.250000"),
            fee_spread_drag_ratio=d("0.080000"),
            liquidity_constraint_score=d("0.800000"),
        ),
    )

    assert type(friction_report) is ResearchMarketSettlementResolutionFrictionReport
    assert friction_report.generated_at == GENERATED_AT
    assert friction_report.config_version == (
        DEFAULT_RESEARCH_MARKET_SETTLEMENT_RESOLUTION_FRICTION_CONFIG_VERSION
    )
    assert friction_report.candidate_count == d("3.000000")
    assert friction_report.pass_count == ONE
    assert friction_report.watch_count == ONE
    assert friction_report.block_count == ONE
    assert friction_report.mean_friction_score == d("0.455000")
    assert friction_report.mean_settlement_lag_hours == d("44.000000")
    assert friction_report.max_fee_spread_drag_ratio == d("0.080000")
    assert friction_report.status == "block"
    assert friction_report.reason_codes == (
        "settlement_lag_detected",
        "resolution_ambiguity_detected",
        "source_rule_alignment_gap_detected",
        "fee_spread_drag_detected",
        "liquidity_constraint_detected",
        "composite_resolution_friction_detected",
    )
    assert friction_report.paper_only is True
    assert friction_report.report_only is True
    assert friction_report.readonly is True

    first, second, third = friction_report.rows
    assert type(first) is ResearchMarketSettlementResolutionFrictionRow
    assert tuple(row.status for row in friction_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert first.row_number == ONE
    assert first.settlement_lag_score == ONE
    assert first.resolution_ambiguity_score == d("0.850000")
    assert first.source_rule_gap_score == d("0.750000")
    assert first.fee_spread_drag_score == ONE
    assert first.liquidity_constraint_score == d("0.800000")
    assert first.friction_score == d("0.872500")
    assert first.reason_codes == (
        "settlement_lag_blocking",
        "resolution_ambiguity_blocking",
        "source_rule_alignment_gap_blocking",
        "fee_spread_drag_blocking",
        "liquidity_constraint_blocking",
        "composite_resolution_friction_blocking",
    )
    assert second.friction_score == d("0.395833")
    assert second.source_rule_gap_score == d("0.400000")
    assert second.reason_codes == (
        "settlement_lag_watch",
        "resolution_ambiguity_watch",
        "source_rule_alignment_gap_watch",
        "fee_spread_drag_watch",
        "liquidity_constraint_watch",
        "composite_resolution_friction_watch",
    )
    assert third.friction_score == d("0.096667")
    assert third.source_rule_gap_score == d("0.100000")
    assert third.reason_codes == ("settlement_resolution_friction_clear",)


def test_payload_digest_is_deterministic_public_safe_and_decimal_only() -> None:
    from polymarket_alpha_lab import (
        research_market_settlement_resolution_friction_report as api,
    )

    left = report(
        candidate("raw-z-pass"),
        candidate(
            "raw-a-block",
            settlement_lag_hours=d("96.000000"),
            resolution_ambiguity_score=d("0.850000"),
            source_rule_alignment_score=d("0.250000"),
            fee_spread_drag_ratio=d("0.080000"),
            liquidity_constraint_score=d("0.800000"),
        ),
        candidate(
            "raw-m-watch",
            settlement_lag_hours=d("30.000000"),
            resolution_ambiguity_score=d("0.400000"),
            source_rule_alignment_score=d("0.600000"),
            fee_spread_drag_ratio=d("0.025000"),
            liquidity_constraint_score=d("0.350000"),
        ),
    )
    right = report(
        candidate(
            "raw-m-watch",
            settlement_lag_hours=d("30.000000"),
            resolution_ambiguity_score=d("0.400000"),
            source_rule_alignment_score=d("0.600000"),
            fee_spread_drag_ratio=d("0.025000"),
            liquidity_constraint_score=d("0.350000"),
        ),
        candidate("raw-z-pass"),
        candidate(
            "raw-a-block",
            settlement_lag_hours=d("96.000000"),
            resolution_ambiguity_score=d("0.850000"),
            source_rule_alignment_score=d("0.250000"),
            fee_spread_drag_ratio=d("0.080000"),
            liquidity_constraint_score=d("0.800000"),
        ),
    )

    left_payload = research_market_settlement_resolution_friction_report_payload(left)
    right_payload = research_market_settlement_resolution_friction_report_payload(right)

    assert left_payload == right_payload
    assert research_market_settlement_resolution_friction_digest(left) == (
        left.public_report_digest
    )
    assert left.public_report_digest == right.public_report_digest
    assert len(left.public_report_digest) == 64
    assert left_payload["candidate_count"] == "3.000000"
    assert left_payload["rows"][0]["friction_score"] == "0.872500"
    assert api.__all__ == (
        "DEFAULT_RESEARCH_MARKET_SETTLEMENT_RESOLUTION_FRICTION_CONFIG_VERSION",
        "ResearchMarketSettlementResolutionFrictionCandidate",
        "ResearchMarketSettlementResolutionFrictionConfig",
        "ResearchMarketSettlementResolutionFrictionReasonCodeCount",
        "ResearchMarketSettlementResolutionFrictionReport",
        "ResearchMarketSettlementResolutionFrictionRow",
        "build_research_market_settlement_resolution_friction_report",
        "research_market_settlement_resolution_friction_digest",
        "research_market_settlement_resolution_friction_report_payload",
    )
    assert set(left_payload) == {
        "generated_at",
        "config_version",
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "settlement_lag_count",
        "resolution_ambiguity_count",
        "source_rule_alignment_gap_count",
        "fee_spread_drag_count",
        "liquidity_constraint_count",
        "mean_friction_score",
        "mean_settlement_lag_hours",
        "max_fee_spread_drag_ratio",
        "status",
        "reason_code_counts",
        "reason_codes",
        "rows",
        "public_report_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert set(left_payload["rows"][0]) == {
        "row_number",
        "observed_at",
        "settlement_lag_hours",
        "settlement_lag_score",
        "resolution_ambiguity_score",
        "source_rule_gap_score",
        "fee_spread_drag_ratio",
        "fee_spread_drag_score",
        "liquidity_constraint_score",
        "friction_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert set(left_payload["reason_code_counts"][0]) == {
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    }
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
        "buy sell sizing",
    ):
        assert sensitive_value not in encoded
    for sensitive_key in (
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
    ):
        assert sensitive_key not in encoded

    object.__setattr__(left, "public_report_digest", "0" * 64)
    with pytest.raises(ValueError, match="public_report_digest"):
        research_market_settlement_resolution_friction_report_payload(left)

    tampered_report_flags = report(candidate("report-flag-leak"))
    object.__setattr__(tampered_report_flags, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        research_market_settlement_resolution_friction_report_payload(
            tampered_report_flags,
        )

    tampered_row_flags = report(candidate("row-flag-leak"))
    object.__setattr__(tampered_row_flags.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        research_market_settlement_resolution_friction_report_payload(
            tampered_row_flags,
        )


def test_public_payload_sort_is_deterministic_without_raw_candidate_tiebreaker() -> None:
    first = candidate(
        "raw-first",
        resolution_ambiguity_score=d("0.200000"),
        source_rule_alignment_score=d("0.900000"),
        liquidity_constraint_score=d("0.100000"),
    )
    second = candidate(
        "raw-second",
        resolution_ambiguity_score=d("0.100000"),
        source_rule_alignment_score=d("0.775000"),
        liquidity_constraint_score=d("0.100000"),
    )

    left_payload = research_market_settlement_resolution_friction_report_payload(
        report(first, second),
    )
    right_payload = research_market_settlement_resolution_friction_report_payload(
        report(second, first),
    )

    assert left_payload == right_payload


def test_empty_inputs_block_with_public_reason_count() -> None:
    friction_report = report()

    assert friction_report.status == "block"
    assert friction_report.candidate_count == ZERO
    assert friction_report.reason_codes == (
        "no_settlement_resolution_friction_candidates",
    )
    assert friction_report.reason_code_counts == (
        ResearchMarketSettlementResolutionFrictionReasonCodeCount(
            reason_code="no_settlement_resolution_friction_candidates",
            count=ONE,
        ),
    )
    assert friction_report.rows == ()


def test_validation_rejects_non_decimal_bad_time_bad_status_and_flags() -> None:
    with pytest.raises(ValueError, match="settlement_lag_hours"):
        candidate("bad-int", settlement_lag_hours=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fee_spread_drag_ratio"):
        candidate("bad-float", fee_spread_drag_ratio=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="liquidity_constraint_score"):
        candidate("bad-subclass", liquidity_constraint_score=_DecimalSubclass("0.1"))
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
    with pytest.raises(ValueError, match="source_rule_alignment_block_score"):
        config(source_rule_alignment_block_score=d("0.650000"))
    with pytest.raises(ValueError, match="settlement_lag_block_hours must exceed"):
        config(settlement_lag_block_hours=d("24.000000"))

    friction_report = report(candidate("status-check"))
    with pytest.raises(ValueError, match="status"):
        replace(friction_report.rows[0], status="blocked")


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "api_key",
        "authentication",
        "execution",
        "live-trading",
        "market-id",
        "postgres",
        "recommendation",
        "sizing",
        "token",
        "wallet-order",
    ),
)
def test_config_rejects_unsafe_public_version_values(unsafe_value: str) -> None:
    with pytest.raises(ValueError, match="config_version.*unsafe"):
        config(config_version=unsafe_value)


def test_payload_rejects_plain_integer_tampering() -> None:
    friction_report = report(candidate("plain-int"))
    object.__setattr__(friction_report, "candidate_count", 1)

    with pytest.raises(ValueError, match="Decimal-derived"):
        research_market_settlement_resolution_friction_report_payload(
            friction_report,
        )


def test_public_dataclasses_are_frozen_and_module_has_no_live_surfaces() -> None:
    friction_report = report(candidate("frozen"))

    with pytest.raises(FrozenInstanceError):
        friction_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        friction_report.rows[0].friction_score = d("0.500000")  # type: ignore[misc]

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
    if type(value) is int:
        pytest.fail(f"found plain integer in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)
