from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_market_resolution_evidence_queue_report as api
from polymarket_alpha_lab.research_market_resolution_evidence_queue_report import (
    DEFAULT_RESEARCH_MARKET_RESOLUTION_EVIDENCE_QUEUE_REPORT_CONFIG_VERSION,
    ResearchMarketResolutionEvidenceQueueConfig,
    ResearchMarketResolutionEvidenceQueueInput,
    ResearchMarketResolutionEvidenceQueuePublicPayloadItem,
    ResearchMarketResolutionEvidenceQueueReport,
    ResearchMarketResolutionEvidenceQueueRow,
    build_research_market_resolution_evidence_queue_report,
    research_market_resolution_evidence_queue_report_payload,
)


NOW = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _item(
    *,
    review_key: str = "review_pass",
    parsed_rule_count: Decimal = d("2.000000"),
    result_evidence_count: Decimal = d("2.000000"),
    conflict_evidence_count: Decimal = d("0.000000"),
    rule_confidence_score: Decimal = d("0.900000"),
    result_evidence_score: Decimal = d("0.800000"),
    conflict_severity_score: Decimal = d("0.000000"),
    hard_block_flag: bool = False,
    hard_watch_flag: bool = False,
    report_only: bool = True,
) -> ResearchMarketResolutionEvidenceQueueInput:
    return ResearchMarketResolutionEvidenceQueueInput(
        review_key=review_key,
        parsed_rule_count=parsed_rule_count,
        result_evidence_count=result_evidence_count,
        conflict_evidence_count=conflict_evidence_count,
        rule_confidence_score=rule_confidence_score,
        result_evidence_score=result_evidence_score,
        conflict_severity_score=conflict_severity_score,
        hard_block_flag=hard_block_flag,
        hard_watch_flag=hard_watch_flag,
        report_only=report_only,
    )


def _report(
    rows: tuple[ResearchMarketResolutionEvidenceQueueInput, ...],
    *,
    config: ResearchMarketResolutionEvidenceQueueConfig | None = None,
    public_payload: tuple[ResearchMarketResolutionEvidenceQueuePublicPayloadItem, ...] = (),
) -> ResearchMarketResolutionEvidenceQueueReport:
    return build_research_market_resolution_evidence_queue_report(
        rows,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_report_orders_block_watch_pass_for_human_review_queue() -> None:
    report = _report(
        (
            _item(review_key="review_pass"),
            _item(
                review_key="review_watch",
                parsed_rule_count=d("1.000000"),
                result_evidence_count=d("1.000000"),
                rule_confidence_score=d("0.600000"),
                result_evidence_score=d("0.600000"),
            ),
            _item(
                review_key="review_block",
                conflict_evidence_count=d("1.000000"),
                conflict_severity_score=d("0.850000"),
            ),
        ),
    )

    assert report.public_status == "block"
    assert report.item_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert tuple(row.review_key for row in report.rows) == (
        "review_block",
        "review_watch",
        "review_pass",
    )
    assert tuple(row.queue_rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )

    block, watch, passed = report.rows
    assert block.public_status == "block"
    assert block.resolution_evidence_score == d("0.000000")
    assert block.review_priority_score == d("1.000000")
    assert block.reason_codes == (
        "parsed_rules_present",
        "result_evidence_present",
        "conflict_evidence_present",
        "resolution_evidence_score_block",
        "human_review_required",
    )
    assert watch.public_status == "watch"
    assert watch.resolution_evidence_score == d("0.600000")
    assert "resolution_evidence_score_watch" in watch.reason_codes
    assert passed.public_status == "pass"
    assert passed.review_priority_score == d("0.150000")
    assert passed.reason_codes == (
        "parsed_rules_present",
        "result_evidence_present",
        "no_conflict_evidence",
        "resolution_evidence_score_pass",
        "human_review_not_required",
    )


def test_payload_serializes_decimals_and_matches_digest_report_helper() -> None:
    report = _report(
        (
            _item(review_key="review_pass"),
            _item(
                review_key="review_watch",
                parsed_rule_count=d("1.000000"),
                result_evidence_count=d("1.000000"),
                rule_confidence_score=d("0.600000"),
                result_evidence_score=d("0.600000"),
            ),
        ),
        public_payload=(
            ResearchMarketResolutionEvidenceQueuePublicPayloadItem(
                key="safe_summary",
                value="human review queue only",
            ),
        ),
    )

    payload = report.payload
    function_payload = research_market_resolution_evidence_queue_report_payload(report)
    json.dumps(payload, sort_keys=True)
    assert function_payload == payload
    assert payload["config_version"] == (
        DEFAULT_RESEARCH_MARKET_RESOLUTION_EVIDENCE_QUEUE_REPORT_CONFIG_VERSION
    )
    assert payload["item_count"] == "2.000000"
    assert payload["rows"][0]["queue_rank"] == "1.000000"
    assert payload["rows"][0]["resolution_evidence_score"] == "0.600000"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)


