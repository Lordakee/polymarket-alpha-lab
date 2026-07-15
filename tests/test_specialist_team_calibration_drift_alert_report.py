from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_calibration_drift_alert_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_calibration_drift_alert_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    payload_without_digest = dict(payload)
    payload_without_digest.pop("payload_digest")
    encoded = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_report(**overrides: object) -> Any:
    values: dict[str, object] = {
        "team_id": "team_macro",
        "recent_prediction_count": d("30.000000"),
        "recent_error_probability": d("0.180000"),
        "historical_error_probability": d("0.060000"),
        "drift_threshold_probability": d("0.050000"),
    }
    values.update(overrides)
    return api().build_specialist_team_calibration_drift_alert_report(**values)


def assert_no_public_numeric_scalars(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"public numeric scalar leaked: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_public_numeric_scalars(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_public_numeric_scalars(child)


def test_threshold_breach_outputs_block_alert_reason_codes_and_payload_digest() -> None:
    module = api()

    report = build_report()

    assert is_dataclass(report)
    assert module.SPECIALIST_TEAM_CALIBRATION_DRIFT_ALERT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.team_id == "team_macro"
    assert report.recent_prediction_count == d("30.000000")
    assert report.recent_error_probability == d("0.180000")
    assert report.historical_error_probability == d("0.060000")
    assert report.drift_threshold_probability == d("0.050000")
    assert report.drift_probability == d("0.120000")
    assert report.calibration_drift_status == "block"
    assert report.reason_codes == (
        "calibration_drift_threshold_breached",
        "recent_error_above_historical_probability",
    )
    assert report.manual_next_step == "manual_escalate_calibration_drift_alert"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.specialist_team_calibration_drift_alert_report_payload(report)
    assert payload == report.public_payload
    assert payload["recent_prediction_count"] == "30.000000"
    assert payload["recent_error_probability"] == "0.180000"
    assert payload["historical_error_probability"] == "0.060000"
    assert payload["drift_threshold_probability"] == "0.050000"
    assert payload["drift_probability"] == "0.120000"
    assert payload["calibration_drift_status"] == "block"
    assert payload["manual_next_step"] == "manual_escalate_calibration_drift_alert"
    assert payload["payload_digest"] == report.payload_digest
    assert payload["payload_digest"] == canonical_digest(payload)
    assert len(report.payload_digest) == 64
    int(report.payload_digest, 16)
    assert_no_public_numeric_scalars(payload)
    json.dumps(payload, sort_keys=True)


def test_clear_soft_drift_and_missing_recent_predictions_are_report_only() -> None:
    clear = build_report(
        recent_error_probability=d("0.050000"),
        historical_error_probability=d("0.070000"),
    )
    assert clear.drift_probability == d("-0.020000")
    assert clear.calibration_drift_status == "pass"
    assert clear.reason_codes == ("calibration_drift_clear",)
    assert clear.manual_next_step == "manual_no_action"

    soft_drift = build_report(
        recent_error_probability=d("0.074000"),
        historical_error_probability=d("0.070000"),
        drift_threshold_probability=d("0.010000"),
    )
    assert soft_drift.drift_probability == d("0.004000")
    assert soft_drift.calibration_drift_status == "watch"
    assert soft_drift.reason_codes == ("recent_error_above_historical_probability",)
    assert soft_drift.manual_next_step == "manual_review_calibration_drift_evidence"

    no_recent = build_report(
        recent_prediction_count=d("0.000000"),
        recent_error_probability=d("0.220000"),
        historical_error_probability=d("0.050000"),
    )
    assert no_recent.calibration_drift_status == "watch"
    assert no_recent.reason_codes == ("no_recent_predictions",)
    assert no_recent.manual_next_step == "manual_review_calibration_drift_evidence"
    assert no_recent.paper_only is True
    assert no_recent.report_only is True
    assert no_recent.readonly is True


def test_contract_is_frozen_decimal_only_and_strictly_validated() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_SPECIALIST_TEAM_CALIBRATION_DRIFT_ALERT_CONFIG_VERSION",
        "SPECIALIST_TEAM_CALIBRATION_DRIFT_ALERT_STATUSES",
        "SpecialistTeamCalibrationDriftAlertReport",
        "build_specialist_team_calibration_drift_alert_report",
        "specialist_team_calibration_drift_alert_report_digest",
        "specialist_team_calibration_drift_alert_report_payload",
        "validate_specialist_team_calibration_drift_alert_public_payload",
    )
    assert module.SpecialistTeamCalibrationDriftAlertReport.__dataclass_params__.frozen is True

    hints = get_type_hints(module.SpecialistTeamCalibrationDriftAlertReport)
    for field_name in (
        "recent_prediction_count",
        "recent_error_probability",
        "historical_error_probability",
        "drift_threshold_probability",
        "drift_probability",
    ):
        assert hints[field_name] is Decimal

    report = build_report()
    with pytest.raises(FrozenInstanceError):
        report.calibration_drift_status = "pass"  # type: ignore[misc]

    for item in fields(report):
        value = getattr(report, item.name)
        if item.name in {
            "recent_prediction_count",
            "recent_error_probability",
            "historical_error_probability",
            "drift_threshold_probability",
            "drift_probability",
        }:
            assert type(value) is Decimal

    with pytest.raises(ValueError, match="recent_prediction_count must be a Decimal"):
        build_report(recent_prediction_count=30)
    with pytest.raises(ValueError, match="recent_error_probability must be a Decimal"):
        build_report(recent_error_probability=_DecimalSubclass("0.180000"))
    with pytest.raises(ValueError, match="recent_prediction_count must be an integer Decimal"):
        build_report(recent_prediction_count=d("30.500000"))
    with pytest.raises(ValueError, match="recent_prediction_count must be nonnegative"):
        build_report(recent_prediction_count=d("-1.000000"))
    with pytest.raises(ValueError, match="historical_error_probability must be between"):
        build_report(historical_error_probability=d("1.000001"))
    with pytest.raises(ValueError, match="drift_threshold_probability must be positive"):
        build_report(drift_threshold_probability=d("0.000000"))
    with pytest.raises(ValueError, match="team_id must be a public code"):
        build_report(team_id="Team Macro")
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="calibration_drift_status must match reason_codes"):
        replace(report, calibration_drift_status="pass")
    with pytest.raises(ValueError, match="payload_digest must match public_payload"):
        replace(report, payload_digest="0" * 64)


