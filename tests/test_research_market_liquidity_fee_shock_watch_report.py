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


MODULE_NAME = "polymarket_alpha_lab.research_market_liquidity_fee_shock_watch_report"
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
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
            module.DEFAULT_RESEARCH_MARKET_LIQUIDITY_FEE_SHOCK_WATCH_CONFIG_VERSION
        ),
        "watch_liquidity_shock_ratio": d("0.200000"),
        "block_liquidity_shock_ratio": d("0.500000"),
        "watch_fee_shock_ratio": d("0.030000"),
        "block_fee_shock_ratio": d("0.100000"),
        "watch_spread_ratio": d("0.050000"),
        "block_spread_ratio": d("0.120000"),
        "watch_quote_staleness_seconds": d("300.000000"),
        "block_quote_staleness_seconds": d("900.000000"),
        "watch_catalyst_pressure": d("0.600000"),
        "block_catalyst_pressure": d("0.850000"),
    }
    values.update(overrides)
    return module.ResearchMarketLiquidityFeeShockWatchConfig(**values)


def observation(
    public_bucket: str = "public-liquidity-fee",
    *,
    observed_at: datetime | None = None,
    sample_count: Decimal = d("5"),
    liquidity_shock_ratio: Decimal = d("0.050000"),
    fee_shock_ratio: Decimal = d("0.010000"),
    bid_ask_spread_ratio: Decimal = d("0.010000"),
    quote_staleness_seconds: Decimal = d("60.000000"),
    catalyst_pressure: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
) -> Any:
    module = api()
    return module.ResearchMarketLiquidityFeeShockWatchObservation(
        public_bucket=public_bucket,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=5),
        sample_count=sample_count,
        liquidity_shock_ratio=liquidity_shock_ratio,
        fee_shock_ratio=fee_shock_ratio,
        bid_ask_spread_ratio=bid_ask_spread_ratio,
        quote_staleness_seconds=quote_staleness_seconds,
        catalyst_pressure=catalyst_pressure,
        reason_codes=reason_codes,
    )


