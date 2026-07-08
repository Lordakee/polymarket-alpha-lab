from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_market_spread_volatility_watch_report"
GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_SPREAD_VOLATILITY_WATCH_CONFIG_VERSION
        ),
        "watch_spread_volatility_ratio": d("0.020000"),
        "block_spread_volatility_ratio": d("0.060000"),
        "watch_depth_instability_ratio": d("0.250000"),
        "block_depth_instability_ratio": d("0.650000"),
        "watch_fee_friction_ratio": d("0.015000"),
        "block_fee_friction_ratio": d("0.040000"),
        "watch_settlement_cost_pressure": d("0.300000"),
        "block_settlement_cost_pressure": d("0.700000"),
        "watch_composite_pressure": d("0.300000"),
        "block_composite_pressure": d("0.700000"),
        "spread_volatility_weight": d("0.350000"),
        "depth_instability_weight": d("0.250000"),
        "fee_friction_weight": d("0.200000"),
        "settlement_cost_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchMarketSpreadVolatilityWatchConfig(**values)


def observation(
    public_bucket: str = "public-spread-volatility",
    *,
    observed_at: datetime | None = None,
    sample_count: Decimal = d("5"),
    aggregate_spread_volatility_ratio: Decimal = d("0.006000"),
    depth_instability_ratio: Decimal = d("0.050000"),
    fee_friction_ratio: Decimal = d("0.004000"),
    settlement_cost_pressure_score: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketSpreadVolatilityWatchObservation(
        public_bucket=public_bucket,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=5),
        sample_count=sample_count,
        aggregate_spread_volatility_ratio=aggregate_spread_volatility_ratio,
        depth_instability_ratio=depth_instability_ratio,
        fee_friction_ratio=fee_friction_ratio,
        settlement_cost_pressure_score=settlement_cost_pressure_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *observations: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_market_spread_volatility_watch_report(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_payload_values(nested))
    if isinstance(value, list):
        return tuple(item for nested in value for item in walk_payload_values(nested))
    return (value,)


def test_spread_volatility_watch_report_summarizes_pass_watch_and_block_rows() -> None:
    module = api()
    built = report(
        observation("quiet-public-bucket"),
        observation(
            "watch-public-bucket",
            aggregate_spread_volatility_ratio=d("0.030000"),
            depth_instability_ratio=d("0.300000"),
            fee_friction_ratio=d("0.020000"),
            settlement_cost_pressure_score=d("0.350000"),
            reason_codes=("manual_review",),
        ),
        observation(
            "blocked-public-bucket",
            sample_count=d("7"),
            aggregate_spread_volatility_ratio=d("0.080000"),
            depth_instability_ratio=d("0.700000"),
            fee_friction_ratio=d("0.050000"),
            settlement_cost_pressure_score=d("0.800000"),
        ),
    )

    assert type(built) is module.ResearchMarketSpreadVolatilityWatchReport
    assert is_dataclass(built)
    assert module.STATUSES == ("pass", "watch", "block")
    assert built.status == "block"
    assert built.generated_at == GENERATED_AT
    assert built.observation_count == d("3.000000")
    assert built.sample_count == d("17.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.spread_volatility_watch_count == d("2.000000")
    assert built.depth_instability_watch_count == d("2.000000")
    assert built.fee_friction_watch_count == d("2.000000")
    assert built.settlement_cost_pressure_count == d("2.000000")
    assert built.max_composite_pressure == d("1.000000")
    assert built.mean_composite_pressure == d("0.394583")
    assert built.manual_review_required is True

    blocked, watched, passed = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert blocked.public_bucket == "blocked-public-bucket"
    assert blocked.composite_pressure == d("1.000000")
    assert blocked.reason_codes == (
        "spread_volatility_watch_aggregate_spread_volatility_block",
        "spread_volatility_watch_depth_instability_block",
        "spread_volatility_watch_fee_friction_block",
        "spread_volatility_watch_settlement_cost_pressure_block",
        "spread_volatility_watch_composite_pressure_block",
    )
    assert watched.public_bucket == "watch-public-bucket"
    assert watched.spread_volatility_pressure == d("0.250000")
    assert watched.depth_instability_pressure == d("0.125000")
    assert watched.fee_friction_pressure == d("0.200000")
    assert watched.settlement_cost_pressure == d("0.125000")
    assert watched.composite_pressure == d("0.183750")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "input_manual_review",
        "spread_volatility_watch_aggregate_spread_volatility_watch",
        "spread_volatility_watch_depth_instability_watch",
        "spread_volatility_watch_fee_friction_watch",
        "spread_volatility_watch_settlement_cost_pressure_watch",
        "spread_volatility_watch_manual_review_watch",
    )
    assert passed.reason_codes == ("spread_volatility_watch_clear",)
    assert all(row.paper_only and row.report_only and row.readonly for row in built.rows)
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True


def test_composite_pressure_block_accepts_threshold_pressure_below_full() -> None:
    module = api()
    built = report(
        observation(
            "composite-block-public-bucket",
            aggregate_spread_volatility_ratio=d("0.052000"),
            depth_instability_ratio=d("0.570000"),
            fee_friction_ratio=d("0.035000"),
            settlement_cost_pressure_score=d("0.620000"),
        ),
    )

    (row,) = built.rows
    assert row.status == "block"
    assert row.composite_pressure == d("0.800000")
    assert config().block_composite_pressure <= row.composite_pressure < d("1.000000")
    assert (
        "spread_volatility_watch_composite_pressure_block"
        in row.reason_codes
    )
    assert (
        "spread_volatility_watch_aggregate_spread_volatility_block"
        not in row.reason_codes
    )
    payload = module.research_market_spread_volatility_watch_report_payload(built)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_payload_values(payload))


