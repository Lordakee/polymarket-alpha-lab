from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_candidate_triage_playbook_report import (
    DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_PLAYBOOK_REPORT_CONFIG_VERSION,
    ResearchStrategyCandidateTriagePlaybookConfig,
    ResearchStrategyCandidateTriagePlaybookInput,
    ResearchStrategyCandidateTriagePlaybookReasonCodeCount,
    ResearchStrategyCandidateTriagePlaybookReport,
    ResearchStrategyCandidateTriagePlaybookRow,
    build_research_strategy_candidate_triage_playbook_report,
    research_strategy_candidate_triage_playbook_report_digest,
    research_strategy_candidate_triage_playbook_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_candidate_triage_playbook_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyCandidateTriagePlaybookConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_PLAYBOOK_REPORT_CONFIG_VERSION
        ),
        "evidence_quality_pass_floor": d("0.800000"),
        "evidence_quality_watch_floor": d("0.600000"),
        "probability_gap_pass_floor": d("0.050000"),
        "probability_gap_watch_floor": d("0.020000"),
        "liquidity_cost_pressure_watch": d("0.350000"),
        "liquidity_cost_pressure_block": d("0.750000"),
        "review_urgency_watch": d("0.400000"),
        "review_urgency_block": d("0.800000"),
    }
    values.update(overrides)
    return ResearchStrategyCandidateTriagePlaybookConfig(**values)


