from __future__ import annotations

import ast
import importlib
from collections.abc import Mapping
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from types import MappingProxyType

import pytest

from polymarket_alpha_lab.market_research_crypto_basis_trade_unwind_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_BASIS_TRADE_UNWIND_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoBasisTradeUnwindDigestConfig,
    MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount,
    MarketResearchCryptoBasisTradeUnwindDigestReport,
    MarketResearchCryptoBasisTradeUnwindDigestRow,
    MarketResearchCryptoBasisTradeUnwindSnapshot,
    build_market_research_crypto_basis_trade_unwind_digest,
    market_research_crypto_basis_trade_unwind_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
BASE_REASON = "market_research_crypto_basis_trade_unwind_digest_"
READY_REASON = BASE_REASON + "ready"
NO_INPUTS_REASON = BASE_REASON + "no_inputs"
BASIS_COMPRESSION_REASON = BASE_REASON + "basis_compression"
FUNDING_COMPRESSION_REASON = BASE_REASON + "funding_compression"
OPEN_INTEREST_DROP_REASON = BASE_REASON + "open_interest_drop"
SPOT_DEPTH_DROP_REASON = BASE_REASON + "spot_depth_drop"
LIQUIDATION_PRESSURE_REASON = BASE_REASON + "liquidation_pressure"
UNWIND_RATIO_PRESSURE_REASON = BASE_REASON + "unwind_ratio_pressure"
SOURCE_DIVERSITY_GAP_REASON = BASE_REASON + "source_diversity_gap"
STALE_SNAPSHOT_REASON = BASE_REASON + "stale_snapshot"
CONFIDENCE_GAP_REASON = BASE_REASON + "confidence_gap"


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


