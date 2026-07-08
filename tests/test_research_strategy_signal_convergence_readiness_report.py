from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_signal_convergence_readiness_report import (
    DEFAULT_RESEARCH_STRATEGY_SIGNAL_CONVERGENCE_READINESS_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_SIGNAL_CONVERGENCE_READINESS_STATUSES,
    ResearchStrategySignalConvergenceReadinessConfig,
    ResearchStrategySignalConvergenceReadinessInput,
    ResearchStrategySignalConvergenceReadinessReasonCodeCount,
    ResearchStrategySignalConvergenceReadinessReport,
    ResearchStrategySignalConvergenceReadinessRow,
    build_research_strategy_signal_convergence_readiness_report,
    research_strategy_signal_convergence_readiness_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategySignalConvergenceReadinessConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_SIGNAL_CONVERGENCE_READINESS_REPORT_CONFIG_VERSION
        ),
        "convergence_pass_floor": d("0.800000"),
        "convergence_watch_floor": d("0.600000"),
        "probability_model_agreement_pass_floor": d("0.800000"),
        "probability_model_agreement_watch_floor": d("0.600000"),
        "independent_consensus_pass_floor": d("0.750000"),
        "independent_consensus_watch_floor": d("0.550000"),
        "mechanics_pass_floor": d("0.700000"),
        "mechanics_watch_floor": d("0.500000"),
        "resolution_clarity_pass_floor": d("0.800000"),
        "resolution_clarity_watch_floor": d("0.600000"),
        "specialist_memory_confidence_pass_floor": d("0.750000"),
        "specialist_memory_confidence_watch_floor": d("0.550000"),
    }
    values.update(overrides)
    return ResearchStrategySignalConvergenceReadinessConfig(**values)


def signal_input(**overrides: object) -> ResearchStrategySignalConvergenceReadinessInput:
    values = {
        "signal_ref": "signal_alpha",
        "strategy_ref": "strategy_alpha",
        "observed_at": datetime(2026, 7, 8, 11, 40, tzinfo=UTC),
        "probability_model_agreement_score": d("0.880000"),
        "independent_consensus_score": d("0.820000"),
        "mechanics_score": d("0.760000"),
        "resolution_clarity_score": d("0.860000"),
        "specialist_memory_confidence_score": d("0.810000"),
    }
    values.update(overrides)
    return ResearchStrategySignalConvergenceReadinessInput(**values)


