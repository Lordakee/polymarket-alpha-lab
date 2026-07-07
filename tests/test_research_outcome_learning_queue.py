from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_outcome_learning_queue import (
    ResearchOutcomeLearningQueueConfig,
    ResearchOutcomeLearningRecord,
    ResearchOutcomeLearningQueueReport,
    build_research_outcome_learning_queue,
    research_outcome_learning_queue_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
PUBLIC_STATES = {"pass", "watch", "block"}
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "raw-candidate",
    "raw-market",
    "market-slug",
    "will this resolve",
    "source-ref",
    "https://",
    "postgres://",
    "wallet",
    "auth",
    "token",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def record(
    suffix: str,
    predicted_probability: str,
    resolved_probability: str,
    *,
    settlement_state: str = "settled",
    evidence_quality_score: str = "0.950000",
    review_completeness_score: str = "0.950000",
) -> ResearchOutcomeLearningRecord:
    return ResearchOutcomeLearningRecord(
        private_case_ref=f"raw-candidate-{suffix}",
        private_event_ref=(
            f"raw-market-{suffix}|market-slug-{suffix}|"
            f"Will this resolve {suffix}?|source-ref=https://example.invalid/{suffix}"
        ),
        settlement_state=settlement_state,
        predicted_probability=d(predicted_probability),
        resolved_probability=d(resolved_probability),
        evidence_quality_score=d(evidence_quality_score),
        review_completeness_score=d(review_completeness_score),
    )


def report(*records: ResearchOutcomeLearningRecord) -> ResearchOutcomeLearningQueueReport:
    return build_research_outcome_learning_queue(
        records,
        generated_at=GENERATED_AT,
    )


def test_learning_queue_prioritizes_pass_watch_block_without_leaking_raw_refs() -> None:
    result = report(
        record("pass", "0.550000", "0.500000"),
        record(
            "watch",
            "0.750000",
            "0.500000",
            evidence_quality_score="0.650000",
            review_completeness_score="0.750000",
        ),
        record(
            "block",
            "1.000000",
            "0.000000",
            settlement_state="pending",
            evidence_quality_score="0.300000",
            review_completeness_score="0.400000",
        ),
    )

    assert result.queue_status == "block"
    assert result.case_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert tuple(row.learning_status for row in result.rows) == (
        "block",
        "watch",
        "pass",
    )

    block_row, watch_row, pass_row = result.rows
    assert block_row.rank == d("1.000000")
    assert block_row.settlement_gate == "block"
    assert block_row.prediction_gate == "block"
    assert block_row.evidence_quality_gate == "block"
    assert block_row.review_completeness_gate == "block"
    assert block_row.priority_score == d("0.860000")
    assert block_row.reason_codes == (
        "settlement_not_final_block",
        "prediction_deviation_high_block",
        "evidence_quality_low_block",
        "review_incomplete_block",
    )

    assert watch_row.learning_status == "watch"
    assert watch_row.priority_score == d("0.220000")
    assert watch_row.reason_codes == (
        "prediction_deviation_high_watch",
        "evidence_quality_low_watch",
        "review_incomplete_watch",
    )

    assert pass_row.learning_status == "pass"
    assert pass_row.priority_score == d("0.040000")
    assert pass_row.reason_codes == ("learning_ready",)

    payload = research_outcome_learning_queue_payload(result)
    serialized = json.dumps(payload, sort_keys=True)
    assert not _contains_float(payload)
    _assert_status_values_are_public(payload)
    for fragment in FORBIDDEN_PUBLIC_FRAGMENTS:
        assert fragment.lower() not in serialized.lower()


def test_decimal_type_rejection_is_exact() -> None:
    with pytest.raises(ValueError, match="predicted_probability"):
        ResearchOutcomeLearningRecord(
            private_case_ref="case",
            private_event_ref="event",
            settlement_state="settled",
            predicted_probability=_DecimalSubclass("0.500000"),
            resolved_probability=d("1.000000"),
            evidence_quality_score=d("0.900000"),
            review_completeness_score=d("0.900000"),
        )

    with pytest.raises(ValueError, match="evidence_quality_score"):
        ResearchOutcomeLearningRecord(
            private_case_ref="case",
            private_event_ref="event",
            settlement_state="settled",
            predicted_probability=d("0.500000"),
            resolved_probability=d("1.000000"),
            evidence_quality_score=1,  # type: ignore[arg-type]
            review_completeness_score=d("0.900000"),
        )

    with pytest.raises(ValueError, match="watch_prediction_deviation"):
        ResearchOutcomeLearningQueueConfig(
            watch_prediction_deviation=0.1,  # type: ignore[arg-type]
        )


def test_public_payload_rejects_leaky_keys_values_and_non_public_statuses() -> None:
    base_payload = {"paper_only": True, "report_only": True, "readonly": True}
    leaky_keys = (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy_signal",
        "sell_signal",
        "recommendation",
    )
    for key in leaky_keys:
        with pytest.raises(ValueError, match="unsafe"):
            research_outcome_learning_queue_payload({**base_payload, key: "safe"})

    leaky_values = (
        "raw candidate abc",
        "market-123",
        "source-ref",
        "https://example.invalid/source",
        "postgres://user:pass@localhost/db",
        "wallet auth token",
        "open order",
        "trade fill",
        "position size",
        "buy now",
        "sell now",
        "recommendation text",
    )
    for value in leaky_values:
        with pytest.raises(ValueError, match="unsafe"):
            research_outcome_learning_queue_payload({**base_payload, "safe_key": value})

    with pytest.raises(ValueError, match="public status"):
        research_outcome_learning_queue_payload(
            {**base_payload, "settlement_status": "settled"},
        )


def test_hard_flags_are_required_and_dataclasses_are_frozen() -> None:
    item = record("pass", "0.550000", "0.500000")
    result = report(item)

    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    for value in (item, result, result.rows[0]):
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly"):
        replace(item, readonly=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        research_outcome_learning_queue_payload(
            {"paper_only": True, "report_only": True},
        )


def test_output_is_deterministic_for_input_order_and_json_ready() -> None:
    rows = (
        record("a", "0.800000", "0.000000"),
        record("b", "0.450000", "0.500000"),
        record("c", "0.700000", "0.500000", evidence_quality_score="0.650000"),
    )

    first = report(*rows)
    second = report(*reversed(rows))

    assert first == second
    assert first.derived_validation_digest == second.derived_validation_digest
    assert research_outcome_learning_queue_payload(first) == (
        research_outcome_learning_queue_payload(second)
    )
    json.dumps(research_outcome_learning_queue_payload(first), sort_keys=True)


def test_static_module_has_no_network_chain_or_write_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_outcome_learning_queue.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_modules = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "sqlite3",
        "psycopg",
        "supabase",
        "sqlalchemy",
        "web3",
    )
    forbidden_calls = (
        "open",
        "connect",
        "execute",
        "commit",
        "write",
        "send",
        "post",
        "put",
        "patch",
        "delete",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_modules
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_modules
        if isinstance(node, ast.Call):
            call_name = ""
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            assert call_name not in forbidden_calls


def _contains_float(value: object) -> bool:
    if type(value) is float:
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False


def _assert_status_values_are_public(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.endswith("status") or key.endswith("gate"):
                assert item in PUBLIC_STATES
            _assert_status_values_are_public(item)
    elif isinstance(value, list):
        for item in value:
            _assert_status_values_are_public(item)
