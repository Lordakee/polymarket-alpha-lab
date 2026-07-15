from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 30, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_assignment_routing_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object):
    return api().ResearchTeamSpecialistAssignmentRoutingConfig(**overrides)


def topic(
    raw_topic_key: str,
    domain_label: str,
    *,
    source_gap_score: Decimal = d("0.100000"),
    memory_quality_score: Decimal = d("0.900000"),
    workload_pressure_score: Decimal = d("0.200000"),
    calibration_backlog_score: Decimal = d("0.100000"),
    observed_at: datetime = OBSERVED_AT,
):
    return api().ResearchTeamSpecialistAssignmentRoutingInput(
        raw_topic_key=raw_topic_key,
        domain_label=domain_label,
        source_gap_score=source_gap_score,
        memory_quality_score=memory_quality_score,
        workload_pressure_score=workload_pressure_score,
        calibration_backlog_score=calibration_backlog_score,
        observed_at=observed_at,
    )


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    return api().build_research_team_specialist_assignment_routing_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_assignment_routing_scores_topics_and_validates_digest() -> None:
    rows = (
        topic("candidate-topic-alpha-raw-id", "sports.soccer"),
        topic(
            "candidate-topic-beta-raw-id",
            "crypto",
            source_gap_score=d("0.650000"),
            memory_quality_score=d("0.500000"),
            workload_pressure_score=d("0.600000"),
            calibration_backlog_score=d("0.500000"),
        ),
        topic(
            "candidate-topic-gamma-raw-id",
            "macro.rates",
            source_gap_score=d("0.950000"),
            memory_quality_score=d("0.200000"),
            workload_pressure_score=d("0.900000"),
            calibration_backlog_score=d("0.800000"),
        ),
    )

    report = build_report(*rows)
    reversed_report = build_report(*reversed(rows))

    assert api().ASSIGNMENT_ROUTING_STATUSES == ("pass", "watch", "block")
    assert report.status == "block"
    assert report.paper_queue_action == "paper_specialist_assignment_block"
    assert report.topic_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.routed_topic_count == d("3.000000")
    assert report.manual_review_topic_count == d("2.000000")
    assert report.manual_review_topic_ratio == d("0.666667")
    assert report.max_routing_pressure_score == d("0.862500")
    assert report.avg_routing_pressure_score == d("0.512500")
    assert report.max_source_gap_score == d("0.950000")
    assert report.min_memory_quality_score == d("0.200000")
    assert report.max_workload_pressure_score == d("0.900000")
    assert report.max_calibration_backlog_score == d("0.800000")

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.assignment_rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert blocked.specialist_team_label == "team_macro"
    assert blocked.routing_pressure_score == d("0.862500")
    assert blocked.memory_gap_score == d("0.800000")
    assert blocked.reason_codes == (
        "assignment_routing_source_gap_block",
        "assignment_routing_memory_quality_block",
        "assignment_routing_workload_pressure_block",
        "assignment_routing_calibration_backlog_block",
    )
    assert watched.specialist_team_label == "team_crypto"
    assert watched.reason_codes == (
        "assignment_routing_source_gap_watch",
        "assignment_routing_memory_quality_watch",
        "assignment_routing_workload_pressure_watch",
        "assignment_routing_calibration_backlog_watch",
    )
    assert passed.specialist_team_label == "team_soccer"
    assert passed.reason_codes == ("assignment_routing_clear",)

    payload = api().research_team_specialist_assignment_routing_report_payload(report)
    reversed_payload = api().research_team_specialist_assignment_routing_report_payload(
        reversed_report,
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["manual_review_topic_count"] == "2.000000"
    assert payload["manual_review_topic_ratio"] == "0.666667"
    assert payload["rows"][0]["routing_pressure_score"] == "0.862500"
    assert api().research_team_specialist_assignment_routing_report_digest(report) == (
        payload["derived_validation_digest"]
    )
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_assignment_routing_is_report_only_public_safe_and_decimal_strict() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_SPECIALIST_ASSIGNMENT_ROUTING_CONFIG_VERSION",
        "ASSIGNMENT_ROUTING_STATUSES",
        "ResearchTeamSpecialistAssignmentRoutingConfig",
        "ResearchTeamSpecialistAssignmentRoutingInput",
        "ResearchTeamSpecialistAssignmentRoutingReasonCodeCount",
        "ResearchTeamSpecialistAssignmentRoutingReport",
        "ResearchTeamSpecialistAssignmentRoutingRow",
        "build_research_team_specialist_assignment_routing_report",
        "research_team_specialist_assignment_routing_report_digest",
        "research_team_specialist_assignment_routing_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    empty = build_report()
    assert empty.status == "pass"
    assert empty.paper_queue_action == "paper_specialist_assignment_monitor"
    assert empty.reason_codes == ("assignment_routing_no_topics",)
    assert empty.topic_count == d("0.000000")
    assert empty.manual_review_topic_count == d("0.000000")
    assert empty.manual_review_topic_ratio == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_code_counts == ()

    populated = build_report(topic("raw-topic-safe-id", "politics"))
    for value in (
        config(),
        topic("raw-topic-other-id", "energy"),
        populated,
        *populated.rows,
        *populated.reason_code_counts,
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(("_count", "_ratio", "_score", "_rank")):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="source_gap_score must be a Decimal"):
        topic("raw-topic", "politics", source_gap_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        topic("raw-topic", "politics", observed_at=datetime(2026, 7, 8, 10, 0))
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            topic("raw-topic", "politics"),
            generated_at=datetime(
                2026,
                7,
                8,
                12,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="raw_topic_key values must be unique"):
        build_report(topic("raw-topic", "politics"), topic("raw-topic", "crypto"))
    with pytest.raises(ValueError, match="domain_label"):
        topic("raw-topic", "market_slug")
    with pytest.raises(ValueError, match="max_watch_source_gap_score"):
        config(
            max_pass_source_gap_score=d("0.600000"),
            max_watch_source_gap_score=d("0.500000"),
        )

    payload = module.research_team_specialist_assignment_routing_report_payload(
        populated,
    )
    public = repr(payload).lower()
    forbidden = (
        "raw-topic-safe-id",
        "raw-topic-other-id",
        "candidate",
        "market",
        "slug",
        "question",
        "https://",
        "source_url",
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
        "live",
    )
    for token_value in forbidden:
        assert token_value not in public


def test_assignment_routing_rejects_payload_leaks_and_digest_tampering() -> None:
    module = api()
    report = build_report(
        topic(
            "raw-sensitive-candidate-id",
            "weather",
            source_gap_score=d("0.700000"),
            memory_quality_score=d("0.400000"),
        ),
    )
    payload = module.research_team_specialist_assignment_routing_report_payload(report)
    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_assignment_routing_report_payload(tampered)

    for unsafe_key, unsafe_value in (
        ("candidate_id", "opaque"),
        ("market_slug", "will-fed-cut-rates"),
        ("question", "Will this resolve yes?"),
        ("source_url", "https://example.test/item"),
        ("dsn", "postgres://example"),
        ("wallet", "0xabc"),
        ("order_ticket", "abc"),
        ("sizing", "100"),
        ("recommendation", "buy"),
    ):
        leaked = dict(payload)
        leaked[unsafe_key] = unsafe_value
        leaked["derived_validation_digest"] = canonical_digest(leaked)
        with pytest.raises(ValueError, match="unsafe"):
            module.research_team_specialist_assignment_routing_report_payload(leaked)


def test_assignment_routing_rejects_mapping_payload_schema_extensions() -> None:
    module = api()
    payload = module.research_team_specialist_assignment_routing_report_payload(
        build_report(topic("raw-topic-safe-id", "politics")),
    )

    int_numeric = dict(payload)
    int_numeric["topic_count"] = 1
    int_numeric["derived_validation_digest"] = canonical_digest(int_numeric)
    with pytest.raises(ValueError, match="Decimal"):
        module.research_team_specialist_assignment_routing_report_payload(int_numeric)

    unsafe_variant_key = dict(payload)
    unsafe_variant_key["candidateId"] = "opaque"
    unsafe_variant_key["derived_validation_digest"] = canonical_digest(unsafe_variant_key)
    with pytest.raises(ValueError, match="unsafe"):
        module.research_team_specialist_assignment_routing_report_payload(
            unsafe_variant_key,
        )

    raw_topic_ref = dict(payload)
    raw_topic_ref["rows"] = [dict(payload["rows"][0], topic_ref="raw-topic-safe-id")]
    raw_topic_ref["derived_validation_digest"] = canonical_digest(raw_topic_ref)
    with pytest.raises(ValueError, match="topic_ref"):
        module.research_team_specialist_assignment_routing_report_payload(raw_topic_ref)

    unexpected_extra = dict(payload)
    unexpected_extra["review_note"] = "internal note"
    unexpected_extra["derived_validation_digest"] = canonical_digest(unexpected_extra)
    with pytest.raises(ValueError, match="unexpected public payload field"):
        module.research_team_specialist_assignment_routing_report_payload(
            unexpected_extra,
        )


def _float_paths(value: object, path: str = "") -> tuple[str, ...]:
    if type(value) is float:
        return (path or "<root>",)
    if isinstance(value, dict):
        found: list[str] = []
        for key, item in value.items():
            found.extend(_float_paths(item, f"{path}.{key}" if path else str(key)))
        return tuple(found)
    if isinstance(value, list):
        found = []
        for index, item in enumerate(value):
            found.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(found)
    return ()
