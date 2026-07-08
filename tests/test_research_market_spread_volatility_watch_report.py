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
        "watch_spread_instability_ratio": d("0.020000"),
        "block_spread_instability_ratio": d("0.060000"),
        "watch_depth_decay_ratio": d("0.250000"),
        "block_depth_decay_ratio": d("0.650000"),
        "watch_quote_age_seconds": d("300.000000"),
        "block_quote_age_seconds": d("900.000000"),
        "watch_cost_risk_pressure_score": d("0.300000"),
        "block_cost_risk_pressure_score": d("0.700000"),
        "watch_composite_pressure": d("0.300000"),
        "block_composite_pressure": d("0.700000"),
        "spread_instability_weight": d("0.350000"),
        "depth_decay_weight": d("0.250000"),
        "quote_age_weight": d("0.200000"),
        "cost_risk_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchMarketSpreadVolatilityWatchConfig(**values)


def observation(
    public_cohort: str = "public-spread-volatility",
    *,
    observed_at: datetime | None = None,
    sample_count: Decimal = d("5"),
    aggregate_spread_instability_ratio: Decimal = d("0.006000"),
    depth_decay_ratio: Decimal = d("0.050000"),
    quote_age_seconds: Decimal = d("120.000000"),
    cost_risk_pressure_score: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketSpreadVolatilityWatchObservation(
        public_cohort=public_cohort,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=5),
        sample_count=sample_count,
        aggregate_spread_instability_ratio=aggregate_spread_instability_ratio,
        depth_decay_ratio=depth_decay_ratio,
        quote_age_seconds=quote_age_seconds,
        cost_risk_pressure_score=cost_risk_pressure_score,
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


def walk_payload_keys(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        return tuple(
            item
            for key, nested in value.items()
            for item in (str(key), *walk_payload_keys(nested))
        )
    if isinstance(value, list):
        return tuple(item for nested in value for item in walk_payload_keys(nested))
    return ()


def test_empty_report_blocks_with_public_digest_and_hard_flags() -> None:
    module = api()
    empty = report()

    assert module.STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_SPREAD_VOLATILITY_WATCH_CONFIG_VERSION",
        "STATUSES",
        "ResearchMarketSpreadVolatilityWatchConfig",
        "ResearchMarketSpreadVolatilityWatchObservation",
        "ResearchMarketSpreadVolatilityWatchReasonCodeCount",
        "ResearchMarketSpreadVolatilityWatchReport",
        "ResearchMarketSpreadVolatilityWatchRow",
        "build_research_market_spread_volatility_watch_report",
        "research_market_spread_volatility_watch_report_digest",
        "research_market_spread_volatility_watch_report_payload",
    )
    assert type(empty) is module.ResearchMarketSpreadVolatilityWatchReport
    assert is_dataclass(empty)
    assert empty.status == "block"
    assert empty.generated_at == GENERATED_AT
    assert empty.observation_count == ZERO
    assert empty.sample_count == ZERO
    assert empty.row_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.spread_instability_watch_count == ZERO
    assert empty.depth_decay_watch_count == ZERO
    assert empty.quote_age_watch_count == ZERO
    assert empty.cost_risk_pressure_count == ZERO
    assert empty.mean_quote_age_seconds == ZERO
    assert empty.max_composite_pressure == ZERO
    assert empty.manual_review_required is True
    assert empty.reason_codes == ("spread_volatility_watch_no_observations",)
    assert empty.reason_code_counts == (
        module.ResearchMarketSpreadVolatilityWatchReasonCodeCount(
            reason_code="spread_volatility_watch_no_observations",
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


def test_spread_volatility_watch_summarizes_instability_decay_age_and_cost_risk() -> None:
    module = api()
    built = report(
        observation("quiet-public-cohort"),
        observation(
            "watch-public-cohort",
            aggregate_spread_instability_ratio=d("0.030000"),
            depth_decay_ratio=d("0.300000"),
            quote_age_seconds=d("420.000000"),
            cost_risk_pressure_score=d("0.350000"),
            reason_codes=("manual_review",),
        ),
        observation(
            "blocked-public-cohort",
            sample_count=d("7"),
            aggregate_spread_instability_ratio=d("0.080000"),
            depth_decay_ratio=d("0.700000"),
            quote_age_seconds=d("1200.000000"),
            cost_risk_pressure_score=d("0.800000"),
        ),
    )

    assert built.status == "block"
    assert built.observation_count == d("3.000000")
    assert built.sample_count == d("17.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.spread_instability_watch_count == d("2.000000")
    assert built.depth_decay_watch_count == d("2.000000")
    assert built.quote_age_watch_count == d("2.000000")
    assert built.cost_risk_pressure_count == d("2.000000")
    assert built.mean_aggregate_spread_instability_ratio == d("0.038667")
    assert built.mean_depth_decay_ratio == d("0.350000")
    assert built.mean_quote_age_seconds == d("580.000000")
    assert built.mean_cost_risk_pressure_score == d("0.416667")
    assert built.mean_composite_pressure == d("0.394583")
    assert built.max_composite_pressure == d("1.000000")
    assert built.manual_review_required is True

    blocked, watched, passed = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert blocked.public_cohort == "blocked-public-cohort"
    assert blocked.composite_pressure == d("1.000000")
    assert blocked.reason_codes == (
        "spread_volatility_watch_composite_pressure_block",
        "spread_volatility_watch_cost_risk_pressure_block",
        "spread_volatility_watch_depth_decay_block",
        "spread_volatility_watch_quote_age_block",
        "spread_volatility_watch_spread_instability_block",
    )
    assert watched.public_cohort == "watch-public-cohort"
    assert watched.spread_instability_pressure == d("0.250000")
    assert watched.depth_decay_pressure == d("0.125000")
    assert watched.quote_age_pressure == d("0.200000")
    assert watched.cost_risk_pressure == d("0.125000")
    assert watched.composite_pressure == d("0.183750")
    assert watched.reason_codes == (
        "input_manual_review",
        "spread_volatility_watch_cost_risk_pressure_watch",
        "spread_volatility_watch_depth_decay_watch",
        "spread_volatility_watch_manual_review_watch",
        "spread_volatility_watch_quote_age_watch",
        "spread_volatility_watch_spread_instability_watch",
    )
    assert passed.reason_codes == ("spread_volatility_watch_clear",)
    assert all(row.paper_only and row.report_only and row.readonly for row in built.rows)


def test_composite_pressure_block_accepts_sub_block_component_pressure() -> None:
    module = api()
    built = report(
        observation(
            "composite-block-public-cohort",
            aggregate_spread_instability_ratio=d("0.052000"),
            depth_decay_ratio=d("0.570000"),
            quote_age_seconds=d("780.000000"),
            cost_risk_pressure_score=d("0.620000"),
        ),
    )

    (row,) = built.rows
    assert row.status == "block"
    assert row.composite_pressure == d("0.800000")
    assert config().block_composite_pressure <= row.composite_pressure < d("1.000000")
    assert "spread_volatility_watch_composite_pressure_block" in row.reason_codes
    assert "spread_volatility_watch_spread_instability_block" not in row.reason_codes
    payload = module.research_market_spread_volatility_watch_report_payload(built)
    assert payload["derived_validation_digest"] == built.derived_validation_digest
    assert not any(isinstance(value, float) for value in walk_payload_values(payload))


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        observation(
            "beta-public-cohort",
            aggregate_spread_instability_ratio=d("0.030000"),
            reason_codes=("zeta", "alpha"),
        ),
        observation("alpha-public-cohort"),
    )
    second = report(
        observation("alpha-public-cohort"),
        observation(
            "beta-public-cohort",
            aggregate_spread_instability_ratio=d("0.030000"),
            reason_codes=("alpha", "zeta"),
        ),
    )
    first_payload = module.research_market_spread_volatility_watch_report_payload(first)
    second_payload = module.research_market_spread_volatility_watch_report_payload(second)
    digest_payload = dict(first_payload)
    digest_payload.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()

    assert first == second
    assert first_payload == second_payload
    assert module.research_market_spread_volatility_watch_report_digest(first) == expected_digest
    assert first_payload["derived_validation_digest"] == expected_digest
    assert first_payload["generated_at"] == "2026-07-08T18:00:00+00:00"
    assert first_payload["observation_count"] == "2.000000"
    assert first_payload["rows"][0]["public_cohort"] == "beta-public-cohort"
    assert first_payload["rows"][0]["aggregate_spread_instability_ratio"] == "0.030000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(first_payload))
    assert not any(_has_forbidden_public_surface_key(key) for key in walk_payload_keys(first_payload))
    encoded = json.dumps(first_payload, sort_keys=True).lower()
    for fragment in (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "sizing",
        "recommendation",
    ):
        assert fragment not in encoded


def test_validation_rejects_bad_numeric_types_flags_times_and_digest_tampering() -> None:
    module = api()
    good = report(observation())

    with pytest.raises(FrozenInstanceError):
        good.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        good.rows[0].composite_pressure = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="aggregate_spread_instability_ratio"):
        observation(aggregate_spread_instability_ratio=0.006)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="depth_decay_ratio"):
        observation(depth_decay_ratio=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="quote_age_seconds"):
        observation(quote_age_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="observed_at"):
        replace(observation(), observed_at=datetime(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(), generated_at=_DatetimeSubclass(2026, 7, 8, 18, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)
    with pytest.raises(ValueError, match="public_cohort"):
        observation("market_slug:raw-source-id")
    with pytest.raises(ValueError, match="reason_code"):
        observation(reason_codes=("source_text",))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(good, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(good.rows[0], status="blocked")

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


def test_public_dataclasses_are_frozen_exact_types_without_side_effect_surfaces() -> None:
    module = api()
    built = report(observation())
    instances = (
        config(),
        observation(),
        built.rows[0],
        built.reason_code_counts[0],
        built,
    )
    for instance in instances:
        assert is_dataclass(instance)
        assert type(instance).__dataclass_params__.frozen
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True

    with pytest.raises(TypeError):
        type("BadConfig", (module.ResearchMarketSpreadVolatilityWatchConfig,), {})
    with pytest.raises(TypeError):
        type("BadObservation", (module.ResearchMarketSpreadVolatilityWatchObservation,), {})
    with pytest.raises(TypeError):
        type("BadRow", (module.ResearchMarketSpreadVolatilityWatchRow,), {})
    with pytest.raises(TypeError):
        type("BadReasonCount", (module.ResearchMarketSpreadVolatilityWatchReasonCodeCount,), {})
    with pytest.raises(TypeError):
        type("BadReport", (module.ResearchMarketSpreadVolatilityWatchReport,), {})

    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    for fragment in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "postgres",
        "psycopg",
        "sqlalchemy",
        "web3",
        "clob",
        "place_order",
        "submit_order",
        "cancel_order",
        "wallet",
        "private_key",
        "execute_trade",
        "trade_recommendation",
        "position_size",
        "live_trading",
        "sizing",
        "recommendation",
        "buy_",
        "sell_",
        "connect(",
        "open(",
    ):
        assert fragment not in source

    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type) and is_dataclass(exported):
            names = {field.name for field in fields(exported)}
            assert {"paper_only", "report_only", "readonly"} <= names


def _has_forbidden_public_surface_key(key: str) -> bool:
    normalized = key.lower()
    forbidden_fragments = (
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "size",
        "sizing",
        "recommendation",
    )
    return any(fragment in normalized for fragment in forbidden_fragments)
