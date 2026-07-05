from __future__ import annotations

import ast
import importlib
from collections.abc import Mapping
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_crypto_funding_rate_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_FUNDING_RATE_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoFundingRateDigestConfig,
    MarketResearchCryptoFundingRateDigestReasonCodeCount,
    MarketResearchCryptoFundingRateDigestReport,
    MarketResearchCryptoFundingRateDigestRow,
    MarketResearchCryptoFundingRateSnapshot,
    build_market_research_crypto_funding_rate_digest,
    market_research_crypto_funding_rate_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> MarketResearchCryptoFundingRateDigestConfig:
    values = {
        "config_version": DEFAULT_MARKET_RESEARCH_CRYPTO_FUNDING_RATE_DIGEST_CONFIG_VERSION,
        "max_snapshot_age_seconds": d("3600.000000"),
        "max_funding_rate_abs": d("0.010000"),
        "max_predicted_funding_rate_abs": d("0.012000"),
        "max_funding_rate_change_abs": d("0.006000"),
        "min_exchange_source_count": d("3.000000"),
        "min_open_interest_usd": d("1000000.000000"),
        "min_confidence": d("0.650000"),
    }
    values.update(overrides)
    return MarketResearchCryptoFundingRateDigestConfig(**values)


def _snapshot(
    condition_id: str = "condition_alpha",
    funding_rate_key: str = "btc_perp_funding",
    *,
    asset_symbol: str = "BTC",
    exchange_source_count: Decimal = d("3.000000"),
    funding_rate: Decimal = d("0.004000"),
    predicted_funding_rate: Decimal = d("0.005000"),
    previous_funding_rate: Decimal = d("0.002000"),
    open_interest_usd: Decimal = d("2400000.000000"),
    confidence: Decimal = d("0.820000"),
    observed_at: datetime = GENERATED_AT,
    source_config_version: str = "funding-rate-source-v0",
) -> MarketResearchCryptoFundingRateSnapshot:
    return MarketResearchCryptoFundingRateSnapshot(
        condition_id=condition_id,
        funding_rate_key=funding_rate_key,
        asset_symbol=asset_symbol,
        observed_at=observed_at,
        exchange_source_count=exchange_source_count,
        funding_rate=funding_rate,
        predicted_funding_rate=predicted_funding_rate,
        previous_funding_rate=previous_funding_rate,
        open_interest_usd=open_interest_usd,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *snapshots: MarketResearchCryptoFundingRateSnapshot,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoFundingRateDigestConfig | None = None,
) -> MarketResearchCryptoFundingRateDigestReport:
    return build_market_research_crypto_funding_rate_digest(
        snapshots,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_funding_rate_digest_models_pressure_gaps_and_confidence() -> None:
    report = _report(
        _snapshot(
            "condition_beta",
            "eth_perp_funding",
            asset_symbol="ETH",
            observed_at=GENERATED_AT - timedelta(seconds=4_200),
            exchange_source_count=d("1.000000"),
            funding_rate=d("-0.018000"),
            predicted_funding_rate=d("-0.016000"),
            previous_funding_rate=d("-0.006000"),
            open_interest_usd=d("700000.000000"),
            confidence=d("0.520000"),
        ),
        _snapshot(
            "condition_alpha",
            "btc_perp_funding",
            observed_at=GENERATED_AT - timedelta(seconds=120),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_funding_rate_digest"
    )
    assert report.snapshot_count == d("2.000000")
    assert report.ready_snapshot_count == d("1.000000")
    assert report.watch_snapshot_count == d("0.000000")
    assert report.blocked_snapshot_count == d("1.000000")
    assert report.funding_rate_pressure_snapshot_count == d("1.000000")
    assert report.predicted_funding_rate_pressure_snapshot_count == d("1.000000")
    assert report.funding_rate_change_snapshot_count == d("1.000000")
    assert report.source_diversity_gap_snapshot_count == d("1.000000")
    assert report.open_interest_gap_snapshot_count == d("1.000000")
    assert report.stale_snapshot_count == d("1.000000")
    assert report.confidence_gap_snapshot_count == d("1.000000")
    assert report.average_funding_rate == d("-0.007000")
    assert report.average_predicted_funding_rate == d("-0.005500")
    assert report.average_funding_rate_change_abs == d("0.007000")
    assert report.max_snapshot_age_seconds == d("4200.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.condition_id, row.funding_rate_key) for row in report.rows) == (
        ("condition_beta", "eth_perp_funding"),
        ("condition_alpha", "btc_perp_funding"),
    )
    beta = report.rows[0]
    assert beta.digest_status == "blocked"
    assert beta.snapshot_age_seconds == d("4200.000000")
    assert beta.funding_rate_abs == d("0.018000")
    assert beta.predicted_funding_rate_abs == d("0.016000")
    assert beta.funding_rate_change_abs == d("0.012000")
    assert beta.reason_codes == (
        "market_research_crypto_funding_rate_digest_funding_rate_pressure",
        "market_research_crypto_funding_rate_digest_predicted_funding_rate_pressure",
        "market_research_crypto_funding_rate_digest_funding_rate_change",
        "market_research_crypto_funding_rate_digest_source_diversity_gap",
        "market_research_crypto_funding_rate_digest_open_interest_gap",
        "market_research_crypto_funding_rate_digest_stale_snapshot",
        "market_research_crypto_funding_rate_digest_confidence_gap",
    )
    assert report.reason_codes == beta.reason_codes


def test_funding_rate_digest_normalizes_timezones_and_reason_counts() -> None:
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 2, 12, 0, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _snapshot(
            "condition_gamma",
            "sol_perp_funding",
            asset_symbol="SOL",
            observed_at=observed_at,
            exchange_source_count=d("2.000000"),
            funding_rate=d("0.006000"),
            predicted_funding_rate=d("0.004000"),
            previous_funding_rate=d("0.001000"),
            open_interest_usd=d("2000000.000000"),
            confidence=d("0.760000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 7, 2, 11, 0, tzinfo=UTC)
    assert report.max_snapshot_age_seconds == d("3600.000000")
    assert report.digest_status == "watch"
    assert report.reason_code_counts == (
        MarketResearchCryptoFundingRateDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_funding_rate_digest_source_diversity_gap"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("sol_perp_funding", "funding-rate-source-v0"),
    )


def test_funding_rate_digest_empty_input_is_blocked_and_sorted_deterministically() -> None:
    empty = _report()
    assert empty.digest_status == "blocked"
    assert empty.recommended_next_step == (
        "block_report_only_market_research_crypto_funding_rate_digest"
    )
    assert empty.snapshot_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == ("market_research_crypto_funding_rate_digest_no_inputs",)
    assert empty.reason_code_counts == (
        MarketResearchCryptoFundingRateDigestReasonCodeCount(
            reason_code="market_research_crypto_funding_rate_digest_no_inputs",
            count=d("1.000000"),
            snapshot_ratio=d("0.000000"),
        ),
    )

    empty_payload = market_research_crypto_funding_rate_digest_payload(empty)
    assert empty_payload["reason_code_counts"][0]["reason_code"] == (
        "market_research_crypto_funding_rate_digest_no_inputs"
    )
    assert empty_payload["reason_code_counts"][0]["count"] == "1.000000"
    assert empty_payload["reason_code_counts"][0]["snapshot_ratio"] == "0.000000"

    first = _report(
        _snapshot("condition_b", "source_b"),
        _snapshot("condition_a", "source_a"),
    )
    second = _report(
        _snapshot("condition_a", "source_a"),
        _snapshot("condition_b", "source_b"),
    )

    assert first == second
    assert tuple(row.funding_rate_key for row in first.rows) == ("source_a", "source_b")


def test_funding_rate_digest_validates_exact_types_flags_and_freezing() -> None:
    assert MarketResearchCryptoFundingRateDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoFundingRateSnapshot.__dataclass_params__.frozen
    assert MarketResearchCryptoFundingRateDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoFundingRateDigestReasonCodeCount.__dataclass_params__.frozen
    assert MarketResearchCryptoFundingRateDigestReport.__dataclass_params__.frozen

    for public_model in (
        MarketResearchCryptoFundingRateDigestConfig,
        MarketResearchCryptoFundingRateSnapshot,
        MarketResearchCryptoFundingRateDigestRow,
        MarketResearchCryptoFundingRateDigestReasonCodeCount,
        MarketResearchCryptoFundingRateDigestReport,
    ):
        with pytest.raises(TypeError, match="subclassing"):

            class _RejectedSubclass(public_model):  # type: ignore[misc, valid-type]
                pass

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("funding-rate-v0"))
    with pytest.raises(ValueError, match="max_funding_rate_abs"):
        _config(max_funding_rate_abs=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="min_exchange_source_count"):
        _config(min_exchange_source_count=3)
    with pytest.raises(ValueError, match="confidence"):
        _snapshot(confidence=0.8)
    with pytest.raises(ValueError, match="condition_id"):
        _snapshot(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="redacted"):
        _snapshot(source_config_version="source-order-v0")
    for unsafe_text in (
        "source-auth-v0",
        "source-api_key-v0",
        "source-cancel-v0",
        "source-replace-v0",
        "source-exchange-v0",
        "source-secret-v0",
    ):
        with pytest.raises(ValueError, match="redacted"):
            _snapshot(source_config_version=unsafe_text)
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config"):
        build_market_research_crypto_funding_rate_digest(
            (),
            config=False,  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _snapshot(observed_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="future"):
        _report(_snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_snapshot(), paper_only=False)
    report = _report(_snapshot())
    with pytest.raises(ValueError, match="report_only"):
        replace(report.reason_code_counts[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(FrozenInstanceError):
        _snapshot().paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.reason_code_counts[0].readonly = False  # type: ignore[misc]


def test_funding_rate_digest_public_numeric_fields_are_decimal_only() -> None:
    report = _report(_snapshot())

    for row in report.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_seconds")
                or field.name.endswith("_rate")
                or field.name.endswith("_abs")
                or field.name.endswith("_usd")
                or field.name == "confidence"
            ):
                assert type(value) is Decimal
    for field in fields(report):
        value = getattr(report, field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
            or field.name.endswith("_rate")
            or field.name.endswith("_abs")
        ):
            assert type(value) is Decimal
    for reason_count in report.reason_code_counts:
        assert type(reason_count.count) is Decimal
        assert type(reason_count.snapshot_ratio) is Decimal

    with pytest.raises(ValueError, match="snapshot_count"):
        MarketResearchCryptoFundingRateDigestReport(
            generated_at=GENERATED_AT,
            config_version=DEFAULT_MARKET_RESEARCH_CRYPTO_FUNDING_RATE_DIGEST_CONFIG_VERSION,
            digest_status="ready",
            recommended_next_step=(
                "allow_report_only_market_research_crypto_funding_rate_digest"
            ),
            snapshot_count=1,  # type: ignore[arg-type]
            ready_snapshot_count=d("1.000000"),
            watch_snapshot_count=d("0.000000"),
            blocked_snapshot_count=d("0.000000"),
            funding_rate_pressure_snapshot_count=d("0.000000"),
            predicted_funding_rate_pressure_snapshot_count=d("0.000000"),
            funding_rate_change_snapshot_count=d("0.000000"),
            source_diversity_gap_snapshot_count=d("0.000000"),
            open_interest_gap_snapshot_count=d("0.000000"),
            stale_snapshot_count=d("0.000000"),
            confidence_gap_snapshot_count=d("0.000000"),
            average_funding_rate=d("0.004000"),
            average_predicted_funding_rate=d("0.005000"),
            average_funding_rate_change_abs=d("0.002000"),
            max_snapshot_age_seconds=d("0.000000"),
            max_allowed_snapshot_age_seconds=d("3600.000000"),
            max_allowed_funding_rate_abs=d("0.010000"),
            max_allowed_predicted_funding_rate_abs=d("0.012000"),
            max_allowed_funding_rate_change_abs=d("0.006000"),
            min_exchange_source_count=d("3.000000"),
            min_open_interest_usd=d("1000000.000000"),
            min_confidence=d("0.650000"),
            rows=report.rows,
            source_config_versions=(("btc_perp_funding", "funding-rate-source-v0"),),
            reason_code_counts=report.reason_code_counts,
            reason_codes=("market_research_crypto_funding_rate_digest_ready",),
        )


def test_funding_rate_digest_payload_is_immutable_redacted_and_report_only() -> None:
    payload = market_research_crypto_funding_rate_digest_payload(
        _report(
            _snapshot(
                "condition_redacted",
                "btc_perp_funding_redacted",
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
    assert payload["snapshot_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["rows"][0]["funding_rate"] == "0.004000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["reason_code_counts"][0]["paper_only"] is True
    assert payload["reason_code_counts"][0]["report_only"] is True
    assert payload["reason_code_counts"][0]["readonly"] is True
    with pytest.raises(TypeError):
        payload["snapshot_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["funding_rate"] = "0.000000"  # type: ignore[index]

    def assert_six_decimal_numeric_strings(value: object) -> None:
        if isinstance(value, str):
            if value.replace("-", "", 1).replace(".", "", 1).isdigit() and "." in value:
                fractional = value.rsplit(".", maxsplit=1)[1]
                assert len(fractional) == 6
            return
        if isinstance(value, Mapping):
            for item in value.values():
                assert_six_decimal_numeric_strings(item)
            return
        if isinstance(value, tuple):
            for item in value:
                assert_six_decimal_numeric_strings(item)

    assert_six_decimal_numeric_strings(payload)


def test_funding_rate_digest_payload_rejects_tampered_nested_public_values() -> None:
    report = _report(_snapshot())

    object.__setattr__(report.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_crypto_funding_rate_digest_payload(report)
    object.__setattr__(report.rows[0], "readonly", True)

    object.__setattr__(report.reason_code_counts[0], "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        market_research_crypto_funding_rate_digest_payload(report)
    object.__setattr__(report.reason_code_counts[0], "report_only", True)

    object.__setattr__(report.rows[0], "funding_rate", d("0.0040001"))
    with pytest.raises(ValueError, match="six decimals"):
        market_research_crypto_funding_rate_digest_payload(report)


def test_funding_rate_digest_rejects_duplicates_and_bad_report_consistency() -> None:
    with pytest.raises(ValueError, match="unique"):
        _report(
            _snapshot(funding_rate_key="duplicate"),
            _snapshot(funding_rate_key="duplicate"),
        )

    valid = _report(
        _snapshot("condition_a", "source_a"),
        _snapshot("condition_b", "source_b"),
    )
    kwargs = {
        field.name: getattr(valid, field.name)
        for field in fields(MarketResearchCryptoFundingRateDigestReport)
    }
    assert MarketResearchCryptoFundingRateDigestReport(**kwargs).digest_status == "ready"

    with pytest.raises(ValueError, match="snapshot_count"):
        MarketResearchCryptoFundingRateDigestReport(
            **{**kwargs, "snapshot_count": d("3.000000")},
        )
    with pytest.raises(ValueError, match="digest_status"):
        MarketResearchCryptoFundingRateDigestReport(
            **{**kwargs, "digest_status": "blocked"},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoFundingRateDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    MarketResearchCryptoFundingRateDigestReasonCodeCount(
                        reason_code="market_research_crypto_funding_rate_digest_ready",
                        count=d("3.000000"),
                        snapshot_ratio=d("1.000000"),
                    ),
                ),
            },
        )
    with pytest.raises(ValueError, match="rows"):
        MarketResearchCryptoFundingRateDigestReport(
            **{**kwargs, "rows": tuple(reversed(valid.rows))},
        )
    with pytest.raises(ValueError, match="source_config_versions"):
        MarketResearchCryptoFundingRateDigestReport(
            **{
                **kwargs,
                "source_config_versions": tuple(reversed(valid.source_config_versions)),
            },
        )
    with pytest.raises(ValueError, match="source_config_versions"):
        MarketResearchCryptoFundingRateDigestReport(
            **{
                **kwargs,
                "source_config_versions": (
                    ("source_a", "funding-rate-source-v0"),
                    ("source_z", "funding-rate-source-v0"),
                ),
            },
        )


def test_funding_rate_digest_rejects_manual_zero_and_nondeterministic_reason_counts() -> None:
    with pytest.raises(ValueError, match="count"):
        MarketResearchCryptoFundingRateDigestReasonCodeCount(
            reason_code="market_research_crypto_funding_rate_digest_ready",
            count=d("0.000000"),
            snapshot_ratio=d("0.000000"),
        )

    report = _report(
        _snapshot("condition_ready", "ready_source"),
        _snapshot(
            "condition_gap",
            "gap_source",
            exchange_source_count=d("1.000000"),
        ),
    )
    assert tuple(item.reason_code for item in report.reason_code_counts) == (
        "market_research_crypto_funding_rate_digest_source_diversity_gap",
        "market_research_crypto_funding_rate_digest_ready",
    )

    kwargs = {
        field.name: getattr(report, field.name)
        for field in fields(MarketResearchCryptoFundingRateDigestReport)
    }
    with pytest.raises(ValueError, match="deterministic"):
        MarketResearchCryptoFundingRateDigestReport(
            **{
                **kwargs,
                "reason_code_counts": tuple(reversed(report.reason_code_counts)),
            },
        )


def test_funding_rate_digest_module_scope_excludes_execution_io_network_and_persistence() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_funding_rate_digest",
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
