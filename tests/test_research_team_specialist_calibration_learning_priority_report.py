from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_team_specialist_calibration_learning_priority_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_team_specialist_calibration_learning_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            "research-team-specialist-calibration-learning-priority-report-v0"
        ),
        "recent_miss_severity_weight": d("0.300000"),
        "calibration_age_weight": d("0.200000"),
        "feedback_absorption_weight": d("0.200000"),
        "evidence_reuse_quality_weight": d("0.150000"),
        "review_backlog_pressure_weight": d("0.150000"),
        "watch_priority_score_floor": d("0.300000"),
        "block_priority_score_floor": d("0.600000"),
        "watch_recent_miss_severity": d("0.150000"),
        "block_recent_miss_severity": d("0.350000"),
        "max_pass_calibration_age_days": d("14"),
        "max_watch_calibration_age_days": d("45"),
        "min_pass_feedback_absorption_ratio": d("0.850000"),
        "min_watch_feedback_absorption_ratio": d("0.650000"),
        "min_pass_evidence_reuse_quality": d("0.800000"),
        "min_watch_evidence_reuse_quality": d("0.600000"),
        "max_pass_review_backlog_pressure": d("0.400000"),
        "max_watch_review_backlog_pressure": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistCalibrationLearningPriorityConfig(**values)


def learning_signal(**overrides: object):
    module = api()
    values = {
        "specialist_key": "sports_models",
        "learning_track": "sports_calibration",
        "recent_miss_severity": d("0.050000"),
        "calibration_age_days": d("7"),
        "feedback_absorption_ratio": d("0.950000"),
        "evidence_reuse_quality": d("0.900000"),
        "review_backlog_pressure": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistCalibrationLearningPriorityInput(**values)


def build_report(*items: object, cfg=None):
    module = api()
    return module.build_research_team_specialist_calibration_learning_priority_report(
        items,
        config=cfg or config(),
    )


def assert_no_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)


