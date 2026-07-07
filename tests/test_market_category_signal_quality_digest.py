import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_category_signal_quality_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    category_id: str,
    market_id: str,
    *,
    source_family: str = "news",
    source_observed_at: datetime | None = None,
    forecast_low: str = "0.450000",
    forecast_high: str = "0.550000",
    probability_now: str = "0.500000",
    probability_previous: str = "0.510000",
    probability_observed_at: datetime | None = None,
    resolution_ready: bool = True,
    resolution_source_count: str = "2",
    reason_codes: tuple[str, ...] = ("input_signal_quality_available",),
):
    digest = api()
    observed_at = source_observed_at or GENERATED_AT - timedelta(hours=2)
    probability_at = probability_observed_at or GENERATED_AT - timedelta(hours=1)
    return digest.MarketCategorySignalQualityInput(
        category_id=category_id,
        market_id=market_id,
        source_family=source_family,
        source_observed_at=observed_at,
        forecast_low=d(forecast_low),
        forecast_high=d(forecast_high),
        probability_now=d(probability_now),
        probability_previous=d(probability_previous),
        probability_observed_at=probability_at,
        resolution_ready=resolution_ready,
        resolution_source_count=d(resolution_source_count),
        reason_codes=reason_codes,
    )


def report(*rows, generated_at: datetime = GENERATED_AT):
    digest = api()
    return digest.build_market_category_signal_quality_digest_report(
        rows,
        config=digest.MarketCategorySignalQualityDigestConfig(),
        generated_at=generated_at,
    )