def test_public_payload_rejects_tampering_leaks_and_module_side_effect_surfaces() -> None:
    module = api()
    report = build_report()
    payload = report.public_payload

    tampered = dict(payload)
    tampered["calibration_drift_status"] = "pass"
    with pytest.raises(ValueError, match="payload_digest"):
        module.validate_specialist_team_calibration_drift_alert_public_payload(tampered)

    unsafe_fragments = ("live", "auth", "wallet", "order", "private_key")
    for fragment in unsafe_fragments:
        leaked = dict(payload)
        leaked["team_id"] = fragment
        leaked["payload_digest"] = canonical_digest(leaked)
        with pytest.raises(ValueError, match="unsafe public payload"):
            module.validate_specialist_team_calibration_drift_alert_public_payload(leaked)

    assert module.specialist_team_calibration_drift_alert_report_digest(report) == (
        payload["payload_digest"]
    )
    assert module.validate_specialist_team_calibration_drift_alert_public_payload(payload)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: set[str] = set()
    calls: set[str] = set()
    attributes: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name is not None:
                calls.add(name)
        elif isinstance(node, ast.Attribute):
            attributes.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_or_attribute_names = {
        "__import__",
        "cancel",
        "commit",
        "connect",
        "cursor",
        "eval",
        "exec",
        "open",
        "print",
        "rollback",
        "send",
        "write",
    }
    assert not float_constants
    assert imports.isdisjoint(forbidden_import_roots)
    assert calls.isdisjoint(forbidden_call_or_attribute_names)
    assert attributes.isdisjoint(forbidden_call_or_attribute_names)

    module_text = MODULE_PATH.read_text(encoding="utf-8").casefold()
    for forbidden in ("live", "auth", "wallet", "order", "private_key"):
        assert forbidden not in module_text


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
