from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_crypto_etf_flow_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoEtfFlowDigestConfig,
    MarketResearchCryptoEtfFlowDigestReasonCodeCount,
    MarketResearchCryptoEtfFlowDigestReport,
    MarketResearchCryptoEtfFlowDigestRow,
    MarketResearchCryptoEtfFlowObservation,
    build_market_research_crypto_etf_flow_digest,
    market_research_crypto_etf_flow_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


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


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> MarketResearchCryptoEtfFlowDigestConfig:
    values = {
        "config_version": DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_DIGEST_CONFIG_VERSION,
        "max_observation_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "min_abs_net_flow_usd": d("25000000.000000"),
        "min_flow_confidence": d("0.650000"),
        "max_premium_discount_abs": d("0.020000"),
    }
    values.update(overrides)
    return MarketResearchCryptoEtfFlowDigestConfig(**values)


def _observation(
    condition_id: str = "condition_alpha",
    flow_key: str = "btc_spot_etf_flow",
    *,
    asset_symbol: str = "BTC",
    observed_at: datetime = GENERATED_AT,
    net_flow_usd: Decimal = d("64000000.000000"),
    previous_net_flow_usd: Decimal = d("12000000.000000"),
    source_count: Decimal = d("3.000000"),
    flow_confidence: Decimal = d("0.820000"),
    premium_discount: Decimal = d("0.004000"),
    source_config_version: str = "crypto-etf-flow-source-v0",
) -> MarketResearchCryptoEtfFlowObservation:
    return MarketResearchCryptoEtfFlowObservation(
        condition_id=condition_id,
        flow_key=flow_key,
        asset_symbol=asset_symbol,
        observed_at=observed_at,
        net_flow_usd=net_flow_usd,
        previous_net_flow_usd=previous_net_flow_usd,
        source_count=source_count,
        flow_confidence=flow_confidence,
        premium_discount=premium_discount,
        source_config_version=source_config_version,
    )