def report(
    *observations: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_market_liquidity_fee_shock_watch_report(
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


def expected_digest(payload: dict[str, object]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    return hashlib.sha256(
        json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def test_liquidity_fee_shock_watch_report_summarizes_block_watch_pass_rows() -> None:
    module = api()
    built = report(
        observation("quiet-public-bucket"),
        observation(
            "watch-public-bucket",
            liquidity_shock_ratio=d("0.250000"),
            fee_shock_ratio=d("0.040000"),
            bid_ask_spread_ratio=d("0.060000"),
            quote_staleness_seconds=d("400.000000"),
            catalyst_pressure=d("0.650000"),
        ),
        observation(
            "blocked-public-bucket",
            sample_count=d("7"),
            liquidity_shock_ratio=d("0.550000"),
            fee_shock_ratio=d("0.110000"),
            bid_ask_spread_ratio=d("0.130000"),
            quote_staleness_seconds=d("1200.000000"),
            catalyst_pressure=d("0.900000"),
            reason_codes=("public_fee_notice",),
        ),
    )

    assert type(built) is module.ResearchMarketLiquidityFeeShockWatchReport
    assert is_dataclass(built)
    assert module.STATUSES == ("pass", "watch", "block")
    assert built.status == "block"
    assert built.generated_at == GENERATED_AT
    assert built.observation_count == d("3.000000")
    assert built.sample_count == d("17.000000")
    assert built.row_count == d("3.000000")
    assert built.block_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.pass_count == d("1.000000")
    assert built.liquidity_shock_watch_count == d("2.000000")
    assert built.fee_shock_watch_count == d("2.000000")
    assert built.spread_watch_count == d("2.000000")
    assert built.quote_stale_count == d("2.000000")
    assert built.catalyst_pressure_count == d("2.000000")
    assert built.max_shock_score == d("1.000000")

    blocked, watched, passed = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert blocked.public_bucket == "blocked-public-bucket"
    assert blocked.reason_codes == (
        "input_public_fee_notice",
        "research_market_liquidity_fee_shock_watch_catalyst_pressure_block",
        "research_market_liquidity_fee_shock_watch_fee_shock_block",
        "research_market_liquidity_fee_shock_watch_liquidity_shock_block",
        "research_market_liquidity_fee_shock_watch_quote_staleness_block",
        "research_market_liquidity_fee_shock_watch_spread_block",
    )
    assert watched.reason_codes == (
        "research_market_liquidity_fee_shock_watch_catalyst_pressure_watch",
        "research_market_liquidity_fee_shock_watch_fee_shock_watch",
        "research_market_liquidity_fee_shock_watch_liquidity_shock_watch",
        "research_market_liquidity_fee_shock_watch_quote_staleness_watch",
        "research_market_liquidity_fee_shock_watch_spread_watch",
    )
    assert passed.reason_codes == ("research_market_liquidity_fee_shock_watch_clear",)
    assert all(row.paper_only and row.report_only and row.readonly for row in built.rows)
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True


def test_payload_digest_is_deterministic_and_uses_decimal_strings() -> None:
    module = api()
    empty = report()

    assert empty.status == "block"
    assert empty.observation_count == ZERO
    assert empty.row_count == ZERO
    assert empty.rows == ()
    assert empty.reason_codes == (
        "research_market_liquidity_fee_shock_watch_no_observations",
    )
    assert empty.reason_code_counts == (
        module.ResearchMarketLiquidityFeeShockWatchReasonCodeCount(
            reason_code="research_market_liquidity_fee_shock_watch_no_observations",
            count=d("1.000000"),
            sample_ratio=ZERO,
        ),
    )

    first = report(
        observation("beta-public-bucket", fee_shock_ratio=d("0.040000")),
        observation("alpha-public-bucket"),
    )
    second = report(
        observation("alpha-public-bucket"),
        observation("beta-public-bucket", fee_shock_ratio=d("0.040000")),
    )
    first_payload = module.research_market_liquidity_fee_shock_watch_report_payload(first)
    second_payload = module.research_market_liquidity_fee_shock_watch_report_payload(second)

    assert first == second
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True)
    assert first_payload["derived_validation_digest"] == expected_digest(first_payload)
    assert first.derived_validation_digest == first_payload["derived_validation_digest"]
    assert first_payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert first_payload["observation_count"] == "2.000000"
    assert first_payload["rows"][0]["public_bucket"] == "beta-public-bucket"
    assert first_payload["rows"][0]["fee_shock_ratio"] == "0.040000"
    assert first_payload["reason_code_counts"][0]["count"] == "1.000000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(first_payload))

    duplicate_newer = observation(
        "duplicate-public-bucket",
        observed_at=GENERATED_AT - timedelta(minutes=4),
        sample_count=d("5"),
        liquidity_shock_ratio=d("0.050000"),
    )
    duplicate_older = observation(
        "duplicate-public-bucket",
        observed_at=GENERATED_AT - timedelta(minutes=7),
        sample_count=d("6"),
        liquidity_shock_ratio=d("0.060000"),
    )
    duplicate_first = report(duplicate_newer, duplicate_older)
    duplicate_second = report(duplicate_older, duplicate_newer)

    assert duplicate_first == duplicate_second
    assert module.research_market_liquidity_fee_shock_watch_report_payload(
        duplicate_first,
    ) == module.research_market_liquidity_fee_shock_watch_report_payload(
        duplicate_second,
    )


def test_payload_revalidates_tampered_reports_and_public_safety() -> None:
    module = api()
    good = report(observation())

    tampered_count = replace(good)
    object.__setattr__(tampered_count, "observation_count", d("2.000000"))
    with pytest.raises(ValueError, match="observation_count"):
        module.research_market_liquidity_fee_shock_watch_report_payload(tampered_count)

    tampered_digest = replace(good)
    object.__setattr__(tampered_digest, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_liquidity_fee_shock_watch_report_payload(tampered_digest)

    unsafe_row = replace(good.rows[0])
    object.__setattr__(unsafe_row, "public_bucket", "raw-candidate-market-id")
    tampered_row = replace(good)
    object.__setattr__(tampered_row, "rows", (unsafe_row,))
    with pytest.raises(ValueError, match="public_bucket|unsafe"):
        module.research_market_liquidity_fee_shock_watch_report_payload(tampered_row)

    tampered_flags = replace(good)
    object.__setattr__(tampered_flags, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        module.research_market_liquidity_fee_shock_watch_report_payload(tampered_flags)

    bad_flag_row = replace(good.rows[0])
    object.__setattr__(bad_flag_row, "paper_only", False)
    tampered_nested_flags = replace(good)
    object.__setattr__(tampered_nested_flags, "rows", (bad_flag_row,))
    with pytest.raises(ValueError, match="paper_only"):
        module.research_market_liquidity_fee_shock_watch_report_payload(
            tampered_nested_flags,
        )

    with pytest.raises(ValueError, match="ResearchMarketLiquidityFeeShockWatchReport"):
        module.research_market_liquidity_fee_shock_watch_report_payload({"payload": 1})
    with pytest.raises(ValueError, match="public_bucket"):
        observation(public_bucket="candidate-slug-question")
    with pytest.raises(ValueError, match="reason_codes"):
        observation(reason_codes=("wallet_order_trade_token",))

    encoded = json.dumps(
        module.research_market_liquidity_fee_shock_watch_report_payload(good),
    ).lower()
    for unsafe in (
        "candidate",
        "market_id",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "raw",
        "://",
        "?",
    ):
        assert unsafe not in encoded


@pytest.mark.parametrize(
    "unsafe_text",
    (
        "auth",
        "live",
        "trading",
        "sizing",
        "recommendation",
        "execution",
    ),
)
def test_public_text_rejects_operational_leakage(unsafe_text: str) -> None:
    with pytest.raises(ValueError, match="unsafe"):
        observation(public_bucket=f"public-{unsafe_text}-bucket")
    with pytest.raises(ValueError, match="unsafe"):
        observation(reason_codes=(f"public_{unsafe_text}_notice",))


def test_report_rejects_unsupported_config_version_before_signing() -> None:
    built = report(observation())

    with pytest.raises(ValueError, match="config_version"):
        replace(
            built,
            config_version="research-market-liquidity-fee-shock-watch-v999",
            derived_validation_digest=None,
        )


def test_public_count_fields_require_whole_decimals() -> None:
    module = api()
    built = report(observation())

    with pytest.raises(ValueError, match="count"):
        module.ResearchMarketLiquidityFeeShockWatchReasonCodeCount(
            reason_code="research_market_liquidity_fee_shock_watch_clear",
            count=d("0.500000"),
            sample_ratio=d("0.500000"),
        )
    with pytest.raises(ValueError, match="liquidity_shock_watch_count"):
        replace(
            built,
            liquidity_shock_watch_count=d("0.500000"),
            derived_validation_digest=None,
        )


def test_dataclasses_are_frozen_hard_flagged_decimal_only_and_exact_typed() -> None:
    module = api()
    built = report(observation())

    public_types = (
        module.ResearchMarketLiquidityFeeShockWatchConfig,
        module.ResearchMarketLiquidityFeeShockWatchObservation,
        module.ResearchMarketLiquidityFeeShockWatchReasonCodeCount,
        module.ResearchMarketLiquidityFeeShockWatchReport,
        module.ResearchMarketLiquidityFeeShockWatchRow,
    )
    for public_type in public_types:
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen
        assert all("float" not in str(field.type) for field in fields(public_type))
        assert all("int" not in str(field.type) for field in fields(public_type))
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Unsafe{public_type.__name__}", (public_type,), {})

    with pytest.raises(FrozenInstanceError):
        built.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].shock_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")
    with pytest.raises(ValueError, match="watch_liquidity_shock_ratio"):
        config(watch_liquidity_shock_ratio=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="liquidity_shock_ratio"):
        observation(liquidity_shock_ratio=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="quote_staleness_seconds"):
        observation(quote_staleness_seconds=60)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(), generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="public_bucket"):
        observation(public_bucket="source-url-raw")
    with pytest.raises(ValueError, match="reason_codes"):
        observation(reason_codes=("NeedsReview",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(), paper_only=False)


def test_owned_module_has_no_io_db_network_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_liquidity_fee_shock_watch_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "psycopg",
        "sqlite",
        "supabase",
        "private_key",
        "api_key",
        "credential",
        "buy(",
        "sell(",
        "position",
        "recommendation",
        "sizing",
        "submit",
        "cancel",
        "live trading",
    )

    assert all(term not in source for term in forbidden_terms)
