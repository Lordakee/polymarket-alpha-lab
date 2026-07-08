from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_calibration_drift_alert_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_calibration_drift_alert_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-calibration-drift-alert-report-test",
        "watch_brier_score_delta": d("0.030000"),
        "block_brier_score_delta": d("0.070000"),
        "watch_expected_calibration_error_delta": d("0.025000"),
        "block_expected_calibration_error_delta": d("0.060000"),
        "min_settled_count": d("20"),
    }
    values.update(overrides)
    return module.ResearchCalibrationDriftAlertConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "cohort_key": "cohort_alpha",
        "window_start_at": GENERATED_AT - timedelta(days=14),
        "window_end_at": GENERATED_AT - timedelta(days=7),
        "settled_count": d("40"),
        "baseline_brier_score": d("0.180000"),
        "current_brier_score": d("0.200000"),
        "baseline_expected_calibration_error": d("0.050000"),
        "current_expected_calibration_error": d("0.060000"),
        "manual_block_flag": False,
        "reason_codes": (),
    }
    values.update(overrides)
    return module.ResearchCalibrationDriftObservation(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_calibration_drift_alert_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal:
        return
    if isinstance(value, datetime):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_public_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "raw",
        "candidate_id",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "http://",
        "https://",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "buy",
        "sell",
        "recommend",
        "position",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def test_public_api_declares_readonly_report_contract() -> None:
    module = api()

    assert module.DEFAULT_RESEARCH_CALIBRATION_DRIFT_ALERT_CONFIG_VERSION == (
        "research-calibration-drift-alert-report-v0"
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_CALIBRATION_DRIFT_ALERT_CONFIG_VERSION",
        "ResearchCalibrationDriftAlertConfig",
        "ResearchCalibrationDriftObservation",
        "ResearchCalibrationDriftAlertRow",
        "ResearchCalibrationDriftAlertDigest",
        "ResearchCalibrationDriftAlertReport",
        "build_research_calibration_drift_alert_report",
        "research_calibration_drift_alert_report_payload",
        "research_calibration_drift_alert_digest_payload",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(module.ResearchCalibrationDriftAlertConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True


def test_builds_pass_watch_and_block_human_review_statuses() -> None:
    report = build_report(
        observation(cohort_key="alpha_pass"),
        observation(
            cohort_key="beta_watch",
            current_brier_score=d("0.225000"),
            current_expected_calibration_error=d("0.082000"),
        ),
        observation(
            cohort_key="gamma_block",
            current_brier_score=d("0.270000"),
            current_expected_calibration_error=d("0.120000"),
        ),
    )

    assert is_dataclass(report)
    assert report.status == "block"
    assert report.cohort_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_absolute_brier_score_delta == d("0.051667")
    assert report.max_absolute_brier_score_delta == d("0.090000")
    assert report.average_absolute_expected_calibration_error_delta == d("0.037333")
    assert report.max_absolute_expected_calibration_error_delta == d("0.070000")
    assert report.reason_codes == (
        "calibration_drift_report_block_rows",
        "calibration_drift_report_watch_rows",
    )

    assert tuple(row.cohort_key for row in report.rows) == (
        "alpha_pass",
        "beta_watch",
        "gamma_block",
    )
    assert tuple(row.status for row in report.rows) == ("pass", "watch", "block")
    assert report.rows[0].reason_codes == ("calibration_drift_pass",)
    assert report.rows[1].reason_codes == (
        "brier_score_drift_watch",
        "calibration_drift_watch",
        "expected_calibration_error_drift_watch",
    )
    assert report.rows[2].reason_codes == (
        "brier_score_drift_block",
        "calibration_drift_block",
        "expected_calibration_error_drift_block",
    )


def test_empty_and_manual_flagged_reports_block_for_human_review() -> None:
    module = api()
    empty = build_report()

    assert empty.status == "block"
    assert empty.cohort_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == ("no_calibration_drift_observations",)

    flagged = build_report(observation(manual_block_flag=True))
    assert flagged.status == "block"
    assert flagged.block_count == d("1.000000")
    assert flagged.rows[0].reason_codes == (
        "calibration_drift_block",
        "manual_review_required",
    )

    with pytest.raises(ValueError, match="manual_block_flag must be a bool"):
        replace(observation(), manual_block_flag=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(flagged.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(flagged.digest, status="ready")
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        module.ResearchCalibrationDriftAlertReport(
            **{**flagged.__dict__, "status": "review"},
        )


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: observation(settled_count=40),
            "settled_count must be exactly Decimal",
        ),
        (
            lambda: observation(baseline_brier_score=0.18),
            "baseline_brier_score must be exactly Decimal",
        ),
        (
            lambda: observation(current_brier_score=_DecimalSubclass("0.180000")),
            "current_brier_score must be exactly Decimal",
        ),
        (
            lambda: observation(current_expected_calibration_error=d("0.6000001")),
            "current_expected_calibration_error must use six decimal places or fewer",
        ),
        (
            lambda: config(min_settled_count=d("20.5")),
            "min_settled_count must be an integral Decimal",
        ),
        (
            lambda: build_report(
                observation(),
                generated_at=datetime(2026, 7, 8, 12, 0),
            ),
            "generated_at must be timezone-aware",
        ),
    ),
)
def test_decimal_and_type_validation_rejects_public_numeric_shortcuts(
    factory: Any,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()


def test_public_leak_rejection_blocks_sensitive_identifiers_and_payload_tampering() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public payload"):
        observation(cohort_key="candidate-alpha")
    with pytest.raises(ValueError, match="unsafe public payload"):
        observation(reason_codes=("source_url",))

    report = build_report(observation())
    payload = dict(report.payload)
    payload["market_id"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_calibration_drift_alert_report_payload(payload)

    row_payload = dict(report.payload)
    row_payload["rows"] = [dict(row_payload["rows"][0])]
    row_payload["rows"][0]["source_text"] = "hidden note"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_calibration_drift_alert_report_payload(row_payload)

    assert_public_payload_has_no_forbidden_surface(report.payload)
    assert "alpha" not in json.dumps(report.payload, sort_keys=True).lower()


def test_hard_flags_are_enforced_and_public_dataclasses_are_frozen() -> None:
    module = api()
    cfg = config()
    item = observation()
    report = build_report(item)
    row = report.rows[0]
    digest = report.digest

    for value in (cfg, item, row, digest, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(value)

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchCalibrationDriftAlertConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_payload_and_digest_are_deterministic_decimal_stringed_and_consistent() -> None:
    module = api()
    left = observation(cohort_key="left_pass")
    right = observation(
        cohort_key="right_watch",
        current_brier_score=d("0.225000"),
        current_expected_calibration_error=d("0.082000"),
    )

    report_a = build_report(right, left)
    report_b = build_report(left, right)
    payload = module.research_calibration_drift_alert_report_payload(report_a)
    digest_payload = module.research_calibration_drift_alert_digest_payload(report_a.digest)

    assert report_a.payload == report_b.payload
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert report_a.digest == report_b.digest
    assert payload["cohort_count"] == "2.000000"
    assert payload["rows"][0]["absolute_brier_score_delta"] == "0.020000"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["derived_validation_digest"] == report_a.derived_validation_digest
    assert payload["digest"] == digest_payload
    assert digest_payload["derived_validation_digest"] == report_a.digest.derived_validation_digest
    assert digest_payload["status"] == report_a.status
    assert digest_payload["cohort_count"] == payload["cohort_count"]
    assert_no_float_values(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    statuses = {report_a.status, report_a.digest.status}
    statuses.update(row.status for row in report_a.rows)
    assert statuses <= {"pass", "watch", "block"}


def test_report_and_digest_validation_rejects_tampering() -> None:
    module = api()
    report = build_report(
        observation(),
        observation(
            cohort_key="watch_cohort",
            current_brier_score=d("0.225000"),
            current_expected_calibration_error=d("0.082000"),
        ),
    )

    with pytest.raises(ValueError, match="pass_count must match rows"):
        replace(report, pass_count=d("0.000000"))
    with pytest.raises(ValueError, match="average_absolute_brier_score_delta must match rows"):
        replace(report, average_absolute_brier_score_delta=d("0.500000"))
    with pytest.raises(ValueError, match="digest must match report summary"):
        replace(report, digest=build_report().digest)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)

    payload = dict(report.payload)
    payload["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest must match payload fields"):
        module.research_calibration_drift_alert_report_payload(payload)

    digest_payload = dict(report.digest.payload)
    digest_payload["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest must match payload fields"):
        module.research_calibration_drift_alert_digest_payload(digest_payload)


def test_module_stays_readonly_without_network_wallet_or_execution_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sql",
        "subprocess",
        "urllib",
    )
    forbidden_call_fragments = (
        "connect",
        "delete",
        "execute",
        "insert",
        "open",
        "patch",
        "post",
        "put",
        "request",
        "send",
        "sign",
        "submit",
        "update",
        "write",
    )
    forbidden_attribute_fragments = (
        "private_key",
        "place_order",
        "submit_order",
        "wallet",
    )

    assert float_constants == []
    assert not any(
        fragment in imported.lower()
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(
        fragment in call.lower()
        for call in call_names
        for fragment in forbidden_call_fragments
    )
    assert not any(
        fragment in attribute.lower()
        for attribute in attribute_names
        for fragment in forbidden_attribute_fragments
    )
