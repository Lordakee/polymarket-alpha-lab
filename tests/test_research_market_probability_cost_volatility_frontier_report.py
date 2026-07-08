from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 16, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_probability_cost_volatility_frontier_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_VOLATILITY_FRONTIER_REPORT_CONFIG_VERSION
        ),
        "minimum_pass_sanitized_edge_probability": d("0.050000"),
        "minimum_watch_sanitized_edge_probability": d("0.020000"),
        "maximum_pass_edge_stability_delta": d("0.006000"),
        "maximum_watch_edge_stability_delta": d("0.020000"),
        "maximum_pass_fee_pressure_ratio": d("0.010000"),
        "maximum_watch_fee_pressure_ratio": d("0.030000"),
        "maximum_pass_spread_pressure_ratio": d("0.020000"),
        "maximum_watch_spread_pressure_ratio": d("0.060000"),
        "maximum_pass_slippage_pressure_ratio": d("0.010000"),
        "maximum_watch_slippage_pressure_ratio": d("0.040000"),
        "maximum_pass_volatility_pressure_ratio": d("0.050000"),
        "maximum_watch_volatility_pressure_ratio": d("0.160000"),
        "maximum_pass_total_pressure_ratio": d("0.070000"),
        "maximum_watch_total_pressure_ratio": d("0.220000"),
        "minimum_pass_net_cost_adjusted_edge_probability": d("0.015000"),
        "minimum_watch_net_cost_adjusted_edge_probability": d("0.000000"),
        "minimum_pass_frontier_score": d("0.750000"),
        "minimum_watch_frontier_score": d("0.450000"),
    }
    values.update(overrides)
    return module.ResearchMarketProbabilityCostVolatilityFrontierConfig(**values)


