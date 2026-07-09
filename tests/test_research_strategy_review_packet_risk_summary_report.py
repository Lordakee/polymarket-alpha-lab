from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_strategy_review_packet_risk_summary_report as api
from polymarket_alpha_lab.research_strategy_review_packet_risk_summary_report import (
    DEFAULT_RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_STATUSES,
    ResearchStrategyReviewPacketRiskInput,
    ResearchStrategyReviewPacketRiskReasonCodeCount,
    ResearchStrategyReviewPacketRiskSummaryConfig,
    ResearchStrategyReviewPacketRiskSummaryReport,
    ResearchStrategyReviewPacketRiskSummaryRow,
    build_research_strategy_review_packet_risk_summary_report,
    research_strategy_review_packet_risk_summary_report_digest,
    research_strategy_review_packet_risk_summary_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 15, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_review_packet_risk_summary_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyReviewPacketRiskSummaryConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_REPORT_CONFIG_VERSION
        ),
        "max_pass_dimension_risk_score": d("0.250000"),
        "max_watch_dimension_risk_score": d("0.500000"),
        "max_pass_aggregate_risk_score": d("0.250000"),
        "max_watch_aggregate_risk_score": d("0.500000"),
        "min_pass_liquidity_quality_score": d("0.750000"),
        "min_watch_liquidity_quality_score": d("0.500000"),
        "evidence_gap_weight": d("0.180000"),
        "source_conflict_weight": d("0.160000"),
        "market_cost_pressure_weight": d("0.150000"),
        "liquidity_quality_weight": d("0.140000"),
        "resolution_ambiguity_weight": d("0.150000"),
        "team_memory_gap_weight": d("0.120000"),
        "capacity_pressure_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchStrategyReviewPacketRiskSummaryConfig(**values)


