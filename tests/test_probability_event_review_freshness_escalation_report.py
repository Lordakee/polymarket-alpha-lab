from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_review_freshness_escalation_report import (
    PROBABILITY_EVENT_REVIEW_FRESHNESS_ESCALATION_REPORT_VERSION,
    ProbabilityEventReviewFreshnessEscalationInput,
    ProbabilityEventReviewFreshnessEscalationReport,
    build_probability_event_review_freshness_escalation_report,
    probability_event_review_freshness_escalation_report_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_review_freshness_escalation_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def review_input(
    **overrides: object,
) -> ProbabilityEventReviewFreshnessEscalationInput:
    values = {
        "last_operator_review_age_hours": d("1"),
        "source_refresh_age_hours": d("1"),
        "price_move_since_review_probability": d("0.020"),
        "market_close_hours": d("72"),
        "blocking_reason_count": d("0"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ProbabilityEventReviewFreshnessEscalationInput(**values)


def report(**overrides: object) -> ProbabilityEventReviewFreshnessEscalationReport:
    return build_probability_event_review_freshness_escalation_report(
        review_input(**overrides),
    )


def test_current_review_payload_is_readonly_and_decimal_serialized() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventReviewFreshnessEscalationReport
    assert is_dataclass(first)
    assert first.__dataclass_params__.frozen is True
    assert first.config_version == (
        PROBABILITY_EVENT_REVIEW_FRESHNESS_ESCALATION_REPORT_VERSION
    )
    assert first.escalation_status == "current"
    assert first.reason_codes == ()
    assert first.manual_next_step == "continue_standard_monitoring"
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second

    payload = probability_event_review_freshness_escalation_report_payload(first)
    assert payload == {
        "config_version": "probability-event-review-freshness-escalation-v0",
        "last_operator_review_age_hours": "1.000000",
        "source_refresh_age_hours": "1.000000",
        "price_move_since_review_probability": "0.020000",
        "market_close_hours": "72.000000",
        "blocking_reason_count": "0.000000",
        "escalation_status": "current",
        "reason_codes": (),
        "manual_next_step": "continue_standard_monitoring",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert _float_or_int_paths(payload) == ()

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["escalation_status"] = "manual_review"  # type: ignore[index]


def test_manual_review_escalates_stale_review_and_source_refresh() -> None:
    result = report(
        last_operator_review_age_hours=d("13"),
        source_refresh_age_hours=d("7"),
        price_move_since_review_probability=d("0.040"),
        market_close_hours=d("36"),
        blocking_reason_count=d("0"),
    )

    assert result.escalation_status == "manual_review"
    assert result.reason_codes == (
        "operator_review_stale",
        "source_refresh_stale",
    )
    assert result.manual_next_step == "refresh_sources_then_operator_review"


def test_urgent_escalation_prioritizes_blockers_close_and_large_move() -> None:
    result = report(
        last_operator_review_age_hours=d("25"),
        source_refresh_age_hours=d("13"),
        price_move_since_review_probability=d("0.120"),
        market_close_hours=d("5"),
        blocking_reason_count=d("2"),
    )

    assert result.escalation_status == "urgent_manual_review"
    assert result.reason_codes == (
        "operator_review_expired",
        "source_refresh_expired",
        "price_move_requires_review",
        "market_close_imminent",
        "blocking_reasons_present",
    )
    assert result.manual_next_step == "escalate_to_operator_before_any_action"


def test_blocking_reason_alone_requires_manual_resolution_not_execution() -> None:
    result = report(
        blocking_reason_count=d("1"),
        last_operator_review_age_hours=d("1"),
        source_refresh_age_hours=d("1"),
        price_move_since_review_probability=d("0.010"),
        market_close_hours=d("72"),
    )

    assert result.escalation_status == "manual_review"
    assert result.reason_codes == ("blocking_reasons_present",)
    assert result.manual_next_step == "resolve_blocking_reasons_manually"


def test_frozen_exact_decimal_inputs_and_hard_flags() -> None:
    input_value = review_input()
    result = report()

    assert is_dataclass(input_value)
    assert input_value.__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        input_value.last_operator_review_age_hours = d("2")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.escalation_status = "manual_review"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventReviewFreshnessEscalationInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventReviewFreshnessEscalationReport):
            pass

    with pytest.raises(ValueError, match="last_operator_review_age_hours"):
        review_input(last_operator_review_age_hours=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="price_move_since_review_probability"):
        review_input(price_move_since_review_probability=d("1.001"))
    with pytest.raises(ValueError, match="blocking_reason_count"):
        review_input(blocking_reason_count=d("1.5"))
    with pytest.raises(ValueError, match="paper_only"):
        review_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, reason_codes=("unsupported_reason",))
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(result, manual_next_step="place_order")

    hints = get_type_hints(ProbabilityEventReviewFreshnessEscalationReport)
    for field in fields(ProbabilityEventReviewFreshnessEscalationReport):
        value = getattr(result, field.name)
        if field.name.endswith("_hours") or field.name.endswith("_probability"):
            assert type(value) is Decimal
            assert hints[field.name] is Decimal
        elif field.name == "blocking_reason_count":
            assert type(value) is Decimal
            assert hints[field.name] is Decimal
        elif type(value) in (int, float):
            pytest.fail(f"runtime public numeric field is not Decimal: {field.name}")


def test_module_is_report_only_and_has_no_execution_or_persistence_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "web3",
        "private_key",
        "wallet",
        "authentication",
        "auth",
        "live",
        "trading",
        "order",
        "execution",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "database",
        "persist",
        "network",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "web3",
    }
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
        "write_text",
        "write_bytes",
    }
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not imported_roots.intersection(forbidden_imports)
    assert not call_names.intersection(forbidden_call_names)
    assert float_constants == []


def _float_or_int_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if type(value) in (int, float, Decimal):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_or_int_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, (list, tuple)):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_or_int_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()
