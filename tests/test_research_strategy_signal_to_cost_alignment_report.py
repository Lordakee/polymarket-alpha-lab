from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_signal_to_cost_alignment_report import (
    DEFAULT_RESEARCH_STRATEGY_SIGNAL_TO_COST_ALIGNMENT_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_SIGNAL_TO_COST_ALIGNMENT_STATUSES,
    ResearchStrategySignalToCostAlignmentConfig,
    ResearchStrategySignalToCostAlignmentInput,
    ResearchStrategySignalToCostAlignmentReasonCodeCount,
    ResearchStrategySignalToCostAlignmentReport,
    ResearchStrategySignalToCostAlignmentRow,
    build_research_strategy_signal_to_cost_alignment_report,
    research_strategy_signal_to_cost_alignment_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategySignalToCostAlignmentConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_SIGNAL_TO_COST_ALIGNMENT_REPORT_CONFIG_VERSION
        ),
        "net_signal_pass_floor": d("0.030000"),
        "net_signal_watch_floor": d("0.000000"),
        "signal_to_cost_ratio_pass_floor": d("2.000000"),
        "signal_to_cost_ratio_watch_floor": d("1.000000"),
        "total_cost_friction_pass_ceiling": d("0.040000"),
        "total_cost_friction_watch_ceiling": d("0.080000"),
        "evidence_quality_pass_floor": d("0.800000"),
        "evidence_quality_watch_floor": d("0.500000"),
        "friction_assumption_quality_pass_floor": d("0.750000"),
        "friction_assumption_quality_watch_floor": d("0.450000"),
        "freshness_pass_floor": d("0.700000"),
        "freshness_watch_floor": d("0.400000"),
    }
    values.update(overrides)
    return ResearchStrategySignalToCostAlignmentConfig(**values)


def alignment_input(**overrides: object) -> ResearchStrategySignalToCostAlignmentInput:
    values = {
        "alignment_case_ref": "case_alpha",
        "strategy_ref": "strategy_alpha",
        "observed_at": datetime(2026, 7, 8, 11, 40, tzinfo=UTC),
        "evidence_signal_strength": d("0.120000"),
        "fee_probability_drag": d("0.010000"),
        "spread_probability_drag": d("0.015000"),
        "slippage_probability_drag": d("0.005000"),
        "settlement_friction_probability_drag": d("0.010000"),
        "evidence_quality_score": d("0.900000"),
        "friction_assumption_quality_score": d("0.850000"),
        "freshness_score": d("0.800000"),
    }
    values.update(overrides)
    return ResearchStrategySignalToCostAlignmentInput(**values)


