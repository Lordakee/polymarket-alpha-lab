from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_crypto_exchange_outflow_spike_digest.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_exchange_outflow_spike_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def outflow_observation(
    source_id: str = "source-alpha",
    *,
    exchange_id: str = "exchange-alpha",
    asset_symbol: str = "btc",
    market_slug: str = "btc-exchange-outflow-spike",
    exchange_balance_usd: str | Decimal = "800000000.000000",
    net_outflow_usd: str | Decimal = "120000000.000000",
    baseline_outflow_usd: str | Decimal = "24000000.000000",
    source_row_count: str | Decimal = "4.000000",
    observation_timestamp: datetime = datetime(2026, 7, 4, 14, 30, tzinfo=UTC),
    reason_codes: tuple[str, ...] = (
        "crypto_exchange_outflow_spike_pressure",
        "crypto_exchange_outflow_balance_drawdown_pressure",
    ),
):
    module = api()
    return module.CryptoExchangeOutflowSpikeObservation(
        source_id=source_id,
        exchange_id=exchange_id,
        asset_symbol=asset_symbol,
        market_slug=market_slug,
        exchange_balance_usd=(
            exchange_balance_usd
            if isinstance(exchange_balance_usd, Decimal)
            else d(exchange_balance_usd)
        ),
        net_outflow_usd=(
            net_outflow_usd
            if isinstance(net_outflow_usd, Decimal)
            else d(net_outflow_usd)
        ),
        baseline_outflow_usd=(
            baseline_outflow_usd
            if isinstance(baseline_outflow_usd, Decimal)
            else d(baseline_outflow_usd)
        ),
        source_row_count=(
            source_row_count if isinstance(source_row_count, Decimal) else d(source_row_count)
        ),
        observation_timestamp=observation_timestamp,
        reason_codes=reason_codes,
    )


