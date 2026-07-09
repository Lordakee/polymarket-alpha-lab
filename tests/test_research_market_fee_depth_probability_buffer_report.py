from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib
import json
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_fee_depth_probability_buffer_report"
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
        "pass_net_probability_buffer_threshold": d("0.020000"),
        "watch_net_probability_buffer_threshold": d("0.005000"),
        "minimum_depth_coverage_ratio": d("1.000000"),
        "depth_shortfall_buffer_rate": d("0.030000"),
        "block_required_probability_buffer_threshold": d("0.090000"),
    }
    values.update(overrides)
    return api().ResearchMarketFeeDepthProbabilityBufferConfig(**values)


def sample(reference: str, **overrides: Any) -> object:
    values: dict[str, object] = {
        "research_reference": reference,
        "model_probability": d("0.640000"),
        "market_probability": d("0.550000"),
        "fee_rate": d("0.010000"),
        "bid_ask_spread_rate": d("0.020000"),
        "depth_coverage_ratio": d("0.800000"),
        "probability_uncertainty_buffer_rate": d("0.014000"),
        "observed_at": GENERATED_AT,
    }
    values.update(overrides)
    return api().ResearchMarketFeeDepthProbabilityBufferInput(**values)


def build_report(*inputs: object, cfg: object | None = None) -> object:
    return api().build_research_market_fee_depth_probability_buffer_report(
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


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    canonical = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    signed_payload = dict(payload)
    signed_payload["derived_validation_digest"] = hashlib.sha256(
        canonical.encode("utf-8"),
    ).hexdigest()
    return signed_payload


def test_probability_buffer_subtracts_fee_depth_spread_and_uncertainty() -> None:
    module = api()

    report = build_report(
        sample(
            "raw-candidate pass market-id slug question https://example.invalid "
            "source text token=secret wallet order trade",
        ),
    )

    assert type(report) is module.ResearchMarketFeeDepthProbabilityBufferReport
    assert report.input_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.report_status == "pass"
    assert report.average_net_probability_buffer == d("0.050000")
    assert report.top_net_probability_buffer == d("0.050000")
    assert report.max_required_probability_buffer == d("0.040000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    row = report.rows[0]
    assert row.rank == d("1.000000")
    assert row.gross_probability_edge == d("0.090000")
    assert row.fee_buffer == d("0.010000")
    assert row.spread_buffer == d("0.010000")
    assert row.depth_shortfall_buffer == d("0.006000")
    assert row.probability_uncertainty_buffer == d("0.014000")
    assert row.required_probability_buffer == d("0.040000")
    assert row.net_probability_buffer == d("0.050000")
    assert row.buffer_status == "pass"
    assert row.reason_codes == (
        "depth_shortfall_buffer_applied",
        "fee_buffer_applied",
        "positive_probability_edge",
        "probability_buffer_pass",
        "probability_uncertainty_buffer_applied",
        "spread_buffer_applied",
    )


def test_watch_and_block_rows_rank_deterministically_with_allowed_statuses() -> None:
    report = build_report(
        sample(
            "candidate-cost-block dsn=postgres table=markets",
            model_probability=d("0.800000"),
            market_probability=d("0.550000"),
            fee_rate=d("0.050000"),
            bid_ask_spread_rate=d("0.080000"),
            depth_coverage_ratio=d("0.000000"),
            probability_uncertainty_buffer_rate=d("0.000000"),
        ),
        sample(
            "candidate-watch market-id raw question",
            model_probability=d("0.610000"),
            market_probability=d("0.550000"),
            fee_rate=d("0.010000"),
            bid_ask_spread_rate=d("0.020000"),
            depth_coverage_ratio=d("1.000000"),
            probability_uncertainty_buffer_rate=d("0.035000"),
        ),
        sample(
            "candidate-block negative edge market slug question",
            model_probability=d("0.520000"),
            market_probability=d("0.550000"),
            fee_rate=d("0.005000"),
            bid_ask_spread_rate=d("0.010000"),
            depth_coverage_ratio=d("1.000000"),
            probability_uncertainty_buffer_rate=d("0.000000"),
        ),
    )

    assert report.input_count == d("3.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("2.000000")
    assert report.report_status == "block"
    assert tuple(row.rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.buffer_status for row in report.rows) == (
        "block",
        "watch",
        "block",
    )
    assert set(row.buffer_status for row in report.rows) <= {"pass", "watch", "block"}
    assert tuple(row.net_probability_buffer for row in report.rows) == (
        d("0.130000"),
        d("0.005000"),
        d("-0.040000"),
    )
    assert "required_probability_buffer_blocks_edge" in report.rows[0].reason_codes
    assert "probability_buffer_watch" in report.rows[1].reason_codes
    assert "non_positive_probability_edge" in report.rows[2].reason_codes


def test_empty_input_blocks_without_rows() -> None:
    report = build_report()

    assert report.input_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_net_probability_buffer is None
    assert report.top_net_probability_buffer is None
    assert report.max_required_probability_buffer == d("0.000000")
    assert report.report_status == "block"
    assert report.reason_codes == ("missing_fee_depth_probability_buffer_inputs",)
    assert report.rows == ()


def test_public_payload_is_deterministic_sha256_bound_and_safe() -> None:
    module = api()
    raw_reference = (
        "candidate-alpha market-id market-slug raw question text "
        "https://example.invalid dsn=postgres table=markets token=secret "
        "wallet order trade"
    )
    report = build_report(sample(raw_reference))
    same_report = module.build_research_market_fee_depth_probability_buffer_report(
        (
            sample(
                raw_reference,
                observed_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
            ),
        ),
        config=config(),
        generated_at=GENERATED_AT,
    )

    payload = module.research_market_fee_depth_probability_buffer_report_payload(report)
    encoded = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert report.derived_validation_digest == same_report.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert set(report.derived_validation_digest) <= set("0123456789abcdef")
    assert payload["generated_at"] == "2026-07-09T14:15:00+00:00"
    assert payload["rows"][0]["research_digest"] == report.rows[0].research_digest
    assert payload["rows"][0]["net_probability_buffer"] == "0.050000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) in (int, float) for value in walk_json(payload))

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
        sample(raw_reference, depth_coverage_ratio=d("0.790000")),
    )
    assert changed_report.derived_validation_digest != report.derived_validation_digest
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, max_required_probability_buffer=d("0.999999"))

    tampered_payload = dict(payload)
    tampered_payload["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_fee_depth_probability_buffer_report_payload(
            tampered_payload,
        )

    unsafe_payload = dict(payload)
    unsafe_payload["market_id"] = "leaked-market"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_market_fee_depth_probability_buffer_report_payload(
            unsafe_payload,
        )

    extra_payload = resign_payload(
        {
            **payload,
            "summary": "Will Bitcoin settle above 100000 by Friday",
        },
    )
    with pytest.raises(ValueError, match="unexpected public payload field"):
        module.research_market_fee_depth_probability_buffer_report_payload(
            extra_payload,
        )

    bad_status_payload = resign_payload({**payload, "report_status": "clear"})
    with pytest.raises(ValueError, match="report_status"):
        module.research_market_fee_depth_probability_buffer_report_payload(
            bad_status_payload,
        )

    row_flag_payload = resign_payload(
        {
            **payload,
            "rows": [{**payload["rows"][0], "paper_only": False}],
        },
    )
    with pytest.raises(ValueError, match="paper_only"):
        module.research_market_fee_depth_probability_buffer_report_payload(
            row_flag_payload,
        )


def test_frozen_decimal_only_flags_and_source_surface_contracts() -> None:
    module = api()
    report = build_report(sample("contract-check"))

    for contract in (
        module.ResearchMarketFeeDepthProbabilityBufferConfig,
        module.ResearchMarketFeeDepthProbabilityBufferInput,
        module.ResearchMarketFeeDepthProbabilityBufferReportRow,
        module.ResearchMarketFeeDepthProbabilityBufferReport,
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

        class BadConfig(module.ResearchMarketFeeDepthProbabilityBufferConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        sample("decimal-subclass", model_probability=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="pass_net_probability_buffer_threshold"):
        config(
            pass_net_probability_buffer_threshold=d("0.004000"),
            watch_net_probability_buffer_threshold=d("0.005000"),
        )
    with pytest.raises(ValueError, match="block_required_probability_buffer_threshold"):
        config(block_required_probability_buffer_threshold=d("0.000000"))

    source = module.__loader__.get_source(module.__name__).lower()
    assert "research_market_fee_depth_probability_buffer_report_payload" in (
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
        "recommendation",
        "sizing",
    ):
        assert banned not in source
