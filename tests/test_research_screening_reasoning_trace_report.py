from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_screening_reasoning_trace_report import (
    ResearchScreeningReasoningTraceConfig,
    ResearchScreeningReasoningTraceInput,
    ResearchScreeningReasoningTraceReport,
    build_research_screening_reasoning_trace_report,
    research_screening_reasoning_trace_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchScreeningReasoningTraceConfig:
    values = {
        "config_version": "research-screening-reasoning-trace-report-v0",
        "pass_score_threshold": d("0.700000"),
        "block_score_threshold": d("0.400000"),
        "min_scoring_source_count": d("2.000000"),
    }
    values.update(overrides)
    return ResearchScreeningReasoningTraceConfig(**values)


def trace_input(
    trace_key: str,
    *,
    screening_stage: str = "initial_screen",
    scoring_source_codes: tuple[str, ...] = ("source_quality", "cross_source_agreement"),
    screening_score: Decimal = d("0.850000"),
    source_quality_score: Decimal = d("0.800000"),
    source_agreement_score: Decimal = d("0.900000"),
    freshness_score: Decimal = d("0.750000"),
    safety_score: Decimal = d("0.950000"),
    blocking_reason_codes: tuple[str, ...] = (),
    review_prompt_codes: tuple[str, ...] = (),
) -> ResearchScreeningReasoningTraceInput:
    return ResearchScreeningReasoningTraceInput(
        trace_key=trace_key,
        screening_stage=screening_stage,
        scoring_source_codes=scoring_source_codes,
        screening_score=screening_score,
        source_quality_score=source_quality_score,
        source_agreement_score=source_agreement_score,
        freshness_score=freshness_score,
        safety_score=safety_score,
        blocking_reason_codes=blocking_reason_codes,
        review_prompt_codes=review_prompt_codes,
    )


def report(
    *rows: ResearchScreeningReasoningTraceInput,
    cfg: ResearchScreeningReasoningTraceConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchScreeningReasoningTraceReport:
    return build_research_screening_reasoning_trace_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_builds_pass_watch_and_block_reasoning_trace_report() -> None:
    trace_report = report(
        trace_input("trace_pass", screening_score=d("0.900000")),
        trace_input(
            "trace_watch_prompt",
            screening_score=d("0.650000"),
            review_prompt_codes=("verify_public_source_agreement",),
        ),
        trace_input(
            "trace_block",
            scoring_source_codes=("source_quality",),
            screening_score=d("0.350000"),
            blocking_reason_codes=("unsafe_reasoning_surface_block",),
        ),
    )

    assert type(trace_report) is ResearchScreeningReasoningTraceReport
    assert trace_report.generated_at == GENERATED_AT
    assert trace_report.input_trace_count == d("3.000000")
    assert trace_report.pass_trace_count == d("1.000000")
    assert trace_report.watch_trace_count == d("1.000000")
    assert trace_report.block_trace_count == d("1.000000")
    assert trace_report.review_prompt_trace_count == d("1.000000")
    assert trace_report.blocking_reason_trace_count == d("1.000000")
    assert trace_report.thin_source_trace_count == d("1.000000")
    assert trace_report.average_screening_score == d("0.633333")
    assert trace_report.min_screening_score == d("0.350000")
    assert trace_report.report_status == "block"
    assert trace_report.reason_codes == (
        "research_screening_reasoning_trace_block",
        "screening_blocking_reasons_present",
        "screening_review_prompts_present",
        "screening_score_block_present",
        "screening_score_watch_present",
        "screening_sources_thin_present",
    )

    assert tuple(row.trace_key for row in trace_report.rows) == (
        "trace_block",
        "trace_watch_prompt",
        "trace_pass",
    )
    assert tuple(row.trace_rank for row in trace_report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.trace_status for row in trace_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert trace_report.rows[0].reason_codes == (
        "screening_blocking_reasons_present",
        "screening_score_block",
        "screening_sources_thin",
        "screening_trace_block",
    )


def test_empty_input_blocks_with_clear_review_only_surface() -> None:
    trace_report = report()

    assert trace_report.input_trace_count == d("0.000000")
    assert trace_report.pass_trace_count == d("0.000000")
    assert trace_report.watch_trace_count == d("0.000000")
    assert trace_report.block_trace_count == d("0.000000")
    assert trace_report.average_screening_score == d("0.000000")
    assert trace_report.report_status == "block"
    assert trace_report.reason_codes == ("no_screening_traces",)
    assert trace_report.rows == ()
    assert trace_report.reason_code_counts[0].reason_code == "no_screening_traces"
    assert trace_report.reason_code_counts[0].count == d("1.000000")
    assert trace_report.paper_only is True
    assert trace_report.report_only is True
    assert trace_report.readonly is True


def test_payload_uses_decimal_strings_and_contains_no_sensitive_surface() -> None:
    payload = research_screening_reasoning_trace_report_payload(
        report(
            trace_input(
                "trace_payload",
                screening_score=d("0.650000"),
                review_prompt_codes=("review_public_evidence_gap",),
            ),
        ),
    )

    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["input_trace_count"] == "1.000000"
    assert payload["rows"][0]["screening_score"] == "0.650000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.65" not in encoded
    lowered_payload = encoded.lower()
    for unsafe in (
        "raw_id",
        "source_url",
        "raw_text",
        "market_question",
        "dsn",
        "table",
        "token",
        "buy",
        "sell",
        "position",
        "recommend",
    ):
        assert unsafe not in lowered_payload


def test_frozen_dataclasses_strict_decimal_inputs_and_safe_codes() -> None:
    trace_report = report(trace_input("trace_safe"))

    with pytest.raises(FrozenInstanceError):
        trace_report.report_status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        trace_report.rows[0].screening_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="screening_score"):
        trace_input("trace_float", screening_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_quality_score"):
        trace_input("trace_decimal_subclass", source_quality_score=_DecimalSubclass("0.7"))
    with pytest.raises(ValueError, match="scoring_source_codes"):
        trace_input(
            "trace_list_sources",
            scoring_source_codes=["source_quality"],  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="unsafe public string"):
        trace_input("trace_url", scoring_source_codes=("https://example.test/source",))
    with pytest.raises(ValueError, match="unsafe public string"):
        trace_input("trace_action", review_prompt_codes=("reco" "mmend_entry",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(trace_input("trace_flags"), paper_only=False)


def test_payload_rejects_nested_flag_and_payload_tampering() -> None:
    import polymarket_alpha_lab.research_screening_reasoning_trace_report as module

    trace_report = report(trace_input("trace_tamper"))

    object.__setattr__(trace_report.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        research_screening_reasoning_trace_report_payload(trace_report)
    object.__setattr__(trace_report.rows[0], "paper_only", True)

    original_asdict = module.asdict
    try:
        module.asdict = lambda value: {  # type: ignore[method-assign]
            **original_asdict(value),
            "raw_id": "abc",
        }
        with pytest.raises(ValueError, match="unsafe public surface field"):
            research_screening_reasoning_trace_report_payload(trace_report)

        module.asdict = lambda value: {  # type: ignore[method-assign]
            **original_asdict(value),
            "input_trace_count": 1.0,
        }
        with pytest.raises(ValueError, match="must not be a float"):
            research_screening_reasoning_trace_report_payload(trace_report)
    finally:
        module.asdict = original_asdict  # type: ignore[method-assign]


def test_owned_module_has_no_network_filesystem_execution_or_action_language_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_screening_reasoning_trace_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "buy",
        "sell",
        "position",
        "recommend",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
