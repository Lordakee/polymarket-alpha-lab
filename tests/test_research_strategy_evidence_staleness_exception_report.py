from __future__ import annotations

import ast
import hashlib
import inspect
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_evidence_staleness_exception_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_EVIDENCE_STALENESS_EXCEPTION_REPORT_CONFIG_VERSION
        ),
        "max_pass_evidence_age_seconds": d("3600.000000"),
        "max_watch_evidence_age_seconds": d("86400.000000"),
        "max_pass_quorum_freshness_age_seconds": d("1800.000000"),
        "max_watch_quorum_freshness_age_seconds": d("7200.000000"),
        "max_pass_contradiction_age_seconds": d("14400.000000"),
        "max_watch_contradiction_age_seconds": d("86400.000000"),
        "max_pass_specialist_review_age_seconds": d("86400.000000"),
        "max_watch_specialist_review_age_seconds": d("259200.000000"),
        "max_pass_manual_escalation_urgency": d("0.300000"),
        "max_watch_manual_escalation_urgency": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchStrategyEvidenceStalenessExceptionConfig(**values)


def stale_input(
    aggregation_key: str = "private-row-alpha",
    *,
    evidence_age_seconds: Decimal = d("1800.000000"),
    quorum_freshness_age_seconds: Decimal = d("900.000000"),
    contradiction_age_seconds: Decimal = d("3600.000000"),
    specialist_review_age_seconds: Decimal = d("43200.000000"),
    manual_escalation_urgency: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchStrategyEvidenceStalenessExceptionInput(
        aggregation_key=aggregation_key,
        evidence_age_seconds=evidence_age_seconds,
        quorum_freshness_age_seconds=quorum_freshness_age_seconds,
        contradiction_age_seconds=contradiction_age_seconds,
        specialist_review_age_seconds=specialist_review_age_seconds,
        manual_escalation_urgency=manual_escalation_urgency,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_research_strategy_evidence_staleness_exception_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_manual_evidence_staleness_exception_review() -> None:
    module = api()
    summary = report()

    assert module.RESEARCH_STRATEGY_EVIDENCE_STALENESS_EXCEPTION_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_EVIDENCE_STALENESS_EXCEPTION_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_EVIDENCE_STALENESS_EXCEPTION_STATUSES",
        "ResearchStrategyEvidenceStalenessExceptionConfig",
        "ResearchStrategyEvidenceStalenessExceptionInput",
        "ResearchStrategyEvidenceStalenessExceptionReasonCodeCount",
        "ResearchStrategyEvidenceStalenessExceptionRow",
        "ResearchStrategyEvidenceStalenessExceptionReport",
        "build_research_strategy_evidence_staleness_exception_report",
        "research_strategy_evidence_staleness_exception_report_payload",
        "research_strategy_evidence_staleness_exception_report_digest",
    )
    assert type(summary) is module.ResearchStrategyEvidenceStalenessExceptionReport
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.config_version == "research-strategy-evidence-staleness-exception-report-v0"
    assert summary.input_row_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.mean_evidence_age_seconds == ZERO
    assert summary.mean_quorum_freshness_age_seconds == ZERO
    assert summary.mean_contradiction_age_seconds == ZERO
    assert summary.mean_specialist_review_age_seconds == ZERO
    assert summary.max_manual_escalation_urgency == ZERO
    assert summary.mean_evidence_staleness_exception_score == ZERO
    assert summary.status == "block"
    assert summary.reason_codes == ("evidence_staleness_exception_report_empty",)
    assert summary.reason_code_counts == ()
    assert summary.rows == ()
    assert len(summary.derived_validation_digest) == 64
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_report_aggregates_evidence_quorum_contradiction_review_and_manual_urgency() -> None:
    summary = report(
        stale_input(
            "raw-candidate-id-should-only-appear-as-a-hash",
            evidence_age_seconds=d("90000.000000"),
            quorum_freshness_age_seconds=d("9000.000000"),
            contradiction_age_seconds=d("100000.000000"),
            specialist_review_age_seconds=d("300000.000000"),
            manual_escalation_urgency=d("0.900000"),
        ),
        stale_input("private-row-pass"),
        stale_input(
            "private-row-watch",
            evidence_age_seconds=d("7200.000000"),
            quorum_freshness_age_seconds=d("3600.000000"),
            contradiction_age_seconds=d("43200.000000"),
            specialist_review_age_seconds=d("129600.000000"),
            manual_escalation_urgency=d("0.500000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.input_row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_evidence_age_seconds == d("33000.000000")
    assert summary.mean_quorum_freshness_age_seconds == d("4500.000000")
    assert summary.mean_contradiction_age_seconds == d("48933.333333")
    assert summary.mean_specialist_review_age_seconds == d("157600.000000")
    assert summary.max_manual_escalation_urgency == d("0.900000")
    assert summary.mean_evidence_staleness_exception_score == d("0.497500")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "evidence_staleness_exception_report_block",
        "evidence_age_exception",
        "quorum_freshness_exception",
        "contradiction_age_exception",
        "specialist_review_age_exception",
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
        b"raw-candidate-id-should-only-appear-as-a-hash",
    ).hexdigest()
    assert blocked.evidence_staleness_exception_score == ZERO
    assert blocked.reason_codes == (
        "evidence_staleness_exception_block",
        "evidence_age_block",
        "quorum_freshness_block",
        "contradiction_age_block",
        "specialist_review_age_block",
        "manual_escalation_urgency_block",
    )
    assert watched.evidence_staleness_exception_score == d("0.583333")
    assert watched.reason_codes == (
        "evidence_staleness_exception_watch",
        "evidence_age_watch",
        "quorum_freshness_watch",
        "contradiction_age_watch",
        "specialist_review_age_watch",
        "manual_escalation_urgency_watch",
    )
    assert passed.evidence_staleness_exception_score == d("0.909167")
    assert passed.reason_codes == ("evidence_staleness_exception_pass",)

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["evidence_age_block"] == (
        api().ResearchStrategyEvidenceStalenessExceptionReasonCodeCount(
            reason_code="evidence_age_block",
            count=d("1.000000"),
            input_ratio=d("0.333333"),
        )
    )


def test_payload_is_deterministic_public_safe_decimal_stringed_and_digest_guarded() -> None:
    module = api()
    first = report(
        stale_input("private-row-z"),
        stale_input("private-row-a"),
    )
    second = report(
        stale_input("private-row-a"),
        stale_input("private-row-z"),
    )

    first_payload = module.research_strategy_evidence_staleness_exception_report_payload(first)
    second_payload = module.research_strategy_evidence_staleness_exception_report_payload(second)

    assert first_payload == second_payload
    assert module.research_strategy_evidence_staleness_exception_report_digest(first) == (
        module.research_strategy_evidence_staleness_exception_report_digest(second)
    )
    assert len(module.research_strategy_evidence_staleness_exception_report_digest(first)) == 64
    assert first_payload["generated_at"] == "2026-07-08T18:00:00+00:00"
    assert first_payload["input_row_count"] == "2.000000"
    assert first_payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert len(first_payload["rows"][0]["aggregate_hash"]) == 64
    assert first_payload["rows"][0]["evidence_staleness_exception_score"] == "0.909167"
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
        "private-row",
        "candidate",
        "market",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
    )
    assert all(fragment not in payload_text for fragment in forbidden_public_fragments)

    tampered_payload = module.research_strategy_evidence_staleness_exception_report_payload(
        report(stale_input()),
    )
    tampered_payload["rows"][0]["evidence_age_seconds"] = "999999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_evidence_staleness_exception_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_evidence_staleness_exception_report_payload(
            {
                "market_id": "hidden",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_non_decimal_bad_flags_bad_times_and_duplicates() -> None:
    module = api()
    summary = report(stale_input())
    row = summary.rows[0]

    for value in (config(), stale_input(), row, summary, *summary.reason_code_counts):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item_value is None or item.name in {
                "aggregation_key",
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
                for token in ("age", "count", "number", "ratio", "score", "urgency")
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="evidence_age_seconds"):
        stale_input(evidence_age_seconds=1800)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="quorum_freshness_age_seconds"):
        stale_input(quorum_freshness_age_seconds=_DecimalSubclass("120.000000"))
    with pytest.raises(ValueError, match="manual_escalation_urgency"):
        stale_input(manual_escalation_urgency=d("1.100000"))
    with pytest.raises(ValueError, match="contradiction_age_seconds"):
        stale_input(contradiction_age_seconds=-d("1.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(stale_input(), generated_at=datetime(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            stale_input(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="duplicate"):
        report(stale_input("same"), stale_input("same"))
    with pytest.raises(ValueError, match="max_pass_evidence_age_seconds"):
        config(max_pass_evidence_age_seconds=d("90000.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        stale_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            evidence_staleness_exception_score=d("0.100000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            input_row_count=d("2.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="report"):
        module.research_strategy_evidence_staleness_exception_report_payload(object())


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
