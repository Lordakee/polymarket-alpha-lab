from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_resolution_authority_cost_edge_gate_report"
)
GENERATED_AT = datetime(2026, 7, 9, 14, 15, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def api() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} must exist")
        raise


def config(**overrides: object) -> object:
    values: dict[str, object] = {
        "cost_adjusted_edge_pass_floor": d("0.020000"),
        "cost_adjusted_edge_watch_floor": d("0.000000"),
        "total_cost_drag_pass_ceiling": d("0.030000"),
        "total_cost_drag_watch_ceiling": d("0.060000"),
        "resolution_authority_pass_floor": d("0.800000"),
        "resolution_authority_watch_floor": d("0.500000"),
    }
    values.update(overrides)
    return api().ResearchStrategyResolutionAuthorityCostEdgeGateConfig(**values)


def gate_input(**overrides: object) -> object:
    values: dict[str, object] = {
        "candidate_id": "candidate_alpha_raw_id",
        "market_id": "market_alpha_raw_id",
        "market_slug": "market-alpha-slug",
        "market_question": "Will alpha resolve yes?",
        "source_url": "https://example.invalid/private-alpha",
        "source_text": (
            "private source text dsn=postgres table=markets token=secret "
            "wallet order trade"
        ),
        "observed_at": datetime(2026, 7, 9, 13, 45, tzinfo=UTC),
        "forecast_probability": d("0.620000"),
        "market_probability": d("0.570000"),
        "fee_probability_drag": d("0.006000"),
        "spread_probability_drag": d("0.004000"),
        "liquidity_probability_drag": d("0.003000"),
        "resolution_cost_probability_drag": d("0.002000"),
        "resolution_authority_score": d("0.900000"),
    }
    values.update(overrides)
    return api().ResearchStrategyResolutionAuthorityCostEdgeGateInput(**values)


