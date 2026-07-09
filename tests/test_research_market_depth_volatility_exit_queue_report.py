from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 14, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 13, 45, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_market_depth_volatility_exit_queue_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_depth_volatility_exit_queue_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_DEPTH_VOLATILITY_EXIT_QUEUE_REPORT_CONFIG_VERSION
        ),
        "minimum_depth_coverage_ratio": d("1.000000"),
        "depth_coverage_watch_threshold": d("0.750000"),
        "depth_coverage_block_threshold": d("0.350000"),
        "exit_queue_pressure_watch_threshold": d("0.500000"),
        "exit_queue_pressure_block_threshold": d("1.200000"),
        "depth_volatility_watch_threshold": d("0.200000"),
        "depth_volatility_block_threshold": d("0.600000"),
        "price_volatility_watch_threshold": d("0.080000"),
        "price_volatility_block_threshold": d("0.160000"),
        "spread_width_watch_threshold": d("0.030000"),
        "spread_width_block_threshold": d("0.070000"),
        "book_age_watch_seconds": d("300.000000"),
        "book_age_block_seconds": d("900.000000"),
        "watch_exit_queue_risk_score": d("0.350000"),
        "block_exit_queue_risk_score": d("0.700000"),
        "depth_coverage_weight": d("0.300000"),
        "exit_queue_pressure_weight": d("0.250000"),
        "depth_volatility_weight": d("0.150000"),
        "price_volatility_weight": d("0.150000"),
        "spread_width_weight": d("0.100000"),
        "book_age_weight": d("0.050000"),
    }
    values.update(overrides)
    return module.ResearchMarketDepthVolatilityExitQueueConfig(**values)