def packet(
    internal_packet_ref: str = (
        "candidate_id=raw-1 market_id=hidden market_slug=private-question "
        "question=leaky source_url=https://private.example/token wallet=secret"
    ),
    *,
    evidence_gap_score: Decimal = d("0.100000"),
    source_conflict_score: Decimal = d("0.080000"),
    market_cost_pressure_score: Decimal = d("0.120000"),
    liquidity_quality_score: Decimal = d("0.900000"),
    resolution_ambiguity_score: Decimal = d("0.100000"),
    team_memory_gap_score: Decimal = d("0.120000"),
    capacity_pressure_score: Decimal = d("0.100000"),
    observed_at: datetime = OBSERVED_AT,
    reason_codes: tuple[str, ...] = ("analyst_packet_scope_ready",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyReviewPacketRiskInput:
    return ResearchStrategyReviewPacketRiskInput(
        internal_packet_ref=internal_packet_ref,
        evidence_gap_score=evidence_gap_score,
        source_conflict_score=source_conflict_score,
        market_cost_pressure_score=market_cost_pressure_score,
        liquidity_quality_score=liquidity_quality_score,
        resolution_ambiguity_score=resolution_ambiguity_score,
        team_memory_gap_score=team_memory_gap_score,
        capacity_pressure_score=capacity_pressure_score,
        observed_at=observed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *packets: ResearchStrategyReviewPacketRiskInput,
    cfg: ResearchStrategyReviewPacketRiskSummaryConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyReviewPacketRiskSummaryReport:
    return build_research_strategy_review_packet_risk_summary_report(
        packets,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(("_count", "_score", "_weight")):
            assert type(item) is Decimal


def assert_no_public_numeric_primitives(value: Any) -> None:
    for item in walk_values(value):
        assert type(item) is not float
        if type(item) is bool:
            continue
        assert type(item) is not int


def test_status_vocabulary_is_exact() -> None:
    assert RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_STATUSES == (
        "pass",
        "watch",
        "block",
    )


def test_builds_pass_watch_block_packet_risk_summary_without_raw_leakage() -> None:
    pass_item = packet(
        "candidate_id=pass market_id=hidden market_slug=private "
        "question=hidden source_url=https://private/pass",
    )
    watch_item = packet(
        "candidate_id=watch market_id=hidden market_slug=private "
        "question=hidden source_url=https://private/watch",
        evidence_gap_score=d("0.350000"),
        source_conflict_score=d("0.300000"),
        market_cost_pressure_score=d("0.320000"),
        liquidity_quality_score=d("0.680000"),
        resolution_ambiguity_score=d("0.300000"),
        team_memory_gap_score=d("0.280000"),
        capacity_pressure_score=d("0.300000"),
        reason_codes=("manual_review_requested",),
    )
    block_item = packet(
        "candidate_id=block market_id=hidden market_slug=private "
        "question=hidden source_url=https://private/block token=secret",
        evidence_gap_score=d("0.700000"),
        source_conflict_score=d("0.650000"),
        market_cost_pressure_score=d("0.720000"),
        liquidity_quality_score=d("0.250000"),
        resolution_ambiguity_score=d("0.800000"),
        team_memory_gap_score=d("0.600000"),
        capacity_pressure_score=d("0.620000"),
        reason_codes=("manual_review_requested", "capacity_review_requested"),
    )

    first = report(
        watch_item,
        block_item,
        pass_item,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )
    second = report(pass_item, watch_item, block_item)

    assert is_dataclass(first)
    assert type(first) is ResearchStrategyReviewPacketRiskSummaryReport
    assert first.generated_at == GENERATED_AT
    assert first.generated_at.tzinfo is UTC
    assert first.config_version == (
        DEFAULT_RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_REPORT_CONFIG_VERSION
    )
    assert first.status == "block"
    assert first.packet_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.average_aggregate_risk_score == d("0.370533")
    assert first.max_aggregate_risk_score == d("0.697000")
    assert first.max_evidence_gap_score == d("0.700000")
    assert first.max_source_conflict_score == d("0.650000")
    assert first.max_market_cost_pressure_score == d("0.720000")
    assert first.min_liquidity_quality_score == d("0.250000")
    assert first.max_resolution_ambiguity_score == d("0.800000")
    assert first.max_team_memory_gap_score == d("0.600000")
    assert first.max_capacity_pressure_score == d("0.620000")
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True

    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert tuple(row.row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )

    blocked = first.rows[0]
    assert type(blocked) is ResearchStrategyReviewPacketRiskSummaryRow
    assert blocked.liquidity_risk_score == d("0.750000")
    assert blocked.aggregate_risk_score == d("0.697000")
    assert blocked.reason_codes == (
        "manual_review_requested",
        "capacity_review_requested",
        "evidence_gap_block",
        "source_conflict_block",
        "market_cost_pressure_block",
        "liquidity_quality_block",
        "resolution_ambiguity_block",
        "team_memory_gap_block",
        "capacity_pressure_block",
        "aggregate_risk_block",
    )
    assert blocked.review_state == "risk_summary_block"
    assert blocked.review_packet_digest.startswith("sha256:")
    assert_digest(blocked.validation_digest)

    watched = first.rows[1]
    assert watched.aggregate_risk_score == d("0.312400")
    assert watched.reason_codes == (
        "manual_review_requested",
        "evidence_gap_watch",
        "source_conflict_watch",
        "market_cost_pressure_watch",
        "liquidity_quality_watch",
        "resolution_ambiguity_watch",
        "team_memory_gap_watch",
        "capacity_pressure_watch",
        "aggregate_risk_watch",
    )
    assert watched.review_state == "risk_summary_watch"

    passed = first.rows[2]
    assert passed.aggregate_risk_score == d("0.102200")
    assert passed.reason_codes == (
        "analyst_packet_scope_ready",
        "review_packet_risk_summary_pass",
    )
    assert passed.review_state == "risk_summary_pass"

    assert first.reason_code_counts[0] == ResearchStrategyReviewPacketRiskReasonCodeCount(
        reason_code="manual_review_requested",
        count=d("2.000000"),
        packet_ratio=d("0.666667"),
    )

    payload = research_strategy_review_packet_risk_summary_report_payload(first)
    assert payload == research_strategy_review_packet_risk_summary_report_payload(second)
    assert payload == first.payload
    assert payload["packet_count"] == "3.000000"
    assert payload["rows"][0]["aggregate_risk_score"] == "0.697000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_digest(first.derived_validation_digest)
    assert_no_public_numeric_primitives(payload)
    json.dumps(payload, sort_keys=True, allow_nan=False)

    digest = research_strategy_review_packet_risk_summary_report_digest(first)
    assert "rows" not in digest
    assert digest["packet_count"] == payload["packet_count"]
    assert digest["status"] == "block"
    assert digest["derived_validation_digest"] == first.derived_validation_digest
    assert_no_public_numeric_primitives(digest)

    rendered = json.dumps(payload, sort_keys=True).casefold()
    for raw_fragment in (
        "candidate_id",
        "market_id",
        "market_slug",
        "private-question",
        "question=hidden",
        "source_url",
        "https://private",
        "token=secret",
        "wallet=secret",
        "internal_packet_ref",
    ):
        assert raw_fragment not in rendered
        assert raw_fragment not in repr(first).casefold()


def test_empty_report_is_readonly_block_without_rows() -> None:
    summary = report()

    assert summary.status == "block"
    assert summary.packet_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.average_aggregate_risk_score == ZERO
    assert summary.max_aggregate_risk_score == ZERO
    assert summary.max_evidence_gap_score == ZERO
    assert summary.max_source_conflict_score == ZERO
    assert summary.max_market_cost_pressure_score == ZERO
    assert summary.min_liquidity_quality_score == ZERO
    assert summary.max_resolution_ambiguity_score == ZERO
    assert summary.max_team_memory_gap_score == ZERO
    assert summary.max_capacity_pressure_score == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == ("empty_input",)
    assert summary.reason_code_counts == (
        ResearchStrategyReviewPacketRiskReasonCodeCount(
            reason_code="empty_input",
            count=ONE,
            packet_ratio=ONE,
        ),
    )

    payload = research_strategy_review_packet_risk_summary_report_payload(summary)
    assert payload["rows"] == []
    assert payload["reason_codes"] == ["empty_input"]


def test_frozen_dataclasses_decimal_types_and_hard_flags_are_enforced() -> None:
    assert is_dataclass(ResearchStrategyReviewPacketRiskSummaryConfig)
    assert is_dataclass(ResearchStrategyReviewPacketRiskInput)
    assert is_dataclass(ResearchStrategyReviewPacketRiskSummaryRow)
    assert is_dataclass(ResearchStrategyReviewPacketRiskSummaryReport)
    assert is_dataclass(ResearchStrategyReviewPacketRiskReasonCodeCount)

    cfg = config()
    source_packet = packet()
    summary = report(source_packet, cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_packet.evidence_gap_score = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].aggregate_risk_score = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                DEFAULT_RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_REPORT_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="status"):
        replace(summary.rows[0], status=_StringSubclass("pass"))
    with pytest.raises(ValueError, match="review_state"):
        replace(summary.rows[0], review_state=_StringSubclass("risk_summary_pass"))
    with pytest.raises(ValueError, match="max_pass_dimension_risk_score"):
        config(max_pass_dimension_risk_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_watch_dimension_risk_score"):
        config(max_watch_dimension_risk_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="max_pass_dimension_risk_score"):
        config(max_pass_dimension_risk_score=d("0.600000"))
    with pytest.raises(ValueError, match="min_pass_liquidity_quality_score"):
        config(min_pass_liquidity_quality_score=d("0.400000"))
    with pytest.raises(ValueError, match="weights"):
        config(evidence_gap_weight=d("0.190000"))

    with pytest.raises(ValueError, match="internal_packet_ref"):
        packet(_StringSubclass("packet-alpha"))
    with pytest.raises(ValueError, match="evidence_gap_score"):
        packet(evidence_gap_score="0.100000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_conflict_score"):
        packet(source_conflict_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_cost_pressure_score"):
        packet(market_cost_pressure_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="observed_at"):
        packet(observed_at=_DatetimeSubclass(2026, 7, 8, 15, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=datetime(2026, 7, 8, 16, 0))
    with pytest.raises(ValueError, match="config"):
        report(cfg=object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="packets"):
        build_research_strategy_review_packet_risk_summary_report(
            (object(),),  # type: ignore[arg-type]
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(packet(observed_at=datetime(2026, 7, 8, 16, 1, tzinfo=UTC)))

    for flag in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=flag):
            config(**{flag: False})
        with pytest.raises(ValueError, match=flag):
            packet(**{flag: False})
        with pytest.raises(ValueError, match=flag):
            replace(summary, **{flag: False})
        with pytest.raises(ValueError, match=flag):
            replace(summary.rows[0], **{flag: False})


def test_public_payload_rejects_leaky_fields_values_statuses_and_digest_tampering() -> None:
    summary = report(packet())
    payload = research_strategy_review_packet_risk_summary_report_payload(summary)

    tampered_status = dict(payload)
    tampered_status["status"] = "blocked"
    with pytest.raises(ValueError, match="pass, watch, or block"):
        research_strategy_review_packet_risk_summary_report_payload(tampered_status)

    tampered_field = dict(payload)
    tampered_field["market_id"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public field"):
        research_strategy_review_packet_risk_summary_report_payload(tampered_field)

    tampered_value = dict(payload)
    tampered_value["review_note"] = "source_url=https://private.example/raw"
    with pytest.raises(ValueError, match="unsafe public value"):
        research_strategy_review_packet_risk_summary_report_payload(tampered_value)

    tampered_digest = dict(payload)
    tampered_digest["packet_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_review_packet_risk_summary_report_payload(tampered_digest)

    tampered_row = dict(payload)
    rows = list(payload["rows"])  # type: ignore[arg-type]
    rows[0] = dict(rows[0])
    rows[0]["aggregate_risk_score"] = "0.999999"
    tampered_row["rows"] = rows
    with pytest.raises(ValueError, match="validation_digest"):
        research_strategy_review_packet_risk_summary_report_payload(tampered_row)


def test_manual_report_and_row_drift_rejected() -> None:
    summary = report(packet())
    row = summary.rows[0]

    with pytest.raises(ValueError, match="status"):
        replace(row, status="watch")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=("review_packet_risk_summary_pass", "aggregate_risk_watch"))
    with pytest.raises(ValueError, match="aggregate_risk_score"):
        replace(row, aggregate_risk_score=ZERO, validation_config=config())
    with pytest.raises(ValueError, match="review_packet_digest"):
        replace(row, review_packet_digest="candidate_id=raw-market")
    with pytest.raises(ValueError, match="validation_digest"):
        replace(row, validation_digest="0" * 64)

    with pytest.raises(ValueError, match="pass_count"):
        replace(summary, pass_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            packet("packet-z", evidence_gap_score=d("0.700000")),
            packet("packet-a"),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary, derived_validation_digest="0" * 64)


def test_public_numeric_fields_are_decimals() -> None:
    source_packet = packet()
    summary = report(source_packet)

    assert_decimal_numeric_fields(config())
    assert_decimal_numeric_fields(source_packet)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_scope_is_report_only_and_public_api_is_narrow() -> None:
    assert api.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_STATUSES",
        "ResearchStrategyReviewPacketRiskInput",
        "ResearchStrategyReviewPacketRiskReasonCodeCount",
        "ResearchStrategyReviewPacketRiskSummaryConfig",
        "ResearchStrategyReviewPacketRiskSummaryReport",
        "ResearchStrategyReviewPacketRiskSummaryRow",
        "build_research_strategy_review_packet_risk_summary_report",
        "research_strategy_review_packet_risk_summary_report_digest",
        "research_strategy_review_packet_risk_summary_report_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "read_text",
        "read_bytes",
        "urlopen",
        "post",
        "get",
        "put",
        "delete",
        "patch",
    }
    forbidden_public_fragments = (
        "market_id",
        "market_slug",
        "candidate_id",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order_id",
        "trade_id",
        "position_id",
        "private_key",
    )

    assert not (imported_modules & forbidden_import_roots)
    assert not (set(call_names) & forbidden_calls)
    for fragment in forbidden_public_fragments:
        assert fragment not in source