def _report(
    *observations: MarketResearchCryptoEtfFlowObservation,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoEtfFlowDigestConfig | None = None,
) -> MarketResearchCryptoEtfFlowDigestReport:
    return build_market_research_crypto_etf_flow_digest(
        observations,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_etf_flow_digest_summarizes_flow_pressure_gaps_and_premium_risk() -> None:
    report = _report(
        _observation(
            "condition_beta",
            "eth_spot_etf_flow",
            asset_symbol="ETH",
            observed_at=GENERATED_AT - timedelta(seconds=9_000),
            net_flow_usd=d("-125000000.000000"),
            previous_net_flow_usd=d("-20000000.000000"),
            source_count=d("1.000000"),
            flow_confidence=d("0.540000"),
            premium_discount=d("-0.031000"),
        ),
        _observation(
            "condition_alpha",
            "btc_spot_etf_flow",
            observed_at=GENERATED_AT - timedelta(seconds=120),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_etf_flow_digest"
    )
    assert report.observation_count == d("2.000000")
    assert report.ready_observation_count == d("1.000000")
    assert report.watch_observation_count == d("0.000000")
    assert report.blocked_observation_count == d("1.000000")
    assert report.flow_pressure_observation_count == d("2.000000")
    assert report.flow_reversal_observation_count == d("1.000000")
    assert report.source_gap_observation_count == d("1.000000")
    assert report.confidence_gap_observation_count == d("1.000000")
    assert report.premium_discount_pressure_observation_count == d("1.000000")
    assert report.stale_observation_count == d("1.000000")
    assert report.total_net_flow_usd == d("-61000000.000000")
    assert report.average_net_flow_usd == d("-30500000.000000")
    assert report.average_flow_confidence == d("0.680000")
    assert report.max_observation_age_seconds == d("9000.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.condition_id, row.flow_key) for row in report.rows) == (
        ("condition_beta", "eth_spot_etf_flow"),
        ("condition_alpha", "btc_spot_etf_flow"),
    )
    beta = report.rows[0]
    assert beta.digest_status == "blocked"
    assert beta.observation_age_seconds == d("9000.000000")
    assert beta.net_flow_abs_usd == d("125000000.000000")
    assert beta.flow_change_abs_usd == d("105000000.000000")
    assert beta.premium_discount_abs == d("0.031000")
    assert beta.reason_codes == (
        "market_research_crypto_etf_flow_digest_flow_pressure",
        "market_research_crypto_etf_flow_digest_flow_reversal",
        "market_research_crypto_etf_flow_digest_source_gap",
        "market_research_crypto_etf_flow_digest_confidence_gap",
        "market_research_crypto_etf_flow_digest_premium_discount_pressure",
        "market_research_crypto_etf_flow_digest_stale_observation",
    )
    assert report.reason_codes == beta.reason_codes


def test_etf_flow_digest_normalizes_timezones_reason_counts_and_source_versions() -> None:
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 2, 12, 0, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _observation(
            "condition_gamma",
            "sol_spot_etf_flow",
            asset_symbol="SOL",
            observed_at=observed_at,
            net_flow_usd=d("9000000.000000"),
            previous_net_flow_usd=d("8000000.000000"),
            source_count=d("1.000000"),
            flow_confidence=d("0.760000"),
            premium_discount=d("0.006000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 7, 2, 11, 0, tzinfo=UTC)
    assert report.max_observation_age_seconds == d("3600.000000")
    assert report.digest_status == "watch"
    assert report.reason_code_counts == (
        MarketResearchCryptoEtfFlowDigestReasonCodeCount(
            reason_code="market_research_crypto_etf_flow_digest_source_gap",
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("sol_spot_etf_flow", "crypto-etf-flow-source-v0"),
    )


def test_etf_flow_digest_empty_input_is_watch_and_sorting_is_deterministic() -> None:
    empty = _report()
    assert empty.digest_status == "watch"
    assert empty.observation_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_crypto_etf_flow_digest_no_inputs",
    )

    first = _report(
        _observation("condition_b", "source_b"),
        _observation("condition_a", "source_a"),
    )
    second = _report(
        _observation("condition_a", "source_a"),
        _observation("condition_b", "source_b"),
    )

    assert first == second
    assert tuple(row.flow_key for row in first.rows) == ("source_a", "source_b")


def test_etf_flow_digest_validates_exact_types_flags_freezing_and_duplicates() -> None:
    assert MarketResearchCryptoEtfFlowDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoEtfFlowObservation.__dataclass_params__.frozen
    assert MarketResearchCryptoEtfFlowDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoEtfFlowDigestReasonCodeCount.__dataclass_params__.frozen
    assert MarketResearchCryptoEtfFlowDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("crypto-etf-flow-v0"))
    with pytest.raises(ValueError, match="min_abs_net_flow_usd"):
        _config(min_abs_net_flow_usd=_DecimalSubclass("25000000.000000"))
    with pytest.raises(ValueError, match="source_count"):
        _config(min_source_count=2)
    with pytest.raises(ValueError, match="flow_confidence"):
        _observation(flow_confidence=0.8)
    with pytest.raises(ValueError, match="condition_id"):
        _observation(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _observation(
            observed_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="future"):
        _report(_observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="redacted"):
        _observation(flow_key="private_key_0xabc")
    with pytest.raises(ValueError, match="redacted"):
        _observation(source_config_version="source-order-v0")
    with pytest.raises(ValueError, match="unique"):
        _report(_observation(flow_key="duplicate"), _observation(flow_key="duplicate"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_observation(), paper_only=False)
    with pytest.raises(FrozenInstanceError):
        _observation().paper_only = False  # type: ignore[misc]


def test_etf_flow_digest_public_numeric_fields_are_decimal_only_and_consistent() -> None:
    report = _report(_observation())

    for row in report.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_seconds")
                or field.name.endswith("_ratio")
                or field.name.endswith("_usd")
                or field.name.endswith("_abs")
                or field.name.endswith("_confidence")
                or field.name == "premium_discount"
            ):
                assert type(value) is Decimal
    for field in fields(report):
        value = getattr(report, field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
            or field.name.endswith("_usd")
            or field.name.endswith("_confidence")
        ):
            assert type(value) is Decimal
    for reason_count in report.reason_code_counts:
        assert reason_count.paper_only is True
        assert reason_count.report_only is True
        assert reason_count.readonly is True
        assert type(reason_count.count) is Decimal
        assert type(reason_count.observation_ratio) is Decimal

    kwargs = {
        field.name: getattr(report, field.name)
        for field in fields(MarketResearchCryptoEtfFlowDigestReport)
    }
    assert MarketResearchCryptoEtfFlowDigestReport(**kwargs).digest_status == "ready"
    with pytest.raises(ValueError, match="observation_count"):
        MarketResearchCryptoEtfFlowDigestReport(
            **{**kwargs, "observation_count": d("2.000000")},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoEtfFlowDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    MarketResearchCryptoEtfFlowDigestReasonCodeCount(
                        reason_code="market_research_crypto_etf_flow_digest_ready",
                        count=d("2.000000"),
                        observation_ratio=d("1.000000"),
                    ),
                ),
            },
        )


def test_etf_flow_digest_payload_is_immutable_redacted_and_report_only() -> None:
    payload = market_research_crypto_etf_flow_digest_payload(
        _report(
            _observation(
                "condition_redacted",
                "btc_spot_etf_flow_redacted",
                asset_symbol="BTC",
            ),
        ),
    )
    payload_text = repr(payload).lower()

    for forbidden in (
        "market_slug",
        "question",
        "wallet",
        "order",
        "auth",
        "token",
        "private",
        "payload_json",
    ):
        assert forbidden not in payload_text
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["rows"][0]["net_flow_usd"] == "64000000.000000"
    assert payload["rows"][0]["paper_only"] is True
    with pytest.raises(TypeError):
        payload["observation_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["net_flow_usd"] = "0.000000"  # type: ignore[index]


def test_etf_flow_digest_payload_rejects_tampered_public_numeric_values() -> None:
    report = _report(_observation())
    object.__setattr__(report, "observation_count", 1)
    with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
        market_research_crypto_etf_flow_digest_payload(report)

    report = _report(_observation())
    object.__setattr__(report, "average_flow_confidence", 0.82)
    with pytest.raises(ValueError, match="JSON value must not be a float"):
        market_research_crypto_etf_flow_digest_payload(report)

    report = _report(_observation())
    object.__setattr__(report, "total_net_flow_usd", _DecimalSubclass("64000000"))
    with pytest.raises(ValueError, match="JSON Decimal value must be exactly Decimal"):
        market_research_crypto_etf_flow_digest_payload(report)


def test_etf_flow_digest_payload_rejects_tampered_flags_and_unknown_values() -> None:
    report = _report(_observation())
    object.__setattr__(report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        market_research_crypto_etf_flow_digest_payload(report)

    report = _report(_observation())
    object.__setattr__(report, "rows", (object(),))
    with pytest.raises(ValueError, match="JSON serializable"):
        market_research_crypto_etf_flow_digest_payload(report)


def test_etf_flow_digest_module_scope_excludes_io_network_durable_store_and_execution_surface() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_etf_flow_digest",
    )
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    forbidden_literals = (
        "market_slug",
        "question",
        "trading",
        "trade",
        "auth",
        "wallet",
        "order",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
        "network",
        "database",
        "store",
        "durable",
        "supabase",
        "persist",
        "sqlite",
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
            assert callee_name not in {"open", "read", "write", "submit", "cancel"}
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "socket",
        "urllib",
        "pathlib",
        "sqlite",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