def report(
    *rows: ResearchStrategySignalConvergenceReadinessInput,
    cfg: ResearchStrategySignalConvergenceReadinessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategySignalConvergenceReadinessReport:
    return build_research_strategy_signal_convergence_readiness_report(
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


def test_report_scores_signal_convergence_readiness_for_research_review() -> None:
    summary = report(
        signal_input(
            signal_ref="signal_alpha",
            strategy_ref="strategy_alpha",
            probability_model_agreement_score=d("0.880000"),
            independent_consensus_score=d("0.820000"),
            mechanics_score=d("0.760000"),
            resolution_clarity_score=d("0.860000"),
            specialist_memory_confidence_score=d("0.810000"),
        ),
        signal_input(
            signal_ref="signal_beta",
            strategy_ref="strategy_beta",
            probability_model_agreement_score=d("0.720000"),
            independent_consensus_score=d("0.700000"),
            mechanics_score=d("0.650000"),
            resolution_clarity_score=d("0.740000"),
            specialist_memory_confidence_score=d("0.650000"),
        ),
        signal_input(
            signal_ref="signal_gamma",
            strategy_ref="strategy_gamma",
            probability_model_agreement_score=d("0.520000"),
            independent_consensus_score=d("0.480000"),
            mechanics_score=d("0.460000"),
            resolution_clarity_score=d("0.580000"),
            specialist_memory_confidence_score=d("0.500000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategySignalConvergenceReadinessReport
    assert summary.generated_at == GENERATED_AT
    assert summary.input_row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_convergence_score == d("0.675333")
    assert summary.mean_probability_model_agreement_score == d("0.706667")
    assert summary.mean_independent_consensus_score == d("0.666667")
    assert summary.mean_mechanics_score == d("0.623333")
    assert summary.mean_resolution_clarity_score == d("0.726667")
    assert summary.mean_specialist_memory_confidence_score == d("0.653333")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "signal_convergence_readiness_report_block",
        "independent_consensus_review",
        "mechanics_review",
        "probability_model_agreement_review",
        "resolution_clarity_review",
        "specialist_memory_confidence_review",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64
    assert tuple(row.signal_ref for row in summary.rows) == (
        "signal_gamma",
        "signal_beta",
        "signal_alpha",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategySignalConvergenceReadinessRow)
    assert blocked.convergence_score == d("0.508000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "convergence_score_block",
        "independent_consensus_block",
        "mechanics_block",
        "probability_model_agreement_block",
        "resolution_clarity_block",
        "specialist_memory_confidence_block",
    )

    watched = summary.rows[1]
    assert watched.convergence_score == d("0.692000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "independent_consensus_watch",
        "mechanics_watch",
        "probability_model_agreement_watch",
        "resolution_clarity_watch",
        "specialist_memory_confidence_watch",
    )

    passed = summary.rows[2]
    assert passed.convergence_score == d("0.826000")
    assert passed.status == "pass"
    assert passed.reason_codes == ("signal_convergence_readiness_pass",)

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts[
        "mechanics_watch"
    ] == ResearchStrategySignalConvergenceReadinessReasonCodeCount(
        reason_code="mechanics_watch",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_payload_is_deterministic_decimal_stringed_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_signal_convergence_readiness_report_payload(
        report(signal_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_signal_convergence_readiness_report_payload(
        report(signal_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["input_row_count"] == "1.000000"
    assert first_payload["rows"][0]["convergence_score"] == "0.826000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )

    forbidden_payload_fragments = (
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "recommend",
        "sizing",
    )
    payload_text = repr(first_payload).lower()
    assert all(fragment not in payload_text for fragment in forbidden_payload_fragments)

    tampered_payload = research_strategy_signal_convergence_readiness_report_payload(
        report(signal_input()),
    )
    tampered_payload["rows"][0]["mechanics_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_signal_convergence_readiness_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_signal_convergence_readiness_report_payload(
            {
                "token_ref": "redacted",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_non_decimal_flags_bad_times_and_duplicate_refs() -> None:
    with pytest.raises(ValueError, match="probability_model_agreement_score"):
        signal_input(probability_model_agreement_score=0.88)
    with pytest.raises(ValueError, match="independent_consensus_score"):
        signal_input(independent_consensus_score=_DecimalSubclass("0.820000"))
    with pytest.raises(ValueError, match="mechanics_score"):
        signal_input(mechanics_score=d("1.200000"))
    with pytest.raises(ValueError, match="observed_at"):
        signal_input(observed_at=datetime(2026, 7, 8, 11, 40))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            signal_input(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(signal_input(observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            signal_input(signal_ref="same_signal"),
            signal_input(signal_ref="same_signal", strategy_ref="strategy_beta"),
        )
    with pytest.raises(ValueError, match="convergence_pass_floor"):
        config(convergence_pass_floor=d("0.500000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="unsafe public"):
        signal_input(signal_ref="market_slug_alpha")


def test_dataclasses_are_frozen_decimal_only_and_module_has_no_execution_surfaces() -> None:
    summary = report(signal_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_SIGNAL_CONVERGENCE_READINESS_STATUSES == (
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
            convergence_score=d("0.010000"),
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
        signal_input(),
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
                "signal_ref",
                "strategy_ref",
            }:
                continue
            if any(
                token in item.name
                for token in (
                    "count",
                    "ratio",
                    "score",
                    "floor",
                )
            ):
                assert type(item_value) is Decimal

    import polymarket_alpha_lab.research_strategy_signal_convergence_readiness_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_SIGNAL_CONVERGENCE_READINESS_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_SIGNAL_CONVERGENCE_READINESS_STATUSES",
        "ResearchStrategySignalConvergenceReadinessConfig",
        "ResearchStrategySignalConvergenceReadinessInput",
        "ResearchStrategySignalConvergenceReadinessReasonCodeCount",
        "ResearchStrategySignalConvergenceReadinessRow",
        "ResearchStrategySignalConvergenceReadinessReport",
        "build_research_strategy_signal_convergence_readiness_report",
        "research_strategy_signal_convergence_readiness_report_payload",
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
        "candidate_id",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
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
