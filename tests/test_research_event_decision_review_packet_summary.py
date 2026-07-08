from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_event_decision_review_packet_summary import (
    DEFAULT_RESEARCH_EVENT_DECISION_REVIEW_PACKET_SUMMARY_CONFIG_VERSION,
    ResearchEventDecisionReviewPacketSummaryConfig,
    ResearchEventDecisionReviewPacketSummaryInput,
    ResearchEventDecisionReviewPacketSummaryReport,
    build_research_event_decision_review_packet_summary,
    research_event_decision_review_packet_summary_digest,
    research_event_decision_review_packet_summary_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_event_decision_review_packet_summary.py",
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEventDecisionReviewPacketSummaryConfig:
    values: dict[str, object] = {
        "config_version": (
            DEFAULT_RESEARCH_EVENT_DECISION_REVIEW_PACKET_SUMMARY_CONFIG_VERSION
        ),
        "pass_score_threshold": d("0.750000"),
        "watch_score_threshold": d("0.500000"),
        "component_floor": d("0.700000"),
        "block_component_floor": d("0.400000"),
    }
    values.update(overrides)
    return ResearchEventDecisionReviewPacketSummaryConfig(**values)


def packet(
    **overrides: object,
) -> ResearchEventDecisionReviewPacketSummaryInput:
    values: dict[str, object] = {
        "review_topic_key": "event-review-public-rates",
        "decision_material_label": "rates-review-memo",
        "prepared_at": GENERATED_AT - timedelta(hours=1),
        "research_quality_score": d("0.800000"),
        "evidence_balance_score": d("0.820000"),
        "counterpoint_coverage_score": d("0.780000"),
        "resolution_rule_clarity_score": d("0.760000"),
        "human_review_readiness_score": d("0.810000"),
        "unresolved_blocker_count": d("0"),
        "caution_item_count": d("0"),
    }
    values.update(overrides)
    return ResearchEventDecisionReviewPacketSummaryInput(**values)


def summary(
    subject: object | None = None,
    *,
    cfg: ResearchEventDecisionReviewPacketSummaryConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventDecisionReviewPacketSummaryReport:
    return build_research_event_decision_review_packet_summary(
        packet() if subject is None else subject,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_no_concrete_numeric_payload_values(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected concrete numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_concrete_numeric_payload_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_concrete_numeric_payload_values(item)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(("_score", "_count", "_threshold", "_floor")):
            assert type(item) is Decimal


def test_pass_summary_is_public_report_only_and_digest_stable() -> None:
    report = summary(
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        DEFAULT_RESEARCH_EVENT_DECISION_REVIEW_PACKET_SUMMARY_CONFIG_VERSION
    )
    assert report.review_topic_key == "event-review-public-rates"
    assert report.public_status == "pass"
    assert report.review_score == d("0.794000")
    assert report.next_review_step == "pass_human_review_packet_summary"
    assert report.reason_codes == (
        "research_event_decision_review_packet_summary_pass",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert type(report.review_score) is Decimal
    assert_decimal_numeric_fields(report)
    with pytest.raises(FrozenInstanceError):
        report.public_status = "watch"  # type: ignore[misc]

    payload = research_event_decision_review_packet_summary_payload(report)
    json.dumps(payload, sort_keys=True)
    assert payload == report.payload
    assert payload["review_score"] == "0.794000"
    assert payload["public_status"] == "pass"
    assert payload["summary_digest"] == report.summary_digest
    assert_no_concrete_numeric_payload_values(payload)


def test_watch_summary_captures_low_component_and_caution_items() -> None:
    report = summary(
        packet(
            evidence_balance_score=d("0.650000"),
            caution_item_count=d("2"),
        ),
    )

    assert report.public_status == "watch"
    assert report.review_score == d("0.760000")
    assert report.next_review_step == "watch_human_review_packet_summary"
    assert report.reason_codes == (
        "research_event_decision_review_packet_summary_evidence_balance_watch",
        "research_event_decision_review_packet_summary_caution_items_present",
        "research_event_decision_review_packet_summary_watch",
    )


def test_block_summary_captures_hard_blockers_and_low_scores() -> None:
    report = summary(
        packet(
            counterpoint_coverage_score=d("0.300000"),
            resolution_rule_clarity_score=d("0.390000"),
            unresolved_blocker_count=d("1"),
            caution_item_count=d("1"),
        ),
    )

    assert report.public_status == "block"
    assert report.review_score == d("0.576000")
    assert report.next_review_step == "block_human_review_packet_summary"
    assert report.reason_codes == (
        "research_event_decision_review_packet_summary_unresolved_blockers",
        "research_event_decision_review_packet_summary_counterpoint_coverage_block",
        "research_event_decision_review_packet_summary_resolution_rule_clarity_block",
        "research_event_decision_review_packet_summary_caution_items_present",
        "research_event_decision_review_packet_summary_block",
    )


def test_type_rejection_decimal_exactness_ranges_and_flags() -> None:
    with pytest.raises(ValueError, match="value must be a ResearchEventDecision"):
        summary(object())
    with pytest.raises(ValueError, match="config must be a ResearchEventDecision"):
        summary(cfg=object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        summary(generated_at=_DateTimeSubclass(2026, 7, 4, tzinfo=UTC))
    with pytest.raises(ValueError, match="review_topic_key must be exactly str"):
        packet(review_topic_key=_StringSubclass("event-review-public-rates"))
    with pytest.raises(ValueError, match="research_quality_score must be a Decimal"):
        packet(research_quality_score=1)
    with pytest.raises(ValueError, match="evidence_balance_score must be a Decimal"):
        packet(evidence_balance_score=1.0)
    with pytest.raises(ValueError, match="counterpoint_coverage_score must be a Decimal"):
        packet(counterpoint_coverage_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="human_review_readiness_score must be between"):
        packet(human_review_readiness_score=d("1.000001"))
    with pytest.raises(ValueError, match="unresolved_blocker_count must be a whole"):
        packet(unresolved_blocker_count=d("1.500000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        packet(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        summary(packet(readonly=False))


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("review_topic_key", "candidate-raw-alpha"),
        ("review_topic_key", "market_slug_hidden"),
        ("review_topic_key", "condition-question-hidden"),
        ("decision_material_label", "https://example.test/path"),
        ("decision_material_label", "source_ref_private"),
        ("decision_material_label", "raw_text_excerpt"),
        ("decision_material_label", "postgres_dsn_secret"),
        ("decision_material_label", "warehouse_table_name"),
        ("decision_material_label", "api_token_here"),
        ("decision_material_label", "wallet_payload"),
        ("decision_material_label", "order_ticket"),
        ("decision_material_label", "trade_instruction"),
        ("decision_material_label", "position_size_hint"),
        ("decision_material_label", "buy-the-event"),
        ("decision_material_label", "sell-the-event"),
        ("decision_material_label", "recommended-action"),
    ),
)
def test_public_input_rejects_sensitive_or_actionable_text(
    field_name: str,
    value: str,
) -> None:
    with pytest.raises(ValueError, match="restricted public text"):
        packet(**{field_name: value})


def test_public_payload_rejects_manual_leaks_tampering_and_bad_status() -> None:
    report = summary()

    with pytest.raises(ValueError, match="public_status must be one of"):
        replace(report, public_status="blocked")
    with pytest.raises(ValueError, match="summary_digest must match"):
        replace(report, summary_digest="0" * 64)
    with pytest.raises(ValueError, match="restricted public text"):
        replace(report, decision_material_label="source_ref_private")
    with pytest.raises(ValueError, match="review_score must match"):
        replace(report, review_score=d("0.900000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            report,
            reason_codes=(
                "research_event_decision_review_packet_summary_watch",
            ),
        )


def test_deterministic_payload_and_digest_match_across_rebuilds() -> None:
    first = summary(
        packet(
            review_topic_key="event-review-public-jobs",
            decision_material_label="jobs-review-memo",
            research_quality_score=d("0.710000"),
            evidence_balance_score=d("0.720000"),
            counterpoint_coverage_score=d("0.740000"),
            resolution_rule_clarity_score=d("0.730000"),
            human_review_readiness_score=d("0.750000"),
        ),
    )
    second = summary(
        packet(
            decision_material_label="jobs-review-memo",
            review_topic_key="event-review-public-jobs",
            human_review_readiness_score=d("0.750000"),
            resolution_rule_clarity_score=d("0.730000"),
            counterpoint_coverage_score=d("0.740000"),
            evidence_balance_score=d("0.720000"),
            research_quality_score=d("0.710000"),
        ),
    )

    assert first == second
    assert first.payload == second.payload
    assert first.summary_digest == second.summary_digest
    assert research_event_decision_review_packet_summary_digest(first) == (
        first.summary_digest
    )

    payload_without_digest = dict(first.payload)
    digest = payload_without_digest.pop("summary_digest")
    assert digest == first.summary_digest
    assert digest not in json.dumps(payload_without_digest, sort_keys=True)


def test_report_digest_and_payload_consistency_rejects_public_leaks() -> None:
    report = summary()
    payload = research_event_decision_review_packet_summary_payload(report)

    assert payload == report.payload
    assert payload["summary_digest"] == (
        research_event_decision_review_packet_summary_digest(report)
    )
    for value in walk_values(payload):
        if isinstance(value, str):
            lowered = value.lower()
            assert "candidate" not in lowered
            assert "market_" not in lowered
            assert "slug" not in lowered
            assert "question" not in lowered
            assert "source_ref" not in lowered
            assert "raw_text" not in lowered
            assert "dsn" not in lowered
            assert "table" not in lowered
            assert "token" not in lowered
            assert "wallet" not in lowered
            assert "order" not in lowered
            assert "trade" not in lowered
            assert "position" not in lowered
            assert "buy" not in lowered
            assert "sell" not in lowered
            assert "recommend" not in lowered


def test_module_has_no_io_runtime_surface_or_float_literals() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    forbidden_import_roots = {
        "boto3",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "commit",
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "urlopen",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
        if isinstance(node, ast.Constant) and type(node.value) is float:
            raise AssertionError(f"float literal found: {node.value!r}")
