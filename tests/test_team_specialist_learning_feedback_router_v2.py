from __future__ import annotations

import ast
import importlib
from copy import deepcopy
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
    / "team_specialist_learning_feedback_router_v2.py"
)
GENERATED_AT = datetime(2026, 1, 15, 16, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_learning_feedback_router_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def route(domain: str, team: str):
    module = api()
    return module.TeamSpecialistLearningFeedbackRouterV2DomainRoute(
        domain=domain,
        specialist_team_id=team,
    )


def config(**overrides: object):
    module = api()
    values = {
        "domain_routes": (
            route("macro.rates", "macro-rates-learning"),
            route("crypto.majors", "crypto-majors-learning"),
        ),
    }
    values.update(overrides)
    return module.TeamSpecialistLearningFeedbackRouterV2Config(**values)


def feedback(feedback_id: str = "feedback-macro-calibration", **overrides: object):
    module = api()
    values = {
        "feedback_id": feedback_id,
        "domain": "macro.rates",
        "observed_at": GENERATED_AT - timedelta(hours=2),
        "calibration_gap": d("0.200000"),
        "source_quality_failure_score": d("0.000000"),
        "resolution_rule_miss_score": d("0.000000"),
        "forecast_error_severity": d("0.850000"),
        "stale_playbook_risk": d("0.100000"),
        "unresolved_postmortem_pressure": d("0.000000"),
        "source_reference": "public:macro-calibration-feedback",
    }
    values.update(overrides)
    return module.TeamSpecialistLearningFeedbackRouterV2Feedback(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_specialist_learning_feedback_router_v2_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_scalars(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"public numeric scalar must be serialized as a string: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_public_numeric_scalars(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            assert_no_public_numeric_scalars(child)


def test_routes_feedback_by_domain_and_learning_pressure_dimensions() -> None:
    module = api()
    crypto_feedback = feedback(
        "feedback-crypto-quality",
        domain="crypto.majors",
        calibration_gap=d("0.000000"),
        source_quality_failure_score=d("0.350000"),
        resolution_rule_miss_score=d("0.250000"),
        forecast_error_severity=d("0.300000"),
        stale_playbook_risk=d("0.450000"),
        unresolved_postmortem_pressure=d("0.600000"),
        source_reference="memory:crypto-source-quality-feedback",
    )

    report = build_report(feedback(), crypto_feedback)

    assert is_dataclass(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.feedback_count == d("2")
    assert report.specialist_team_count == d("2")
    assert report.assignment_count == d("2")
    assert report.blocked_count == d("1")
    assert report.watch_count == d("1")
    assert report.pass_count == d("0")
    assert report.average_priority_score == d("0.281250")
    assert report.route_status == "blocked"
    assert report.reason_codes == (
        module.REPORT_BLOCKED_REASON,
        module.CALIBRATION_GAP_REASON,
        module.SOURCE_QUALITY_FAILURE_REASON,
        module.RESOLUTION_RULE_MISS_REASON,
        module.FORECAST_ERROR_SEVERE_REASON,
        module.FORECAST_ERROR_WATCH_REASON,
        module.STALE_PLAYBOOK_RISK_REASON,
        module.UNRESOLVED_POSTMORTEM_PRESSURE_REASON,
    )

    blocked, watch = report.assignments
    assert blocked.feedback_id == "feedback-macro-calibration"
    assert blocked.specialist_team_id == "macro-rates-learning"
    assert blocked.priority_score == d("0.262500")
    assert blocked.route_status == "blocked"
    assert blocked.reason_codes == (
        module.DOMAIN_ROUTE_MATCH_REASON,
        module.CALIBRATION_GAP_REASON,
        module.FORECAST_ERROR_SEVERE_REASON,
    )
    assert watch.feedback_id == "feedback-crypto-quality"
    assert watch.specialist_team_id == "crypto-majors-learning"
    assert watch.priority_score == d("0.300000")
    assert watch.route_status == "watch"
    assert watch.reason_codes == (
        module.DOMAIN_ROUTE_MATCH_REASON,
        module.SOURCE_QUALITY_FAILURE_REASON,
        module.RESOLUTION_RULE_MISS_REASON,
        module.FORECAST_ERROR_WATCH_REASON,
        module.STALE_PLAYBOOK_RISK_REASON,
        module.UNRESOLVED_POSTMORTEM_PRESSURE_REASON,
    )


def test_payload_serializes_decimal_strings_flags_and_rejects_tampering() -> None:
    module = api()
    report = build_report(
        feedback(),
        feedback(
            "feedback-crypto-quality",
            domain="crypto.majors",
            calibration_gap=d("0.000000"),
            source_quality_failure_score=d("0.350000"),
            resolution_rule_miss_score=d("0.250000"),
            forecast_error_severity=d("0.300000"),
            stale_playbook_risk=d("0.450000"),
            unresolved_postmortem_pressure=d("0.600000"),
            source_reference="memory:crypto-source-quality-feedback",
        ),
    )

    payload = module.team_specialist_learning_feedback_router_v2_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["feedback_count"] == "2"
    assert payload["average_priority_score"] == "0.281250"
    assert payload["assignments"][0]["priority_score"] == "0.262500"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert module.validate_team_specialist_learning_feedback_router_v2_public_payload(
        payload,
    )
    assert_no_public_numeric_scalars(payload)

    tampered = deepcopy(payload)
    tampered["assignments"][0]["priority_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_team_specialist_learning_feedback_router_v2_public_payload(
            tampered,
        )

    missing_digest = deepcopy(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_team_specialist_learning_feedback_router_v2_public_payload(
            missing_digest,
        )


def test_frozen_dataclasses_exact_decimal_flags_and_digest_revalidation() -> None:
    module = api()
    item = feedback()
    report = build_report(item)
    assignment = report.assignments[0]

    for value in (item, assignment, report, config().domain_routes[0], config()):
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        for field in fields(value):
            field_value = getattr(value, field.name)
            if field.name.endswith("_score") or field.name in {
                "calibration_gap",
                "source_quality_failure_score",
                "resolution_rule_miss_score",
                "forecast_error_severity",
                "stale_playbook_risk",
                "unresolved_postmortem_pressure",
                "feedback_count",
                "specialist_team_count",
                "assignment_count",
                "blocked_count",
                "watch_count",
                "pass_count",
                "average_priority_score",
            }:
                assert type(field_value) is Decimal

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(assignment, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="calibration_gap must be a Decimal"):
        feedback(calibration_gap=0.2)
    with pytest.raises(ValueError, match="source_quality_failure_score must be a Decimal"):
        feedback(source_quality_failure_score=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        feedback(observed_at=_DatetimeSubclass(2026, 1, 15, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only must be True"):
        feedback(paper_only=False)

    tampered_config = config()
    object.__setattr__(tampered_config, "readonly", False)
    with pytest.raises(ValueError, match="readonly must be True"):
        build_report(feedback(), cfg=tampered_config)


def test_public_payload_rejects_unsafe_keys_values_and_module_has_no_io_surface() -> None:
    module = api()
    payload = module.team_specialist_learning_feedback_router_v2_payload(
        build_report(feedback()),
    )

    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_terms:
        unsafe_key_payload = deepcopy(payload)
        unsafe_key_payload[f"{term}_surface"] = "blocked"
        with pytest.raises(ValueError, match="unsafe public"):
            module.validate_team_specialist_learning_feedback_router_v2_public_payload(
                unsafe_key_payload,
            )

        unsafe_value_payload = deepcopy(payload)
        unsafe_value_payload["assignments"][0]["redacted_source_reference"] = (
            f"contains {term} surface"
        )
        with pytest.raises(ValueError, match="unsafe public"):
            module.validate_team_specialist_learning_feedback_router_v2_public_payload(
                unsafe_value_payload,
            )

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
        "order",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
