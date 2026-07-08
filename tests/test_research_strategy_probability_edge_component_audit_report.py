from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_probability_edge_component_audit_report import (
    DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_COMPONENT_AUDIT_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_PROBABILITY_EDGE_COMPONENT_AUDIT_STATUSES,
    ResearchStrategyProbabilityEdgeComponentAuditConfig,
    ResearchStrategyProbabilityEdgeComponentAuditInput,
    ResearchStrategyProbabilityEdgeComponentAuditReasonCodeCount,
    ResearchStrategyProbabilityEdgeComponentAuditReport,
    ResearchStrategyProbabilityEdgeComponentAuditRow,
    build_research_strategy_probability_edge_component_audit_report,
    research_strategy_probability_edge_component_audit_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyProbabilityEdgeComponentAuditConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_COMPONENT_AUDIT_REPORT_CONFIG_VERSION
        ),
        "probability_component_pass_floor": d("0.800000"),
        "probability_component_watch_floor": d("0.500000"),
        "cost_component_pass_floor": d("0.800000"),
        "cost_component_watch_floor": d("0.500000"),
        "confidence_component_pass_floor": d("0.800000"),
        "confidence_component_watch_floor": d("0.500000"),
        "evidence_maturity_component_pass_floor": d("0.800000"),
        "evidence_maturity_component_watch_floor": d("0.500000"),
    }
    values.update(overrides)
    return ResearchStrategyProbabilityEdgeComponentAuditConfig(**values)


def audit_input(
    **overrides: object,
) -> ResearchStrategyProbabilityEdgeComponentAuditInput:
    values = {
        "audit_ref": "raw-" + "candidate-alpha-" + "market-slug",
        "observed_at": datetime(2026, 7, 8, 11, 40, tzinfo=UTC),
        "probability_component_score": d("0.920000"),
        "cost_component_score": d("0.880000"),
        "confidence_component_score": d("0.910000"),
        "evidence_maturity_component_score": d("0.860000"),
    }
    values.update(overrides)
    return ResearchStrategyProbabilityEdgeComponentAuditInput(**values)


