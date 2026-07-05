from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 3, 14, 0, tzinfo=UTC)


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "none-offset"


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_export_price_surprise_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object):
    digest = api()
    values = {
        "max_release_age_seconds": d("7200.000000"),
        "material_surprise_threshold": d("0.020000"),
        "high_revision_threshold": d("0.015000"),
        "min_source_count": d("2"),
        "watch_confidence_threshold": d("0.700000"),
    }
    values.update(overrides)
    return digest.MarketResearchExportPriceSurpriseDigestConfig(**values)


def item(
    release_key: str,
    *,
    country_code: str = "US",
    period: str = "2026-06",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=30),
    expected_price_index: str = "100.000000",
    actual_price_index: str = "101.000000",
    prior_price_index: str = "100.500000",
    surprise_ratio: str = "0.010000",
    source_count: str = "3",
    revision_ratio: str = "0.005000",
    base_confidence: str = "0.900000",
    signal_config_version: str = "export-price-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = api()
    return digest.MarketResearchExportPriceSurpriseInput(
        release_key=release_key,
        country_code=country_code,
        period=period,
        observed_at=observed_at,
        expected_price_index=d(expected_price_index),
        actual_price_index=d(actual_price_index),
        prior_price_index=d(prior_price_index),
        surprise_ratio=d(surprise_ratio),
        source_count=d(source_count),
        revision_ratio=d(revision_ratio),
        base_confidence=d(base_confidence),
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*rows, config=None, generated_at: datetime = GENERATED_AT):
    digest = api()
    return digest.build_market_research_export_price_surprise_digest(
        rows,
        config=config or cfg(),
        generated_at=generated_at,
    )


