from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_research_crypto_exchange_reserve_digest"
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": module.DEFAULT_MARKET_RESEARCH_CRYPTO_EXCHANGE_RESERVE_DIGEST_CONFIG_VERSION,
        "fresh_snapshot_max_age_seconds": d("7200.000000"),
        "material_reserve_drop_ratio": d("0.050000"),
        "min_attestation_count": d("2"),
        "high_outflow_ratio": d("0.100000"),
    }
    values.update(overrides)
    return module.MarketResearchCryptoExchangeReserveDigestConfig(**values)


def input_row(
    research_key: str = "research.crypto.reserve.binance.btc",
    *,
    condition_id: str = "condition_crypto_exchange_reserve",
    venue_key: str = "binance",
    asset_key: str = "btc",
    reserve_source_reference: str = "https://reserves.example/binance?api_key=secret-123",
    observed_at: datetime | None = None,
    acknowledged_at: datetime | None = None,
    attestation_count: Decimal = d("3"),
    reserve_balance: Decimal = d("1000.000000"),
    prior_reserve_balance: Decimal = d("1040.000000"),
    net_flow_24h: Decimal = d("-40.000000"),
    market_probability_before: Decimal = d("0.430000"),
    market_probability_after: Decimal = d("0.460000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketResearchCryptoExchangeReserveDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        venue_key=venue_key,
        asset_key=asset_key,
        reserve_source_reference=reserve_source_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        acknowledged_at=(
            acknowledged_at
            if acknowledged_at is not None
            else GENERATED_AT - timedelta(minutes=20)
        ),
        attestation_count=attestation_count,
        reserve_balance=reserve_balance,
        prior_reserve_balance=prior_reserve_balance,
        net_flow_24h=net_flow_24h,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(*rows: object, generated_at: datetime = GENERATED_AT, cfg: object | None = None) -> Any:
    module = api()
    return module.build_market_research_crypto_exchange_reserve_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def decimal_payload_values(source: object, payload: object) -> tuple[object, ...]:
    if type(source) is Decimal:
        return (payload,)
    if is_dataclass(source) and not isinstance(source, type):
        assert isinstance(payload, dict)
        return tuple(
            item
            for field in fields(source)
            for item in decimal_payload_values(
                getattr(source, field.name),
                payload[field.name],
            )
        )
    if isinstance(source, tuple):
        assert isinstance(payload, list)
        return tuple(
            item
            for source_item, payload_item in zip(source, payload, strict=True)
            for item in decimal_payload_values(source_item, payload_item)
        )
    return ()


def test_crypto_exchange_reserve_digest_flags_material_outflow_and_sorts_rows() -> None:
    module = api()
    report = digest(
        input_row(
            "research.crypto.reserve.kraken.eth",
            condition_id="condition_crypto_eth",
            venue_key="kraken",
            asset_key="eth",
            observed_at=GENERATED_AT - timedelta(hours=3),
            acknowledged_at=GENERATED_AT - timedelta(minutes=95),
            attestation_count=d("1"),
            reserve_balance=d("900.000000"),
            prior_reserve_balance=d("1000.000000"),
            net_flow_24h=d("-120.000000"),
            market_probability_before=d("0.410000"),
            market_probability_after=d("0.560000"),
        ),
        input_row(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(report, module.MarketResearchCryptoExchangeReserveDigestReport)
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.reserve_snapshot_count == d("2")
    assert report.ready_snapshot_count == d("1")
    assert report.watch_snapshot_count == d("1")
    assert report.blocked_snapshot_count == d("0")
    assert report.material_reserve_drop_count == d("1")
    assert report.high_outflow_count == d("1")
    assert report.thin_attestation_count == d("1")
    assert report.stale_snapshot_count == d("1")
    assert report.average_reserve_drop_ratio == d("0.069231")
    assert report.max_snapshot_age_seconds == d("10800.000000")
    assert tuple((row.venue_key, row.asset_key) for row in report.rows) == (
        ("kraken", "eth"),
        ("binance", "btc"),
    )
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)
    assert report.rows[0].reserve_drop_ratio == d("0.100000")
    assert report.rows[0].net_flow_24h == d("-120.000000")
    assert report.rows[0].redacted_reserve_source_reference.startswith("sha256:")
    assert report.reason_codes == (
        "market_research_crypto_exchange_reserve_digest_material_reserve_drop",
        "market_research_crypto_exchange_reserve_digest_stale_snapshot",
        "market_research_crypto_exchange_reserve_digest_probability_repricing",
        "market_research_crypto_exchange_reserve_digest_high_outflow",
        "market_research_crypto_exchange_reserve_digest_slow_acknowledgement",
        "market_research_crypto_exchange_reserve_digest_thin_attestation",
        "market_research_crypto_exchange_reserve_digest_ready",
    )

    with pytest.raises(FrozenInstanceError):
        report.reserve_snapshot_count = d("3")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        input_row(attestation_count=2)  # type: ignore[arg-type]


def test_public_records_are_frozen_and_reject_subclassing() -> None:
    module = api()

    for public_type in (
        module.MarketResearchCryptoExchangeReserveDigestConfig,
        module.MarketResearchCryptoExchangeReserveDigestInputRow,
        module.MarketResearchCryptoExchangeReserveDigestRow,
        module.MarketResearchCryptoExchangeReserveDigestReasonCodeCount,
        module.MarketResearchCryptoExchangeReserveDigestReport,
    ):
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen
        with pytest.raises(TypeError, match="subclassing"):
            type(f"Derived{public_type.__name__}", (public_type,), {})


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_hard_flags_reject_false_values_across_public_records(flag_name: str) -> None:
    module = api()

    with pytest.raises(ValueError, match=flag_name):
        config(**{flag_name: False})
    with pytest.raises(ValueError, match=flag_name):
        input_row(**{flag_name: False})

    report = digest(input_row())
    for public_record in (
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        with pytest.raises(ValueError, match=flag_name):
            replace(public_record, **{flag_name: False})

    payload = module.market_research_crypto_exchange_reserve_digest_payload(report)
    with pytest.raises(ValueError, match=flag_name):
        module.market_research_crypto_exchange_reserve_digest_payload(
            {**payload, flag_name: False},
        )


def test_decimal_only_public_numerics_and_manual_reason_counts_are_strict() -> None:
    module = api()

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="fresh_snapshot_max_age_seconds must be a Decimal"):
        config(fresh_snapshot_max_age_seconds=DerivedDecimal("7200.000000"))
    with pytest.raises(ValueError, match="reserve_balance must be a Decimal"):
        input_row(reserve_balance=DerivedDecimal("1000.000000"))
    with pytest.raises(ValueError, match="count must be a Decimal"):
        module.MarketResearchCryptoExchangeReserveDigestReasonCodeCount(
            reason_code="market_research_crypto_exchange_reserve_digest_ready",
            count=DerivedDecimal("1.000000"),
            snapshot_ratio=d("1.000000"),
        )
    with pytest.raises(ValueError, match="snapshot_ratio must be a Decimal"):
        module.MarketResearchCryptoExchangeReserveDigestReasonCodeCount(
            reason_code="market_research_crypto_exchange_reserve_digest_ready",
            count=d("1.000000"),
            snapshot_ratio=DerivedDecimal("1.000000"),
        )
    with pytest.raises(ValueError, match="count must be positive"):
        module.MarketResearchCryptoExchangeReserveDigestReasonCodeCount(
            reason_code="market_research_crypto_exchange_reserve_digest_no_inputs",
            count=d("0.000000"),
            snapshot_ratio=d("0.000000"),
        )


def test_public_record_constructors_reject_noncanonical_ordering() -> None:
    report = digest(
        input_row(
            "research.crypto.reserve.kraken.eth",
            condition_id="condition_crypto_eth",
            venue_key="kraken",
            asset_key="eth",
            observed_at=GENERATED_AT - timedelta(hours=3),
            acknowledged_at=GENERATED_AT - timedelta(minutes=95),
            attestation_count=d("1.000000"),
            reserve_balance=d("900.000000"),
            prior_reserve_balance=d("1000.000000"),
            net_flow_24h=d("-120.000000"),
            market_probability_before=d("0.410000"),
            market_probability_after=d("0.560000"),
        ),
        input_row(),
    )

    with pytest.raises(ValueError, match="reason_codes must be sorted"):
        replace(report.rows[0], reason_codes=tuple(reversed(report.rows[0].reason_codes)))
    with pytest.raises(ValueError, match="rows must be sorted"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="reason_code_counts must be sorted"):
        replace(report, reason_code_counts=tuple(reversed(report.reason_code_counts)))
    with pytest.raises(ValueError, match="reason_codes must be sorted"):
        replace(report, reason_codes=tuple(reversed(report.reason_codes)))


def test_payload_is_json_ready_redacted_and_decimal_string_only() -> None:
    module = api()
    report = digest(input_row())

    payload = module.market_research_crypto_exchange_reserve_digest_payload(report)

    json.dumps(payload, sort_keys=True)
    assert payload == module.market_research_crypto_exchange_reserve_digest_payload(report)
    assert payload["reserve_snapshot_count"] == "1.000000"
    assert payload["average_reserve_drop_ratio"] == "0.038462"
    assert payload["max_snapshot_age_seconds"] == "1800.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["reserve_balance"] == "1000.000000"
    assert payload["rows"][0]["prior_reserve_balance"] == "1040.000000"
    assert payload["rows"][0]["net_flow_24h"] == "-40.000000"
    assert payload["rows"][0]["reserve_drop_ratio"] == "0.038462"
    assert payload["rows"][0]["redacted_reserve_source_reference"].startswith("sha256:")
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["snapshot_ratio"] == "1.000000"
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))
    for serialized_decimal in decimal_payload_values(report, payload):
        assert isinstance(serialized_decimal, str)
        assert re.fullmatch(r"-?\d+\.\d{6}", serialized_decimal) is not None
    assert "secret-123" not in repr(payload).lower()
    assert "api_key" not in repr(payload).lower()
    assert "wallet" not in repr(payload).lower()

    unsafe_report = replace(report)
    object.__setattr__(unsafe_report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        module.market_research_crypto_exchange_reserve_digest_payload(unsafe_report)
    with pytest.raises(ValueError, match="Decimal-derived"):
        module.market_research_crypto_exchange_reserve_digest_payload(
            {**payload, "reserve_snapshot_count": 1},
        )
    with pytest.raises(ValueError, match="float"):
        module.market_research_crypto_exchange_reserve_digest_payload(
            {**payload, "average_reserve_drop_ratio": 0.1},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.market_research_crypto_exchange_reserve_digest_payload(
            {**payload, "operator_token": "redacted"},
        )


def test_payload_rejects_tampered_nested_public_values() -> None:
    module = api()
    report = digest(input_row())

    object.__setattr__(report.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        module.market_research_crypto_exchange_reserve_digest_payload(report)
    object.__setattr__(report.rows[0], "readonly", True)

    object.__setattr__(report.reason_code_counts[0], "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        module.market_research_crypto_exchange_reserve_digest_payload(report)
    object.__setattr__(report.reason_code_counts[0], "report_only", True)

    object.__setattr__(report.rows[0], "reserve_balance", d("1000.0000001"))
    with pytest.raises(ValueError, match="six decimals"):
        module.market_research_crypto_exchange_reserve_digest_payload(report)


def test_empty_input_and_datetime_validation_are_strict() -> None:
    module = api()

    report = digest()
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_exchange_reserve_digest"
    )
    assert report.reserve_snapshot_count == d("0")
    assert report.average_reserve_drop_ratio == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "market_research_crypto_exchange_reserve_digest_no_inputs",
    )
    assert report.reason_code_counts == (
        module.MarketResearchCryptoExchangeReserveDigestReasonCodeCount(
            reason_code="market_research_crypto_exchange_reserve_digest_no_inputs",
            count=d("1.000000"),
            snapshot_ratio=d("0.000000"),
        ),
    )
    payload = module.market_research_crypto_exchange_reserve_digest_payload(report)
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["snapshot_ratio"] == "0.000000"

    class MissingOffsetTz(tzinfo):
        def utcoffset(self, dt: datetime | None) -> None:
            return None

        def dst(self, dt: datetime | None) -> None:
            return None

    class DerivedDateTime(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at"):
        digest(input_row(), generated_at=DerivedDateTime(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="config"):
        module.build_market_research_crypto_exchange_reserve_digest(
            (),
            config=False,  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        input_row(observed_at=datetime(2026, 7, 4, 11, 30))
    with pytest.raises(ValueError, match="timezone-aware"):
        input_row(observed_at=datetime(2026, 7, 4, 11, 30, tzinfo=MissingOffsetTz()))
    with pytest.raises(ValueError, match="timezone-aware"):
        digest(
            input_row(),
            generated_at=datetime(2026, 7, 4, 12, 0, tzinfo=MissingOffsetTz()),
        )
    with pytest.raises(ValueError, match="public identifier"):
        input_row(research_key="research.wallet.crypto")
    with pytest.raises(ValueError, match="redacted"):
        replace(
            digest(input_row()).rows[0],
            redacted_reserve_source_reference=(
                "https://reserves.example/binance?api_key=secret-123"
            ),
        )


def test_module_has_no_live_durable_or_forbidden_surface() -> None:
    module_path = Path(__file__).resolve().parents[1] / (
        "src/polymarket_alpha_lab/market_research_crypto_exchange_reserve_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    lowered = source.lower()
    tree = ast.parse(source)

    for token in (
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
        "replace_order",
        "live trading",
        "wallet",
        "private_key",
        "sqlite",
        "postgres",
        "redis",
    ):
        assert token not in lowered

    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "subprocess",
        "psycopg",
        "psycopg2",
        "supabase",
        "sqlite3",
        "web3",
        "pathlib",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
        "replace_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in forbidden_call_names
            elif isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names