def digest_report(*rows: object, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_market_research_crypto_exchange_outflow_spike_digest(
        rows,
        config=module.CryptoExchangeOutflowSpikeDigestConfig(),
        generated_at=generated_at.astimezone(timezone(timedelta(hours=-4))),
    )


def assert_payload_has_no_public_numbers(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_public_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_payload_has_no_public_numbers(item)
        return
    if isinstance(value, bool):
        return
    assert not isinstance(value, (Decimal, float, int))


def test_exchange_outflow_spike_digest_reduces_rows_deterministically() -> None:
    module = api()

    report = digest_report(
        outflow_observation(
            "source-watch",
            exchange_id="exchange-beta",
            asset_symbol="eth",
            market_slug="eth-exchange-outflow-watch",
            exchange_balance_usd="500000000.000000",
            net_outflow_usd="30000000.000000",
            baseline_outflow_usd="15000000.000000",
            source_row_count="3.000000",
        ),
        outflow_observation(
            "source-pass",
            exchange_id="exchange-gamma",
            asset_symbol="usdc",
            market_slug="usdc-exchange-outflow-clear",
            exchange_balance_usd="400000000.000000",
            net_outflow_usd="8000000.000000",
            baseline_outflow_usd="8000000.000000",
            source_row_count="1.000000",
            observation_timestamp=datetime(
                2026,
                7,
                4,
                10,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            reason_codes=("crypto_exchange_outflow_spike_observed_stable",),
        ),
        outflow_observation("source-blocked"),
    )

    assert isinstance(report, module.CryptoExchangeOutflowSpikeDigestReport)
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "market-research-crypto-exchange-outflow-spike-digest-v0"
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_exchange_outflow_spike_digest"
    )
    assert report.source_row_count == d("8.000000")
    assert report.observation_count == d("3.000000")
    assert report.blocked_exchange_count == d("1.000000")
    assert report.watch_exchange_count == d("1.000000")
    assert report.pass_exchange_count == d("1.000000")
    assert report.total_net_outflow_usd == d("158000000.000000")
    assert report.max_spike_multiple == d("5.000000")
    assert report.max_balance_drawdown_ratio == d("0.150000")
    assert report.max_screening_score == d("1.000000")
    assert report.average_screening_score == d("0.616667")
    assert report.blocked_observation_ratio == d("0.333333")
    assert report.reason_codes == (
        "crypto_exchange_outflow_spike_blocked_present",
        "crypto_exchange_outflow_spike_watch_present",
    )
    assert report.reason_code_counts == (
        module.CryptoExchangeOutflowSpikeReasonCodeCount(
            reason_code="crypto_exchange_outflow_spike_blocked",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        module.CryptoExchangeOutflowSpikeReasonCodeCount(
            reason_code="crypto_exchange_balance_drawdown_blocked",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        module.CryptoExchangeOutflowSpikeReasonCodeCount(
            reason_code="crypto_exchange_outflow_spike_watch",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        module.CryptoExchangeOutflowSpikeReasonCodeCount(
            reason_code="crypto_exchange_balance_drawdown_watch",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        module.CryptoExchangeOutflowSpikeReasonCodeCount(
            reason_code="crypto_exchange_outflow_spike_observed_stable",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.exchange_id for row in report.exchange_rows) == (
        "exchange-alpha",
        "exchange-beta",
        "exchange-gamma",
    )
    blocked, watch, passed = report.exchange_rows
    assert blocked.screening_status == "blocked"
    assert blocked.spike_multiple == d("5.000000")
    assert blocked.balance_drawdown_ratio == d("0.150000")
    assert blocked.screening_score == d("1.000000")
    assert blocked.reason_codes == (
        "crypto_exchange_outflow_spike_blocked",
        "crypto_exchange_balance_drawdown_blocked",
    )
    assert watch.screening_status == "watch"
    assert watch.spike_multiple == d("2.000000")
    assert watch.balance_drawdown_ratio == d("0.060000")
    assert watch.screening_score == d("0.600000")
    assert watch.reason_codes == (
        "crypto_exchange_outflow_spike_watch",
        "crypto_exchange_balance_drawdown_watch",
    )
    assert passed.screening_status == "pass"
    assert passed.spike_multiple == d("1.000000")
    assert passed.balance_drawdown_ratio == d("0.020000")
    assert passed.screening_score == d("0.250000")
    assert passed.observation_timestamp == datetime(2026, 7, 4, 14, 30, tzinfo=UTC)
    assert passed.reason_codes == ("crypto_exchange_outflow_spike_observed_stable",)


def test_empty_exchange_outflow_spike_digest_is_report_only_blocked() -> None:
    module = api()

    report = digest_report()

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_exchange_outflow_spike_digest"
    )
    assert report.source_row_count == d("0.000000")
    assert report.observation_count == d("0.000000")
    assert report.blocked_exchange_count == d("0.000000")
    assert report.watch_exchange_count == d("0.000000")
    assert report.pass_exchange_count == d("0.000000")
    assert report.total_net_outflow_usd == d("0.000000")
    assert report.max_spike_multiple == d("0.000000")
    assert report.max_balance_drawdown_ratio == d("0.000000")
    assert report.max_screening_score == d("0.000000")
    assert report.average_screening_score == d("0.000000")
    assert report.blocked_observation_ratio == d("0.000000")
    assert report.exchange_rows == ()
    assert report.reason_codes == ("crypto_exchange_outflow_spike_digest_empty",)
    assert report.reason_code_counts == (
        module.CryptoExchangeOutflowSpikeReasonCodeCount(
            reason_code="crypto_exchange_outflow_spike_digest_empty",
            count=d("1.000000"),
            observation_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_validation_rejects_bad_decimals_times_flags_duplicates_and_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="exchange_balance_usd must be a Decimal"):
        outflow_observation(exchange_balance_usd=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="baseline_outflow_usd must be positive"):
        outflow_observation(baseline_outflow_usd="0.000000")
    with pytest.raises(ValueError, match="source_row_count must be whole"):
        outflow_observation(source_row_count="0.500000")
    with pytest.raises(ValueError, match="observation_timestamp must be timezone-aware"):
        outflow_observation(observation_timestamp=datetime(2026, 7, 4, 14, 30))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_crypto_exchange_outflow_spike_digest(
            (),
            config=module.CryptoExchangeOutflowSpikeDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        digest_report(
            outflow_observation("source-dupe"),
            outflow_observation("source-dupe"),
        )
    with pytest.raises(ValueError, match="reason_codes must match exchange outflow metrics"):
        outflow_observation(
            net_outflow_usd="120000000.000000",
            baseline_outflow_usd="24000000.000000",
            reason_codes=("crypto_exchange_outflow_spike_observed_stable",),
        )
    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.CryptoExchangeOutflowSpikeDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(outflow_observation("source-flags"), report_only=False)
    with pytest.raises(ValueError, match="total_net_outflow_usd must match rows"):
        replace(digest_report(outflow_observation("source-valid")), total_net_outflow_usd=d("1"))

    row = outflow_observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        row.exchange_id = "exchange-other"  # type: ignore[misc]


def test_payload_public_numerics_are_six_decimal_strings_and_source_is_pure() -> None:
    module = api()
    report = digest_report(outflow_observation("source-json"))

    payload = module.market_research_crypto_exchange_outflow_spike_digest_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["source_row_count"] == "4.000000"
    assert payload["observation_count"] == "1.000000"
    assert payload["exchange_rows"][0]["exchange_balance_usd"] == "800000000.000000"
    assert payload["exchange_rows"][0]["net_outflow_usd"] == "120000000.000000"
    assert payload["exchange_rows"][0]["spike_multiple"] == "5.000000"
    assert payload["exchange_rows"][0]["screening_score"] == "1.000000"
    assert payload["exchange_rows"][0]["observation_timestamp"] == "2026-07-04T14:30:00+00:00"
    assert_payload_has_no_public_numbers(payload)

    for value in (
        module.CryptoExchangeOutflowSpikeDigestConfig(),
        outflow_observation("source-decimal"),
        report.exchange_rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if _is_public_numeric_field(field.name):
                assert type(getattr(value, field.name)) is Decimal, field.name

    payload_text = repr(payload).lower()
    for forbidden in ("private_key", "api_key", "secret", "wallet", "auth"):
        assert forbidden not in payload_text

    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "api_key",
        "mnemonic",
        "wallet",
        "auth",
        "urlopen",
        "connect(",
        "execute(",
        "submit_order",
        "cancel_order",
        "replace_order",
        "fast_mode",
        "fast mode",
    ):
        assert forbidden not in source.lower()

    with pytest.raises(ValueError, match="report must be exactly"):
        module.market_research_crypto_exchange_outflow_spike_digest_payload(object())


def _is_public_numeric_field(field_name: str) -> bool:
    return field_name.endswith(
        (
            "_count",
            "_ratio",
            "_usd",
            "_score",
            "_multiple",
        ),
    )
