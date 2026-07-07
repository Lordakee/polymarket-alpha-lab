from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.research_settlement_monitoring_plan"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_settlement_monitoring_plan.py"
)
ALLOWED_PUBLIC_STATUSES = {"pass", "watch", "block"}
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
    "recommend",
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "watch_within_seconds": d("3600.000000"),
        "block_within_seconds": d("900.000000"),
        "rule_risk_watch_threshold": d("0.500000"),
        "rule_risk_block_threshold": d("0.850000"),
        "review_readiness_watch_below": d("0.750000"),
        "review_readiness_block_below": d("0.400000"),
    }
    values.update(overrides)
    return module.ResearchSettlementMonitoringConfig(**values)


def case(
    anonymous_case_label: str,
    *,
    settlement_seconds_from_now: int = 7200,
    anonymized_settlement_at: datetime | None = None,
    rule_risk_score: Decimal = d("0.100000"),
    review_readiness_score: Decimal = d("0.950000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    if anonymized_settlement_at is None:
        anonymized_settlement_at = GENERATED_AT + timedelta(
            seconds=settlement_seconds_from_now,
        )
    return module.ResearchSettlementMonitoringCandidate(
        anonymous_case_label=anonymous_case_label,
        anonymized_settlement_at=anonymized_settlement_at,
        rule_risk_score=rule_risk_score,
        review_readiness_score=review_readiness_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_plan(*cases: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_settlement_monitoring_plan(
        cases,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_pass_watch_block_rollup_priority_and_payload_are_deterministic() -> None:
    module = api()
    passing = case("anon_case_pass", settlement_seconds_from_now=14400)
    watching = case(
        "anon_case_watch",
        settlement_seconds_from_now=1800,
        rule_risk_score=d("0.600000"),
        review_readiness_score=d("0.700000"),
    )
    blocked = case(
        "anon_case_block",
        settlement_seconds_from_now=300,
        rule_risk_score=d("0.900000"),
        review_readiness_score=d("0.250000"),
    )

    plan = build_plan(passing, watching, blocked)

    assert type(plan) is module.ResearchSettlementMonitoringPlan
    assert plan.status == "block"
    assert plan.reason_codes == (
        "settlement_monitoring_window_block",
        "settlement_monitoring_rule_risk_block",
        "settlement_monitoring_review_readiness_block",
        "settlement_monitoring_window_watch",
        "settlement_monitoring_rule_risk_watch",
        "settlement_monitoring_review_readiness_watch",
    )
    assert plan.case_count == d("3.000000")
    assert plan.pass_count == d("1.000000")
    assert plan.watch_count == d("1.000000")
    assert plan.block_count == d("1.000000")
    assert plan.max_priority_score == d("2.816667")
    assert tuple(row.anonymous_case_label for row in plan.rows) == (
        "anon_case_block",
        "anon_case_watch",
        "anon_case_pass",
    )
    assert tuple(row.status for row in plan.rows) == ("block", "watch", "pass")
    assert tuple(row.manual_monitoring_priority for row in plan.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )

    payload = module.research_settlement_monitoring_plan_payload(plan)
    module.validate_research_settlement_monitoring_public_payload(payload)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["status"] == "block"
    assert payload["max_priority_score"] == "2.816667"
    assert payload["rows"][0]["status"] == "block"
    assert payload["rows"][0]["manual_monitoring_priority"] == "1.000000"
    _assert_public_statuses_only(payload)
    _assert_no_public_float_or_int(payload)
    _assert_no_forbidden_public_surface(payload)
    json.dumps(payload, sort_keys=True)

    shuffled_payload = module.research_settlement_monitoring_plan_payload(
        build_plan(blocked, passing, watching),
    )
    assert shuffled_payload == payload


def test_empty_plan_passes_without_non_public_statuses() -> None:
    module = api()
    plan = build_plan()

    assert plan.status == "pass"
    assert plan.reason_codes == ("settlement_monitoring_no_cases",)
    assert plan.case_count == d("0.000000")
    assert plan.rows == ()

    payload = module.research_settlement_monitoring_plan_payload(plan)
    assert payload["status"] == "pass"
    _assert_public_statuses_only(payload)


def test_frozen_dataclasses_exact_decimal_types_and_hard_flags() -> None:
    module = api()
    plan = build_plan(case("anon_case_pass"))

    for cls in (
        module.ResearchSettlementMonitoringConfig,
        module.ResearchSettlementMonitoringCandidate,
        module.ResearchSettlementMonitoringRow,
        module.ResearchSettlementMonitoringPlan,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        plan.status = "pass"  # type: ignore[misc]

    _assert_decimal_public_fields(plan)
    for row in plan.rows:
        _assert_decimal_public_fields(row)

    with pytest.raises(ValueError, match="watch_within_seconds"):
        config(watch_within_seconds=3600)
    with pytest.raises(ValueError, match="rule_risk_score"):
        case("anon_case_float", rule_risk_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="review_readiness_score"):
        case(
            "anon_case_decimal_subclass",
            review_readiness_score=_DecimalSubclass("0.500000"),
        )
    with pytest.raises(ValueError, match="anonymized_settlement_at must be timezone-aware"):
        case(
            "anon_case_naive",
            anonymized_settlement_at=datetime(2026, 7, 6, 13, 0),
        )
    with pytest.raises(ValueError, match="paper_only"):
        case("anon_case_flag", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(plan, readonly=False)


def test_datetime_normalization_and_threshold_validation() -> None:
    offset = timezone(timedelta(hours=-4))
    normalized = case(
        "anon_case_offset",
        anonymized_settlement_at=datetime(2026, 7, 6, 9, 0, tzinfo=offset),
    )

    assert normalized.anonymized_settlement_at == datetime(2026, 7, 6, 13, 0, tzinfo=UTC)
    assert build_plan(normalized).rows[0].seconds_to_settlement == d("3600.000000")

    with pytest.raises(ValueError, match="block_within_seconds"):
        config(block_within_seconds=d("3600.000000"))
    with pytest.raises(ValueError, match="rule_risk_watch_threshold"):
        config(rule_risk_watch_threshold=d("0.900000"))
    with pytest.raises(ValueError, match="review_readiness_watch_below"):
        config(review_readiness_watch_below=d("0.300000"))
    with pytest.raises(ValueError, match="rule_risk_score"):
        case("anon_case_bad_risk", rule_risk_score=d("1.100000"))
    with pytest.raises(ValueError, match="review_readiness_score"):
        case("anon_case_bad_readiness", review_readiness_score=d("-0.100000"))


def test_public_payload_rejects_leaky_keys_values_numerics_and_flag_downgrades() -> None:
    module = api()
    payload = module.research_settlement_monitoring_plan_payload(
        build_plan(case("anon_case_pass")),
    )

    module.validate_research_settlement_monitoring_public_payload(payload)

    for leaky_payload in (
        {**payload, "market_id": "abc"},
        {**payload, "candidate_id": "abc"},
        {**payload, "source_url": "https://example.invalid"},
        {**payload, "dsn": "postgres://example"},
        {**payload, "rows": [{**payload["rows"][0], "source_text": "official result"}]},
        {**payload, "rows": [{**payload["rows"][0], "audit_note": "wallet token"}]},
        {**payload, "rows": [{**payload["rows"][0], "audit_note": "buy this case"}]},
        {**payload, "rows": [{**payload["rows"][0], "audit_note": "sell this case"}]},
        {**payload, "rows": [{**payload["rows"][0], "audit_note": "recommendation"}]},
    ):
        with pytest.raises(ValueError):
            module.validate_research_settlement_monitoring_public_payload(leaky_payload)

    with pytest.raises(ValueError, match="Decimal-derived"):
        module.validate_research_settlement_monitoring_public_payload(
            {**payload, "case_count": 1},
        )
    with pytest.raises(ValueError, match="report_only"):
        module.validate_research_settlement_monitoring_public_payload(
            {**payload, "report_only": False},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_settlement_monitoring_public_payload(
            {**payload, "case_count": "9.000000"},
        )


def test_module_scope_is_report_only_readonly_and_external_io_free() -> None:
    module = api()

    assert set(module.__all__) == {
        "DEFAULT_RESEARCH_SETTLEMENT_MONITORING_PLAN_CONFIG_VERSION",
        "ResearchSettlementMonitoringConfig",
        "ResearchSettlementMonitoringCandidate",
        "ResearchSettlementMonitoringRow",
        "ResearchSettlementMonitoringPlan",
        "build_research_settlement_monitoring_plan",
        "research_settlement_monitoring_plan_payload",
        "validate_research_settlement_monitoring_public_payload",
    }

    tree = ast.parse(MODULE_PATH.read_text())
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    assigned_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
        elif isinstance(node, ast.Name):
            assigned_names.add(node.id)

    assert not imported_roots.intersection(
        {
            "requests",
            "urllib",
            "httpx",
            "socket",
            "websocket",
            "psycopg",
            "sqlite3",
            "sqlalchemy",
            "supabase",
            "subprocess",
        },
    )
    assert not called_names.intersection(
        {
            "open",
            "connect",
            "request",
            "post",
            "put",
            "patch",
            "delete",
            "execute",
            "commit",
            "rollback",
            "place_order",
            "submit_order",
            "cancel_order",
        },
    )
    assert not assigned_names.intersection(
        {
            "live_trading",
            "wallet",
            "auth",
            "order_client",
            "network_client",
            "database",
            "persistence",
            "dsn",
            "table",
        },
    )


def _assert_decimal_public_fields(value: Any) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal


def _assert_no_public_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_float_or_int(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_public_float_or_int(item)


def _assert_public_statuses_only(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status":
                assert item in ALLOWED_PUBLIC_STATUSES
            _assert_public_statuses_only(item)
    elif isinstance(value, list):
        for item in value:
            _assert_public_statuses_only(item)


def _assert_no_forbidden_public_surface(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(fragment in lowered_key for fragment in FORBIDDEN_PUBLIC_FRAGMENTS)
            _assert_no_forbidden_public_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_no_forbidden_public_surface(item)
        return
    if type(value) is str:
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in FORBIDDEN_PUBLIC_FRAGMENTS)
