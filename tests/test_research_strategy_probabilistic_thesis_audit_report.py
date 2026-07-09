from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_probabilistic_thesis_audit_report import (
    DEFAULT_RESEARCH_STRATEGY_PROBABILISTIC_THESIS_AUDIT_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_PROBABILISTIC_THESIS_AUDIT_STATUSES,
    ResearchStrategyProbabilisticThesisAuditConfig,
    ResearchStrategyProbabilisticThesisAuditInput,
    ResearchStrategyProbabilisticThesisAuditReasonCodeCount,
    ResearchStrategyProbabilisticThesisAuditReport,
    ResearchStrategyProbabilisticThesisAuditRow,
    build_research_strategy_probabilistic_thesis_audit_report,
    research_strategy_probabilistic_thesis_audit_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyProbabilisticThesisAuditConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_PROBABILISTIC_THESIS_AUDIT_REPORT_CONFIG_VERSION
        ),
        "evidence_strength_pass_floor": d("0.750000"),
        "evidence_strength_watch_floor": d("0.500000"),
        "source_age_pass_ceiling_seconds": d("86400.000000"),
        "source_age_watch_ceiling_seconds": d("259200.000000"),
        "model_market_divergence_pass_ceiling": d("0.080000"),
        "model_market_divergence_watch_ceiling": d("0.180000"),
        "cost_drag_pass_ceiling": d("0.025000"),
        "cost_drag_watch_ceiling": d("0.070000"),
        "liquidity_reliability_pass_floor": d("0.750000"),
        "liquidity_reliability_watch_floor": d("0.450000"),
        "resolution_clarity_pass_floor": d("0.800000"),
        "resolution_clarity_watch_floor": d("0.500000"),
        "specialist_memory_confidence_pass_floor": d("0.700000"),
        "specialist_memory_confidence_watch_floor": d("0.450000"),
    }
    values.update(overrides)
    return ResearchStrategyProbabilisticThesisAuditConfig(**values)


def audit_input(**overrides: object) -> ResearchStrategyProbabilisticThesisAuditInput:
    values = {
        "thesis_ref": "thesis-alpha",
        "observed_at": datetime(2026, 7, 8, 11, 40, tzinfo=UTC),
        "evidence_strength_score": d("0.900000"),
        "source_age_seconds": d("3600.000000"),
        "model_probability": d("0.620000"),
        "reference_probability": d("0.570000"),
        "cost_drag_score": d("0.012000"),
        "liquidity_reliability_score": d("0.900000"),
        "resolution_clarity_score": d("0.880000"),
        "specialist_memory_confidence_score": d("0.840000"),
    }
    values.update(overrides)
    return ResearchStrategyProbabilisticThesisAuditInput(**values)


