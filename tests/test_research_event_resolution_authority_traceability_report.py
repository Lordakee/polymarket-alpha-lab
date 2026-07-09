from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_event_resolution_authority_traceability_report"
)
GENERATED_AT = datetime(2026, 7, 8, 14, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_TRACEABILITY_REPORT_CONFIG_VERSION
        ),
        "min_pass_rule_clarity": d("0.800000"),
        "min_watch_rule_clarity": d("0.600000"),
        "min_pass_source_authority": d("0.800000"),
        "min_watch_source_authority": d("0.600000"),
        "max_pass_ambiguity_risk": d("0.100000"),
        "max_watch_ambiguity_risk": d("0.300000"),
        "max_pass_contradiction_pressure": d("0.100000"),
        "max_watch_contradiction_pressure": d("0.300000"),
        "max_pass_stale_rule_age_days": d("7"),
        "max_watch_stale_rule_age_days": d("30"),
        "min_pass_manual_verification_coverage": d("0.900000"),
        "min_watch_manual_verification_coverage": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchEventResolutionAuthorityTraceabilityConfig(**values)


def event_input(
    event_reference_key: str = "private-event-pass",
    *,
    rule_clarity: Decimal = d("0.950000"),
    source_authority: Decimal = d("0.900000"),
    ambiguity_risk: Decimal = d("0.050000"),
    contradiction_pressure: Decimal = d("0.020000"),
    stale_rule_age_days: Decimal = d("3"),
    manual_verification_required_count: Decimal = d("4"),
    manual_verification_completed_count: Decimal = d("4"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchEventResolutionAuthorityTraceabilityInput(
        event_reference_key=event_reference_key,
        rule_clarity=rule_clarity,
        source_authority=source_authority,
        ambiguity_risk=ambiguity_risk,
        contradiction_pressure=contradiction_pressure,
        stale_rule_age_days=stale_rule_age_days,
        manual_verification_required_count=manual_verification_required_count,
        manual_verification_completed_count=manual_verification_completed_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_research_event_resolution_authority_traceability_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_report_blocks_before_strategy_review_without_authority_inputs() -> None:
    module = api()
    result = report()

    assert module.RESEARCH_EVENT_RESOLUTION_AUTHORITY_TRACEABILITY_REPORT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_TRACEABILITY_REPORT_CONFIG_VERSION",
        "RESEARCH_EVENT_RESOLUTION_AUTHORITY_TRACEABILITY_REPORT_STATUSES",
        "ResearchEventResolutionAuthorityTraceabilityConfig",
        "ResearchEventResolutionAuthorityTraceabilityInput",
        "ResearchEventResolutionAuthorityTraceabilityReasonCodeCount",
        "ResearchEventResolutionAuthorityTraceabilityRow",
        "ResearchEventResolutionAuthorityTraceabilityReport",
        "build_research_event_resolution_authority_traceability_report",
        "research_event_resolution_authority_traceability_report_payload",
        "research_event_resolution_authority_traceability_report_digest",
    )
    assert type(result) is module.ResearchEventResolutionAuthorityTraceabilityReport
    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "research-event-resolution-authority-traceability-report-v0"
    )
    assert result.input_row_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.mean_authority_traceability_score == ZERO
    assert result.min_rule_clarity == ZERO
    assert result.min_source_authority == ZERO
    assert result.max_ambiguity_risk == ZERO
    assert result.max_contradiction_pressure == ZERO
    assert result.max_stale_rule_age_days == ZERO
    assert result.mean_manual_verification_coverage == ZERO
    assert result.status == "block"
    assert result.reason_codes == (
        "event_resolution_authority_traceability_report_empty",
    )
    assert result.reason_code_counts == ()
    assert result.rows == ()
    assert len(result.derived_validation_digest) == 64
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_report_scores_resolution_authority_traceability_pass_watch_block() -> None:
    result = report(
        event_input(
            "raw_candidate_id_market_id_market_slug_question_source_url_text_token",
            rule_clarity=d("0.400000"),
            source_authority=d("0.500000"),
            ambiguity_risk=d("0.500000"),
            contradiction_pressure=d("0.600000"),
            stale_rule_age_days=d("45"),
            manual_verification_required_count=d("4"),
            manual_verification_completed_count=d("1"),
        ),
        event_input(
            "private-event-watch",
            rule_clarity=d("0.700000"),
            source_authority=d("0.700000"),
            ambiguity_risk=d("0.200000"),
            contradiction_pressure=d("0.200000"),
            stale_rule_age_days=d("15"),
            manual_verification_required_count=d("4"),
            manual_verification_completed_count=d("3"),
        ),
        event_input("private-event-pass"),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    assert result.generated_at == GENERATED_AT
    assert result.input_row_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.mean_authority_traceability_score == d("0.665556")
    assert result.min_rule_clarity == d("0.400000")
    assert result.min_source_authority == d("0.500000")
    assert result.max_ambiguity_risk == d("0.500000")
    assert result.max_contradiction_pressure == d("0.600000")
    assert result.max_stale_rule_age_days == d("45.000000")
    assert result.mean_manual_verification_coverage == d("0.666667")
    assert result.status == "block"
    assert result.reason_codes == (
        "event_resolution_authority_traceability_report_block",
        "rule_clarity_exception",
        "source_authority_exception",
        "ambiguity_risk_exception",
        "contradiction_pressure_exception",
        "stale_rule_age_exception",
        "manual_verification_coverage_exception",
    )

    blocked, watched, passed = result.rows
    assert tuple(row.aggregate_row_number for row in result.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    assert blocked.event_trace_hash == hashlib.sha256(
        b"raw_candidate_id_market_id_market_slug_question_source_url_text_token",
    ).hexdigest()
    assert blocked.manual_verification_coverage == d("0.250000")
    assert blocked.authority_traceability_score == d("0.341667")
    assert blocked.reason_codes == (
        "event_resolution_authority_traceability_block",
        "rule_clarity_block",
        "source_authority_block",
        "ambiguity_risk_block",
        "contradiction_pressure_block",
        "stale_rule_age_block",
        "manual_verification_coverage_block",
    )
    assert watched.manual_verification_coverage == d("0.750000")
    assert watched.authority_traceability_score == d("0.708333")
    assert watched.reason_codes == (
        "event_resolution_authority_traceability_watch",
        "rule_clarity_watch",
        "source_authority_watch",
        "ambiguity_risk_watch",
        "contradiction_pressure_watch",
        "stale_rule_age_watch",
        "manual_verification_coverage_watch",
    )
    assert passed.authority_traceability_score == d("0.946667")
    assert passed.reason_codes == ("event_resolution_authority_traceability_pass",)

    counts = {item.reason_code: item for item in result.reason_code_counts}
    assert counts["stale_rule_age_block"] == (
        api().ResearchEventResolutionAuthorityTraceabilityReasonCodeCount(
            reason_code="stale_rule_age_block",
            count=d("1.000000"),
            input_ratio=d("0.333333"),
        )
    )


def test_payload_is_deterministic_public_safe_decimal_stringed_and_digest_guarded() -> None:
    module = api()
    first = report(event_input("private-event-z"), event_input("private-event-a"))
    second = report(event_input("private-event-a"), event_input("private-event-z"))

    first_payload = module.research_event_resolution_authority_traceability_report_payload(
        first,
    )
    second_payload = module.research_event_resolution_authority_traceability_report_payload(
        second,
    )

    assert first_payload == second_payload
    assert module.research_event_resolution_authority_traceability_report_digest(first) == (
        module.research_event_resolution_authority_traceability_report_digest(second)
    )
    assert len(module.research_event_resolution_authority_traceability_report_digest(first)) == 64
    assert first_payload["generated_at"] == "2026-07-08T14:30:00+00:00"
    assert first_payload["input_row_count"] == "2.000000"
    assert first_payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert len(first_payload["rows"][0]["event_trace_hash"]) == 64
    assert first_payload["rows"][0]["authority_traceability_score"] == "0.946667"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in _walk_payload_values(first_payload)
    )

    rendered = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "private-event",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
    ):
        assert forbidden not in rendered

    tampered_payload = module.research_event_resolution_authority_traceability_report_payload(
        report(event_input()),
    )
    tampered_payload["rows"][0]["authority_traceability_score"] = "0.100000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_event_resolution_authority_traceability_report_payload(
            tampered_payload,
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.research_event_resolution_authority_traceability_report_payload(
            {
                "market_id": "hidden",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )

    numeric_payload = module.research_event_resolution_authority_traceability_report_payload(
        report(event_input()),
    )
    numeric_payload["numeric_probe"] = float("0.5")
    numeric_payload["derived_validation_digest"] = _payload_digest(
        {
            key: value
            for key, value in numeric_payload.items()
            if key != "derived_validation_digest"
        },
    )
    with pytest.raises(ValueError, match="primitive numerics"):
        module.research_event_resolution_authority_traceability_report_payload(
            numeric_payload,
        )


def test_validation_rejects_non_decimal_bad_flags_bad_times_and_duplicates() -> None:
    module = api()
    result = report(event_input())
    row = result.rows[0]

    for value in (config(), event_input(), row, result, *result.reason_code_counts):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item_value is None or item.name in {
                "config_version",
                "derived_validation_digest",
                "event_reference_key",
                "event_trace_hash",
                "paper_only",
                "readonly",
                "reason_codes",
                "reason_code_counts",
                "report_only",
                "rows",
                "status",
            }:
                continue
            if any(
                token in item.name
                for token in (
                    "age",
                    "count",
                    "coverage",
                    "pressure",
                    "risk",
                    "score",
                    "authority",
                    "clarity",
                )
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="rule_clarity"):
        event_input(rule_clarity=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_authority"):
        event_input(source_authority=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="manual_verification_completed_count"):
        event_input(
            manual_verification_required_count=d("1"),
            manual_verification_completed_count=d("2"),
        )
    with pytest.raises(ValueError, match="stale_rule_age_days"):
        event_input(stale_rule_age_days=-d("1"))
    with pytest.raises(ValueError, match="generated_at"):
        report(event_input(), generated_at=datetime(2026, 7, 8, 14, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            event_input(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 14, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="duplicate"):
        report(event_input("same"), event_input("same"))
    with pytest.raises(ValueError, match="min_pass_rule_clarity"):
        config(min_pass_rule_clarity=d("0.500000"))
    with pytest.raises(ValueError, match="paper_only"):
        event_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            authority_traceability_score=d("0.100000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            result,
            input_row_count=d("2.000000"),
            derived_validation_digest=result.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="report"):
        module.research_event_resolution_authority_traceability_report_payload(object())


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


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
