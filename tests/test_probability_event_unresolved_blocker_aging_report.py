from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_unresolved_blocker_aging_report import (
    PROBABILITY_EVENT_UNRESOLVED_BLOCKER_AGING_REPORT_VERSION,
    ProbabilityEventUnresolvedBlockerAgingInput,
    ProbabilityEventUnresolvedBlockerAgingReport,
    build_probability_event_unresolved_blocker_aging_report,
    probability_event_unresolved_blocker_aging_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_unresolved_blocker_aging_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def aging_input(**overrides: object) -> ProbabilityEventUnresolvedBlockerAgingInput:
    values = {
        "blocker_count": d("0.000000"),
        "oldest_blocker_age_hours": d("0.000000"),
        "market_close_hours": d("72.000000"),
        "owner_assigned": True,
        "retry_count": d("0.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ProbabilityEventUnresolvedBlockerAgingInput(**values)


def report(**overrides: object) -> ProbabilityEventUnresolvedBlockerAgingReport:
    return build_probability_event_unresolved_blocker_aging_report(
        aging_input(**overrides),
    )


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) is int or type(value) is float or type(value) is Decimal:
        pytest.fail(f"payload contains runtime numeric value: {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            for forbidden in (
                "live",
                "auth",
                "wallet",
                "position",
                "database",
                "network",
                "order",
            ):
                assert forbidden not in lowered_key
            assert_no_runtime_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_clear_blocker_aging_report_payload_schema_and_manual_step() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventUnresolvedBlockerAgingReport
    assert is_dataclass(first)
    assert first.__dataclass_params__.frozen is True
    assert (
        first.config_version
        == PROBABILITY_EVENT_UNRESOLVED_BLOCKER_AGING_REPORT_VERSION
    )
    assert first.blocker_aging_status == "clear"
    assert first.reason_codes == ("no_unresolved_blockers",)
    assert first.manual_next_step == "continue_paper_monitoring"
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second

    payload = probability_event_unresolved_blocker_aging_report_payload(first)
    assert payload == first.public_payload
    assert payload == {
        "config_version": "probability-event-unresolved-blocker-aging-v0",
        "blocker_aging_status": "clear",
        "blocker_count": "0.000000",
        "oldest_blocker_age_hours": "0.000000",
        "market_close_hours": "72.000000",
        "owner_assigned": True,
        "retry_count": "0.000000",
        "reason_codes": ("no_unresolved_blockers",),
        "manual_next_step": "continue_paper_monitoring",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert_no_runtime_numbers(payload)
    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["blocker_aging_status"] = "blocked"


def test_watch_blocker_aging_report_surfaces_reviewable_reasons() -> None:
    result = report(
        blocker_count=d("1.000000"),
        oldest_blocker_age_hours=d("13.000000"),
        market_close_hours=d("18.000000"),
        retry_count=d("2.000000"),
    )

    assert result.blocker_aging_status == "watch"
    assert result.reason_codes == (
        "blocker_age_watch",
        "market_close_watch_window",
        "retry_count_watch",
    )
    assert result.manual_next_step == "refresh_blocker_owner_and_retry_plan"


def test_blocked_blocker_aging_report_prioritizes_stale_ownerless_close_risk() -> None:
    result = report(
        blocker_count=d("3.000000"),
        oldest_blocker_age_hours=d("30.000000"),
        market_close_hours=d("3.000000"),
        owner_assigned=False,
        retry_count=d("5.000000"),
    )

    assert result.blocker_aging_status == "blocked"
    assert result.reason_codes == (
        "blocker_age_block",
        "market_close_block_window",
        "owner_unassigned_block",
        "retry_count_block",
    )
    assert result.manual_next_step == "escalate_unresolved_blockers_before_paper_review"


def test_frozen_decimal_only_flags_and_report_consistency_are_enforced() -> None:
    input_value = aging_input()
    result = report()

    assert is_dataclass(input_value)
    assert input_value.__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        input_value.retry_count = d("1.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.blocker_aging_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventUnresolvedBlockerAgingInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventUnresolvedBlockerAgingReport):
            pass

    hints = get_type_hints(ProbabilityEventUnresolvedBlockerAgingReport)
    for field in fields(ProbabilityEventUnresolvedBlockerAgingReport):
        value = getattr(result, field.name)
        if field.name in {
            "blocker_count",
            "oldest_blocker_age_hours",
            "market_close_hours",
            "retry_count",
        }:
            assert type(value) is Decimal
            assert hints[field.name] is Decimal
        elif type(value) in (int, float):
            pytest.fail(f"runtime public numeric field is not Decimal: {field.name}")

    with pytest.raises(ValueError, match="blocker_count"):
        aging_input(blocker_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="blocker_count"):
        aging_input(blocker_count=d("1.500000"))
    with pytest.raises(ValueError, match="oldest_blocker_age_hours"):
        aging_input(oldest_blocker_age_hours=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="market_close_hours"):
        aging_input(market_close_hours=d("-0.000001"))
    with pytest.raises(ValueError, match="owner_assigned"):
        aging_input(owner_assigned=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="retry_count"):
        aging_input(retry_count=d("-1.000000"))
    with pytest.raises(ValueError, match="retry_count"):
        aging_input(retry_count=d("1.250000"))
    with pytest.raises(ValueError, match="paper_only"):
        aging_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="blocker_aging_status"):
        replace(result, blocker_aging_status="ready")
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(result, manual_next_step="submit_trade")

    object.__setattr__(result, "reason_codes", ("unsupported_reason",))
    with pytest.raises(ValueError, match="reason_codes"):
        probability_event_unresolved_blocker_aging_report_payload(result)


def test_module_is_readonly_report_only_and_has_no_io_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live",
        "auth",
        "wallet",
        "position",
        "private_key",
        "database",
        "network",
        "persist",
        "submit_order",
        "cancel_order",
        "replace_order",
        "create_order",
        "place_order",
        "urlopen",
        "connect(",
        "execute(",
        "write_text",
        "write_bytes",
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
        "sqlite3",
        "psycopg",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "__import__",
        "open",
        "connect",
        "execute",
        "request",
        "write",
        "write_text",
        "write_bytes",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
