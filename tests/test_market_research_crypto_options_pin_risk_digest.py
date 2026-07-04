from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from types import ModuleType

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


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
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_options_pin_risk_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> object:
    module = _module()
    values = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_CRYPTO_OPTIONS_PIN_RISK_DIGEST_CONFIG_VERSION
        ),
        "max_snapshot_age_seconds": d("3600.000000"),
        "max_hours_to_expiry": d("24.000000"),
        "max_strike_distance_ratio": d("0.010000"),
        "max_max_pain_distance_ratio": d("0.015000"),
        "min_near_strike_open_interest_ratio": d("0.300000"),
        "min_gamma_concentration_ratio": d("0.350000"),
        "min_expiry_notional_usd": d("10000000.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return module.MarketResearchCryptoOptionsPinRiskDigestConfig(**values)


def _snapshot(
    condition_id: str = "condition_alpha",
    pin_risk_key: str = "btc_options_pin_ready",
    *,
    asset_symbol: str = "BTC",
    expiry_bucket: str = "weekly",
    observed_at: datetime = GENERATED_AT,
    spot_price: Decimal = d("100.000000"),
    nearest_strike_price: Decimal = d("106.000000"),
    max_pain_price: Decimal = d("108.000000"),
    expiry_notional_usd: Decimal = d("25000000.000000"),
    near_strike_open_interest_ratio: Decimal = d("0.120000"),
    gamma_concentration_ratio: Decimal = d("0.100000"),
    hours_to_expiry: Decimal = d("48.000000"),
    confidence: Decimal = d("0.860000"),
    source_config_version: str = "crypto-options-pin-risk-source-v0",
) -> object:
    module = _module()
    return module.MarketResearchCryptoOptionsPinRiskSnapshot(
        condition_id=condition_id,
        pin_risk_key=pin_risk_key,
        asset_symbol=asset_symbol,
        expiry_bucket=expiry_bucket,
        observed_at=observed_at,
        spot_price=spot_price,
        nearest_strike_price=nearest_strike_price,
        max_pain_price=max_pain_price,
        expiry_notional_usd=expiry_notional_usd,
        near_strike_open_interest_ratio=near_strike_open_interest_ratio,
        gamma_concentration_ratio=gamma_concentration_ratio,
        hours_to_expiry=hours_to_expiry,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *snapshots: object,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
) -> object:
    module = _module()
    return module.build_market_research_crypto_options_pin_risk_digest(
        snapshots,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_pin_risk_digest_empty_input_is_watch_and_report_only() -> None:
    report = _report()

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_market_research_crypto_options_pin_risk_digest"
    )
    assert report.snapshot_count == d("0.000000")
    assert report.ready_snapshot_count == d("0.000000")
    assert report.watch_snapshot_count == d("0.000000")
    assert report.blocked_snapshot_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "market_research_crypto_options_pin_risk_digest_no_inputs",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_pin_risk_digest_flags_high_risk_expiry_pin_cluster() -> None:
    report = _report(
        _snapshot(
            "condition_beta",
            "eth_options_pin_high",
            asset_symbol="ETH",
            observed_at=GENERATED_AT - timedelta(seconds=900),
            spot_price=d("100.000000"),
            nearest_strike_price=d("100.250000"),
            max_pain_price=d("100.500000"),
            expiry_notional_usd=d("42000000.000000"),
            near_strike_open_interest_ratio=d("0.470000"),
            gamma_concentration_ratio=d("0.610000"),
            hours_to_expiry=d("6.000000"),
            confidence=d("0.780000"),
        ),
        _snapshot(
            "condition_alpha",
            "btc_options_pin_ready",
            observed_at=GENERATED_AT - timedelta(seconds=120),
        ),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_options_pin_risk_digest"
    )
    assert report.snapshot_count == d("2.000000")
    assert report.ready_snapshot_count == d("1.000000")
    assert report.watch_snapshot_count == d("0.000000")
    assert report.blocked_snapshot_count == d("1.000000")
    assert report.pin_cluster_snapshot_count == d("1.000000")
    assert report.max_pain_alignment_snapshot_count == d("1.000000")
    assert report.expiry_window_snapshot_count == d("1.000000")
    assert report.notional_gap_snapshot_count == d("0.000000")
    assert report.stale_snapshot_count == d("0.000000")
    assert report.confidence_gap_snapshot_count == d("0.000000")
    assert report.average_strike_distance_ratio == d("0.031250")
    assert report.average_max_pain_distance_ratio == d("0.042500")
    assert report.average_near_strike_open_interest_ratio == d("0.295000")
    assert report.average_gamma_concentration_ratio == d("0.355000")
    assert report.average_hours_to_expiry == d("27.000000")
    assert report.max_snapshot_age_seconds == d("900.000000")
    assert report.pin_cluster_snapshot_ratio == d("0.500000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.condition_id, row.pin_risk_key) for row in report.rows) == (
        ("condition_beta", "eth_options_pin_high"),
        ("condition_alpha", "btc_options_pin_ready"),
    )
    beta = report.rows[0]
    assert beta.digest_status == "blocked"
    assert beta.snapshot_age_seconds == d("900.000000")
    assert beta.strike_distance_ratio == d("0.002500")
    assert beta.max_pain_distance_ratio == d("0.005000")
    assert beta.reason_codes == (
        "market_research_crypto_options_pin_risk_digest_pin_cluster",
        "market_research_crypto_options_pin_risk_digest_max_pain_alignment",
        "market_research_crypto_options_pin_risk_digest_expiry_window",
    )
    assert report.reason_codes == beta.reason_codes


def test_pin_risk_digest_deterministic_sorting_timezones_and_reason_counts() -> None:
    module = _module()
    generated_at = datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 4, 13, 0, tzinfo=timezone(timedelta(hours=1)))

    first = _report(
        _snapshot("condition_b", "source_b", observed_at=observed_at),
        _snapshot("condition_a", "source_a", observed_at=observed_at),
        generated_at=generated_at,
    )
    second = _report(
        _snapshot("condition_a", "source_a", observed_at=observed_at),
        _snapshot("condition_b", "source_b", observed_at=observed_at),
        generated_at=generated_at,
    )

    assert first == second
    assert first.generated_at == GENERATED_AT
    assert first.rows[0].observed_at == GENERATED_AT
    assert tuple(row.pin_risk_key for row in first.rows) == ("source_a", "source_b")
    assert first.source_config_versions == (
        ("source_a", "crypto-options-pin-risk-source-v0"),
        ("source_b", "crypto-options-pin-risk-source-v0"),
    )
    assert first.reason_code_counts == (
        module.MarketResearchCryptoOptionsPinRiskDigestReasonCodeCount(
            reason_code="market_research_crypto_options_pin_risk_digest_ready",
            count=d("2.000000"),
            snapshot_ratio=d("1.000000"),
        ),
    )


