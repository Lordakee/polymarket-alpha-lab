from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_superforecast_prompt_quality_gate_report import (
    DEFAULT_RESEARCH_STRATEGY_SUPERFORECAST_PROMPT_QUALITY_GATE_REPORT_CONFIG_VERSION,
    PROMPT_QUALITY_GATE_STATUSES,
    ResearchStrategySuperforecastPromptContext,
    ResearchStrategySuperforecastPromptQualityGateConfig,
    ResearchStrategySuperforecastPromptQualityGateReasonCodeCount,
    ResearchStrategySuperforecastPromptQualityGateReport,
    ResearchStrategySuperforecastPromptQualityGateRow,
    build_research_strategy_superforecast_prompt_quality_gate_report,
    research_strategy_superforecast_prompt_quality_gate_report_digest,
    research_strategy_superforecast_prompt_quality_gate_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_superforecast_prompt_quality_gate_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategySuperforecastPromptQualityGateConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_SUPERFORECAST_PROMPT_QUALITY_GATE_REPORT_CONFIG_VERSION
        ),
        "sanitized_prompt_context_completeness_pass_floor": d("0.800000"),
        "sanitized_prompt_context_completeness_watch_floor": d("0.550000"),
        "source_diversity_pass_floor": d("0.700000"),
        "source_diversity_watch_floor": d("0.450000"),
        "cost_context_pass_floor": d("0.700000"),
        "cost_context_watch_floor": d("0.500000"),
        "resolution_clarity_pass_floor": d("0.800000"),
        "resolution_clarity_watch_floor": d("0.550000"),
        "domain_memory_readiness_pass_floor": d("0.750000"),
        "domain_memory_readiness_watch_floor": d("0.500000"),
    }
    values.update(overrides)
    return ResearchStrategySuperforecastPromptQualityGateConfig(**values)


