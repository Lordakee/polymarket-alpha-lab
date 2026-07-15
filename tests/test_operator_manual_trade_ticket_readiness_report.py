from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path
import hashlib
import importlib
import json

import pytest

from polymarket_alpha_lab.operator_manual_trade_ticket_readiness_report import (
    OperatorManualTradeTicketReadinessInput,
    OperatorManualTradeTicketReadinessReport,
    build_operator_manual_trade_ticket_readiness_report,
    operator_manual_trade_ticket_readiness_report_payload_digest,
    validate_operator_manual_trade_ticket_readiness_public_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def readiness_input(**overrides: object) -> OperatorManualTradeTicketReadinessInput:
    values = {
        "market_ref_present": True,
        "outcome_ref_present": True,
        "side_label_present": True,
        "max_manual_size_probability": d("0.020000"),
        "net_edge_probability": d("0.060000"),
        "all_gates_passed": True,
    }
    values.update(overrides)
    return OperatorManualTradeTicketReadinessInput(**values)


def report(
    **overrides: object,
) -> OperatorManualTradeTicketReadinessReport:
    return build_operator_manual_trade_ticket_readiness_report(
        readiness_input(**overrides),
    )


def payload_without_digest(payload: dict[str, object]) -> dict[str, object]:
    copy = dict(payload)
    copy.pop("payload_digest", None)
    return copy


def test_ready_ticket_emits_manual_review_payload_and_digest() -> None:
    ready = report()

    assert ready.ticket_status == "ready_for_manual_review"
    assert ready.reason_codes == ("manual_trade_ticket_ready_for_human_review",)
    assert ready.manual_next_step == "human_review_ticket_before_any_external_action"
    assert ready.paper_only is True
    assert ready.report_only is True
    assert ready.readonly is True
    assert ready.max_manual_size_probability == d("0.020000")
    assert ready.net_edge_probability == d("0.060000")

    payload = ready.public_payload
    assert payload["ticket_status"] == "ready_for_manual_review"
    assert payload["manual_next_step"] == "human_review_ticket_before_any_external_action"
    assert payload["max_manual_size_probability"] == "0.020000"
    assert payload["net_edge_probability"] == "0.060000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == ready.payload_digest
    assert validate_operator_manual_trade_ticket_readiness_public_payload(payload) is True
    assert operator_manual_trade_ticket_readiness_report_payload_digest(
        ready,
    ) == hashlib.sha256(
        json.dumps(
            payload_without_digest(payload),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    (
        ({"market_ref_present": False}, "missing_market_reference"),
        ({"outcome_ref_present": False}, "missing_outcome_reference"),
        ({"side_label_present": False}, "missing_side_label"),
        ({"max_manual_size_probability": d("0.000000")}, "manual_size_not_positive"),
        ({"net_edge_probability": d("0.000000")}, "net_edge_not_positive"),
        ({"all_gates_passed": False}, "upstream_gates_not_passed"),
    ),
)
def test_blocked_ticket_reports_specific_reason_codes(
    overrides: dict[str, object],
    expected_reason: str,
) -> None:
    blocked = report(**overrides)

    assert blocked.ticket_status == "blocked_for_manual_review"
    assert expected_reason in blocked.reason_codes
    assert blocked.manual_next_step == "do_not_prepare_ticket_until_reasons_are_resolved"


def test_multiple_blockers_use_canonical_order() -> None:
    blocked = report(
        market_ref_present=False,
        side_label_present=False,
        net_edge_probability=d("-0.010000"),
        all_gates_passed=False,
    )

    assert blocked.reason_codes == (
        "missing_market_reference",
        "missing_side_label",
        "net_edge_not_positive",
        "upstream_gates_not_passed",
    )


@pytest.mark.parametrize(
    ("factory", "match"),
    (
        (lambda: readiness_input(max_manual_size_probability=0.02), "max_manual_size_probability"),
        (lambda: readiness_input(net_edge_probability="0.06"), "net_edge_probability"),
        (lambda: readiness_input(market_ref_present=1), "market_ref_present"),
        (lambda: readiness_input(paper_only=False), "paper_only"),
        (lambda: readiness_input(report_only=False), "report_only"),
        (lambda: readiness_input(readonly=False), "readonly"),
    ),
)
def test_inputs_are_decimal_only_and_hard_flags_are_enforced(
    factory: object,
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        factory()


def test_report_dataclass_is_frozen_and_revalidates_tampering() -> None:
    ready = report()

    with pytest.raises(FrozenInstanceError):
        ready.ticket_status = "changed"
    with pytest.raises(ValueError, match="paper_only"):
        replace(ready, paper_only=False)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(ready, reason_codes=())
    with pytest.raises(ValueError, match="payload_digest"):
        replace(ready, payload_digest="0" * 64)


def test_public_payload_rejects_numeric_and_status_tampering() -> None:
    payload = report().public_payload

    numeric_tampered = dict(payload)
    numeric_tampered["net_edge_probability"] = 0.06
    with pytest.raises(ValueError, match="net_edge_probability"):
        validate_operator_manual_trade_ticket_readiness_public_payload(numeric_tampered)

    status_tampered = dict(payload)
    status_tampered["ticket_status"] = "ready_for_manual_review"
    status_tampered["all_gates_passed"] = False
    status_tampered["payload_digest"] = hashlib.sha256(
        json.dumps(
            payload_without_digest(status_tampered),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    with pytest.raises(ValueError, match="ticket_status|reason_codes"):
        validate_operator_manual_trade_ticket_readiness_public_payload(status_tampered)


def test_public_dataclasses_reject_subclassing() -> None:
    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeInput(OperatorManualTradeTicketReadinessInput):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(OperatorManualTradeTicketReadinessReport):
            pass


def test_static_forbidden_surface_terms_are_absent() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.operator_manual_trade_ticket_readiness_report",
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
        "order",
        "private_key",
        "api_key",
        "secret_key",
        "sign",
        "auto",
        "execute",
        "execution",
        "jsonl",
        "persist",
        "open(",
    )

    for term in forbidden_terms:
        assert term not in source