def test_payload_and_digest_are_deterministic_decimal_strings_and_report_only() -> None:
    module = api()
    first = report(
        observation("beta-public-bucket", aggregate_spread_volatility_ratio=d("0.030000")),
        observation("alpha-public-bucket"),
    )
    second = report(
        observation("alpha-public-bucket"),
        observation("beta-public-bucket", aggregate_spread_volatility_ratio=d("0.030000")),
    )
    first_payload = module.research_market_spread_volatility_watch_report_payload(first)
    second_payload = module.research_market_spread_volatility_watch_report_payload(second)
    digest = module.research_market_spread_volatility_watch_report_digest(first)

    assert first == second
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True)
    assert digest == hashlib.sha256(
        json.dumps(first_payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert digest == module.research_market_spread_volatility_watch_report_digest(second)
    assert first_payload["generated_at"] == "2026-07-08T18:00:00+00:00"
    assert first_payload["observation_count"] == "2.000000"
    assert first_payload["rows"][0]["public_bucket"] == "beta-public-bucket"
    assert first_payload["rows"][0]["aggregate_spread_volatility_ratio"] == "0.030000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(first_payload))
    assert "order" not in json.dumps(first_payload).lower()
    assert "trade" not in json.dumps(first_payload).lower()
    assert "sizing" not in json.dumps(first_payload).lower()
    assert "recommend" not in json.dumps(first_payload).lower()


def test_empty_report_blocks_for_manual_review_with_public_reason() -> None:
    module = api()
    empty = report()

    assert empty.status == "block"
    assert empty.observation_count == ZERO
    assert empty.row_count == ZERO
    assert empty.rows == ()
    assert empty.manual_review_required is True
    assert empty.reason_codes == ("spread_volatility_watch_no_observations",)
    assert empty.reason_code_counts == (
        module.ResearchMarketSpreadVolatilityWatchReasonCodeCount(
            reason_code="spread_volatility_watch_no_observations",
            count=d("1.000000"),
            sample_ratio=ZERO,
        ),
    )


def test_validation_rejects_bad_numeric_types_flags_times_and_tampering() -> None:
    module = api()
    good = report(observation())

    with pytest.raises(FrozenInstanceError):
        good.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        good.rows[0].composite_pressure = d("0.500000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="aggregate_spread_volatility_ratio"):
        observation(aggregate_spread_volatility_ratio=0.006)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="depth_instability_ratio"):
        observation(depth_instability_ratio=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="observed_at"):
        replace(observation(), observed_at=datetime(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(), generated_at=_DatetimeSubclass(2026, 7, 8, 18, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)
    with pytest.raises(ValueError, match="public_bucket"):
        observation("market_slug:raw-source-id")

    tampered = replace(good)
    object.__setattr__(tampered, "observation_count", d("2.000000"))
    with pytest.raises(ValueError, match="observation_count"):
        module.research_market_spread_volatility_watch_report_payload(tampered)

    bad_flag_row = replace(good.rows[0])
    object.__setattr__(bad_flag_row, "report_only", False)
    bad_nested = replace(good)
    object.__setattr__(bad_nested, "rows", (bad_flag_row,))
    with pytest.raises(ValueError, match="report_only"):
        module.research_market_spread_volatility_watch_report_payload(bad_nested)


def test_module_is_pure_report_only_without_side_effect_surfaces() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8")
    forbidden_import_fragments = (
        "requests",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "web3",
        "clob",
    )
    forbidden_text_fragments = (
        "place_order",
        "submit_order",
        "wallet",
        "private_key",
        "execute_trade",
        "trade_recommendation",
        "position_size",
    )

    for fragment in forbidden_import_fragments:
        assert fragment not in source
    for fragment in forbidden_text_fragments:
        assert fragment not in source

    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type) and is_dataclass(exported):
            names = {field.name for field in fields(exported)}
            if {"paper_only", "report_only", "readonly"} <= names:
                instance = (
                    config()
                    if exported_name.endswith("Config")
                    else observation()
                    if exported_name.endswith("Observation")
                    else report()
                    if exported_name.endswith("Report")
                    else None
                )
                if instance is not None:
                    assert instance.paper_only is True
                    assert instance.report_only is True
                    assert instance.readonly is True