def prompt_context(
    prompt_context_key: str = "internal-prompt-pass",
    *,
    sanitized_prompt_context_completeness: Decimal = d("0.900000"),
    source_diversity: Decimal = d("0.850000"),
    cost_context: Decimal = d("0.800000"),
    resolution_clarity: Decimal = d("0.880000"),
    domain_memory_readiness: Decimal = d("0.820000"),
    observed_at: datetime = GENERATED_AT - timedelta(minutes=7),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategySuperforecastPromptContext:
    return ResearchStrategySuperforecastPromptContext(
        prompt_context_key=prompt_context_key,
        sanitized_prompt_context_completeness=sanitized_prompt_context_completeness,
        source_diversity=source_diversity,
        cost_context=cost_context,
        resolution_clarity=resolution_clarity,
        domain_memory_readiness=domain_memory_readiness,
        observed_at=observed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchStrategySuperforecastPromptContext,
    cfg: ResearchStrategySuperforecastPromptQualityGateConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategySuperforecastPromptQualityGateReport:
    return build_research_strategy_superforecast_prompt_quality_gate_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_int_float_or_decimal_values(value: Any) -> None:
    if isinstance(value, bool):
        return
    assert type(value) is not int
    assert type(value) is not float
    assert type(value) is not Decimal
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_float_or_decimal_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_float_or_decimal_values(item)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_prompt_quality_gate_aggregates_pass_watch_block_rows_deterministically() -> None:
    pass_item = prompt_context("internal-prompt-pass", reason_codes=("manual_check",))
    watch_item = prompt_context(
        "internal-prompt-watch",
        sanitized_prompt_context_completeness=d("0.720000"),
        source_diversity=d("0.600000"),
        cost_context=d("0.650000"),
        resolution_clarity=d("0.700000"),
        domain_memory_readiness=d("0.620000"),
    )
    block_item = prompt_context(
        "internal-prompt-block",
        sanitized_prompt_context_completeness=d("0.500000"),
        source_diversity=d("0.400000"),
        cost_context=d("0.450000"),
        resolution_clarity=d("0.520000"),
        domain_memory_readiness=d("0.350000"),
    )

    first = report(watch_item, block_item, pass_item)
    second = report(pass_item, watch_item, block_item)

    assert is_dataclass(first)
    assert PROMPT_QUALITY_GATE_STATUSES == ("pass", "watch", "block")
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        DEFAULT_RESEARCH_STRATEGY_SUPERFORECAST_PROMPT_QUALITY_GATE_REPORT_CONFIG_VERSION
    )
    assert first.prompt_context_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.status == "block"
    assert first.average_prompt_quality_score == d("0.650667")
    assert first.min_prompt_quality_score == d("0.444000")
    assert first.max_prompt_age_seconds == d("420.000000")
    assert tuple(row.row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert len({row.public_prompt_context_hash for row in first.rows}) == 3
    assert all(row.public_prompt_context_hash.startswith("sha256:") for row in first.rows)
    assert all("internal-prompt" not in row.public_prompt_context_hash for row in first.rows)

    blocked = first.rows[0]
    assert blocked.prompt_quality_score == d("0.444000")
    assert blocked.prompt_age_seconds == d("420.000000")
    assert blocked.reason_codes == (
        "sanitized_prompt_context_completeness_block",
        "source_diversity_block",
        "cost_context_block",
        "resolution_clarity_block",
        "domain_memory_readiness_block",
    )
    assert_digest(blocked.validation_digest)
    assert_digest(first.validation_digest)

    payload = research_strategy_superforecast_prompt_quality_gate_report_payload(first)
    assert payload == research_strategy_superforecast_prompt_quality_gate_report_payload(
        second,
    )
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["prompt_context_count"] == "3.000000"
    assert payload["average_prompt_quality_score"] == "0.650667"
    assert payload["rows"][0]["row_number"] == "1.000000"
    assert payload["rows"][0]["prompt_quality_score"] == "0.444000"
    assert payload["rows"][0]["validation_digest"] == blocked.validation_digest
    serialized = json.dumps(payload, sort_keys=True)
    assert "internal-prompt" not in serialized
    assert "prompt_context_key" not in serialized
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_int_float_or_decimal_values(payload)

    digest = research_strategy_superforecast_prompt_quality_gate_report_digest(first)
    assert digest == first.validation_digest
    assert digest == payload["validation_digest"]


def test_empty_report_blocks_with_reason_count() -> None:
    gate = report()

    assert gate.prompt_context_count == ZERO
    assert gate.pass_count == ZERO
    assert gate.watch_count == ZERO
    assert gate.block_count == ZERO
    assert gate.average_prompt_quality_score == ZERO
    assert gate.min_prompt_quality_score == ZERO
    assert gate.max_prompt_age_seconds == ZERO
    assert gate.status == "block"
    assert gate.reason_codes == ("superforecast_prompt_quality_no_prompt_contexts",)
    assert gate.reason_code_counts == (
        ResearchStrategySuperforecastPromptQualityGateReasonCodeCount(
            reason_code="superforecast_prompt_quality_no_prompt_contexts",
            count=d("1.000000"),
        ),
    )
    assert gate.rows == ()
    assert gate.paper_only is True
    assert gate.report_only is True
    assert gate.readonly is True
    assert_digest(gate.validation_digest)


def test_input_reason_code_status_suffixes_do_not_escalate_gate_status() -> None:
    gate = report(
        prompt_context(
            "internal-prompt-input-suffix",
            reason_codes=("manual_block", "operator_watch"),
        ),
    )

    assert gate.status == "pass"
    assert gate.pass_count == ONE
    assert gate.watch_count == ZERO
    assert gate.block_count == ZERO
    assert gate.reason_codes == (
        "superforecast_prompt_quality_pass",
        "input_manual_block",
        "input_operator_watch",
    )
    assert gate.rows[0].status == "pass"
    assert gate.rows[0].reason_codes == (
        "superforecast_prompt_quality_pass",
        "input_manual_block",
        "input_operator_watch",
    )


def test_decimal_only_frozen_flags_and_validation() -> None:
    gate = report(prompt_context("internal-prompt-frozen"))

    assert is_dataclass(ResearchStrategySuperforecastPromptQualityGateConfig)
    assert is_dataclass(ResearchStrategySuperforecastPromptContext)
    assert is_dataclass(ResearchStrategySuperforecastPromptQualityGateRow)
    assert is_dataclass(ResearchStrategySuperforecastPromptQualityGateReasonCodeCount)
    assert is_dataclass(ResearchStrategySuperforecastPromptQualityGateReport)
    with pytest.raises(FrozenInstanceError):
        gate.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        gate.rows[0].prompt_quality_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        prompt_context(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(gate, readonly=False)

    with pytest.raises(ValueError, match="sanitized_prompt_context_completeness"):
        prompt_context(sanitized_prompt_context_completeness=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_diversity"):
        prompt_context(source_diversity=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="resolution_clarity"):
        prompt_context(resolution_clarity=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="observed_at"):
        prompt_context(observed_at=datetime(2026, 7, 8, 17, 53))
    with pytest.raises(ValueError, match="observed_at"):
        prompt_context(observed_at=datetime(2026, 7, 8, 17, 53, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            prompt_context(
                "internal-prompt-future",
                observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(
            prompt_context("internal-prompt-aware"),
            generated_at=datetime(2026, 7, 8, 18, 0),
        )
    with pytest.raises(ValueError, match="prompt_context_key"):
        report(
            prompt_context("internal-prompt-dupe"),
            prompt_context("internal-prompt-dupe"),
        )
    with pytest.raises(ValueError, match="sanitized_prompt_context_completeness_pass_floor"):
        config(
            sanitized_prompt_context_completeness_pass_floor=d("0.500000"),
            sanitized_prompt_context_completeness_watch_floor=d("0.600000"),
        )
    with pytest.raises(ValueError, match="domain_memory_readiness_pass_floor"):
        config(
            domain_memory_readiness_pass_floor=d("0.400000"),
            domain_memory_readiness_watch_floor=d("0.500000"),
        )

    for item in (gate, *gate.rows, *gate.reason_code_counts):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, tuple):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_payload_rejects_tampering_and_unsafe_public_leaks() -> None:
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
        "order-id",
        "trade-id",
        "buy",
        "sell",
        "recommendation",
        "sizing",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            prompt_context(prompt_context_key=unsafe_value)

    gate = report(prompt_context("internal-prompt-consistent"))
    row = gate.rows[0]

    with pytest.raises(ValueError, match="prompt_quality_score must match"):
        replace(row, prompt_quality_score=row.prompt_quality_score - d("0.000001"))
    with pytest.raises(ValueError, match="status must match"):
        replace(row, status="block")
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(row, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count must match"):
        replace(gate, pass_count=d("2.000000"))
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(gate, rows=(report(prompt_context("internal-prompt-zeta")).rows[0], row))
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(gate, validation_digest="0" * 64)

    payload = research_strategy_superforecast_prompt_quality_gate_report_payload(gate)
    assert research_strategy_superforecast_prompt_quality_gate_report_payload(payload) == payload
    with pytest.raises(ValueError, match="readonly"):
        research_strategy_superforecast_prompt_quality_gate_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_superforecast_prompt_quality_gate_report_payload(
            {**payload, "wal" "let": {"address": "0x0"}},
        )
    with pytest.raises(ValueError, match="numeric"):
        research_strategy_superforecast_prompt_quality_gate_report_payload(
            {**payload, "prompt_context_count": 1},
        )
    tampered = dict(payload)
    tampered["average_prompt_quality_score"] = "0.650668"
    with pytest.raises(ValueError, match="validation_digest"):
        research_strategy_superforecast_prompt_quality_gate_report_payload(tampered)

    object.__setattr__(gate.rows[0], "public_prompt_context_hash", "source_url:https")
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_superforecast_prompt_quality_gate_report_payload(gate)


def test_public_exports_and_static_report_only_surface() -> None:
    import polymarket_alpha_lab.research_strategy_superforecast_prompt_quality_gate_report as gate

    assert gate.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_SUPERFORECAST_PROMPT_QUALITY_GATE_REPORT_CONFIG_VERSION",
        "PROMPT_QUALITY_GATE_STATUSES",
        "ResearchStrategySuperforecastPromptContext",
        "ResearchStrategySuperforecastPromptQualityGateConfig",
        "ResearchStrategySuperforecastPromptQualityGateReasonCodeCount",
        "ResearchStrategySuperforecastPromptQualityGateReport",
        "ResearchStrategySuperforecastPromptQualityGateRow",
        "build_research_strategy_superforecast_prompt_quality_gate_report",
        "research_strategy_superforecast_prompt_quality_gate_report_digest",
        "research_strategy_superforecast_prompt_quality_gate_report_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "trading",
        "position_size",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "database",
        "network",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "auth",
    )
    assert [term for term in forbidden_terms if term in lowered] == []

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
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "send",
        "submit",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
