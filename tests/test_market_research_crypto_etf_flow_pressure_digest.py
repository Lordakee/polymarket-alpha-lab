from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.market_research_crypto_etf_flow_pressure_digest"
)
GENERATED_AT = datetime(2026, 7, 5, 18, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def _module() -> ModuleType:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> object:
    module = _module()
    values: dict[str, object] = {
        "config_version": (
            module
            .DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_PRESSURE_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "watch_abs_net_flow_usd": d("50000000.000000"),
        "blocked_abs_net_flow_usd": d("250000000.000000"),
        "watch_flow_pressure_ratio": d("0.030000"),
        "blocked_flow_pressure_ratio": d("0.080000"),
        "max_premium_discount_abs": d("0.020000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return module.MarketResearchCryptoEtfFlowPressureDigestConfig(**values)


def _observation(
    condition_id: str = "condition_alpha",
    pressure_key: str = "btc_spot_etf_pressure",
    *,
    etf_ticker: str = "IBIT",
    asset_symbol: str = "BTC",
    observed_at: datetime = GENERATED_AT,
    net_flow_usd: Decimal = d("10000000.000000"),
    previous_net_flow_usd: Decimal = d("9000000.000000"),
    assets_under_management_usd: Decimal = d("2000000000.000000"),
    premium_discount: Decimal = d("0.002000"),
    source_count: Decimal = d("3.000000"),
    confidence: Decimal = d("0.850000"),
    source_config_version: str = "crypto-etf-flow-pressure-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> object:
    module = _module()
    return module.MarketResearchCryptoEtfFlowPressureObservation(
        condition_id=condition_id,
        pressure_key=pressure_key,
        etf_ticker=etf_ticker,
        asset_symbol=asset_symbol,
        observed_at=observed_at,
        net_flow_usd=net_flow_usd,
        previous_net_flow_usd=previous_net_flow_usd,
        assets_under_management_usd=assets_under_management_usd,
        premium_discount=premium_discount,
        source_count=source_count,
        confidence=confidence,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    *observations: object,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
) -> object:
    module = _module()
    return module.build_market_research_crypto_etf_flow_pressure_digest(
        observations,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def _walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in _walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in _walk_values(nested))
    return (value,)


def test_empty_input_is_blocked_with_manual_reason_count() -> None:
    module = _module()

    digest_report = _report()

    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen is True
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_market_research_crypto_etf_flow_pressure_digest"
    )
    assert digest_report.observation_count == d("0.000000")
    assert digest_report.ready_observation_count == d("0.000000")
    assert digest_report.watch_observation_count == d("0.000000")
    assert digest_report.blocked_observation_count == d("0.000000")
    assert digest_report.total_net_flow_usd == d("0.000000")
    assert digest_report.max_net_flow_abs_usd == d("0.000000")
    assert digest_report.average_flow_pressure_ratio == d("0.000000")
    assert digest_report.max_flow_pressure_ratio == d("0.000000")
    assert digest_report.average_confidence == d("0.000000")
    assert digest_report.max_observation_age_seconds == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "market_research_crypto_etf_flow_pressure_digest_no_inputs",
    )
    assert digest_report.reason_code_counts == (
        module.MarketResearchCryptoEtfFlowPressureDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_etf_flow_pressure_digest_no_inputs"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_flow_pressure_digest_summarizes_pressure_and_source_gaps() -> None:
    digest_report = _report(
        _observation(
            "condition_ready",
            "eth_spot_etf_pressure",
            etf_ticker="ETHA",
            asset_symbol="ETH",
        ),
        _observation(
            "condition_blocked",
            "btc_spot_etf_pressure",
            observed_at=GENERATED_AT - timedelta(seconds=9000),
            net_flow_usd=d("-320000000.000000"),
            previous_net_flow_usd=d("20000000.000000"),
            assets_under_management_usd=d("2000000000.000000"),
            premium_discount=d("-0.036000"),
            source_count=d("1.000000"),
            confidence=d("0.520000"),
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.observation_count == d("2.000000")
    assert digest_report.ready_observation_count == d("1.000000")
    assert digest_report.watch_observation_count == d("0.000000")
    assert digest_report.blocked_observation_count == d("1.000000")
    assert digest_report.flow_pressure_observation_count == d("1.000000")
    assert digest_report.flow_acceleration_observation_count == d("1.000000")
    assert digest_report.premium_discount_pressure_observation_count == d("1.000000")
    assert digest_report.source_gap_observation_count == d("1.000000")
    assert digest_report.confidence_gap_observation_count == d("1.000000")
    assert digest_report.stale_observation_count == d("1.000000")
    assert digest_report.total_net_flow_usd == d("-310000000.000000")
    assert digest_report.max_net_flow_abs_usd == d("320000000.000000")
    assert digest_report.average_flow_pressure_ratio == d("0.082500")
    assert digest_report.max_flow_pressure_ratio == d("0.160000")
    assert digest_report.average_confidence == d("0.685000")
    assert digest_report.max_observation_age_seconds == d("9000.000000")
    assert digest_report.source_config_versions == (
        ("btc_spot_etf_pressure", "crypto-etf-flow-pressure-source-v0"),
        ("eth_spot_etf_pressure", "crypto-etf-flow-pressure-source-v0"),
    )

    assert tuple(row.pressure_key for row in digest_report.rows) == (
        "btc_spot_etf_pressure",
        "eth_spot_etf_pressure",
    )
    blocked_row = digest_report.rows[0]
    assert blocked_row.digest_status == "blocked"
    assert blocked_row.observation_age_seconds == d("9000.000000")
    assert blocked_row.net_flow_abs_usd == d("320000000.000000")
    assert blocked_row.flow_change_abs_usd == d("340000000.000000")
    assert blocked_row.flow_pressure_ratio == d("0.160000")
    assert blocked_row.flow_acceleration_ratio == d("0.170000")
    assert blocked_row.premium_discount_abs == d("0.036000")
    assert blocked_row.reason_codes == (
        "market_research_crypto_etf_flow_pressure_digest_flow_pressure",
        "market_research_crypto_etf_flow_pressure_digest_flow_acceleration",
        "market_research_crypto_etf_flow_pressure_digest_premium_discount_pressure",
        "market_research_crypto_etf_flow_pressure_digest_source_gap",
        "market_research_crypto_etf_flow_pressure_digest_confidence_gap",
        "market_research_crypto_etf_flow_pressure_digest_stale_observation",
    )
    assert digest_report.reason_codes == blocked_row.reason_codes
    assert digest_report.rows[1].reason_codes == (
        "market_research_crypto_etf_flow_pressure_digest_ready",
    )


def test_timezones_reason_counts_and_source_versions_are_normalized() -> None:
    module = _module()
    generated_at = datetime(2026, 7, 5, 14, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 5, 18, 0, tzinfo=timezone(timedelta(hours=1)))

    digest_report = _report(
        _observation(
            "condition_sol",
            "sol_spot_etf_pressure",
            etf_ticker="SOLZ",
            asset_symbol="SOL",
            observed_at=observed_at,
            source_count=d("1.000000"),
        ),
        generated_at=generated_at,
    )

    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.rows[0].observed_at == datetime(2026, 7, 5, 17, 0, tzinfo=UTC)
    assert digest_report.max_observation_age_seconds == d("3600.000000")
    assert digest_report.digest_status == "watch"
    assert digest_report.reason_code_counts == (
        module.MarketResearchCryptoEtfFlowPressureDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_etf_flow_pressure_digest_source_gap"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
    )
    assert digest_report.source_config_versions == (
        ("sol_spot_etf_pressure", "crypto-etf-flow-pressure-source-v0"),
    )


def test_rows_and_public_reason_fields_are_canonical() -> None:
    first = _report(
        _observation(
            "condition_beta",
            "beta_pressure",
            net_flow_usd=d("60000000.000000"),
            previous_net_flow_usd=d("1000000.000000"),
        ),
        _observation(
            "condition_alpha",
            "alpha_pressure",
            net_flow_usd=d("60000000.000000"),
            previous_net_flow_usd=d("1000000.000000"),
        ),
    )
    second = _report(
        _observation(
            "condition_alpha",
            "alpha_pressure",
            net_flow_usd=d("60000000.000000"),
            previous_net_flow_usd=d("1000000.000000"),
        ),
        _observation(
            "condition_beta",
            "beta_pressure",
            net_flow_usd=d("60000000.000000"),
            previous_net_flow_usd=d("1000000.000000"),
        ),
    )

    assert first == second
    assert tuple(row.pressure_key for row in first.rows) == (
        "alpha_pressure",
        "beta_pressure",
    )
    with pytest.raises(ValueError, match="rows"):
        replace(first, rows=tuple(reversed(first.rows)))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(first, reason_codes=tuple(reversed(first.reason_codes)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(first, reason_code_counts=tuple(reversed(first.reason_code_counts)))
    with pytest.raises(ValueError, match="source_config_versions"):
        replace(
            first,
            source_config_versions=tuple(reversed(first.source_config_versions)),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(first.rows[0], reason_codes=tuple(reversed(first.rows[0].reason_codes)))


def test_validation_rejects_exact_type_violations_false_flags_and_duplicates() -> None:
    module = _module()

    for type_ in (
        module.MarketResearchCryptoEtfFlowPressureDigestConfig,
        module.MarketResearchCryptoEtfFlowPressureObservation,
        module.MarketResearchCryptoEtfFlowPressureDigestRow,
        module.MarketResearchCryptoEtfFlowPressureDigestReasonCodeCount,
        module.MarketResearchCryptoEtfFlowPressureDigestReport,
    ):
        assert type_.__dataclass_params__.frozen is True
        with pytest.raises(TypeError, match="subclassing"):
            type(f"{type_.__name__}Subclass", (type_,), {})
        for field in fields(type_):
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("flow-pressure-v0"))
    with pytest.raises(ValueError, match="blocked_abs_net_flow_usd"):
        _config(blocked_abs_net_flow_usd=_DecimalSubclass("250000000.000000"))
    with pytest.raises(ValueError, match="min_source_count"):
        _config(min_source_count=2)
    with pytest.raises(ValueError, match="watch_flow_pressure_ratio"):
        _config(
            watch_flow_pressure_ratio=d("0.090000"),
            blocked_flow_pressure_ratio=d("0.080000"),
        )
    with pytest.raises(ValueError, match="net_flow_usd"):
        _observation(net_flow_usd=10000000)
    with pytest.raises(ValueError, match="confidence"):
        _observation(confidence=0.85)
    with pytest.raises(ValueError, match="condition_id"):
        _observation(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="observed_at"):
        _observation(observed_at=datetime(2026, 7, 5, 18, 0))
    with pytest.raises(ValueError, match="observed_at"):
        _observation(
            observed_at=datetime(2026, 7, 5, 18, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=_DateTimeSubclass(2026, 7, 5, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config"):
        _report(config=False)
    with pytest.raises(ValueError, match="future"):
        _report(_observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="redacted"):
        _observation(pressure_key="private_key_0xabc")
    with pytest.raises(ValueError, match="redacted"):
        _observation(source_config_version="source-order-v0")
    with pytest.raises(ValueError, match="unique"):
        _report(
            _observation(pressure_key="duplicate"),
            _observation("condition_beta", "duplicate"),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        module.build_market_research_crypto_etf_flow_pressure_digest(
            ("not-an-observation",),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    digest_report = _report(_observation())
    with pytest.raises(FrozenInstanceError):
        digest_report.rows = ()  # type: ignore[misc]
    with pytest.raises(ValueError, match="config paper_only must be True"):
        _config(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(_observation(), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason code count paper_only must be True"):
        replace(digest_report.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report readonly must be True"):
        replace(digest_report, readonly=False)
    with pytest.raises(ValueError, match="count"):
        module.MarketResearchCryptoEtfFlowPressureDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_etf_flow_pressure_digest_no_inputs"
            ),
            count=d("0.000000"),
            observation_ratio=d("0.000000"),
        )


def test_public_decimal_fields_are_six_place_and_payload_is_json_ready() -> None:
    module = _module()
    digest_report = _report(
        _observation(
            "condition_payload",
            "payload_pressure",
            net_flow_usd=d("-320000000.000000"),
            previous_net_flow_usd=d("20000000.000000"),
            assets_under_management_usd=d("2000000000.000000"),
            premium_discount=d("-0.036000"),
            source_count=d("1.000000"),
            confidence=d("0.520000"),
        ),
    )

    for public_record in (
        _config(),
        _observation("condition_numeric", "numeric_pressure"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen is True
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if _is_public_numeric_field(field.name):
                assert type(value) is Decimal, field.name
                assert value.as_tuple().exponent == -6, field.name

    payload = module.market_research_crypto_etf_flow_pressure_digest_payload(
        digest_report,
    )
    json.dumps(payload, sort_keys=True)
    assert not any(isinstance(value, Decimal) for value in _walk_values(payload))
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    payload_text = repr(payload).lower()
    for forbidden in (
        "wallet",
        "auth",
        "private",
        "secret",
        "order",
        "cancel",
        "replace",
        "exchange",
        "payload_json",
    ):
        assert forbidden not in payload_text
    assert payload["generated_at"] == "2026-07-05T18:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["total_net_flow_usd"] == "-320000000.000000"
    assert payload["average_flow_pressure_ratio"] == "0.160000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-05T18:00:00+00:00"
    assert payload["rows"][0]["net_flow_usd"] == "-320000000.000000"
    assert payload["rows"][0]["flow_pressure_ratio"] == "0.160000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["observation_ratio"] == "1.000000"

    with pytest.raises(
        ValueError,
        match="report must be exactly",
    ):
        module.market_research_crypto_etf_flow_pressure_digest_payload(payload)

    object.__setattr__(digest_report, "observation_count", 1)
    with pytest.raises(ValueError, match="Decimal"):
        module.market_research_crypto_etf_flow_pressure_digest_payload(digest_report)

    digest_report = _report(_observation("condition_float", "float_pressure"))
    object.__setattr__(digest_report, "average_confidence", 0.85)
    with pytest.raises(ValueError, match="float"):
        module.market_research_crypto_etf_flow_pressure_digest_payload(digest_report)

    digest_report = _report(
        _observation("condition_flag_tamper", "flag_tamper_pressure"),
    )
    object.__setattr__(digest_report.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        module.market_research_crypto_etf_flow_pressure_digest_payload(digest_report)

    digest_report = _report(
        _observation("condition_decimal_tamper", "decimal_tamper_pressure"),
    )
    object.__setattr__(digest_report.rows[0], "source_count", d("3.0000001"))
    with pytest.raises(ValueError, match="six decimals"):
        module.market_research_crypto_etf_flow_pressure_digest_payload(digest_report)


def test_module_scope_excludes_io_live_surfaces_and_mutation_language() -> None:
    module = _module()
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    forbidden_literals = (
        "live trading",
        "account authentication",
        "private_key",
        "api_key",
        "wallet",
        "order",
        "cancel",
        "replace",
        "exchange mutation",
        "database",
        "sqlite",
        "supabase",
        "secret",
        "payload_json",
        "requests",
        "httpx",
        "socket",
        "urlopen",
        "psycopg",
        "subprocess",
    )
    assert not any(token in lowered for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            callee_name = ""
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in {
                "open",
                "read",
                "write",
                "submit",
                "cancel",
                "replace",
                "connect",
                "execute",
                "getenv",
                "request",
                "urlopen",
            }
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    allowed_import_roots = {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "typing",
    }
    for imported_module in imported_modules:
        assert imported_module.split(".")[0] in allowed_import_roots


def _is_public_numeric_field(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_seconds")
        or field_name.endswith("_ratio")
        or field_name.endswith("_usd")
        or field_name.endswith("_abs")
        or field_name.endswith("_confidence")
        or field_name
        in {
            "confidence",
            "min_confidence",
            "premium_discount",
            "premium_discount_abs",
            "average_confidence",
            "max_premium_discount_abs",
        }
    )
