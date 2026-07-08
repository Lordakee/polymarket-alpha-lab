from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_market_quote_staleness_exception_report"
GENERATED_AT = datetime(2026, 7, 8, 20, 30, tzinfo=UTC)
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
            module.DEFAULT_RESEARCH_MARKET_QUOTE_STALENESS_EXCEPTION_CONFIG_VERSION
        ),
        "watch_quote_age_seconds": d("120.000000"),
        "block_quote_age_seconds": d("300.000000"),
        "watch_spread_ratio": d("0.020000"),
        "block_spread_ratio": d("0.060000"),
        "watch_depth_pressure": d("0.250000"),
        "block_depth_pressure": d("0.650000"),
        "watch_cost_staleness_pressure": d("0.300000"),
        "block_cost_staleness_pressure": d("0.700000"),
        "watch_exception_pressure": d("0.300000"),
        "block_exception_pressure": d("0.700000"),
        "quote_age_weight": d("0.350000"),
        "spread_weight": d("0.250000"),
        "depth_weight": d("0.200000"),
        "cost_staleness_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchMarketQuoteStalenessExceptionConfig(**values)


def observation(
    public_segment: str = "quiet-public-segment",
    *,
    observed_at: datetime | None = None,
    sample_count: Decimal = d("4"),
    aggregate_quote_age_seconds: Decimal = d("60.000000"),
    aggregate_spread_ratio: Decimal = d("0.010000"),
    aggregate_depth_pressure: Decimal = d("0.100000"),
    cost_staleness_pressure: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketQuoteStalenessExceptionObservation(
        public_segment=public_segment,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=4),
        sample_count=sample_count,
        aggregate_quote_age_seconds=aggregate_quote_age_seconds,
        aggregate_spread_ratio=aggregate_spread_ratio,
        aggregate_depth_pressure=aggregate_depth_pressure,
        cost_staleness_pressure=cost_staleness_pressure,
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
    return module.build_research_market_quote_staleness_exception_report(
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
        "DEFAULT_RESEARCH_MARKET_QUOTE_STALENESS_EXCEPTION_CONFIG_VERSION",
        "STATUSES",
        "ResearchMarketQuoteStalenessExceptionConfig",
        "ResearchMarketQuoteStalenessExceptionObservation",
        "ResearchMarketQuoteStalenessExceptionReasonCodeCount",
        "ResearchMarketQuoteStalenessExceptionReport",
        "ResearchMarketQuoteStalenessExceptionRow",
        "build_research_market_quote_staleness_exception_report",
        "research_market_quote_staleness_exception_report_digest",
        "research_market_quote_staleness_exception_report_payload",
    )
    assert type(empty) is module.ResearchMarketQuoteStalenessExceptionReport
    assert is_dataclass(empty)
    assert empty.status == "block"
    assert empty.generated_at == GENERATED_AT
    assert empty.observation_count == ZERO
    assert empty.sample_count == ZERO
    assert empty.row_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.quote_age_exception_count == ZERO
    assert empty.spread_exception_count == ZERO
    assert empty.depth_exception_count == ZERO
    assert empty.cost_staleness_exception_count == ZERO
    assert empty.mean_aggregate_quote_age_seconds == ZERO
    assert empty.max_exception_pressure == ZERO
    assert empty.reason_codes == ("quote_staleness_exception_no_observations",)
    assert empty.reason_code_counts == (
        module.ResearchMarketQuoteStalenessExceptionReasonCodeCount(
            reason_code="quote_staleness_exception_no_observations",
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


def test_exception_report_aggregates_quote_age_spread_depth_and_cost_pressure() -> None:
    built = report(
        observation("quiet-public-segment"),
        observation(
            "watch-public-segment",
            sample_count=d("5"),
            aggregate_quote_age_seconds=d("180.000000"),
            aggregate_spread_ratio=d("0.030000"),
            aggregate_depth_pressure=d("0.300000"),
            cost_staleness_pressure=d("0.350000"),
        ),
        observation(
            "blocked-public-segment",
            sample_count=d("6"),
            aggregate_quote_age_seconds=d("360.000000"),
            aggregate_spread_ratio=d("0.080000"),
            aggregate_depth_pressure=d("0.700000"),
            cost_staleness_pressure=d("0.800000"),
        ),
    )

    assert built.status == "block"
    assert built.observation_count == d("3.000000")
    assert built.sample_count == d("15.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.quote_age_exception_count == d("2.000000")
    assert built.spread_exception_count == d("2.000000")
    assert built.depth_exception_count == d("2.000000")
    assert built.cost_staleness_exception_count == d("2.000000")
    assert built.mean_aggregate_quote_age_seconds == d("200.000000")
    assert built.max_aggregate_quote_age_seconds == d("360.000000")
    assert built.mean_aggregate_spread_ratio == d("0.040000")
    assert built.mean_aggregate_depth_pressure == d("0.366667")
    assert built.mean_cost_staleness_pressure == d("0.416667")
    assert built.mean_exception_pressure == d("0.566105")
    assert built.max_exception_pressure == d("1.000000")
    assert built.reason_codes == (
        "quote_staleness_exception_report_quote_age_detected",
        "quote_staleness_exception_report_spread_detected",
        "quote_staleness_exception_report_depth_detected",
        "quote_staleness_exception_report_cost_staleness_detected",
        "quote_staleness_exception_report_exception_pressure_detected",
        "quote_staleness_exception_report_review_required",
    )

    blocked, watched, passed = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert blocked.public_segment == "blocked-public-segment"
    assert blocked.quote_age_pressure == d("1.000000")
    assert blocked.spread_pressure == d("1.000000")
    assert blocked.depth_pressure == d("1.000000")
    assert blocked.cost_pressure == d("1.000000")
    assert blocked.exception_pressure == d("1.000000")
    assert blocked.reason_codes == (
        "quote_staleness_exception_cost_staleness_block",
        "quote_staleness_exception_depth_block",
        "quote_staleness_exception_exception_pressure_block",
        "quote_staleness_exception_quote_age_block",
        "quote_staleness_exception_spread_block",
    )
    assert watched.public_segment == "watch-public-segment"
    assert watched.quote_age_pressure == d("0.600000")
    assert watched.spread_pressure == d("0.500000")
    assert watched.depth_pressure == d("0.461538")
    assert watched.cost_pressure == d("0.500000")
    assert watched.exception_pressure == d("0.527308")
    assert watched.reason_codes == (
        "quote_staleness_exception_cost_staleness_watch",
        "quote_staleness_exception_depth_watch",
        "quote_staleness_exception_exception_pressure_watch",
        "quote_staleness_exception_quote_age_watch",
        "quote_staleness_exception_spread_watch",
    )
    assert passed.reason_codes == ("quote_staleness_exception_clear",)
    assert all(row.paper_only and row.report_only and row.readonly for row in built.rows)


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        observation(
            "beta-public-segment",
            aggregate_quote_age_seconds=d("180.000000"),
            reason_codes=("zeta", "alpha"),
        ),
        observation("alpha-public-segment"),
    )
    second = report(
        observation("alpha-public-segment"),
        observation(
            "beta-public-segment",
            aggregate_quote_age_seconds=d("180.000000"),
            reason_codes=("alpha", "zeta"),
        ),
    )
    first_payload = module.research_market_quote_staleness_exception_report_payload(first)
    second_payload = module.research_market_quote_staleness_exception_report_payload(second)
    digest_payload = dict(first_payload)
    digest_payload.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(
            digest_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()

    assert first == second
    assert first_payload == second_payload
    assert (
        module.research_market_quote_staleness_exception_report_digest(first)
        == expected_digest
    )
    assert (
        module.research_market_quote_staleness_exception_report_digest(first_payload)
        == expected_digest
    )
    assert first_payload["derived_validation_digest"] == expected_digest
    assert first_payload["generated_at"] == "2026-07-08T20:30:00+00:00"
    assert first_payload["observation_count"] == "2.000000"
    assert first_payload["rows"][0]["public_segment"] == "beta-public-segment"
    assert first_payload["rows"][0]["aggregate_quote_age_seconds"] == "180.000000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(first_payload))
    assert not any(_has_forbidden_public_surface_key(key) for key in walk_payload_keys(first_payload))
    encoded = json.dumps(first_payload, sort_keys=True).lower()
    for fragment in (
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
        "sizing",
        "recommendation",
    ):
        assert fragment not in encoded


def test_validation_rejects_bad_numeric_types_flags_surfaces_and_digest_tampering() -> None:
    module = api()
    good = report(observation())

    with pytest.raises(FrozenInstanceError):
        good.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        good.rows[0].exception_pressure = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="aggregate_quote_age_seconds"):
        observation(aggregate_quote_age_seconds=60)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="aggregate_spread_ratio"):
        observation(aggregate_spread_ratio=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="aggregate_depth_pressure"):
        observation(aggregate_depth_pressure=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="cost_staleness_pressure"):
        observation(cost_staleness_pressure=d("-0.100000"))
    with pytest.raises(ValueError, match="observed_at"):
        replace(observation(), observed_at=datetime(2026, 7, 8, 20, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(), generated_at=_DatetimeSubclass(2026, 7, 8, 20, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)
    with pytest.raises(ValueError, match="public_segment"):
        observation("market_id-secret")
    with pytest.raises(ValueError, match="reason_code"):
        observation(reason_codes=("source_text",))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(good, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(good.rows[0], status="blocked")
    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.research_market_quote_staleness_exception_report_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "value": 1.5},
        )
    with pytest.raises(ValueError, match="unsafe surface"):
        module.research_market_quote_staleness_exception_report_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "wallet": "redacted"},
        )

    tampered = replace(good)
    object.__setattr__(tampered, "observation_count", d("2.000000"))
    with pytest.raises(ValueError, match="observation_count"):
        module.research_market_quote_staleness_exception_report_payload(tampered)

    bad_flag_row = replace(good.rows[0])
    object.__setattr__(bad_flag_row, "report_only", False)
    bad_nested = replace(good)
    object.__setattr__(bad_nested, "rows", (bad_flag_row,))
    with pytest.raises(ValueError, match="report_only"):
        module.research_market_quote_staleness_exception_report_payload(bad_nested)

    payload = module.research_market_quote_staleness_exception_report_payload(good)
    payload["observation_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_quote_staleness_exception_report_digest(payload)


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
        type("BadConfig", (module.ResearchMarketQuoteStalenessExceptionConfig,), {})
    with pytest.raises(TypeError):
        type("BadObservation", (module.ResearchMarketQuoteStalenessExceptionObservation,), {})
    with pytest.raises(TypeError):
        type("BadRow", (module.ResearchMarketQuoteStalenessExceptionRow,), {})
    with pytest.raises(TypeError):
        type("BadReasonCount", (module.ResearchMarketQuoteStalenessExceptionReasonCodeCount,), {})
    with pytest.raises(TypeError):
        type("BadReport", (module.ResearchMarketQuoteStalenessExceptionReport,), {})

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
        "auth",
        "wallet",
        "broker",
        "signing",
        "network",
        "database",
        "live_trading",
        "private_key",
        "execute_trade",
        "trade_recommendation",
        "position_size",
        "recommendation",
        "sizing",
        "buy_",
        "sell_",
        "connect(",
        "open(",
    ):
        assert fragment not in source

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"

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
