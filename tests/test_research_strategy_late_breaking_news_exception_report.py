from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 19, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_late_breaking_news_exception_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_LATE_BREAKING_NEWS_EXCEPTION_REPORT_CONFIG_VERSION
        ),
        "max_pass_news_freshness_delta_seconds": d("900.000000"),
        "max_watch_news_freshness_delta_seconds": d("3600.000000"),
        "min_pass_source_class_quorum_count": d("3.000000"),
        "min_watch_source_class_quorum_count": d("2.000000"),
        "max_pass_contradiction_pressure": d("0.200000"),
        "max_watch_contradiction_pressure": d("0.600000"),
        "max_pass_impacted_candidate_count": d("1.000000"),
        "max_watch_impacted_candidate_count": d("5.000000"),
        "max_pass_manual_escalation_urgency": d("0.300000"),
        "max_watch_manual_escalation_urgency": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchStrategyLateBreakingNewsExceptionConfig(**values)


def news_input(
    aggregate_key: str = "raw-row-alpha",
    *,
    news_freshness_delta_seconds: Decimal = d("300.000000"),
    source_class_quorum_count: Decimal = d("4.000000"),
    contradiction_pressure: Decimal = d("0.100000"),
    impacted_candidate_count: Decimal = d("1.000000"),
    manual_escalation_urgency: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchStrategyLateBreakingNewsExceptionInput(
        aggregate_key=aggregate_key,
        news_freshness_delta_seconds=news_freshness_delta_seconds,
        source_class_quorum_count=source_class_quorum_count,
        contradiction_pressure=contradiction_pressure,
        impacted_candidate_count=impacted_candidate_count,
        manual_escalation_urgency=manual_escalation_urgency,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_research_strategy_late_breaking_news_exception_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_late_breaking_news_exception_review() -> None:
    module = api()
    summary = report()

    assert module.RESEARCH_STRATEGY_LATE_BREAKING_NEWS_EXCEPTION_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_LATE_BREAKING_NEWS_EXCEPTION_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_LATE_BREAKING_NEWS_EXCEPTION_STATUSES",
        "ResearchStrategyLateBreakingNewsExceptionConfig",
        "ResearchStrategyLateBreakingNewsExceptionInput",
        "ResearchStrategyLateBreakingNewsExceptionReasonCodeCount",
        "ResearchStrategyLateBreakingNewsExceptionRow",
        "ResearchStrategyLateBreakingNewsExceptionReport",
        "build_research_strategy_late_breaking_news_exception_report",
        "research_strategy_late_breaking_news_exception_report_payload",
        "research_strategy_late_breaking_news_exception_report_digest",
    )
    assert type(summary) is module.ResearchStrategyLateBreakingNewsExceptionReport
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.config_version == "research-strategy-late-breaking-news-exception-report-v0"
    assert summary.input_row_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.max_news_freshness_delta_seconds == ZERO
    assert summary.min_source_class_quorum_count == ZERO
    assert summary.max_contradiction_pressure == ZERO
    assert summary.total_impacted_candidate_count == ZERO
    assert summary.max_manual_escalation_urgency == ZERO
    assert summary.mean_late_breaking_news_exception_score == ZERO
    assert summary.status == "block"
    assert summary.reason_codes == ("late_breaking_news_exception_report_empty",)
    assert summary.reason_code_counts == ()
    assert summary.rows == ()
    assert len(summary.derived_validation_digest) == 64
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_report_aggregates_freshness_quorum_contradiction_impact_and_urgency() -> None:
    summary = report(
        news_input(
            "raw-candidate-market-slug-question-source-url-should-only-hash",
            news_freshness_delta_seconds=d("7200.000000"),
            source_class_quorum_count=d("1.000000"),
            contradiction_pressure=d("0.900000"),
            impacted_candidate_count=d("7.000000"),
            manual_escalation_urgency=d("0.900000"),
        ),
        news_input("raw-row-pass"),
        news_input(
            "raw-row-watch",
            news_freshness_delta_seconds=d("1800.000000"),
            source_class_quorum_count=d("2.000000"),
            contradiction_pressure=d("0.400000"),
            impacted_candidate_count=d("3.000000"),
            manual_escalation_urgency=d("0.500000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.input_row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.max_news_freshness_delta_seconds == d("7200.000000")
    assert summary.min_source_class_quorum_count == d("1.000000")
    assert summary.max_contradiction_pressure == d("0.900000")
    assert summary.total_impacted_candidate_count == d("11.000000")
    assert summary.max_manual_escalation_urgency == d("0.900000")
    assert summary.mean_late_breaking_news_exception_score == d("0.456667")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "late_breaking_news_exception_report_block",
        "news_freshness_delta_exception",
        "source_class_quorum_exception",
        "contradiction_pressure_exception",
        "impacted_candidate_count_exception",
        "manual_escalation_urgency_exception",
    )

    blocked, watched, passed = summary.rows
    assert tuple(row.aggregate_row_number for row in summary.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")
    assert blocked.aggregate_hash == hashlib.sha256(
        b"raw-candidate-market-slug-question-source-url-should-only-hash",
    ).hexdigest()
    assert blocked.late_breaking_news_exception_score == ZERO
    assert blocked.reason_codes == (
        "late_breaking_news_exception_block",
        "news_freshness_delta_block",
        "source_class_quorum_block",
        "contradiction_pressure_block",
        "impacted_candidate_count_block",
        "manual_escalation_urgency_block",
    )
    assert watched.late_breaking_news_exception_score == d("0.480000")
    assert watched.reason_codes == (
        "late_breaking_news_exception_watch",
        "news_freshness_delta_watch",
        "source_class_quorum_watch",
        "contradiction_pressure_watch",
        "impacted_candidate_count_watch",
        "manual_escalation_urgency_watch",
    )
    assert passed.late_breaking_news_exception_score == d("0.890000")
    assert passed.reason_codes == ("late_breaking_news_exception_pass",)

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["news_freshness_delta_block"] == (
        api().ResearchStrategyLateBreakingNewsExceptionReasonCodeCount(
            reason_code="news_freshness_delta_block",
            count=d("1.000000"),
            input_ratio=d("0.333333"),
        )
    )


def test_payload_is_deterministic_public_safe_decimal_stringed_and_digest_guarded() -> None:
    module = api()
    first = report(
        news_input("raw-row-z"),
        news_input("raw-row-a"),
    )
    second = report(
        news_input("raw-row-a"),
        news_input("raw-row-z"),
    )

    first_payload = module.research_strategy_late_breaking_news_exception_report_payload(first)
    second_payload = module.research_strategy_late_breaking_news_exception_report_payload(second)

    assert first_payload == second_payload
    assert module.research_strategy_late_breaking_news_exception_report_digest(first) == (
        module.research_strategy_late_breaking_news_exception_report_digest(second)
    )
    assert len(module.research_strategy_late_breaking_news_exception_report_digest(first)) == 64
    assert first_payload["generated_at"] == "2026-07-08T19:00:00+00:00"
    assert first_payload["input_row_count"] == "2.000000"
    assert first_payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert len(first_payload["rows"][0]["aggregate_hash"]) == 64
    assert first_payload["rows"][0]["late_breaking_news_exception_score"] == "0.890000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in _walk_payload_values(first_payload)
    )

    payload_text = repr(first_payload).lower()
    forbidden_public_fragments = (
        "raw-row",
        "raw-candidate",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
    )
    assert all(fragment not in payload_text for fragment in forbidden_public_fragments)

    tampered_payload = module.research_strategy_late_breaking_news_exception_report_payload(
        report(news_input()),
    )
    tampered_payload["rows"][0]["news_freshness_delta_seconds"] = "999999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_late_breaking_news_exception_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_late_breaking_news_exception_report_payload(
            {
                "market_id": "hidden",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_non_decimal_bad_flags_bad_times_and_duplicates() -> None:
    module = api()
    summary = report(news_input())
    row = summary.rows[0]

    for value in (config(), news_input(), row, summary, *summary.reason_code_counts):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item_value is None or item.name in {
                "aggregate_key",
                "aggregate_hash",
                "config_version",
                "derived_validation_digest",
                "paper_only",
                "reason_codes",
                "reason_code_counts",
                "readonly",
                "report_only",
                "rows",
                "status",
            }:
                continue
            if any(
                token in item.name
                for token in ("count", "delta", "number", "pressure", "score", "urgency")
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="news_freshness_delta_seconds"):
        news_input(news_freshness_delta_seconds=300)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_class_quorum_count"):
        news_input(source_class_quorum_count=_DecimalSubclass("2.000000"))
    with pytest.raises(ValueError, match="contradiction_pressure"):
        news_input(contradiction_pressure=d("1.100000"))
    with pytest.raises(ValueError, match="impacted_candidate_count"):
        news_input(impacted_candidate_count=-d("1.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(news_input(), generated_at=datetime(2026, 7, 8, 19, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            news_input(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 19, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="duplicate"):
        report(news_input("same"), news_input("same"))
    with pytest.raises(ValueError, match="max_pass_news_freshness_delta_seconds"):
        config(max_pass_news_freshness_delta_seconds=d("4000.000000"))
    with pytest.raises(ValueError, match="min_pass_source_class_quorum_count"):
        config(min_pass_source_class_quorum_count=d("1.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        news_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            late_breaking_news_exception_score=d("0.100000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            input_row_count=d("2.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="report"):
        module.research_strategy_late_breaking_news_exception_report_payload(object())


def test_owned_module_has_no_external_execution_or_private_public_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

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
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "recommendation",
        "sizing",
        "buy",
        "sell",
        "wallet",
        "order",
        "live",
        "trading",
        "database",
        "network",
        "request",
        "socket",
        "subprocess",
        "open(",
        "connect(",
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


def _walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(_walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_payload_values(item))
        return tuple(values)
    return (value,)
