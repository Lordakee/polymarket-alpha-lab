from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.specialist_team_settlement_feedback_memory_queue_report import (
    SpecialistTeamSettlementFeedbackMemoryQueueInput,
    SpecialistTeamSettlementFeedbackMemoryQueueReport,
    build_specialist_team_settlement_feedback_memory_queue_report,
    specialist_team_settlement_feedback_memory_queue_report_public_payload,
    validate_specialist_team_settlement_feedback_memory_queue_payload_digest,
)


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(
    *,
    settled_event_count: Decimal = d("8"),
    feedback_item_count: Decimal = d("8"),
    memory_write_ready_count: Decimal = d("8"),
    calibration_update_count: Decimal = d("3"),
    oldest_feedback_age_hours: Decimal = d("12.000000"),
) -> SpecialistTeamSettlementFeedbackMemoryQueueReport:
    queue_input = SpecialistTeamSettlementFeedbackMemoryQueueInput(
        settled_event_count=settled_event_count,
        feedback_item_count=feedback_item_count,
        memory_write_ready_count=memory_write_ready_count,
        calibration_update_count=calibration_update_count,
        oldest_feedback_age_hours=oldest_feedback_age_hours,
    )
    return build_specialist_team_settlement_feedback_memory_queue_report(queue_input)


def test_ready_report_surfaces_public_payload_and_digest() -> None:
    report = build_report()
    payload = specialist_team_settlement_feedback_memory_queue_report_public_payload(
        report,
    )
    payload_without_digest = dict(payload)
    payload_digest = payload_without_digest.pop("payload_digest")
    encoded_body = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )

    assert type(report) is SpecialistTeamSettlementFeedbackMemoryQueueReport
    assert report.feedback_queue_status == "ready"
    assert report.reason_codes == ("settlement_feedback_memory_queue_ready",)
    assert report.manual_next_step == "continue_readonly_memory_queue_monitoring"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert payload["settled_event_count"] == "8"
    assert payload["feedback_item_count"] == "8"
    assert payload["memory_write_ready_count"] == "8"
    assert payload["calibration_update_count"] == "3"
    assert payload["oldest_feedback_age_hours"] == "12.000000"
    assert payload["feedback_queue_status"] == "ready"
    assert payload["reason_codes"] == ["settlement_feedback_memory_queue_ready"]
    assert payload["manual_next_step"] == "continue_readonly_memory_queue_monitoring"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload_digest == report.payload_digest
    assert payload_digest == hashlib.sha256(encoded_body.encode("utf-8")).hexdigest()
    assert validate_specialist_team_settlement_feedback_memory_queue_payload_digest(
        payload,
    )
    assert not any(type(value) in (int, float) for value in _walk(payload))


def test_watch_status_when_feedback_or_memory_queue_is_incomplete() -> None:
    report = build_report(
        settled_event_count=d("10"),
        feedback_item_count=d("7"),
        memory_write_ready_count=d("5"),
        calibration_update_count=d("1"),
        oldest_feedback_age_hours=d("30.000000"),
    )

    assert report.feedback_queue_status == "watch"
    assert report.reason_codes == (
        "settlement_feedback_items_missing",
        "settlement_feedback_memory_writes_pending",
        "settlement_feedback_calibration_updates_sparse",
        "settlement_feedback_queue_age_watch",
    )
    assert report.manual_next_step == "review_pending_feedback_before_memory_queue_write"


def test_block_status_when_settlements_are_absent_or_feedback_is_stale() -> None:
    report = build_report(
        settled_event_count=d("0"),
        feedback_item_count=d("0"),
        memory_write_ready_count=d("0"),
        calibration_update_count=d("0"),
        oldest_feedback_age_hours=d("96.000000"),
    )

    assert report.feedback_queue_status == "block"
    assert report.reason_codes == (
        "settled_events_missing",
        "settlement_feedback_items_missing",
        "settlement_feedback_memory_writes_pending",
        "settlement_feedback_calibration_updates_sparse",
        "settlement_feedback_queue_age_block",
    )
    assert report.manual_next_step == "manual_settlement_feedback_triage_required"


def test_decimal_only_inputs_hard_flags_frozen_and_tamper_checked() -> None:
    with pytest.raises(ValueError, match="settled_event_count"):
        build_report(settled_event_count=8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="feedback_item_count"):
        build_report(feedback_item_count=DecimalSubclass("8"))
    with pytest.raises(ValueError, match="oldest_feedback_age_hours"):
        build_report(oldest_feedback_age_hours=d("-0.000001"))

    report = build_report()
    with pytest.raises(FrozenInstanceError):
        report.feedback_queue_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="payload_digest"):
        replace(report, payload_digest="0" * 64)

    payload = specialist_team_settlement_feedback_memory_queue_report_public_payload(
        report,
    )
    tampered = dict(payload)
    tampered["feedback_item_count"] = "1"
    assert not validate_specialist_team_settlement_feedback_memory_queue_payload_digest(
        tampered,
    )


def test_module_has_no_live_auth_wallet_database_or_file_persistence_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "specialist_team_settlement_feedback_memory_queue_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "database",
        "jsonl",
        "wallet",
        "auth",
        "private_key",
        "sign",
        "live",
        "execute",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        values.extend(value.keys())
        for item_value in value.values():
            values.extend(_walk(item_value))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk(item))
    else:
        values.append(value)
    return tuple(values)