def item(
    triage_key: str = "triage-alpha",
    *,
    evidence_quality_score: Decimal = d("0.900000"),
    probability_gap: Decimal = d("0.090000"),
    liquidity_cost_pressure: Decimal = d("0.100000"),
    review_urgency: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyCandidateTriagePlaybookInput:
    return ResearchStrategyCandidateTriagePlaybookInput(
        triage_key=triage_key,
        evidence_quality_score=evidence_quality_score,
        probability_gap=probability_gap,
        liquidity_cost_pressure=liquidity_cost_pressure,
        review_urgency=review_urgency,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchStrategyCandidateTriagePlaybookInput,
    cfg: ResearchStrategyCandidateTriagePlaybookConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyCandidateTriagePlaybookReport:
    return build_research_strategy_candidate_triage_playbook_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_float_or_int_values(nested)
    elif isinstance(value, list):
        for nested in value:
            assert_no_float_or_int_values(nested)


def test_playbook_report_aggregates_sanitized_rows_payload_and_digest() -> None:
    pass_item = item("triage-pass")
    watch_item = item(
        "triage-watch",
        evidence_quality_score=d("0.700000"),
        probability_gap=d("0.030000"),
        liquidity_cost_pressure=d("0.500000"),
        review_urgency=d("0.450000"),
    )
    block_item = item(
        "triage-block",
        evidence_quality_score=d("0.500000"),
        probability_gap=d("0.010000"),
        liquidity_cost_pressure=d("0.800000"),
        review_urgency=d("0.850000"),
    )

    first = report(watch_item, block_item, pass_item)
    second = report(pass_item, watch_item, block_item)

    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_PLAYBOOK_REPORT_CONFIG_VERSION
    )
    assert first.candidate_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.status == "block"
    assert first.evidence_quality_attention_count == d("2.000000")
    assert first.probability_gap_attention_count == d("2.000000")
    assert first.liquidity_cost_attention_count == d("2.000000")
    assert first.review_urgency_attention_count == d("2.000000")
    assert first.mean_evidence_quality_score == d("0.700000")
    assert first.mean_probability_gap == d("0.043333")
    assert first.mean_liquidity_cost_pressure == d("0.466667")
    assert first.mean_review_urgency == d("0.466667")
    assert first.mean_playbook_priority_score == d("0.547500")
    assert first.max_review_urgency == d("0.850000")
    assert first.reason_codes == (
        "strategy_candidate_triage_playbook_block",
        "evidence_quality_block",
        "evidence_quality_watch",
        "liquidity_cost_pressure_block",
        "liquidity_cost_pressure_watch",
        "probability_gap_block",
        "probability_gap_watch",
        "review_urgency_block",
        "review_urgency_watch",
    )
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True

    assert tuple(row.aggregate_row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert first.rows[0].aggregate_row_hash == hashlib.sha256(
        b"triage-block",
    ).hexdigest()
    assert first.rows[0].playbook_priority_score == d("0.785000")
    assert first.rows[0].reason_codes == (
        "evidence_quality_block",
        "liquidity_cost_pressure_block",
        "probability_gap_block",
        "review_urgency_block",
    )
    assert first.rows[2].reason_codes == ("strategy_candidate_triage_playbook_clear",)
    assert not hasattr(first.rows[0], "triage_key")

    payload = research_strategy_candidate_triage_playbook_report_payload(first)
    assert payload == research_strategy_candidate_triage_playbook_report_payload(second)
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["candidate_count"] == "3.000000"
    assert payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert payload["rows"][0]["playbook_priority_score"] == "0.785000"
    assert payload["public_digest"] == first.public_digest
    assert "triage_key" not in json.dumps(payload, sort_keys=True)
    assert "triage-block" not in json.dumps(payload, sort_keys=True)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    digest = research_strategy_candidate_triage_playbook_report_digest(first)
    assert digest == first.public_digest
    assert len(digest) == 64
    assert set(digest) <= set("0123456789abcdef")


def test_empty_inputs_block_with_no_inputs_reason_count() -> None:
    triage = report()

    assert triage.status == "block"
    assert triage.candidate_count == ZERO
    assert triage.pass_count == ZERO
    assert triage.watch_count == ZERO
    assert triage.block_count == ZERO
    assert triage.mean_playbook_priority_score == ZERO
    assert triage.max_review_urgency == ZERO
    assert triage.reason_codes == ("strategy_candidate_triage_playbook_no_inputs",)
    assert triage.reason_code_counts == (
        ResearchStrategyCandidateTriagePlaybookReasonCodeCount(
            reason_code="strategy_candidate_triage_playbook_no_inputs",
            count=ONE,
        ),
    )
    assert triage.rows == ()


def test_status_boundary_coverage() -> None:
    boundary = report(
        item(
            "floor-pass",
            evidence_quality_score=d("0.800000"),
            probability_gap=d("0.050000"),
            liquidity_cost_pressure=d("0.349999"),
            review_urgency=d("0.399999"),
        ),
        item(
            "floor-watch",
            evidence_quality_score=d("0.799999"),
            probability_gap=d("0.049999"),
            liquidity_cost_pressure=d("0.350000"),
            review_urgency=d("0.400000"),
        ),
        item(
            "floor-block",
            evidence_quality_score=d("0.599999"),
            probability_gap=d("0.019999"),
            liquidity_cost_pressure=d("0.750000"),
            review_urgency=d("0.800000"),
        ),
    )

    assert tuple(row.status for row in boundary.rows) == ("block", "watch", "pass")
    assert boundary.rows[0].reason_codes == (
        "evidence_quality_block",
        "liquidity_cost_pressure_block",
        "probability_gap_block",
        "review_urgency_block",
    )
    assert boundary.rows[1].reason_codes == (
        "evidence_quality_watch",
        "liquidity_cost_pressure_watch",
        "probability_gap_watch",
        "review_urgency_watch",
    )
    assert boundary.rows[2].reason_codes == (
        "strategy_candidate_triage_playbook_clear",
    )


def test_custom_config_behavior_changes_statuses() -> None:
    strict = config(
        evidence_quality_pass_floor=d("0.900000"),
        evidence_quality_watch_floor=d("0.700000"),
        probability_gap_pass_floor=d("0.100000"),
        probability_gap_watch_floor=d("0.040000"),
        liquidity_cost_pressure_watch=d("0.200000"),
        liquidity_cost_pressure_block=d("0.600000"),
        review_urgency_watch=d("0.200000"),
        review_urgency_block=d("0.600000"),
    )

    triage = report(
        item(
            "custom-watch",
            evidence_quality_score=d("0.850000"),
            probability_gap=d("0.060000"),
            liquidity_cost_pressure=d("0.250000"),
            review_urgency=d("0.250000"),
        ),
        cfg=strict,
    )

    assert triage.status == "watch"
    assert triage.rows[0].reason_codes == (
        "evidence_quality_watch",
        "liquidity_cost_pressure_watch",
        "probability_gap_watch",
        "review_urgency_watch",
    )


def test_decimal_datetime_and_public_boundary_validation() -> None:
    triage = report(
        item("time-normalized"),
        generated_at=datetime(
            2026,
            7,
            8,
            11,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert triage.generated_at == GENERATED_AT

    with pytest.raises(ValueError, match="evidence_quality_pass_floor"):
        config(evidence_quality_pass_floor=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_quality_score"):
        item(evidence_quality_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="probability_gap"):
        item(probability_gap=_DecimalSubclass("0.090000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(item("naive-time"), generated_at=datetime(2026, 7, 8, 15, 0))
    with pytest.raises(ValueError, match="reason_codes"):
        item(reason_codes=["manual_review"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="duplicate triage_key"):
        report(item("duplicate-key"), item("duplicate-key"))

    for public_value in (triage, *triage.rows, *triage.reason_code_counts):
        for field in fields(public_value):
            value = getattr(public_value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_public_leak_rejection_at_construction_and_payload_boundary() -> None:
    for unsafe_value in (
        "raw_candidate_id:abc",
        "market_id:123",
        "market_slug:event",
        "question:will-it-happen",
        "source_url:https://example.invalid",
        "source_text:verbatim",
        "dsn=postgres://example",
        "table_name:research",
        "private_token=secret",
        "wallet-address",
        "order-ticket",
        "trade-ticket",
        "recommendation-note",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            item(triage_key=unsafe_value)

    triage = report(item("safe-triage-key"))
    object.__setattr__(triage.rows[0], "reason_codes", ("source_url_leak",))
    with pytest.raises(ValueError, match="unsafe|reason_codes"):
        research_strategy_candidate_triage_playbook_report_payload(triage)


def test_hard_flags_frozen_dataclasses_and_digest_validation() -> None:
    triage = report(item("frozen-triage"))

    assert is_dataclass(ResearchStrategyCandidateTriagePlaybookConfig)
    assert is_dataclass(ResearchStrategyCandidateTriagePlaybookInput)
    assert is_dataclass(ResearchStrategyCandidateTriagePlaybookRow)
    assert is_dataclass(ResearchStrategyCandidateTriagePlaybookReasonCodeCount)
    assert is_dataclass(ResearchStrategyCandidateTriagePlaybookReport)
    with pytest.raises(FrozenInstanceError):
        triage.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        triage.rows[0].playbook_priority_score = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        item(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(triage, readonly=False)
    with pytest.raises(ValueError, match="public_digest"):
        replace(triage, public_digest="0" * 64)
    with pytest.raises(ValueError, match="candidate_count"):
        replace(triage, candidate_count=d("9.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(triage, status="block")

    object.__setattr__(triage.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        research_strategy_candidate_triage_playbook_report_payload(triage)


def test_reason_counts_public_exports_and_static_io_absence() -> None:
    triage = report(
        item(
            "watch-one",
            evidence_quality_score=d("0.700000"),
            reason_codes=("manual_review_requested",),
        ),
        item(
            "watch-two",
            probability_gap=d("0.030000"),
            review_urgency=d("0.500000"),
        ),
        item("pass-one"),
    )

    assert triage.reason_code_counts == (
        ResearchStrategyCandidateTriagePlaybookReasonCodeCount(
            reason_code="evidence_quality_watch",
            count=ONE,
        ),
        ResearchStrategyCandidateTriagePlaybookReasonCodeCount(
            reason_code="manual_review_requested",
            count=ONE,
        ),
        ResearchStrategyCandidateTriagePlaybookReasonCodeCount(
            reason_code="probability_gap_watch",
            count=ONE,
        ),
        ResearchStrategyCandidateTriagePlaybookReasonCodeCount(
            reason_code="review_urgency_watch",
            count=ONE,
        ),
        ResearchStrategyCandidateTriagePlaybookReasonCodeCount(
            reason_code="strategy_candidate_triage_playbook_clear",
            count=ONE,
        ),
    )

    import polymarket_alpha_lab.research_strategy_candidate_triage_playbook_report as triage_module

    assert triage_module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_PLAYBOOK_REPORT_CONFIG_VERSION",
        "ResearchStrategyCandidateTriagePlaybookConfig",
        "ResearchStrategyCandidateTriagePlaybookInput",
        "ResearchStrategyCandidateTriagePlaybookReasonCodeCount",
        "ResearchStrategyCandidateTriagePlaybookReport",
        "ResearchStrategyCandidateTriagePlaybookRow",
        "build_research_strategy_candidate_triage_playbook_report",
        "research_strategy_candidate_triage_playbook_report_digest",
        "research_strategy_candidate_triage_playbook_report_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "wallet",
        "order",
        "trade",
        "trading",
        "position_size",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "auth",
        "database",
        "network",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
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
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__", "asdict"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
            assert all(alias.name != "asdict" for alias in node.names)
