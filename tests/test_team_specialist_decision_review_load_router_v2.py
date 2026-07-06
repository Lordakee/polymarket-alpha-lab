from __future__ import annotations

import ast
import importlib
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_decision_review_load_router_v2.py"
)
GENERATED_AT = datetime(2026, 2, 20, 15, 45, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_decision_review_load_router_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def category_route(category_id: str, specialist_team_id: str):
    module = api()
    return module.TeamSpecialistDecisionReviewLoadRouterV2CategoryRoute(
        category_id=category_id,
        specialist_team_id=specialist_team_id,
    )


def config(**overrides: object):
    module = api()
    values = {
        "category_routes": (
            category_route("macro.rates", "macro-review"),
            category_route("crypto.majors", "crypto-review"),
        ),
    }
    values.update(overrides)
    return module.TeamSpecialistDecisionReviewLoadRouterV2Config(**values)


def team_load(
    specialist_team_id: str = "macro-review",
    *,
    assigned: str = "1",
    capacity: str = "4",
):
    module = api()
    return module.TeamSpecialistDecisionReviewLoadRouterV2TeamLoad(
        specialist_team_id=specialist_team_id,
        assigned_review_count=d(assigned),
        capacity_review_count=d(capacity),
    )


def review(review_item_id: str = "review-macro-low", **overrides: object):
    module = api()
    values = {
        "review_item_id": review_item_id,
        "category_id": "macro.rates",
        "queued_at": GENERATED_AT - timedelta(minutes=45),
        "evidence_gap_score": d("0.100000"),
        "decision_uncertainty_score": d("0.100000"),
        "conflict_severity_score": d("0.050000"),
        "deadline_pressure_score": d("0.100000"),
        "urgent_review": False,
        "source_reference": "public:macro-review-case",
    }
    values.update(overrides)
    return module.TeamSpecialistDecisionReviewLoadRouterV2Review(**values)


def build_report(*items: object, cfg=None, loads=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_specialist_decision_review_load_router_v2_report(
        items,
        team_loads=loads
        or (
            team_load("macro-review", assigned="1", capacity="4"),
            team_load("crypto-review", assigned="4", capacity="3"),
        ),
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


def test_routes_decision_reviews_across_specialist_teams_with_overload_penalty() -> None:
    module = api()
    crypto_review = review(
        "review-crypto-overloaded",
        category_id="crypto.majors",
        queued_at=GENERATED_AT - timedelta(minutes=30),
        evidence_gap_score=d("0.600000"),
        decision_uncertainty_score=d("0.300000"),
        conflict_severity_score=d("0.400000"),
        deadline_pressure_score=d("0.200000"),
        source_reference="memory:crypto-review-case",
    )

    report = build_report(review(), crypto_review)

    assert is_dataclass(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.review_count == d("2")
    assert report.specialist_team_count == d("2")
    assert report.assignment_count == d("2")
    assert report.blocked_count == d("1")
    assert report.watch_count == d("0")
    assert report.pass_count == d("1")
    assert report.urgent_review_count == d("0")
    assert report.overloaded_team_count == d("1")
    assert report.max_team_load_ratio == d("1.333333")
    assert report.route_status == "blocked"
    assert report.reason_codes == (
        module.REPORT_BLOCKED_REASON,
        module.EVIDENCE_GAP_REASON,
        module.TEAM_LOAD_OVER_CAPACITY_REASON,
    )

    blocked, passed = report.assignments
    assert blocked.review_item_id == "review-crypto-overloaded"
    assert blocked.specialist_team_id == "crypto-review"
    assert blocked.team_load_ratio == d("1.333333")
    assert blocked.overload_penalty_score == d("0.300000")
    assert blocked.priority_score == d("0.695000")
    assert blocked.route_status == "blocked"
    assert blocked.reason_codes == (
        module.CATEGORY_ROUTE_MATCH_REASON,
        module.EVIDENCE_GAP_REASON,
        module.TEAM_LOAD_OVER_CAPACITY_REASON,
    )

    assert passed.review_item_id == "review-macro-low"
    assert passed.specialist_team_id == "macro-review"
    assert passed.base_priority_score == d("0.087500")
    assert passed.overload_penalty_score == d("0.000000")
    assert passed.priority_score == d("0.087500")
    assert passed.route_status == "pass"
    assert passed.reason_codes == (
        module.CATEGORY_ROUTE_MATCH_REASON,
        module.TEAM_LOAD_READY_REASON,
        module.DECISION_REVIEW_PASS_REASON,
    )


def test_urgent_review_priority_sorts_ahead_of_nonurgent_reviews() -> None:
    module = api()
    urgent = review(
        "review-urgent-deadline",
        queued_at=GENERATED_AT - timedelta(minutes=5),
        urgent_review=True,
        source_reference="public:urgent-review-case",
    )
    nonurgent = review(
        "review-nonurgent-evidence",
        queued_at=GENERATED_AT - timedelta(minutes=10),
        evidence_gap_score=d("0.500000"),
        decision_uncertainty_score=d("0.300000"),
        conflict_severity_score=d("0.200000"),
        deadline_pressure_score=d("0.125000"),
        source_reference="source:nonurgent-evidence-case",
    )

    report = build_report(
        urgent,
        nonurgent,
        loads=(team_load("macro-review", assigned="1", capacity="4"),),
    )

    first, second = report.assignments
    assert first.review_item_id == "review-urgent-deadline"
    assert first.urgent_review is True
    assert first.priority_score == d("0.337500")
    assert first.route_status == "watch"
    assert first.reason_codes == (
        module.CATEGORY_ROUTE_MATCH_REASON,
        module.TEAM_LOAD_READY_REASON,
        module.URGENT_REVIEW_REASON,
    )
    assert second.review_item_id == "review-nonurgent-evidence"
    assert second.urgent_review is False
    assert second.priority_score == d("0.300000")
    assert report.urgent_review_count == d("1")
    assert report.route_status == "watch"


def test_payload_serializes_decimal_strings_and_rejects_digest_tampering() -> None:
    module = api()
    report = build_report(
        review(),
        review(
            "review-crypto-overloaded",
            category_id="crypto.majors",
            evidence_gap_score=d("0.600000"),
            decision_uncertainty_score=d("0.300000"),
            conflict_severity_score=d("0.400000"),
            deadline_pressure_score=d("0.200000"),
            source_reference="memory:crypto-review-case",
        ),
    )

    payload = module.team_specialist_decision_review_load_router_v2_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["review_count"] == "2"
    assert payload["max_team_load_ratio"] == "1.333333"
    assert payload["assignments"][0]["priority_score"] == "0.695000"
    assert payload["assignments"][0]["team_load_ratio"] == "1.333333"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert module.validate_team_specialist_decision_review_load_router_v2_public_payload(
        payload,
    )
    assert_no_public_numeric_scalars(payload)

    assignment_tamper = deepcopy(payload)
    assignment_tamper["assignments"][0]["priority_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_team_specialist_decision_review_load_router_v2_public_payload(
            assignment_tamper,
        )

    report_tamper = deepcopy(payload)
    report_tamper["blocked_count"] = "0"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_team_specialist_decision_review_load_router_v2_public_payload(
            report_tamper,
        )

    missing_digest = deepcopy(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_team_specialist_decision_review_load_router_v2_public_payload(
            missing_digest,
        )


def test_frozen_dataclasses_decimal_only_flags_and_digest_revalidation() -> None:
    module = api()
    item = review()
    load = team_load()
    report = build_report(item, loads=(load,))
    assignment = report.assignments[0]
    cfg = config()

    for value in (item, load, assignment, report, cfg.category_routes[0], cfg):
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        for field in fields(value):
            field_value = getattr(value, field.name)
            if field.name in {
                "evidence_gap_score",
                "decision_uncertainty_score",
                "conflict_severity_score",
                "deadline_pressure_score",
                "assigned_review_count",
                "capacity_review_count",
                "base_priority_score",
                "overload_penalty_score",
                "priority_score",
                "team_load_ratio",
                "team_assigned_review_count",
                "team_capacity_review_count",
                "review_count",
                "specialist_team_count",
                "assignment_count",
                "blocked_count",
                "watch_count",
                "pass_count",
                "urgent_review_count",
                "overloaded_team_count",
                "average_priority_score",
                "max_team_load_ratio",
            }:
                assert type(field_value) is Decimal

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(assignment, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="evidence_gap_score must be a Decimal"):
        review(evidence_gap_score=0.1)
    with pytest.raises(ValueError, match="decision_uncertainty_score must be a Decimal"):
        review(decision_uncertainty_score=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="queued_at must be a datetime"):
        review(queued_at=_DatetimeSubclass(2026, 2, 20, tzinfo=UTC))
    with pytest.raises(ValueError, match="urgent_review must be a bool"):
        review(urgent_review=1)
    with pytest.raises(ValueError, match="paper_only must be True"):
        review(paper_only=False)

    tampered_config = config()
    object.__setattr__(tampered_config, "readonly", False)
    with pytest.raises(ValueError, match="readonly must be True"):
        build_report(review(), cfg=tampered_config)


def test_public_payload_rejects_unsafe_keys_values_and_module_has_no_io_surface() -> None:
    module = api()
    payload = module.team_specialist_decision_review_load_router_v2_payload(
        build_report(review()),
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
            module.validate_team_specialist_decision_review_load_router_v2_public_payload(
                unsafe_key_payload,
            )

        unsafe_value_payload = deepcopy(payload)
        unsafe_value_payload["assignments"][0]["redacted_source_reference"] = (
            f"contains {term} surface"
        )
        with pytest.raises(ValueError, match="unsafe public"):
            module.validate_team_specialist_decision_review_load_router_v2_public_payload(
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