def observation(
    internal_observation_ref: str,
    *,
    planned_exit_notional: Decimal,
    available_exit_depth: Decimal,
    exit_queue_notional: Decimal,
    depth_volatility_rate: Decimal,
    price_volatility_rate: Decimal,
    spread_width_rate: Decimal,
    book_age_seconds: Decimal,
    observed_at: datetime = OBSERVED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketDepthVolatilityExitQueueObservation(
        internal_observation_ref=internal_observation_ref,
        observed_at=observed_at,
        planned_exit_notional=planned_exit_notional,
        available_exit_depth=available_exit_depth,
        exit_queue_notional=exit_queue_notional,
        depth_volatility_rate=depth_volatility_rate,
        price_volatility_rate=price_volatility_rate,
        spread_width_rate=spread_width_rate,
        book_age_seconds=book_age_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*observations: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_research_market_depth_volatility_exit_queue_report(
        observations,
        config=config() if cfg is None else cfg,
        generated_at=GENERATED_AT,
    )


def walk_payload(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            yield from walk_payload(item)
        return
    yield value


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_depth_volatility_exit_queue_report_scores_sorts_and_aggregates() -> None:
    module = api()
    result = build_report(
        observation(
            "candidate-pass market-slug question https://example.invalid token=secret",
            planned_exit_notional=d("100.000000"),
            available_exit_depth=d("100.000000"),
            exit_queue_notional=d("0.000000"),
            depth_volatility_rate=d("0.000000"),
            price_volatility_rate=d("0.000000"),
            spread_width_rate=d("0.000000"),
            book_age_seconds=d("0.000000"),
        ),
        observation(
            "candidate-block market-id question dsn=postgres table=events",
            planned_exit_notional=d("100.000000"),
            available_exit_depth=d("20.000000"),
            exit_queue_notional=d("150.000000"),
            depth_volatility_rate=d("0.700000"),
            price_volatility_rate=d("0.180000"),
            spread_width_rate=d("0.080000"),
            book_age_seconds=d("1200.000000"),
        ),
        observation(
            "candidate-watch market-slug source text wallet order trade",
            planned_exit_notional=d("100.000000"),
            available_exit_depth=d("60.000000"),
            exit_queue_notional=d("60.000000"),
            depth_volatility_rate=d("0.300000"),
            price_volatility_rate=d("0.090000"),
            spread_width_rate=d("0.040000"),
            book_age_seconds=d("360.000000"),
        ),
    )

    assert module.MARKET_DEPTH_VOLATILITY_EXIT_QUEUE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert type(result) is module.ResearchMarketDepthVolatilityExitQueueReport
    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.observation_count == d("3.000000")
    assert result.pass_count == ONE
    assert result.watch_count == ONE
    assert result.block_count == ONE
    assert result.min_depth_coverage_ratio == d("0.200000")
    assert result.max_exit_queue_pressure_ratio == d("1.500000")
    assert result.max_depth_volatility_rate == d("0.700000")
    assert result.max_price_volatility_rate == d("0.180000")
    assert result.max_exit_queue_risk_score == d("0.940000")
    assert result.average_exit_queue_risk_score == d("0.473839")
    assert result.status == "block"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    block_row, watch_row, pass_row = result.rows
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    assert tuple(row.public_row_ref for row in result.rows) == (
        "depth_volatility_exit_queue_row_001",
        "depth_volatility_exit_queue_row_002",
        "depth_volatility_exit_queue_row_003",
    )
    assert block_row.depth_coverage_ratio == d("0.200000")
    assert block_row.exit_queue_pressure_ratio == d("1.500000")
    assert block_row.exit_queue_risk_score == d("0.940000")
    assert block_row.reason_codes == (
        "depth_coverage_block",
        "exit_queue_pressure_block",
        "depth_volatility_block",
        "price_volatility_block",
        "spread_width_block",
        "book_age_block",
        "exit_queue_risk_score_block",
    )
    assert watch_row.exit_queue_risk_score == d("0.481518")
    assert watch_row.reason_codes == (
        "depth_coverage_watch",
        "exit_queue_pressure_watch",
        "depth_volatility_watch",
        "price_volatility_watch",
        "spread_width_watch",
        "book_age_watch",
        "exit_queue_risk_score_watch",
    )
    assert pass_row.exit_queue_risk_score == ZERO
    assert pass_row.reason_codes == ("depth_volatility_exit_queue_pass",)
    assert_digest(block_row.row_validation_digest)
    assert_digest(result.derived_validation_digest)


def test_public_payload_is_deterministic_digest_bound_decimal_only_and_safe() -> None:
    module = api()
    private_ref = (
        "candidate-alpha market-id market-slug raw question text "
        "https://example.invalid source_url=https://example.invalid "
        "source_text=secret dsn=postgres table=events token=secret wallet order trade"
    )
    first = build_report(
        observation(
            private_ref,
            planned_exit_notional=d("100.000000"),
            available_exit_depth=d("20.000000"),
            exit_queue_notional=d("150.000000"),
            depth_volatility_rate=d("0.700000"),
            price_volatility_rate=d("0.180000"),
            spread_width_rate=d("0.080000"),
            book_age_seconds=d("1200.000000"),
        ),
    )
    second = build_report(
        observation(
            private_ref,
            observed_at=OBSERVED_AT.astimezone(timezone(timedelta(hours=-4))),
            planned_exit_notional=d("100.000000"),
            available_exit_depth=d("20.000000"),
            exit_queue_notional=d("150.000000"),
            depth_volatility_rate=d("0.700000"),
            price_volatility_rate=d("0.180000"),
            spread_width_rate=d("0.080000"),
            book_age_seconds=d("1200.000000"),
        ),
    )

    payload = module.research_market_depth_volatility_exit_queue_report_payload(first)
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    encoded_digest_payload = json.dumps(
        digest_payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    encoded_payload = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert payload == module.research_market_depth_volatility_exit_queue_report_payload(
        second,
    )
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert module.research_market_depth_volatility_exit_queue_report_digest(first) == (
        first.derived_validation_digest
    )
    assert hashlib.sha256(encoded_digest_payload.encode("utf-8")).hexdigest() == (
        first.derived_validation_digest
    )
    assert payload["generated_at"] == "2026-07-09T14:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["rows"][0]["available_exit_depth"] == "20.000000"
    assert payload["rows"][0]["internal_observation_ref_digest"] == (
        first.rows[0].internal_observation_ref_digest
    )
    assert private_ref not in encoded_payload
    assert all(
        fragment not in encoded_payload.lower()
        for fragment in (
            "candidate-alpha",
            "market-id",
            "market_id",
            "market-slug",
            "market_slug",
            "raw question",
            "source_url",
            "source_text",
            "https://example.invalid",
            "dsn=postgres",
            "table=events",
            "token=secret",
            "wallet",
            "order",
            "trade",
            "live",
            "recommend",
            "sizing",
        )
    )
    assert not any(type(value) in (float, int) for value in walk_payload(payload))


def test_empty_input_blocks_without_public_private_identifier_surface() -> None:
    result = build_report()

    assert result.observation_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.min_depth_coverage_ratio == ZERO
    assert result.max_exit_queue_pressure_ratio == ZERO
    assert result.max_depth_volatility_rate == ZERO
    assert result.max_price_volatility_rate == ZERO
    assert result.max_exit_queue_risk_score == ZERO
    assert result.average_exit_queue_risk_score is None
    assert result.status == "block"
    assert result.rows == ()
    assert result.reason_codes == (
        "missing_depth_volatility_exit_queue_observations",
    )
    assert_digest(result.derived_validation_digest)


def test_validation_enforces_frozen_decimal_only_flags_and_digest_contract() -> None:
    module = api()
    result = build_report(
        observation(
            "internal-alpha",
            planned_exit_notional=d("100.000000"),
            available_exit_depth=d("100.000000"),
            exit_queue_notional=d("0.000000"),
            depth_volatility_rate=d("0.000000"),
            price_volatility_rate=d("0.000000"),
            spread_width_rate=d("0.000000"),
            book_age_seconds=d("0.000000"),
        ),
    )

    assert is_dataclass(module.ResearchMarketDepthVolatilityExitQueueConfig)
    assert is_dataclass(module.ResearchMarketDepthVolatilityExitQueueObservation)
    assert is_dataclass(module.ResearchMarketDepthVolatilityExitQueueRow)
    assert is_dataclass(module.ResearchMarketDepthVolatilityExitQueueReport)
    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        observation(
            "internal-flags",
            planned_exit_notional=d("100.000000"),
            available_exit_depth=d("100.000000"),
            exit_queue_notional=d("0.000000"),
            depth_volatility_rate=d("0.000000"),
            price_volatility_rate=d("0.000000"),
            spread_width_rate=d("0.000000"),
            book_age_seconds=d("0.000000"),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="planned_exit_notional"):
        observation(
            "internal-decimal",
            planned_exit_notional=100,  # type: ignore[arg-type]
            available_exit_depth=d("100.000000"),
            exit_queue_notional=d("0.000000"),
            depth_volatility_rate=d("0.000000"),
            price_volatility_rate=d("0.000000"),
            spread_width_rate=d("0.000000"),
            book_age_seconds=d("0.000000"),
        )
    with pytest.raises(ValueError, match="available_exit_depth"):
        observation(
            "internal-decimal-subclass",
            planned_exit_notional=d("100.000000"),
            available_exit_depth=_DecimalSubclass("100.000000"),
            exit_queue_notional=d("0.000000"),
            depth_volatility_rate=d("0.000000"),
            price_volatility_rate=d("0.000000"),
            spread_width_rate=d("0.000000"),
            book_age_seconds=d("0.000000"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_depth_volatility_exit_queue_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 9, 14, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_depth_volatility_exit_queue_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 9, 14, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="internal_observation_ref values"):
        build_report(
            observation(
                "internal-dupe",
                planned_exit_notional=d("100.000000"),
                available_exit_depth=d("100.000000"),
                exit_queue_notional=d("0.000000"),
                depth_volatility_rate=d("0.000000"),
                price_volatility_rate=d("0.000000"),
                spread_width_rate=d("0.000000"),
                book_age_seconds=d("0.000000"),
            ),
            observation(
                "internal-dupe",
                planned_exit_notional=d("100.000000"),
                available_exit_depth=d("100.000000"),
                exit_queue_notional=d("0.000000"),
                depth_volatility_rate=d("0.000000"),
                price_volatility_rate=d("0.000000"),
                spread_width_rate=d("0.000000"),
                book_age_seconds=d("0.000000"),
            ),
        )
    with pytest.raises(ValueError, match="status"):
        replace(result.rows[0], status="halt")
    with pytest.raises(ValueError, match="row_validation_digest"):
        replace(result.rows[0], row_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)


def test_public_payload_validator_rejects_private_surface_and_bad_digest() -> None:
    module = api()
    result = build_report(
        observation(
            "internal-alpha",
            planned_exit_notional=d("100.000000"),
            available_exit_depth=d("100.000000"),
            exit_queue_notional=d("0.000000"),
            depth_volatility_rate=d("0.000000"),
            price_volatility_rate=d("0.000000"),
            spread_width_rate=d("0.000000"),
            book_age_seconds=d("0.000000"),
        ),
    )
    payload = module.research_market_depth_volatility_exit_queue_report_payload(result)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["candidate_id"] = "hidden"
    with pytest.raises(ValueError, match="public payload"):
        module.validate_research_market_depth_volatility_exit_queue_public_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["notes"] = "https://example.invalid/source"
    with pytest.raises(ValueError, match="public payload"):
        module.validate_research_market_depth_volatility_exit_queue_public_payload(
            unsafe_value_payload,
        )

    bad_digest_payload = dict(payload)
    bad_digest_payload["observation_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_depth_volatility_exit_queue_public_payload(
            bad_digest_payload,
        )


def test_owned_module_has_no_runtime_side_effect_or_advice_surface() -> None:
    module_text = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
    )

    assert all(term not in module_text for term in forbidden_terms)