def test_pin_risk_digest_validates_exact_types_hard_flags_and_freezing() -> None:
    module = _module()

    assert module.MarketResearchCryptoOptionsPinRiskDigestConfig.__dataclass_params__.frozen
    assert module.MarketResearchCryptoOptionsPinRiskSnapshot.__dataclass_params__.frozen
    assert module.MarketResearchCryptoOptionsPinRiskDigestRow.__dataclass_params__.frozen
    assert (
        module.MarketResearchCryptoOptionsPinRiskDigestReasonCodeCount
        .__dataclass_params__
        .frozen
    )
    assert module.MarketResearchCryptoOptionsPinRiskDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("pin-risk-v0"))
    with pytest.raises(ValueError, match="max_strike_distance_ratio"):
        _config(max_strike_distance_ratio=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="max_hours_to_expiry"):
        _config(max_hours_to_expiry=24)
    with pytest.raises(ValueError, match="confidence"):
        _snapshot(confidence=0.8)
    with pytest.raises(ValueError, match="condition_id"):
        _snapshot(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="source_config_version"):
        _snapshot(source_config_version="pin-risk-secret-v0")
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _snapshot(observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="future"):
        _report(_snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        _report(
            _snapshot(pin_risk_key="duplicate"),
            _snapshot(condition_id="condition_beta", pin_risk_key="duplicate"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_snapshot(), paper_only=False)
    with pytest.raises(FrozenInstanceError):
        _snapshot().paper_only = False  # type: ignore[misc]


def test_pin_risk_digest_public_numeric_fields_are_decimal_only() -> None:
    module = _module()
    report = _report(_snapshot())
    config = _config()

    for item in (config, *report.rows, *report.reason_code_counts, report):
        for field in fields(item):
            value = getattr(item, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
                or field.name.endswith("_usd")
                or field.name.endswith("_price")
                or field.name.endswith("_expiry")
                or field.name == "confidence"
            ):
                assert type(value) is Decimal

    kwargs = {field.name: getattr(report, field.name) for field in fields(report)}
    with pytest.raises(ValueError, match="snapshot_count"):
        module.MarketResearchCryptoOptionsPinRiskDigestReport(
            **{**kwargs, "snapshot_count": 1},
        )


def test_pin_risk_digest_non_default_thresholds_are_reflected_and_applied() -> None:
    default_report = _report(
        _snapshot(
            observed_at=GENERATED_AT - timedelta(seconds=120),
            confidence=d("0.820000"),
        ),
    )
    strict_report = _report(
        _snapshot(
            observed_at=GENERATED_AT - timedelta(seconds=120),
            confidence=d("0.820000"),
        ),
        config=_config(
            config_version="strict-pin-risk-v1",
            max_snapshot_age_seconds=d("60.000000"),
            min_confidence=d("0.900000"),
        ),
    )

    assert default_report.digest_status == "ready"
    assert default_report.reason_codes == (
        "market_research_crypto_options_pin_risk_digest_ready",
    )
    assert strict_report.config_version == "strict-pin-risk-v1"
    assert strict_report.max_allowed_snapshot_age_seconds == d("60.000000")
    assert strict_report.min_confidence == d("0.900000")
    assert strict_report.digest_status == "blocked"
    assert strict_report.stale_snapshot_count == d("1.000000")
    assert strict_report.confidence_gap_snapshot_count == d("1.000000")
    assert strict_report.rows[0].reason_codes == (
        "market_research_crypto_options_pin_risk_digest_stale_snapshot",
        "market_research_crypto_options_pin_risk_digest_confidence_gap",
    )


def test_pin_risk_digest_payload_is_immutable_redacted_and_has_no_live_surface() -> None:
    module = _module()
    payload = module.market_research_crypto_options_pin_risk_digest_payload(
        _report(
            _snapshot(
                "condition_redacted",
                "btc_options_pin_redacted",
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
        "secret",
        "payload_json",
    ):
        assert forbidden not in payload_text
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["snapshot_count"] == "1.000000"
    assert payload["average_strike_distance_ratio"] == "0.060000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["rows"][0]["spot_price"] == "100.000000"
    assert payload["rows"][0]["paper_only"] is True
    with pytest.raises(TypeError):
        payload["snapshot_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["spot_price"] = "0.000000"  # type: ignore[index]


def test_pin_risk_digest_module_scope_excludes_io_and_mutation() -> None:
    module = _module()
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
        "replace",
        "account",
        "secret",
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
            assert callee_name not in {
                "open",
                "read",
                "write",
                "submit",
                "cancel",
                "replace",
            }
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
