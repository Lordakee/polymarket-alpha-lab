from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import importlib
import inspect
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_transaction_cost_threshold_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "research-strategy-transaction-cost-threshold-report-test",
        "watch_total_cost_threshold": d("0.030000"),
        "block_total_cost_threshold": d("0.080000"),
        "watch_component_cost_threshold": d("0.020000"),
        "block_component_cost_threshold": d("0.050000"),
    }
    values.update(overrides)
    return module.ResearchStrategyTransactionCostThresholdConfig(**values)


def review_input(**overrides: object) -> Any:
    module = api()
    values = {
        "review_label": "case-alpha",
        "spread_cost": d("0.001000"),
        "taker_fee_cost": d("0.002000"),
        "gas_friction_cost": d("0.001000"),
        "deposit_friction_cost": d("0.000000"),
        "settlement_friction_cost": d("0.000000"),
    }
    values.update(overrides)
    return module.ResearchStrategyTransactionCostThresholdInput(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_strategy_transaction_cost_threshold_report(
        items,
        config=cfg(),
        generated_at=generated_at,
    )


def assert_no_float_or_int(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int(item)
        return
    assert type(value) not in (float, int)


def unsafe_terms() -> tuple[str, ...]:
    return (
        "candidate_id",
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "https://example.invalid/ref",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "private_key",
        "buy",
        "sell",
        "recommend",
        "position_size",
    )


def test_report_summarizes_cost_thresholds_without_action_decisions() -> None:
    report = build_report(
        review_input(review_label="case-alpha"),
        review_input(
            review_label="case-beta",
            spread_cost=d("0.010000"),
            taker_fee_cost=d("0.012000"),
            gas_friction_cost=d("0.008000"),
            deposit_friction_cost=d("0.003000"),
            settlement_friction_cost=d("0.002000"),
        ),
        review_input(
            review_label="case-gamma",
            spread_cost=d("0.001000"),
            taker_fee_cost=d("0.001000"),
            gas_friction_cost=d("0.055000"),
            deposit_friction_cost=d("0.001000"),
            settlement_friction_cost=d("0.000000"),
        ),
    )

    rows = {row.review_label: row for row in report.rows}
    assert rows["case-alpha"].total_cost == d("0.004000")
    assert rows["case-alpha"].max_component_cost == d("0.002000")
    assert rows["case-alpha"].threshold_status == "pass"
    assert rows["case-alpha"].reason_codes == ("total_cost_pass",)

    assert rows["case-beta"].total_cost == d("0.035000")
    assert rows["case-beta"].threshold_status == "watch"
    assert "total_cost_watch" in rows["case-beta"].reason_codes
    assert "spread_cost_present" in rows["case-beta"].reason_codes
    assert "settlement_friction_present" in rows["case-beta"].reason_codes

    assert rows["case-gamma"].total_cost == d("0.058000")
    assert rows["case-gamma"].max_component_cost == d("0.055000")
    assert rows["case-gamma"].threshold_status == "block"
    assert rows["case-gamma"].reason_codes[:2] == (
        "component_cost_block",
        "total_cost_watch",
    )

    assert report.threshold_status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.max_total_cost == d("0.058000")
    assert report.average_total_cost == d("0.032333")

    for item in (cfg(), *report.rows, report):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            if field.name.endswith(("_cost", "_count", "_threshold", "_rank")):
                assert type(value) is Decimal


def test_payload_and_digest_are_canonical_and_deterministic() -> None:
    module = api()
    first = build_report(
        review_input(review_label="case-beta", spread_cost=d("0.030000")),
        review_input(review_label="case-alpha"),
    )
    second = build_report(
        review_input(review_label="case-alpha"),
        review_input(review_label="case-beta", spread_cost=d("0.030000")),
    )

    first_payload = module.research_strategy_transaction_cost_threshold_report_payload(first)
    second_payload = module.research_strategy_transaction_cost_threshold_report_payload(second)

    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["row_count"] == "2.000000"
    assert first_payload["rows"][0]["review_label"] == "case-alpha"
    assert first_payload["rows"][0]["total_cost"] == "0.004000"
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert module.validate_research_strategy_transaction_cost_threshold_report_payload(
        first_payload,
    )
    assert_no_float_or_int(first_payload)
    json.dumps(first_payload, sort_keys=True)


def test_dataclasses_are_frozen_strict_and_decimal_only() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_TRANSACTION_COST_THRESHOLD_CONFIG_VERSION",
        "ResearchStrategyTransactionCostThresholdConfig",
        "ResearchStrategyTransactionCostThresholdInput",
        "ResearchStrategyTransactionCostThresholdRow",
        "ResearchStrategyTransactionCostThresholdReport",
        "build_research_strategy_transaction_cost_threshold_report",
        "research_strategy_transaction_cost_threshold_report_payload",
        "validate_research_strategy_transaction_cost_threshold_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(review_input())
    with pytest.raises(FrozenInstanceError):
        report.rows[0].threshold_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.ResearchStrategyTransactionCostThresholdConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeInput(module.ResearchStrategyTransactionCostThresholdInput):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(module.ResearchStrategyTransactionCostThresholdRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.ResearchStrategyTransactionCostThresholdReport):
            pass

    with pytest.raises(ValueError, match="spread_cost must be a Decimal"):
        review_input(spread_cost=DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="taker_fee_cost must be a Decimal"):
        review_input(taker_fee_cost=1)


def test_hard_report_flags_are_enforced() -> None:
    module = api()
    with pytest.raises(ValueError, match="paper_only must be True"):
        review_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        cfg(readonly=False)

    report = build_report(review_input())
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)

    payload = module.research_strategy_transaction_cost_threshold_report_payload(report)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    flag_payload = dict(payload)
    flag_payload["report_only"] = False
    with pytest.raises(ValueError, match="payload report_only must be True"):
        module.validate_research_strategy_transaction_cost_threshold_report_payload(
            flag_payload,
        )


def test_digest_tampering_is_rejected_for_report_and_payload() -> None:
    module = api()
    report = build_report(review_input())

    with pytest.raises(ValueError, match="average_total_cost"):
        replace(report, average_total_cost=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = module.research_strategy_transaction_cost_threshold_report_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_strategy_transaction_cost_threshold_report_payload(
            tampered_payload,
        )

    object.__setattr__(report.rows[0], "total_cost", d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_transaction_cost_threshold_report_payload(report)


def test_unsafe_identifiers_sources_storage_and_execution_surfaces_are_rejected() -> None:
    module = api()

    for term in unsafe_terms():
        with pytest.raises(ValueError, match="unsafe public surface"):
            review_input(review_label=f"case-{term}")

    payload = module.research_strategy_transaction_cost_threshold_report_payload(
        build_report(review_input()),
    )
    for key in (
        "candidate_id",
        "market_slug",
        "question",
        "source_url",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "private_key",
    ):
        unsafe_payload = dict(payload)
        unsafe_payload[key] = "forbidden"
        with pytest.raises(ValueError, match="unsafe public surface"):
            module.validate_research_strategy_transaction_cost_threshold_report_payload(
                unsafe_payload,
            )

    numeric_payload = dict(payload)
    numeric_payload["row_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        module.validate_research_strategy_transaction_cost_threshold_report_payload(
            numeric_payload,
        )


def test_module_exposes_no_storage_network_or_execution_surface() -> None:
    module = api()
    public_names = set(module.__all__) | {
        name for name in dir(module) if not name.startswith("_")
    }
    for public_name in public_names:
        lower_name = public_name.lower()
        for term in unsafe_terms():
            assert term.replace("_", "") not in lower_name.replace("_", "")

    source = inspect.getsource(module)
    for forbidden in (
        "requests",
        "urllib",
        "http.client",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "subprocess",
        "Path(",
        "open(",
        ".write(",
        ".read(",
        "recommendation",
        "position_size",
    ):
        assert forbidden not in source
