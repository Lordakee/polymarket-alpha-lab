from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_event_category_risk_budget_allocator_v2"
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 9, 30, tzinfo=UTC)


class DerivedDatetime(datetime):
    pass


class DerivedDecimal(Decimal):
    pass


class NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def module() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    allocator_module = module()
    values = {
        "config_version": "event-category-risk-budget-allocator-v2-test",
        "total_paper_risk_budget": d("1000.000000"),
        "watch_allocation_score_threshold": d("0.400000"),
        "block_allocation_score_threshold": d("0.150000"),
        "hard_risk_score_threshold": d("0.850000"),
    }
    values.update(overrides)
    return allocator_module.StrategyEventCategoryRiskBudgetAllocatorV2Config(**values)


def signal(**overrides: object) -> Any:
    allocator_module = module()
    values = {
        "event_category": "sports",
        "observed_at": OBSERVED_AT,
        "calibration_score": d("0.900000"),
        "liquidity_score": d("0.800000"),
        "correlation_risk_score": d("0.100000"),
        "settlement_cluster_risk_score": d("0.200000"),
        "resolution_risk_score": d("0.100000"),
        "information_quality_score": d("0.700000"),
        "reason_codes": ("category_signal_reviewed",),
    }
    values.update(overrides)
    return allocator_module.StrategyEventCategoryRiskBudgetAllocatorV2Signal(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    allocator_module = module()
    return allocator_module.build_strategy_event_category_risk_budget_allocator_v2_report(
        items,
        config=cfg(),
        generated_at=generated_at,
    )


def test_builds_readonly_paper_budget_report_with_risk_adjusted_allocations() -> None:
    allocator_module = module()
    report = build_report(
        signal(event_category="sports"),
        signal(
            event_category="macro",
            calibration_score=d("0.700000"),
            liquidity_score=d("0.500000"),
            correlation_risk_score=d("0.300000"),
            settlement_cluster_risk_score=d("0.400000"),
            resolution_risk_score=d("0.200000"),
            information_quality_score=d("0.600000"),
        ),
        signal(
            event_category="politics",
            calibration_score=d("0.400000"),
            liquidity_score=d("0.300000"),
            correlation_risk_score=d("0.900000"),
            settlement_cluster_risk_score=d("0.600000"),
            resolution_risk_score=d("0.700000"),
            information_quality_score=d("0.200000"),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "event-category-risk-budget-allocator-v2-test"
    assert report.input_count == d("3.000000")
    assert report.category_count == d("3.000000")
    assert report.allocated_category_count == d("2.000000")
    assert report.blocked_category_count == d("1.000000")
    assert report.watch_category_count == d("0.000000")
    assert report.pass_category_count == d("2.000000")
    assert report.total_paper_risk_budget == d("1000.000000")
    assert report.allocated_paper_risk_budget == d("1000.000000")
    assert report.unallocated_paper_risk_budget == d("0.000000")
    assert report.reason_codes == (
        "category_hard_risk_limit_breached",
        "category_risk_budget_blocked",
    )
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.event_category for row in report.rows) == (
        "sports",
        "macro",
        "politics",
    )
    sports, macro, politics = report.rows
    assert sports.positive_signal_score == d("0.800000")
    assert sports.risk_pressure_score == d("0.130000")
    assert sports.allocation_score == d("0.696000")
    assert sports.paper_risk_budget == d("621.706119")
    assert sports.allocation_status == "pass"
    assert sports.reason_codes == ("category_risk_budget_allocated",)

    assert macro.positive_signal_score == d("0.605000")
    assert macro.risk_pressure_score == d("0.300000")
    assert macro.allocation_score == d("0.423500")
    assert macro.paper_risk_budget == d("378.293881")
    assert macro.allocation_status == "pass"

    assert politics.allocation_score == d("0.075000")
    assert politics.allocation_weight == d("0.000000")
    assert politics.paper_risk_budget == d("0.000000")
    assert politics.allocation_status == "blocked"
    assert politics.reason_codes == (
        "category_hard_risk_limit_breached",
        "category_risk_budget_blocked",
    )

    payload = allocator_module.strategy_event_category_risk_budget_allocator_v2_payload(report)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["total_paper_risk_budget"] == "1000.000000"
    assert payload["allocated_paper_risk_budget"] == "1000.000000"
    assert payload["rows"][0]["allocation_score"] == "0.696000"
    assert payload["rows"][0]["paper_risk_budget"] == "621.706119"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert allocator_module.validate_strategy_event_category_risk_budget_allocator_v2_payload(payload)
    assert_no_public_numeric(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_empty_and_all_blocked_inputs_are_deterministic_readonly_reports() -> None:
    empty = build_report()
    assert empty.input_count == d("0.000000")
    assert empty.category_count == d("0.000000")
    assert empty.allocated_paper_risk_budget == d("0.000000")
    assert empty.unallocated_paper_risk_budget == d("1000.000000")
    assert empty.reason_codes == ("category_risk_budget_allocator_empty",)
    assert empty.rows == ()

    blocked = build_report(
        signal(event_category="alpha", correlation_risk_score=d("0.950000")),
        signal(event_category="beta", resolution_risk_score=d("0.950000")),
    )
    assert blocked.input_count == d("2.000000")
    assert blocked.allocated_category_count == d("0.000000")
    assert blocked.blocked_category_count == d("2.000000")
    assert blocked.allocated_paper_risk_budget == d("0.000000")
    assert blocked.unallocated_paper_risk_budget == d("1000.000000")
    assert blocked.reason_codes == (
        "category_hard_risk_limit_breached",
        "category_risk_budget_blocked",
    )
    assert tuple(row.event_category for row in blocked.rows) == ("alpha", "beta")


def test_datetimes_normalize_to_utc_and_payload_uses_decimal_strings() -> None:
    eastern = timezone(timedelta(hours=-4))
    report = build_report(
        signal(
            event_category="time-zone-case",
            observed_at=datetime(2026, 7, 6, 7, 30, tzinfo=eastern),
        ),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=eastern),
    )

    row = report.rows[0]
    assert row.observed_at == datetime(2026, 7, 6, 11, 30, tzinfo=UTC)
    assert report.generated_at == datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
    assert row.signal_age_seconds == d("1800.000000")

    payload = module().strategy_event_category_risk_budget_allocator_v2_payload(report)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["observed_at"] == "2026-07-06T11:30:00+00:00"
    assert payload["rows"][0]["signal_age_seconds"] == "1800.000000"
    assert_no_public_numeric(payload)


def test_dataclasses_are_frozen_decimal_only_and_reject_subclassing() -> None:
    allocator_module = module()

    assert allocator_module.__all__ == (
        "DEFAULT_STRATEGY_EVENT_CATEGORY_RISK_BUDGET_ALLOCATOR_V2_CONFIG_VERSION",
        "StrategyEventCategoryRiskBudgetAllocatorV2Config",
        "StrategyEventCategoryRiskBudgetAllocatorV2Signal",
        "StrategyEventCategoryRiskBudgetAllocatorV2Row",
        "StrategyEventCategoryRiskBudgetAllocatorV2Report",
        "build_strategy_event_category_risk_budget_allocator_v2_report",
        "strategy_event_category_risk_budget_allocator_v2_payload",
        "validate_strategy_event_category_risk_budget_allocator_v2_payload",
    )
    for exported_name in allocator_module.__all__:
        value = getattr(allocator_module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(signal())
    for item in (cfg(), signal(), report, *report.rows):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            if (
                field.name.endswith("_budget")
                or field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_score")
                or field.name.endswith("_seconds")
                or field.name == "allocation_weight"
            ):
                assert value is None or type(value) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].allocation_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="calibration_score must be a Decimal"):
        signal(calibration_score=1)
    with pytest.raises(ValueError, match="total_paper_risk_budget must be a Decimal"):
        cfg(total_paper_risk_budget=DerivedDecimal("1000.000000"))
    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(allocator_module.StrategyEventCategoryRiskBudgetAllocatorV2Config):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeSignal(allocator_module.StrategyEventCategoryRiskBudgetAllocatorV2Signal):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(allocator_module.StrategyEventCategoryRiskBudgetAllocatorV2Row):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(allocator_module.StrategyEventCategoryRiskBudgetAllocatorV2Report):
            pass


def test_validation_rejects_bad_inputs_sequences_and_false_hard_flags() -> None:
    allocator_module = module()

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        allocator_module.build_strategy_event_category_risk_budget_allocator_v2_report(
            (),
            config=cfg(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        allocator_module.build_strategy_event_category_risk_budget_allocator_v2_report(
            (),
            config=cfg(),
            generated_at=DerivedDatetime(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 6, 9, 30))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 6, 9, 30, tzinfo=NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="calibration_score must be at most one"):
        signal(calibration_score=d("1.000001"))
    with pytest.raises(ValueError, match="reason_codes"):
        signal(reason_codes=("dup", "dup"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        cfg(readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        build_report(signal(observed_at=datetime(2026, 7, 6, 13, 0, tzinfo=UTC)))
    with pytest.raises(ValueError, match="signals"):
        allocator_module.build_strategy_event_category_risk_budget_allocator_v2_report(
            "bad",
            config=cfg(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="duplicate event_category"):
        build_report(signal(event_category="sports"), signal(event_category="sports"))


def test_report_consistency_and_digest_are_tamper_evident() -> None:
    allocator_module = module()
    report = build_report(signal())

    with pytest.raises(ValueError, match="category_count"):
        replace(report, category_count=d("2.000000"))
    with pytest.raises(ValueError, match="allocated_paper_risk_budget"):
        replace(report, allocated_paper_risk_budget=d("999.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=(report.rows[0], report.rows[0]))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = allocator_module.strategy_event_category_risk_budget_allocator_v2_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["allocated_category_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        allocator_module.validate_strategy_event_category_risk_budget_allocator_v2_payload(
            tampered_payload,
        )

    object.__setattr__(report.rows[0], "event_category", "mutated-category")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        allocator_module.strategy_event_category_risk_budget_allocator_v2_payload(report)


def test_unsafe_public_surface_values_and_payload_keys_are_rejected() -> None:
    allocator_module = module()
    unsafe_terms = (
        "".join(("li", "ve")),
        "".join(("au", "th")),
        "".join(("wall", "et")),
        "".join(("or", "der")),
        "".join(("net", "work")),
        "".join(("data", "base")),
        "".join(("per", "sist")),
        "".join(("sign", "ing")),
        "".join(("muta", "tion")),
        "".join(("b", "uy")),
        "".join(("s", "ell")),
        "".join(("tr", "ade")),
    )

    for unsafe_term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public surface"):
            signal(event_category=f"category-{unsafe_term}")

    report = build_report(signal())
    payload = allocator_module.strategy_event_category_risk_budget_allocator_v2_payload(report)

    unsafe_payload = dict(payload)
    unsafe_payload["".join(("wall", "et"))] = "forbidden"
    with pytest.raises(ValueError, match="unsafe public surface"):
        allocator_module.validate_strategy_event_category_risk_budget_allocator_v2_payload(
            unsafe_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["reason_codes"] = ["".join(("li", "ve"))]
    with pytest.raises(ValueError, match="unsafe public surface"):
        allocator_module.validate_strategy_event_category_risk_budget_allocator_v2_payload(
            unsafe_value_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["allocated_category_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        allocator_module.validate_strategy_event_category_risk_budget_allocator_v2_payload(
            numeric_payload,
        )


def test_module_omits_runtime_financial_action_and_storage_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_event_category_risk_budget_allocator_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "sqlalchemy",
        "private_key",
        "account",
        "broker",
        "submit",
        "cancel",
        "advice",
        "socket",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def assert_no_public_numeric(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("payload must not contain floats")
    if type(value) is int:
        raise AssertionError("payload numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numeric(item)
