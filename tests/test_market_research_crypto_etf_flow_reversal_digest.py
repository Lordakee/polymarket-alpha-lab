from __future__ import annotations

import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_etf_flow_reversal_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "market-research-crypto-etf-flow-reversal-digest-v0",
        "watch_reversal_abs_usd": d("50000000.000000"),
        "blocked_reversal_abs_usd": d("250000000.000000"),
        "max_source_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "min_confirmation_count": d("1.000000"),
        "min_flow_confidence": d("0.650000"),
    }
    values.update(overrides)
    return module.MarketResearchCryptoEtfFlowReversalDigestConfig(**values)


def observation(
    source_id: str = "source-alpha",
    *,
    research_key: str = "research.btc.etf.flow",
    market_slug: str = "crypto-etf-flow-reversal",
    asset_symbol: str = "btc",
    etf_ticker: str = "IBIT",
    current_net_flow_usd: Decimal = d("-325000000.000000"),
    previous_net_flow_usd: Decimal = d("180000000.000000"),
    source_count: Decimal = d("3.000000"),
    confirmation_count: Decimal = d("2.000000"),
    flow_confidence: Decimal = d("0.820000"),
    observed_at: datetime = GENERATED_AT - timedelta(seconds=60),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketResearchCryptoEtfFlowReversalObservation(
        source_id=source_id,
        research_key=research_key,
        market_slug=market_slug,
        asset_symbol=asset_symbol,
        etf_ticker=etf_ticker,
        current_net_flow_usd=current_net_flow_usd,
        previous_net_flow_usd=previous_net_flow_usd,
        source_count=source_count,
        confirmation_count=confirmation_count,
        flow_confidence=flow_confidence,
        observed_at=observed_at,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(inputs: tuple[Any, ...], *, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_research_crypto_etf_flow_reversal_digest(
        inputs,
        config=config(),
        generated_at=generated_at,
    )


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail(f"public payload must not contain floats: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    elif isinstance(value, list | tuple):
        for item in value:
            assert_no_floats(item)


def test_builds_report_only_crypto_etf_flow_reversal_digest_deterministically() -> None:
    report = digest(
        (
            observation(
                "sol-routine",
                research_key="research.sol.etf.flow",
                market_slug="sol-etf-flow",
                asset_symbol="sol",
                etf_ticker="SOLZ",
                current_net_flow_usd=d("15000000.000000"),
                previous_net_flow_usd=d("20000000.000000"),
                flow_confidence=d("0.910000"),
                observed_at=GENERATED_AT - timedelta(seconds=120),
            ),
            observation(
                "btc-blocked",
                research_key="research.btc.etf.flow",
                market_slug="btc-etf-flow",
                asset_symbol="btc",
                etf_ticker="IBIT",
                current_net_flow_usd=d("-325000000.000000"),
                previous_net_flow_usd=d("180000000.000000"),
                flow_confidence=d("0.820000"),
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    59,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                upstream_reason_codes=("desk_flow_note",),
            ),
            observation(
                "eth-watch",
                research_key="research.eth.etf.flow",
                market_slug="eth-etf-flow",
                asset_symbol="eth",
                etf_ticker="ETHA",
                current_net_flow_usd=d("90000000.000000"),
                previous_net_flow_usd=d("-40000000.000000"),
                flow_confidence=d("0.760000"),
                observed_at=GENERATED_AT - timedelta(minutes=30),
            ),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-research-crypto-etf-flow-reversal-digest-v0"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_reversal_count == d("1.000000")
    assert report.watch_reversal_count == d("1.000000")
    assert report.routine_count == d("1.000000")
    assert report.outflow_reversal_count == d("1.000000")
    assert report.inflow_reversal_count == d("1.000000")
    assert report.no_reversal_count == d("1.000000")
    assert report.stale_source_count == d("0.000000")
    assert report.thin_source_count == d("0.000000")
    assert report.low_confirmation_count == d("0.000000")
    assert report.low_confidence_count == d("0.000000")
    assert report.max_reversal_magnitude_usd == d("505000000.000000")
    assert report.net_current_flow_usd == d("-220000000.000000")
    assert report.net_previous_flow_usd == d("160000000.000000")
    assert report.aggregate_flow_change_usd == d("-380000000.000000")
    assert report.average_flow_confidence == d("0.830000")
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_etf_flow_reversal_digest"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [
        (row.source_id, row.reversal_status, row.reversal_magnitude_usd)
        for row in report.rows
    ] == [
        ("btc-blocked", "blocked", d("505000000.000000")),
        ("eth-watch", "watch", d("130000000.000000")),
        ("sol-routine", "pass", d("0.000000")),
    ]

    blocked, watch, passed = report.rows
    assert blocked.observed_at == datetime(2026, 7, 4, 11, 59, tzinfo=UTC)
    assert blocked.source_age_seconds == d("60.000000")
    assert blocked.flow_change_usd == d("-505000000.000000")
    assert blocked.flow_change_abs_usd == d("505000000.000000")
    assert blocked.reversal_direction == "outflow_reversal"
    assert blocked.reason_codes == (
        "crypto_etf_flow_reversal_large",
        "crypto_etf_flow_reversal_material",
        "crypto_etf_flow_reversal_outflow",
        "desk_flow_note",
        "source_fresh",
    )

    assert watch.source_age_seconds == d("1800.000000")
    assert watch.flow_change_usd == d("130000000.000000")
    assert watch.reversal_direction == "inflow_reversal"
    assert watch.reason_codes == (
        "crypto_etf_flow_reversal_inflow",
        "crypto_etf_flow_reversal_material",
        "source_fresh",
    )

    assert passed.reversal_direction == "no_reversal"
    assert passed.flow_change_usd == d("-5000000.000000")
    assert passed.reason_codes == (
        "crypto_etf_flow_reversal_absent",
        "source_fresh",
    )

    assert report.reason_codes == (
        "crypto_etf_flow_reversal_absent",
        "crypto_etf_flow_reversal_inflow",
        "crypto_etf_flow_reversal_large",
        "crypto_etf_flow_reversal_material",
        "crypto_etf_flow_reversal_outflow",
        "desk_flow_note",
        "source_fresh",
    )
    assert report.reason_code_counts[0].reason_code == (
        "crypto_etf_flow_reversal_absent"
    )
    assert report.reason_code_counts[0].count == d("1.000000")
    assert report.reason_code_counts[-1].reason_code == "source_fresh"
    assert report.reason_code_counts[-1].count == d("3.000000")
    assert report.reason_code_counts[-1].row_ratio == d("1.000000")


def test_empty_digest_and_payload_are_decimal_stringed_report_only_readonly() -> None:
    module = api()
    report = digest(())
    payload = module.market_research_crypto_etf_flow_reversal_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.blocked_reversal_count == d("0.000000")
    assert report.max_reversal_magnitude_usd == d("0.000000")
    assert report.average_flow_confidence == d("0.000000")
    assert report.digest_status == "blocked"
    assert report.reason_codes == ("crypto_etf_flow_reversal_digest_empty",)
    assert report.reason_code_counts == (
        module.MarketResearchCryptoEtfFlowReversalReasonCodeCount(
            reason_code="crypto_etf_flow_reversal_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["max_reversal_magnitude_usd"] == "0.000000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_floats(payload)


def test_rejects_bad_public_types_datetimes_duplicates_future_rows_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="current_net_flow_usd"):
        observation(current_net_flow_usd=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="flow_confidence"):
        observation(flow_confidence=d("1.100000"))

    with pytest.raises(ValueError, match="watch_reversal_abs_usd"):
        config(watch_reversal_abs_usd=50000000)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest((observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="inputs must not contain duplicate source_id"):
        digest((observation("dupe"), observation("dupe")))

    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    report = digest((observation(),))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    classes = (
        module.MarketResearchCryptoEtfFlowReversalDigestConfig,
        module.MarketResearchCryptoEtfFlowReversalObservation,
        module.MarketResearchCryptoEtfFlowReversalRow,
        module.MarketResearchCryptoEtfFlowReversalReasonCodeCount,
        module.MarketResearchCryptoEtfFlowReversalReport,
    )
    for type_ in classes:
        assert type_.__dataclass_params__.frozen is True
        for field in fields(type_):
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type


def test_module_scope_is_pure_in_memory_without_live_or_durable_surfaces() -> None:
    source = inspect.getsource(api()).lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "open(",
        "path(",
        "read(",
        "write(",
        "connect(",
        "cursor(",
        "execute(",
        "wallet",
        "private_key",
        "api_key",
        "secret",
        "auth",
        "web3",
        "live_trading",
        "exchange",
        "place_order",
        "cancel_order",
        "replace_order",
        "submit_order",
    ):
        assert forbidden not in source
