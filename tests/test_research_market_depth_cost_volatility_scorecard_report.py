from __future__ import annotations

import importlib
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_depth_cost_volatility_scorecard_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_market_depth_cost_volatility_scorecard_report.py"
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
        "spread_watch_threshold": d("0.030000"),
        "spread_block_threshold": d("0.060000"),
        "fee_drag_watch_threshold": d("0.010000"),
        "fee_drag_block_threshold": d("0.030000"),
        "slippage_cushion_watch_threshold": d("0.050000"),
        "slippage_cushion_block_threshold": d("0.020000"),
        "book_age_watch_seconds": d("300.000000"),
        "book_age_block_seconds": d("900.000000"),
        "volatility_watch_threshold": d("0.080000"),
        "volatility_block_threshold": d("0.160000"),
        "settlement_friction_watch_threshold": d("0.050000"),
        "settlement_friction_block_threshold": d("0.100000"),
        "quality_score_watch_threshold": d("0.700000"),
        "quality_score_block_threshold": d("0.400000"),
    }
    values.update(overrides)
    return module.ResearchMarketDepthCostVolatilityScorecardConfig(**values)


def observation(
    cohort_key: str,
    *,
    depth_band: str = "deep",
    spread_width: Decimal = d("0.010000"),
    fee_drag: Decimal = d("0.002000"),
    slippage_cushion: Decimal = d("0.090000"),
    book_age_seconds: Decimal = d("120.000000"),
    volatility: Decimal = d("0.030000"),
    settlement_friction: Decimal = d("0.010000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketDepthCostVolatilityScorecardObservation(
        cohort_key=cohort_key,
        depth_band=depth_band,
        spread_width=spread_width,
        fee_drag=fee_drag,
        slippage_cushion=slippage_cushion,
        book_age_seconds=book_age_seconds,
        volatility=volatility,
        settlement_friction=settlement_friction,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_market_depth_cost_volatility_scorecard_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_build_requires_explicit_generated_at_for_deterministic_payload() -> None:
    module = api()

    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_depth_cost_volatility_scorecard_report(
            (observation("cohort_pass"),),
            config=config(),
        )


def test_empty_report_is_watch_frozen_digest_and_public_payload_safe() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchMarketDepthCostVolatilityScorecardReport
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert report.generated_at == GENERATED_AT
    assert report.status == "watch"
    assert report.cohort_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.pass_ratio == d("0.000000")
    assert report.average_quality_score == d("0.000000")
    assert report.max_total_cost_drag == d("0.000000")
    assert report.max_book_age_seconds == d("0.000000")
    assert report.max_volatility == d("0.000000")
    assert report.max_settlement_friction == d("0.000000")
    assert report.reason_codes == ("depth_cost_volatility_scorecard_empty",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]

    payload = module.research_market_depth_cost_volatility_scorecard_report_payload(
        report,
    )
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["cohort_count"] == "0.000000"
    assert payload["pass_ratio"] == "0.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    module.validate_research_market_depth_cost_volatility_scorecard_public_payload(
        payload,
    )
    json.dumps(payload, sort_keys=True)
    _assert_no_public_float_or_int(payload)
    _assert_no_forbidden_public_surface(payload)


def test_depth_cost_volatility_rows_roll_up_deterministically() -> None:
    report = build_report(
        observation("cohort_pass"),
        observation(
            "cohort_watch",
            depth_band="adequate",
            spread_width=d("0.040000"),
            fee_drag=d("0.012000"),
            slippage_cushion=d("0.040000"),
            book_age_seconds=d("360.000000"),
            volatility=d("0.090000"),
            settlement_friction=d("0.060000"),
        ),
        observation(
            "cohort_block",
            depth_band="thin",
            spread_width=d("0.070000"),
            fee_drag=d("0.035000"),
            slippage_cushion=d("0.010000"),
            book_age_seconds=d("1200.000000"),
            volatility=d("0.170000"),
            settlement_friction=d("0.120000"),
        ),
    )

    assert report.status == "block"
    assert report.reason_codes == (
        "spread_width_block",
        "fee_drag_block",
        "slippage_cushion_block",
        "book_age_block",
        "volatility_block",
        "settlement_friction_block",
        "spread_width_watch",
        "fee_drag_watch",
        "slippage_cushion_watch",
        "book_age_watch",
        "volatility_watch",
        "settlement_friction_watch",
    )
    assert report.cohort_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.pass_ratio == d("0.333333")
    assert report.average_quality_score == d("0.614683")
    assert report.max_total_cost_drag == d("0.105000")
    assert report.max_book_age_seconds == d("1200.000000")
    assert report.max_volatility == d("0.170000")
    assert report.max_settlement_friction == d("0.120000")

    assert tuple(row.cohort_key for row in report.rows) == (
        "cohort_block",
        "cohort_watch",
        "cohort_pass",
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.depth_band_score for row in report.rows) == (
        d("0.350000"),
        d("0.750000"),
        d("1.000000"),
    )
    assert tuple(row.total_cost_drag for row in report.rows) == (
        d("0.105000"),
        d("0.052000"),
        d("0.012000"),
    )
    assert tuple(row.quality_score for row in report.rows) == (
        d("0.050000"),
        d("0.794048"),
        d("1.000000"),
    )


def test_dataclasses_are_exact_decimal_only_and_flags_are_hard() -> None:
    module = api()
    report = build_report(observation("cohort_pass"))

    for cls in (
        module.ResearchMarketDepthCostVolatilityScorecardConfig,
        module.ResearchMarketDepthCostVolatilityScorecardObservation,
        module.ResearchMarketDepthCostVolatilityScorecardRow,
        module.ResearchMarketDepthCostVolatilityScorecardReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    _assert_decimal_public_fields(report)
    for row in report.rows:
        _assert_decimal_public_fields(row)

    with pytest.raises(ValueError, match="spread_watch_threshold"):
        config(spread_watch_threshold=0.03)
    with pytest.raises(ValueError, match="fee_drag_block_threshold"):
        config(fee_drag_block_threshold=_DecimalSubclass("0.030000"))
    with pytest.raises(ValueError, match="spread_block_threshold"):
        config(spread_watch_threshold=d("0.060000"))
    with pytest.raises(ValueError, match="spread_width"):
        observation("bad_spread", spread_width=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="depth_band"):
        observation("bad_band", depth_band="shallow")
    with pytest.raises(ValueError, match="paper_only"):
        observation("bad_flag", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_payload_digest_validation_and_public_surface_rejection() -> None:
    module = api()
    report = build_report(observation("cohort_pass"))
    payload = module.research_market_depth_cost_volatility_scorecard_report_payload(
        report,
    )

    tampered = dict(payload)
    tampered["pass_ratio"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_depth_cost_volatility_scorecard_public_payload(
            tampered,
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.validate_research_market_depth_cost_volatility_scorecard_public_payload(
            {
                **payload,
                "candidate_id": "raw_candidate_123",
            },
        )
    unsafe_value = dict(payload)
    unsafe_value["rows"] = [
        {
            **payload["rows"][0],
            "cohort_key": "https://example.test/raw-question",
        },
    ]
    with pytest.raises(ValueError, match="unsafe"):
        module.validate_research_market_depth_cost_volatility_scorecard_public_payload(
            unsafe_value,
        )


def test_public_payload_validation_rejects_resigned_invalid_statuses() -> None:
    module = api()
    report = build_report(observation("cohort_pass"))
    payload = module.research_market_depth_cost_volatility_scorecard_report_payload(
        report,
    )

    invalid_report_status = _resign_payload({**payload, "status": "hold"})
    with pytest.raises(ValueError, match="status"):
        module.validate_research_market_depth_cost_volatility_scorecard_public_payload(
            invalid_report_status,
        )

    invalid_row_status = _resign_payload(
        {
            **payload,
            "rows": [
                {
                    **payload["rows"][0],
                    "status": "hold",
                },
            ],
        },
    )
    with pytest.raises(ValueError, match="status"):
        module.validate_research_market_depth_cost_volatility_scorecard_public_payload(
            invalid_row_status,
        )


def test_public_payload_validation_rejects_raw_decimal_values() -> None:
    module = api()
    report = build_report(observation("cohort_pass"))
    payload = module.research_market_depth_cost_volatility_scorecard_report_payload(
        report,
    )

    raw_decimal = {**payload, "pass_ratio": d("0.999999")}
    with pytest.raises(ValueError, match="public payload numerics"):
        module.validate_research_market_depth_cost_volatility_scorecard_public_payload(
            raw_decimal,
        )


def test_public_payload_validation_rejects_auth_surfaces() -> None:
    module = api()
    report = build_report(observation("cohort_pass"))
    payload = module.research_market_depth_cost_volatility_scorecard_report_payload(
        report,
    )

    with pytest.raises(ValueError, match="unsafe"):
        module.validate_research_market_depth_cost_volatility_scorecard_public_payload(
            {
                **payload,
                "auth_header": "redacted",
            },
        )


def test_module_does_not_contain_trade_recommendation_language() -> None:
    source = MODULE_PATH.read_text()
    forbidden_terms = (
        "recommend_trade",
        "recommend_position",
        "order_placement",
        "position_size",
        "trade_size",
        "sizing",
    )
    lowered = source.lower()
    for term in forbidden_terms:
        assert term not in lowered


def _assert_decimal_public_fields(value: Any) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if field.name in {
            "generated_at",
            "config_version",
            "cohort_key",
            "depth_band",
            "status",
            "reason_codes",
            "rows",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        }:
            continue
        assert type(item) is Decimal, field.name


def _assert_no_public_float_or_int(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise AssertionError(f"public payload leaked numeric {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_public_float_or_int(item)


def _assert_no_forbidden_public_surface(value: object) -> None:
    serialized = json.dumps(value, sort_keys=True).lower()
    forbidden = (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "http://",
        "https://",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "position",
    )
    for term in forbidden:
        assert term not in serialized


def _resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        **payload,
        "derived_validation_digest": hashlib.sha256(encoded).hexdigest(),
    }
