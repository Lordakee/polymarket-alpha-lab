from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_screen_operating_review_report import (
    PROBABILITY_EVENT_SCREEN_OPERATING_REVIEW_REPORT_VERSION,
    ProbabilityEventScreenOperatingReviewInput,
    ProbabilityEventScreenOperatingReviewReport,
    build_probability_event_screen_operating_review_report,
    probability_event_screen_operating_review_report_digest,
    probability_event_screen_operating_review_report_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_screen_operating_review_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def review_input(**overrides: object) -> ProbabilityEventScreenOperatingReviewInput:
    values = {
        "daily_brief_ready": True,
        "batch_triage_ready": True,
        "exception_queue_ready": True,
        "manual_decision_gate_ready": True,
        "postmortem_ready": True,
        "team_scorecard_ready": True,
        "supabase_export_manifest_ready": True,
        "operator_safety_ready": True,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ProbabilityEventScreenOperatingReviewInput(**values)


def report(**overrides: object) -> ProbabilityEventScreenOperatingReviewReport:
    return build_probability_event_screen_operating_review_report(
        review_input(**overrides),
    )


def test_ready_operating_review_payload_digest_and_public_schema() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventScreenOperatingReviewReport
    assert is_dataclass(first)
    assert first.__dataclass_params__.frozen is True
    assert first.config_version == PROBABILITY_EVENT_SCREEN_OPERATING_REVIEW_REPORT_VERSION
    assert first.operating_review_ready is True
    assert first.review_band == "ready"
    assert first.blocked_reason_codes == ()
    assert first.attention_reason_codes == ()
    assert first.ready_signal_count == d("8.000000")
    assert first.total_signal_count == d("8.000000")
    assert first.ready_ratio == d("1.000000")
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second
    assert first.digest == second.digest
    assert probability_event_screen_operating_review_report_digest(first) == first.digest

    payload = probability_event_screen_operating_review_report_payload(first)
    assert payload == first.public_payload
    assert payload == {
        "config_version": "probability-event-screen-operating-review-v0",
        "operating_review_ready": True,
        "review_band": "ready",
        "daily_brief_ready": True,
        "batch_triage_ready": True,
        "exception_queue_ready": True,
        "manual_decision_gate_ready": True,
        "postmortem_ready": True,
        "team_scorecard_ready": True,
        "supabase_export_manifest_ready": True,
        "operator_safety_ready": True,
        "ready_signal_count": "8.000000",
        "total_signal_count": "8.000000",
        "blocked_reason_codes": (),
        "attention_reason_codes": (),
        "ready_ratio": "1.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "digest": first.digest,
    }
    json.dumps(payload, sort_keys=True)
    expected_digest = sha256(
        json.dumps(
            {**payload, "digest": ""},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    assert first.digest == expected_digest
    assert _float_or_int_paths(payload) == ()

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["review_band"] = "blocked"


def test_blocked_operating_review_lists_blockers_before_attention() -> None:
    result = report(
        daily_brief_ready=False,
        batch_triage_ready=False,
        exception_queue_ready=False,
        manual_decision_gate_ready=False,
        postmortem_ready=False,
        team_scorecard_ready=False,
        supabase_export_manifest_ready=False,
        operator_safety_ready=False,
    )

    assert result.operating_review_ready is False
    assert result.review_band == "blocked"
    assert result.ready_signal_count == d("0.000000")
    assert result.ready_ratio == d("0.000000")
    assert result.blocked_reason_codes == (
        "daily_brief_not_ready",
        "batch_triage_not_ready",
        "exception_queue_not_ready",
        "manual_decision_gate_not_ready",
        "supabase_export_manifest_not_ready",
        "operator_safety_not_ready",
    )
    assert result.attention_reason_codes == (
        "postmortem_not_ready",
        "team_scorecard_not_ready",
    )
    assert result.public_payload["blocked_reason_codes"] == result.blocked_reason_codes
    assert result.public_payload["attention_reason_codes"] == result.attention_reason_codes


def test_watch_operating_review_keeps_report_available_for_learning_gaps() -> None:
    result = report(postmortem_ready=False, team_scorecard_ready=False)

    assert result.operating_review_ready is False
    assert result.review_band == "watch"
    assert result.ready_signal_count == d("6.000000")
    assert result.ready_ratio == d("0.750000")
    assert result.blocked_reason_codes == ()
    assert result.attention_reason_codes == (
        "postmortem_not_ready",
        "team_scorecard_not_ready",
    )


def test_frozen_decimal_only_exact_types_and_hard_flags() -> None:
    input_value = review_input()
    result = report()

    assert is_dataclass(input_value)
    assert input_value.__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        input_value.daily_brief_ready = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.review_band = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenOperatingReviewInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventScreenOperatingReviewReport):
            pass

    with pytest.raises(ValueError, match="daily_brief_ready"):
        review_input(daily_brief_ready=1)
    with pytest.raises(ValueError, match="paper_only"):
        review_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="ready_signal_count"):
        replace(result, ready_signal_count=8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ready_ratio must match"):
        replace(result, ready_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="digest"):
        probability_event_screen_operating_review_report_payload(
            replace(result, digest="0" * 64),
        )

    hints = get_type_hints(ProbabilityEventScreenOperatingReviewReport)
    for field in fields(ProbabilityEventScreenOperatingReviewReport):
        value = getattr(result, field.name)
        if field.name.endswith("_count") or field.name == "ready_ratio":
            assert type(value) is Decimal
            assert hints[field.name] is Decimal
        elif type(value) in (int, float):
            pytest.fail(f"runtime public numeric field is not Decimal: {field.name}")


def test_module_is_readonly_report_only_and_has_no_live_execution_or_io_surface() -> None:
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
        "live_trading",
        "order execution",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "database",
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