def report(
    *rows: ResearchStrategyProbabilisticThesisAuditInput,
    cfg: ResearchStrategyProbabilisticThesisAuditConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyProbabilisticThesisAuditReport:
    return build_research_strategy_probabilistic_thesis_audit_report(
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


def test_report_audits_probabilistic_thesis_support_across_dimensions() -> None:
    summary = report(
        audit_input(thesis_ref="thesis-alpha"),
        audit_input(
            thesis_ref="thesis-beta",
            evidence_strength_score=d("0.650000"),
            source_age_seconds=d("172800.000000"),
            model_probability=d("0.610000"),
            reference_probability=d("0.500000"),
            cost_drag_score=d("0.040000"),
            liquidity_reliability_score=d("0.600000"),
            resolution_clarity_score=d("0.650000"),
            specialist_memory_confidence_score=d("0.600000"),
        ),
        audit_input(
            thesis_ref="thesis-gamma",
            evidence_strength_score=d("0.300000"),
            source_age_seconds=d("400000.000000"),
            model_probability=d("0.760000"),
            reference_probability=d("0.500000"),
            cost_drag_score=d("0.110000"),
            liquidity_reliability_score=d("0.250000"),
            resolution_clarity_score=d("0.300000"),
            specialist_memory_confidence_score=d("0.200000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategyProbabilisticThesisAuditReport
    assert summary.generated_at == GENERATED_AT
    assert summary.source_row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_evidence_strength_score == d("0.616667")
    assert summary.mean_model_market_divergence == d("0.140000")
    assert summary.mean_cost_drag_score == d("0.054000")
    assert summary.mean_liquidity_reliability_score == d("0.583333")
    assert summary.mean_resolution_clarity_score == d("0.610000")
    assert summary.mean_specialist_memory_confidence_score == d("0.546667")
    assert summary.max_source_age_seconds == d("400000.000000")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "probabilistic_thesis_audit_report_block",
        "cost_drag_review",
        "evidence_strength_review",
        "liquidity_reliability_review",
        "model_market_divergence_review",
        "resolution_clarity_review",
        "source_freshness_review",
        "specialist_memory_confidence_review",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64
    assert tuple(row.thesis_ref for row in summary.rows) == (
        "thesis-gamma",
        "thesis-beta",
        "thesis-alpha",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyProbabilisticThesisAuditRow)
    assert blocked.model_market_divergence == d("0.260000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "cost_drag_block",
        "evidence_strength_block",
        "liquidity_reliability_block",
        "model_market_divergence_block",
        "resolution_clarity_block",
        "source_freshness_block",
        "specialist_memory_confidence_block",
    )

    watched = summary.rows[1]
    assert watched.model_market_divergence == d("0.110000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "cost_drag_watch",
        "evidence_strength_watch",
        "liquidity_reliability_watch",
        "model_market_divergence_watch",
        "resolution_clarity_watch",
        "source_freshness_watch",
        "specialist_memory_confidence_watch",
    )

    passed = summary.rows[2]
    assert passed.status == "pass"
    assert passed.reason_codes == ("probabilistic_thesis_audit_pass",)

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["cost_drag_watch"] == ResearchStrategyProbabilisticThesisAuditReasonCodeCount(
        reason_code="cost_drag_watch",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_payload_is_deterministic_redacted_decimal_stringed_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_probabilistic_thesis_audit_report_payload(
        report(audit_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_probabilistic_thesis_audit_report_payload(
        report(audit_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["source_row_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["model_market_divergence"] == "0.050000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )
    payload_text = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "thesis_ref",
        "thesis-alpha",
        "candidate",
        "market_slug",
        "question",
        "https://",
        "postgres://",
        "wallet",
        "order",
        "trade",
        "live",
    ):
        assert forbidden not in payload_text

    tampered_payload = research_strategy_probabilistic_thesis_audit_report_payload(
        report(audit_input()),
    )
    tampered_payload["rows"][0]["cost_drag_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_probabilistic_thesis_audit_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_probabilistic_thesis_audit_report_payload(
            {
                "market_slug": "redacted",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_non_decimal_flags_bad_times_and_duplicate_theses() -> None:
    with pytest.raises(ValueError, match="model_probability"):
        audit_input(model_probability=0.62)
    with pytest.raises(ValueError, match="source_age_seconds"):
        audit_input(source_age_seconds=_DecimalSubclass("3600.000000"))
    with pytest.raises(ValueError, match="reference_probability"):
        audit_input(reference_probability=d("1.200000"))
    with pytest.raises(ValueError, match="observed_at"):
        audit_input(observed_at=datetime(2026, 7, 8, 11, 40))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            audit_input(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(audit_input(observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            audit_input(thesis_ref="same-thesis"),
            audit_input(thesis_ref="same-thesis", evidence_strength_score=d("0.800000")),
        )
    with pytest.raises(ValueError, match="evidence_strength_pass_floor"):
        config(evidence_strength_pass_floor=d("0.400000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_module_has_no_action_surfaces() -> None:
    summary = report(audit_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_PROBABILISTIC_THESIS_AUDIT_STATUSES == (
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
            cost_drag_score=d("0.020000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            source_row_count=d("2.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )

    for value in (
        config(),
        audit_input(),
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
                "thesis_ref",
            }:
                continue
            if any(
                token in item.name
                for token in (
                    "age",
                    "ceiling",
                    "confidence",
                    "count",
                    "drag",
                    "floor",
                    "probability",
                    "ratio",
                    "score",
                    "divergence",
                )
            ):
                assert type(item_value) is Decimal

    import polymarket_alpha_lab.research_strategy_probabilistic_thesis_audit_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_PROBABILISTIC_THESIS_AUDIT_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_PROBABILISTIC_THESIS_AUDIT_STATUSES",
        "ResearchStrategyProbabilisticThesisAuditConfig",
        "ResearchStrategyProbabilisticThesisAuditInput",
        "ResearchStrategyProbabilisticThesisAuditReasonCodeCount",
        "ResearchStrategyProbabilisticThesisAuditRow",
        "ResearchStrategyProbabilisticThesisAuditReport",
        "build_research_strategy_probabilistic_thesis_audit_report",
        "research_strategy_probabilistic_thesis_audit_report_payload",
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

    forbidden_source_terms = (
        "reco" + "mmendation",
        "siz" + "ing",
        "b" + "uy",
        "se" + "ll",
        "wal" + "let",
        "or" + "der",
        "li" + "ve",
        "trad" + "e",
        "position",
        "socket",
        "subprocess",
        "open(",
    )
    assert all(term not in source.lower() for term in forbidden_source_terms)

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