def build_report(*inputs: object, cfg: object | None = None) -> object:
    return api().build_research_strategy_resolution_authority_cost_edge_gate_report(
        inputs,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def walk_json(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_json(item)
        return
    if isinstance(value, list):
        for item in value:
            yield from walk_json(item)
        return
    yield value


def redigest(payload: dict[str, Any]) -> None:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        payload_without_digest,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    payload["derived_validation_digest"] = sha256(encoded.encode("utf-8")).hexdigest()


def test_report_gates_resolution_authority_cost_adjusted_edge() -> None:
    module = api()

    report = build_report(
        gate_input(),
        gate_input(
            candidate_id="candidate_beta_raw_id",
            market_id="market_beta_raw_id",
            market_slug="market-beta-slug",
            market_question="Will beta resolve no?",
            source_url="https://example.invalid/private-beta",
            source_text="private beta source",
            forecast_probability=d("0.600000"),
            market_probability=d("0.550000"),
            fee_probability_drag=d("0.010000"),
            spread_probability_drag=d("0.008000"),
            liquidity_probability_drag=d("0.004000"),
            resolution_cost_probability_drag=d("0.003000"),
            resolution_authority_score=d("0.700000"),
        ),
        gate_input(
            candidate_id="candidate_gamma_raw_id",
            market_id="market_gamma_raw_id",
            market_slug="market-gamma-slug",
            market_question="Will gamma resolve yes?",
            source_url="https://example.invalid/private-gamma",
            source_text="private gamma source",
            forecast_probability=d("0.530000"),
            market_probability=d("0.510000"),
            fee_probability_drag=d("0.020000"),
            spread_probability_drag=d("0.020000"),
            liquidity_probability_drag=d("0.020000"),
            resolution_cost_probability_drag=d("0.010000"),
            resolution_authority_score=d("0.300000"),
        ),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyResolutionAuthorityCostEdgeGateReport
    assert report.generated_at == GENERATED_AT
    assert report.source_row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.mean_cost_adjusted_edge_probability == d("0.003333")
    assert report.mean_total_cost_drag_probability == d("0.036667")
    assert report.mean_resolution_authority_score == d("0.633333")
    assert report.status == "block"
    assert report.reason_codes == (
        "resolution_authority_cost_edge_gate_report_block",
        "cost_adjusted_edge_review",
        "total_cost_drag_review",
        "resolution_authority_review",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    blocked, watched, passed = report.rows
    assert blocked.raw_forecast_edge_probability == d("0.020000")
    assert blocked.total_cost_drag_probability == d("0.070000")
    assert blocked.cost_adjusted_edge_probability == d("-0.050000")
    assert blocked.reason_codes == (
        "cost_adjusted_edge_block",
        "resolution_authority_block",
        "total_cost_drag_block",
    )
    assert watched.cost_adjusted_edge_probability == d("0.025000")
    assert watched.reason_codes == ("resolution_authority_watch",)
    assert passed.cost_adjusted_edge_probability == d("0.035000")
    assert passed.reason_codes == ("resolution_authority_cost_edge_gate_pass",)

    counts = {item.reason_code: item for item in report.reason_code_counts}
    assert counts[
        "resolution_authority_watch"
    ] == module.ResearchStrategyResolutionAuthorityCostEdgeGateReasonCodeCount(
        reason_code="resolution_authority_watch",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_payload_is_deterministic_sha256_bound_decimal_stringed_and_redacted() -> None:
    module = api()
    generated_at = GENERATED_AT.astimezone(timezone(timedelta(hours=-4)))
    raw_values = (
        "candidate_alpha_raw_id",
        "market_alpha_raw_id",
        "market-alpha-slug",
        "Will alpha resolve yes?",
        "https://example.invalid/private-alpha",
        "private source text",
        "dsn=postgres",
        "table=markets",
        "token=secret",
        "wallet",
        "order",
        "trade",
    )
    first = module.build_research_strategy_resolution_authority_cost_edge_gate_report(
        (gate_input(),),
        config=config(),
        generated_at=generated_at,
    )
    second = module.build_research_strategy_resolution_authority_cost_edge_gate_report(
        tuple(reversed((gate_input(),))),
        config=config(),
        generated_at=generated_at,
    )

    payload = module.research_strategy_resolution_authority_cost_edge_gate_report_payload(
        first,
    )
    encoded = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-09T14:15:00+00:00"
    assert payload["source_row_count"] == "1.000000"
    assert payload["rows"][0]["row_number"] == "1.000000"
    assert payload["rows"][0]["cost_adjusted_edge_probability"] == "0.035000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) in (int, float, Decimal) for value in walk_json(payload))

    for forbidden in raw_values + (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
    ):
        assert forbidden.lower() not in encoded.lower()

    changed = build_report(gate_input(resolution_authority_score=d("0.899999")))
    assert changed.derived_validation_digest != first.derived_validation_digest
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, mean_total_cost_drag_probability=d("0.999999"))

    tampered_payload = dict(payload)
    tampered_payload["source_row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_resolution_authority_cost_edge_gate_report_payload(
            tampered_payload,
        )

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["market_id"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_resolution_authority_cost_edge_gate_report_payload(
            unsafe_key_payload,
        )


def test_empty_input_blocks_with_report_only_flags() -> None:
    report = build_report()

    assert report.source_row_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.mean_cost_adjusted_edge_probability == d("0.000000")
    assert report.mean_total_cost_drag_probability == d("0.000000")
    assert report.mean_resolution_authority_score == d("0.000000")
    assert report.status == "block"
    assert report.reason_codes == (
        "resolution_authority_cost_edge_gate_report_empty",
    )
    assert report.rows == ()
    assert report.reason_code_counts == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_dict_requires_exact_canonical_schema_and_semantics() -> None:
    module = api()
    payload = module.research_strategy_resolution_authority_cost_edge_gate_report_payload(
        build_report(gate_input()),
    )

    unexpected_field = deepcopy(payload)
    unexpected_field["notes"] = "safe"
    redigest(unexpected_field)

    missing_rows = deepcopy(payload)
    missing_rows.pop("rows")
    redigest(missing_rows)

    false_flag = deepcopy(payload)
    false_flag["paper_only"] = False
    redigest(false_flag)

    inconsistent_row = deepcopy(payload)
    inconsistent_row["rows"][0]["status"] = "watch"
    redigest(inconsistent_row)

    noncanonical_decimal = deepcopy(payload)
    noncanonical_decimal["source_row_count"] = "01.000000"
    redigest(noncanonical_decimal)

    for invalid_payload in (
        unexpected_field,
        missing_rows,
        false_flag,
        inconsistent_row,
        noncanonical_decimal,
    ):
        with pytest.raises(ValueError, match="payload schema"):
            module.research_strategy_resolution_authority_cost_edge_gate_report_payload(
                invalid_payload,
            )


def test_frozen_decimal_only_status_flags_and_validation_contracts() -> None:
    module = api()
    report = build_report(gate_input())

    assert module.RESEARCH_STRATEGY_RESOLUTION_AUTHORITY_COST_EDGE_GATE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    for contract in (
        module.ResearchStrategyResolutionAuthorityCostEdgeGateConfig,
        module.ResearchStrategyResolutionAuthorityCostEdgeGateInput,
        module.ResearchStrategyResolutionAuthorityCostEdgeGateReasonCodeCount,
        module.ResearchStrategyResolutionAuthorityCostEdgeGateRow,
        module.ResearchStrategyResolutionAuthorityCostEdgeGateReport,
    ):
        assert contract.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        assert all(field.type not in (int, float) for field in fields(contract))

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadConfig(module.ResearchStrategyResolutionAuthorityCostEdgeGateConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        gate_input(forecast_probability=_DecimalSubclass("0.620000"))
    with pytest.raises(ValueError, match="cost_adjusted_edge_pass_floor"):
        config(
            cost_adjusted_edge_pass_floor=d("-0.010000"),
            cost_adjusted_edge_watch_floor=d("0.000000"),
        )
    with pytest.raises(ValueError, match="total_cost_drag"):
        config(
            total_cost_drag_pass_ceiling=d("0.070000"),
            total_cost_drag_watch_ceiling=d("0.060000"),
        )

    source = module.__loader__.get_source(module.__name__).lower()
    assert "research_strategy_resolution_authority_cost_edge_gate_report_payload" in (
        module.__all__
    )
    for forbidden_import in (
        "requests",
        "httpx",
        "psycopg",
        "sqlalchemy",
        "web3",
        "py_clob_client",
    ):
        assert forbidden_import not in source