def frontier_input(
    private_event_ref: str = "event-alpha",
    *,
    private_group_ref: str = "group-alpha",
    observed_at: datetime | None = None,
    sanitized_probability_edge: Decimal = d("0.080000"),
    prior_sanitized_probability_edge: Decimal = d("0.078000"),
    fee_pressure_ratio: Decimal = d("0.005000"),
    spread_pressure_ratio: Decimal = d("0.010000"),
    slippage_pressure_ratio: Decimal = d("0.005000"),
    volatility_pressure_ratio: Decimal = d("0.020000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketProbabilityCostVolatilityFrontierInput(
        private_event_ref=private_event_ref,
        private_group_ref=private_group_ref,
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(minutes=3)
        ),
        sanitized_probability_edge=sanitized_probability_edge,
        prior_sanitized_probability_edge=prior_sanitized_probability_edge,
        fee_pressure_ratio=fee_pressure_ratio,
        spread_pressure_ratio=spread_pressure_ratio,
        slippage_pressure_ratio=slippage_pressure_ratio,
        volatility_pressure_ratio=volatility_pressure_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_market_probability_cost_volatility_frontier_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_frontier_report_blocks_without_exposing_inputs() -> None:
    module = api()
    empty = report()

    assert module.PROBABILITY_COST_VOLATILITY_FRONTIER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "PROBABILITY_COST_VOLATILITY_FRONTIER_STATUSES",
        "DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_VOLATILITY_FRONTIER_REPORT_CONFIG_VERSION",
        "ResearchMarketProbabilityCostVolatilityFrontierConfig",
        "ResearchMarketProbabilityCostVolatilityFrontierInput",
        "ResearchMarketProbabilityCostVolatilityFrontierReasonCodeCount",
        "ResearchMarketProbabilityCostVolatilityFrontierReport",
        "ResearchMarketProbabilityCostVolatilityFrontierRow",
        "build_research_market_probability_cost_volatility_frontier_report",
        "research_market_probability_cost_volatility_frontier_report_payload",
        "validate_research_market_probability_cost_volatility_frontier_report_payload",
    )
    assert empty.generated_at == GENERATED_AT
    assert empty.status == "block"
    assert empty.input_count == ZERO
    assert empty.row_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.average_frontier_score == ZERO
    assert empty.min_net_cost_adjusted_edge_probability == ZERO
    assert empty.max_total_pressure_ratio == ZERO
    assert empty.max_edge_stability_delta == ZERO
    assert empty.reason_codes == ("frontier_no_inputs",)
    assert empty.reason_code_counts == (
        module.ResearchMarketProbabilityCostVolatilityFrontierReasonCodeCount(
            reason_code="frontier_no_inputs",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert empty.rows == ()
    assert len(empty.derived_validation_digest) == 64
    int(empty.derived_validation_digest, 16)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_cost_volatility_math_and_pass_watch_block_thresholds() -> None:
    combined = report(
        frontier_input(
            "event-block",
            private_group_ref="group-block",
            sanitized_probability_edge=d("0.030000"),
            prior_sanitized_probability_edge=d("0.000000"),
            fee_pressure_ratio=d("0.040000"),
            spread_pressure_ratio=d("0.070000"),
            slippage_pressure_ratio=d("0.050000"),
            volatility_pressure_ratio=d("0.200000"),
            reason_codes=("manual_review",),
        ),
        frontier_input("event-pass", private_group_ref="group-pass"),
        frontier_input(
            "event-watch",
            private_group_ref="group-watch",
            sanitized_probability_edge=d("0.040000"),
            prior_sanitized_probability_edge=d("0.025000"),
            fee_pressure_ratio=d("0.006000"),
            spread_pressure_ratio=d("0.012000"),
            slippage_pressure_ratio=d("0.006000"),
            volatility_pressure_ratio=d("0.030000"),
        ),
    )

    assert combined.input_count == d("3.000000")
    assert combined.row_count == d("3.000000")
    assert combined.pass_count == d("1.000000")
    assert combined.watch_count == d("1.000000")
    assert combined.block_count == d("1.000000")
    assert combined.status == "block"
    assert combined.weak_edge_strength_count == d("2.000000")
    assert combined.unstable_edge_count == d("2.000000")
    assert combined.high_fee_pressure_count == d("1.000000")
    assert combined.wide_spread_pressure_count == d("1.000000")
    assert combined.high_slippage_pressure_count == d("1.000000")
    assert combined.high_volatility_pressure_count == d("1.000000")
    assert combined.high_total_pressure_count == d("1.000000")
    assert combined.weak_net_cost_adjusted_edge_count == d("1.000000")
    assert combined.average_frontier_score == d("0.639881")
    assert combined.min_net_cost_adjusted_edge_probability == d("-0.130000")
    assert combined.max_total_pressure_ratio == d("0.360000")
    assert combined.max_edge_stability_delta == d("0.030000")

    block_row, watch_row, pass_row = combined.rows
    assert tuple(row.status for row in combined.rows) == ("block", "watch", "pass")
    assert block_row.edge_stability_delta == d("0.030000")
    assert block_row.total_pressure_ratio == d("0.360000")
    assert block_row.net_cost_adjusted_edge_probability == d("-0.130000")
    assert block_row.edge_strength_score == d("0.333333")
    assert block_row.frontier_score == d("0.041667")
    assert "frontier_status_block" in block_row.reason_codes
    assert "frontier_fee_pressure_block" in block_row.reason_codes
    assert "input_manual_review" in block_row.reason_codes
    assert watch_row.edge_strength_score == d("0.666667")
    assert watch_row.edge_stability_score == d("0.357143")
    assert watch_row.total_pressure_ratio == d("0.054000")
    assert watch_row.net_cost_adjusted_edge_probability == d("0.016000")
    assert watch_row.frontier_score == d("0.877976")
    assert "frontier_edge_stability_watch" in watch_row.reason_codes
    assert pass_row.frontier_score == d("1.000000")
    assert pass_row.net_cost_adjusted_edge_probability == d("0.060000")
    assert "frontier_status_pass" in pass_row.reason_codes


def test_total_pressure_can_exceed_one_without_breaking_report_construction() -> None:
    built = report(
        frontier_input(
            "event-high-pressure",
            sanitized_probability_edge=d("0.950000"),
            prior_sanitized_probability_edge=d("0.900000"),
            fee_pressure_ratio=d("0.300000"),
            spread_pressure_ratio=d("0.300000"),
            slippage_pressure_ratio=d("0.300000"),
            volatility_pressure_ratio=d("0.300000"),
        ),
    )

    assert built.max_total_pressure_ratio == d("1.200000")
    assert built.rows[0].total_pressure_ratio == d("1.200000")
    assert built.rows[0].status == "block"


def test_payload_is_deterministic_decimal_string_serialized_and_digest_validated() -> None:
    module = api()
    first = report(
        frontier_input(
            "zulu-event",
            private_group_ref="group-z",
            reason_codes=("zeta", "alpha"),
        ),
        frontier_input("alpha-event", private_group_ref="group-a"),
    )
    second = report(
        frontier_input("alpha-event", private_group_ref="group-a"),
        frontier_input(
            "zulu-event",
            private_group_ref="group-z",
            reason_codes=("alpha", "zeta"),
        ),
    )

    first_payload = module.research_market_probability_cost_volatility_frontier_report_payload(
        first,
    )
    second_payload = module.research_market_probability_cost_volatility_frontier_report_payload(
        second,
    )
    digest_payload = dict(first_payload)
    provided_digest = digest_payload.pop("derived_validation_digest")
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert provided_digest == hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    assert first_payload["row_count"] == "2.000000"
    assert first_payload["rows"][0]["fee_pressure_ratio"] == "0.005000"
    assert first_payload["rows"][0]["frontier_score"] == "1.000000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(first_payload))
    assert not any(
        isinstance(value, (float, int)) and not isinstance(value, bool)
        for value in walk_payload_values(first_payload)
    )
    assert (
        module.validate_research_market_probability_cost_volatility_frontier_report_payload(
            first_payload,
        )
        == first_payload
    )

    tampered = dict(first_payload)
    tampered["row_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_probability_cost_volatility_frontier_report_payload(
            tampered,
        )


def test_public_payload_excludes_sensitive_inputs_and_decision_surfaces() -> None:
    module = api()
    built = report(
        frontier_input(
            "candidate-id-123-private",
            private_group_ref=(
                "market-id-99/will-this-question-resolve/"
                "https://example.test/source?token=secret&wallet=abc"
            ),
        ),
    )
    payload = module.research_market_probability_cost_volatility_frontier_report_payload(
        built,
    )
    rendered = json.dumps(payload, sort_keys=True).lower()

    for forbidden in (
        "candidate-id-123-private",
        "market-id-99",
        "will-this-question-resolve",
        "https://example.test",
        "source?token",
        "secret",
        "wallet",
        "private_event_ref",
        "private_group_ref",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "order",
        "trade",
        "live",
        "recommend",
        "position",
        "sizing",
    ):
        assert forbidden not in rendered

    unsafe_report = replace(built)
    object.__setattr__(unsafe_report, "reason_codes", ("frontier_status_pass", "token_seen"))
    object.__setattr__(unsafe_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_market_probability_cost_volatility_frontier_report_payload(
            unsafe_report,
        )


def test_custom_config_validation_and_threshold_effects() -> None:
    forgiving = config(
        minimum_pass_sanitized_edge_probability=d("0.035000"),
        maximum_pass_edge_stability_delta=d("0.020000"),
        maximum_watch_edge_stability_delta=d("0.040000"),
    )
    built = report(
        frontier_input(
            "event-watch-promoted",
            sanitized_probability_edge=d("0.040000"),
            prior_sanitized_probability_edge=d("0.025000"),
            fee_pressure_ratio=d("0.006000"),
            spread_pressure_ratio=d("0.012000"),
            slippage_pressure_ratio=d("0.006000"),
            volatility_pressure_ratio=d("0.030000"),
        ),
        cfg=forgiving,
    )

    assert built.status == "pass"
    assert built.rows[0].status == "pass"
    assert built.rows[0].edge_stability_score == d("1.000000")

    with pytest.raises(ValueError, match="config_version"):
        config(config_version="unsupported")
    with pytest.raises(ValueError, match="sanitized_edge_probability"):
        config(minimum_pass_sanitized_edge_probability=d("0.010000"))
    with pytest.raises(ValueError, match="fee_pressure_ratio"):
        config(maximum_pass_fee_pressure_ratio=d("0.040000"))
    with pytest.raises(ValueError, match="frontier_score"):
        config(minimum_pass_frontier_score=d("0.400000"))
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="maximum_watch_spread_pressure_ratio"):
        config(maximum_watch_spread_pressure_ratio=0.06)  # type: ignore[arg-type]


def test_rejects_bad_numeric_datetime_flag_status_and_digest_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="minimum_pass_sanitized_edge_probability"):
        config(minimum_pass_sanitized_edge_probability=DecimalSubclass("0.050000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(frontier_input(), generated_at=datetime(2026, 7, 8, 16, 45))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            frontier_input(),
            generated_at=DatetimeSubclass(2026, 7, 8, 16, 45, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        frontier_input(observed_at=datetime(2026, 7, 8, 16, 45))
    with pytest.raises(ValueError, match="observed_at"):
        report(frontier_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="sanitized_probability_edge"):
        frontier_input(sanitized_probability_edge=d("NaN"))
    with pytest.raises(ValueError, match="fee_pressure_ratio"):
        frontier_input(fee_pressure_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_pressure_ratio"):
        frontier_input(spread_pressure_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        frontier_input(reason_codes=("token_seen",))
    with pytest.raises(ValueError, match="readonly"):
        report(frontier_input(readonly=False))

    built = report(frontier_input())
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")
    with pytest.raises(ValueError, match="frontier_score"):
        replace(built.rows[0], frontier_score=d("0.500000"))
    with pytest.raises(ValueError, match="status"):
        replace(built, status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_market_probability_cost_volatility_frontier_report_payload(object())

    unsafe_payload = module.research_market_probability_cost_volatility_frontier_report_payload(
        built,
    )
    unsafe_payload = dict(unsafe_payload)
    unsafe_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_market_probability_cost_volatility_frontier_report_payload(
            unsafe_payload,
        )


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    built = report(frontier_input())

    for item in (config(), frontier_input(), built, *built.reason_code_counts, *built.rows):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True

    with pytest.raises(FrozenInstanceError):
        built.row_count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].frontier_score = ZERO  # type: ignore[misc]

    for klass in (
        module.ResearchMarketProbabilityCostVolatilityFrontierConfig,
        module.ResearchMarketProbabilityCostVolatilityFrontierInput,
        module.ResearchMarketProbabilityCostVolatilityFrontierRow,
        module.ResearchMarketProbabilityCostVolatilityFrontierReasonCodeCount,
        module.ResearchMarketProbabilityCostVolatilityFrontierReport,
    ):
        assert klass.__dataclass_params__.frozen is True
        for field in fields(klass):
            if field.name in {
                "paper_only",
                "report_only",
                "readonly",
                "private_event_ref",
                "private_group_ref",
                "config_version",
                "public_row_ref",
                "status",
                "reason_code",
                "reason_codes",
                "reason_code_counts",
                "rows",
                "derived_validation_digest",
                "observed_at",
                "generated_at",
            }:
                continue
            assert field.type in (Decimal, "Decimal")

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.ResearchMarketProbabilityCostVolatilityFrontierConfig):
            pass


def test_owned_module_has_no_storage_connectivity_or_decision_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_probability_cost_volatility_frontier_report.py"
    )
    module_text = module_path.read_text(encoding="utf-8").lower()
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    for token in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "read_text",
        "write_text",
        "connect(",
        "execute(",
        "database",
        "network",
        "auth",
        "private_key",
        "api_key",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "position",
        "sizing",
    ):
        assert token not in module_text

    forbidden_calls = {
        "open",
        "connect",
        "execute",
        "request",
        "create_order",
        "submit_order",
        "place_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls


def walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
