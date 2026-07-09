from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 18, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 17, 45, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab."
        "research_market_probability_exit_cost_tail_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def sample(reference: str, **overrides: object) -> Any:
    module = api()
    values = {
        "private_research_reference": reference,
        "observed_at": OBSERVED_AT,
        "model_probability": d("0.650000"),
        "market_probability": d("0.560000"),
        "expected_exit_cost_rate": d("0.015000"),
        "tail_exit_cost_rate": d("0.010000"),
        "probability_tail_risk_rate": d("0.040000"),
        "cost_uncertainty_buffer_rate": d("0.004000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchMarketProbabilityExitCostTailInput(**values)


def build_report(*inputs: object, config: object | None = None) -> Any:
    module = api()
    return module.build_research_market_probability_exit_cost_tail_report(
        inputs,
        generated_at=GENERATED_AT,
        config=config,
    )


def walk_json(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_json(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from walk_json(item)
        return
    yield value


def test_exit_cost_tail_scores_sorts_and_summarizes_pass_watch_block() -> None:
    module = api()
    passed = sample(
        "candidate-pass market_id=mid market_slug=slug question https://example.invalid",
    )
    watched = sample(
        "candidate-watch source_text source_url=https://example.invalid/a",
        model_probability=d("0.650000"),
        market_probability=d("0.590000"),
        expected_exit_cost_rate=d("0.022000"),
        tail_exit_cost_rate=d("0.014000"),
        probability_tail_risk_rate=d("0.120000"),
        cost_uncertainty_buffer_rate=d("0.004000"),
    )
    blocked = sample(
        "candidate-block dsn=postgres table_name=markets token=secret wallet order trade",
        model_probability=d("0.620000"),
        market_probability=d("0.600000"),
        expected_exit_cost_rate=d("0.040000"),
        tail_exit_cost_rate=d("0.080000"),
        probability_tail_risk_rate=d("0.320000"),
        cost_uncertainty_buffer_rate=d("0.020000"),
    )

    report = build_report(passed, watched, blocked)
    repeated_report = build_report(blocked, passed, watched)

    assert type(report) is module.ResearchMarketProbabilityExitCostTailReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_gross_probability_edge == d("0.056667")
    assert report.max_total_exit_cost_tail_rate == d("0.140000")
    assert report.min_net_probability_after_tail_rate == d("-0.120000")
    assert report.max_tail_cost_to_edge_ratio == d("7.000000")
    assert report.max_probability_tail_risk_rate == d("0.320000")
    assert report.derived_validation_digest == repeated_report.derived_validation_digest

    block_row, watch_row, pass_row = report.rows
    assert [row.status for row in report.rows] == ["block", "watch", "pass"]

    assert block_row.gross_probability_edge == d("0.020000")
    assert block_row.total_exit_cost_tail_rate == d("0.140000")
    assert block_row.net_probability_after_tail_rate == d("-0.120000")
    assert block_row.tail_cost_to_edge_ratio == d("7.000000")
    assert block_row.tail_cost_buffer_coverage_ratio == d("0.142857")
    assert block_row.reason_codes == (
        "probability_exit_cost_tail_block",
        "net_probability_tail_buffer_block",
        "total_exit_cost_tail_block",
        "tail_cost_to_edge_ratio_block",
        "probability_tail_pressure_block",
    )

    assert watch_row.gross_probability_edge == d("0.060000")
    assert watch_row.total_exit_cost_tail_rate == d("0.040000")
    assert watch_row.net_probability_after_tail_rate == d("0.020000")
    assert watch_row.tail_cost_to_edge_ratio == d("0.666667")
    assert watch_row.tail_cost_buffer_coverage_ratio == d("1.500000")
    assert watch_row.reason_codes == (
        "probability_exit_cost_tail_watch",
        "net_probability_tail_buffer_watch",
        "total_exit_cost_tail_watch",
        "tail_cost_to_edge_ratio_watch",
        "probability_tail_pressure_watch",
    )

    assert pass_row.gross_probability_edge == d("0.090000")
    assert pass_row.total_exit_cost_tail_rate == d("0.029000")
    assert pass_row.net_probability_after_tail_rate == d("0.061000")
    assert pass_row.reason_codes == ("probability_exit_cost_tail_pass",)
    assert len({row.signal_digest for row in report.rows}) == 3
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)


def test_public_payload_is_json_ready_immutable_digest_bound_and_safe() -> None:
    module = api()
    raw_reference = (
        "raw_candidate=alpha candidate_id=cid market_id=mid market_slug=slug "
        "question text source_url=https://example.invalid/a source_text dsn=postgres "
        "table_name=markets token=secret wallet order trade"
    )
    report = build_report(
        sample(
            raw_reference,
            model_probability=d("0.620000"),
            market_probability=d("0.600000"),
            expected_exit_cost_rate=d("0.040000"),
            tail_exit_cost_rate=d("0.080000"),
            probability_tail_risk_rate=d("0.320000"),
            cost_uncertainty_buffer_rate=d("0.020000"),
        ),
    )
    same_instant_report = build_report(
        sample(
            raw_reference,
            observed_at=OBSERVED_AT.astimezone(timezone(timedelta(hours=-4))),
            model_probability=d("0.620000"),
            market_probability=d("0.600000"),
            expected_exit_cost_rate=d("0.040000"),
            tail_exit_cost_rate=d("0.080000"),
            probability_tail_risk_rate=d("0.320000"),
            cost_uncertainty_buffer_rate=d("0.020000"),
        ),
    )

    payload = module.research_market_probability_exit_cost_tail_report_payload(report)
    rendered_payload = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert report.derived_validation_digest == same_instant_report.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert set(report.derived_validation_digest) <= set("0123456789abcdef")
    assert payload["generated_at"] == "2026-07-09T18:00:00+00:00"
    assert payload["rows"][0]["signal_digest"] == report.rows[0].signal_digest
    assert payload["rows"][0]["total_exit_cost_tail_rate"] == "0.140000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) in (int, float) for value in walk_json(payload))

    for forbidden in (
        raw_reference,
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question text",
        "source_url",
        "source_text",
        "https://example.invalid/a",
        "dsn=postgres",
        "table_name",
        "token=secret",
        "wallet",
        "order",
        "trade",
    ):
        assert forbidden.lower() not in rendered_payload.lower()

    with pytest.raises(TypeError, match="payload is immutable"):
        payload["status"] = "pass"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]

    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_probability_exit_cost_tail_report_payload(tampered)

    unsafe_payload = dict(payload)
    unsafe_payload["market_id"] = "leaked"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_market_probability_exit_cost_tail_report_payload(unsafe_payload)

    for unsafe_key in ("execution_surface", "live_trading_surface"):
        unsafe_surface_payload = dict(payload)
        unsafe_surface_payload[unsafe_key] = "blocked"
        with pytest.raises(ValueError, match="unsafe public field"):
            module.research_market_probability_exit_cost_tail_report_payload(
                unsafe_surface_payload,
            )


def test_empty_input_blocks_without_row_leakage() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.input_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_gross_probability_edge == d("0.000000")
    assert report.max_total_exit_cost_tail_rate == d("0.000000")
    assert report.min_net_probability_after_tail_rate == d("0.000000")
    assert report.max_tail_cost_to_edge_ratio == d("0.000000")
    assert report.max_probability_tail_risk_rate == d("0.000000")
    assert report.reason_codes == ("missing_probability_exit_cost_tail_inputs",)
    assert report.reason_code_counts == ()
    assert report.rows == ()


def test_contracts_are_frozen_decimal_only_strict_and_flag_locked() -> None:
    module = api()
    report = build_report(sample("strict-contracts"))

    for contract in (
        module.ResearchMarketProbabilityExitCostTailConfig,
        module.ResearchMarketProbabilityExitCostTailInput,
        module.ResearchMarketProbabilityExitCostTailRow,
        module.ResearchMarketProbabilityExitCostTailReasonCodeCount,
        module.ResearchMarketProbabilityExitCostTailReport,
    ):
        assert contract.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        assert all(field.type not in (int, float) for field in fields(contract))
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"{contract.__name__}Child", (contract,), {})

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        sample("decimal-subclass", tail_exit_cost_rate=_DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="datetime"):
        sample("datetime-subclass", observed_at=_DateTimeSubclass(2026, 7, 9, tzinfo=UTC))
    with pytest.raises(ValueError, match="block threshold"):
        module.ResearchMarketProbabilityExitCostTailConfig(
            watch_tail_cost_to_edge_ratio=d("1.000000"),
            block_tail_cost_to_edge_ratio=d("0.500000"),
        )
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="clear")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, max_tail_cost_to_edge_ratio=d("99.000000"))


def test_source_excludes_network_database_wallet_action_and_advice_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__).lower()
    tree = ast.parse(source)
    imported_modules: set[str] = set()

    assert "research_market_probability_exit_cost_tail_report_payload" in module.__all__
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for banned in (
        "api_key",
        "private_key",
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "open(",
        ".read(",
        ".write(",
        "place_order",
        "submit_order",
        "cancel_order",
        "sign_order",
        "live_trading",
        "recommendation",
        "position_size",
    ):
        assert banned not in source
