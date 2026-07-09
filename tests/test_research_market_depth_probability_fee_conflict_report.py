from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import importlib
import json
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_depth_probability_fee_conflict_report"
)
GENERATED_AT = datetime(2026, 7, 9, 16, 30, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 16, 15, tzinfo=UTC)


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
        "pass_net_probability_edge_threshold": d("0.025000"),
        "watch_net_probability_edge_threshold": d("0.005000"),
        "minimum_depth_coverage_ratio": d("1.000000"),
        "depth_shortfall_penalty_rate": d("0.040000"),
        "fee_drag_watch_threshold": d("0.020000"),
        "fee_drag_block_threshold": d("0.060000"),
    }
    values.update(overrides)
    return api().ResearchMarketDepthProbabilityFeeConflictConfig(**values)


def sample(reference: str, **overrides: Any) -> object:
    values: dict[str, object] = {
        "research_reference": reference,
        "model_probability": d("0.700000"),
        "market_probability": d("0.600000"),
        "fee_rate": d("0.005000"),
        "bid_ask_spread_rate": d("0.010000"),
        "depth_coverage_ratio": d("0.900000"),
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return api().ResearchMarketDepthProbabilityFeeConflictInput(**values)


def build_report(*inputs: object, cfg: object | None = None) -> object:
    return api().build_research_market_depth_probability_fee_conflict_report(
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


def test_depth_probability_fee_conflicts_are_scored_and_ranked() -> None:
    module = api()

    report = build_report(
        sample(
            "pass raw-candidate market-id slug question https://example.invalid",
        ),
        sample(
            "watch raw candidate source text",
            model_probability=d("0.620000"),
            market_probability=d("0.580000"),
            fee_rate=d("0.015000"),
            bid_ask_spread_rate=d("0.020000"),
            depth_coverage_ratio=d("1.000000"),
        ),
        sample(
            "block market-id dsn=postgres table=markets token=secret wallet order trade",
            model_probability=d("0.590000"),
            market_probability=d("0.580000"),
            fee_rate=d("0.040000"),
            bid_ask_spread_rate=d("0.060000"),
            depth_coverage_ratio=d("0.250000"),
        ),
    )

    assert type(report) is module.ResearchMarketDepthProbabilityFeeConflictReport
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.report_status == "block"
    assert report.worst_net_probability_edge == d("-0.090000")
    assert report.average_net_probability_edge == d("0.003667")
    assert report.max_required_probability_drag == d("0.100000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    block_row, watch_row, pass_row = report.rows
    assert tuple(row.rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.conflict_status for row in report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert set(row.conflict_status for row in report.rows) <= {"pass", "watch", "block"}

    assert block_row.gross_probability_edge == d("0.010000")
    assert block_row.fee_drag_rate == d("0.070000")
    assert block_row.depth_shortfall_penalty == d("0.030000")
    assert block_row.required_probability_drag == d("0.100000")
    assert block_row.net_probability_edge == d("-0.090000")
    assert block_row.reason_codes == (
        "depth_shortfall_penalty_applied",
        "fee_drag_block",
        "positive_probability_edge",
        "probability_fee_conflict_block",
        "required_drag_exceeds_probability_edge",
    )

    assert watch_row.gross_probability_edge == d("0.040000")
    assert watch_row.fee_drag_rate == d("0.025000")
    assert watch_row.depth_shortfall_penalty == d("0.000000")
    assert watch_row.required_probability_drag == d("0.025000")
    assert watch_row.net_probability_edge == d("0.015000")
    assert watch_row.reason_codes == (
        "fee_drag_watch",
        "positive_probability_edge",
        "probability_fee_conflict_watch",
    )

    assert pass_row.gross_probability_edge == d("0.100000")
    assert pass_row.fee_drag_rate == d("0.010000")
    assert pass_row.depth_shortfall_penalty == d("0.004000")
    assert pass_row.required_probability_drag == d("0.014000")
    assert pass_row.net_probability_edge == d("0.086000")
    assert pass_row.reason_codes == (
        "depth_shortfall_penalty_applied",
        "positive_probability_edge",
        "probability_fee_conflict_pass",
    )
    assert len({row.research_digest for row in report.rows}) == 3


def test_empty_input_blocks_without_row_leakage() -> None:
    report = build_report()

    assert report.input_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.worst_net_probability_edge is None
    assert report.average_net_probability_edge is None
    assert report.max_required_probability_drag == d("0.000000")
    assert report.report_status == "block"
    assert report.reason_codes == ("missing_depth_probability_fee_conflict_inputs",)
    assert report.rows == ()


def test_public_payload_is_deterministic_sha256_bound_and_safe() -> None:
    module = api()
    raw_reference = (
        "candidate-alpha market-id market-slug raw question text "
        "https://example.invalid dsn=postgres table=markets token=secret "
        "wallet order trade"
    )
    report = build_report(sample(raw_reference))
    same_report = build_report(
        sample(
            raw_reference,
            observed_at=OBSERVED_AT.astimezone(timezone(timedelta(hours=-7))),
        ),
    )

    payload = module.research_market_depth_probability_fee_conflict_report_payload(
        report,
    )
    encoded = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert report.derived_validation_digest == same_report.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert set(report.derived_validation_digest) <= set("0123456789abcdef")
    assert payload["generated_at"] == "2026-07-09T16:30:00+00:00"
    assert payload["rows"][0]["research_digest"] == report.rows[0].research_digest
    assert payload["rows"][0]["net_probability_edge"] == "0.086000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) in (int, float, Decimal) for value in walk_json(payload))

    for forbidden in (
        raw_reference,
        "candidate-alpha",
        "market-id",
        "market-slug",
        "raw question text",
        "https://",
        "dsn=",
        "table=markets",
        "token=secret",
        "wallet",
        "order",
        "trade",
        "research_reference",
    ):
        assert forbidden.lower() not in encoded.lower()

    changed_report = build_report(
        sample(raw_reference, fee_rate=d("0.006000")),
    )
    assert changed_report.derived_validation_digest != report.derived_validation_digest
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, max_required_probability_drag=d("0.999999"))

    unsafe_payload = dict(payload)
    unsafe_payload["question"] = "leaked question"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_market_depth_probability_fee_conflict_report_payload(
            unsafe_payload,
        )


def test_frozen_decimal_only_flags_and_source_surface_contracts() -> None:
    module = api()
    report = build_report(sample("contract-check"))

    for contract in (
        module.ResearchMarketDepthProbabilityFeeConflictConfig,
        module.ResearchMarketDepthProbabilityFeeConflictInput,
        module.ResearchMarketDepthProbabilityFeeConflictReportRow,
        module.ResearchMarketDepthProbabilityFeeConflictReport,
    ):
        assert contract.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        assert all(field.type not in (int, float) for field in fields(contract))

    with pytest.raises(FrozenInstanceError):
        report.report_status = "pass"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadConfig(module.ResearchMarketDepthProbabilityFeeConflictConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        sample("decimal-subclass", model_probability=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="pass_net_probability_edge_threshold"):
        config(
            pass_net_probability_edge_threshold=d("0.004000"),
            watch_net_probability_edge_threshold=d("0.005000"),
        )
    with pytest.raises(ValueError, match="fee_drag_block_threshold"):
        config(fee_drag_block_threshold=d("0.010000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_market_depth_probability_fee_conflict_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 9, 16, 30),
        )

    source = module.__loader__.get_source(module.__name__).lower()
    assert "research_market_depth_probability_fee_conflict_report_payload" in (
        module.__all__
    )
    for banned in (
        "api_key",
        "private_key",
        "wallet",
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
        "sizing",
        "recommendation",
    ):
        assert banned not in source
