from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_screen_review_packet_index_report import (
    PROBABILITY_EVENT_SCREEN_REVIEW_PACKET_INDEX_REPORT_VERSION,
    ProbabilityEventScreenReviewPacketIndexInput,
    ProbabilityEventScreenReviewPacketIndexReport,
    build_probability_event_screen_review_packet_index_report,
    probability_event_screen_review_packet_index_report_digest,
    probability_event_screen_review_packet_index_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_screen_review_packet_index_report.py",
)


def d(value: str) -> Decimal:
    return Decimal(value)


def index_input(
    **overrides: object,
) -> ProbabilityEventScreenReviewPacketIndexInput:
    values = {
        "screen_digest_present": True,
        "research_packet_digest_present": True,
        "source_reliability_digest_present": True,
        "due_diligence_digest_present": True,
        "quality_index_digest_present": True,
        "decision_memo_digest_present": True,
        "export_manifest_digest_present": True,
        "operator_safety_digest_present": True,
    }
    values.update(overrides)
    return ProbabilityEventScreenReviewPacketIndexInput(**values)


def report(**overrides: object) -> ProbabilityEventScreenReviewPacketIndexReport:
    return build_probability_event_screen_review_packet_index_report(
        index_input(**overrides),
    )


def test_complete_review_packet_index_is_ready_with_stable_payload_digest() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventScreenReviewPacketIndexReport
    assert is_dataclass(first)
    assert (
        first.config_version
        == PROBABILITY_EVENT_SCREEN_REVIEW_PACKET_INDEX_REPORT_VERSION
    )
    assert first.review_packet_index_ready is True
    assert first.missing_artifact_count == d("0.000000")
    assert first.index_completeness_score == d("1.000000")
    assert first.ready_ratio == d("1.000000")
    assert first.blocked_reason_codes == ("review_packet_index_ready",)
    assert first.attention_reason_codes == ()
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second
    assert first.digest == second.digest
    assert probability_event_screen_review_packet_index_report_digest(first) == first.digest

    payload = probability_event_screen_review_packet_index_report_payload(first)
    assert payload == first.public_payload
    assert payload["review_packet_index_ready"] is True
    assert payload["missing_artifact_count"] == "0.000000"
    assert payload["index_completeness_score"] == "1.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["digest"] == first.digest
    json.dumps(payload, sort_keys=True)
    assert not any(_is_forbidden_number(value) for value in _walk_payload_values(payload))

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["review_packet_index_ready"] = False


def test_missing_required_artifacts_block_index_and_roll_up_counts() -> None:
    result = report(
        research_packet_digest_present=False,
        source_reliability_digest_present=False,
        due_diligence_digest_present=False,
        quality_index_digest_present=False,
        decision_memo_digest_present=False,
        export_manifest_digest_present=False,
    )

    assert result.review_packet_index_ready is False
    assert result.missing_artifact_count == d("6.000000")
    assert result.index_completeness_score == d("0.250000")
    assert result.ready_ratio == d("0.250000")
    assert result.blocked_reason_codes == (
        "research_packet_digest_missing",
        "source_reliability_digest_missing",
        "due_diligence_digest_missing",
        "quality_index_digest_missing",
        "decision_memo_digest_missing",
        "export_manifest_digest_missing",
    )
    assert result.attention_reason_codes == (
        "review_packet_index_incomplete_attention",
    )
    assert result.public_payload["missing_artifact_count"] == "6.000000"
    assert result.public_payload["attention_reason_codes"] == (
        "review_packet_index_incomplete_attention",
    )


def test_operator_safety_gap_is_hard_blocker_not_execution_surface() -> None:
    result = report(operator_safety_digest_present=False)

    assert result.review_packet_index_ready is False
    assert result.missing_artifact_count == d("1.000000")
    assert result.index_completeness_score == d("0.875000")
    assert result.ready_ratio == d("0.875000")
    assert result.blocked_reason_codes == ("operator_safety_digest_missing",)
    assert result.attention_reason_codes == (
        "operator_safety_digest_missing_attention",
        "review_packet_index_incomplete_attention",
    )


def test_dataclasses_are_frozen_flag_guarded_and_decimal_only() -> None:
    input_value = index_input()
    result = report()

    assert is_dataclass(ProbabilityEventScreenReviewPacketIndexInput)
    assert is_dataclass(ProbabilityEventScreenReviewPacketIndexReport)
    assert result.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        input_value.screen_digest_present = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.review_packet_index_ready = False  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenReviewPacketIndexInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventScreenReviewPacketIndexReport):
            pass

    with pytest.raises(ValueError, match="screen_digest_present"):
        index_input(screen_digest_present=1)
    with pytest.raises(ValueError, match="paper_only"):
        index_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="missing_artifact_count"):
        replace(result, missing_artifact_count=0)  # type: ignore[arg-type]

    numeric_fields = {
        "artifact_count",
        "present_artifact_count",
        "missing_artifact_count",
        "index_completeness_score",
        "ready_ratio",
    }
    hints = get_type_hints(ProbabilityEventScreenReviewPacketIndexReport)
    for field in fields(ProbabilityEventScreenReviewPacketIndexReport):
        if field.name in numeric_fields:
            assert hints[field.name] is Decimal
            assert type(getattr(result, field.name)) is Decimal


def test_public_payload_tamper_checks_and_no_live_io_surface() -> None:
    payload = dict(report().public_payload)
    assert payload["digest"]

    with pytest.raises(ValueError, match="digest"):
        probability_event_screen_review_packet_index_report_payload(
            replace(report(), digest="0" * 64),
        )

    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "postgres://",
        "postgresql://",
        "service_role",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
    ):
        assert forbidden not in encoded

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "web3",
        "private_key",
        "live_trading",
        "place_order",
        "submit_order",
        "cancel_order",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source)
    forbidden_call_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "delete",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "open",
        "post",
        "put",
        "rollback",
        "sell",
        "send",
        "sign",
        "upsert",
        "write",
    }
    call_names: list[str] = []
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not float_constants
    assert not any(name in forbidden_call_names for name in call_names)


def _walk_payload_values(value: object) -> list[object]:
    if isinstance(value, dict):
        values: list[object] = []
        for item in value.values():
            values.extend(_walk_payload_values(item))
        return values
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_walk_payload_values(item))
        return values
    return [value]


def _is_forbidden_number(value: object) -> bool:
    return type(value) in (int, float, Decimal)
