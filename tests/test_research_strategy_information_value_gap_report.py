from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_strategy_information_value_gap_report import (
    DEFAULT_RESEARCH_STRATEGY_INFORMATION_VALUE_GAP_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_INFORMATION_VALUE_GAP_STATUSES,
    ResearchStrategyInformationValueGapConfig,
    ResearchStrategyInformationValueGapInput,
    ResearchStrategyInformationValueGapReport,
    ResearchStrategyInformationValueGapRow,
    build_research_strategy_information_value_gap_report,
    research_strategy_information_value_gap_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyInformationValueGapConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_INFORMATION_VALUE_GAP_REPORT_CONFIG_VERSION
        ),
        "value_gap_watch_threshold": d("0.200000"),
        "value_gap_block_threshold": d("0.600000"),
        "evidence_quality_watch_floor": d("0.600000"),
        "evidence_quality_block_floor": d("0.250000"),
        "category_importance_watch_threshold": d("0.700000"),
        "readiness_dependency_watch_threshold": d("0.700000"),
    }
    values.update(overrides)
    return ResearchStrategyInformationValueGapConfig(**values)


def gap_input(**overrides: object) -> ResearchStrategyInformationValueGapInput:
    values = {
        "evidence_gap_ref": "gap_alpha",
        "strategy_ref": "strategy_alpha",
        "missing_evidence_category": "source_corroboration",
        "observed_at": datetime(2026, 7, 8, 11, 45, tzinfo=UTC),
        "category_importance_score": d("0.900000"),
        "available_evidence_score": d("0.100000"),
        "readiness_dependency_score": d("0.900000"),
    }
    values.update(overrides)
    return ResearchStrategyInformationValueGapInput(**values)


def report(
    *rows: ResearchStrategyInformationValueGapInput,
    cfg: ResearchStrategyInformationValueGapConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyInformationValueGapReport:
    return build_research_strategy_information_value_gap_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_report_prioritizes_sanitized_missing_evidence_categories_for_review() -> None:
    summary = report(
        gap_input(),
        gap_input(
            evidence_gap_ref="gap_beta",
            strategy_ref="strategy_beta",
            missing_evidence_category="resolution_rule",
            observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
            category_importance_score=d("0.800000"),
            available_evidence_score=d("0.500000"),
            readiness_dependency_score=d("0.600000"),
        ),
        gap_input(
            evidence_gap_ref="gap_gamma",
            strategy_ref="strategy_gamma",
            missing_evidence_category="base_rate_context",
            observed_at=datetime(2026, 7, 8, 11, 55, tzinfo=UTC),
            category_importance_score=d("0.500000"),
            available_evidence_score=d("0.900000"),
            readiness_dependency_score=d("0.400000"),
        ),
    )

    assert summary.generated_at == GENERATED_AT
    assert (
        summary.config_version
        == DEFAULT_RESEARCH_STRATEGY_INFORMATION_VALUE_GAP_REPORT_CONFIG_VERSION
    )
    assert summary.source_row_count == d("3")
    assert summary.pass_count == d("1")
    assert summary.watch_count == d("1")
    assert summary.block_count == d("1")
    assert summary.mean_missing_evidence_quality_gap == d("0.500000")
    assert summary.mean_information_value_gap_score == d("0.329667")
    assert summary.highest_information_value_gap_score == d("0.729000")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "category_importance_review",
        "evidence_quality_review",
        "information_value_gap_block",
        "readiness_dependency_review",
        "value_gap_review",
    )
    assert tuple(row.missing_evidence_category for row in summary.rows) == (
        "source_corroboration",
        "resolution_rule",
        "base_rate_context",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyInformationValueGapRow)
    assert blocked.missing_evidence_quality_gap == d("0.900000")
    assert blocked.information_value_gap_score == d("0.729000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "evidence_quality_block",
        "high_category_importance",
        "high_readiness_dependency",
        "value_gap_block",
    )

    watched = summary.rows[1]
    assert watched.missing_evidence_quality_gap == d("0.500000")
    assert watched.information_value_gap_score == d("0.240000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "evidence_quality_watch",
        "value_gap_watch",
    )

    passed = summary.rows[2]
    assert passed.missing_evidence_quality_gap == d("0.100000")
    assert passed.information_value_gap_score == d("0.020000")
    assert passed.status == "pass"
    assert passed.reason_codes == ("information_value_gap_pass",)
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True
    assert len(passed.derived_validation_digest) == 64


def test_payload_is_deterministic_decimal_stringed_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_information_value_gap_report_payload(
        report(gap_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_information_value_gap_report_payload(
        report(gap_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["source_row_count"] == "1.000000"
    assert first_payload["highest_information_value_gap_score"] == "0.729000"
    assert first_payload["rows"][0]["missing_evidence_quality_gap"] == "0.900000"
    assert first_payload["rows"][0]["information_value_gap_score"] == "0.729000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64

    payload_text = repr(first_payload).lower()
    forbidden_payload_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "sizing",
    )
    assert all(fragment not in payload_text for fragment in forbidden_payload_fragments)

    tampered_payload = research_strategy_information_value_gap_report_payload(
        report(gap_input()),
    )
    tampered_payload["rows"][0]["information_value_gap_score"] = "0.010000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_information_value_gap_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_information_value_gap_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "token_ref": "redacted",
            },
        )

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_information_value_gap_report_payload(
            {
                "note": "connect wallet",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_non_decimal_flags_times_categories_and_duplicates() -> None:
    with pytest.raises(ValueError, match="category_importance_score"):
        gap_input(category_importance_score=0.9)
    with pytest.raises(ValueError, match="available_evidence_score"):
        gap_input(available_evidence_score=d("1.200000"))
    with pytest.raises(ValueError, match="missing_evidence_category"):
        gap_input(missing_evidence_category="raw_url")
    with pytest.raises(ValueError, match="evidence_gap_ref"):
        gap_input(evidence_gap_ref="wallet_reference")
    with pytest.raises(ValueError, match="observed_at"):
        gap_input(observed_at=datetime(2026, 7, 8, 11, 45))
    with pytest.raises(ValueError, match="generated_at"):
        report(gap_input(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(gap_input(observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            gap_input(evidence_gap_ref="same_gap"),
            gap_input(evidence_gap_ref="same_gap", strategy_ref="strategy_beta"),
        )
    with pytest.raises(ValueError, match="threshold"):
        config(value_gap_watch_threshold=d("0.700000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_reject_tampering() -> None:
    summary = report(gap_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_INFORMATION_VALUE_GAP_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    with pytest.raises(FrozenInstanceError):
        row.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            information_value_gap_score=d("0.010000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            source_row_count=d("0"),
            derived_validation_digest=summary.derived_validation_digest,
        )


def test_module_scope_is_pure_report_reducer_with_local_exports_only() -> None:
    import polymarket_alpha_lab.research_strategy_information_value_gap_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_INFORMATION_VALUE_GAP_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_INFORMATION_VALUE_GAP_STATUSES",
        "ResearchStrategyInformationValueGapConfig",
        "ResearchStrategyInformationValueGapInput",
        "ResearchStrategyInformationValueGapRow",
        "ResearchStrategyInformationValueGapReport",
        "build_research_strategy_information_value_gap_report",
        "research_strategy_information_value_gap_report_payload",
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
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wal" + "let",
        "or" + "der",
        "li" + "ve",
        "trad" + "e",
        "trad" + "ing",
        "b" + "uy",
        "se" + "ll",
        "reco" + "mmendation",
        "siz" + "ing",
        "data" + "base",
        "net" + "work",
        "request",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
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