def test_export_price_surprise_digest_reduces_and_sorts_deterministically() -> None:
    digest_report = report(
        item(
            "exports.jp.price_index",
            country_code="JP",
            observed_at=GENERATED_AT - timedelta(hours=3),
            expected_price_index="98.000000",
            actual_price_index="94.500000",
            prior_price_index="95.000000",
            surprise_ratio="-0.035714",
            source_count="1",
            revision_ratio="0.018000",
            base_confidence="0.860000",
        ),
        item(
            "exports.us.price_index",
            country_code="US",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            expected_price_index="100.000000",
            actual_price_index="103.000000",
            prior_price_index="101.000000",
            surprise_ratio="0.030000",
            source_count="3",
            revision_ratio="0.010000",
            base_confidence="0.920000",
        ),
        item(
            "exports.eu.price_index",
            country_code="EU",
            observed_at=GENERATED_AT - timedelta(minutes=10),
            expected_price_index="100.000000",
            actual_price_index="100.500000",
            prior_price_index="100.200000",
            surprise_ratio="0.005000",
            source_count="2",
            revision_ratio="0.003000",
            base_confidence="0.930000",
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    digest = api()
    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        digest.DEFAULT_MARKET_RESEARCH_EXPORT_PRICE_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_market_research_export_price_surprise_digest"
    )
    assert digest_report.input_count == d("3")
    assert digest_report.ready_count == d("1")
    assert digest_report.watch_count == d("1")
    assert digest_report.blocked_count == d("1")
    assert digest_report.material_surprise_count == d("2")
    assert digest_report.stale_release_count == d("1")
    assert digest_report.thin_source_count == d("1")
    assert digest_report.high_revision_count == d("1")
    assert digest_report.average_abs_surprise_ratio == d("0.023571")
    assert digest_report.max_abs_surprise_ratio == d("0.035714")
    assert digest_report.max_release_age_seconds == d("10800.000000")
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    assert tuple(row.release_key for row in digest_report.rows) == (
        "exports.jp.price_index",
        "exports.us.price_index",
        "exports.eu.price_index",
    )

    jp = digest_report.rows[0]
    assert jp.digest_status == "blocked"
    assert jp.release_age_seconds == d("10800.000000")
    assert jp.surprise_delta == d("-3.500000")
    assert jp.prior_revision_delta == d("-0.500000")
    assert jp.surprise_direction == "negative"
    assert jp.final_confidence == d("0.430000")
    assert jp.reason_codes == (
        "market_research_export_price_surprise_digest_stale_release",
        "market_research_export_price_surprise_digest_material_surprise",
        "market_research_export_price_surprise_digest_thin_sources",
        "market_research_export_price_surprise_digest_high_revision",
    )

    us = digest_report.rows[1]
    assert us.digest_status == "watch"
    assert us.release_age_seconds == d("1200.000000")
    assert us.surprise_delta == d("3.000000")
    assert us.prior_revision_delta == d("2.000000")
    assert us.surprise_direction == "positive"
    assert us.final_confidence == d("0.828000")
    assert us.reason_codes == (
        "market_research_export_price_surprise_digest_material_surprise",
    )

    eu = digest_report.rows[2]
    assert eu.digest_status == "ready"
    assert eu.surprise_direction == "neutral"
    assert eu.final_confidence == d("0.930000")
    assert eu.reason_codes == (
        "market_research_export_price_surprise_digest_ready",
    )

    assert digest_report.reason_code_counts == (
        digest.MarketResearchExportPriceSurpriseReasonCodeCount(
            reason_code="market_research_export_price_surprise_digest_material_surprise",
            count=d("2"),
            input_ratio=d("0.666667"),
        ),
        digest.MarketResearchExportPriceSurpriseReasonCodeCount(
            reason_code="market_research_export_price_surprise_digest_stale_release",
            count=d("1"),
            input_ratio=d("0.333333"),
        ),
        digest.MarketResearchExportPriceSurpriseReasonCodeCount(
            reason_code="market_research_export_price_surprise_digest_thin_sources",
            count=d("1"),
            input_ratio=d("0.333333"),
        ),
        digest.MarketResearchExportPriceSurpriseReasonCodeCount(
            reason_code="market_research_export_price_surprise_digest_high_revision",
            count=d("1"),
            input_ratio=d("0.333333"),
        ),
        digest.MarketResearchExportPriceSurpriseReasonCodeCount(
            reason_code="market_research_export_price_surprise_digest_ready",
            count=d("1"),
            input_ratio=d("0.333333"),
        ),
    )
    assert digest_report.reason_codes == tuple(
        row.reason_code for row in digest_report.reason_code_counts
    )


def test_empty_digest_is_report_only_blocked_and_uses_decimal_zeroes() -> None:
    digest_report = report()

    assert digest_report.input_count == d("0")
    assert digest_report.ready_count == d("0")
    assert digest_report.watch_count == d("0")
    assert digest_report.blocked_count == d("0")
    assert digest_report.material_surprise_count == d("0")
    assert digest_report.stale_release_count == d("0")
    assert digest_report.thin_source_count == d("0")
    assert digest_report.high_revision_count == d("0")
    assert digest_report.average_abs_surprise_ratio == d("0.000000")
    assert digest_report.max_abs_surprise_ratio == d("0.000000")
    assert digest_report.max_release_age_seconds == d("0.000000")
    assert digest_report.digest_status == "blocked"
    assert digest_report.reason_codes == (
        "market_research_export_price_surprise_digest_no_inputs",
    )
    assert digest_report.rows == ()
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_digest_rejects_float_numeric_inputs_naive_datetimes_duplicates_and_mutation() -> None:
    digest = api()

    with pytest.raises(ValueError, match="actual_price_index must be a Decimal"):
        digest.MarketResearchExportPriceSurpriseInput(
            release_key="exports.us.price_index",
            country_code="US",
            period="2026-06",
            observed_at=GENERATED_AT,
            expected_price_index=d("100"),
            actual_price_index=101.0,
            prior_price_index=d("100"),
            surprise_ratio=d("0.010000"),
            source_count=d("1"),
            revision_ratio=d("0.000000"),
            base_confidence=d("0.900000"),
            signal_config_version="export-price-signal-v0",
        )

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        item("exports.us.price_index", observed_at=datetime(2026, 7, 3, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        item(
            "exports.no-offset",
            observed_at=datetime(2026, 7, 3, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )

    row = item("exports.us.price_index")
    with pytest.raises(FrozenInstanceError):
        row.actual_price_index = d("1")  # type: ignore[misc]

    config = cfg()
    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]

    digest_report = report(
        item(
            "exports.frozen.price_index",
            expected_price_index="100.000000",
            actual_price_index="103.000000",
            prior_price_index="101.000000",
            surprise_ratio="0.030000",
        ),
    )
    with pytest.raises(FrozenInstanceError):
        digest_report.digest_status = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest_report.rows[0].digest_status = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest_report.reason_code_counts[0].count = d("2.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        digest.MarketResearchExportPriceSurpriseDigestConfig(readonly=False)

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(
            item("exports.us.price_index", period="2026-06"),
            item("exports.us.price_index", period="2026-06"),
        )


def test_payload_is_json_ready_and_omits_live_or_durable_surfaces() -> None:
    payload = api().market_research_export_price_surprise_digest_payload(
        report(
            item(
                "exports.us.price_index",
                expected_price_index="100.000000",
                actual_price_index="103.000000",
                prior_price_index="101.000000",
                surprise_ratio="0.030000",
            ),
        ),
    )

    payload_text = repr(payload).lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "market_slug",
        "question",
        "payload_json",
        "investment_recommendation",
        "durable",
        "order_id",
        "submit_order",
        "cancel_order",
    ):
        assert forbidden not in payload_text
    assert payload["input_count"] == "1.000000"
    assert payload["ready_count"] == "0.000000"
    assert payload["watch_count"] == "1.000000"
    assert payload["blocked_count"] == "0.000000"
    assert payload["max_abs_surprise_ratio"] == "0.030000"
    assert payload["rows"][0]["surprise_ratio"] == "0.030000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"


def test_digest_rejects_each_false_report_only_flag() -> None:
    digest = api()
    digest_report = report(item("exports.us.price_index"))
    row = digest_report.rows[0]
    reason_count = digest_report.reason_code_counts[0]

    false_flag_cases = (
        lambda: cfg(paper_only=False),
        lambda: cfg(report_only=False),
        lambda: cfg(readonly=False),
        lambda: item("exports.config.flag.paper", paper_only=False),
        lambda: item("exports.config.flag.report", report_only=False),
        lambda: item("exports.config.flag.readonly", readonly=False),
        lambda: replace(row, paper_only=False),
        lambda: replace(row, report_only=False),
        lambda: replace(row, readonly=False),
        lambda: replace(reason_count, paper_only=False),
        lambda: replace(reason_count, report_only=False),
        lambda: replace(reason_count, readonly=False),
        lambda: replace(digest_report, paper_only=False),
        lambda: replace(digest_report, report_only=False),
        lambda: replace(digest_report, readonly=False),
    )

    for make_invalid_record in false_flag_cases:
        with pytest.raises(ValueError, match="must be True"):
            make_invalid_record()

    with pytest.raises(ValueError, match="report must be"):
        digest.market_research_export_price_surprise_digest_payload(
            {"paper_only": False, "report_only": False, "readonly": False},
        )


def test_module_scope_has_no_network_store_fast_live_trading_or_float_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_research_export_price_surprise_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "psycopg",
        "sqlite",
        "supabase",
        "auth",
        "wallet",
        "account",
        "market_slug",
        "question",
        "payload_json",
        "investment_recommendation",
        "durable",
        "open(",
        "trade",
        "order_id",
        "submit_order",
        "cancel_order",
        "fast",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