def assert_public_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "raw",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "http://",
        "https://",
        "source_url",
        "source_text",
        "dsn",
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
    if isinstance(value, list):
        for item in value:
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def assert_decimal_public_fields(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if field.name in {"paper_only", "report_only", "readonly"}:
            assert item is True
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
        if field.name.endswith(("_count", "_ratio", "_score", "_severity", "_days")):
            assert type(item) is Decimal


def test_learning_priority_scores_and_bands_pass_watch_block_rows() -> None:
    report = build_report(
        learning_signal(specialist_key="sports_models", learning_track="sports_calibration"),
        learning_signal(
            specialist_key="macro_models",
            learning_track="macro_calibration",
            recent_miss_severity=d("0.600000"),
            calibration_age_days=d("60"),
            feedback_absorption_ratio=d("0.300000"),
            evidence_reuse_quality=d("0.250000"),
            review_backlog_pressure=d("0.900000"),
        ),
        learning_signal(
            specialist_key="crypto_models",
            learning_track="crypto_calibration",
            recent_miss_severity=d("0.200000"),
            calibration_age_days=d("30"),
            feedback_absorption_ratio=d("0.800000"),
            evidence_reuse_quality=d("0.700000"),
            review_backlog_pressure=d("0.550000"),
        ),
    )

    assert is_dataclass(report)
    assert report.config_version == (
        "research-team-specialist-calibration-learning-priority-report-v0"
    )
    assert report.status == "block"
    assert report.specialist_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.learning_priority_team_count == d("2")
    assert report.average_learning_priority_score == d("0.409815")
    assert report.max_learning_priority_score == d("0.767500")
    assert report.min_learning_priority_score == d("0.101111")
    assert report.average_recent_miss_severity == d("0.283333")
    assert report.max_calibration_age_days == d("60")
    assert report.min_feedback_absorption_ratio == d("0.300000")
    assert report.min_evidence_reuse_quality == d("0.250000")
    assert report.max_review_backlog_pressure == d("0.900000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked, watched, passed = report.rows
    assert tuple((row.status, row.learning_track) for row in report.rows) == (
        ("block", "macro_calibration"),
        ("watch", "crypto_calibration"),
        ("pass", "sports_calibration"),
    )
    assert blocked.learning_priority_score == d("0.767500")
    assert blocked.calibration_age_pressure_score == d("1.000000")
    assert blocked.feedback_gap_score == d("0.700000")
    assert blocked.evidence_gap_score == d("0.750000")
    assert blocked.reason_codes == (
        "specialist_learning_recent_miss_block",
        "specialist_learning_calibration_age_block",
        "specialist_learning_feedback_absorption_block",
        "specialist_learning_evidence_reuse_block",
        "specialist_learning_review_backlog_block",
    )
    assert watched.learning_priority_score == d("0.360833")
    assert watched.reason_codes == (
        "specialist_learning_recent_miss_watch",
        "specialist_learning_calibration_age_watch",
        "specialist_learning_feedback_absorption_watch",
        "specialist_learning_evidence_reuse_watch",
        "specialist_learning_review_backlog_watch",
    )
    assert passed.learning_priority_score == d("0.101111")
    assert passed.reason_codes == ("specialist_calibration_learning_priority_clear",)
    assert report.reason_codes[:2] == (
        "specialist_calibration_learning_priority_report_block",
        "specialist_learning_recent_miss_block",
    )
    assert len(report.derived_validation_digest) == 64


def test_calibration_thresholds_and_empty_reports_block() -> None:
    module = api()
    empty = build_report()

    assert empty.status == "block"
    assert empty.specialist_count == d("0")
    assert empty.rows == ()
    assert empty.reason_codes == ("specialist_calibration_learning_priority_no_rows",)
    assert empty.reason_code_counts == (
        module.ResearchTeamSpecialistCalibrationLearningPriorityReasonCodeCount(
            reason_code="specialist_calibration_learning_priority_no_rows",
            count=d("1"),
            specialist_ratio=d("1.000000"),
        ),
    )

    aged_watch = build_report(learning_signal(calibration_age_days=d("15"))).rows[0]
    assert aged_watch.status == "watch"
    assert aged_watch.reason_codes == ("specialist_learning_calibration_age_watch",)

    aged_block = build_report(learning_signal(calibration_age_days=d("46"))).rows[0]
    assert aged_block.status == "block"
    assert aged_block.reason_codes == ("specialist_learning_calibration_age_block",)

    custom = config(
        max_pass_calibration_age_days=d("7"),
        max_watch_calibration_age_days=d("21"),
        watch_priority_score_floor=d("0.200000"),
        block_priority_score_floor=d("0.500000"),
    )
    custom_row = build_report(
        learning_signal(calibration_age_days=d("22")),
        cfg=custom,
    ).rows[0]
    assert custom_row.status == "block"


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    module = api()
    left = learning_signal(specialist_key="sports_models", learning_track="sports_calibration")
    right = learning_signal(
        specialist_key="crypto_models",
        learning_track="crypto_calibration",
        recent_miss_severity=d("0.200000"),
        calibration_age_days=d("30"),
        feedback_absorption_ratio=d("0.800000"),
        evidence_reuse_quality=d("0.700000"),
        review_backlog_pressure=d("0.550000"),
    )

    report_a = build_report(right, left)
    report_b = build_report(left, right)
    payload = (
        module.research_team_specialist_calibration_learning_priority_report_public_payload(
            report_a,
        )
    )

    assert payload == (
        module.research_team_specialist_calibration_learning_priority_report_public_payload(
            report_b,
        )
    )
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert payload["specialist_count"] == "2"
    assert payload["average_learning_priority_score"] == "0.230972"
    assert payload["rows"][0]["learning_priority_score"] == "0.360833"
    assert payload["rows"][0]["specialist_digest"].startswith("sha256:")
    public_json = json.dumps(payload, sort_keys=True)
    assert "specialist_key" not in public_json
    assert "sports_models" not in public_json
    assert "crypto_models" not in public_json
    assert "learning_track" not in public_json
    assert "sports_calibration" not in public_json
    assert payload["derived_validation_digest"] == report_a.derived_validation_digest
    assert_no_public_numeric_values(payload)
    assert_public_payload_has_no_forbidden_surface(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest does not match"):
        module.research_team_specialist_calibration_learning_priority_report_public_payload(
            tampered,
        )

    unsafe = dict(payload)
    unsafe["source_url"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_specialist_calibration_learning_priority_report_public_payload(
            unsafe,
        )


def test_validates_config_decimal_flags_frozen_and_leak_surfaces() -> None:
    module = api()
    cfg = config()
    item = learning_signal()
    report = build_report(item)

    for value in (cfg, item, report.rows[0], report.reason_code_counts[0], report):
        assert_decimal_public_fields(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="recent_miss_severity must be a Decimal"):
        learning_signal(recent_miss_severity=0.1)
    with pytest.raises(ValueError, match="review_backlog_pressure must be a Decimal"):
        learning_signal(review_backlog_pressure=_DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="calibration_age_days must be integral"):
        learning_signal(calibration_age_days=d("1.5"))
    with pytest.raises(ValueError, match="weights must sum to 1.000000"):
        config(recent_miss_severity_weight=d("0.310000"))
    with pytest.raises(ValueError, match="block_priority_score_floor"):
        config(watch_priority_score_floor=d("0.700000"))
    with pytest.raises(ValueError, match="max_watch_calibration_age_days"):
        config(max_pass_calibration_age_days=d("46"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchTeamSpecialistCalibrationLearningPriorityConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        replace(report.rows[0], status="review")
    with pytest.raises(ValueError, match="unsafe public"):
        learning_signal(specialist_key="market_alpha")
    with pytest.raises(ValueError, match="unsafe public"):
        learning_signal(learning_track="question_review")


def test_module_stays_report_only_without_live_or_storage_surface() -> None:
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
