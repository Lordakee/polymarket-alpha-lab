from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_retrieval_tool_failover_quality_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_retrieval_tool_failover_quality_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


PRIMARY_TOOL = "primary_retriever"
FALLBACK_TOOL = "fallback_retriever"
ALTERNATE_FALLBACK_TOOL = "alternate_retriever"


def joined(*parts: str) -> str:
    return "".join(parts)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "fresh_observation_age_seconds": d("3600.000000"),
        "stale_observation_age_seconds": d("21600.000000"),
        "pass_failover_quality_score": d("0.800000"),
        "watch_failover_quality_score": d("0.500000"),
        "min_primary_tool_success_ratio": d("0.700000"),
        "min_fallback_success_ratio": d("0.600000"),
        "max_failover_dependency_ratio": d("0.500000"),
        "max_fallback_latency_seconds": d("5.000000"),
        "coverage_weight": d("0.300000"),
        "freshness_weight": d("0.200000"),
        "latency_weight": d("0.200000"),
        "dependency_weight": d("0.200000"),
        "fallback_success_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchSourceRetrievalToolFailoverQualityConfig(**values)


def observation(
    retrieval_scope: str,
    primary_tool: str,
    fallback_tool: str,
    *,
    observed_seconds_ago: int = 900,
    primary_attempt_count: Decimal = d("10.000000"),
    primary_success_count: Decimal = d("9.000000"),
    fallback_attempt_count: Decimal = d("2.000000"),
    fallback_success_count: Decimal = d("2.000000"),
    failover_trigger_count: Decimal = d("1.000000"),
    fallback_latency_seconds: Decimal = d("1.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceRetrievalToolFailoverQualityObservation(
        retrieval_scope=retrieval_scope,
        primary_tool=primary_tool,
        fallback_tool=fallback_tool,
        observed_at=GENERATED_AT - timedelta(seconds=observed_seconds_ago),
        primary_attempt_count=primary_attempt_count,
        primary_success_count=primary_success_count,
        fallback_attempt_count=fallback_attempt_count,
        fallback_success_count=fallback_success_count,
        failover_trigger_count=failover_trigger_count,
        fallback_latency_seconds=fallback_latency_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*observations: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_retrieval_tool_failover_quality_report(
        observations,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_failover_quality_scores_pass_watch_and_block_rows() -> None:
    module = api()
    report = build_report(
        observation("macro-calendar-pass", PRIMARY_TOOL, FALLBACK_TOOL),
        observation(
            "macro-calendar-watch",
            PRIMARY_TOOL,
            ALTERNATE_FALLBACK_TOOL,
            observed_seconds_ago=7200,
            primary_attempt_count=d("10.000000"),
            primary_success_count=d("6.000000"),
            fallback_attempt_count=d("5.000000"),
            fallback_success_count=d("3.000000"),
            failover_trigger_count=d("5.000000"),
            fallback_latency_seconds=d("4.000000"),
        ),
        observation(
            "macro-calendar-block",
            PRIMARY_TOOL,
            "fallback",
            observed_seconds_ago=28800,
            primary_attempt_count=d("10.000000"),
            primary_success_count=d("2.000000"),
            fallback_attempt_count=d("5.000000"),
            fallback_success_count=d("2.000000"),
            failover_trigger_count=d("8.000000"),
            fallback_latency_seconds=d("8.000000"),
        ),
    )

    assert type(report) is module.ResearchSourceRetrievalToolFailoverQualityReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.retrieval_scope_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_failover_quality_score == d("0.521111")
    assert report.lowest_failover_quality_score == d("0.140000")
    assert report.highest_failover_dependency_ratio == d("0.800000")
    assert report.highest_fallback_latency_seconds == d("8.000000")
    assert tuple(row.retrieval_scope for row in report.rows) == (
        "macro-calendar-block",
        "macro-calendar-watch",
        "macro-calendar-pass",
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert blocked.primary_success_ratio == d("0.200000")
    assert blocked.fallback_success_ratio == d("0.400000")
    assert blocked.failover_dependency_ratio == d("0.800000")
    assert blocked.freshness_score == d("0.000000")
    assert blocked.latency_score == d("0.000000")
    assert blocked.dependency_score == d("0.200000")
    assert blocked.failover_quality_score == d("0.140000")
    assert blocked.reason_codes == (
        "retrieval_tool_failover_quality_block",
        "fallback_latency_block",
        "fallback_success_block",
        "failover_dependency_block",
        "primary_tool_success_block",
        "retrieval_observation_stale_block",
    )

    watched = report.rows[1]
    assert watched.failover_quality_score == d("0.513333")
    assert watched.reason_codes == (
        "retrieval_tool_failover_quality_watch",
        "fallback_latency_watch",
        "failover_dependency_watch",
        "primary_tool_success_watch",
        "retrieval_observation_stale_watch",
    )

    passed = report.rows[2]
    assert passed.failover_quality_score == d("0.910000")
    assert passed.reason_codes == ("retrieval_tool_failover_quality_pass",)
    assert report.reason_codes == (
        "retrieval_tool_failover_quality_block",
        "fallback_latency_block",
        "fallback_success_block",
        "failover_dependency_block",
        "primary_tool_success_block",
        "retrieval_observation_stale_block",
        "retrieval_tool_failover_quality_watch",
        "fallback_latency_watch",
        "failover_dependency_watch",
        "primary_tool_success_watch",
        "retrieval_observation_stale_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_report_blocks_with_deterministic_digest() -> None:
    module = api()
    report = build_report()

    assert report.status == "block"
    assert report.retrieval_scope_count == d("0.000000")
    assert report.average_failover_quality_score == d("0.000000")
    assert report.lowest_failover_quality_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("retrieval_tool_failover_quality_no_inputs",)
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert report.derived_validation_digest == (
        module.research_source_retrieval_tool_failover_quality_report_digest(report)
    )


def test_score_only_watch_uses_single_status_reason_code() -> None:
    report = build_report(
        observation(
            "macro-calendar-score-watch",
            PRIMARY_TOOL,
            FALLBACK_TOOL,
            primary_attempt_count=d("10.000000"),
            primary_success_count=d("7.000000"),
            fallback_attempt_count=d("5.000000"),
            fallback_success_count=d("3.000000"),
            failover_trigger_count=d("4.000000"),
            fallback_latency_seconds=d("3.000000"),
        ),
    )

    row = report.rows[0]
    assert row.failover_quality_score == d("0.670000")
    assert row.status == "watch"
    assert row.reason_codes == ("retrieval_tool_failover_quality_watch",)
    assert report.reason_codes == ("retrieval_tool_failover_quality_watch",)


def test_public_payload_is_deterministic_decimal_only_safe_and_digest_checked() -> None:
    module = api()
    rows = (
        observation("macro-calendar-pass", PRIMARY_TOOL, FALLBACK_TOOL),
        observation(
            "macro-calendar-watch",
            PRIMARY_TOOL,
            ALTERNATE_FALLBACK_TOOL,
            observed_seconds_ago=7200,
            primary_attempt_count=d("10.000000"),
            primary_success_count=d("6.000000"),
            fallback_attempt_count=d("5.000000"),
            fallback_success_count=d("3.000000"),
            failover_trigger_count=d("5.000000"),
            fallback_latency_seconds=d("4.000000"),
        ),
    )
    report_a = build_report(*rows)
    report_b = build_report(*reversed(rows))
    payload_a = (
        module.research_source_retrieval_tool_failover_quality_report_payload(report_a)
    )
    payload_b = (
        module.research_source_retrieval_tool_failover_quality_report_payload(report_b)
    )

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert payload_a == payload_b
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert payload_a["derived_validation_digest"] == report_a.derived_validation_digest
    assert len(payload_a["derived_validation_digest"]) == 64
    json.dumps(payload_a, sort_keys=True, allow_nan=False)
    assert payload_a["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload_a["rows"][0]["failover_quality_score"] == "0.513333"
    assert_no_public_numbers_or_decimal_objects(payload_a)
    assert_no_unsafe_public_payload(payload_a)
    assert module.validate_research_source_retrieval_tool_failover_quality_report_digest(
        report_a,
    )
    assert module.validate_research_source_retrieval_tool_failover_quality_public_payload(
        payload_a,
    )

    tampered = dict(payload_a)
    tampered["watch_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_retrieval_tool_failover_quality_public_payload(
            tampered,
        )


def test_validation_rejects_bad_types_flags_sensitive_labels_and_tampering() -> None:
    module = api()
    with pytest.raises(ValueError, match="fresh_observation_age_seconds"):
        config(fresh_observation_age_seconds=3600)
    with pytest.raises(ValueError, match="coverage_weight"):
        config(coverage_weight=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="primary_attempt_count"):
        observation(
            "macro-calendar",
            PRIMARY_TOOL,
            FALLBACK_TOOL,
            primary_attempt_count=10,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="primary_success_count"):
        observation(
            "macro-calendar",
            PRIMARY_TOOL,
            FALLBACK_TOOL,
            primary_success_count=d("11.000000"),
        )
    with pytest.raises(ValueError, match="retrieval_scope"):
        observation(
            joined("market", "_", "sl", "ug-alpha"),
            PRIMARY_TOOL,
            FALLBACK_TOOL,
        )
    with pytest.raises(ValueError, match="primary_tool"):
        observation("macro-calendar", joined("ht", "tps://source.invalid"), FALLBACK_TOOL)
    with pytest.raises(ValueError, match="fallback_tool"):
        observation("macro-calendar", PRIMARY_TOOL, joined("wal", "let-to", "ken"))
    for sensitive_tool in (
        joined("sc", "rapling"),
        joined("agent", "_", "reach"),
        joined("agent", "-", "reach"),
        joined("brow", "ser_capture"),
        joined("net", "work_probe"),
        joined("data", "base_reader"),
        joined("d", "b_reader"),
    ):
        with pytest.raises(ValueError, match="primary_tool"):
            observation("macro-calendar", sensitive_tool, FALLBACK_TOOL)
        with pytest.raises(ValueError, match="fallback_tool"):
            observation("macro-calendar", PRIMARY_TOOL, sensitive_tool)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation("macro-calendar", PRIMARY_TOOL, FALLBACK_TOOL, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        observation("macro-calendar", PRIMARY_TOOL, FALLBACK_TOOL, readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_source_retrieval_tool_failover_quality_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )

    report = build_report(observation("macro-calendar", PRIMARY_TOOL, FALLBACK_TOOL))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="failover_quality_score"):
        replace(report.rows[0], failover_quality_score=d("0.100000"))


def test_exports_frozen_dataclasses_and_has_no_runtime_side_effect_surface() -> None:
    module = api()
    report = build_report(observation("macro-calendar", PRIMARY_TOOL, FALLBACK_TOOL))

    assert module.STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_RETRIEVAL_TOOL_FAILOVER_QUALITY_CONFIG_VERSION",
        "STATUSES",
        "ResearchSourceRetrievalToolFailoverQualityConfig",
        "ResearchSourceRetrievalToolFailoverQualityObservation",
        "ResearchSourceRetrievalToolFailoverQualityReasonCodeCount",
        "ResearchSourceRetrievalToolFailoverQualityReport",
        "ResearchSourceRetrievalToolFailoverQualityRow",
        "build_research_source_retrieval_tool_failover_quality_report",
        "research_source_retrieval_tool_failover_quality_report_digest",
        "research_source_retrieval_tool_failover_quality_report_payload",
        "validate_research_source_retrieval_tool_failover_quality_public_payload",
        "validate_research_source_retrieval_tool_failover_quality_report_digest",
    )
    assert is_dataclass(config())
    assert is_dataclass(
        observation("macro-calendar", PRIMARY_TOOL, FALLBACK_TOOL),
    )
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"

    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        joined("sc", "rapling"),
        joined("agent", "_", "reach"),
        joined("agent", "-", "reach"),
        joined("brow", "ser"),
        joined("net", "work"),
        joined("re", "quests"),
        joined("ur", "llib"),
        joined("htt", "px"),
        joined("aio", "http"),
        joined("so", "cket"),
        joined("sub", "process"),
        joined("psy", "copg"),
        joined("s", "ql"),
        "connect(",
        joined("wal", "let"),
        joined("to", "ken"),
        joined("or", "der"),
        joined("tr", "ade"),
        joined("si", "zing"),
        joined("reco", "mmendation"),
    )
    assert all(term not in source for term in forbidden_terms)
    public_fields = {field.name for field in fields(report.rows[0])}
    sensitive_field_names = {
        joined("candi", "date_id"),
        joined("market", "_id"),
        joined("market", "_", "sl", "ug"),
        joined("sl", "ug"),
        joined("ques", "tion"),
        joined("source", "_", "u", "rl"),
        joined("source", "_text"),
        joined("raw_", "candi", "date_id"),
        joined("raw_", "market", "_id"),
    }
    assert not sensitive_field_names & public_fields


def assert_no_public_numbers_or_decimal_objects(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numbers_or_decimal_objects(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_public_numbers_or_decimal_objects(item)
        return
    assert not isinstance(value, Decimal)
    assert type(value) not in {float, int}


def assert_no_unsafe_public_payload(payload: object) -> None:
    encoded = json.dumps(payload, sort_keys=True).lower()
    unsafe_fragments = (
        joined("candi", "date_id"),
        joined("candi", "date-id"),
        joined("market", "_id"),
        joined("market", "-id"),
        joined("market", "_", "sl", "ug"),
        joined("market", "-", "sl", "ug"),
        joined("sl", "ug"),
        joined("ques", "tion"),
        joined("source", "_", "u", "rl"),
        joined("source", "-", "u", "rl"),
        joined("raw_", "u", "rl"),
        joined("u", "rl"),
        joined("source", "_text"),
        joined("raw_text"),
        joined("d", "sn"),
        joined("ta", "ble"),
        joined("to", "ken"),
        joined("wal", "let"),
        joined("or", "der"),
        joined("tr", "ade"),
        joined("li", "ve"),
        joined("si", "zing"),
        joined("reco", "mmendation"),
        joined("ht", "tp://"),
        joined("ht", "tps://"),
        "www.",
    )
    assert all(fragment not in encoded for fragment in unsafe_fragments)