def report(
    *rows: ResearchStrategyProbabilityEdgeComponentAuditInput,
    cfg: ResearchStrategyProbabilityEdgeComponentAuditConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyProbabilityEdgeComponentAuditReport:
    return build_research_strategy_probability_edge_component_audit_report(
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


def test_report_decomposes_probability_edge_component_review_readiness() -> None:
    summary = report(
        audit_input(
            audit_ref="raw-" + "candidate-gamma-" + "market-slug",
            probability_component_score=d("0.400000"),
            cost_component_score=d("0.300000"),
            confidence_component_score=d("0.250000"),
            evidence_maturity_component_score=d("0.450000"),
        ),
        audit_input(
            audit_ref="raw-" + "candidate-beta-" + "market-slug",
            probability_component_score=d("0.700000"),
            cost_component_score=d("0.680000"),
            confidence_component_score=d("0.720000"),
            evidence_maturity_component_score=d("0.650000"),
        ),
        audit_input(
            audit_ref="raw-" + "candidate-alpha-" + "market-slug",
            probability_component_score=d("0.920000"),
            cost_component_score=d("0.880000"),
            confidence_component_score=d("0.910000"),
            evidence_maturity_component_score=d("0.860000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategyProbabilityEdgeComponentAuditReport
    assert summary.generated_at == GENERATED_AT
    assert summary.input_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_probability_component_score == d("0.673333")
    assert summary.mean_cost_component_score == d("0.620000")
    assert summary.mean_confidence_component_score == d("0.626667")
    assert summary.mean_evidence_maturity_component_score == d("0.653333")
    assert summary.mean_minimum_component_score == d("0.586667")
    assert summary.minimum_component_floor == d("0.250000")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "confidence_component_review",
        "cost_component_review",
        "evidence_maturity_component_review",
        "probability_component_review",
        "strategy_probability_edge_component_audit_report_block",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64
    assert tuple(row.audit_ref for row in summary.rows) == (
        "raw-" + "candidate-gamma-" + "market-slug",
        "raw-" + "candidate-beta-" + "market-slug",
        "raw-" + "candidate-alpha-" + "market-slug",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyProbabilityEdgeComponentAuditRow)
    assert blocked.minimum_component_score == d("0.250000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "confidence_component_block",
        "cost_component_block",
        "evidence_maturity_component_block",
        "probability_component_block",
    )

    watched = summary.rows[1]
    assert watched.minimum_component_score == d("0.650000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "confidence_component_watch",
        "cost_component_watch",
        "evidence_maturity_component_watch",
        "probability_component_watch",
    )

    passed = summary.rows[2]
    assert passed.status == "pass"
    assert passed.reason_codes == ("strategy_probability_edge_component_audit_pass",)
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["cost_component_watch"] == ResearchStrategyProbabilityEdgeComponentAuditReasonCodeCount(
        reason_code="cost_component_watch",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_empty_report_blocks_for_missing_review_inputs() -> None:
    summary = report()

    assert summary.status == "block"
    assert summary.input_count == d("0.000000")
    assert summary.reason_codes == (
        "strategy_probability_edge_component_audit_report_empty",
    )
    assert summary.reason_code_counts == (
        ResearchStrategyProbabilityEdgeComponentAuditReasonCodeCount(
            reason_code="strategy_probability_edge_component_audit_report_empty",
            count=d("1.000000"),
            input_ratio=d("0.000000"),
        ),
    )
    assert summary.rows == ()


def test_payload_is_deterministic_public_safe_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_probability_edge_component_audit_report_payload(
        report(audit_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_probability_edge_component_audit_report_payload(
        report(audit_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["input_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["minimum_component_score"] == "0.860000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )

    digest_input = dict(first_payload)
    digest_input.pop("derived_validation_digest")
    expected_digest = __import__("hashlib").sha256(
        json.dumps(
            digest_input,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert first_payload["derived_validation_digest"] == expected_digest

    payload_text = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "audit_ref",
        "raw-" + "candidate-alpha",
        "market-slug",
        "question",
        "url",
        "source",
        "dsn",
        "table",
        "token",
        "wal" + "let",
        "or" + "der",
        "trad" + "e",
        "b" + "uy",
        "se" + "ll",
        "reco" + "mmend",
        "siz" + "ing",
    ):
        assert forbidden not in payload_text

    tampered_payload = research_strategy_probability_edge_component_audit_report_payload(
        report(audit_input()),
    )
    tampered_payload["rows"][0]["probability_component_score"] = "0.010000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_probability_edge_component_audit_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_probability_edge_component_audit_report_payload(
            {
                "secret_ref": "redacted",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_non_decimal_bad_times_flags_and_duplicates() -> None:
    with pytest.raises(ValueError, match="probability_component_score"):
        audit_input(probability_component_score=0.92)
    with pytest.raises(ValueError, match="cost_component_score"):
        audit_input(cost_component_score=_DecimalSubclass("0.880000"))
    with pytest.raises(ValueError, match="confidence_component_score"):
        audit_input(confidence_component_score=d("1.200000"))
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
            audit_input(audit_ref="same-ref"),
            audit_input(audit_ref="same-ref"),
        )
    with pytest.raises(ValueError, match="probability_component_pass_floor"):
        config(probability_component_pass_floor=d("0.400000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_have_no_execution_surfaces() -> None:
    summary = report(audit_input())
    row = summary.rows[0]

    assert RESEARCH_STRATEGY_PROBABILITY_EDGE_COMPONENT_AUDIT_STATUSES == (
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
            probability_component_score=d("0.010000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            input_count=d("2.000000"),
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
                "audit_ref",
            }:
                continue
            if any(
                token in item.name
                for token in (
                    "count",
                    "floor",
                    "ratio",
                    "score",
                )
            ):
                assert type(item_value) is Decimal

    import polymarket_alpha_lab.research_strategy_probability_edge_component_audit_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_COMPONENT_AUDIT_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_PROBABILITY_EDGE_COMPONENT_AUDIT_STATUSES",
        "ResearchStrategyProbabilityEdgeComponentAuditConfig",
        "ResearchStrategyProbabilityEdgeComponentAuditInput",
        "ResearchStrategyProbabilityEdgeComponentAuditReasonCodeCount",
        "ResearchStrategyProbabilityEdgeComponentAuditRow",
        "ResearchStrategyProbabilityEdgeComponentAuditReport",
        "build_research_strategy_probability_edge_component_audit_report",
        "research_strategy_probability_edge_component_audit_report_payload",
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
        "trad" + "ing",
        "data" + "base",
        "net" + "work",
        "request",
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