def test_decimal_type_rejection_and_status_validation() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        _item(parsed_rule_count=2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Decimal"):
        _item(rule_confidence_score=0.9)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="timezone-aware"):
        build_research_market_resolution_evidence_queue_report(
            (_item(),),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )

    report = _report((_item(),))
    with pytest.raises(ValueError, match="known public status"):
        replace(report.rows[0], public_status="clear")


def test_public_leak_rejection_blocks_sensitive_identifiers_and_language() -> None:
    forbidden_values = (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    )
    for value in forbidden_values:
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchMarketResolutionEvidenceQueuePublicPayloadItem(value, "safe value")
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchMarketResolutionEvidenceQueuePublicPayloadItem("safe_key", value)
        with pytest.raises(ValueError, match="unsafe public"):
            _item(review_key=value)

    report = _report((_item(review_key="review_safe"),))
    public_json = json.dumps(report.payload, sort_keys=True).lower()
    assert "raw_candidate_id" not in public_json
    assert "market_id" not in public_json
    assert "market_slug" not in public_json
    assert "market_question" not in public_json
    assert "source_ref" not in public_json
    assert "source_url" not in public_json
    assert "source_text" not in public_json
    assert "wallet" not in public_json
    assert "order" not in public_json
    assert "trade" not in public_json
    assert "buy" not in public_json
    assert "sell" not in public_json
    assert "recommendation" not in public_json


def test_hard_flags_are_enforced_on_all_public_dataclasses() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchMarketResolutionEvidenceQueueConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _item(review_key="review_safe", hard_watch_flag=True, report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        ResearchMarketResolutionEvidenceQueuePublicPayloadItem(
            "safe_key",
            "safe value",
            readonly=False,
        )

    report = _report((_item(),))
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(FrozenInstanceError):
        report.public_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchMarketResolutionEvidenceQueueConfig):
            pass


def test_hard_watch_and_hard_block_flags_drive_queue_status() -> None:
    report = _report(
        (
            _item(review_key="review_manual_watch", hard_watch_flag=True),
            _item(review_key="review_manual_block", hard_block_flag=True),
        ),
    )

    assert tuple(row.public_status for row in report.rows) == ("block", "watch")
    assert report.rows[0].reason_codes == (
        "parsed_rules_present",
        "result_evidence_present",
        "no_conflict_evidence",
        "hard_block_flag",
        "resolution_evidence_score_pass",
        "human_review_required",
    )
    assert report.rows[1].reason_codes == (
        "parsed_rules_present",
        "result_evidence_present",
        "no_conflict_evidence",
        "hard_watch_flag",
        "resolution_evidence_score_pass",
        "human_review_required",
    )


def test_deterministic_payload_is_independent_of_input_order() -> None:
    rows = (
        _item(review_key="review_pass"),
        _item(
            review_key="review_watch",
            parsed_rule_count=d("1.000000"),
            result_evidence_count=d("1.000000"),
            rule_confidence_score=d("0.600000"),
            result_evidence_score=d("0.600000"),
        ),
        _item(
            review_key="review_block",
            conflict_evidence_count=d("1.000000"),
            conflict_severity_score=d("0.850000"),
        ),
    )
    first = _report(rows)
    second = _report(tuple(reversed(rows)))

    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest


def test_report_rejects_digest_and_summary_tampering() -> None:
    report = _report((_item(),))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="item_count"):
        replace(report, item_count=d("2.000000"))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchMarketResolutionEvidenceQueuePublicPayloadItem(
                    "safe_key",
                    "changed safe value",
                ),
            ),
        )


def test_no_network_storage_or_trading_surfaces_are_exposed() -> None:
    assert api.__all__ == (
        "DEFAULT_RESEARCH_MARKET_RESOLUTION_EVIDENCE_QUEUE_REPORT_CONFIG_VERSION",
        "ResearchMarketResolutionEvidenceQueueConfig",
        "ResearchMarketResolutionEvidenceQueueInput",
        "ResearchMarketResolutionEvidenceQueuePublicPayloadItem",
        "ResearchMarketResolutionEvidenceQueueReport",
        "ResearchMarketResolutionEvidenceQueueRow",
        "build_research_market_resolution_evidence_queue_report",
        "research_market_resolution_evidence_queue_report_payload",
    )

    forbidden_public_fragments = (
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_public_fragments)

    for cls in (
        ResearchMarketResolutionEvidenceQueueConfig,
        ResearchMarketResolutionEvidenceQueueInput,
        ResearchMarketResolutionEvidenceQueuePublicPayloadItem,
        ResearchMarketResolutionEvidenceQueueReport,
        ResearchMarketResolutionEvidenceQueueRow,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_public_fragments)

    source = Path(api.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "ccxt",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "urllib",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "commit",
        "delete",
        "execute",
        "open",
        "post",
        "put",
        "request",
        "send",
        "submit",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                assert target.id not in forbidden_call_names
            if isinstance(target, ast.Attribute):
                assert target.attr not in forbidden_call_names


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
