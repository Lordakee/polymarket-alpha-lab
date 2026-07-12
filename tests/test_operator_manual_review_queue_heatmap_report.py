from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path
import hashlib
import importlib
import json

import pytest

from polymarket_alpha_lab.operator_manual_review_queue_heatmap_report import (
    OperatorManualReviewQueueHeatmapInput,
    OperatorManualReviewQueueHeatmapReport,
    build_operator_manual_review_queue_heatmap_report,
    operator_manual_review_queue_heatmap_report_payload_digest,
    validate_operator_manual_review_queue_heatmap_public_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def queue_input(**overrides: object) -> OperatorManualReviewQueueHeatmapInput:
    values = {
        "queue_item_count": d("4"),
        "urgent_item_count": d("1"),
        "blocked_item_count": d("0"),
        "ready_packet_count": d("4"),
        "manual_capacity_count": d("4"),
    }
    values.update(overrides)
    return OperatorManualReviewQueueHeatmapInput(**values)


def report(**overrides: object) -> OperatorManualReviewQueueHeatmapReport:
    return build_operator_manual_review_queue_heatmap_report(queue_input(**overrides))


def payload_without_digest(payload: dict[str, object]) -> dict[str, object]:
    copy = dict(payload)
    copy.pop("payload_digest", None)
    return copy


def test_ready_queue_heatmap_reports_manual_capacity_ready_payload_and_digest() -> None:
    ready = report()

    assert ready.heatmap_status == "ready"
    assert ready.reason_codes == ("manual_review_queue_heatmap_ready",)
    assert ready.manual_next_step == "continue_manual_review_from_ready_packet_queue"
    assert ready.queue_item_count == d("4.000000")
    assert ready.urgent_item_count == d("1.000000")
    assert ready.blocked_item_count == d("0.000000")
    assert ready.ready_packet_count == d("4.000000")
    assert ready.manual_capacity_count == d("4.000000")
    assert ready.paper_only is True
    assert ready.report_only is True
    assert ready.readonly is True

    payload = ready.public_payload
    assert payload["heatmap_status"] == "ready"
    assert payload["reason_codes"] == ("manual_review_queue_heatmap_ready",)
    assert payload["manual_next_step"] == "continue_manual_review_from_ready_packet_queue"
    assert payload["queue_item_count"] == "4.000000"
    assert payload["urgent_item_count"] == "1.000000"
    assert payload["blocked_item_count"] == "0.000000"
    assert payload["ready_packet_count"] == "4.000000"
    assert payload["manual_capacity_count"] == "4.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == ready.payload_digest
    assert validate_operator_manual_review_queue_heatmap_public_payload(payload) is True
    assert operator_manual_review_queue_heatmap_report_payload_digest(
        ready,
    ) == hashlib.sha256(
        json.dumps(
            payload_without_digest(payload),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


@pytest.mark.parametrize(
    ("overrides", "expected_status", "expected_reason", "expected_next_step"),
    (
        (
            {"manual_capacity_count": d("3")},
            "blocked",
            "manual_capacity_below_queue_count",
            "resolve_manual_review_queue_blockers_before_triage",
        ),
        (
            {"blocked_item_count": d("1")},
            "blocked",
            "blocked_items_present",
            "resolve_manual_review_queue_blockers_before_triage",
        ),
        (
            {"urgent_item_count": d("2")},
            "watch",
            "urgent_items_need_manual_triage",
            "triage_urgent_manual_review_items_first",
        ),
        (
            {"ready_packet_count": d("3")},
            "watch",
            "ready_packets_below_queue_count",
            "complete_ready_packets_before_manual_review",
        ),
        (
            {"queue_item_count": d("0")},
            "watch",
            "manual_review_queue_empty",
            "wait_for_manual_review_queue_items",
        ),
    ),
)
def test_heatmap_status_reason_and_manual_next_step_follow_queue_pressure(
    overrides: dict[str, object],
    expected_status: str,
    expected_reason: str,
    expected_next_step: str,
) -> None:
    value = report(**overrides)

    assert value.heatmap_status == expected_status
    assert expected_reason in value.reason_codes
    assert value.manual_next_step == expected_next_step


def test_multiple_queue_reasons_use_canonical_order() -> None:
    blocked = report(
        queue_item_count=d("5"),
        urgent_item_count=d("3"),
        blocked_item_count=d("2"),
        ready_packet_count=d("1"),
        manual_capacity_count=d("4"),
    )

    assert blocked.heatmap_status == "blocked"
    assert blocked.reason_codes == (
        "manual_capacity_below_queue_count",
        "blocked_items_present",
        "urgent_items_need_manual_triage",
        "ready_packets_below_queue_count",
    )
    assert blocked.manual_next_step == "resolve_manual_review_queue_blockers_before_triage"


@pytest.mark.parametrize(
    ("factory", "match"),
    (
        (lambda: queue_input(queue_item_count=4), "queue_item_count"),
        (lambda: queue_input(urgent_item_count="1"), "urgent_item_count"),
        (lambda: queue_input(blocked_item_count=d("-1")), "blocked_item_count"),
        (lambda: queue_input(ready_packet_count=d("1.5")), "ready_packet_count"),
        (lambda: queue_input(manual_capacity_count=d("NaN")), "manual_capacity_count"),
        (lambda: queue_input(paper_only=False), "paper_only"),
        (lambda: queue_input(report_only=False), "report_only"),
        (lambda: queue_input(readonly=False), "readonly"),
    ),
)
def test_inputs_are_decimal_only_whole_counts_and_hard_flags_are_enforced(
    factory: object,
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        factory()


def test_report_dataclass_is_frozen_and_revalidates_tampering() -> None:
    ready = report()

    with pytest.raises(FrozenInstanceError):
        ready.heatmap_status = "changed"
    with pytest.raises(ValueError, match="paper_only"):
        replace(ready, paper_only=False)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(ready, reason_codes=())
    with pytest.raises(ValueError, match="payload_digest"):
        replace(ready, payload_digest="0" * 64)


def test_public_payload_rejects_numeric_schema_and_digest_tampering() -> None:
    payload = report().public_payload

    numeric_tampered = dict(payload)
    numeric_tampered["queue_item_count"] = 4
    with pytest.raises(ValueError, match="queue_item_count"):
        validate_operator_manual_review_queue_heatmap_public_payload(numeric_tampered)

    status_tampered = dict(payload)
    status_tampered["heatmap_status"] = "blocked"
    status_tampered["payload_digest"] = hashlib.sha256(
        json.dumps(
            payload_without_digest(status_tampered),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    with pytest.raises(ValueError, match="heatmap_status|reason_codes|manual_next_step"):
        validate_operator_manual_review_queue_heatmap_public_payload(status_tampered)

    extra_key = dict(payload)
    extra_key["durable_path"] = "not-allowed"
    with pytest.raises(ValueError, match="schema"):
        validate_operator_manual_review_queue_heatmap_public_payload(extra_key)


def test_public_dataclasses_reject_subclassing() -> None:
    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeInput(OperatorManualReviewQueueHeatmapInput):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(OperatorManualReviewQueueHeatmapReport):
            pass


def test_static_module_surface_is_readonly_report_only_and_has_no_unsafe_paths() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.operator_manual_review_queue_heatmap_report",
    )
    source = Path(module.__file__).read_text(encoding="utf-8")
    forbidden_terms = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "live",
        "auth",
        "wallet",
        "key",
        "signing",
        "execute",
        "execution",
        "jsonl",
        "persist",
        "open(",
    )

    assert "paper_only: bool = True" in source
    assert "report_only: bool = True" in source
    assert "readonly: bool = True" in source
    for term in forbidden_terms:
        assert term not in source