def report(
    *rows: ResearchStrategySignalToCostAlignmentInput,
    cfg: ResearchStrategySignalToCostAlignmentConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategySignalToCostAlignmentReport:
    return build_research_strategy_signal_to_cost_alignment_report(
        rows,
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


def test_report_aggregates_signal_remaining_after_cost_and_settlement_friction() -> None:
    summary = report(
        alignment_input(
            alignment_case_ref="case_alpha",
            strategy_ref="strategy_alpha",
            evidence_signal_strength=d("0.120000"),
            fee_probability_drag=d("0.010000"),
            spread_probability_drag=d("0.015000"),
            slippage_probability_drag=d("0.005000"),
            settlement_friction_probability_drag=d("0.010000"),
            evidence_quality_score=d("0.900000"),
            friction_assumption_quality_score=d("0.850000"),
            freshness_score=d("0.800000"),
        ),
        alignment_input(
            alignment_case_ref="case_beta",
            strategy_ref="strategy_beta",
            evidence_signal_strength=d("0.090000"),
            fee_probability_drag=d("0.015000"),
            spread_probability_drag=d("0.020000"),
            slippage_probability_drag=d("0.010000"),
            settlement_friction_probability_drag=d("0.015000"),
            evidence_quality_score=d("0.700000"),
            friction_assumption_quality_score=d("0.650000"),
            freshness_score=d("0.550000"),
        ),
        alignment_input(
            alignment_case_ref="case_gamma",
            strategy_ref="strategy_gamma",
            evidence_signal_strength=d("0.050000"),
            fee_probability_drag=d("0.020000"),
            spread_probability_drag=d("0.030000"),
            slippage_probability_drag=d("0.020000"),
            settlement_friction_probability_drag=d("0.020000"),
            evidence_quality_score=d("0.350000"),
            friction_assumption_quality_score=d("0.300000"),
            freshness_score=d("0.250000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategySignalToCostAlignmentReport
    assert summary.generated_at == GENERATED_AT
    assert summary.input_row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_evidence_signal_strength == d("0.086667")
    assert summary.mean_total_cost_friction_probability == d("0.063333")
    assert summary.mean_net_signal_strength == d("0.023333")
    assert summary.mean_signal_to_cost_ratio == d("1.685185")
    assert summary.mean_evidence_quality_score == d("0.650000")
    assert summary.mean_friction_assumption_quality_score == d("0.600000")
    assert summary.mean_freshness_score == d("0.533333")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "signal_to_cost_alignment_report_block",
        "cost_friction_review",
        "evidence_quality_review",
        "freshness_review",
        "friction_assumption_quality_review",
        "net_signal_review",
        "signal_to_cost_ratio_review",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64
    assert tuple(row.alignment_case_ref for row in summary.rows) == (
        "case_gamma",
        "case_beta",
        "case_alpha",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategySignalToCostAlignmentRow)
    assert blocked.total_cost_friction_probability == d("0.090000")
    assert blocked.net_signal_strength == d("-0.040000")
    assert blocked.signal_to_cost_ratio == d("0.555556")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "cost_friction_block",
        "evidence_quality_block",
        "freshness_block",
        "friction_assumption_quality_block",
        "net_signal_block",
        "signal_to_cost_ratio_block",
    )

    watched = summary.rows[1]
    assert watched.total_cost_friction_probability == d("0.060000")
    assert watched.net_signal_strength == d("0.030000")
    assert watched.signal_to_cost_ratio == d("1.500000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "cost_friction_watch",
        "evidence_quality_watch",
        "freshness_watch",
        "friction_assumption_quality_watch",
        "signal_to_cost_ratio_watch",
    )

    passed = summary.rows[2]
    assert passed.net_signal_strength == d("0.080000")
    assert passed.signal_to_cost_ratio == d("3.000000")
    assert passed.status == "pass"
    assert passed.reason_codes == ("signal_to_cost_alignment_pass",)

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["cost_friction_watch"] == ResearchStrategySignalToCostAlignmentReasonCodeCount(
        reason_code="cost_friction_watch",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_payload_is_deterministic_decimal_stringed_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_signal_to_cost_alignment_report_payload(
        report(alignment_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_signal_to_cost_alignment_report_payload(
        report(alignment_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["input_row_count"] == "1.000000"
    assert first_payload["rows"][0]["total_cost_friction_probability"] == "0.040000"
    assert first_payload["rows"][0]["net_signal_strength"] == "0.080000"
    assert first_payload["rows"][0]["signal_to_cost_ratio"] == "3.000000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )

    forbidden_payload_fragments = (
        "market",
        "source",
        "notional",
        "position",
        "stake",
        "amount",
        "quantity",
        "recommend",
    )
    payload_text = repr(first_payload).lower()
    assert all(fragment not in payload_text for fragment in forbidden_payload_fragments)

    tampered_payload = research_strategy_signal_to_cost_alignment_report_payload(
        report(alignment_input()),
    )
    tampered_payload["rows"][0]["settlement_friction_probability_drag"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_signal_to_cost_alignment_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_signal_to_cost_alignment_report_payload(
            {
                "secret_ref": "redacted",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_non_decimal_flags_bad_times_and_duplicate_cases() -> None:
    with pytest.raises(ValueError, match="evidence_signal_strength"):
        alignment_input(evidence_signal_strength=0.12)
    with pytest.raises(ValueError, match="fee_probability_drag"):
        alignment_input(fee_probability_drag=_DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="settlement_friction_probability_drag"):
        alignment_input(settlement_friction_probability_drag=d("1.200000"))
    with pytest.raises(ValueError, match="observed_at"):
        alignment_input(observed_at=datetime(2026, 7, 8, 11, 40))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            alignment_input(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(alignment_input(observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            alignment_input(alignment_case_ref="same_case"),
            alignment_input(alignment_case_ref="same_case", strategy_ref="strategy_beta"),
        )
    with pytest.raises(ValueError, match="evidence_quality_pass_floor"):
        config(evidence_quality_pass_floor=d("0.400000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_module_has_no_external_surfaces() -> None:
    summary = report(alignment_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_SIGNAL_TO_COST_ALIGNMENT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            total_cost_friction_probability=d("0.010000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            input_row_count=d("2.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )

    for value in (
        config(),
        alignment_input(),
        row,
        summary,
        *summary.reason_code_counts,
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item_value is None or item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "reason_codes",
                "reason_code_counts",
                "rows",
                "alignment_case_ref",
                "strategy_ref",
            }:
                continue
            if any(
                token in item.name
                for token in (
                    "count",
                    "drag",
                    "friction",
                    "ratio",
                    "score",
                    "signal",
                )
            ):
                assert type(item_value) is Decimal

    import polymarket_alpha_lab.research_strategy_signal_to_cost_alignment_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_SIGNAL_TO_COST_ALIGNMENT_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_SIGNAL_TO_COST_ALIGNMENT_STATUSES",
        "ResearchStrategySignalToCostAlignmentConfig",
        "ResearchStrategySignalToCostAlignmentInput",
        "ResearchStrategySignalToCostAlignmentReasonCodeCount",
        "ResearchStrategySignalToCostAlignmentRow",
        "ResearchStrategySignalToCostAlignmentReport",
        "build_research_strategy_signal_to_cost_alignment_report",
        "research_strategy_signal_to_cost_alignment_report_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }

    forbidden_terms = (
        "reco" + "mmendation",
        "siz" + "ing",
        "b" + "uy",
        "se" + "ll",
        "wal" + "let",
        "or" + "der",
        "li" + "ve",
        "trad" + "ing",
        "data" + "base",
        "net" + "work",
        "request",
        "socket",
        "subprocess",
        "open(",
        "market_slug",
        "source_ref",
    )
    assert all(term not in source.lower() for term in forbidden_terms)

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