def _config(
    **overrides: object,
) -> MarketResearchCryptoBasisTradeUnwindDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_BASIS_TRADE_UNWIND_DIGEST_CONFIG_VERSION
        ),
        "max_snapshot_age_seconds": d("1800.000000"),
        "watch_basis_compression_abs": d("0.010000"),
        "blocked_basis_compression_abs": d("0.030000"),
        "watch_funding_compression_abs": d("0.003000"),
        "blocked_funding_compression_abs": d("0.008000"),
        "watch_open_interest_drop_ratio": d("0.100000"),
        "blocked_open_interest_drop_ratio": d("0.300000"),
        "watch_spot_depth_drop_ratio": d("0.150000"),
        "blocked_spot_depth_drop_ratio": d("0.400000"),
        "watch_liquidation_usd": d("500000.000000"),
        "blocked_liquidation_usd": d("1500000.000000"),
        "watch_unwind_ratio": d("0.100000"),
        "blocked_unwind_ratio": d("0.350000"),
        "min_venue_source_count": d("3.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoBasisTradeUnwindDigestConfig(**values)


def _snapshot(
    condition_id: str = "condition_alpha",
    unwind_key: str = "btc_basis_unwind",
    *,
    asset_symbol: str = "BTC",
    observed_at: datetime = GENERATED_AT,
    venue_source_count: Decimal = d("3.000000"),
    current_basis: Decimal = d("0.020000"),
    previous_basis: Decimal = d("0.025000"),
    current_funding_rate: Decimal = d("0.002000"),
    previous_funding_rate: Decimal = d("0.003000"),
    open_interest_usd: Decimal = d("5000000.000000"),
    previous_open_interest_usd: Decimal = d("5200000.000000"),
    spot_depth_usd: Decimal = d("2000000.000000"),
    previous_spot_depth_usd: Decimal = d("2100000.000000"),
    liquidation_usd: Decimal = d("100000.000000"),
    unwind_ratio: Decimal = d("0.050000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "basis-unwind-source-v0",
) -> MarketResearchCryptoBasisTradeUnwindSnapshot:
    return MarketResearchCryptoBasisTradeUnwindSnapshot(
        condition_id=condition_id,
        unwind_key=unwind_key,
        asset_symbol=asset_symbol,
        observed_at=observed_at,
        venue_source_count=venue_source_count,
        current_basis=current_basis,
        previous_basis=previous_basis,
        current_funding_rate=current_funding_rate,
        previous_funding_rate=previous_funding_rate,
        open_interest_usd=open_interest_usd,
        previous_open_interest_usd=previous_open_interest_usd,
        spot_depth_usd=spot_depth_usd,
        previous_spot_depth_usd=previous_spot_depth_usd,
        liquidation_usd=liquidation_usd,
        unwind_ratio=unwind_ratio,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *snapshots: MarketResearchCryptoBasisTradeUnwindSnapshot,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoBasisTradeUnwindDigestConfig | None = None,
) -> MarketResearchCryptoBasisTradeUnwindDigestReport:
    return build_market_research_crypto_basis_trade_unwind_digest(
        snapshots,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_basis_trade_unwind_digest_blocks_empty_input_report_only() -> None:
    report = _report()

    assert isinstance(report, MarketResearchCryptoBasisTradeUnwindDigestReport)
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-crypto-basis-trade-unwind-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_basis_trade_unwind_digest"
    )
    assert report.snapshot_count == d("0.000000")
    assert report.ready_snapshot_count == d("0.000000")
    assert report.watch_snapshot_count == d("0.000000")
    assert report.blocked_snapshot_count == d("0.000000")
    assert report.rows == ()
    assert report.source_config_versions == ()
    assert report.reason_codes == (NO_INPUTS_REASON,)
    assert report.reason_code_counts == (
        MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount(
            reason_code=NO_INPUTS_REASON,
            count=d("1.000000"),
            snapshot_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_basis_trade_unwind_digest_models_unwind_pressure_and_counts() -> None:
    report = _report(
        _snapshot(
            "condition_beta",
            "eth_basis_unwind",
            asset_symbol="ETH",
            observed_at=GENERATED_AT - timedelta(seconds=2400),
            venue_source_count=d("1.000000"),
            current_basis=d("0.005000"),
            previous_basis=d("0.060000"),
            current_funding_rate=d("0.001000"),
            previous_funding_rate=d("0.014000"),
            open_interest_usd=d("2000000.000000"),
            previous_open_interest_usd=d("5000000.000000"),
            spot_depth_usd=d("1000000.000000"),
            previous_spot_depth_usd=d("3000000.000000"),
            liquidation_usd=d("2500000.000000"),
            unwind_ratio=d("0.550000"),
            confidence=d("0.520000"),
        ),
        _snapshot(),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_basis_trade_unwind_digest"
    )
    assert report.snapshot_count == d("2.000000")
    assert report.ready_snapshot_count == d("1.000000")
    assert report.watch_snapshot_count == d("0.000000")
    assert report.blocked_snapshot_count == d("1.000000")
    assert report.basis_compression_snapshot_count == d("1.000000")
    assert report.funding_compression_snapshot_count == d("1.000000")
    assert report.open_interest_drop_snapshot_count == d("1.000000")
    assert report.spot_depth_drop_snapshot_count == d("1.000000")
    assert report.liquidation_pressure_snapshot_count == d("1.000000")
    assert report.unwind_ratio_pressure_snapshot_count == d("1.000000")
    assert report.source_diversity_gap_snapshot_count == d("1.000000")
    assert report.stale_snapshot_count == d("1.000000")
    assert report.confidence_gap_snapshot_count == d("1.000000")
    assert report.average_basis_compression_abs == d("0.030000")
    assert report.average_funding_compression_abs == d("0.007000")
    assert report.average_open_interest_drop_ratio == d("0.319231")
    assert report.average_spot_depth_drop_ratio == d("0.357143")
    assert report.total_liquidation_usd == d("2600000.000000")
    assert report.average_unwind_ratio == d("0.300000")
    assert report.average_confidence == d("0.670000")
    assert report.max_snapshot_age_seconds == d("2400.000000")

    assert tuple((row.condition_id, row.unwind_key) for row in report.rows) == (
        ("condition_beta", "eth_basis_unwind"),
        ("condition_alpha", "btc_basis_unwind"),
    )
    beta = report.rows[0]
    assert beta.digest_status == "blocked"
    assert beta.snapshot_age_seconds == d("2400.000000")
    assert beta.basis_compression_abs == d("0.055000")
    assert beta.funding_compression_abs == d("0.013000")
    assert beta.open_interest_drop_ratio == d("0.600000")
    assert beta.spot_depth_drop_ratio == d("0.666667")
    assert beta.reason_codes == (
        BASIS_COMPRESSION_REASON,
        FUNDING_COMPRESSION_REASON,
        OPEN_INTEREST_DROP_REASON,
        SPOT_DEPTH_DROP_REASON,
        LIQUIDATION_PRESSURE_REASON,
        UNWIND_RATIO_PRESSURE_REASON,
        SOURCE_DIVERSITY_GAP_REASON,
        STALE_SNAPSHOT_REASON,
        CONFIDENCE_GAP_REASON,
    )
    assert report.reason_codes == beta.reason_codes
    assert report.reason_code_counts == tuple(
        MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount(
            reason_code=reason_code,
            count=d("1.000000"),
            snapshot_ratio=d("0.500000"),
        )
        for reason_code in beta.reason_codes
    )


def test_basis_trade_unwind_digest_normalizes_timezones_and_watch_reasons() -> None:
    generated_at = datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 6, 13, 0, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _snapshot(
            "condition_gamma",
            "sol_basis_unwind",
            asset_symbol="SOL",
            observed_at=observed_at,
            venue_source_count=d("2.000000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == GENERATED_AT
    assert report.rows[0].snapshot_age_seconds == d("0.000000")
    assert report.digest_status == "watch"
    assert report.reason_code_counts == (
        MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount(
            reason_code=SOURCE_DIVERSITY_GAP_REASON,
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("sol_basis_unwind", "basis-unwind-source-v0"),
    )


def test_basis_trade_unwind_digest_validates_types_flags_and_freezing() -> None:
    for item_type in (
        MarketResearchCryptoBasisTradeUnwindDigestConfig,
        MarketResearchCryptoBasisTradeUnwindSnapshot,
        MarketResearchCryptoBasisTradeUnwindDigestRow,
        MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount,
        MarketResearchCryptoBasisTradeUnwindDigestReport,
    ):
        assert item_type.__dataclass_params__.frozen
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Unsupported{item_type.__name__}", (item_type,), {})

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("basis-trade-unwind-v0"))
    with pytest.raises(ValueError, match="blocked_basis_compression_abs"):
        _config(blocked_basis_compression_abs=_DecimalSubclass("0.030000"))
    with pytest.raises(ValueError, match="min_confidence"):
        _config(min_confidence=d("0.7"))
    with pytest.raises(ValueError, match="min_venue_source_count"):
        _config(min_venue_source_count=3)
    with pytest.raises(ValueError, match="condition_id"):
        _snapshot(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="confidence"):
        _snapshot(confidence=0.8)
    with pytest.raises(ValueError, match="confidence"):
        _snapshot(confidence=d("0.82"))
    with pytest.raises(ValueError, match="redacted"):
        _snapshot(source_config_version="source-auth-v0")
    with pytest.raises(ValueError, match="generated_at"):
        _report(_snapshot(), generated_at=_DateTimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        _report(_snapshot(), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        _snapshot(observed_at=_DateTimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        _snapshot(observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        _snapshot(observed_at=datetime(2026, 7, 6, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="future"):
        _report(_snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)))

    report = _report(_snapshot())
    for item in (_config(), _snapshot(), report.rows[0], report.reason_code_counts[0], report):
        for flag in ("paper_only", "report_only", "readonly"):
            with pytest.raises(ValueError, match=flag):
                replace(item, **{flag: False})
    with pytest.raises(FrozenInstanceError):
        _snapshot().paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.reason_code_counts[0].readonly = False  # type: ignore[misc]


def test_basis_trade_unwind_digest_public_numerics_are_decimal_only() -> None:
    report = _report(_snapshot())

    for item in (_config(), *report.rows, *report.reason_code_counts, report):
        for field in fields(item):
            value = getattr(item, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
                or field.name.endswith("_usd")
                or field.name.endswith("_abs")
                or field.name.endswith("_rate")
                or field.name
                in {
                    "current_basis",
                    "previous_basis",
                    "unwind_ratio",
                    "confidence",
                    "min_confidence",
                }
            ):
                assert type(value) is Decimal
                assert value.as_tuple().exponent == d("0.000001").as_tuple().exponent

    valid_kwargs = {
        field.name: getattr(report, field.name)
        for field in fields(MarketResearchCryptoBasisTradeUnwindDigestReport)
    }
    with pytest.raises(ValueError, match="snapshot_count"):
        MarketResearchCryptoBasisTradeUnwindDigestReport(
            **{**valid_kwargs, "snapshot_count": 1},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoBasisTradeUnwindDigestReport(
            **{
                **valid_kwargs,
                "reason_code_counts": (
                    MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount(
                        reason_code=READY_REASON,
                        count=d("2.000000"),
                        snapshot_ratio=d("1.000000"),
                    ),
                ),
            },
        )
    with pytest.raises(ValueError, match="count"):
        MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount(
            reason_code=READY_REASON,
            count=d("0.500000"),
            snapshot_ratio=d("1.000000"),
        )
    with pytest.raises(ValueError, match="count"):
        MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount(
            reason_code=READY_REASON,
            count=d("0.000000"),
            snapshot_ratio=d("1.000000"),
        )


def test_basis_trade_unwind_digest_payload_is_immutable_redacted_and_six_decimal() -> None:
    report = _report(_snapshot())
    assert type(report.rows) is tuple
    assert type(report.rows[0].reason_codes) is tuple
    assert type(report.reason_codes) is tuple
    assert type(report.reason_code_counts) is tuple
    assert type(report.source_config_versions) is tuple
    payload = market_research_crypto_basis_trade_unwind_digest_payload(report)
    payload_text = repr(payload).lower()

    assert type(payload) is MappingProxyType
    for forbidden in ("market" + "_slug", "ques" + "tion", "payload" + "_json"):
        assert forbidden not in payload_text
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["snapshot_count"] == "1.000000"
    assert payload["average_basis_compression_abs"] == "0.005000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["current_basis"] == "0.020000"
    assert payload["reason_code_counts"][0]["paper_only"] is True
    with pytest.raises(TypeError):
        payload["snapshot_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["current_basis"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["reason_code_counts"][0]["count"] = "0.000000"  # type: ignore[index]

    def assert_six_decimal_numeric_strings(value: object) -> None:
        if isinstance(value, str):
            if value.replace("-", "", 1).replace(".", "", 1).isdigit() and "." in value:
                assert len(value.rsplit(".", maxsplit=1)[1]) == 6
            return
        if isinstance(value, Mapping):
            for item in value.values():
                assert_six_decimal_numeric_strings(item)
            return
        if isinstance(value, tuple):
            for item in value:
                assert_six_decimal_numeric_strings(item)

    assert_six_decimal_numeric_strings(payload)


def test_basis_trade_unwind_digest_payload_revalidates_tampered_values() -> None:
    report = _report(_snapshot())
    object.__setattr__(report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        market_research_crypto_basis_trade_unwind_digest_payload(report)

    report = _report(_snapshot())
    object.__setattr__(report, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        market_research_crypto_basis_trade_unwind_digest_payload(report)

    report = _report(_snapshot())
    object.__setattr__(report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_crypto_basis_trade_unwind_digest_payload(report)

    report = _report(_snapshot())
    object.__setattr__(report.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        market_research_crypto_basis_trade_unwind_digest_payload(report)

    report = _report(_snapshot())
    object.__setattr__(report.rows[0], "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        market_research_crypto_basis_trade_unwind_digest_payload(report)

    report = _report(_snapshot())
    object.__setattr__(report.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_crypto_basis_trade_unwind_digest_payload(report)

    report = _report(_snapshot())
    object.__setattr__(
        report,
        "generated_at",
        datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="UTC"):
        market_research_crypto_basis_trade_unwind_digest_payload(report)

    report = _report(_snapshot())
    object.__setattr__(report.rows[0], "current_basis", d("0.0200000"))
    with pytest.raises(ValueError, match="six-decimal"):
        market_research_crypto_basis_trade_unwind_digest_payload(report)

    report = _report(_snapshot())
    object.__setattr__(report.reason_code_counts[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        market_research_crypto_basis_trade_unwind_digest_payload(report)

    report = _report(_snapshot())
    object.__setattr__(report.reason_code_counts[0], "count", d("0.000000"))
    with pytest.raises(ValueError, match="count"):
        market_research_crypto_basis_trade_unwind_digest_payload(report)

    report = _report(_snapshot())
    object.__setattr__(report.reason_code_counts[0], "count", d("0.500000"))
    with pytest.raises(ValueError, match="count"):
        market_research_crypto_basis_trade_unwind_digest_payload(report)

    report = _report(_snapshot())
    object.__setattr__(report.reason_code_counts[0], "snapshot_ratio", d("1.500000"))
    with pytest.raises(ValueError, match="snapshot_ratio"):
        market_research_crypto_basis_trade_unwind_digest_payload(report)

    report = _report(_snapshot())
    object.__setattr__(
        report.rows[0],
        "observed_at",
        _DateTimeSubclass(2026, 7, 6, 8, 0, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="observed_at"):
        market_research_crypto_basis_trade_unwind_digest_payload(report)


def test_basis_trade_unwind_digest_rejects_duplicates_and_bad_consistency() -> None:
    with pytest.raises(ValueError, match="unique"):
        _report(
            _snapshot(unwind_key="duplicate"),
            _snapshot(unwind_key="duplicate"),
        )

    report = _report(
        _snapshot("condition_a", "source_a"),
        _snapshot("condition_b", "source_b"),
    )
    kwargs = {
        field.name: getattr(report, field.name)
        for field in fields(MarketResearchCryptoBasisTradeUnwindDigestReport)
    }
    assert MarketResearchCryptoBasisTradeUnwindDigestReport(**kwargs).digest_status == "ready"

    with pytest.raises(ValueError, match="rows"):
        MarketResearchCryptoBasisTradeUnwindDigestReport(
            **{**kwargs, "rows": tuple(reversed(report.rows))},
        )
    with pytest.raises(ValueError, match="source_config_versions"):
        MarketResearchCryptoBasisTradeUnwindDigestReport(
            **{
                **kwargs,
                "source_config_versions": tuple(reversed(report.source_config_versions)),
            },
        )


def test_basis_trade_unwind_digest_module_scope_excludes_io_and_forbidden_surface() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_basis_trade_unwind_digest",
    )
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    assert "as" + "dict" not in lowered
    for token in ("market" + "_slug", "ques" + "tion", "payload" + "_json"):
        assert token not in lowered

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
            assert callee_name not in {"open", "read", "write"}
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psy" + "copg",
        "req" + "uests",
        "sock" + "et",
        "url" + "lib",
        "path" + "lib",
        "sql" + "ite",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
