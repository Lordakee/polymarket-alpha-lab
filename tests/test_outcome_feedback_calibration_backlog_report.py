from __future__ import annotations

import ast
import hashlib
import importlib
import json
import sys
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.outcome_feedback_calibration_backlog_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "outcome_feedback_calibration_backlog_report.py"
)
SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
GENERATED_AT = datetime(2026, 7, 12, 9, 30, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def item(
    feedback_key: str,
    *,
    settled_count: Decimal = d("40.000000"),
    pending_count: Decimal = d("1.000000"),
    calibration_error: Decimal = d("0.030000"),
    source_error_pattern_count: Decimal = d("0.000000"),
    team_memory_update_needed: bool = False,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return api().OutcomeFeedbackCalibrationBacklogInput(
        feedback_key=feedback_key,
        settled_count=settled_count,
        pending_count=pending_count,
        calibration_error=calibration_error,
        source_error_pattern_count=source_error_pattern_count,
        team_memory_update_needed=team_memory_update_needed,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    return api().build_outcome_feedback_calibration_backlog_report(
        items,
        generated_at=generated_at,
    )


def test_report_prioritizes_learning_backlog_without_execution_side_effects() -> None:
    module = api()
    rows = (
        item("stable_pass"),
        item(
            "memory_watch",
            settled_count=d("30.000000"),
            pending_count=d("5.000000"),
            calibration_error=d("0.090000"),
            source_error_pattern_count=d("1.000000"),
            team_memory_update_needed=True,
        ),
        item(
            "calibration_block",
            settled_count=d("8.000000"),
            pending_count=d("12.000000"),
            calibration_error=d("0.180000"),
            source_error_pattern_count=d("3.000000"),
            team_memory_update_needed=True,
        ),
    )

    report = build_report(*rows)
    reversed_report = build_report(*reversed(rows))

    assert module.OUTCOME_FEEDBACK_CALIBRATION_BACKLOG_PRIORITIES == (
        "low",
        "medium",
        "high",
    )
    assert report.report_status == "block"
    assert report.input_count == d("3.000000")
    assert report.learning_backlog_count == d("2.000000")
    assert report.low_priority_count == d("1.000000")
    assert report.medium_priority_count == d("1.000000")
    assert report.high_priority_count == d("1.000000")
    assert report.total_settled_count == d("78.000000")
    assert report.total_pending_count == d("18.000000")
    assert report.max_calibration_error == d("0.180000")
    assert report.max_source_error_pattern_count == d("3.000000")
    assert report.team_memory_update_needed_count == d("2.000000")

    high, medium, low = report.backlog_items
    assert (high.feedback_key, medium.feedback_key, low.feedback_key) == (
        "calibration_block",
        "memory_watch",
        "stable_pass",
    )
    assert high.backlog_priority == "high"
    assert high.manual_next_step == "open_manual_calibration_review_packet"
    assert high.reason_codes == (
        "outcome_feedback_calibration_settled_sample_block",
        "outcome_feedback_calibration_pending_backlog_block",
        "outcome_feedback_calibration_error_block",
        "outcome_feedback_calibration_source_error_pattern_block",
        "outcome_feedback_calibration_team_memory_update_needed",
    )
    assert medium.backlog_priority == "medium"
    assert medium.manual_next_step == "queue_team_memory_update_review"
    assert medium.reason_codes == (
        "outcome_feedback_calibration_pending_backlog_watch",
        "outcome_feedback_calibration_error_watch",
        "outcome_feedback_calibration_source_error_pattern_watch",
        "outcome_feedback_calibration_team_memory_update_needed",
    )
    assert low.backlog_priority == "low"
    assert low.manual_next_step == "continue_readonly_outcome_monitoring"
    assert low.reason_codes == ("outcome_feedback_calibration_backlog_clear",)
    assert report.reason_codes == high.reason_codes + medium.reason_codes

    payload = module.outcome_feedback_calibration_backlog_report_payload(report)
    reversed_payload = module.outcome_feedback_calibration_backlog_report_payload(
        reversed_report,
    )
    assert payload == reversed_payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-12T09:30:00+00:00"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["backlog_items"][0]["calibration_error"] == "0.180000"
    assert _float_or_int_paths(payload) == ()
    assert _forbidden_public_fragments(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_empty_report_is_readonly_learning_backlog_and_decimal_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_OUTCOME_FEEDBACK_CALIBRATION_BACKLOG_CONFIG_VERSION",
        "OUTCOME_FEEDBACK_CALIBRATION_BACKLOG_PRIORITIES",
        "OutcomeFeedbackCalibrationBacklogInput",
        "OutcomeFeedbackCalibrationBacklogItem",
        "OutcomeFeedbackCalibrationBacklogReasonCodeCount",
        "OutcomeFeedbackCalibrationBacklogReport",
        "build_outcome_feedback_calibration_backlog_report",
        "outcome_feedback_calibration_backlog_report_digest",
        "outcome_feedback_calibration_backlog_report_payload",
        "validate_outcome_feedback_calibration_backlog_public_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    report = build_report()
    assert report.report_status == "pass"
    assert report.reason_codes == ("outcome_feedback_calibration_backlog_empty",)
    assert report.backlog_items == ()
    assert report.input_count == d("0.000000")
    assert report.learning_backlog_count == d("0.000000")
    assert report.total_settled_count == d("0.000000")
    assert report.total_pending_count == d("0.000000")
    assert report.max_calibration_error == d("0.000000")
    assert report.max_source_error_pattern_count == d("0.000000")
    assert report.team_memory_update_needed_count == d("0.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.outcome_feedback_calibration_backlog_report_payload(report)
    assert payload["reason_codes"] == ["outcome_feedback_calibration_backlog_empty"]
    assert payload["input_count"] == "0.000000"
    assert _float_or_int_paths(payload) == ()
    assert module.validate_outcome_feedback_calibration_backlog_public_payload(
        payload,
    ) == payload

    with pytest.raises(FrozenInstanceError):
        report.report_status = "block"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclass"):
        class Child(module.OutcomeFeedbackCalibrationBacklogInput):
            pass


def test_validation_rejects_non_decimal_inputs_flags_and_tampered_payloads() -> None:
    module = api()

    with pytest.raises(ValueError, match="Decimal"):
        item("bad_count", settled_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        item("bad_subclass", calibration_error=DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="nonnegative"):
        item("bad_pending", pending_count=d("-1.000000"))
    with pytest.raises(ValueError, match="ratio"):
        item("bad_error", calibration_error=d("1.100000"))
    with pytest.raises(ValueError, match="paper_only"):
        item("bad_flag", paper_only=False)
    with pytest.raises(ValueError, match="feedback_key"):
        item("market_slug")

    report = build_report(item("needs_memory", team_memory_update_needed=True))
    tampered = module.outcome_feedback_calibration_backlog_report_payload(report)
    tampered["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        module.validate_outcome_feedback_calibration_backlog_public_payload(tampered)

    numeric_payload = module.outcome_feedback_calibration_backlog_report_payload(report)
    numeric_payload["input_count"] = 1
    with pytest.raises(ValueError, match="numeric values must be strings"):
        module.validate_outcome_feedback_calibration_backlog_public_payload(
            numeric_payload,
        )

    unsafe_payload = module.outcome_feedback_calibration_backlog_report_payload(report)
    unsafe_payload["wallet"] = "readonly"
    unsafe_payload["derived_validation_digest"] = canonical_digest(unsafe_payload)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.validate_outcome_feedback_calibration_backlog_public_payload(
            unsafe_payload,
        )

    digest_payload = module.outcome_feedback_calibration_backlog_report_payload(report)
    digest_payload["reason_codes"] = ["outcome_feedback_calibration_error_block"]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_outcome_feedback_calibration_backlog_public_payload(
            digest_payload,
        )

    with pytest.raises(ValueError, match="report_status"):
        replace(report, report_status="pass")


def test_source_file_contains_no_persistence_live_auth_wallet_or_order_surface() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    forbidden = ("persist", "live", "auth", "wallet", "order")

    assert "open(" not in source
    assert "Path(" not in source
    assert "requests" not in source
    assert "httpx" not in source
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imported = " ".join(alias.name for alias in node.names)
            assert not any(term in imported.lower() for term in forbidden)
        elif isinstance(node, ast.Name):
            assert not any(term in node.id.lower() for term in forbidden)
        elif isinstance(node, ast.Attribute):
            assert not any(term in node.attr.lower() for term in forbidden)


def _float_or_int_paths(value: Any, path: str = "$") -> tuple[str, ...]:
    if type(value) in (int, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item_value in value.items():
            paths.extend(_float_or_int_paths(item_value, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item_value in enumerate(value):
            paths.extend(_float_or_int_paths(item_value, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _forbidden_public_fragments(value: Any) -> tuple[str, ...]:
    forbidden = ("persist", "live", "auth", "wallet", "order")
    encoded = json.dumps(value, sort_keys=True).lower()
    return tuple(term for term in forbidden if term in encoded)