def assert_no_public_numbers(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload contains public numeric {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numbers(item)


def test_empty_input_returns_blocked_report_only_decimal_counts() -> None:
    quality = report()

    assert is_dataclass(quality)
    assert quality.generated_at == GENERATED_AT
    assert quality.config_version == "market-category-signal-quality-digest-v0"
    assert quality.category_count == d("0")
    assert quality.market_count == d("0")
    assert quality.clear_count == d("0")
    assert quality.watch_count == d("0")
    assert quality.blocked_count == d("0")
    assert quality.status == "blocked"
    assert quality.reason_codes == ("signal_quality_digest_empty",)
    assert quality.category_rows == ()
    assert quality.paper_only is True
    assert quality.report_only is True
    assert quality.readonly is True


def test_clear_watch_and_blocked_category_rows_roll_up_deterministically() -> None:
    quality = report(
        signal("politics", "pol-1", source_family="news"),
        signal(
            "politics",
            "pol-2",
            source_family="research",
            probability_now="0.520000",
            probability_previous="0.500000",
        ),
        signal(
            "crypto",
            "btc-1",
            source_observed_at=GENERATED_AT - timedelta(hours=30),
        ),
        signal(
            "sports",
            "cup-1",
            forecast_low="0.100000",
            forecast_high="0.950000",
            resolution_ready=False,
            resolution_source_count="0",
        ),
    )

    assert quality.status == "blocked"
    assert quality.category_count == d("3")
    assert quality.market_count == d("4")
    assert quality.clear_count == d("1")
    assert quality.watch_count == d("1")
    assert quality.blocked_count == d("1")
    assert quality.reason_codes == (
        "signal_quality_digest_blocked",
        "signal_quality_resolution_not_ready",
        "signal_quality_sources_stale",
    )
    assert tuple(row.category_id for row in quality.category_rows) == (
        "sports",
        "crypto",
        "politics",
    )

    sports, crypto, politics = quality.category_rows
    assert sports.status == "blocked"
    assert sports.reason_codes == (
        "category_forecast_dispersion_excessive",
        "category_resolution_not_ready",
    )
    assert sports.source_family_count == d("1")
    assert sports.forecast_dispersion == d("0.850000")
    assert sports.resolution_ready_count == d("0")

    assert crypto.status == "watch"
    assert crypto.max_source_age_seconds == d("108000")
    assert crypto.reason_codes == (
        "category_low_source_family_diversity",
        "category_sources_stale",
    )

    assert politics.status == "clear"
    assert politics.source_family_count == d("2")
    assert politics.forecast_dispersion == d("0.100000")
    assert politics.momentum_delta_abs == d("0.020000")
    assert politics.resolution_ready_ratio == d("1.000000")
    assert politics.reason_codes == ("category_signal_quality_clear",)


def test_low_diversity_excessive_dispersion_and_unstable_momentum_thresholds() -> None:
    quality = report(
        signal(
            "macro",
            "rates-1",
            forecast_low="0.200000",
            forecast_high="0.900000",
            probability_now="0.850000",
            probability_previous="0.500000",
        ),
        signal(
            "macro",
            "rates-2",
            forecast_low="0.100000",
            forecast_high="0.800000",
            probability_now="0.150000",
            probability_previous="0.500000",
        ),
    )

    row = quality.category_rows[0]
    assert row.category_id == "macro"
    assert row.status == "blocked"
    assert row.source_family_count == d("1")
    assert row.forecast_dispersion == d("0.800000")
    assert row.momentum_delta_abs == d("0.350000")
    assert row.reason_codes == (
        "category_forecast_dispersion_excessive",
        "category_low_source_family_diversity",
        "category_probability_momentum_unstable",
    )


def test_sorting_uses_status_risk_metrics_and_category_id() -> None:
    quality = report(
        signal("zz-clear", "z-1", source_family="news"),
        signal(
            "aa-watch",
            "a-1",
            source_observed_at=GENERATED_AT - timedelta(hours=25),
        ),
        signal(
            "mm-watch",
            "m-1",
            probability_now="0.820000",
            probability_previous="0.500000",
        ),
        signal(
            "bb-blocked",
            "b-1",
            forecast_low="0.100000",
            forecast_high="0.950000",
        ),
        signal(
            "aa-blocked",
            "ab-1",
            resolution_ready=False,
            resolution_source_count="0",
        ),
    )

    assert tuple(row.category_id for row in quality.category_rows) == (
        "aa-blocked",
        "bb-blocked",
        "mm-watch",
        "aa-watch",
        "zz-clear",
    )


def test_payload_helper_uses_decimal_strings_and_no_float_surfaces() -> None:
    digest = api()
    quality = report(
        signal(
            "politics",
            "pol-1",
            source_observed_at=GENERATED_AT - timedelta(hours=2),
        ),
    )

    payload = digest.market_category_signal_quality_digest_payload(quality)
    payload_text = repr(payload).lower()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["market_count"] == "1"
    assert payload["category_rows"][0]["source_freshness_ratio"] == "1.000000"
    assert payload["category_rows"][0]["max_source_age_seconds"] == "7200"
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert '"1.000000"' in encoded
    assert_no_public_numbers(payload)
    assert "wallet" not in payload_text
    assert "secret" not in payload_text
    assert "token" not in payload_text
    assert "order" not in payload_text
    assert "recommend" not in payload_text
    assert "advice" not in payload_text


def test_validation_digest_is_deterministic_payload_bound_and_tamper_evident() -> None:
    digest = api()
    first = report(
        signal("politics", "pol-1", source_family="news"),
        signal("crypto", "btc-1", source_family="research"),
    )
    second = report(
        signal("crypto", "btc-1", source_family="research"),
        signal("politics", "pol-1", source_family="news"),
    )

    assert first.category_rows == second.category_rows
    assert first.derived_validation_digest == second.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in first.derived_validation_digest)

    payload = digest.market_category_signal_quality_digest_payload(first)
    assert payload["derived_validation_digest"] == first.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            first,
            category_rows=(
                replace(
                    first.category_rows[0],
                    latest_source_observed_at=(
                        first.category_rows[0].latest_source_observed_at
                        - timedelta(seconds=1)
                    ),
                ),
                *first.category_rows[1:],
            ),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_validation_errors_reject_bad_types_ranges_duplicates_and_flags() -> None:
    digest = api()

    with pytest.raises(ValueError, match="forecast_low must be a Decimal"):
        signal("politics", "pol-1", forecast_low="0.100000").__class__(
            category_id="politics",
            market_id="pol-2",
            source_family="news",
            source_observed_at=GENERATED_AT,
            forecast_low=0.1,
            forecast_high=d("0.500000"),
            probability_now=d("0.500000"),
            probability_previous=d("0.500000"),
            probability_observed_at=GENERATED_AT,
            resolution_ready=True,
            resolution_source_count=d("1"),
            reason_codes=("input_signal_quality_available",),
        )

    with pytest.raises(ValueError, match="forecast_high must be a Decimal"):
        replace(signal("politics", "pol-2"), forecast_high=1)

    with pytest.raises(ValueError, match="probability_now must be a Decimal"):
        replace(
            signal("politics", "pol-3"),
            probability_now=_DecimalSubclass("0.500000"),
        )

    with pytest.raises(ValueError, match="resolution_source_count must be a Decimal"):
        replace(signal("politics", "pol-4"), resolution_source_count=1)

    with pytest.raises(ValueError, match="resolution_ready must be a bool"):
        replace(signal("politics", "pol-5"), resolution_ready=1)

    with pytest.raises(ValueError, match="forecast_high must be finite"):
        replace(signal("politics", "pol-6"), forecast_high=Decimal("NaN"))

    with pytest.raises(ValueError, match="forecast_low must be less than or equal"):
        signal("politics", "pol-1", forecast_low="0.700000", forecast_high="0.600000")

    with pytest.raises(ValueError, match="inputs must not contain duplicate market_id"):
        report(signal("politics", "same"), signal("crypto", "same"))

    with pytest.raises(ValueError, match="config must be"):
        digest.build_market_category_signal_quality_digest_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        digest.MarketCategorySignalQualityDigestConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        digest.MarketCategorySignalQualityDigestConfig(report_only=False)

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(signal("politics", "pol-1"), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(signal("politics", "pol-1"), readonly=False)

    with pytest.raises(ValueError, match="report must be"):
        digest.market_category_signal_quality_digest_payload(object())

    quality = report(signal("politics", "pol-7"))
    with pytest.raises(ValueError, match="category_count"):
        replace(quality, category_count=d("2"))

    with pytest.raises(ValueError, match="category_rows"):
        replace(quality, category_rows=(object(),))

    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(quality, reason_code_counts=(object(),))

    with pytest.raises(FrozenInstanceError):
        quality.category_rows[0].status = "watch"  # type: ignore[misc]


def test_rejects_naive_datetimes() -> None:
    digest = api()

    with pytest.raises(ValueError, match="source_observed_at must be timezone-aware"):
        signal(
            "politics",
            "pol-1",
            source_observed_at=datetime(2026, 7, 2, 10, 0),
        )

    with pytest.raises(ValueError, match="probability_observed_at must be timezone-aware"):
        signal(
            "politics",
            "pol-1",
            probability_observed_at=datetime(2026, 7, 2, 10, 0),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest.build_market_category_signal_quality_digest_report(
            (),
            config=digest.MarketCategorySignalQualityDigestConfig(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )

    with pytest.raises(ValueError, match="source_observed_at must be timezone-aware"):
        signal(
            "politics",
            "pol-2",
            source_observed_at=datetime(
                2026,
                7,
                2,
                10,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )

    with pytest.raises(ValueError, match="probability_observed_at must be timezone-aware"):
        signal(
            "politics",
            "pol-3",
            probability_observed_at=datetime(
                2026,
                7,
                2,
                10,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        digest.build_market_category_signal_quality_digest_report(
            (),
            config=digest.MarketCategorySignalQualityDigestConfig(),
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )


def test_frozen_dataclasses_and_utc_datetime_normalization() -> None:
    digest = api()
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    quality = report(
        signal(
            "politics",
            "pol-1",
            source_observed_at=datetime(
                2026,
                7,
                2,
                3,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            probability_observed_at=datetime(
                2026,
                7,
                2,
                3,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=generated_at,
    )

    assert quality.generated_at == GENERATED_AT
    assert quality.generated_at.tzinfo is UTC
    assert quality.category_rows[0].latest_source_observed_at == datetime(
        2026,
        7,
        2,
        7,
        0,
        tzinfo=UTC,
    )
    assert quality.category_rows[0].latest_probability_observed_at == datetime(
        2026,
        7,
        2,
        7,
        30,
        tzinfo=UTC,
    )

    for value in (
        digest.MarketCategorySignalQualityDigestConfig(),
        signal("crypto", "btc-1"),
        quality.category_rows[0],
        quality.reason_code_counts[0],
        quality,
    ):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False


def test_public_dataclasses_expose_only_decimal_public_numerics() -> None:
    digest = api()
    quality = report(signal("politics", "pol-1"))
    values = {
        digest.MarketCategorySignalQualityDigestConfig: (
            digest.MarketCategorySignalQualityDigestConfig(),
            (
                "stale_source_age_seconds",
                "minimum_source_family_count",
                "excessive_forecast_dispersion",
                "unstable_momentum_delta",
            ),
        ),
        digest.MarketCategorySignalQualityInput: (
            signal("crypto", "btc-1"),
            (
                "forecast_low",
                "forecast_high",
                "probability_now",
                "probability_previous",
                "resolution_source_count",
            ),
        ),
        digest.MarketCategorySignalQualityCategoryRow: (
            quality.category_rows[0],
            (
                "market_count",
                "source_family_count",
                "fresh_source_count",
                "stale_source_count",
                "source_freshness_ratio",
                "max_source_age_seconds",
                "forecast_dispersion",
                "momentum_delta_abs",
                "resolution_ready_count",
                "resolution_not_ready_count",
                "resolution_ready_ratio",
                "resolution_source_count",
            ),
        ),
        digest.MarketCategorySignalQualityReasonCodeCount: (
            quality.reason_code_counts[0],
            ("count",),
        ),
        digest.MarketCategorySignalQualityDigestReport: (
            quality,
            (
                "category_count",
                "market_count",
                "clear_count",
                "watch_count",
                "blocked_count",
            ),
        ),
    }

    assert digest.__all__ == (
        "DEFAULT_MARKET_CATEGORY_SIGNAL_QUALITY_DIGEST_CONFIG_VERSION",
        "MarketCategorySignalQualityDigestConfig",
        "MarketCategorySignalQualityInput",
        "MarketCategorySignalQualityCategoryRow",
        "MarketCategorySignalQualityReasonCodeCount",
        "MarketCategorySignalQualityDigestReport",
        "build_market_category_signal_quality_digest_report",
        "market_category_signal_quality_digest_payload",
    )

    for exported_name in digest.__all__:
        exported = getattr(digest, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    for dataclass_type, (value, decimal_fields) in values.items():
        hints = get_type_hints(dataclass_type)
        dataclass_field_names = {item.name for item in fields(value)}
        for field_name in decimal_fields:
            assert field_name in dataclass_field_names
            assert hints[field_name] is Decimal
            assert type(getattr(value, field_name)) is Decimal


def test_public_strings_reject_unsafe_phase1_surface_values_without_leaking() -> None:
    digest = api()

    with pytest.raises(ValueError, match="config_version has unsafe value"):
        digest.MarketCategorySignalQualityDigestConfig(
            config_version="wallet-config",
        )

    for field_name, kwargs in (
        ("category_id", {"category_id": "wallet_team"}),
        ("market_id", {"market_id": "auth_market"}),
        ("source_family", {"source_family": "secret_feed"}),
    ):
        values = {
            "category_id": "politics",
            "market_id": "pol-1",
            "source_family": "news",
            **kwargs,
        }
        with pytest.raises(ValueError, match=f"{field_name} has unsafe value") as exc_info:
            signal(**values)
        assert next(iter(kwargs.values())) not in str(exc_info.value)


def test_module_scope_has_no_forbidden_live_or_advice_surface_terms() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_category_signal_quality_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "cancel",
        "replace",
        "exchange_mutation",
        "private_key",
        "secret",
        "token",
        "password",
        "payload_json",
        "investment_recommendation",
        "live trading",
        "order",
        "advice",
        "sqlite",
        "psycopg",
        "requests",
        "urllib",
        "open(",
        "httpx",
        "socket",
        "subprocess",
        "supabase",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imports: list[str] = []
    forbidden_import_fragments = (
        "auth",
        "broker",
        "client",
        "db",
        "http",
        "network",
        "order",
        "psycopg",
        "request",
        "socket",
        "sql",
        "subprocess",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "trade",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "file",
        "network",
        "order",
        "persist",
        "request",
        "submit",
        "trade",
        "wallet",
        "write",
    )
    forbidden_attr_names = {
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
            assert node.func.id not in forbidden_call_names
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_call_names
        if isinstance(node, ast.Attribute):
            lowered_attr = node.attr.lower()
            assert lowered_attr not in forbidden_attr_names
            assert not any(fragment in lowered_attr for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        lowered_module_name = module_name.lower()
        assert not any(fragment in lowered_module_name for fragment in forbidden_import_fragments)
