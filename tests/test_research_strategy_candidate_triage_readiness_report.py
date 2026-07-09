from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_strategy_candidate_triage_readiness_report"
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_candidate_triage_readiness_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 14, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def load_module() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_READINESS_REPORT_CONFIG_VERSION
        ),
        "evidence_maturity_pass_floor": d("0.800000"),
        "evidence_maturity_watch_floor": d("0.600000"),
        "source_coverage_pass_floor": d("0.800000"),
        "source_coverage_watch_floor": d("0.600000"),
        "cost_freshness_pass_floor": d("0.800000"),
        "cost_freshness_watch_floor": d("0.600000"),
        "settlement_clarity_pass_floor": d("0.800000"),
        "settlement_clarity_watch_floor": d("0.600000"),
        "team_memory_quality_pass_floor": d("0.800000"),
        "team_memory_quality_watch_floor": d("0.600000"),
        "manual_review_pressure_watch": d("0.400000"),
        "manual_review_pressure_block": d("0.750000"),
    }
    values.update(overrides)
    return module.ResearchStrategyCandidateTriageReadinessConfig(**values)


def triage_input(
    module: Any,
    triage_key: str = "triage-alpha",
    *,
    evidence_maturity_score: Decimal = d("0.900000"),
    source_coverage_score: Decimal = d("0.900000"),
    cost_freshness_score: Decimal = d("0.900000"),
    settlement_clarity_score: Decimal = d("0.900000"),
    team_memory_quality_score: Decimal = d("0.900000"),
    manual_review_pressure: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return module.ResearchStrategyCandidateTriageReadinessInput(
        triage_key=triage_key,
        evidence_maturity_score=evidence_maturity_score,
        source_coverage_score=source_coverage_score,
        cost_freshness_score=cost_freshness_score,
        settlement_clarity_score=settlement_clarity_score,
        team_memory_quality_score=team_memory_quality_score,
        manual_review_pressure=manual_review_pressure,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    module: Any,
    *rows: Any,
    config: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_candidate_triage_readiness_report(
        rows,
        config=cfg(module) if config is None else config,
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_triage_readiness_aggregates_public_rows_payload_and_digest() -> None:
    module = load_module()
    pass_item = triage_input(module, "triage-pass")
    watch_item = triage_input(
        module,
        "triage-watch",
        evidence_maturity_score=d("0.700000"),
        source_coverage_score=d("0.650000"),
        cost_freshness_score=d("0.650000"),
        settlement_clarity_score=d("0.700000"),
        team_memory_quality_score=d("0.700000"),
        manual_review_pressure=d("0.500000"),
    )
    block_item = triage_input(
        module,
        "triage-block",
        evidence_maturity_score=d("0.500000"),
        source_coverage_score=d("0.400000"),
        cost_freshness_score=d("0.550000"),
        settlement_clarity_score=d("0.500000"),
        team_memory_quality_score=d("0.450000"),
        manual_review_pressure=d("0.800000"),
    )

    first = report(module, watch_item, block_item, pass_item)
    second = report(module, pass_item, watch_item, block_item)

    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_READINESS_REPORT_CONFIG_VERSION
    )
    assert first.candidate_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.status == "block"
    assert first.evidence_maturity_attention_count == d("2.000000")
    assert first.source_coverage_attention_count == d("2.000000")
    assert first.cost_freshness_attention_count == d("2.000000")
    assert first.settlement_clarity_attention_count == d("2.000000")
    assert first.team_memory_quality_attention_count == d("2.000000")
    assert first.manual_review_attention_count == d("2.000000")
    assert first.mean_evidence_maturity_score == d("0.700000")
    assert first.mean_source_coverage_score == d("0.650000")
    assert first.mean_cost_freshness_score == d("0.700000")
    assert first.mean_settlement_clarity_score == d("0.700000")
    assert first.mean_team_memory_quality_score == d("0.683333")
    assert first.mean_triage_readiness_score == d("0.686667")
    assert first.max_manual_review_pressure == d("0.800000")
    assert first.reason_codes == (
        "candidate_triage_readiness_block",
        "cost_freshness_block",
        "cost_freshness_watch",
        "evidence_maturity_block",
        "evidence_maturity_watch",
        "manual_review_pressure_block",
        "manual_review_pressure_watch",
        "settlement_clarity_block",
        "settlement_clarity_watch",
        "source_coverage_block",
        "source_coverage_watch",
        "team_memory_quality_block",
        "team_memory_quality_watch",
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
    assert first.rows[0].triage_readiness_score == d("0.480000")
    assert first.rows[0].reason_codes == (
        "cost_freshness_block",
        "evidence_maturity_block",
        "manual_review_pressure_block",
        "settlement_clarity_block",
        "source_coverage_block",
        "team_memory_quality_block",
    )
    assert first.rows[2].reason_codes == ("triage_readiness_clear",)
    assert not hasattr(first.rows[0], "triage_key")

    payload = module.research_strategy_candidate_triage_readiness_report_payload(first)
    assert payload == module.research_strategy_candidate_triage_readiness_report_payload(
        second,
    )
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["candidate_count"] == "3.000000"
    assert payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert payload["rows"][0]["triage_readiness_score"] == "0.480000"
    assert payload["public_digest"] == first.public_digest
    assert "triage_key" not in json.dumps(payload, sort_keys=True)
    assert "triage-block" not in json.dumps(payload, sort_keys=True)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    digest = module.research_strategy_candidate_triage_readiness_report_digest(first)
    assert digest == first.public_digest
    assert_digest(digest)


def test_empty_inputs_block_with_no_inputs_reason_count() -> None:
    module = load_module()

    triage = report(module)

    assert triage.status == "block"
    assert triage.candidate_count == ZERO
    assert triage.pass_count == ZERO
    assert triage.watch_count == ZERO
    assert triage.block_count == ZERO
    assert triage.mean_triage_readiness_score == ZERO
    assert triage.max_manual_review_pressure == ZERO
    assert triage.reason_codes == ("candidate_triage_readiness_no_inputs",)
    assert triage.reason_code_counts == (
        module.ResearchStrategyCandidateTriageReadinessReasonCodeCount(
            reason_code="candidate_triage_readiness_no_inputs",
            count=ONE,
        ),
    )
    assert triage.rows == ()


def test_decimal_datetime_and_public_boundary_validation() -> None:
    module = load_module()

    triage = report(
        module,
        triage_input(module),
        generated_at=datetime(
            2026,
            7,
            8,
            10,
            30,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert triage.generated_at == GENERATED_AT

    with pytest.raises(ValueError, match="evidence_maturity_pass_floor"):
        cfg(module, evidence_maturity_pass_floor=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_maturity_score"):
        triage_input(module, evidence_maturity_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_coverage_score"):
        triage_input(module, source_coverage_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(module, triage_input(module), generated_at=datetime(2026, 7, 8, 14, 30))
    with pytest.raises(ValueError, match="reason_codes"):
        triage_input(module, reason_codes=["triage_watch"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="duplicate triage_key"):
        report(
            module,
            triage_input(module, "duplicate-key"),
            triage_input(module, "duplicate-key"),
        )

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
    module = load_module()
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
            triage_input(module, triage_key=unsafe_value)

    triage = report(module, triage_input(module, "safe-triage-key"))
    object.__setattr__(triage.rows[0], "aggregate_row_hash", "source_url:https")
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_candidate_triage_readiness_report_payload(triage)


def test_hard_flags_frozen_dataclasses_and_payload_revalidation() -> None:
    module = load_module()
    triage = report(module, triage_input(module, "frozen-triage"))

    assert is_dataclass(module.ResearchStrategyCandidateTriageReadinessConfig)
    assert is_dataclass(module.ResearchStrategyCandidateTriageReadinessInput)
    assert is_dataclass(module.ResearchStrategyCandidateTriageReadinessRow)
    assert is_dataclass(module.ResearchStrategyCandidateTriageReadinessReasonCodeCount)
    assert is_dataclass(module.ResearchStrategyCandidateTriageReadinessReport)
    with pytest.raises(FrozenInstanceError):
        triage.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        triage.rows[0].triage_readiness_score = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        triage_input(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        cfg(module, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(triage, readonly=False)

    object.__setattr__(triage.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        module.research_strategy_candidate_triage_readiness_report_payload(triage)


def test_reason_counts_public_exports_and_digest_validation() -> None:
    module = load_module()

    triage = report(
        module,
        triage_input(
            module,
            "watch-one",
            evidence_maturity_score=d("0.700000"),
            team_memory_quality_score=d("0.700000"),
        ),
        triage_input(
            module,
            "watch-two",
            source_coverage_score=d("0.700000"),
            team_memory_quality_score=d("0.700000"),
        ),
        triage_input(module, "pass-one"),
    )

    assert tuple(row.status for row in triage.rows) == ("watch", "watch", "pass")
    assert triage.status == "watch"
    assert triage.reason_code_counts == (
        module.ResearchStrategyCandidateTriageReadinessReasonCodeCount(
            reason_code="team_memory_quality_watch",
            count=d("2.000000"),
        ),
        module.ResearchStrategyCandidateTriageReadinessReasonCodeCount(
            reason_code="evidence_maturity_watch",
            count=ONE,
        ),
        module.ResearchStrategyCandidateTriageReadinessReasonCodeCount(
            reason_code="source_coverage_watch",
            count=ONE,
        ),
        module.ResearchStrategyCandidateTriageReadinessReasonCodeCount(
            reason_code="triage_readiness_clear",
            count=ONE,
        ),
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_READINESS_REPORT_CONFIG_VERSION",
        "ResearchStrategyCandidateTriageReadinessConfig",
        "ResearchStrategyCandidateTriageReadinessInput",
        "ResearchStrategyCandidateTriageReadinessReasonCodeCount",
        "ResearchStrategyCandidateTriageReadinessReport",
        "ResearchStrategyCandidateTriageReadinessRow",
        "build_research_strategy_candidate_triage_readiness_report",
        "research_strategy_candidate_triage_readiness_report_digest",
        "research_strategy_candidate_triage_readiness_report_payload",
    )

    with pytest.raises(ValueError, match="public_digest"):
        replace(triage, public_digest="0" * 64)
    with pytest.raises(ValueError, match="candidate_count"):
        replace(triage, candidate_count=d("9.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(triage, status="pass")
    with pytest.raises(ValueError, match="status"):
        replace(triage.rows[0], status="review")


def test_static_forbidden_public_surfaces_and_io_are_absent() -> None:
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
        "pathlib",
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
